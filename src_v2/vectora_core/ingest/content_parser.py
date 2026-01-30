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
            content = _clean_html_content(content)
            
            # Enrichissement selon configuration source
            content_strategy = source_meta.get('content_enrichment', 'basic')
            if content_strategy != 'basic' and url:
                try:
                    enriched_content = enrich_content_extraction(url, content, source_meta)
                    if enriched_content and len(enriched_content) > len(content):
                        content = enriched_content
                        logger.info(f"Content enriched: {len(content)} chars (strategy: {content_strategy})")
                except Exception as e:
                    logger.debug(f"Content enrichment failed: {e}")
            
            # Date de publication avec configuration source
            published_at = _extract_published_date_with_config(entry, source_meta)
            
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
            content = desc.get_text(separator=' ', strip=True)
        else:
            # Fallback : prendre tout le texte de l'élément
            content = element.get_text(separator=' ', strip=True)[:500]  # Limiter à 500 caractères
        
        if not content:
            return None
        
        # Date : utiliser fonction d'extraction avancée
        published_at = None
        
        # Créer objet compatible avec extract_real_publication_date
        pseudo_entry = {
            'content': content,
            'title': title,
            'summary': content[:200]
        }
        
        try:
            date_result = extract_real_publication_date(pseudo_entry, source_meta)
            published_at = date_result['date']
            logger.info(f"Date extracted: {published_at} (source: {date_result.get('date_source')})")
        except Exception as e:
            logger.debug(f"Advanced date extraction failed: {e}")
            # Fallback sur ancienne méthode
            published_at = _extract_date_from_html_element(element)
        
        if not published_at:
            published_at = datetime.now().strftime('%Y-%m-%d')
            logger.warning(f"Using ingestion fallback for {title[:50]}...")
        
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


