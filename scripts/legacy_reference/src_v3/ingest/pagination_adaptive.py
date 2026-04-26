"""
Pagination Adaptative Universelle - Vectora Inbox V3

Ce module calcule automatiquement les limites de pagination optimales
pour toutes les sources selon la période d'ingestion et l'activité de la source.

Principe :
- Classification automatique par source_type + source_key
- Override manuel possible via activity_level
- Adaptation automatique selon la période (7j → 1000j)
- Solution universelle pour toutes les sources
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def get_universal_pagination_config(source_config: Dict[str, Any], period_days: int, canonical_config=None) -> Dict[str, Any]:
    """
    Solution universelle pour toutes les sources - calcule automatiquement
    la pagination optimale selon la période et le type de source
    
    Args:
        source_config: Configuration de la source
        period_days: Période d'ingestion en jours
        canonical_config: Configuration canonical (optionnel, pour classification intelligente)
    
    Returns:
        Configuration de pagination adaptative
    """
    
    # 1. CLASSIFICATION AUTOMATIQUE par type de source
    source_type = source_config.get('source_type', 'unknown')
    source_key = source_config.get('source_key', '')
    
    # Extraire company_id depuis source_key (format: source_type__company_id)
    company_id = None
    if '__' in source_key:
        parts = source_key.split('__')
        if len(parts) >= 2:
            company_id = parts[1]
    
    # Classification automatique par défaut
    if source_type == 'press_corporate':
        if canonical_config and company_id:
            # Utiliser les scopes canonical pour classification intelligente
            company_scopes = canonical_config.company_scopes
            hybrid_companies = company_scopes.get('lai_companies_hybrid', [])
            pure_companies = company_scopes.get('lai_companies_pure_players', [])
            
            if company_id in hybrid_companies:
                default_activity = 'high'    # Hybrid players (Big Pharma) = très actif
            elif company_id in pure_companies:
                default_activity = 'medium'  # Pure players LAI = moyennement actif
            else:
                default_activity = 'low'     # Autres corporate = peu actif
        else:
            # Fallback : classification hardcodée si pas de canonical_config
            if any(x in source_key for x in ['pfizer', 'novartis', 'roche', 'jnj', 'merck', 'abbvie', 'amgen']):
                default_activity = 'high'    # Big Pharma = très actif
            elif any(x in source_key for x in ['medincell', 'camurus', 'alkermes', 'delsitech', 'nanexa']):
                default_activity = 'medium'  # Pure players LAI = moyennement actif
            else:
                default_activity = 'low'     # Autres corporate = peu actif
    
    elif source_type == 'press_sector':
        default_activity = 'high'        # Presse sectorielle = très active
    
    elif source_type in ['api_pubmed', 'api_clinicaltrials', 'api_fda_labels']:
        default_activity = 'medium'      # APIs = moyennement actif
    
    else:
        default_activity = 'medium'      # Défaut sécurisé
    
    # 2. OVERRIDE MANUEL possible
    activity_level = source_config.get('activity_level', default_activity)
    
    # 3. CALCUL ADAPTATIF selon période
    base_pages = _calculate_base_pages(period_days, activity_level)
    
    # 4. RESPECT des limites manuelles si définies (seulement pour runs courts)
    manual_max = source_config.get('pagination', {}).get('max_pages')
    if manual_max and period_days <= 7:
        # En mode court, respecter les limites manuelles si elles sont plus restrictives
        final_max_pages = min(manual_max, base_pages)
        calculation_method = 'manual_limited'
    else:
        # En mode long, utiliser le calcul adaptatif
        final_max_pages = base_pages
        calculation_method = 'adaptive'
    
    return {
        'max_pages': final_max_pages,
        'activity_level': activity_level,
        'period_days': period_days,
        'calculation_method': calculation_method,
        'default_activity': default_activity,
        'manual_override': activity_level != default_activity
    }


def _calculate_base_pages(period_days: int, activity_level: str) -> int:
    """
    Calcul universel des pages selon période et activité
    
    Args:
        period_days: Période d'ingestion en jours
        activity_level: Niveau d'activité ('high', 'medium', 'low')
    
    Returns:
        Nombre maximum de pages à scanner
    """
    
    # Matrice universelle période × activité
    pagination_matrix = {
        # period_days: {activity: max_pages}
        7:    {'high': 2,  'medium': 1,  'low': 1},     # Hebdomadaire
        30:   {'high': 6,  'medium': 4,  'low': 2},     # Mensuel  
        90:   {'high': 12, 'medium': 8,  'low': 4},     # Trimestriel
        200:  {'high': 20, 'medium': 12, 'low': 6},     # Période standard
        365:  {'high': 35, 'medium': 20, 'low': 10},    # Annuel
        1000: {'high': 50, 'medium': 30, 'low': 15},    # Historique complet
    }
    
    # Trouver la période la plus proche
    closest_period = min(pagination_matrix.keys(), 
                        key=lambda x: abs(x - period_days))
    
    base_pages = pagination_matrix[closest_period][activity_level]
    
    logger.debug(f"Period {period_days}d → closest {closest_period}d, "
                f"activity {activity_level} → {base_pages} pages")
    
    return base_pages


def test_pagination_scenarios():
    """Test des différents scénarios de pagination"""
    
    # Sources de test
    test_sources = [
        {
            'source_key': 'press_corporate__pfizer',
            'source_type': 'press_corporate',
            'pagination': {'max_pages': 1}  # Ancienne limite
        },
        {
            'source_key': 'press_corporate__medincell', 
            'source_type': 'press_corporate'
        },
        {
            'source_key': 'press_sector__fiercebiotech',
            'source_type': 'press_sector'
        },
        {
            'source_key': 'science_pubmed_api',
            'source_type': 'api_pubmed'
        },
        {
            'source_key': 'press_corporate__unknown_company',
            'source_type': 'press_corporate'
        }
    ]
    
    # Périodes de test
    test_periods = [7, 30, 200, 1000]
    
    print("=== TEST PAGINATION ADAPTATIVE UNIVERSELLE ===\n")
    
    for period in test_periods:
        print(f"PERIODE: {period} jours")
        print("-" * 50)
        
        for source in test_sources:
            config = get_universal_pagination_config(source, period)
            
            print(f"  {source['source_key'][:30]:<30} -> "
                  f"{config['max_pages']:2d} pages "
                  f"(activity={config['activity_level']}, "
                  f"method={config['calculation_method']})")
        
        print()


if __name__ == "__main__":
    test_pagination_scenarios()