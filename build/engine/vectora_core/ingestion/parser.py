"""
Module de parsing des contenus bruts en items structurés.

Ce module convertit les contenus bruts (RSS, HTML, JSON) en items bruts
avec une structure uniforme.

Pour le MVP, on se concentre sur les flux RSS/Atom.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

import feedparser

logger = logging.getLogger(__name__)


def parse_source_content(
    raw_content: str,
    source_meta: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Parse le contenu brut d'une source en liste d'items bruts.
    
    Détecte automatiquement le type de contenu et applique le parser approprié.
    Pour le MVP, on supporte principalement les flux RSS/Atom.
    
    Args:
        raw_content: Contenu brut (XML, HTML, JSON)
        source_meta: Métadonnées de la source (source_key, source_type, etc.)
    
    Returns:
        Liste d'items bruts, chaque item contenant :
        - title: titre de l'item
        - url: lien vers l'article original
        - published_at: date de publication (ISO8601 si possible)
        - raw_text: texte brut (description ou contenu)
        - source_key: identifiant de la source
        - source_type: type de source
    """
    source_key = source_meta.get('source_key')
    source_type = source_meta.get('source_type')
    
    logger.info(f"Parsing du contenu de {source_key} (type: {source_type})")
    
    # Pour le MVP, on traite tout comme du RSS/Atom
    items = _parse_rss_feed(raw_content, source_key, source_type)
    
    logger.info(f"Source {source_key} : {len(items)} items parsés")
    
    return items


def _parse_rss_feed(
    raw_content: str,
    source_key: str,
    source_type: str
) -> List[Dict[str, Any]]:
    """
    Parse un flux RSS/Atom avec feedparser.
    
    Args:
        raw_content: Contenu XML du flux
        source_key: Identifiant de la source
        source_type: Type de source
    
    Returns:
        Liste d'items bruts
    """
    try:
        feed = feedparser.parse(raw_content)
        
        if feed.bozo:
            logger.warning(f"Source {source_key} : flux RSS mal formé (bozo=True)")
        
        items = []
        
        for entry in feed.entries:
            # Extraction des champs de base
            title = entry.get('title', '').strip()
            url = entry.get('link', '').strip()
            
            # Description ou contenu
            raw_text = ''
            if 'summary' in entry:
                raw_text = entry.summary
            elif 'description' in entry:
                raw_text = entry.description
            elif 'content' in entry and len(entry.content) > 0:
                raw_text = entry.content[0].get('value', '')
            
            # Date de publication
            published_at = _extract_published_date(entry)
            
            # Ne garder que les items avec au moins un titre et une URL
            if title and url:
                items.append({
                    'title': title,
                    'url': url,
                    'published_at': published_at,
                    'raw_text': raw_text,
                    'source_key': source_key,
                    'source_type': source_type
                })
        
        return items
    
    except Exception as e:
        logger.error(f"Erreur lors du parsing RSS de {source_key}: {e}")
        return []


def _extract_published_date(entry: Any) -> str:
    """
    Extrait la date de publication d'une entrée RSS et la formate en ISO8601.
    
    Args:
        entry: Entrée feedparser
    
    Returns:
        Date au format ISO8601 (YYYY-MM-DD) ou date actuelle si non trouvée
    """
    try:
        # feedparser fournit published_parsed ou updated_parsed
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime(*entry.published_parsed[:6])
            return dt.strftime('%Y-%m-%d')
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            dt = datetime(*entry.updated_parsed[:6])
            return dt.strftime('%Y-%m-%d')
    except Exception as e:
        logger.debug(f"Impossible d'extraire la date de publication: {e}")
    
    # Par défaut : date actuelle
    return datetime.now().strftime('%Y-%m-%d')
