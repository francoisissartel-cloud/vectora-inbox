"""
Configuration Loader pour Vectora Inbox V2.

Ce module gère le chargement et la résolution des configurations depuis S3 :
- Configuration client (client_config/{client_id}.yaml)
- Catalogues canonical (sources, profils d'ingestion)
- Résolution des bouquets de sources en sources individuelles

Responsabilités :
- Charger les fichiers YAML depuis S3
- Résoudre les bouquets en liste de sources
- Calculer la fenêtre temporelle selon la hiérarchie de priorité
- Valider la cohérence des configurations
"""

from typing import Any, Dict, List, Optional
import logging
from . import s3_io

logger = logging.getLogger(__name__)


def load_client_config(client_id: str, config_bucket: str) -> Dict[str, Any]:
    """
    Charge la configuration d'un client depuis S3.
    
    Args:
        client_id: Identifiant du client (ex: "lai_weekly_v3")
        config_bucket: Nom du bucket de configuration S3
    
    Returns:
        Dict contenant la configuration client complète
    
    Raises:
        Exception: Si le fichier de config n'existe pas ou est invalide
    """
    key = f"clients/{client_id}.yaml"
    logger.info(f"Chargement de la configuration client : {client_id}")
    
    config = s3_io.read_yaml_from_s3(config_bucket, key)
    logger.info(f"Configuration client chargée : {config.get('client_profile', {}).get('name', client_id)}")
    
    return config


def load_source_catalog(config_bucket: str) -> Dict[str, Any]:
    """
    Charge le catalogue des sources depuis S3.
    
    Args:
        config_bucket: Nom du bucket de configuration S3
    
    Returns:
        Dict contenant sources et bouquets du catalogue canonical
    
    Raises:
        Exception: Si le catalogue n'existe pas ou est invalide
    """
    key = "canonical/sources/source_catalog.yaml"
    logger.info("Chargement du catalogue des sources")
    
    catalog = s3_io.read_yaml_from_s3(config_bucket, key)
    
    num_sources = len(catalog.get('sources', []))
    num_bouquets = len(catalog.get('bouquets', []))
    logger.info(f"Catalogue chargé : {num_sources} sources, {num_bouquets} bouquets")
    
    return catalog


def load_ingestion_profiles(config_bucket: str) -> Dict[str, Any]:
    """
    Charge les profils d'ingestion depuis S3.
    
    Args:
        config_bucket: Nom du bucket de configuration S3
    
    Returns:
        Dict contenant les profils d'ingestion canonical
    
    Raises:
        Exception: Si les profils n'existent pas ou sont invalides
    """
    key = "canonical/ingestion/ingestion_profiles.yaml"
    logger.info("Chargement des profils d'ingestion")
    
    profiles = s3_io.read_yaml_from_s3(config_bucket, key)
    logger.info("Profils d'ingestion chargés")
    
    return profiles


def resolve_sources_for_client(
    client_config: Dict[str, Any],
    source_catalog: Dict[str, Any],
    sources_filter: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Résout les sources à traiter pour un client.
    
    Développe les bouquets en sources individuelles et applique les filtres.
    
    Args:
        client_config: Configuration du client
        source_catalog: Catalogue des sources canonical
        sources_filter: Liste optionnelle de source_key à filtrer
    
    Returns:
        Liste des sources à traiter avec leurs métadonnées complètes
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
    
    # Étape 3 : Appliquer le filtre sources si fourni
    if sources_filter:
        source_keys = source_keys.intersection(set(sources_filter))
        logger.info(f"Filtrage sur sources spécifiques : {len(source_keys)} sources conservées")
    
    logger.info(f"Total de sources uniques après résolution : {len(source_keys)}")
    
    # Étape 4 : Récupérer les métadonnées pour chaque source
    enabled_sources = []
    disabled_count = 0
    
    for source_key in source_keys:
        source_meta = _find_source(source_catalog, source_key)
        if source_meta:
            # Filtrer sur enabled=true
            enabled = source_meta.get('enabled', False)
            ingestion_mode = source_meta.get('ingestion_mode', 'none')
            
            if not enabled:
                logger.warning(f"Source '{source_key}' est désactivée (enabled=false), ignorée")
                disabled_count += 1
            elif ingestion_mode == 'none':
                logger.warning(f"Source '{source_key}' a ingestion_mode='none', ignorée")
                disabled_count += 1
            else:
                enabled_sources.append(source_meta)
        else:
            logger.warning(f"Source '{source_key}' introuvable dans le catalogue")
    
    logger.info(f"Filtrage sur enabled=true : {len(enabled_sources)} sources activées, {disabled_count} sources ignorées")
    
    return enabled_sources


def resolve_period_days(
    period_days_event: Optional[int],
    client_config: Dict[str, Any],
    default: int = 7
) -> int:
    """
    Résout la valeur de period_days selon la hiérarchie de priorité.
    
    Priorité : event > client_config > défaut
    
    Args:
        period_days_event: Valeur fournie dans l'event Lambda
        client_config: Configuration du client
        default: Valeur par défaut si aucune autre n'est définie
    
    Returns:
        Nombre de jours à utiliser pour la fenêtre temporelle
    """
    # Hiérarchie de priorité
    if period_days_event is not None:
        logger.info(f"Utilisation period_days de l'event : {period_days_event}")
        return period_days_event
    
    client_period_days = client_config.get('pipeline', {}).get('default_period_days')
    if client_period_days is not None:
        logger.info(f"Utilisation period_days de la config client : {client_period_days}")
        return client_period_days
    
    logger.info(f"Utilisation period_days par défaut : {default}")
    return default


def _find_bouquet(source_catalog: Dict[str, Any], bouquet_id: str) -> Optional[Dict[str, Any]]:
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


def _find_source(source_catalog: Dict[str, Any], source_key: str) -> Optional[Dict[str, Any]]:
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