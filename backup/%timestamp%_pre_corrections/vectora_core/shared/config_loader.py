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


def list_client_configs(config_bucket: str) -> List[str]:
    """
    Liste tous les client_config disponibles dans S3.
    
    Args:
        config_bucket: Nom du bucket de configuration S3
    
    Returns:
        Liste des client_id disponibles
    """
    logger.info("Scan des client_config disponibles dans S3")
    
    objects = s3_io.list_objects_with_prefix(config_bucket, "clients/")
    client_ids = []
    
    for obj_key in objects:
        if obj_key.endswith('.yaml'):
            client_id = obj_key.replace('clients/', '').replace('.yaml', '')
            client_ids.append(client_id)
    
    logger.info(f"Client configs trouvés : {len(client_ids)} ({client_ids})")
    return client_ids


def load_all_client_configs(config_bucket: str) -> Dict[str, Dict[str, Any]]:
    """
    Charge toutes les configurations client depuis S3.
    
    Args:
        config_bucket: Nom du bucket de configuration S3
    
    Returns:
        Dict {client_id: config} pour tous les clients
    """
    logger.info("Chargement de toutes les configurations client")
    
    client_ids = list_client_configs(config_bucket)
    all_configs = {}
    
    for client_id in client_ids:
        try:
            config = load_client_config(client_id, config_bucket)
            all_configs[client_id] = config
        except Exception as e:
            logger.warning(f"Impossible de charger la config pour {client_id} : {e}")
    
    logger.info(f"Configurations chargées : {len(all_configs)}/{len(client_ids)}")
    return all_configs


def filter_active_clients(client_configs: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Filtre les clients ayant active: true dans leur configuration.
    
    Args:
        client_configs: Dict {client_id: config} de toutes les configs
    
    Returns:
        Liste des client_id ayant active: true
    """
    logger.info("Filtrage des clients actifs")
    
    active_clients = []
    
    for client_id, config in client_configs.items():
        client_profile = config.get('client_profile', {})
        is_active = client_profile.get('active', False)
        
        if is_active:
            active_clients.append(client_id)
            logger.info(f"Client actif trouvé : {client_id}")
        else:
            logger.debug(f"Client inactif ignoré : {client_id}")
    
    logger.info(f"Clients actifs : {len(active_clients)}/{len(client_configs)}")
    return active_clients


def load_canonical_scopes(config_bucket: str) -> Dict[str, Any]:
    """
    Charge tous les scopes canonical depuis S3.
    Aplatit automatiquement les scopes complexes (ex: lai_keywords).
    
    Args:
        config_bucket: Nom du bucket de configuration S3
    
    Returns:
        Dict contenant tous les scopes par catégorie
    """
    logger.info("Chargement des scopes canonical")
    
    all_scopes = {}
    
    # Chargement des différents types de scopes
    scope_files = {
        "companies": "canonical/scopes/company_scopes.yaml",
        "molecules": "canonical/scopes/molecule_scopes.yaml", 
        "technologies": "canonical/scopes/technology_scopes.yaml",
        "trademarks": "canonical/scopes/trademark_scopes.yaml",
        "exclusions": "canonical/scopes/exclusion_scopes.yaml"
    }
    
    for scope_type, file_path in scope_files.items():
        try:
            scope_data = s3_io.read_yaml_from_s3(config_bucket, file_path)
            
            # Aplatissement des scopes complexes
            flattened_scopes = {}
            for scope_name, scope_content in scope_data.items():
                if isinstance(scope_content, dict) and not scope_name.startswith('_'):
                    # Scope complexe : aplatir toutes les sous-catégories
                    flattened_terms = []
                    for category, terms in scope_content.items():
                        if isinstance(terms, list) and not category.startswith('_'):
                            flattened_terms.extend(terms)
                    flattened_scopes[scope_name] = flattened_terms
                    logger.info(f"Scope complexe aplati : {scope_name} ({len(flattened_terms)} termes)")
                else:
                    # Scope simple : conserver tel quel
                    flattened_scopes[scope_name] = scope_content
            
            all_scopes.update(flattened_scopes)
            logger.info(f"Scopes {scope_type} chargés : {len(flattened_scopes)} scopes")
        except Exception as e:
            logger.warning(f"Impossible de charger {file_path}: {str(e)}")
    
    logger.info(f"Total scopes chargés : {len(all_scopes)}")
    return all_scopes


def load_canonical_prompts(config_bucket: str) -> Dict[str, Any]:
    """
    Charge les prompts canonical avec validation depuis S3.
    
    Args:
        config_bucket: Nom du bucket de configuration S3
    
    Returns:
        Dict contenant les prompts canonical
    """
    logger.info("Chargement des prompts canonical")
    
    try:
        prompts = s3_io.read_yaml_from_s3(config_bucket, "canonical/prompts/global_prompts.yaml")
        
        # Validation présence prompts anti-hallucinations
        if 'normalization' in prompts and 'lai_default' in prompts['normalization']:
            user_template = prompts['normalization']['lai_default'].get('user_template', '')
            if 'CRITICAL' in user_template and 'FORBIDDEN' in user_template:
                logger.info("✅ Anti-hallucination prompts loaded successfully")
            else:
                logger.warning("⚠️ Anti-hallucination keywords not found in prompts")
        else:
            logger.warning("⚠️ Normalization prompts structure incomplete")
        
        logger.info("Prompts canonical chargés avec succès")
        return prompts
    except Exception as e:
        logger.error(f"Impossible de charger les prompts canonical: {str(e)}")
        return {}