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

def initialize_exclusion_scopes(s3_io, config_bucket: str):
    """Charge les exclusion_scopes depuis S3 (appelé au démarrage)."""
    global _exclusion_scopes_cache
    
    try:
        scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/exclusion_scopes.yaml')
        _exclusion_scopes_cache = scopes or {}
        logger.info(f"Exclusion scopes chargés: {len(_exclusion_scopes_cache)} catégories")
    except Exception as e:
        logger.warning(f"Échec chargement exclusion_scopes: {e}. Utilisation fallback.")
        _exclusion_scopes_cache = {}

def _get_exclusion_terms() -> List[str]:
    """Retourne la liste combinée des termes d'exclusion depuis S3."""
    if not _exclusion_scopes_cache:
        # Fallback sur keywords hardcodés
        return EXCLUSION_KEYWORDS
    
    # Combiner hr_content, financial_generic, hr_recruitment_terms, financial_reporting_terms
    terms = []
    for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
        scope_terms = _exclusion_scopes_cache.get(scope_name, [])
        terms.extend(scope_terms)
    
    return terms if terms else EXCLUSION_KEYWORDS

# Mots-clés LAI pour filtrage de la presse
LAI_KEYWORDS = [
    # Technologies LAI
    "injectable", "injection", "long-acting", "extended-release", "depot", 
    "sustained-release", "controlled-release", "implant", "microsphere",
    "LAI", "long acting injectable", "once-monthly", "once-weekly",
    
    # Entreprises LAI
    "medincell", "camurus", "delsitech", "nanexa", "peptron", "teva",
    "uzedy", "bydureon", "invega", "risperdal", "abilify maintena",
    
    # Molécules LAI
    "olanzapine", "risperidone", "paliperidone", "aripiprazole", 
    "haloperidol", "fluphenazine", "exenatide", "naltrexone",
    
    # Routes d'administration
    "intramuscular", "subcutaneous", "im injection", "sc injection"
]

# Mots-clés d'exclusion (bruit)
EXCLUSION_KEYWORDS = [
    # RH et recrutement
    "hiring", "recruitment", "job opening", "career", "seeks an experienced",
    "is hiring", "appointment of", "leadership change", "joins as",
    
    # Événements corporate génériques
    "conference", "webinar", "presentation", "meeting", "congress",
    "summit", "symposium", "event", "participate in", "to present at",
    
    # Routes non-LAI
    "oral", "tablet", "capsule", "pill", "topical", "nasal spray",
    "eye drops", "cream", "gel", "patch"
]


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
    lai_pure_players = ['medincell', 'camurus', 'delsitech', 'nanexa', 'peptron']
    is_lai_pure_player = company_id.lower() in lai_pure_players
    
    if is_lai_pure_player:
        logger.info(f"Pure player LAI détecté : {company_id} - ingestion large avec exclusions minimales")
        filtered_items = []
        
        for item in items:
            title = item.get('title', '').lower()
            content = item.get('content', '').lower()
            text = f"{title} {content}"
            
            # Exclure le bruit évident
            if _contains_exclusion_keywords(text):
                logger.debug(f"Item corporate exclu (bruit) : {item.get('title', '')[:50]}...")
                continue
            
            filtered_items.append(item)
        
        logger.info(f"Profil corporate LAI : {len(filtered_items)}/{len(items)} items conservés")
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
    text_lower = text.lower()
    
    for keyword in LAI_KEYWORDS:
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