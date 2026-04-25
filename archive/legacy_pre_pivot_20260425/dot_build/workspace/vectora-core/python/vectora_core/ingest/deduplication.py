"""
Déduplication des items pour éviter les appels Bedrock redondants.
"""

import hashlib
import logging
from typing import List, Dict, Any, Set

logger = logging.getLogger(__name__)


def deduplicate_items(items: List[Dict], source_key: str, s3_io, bucket: str) -> List[Dict]:
    """
    Déduplique les items déjà vus en utilisant un hash du contenu.
    
    Args:
        items: Liste d'items parsés
        source_key: Identifiant de la source
        s3_io: Client S3
        bucket: Bucket de configuration
    
    Returns:
        Liste d'items nouveaux uniquement
    """
    if not items:
        return []
    
    # Charger l'index des items déjà vus
    cache_key = f"ingestion_cache/{source_key}_seen.json"
    try:
        seen_hashes = set(s3_io.read_json_from_s3(bucket, cache_key) or [])
        logger.info(f"{source_key}: {len(seen_hashes)} items déjà vus en cache")
    except Exception as e:
        logger.warning(f"Impossible de charger le cache: {e}")
        seen_hashes = set()
    
    new_items = []
    new_hashes = set()
    
    for item in items:
        # Hash basé sur titre + premiers 200 chars du contenu
        content_hash = hashlib.md5(
            f"{item.get('title', '')}{item.get('content', '')[:200]}".encode()
        ).hexdigest()
        
        if content_hash not in seen_hashes:
            new_items.append(item)
            new_hashes.add(content_hash)
        else:
            logger.debug(f"Item dupliqué ignoré: {item.get('title', '')[:50]}")
    
    # Sauvegarder les nouveaux hash (garder max 1000 derniers)
    if new_hashes:
        updated_hashes = list(seen_hashes.union(new_hashes))[-1000:]
        try:
            s3_io.write_json_to_s3(bucket, cache_key, updated_hashes)
            logger.info(f"{source_key}: Cache mis à jour avec {len(new_hashes)} nouveaux items")
        except Exception as e:
            logger.error(f"Impossible de sauvegarder le cache: {e}")
    
    logger.info(f"{source_key}: {len(new_items)}/{len(items)} nouveaux items (déduplication: {len(items) - len(new_items)} ignorés)")
    return new_items
