"""
Profils d'ingestion pour Vectora Inbox V2.

Ce module implémente la logique des profils d'ingestion définis dans canonical.
Il permet de différencier le traitement entre sources corporate et presse.

Responsabilités :
- Appliquer les profils d'ingestion selon le type de source
- Filtrer la presse sectorielle par mots-clés LAI
- Ingestion large pour les pure players LAI
- Exclusion du bruit (RH, événements génériques)
"""

from typing import Any, Dict, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

# Variables globales pour scopes chargés depuis S3
_exclusion_scopes_cache = None
_pure_players_cache = None
_hybrid_players_cache = None
_lai_keywords_cache = None

def initialize_exclusion_scopes(s3_io, config_bucket: str):
    """Charge les exclusion_scopes depuis S3 (appelé au démarrage)."""
    global _exclusion_scopes_cache
    
    try:
        scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/exclusion_scopes.yaml')
        _exclusion_scopes_cache = scopes or {}
        logger.info(f"Exclusion scopes chargés: {len(_exclusion_scopes_cache)} catégories")
        
        # Log détaillé des scopes chargés
        for scope_name, scope_terms in _exclusion_scopes_cache.items():
            if isinstance(scope_terms, list):
                logger.debug(f"Scope '{scope_name}': {len(scope_terms)} termes")
    except Exception as e:
        logger.error(f"Échec chargement exclusion_scopes: {e}")
        raise RuntimeError(f"Impossible de charger exclusion_scopes depuis S3: {e}")

def initialize_company_scopes(s3_io, config_bucket: str):
    """Charge les company scopes depuis S3 (appelé au démarrage)."""
    global _pure_players_cache, _hybrid_players_cache
    
    try:
        scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/company_scopes.yaml')
        
        pure_players = scopes.get('lai_companies_pure_players', [])
        _pure_players_cache = [company.lower() for company in pure_players]
        
        hybrid_players = scopes.get('lai_companies_hybrid', [])
        _hybrid_players_cache = [company.lower() for company in hybrid_players]
        
        logger.info(f"Company scopes: {len(_pure_players_cache)} pure players, {len(_hybrid_players_cache)} hybrid players")
    except Exception as e:
        logger.error(f"Échec chargement company_scopes: {e}")
        raise RuntimeError(f"Impossible de charger company_scopes depuis S3: {e}")

def initialize_lai_keywords(s3_io, config_bucket: str):
    """Charge les LAI keywords depuis S3 (appelé au démarrage)."""
    global _lai_keywords_cache
    
    try:
        # Charger technology_scopes.yaml et trademark_scopes.yaml
        tech_scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/technology_scopes.yaml')
        trademark_scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/trademark_scopes.yaml')
        
        keywords = []
        # Ajouter core_phrases, technology_terms_high_precision, interval_patterns
        lai_keywords_section = tech_scopes.get('lai_keywords', {})
        for scope in ['core_phrases', 'technology_terms_high_precision', 'interval_patterns']:
            keywords.extend(lai_keywords_section.get(scope, []))
        
        # Ajouter trademarks
        keywords.extend(trademark_scopes.get('lai_trademarks_global', []))
        
        _lai_keywords_cache = keywords
        logger.info(f"LAI keywords: {len(_lai_keywords_cache)} termes chargés")
    except Exception as e:
        logger.error(f"Échec chargement LAI keywords: {e}")
        raise RuntimeError(f"Impossible de charger LAI keywords depuis S3: {e}")

def _get_exclusion_terms() -> List[str]:
    """Retourne la liste combinée des termes d'exclusion depuis S3."""
    if not _exclusion_scopes_cache:
        raise RuntimeError("Exclusion scopes non initialisés")
    
    # Combiner tous les scopes d'exclusion pertinents
    terms = []
    for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms', 
                       'esg_generic', 'event_generic', 'corporate_noise_terms', 'anti_lai_routes']:
        scope_terms = _exclusion_scopes_cache.get(scope_name, [])
        if isinstance(scope_terms, list):
            terms.extend(scope_terms)
    
    return terms

def _is_pure_player(company_id: str) -> bool:
    """Vérifie si l'entreprise est un pure player LAI."""
    if not _pure_players_cache:
        raise RuntimeError("Company scopes non initialisés")
    return company_id.lower() in _pure_players_cache

def _is_hybrid_player(company_id: str) -> bool:
    """Vérifie si l'entreprise est un hybrid player."""
    if not _hybrid_players_cache:
        raise RuntimeError("Company scopes non initialisés")
    return company_id.lower() in _hybrid_players_cache


