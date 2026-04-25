"""
Source Fetcher pour Vectora Inbox V2.

Ce module gère la récupération des contenus bruts depuis les sources externes :
- Flux RSS (parsing XML)
- Pages HTML (scraping avec extraction de contenu)
- APIs REST (requêtes HTTP avec authentification)

Responsabilités :
- Requêtes HTTP avec gestion des timeouts et retry
- Parsing des flux RSS en items structurés
- Extraction de contenu depuis les pages HTML
- Respect des limites de débit (rate limiting)
- Gestion des erreurs réseau et des codes de statut HTTP
"""

from typing import Any, Dict, List, Optional
import logging
import requests
import time
from .format_detector import UniversalFormatDetector

logger = logging.getLogger(__name__)

# Configuration des timeouts et retry
DEFAULT_TIMEOUT = 30  # secondes
MAX_RETRIES = 3  # Augmenté de 2 à 3
RETRY_BACKOFF_BASE = 2  # Backoff exponentiel: 2^attempt secondes

# Initialiser le détecteur de format
_format_detector = UniversalFormatDetector()


def fetch_source_content(source_meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Récupère le contenu brut d'une source selon son type.
    
    Args:
        source_meta: Métadonnées de la source contenant :
            - source_key: Identifiant unique de la source
            - ingestion_mode: "rss", "html", ou "api"
            - rss_url: URL du flux RSS (si mode rss)
            - html_url: URL de la page HTML (si mode html)
            - api_url: URL de l'API (si mode api)
            - ingestion_profile: Profil d'ingestion à appliquer
    
    Returns:
        Dict contenant le contenu brut récupéré :
            - source_key: Identifiant de la source
            - source_type: Type de source (rss/html/api)
            - url: URL utilisée pour la récupération
            - fetched_at: Timestamp de récupération (ISO8601)
            - raw_content: Contenu brut récupéré
            - http_status: Code de statut HTTP
            - content_type: Type MIME du contenu
            - error: Message d'erreur si échec
        
        None si la récupération échoue complètement
    
    Raises:
        Exception: En cas d'erreur de configuration ou de réseau critique
    """
    source_key = source_meta.get('source_key')
    ingestion_mode = source_meta.get('ingestion_mode', 'rss')
    
    logger.info(f"Récupération du contenu pour la source : {source_key}")
    
    # Déterminer l'URL à utiliser selon le mode
    url = None
    if ingestion_mode == 'rss':
        url = source_meta.get('rss_url') or source_meta.get('homepage_url')
    elif ingestion_mode == 'html':
        url = source_meta.get('html_url') or source_meta.get('homepage_url')
    elif ingestion_mode == 'api':
        url = source_meta.get('api_url')
    else:
        logger.warning(f"Source {source_key} : ingestion_mode='{ingestion_mode}' non supporté")
        return None
    
    if not url or url == "":
        logger.warning(f"Source {source_key} : URL vide pour mode '{ingestion_mode}', skip")
        return None
    
    logger.info(f"Récupération de {source_key} (mode: {ingestion_mode}) depuis {url}")
    
    # Support pagination pour HTML (3 pages par défaut)
    if ingestion_mode == 'html':
        max_pages = 3
        logger.info(f"{source_key}: Pagination activée, max_pages={max_pages}")
        return _fetch_html_with_pagination(url, source_key, source_meta, max_pages)
    
    # Appliquer rate limiting si nécessaire
    apply_rate_limiting(source_meta)
    
    # Timeout configurable par source
    timeout = source_meta.get('timeout_seconds', DEFAULT_TIMEOUT)
    
    # Retry avec backoff exponentiel
    response = _fetch_with_retry(url, timeout, source_key)
    
    try:
        if not response:
            logger.error(f"Source {source_key} : échec après {MAX_RETRIES} tentatives")
            return {
                'source_key': source_key,
                'source_type': source_meta.get('source_type', 'unknown'),
                'url': url,
                'fetched_at': _get_current_timestamp(),
                'raw_content': '',
                'http_status': 0,
                'content_type': '',
                'error': f'Échec après {MAX_RETRIES} tentatives'
            }
        
        if response.status_code != 200:
            logger.warning(f"Source {source_key} : HTTP {response.status_code}")
            return {
                'source_key': source_key,
                'source_type': source_meta.get('source_type', 'unknown'),
                'url': url,
                'fetched_at': _get_current_timestamp(),
                'raw_content': '',
                'http_status': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'error': f'HTTP {response.status_code}'
            }
        
        content = response.text
        logger.info(f"Source {source_key} : {len(content)} caractères récupérés")
        
        # Détecter le format automatiquement
        detected_format = _format_detector.detect(
            url, 
            response.content, 
            response.headers.get('content-type', '')
        )
        logger.info(f"Source {source_key} : format détecté = {detected_format}")
        
        return {
            'source_key': source_key,
            'source_type': source_meta.get('source_type', 'unknown'),
            'url': url,
            'fetched_at': _get_current_timestamp(),
            'raw_content': content,
            'http_status': response.status_code,
            'content_type': response.headers.get('content-type', ''),
            'detected_format': detected_format,
            'error': None
        }
    
    except Exception as e:
        logger.error(f"Source {source_key} : erreur inattendue - {e}")
        return {
            'source_key': source_key,
            'source_type': source_meta.get('source_type', 'unknown'),
            'url': url,
            'fetched_at': _get_current_timestamp(),
            'raw_content': '',
            'http_status': 0,
            'content_type': '',
            'error': str(e)
        }


def apply_rate_limiting(source_meta: Dict[str, Any]) -> None:
    """
    Applique les limites de débit selon le profil d'ingestion.
    
    Args:
        source_meta: Métadonnées de la source avec profil d'ingestion
    """
    ingestion_profile = source_meta.get('ingestion_profile', 'default_broad')
    
    # Délais par profil (en secondes)
    profile_delays = {
        'corporate_pure_player_broad': 1.0,
        'press_technology_focused': 2.0,
        'default_broad': 0.5
    }
    
    delay = profile_delays.get(ingestion_profile, 0.5)
    if delay > 0:
        logger.debug(f"Application du rate limiting : {delay}s pour profil {ingestion_profile}")
        time.sleep(delay)


def _fetch_with_retry(url: str, timeout: int, source_key: str) -> Optional[requests.Response]:
    """
    Récupère une URL avec retry et backoff exponentiel.
    
    Args:
        url: URL à récupérer
        timeout: Timeout en secondes
        source_key: Identifiant de la source (pour logs)
    
    Returns:
        Response si succès, None si échec après tous les retries
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            
            # Succès
            if response.status_code == 200:
                if attempt > 0:
                    logger.info(f"{source_key}: Succès après {attempt + 1} tentatives")
                return response
            
            # Erreur serveur (5xx) → retry
            elif response.status_code >= 500:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(f"{source_key}: HTTP {response.status_code}, retry {attempt + 1}/{MAX_RETRIES} dans {wait}s")
                    time.sleep(wait)
                else:
                    logger.error(f"{source_key}: HTTP {response.status_code} après {MAX_RETRIES} tentatives")
                    return response
            
            # Erreur client (4xx) → pas de retry
            else:
                logger.warning(f"{source_key}: HTTP {response.status_code}, pas de retry")
                return response
        
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(f"{source_key}: Timeout ({timeout}s), retry {attempt + 1}/{MAX_RETRIES} dans {wait}s")
                time.sleep(wait)
            else:
                logger.error(f"{source_key}: Timeout après {MAX_RETRIES} tentatives")
                return None
        
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(f"{source_key}: Erreur réseau ({e}), retry {attempt + 1}/{MAX_RETRIES} dans {wait}s")
                time.sleep(wait)
            else:
                logger.error(f"{source_key}: Erreur réseau après {MAX_RETRIES} tentatives - {e}")
                return None
    
    return None


def _get_current_timestamp() -> str:
    """Retourne le timestamp actuel au format ISO8601."""
    from datetime import datetime
    return datetime.now().isoformat()


def _fetch_html_with_pagination(base_url: str, source_key: str, source_meta: Dict[str, Any], max_pages: int) -> Optional[Dict[str, Any]]:
    """Récupère plusieurs pages HTML et agrège le contenu."""
    logger.info(f"{source_key}: Pagination activée, max_pages={max_pages}")
    
    all_content = []
    
    for page in range(1, max_pages + 1):
        # Page 1: utiliser l'URL de base sans paramètre page
        if page == 1:
            page_url = base_url
        elif '?' in base_url:
            page_url = f"{base_url}&page={page}"
        else:
            page_url = f"{base_url}?page={page}"
        
        logger.info(f"{source_key}: Récupération page {page}/{max_pages}")
        
        apply_rate_limiting(source_meta)
        
        timeout = source_meta.get('timeout_seconds', DEFAULT_TIMEOUT)
        response = _fetch_with_retry(page_url, timeout, source_key)
        
        try:
            if not response:
                logger.error(f"{source_key}: Page {page} échec après retries, arrêt pagination")
                break
            
            if response.status_code == 200:
                all_content.append(response.text)
                logger.info(f"{source_key}: Page {page} OK - {len(response.text)} chars")
            else:
                logger.warning(f"{source_key}: Page {page} HTTP {response.status_code}, arrêt pagination")
                break
        
        except Exception as e:
            logger.error(f"{source_key}: Erreur page {page} - {e}")
            break
    
    if not all_content:
        return None
    
    combined_content = '\n\n<!-- PAGE_SEPARATOR -->\n\n'.join(all_content)
    
    return {
        'source_key': source_key,
        'source_type': source_meta.get('source_type', 'unknown'),
        'url': base_url,
        'fetched_at': _get_current_timestamp(),
        'raw_content': combined_content,
        'http_status': 200,
        'content_type': 'text/html',
        'error': None,
        'pages_fetched': len(all_content)
    }