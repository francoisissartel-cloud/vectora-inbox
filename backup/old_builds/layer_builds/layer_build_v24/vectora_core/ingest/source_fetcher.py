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

logger = logging.getLogger(__name__)

# Configuration des timeouts et retry
REQUEST_TIMEOUT = 30  # secondes
MAX_RETRIES = 2


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
    
    # Appliquer rate limiting si nécessaire
    apply_rate_limiting(source_meta)
    
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={'User-Agent': 'Vectora-Inbox/2.0'}
        )
        
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
        
        return {
            'source_key': source_key,
            'source_type': source_meta.get('source_type', 'unknown'),
            'url': url,
            'fetched_at': _get_current_timestamp(),
            'raw_content': content,
            'http_status': response.status_code,
            'content_type': response.headers.get('content-type', ''),
            'error': None
        }
    
    except requests.exceptions.Timeout:
        logger.error(f"Source {source_key} : timeout après {REQUEST_TIMEOUT}s")
        return {
            'source_key': source_key,
            'source_type': source_meta.get('source_type', 'unknown'),
            'url': url,
            'fetched_at': _get_current_timestamp(),
            'raw_content': '',
            'http_status': 0,
            'content_type': '',
            'error': f'Timeout après {REQUEST_TIMEOUT}s'
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Source {source_key} : erreur HTTP - {e}")
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
    
    except Exception as e:
        logger.error(f"Source {source_key} : erreur inattendue - {e}")
        return None


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


def _get_current_timestamp() -> str:
    """Retourne le timestamp actuel au format ISO8601."""
    from datetime import datetime
    return datetime.now().isoformat()