def extract_real_publication_date(item_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extraction intelligente de la date de publication.
    Gère à la fois les objets feedparser ET les dicts.
    
    1. Parser les champs date RSS (pubDate, dc:date, published_parsed)
    2. Extraction regex dans le contenu HTML
    3. Fallback sur date d'ingestion avec flag
    """
    import re
    
    # Priorité 1: Champs RSS standards - published_parsed
    if hasattr(item_data, 'published_parsed') and item_data.published_parsed:
        try:
            dt = datetime(*item_data.published_parsed[:6])
            return {
                'date': dt.strftime('%Y-%m-%d'),
                'date_source': 'rss_parsed'
            }
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse published_parsed: {e}")
    
    # Priorité 1b: Champ pubDate/published string
    published_str = None
    if hasattr(item_data, 'published'):
        published_str = item_data.published
    elif isinstance(item_data, dict) and 'published' in item_data:
        published_str = item_data['published']
    
    if published_str:
        parsed_date = _parse_date_string(published_str)
        if parsed_date:
            return {
                'date': parsed_date,
                'date_source': 'rss_pubdate'
            }
    
    # Priorité 2: Extraction contenu avec patterns source
    content = ''
    if hasattr(item_data, 'content'):
        content = str(item_data.content)
    elif isinstance(item_data, dict):
        content = str(item_data.get('content', ''))
    
    if hasattr(item_data, 'title'):
        content += ' ' + str(item_data.title)
    elif isinstance(item_data, dict):
        content += ' ' + str(item_data.get('title', ''))
    
    if hasattr(item_data, 'summary'):
        content += ' ' + str(item_data.summary)
    elif isinstance(item_data, dict):
        content += ' ' + str(item_data.get('summary', ''))
    
    date_patterns = source_config.get('date_extraction_patterns', [])
    
    # Patterns par défaut si non configurés - v3 avec word boundaries
    if not date_patterns:
        date_patterns = [
            r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})\b',
            r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s*,?\s*\d{4})\b',
            r'\b(\d{2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})'
        ]
    
    # Logging détaillé pour debugging v3
    title_preview = ''
    if hasattr(item_data, 'title'):
        title_preview = str(item_data.title)[:50]
    elif isinstance(item_data, dict):
        title_preview = str(item_data.get('title', ''))[:50]
    
    logger.debug(f"Attempting date extraction for: {title_preview}")
    logger.debug(f"Content sample: {content[:100]}")
    logger.debug(f"Patterns to try: {len(date_patterns)}")
    
    for i, pattern in enumerate(date_patterns):
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            logger.debug(f"Pattern {i} matched: {matches[:3]}")
        for match in matches:
            parsed_date = _parse_date_string(match)
            if parsed_date:
                logger.info(f"Date extracted from content: {parsed_date} (pattern: {pattern[:30]}...)")
                return {
                    'date': parsed_date,
                    'date_source': 'content_extraction'
                }
    
    # Priorité 3: Fallback avec flag
    logger.warning(f"No date found, using ingestion fallback for: {title_preview}...")
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'date_source': 'ingestion_fallback'
    }


def enrich_content_extraction(url: str, basic_content: str, source_config: Dict[str, Any]) -> str:
    """
    Enrichissement du contenu selon la stratégie source
    """
    strategy = source_config.get('content_enrichment', 'basic')
    max_length = source_config.get('max_content_length', 1000)
    
    if strategy == 'full_article':
        # Extraction complète de l'article
        return extract_full_article_content(url, max_length)
    elif strategy == 'summary_enhanced':
        # Extraction résumé + premiers paragraphes
        return extract_enhanced_summary(url, basic_content, max_length)
    else:
        return basic_content


def extract_full_article_content(url: str, max_length: int = 2000) -> str:
    """
    Extraction complète du contenu d'un article depuis son URL
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return ""
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Supprimer les éléments non pertinents
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Chercher le contenu principal
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=lambda x: x and 'content' in x.lower() if x else False)
        
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)
        
        # Limiter la longueur
        words = text.split()
        if len(words) > max_length // 5:  # Approximation 5 caractères par mot
            text = ' '.join(words[:max_length // 5])
        
        return text
    
    except Exception as e:
        logger.debug(f"Erreur extraction article complet {url}: {e}")
        return ""


def extract_enhanced_summary(url: str, basic_content: str, max_length: int = 1000) -> str:
    """
    Version améliorée avec gestion PDF
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; VectoraBot/1.0)'
        })
        
        if response.status_code != 200:
            logger.warning(f"HTTP {response.status_code} for {url}")
            return basic_content
        
        content_type = response.headers.get('content-type', '').lower()
        
        # Gestion spéciale PDFs
        if 'pdf' in content_type:
            logger.info(f"PDF detected: {url}")
            return _enrich_pdf_context(basic_content, url)
        
        # Traitement HTML normal
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Stratégies multiples pour contenu corporate
        content_selectors = [
            'div.content', 'div.post-content', 'article',
            'div[class*="content"]', 'main', '.entry-content',
            'div.press-release', 'div.news-content'
        ]
        
        enhanced_content = basic_content
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                text = elements[0].get_text(separator=' ', strip=True)
                if len(text) > len(enhanced_content):
                    enhanced_content = text
                break
        
        # Limiter intelligemment (phrases complètes)
        if len(enhanced_content) > max_length:
            sentences = enhanced_content.split('.')
            truncated = ''
            for sentence in sentences:
                if len(truncated + sentence + '.') <= max_length:
                    truncated += sentence + '.'
                else:
                    break
            enhanced_content = truncated
        
        logger.info(f"Content enriched: {len(basic_content)} → {len(enhanced_content)} chars")
        return enhanced_content
        
    except Exception as e:
        logger.warning(f"Content enrichment failed for {url}: {e}")
        return basic_content


def _enrich_pdf_context(basic_content: str, pdf_url: str) -> str:
    """
    Enrichit le contenu de base avec contexte PDF
    """
    enrichments = []
    
    # Patterns spécifiques pour MedinCell
    if 'Gates-Malaria' in pdf_url or 'malaria' in pdf_url.lower():
        enrichments.append("This grant from Gates Foundation supports malaria prevention programs using long-acting injectable formulations for extended protection.")
    
    if 'MDC_' in pdf_url and any(kw in pdf_url for kw in ['PR_', 'press', 'release']):
        enrichments.append("This press release from MedinCell announces developments in long-acting injectable technologies and partnerships.")
    
    if 'NDA' in pdf_url or 'filing' in pdf_url:
        enrichments.append("This regulatory filing relates to New Drug Application submissions for long-acting injectable pharmaceutical products.")
    
    # Ajouter enrichissements au contenu de base
    if enrichments:
        return basic_content + ' ' + ' '.join(enrichments)
    
    return basic_content


def _extract_published_date_with_config(entry: Any, source_meta: Dict[str, Any]) -> str:
    """
    Extraction de date avec configuration source.
    
    Args:
        entry: Entrée feedparser
        source_meta: Configuration de la source avec patterns d'extraction
    
    Returns:
        Date au format ISO8601 (YYYY-MM-DD) ou date actuelle si non trouvée
    """
    try:
        date_result = extract_real_publication_date(entry, source_meta)
        return date_result['date']
    except Exception as e:
        logger.debug(f"Date extraction failed: {e}")
        return datetime.now().strftime('%Y-%m-%d')

def _extract_published_date(entry: Any) -> str:
    """
    Extrait la date de publication d'une entrée RSS et la formate en ISO8601.
    Version de compatibilité - utilise la nouvelle fonction avec config vide.
    
    Args:
        entry: Entrée feedparser
    
    Returns:
        Date au format ISO8601 (YYYY-MM-DD) ou date actuelle si non trouvée
    """
    try:
        # Utiliser la nouvelle fonction d'extraction améliorée
        date_result = extract_real_publication_date(entry, {})
        return date_result['date']
    
    except Exception as e:
        logger.debug(f"Impossible d'extraire la date de publication: {e}")
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
    
    # Nettoyer la chaîne
    date_str = date_str.strip()
    
    # Formats de dates étendus
    date_formats = [
        '%Y-%m-%d',                    # 2025-11-24
        '%Y-%m-%dT%H:%M:%S',          # ISO avec heure
        '%Y-%m-%dT%H:%M:%SZ',         # ISO UTC
        '%Y-%m-%dT%H:%M:%S%z',        # ISO avec timezone
        '%a, %d %b %Y %H:%M:%S %Z',   # RFC 2822
        '%a, %d %b %Y %H:%M:%S %z',   # RFC 2822 avec timezone
        '%d %B %Y',                    # 24 November 2025
        '%B %d, %Y',                   # November 24, 2025
        '%d %b %Y',                    # 24 Nov 2025
        '%b %d, %Y',                   # Nov 24, 2025
        '%d %B, %Y',                   # 27 January, 2026
        '%d/%m/%Y',                    # 24/11/2025
        '%m/%d/%Y',                    # 11/24/2025
        '%d.%m.%Y',                    # 24.11.2025
        '%Y/%m/%d',                    # 2025/11/24
    ]
    
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
    Nettoie le contenu HTML en supprimant les balises et en ajoutant des espaces.
    Version v3 avec separator=' ' pour garantir espaces entre éléments.
    
    Args:
        content: Contenu HTML brut
    
    Returns:
        Contenu textuel nettoyé
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        # Utiliser separator=' ' pour garantir des espaces entre éléments
        return soup.get_text(separator=' ', strip=True)
    except ImportError:
        # Fallback simple sans BeautifulSoup
        import re
        # Remplacer balises par espaces (pas juste supprimer)
        clean = re.sub('<[^<]+?>', ' ', content)
        # Normaliser espaces multiples
        clean = re.sub(r'\s+', ' ', clean)
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