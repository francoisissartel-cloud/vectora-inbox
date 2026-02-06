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
logger.setLevel(logging.DEBUG)  # Force DEBUG pour ce module

# Variables globales pour scopes chargés depuis S3
_exclusion_scopes_cache = None
_pure_players_cache = None
_lai_keywords_cache = None

def initialize_exclusion_scopes(s3_io, config_bucket: str):
    """Charge les exclusion_scopes depuis S3 (appelé au démarrage)."""
    global _exclusion_scopes_cache
    
    scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/exclusion_scopes.yaml')
    _exclusion_scopes_cache = scopes or {}
    logger.info(f"[INIT] Exclusion scopes chargés: {len(_exclusion_scopes_cache)} catégories")
    logger.info(f"[INIT] Catégories: {list(_exclusion_scopes_cache.keys())}")
    
    if not _exclusion_scopes_cache:
        raise RuntimeError("Exclusion scopes vide après chargement S3")

def initialize_lai_keywords(s3_io, config_bucket: str):
    """Charge les LAI keywords depuis S3 (appelé au démarrage)."""
    global _lai_keywords_cache
    
    scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/lai_keywords.yaml')
    keywords = scopes.get('lai_keywords', [])
    _lai_keywords_cache = [kw.lower() for kw in keywords]
    logger.info(f"[INIT] LAI keywords chargés: {len(_lai_keywords_cache)} keywords")
    
    if not _lai_keywords_cache:
        raise RuntimeError("LAI keywords vide après chargement S3")

def initialize_pure_players(s3_io, config_bucket: str):
    """Charge les pure players depuis S3 (appelé au démarrage)."""
    global _pure_players_cache
    
    scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/company_scopes.yaml')
    pure_players = scopes.get('lai_companies_pure_players', [])
    _pure_players_cache = [company.lower() for company in pure_players]
    logger.info(f"[INIT] Pure players chargés: {len(_pure_players_cache)} entreprises")
    
    if not _pure_players_cache:
        raise RuntimeError("Pure players vide après chargement S3")

def _get_exclusion_terms() -> List[str]:
    """Retourne la liste combinée des termes d'exclusion depuis S3."""
    if not _exclusion_scopes_cache:
        logger.error("ERREUR: exclusion_scopes non chargé depuis S3")
        raise RuntimeError("Exclusion scopes non initialisés")
    
    # Lire TOUS les scopes (sauf métadonnées)
    terms = []
    excluded_keys = ['exclude_contexts', 'lai_exclusion_scopes', 'lai_exclude_noise']
    for scope_name, scope_terms in _exclusion_scopes_cache.items():
        if scope_name not in excluded_keys and isinstance(scope_terms, list):
            terms.extend(scope_terms)
            logger.debug(f"[EXCLUSION] Scope '{scope_name}': {len(scope_terms)} termes")
    
    if not terms:
        logger.error("ERREUR: Aucun terme d'exclusion trouvé dans S3")
        raise RuntimeError("Exclusion scopes vides")
    
    logger.debug(f"[EXCLUSION] Total termes combinés: {len(terms)}")
    return terms



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
    Applique le profil corporate_pure_player_broad.
    Ingestion large avec exclusion du bruit évident.
    """
    source_key = source_meta.get('source_key', '')
    company_id = source_meta.get('company_id', '')
    
    # Vérifier si c'est un pure player LAI
    if not _pure_players_cache:
        raise RuntimeError("Pure players non initialisés")
    is_lai_pure_player = company_id.lower() in _pure_players_cache
    
    if is_lai_pure_player:
        logger.info(f"Pure player LAI détecté : {company_id} - ingestion large avec exclusions minimales")
        filtered_items = []
        excluded_count = 0
        
        for item in items:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            text = f"{title} {content}"
            
            logger.debug(f"[PROFIL] Analyse item: '{title[:80]}...'")
            
            # Exclure le bruit évident - FILTRAGE ACTIF
            if _contains_exclusion_keywords(text):
                logger.info(f"[PROFIL] ❌ Item corporate EXCLU (bruit) : {item.get('title', '')[:80]}")
                excluded_count += 1
                continue
            
            logger.debug(f"[PROFIL] ✅ Item corporate CONSERVÉ : {item.get('title', '')[:80]}")
            filtered_items.append(item)
        
        logger.info(f"Profil corporate LAI : {len(filtered_items)}/{len(items)} items conservés, {excluded_count} exclus")
        return filtered_items
    else:
        # Entreprise non-LAI : filtrage plus strict
        logger.info(f"Entreprise non-LAI : {company_id} - filtrage par mots-clés LAI")
        return _filter_by_lai_keywords(items, source_key)


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
    filtered_items = []
    
    for item in items:
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        text = f"{title} {content}"
        
        # Exclure d'abord le bruit évident
        if _contains_exclusion_keywords(text):
            logger.debug(f"Item exclu (bruit) : {item.get('title', '')[:50]}...")
            continue
        
        # Vérifier la présence de mots-clés LAI
        if _contains_lai_keywords(text):
            filtered_items.append(item)
            logger.debug(f"Item conservé (mots-clés LAI) : {item.get('title', '')[:50]}...")
        else:
            logger.debug(f"Item exclu (pas de mots-clés LAI) : {item.get('title', '')[:50]}...")
    
    logger.info(f"Filtrage LAI pour {source_key} : {len(filtered_items)}/{len(items)} items conservés")
    return filtered_items


def _contains_lai_keywords(text: str) -> bool:
    """
    Vérifie si le texte contient des mots-clés LAI.
    """
    if not _lai_keywords_cache:
        raise RuntimeError("LAI keywords non initialisés")
    
    text_lower = text.lower()
    
    for keyword in _lai_keywords_cache:
        if keyword in text_lower:
            return True
    
    return False


def _contains_exclusion_keywords(text: str) -> bool:
    """
    Vérifie si le texte contient des mots-clés d'exclusion (depuis S3 ou fallback).
    """
    text_lower = text.lower()
    exclusion_terms = _get_exclusion_terms()
    
    logger.info(f"[FILTRAGE] Vérification exclusion - Texte: {text_lower[:100]}...")
    logger.info(f"[FILTRAGE] Nombre termes: {len(exclusion_terms)}")
    logger.info(f"[FILTRAGE] Premiers 10 termes: {exclusion_terms[:10]}")
    
    for keyword in exclusion_terms:
        if keyword.lower() in text_lower:
            logger.info(f"[FILTRAGE] MATCH: '{keyword}' trouvé")
            return True
    
    logger.info(f"[FILTRAGE] Aucun match")
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