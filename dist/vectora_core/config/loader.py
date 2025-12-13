"""
Module de chargement des configurations pour Vectora Inbox.

Ce module charge les fichiers de configuration depuis S3 :
- Configuration client (clients/<client_id>.yaml)
- Scopes canonical (canonical/scopes/*.yaml)
- Catalogue de sources (canonical/sources/source_catalog.yaml)
- Règles de scoring (canonical/scoring/scoring_rules.yaml)

Toutes les fonctions retournent des dictionnaires Python prêts à l'emploi.
"""

import logging
from typing import Dict, Any

from vectora_core.storage import s3_client

logger = logging.getLogger(__name__)


def load_client_config(client_id: str, config_bucket: str) -> Dict[str, Any]:
    """
    Charge la configuration d'un client depuis S3.
    
    Le fichier est attendu à l'emplacement : clients/<client_id>.yaml
    
    Args:
        client_id: Identifiant unique du client (ex: "lai_weekly")
        config_bucket: Nom du bucket S3 de configuration
    
    Returns:
        Dictionnaire contenant la configuration client complète
    
    Raises:
        ClientError: Si le fichier n'existe pas
        yaml.YAMLError: Si le fichier n'est pas un YAML valide
    """
    key = f"clients/{client_id}.yaml"
    logger.info(f"Chargement de la configuration client : {client_id}")
    
    config = s3_client.read_yaml_from_s3(config_bucket, key)
    logger.info(f"Configuration client chargée : {config.get('client_profile', {}).get('name', client_id)}")
    
    return config


def load_canonical_scopes(config_bucket: str) -> Dict[str, Dict[str, Any]]:
    """
    Charge tous les scopes canonical depuis S3.
    
    Charge les fichiers suivants depuis canonical/scopes/ :
    - company_scopes.yaml
    - molecule_scopes.yaml
    - trademark_scopes.yaml
    - technology_scopes.yaml
    - indication_scopes.yaml
    - exclusion_scopes.yaml
    
    Args:
        config_bucket: Nom du bucket S3 de configuration
    
    Returns:
        Dictionnaire structuré par type de scope :
        {
            "companies": {...},
            "molecules": {...},
            "trademarks": {...},
            "technologies": {...},
            "indications": {...},
            "exclusions": {...}
        }
    """
    logger.info("Chargement des scopes canonical")
    
    scopes = {}
    
    # Définition des fichiers à charger
    scope_files = {
        "companies": "canonical/scopes/company_scopes.yaml",
        "molecules": "canonical/scopes/molecule_scopes.yaml",
        "trademarks": "canonical/scopes/trademark_scopes.yaml",
        "technologies": "canonical/scopes/technology_scopes.yaml",
        "indications": "canonical/scopes/indication_scopes.yaml",
        "exclusions": "canonical/scopes/exclusion_scopes.yaml"
    }
    
    for scope_type, key in scope_files.items():
        try:
            scopes[scope_type] = s3_client.read_yaml_from_s3(config_bucket, key)
            logger.info(f"Scope {scope_type} chargé : {len(scopes[scope_type])} clés")
        except Exception as e:
            logger.warning(f"Impossible de charger {scope_type} depuis {key}: {e}")
            scopes[scope_type] = {}
    
    return scopes


def load_source_catalog(config_bucket: str) -> Dict[str, Any]:
    """
    Charge le catalogue de sources depuis S3.
    
    Le fichier est attendu à l'emplacement : canonical/sources/source_catalog.yaml
    
    Args:
        config_bucket: Nom du bucket S3 de configuration
    
    Returns:
        Dictionnaire contenant :
        - "sources": liste des sources disponibles
        - "bouquets": liste des bouquets de sources
    """
    key = "canonical/sources/source_catalog.yaml"
    logger.info("Chargement du catalogue de sources")
    
    catalog = s3_client.read_yaml_from_s3(config_bucket, key)
    
    num_sources = len(catalog.get('sources', []))
    num_bouquets = len(catalog.get('bouquets', []))
    logger.info(f"Catalogue chargé : {num_sources} sources, {num_bouquets} bouquets")
    
    return catalog


def load_scoring_rules(config_bucket: str) -> Dict[str, Any]:
    """
    Charge les règles de scoring depuis S3.
    
    Le fichier est attendu à l'emplacement : canonical/scoring/scoring_rules.yaml
    
    Args:
        config_bucket: Nom du bucket S3 de configuration
    
    Returns:
        Dictionnaire contenant les règles de scoring
    """
    key = "canonical/scoring/scoring_rules.yaml"
    logger.info("Chargement des règles de scoring")
    
    rules = s3_client.read_yaml_from_s3(config_bucket, key)
    logger.info("Règles de scoring chargées")
    
    return rules


# ============================================================================
# FONCTIONS DE CHARGEMENT LOCAL (pour tests et debug)
# ============================================================================

def load_canonical_scopes_local() -> Dict[str, Dict[str, Any]]:
    """
    Charge tous les scopes canonical depuis le système de fichiers local.
    Version locale de load_canonical_scopes() pour les tests.
    """
    import yaml
    from pathlib import Path
    
    logger.info("Chargement des scopes canonical (local)")
    
    scopes = {}
    base_path = Path("canonical/scopes")
    
    # Définition des fichiers à charger
    scope_files = {
        "companies": "company_scopes.yaml",
        "molecules": "molecule_scopes.yaml",
        "trademarks": "trademark_scopes.yaml",
        "technologies": "technology_scopes.yaml",
        "indications": "indication_scopes.yaml",
        "exclusions": "exclusion_scopes.yaml"
    }
    
    for scope_type, filename in scope_files.items():
        filepath = base_path / filename
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                scopes[scope_type] = yaml.safe_load(f)
            logger.info(f"Scope {scope_type} chargé : {len(scopes[scope_type])} clés")
        except Exception as e:
            logger.warning(f"Impossible de charger {scope_type} depuis {filepath}: {e}")
            scopes[scope_type] = {}
    
    return scopes


def load_matching_rules_local() -> Dict[str, Any]:
    """
    Charge les règles de matching depuis le système de fichiers local.
    """
    import yaml
    from pathlib import Path
    
    filepath = Path("canonical/matching/domain_matching_rules.yaml")
    logger.info(f"Chargement des règles de matching (local) : {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        logger.info("Règles de matching chargées (local)")
        return rules
    except Exception as e:
        logger.error(f"Erreur chargement règles de matching: {e}")
        return {}


def load_scoring_rules_local() -> Dict[str, Any]:
    """
    Charge les règles de scoring depuis le système de fichiers local.
    """
    import yaml
    from pathlib import Path
    
    filepath = Path("canonical/scoring/scoring_rules.yaml")
    logger.info(f"Chargement des règles de scoring (local) : {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)
        logger.info("Règles de scoring chargées (local)")
        return rules
    except Exception as e:
        logger.error(f"Erreur chargement règles de scoring: {e}")
        return {}


def load_client_config_local(client_id: str) -> Dict[str, Any]:
    """
    Charge la configuration client depuis le système de fichiers local.
    """
    import yaml
    from pathlib import Path
    
    filepath = Path(f"client-config-examples/{client_id}.yaml")
    logger.info(f"Chargement de la configuration client (local) : {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuration client chargée (local) : {config.get('client_profile', {}).get('name', client_id)}")
        return config
    except Exception as e:
        logger.error(f"Erreur chargement config client: {e}")
        return {}