def apply_ingestion_profile(items: List[Dict[str, Any]], source_meta: Dict[str, Any], ingestion_mode: str = "balanced") -> List[Dict[str, Any]]:
    """
    Applique le profil d'ingestion approprié selon le type de source.
    
    Args:
        items: Liste d'items bruts à filtrer
        source_meta: Métadonnées de la source (source_key, source_type, etc.)
    
    Returns:
        Liste d'items filtrés selon le profil
    """
    if not items:
        return []
    
    source_type = source_meta.get('source_type', '')
    source_key = source_meta.get('source_key', '')
    
    logger.info(f"Application du profil d'ingestion pour {source_key} (type: {source_type}, mode: {ingestion_mode})")
    
    if ingestion_mode == "broad":
        # Mode broad : ingestion large pour tous types
        logger.info(f"Mode broad : ingestion large pour {source_key}")
        return items
    elif ingestion_mode == "strict":
        # Mode strict : filtrage maximal pour tous types
        logger.info(f"Mode strict : filtrage maximal pour {source_key}")
        return _filter_by_lai_keywords(items, source_key)
    else:  # balanced
        # Mode balanced : profils différenciés par type
        if source_type == 'press_corporate':
            return _apply_corporate_profile(items, source_meta)
        elif source_type == 'press_sector':
            return _apply_press_profile(items, source_meta)
        else:
            # Profil par défaut : ingestion large
            logger.info(f"Profil par défaut appliqué pour {source_key}")
            return items


def _apply_corporate_profile(items: List[Dict[str, Any]], source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Applique le profil corporate avec différenciation pure/hybrid players.
    """
    source_key = source_meta.get('source_key', '')
    company_id = source_meta.get('company_id', '')
    
    # Vérifier type d'entreprise
    is_pure = _is_pure_player(company_id)
    is_hybrid = _is_hybrid_player(company_id)
    
    if is_pure:
        logger.info(f"Pure player: {company_id} - exclusions seules (pas de filtrage LAI)")
        return _filter_by_exclusions_only(items, source_key)
    
    elif is_hybrid:
        logger.info(f"Hybrid player: {company_id} - exclusions + LAI keywords requis")
        return _filter_by_exclusions_and_lai(items, source_key)
    
    else:
        logger.info(f"Entreprise inconnue: {company_id} - filtrage strict")
        return _filter_by_exclusions_and_lai(items, source_key)

def _filter_by_exclusions_only(items: List[Dict[str, Any]], source_key: str) -> List[Dict[str, Any]]:
    """Filtre uniquement par exclusions (pour pure players)."""
    filtered = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('content', '')}".lower()
        if not _contains_exclusion_keywords(text):
            filtered.append(item)
    logger.info(f"{source_key}: {len(filtered)}/{len(items)} items (exclusions seules)")
    return filtered

def _filter_by_exclusions_and_lai(items: List[Dict[str, Any]], source_key: str) -> List[Dict[str, Any]]:
    """Filtre par exclusions ET LAI keywords (pour hybrid players et inconnus)."""
    filtered = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('content', '')}".lower()
        if not _contains_exclusion_keywords(text) and _contains_lai_keywords(text):
            filtered.append(item)
    logger.info(f"{source_key}: {len(filtered)}/{len(items)} items (exclusions + LAI)")
    return filtered


def _apply_press_profile(items: List[Dict[str, Any]], source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Applique le profil press_technology_focused.
    Filtrage strict par mots-clés LAI pour réduire le bruit.
    """
    source_key = source_meta.get('source_key', '')
    logger.info(f"Profil presse sectorielle : filtrage par mots-clés LAI")
    
    return _filter_by_lai_keywords(items, source_key)


def _filter_by_lai_keywords(items: List[Dict[str, Any]], source_key: str) -> List[Dict[str, Any]]:
    """
    Filtre les items par présence de mots-clés LAI.
    """
    return _filter_by_exclusions_and_lai(items, source_key)


def _contains_lai_keywords(text: str) -> bool:
    """
    Vérifie si le texte contient des mots-clés LAI.
    """
    if not _lai_keywords_cache:
        raise RuntimeError("LAI keywords non initialisés")
    
    text_lower = text.lower()
    for keyword in _lai_keywords_cache:
        if keyword.lower() in text_lower:
            return True
    
    return False


def _contains_exclusion_keywords(text: str) -> bool:
    """
    Vérifie si le texte contient des mots-clés d'exclusion (depuis S3 ou fallback).
    """
    text_lower = text.lower()
    exclusion_terms = _get_exclusion_terms()
    
    for keyword in exclusion_terms:
        if keyword.lower() in text_lower:
            logger.debug(f"Exclusion détectée: '{keyword}' dans texte")
            return True
    
    return False


def get_profile_stats(items_before: int, items_after: int, source_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule les statistiques d'application du profil.
    """
    source_key = source_meta.get('source_key', '')
    source_type = source_meta.get('source_type', '')
    
    filtered_out = items_before - items_after
    retention_rate = (items_after / items_before * 100) if items_before > 0 else 0
    
    return {
        'source_key': source_key,
        'source_type': source_type,
        'items_before': items_before,
        'items_after': items_after,
        'items_filtered_out': filtered_out,
        'retention_rate': round(retention_rate, 1)
    }