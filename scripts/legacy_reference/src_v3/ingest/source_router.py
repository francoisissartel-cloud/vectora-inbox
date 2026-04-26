"""
Source Router V3 - Résolution des bouquets en sources configurées

Ce module résout les bouquets de sources en sources individuelles validées,
combine les métadonnées de source_catalog avec les configs techniques de source_configs
et les profils d'ingestion, puis retourne des objets ResolvedSource prêts à ingérer.

Responsabilités :
- Résoudre les bouquets en listes de source_key
- Valider chaque source (skip si validated: false)
- Combiner source_catalog + source_configs + ingestion_profiles
- Résoudre l'actor_type dynamiquement via company_scopes
- Retourner des ResolvedSource avec toute la config nécessaire
"""

from typing import List, Dict, Any, Optional
import logging

from .config_loader_v3 import CanonicalConfig
from .models import ResolvedSource
from .pagination_adaptive import get_universal_pagination_config
from ..shared.utils import safe_get_nested

logger = logging.getLogger(__name__)


class SourceRouter:
    """
    Routeur de sources V3.
    
    Résout les bouquets de sources en sources individuelles configurées
    et prêtes pour l'ingestion.
    """
    
    def __init__(self, canonical_config: CanonicalConfig):
        """
        Initialise le routeur avec la configuration canonical.
        
        Args:
            canonical_config: Configuration canonical complète
        """
        self.canonical_config = canonical_config
        logger.info("SourceRouter V3 initialisé")
    
    def resolve_sources_from_bouquets(self, bouquet_ids: List[str], period_days: int = None) -> List[ResolvedSource]:
        """
        Résout une liste de bouquets en sources configurées.
        
        Args:
            bouquet_ids: Liste des IDs de bouquets à résoudre
            period_days: Période d'ingestion pour pagination adaptative
        
        Returns:
            Liste des sources résolues et validées
        """
        logger.info(f"Résolution de {len(bouquet_ids)} bouquets : {bouquet_ids}")
        
        # Étape 1 : Résoudre tous les bouquets en source_keys
        all_source_keys = []
        for bouquet_id in bouquet_ids:
            source_keys = self.canonical_config.resolve_bouquet_sources(bouquet_id)
            if source_keys:
                all_source_keys.extend(source_keys)
                logger.info(f"Bouquet '{bouquet_id}' → {len(source_keys)} sources")
            else:
                logger.warning(f"Bouquet '{bouquet_id}' introuvable ou vide")
        
        # Déduplication des source_keys
        unique_source_keys = list(set(all_source_keys))
        logger.info(f"Total : {len(unique_source_keys)} sources uniques à traiter")
        
        # Étape 2 : Résoudre chaque source_key en ResolvedSource
        resolved_sources = []
        for source_key in unique_source_keys:
            try:
                resolved_source = self._resolve_single_source(source_key, period_days)
                if resolved_source:
                    resolved_sources.append(resolved_source)
                else:
                    logger.warning(f"Source '{source_key}' ignorée (non validée ou config manquante)")
            except Exception as e:
                logger.error(f"Erreur lors de la résolution de '{source_key}' : {e}")
        
        logger.info(f"Résolution terminée : {len(resolved_sources)}/{len(unique_source_keys)} sources validées")
        return resolved_sources
    
    def resolve_specific_sources(self, source_keys: List[str], period_days: int = None) -> List[ResolvedSource]:
        """
        Résout une liste spécifique de source_keys (bypass des bouquets).
        
        Args:
            source_keys: Liste des source_keys à résoudre directement
            period_days: Période d'ingestion pour pagination adaptative
        
        Returns:
            Liste des sources résolues et validées
        """
        logger.info(f"Résolution directe de {len(source_keys)} sources : {source_keys}")
        
        resolved_sources = []
        for source_key in source_keys:
            try:
                resolved_source = self._resolve_single_source(source_key, period_days)
                if resolved_source:
                    resolved_sources.append(resolved_source)
                else:
                    logger.warning(f"Source '{source_key}' ignorée (non validée ou config manquante)")
            except Exception as e:
                logger.error(f"Erreur lors de la résolution de '{source_key}' : {e}")
        
        logger.info(f"Résolution directe terminée : {len(resolved_sources)}/{len(source_keys)} sources validées")
        return resolved_sources
    
    def _resolve_single_source(self, source_key: str, period_days: int = None) -> Optional[ResolvedSource]:
        """
        Résout une source individuelle en combinant catalog + config + profil.
        
        Args:
            source_key: Clé de la source à résoudre
            period_days: Période d'ingestion pour pagination adaptative
        
        Returns:
            ResolvedSource ou None si la source n'est pas valide
        """
        logger.debug(f"Résolution de la source : {source_key}")
        
        # Étape 1 : Récupérer les métadonnées depuis source_catalog
        source_meta = self.canonical_config.get_source_by_key(source_key)
        if not source_meta:
            logger.warning(f"Source '{source_key}' absente du source_catalog")
            return None
        
        # Étape 2 : Récupérer la config technique depuis source_configs
        source_config = self.canonical_config.get_source_config(source_key)
        if not source_config:
            logger.warning(f"Source '{source_key}' absente de source_configs")
            return None
        
        # Étape 3 : Vérifier que la source est validée
        if not source_config.get('validated', False):
            logger.info(f"Source '{source_key}' ignorée (validated: false)")
            return None
        
        # Étape 4 : Récupérer le profil d'ingestion
        ingestion_profile_id = source_config.get('ingestion_profile')
        if not ingestion_profile_id:
            logger.error(f"Source '{source_key}' sans ingestion_profile")
            return None
        
        profile_config = self.canonical_config.get_ingestion_profile(ingestion_profile_id)
        if not profile_config:
            logger.error(f"Profil '{ingestion_profile_id}' introuvable pour source '{source_key}'")
            return None
        
        # Étape 5 : Résoudre l'actor_type dynamiquement
        company_id = source_meta.get('company_id')
        source_type = source_meta.get('source_type')
        actor_type = self._resolve_actor_type(company_id, source_type)
        
        # Étape 6 : Construire l'URL de news
        news_url = source_config.get('news_url')
        if not news_url:
            logger.error(f"Source '{source_key}' sans news_url")
            return None
        
        # Étape 7 : PAGINATION ADAPTATIVE - Calculer la pagination optimale
        base_pagination = source_config.get('pagination', {})
        if period_days:
            # Appliquer la pagination adaptative
            adaptive_pagination = get_universal_pagination_config(
                source_config={
                    'source_type': source_type,
                    'source_key': source_key,
                    'pagination': base_pagination
                },
                period_days=period_days,
                canonical_config=self.canonical_config
            )
            
            # Fusionner avec la config de base
            final_pagination = base_pagination.copy()
            final_pagination.update({
                'enabled': True,
                'max_pages': adaptive_pagination['max_pages'],
                'adaptive_config': adaptive_pagination  # Garder les métadonnées
            })
            
            logger.info(f"Pagination adaptative pour {source_key}: {adaptive_pagination['max_pages']} pages (activity: {adaptive_pagination['activity_level']})")
        else:
            final_pagination = base_pagination
        
        # Étape 8 : Construire le ResolvedSource
        resolved_source = ResolvedSource(
            source_key=source_key,
            company_id=company_id,
            source_type=source_type,
            actor_type=actor_type,
            homepage_url=source_meta.get('homepage_url', ''),
            news_url=news_url,
            ingestion_profile=ingestion_profile_id,
            profile_config=profile_config,
            listing_selectors=source_config.get('listing_selectors'),
            date_selectors=source_config.get('date_selectors'),
            prefetch_filter=source_config.get('prefetch_filter', False),
            pagination=final_pagination,  # Utiliser la pagination adaptative
            validated=True,
            default_language=source_meta.get('default_language', 'en')
        )
        
        logger.debug(f"✅ Source '{source_key}' résolue : {actor_type}, profil {ingestion_profile_id}")
        return resolved_source
    
    def _resolve_actor_type(self, company_id: Optional[str], source_type: str) -> str:
        """
        Résout l'actor_type d'une source selon les règles de filter_rules_v3.yaml.
        
        Args:
            company_id: ID de l'entreprise (peut être None)
            source_type: Type de source
        
        Returns:
            Actor type résolu (pure_lai, hybrid, press_sector, unknown)
        """
        # Règle 1 : Si company_id dans pure_players → pure_lai
        if company_id:
            actor_type = self.canonical_config.get_actor_type_for_company(company_id)
            if actor_type != "unknown":
                return actor_type
        
        # Règle 2 : Si source_type == press_sector → press_sector
        if source_type == "press_sector":
            return "press_sector"
        
        # Règle 3 : Défaut → unknown
        return "unknown"
    
    def get_sources_summary(self, resolved_sources: List[ResolvedSource]) -> Dict[str, Any]:
        """
        Génère un résumé des sources résolues pour logging/debug.
        
        Args:
            resolved_sources: Liste des sources résolues
        
        Returns:
            Dictionnaire de résumé
        """
        if not resolved_sources:
            return {"total": 0}
        
        # Compter par actor_type
        actor_type_counts = {}
        for source in resolved_sources:
            actor_type = source.actor_type
            actor_type_counts[actor_type] = actor_type_counts.get(actor_type, 0) + 1
        
        # Compter par profil
        profile_counts = {}
        for source in resolved_sources:
            profile = source.ingestion_profile
            profile_counts[profile] = profile_counts.get(profile, 0) + 1
        
        # Lister les sources avec prefetch_filter
        prefetch_sources = [s.source_key for s in resolved_sources if s.prefetch_filter]
        
        summary = {
            "total": len(resolved_sources),
            "by_actor_type": actor_type_counts,
            "by_profile": profile_counts,
            "prefetch_filter_enabled": len(prefetch_sources),
            "prefetch_sources": prefetch_sources
        }
        
        return summary


def create_source_router(canonical_config: CanonicalConfig) -> SourceRouter:
    """
    Factory function pour créer un SourceRouter.
    
    Args:
        canonical_config: Configuration canonical complète
    
    Returns:
        Instance de SourceRouter configurée
    """
    return SourceRouter(canonical_config)