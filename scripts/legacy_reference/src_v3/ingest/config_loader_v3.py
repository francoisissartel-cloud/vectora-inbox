"""
Config Loader V3 - Chargement de tous les fichiers canonical

Ce module est le point d'entrée unique pour charger TOUTE la configuration canonical V3.
Il expose un objet CanonicalConfig qui contient tous les YAML nécessaires au moteur.

Responsabilités :
- Charger tous les fichiers canonical V3 (local ou S3)
- Valider la cohérence des configurations
- Exposer une interface unifiée pour le reste du code
- Gestion d'erreurs robuste avec fallbacks

Principe : le reste du code ne sait jamais d'où viennent les données.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging
import os
from pathlib import Path

from ..shared.s3_io import read_yaml_from_s3
from ..shared.utils import safe_get_nested

logger = logging.getLogger(__name__)


@dataclass
class CanonicalConfig:
    """
    Configuration canonical complète V3.
    
    Contient tous les fichiers YAML canonical chargés et validés.
    """
    source_catalog: Dict[str, Any]      # source_catalog_v3.yaml → sources + bouquets
    source_configs: Dict[str, Any]      # source_configs_v3.yaml → config validée par source
    ingestion_profiles: Dict[str, Any]  # ingestion_profiles_v3.yaml → profils fetch
    filter_rules: Dict[str, Any]        # filter_rules_v3.yaml → règles filtrage
    company_scopes: Dict[str, Any]      # company_scopes.yaml → pure/hybrid
    exclusion_scopes: Dict[str, Any]    # exclusion_scopes.yaml → termes exclusion
    technology_scopes: Dict[str, Any]   # technology_scopes.yaml → LAI keywords
    trademark_scopes: Dict[str, Any]    # trademark_scopes.yaml → LAI trademarks
    
    def get_source_by_key(self, source_key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une source par sa clé depuis source_catalog.
        
        Args:
            source_key: Clé de la source
        
        Returns:
            Dictionnaire de la source ou None si non trouvée
        """
        sources = safe_get_nested(self.source_catalog, ['sources'], [])
        for source in sources:
            if source.get('source_key') == source_key:
                return source
        return None
    
    def get_source_config(self, source_key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère la config technique d'une source depuis source_configs.
        
        Args:
            source_key: Clé de la source
        
        Returns:
            Dictionnaire de config ou None si non trouvée
        """
        sources = safe_get_nested(self.source_configs, ['sources'], {})
        return sources.get(source_key)
    
    def get_ingestion_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un profil d'ingestion par son ID.
        
        Args:
            profile_id: ID du profil (rss_full, html_generic, etc.)
        
        Returns:
            Dictionnaire du profil ou None si non trouvé
        """
        profiles = safe_get_nested(self.ingestion_profiles, ['profiles'], {})
        return profiles.get(profile_id)
    
    def resolve_bouquet_sources(self, bouquet_id: str) -> list[str]:
        """
        Résout un bouquet en liste de source_key.
        
        Args:
            bouquet_id: ID du bouquet
        
        Returns:
            Liste des source_key du bouquet
        """
        bouquets = safe_get_nested(self.source_catalog, ['bouquets'], [])
        for bouquet in bouquets:
            if bouquet.get('bouquet_id') == bouquet_id:
                return bouquet.get('source_keys', [])
        
        logger.warning(f"Bouquet non trouvé : {bouquet_id}")
        return []
    
    def get_actor_type_for_company(self, company_id: str) -> str:
        """
        Résout l'actor_type d'une entreprise via company_scopes.
        
        Args:
            company_id: ID de l'entreprise
        
        Returns:
            Actor type (pure_lai, hybrid, unknown)
        """
        if not company_id:
            return "unknown"
        
        pure_players = safe_get_nested(self.company_scopes, ['lai_companies_pure_players'], [])
        if company_id in pure_players:
            return "pure_lai"
        
        hybrid_players = safe_get_nested(self.company_scopes, ['lai_companies_hybrid'], [])
        if company_id in hybrid_players:
            return "hybrid"
        
        return "unknown"
    
    def get_exclusion_terms(self, scope_names: list[str]) -> list[str]:
        """
        Récupère tous les termes d'exclusion pour des scopes donnés.
        
        Args:
            scope_names: Liste des noms de scopes
        
        Returns:
            Liste de tous les termes d'exclusion
        """
        all_terms = []
        for scope_name in scope_names:
            terms = safe_get_nested(self.exclusion_scopes, [scope_name], [])
            if isinstance(terms, list):
                all_terms.extend(terms)
            else:
                logger.warning(f"Scope d'exclusion invalide : {scope_name}")
        
        return list(set(all_terms))  # Déduplication
    
    def get_lai_keywords(self, scope_names: list[str]) -> list[str]:
        """
        Récupère tous les mots-clés LAI pour des scopes donnés.
        
        Args:
            scope_names: Liste des noms de scopes
        
        Returns:
            Liste de tous les mots-clés LAI
        """
        all_keywords = []
        
        for scope_name in scope_names:
            # Chercher dans technology_scopes
            tech_terms = safe_get_nested(self.technology_scopes, scope_name.split('.'), [])
            if isinstance(tech_terms, list):
                all_keywords.extend(tech_terms)
            
            # Chercher dans trademark_scopes
            trademark_terms = safe_get_nested(self.trademark_scopes, scope_name.split('.'), [])
            if isinstance(trademark_terms, list):
                all_keywords.extend(trademark_terms)
        
        return list(set(all_keywords))  # Déduplication


def load_from_local(base_path: str) -> CanonicalConfig:
    """
    Charge la configuration canonical depuis le filesystem local.
    
    Args:
        base_path: Chemin vers le dossier canonical (ex: "./canonical")
    
    Returns:
        Configuration canonical complète
    
    Raises:
        FileNotFoundError: Si un fichier canonical est manquant
        Exception: Si erreur de parsing YAML
    """
    logger.info(f"Chargement de la configuration canonical depuis {base_path}")
    
    base_path = Path(base_path)
    
    # Définir les chemins des fichiers canonical V3
    files_to_load = {
        'source_catalog': base_path / 'sources' / 'source_catalog_v3.yaml',
        'source_configs': base_path / 'ingestion' / 'source_configs_v3.yaml',
        'ingestion_profiles': base_path / 'ingestion' / 'ingestion_profiles_v3.yaml',
        'filter_rules': base_path / 'ingestion' / 'filter_rules_v3.yaml',
        'company_scopes': base_path / 'scopes' / 'company_scopes.yaml',
        'exclusion_scopes': base_path / 'scopes' / 'exclusion_scopes.yaml',
        'technology_scopes': base_path / 'scopes' / 'technology_scopes.yaml',
        'trademark_scopes': base_path / 'scopes' / 'trademark_scopes.yaml',
    }
    
    # Charger tous les fichiers
    loaded_configs = {}
    for config_name, file_path in files_to_load.items():
        try:
            logger.info(f"Chargement de {config_name} depuis {file_path}")
            
            if not file_path.exists():
                raise FileNotFoundError(f"Fichier canonical manquant : {file_path}")
            
            import yaml
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            loaded_configs[config_name] = config_data
            logger.info(f"✅ {config_name} chargé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de {config_name} : {e}")
            raise
    
    # Créer l'objet CanonicalConfig
    canonical_config = CanonicalConfig(
        source_catalog=loaded_configs['source_catalog'],
        source_configs=loaded_configs['source_configs'],
        ingestion_profiles=loaded_configs['ingestion_profiles'],
        filter_rules=loaded_configs['filter_rules'],
        company_scopes=loaded_configs['company_scopes'],
        exclusion_scopes=loaded_configs['exclusion_scopes'],
        technology_scopes=loaded_configs['technology_scopes'],
        trademark_scopes=loaded_configs['trademark_scopes'],
    )
    
    # Validation de base
    _validate_canonical_config(canonical_config)
    
    logger.info("✅ Configuration canonical V3 chargée avec succès depuis le filesystem local")
    return canonical_config


def load_from_s3(config_bucket: str) -> CanonicalConfig:
    """
    Charge la configuration canonical depuis S3.
    
    Args:
        config_bucket: Nom du bucket S3 de configuration
    
    Returns:
        Configuration canonical complète
    
    Raises:
        Exception: Si erreur de chargement depuis S3
    """
    logger.info(f"Chargement de la configuration canonical depuis S3 : {config_bucket}")
    
    # Définir les clés S3 des fichiers canonical V3
    s3_keys = {
        'source_catalog': 'canonical/sources/source_catalog_v3.yaml',
        'source_configs': 'canonical/ingestion/source_configs_v3.yaml',
        'ingestion_profiles': 'canonical/ingestion/ingestion_profiles_v3.yaml',
        'filter_rules': 'canonical/ingestion/filter_rules_v3.yaml',
        'company_scopes': 'canonical/scopes/company_scopes.yaml',
        'exclusion_scopes': 'canonical/scopes/exclusion_scopes.yaml',
        'technology_scopes': 'canonical/scopes/technology_scopes.yaml',
        'trademark_scopes': 'canonical/scopes/trademark_scopes.yaml',
    }
    
    # Charger tous les fichiers depuis S3
    loaded_configs = {}
    for config_name, s3_key in s3_keys.items():
        try:
            logger.info(f"Chargement de {config_name} depuis s3://{config_bucket}/{s3_key}")
            
            config_data = read_yaml_from_s3(config_bucket, s3_key)
            loaded_configs[config_name] = config_data
            
            logger.info(f"✅ {config_name} chargé avec succès depuis S3")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de {config_name} depuis S3 : {e}")
            raise
    
    # Créer l'objet CanonicalConfig
    canonical_config = CanonicalConfig(
        source_catalog=loaded_configs['source_catalog'],
        source_configs=loaded_configs['source_configs'],
        ingestion_profiles=loaded_configs['ingestion_profiles'],
        filter_rules=loaded_configs['filter_rules'],
        company_scopes=loaded_configs['company_scopes'],
        exclusion_scopes=loaded_configs['exclusion_scopes'],
        technology_scopes=loaded_configs['technology_scopes'],
        trademark_scopes=loaded_configs['trademark_scopes'],
    )
    
    # Validation de base
    _validate_canonical_config(canonical_config)
    
    logger.info("✅ Configuration canonical V3 chargée avec succès depuis S3")
    return canonical_config


def _validate_canonical_config(config: CanonicalConfig) -> None:
    """
    Valide la cohérence de la configuration canonical.
    
    Args:
        config: Configuration à valider
    
    Raises:
        ValueError: Si la configuration est incohérente
    """
    logger.info("Validation de la configuration canonical...")
    
    # Vérifier que les fichiers principaux ont du contenu
    if not config.source_catalog.get('sources'):
        raise ValueError("source_catalog_v3.yaml ne contient aucune source")
    
    if not config.ingestion_profiles.get('profiles'):
        raise ValueError("ingestion_profiles_v3.yaml ne contient aucun profil")
    
    # Vérifier la cohérence source_catalog <-> source_configs
    catalog_sources = {s['source_key'] for s in config.source_catalog.get('sources', [])}
    config_sources = set(config.source_configs.get('sources', {}).keys())
    
    missing_configs = catalog_sources - config_sources
    if missing_configs:
        logger.warning(f"Sources dans catalog mais pas dans configs : {missing_configs}")
    
    # Vérifier que les profils référencés existent
    available_profiles = set(config.ingestion_profiles.get('profiles', {}).keys())
    for source_key, source_config in config.source_configs.get('sources', {}).items():
        profile_id = source_config.get('ingestion_profile')
        if profile_id and profile_id not in available_profiles:
            raise ValueError(f"Source {source_key} référence un profil inexistant : {profile_id}")
    
    logger.info("✅ Configuration canonical validée avec succès")


def load_client_config_from_local(client_config_path: str) -> Dict[str, Any]:
    """
    Charge un client config depuis le filesystem local.
    
    Args:
        client_config_path: Chemin vers le fichier client config
    
    Returns:
        Configuration client
    """
    logger.info(f"Chargement du client config depuis {client_config_path}")
    
    try:
        import yaml
        with open(client_config_path, 'r', encoding='utf-8') as f:
            client_config = yaml.safe_load(f)
        
        logger.info("✅ Client config chargé avec succès")
        return client_config
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du client config : {e}")
        raise


def load_client_config_from_s3(config_bucket: str, client_id: str) -> Dict[str, Any]:
    """
    Charge un client config depuis S3.
    
    Args:
        config_bucket: Bucket de configuration
        client_id: ID du client
    
    Returns:
        Configuration client
    """
    s3_key = f"config/clients/{client_id}.yaml"
    logger.info(f"Chargement du client config depuis s3://{config_bucket}/{s3_key}")
    
    try:
        client_config = read_yaml_from_s3(config_bucket, s3_key)
        logger.info("✅ Client config chargé avec succès depuis S3")
        return client_config
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement du client config depuis S3 : {e}")
        raise