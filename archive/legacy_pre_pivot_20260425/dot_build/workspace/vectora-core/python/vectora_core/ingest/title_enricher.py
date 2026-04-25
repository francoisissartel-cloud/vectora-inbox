"""
Title Enricher - Enrichit les titres génériques extraits du parsing HTML.

Stratégie:
1. Détecter titres génériques (Press Releases, PRESSRELEASES, etc.)
2. Extraire vrai titre depuis contenu (premières lignes significatives)
3. Fallback: extraire depuis URL (slug)
"""

import re
import logging

logger = logging.getLogger(__name__)

# Titres génériques à enrichir
GENERIC_TITLES = [
    "Press Releases",
    "PRESSRELEASES", 
    "PRESENTATIONS",
    "News",
    "Media",
    "Press Release",
]

def is_generic_title(title: str) -> bool:
    """Vérifie si un titre est générique"""
    return title.strip() in GENERIC_TITLES or len(title.strip()) < 15

def extract_title_from_content(content: str, url: str = None) -> str:
    """
    Extrait un titre significatif depuis le contenu ou l'URL.
    
    Args:
        content: Contenu textuel de l'item
        url: URL de l'item (fallback)
    
    Returns:
        Titre enrichi ou None si échec
    """
    # Patterns génériques à ignorer dans le contenu
    generic_patterns = [
        r'^MEDIA\s+All\s+Press\s+Releases',
        r'^Article\s+\w+\s+Press\s+release',
        r'^\d{1,2}\s+\w+\s+\d{4}$',  # Juste une date
    ]
    
    # Si contenu trop court (< 30 chars), utiliser URL directement
    if len(content.strip()) < 30:
        if url:
            return _extract_title_from_url(url)
        return None
    
    # Chercher dans les premières lignes du contenu
    lines = content.split('\n')
    
    for line in lines[:10]:  # Max 10 premières lignes
        line = line.strip()
        
        # Ignorer lignes vides ou trop courtes
        if not line or len(line) < 20:
            continue
        
        # Ignorer patterns génériques
        is_generic = any(re.match(pattern, line) for pattern in generic_patterns)
        if is_generic:
            continue
        
        # Chercher un titre significatif (commence par majuscule, > 30 chars)
        if line[0].isupper() and len(line) > 30:
            # Nettoyer le titre
            title = re.sub(r'\s+', ' ', line)  # Normaliser espaces
            title = title[:200]  # Limiter longueur
            return title
    
    # Fallback: extraire depuis URL
    if url:
        return _extract_title_from_url(url)
    
    return None

def _extract_title_from_url(url: str) -> str:
    """Extrait un titre depuis le slug de l'URL"""
    if not url:
        return None
    
    # Extraire le slug (dernier segment avant .pdf ou fin)
    match = re.search(r'/([^/]+?)(?:\.pdf)?/?$', url)
    if not match:
        return None
    
    slug = match.group(1)
    
    # Ignorer slugs trop courts ou génériques
    if len(slug) < 3 or slug.lower() in ['index', 'home', 'news', 'media']:
        return None
    
    # Convertir slug en titre
    title = slug.replace('-', ' ').replace('_', ' ')
    title = ' '.join(word.capitalize() for word in title.split())
    
    # Accepter même les titres courts pour les PDFs
    if len(title) > 5:
        return title
    
    return None

def enrich_item_title(item: dict) -> dict:
    """
    Enrichit le titre d'un item s'il est générique.
    
    Args:
        item: Item avec titre potentiellement générique
    
    Returns:
        Item avec titre enrichi (modifié in-place)
    """
    title = item.get('title', '')
    
    if not is_generic_title(title):
        return item  # Titre déjà bon
    
    content = item.get('content', '')
    url = item.get('url', '')
    
    # Extraire nouveau titre
    new_title = extract_title_from_content(content, url)
    
    if new_title:
        logger.info(f"[ENRICH] Title enriched: '{title}' → '{new_title[:60]}'")
        item['title'] = new_title
        item['title_enriched'] = True
        item['original_title'] = title
    else:
        logger.warning(f"[ENRICH] Failed to enrich title: {title}")
    
    return item

def enrich_items_titles(items: list) -> list:
    """
    Enrichit les titres de tous les items d'une liste.
    
    Args:
        items: Liste d'items
    
    Returns:
        Liste d'items avec titres enrichis
    """
    enriched_count = 0
    
    for item in items:
        original_title = item.get('title', '')
        enrich_item_title(item)
        
        if item.get('title') != original_title:
            enriched_count += 1
    
    if enriched_count > 0:
        logger.info(f"[ENRICH] {enriched_count}/{len(items)} titles enriched")
    
    return items
