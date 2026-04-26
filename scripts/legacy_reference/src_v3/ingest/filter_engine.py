"""
Filter Engine V3 - Applique les règles de filtrage depuis filter_rules_v3.yaml
Zéro valeur hardcodée, tout vient des fichiers canonical.

Filtres appliqués séquentiellement :
1. Période (period_days depuis client_config)
2. Exclusions (titre uniquement, selon actor_type)
3. LAI keywords (titre + contenu, selon actor_type et ingestion_mode)
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import re

from ..shared.utils import performance_timer
from .models import StructuredItem, FilterResult
from .pagination_adaptive import get_universal_pagination_config

logger = logging.getLogger(__name__)


class FilterEngineV3:
    """Moteur de filtrage V3 - applique les règles depuis canonical files"""
    
    def __init__(self, canonical_config, client_config: Dict[str, Any]):
        self.canonical_config = canonical_config
        self.client_config = client_config
        self.ingestion_mode = client_config.get('ingestion', {}).get('ingestion_mode', 'balanced')
        
        # VALIDATION OBLIGATOIRE : period_days DOIT être dans le client config
        self.period_days = client_config.get('ingestion', {}).get('default_period_days')
        if self.period_days is None:
            raise ValueError(
                "ERREUR CRITIQUE: default_period_days manquant dans client_config.ingestion.\n"
                "Cette valeur est obligatoire pour le filtrage temporel."
            )
        
        if not isinstance(self.period_days, int) or self.period_days <= 0:
            raise ValueError(
                f"ERREUR CRITIQUE: default_period_days invalide: {self.period_days}\n"
                f"La valeur doit être un entier positif."
            )
        
        # Cache des termes chargés
        self._exclusion_terms_cache = {}
        self._lai_keywords_cache = {}
        
        logger.info(f"FilterEngine initialized - mode: {self.ingestion_mode}, period: {self.period_days} days")
    
    def resolve_source_pagination(self, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée universel pour la pagination adaptative de toutes les sources
        
        Args:
            source_config: Configuration de la source
        
        Returns:
            Configuration de pagination adaptative
        """
        pagination_config = get_universal_pagination_config(
            source_config, 
            self.period_days, 
            self.canonical_config  # Passer canonical_config pour classification intelligente
        )
        
        # Log pour debugging
        logger.info(f"Source {source_config.get('source_key', 'unknown')}: "
                   f"{pagination_config['max_pages']} pages "
                   f"(activity={pagination_config['activity_level']}, "
                   f"method={pagination_config['calculation_method']})")
        
        return pagination_config
    
    @performance_timer
    def filter_items(self, items: List[StructuredItem], company_id: Optional[str] = None) -> Tuple[List[StructuredItem], List[StructuredItem]]:
        """
        Applique tous les filtres sur une liste d'items
        
        Returns:
            Tuple[accepted_items, rejected_items]
        """
        logger.info(f"Starting filter process for {len(items)} items")
        
        accepted_items = []
        rejected_items = []
        
        for item in items:
            # Résoudre l'actor_type pour cet item
            actor_type = self._resolve_actor_type(company_id, item.source_key)
            
            # Appliquer les filtres séquentiellement
            filter_result = self._apply_all_filters(item, actor_type)
            
            # Ajouter l'analyse de filtrage à l'item
            item.filter_analysis = filter_result.to_dict()
            
            if filter_result.passed_all_filters:
                accepted_items.append(item)
            else:
                rejected_items.append(item)
        
        logger.info(f"Filter results: {len(accepted_items)} accepted, {len(rejected_items)} rejected")
        return accepted_items, rejected_items
    
    def _resolve_actor_type(self, company_id: Optional[str], source_key: str) -> str:
        """Résout l'actor_type selon les règles de filter_rules_v3.yaml"""
        
        # Charger les règles de résolution
        actor_type_rules = self.canonical_config.filter_rules.get('actor_type_resolution', {})
        company_scopes = self.canonical_config.company_scopes
        
        # Résolution par company_id
        if company_id:
            pure_lai_companies = company_scopes.get('lai_companies_pure_players', [])
            hybrid_companies = company_scopes.get('lai_companies_hybrid', [])
            
            if company_id in pure_lai_companies:
                return 'pure_lai'
            elif company_id in hybrid_companies:
                return 'hybrid'
        
        # Si pas de company_id explicite, essayer d'extraire depuis source_key
        if not company_id:
            # Format attendu: "source_type__company_id" 
            parts = source_key.split('__')
            if len(parts) >= 2:
                extracted_company_id = parts[1]
                pure_lai_companies = company_scopes.get('lai_companies_pure_players', [])
                hybrid_companies = company_scopes.get('lai_companies_hybrid', [])
                
                if extracted_company_id in pure_lai_companies:
                    return 'pure_lai'
                elif extracted_company_id in hybrid_companies:
                    return 'hybrid'
        
        # Résolution par source_type
        source_meta = self.canonical_config.get_source_by_key(source_key)
        if source_meta:
            source_type = source_meta.get('source_type')
            if source_type == 'press_sector':
                return 'press_sector'
        
        return 'unknown'
    
    def _apply_all_filters(self, item: StructuredItem, actor_type: str) -> FilterResult:
        """Applique tous les filtres séquentiellement"""
        
        filter_result = FilterResult(passed_all_filters=False)  # Initialiser avec False par défaut
        
        # Filtre 1: Période
        period_passed, period_details = self._apply_period_filter(item)
        filter_result.period_filter = period_details
        
        if not period_passed:
            filter_result.passed_all_filters = False
            return filter_result
        
        # Filtre 2: Exclusions (selon ingestion_mode et actor_type)
        exclusion_passed, exclusion_details = self._apply_exclusion_filter(item, actor_type)
        filter_result.exclusion_filter = exclusion_details
        
        if not exclusion_passed:
            filter_result.passed_all_filters = False
            return filter_result
        
        # Filtre 3: LAI keywords (selon ingestion_mode et actor_type)
        lai_passed, lai_details = self._apply_lai_keyword_filter(item, actor_type)
        filter_result.lai_keyword_filter = lai_details
        
        if not lai_passed:
            filter_result.passed_all_filters = False
            return filter_result
        
        filter_result.passed_all_filters = True
        return filter_result
    
    def _apply_period_filter(self, item: StructuredItem) -> Tuple[bool, Dict[str, Any]]:
        """Filtre 1: Période - items trop anciens"""
        
        if not item.published_at:
            return False, {
                "passed": False,
                "period_days": self.period_days,
                "days_ago": None,
                "reason": "no_published_date"
            }
        
        # Calculer l'âge de l'item
        cutoff_date = datetime.now() - timedelta(days=self.period_days)
        published_date = datetime.fromisoformat(item.published_at.replace('Z', '+00:00'))
        
        days_ago = (datetime.now() - published_date.replace(tzinfo=None)).days
        passed = published_date.replace(tzinfo=None) >= cutoff_date
        
        return passed, {
            "passed": passed,
            "period_days": self.period_days,
            "days_ago": days_ago,
            "reason": None if passed else "too_old"
        }
    
    def _apply_exclusion_filter(self, item: StructuredItem, actor_type: str) -> Tuple[bool, Dict[str, Any]]:
        """Filtre 2: Exclusions - termes à exclure dans le titre"""
        
        # Vérifier si les exclusions s'appliquent selon le mode
        if self.ingestion_mode == 'broad':
            return True, {
                "passed": True,
                "scopes_checked": [],
                "terms_found": [],
                "exclusion_reason": None,
                "skipped_reason": "broad_mode"
            }
        
        # Charger les règles pour cet actor_type
        filter_rules = self.canonical_config.filter_rules.get('filter_rules', {})
        actor_rules = filter_rules.get(actor_type, {})
        exclusion_scopes = actor_rules.get('exclusion_scopes', [])
        
        if not exclusion_scopes:
            return True, {
                "passed": True,
                "scopes_checked": [],
                "terms_found": [],
                "exclusion_reason": None,
                "skipped_reason": f"no_exclusion_rules_for_{actor_type}"
            }
        
        # Charger les termes d'exclusion
        exclusion_terms = self._load_exclusion_terms(exclusion_scopes)
        
        # Chercher les termes dans le titre
        title_lower = item.title.lower() if item.title else ""
        found_terms = []
        
        for term in exclusion_terms:
            if re.search(r'\b' + re.escape(term.lower()) + r'\b', title_lower):
                found_terms.append(term)
        
        passed = len(found_terms) == 0
        exclusion_reason = f"found_exclusion_terms: {found_terms}" if found_terms else None
        
        return passed, {
            "passed": passed,
            "scopes_checked": exclusion_scopes,
            "terms_found": found_terms,
            "exclusion_reason": exclusion_reason
        }
    
    def _apply_lai_keyword_filter(self, item: StructuredItem, actor_type: str) -> Tuple[bool, Dict[str, Any]]:
        """Filtre 3: LAI keywords - au moins 1 keyword LAI requis"""
        
        # Charger les règles pour cet actor_type
        filter_rules = self.canonical_config.filter_rules.get('filter_rules', {})
        actor_rules = filter_rules.get(actor_type, {})
        require_lai_keywords = actor_rules.get('require_lai_keywords', True)
        
        # Vérification explicite pour pure_lai (Phase 3 correction)
        if actor_type == "pure_lai":
            return True, {
                "required": False,
                "passed": True,
                "scopes_checked": [],
                "keywords_found": [],
                "match_locations": {"title": [], "content": []},
                "failure_reason": None
            }
        
        # Vérifier si le filtre LAI s'applique selon le mode d'ingestion
        if self.ingestion_mode == 'broad':
            require_lai_keywords = False
        elif self.ingestion_mode == 'strict':
            require_lai_keywords = True
        # Pour balanced mode, utiliser la valeur des règles (déjà chargée)
        
        if not require_lai_keywords:
            return True, {
                "required": False,
                "passed": True,
                "scopes_checked": [],
                "keywords_found": [],
                "match_locations": {"title": [], "content": []},
                "failure_reason": None
            }
        
        # Charger les scopes LAI
        lai_keyword_scopes = actor_rules.get('lai_keyword_scopes', [])
        if not lai_keyword_scopes:
            return False, {
                "required": True,
                "passed": False,
                "scopes_checked": [],
                "keywords_found": [],
                "match_locations": {"title": [], "content": []},
                "failure_reason": f"no_lai_keyword_scopes_for_{actor_type}"
            }
        
        # Charger les keywords LAI
        lai_keywords = self._load_lai_keywords(lai_keyword_scopes)
        
        # Chercher les keywords dans titre + contenu
        title_lower = item.title.lower() if item.title else ""
        content_lower = item.content.lower() if item.content else ""
        
        title_matches = []
        content_matches = []
        
        for keyword in lai_keywords:
            keyword_lower = keyword.lower()
            if re.search(r'\b' + re.escape(keyword_lower) + r'\b', title_lower):
                title_matches.append(keyword)
            if re.search(r'\b' + re.escape(keyword_lower) + r'\b', content_lower):
                content_matches.append(keyword)
        
        all_matches = list(set(title_matches + content_matches))
        passed = len(all_matches) > 0
        
        return passed, {
            "required": True,
            "passed": passed,
            "scopes_checked": lai_keyword_scopes,
            "keywords_found": all_matches,
            "match_locations": {
                "title": title_matches,
                "content": content_matches
            },
            "failure_reason": "no_lai_keywords_found" if not passed else None
        }
    
    def _load_exclusion_terms(self, exclusion_scopes: List[str]) -> List[str]:
        """Charge les termes d'exclusion depuis les scopes"""
        
        cache_key = tuple(sorted(exclusion_scopes))
        if cache_key in self._exclusion_terms_cache:
            return self._exclusion_terms_cache[cache_key]
        
        terms = []
        exclusion_data = self.canonical_config.exclusion_scopes
        
        for scope in exclusion_scopes:
            scope_terms = exclusion_data.get(scope, [])
            terms.extend(scope_terms)
        
        # Déduplication
        unique_terms = list(set(terms))
        self._exclusion_terms_cache[cache_key] = unique_terms
        
        logger.debug(f"Loaded {len(unique_terms)} exclusion terms from scopes: {exclusion_scopes}")
        return unique_terms
    
    def _load_lai_keywords(self, lai_keyword_scopes: List[str]) -> List[str]:
        """Charge les keywords LAI depuis les scopes"""
        
        cache_key = tuple(sorted(lai_keyword_scopes))
        if cache_key in self._lai_keywords_cache:
            return self._lai_keywords_cache[cache_key]
        
        keywords = []
        
        # Charger depuis technology_scopes
        technology_data = self.canonical_config.technology_scopes
        for scope in lai_keyword_scopes:
            if scope.startswith('lai_keywords.'):
                scope_key = scope.replace('lai_keywords.', '')
                # FIX: Naviguer correctement dans la structure YAML
                lai_section = technology_data.get('lai_keywords', {})
                scope_terms = lai_section.get(scope_key, [])
                keywords.extend(scope_terms)
        
        # Charger depuis trademark_scopes
        trademark_data = self.canonical_config.trademark_scopes
        for scope in lai_keyword_scopes:
            if scope.startswith('lai_trademarks'):
                scope_terms = trademark_data.get(scope, [])
                keywords.extend(scope_terms)
        
        # Déduplication
        unique_keywords = list(set(keywords))
        self._lai_keywords_cache[cache_key] = unique_keywords
        
        logger.debug(f"Loaded {len(unique_keywords)} LAI keywords from scopes: {lai_keyword_scopes}")
        return unique_keywords