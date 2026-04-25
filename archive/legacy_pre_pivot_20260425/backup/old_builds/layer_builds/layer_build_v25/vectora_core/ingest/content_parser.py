"""
Content Parser pour Vectora Inbox V2.

Ce module transforme les contenus bruts en items structurés :
- Parsing des flux RSS en articles individuels
- Extraction de contenu depuis les pages HTML
- Normalisation des formats de dates et URLs
- Génération des identifiants uniques et hashes de contenu

Responsabilités :
- Parser les contenus RSS/HTML/API en items structurés
- Extraire les métadonnées (titre, contenu, date, auteur)
- Générer les identifiants uniques (item_id)
- Calculer les hashes de contenu pour la déduplication
- Détecter la langue du contenu
"""

from typing import Any, Dict, List, Optional
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_source_content(raw_content: Dict[str, Any], source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse le contenu brut d'une source en items structurés.
    
    Args:
        raw_content: Contenu brut récupéré par source_fetcher
        source_meta: Métadonnées de la source
    
    Returns:
        Liste d'items structurés selon le format Vectora :
            - item_id: Identifiant unique de l'item
            - source_key: Identifiant de la source
            - source_type: Type de source (rss/html/api)
            - title: Titre de l'item
            - content: Contenu textuel complet
            - url: URL de l'item original
            - published_at: Date de publication (YYYY-MM-DD)
            - ingested_at: Date d'ingestion (ISO8601)
            - language: Code langue détecté
            - content_hash: Hash SHA256 du contenu
            - metadata: Métadonnées supplémentaires
    
    Raises:
        Exception: Si le parsing échoue complètement
    """
    source_key = raw_content.get('source_key')
    source_type = raw_content.get('source_type', 'unknown')
    
    # Vérifier si la récupération a échoué
    if raw_content.get('error') or not raw_content.get('raw_content'):
        logger.warning(f"Contenu vide ou en erreur pour {source_key}, aucun item à parser")
        return []
    
    logger.info(f"Parsing du contenu pour : {source_key}")
    
    ingested_at = raw_content.get('fetched_at', datetime.now().isoformat())
    content_text = raw_content.get('raw_content', '')
    
    # Déterminer le mode de parsing selon le type de source
    ingestion_mode = source_meta.get('ingestion_mode', 'rss')
    
    if ingestion_mode == 'rss':
        return _parse_rss_content(content_text, source_key, source_type, ingested_at)
    elif ingestion_mode == 'html':
        return _parse_html_content(content_text, source_key, source_type, source_meta, ingested_at)
    elif ingestion_mode == 'api':
        return _parse_api_content(content_text, source_key, source_type, ingested_at)
    else:
        logger.error(f"Mode d'ingestion non supporté pour le parsing : {ingestion_mode}")
        return []


def _parse_rss_content(content_text: str, source_key: str, source_type: str, ingested_at: str) -> List[Dict[str, Any]]:
    """
    Parse un flux RSS en items individuels.
    
    Args:
        content_text: Contenu RSS brut
        source_key: Identifiant de la source
        source_type: Type de source
        ingested_at: Timestamp d'ingestion
    
    Returns:
        Liste d'items parsés depuis le flux RSS
    """
    try:
        import feedparser
    except ImportError:
        logger.error("feedparser non installé, impossible de parser RSS")
        return []
    
    try:
        feed = feedparser.parse(content_text)
        
        if feed.bozo:
            logger.warning(f"Source {source_key} : flux RSS mal formé (bozo=True)")
        
        items = []
        
        for entry in feed.entries:
            # Extraction des champs de base
            title = entry.get('title', '').strip()
            url = entry.get('link', '').strip()
            
            # Description ou contenu
            content = ''
            if 'summary' in entry:
                content = entry.summary
            elif 'description' in entry:
                content = entry.description
            elif 'content' in entry and len(entry.content) > 0:
                content = entry.content[0].get('value', '')
            
            # Nettoyer le contenu HTML
            content = _clean_html_content(content)
            
            # Date de publication
            published_at = _extract_published_date(entry)
            
            # Ne garder que les items avec au moins un titre et une URL
            if title and url and content:
                item_id = generate_item_id(source_key, published_at, title)
                content_hash = calculate_content_hash(content)
                language = detect_language(content)
                
                items.append({
                    'item_id': item_id,
                    'source_key': source_key,
                    'source_type': source_type,
                    'title': title,
                    'content': content,
                    'url': url,
                    'published_at': published_at,
                    'ingested_at': ingested_at,
                    'language': language,
                    'content_hash': content_hash,
                    'metadata': {
                        'author': entry.get('author', ''),
                        'tags': [tag.get('term', '') for tag in entry.get('tags', [])],
                        'word_count': len(content.split())
                    }
                })
        
        logger.info(f"RSS parsing : {len(items)} items extraits de {source_key}")
        return items
    
    except Exception as e:
        logger.error(f"Erreur lors du parsing RSS de {source_key}: {e}")
        return []


def _parse_html_content(content_text: str, source_key: str, source_type: str, source_meta: Dict[str, Any], ingested_at: str) -> List[Dict[str, Any]]:
    """
    Parse une page HTML pour extraire les articles.
    
    Args:
        content_text: Contenu HTML brut
        source_key: Identifiant de la source
        source_type: Type de source
        source_meta: Métadonnées de la source
        ingested_at: Timestamp d'ingestion
    
    Returns:
        Liste d'items parsés depuis la page HTML
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.error("BeautifulSoup non installé, impossible de parser HTML")
        return []
    
    try:
        soup = BeautifulSoup(content_text, 'html.parser')
        items = []
        
        # Chercher des patterns courants de news
        # Pattern 1: balises <article>
        articles = soup.find_all('article')
        for article in articles[:20]:  # Limiter à 20 items max
            item = _extract_item_from_element(article, source_key, source_type, source_meta, ingested_at)
            if item:
                items.append(item)
        
        # Pattern 2: si pas d'articles, chercher des divs avec class contenant 'news', 'post', 'item'
        if not items:
            news_divs = soup.find_all('div', class_=lambda x: x and any(k in x.lower() for k in ['news', 'post', 'item', 'press']))
            for div in news_divs[:20]:
                item = _extract_item_from_element(div, source_key, source_type, source_meta, ingested_at)
                if item:
                    items.append(item)
        
        logger.info(f"HTML parsing : {len(items)} items extraits de {source_key}")
        return items
    
    except Exception as e:
        logger.error(f"Erreur lors du parsing HTML de {source_key}: {e}")
        return []


def _parse_api_content(content_text: str, source_key: str, source_type: str, ingested_at: str) -> List[Dict[str, Any]]:
    """
    Parse une réponse API JSON en items individuels.
    
    Args:
        content_text: Contenu API brut (JSON)
        source_key: Identifiant de la source
        source_type: Type de source
        ingested_at: Timestamp d'ingestion
    
    Returns:
        Liste d'items parsés depuis la réponse API
    """
    try:
        import json
        data = json.loads(content_text)
        
        # Structure générique pour APIs - à adapter selon les besoins
        items = []
        if isinstance(data, dict) and 'items' in data:
            for item_data in data['items'][:20]:  # Limiter à 20 items
                title = item_data.get('title', '')
                content = item_data.get('content', item_data.get('description', ''))
                url = item_data.get('url', item_data.get('link', ''))
                
                if title and content and url:
                    published_at = item_data.get('published_at', datetime.now().strftime('%Y-%m-%d'))
                    item_id = generate_item_id(source_key, published_at, title)
                    content_hash = calculate_content_hash(content)
                    language = detect_language(content)
                    
                    items.append({
                        'item_id': item_id,
                        'source_key': source_key,
                        'source_type': source_type,
                        'title': title,
                        'content': content,
                        'url': url,
                        'published_at': published_at,
                        'ingested_at': ingested_at,
                        'language': language,
                        'content_hash': content_hash,
                        'metadata': {
                            'author': item_data.get('author', ''),
                            'tags': item_data.get('tags', []),
                            'word_count': len(content.split())
                        }
                    })
        
        logger.info(f"API parsing : {len(items)} items extraits de {source_key}")
        return items
    
    except Exception as e:
        logger.error(f"Erreur lors du parsing API de {source_key}: {e}")
        return []


def _extract_item_from_element(element, source_key: str, source_type: str, source_meta: Dict[str, Any], ingested_at: str) -> Optional[Dict[str, Any]]:
    """
    Extrait un item depuis un élément HTML (article, div, etc.).
    
    Args:
        element: Élément BeautifulSoup
        source_key: Identifiant de la source
        source_type: Type de source
        source_meta: Métadonnées de la source
        ingested_at: Timestamp d'ingestion
    
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
        
        # Si URL relative, essayer de la compléter
        if url.startswith('/'):
            homepage_url = source_meta.get('homepage_url', '')
            if homepage_url:
                from urllib.parse import urljoin
                url = urljoin(homepage_url, url)
            else:
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
        content = ''
        desc = element.find(['p', 'div'], class_=lambda x: x and 'desc' in x.lower() if x else False)
        if desc:
            content = desc.get_text(strip=True)
        else:
            # Fallback : prendre tout le texte de l'élément
            content = element.get_text(strip=True)[:500]  # Limiter à 500 caractères
        
        if not content:
            return None
        
        # Date : essayer d'extraire depuis l'élément ou utiliser date actuelle
        published_at = _extract_date_from_html_element(element)
        if not published_at:
            published_at = datetime.now().strftime('%Y-%m-%d')
        
        item_id = generate_item_id(source_key, published_at, title)
        content_hash = calculate_content_hash(content)
        language = detect_language(content)
        
        return {
            'item_id': item_id,
            'source_key': source_key,
            'source_type': source_type,
            'title': title,
            'content': content,
            'url': url,
            'published_at': published_at,
            'ingested_at': ingested_at,
            'language': language,
            'content_hash': content_hash,
            'metadata': {
                'author': '',
                'tags': [],
                'word_count': len(content.split())
            }
        }
    
    except Exception as e:
        logger.debug(f"Impossible d'extraire item depuis élément: {e}")
        return None


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
        
        # Fallback : essayer de parser les champs texte
        date_fields = ['published', 'updated', 'pubDate']
        for field in date_fields:
            if hasattr(entry, field) and entry[field]:
                parsed_date = _parse_date_string(entry[field])
                if parsed_date:
                    return parsed_date
    
    except Exception as e:
        logger.debug(f"Impossible d'extraire la date de publication: {e}")
    
    # Par défaut : date actuelle
    return datetime.now().strftime('%Y-%m-%d')


def _parse_date_string(date_str: str) -> Optional[str]:
    """
    Parse une chaîne de date dans différents formats.
    
    Args:
        date_str: Chaîne de date à parser
    
    Returns:
        Date au format YYYY-MM-DD ou None si parsing impossible
    """
    if not date_str:
        return None
    
    # Formats de dates courants
    date_formats = [
        '%Y-%m-%d',  # ISO 8601
        '%Y-%m-%dT%H:%M:%S',  # ISO 8601 avec heure
        '%Y-%m-%dT%H:%M:%SZ',  # ISO 8601 UTC
        '%a, %d %b %Y %H:%M:%S %Z',  # RFC 2822
        '%a, %d %b %Y %H:%M:%S %z',  # RFC 2822 avec timezone
        '%d %b %Y',  # 15 Dec 2025
        '%B %d, %Y',  # December 15, 2025
        '%d/%m/%Y',  # 15/12/2025
        '%m/%d/%Y',  # 12/15/2025
    ]
    
    # Nettoyer la chaîne
    date_str = date_str.strip()
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    # Fallback : essayer de parser avec des expressions régulières
    import re
    
    # Pattern pour YYYY-MM-DD
    iso_pattern = r'(\d{4})-(\d{1,2})-(\d{1,2})'
    match = re.search(iso_pattern, date_str)
    if match:
        year, month, day = match.groups()
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    logger.debug(f"Impossible de parser la date: {date_str}")
    return None


def _clean_html_content(content: str) -> str:
    """
    Nettoie le contenu HTML en supprimant les balises.
    
    Args:
        content: Contenu HTML brut
    
    Returns:
        Contenu textuel nettoyé
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text(strip=True)
    except ImportError:
        # Fallback simple sans BeautifulSoup
        import re
        clean = re.sub('<[^<]+?>', '', content)
        return clean.strip()
    except Exception:
        return content.strip()


def generate_item_id(source_key: str, published_at: str, title: str) -> str:
    """
    Génère un identifiant unique pour un item.
    
    Format : {source_key}_{YYYYMMDD}_{hash_court}
    
    Args:
        source_key: Identifiant de la source
        published_at: Date de publication (YYYY-MM-DD)
        title: Titre de l'item (pour générer le hash)
    
    Returns:
        Identifiant unique de l'item
    """
    date_part = published_at.replace('-', '')
    title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:6]
    return f"{source_key}_{date_part}_{title_hash}"


