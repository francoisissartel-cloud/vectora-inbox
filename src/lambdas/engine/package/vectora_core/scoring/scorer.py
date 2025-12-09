"""
Module scorer - Calcul des scores (règles numériques transparentes).

Ce module calcule les scores de pertinence des items matchés en combinant
plusieurs facteurs (event_type, récence, priorité domaine, etc.).
"""

from typing import Any, Dict, List


def score_items(
    matched_items: List[Dict[str, Any]],
    scoring_rules: Dict[str, Any],
    watch_domains: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Calcule le score de chaque item matché.
    
    Args:
        matched_items: Items annotés avec matched_domains
        scoring_rules: Règles de scoring (poids, facteurs)
        watch_domains: Watch_domains du client (pour les priorités)
    
    Returns:
        Items annotés avec le champ score (float)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Créer un mapping domain_id → priority
    domain_priorities = {d.get('id'): d.get('priority', 'medium') for d in watch_domains}
    
    for item in matched_items:
        # Déterminer la priorité maximale parmi les domaines matchés
        matched_domains = item.get('matched_domains', [])
        if matched_domains:
            priorities = [domain_priorities.get(d, 'medium') for d in matched_domains]
            # Prendre la priorité la plus élevée
            if 'high' in priorities:
                domain_priority = 'high'
            elif 'medium' in priorities:
                domain_priority = 'medium'
            else:
                domain_priority = 'low'
        else:
            domain_priority = 'low'
        
        # Calculer le score
        score = compute_score(item, scoring_rules, domain_priority)
        item['score'] = score
        
        logger.debug(f"Item '{item.get('title', '')[:50]}...' : score = {score:.2f}")
    
    return matched_items


def compute_score(item: Dict[str, Any], scoring_rules: Dict[str, Any], domain_priority: str) -> float:
    """
    Calcule le score d'un item selon les règles de scoring.
    
    Args:
        item: Item normalisé et matché
        scoring_rules: Règles de scoring
        domain_priority: Priorité du domaine (high/medium/low)
    
    Returns:
        Score numérique (float)
    """
    from datetime import datetime, timedelta
    import math
    
    # Extraire les poids depuis les règles
    event_type_weights = scoring_rules.get('event_type_weights', {})
    domain_priority_weights = scoring_rules.get('domain_priority_weights', {})
    other_factors = scoring_rules.get('other_factors', {})
    
    # Facteur 1 : Importance de l'event_type
    event_type = item.get('event_type', 'other')
    event_weight = event_type_weights.get(event_type, 1)
    
    # Facteur 2 : Priorité du domaine
    priority_weight = domain_priority_weights.get(domain_priority, 1)
    
    # Facteur 3 : Récence (décroissance exponentielle)
    recency_factor = _compute_recency_factor(
        item.get('date'),
        other_factors.get('recency_decay_half_life_days', 7)
    )
    
    # Facteur 4 : Type de source
    source_type = item.get('source_type', 'generic')
    if 'corporate' in source_type:
        source_weight = other_factors.get('source_type_weight_corporate', 2)
    elif 'sector' in source_type:
        source_weight = other_factors.get('source_type_weight_sector', 1.5)
    else:
        source_weight = other_factors.get('source_type_weight_generic', 1)
    
    # Facteur 5 : Profondeur du signal (nombre d'entités détectées)
    num_entities = (
        len(item.get('companies_detected', [])) +
        len(item.get('molecules_detected', [])) +
        len(item.get('technologies_detected', [])) +
        len(item.get('indications_detected', []))
    )
    signal_depth_bonus = max(0, num_entities - 1) * other_factors.get('signal_depth_bonus', 0.3)
    
    # Formule de scoring
    base_score = event_weight * priority_weight * recency_factor * source_weight
    final_score = base_score + signal_depth_bonus
    
    return round(final_score, 2)


def _compute_recency_factor(item_date: str, half_life_days: int) -> float:
    """
    Calcule le facteur de récence avec décroissance exponentielle.
    
    Args:
        item_date: Date de l'item (ISO8601)
        half_life_days: Demi-vie en jours
    
    Returns:
        Facteur de récence (1.0 pour aujourd'hui, 0.5 après half_life_days)
    """
    from datetime import datetime
    import math
    
    if not item_date:
        return 0.5  # Valeur par défaut si date manquante
    
    try:
        # Parser la date de l'item
        if 'T' in item_date:
            item_dt = datetime.fromisoformat(item_date.replace('Z', '+00:00'))
        else:
            item_dt = datetime.strptime(item_date, '%Y-%m-%d')
        
        # Calculer l'ancienneté en jours
        now = datetime.now()
        age_days = (now - item_dt.replace(tzinfo=None)).days
        
        # Décroissance exponentielle : factor = 2^(-age_days / half_life_days)
        recency_factor = math.pow(2, -age_days / half_life_days)
        
        return max(0.1, min(1.0, recency_factor))  # Borner entre 0.1 et 1.0
    
    except Exception:
        return 0.5  # Valeur par défaut en cas d'erreur


def rank_items_by_score(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Trie les items par score décroissant.
    
    Args:
        items: Items avec scores
    
    Returns:
        Items triés par score décroissant
    """
    return sorted(items, key=lambda x: x.get('score', 0), reverse=True)
