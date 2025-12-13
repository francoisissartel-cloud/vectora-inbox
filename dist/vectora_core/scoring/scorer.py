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
    canonical_scopes: Dict[str, Any],
    use_domain_relevance: bool = True
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
        if use_domain_relevance and item.get('domain_relevance'):
            # Nouveau système : utiliser domain_relevance
            score = compute_score_with_domain_relevance(item, scoring_rules, canonical_scopes)
        else:
            # Ancien système : utiliser matched_domains
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
    
    # PHASE 4: Appliquer le scoring contextuel si disponible
    contextual_score_bonus = 0
    if scoring_rules.get('contextual_scoring'):
        contextual_score_bonus = compute_contextual_score(item, scoring_rules, canonical_scopes) * 0.3  # Facteur d'ajustement
    
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


def compute_score_with_domain_relevance(item: Dict[str, Any], scoring_rules: Dict[str, Any], canonical_scopes: Dict[str, Any]) -> float:
    """
    Calcule le score d'un item en utilisant les évaluations domain_relevance de Bedrock.
    
    Args:
        item: Item normalisé avec domain_relevance
        scoring_rules: Règles de scoring
        canonical_scopes: Scopes canonical
    
    Returns:
        Score numérique (float)
    """
    from datetime import datetime, timedelta
    import math
    
    # Extraire les poids depuis les règles
    event_type_weights = scoring_rules.get('event_type_weights', {})
    other_factors = scoring_rules.get('other_factors', {})
    
    # Facteur 1 : Importance de l'event_type
    event_type = item.get('event_type', 'other')
    event_weight = event_type_weights.get(event_type, 1)
    
    # Facteur 2 : Domain relevance (nouveau signal principal)
    domain_relevance_score = _compute_domain_relevance_score(item.get('domain_relevance', []), other_factors)
    
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
    
    # Facteur 6 : Company scope bonus (conservé)
    company_bonus = _compute_company_scope_bonus_from_entities(item, canonical_scopes, other_factors)
    
    # Facteur 7 : Trademark bonus (nouveau)
    trademark_bonus = _compute_trademark_bonus(item, canonical_scopes, other_factors)
    
    # Formule de scoring adaptée
    base_score = event_weight * domain_relevance_score * recency_factor * source_weight
    final_score = base_score + signal_depth_bonus + company_bonus + trademark_bonus
    
    return max(0, round(final_score, 2))


def _compute_domain_relevance_score(domain_relevance: List[Dict[str, Any]], other_factors: Dict[str, Any]) -> float:
    """
    Calcule le score de pertinence basé sur les évaluations domain_relevance de Bedrock.
    
    Args:
        domain_relevance: Liste des évaluations de domaines
        other_factors: Facteurs de scoring
    
    Returns:
        Score de pertinence (float)
    """
    if not domain_relevance:
        return other_factors.get('no_domain_relevance_penalty', 0.1)
    
    # Prendre le meilleur score de pertinence parmi tous les domaines
    max_relevance = 0
    high_priority_bonus = 0
    
    for domain_eval in domain_relevance:
        if domain_eval.get('is_on_domain', False):
            relevance_score = domain_eval.get('relevance_score', 0)
            max_relevance = max(max_relevance, relevance_score)
            
            # Bonus pour les domaines high priority (à implémenter si nécessaire)
            # if domain_eval.get('priority') == 'high':
            #     high_priority_bonus += 0.2
    
    # Convertir le score 0-1 en multiplicateur 0.1-3.0
    if max_relevance > 0:
        domain_multiplier = 0.5 + (max_relevance * 2.5)  # 0.5 à 3.0
    else:
        domain_multiplier = other_factors.get('no_relevant_domain_penalty', 0.2)
    
    return domain_multiplier + high_priority_bonus


def _compute_company_scope_bonus_from_entities(item: Dict[str, Any], canonical_scopes: Dict[str, Any], other_factors: Dict[str, Any]) -> float:
    """
    Calcule le bonus basé sur les entités companies détectées (version simplifiée).
    """
    item_companies = set(item.get('companies_detected', []))
    if not item_companies:
        return 0
    
    # Vérifier pure players
    pure_player_scope_key = other_factors.get('pure_player_scope')
    if pure_player_scope_key:
        pure_players = set(canonical_scopes.get('companies', {}).get(pure_player_scope_key, []))
        if item_companies & pure_players:
            return other_factors.get('pure_player_bonus', 3)
    
    # Vérifier hybrid companies (nouveau)
    hybrid_scope_key = other_factors.get('hybrid_company_scope', 'lai_companies_hybrid')
    hybrid_companies = set(canonical_scopes.get('companies', {}).get(hybrid_scope_key, []))
    if item_companies & hybrid_companies:
        return other_factors.get('hybrid_company_bonus', 1)
    
    return 0


