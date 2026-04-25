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
from .date_extractor import DateExtractor
try:
    from .content_extractor import ContentExtractor
    CONTENT_EXTRACTOR_AVAILABLE = True
except ImportError:
    CONTENT_EXTRACTOR_AVAILABLE = False
    ContentExtractor = None
from .content_parser_helpers import _extract_from_links
from .title_enricher import enrich_items_titles

logger = logging.getLogger(__name__)

# Initialiser extracteurs
_date_extractor = DateExtractor()
_content_extractor = ContentExtractor()

# Cache global pour parsing_config
_parsing_config_cache = None
_html_selectors_cache = None


def initialize_parsing_config(s3_io, config_bucket: str):
    """Charge parsing_config.yaml et html_selectors.yaml depuis S3"""
    global _parsing_config_cache, _html_selectors_cache
    try:
        config = s3_io.read_yaml_from_s3(
            config_bucket, 
            'canonical/parsing/parsing_config.yaml'
        )
        _parsing_config_cache = config
        logger.info("Parsing config chargé depuis S3")
    except Exception as e:
        logger.warning(f"Échec chargement parsing_config: {e} - utilisation patterns par défaut")
        _parsing_config_cache = {}
    
    try:
        selectors = s3_io.read_yaml_from_s3(
            config_bucket,
            'canonical/parsing/html_selectors.yaml'
        )
        _html_selectors_cache = selectors
        logger.info("HTML selectors chargés depuis S3")
    except Exception as e:
        logger.warning(f"Échec chargement html_selectors: {e} - utilisation patterns génériques")
        _html_selectors_cache = {}


def _get_date_patterns(source_meta: Dict) -> List[str]:
    """Récupère les patterns de dates depuis parsing_config"""
    if not _parsing_config_cache:
        return []
    
    source_type = source_meta.get('source_type', 'default')
    source_key = source_meta.get('source_key')
    
    # Override spécifique par source_key ?
    patterns_config = _parsing_config_cache.get('date_patterns', {}).get(source_key)
    
    # Sinon, patterns par source_type
    if not patterns_config:
        patterns_config = _parsing_config_cache.get('date_patterns', {}).get(source_type, {})
    
    return patterns_config.get('patterns', [])


def _get_html_selectors(source_key: str) -> Dict[str, Any]:
    """Récupère les selectors HTML pour une source"""
    if not _html_selectors_cache:
        return {}
    
    sources = _html_selectors_cache.get('sources', {})
    return sources.get(source_key, {})



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
        return _parse_rss_content(content_text, source_key, source_type, ingested_at, source_meta)
    elif ingestion_mode == 'html':
        return _parse_html_content(content_text, source_key, source_type, source_meta, ingested_at)
    elif ingestion_mode == 'api':
        return _parse_api_content(content_text, source_key, source_type, ingested_at)
    else:
        logger.error(f"Mode d'ingestion non supporté pour le parsing : {ingestion_mode}")
        return []


