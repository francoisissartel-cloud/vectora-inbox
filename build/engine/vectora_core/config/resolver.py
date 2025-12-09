"""
Module de résolution des sources pour Vectora Inbox.

Ce module résout la liste finale des sources à traiter pour un client donné,
en combinant :
- Les bouquets activés dans la config client
- Les sources additionnelles spécifiques au client
- Les métadonnées des sources depuis le catalogue

La résolution est générique et ne contient aucune logique spécifique à LAI.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def resolve_sources_for_client(
    client_config: Dict[str, Any],
    source_catalog: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Résout la liste finale des sources à traiter pour un client.
    
    Processus :
    1. Lire les bouquets activés dans la config client (source_bouquets_enabled)
    2. Pour chaque bouquet, récupérer la liste des source_key depuis le catalogue
    3. Ajouter les sources additionnelles (sources_extra_enabled)
    4. Dédupliquer la liste finale
    5. Pour chaque source_key, récupérer les métadonnées depuis le catalogue
    
    Args:
        client_config: Configuration client complète
        source_catalog: Catalogue de sources (sources + bouquets)
    
    Returns:
        Liste de dictionnaires, chaque dict contenant :
        - source_key: identifiant unique de la source
        - source_type: type de source (press_corporate, press_sector, etc.)
        - url: URL de la source
        - default_language: langue par défaut
        - vertical_tags: tags métier (optionnel)
    """
    logger.info("Résolution des sources pour le client")
    
    # Récupérer la config des sources du client
    source_config = client_config.get('source_config', {})
    bouquets_enabled = source_config.get('source_bouquets_enabled', [])
    sources_extra = source_config.get('sources_extra_enabled', [])
    
    logger.info(f"Bouquets activés : {bouquets_enabled}")
    logger.info(f"Sources additionnelles : {sources_extra}")
    
    # Étape 1 : Résoudre les bouquets
    source_keys = set()
    
    for bouquet_id in bouquets_enabled:
        bouquet = _find_bouquet(source_catalog, bouquet_id)
        if bouquet:
            keys = bouquet.get('source_keys', [])
            source_keys.update(keys)
            logger.info(f"Bouquet '{bouquet_id}' résolu : {len(keys)} sources")
        else:
            logger.warning(f"Bouquet '{bouquet_id}' introuvable dans le catalogue")
    
    # Étape 2 : Ajouter les sources additionnelles
    source_keys.update(sources_extra)
    
    logger.info(f"Total de sources uniques après résolution : {len(source_keys)}")
    
    # Étape 3 : Récupérer les métadonnées pour chaque source
    resolved_sources = []
    
    for source_key in source_keys:
        source_meta = _find_source(source_catalog, source_key)
        if source_meta:
            resolved_sources.append(source_meta)
        else:
            logger.warning(f"Source '{source_key}' introuvable dans le catalogue")
    
    logger.info(f"Sources résolues avec métadonnées : {len(resolved_sources)}")
    
    return resolved_sources


def _find_bouquet(source_catalog: Dict[str, Any], bouquet_id: str) -> Dict[str, Any]:
    """
    Trouve un bouquet dans le catalogue par son ID.
    
    Args:
        source_catalog: Catalogue de sources
        bouquet_id: Identifiant du bouquet à trouver
    
    Returns:
        Dictionnaire du bouquet ou None si introuvable
    """
    bouquets = source_catalog.get('bouquets', [])
    for bouquet in bouquets:
        if bouquet.get('bouquet_id') == bouquet_id:
            return bouquet
    return None


def _find_source(source_catalog: Dict[str, Any], source_key: str) -> Dict[str, Any]:
    """
    Trouve une source dans le catalogue par sa clé.
    
    Args:
        source_catalog: Catalogue de sources
        source_key: Clé de la source à trouver
    
    Returns:
        Dictionnaire de la source ou None si introuvable
    """
    sources = source_catalog.get('sources', [])
    for source in sources:
        if source.get('source_key') == source_key:
            return source
    return None