def _compute_trademark_bonus(item: Dict[str, Any], canonical_scopes: Dict[str, Any], other_factors: Dict[str, Any]) -> float:
    """
    Calcule le bonus basé sur les trademarks détectées.
    """
    # À implémenter si des trademarks sont détectées dans la normalisation
    trademarks_detected = item.get('trademarks_detected', [])
    if trademarks_detected:
        return len(trademarks_detected) * other_factors.get('trademark_bonus', 0.5)
    return 0


def compute_contextual_score(
    item: Dict[str, Any], 
    scoring_rules: Dict[str, Any], 
    canonical_scopes: Dict[str, Any]
) -> float:
    """
    Calcule le score contextuel selon le plan d'amélioration Phase 4.
    Scoring multi-dimensionnel adapté au type de company.
    
    Args:
        item: Item normalisé et matché
        scoring_rules: Règles de scoring
        canonical_scopes: Scopes canonical
    
    Returns:
        Score contextuel (float)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Déterminer le type de company
    companies_detected = set(item.get('companies_detected', []))
    company_type = _determine_company_type_for_scoring(companies_detected, canonical_scopes)
    
    # Extraire les informations contextuelles
    event_type = item.get('event_type', 'other')
    technologies_detected = set(item.get('technologies_detected', []))
    molecules_detected = set(item.get('molecules_detected', []))
    trademarks_detected = set(item.get('trademarks_detected', []))
    
    lai_relevance_score = item.get('lai_relevance_score', 0)
    anti_lai_detected = item.get('anti_lai_detected', False)
    
    # Règles de scoring contextuel
    contextual_scoring = scoring_rules.get('contextual_scoring', {})
    contextual_penalties = scoring_rules.get('contextual_penalties', {})
    
    # Score de base selon le type de company
    if company_type == 'pure_player':
        base_bonus = contextual_scoring.get('pure_players', {}).get('base_bonus', 2.0)
        context_multipliers = contextual_scoring.get('pure_players', {}).get('context_multipliers', {})
        
        # Multipliers contextuels pour pure players
        context_multiplier = 1.0
        if event_type == 'regulatory':
            context_multiplier = context_multipliers.get('regulatory_milestone', 3.0)
        elif event_type == 'partnership':
            context_multiplier = context_multipliers.get('partnership_bigpharma', 2.5)
        elif 'grant' in item.get('title', '').lower() or 'funding' in item.get('title', '').lower():
            context_multiplier = context_multipliers.get('grant_funding', 2.0)
        elif event_type == 'clinical_update':
            context_multiplier = context_multipliers.get('clinical_update', 2.0)
        
        base_score = base_bonus * context_multiplier
        
    elif company_type == 'hybrid':
        base_bonus = contextual_scoring.get('hybrid_companies', {}).get('base_bonus', 1.0)
        require_explicit_lai = contextual_scoring.get('hybrid_companies', {}).get('require_explicit_lai', True)
        
        # Pour hybrid companies, signaux LAI explicites requis
        if require_explicit_lai and not (technologies_detected or molecules_detected or trademarks_detected):
            logger.info(f"[CONTEXTUAL_SCORING] Hybrid company sans signaux LAI explicites - score réduit")
            base_score = base_bonus * 0.3  # Score très réduit
        else:
            base_score = base_bonus
    
    else:
        # Unknown companies
        base_bonus = contextual_scoring.get('unknown_companies', {}).get('base_bonus', 0.5)
        require_strong_lai = contextual_scoring.get('unknown_companies', {}).get('require_strong_lai', True)
        
        if require_strong_lai and lai_relevance_score < 7:
            logger.info(f"[CONTEXTUAL_SCORING] Unknown company sans signaux LAI forts - score très réduit")
            base_score = base_bonus * 0.2
        else:
            base_score = base_bonus
    
    # Appliquer les pénalités contextuelles
    penalties = 0
    
    # Pénalité contenu HR
    if _is_hr_content(item):
        penalties += contextual_penalties.get('hr_content', -5.0)
        logger.info(f"[CONTEXTUAL_SCORING] Pénalité HR appliquée")
    
    # Pénalité contenu financier uniquement
    if _is_financial_only_content(item):
        penalties += contextual_penalties.get('financial_only', -3.0)
        logger.info(f"[CONTEXTUAL_SCORING] Pénalité financial-only appliquée")
    
    # Pénalité anti-LAI
    if anti_lai_detected:
        penalties += contextual_penalties.get('anti_lai_route', -10.0)
        logger.info(f"[CONTEXTUAL_SCORING] Pénalité anti-LAI appliquée")
    
    # Bonus récence pour signaux forts
    recency_bonus = _compute_recency_bonus(item, event_type, scoring_rules)
    
    final_score = base_score + penalties + recency_bonus
    
    logger.info(f"[CONTEXTUAL_SCORING] Company: {company_type}, Event: {event_type}, Base: {base_score}, Penalties: {penalties}, Recency: {recency_bonus}, Final: {final_score}")
    
    return max(0, round(final_score, 2))


def _determine_company_type_for_scoring(companies_detected: set, canonical_scopes: Dict[str, Any]) -> str:
    """
    Détermine le type de company pour le scoring contextuel.
    
    Args:
        companies_detected: Set des companies détectées
        canonical_scopes: Scopes canonical
    
    Returns:
        'pure_player', 'hybrid', ou 'unknown'
    """
    if not companies_detected:
        return 'unknown'
    
    # Vérifier pure players
    pure_player_scopes = ['lai_companies_pure_players', 'lai_companies_mvp_core']
    for scope_key in pure_player_scopes:
        pure_players = set(canonical_scopes.get('companies', {}).get(scope_key, []))
        if companies_detected & pure_players:
            return 'pure_player'
    
    # Vérifier hybrid
    hybrid_companies = set(canonical_scopes.get('companies', {}).get('lai_companies_hybrid', []))
    if companies_detected & hybrid_companies:
        return 'hybrid'
    
    return 'unknown'


def _is_hr_content(item: Dict[str, Any]) -> bool:
    """
    Détermine si l'item est du contenu RH.
    """
    title = item.get('title', '').lower()
    content = item.get('content', '').lower()
    
    hr_keywords = ['hiring', 'seeks', 'recruiting', 'process engineer', 'quality director', 'job opening']
    
    for keyword in hr_keywords:
        if keyword in title or keyword in content:
            return True
    
    return False


def _is_financial_only_content(item: Dict[str, Any]) -> bool:
    """
    Détermine si l'item est uniquement du contenu financier.
    """
    title = item.get('title', '').lower()
    content = item.get('content', '').lower()
    
    financial_keywords = ['financial results', 'quarterly results', 'interim report', 'earnings']
    
    # Vérifier si c'est du contenu financier
    is_financial = any(keyword in title or keyword in content for keyword in financial_keywords)
    
    # Vérifier s'il y a des signaux LAI
    has_lai_signals = bool(
        item.get('technologies_detected') or 
        item.get('molecules_detected') or 
        item.get('trademarks_detected')
    )
    
    return is_financial and not has_lai_signals


def _compute_recency_bonus(item: Dict[str, Any], event_type: str, scoring_rules: Dict[str, Any]) -> float:
    """
    Calcule le bonus de récence pour signaux forts.
    """
    from datetime import datetime, timedelta
    
    recency_bonuses = scoring_rules.get('recency_bonuses', {})
    
    if not item.get('date'):
        return 0
    
    try:
        # Parser la date de l'item
        item_date = item.get('date')
        if 'T' in item_date:
            item_dt = datetime.fromisoformat(item_date.replace('Z', '+00:00'))
        else:
            item_dt = datetime.strptime(item_date, '%Y-%m-%d')
        
        # Calculer l'ancienneté en jours
        now = datetime.now()
        age_days = (now - item_dt.replace(tzinfo=None)).days
        
        # Bonus selon le type d'événement et l'ancienneté
        if event_type == 'regulatory':
            regulatory_bonuses = recency_bonuses.get('regulatory_milestone', {})
            if age_days <= 7:
                return regulatory_bonuses.get('0_7_days', 2.0)
            elif age_days <= 30:
                return regulatory_bonuses.get('8_30_days', 1.0)
        
        elif event_type == 'partnership':
            partnership_bonuses = recency_bonuses.get('partnership_announcement', {})
            if age_days <= 7:
                return partnership_bonuses.get('0_7_days', 1.5)
            elif age_days <= 30:
                return partnership_bonuses.get('8_30_days', 0.5)
        
        return 0
    
    except Exception:
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