def _parse_rss_content(content_text: str, source_key: str, source_type: str, ingested_at: str, source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse un flux RSS en items individuels.
    
    Args:
        content_text: Contenu RSS brut
        source_key: Identifiant de la source
        source_type: Type de source
        ingested_at: Timestamp d'ingestion
        source_meta: Configuration de la source
    
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
            from ..ingest import content_cleaner
            content = content_cleaner.clean_html_content(content)
            
            # Récupérer raw_html TOUJOURS pour extraction de date
            raw_html = None
            if url:
                try:
                    import requests
                    logger.info(f"[FETCH] Fetching HTML for date extraction: {url[:80]}")
                    response = requests.get(url, timeout=15)
                    if response.status_code == 200:
                        raw_html = response.text
                        logger.info(f"[FETCH] Got {len(raw_html)} chars HTML")
                except Exception as e:
                    logger.warning(f"[FETCH] Failed to get HTML: {e}")
            
            # Enrichissement selon configuration source
            if source_meta.get('source_type') == 'press_corporate':
                content_strategy = 'full_article'
                logger.info(f"[ENRICH] Forcing full_article for corporate source {source_key}")
            else:
                default_strategy = 'full_article' if source_meta.get('source_type') == 'press_corporate' else 'basic'
                content_strategy = source_meta.get('content_enrichment', default_strategy)
            
            enriched_content_for_date = None
            if content_strategy != 'basic' and raw_html:
                enriched_content = enrich_content_extraction(url, content, source_meta)
                if enriched_content and len(enriched_content) > len(content):
                    content = enriched_content
                    enriched_content_for_date = content
                    logger.info(f"[ENRICH] SUCCESS: {len(content)} chars")
            
            # Date de publication - utiliser contenu enrichi si disponible
            item_dict = {
                'title': title,
                'published': entry.get('published', ''),
                'summary': enriched_content_for_date or content,
                'link': url,
                'content': enriched_content_for_date or content
            }
            date_result = _date_extractor.extract(item_dict, raw_html=raw_html)
            published_at = date_result.date
            
            logger.info(f"[DATE] Extracted: {published_at} (source: {date_result.source}, confidence: {date_result.confidence})")
            
            # Date d'extraction (date d'ingéstion)
            extraction_date = datetime.now().strftime('%Y-%m-%d')
            
            # Ne garder que les items avec au moins un titre et une URL
            # Le contenu sera enrichi automatiquement si trop court
            if title and url:
                item_id = generate_item_id(source_key, published_at, title)
                content_hash = calculate_content_hash(content)
                language = detect_language(content)
                
                item = {
                    'item_id': item_id,
                    'source_key': source_key,
                    'source_type': source_type,
                    'title': title,
                    'content': content,
                    'url': url,
                    'published_at': published_at,
                    'extraction_date': extraction_date,
                    'ingested_at': ingested_at,
                    'language': language,
                    'content_hash': content_hash,
                    'metadata': {
                        'author': entry.get('author', ''),
                        'tags': [tag.get('term', '') for tag in entry.get('tags', [])],
                        'word_count': len(content.split())
                    }
                }
                
                # Ajouter métadonnées d'extraction de date
                item['date_extraction'] = {
                    'date_source': date_result.source,
                    'confidence': date_result.confidence
                }
                
                items.append(item)
        
        logger.info(f"RSS parsing : {len(items)} items extraits de {source_key}")
        return items
    
    except Exception as e:
        logger.error(f"Erreur lors du parsing RSS de {source_key}: {e}")
        return []


def _extract_items_from_containers(containers: list, source_key: str, soup, source_meta: dict) -> list:
    """
    Extrait des items depuis une liste de containers HTML.
    """
    items = []
    
    for container in containers:
        try:
            title = None
            if container.name == 'a':
                title = container.get_text(strip=True)
            
            if not title or len(title) < 10:
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    elem = container.find(tag)
                    if elem:
                        title = elem.get_text(strip=True)
                        break
            
            if not title:
                link = container.find('a', href=True)
                if link:
                    title = link.get_text(strip=True)
            
            if not title or len(title) < 10:
                continue
            
            url = None
            if container.name == 'a':
                url = container.get('href', '')
            if not url:
                link = container.find('a', href=True)
                if link:
                    url = link.get('href', '')
            
            if not url:
                continue
            
            if url.startswith('/'):
                base_url = source_meta.get('homepage_url', '')
                if base_url:
                    from urllib.parse import urljoin
                    url = urljoin(base_url, url)
            
            items.append({'title': title, 'link': url, 'content': '', 'source_key': source_key})
        
        except Exception as e:
            logger.debug(f"[{source_key}] Error extracting item: {e}")
    
    return items


def _parse_html_content(content_text: str, source_key: str, source_type: str, source_meta: Dict[str, Any], ingested_at: str) -> List[Dict[str, Any]]:
    """
    Parser adaptatif multi-stratégies avec enrichissement automatique.
    Essaie plusieurs approches pour maximiser la couverture.
    """
    try:
        from bs4 import BeautifulSoup
        import requests
        import re
    except ImportError:
        logger.error("Dépendances manquantes")
        return []
    
    try:
        soup = BeautifulSoup(content_text, 'html.parser')
        items = []
        
        # STRATÉGIE MULTI-NIVEAUX: Essayer plusieurs patterns
        logger.info(f"[{source_key}] Starting multi-strategy HTML parsing")
        
        # Liste des stratégies à essayer dans l'ordre
        strategies = [
            ('h5 press-release', lambda: [h5 for h5 in soup.find_all('h5') if h5.find('a', href=lambda x: x and '/press-release' in x) and not any(parent.name in ['nav', 'header', 'footer'] or 'menu' in str(parent.get('class', '')).lower() for parent in h5.parents)]),
            ('article', lambda: soup.find_all('article')),
            ('li.post/news', lambda: soup.find_all('li', class_=re.compile(r'post|news|item|press', re.I))),
            ('div.post/news', lambda: [d for d in soup.find_all('div', class_=re.compile(r'post|news|item|entry|press|release', re.I)) if not any(x in str(d.get('class', [])).lower() for x in ['filter', 'nav', 'menu', 'sidebar'])]),
            ('press-release links', lambda: [a for a in soup.find_all('a', href=True) if '/press-release' in a.get('href', '').lower() or '/media/press-releases/' in a.get('href', '') and len(a.get_text(strip=True)) > 20]),
            ('links', lambda: _extract_from_links(soup))
        ]
        
        items = []
        for strategy_name, strategy_func in strategies:
            containers = strategy_func()
            logger.info(f"[{source_key}] Strategy '{strategy_name}': {len(containers)} containers found")
            
            if not containers:
                continue
            
            # Essayer d'extraire des items depuis ces containers
            strategy_items = _extract_items_from_containers(containers[:50], source_key, soup, source_meta)
            
            if strategy_items:
                logger.info(f"[{source_key}] ✅ Strategy '{strategy_name}' succeeded: {len(strategy_items)} items extracted")
                items = strategy_items
                break
            else:
                logger.warning(f"[{source_key}] ⚠️ Strategy '{strategy_name}' found containers but extracted 0 items, trying next strategy")
        
        if not items:
            logger.warning(f"[{source_key}] All strategies failed, no items extracted")
            return []
        
        # Transformer items basiques en items structurés complets
        structured_items = []
        for item in items:
            try:
                title = item.get('title', '')
                url = item.get('link', '')
                
                # ENRICHIR LE CONTENU depuis l'URL
                content = ''
                if url and source_type == 'press_corporate':
                    logger.info(f"[{source_key}] Enriching content from {url[:60]}")
                    try:
                        enriched = _content_extractor.extract(url)
                        if enriched and len(enriched) > 100:
                            content = enriched
                            logger.info(f"[{source_key}] Content enriched: {len(content)} chars")
                        else:
                            logger.warning(f"[{source_key}] Enrichment failed, skipping item")
                            continue
                    except Exception as e:
                        logger.warning(f"[{source_key}] Enrichment error: {e}, skipping item")
                        continue
                
                if not content or len(content) < 100:
                    logger.warning(f"[{source_key}] Content too short ({len(content)} chars), skipping")
                    continue
                
                # Date extraction
                item_dict = {'title': title, 'content': content, 'link': url}
                date_result = _date_extractor.extract(item_dict, raw_html=None)
                published_at = date_result.date
                extraction_date = datetime.now().strftime('%Y-%m-%d')
                
                item_id = generate_item_id(source_key, published_at, title)
                content_hash = calculate_content_hash(content)
                language = detect_language(content)
                
                structured_item = {
                    'item_id': item_id,
                    'source_key': source_key,
                    'source_type': source_type,
                    'title': title,
                    'content': content,
                    'url': url,
                    'published_at': published_at,
                    'extraction_date': extraction_date,
                    'ingested_at': ingested_at,
                    'language': language,
                    'content_hash': content_hash,
                    'metadata': {'word_count': len(content.split())},
                    'date_extraction': {
                        'date_source': date_result.source,
                        'confidence': date_result.confidence
                    }
                }
                structured_items.append(structured_item)
            except Exception as e:
                logger.warning(f"[{source_key}] Failed to structure item: {e}")
        
        items = structured_items
        
        logger.info(f"[{source_key}] ✅ Parsing complete: {len(items)} items extracted")
        
        # ENRICHISSEMENT DES TITRES GÉNÉRIQUES
        items = enrich_items_titles(items)
        
        # FALLBACK: Si 0 items, essayer parser simple
        if len(items) == 0:
            logger.warning(f"[{source_key}] No items with complex parser, trying simple fallback")
            items = _parse_html_simple_fallback(content_text, source_key, source_meta, ingested_at)
            logger.info(f"[{source_key}] Simple fallback: {len(items)} items extracted")
        
        return items
    
    except Exception as e:
        logger.error(f"[{source_key}] ❌ Parsing failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
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






def extract_real_publication_date(item_data: Any, source_config: Dict[str, Any], raw_html: Optional[str] = None, enriched_content: Optional[str] = None) -> Dict[str, Any]:
    """
    Extraction intelligente de la date - utilise date_extractor unifié
    """
    item_dict = {
        'title': str(getattr(item_data, 'title', '')) if hasattr(item_data, 'title') else str(item_data.get('title', '')),
        'published': getattr(item_data, 'published', None) or (item_data.get('published') if isinstance(item_data, dict) else None),
        'summary': enriched_content or str(getattr(item_data, 'summary', '')) if hasattr(item_data, 'summary') else str(item_data.get('summary', '')),
        'link': getattr(item_data, 'link', '') if hasattr(item_data, 'link') else item_data.get('url', '')
    }
    
    result = _date_extractor.extract(item_dict, raw_html)
    return {'date': result.date, 'date_source': result.source, 'confidence': result.confidence}


def enrich_content_extraction(url: str, basic_content: str, source_config: Dict[str, Any]) -> str:
    """
    Enrichissement du contenu selon la stratégie source.
    Utilise ContentExtractor pour récupérer le contenu complet.
    """
    strategy = source_config.get('content_enrichment', 'basic')
    
    if strategy == 'full_article':
        enriched = _content_extractor.extract(url)
        return enriched if enriched and len(enriched) > len(basic_content) else basic_content
    elif strategy == 'summary_enhanced':
        enriched = _content_extractor.extract(url)
        if enriched and len(enriched) > len(basic_content):
            max_length = source_config.get('max_content_length', 1000)
            return enriched[:max_length] if len(enriched) > max_length else enriched
        return basic_content
    else:
        return basic_content















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


def _parse_html_simple_fallback(content_text: str, source_key: str, source_meta: Dict[str, Any], ingested_at: str) -> List[Dict[str, Any]]:
    """
    Parser simple en fallback : trouve les liens d'articles et va chercher le contenu complet.
    Utilisé quand le parser complexe échoue.
    """
    try:
        from bs4 import BeautifulSoup
        import requests
        import re
        from urllib.parse import urljoin
        
        soup = BeautifulSoup(content_text, 'html.parser')
        homepage_url = source_meta.get('homepage_url', '')
        items = []
        
        # Trouver liens d'articles
        article_patterns = [
            r'/press-release[s]?/\d{4}/',
            r'/news/\d{4}/',
            r'/\d{4}/\d{2}/',
        ]
        
        links = []
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            
            if any(x in href.lower() for x in ['#', 'javascript:', 'mailto:', 'tel:', '?']):
                continue
            if href.endswith(('/press-releases/', '/news/', '/media/')):
                continue
            
            if any(re.search(p, href, re.I) for p in article_patterns):
                if href.startswith('/'):
                    full_url = urljoin(homepage_url, href)
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                links.append(full_url)
        
        # Dédupliquer
        links = list(dict.fromkeys(links))[:20]
        logger.info(f"[{source_key}] Fallback found {len(links)} article links")
        
        # Extraire chaque article
        for url in links:
            try:
                response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code != 200:
                    continue
                
                article_soup = BeautifulSoup(response.text, 'html.parser')
                
                # Titre
                title = None
                for tag in ['h1', 'h2', '.title', 'title']:
                    elem = article_soup.find(tag)
                    if elem:
                        title = elem.get_text(strip=True)
                        if len(title) > 10:
                            break
                
                if not title or len(title) < 10:
                    continue
                
                # Contenu
                content = None
                for selector in ['article', '.content', '.post-content', 'main', 'body']:
                    elem = article_soup.select_one(selector)
                    if elem:
                        content = elem.get_text(separator=' ', strip=True)
                        if len(content) > 200:
                            break
                
                if not content:
                    continue
                
                content = re.sub(r'\s+', ' ', content).strip()[:3000]
                
                # Date avec date_extractor
                date = None
                time_elem = article_soup.find('time', attrs={'datetime': True})
                if time_elem:
                    date = _date_extractor._parse_date_string(time_elem.get('datetime'))
                
                if not date:
                    item_dict = {'title': title, 'content': content, 'link': url}
                    date_result = _date_extractor.extract(item_dict, raw_html=None)
                    if date_result.confidence >= 0.60:
                        date = date_result.date
                        date_source = date_result.source
                        confidence = date_result.confidence
                    else:
                        date = datetime.now().strftime('%Y-%m-%d')
                        date_source = 'simple_fallback'
                        confidence = 0.0
                else:
                    date_source = 'html_time_tag'
                    confidence = 0.95
                
                effective_date = date
                extraction_date = datetime.now().strftime('%Y-%m-%d')
                
                # Créer item
                item_id = generate_item_id(source_key, date, title)
                items.append({
                    'item_id': item_id,
                    'source_key': source_key,
                    'source_type': source_meta.get('source_type', 'press_corporate'),
                    'title': title,
                    'content': content,
                    'url': url,
                    'published_at': date,
                    'extraction_date': extraction_date,
                    'ingested_at': ingested_at,
                    'language': detect_language(content),
                    'content_hash': calculate_content_hash(content),
                    'metadata': {'word_count': len(content.split())},
                    'date_extraction': {
                        'date_source': date_source,
                        'confidence': confidence
                    }
                })
                
            except Exception as e:
                logger.debug(f"[{source_key}] Failed to extract {url}: {e}")
                continue
        
        return items
        
    except Exception as e:
        logger.error(f"[{source_key}] Simple fallback failed: {e}")
        return []