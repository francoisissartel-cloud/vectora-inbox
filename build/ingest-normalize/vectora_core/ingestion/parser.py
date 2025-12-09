"""
Module de parsing des contenus bruts en items structurés.

Ce module convertit les contenus bruts (RSS, HTML, JSON) en items bruts
avec une structure uniforme.

Pour le MVP, on se concentre sur les flux RSS/Atom.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import feedparser

logger = logging.getLogger(__name__)


def parse_source_content(
    raw_content: str,
    source_meta: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Parse le contenu brut d'une source en liste d'items bruts.
    
    Supporte :
    - Flux RSS/Atom (ingestion_mode='rss')
    - Pages HTML (ingestion_mode='html')
    
    Args:
        raw_content: Contenu brut (XML, HTML)
        source_meta: Métadonnées de la source (source_key, ingestion_mode, etc.)
    
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
    ingestion_mode = source_meta.get('ingestion_mode', 'rss')
    
    logger.info(f"Parsing du contenu de {source_key} (mode: {ingestion_mode})")
    
    items = []
    if ingestion_mode == 'rss':
        items = _parse_rss_feed(raw_content, source_key, source_type)
    elif ingestion_mode == 'html':
        items = _parse_html_page(raw_content, source_key, source_type, source_meta)
    else:
        logger.warning(f"Source {source_key} : mode '{ingestion_mode}' non supporté")
    
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


def _parse_html_page(
    raw_content: str,
    source_key: str,
    source_type: str,
    source_meta: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Parse une page HTML pour extraire des items de news.
    
    Parser générique simple (KISS) qui cherche des patterns courants.
    Ne garantit pas de fonctionner sur toutes les structures HTML.
    
    Args:
        raw_content: Contenu HTML de la page
        source_key: Identifiant de la source
        source_type: Type de source
        source_meta: Métadonnées complètes de la source
    
    Returns:
        Liste d'items bruts (peut être vide si structure non reconnue)
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error(f"BeautifulSoup non installé, impossible de parser HTML pour {source_key}")
        return []
    
    try:
        soup = BeautifulSoup(raw_content, 'html.parser')
        items = []
        
        # Chercher des patterns courants de news
        # Pattern 1: balises <article>
        articles = soup.find_all('article')
        for article in articles[:20]:  # Limiter à 20 items max
            item = _extract_item_from_element(article, source_key, source_type)
            if item:
                items.append(item)
        
        # Pattern 2: si pas d'articles, chercher des divs avec class contenant 'news', 'post', 'item'
        if not items:
            news_divs = soup.find_all('div', class_=lambda x: x and any(k in x.lower() for k in ['news', 'post', 'item', 'press']))
            for div in news_divs[:20]:
                item = _extract_item_from_element(div, source_key, source_type)
                if item:
                    items.append(item)
        
        if not items:
            logger.warning(f"Source {source_key} : parsing HTML n'a produit aucun item (structure non reconnue)")
        
        return items
    
    except Exception as e:
        logger.error(f"Erreur lors du parsing HTML de {source_key}: {e}")
        return []


def _extract_item_from_element(element, source_key: str, source_type: str) -> Optional[Dict[str, Any]]:
    """
    Extrait un item depuis un élément HTML (article, div, etc.).
    
    Args:
        element: Élément BeautifulSoup
        source_key: Identifiant de la source
        source_type: Type de source
    
    Returns:
        Item brut ou None si extraction impossible
    """
    try:
        # Chercher un lien (a href)
        link = element.find('a', href=True)
        if not link:
            return None
        
        url = link.get('href', '')
        if not url:
            return None
        
        # Si URL relative, essayer de la compléter (simplifié)
        if url.startswith('/'):
            # On ne peut pas compléter sans le domaine, on skip
            return None
        
        # Titre : texte du lien ou d'un heading proche
        title = link.get_text(strip=True)
        if not title:
            heading = element.find(['h1', 'h2', 'h3', 'h4'])
            if heading:
                title = heading.get_text(strip=True)
        
        if not title:
            return None
        
        # Description : chercher un paragraphe ou div avec texte
        raw_text = ''
        desc = element.find(['p', 'div'], class_=lambda x: x and 'desc' in x.lower() if x else False)
        if desc:
            raw_text = desc.get_text(strip=True)
        
        # Date : date actuelle par défaut
        published_at = datetime.now().strftime('%Y-%m-%d')
        
        return {
            'title': title,
            'url': url,
            'published_at': published_at,
            'raw_text': raw_text,
            'source_key': source_key,
            'source_type': source_type
        }
    
    except Exception as e:
        logger.debug(f"Impossible d'extraire item depuis élément: {e}")
        return None
