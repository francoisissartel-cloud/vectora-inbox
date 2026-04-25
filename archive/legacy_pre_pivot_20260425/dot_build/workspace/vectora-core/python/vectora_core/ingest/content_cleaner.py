"""
Module de nettoyage et enrichissement du contenu des items.
Appliqué APRÈS parsing et AVANT filtrage pour avoir un contenu propre.
"""

import logging
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_and_enrich_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Nettoie et enrichit les items après parsing et avant filtrage.
    
    Pour chaque item:
    1. Nettoie le contenu (retire footers, headers, disclaimers)
    2. Limite à 3000 chars de contenu principal
    3. Garde le contenu brut dans 'raw_content' pour référence
    
    Args:
        items: Liste d'items parsés
        
    Returns:
        Liste d'items avec contenu nettoyé
    """
    cleaned_items = []
    
    for item in items:
        try:
            cleaned_item = _clean_single_item(item)
            cleaned_items.append(cleaned_item)
        except Exception as e:
            logger.warning(f"Failed to clean item {item.get('url', 'unknown')}: {e}")
            cleaned_items.append(item)  # Keep original if cleaning fails
    
    logger.info(f"Cleaned {len(cleaned_items)} items")
    return cleaned_items


def _clean_single_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Nettoie un seul item."""
    content = item.get('content', '')
    
    if not content or len(content) < 100:
        return item
    
    # Sauvegarder le contenu brut
    item['raw_content'] = content
    
    # Nettoyer le contenu
    cleaned_content = _extract_main_content(content)
    
    # Limiter à 3000 chars
    if len(cleaned_content) > 3000:
        cleaned_content = cleaned_content[:3000]
        logger.debug(f"Content truncated from {len(content)} to 3000 chars")
    
    item['content'] = cleaned_content
    item['content_cleaned'] = True
    
    return item


def clean_html_content(content: str) -> str:
    """
    Nettoie le contenu HTML en supprimant les balises.
    Utilisé pour nettoyer le contenu RSS/HTML brut.
    
    Args:
        content: Contenu HTML brut
    
    Returns:
        Contenu textuel nettoyé
    """
    try:
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except ImportError:
        # Fallback sans BeautifulSoup
        clean = re.sub('<[^<]+?>', ' ', content)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    except Exception:
        return content.strip()


def _extract_main_content(content: str) -> str:
    """
    Extrait le contenu principal en retirant les éléments parasites.
    
    Retire:
    - Footers légaux (disclaimers, forward-looking statements)
    - Headers de navigation
    - Métadonnées de contact
    - Sections "About Company"
    """
    # Patterns de sections à retirer
    footer_patterns = [
        r'forward-looking.*?(?:statements?|information).*?(?:\n\n|\Z)',
        r'disclosure notice.*?(?:\n\n|\Z)',
        r'about (?:pfizer|the company).*?(?:\n\n|\Z)',
        r'media contact.*?(?:\n\n|\Z)',
        r'investor contact.*?(?:\n\n|\Z)',
        r'for more information.*?(?:\n\n|\Z)',
        r'©\s*\d{4}.*?(?:\n|\Z)',
        r'all rights reserved.*?(?:\n|\Z)',
        r'privacy.*?policy.*?(?:\n|\Z)',
        r'terms.*?(?:of use|and conditions).*?(?:\n|\Z)',
    ]
    
    cleaned = content
    
    # Retirer les sections footer
    for pattern in footer_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    
    # Retirer les lignes très courtes (navigation, etc.)
    lines = cleaned.split('\n')
    meaningful_lines = []
    
    for line in lines:
        line = line.strip()
        # Garder les lignes avec au moins 30 chars ou qui sont des titres
        if len(line) >= 30 or (len(line) > 0 and line[0].isupper() and len(line) < 100):
            meaningful_lines.append(line)
    
    cleaned = ' '.join(meaningful_lines)
    
    # Normaliser les espaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned
