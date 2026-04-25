"""
Extraction légère de date d'événement pour filtrage temporel.

Ce module extrait rapidement la date d'événement SANS Bedrock,
permettant de filtrer les items avant normalisation coûteuse.
"""

import re
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def extract_event_date_lightweight(title: str, content: str) -> Dict:
    """
    Extraction rapide de date d'événement par regex.
    
    Utilisé pour filtrage temporel AVANT normalisation Bedrock.
    
    Args:
        title: Titre de l'item
        content: Contenu de l'item (premiers 300 chars suffisent)
    
    Returns:
        {
            'event_date': '2025-11-10' ou None,
            'confidence': 0.0-1.0,
            'source': 'title_prefix' | 'content_extraction' | 'no_event_date'
        }
    """
    
    # Nettoyer le titre (fix "10November2025" → "10 November 2025")
    title_clean = _clean_title_spacing(title)
    
    # Pattern 1: Date en début de titre (haute confiance)
    # "10 November 2025 Regulatory..."
    # "03 November 2025 Camurus launches..."
    match = re.search(r'^(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})', title_clean, re.IGNORECASE)
    if match:
        date_str = match.group(1)
        parsed = _parse_date_string(date_str)
        if parsed:
            logger.info(f"Event date from title prefix: {parsed} (confidence: 0.85)")
            return {
                'event_date': parsed,
                'confidence': 0.85,
                'source': 'title_prefix'
            }
    
    # Pattern 2: Date dans titre (moyenne confiance)
    # "Camurus reports results on 10 November 2025"
    patterns_title = [
        r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
        r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]
    
    for pattern in patterns_title:
        match = re.search(pattern, title_clean, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            parsed = _parse_date_string(date_str)
            if parsed:
                logger.info(f"Event date from title: {parsed} (confidence: 0.75)")
                return {
                    'event_date': parsed,
                    'confidence': 0.75,
                    'source': 'title_extraction'
                }
    
    # Pattern 3: Date dans contenu (basse confiance)
    # "On November 10, 2025, Camurus announced..."
    # "Dated November 10, 2025"
    content_preview = content[:300]
    patterns_content = [
        r'(?:on|dated?)\s+(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4})',
        r'(?:on|dated?)\s+((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
        r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
    ]
    
    for pattern in patterns_content:
        match = re.search(pattern, content_preview, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            parsed = _parse_date_string(date_str)
            if parsed:
                logger.info(f"Event date from content: {parsed} (confidence: 0.60)")
                return {
                    'event_date': parsed,
                    'confidence': 0.60,
                    'source': 'content_extraction'
                }
    
    # Aucune date trouvée
    logger.debug("No event date found in title or content")
    return {
        'event_date': None,
        'confidence': 0.0,
        'source': 'no_event_date'
    }


def _clean_title_spacing(title: str) -> str:
    """
    Nettoie les espaces manquants dans le titre.
    
    Exemples:
        "10November2025Regulatory" → "10 November 2025 Regulatory"
        "03November2025Camurus" → "03 November 2025 Camurus"
    """
    # Ajouter espace entre chiffre et mois
    title = re.sub(r'(\d)(January|February|March|April|May|June|July|August|September|October|November|December)', r'\1 \2', title, flags=re.IGNORECASE)
    
    # Ajouter espace entre année et mot suivant
    title = re.sub(r'(\d{4})([A-Z])', r'\1 \2', title)
    
    return title


def _parse_date_string(date_str: str) -> Optional[str]:
    """
    Parse une chaîne de date en format ISO (YYYY-MM-DD).
    
    Args:
        date_str: Date à parser (ex: "10 November 2025", "2025-11-10")
    
    Returns:
        Date au format YYYY-MM-DD ou None si parsing échoue
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Formats à tester
    date_formats = [
        '%d %B %Y',      # 10 November 2025
        '%d %B, %Y',     # 10 November, 2025
        '%B %d, %Y',     # November 10, 2025
        '%B %d %Y',      # November 10 2025
        '%Y-%m-%d',      # 2025-11-10
        '%d %b %Y',      # 10 Nov 2025
        '%d %b, %Y',     # 10 Nov, 2025
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    logger.debug(f"Failed to parse date: '{date_str}'")
    return None


def should_process_item(item: Dict, cutoff_date: str, min_confidence: float = 0.60) -> bool:
    """
    Détermine si un item doit être traité (normalisé) selon sa date d'événement.
    
    Logique:
    - Si event_date trouvée avec confiance >= min_confidence:
        → Traiter SI event_date >= cutoff_date
    - Si event_date non trouvée ou confiance faible:
        → Traiter (Bedrock extraira la date)
    
    Args:
        item: Item avec event_date_preliminary
        cutoff_date: Date de coupure (YYYY-MM-DD)
        min_confidence: Confiance minimale pour filtrer
    
    Returns:
        True si item doit être traité, False sinon
    """
    event_date = item.get('event_date_preliminary')
    confidence = item.get('event_date_confidence', 0.0)
    
    # Pas de date trouvée → traiter (Bedrock extraira)
    if not event_date:
        logger.debug(f"Item {item.get('title', '')[:50]}: No event date, will process")
        return True
    
    # Date trouvée mais confiance faible → traiter (Bedrock confirmera)
    if confidence < min_confidence:
        logger.debug(f"Item {item.get('title', '')[:50]}: Low confidence ({confidence}), will process")
        return True
    
    # Date trouvée avec bonne confiance → filtrer
    if event_date >= cutoff_date:
        logger.info(f"Item {item.get('title', '')[:50]}: Event date {event_date} >= {cutoff_date}, will process")
        return True
    else:
        logger.info(f"Item {item.get('title', '')[:50]}: Event date {event_date} < {cutoff_date}, SKIP")
        return False