def calculate_content_hash(content: str) -> str:
    """
    Calcule le hash SHA256 du contenu pour la déduplication.
    
    Args:
        content: Contenu textuel de l'item
    
    Returns:
        Hash SHA256 au format "sha256:..."
    """
    if not content:
        return "sha256:empty"
    
    # Normaliser le contenu (supprimer espaces en trop, convertir en minuscules)
    normalized_content = ' '.join(content.strip().lower().split())
    
    # Calculer le hash SHA256
    hash_object = hashlib.sha256(normalized_content.encode('utf-8'))
    hash_hex = hash_object.hexdigest()
    
    return f"sha256:{hash_hex}"


def _extract_date_from_html_element(element) -> Optional[str]:
    """
    Extrait une date depuis un élément HTML.
    
    Args:
        element: Élément BeautifulSoup
    
    Returns:
        Date au format YYYY-MM-DD ou None si non trouvée
    """
    try:
        # Chercher des attributs de date
        date_attrs = ['datetime', 'data-date', 'data-published']
        for attr in date_attrs:
            if element.has_attr(attr):
                date_str = element[attr]
                parsed_date = _parse_date_string(date_str)
                if parsed_date:
                    return parsed_date
        
        # Chercher des éléments time
        time_elem = element.find('time')
        if time_elem:
            if time_elem.has_attr('datetime'):
                parsed_date = _parse_date_string(time_elem['datetime'])
                if parsed_date:
                    return parsed_date
            # Fallback sur le texte de l'élément time
            time_text = time_elem.get_text(strip=True)
            parsed_date = _parse_date_string(time_text)
            if parsed_date:
                return parsed_date
        
        # Chercher des classes ou IDs contenant 'date'
        date_elems = element.find_all(attrs={'class': lambda x: x and 'date' in ' '.join(x).lower() if x else False})
        for date_elem in date_elems:
            date_text = date_elem.get_text(strip=True)
            parsed_date = _parse_date_string(date_text)
            if parsed_date:
                return parsed_date
    
    except Exception as e:
        logger.debug(f"Erreur lors de l'extraction de date HTML: {e}")
    
    return None


def detect_language(text: str) -> str:
    """
    Détecte la langue du contenu textuel.
    
    Args:
        text: Contenu textuel à analyser
    
    Returns:
        Code langue ISO 639-1 (ex: "en", "fr")
    """
    # Détection basique par mots-clés courants
    text_lower = text.lower()
    
    # Compter les mots indicateurs par langue
    en_indicators = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with']
    fr_indicators = ['le', 'la', 'et', 'est', 'dans', 'de', 'un', 'une', 'que', 'avec']
    
    en_count = sum(1 for word in en_indicators if word in text_lower)
    fr_count = sum(1 for word in fr_indicators if word in text_lower)
    
    if fr_count > en_count:
        return 'fr'
    else:
        return 'en'  # Défaut anglais