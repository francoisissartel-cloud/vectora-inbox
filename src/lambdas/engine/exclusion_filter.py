"""
Module de filtrage d'exclusion pour éliminer le bruit HR/finance.

Ce module applique les exclusions définies dans exclusion_scopes.yaml
pour filtrer les items non pertinents avant le matching et scoring.
"""

import yaml
import logging
import re
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def load_exclusion_scopes() -> Dict[str, Any]:
    """
    Charge les exclusion_scopes.yaml depuis le répertoire canonical.
    
    Returns:
        Dictionnaire des scopes d'exclusion
    """
    try:
        with open('canonical/scopes/exclusion_scopes.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load exclusion scopes: {e}")
        return {}


def apply_exclusion_filters(item: Dict[str, Any], exclusion_scopes: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Applique les filtres d'exclusion selon exclusion_scopes.yaml.
    
    Args:
        item: Item normalisé à vérifier
        exclusion_scopes: Scopes d'exclusion chargés
    
    Returns:
        Tuple (is_allowed, reason)
        - is_allowed: True si l'item doit être gardé, False si exclu
        - reason: Raison de l'exclusion ou "Not excluded"
    """
    title_lower = item.get('title', '').lower()
    summary_lower = item.get('summary', '').lower()
    content = f"{title_lower} {summary_lower}"
    
    # Vérifier exclusions HR/recrutement
    hr_terms = exclusion_scopes.get('hr_recruitment_terms', [])
    for term in hr_terms:
        if term.lower() in content:
            logger.info(f"Item excluded by HR term: {term}")
            return False, f"Excluded by HR term: {term}"
    
    # Vérifier exclusions finance/reporting
    finance_terms = exclusion_scopes.get('financial_reporting_terms', [])
    for term in finance_terms:
        # Support des regex patterns pour des termes comme "publishes.*results"
        if '.*' in term:
            pattern = term.lower()
            if re.search(pattern, content):
                logger.info(f"Item excluded by finance pattern: {term}")
                return False, f"Excluded by finance pattern: {term}"
        else:
            if term.lower() in content:
                logger.info(f"Item excluded by finance term: {term}")
                return False, f"Excluded by finance term: {term}"
    
    # Vérifier exclusions anti-LAI (routes orales)
    anti_lai_terms = exclusion_scopes.get('anti_lai_routes', [])
    for term in anti_lai_terms:
        if term.lower() in content:
            logger.info(f"Item excluded by anti-LAI term: {term}")
            return False, f"Excluded by anti-LAI term: {term}"
    
    return True, "Not excluded"


def filter_items_by_exclusions(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtre une liste d'items selon les exclusions.
    
    Args:
        items: Liste d'items normalisés
    
    Returns:
        Liste d'items filtrés (exclusions supprimées)
    """
    exclusion_scopes = load_exclusion_scopes()
    if not exclusion_scopes:
        logger.warning("No exclusion scopes loaded, returning all items")
        return items
    
    filtered_items = []
    excluded_count = 0
    
    for item in items:
        is_allowed, reason = apply_exclusion_filters(item, exclusion_scopes)
        
        if is_allowed:
            filtered_items.append(item)
        else:
            excluded_count += 1
            # Ajouter les métadonnées d'exclusion pour debug
            item['excluded'] = True
            item['exclusion_reason'] = reason
            logger.debug(f"Item excluded: {item.get('title', 'No title')[:50]}... - {reason}")
    
    logger.info(f"Exclusion filter applied: {len(filtered_items)} items kept, {excluded_count} items excluded")
    
    return filtered_items


def get_exclusion_stats(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcule des statistiques sur les exclusions appliquées.
    
    Args:
        items: Liste d'items (incluant les exclus avec metadata)
    
    Returns:
        Dictionnaire de statistiques
    """
    total_items = len(items)
    excluded_items = [item for item in items if item.get('excluded', False)]
    excluded_count = len(excluded_items)
    
    # Compter par type d'exclusion
    exclusion_reasons = {}
    for item in excluded_items:
        reason = item.get('exclusion_reason', 'Unknown')
        exclusion_type = reason.split(':')[0] if ':' in reason else reason
        exclusion_reasons[exclusion_type] = exclusion_reasons.get(exclusion_type, 0) + 1
    
    return {
        'total_items': total_items,
        'excluded_count': excluded_count,
        'kept_count': total_items - excluded_count,
        'exclusion_rate': excluded_count / total_items if total_items > 0 else 0,
        'exclusion_breakdown': exclusion_reasons
    }