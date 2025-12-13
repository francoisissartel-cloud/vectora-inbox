"""
Module scorer - Calcul des scores (règles numériques transparentes).

Ce module calcule les scores de pertinence des items matchés en combinant
plusieurs facteurs (event_type, récence, priorité domaine, etc.).
"""

from typing import Any, Dict, List


def score_items(
    matched_items: List[Dict[str, Any]],
    scoring_rules: Dict[str, Any],
    watch_domains: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Calcule le score de chaque item matché.
    
    Args:
        matched_items: Items annotés avec matched_domains
        scoring_rules: Règles de scoring (poids, facteurs)
        watch_domains: Watch_domains du client (pour les priorités)
        canonical_scopes: Scopes canonical (pour les pure players)
    
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
        score = compute_score(item, scoring_rules, domain_priority, canonical_scopes)
        item['score'] = score
        
        logger.debug(f"Item '{item.get('title', '')[:50]}...' : score = {score:.2f}")
    
    return matched_items


def compute_score(item: Dict[str, Any], scoring_rules: Dict[str, Any], domain_priority: str, canonical_scopes: Dict[str, Any]) -> float:
    """
    Calcule le score d'un item selon les règles de scoring.
    
    Args:
        item: Item normalisé et matché
        scoring_rules: Règles de scoring
        domain_priority: Priorité du domaine (high/medium/low)
        canonical_scopes: Scopes canonical (pour les pure players)
    
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
    
    # Facteur 6 : Match confidence multiplier (nouveau)
    matching_details = item.get('matching_details', {})
    match_confidence = matching_details.get('match_confidence', 'medium')
    confidence_multipliers = {
        'high': other_factors.get('match_confidence_multiplier_high', 1.5),
        'medium': other_factors.get('match_confidence_multiplier_medium', 1.2),
        'low': other_factors.get('match_confidence_multiplier_low', 1.0)
    }
    confidence_multiplier = confidence_multipliers.get(match_confidence, 1.0)
    
    # Facteur 7 : Signal quality score (nouveau)
    signal_quality_score = _compute_signal_quality_score(matching_details, other_factors)
    
    # Facteur 8 : Company scope bonus (amélioré)
    company_bonus = _compute_company_scope_bonus(item, canonical_scopes, other_factors, matching_details)
    
    # Facteur 9 : Negative term penalty (nouveau)
    negative_penalty = 0
    if matching_details.get('negative_terms_detected'):
        negative_penalty = other_factors.get('negative_term_penalty', 10)
    
    # Formule de scoring
    base_score = event_weight * priority_weight * recency_factor * source_weight
    final_score = (base_score * confidence_multiplier) + signal_depth_bonus + signal_quality_score + company_bonus - negative_penalty
    
    return max(0, round(final_score, 2))


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


def _compute_signal_quality_score(matching_details: Dict[str, Any], other_factors: Dict[str, Any]) -> float:
    """Calcule le bonus basé sur la qualité des signaux matchés."""
    if not matching_details:
        return 0
    
    signals_used = matching_details.get('signals_used', {})
    high_precision = signals_used.get('high_precision', 0)
    supporting = signals_used.get('supporting', 0)
    
    weight_high = other_factors.get('signal_quality_weight_high_precision', 2.0)
    weight_supporting = other_factors.get('signal_quality_weight_supporting', 1.0)
    
    return (high_precision * weight_high) + (supporting * weight_supporting)


def _compute_company_scope_bonus(item: Dict[str, Any], canonical_scopes: Dict[str, Any], other_factors: Dict[str, Any], matching_details: Dict[str, Any]) -> float:
    """Calcule le bonus basé sur le type de company scope (pure_player vs hybrid)."""
    item_companies = set(item.get('companies_detected', []))
    if not item_companies:
        return 0
    
    # Vérifier company_scope_type depuis matching_details
    scopes_hit = matching_details.get('scopes_hit', {})
    company_scope_type = scopes_hit.get('company_scope_type', 'other')
    
    if company_scope_type == 'pure_player':
        return other_factors.get('pure_player_bonus', 3)
    elif company_scope_type == 'hybrid':
        return other_factors.get('hybrid_company_bonus', 1)
    
    # Fallback: vérifier pure_player_scope (ancien système)
    pure_player_scope_key = other_factors.get('pure_player_scope')
    if pure_player_scope_key:
        pure_players = set(canonical_scopes.get('companies', {}).get(pure_player_scope_key, []))
        if item_companies & pure_players:
            return other_factors.get('pure_player_bonus', 3)
    
    return 0


def rank_items_by_score(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Trie les items par score décroissant.
    
    Args:
        items: Items avec scores
    
    Returns:
        Items triés par score décroissant
    """
    return sorted(items, key=lambda x: x.get('score', 0), reverse=True)
