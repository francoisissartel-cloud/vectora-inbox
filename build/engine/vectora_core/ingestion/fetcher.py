"""
Module de récupération des contenus bruts depuis les sources externes.

Ce module effectue les appels HTTP vers les sources (RSS, APIs) et retourne
le contenu brut pour parsing ultérieur.

Pour le MVP, on se concentre sur les flux RSS/Atom (sources corporate et presse).
"""

import logging
from typing import Optional

import requests
import feedparser

logger = logging.getLogger(__name__)

# Configuration des timeouts et retry
REQUEST_TIMEOUT = 30  # secondes
MAX_RETRIES = 2


def fetch_source(source_meta: dict) -> Optional[str]:
    """
    Récupère le contenu brut d'une source externe.
    
    Supporte actuellement :
    - Flux RSS/Atom (détection automatique via feedparser)
    - Pages HTML simples (pour extraction future)
    
    Args:
        source_meta: Métadonnées de la source contenant :
            - source_key: identifiant unique
            - source_type: type de source
            - url: URL à interroger
    
    Returns:
        Contenu brut (XML/HTML) ou None en cas d'erreur
    """
    source_key = source_meta.get('source_key')
    url = source_meta.get('url')
    
    if not url or url == "":
        logger.warning(f"Source {source_key} : URL vide, skip")
        return None
    
    logger.info(f"Récupération de {source_key} depuis {url}")
    
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={'User-Agent': 'Vectora-Inbox/1.0'}
        )
        
        if response.status_code != 200:
            logger.warning(f"Source {source_key} : HTTP {response.status_code}")
            return None
        
        content = response.text
        logger.info(f"Source {source_key} : {len(content)} caractères récupérés")
        
        return content
    
    except requests.exceptions.Timeout:
        logger.error(f"Source {source_key} : timeout après {REQUEST_TIMEOUT}s")
        return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Source {source_key} : erreur HTTP - {e}")
        return None
    
    except Exception as e:
        logger.error(f"Source {source_key} : erreur inattendue - {e}")
        return None
