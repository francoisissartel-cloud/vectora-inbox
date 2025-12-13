"""
Module de filtrage d'ingestion basé sur les profils.

Ce module implémente la logique de filtrage intelligent des items bruts
avant normalisation Bedrock, selon les profils d'ingestion définis dans
le canonical.

Responsabilités :
- Charger les profils d'ingestion depuis S3
- Résoudre le profil applicable pour chaque source
- Appliquer la stratégie de filtrage selon le profil
- Détecter les signaux dans le texte brut
- Fournir des métriques de filtrage
"""

import logging
import re
from typing import Dict, List, Any, Optional, Set
from functools import lru_cache

logger = logging.getLogger(__name__)


class IngestionProfileFilter:
    """
    Filtre d'ingestion basé sur les profils configurables.
    
    Cette classe charge les profils d'ingestion depuis le canonical
    et applique la logique de filtrage appropriée pour chaque source.
    """
    
    def __init__(self, config_bucket: str):
        """
        Initialise le filtre avec le bucket de configuration.
        
        Args:
            config_bucket: Nom du bucket S3 contenant le canonical
        """
        self.config_bucket = config_bucket
        self.profiles = {}  # Cache des profils d'ingestion
        self.scopes = {}    # Cache des scopes
        self.source_catalog = {}  # Cache du catalogue de sources
        self._loaded = False
    
    def load_configurations(self):
        """
        Charge les configurations depuis S3 (profils, scopes, source catalog).
        
        Cette méthode est appelée automatiquement lors du premier usage.
        """
        if self._loaded:
            return
            
        logger.info("Chargement des profils d'ingestion depuis S3")
        
        try:
            from vectora_core.storage import s3_client
            
            # Charger les profils d'ingestion
            profiles_data = s3_client.read_yaml_from_s3(
                self.config_bucket, 
                "canonical/ingestion/ingestion_profiles.yaml"
            )
            self.profiles = profiles_data.get('profiles', {})
            logger.info(f"Chargé {len(self.profiles)} profils d'ingestion")
            
            # Charger le catalogue de sources
            catalog_data = s3_client.read_yaml_from_s3(
                self.config_bucket,
                "canonical/sources/source_catalog.yaml"
            )
            self.source_catalog = {
                source['source_key']: source 
                for source in catalog_data.get('sources', [])
            }
            logger.info(f"Chargé {len(self.source_catalog)} sources")
            
            # Charger les scopes nécessaires
            self._load_scopes()
            
            self._loaded = True
            logger.info("Configurations de filtrage d'ingestion chargées avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des configurations: {e}")
            raise
    
    def _load_scopes(self):
        """Charge les scopes référencés par les profils."""
        from vectora_core.storage import s3_client
        
        scope_files = {
            'technology_scopes': 'canonical/scopes/technology_scopes.yaml',
            'company_scopes': 'canonical/scopes/company_scopes.yaml',
            'trademark_scopes': 'canonical/scopes/trademark_scopes.yaml',
            'molecule_scopes': 'canonical/scopes/molecule_scopes.yaml',
            'exclusion_scopes': 'canonical/scopes/exclusion_scopes.yaml'
        }
        
        for scope_type, s3_key in scope_files.items():
            try:
                scope_data = s3_client.read_yaml_from_s3(self.config_bucket, s3_key)
                self.scopes[scope_type] = scope_data
                logger.debug(f"Chargé {scope_type}: {len(scope_data)} scopes")
            except Exception as e:
                logger.warning(f"Impossible de charger {scope_type}: {e}")
                self.scopes[scope_type] = {}
    
    def apply_filter(self, item: Dict[str, Any], source_key: str, client_config: Dict[str, Any] = None) -> bool:
        """
        Applique le filtrage d'ingestion à un item.
        
        Args:
            item: Item brut à filtrer
            source_key: Clé de la source (pour résoudre le profil)
            client_config: Configuration client (pour trademark_privileges v2)
        
        Returns:
            True si l'item doit être ingéré, False s'il doit être filtré
        """
        self.load_configurations()
        
        # NOUVEAU v2 : Vérifier trademark_privileges.ingestion_priority
        if client_config and self._should_force_ingest_for_trademarks(item, client_config):
            logger.info(f"[TRADEMARK_PRIORITY] Item forcé en ingéstion grâce aux trademarks: {item.get('title', '')[:50]}...")
            return True
        
        # Résoudre le profil pour cette source
        profile_name = self._get_profile_for_source(source_key)
        if not profile_name:
            logger.debug(f"Source {source_key}: aucun profil défini, utilisation de default_broad")
            return True  # Comportement par défaut
        
        profile = self.profiles.get(profile_name)
        if not profile:
            logger.warning(f"Profil {profile_name} non trouvé, utilisation de default_broad")
            return True
        
        # Appliquer la stratégie du profil
        strategy = profile.get('strategy', 'no_filtering')
        
        try:
            if strategy == 'broad_ingestion':
                return self._apply_broad_ingestion(item, profile)
            elif strategy == 'signal_based_ingestion':
                return self._apply_signal_based_ingestion(item, profile)
            elif strategy == 'multi_signal_ingestion':
                return self._apply_multi_signal_ingestion(item, profile)
            elif strategy == 'no_filtering':
                return True
            else:
                logger.warning(f"Stratégie {strategy} non reconnue pour {profile_name}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'application du profil {profile_name}: {e}")
            return True  # En cas d'erreur, on ingère (sécurité)
    
    def _get_profile_for_source(self, source_key: str) -> Optional[str]:
        """Résout le profil d'ingestion pour une source."""
        source_meta = self.source_catalog.get(source_key)
        if not source_meta:
            return None
        return source_meta.get('ingestion_profile')
    
    def _apply_broad_ingestion(self, item: Dict[str, Any], profile: Dict[str, Any]) -> bool:
        """
        Applique la stratégie broad_ingestion (ingère tout sauf exclusions).
        
        Args:
            item: Item à filtrer
            profile: Configuration du profil
        
        Returns:
            True si l'item doit être ingéré
        """
        signal_req = profile.get('signal_requirements', {})
        exclusion_scopes = signal_req.get('exclusion_scopes', [])
        
        if not exclusion_scopes:
            return True  # Aucune exclusion définie
        
        # Construire le texte à analyser
        text = self._build_analysis_text(item)
        
        # Vérifier les exclusions
        for exclusion_scope in exclusion_scopes:
            if self._detect_signals_in_scope(text, exclusion_scope) > 0:
                logger.debug(f"Item filtré par exclusion {exclusion_scope}")
                return False
        
        return True
    
    def _apply_signal_based_ingestion(self, item: Dict[str, Any], profile: Dict[str, Any]) -> bool:
        """
        Applique la stratégie signal_based_ingestion (requiert signaux spécifiques).
        
        Args:
            item: Item à filtrer
            profile: Configuration du profil
        
        Returns:
            True si l'item doit être ingéré
        """
        signal_req = profile.get('signal_requirements', {})
        required_groups = signal_req.get('required_signal_groups', [])
        combination_logic = signal_req.get('combination_logic', '')
        min_weight = signal_req.get('minimum_total_weight', 0)
        
        if not required_groups:
            return True
        
        text = self._build_analysis_text(item)
        
        # Évaluer chaque groupe de signaux
        group_results = {}
        total_weight = 0
        
        for group in required_groups:
            group_id = group.get('group_id')
            scopes = group.get('scopes', [])
            min_matches = group.get('min_matches', 1)
            weight = group.get('weight', 1.0)
            
            matches = 0
            for scope in scopes:
                matches += self._detect_signals_in_scope(text, scope)
            
            group_satisfied = matches >= min_matches
            group_results[group_id] = group_satisfied
            
            if group_satisfied:
                total_weight += weight
        
        # Évaluer la logique de combinaison
        if combination_logic:
            result = self._evaluate_combination_logic(combination_logic, group_results)
        else:
            # Par défaut : au moins un groupe doit être satisfait
            result = any(group_results.values())
        
        # Vérifier le poids minimum
        if min_weight > 0:
            result = result and (total_weight >= min_weight)
        
        return result
    
    def _apply_multi_signal_ingestion(self, item: Dict[str, Any], profile: Dict[str, Any]) -> bool:
        """
        Applique la stratégie multi_signal_ingestion (combinaison de signaux multiples).
        
        Similaire à signal_based_ingestion mais avec logique AND par défaut.
        """
        return self._apply_signal_based_ingestion(item, profile)
    
    def _build_analysis_text(self, item: Dict[str, Any]) -> str:
        """
        Construit le texte à analyser à partir d'un item.
        
        Args:
            item: Item brut
        
        Returns:
            Texte combiné (titre + description)
        """
        title = item.get('title', '')
        raw_text = item.get('raw_text', '')
        
        # Combiner titre et texte avec un espace
        combined = f"{title} {raw_text}".strip()
        return combined
    
    @lru_cache(maxsize=1000)
    def _detect_signals_in_scope(self, text: str, scope_key: str) -> int:
        """
        Détecte les signaux d'un scope dans un texte.
        
        Args:
            text: Texte à analyser
            scope_key: Clé du scope (ex: 'lai_keywords.core_phrases')
        
        Returns:
            Nombre de signaux détectés
        """
        keywords = self._get_keywords_for_scope(scope_key)
        if not keywords:
            return 0
        
        text_lower = text.lower()
        matches = 0
        
        for keyword in keywords:
            if isinstance(keyword, str) and keyword.lower() in text_lower:
                matches += 1
        
        return matches
    
    def _get_keywords_for_scope(self, scope_key: str) -> List[str]:
        """
        Récupère les mots-clés pour un scope donné.
        
        Args:
            scope_key: Clé du scope (ex: 'lai_keywords.core_phrases')
        
        Returns:
            Liste des mots-clés
        """
        # Parser la clé du scope
        if '.' in scope_key:
            scope_file, sub_key = scope_key.split('.', 1)
        else:
            scope_file = scope_key
            sub_key = None
        
        # Mapper vers le fichier de scope approprié
        scope_file_mapping = {
            'lai_keywords': 'technology_scopes',
            'lai_companies_global': 'company_scopes',
            'lai_companies_pure_players': 'company_scopes',
            'lai_companies_hybrid': 'company_scopes',
            'lai_companies_mvp_core': 'company_scopes',
            'lai_trademarks_global': 'trademark_scopes',
            'lai_molecules_global': 'molecule_scopes',
            'exclusion_scopes': 'exclusion_scopes'
        }
        
        # Déterminer le fichier de scope
        if scope_file in scope_file_mapping:
            scope_type = scope_file_mapping[scope_file]
        elif scope_key.startswith('exclusion_scopes.'):
            scope_type = 'exclusion_scopes'
            sub_key = scope_key.split('.', 1)[1]
        else:
            logger.warning(f"Scope {scope_key} non reconnu")
            return []
        
        scope_data = self.scopes.get(scope_type, {})
        
        if sub_key:
            # Accès à une sous-clé (ex: lai_keywords.core_phrases)
            if scope_file in scope_data:
                nested_data = scope_data[scope_file]
                if isinstance(nested_data, dict) and sub_key in nested_data:
                    return nested_data[sub_key]
            elif sub_key in scope_data:
                # Accès direct (ex: exclusion_scopes.hr_content)
                return scope_data[sub_key]
        else:
            # Accès direct au scope
            if scope_key in scope_data:
                return scope_data[scope_key]
        
        logger.debug(f"Aucun mot-clé trouvé pour le scope {scope_key}")
        return []
    
    def _evaluate_combination_logic(self, logic: str, group_results: Dict[str, bool]) -> bool:
        """
        Évalue une expression logique simple.
        
        Args:
            logic: Expression logique (ex: "entity_signals AND technology_signals")
            group_results: Résultats par groupe
        
        Returns:
            Résultat de l'évaluation
        """
        try:
            # Remplacer les noms de groupes par leurs valeurs
            expression = logic
            for group_id, result in group_results.items():
                expression = expression.replace(group_id, str(result))
            
            # Remplacer les opérateurs logiques
            expression = expression.replace(' AND ', ' and ')
            expression = expression.replace(' OR ', ' or ')
            expression = expression.replace(' NOT ', ' not ')
            
            # Évaluer l'expression (sécurisé car on contrôle le contenu)
            return eval(expression)
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'évaluation de la logique '{logic}': {e}")
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Retourne les métriques de filtrage.
        
        Returns:
            Dictionnaire des métriques
        """
        return {
            'profiles_loaded': len(self.profiles),
            'scopes_loaded': sum(len(scope) for scope in self.scopes.values()),
            'sources_configured': len(self.source_catalog)
        }
    
    def _should_force_ingest_for_trademarks(self, item: Dict[str, Any], client_config: Dict[str, Any]) -> bool:
        """
        Vérifie si un item doit être forcé en ingéstion grâce aux trademarks.
        
        Args:
            item: Item brut à analyser
            client_config: Configuration client v2
        
        Returns:
            True si l'item contient des trademarks du scope client et que ingestion_priority est activé
        """
        # Vérifier si trademark_privileges.ingestion_priority est activé
        runtime_metadata = client_config.get('_runtime_metadata', {})
        if not runtime_metadata.get('has_trademark_privileges', False):
            return False
        
        matching_config = client_config.get('matching_config', {})
        trademark_privileges = matching_config.get('trademark_privileges', {})
        if not trademark_privileges.get('ingestion_priority', False):
            return False
        
        # Extraire les trademark_scopes du client
        trademark_scopes = runtime_metadata.get('trademark_scopes', [])
        if not trademark_scopes:
            return False
        
        # Construire le texte à analyser
        text = self._build_analysis_text(item)
        
        # Vérifier si des trademarks du scope sont présents
        for scope_key in trademark_scopes:
            trademark_keywords = self._get_keywords_for_scope(scope_key)
            if self._detect_trademarks_in_text(text, trademark_keywords) > 0:
                logger.debug(f"[TRADEMARK_DETECTION] Trademarks détectés dans scope {scope_key}")
                return True
        
        return False
    
    def _detect_trademarks_in_text(self, text: str, trademarks: List[str]) -> int:
        """
        Détecte les trademarks dans un texte avec logique améliorée.
        
        Args:
            text: Texte à analyser
            trademarks: Liste des trademarks à chercher
        
        Returns:
            Nombre de trademarks détectés
        """
        if not trademarks:
            return 0
        
        text_lower = text.lower()
        matches = 0
        
        for trademark in trademarks:
            if isinstance(trademark, str):
                # Recherche exacte (case-insensitive)
                if trademark.lower() in text_lower:
                    matches += 1
                    logger.debug(f"[TRADEMARK_MATCH] '{trademark}' détecté dans le texte")
        
        return matches