"""
Module de scoring de pertinence des items.

Ce module calcule les scores de pertinence basés sur les règles métier,
les bonus/malus configurés et les facteurs de recency.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def score_items(
    matched_items: List[Dict[str, Any]],
    client_config: Dict[str, Any],
    canonical_scopes: Dict[str, Any],
    scoring_mode: str = "balanced",
    target_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Calcule les scores de pertinence pour les items matchés.
    
    Args:
        matched_items: Items avec résultats de matching
        client_config: Configuration du client
        canonical_scopes: Scopes canonical
        scoring_mode: Mode de scoring (strict, balanced, broad)
        target_date: Date de référence pour le scoring
    
    Returns:
        Items avec scores calculés
    """
    logger.info(f"Calcul des scores pour {len(matched_items)} items (mode: {scoring_mode})")
    
    # Configuration du scoring
    scoring_config = client_config.get("scoring_config", {})
    
    # Date de référence
    if target_date:
        reference_date = datetime.fromisoformat(target_date.replace("Z", ""))
    else:
        reference_date = datetime.now()
    
    scored_items = []
    stats = {"total": len(matched_items), "scored": 0, "min_score": float('inf'), "max_score": 0}
    
    for item in matched_items:
        try:
            # Calcul du score pour cet item
            scoring_results = _calculate_item_score(
                item, scoring_config, canonical_scopes, reference_date, scoring_mode
            )
            
            # Enrichissement de l'item
            item["scoring_results"] = scoring_results
            scored_items.append(item)
            
            final_score = scoring_results.get("final_score", 0)
            stats["scored"] += 1
            stats["min_score"] = min(stats["min_score"], final_score)
            stats["max_score"] = max(stats["max_score"], final_score)
            
        except Exception as e:
            item_id = item.get('item_id', 'unknown')
            logger.error(f"Erreur scoring item {item_id}: {str(e)}")
            logger.error(f"Données matching_results: {item.get('matching_results', {})}")
            logger.error(f"Données normalized_content keys: {list(item.get('normalized_content', {}).keys())}")
            
            # Ajout avec score par défaut + diagnostic
            default_result = _create_default_scoring_result()
            default_result["error"] = str(e)
            default_result["error_type"] = type(e).__name__
            item["scoring_results"] = default_result
            scored_items.append(item)
    
    if stats["min_score"] == float('inf'):
        stats["min_score"] = 0
    
    logger.info(f"Scoring terminé: {stats['scored']} items, scores {stats['min_score']:.1f}-{stats['max_score']:.1f}")
    
    # Tri par score décroissant
    scored_items.sort(key=lambda x: x.get("scoring_results", {}).get("final_score", 0), reverse=True)
    
    return scored_items


def _calculate_item_score(
    item: Dict[str, Any],
    scoring_config: Dict[str, Any],
    canonical_scopes: Dict[str, Any],
    reference_date: datetime,
    scoring_mode: str
) -> Dict[str, Any]:
    """Calcule le score d'un item individuel."""
    
    # 0. Utiliser effective_date calculé en amont
    effective_date = item.get('effective_date')
    
    # 1. Score de base selon le type d'événement
    normalized = item.get("normalized_content", {})
    event_type = normalized.get("event_classification", {}).get("primary_type", "other")
    base_score = _get_event_type_score(event_type, scoring_config)
    
    # 2. Facteur de pertinence des domaines
    domain_relevance_factor = _get_domain_relevance_factor(item)
    
    # 3. Facteur de recency (utilise effective_date)
    recency_factor = _get_recency_factor_with_date(effective_date, reference_date)
    
    # 4. Calcul des bonus
    bonuses = _calculate_bonuses(item, scoring_config, canonical_scopes)
    
    # 5. Calcul des pénalités (utilise effective_date)
    penalties = _calculate_penalties_with_date(item, scoring_config, reference_date, effective_date)
    
    # 6. Score final avec logique sophistiquée
    weighted_base = base_score * domain_relevance_factor * recency_factor
    
    # Filtrage des bonus numériques (exclure les détails)
    numeric_bonuses = {k: v for k, v in bonuses.items() if isinstance(v, (int, float))}
    total_bonus = sum(numeric_bonuses.values())
    total_penalty = sum(penalties.values())
    
    # Score avant ajustements
    raw_score = weighted_base + total_bonus + total_penalty
    
    # Application des seuils minimums
    final_score = max(0, raw_score)
    
    # Ajustement selon le mode de scoring
    if scoring_mode == "strict":
        final_score *= 0.75  # Plus strict pour LAI
    elif scoring_mode == "broad":
        final_score *= 1.25  # Plus permissif pour LAI
    # Mode "balanced" : pas d'ajustement
    
    # Plafonnement pour éviter les scores aberrants
    final_score = min(50.0, final_score)
    
    return {
        "base_score": base_score,
        "bonuses": bonuses,
        "penalties": penalties,
        "final_score": round(final_score, 1),
        "effective_date": effective_date,  # NOUVEAU: Date utilisée pour scoring
        "score_breakdown": {
            "base_score": base_score,
            "domain_relevance_factor": round(domain_relevance_factor, 3),
            "recency_factor": round(recency_factor, 3),
            "weighted_base": round(weighted_base, 2),
            "total_bonus": round(total_bonus, 2),
            "total_penalty": round(total_penalty, 2),
            "raw_score": round(raw_score, 2),
            "scoring_mode": scoring_mode
        }
    }


def _get_event_type_score(event_type: str, scoring_config: Dict[str, Any]) -> float:
    """Récupère le score de base selon le type d'événement."""
    
    # Poids par défaut
    default_weights = {
        "partnership": 8.0,
        "clinical_update": 6.0,
        "regulatory": 7.0,
        "scientific_publication": 4.0,
        "corporate_move": 5.0,
        "financial_results": 3.0,
        "safety_signal": 6.0,
        "manufacturing_supply": 4.0,
        "other": 2.0
    }
    
    # Surcharges client
    overrides = scoring_config.get("event_type_weight_overrides", {})
    
    return overrides.get(event_type, default_weights.get(event_type, 2.0))


def _get_domain_relevance_factor(item: Dict[str, Any]) -> float:
    """Calcule le facteur de pertinence sophistiqué basé sur le matching aux domaines."""
    
    matching_results = item.get("matching_results", {})
    domain_relevance = matching_results.get("domain_relevance", {})
    
    if not domain_relevance:
        return 0.05  # Score très faible si pas de matching
    
    # Calcul sophistiqué de la pertinence
    relevance_scores = []
    confidence_scores = []
    trademark_bonuses = []
    
    for domain_id, relevance in domain_relevance.items():
        score = relevance.get("score", 0)
        confidence_str = relevance.get("confidence", "medium")
        reasons = relevance.get("reasons", [])
        
        # CORRECTION: Mapping confidence string → number
        confidence_mapping = {
            "high": 0.9,
            "medium": 0.6,
            "low": 0.3
        }
        confidence = confidence_mapping.get(confidence_str.lower(), 0.5)
        
        relevance_scores.append(score)
        confidence_scores.append(confidence)
        
        # Bonus pour matching par trademark
        if "trademark_privilege" in reasons:
            trademark_bonuses.append(0.2)
        elif "trademark_match" in reasons:
            trademark_bonuses.append(0.1)
    
    if not relevance_scores:
        return 0.3  # Score faible par défaut
    
    # Calcul du facteur final
    avg_relevance = sum(relevance_scores) / len(relevance_scores)
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    trademark_boost = sum(trademark_bonuses) if trademark_bonuses else 0
    
    # Combinaison pondérée
    final_factor = (avg_relevance * 0.6) + (avg_confidence * 0.3) + trademark_boost
    
    # Bonus pour multiples domaines matchés
    if len(domain_relevance) > 1:
        final_factor *= 1.1  # Bonus 10% pour multi-domaines
    
    return min(1.0, final_factor)  # Plafonnement à 1.0


def _get_recency_factor_with_date(effective_date: str, reference_date: datetime) -> float:
    """Calcule le facteur de recency avec date effective (Bedrock ou fallback)."""
    
    if not effective_date:
        return 0.7  # Pénalité plus forte si pas de date
    
    try:
        # Parsing de la date de publication
        if "T" in effective_date:
            pub_date = datetime.fromisoformat(effective_date.replace("Z", ""))
        else:
            pub_date = datetime.strptime(effective_date, "%Y-%m-%d")
        
        # Calcul de l'âge en jours
        age_days = (reference_date - pub_date).days
        
        # Facteur de recency avec dégradation progressive
        if age_days < 0:
            return 1.0  # Article futur (erreur de date)
        elif age_days <= 1:
            return 1.0  # Très récent (24h)
        elif age_days <= 3:
            return 0.98  # Très récent (3 jours)
        elif age_days <= 7:
            return 0.95  # Récent (1 semaine)
        elif age_days <= 14:
            return 0.92  # Assez récent (2 semaines)
        elif age_days <= 30:
            return 0.88  # Récent (1 mois)
        elif age_days <= 60:
            return 0.82  # Moyen (2 mois)
        elif age_days <= 90:
            return 0.75  # Ancien (3 mois)
        elif age_days <= 180:
            return 0.65  # Très ancien (6 mois)
        else:
            return 0.5   # Obsolète (6+ mois)
            
    except Exception as e:
        logger.warning(f"Erreur parsing date {effective_date}: {str(e)}")
        return 0.6  # Pénalité pour date invalide


def _get_recency_factor(item: Dict[str, Any], reference_date: datetime) -> float:
    """Calcule le facteur de recency avec dégradation progressive sophistiquée."""
    
    published_at = item.get("published_at")
    return _get_recency_factor_with_date(published_at, reference_date)


def _calculate_bonuses(
    item: Dict[str, Any],
    scoring_config: Dict[str, Any],
    canonical_scopes: Dict[str, Any]
) -> Dict[str, float]:
    """Calcule les bonus LAI selon les règles métier sophistiquées."""
    
    bonuses = {}
    client_bonuses = scoring_config.get("client_specific_bonuses", {})
    
    # Extraction des entités et métadonnées
    normalized_content = item.get("normalized_content", {})
    entities = normalized_content.get("entities", {})
    companies = entities.get("companies", [])
    trademarks = entities.get("trademarks", [])
    molecules = entities.get("molecules", [])
    technologies = entities.get("technologies", [])
    
    # Bonus pure players LAI (priorité maximale)
    pure_player_config = client_bonuses.get("pure_player_companies", {})
    if pure_player_config:
        scope_name = pure_player_config.get("scope")
        bonus_value = pure_player_config.get("bonus", 0)
        
        if scope_name and bonus_value:
            scope_companies = canonical_scopes.get("companies", {}).get(scope_name, [])
            matched_pure_players = _match_entities_case_insensitive(companies, scope_companies)
            
            if matched_pure_players:
                # Bonus progressif selon le nombre de pure players
                base_bonus = bonus_value
                if len(matched_pure_players) > 1:
                    base_bonus *= 1.2  # Bonus 20% pour multiples pure players
                
                bonuses["pure_player_company"] = base_bonus
                bonuses["pure_player_details"] = {
                    "matched_companies": matched_pure_players,
                    "count": len(matched_pure_players)
                }
    
    # Bonus trademarks LAI (signal très fort)
    trademark_config = client_bonuses.get("trademark_mentions", {})
    if trademark_config:
        scope_name = trademark_config.get("scope")
        bonus_value = trademark_config.get("bonus", 0)
        
        if scope_name and bonus_value and trademarks:
            scope_trademarks = canonical_scopes.get("trademarks", {}).get(scope_name, [])
            matched_trademarks = _match_entities_case_insensitive(trademarks, scope_trademarks)
            
            if matched_trademarks:
                # Bonus progressif selon le nombre de trademarks
                base_bonus = bonus_value
                if len(matched_trademarks) > 1:
                    base_bonus *= 1.3  # Bonus 30% pour multiples trademarks
                
                bonuses["trademark_mention"] = base_bonus
                bonuses["trademark_details"] = {
                    "matched_trademarks": matched_trademarks,
                    "count": len(matched_trademarks)
                }
    
    # Bonus molécules clés LAI
    molecule_config = client_bonuses.get("key_molecules", {})
    if molecule_config:
        scope_name = molecule_config.get("scope")
        bonus_value = molecule_config.get("bonus", 0)
        
        if scope_name and bonus_value and molecules:
            scope_molecules = canonical_scopes.get("molecules", {}).get(scope_name, [])
            matched_molecules = _match_entities_case_insensitive(molecules, scope_molecules)
            
            if matched_molecules:
                bonuses["key_molecule"] = bonus_value
                bonuses["molecule_details"] = {
                    "matched_molecules": matched_molecules,
                    "count": len(matched_molecules)
                }
    
    # Bonus hybrid companies (Big Pharma avec activité LAI)
    hybrid_config = client_bonuses.get("hybrid_companies", {})
    if hybrid_config:
        scope_name = hybrid_config.get("scope")
        bonus_value = hybrid_config.get("bonus", 0)
        
        if scope_name and bonus_value:
            scope_companies = canonical_scopes.get("companies", {}).get(scope_name, [])
            matched_hybrid = _match_entities_case_insensitive(companies, scope_companies)
            
            if matched_hybrid:
                bonuses["hybrid_company"] = bonus_value
                bonuses["hybrid_details"] = {
                    "matched_companies": matched_hybrid,
                    "count": len(matched_hybrid)
                }
    
    # Bonus technologies LAI spécifiques
    if technologies:
        lai_tech_bonus = _calculate_technology_bonus(technologies, canonical_scopes)
        if lai_tech_bonus > 0:
            bonuses["lai_technology"] = lai_tech_bonus
    
    # Bonus type d'événement spécifique LAI
    event_type = normalized_content.get("event_classification", {}).get("primary_type")
    event_bonuses = _calculate_event_type_bonuses(event_type, normalized_content)
    bonuses.update(event_bonuses)
    
    # Bonus contexte pure player (sans mention explicite LAI)
    if normalized_content.get("pure_player_context", False):
        bonuses["pure_player_context"] = 2.0
    
    # REMOVED: Bonus score LAI élevé (deprecated - now using domain_scoring)
    # lai_score = normalized_content.get("lai_relevance_score", 0)
    # if lai_score >= 8:
    #     bonuses["high_lai_relevance"] = 2.5
    # elif lai_score >= 6:
    #     bonuses["medium_lai_relevance"] = 1.5
    
    return bonuses


def _match_entities_case_insensitive(detected: List[str], scope: List[str]) -> List[str]:
    """Matching d'entités insensible à la casse."""
    if not detected or not scope:
        return []
    
    scope_lower = [entity.lower() for entity in scope]
    matched = []
    
    for entity in detected:
        if entity.lower() in scope_lower:
            matched.append(entity)
    
    return matched


def _calculate_technology_bonus(technologies: List[str], canonical_scopes: Dict[str, Any]) -> float:
    """Calcule le bonus pour les technologies LAI détectées."""
    lai_keywords = canonical_scopes.get("technologies", {}).get("lai_keywords", [])
    
    if not lai_keywords:
        return 0.0
    
    matched_tech = _match_entities_case_insensitive(technologies, lai_keywords)
    
    if not matched_tech:
        return 0.0
    
    # Bonus progressif selon le nombre de technologies LAI
    base_bonus = 1.0
    tech_count = len(matched_tech)
    
    if tech_count >= 3:
        return base_bonus * 2.0  # Bonus double pour 3+ technologies
    elif tech_count >= 2:
        return base_bonus * 1.5  # Bonus 50% pour 2 technologies
    else:
        return base_bonus  # Bonus de base pour 1 technologie


def _calculate_event_type_bonuses(event_type: str, normalized_content: Dict[str, Any]) -> Dict[str, float]:
    """Calcule les bonus spécifiques par type d'événement."""
    bonuses = {}
    
    # Bonus par type d'événement (ajustés pour LAI)
    if event_type == "partnership":
        bonuses["partnership_event"] = 3.0
    elif event_type == "regulatory":
        bonuses["regulatory_event"] = 2.5
    elif event_type == "clinical_update":
        bonuses["clinical_event"] = 2.0
    elif event_type == "scientific_publication":
        bonuses["scientific_event"] = 1.5
    
    # Bonus combinaisons spéciales
    entities = normalized_content.get("entities", {})
    has_companies = bool(entities.get("companies", []))
    has_molecules = bool(entities.get("molecules", []))
    has_technologies = bool(entities.get("technologies", []))
    
    # Bonus pour combinaison partnership + molecules + companies
    if event_type == "partnership" and has_companies and has_molecules:
        bonuses["partnership_molecule_combo"] = 1.5
    
    # Bonus pour combinaison regulatory + technologies
    if event_type == "regulatory" and has_technologies:
        bonuses["regulatory_tech_combo"] = 1.0
    
    return bonuses


def _calculate_penalties_with_date(
    item: Dict[str, Any],
    scoring_config: Dict[str, Any],
    reference_date: datetime,
    effective_date: str
) -> Dict[str, float]:
    """Calcule les pénalités sophistiquées avec date effective."""
    
    penalties = {}
    normalized_content = item.get("normalized_content", {})
    
    # Pénalité anti-LAI (signal fort)
    if normalized_content.get("anti_lai_detected", False):
        penalties["anti_lai_penalty"] = -5.0
    
    # REMOVED: Pénalité score LAI très faible (deprecated - now using domain_scoring)
    # lai_score = normalized_content.get("lai_relevance_score", 0)
    # if lai_score <= 2:
    #     penalties["low_lai_score"] = -3.0
    # elif lai_score <= 4:
    #     penalties["medium_lai_score"] = -1.5
    
    # Pénalité âge avec dégradation progressive (utilise effective_date)
    if effective_date:
        try:
            if "T" in effective_date:
                pub_date = datetime.fromisoformat(effective_date.replace("Z", ""))
            else:
                pub_date = datetime.strptime(effective_date, "%Y-%m-%d")
            
            age_days = (reference_date - pub_date).days
            
            # Pénalités progressives selon l'âge
            if age_days > 180:  # Plus de 6 mois
                penalties["very_old_penalty"] = -2.0
            elif age_days > 90:  # Plus de 3 mois
                penalties["old_penalty"] = -1.0
            elif age_days > 60:  # Plus de 2 mois
                penalties["aging_penalty"] = -0.5
                
        except Exception:
            # Pénalité si date invalide
            penalties["invalid_date_penalty"] = -1.0
    
    # Pénalité absence d'entités pertinentes
    entities = normalized_content.get("entities", {})
    has_any_entities = any([
        entities.get("companies", []),
        entities.get("molecules", []),
        entities.get("technologies", []),
        entities.get("trademarks", [])
    ])
    
    if not has_any_entities:
        penalties["no_entities_penalty"] = -2.0
    
    # Pénalité exclusion appliquée
    matching_results = item.get("matching_results", {})
    if matching_results.get("exclusion_applied", False):
        exclusion_reasons = matching_results.get("exclusion_reasons", [])
        if exclusion_reasons:
            penalties["exclusion_penalty"] = -3.0
    
    # Pénalité type d'événement peu pertinent pour LAI
    event_type = normalized_content.get("event_classification", {}).get("primary_type")
    low_relevance_events = ["financial_results", "other"]
    if event_type in low_relevance_events:
        penalties["low_relevance_event"] = -1.0
    
    return penalties


def _calculate_penalties(
    item: Dict[str, Any],
    scoring_config: Dict[str, Any],
    reference_date: datetime
) -> Dict[str, float]:
    """Calcule les pénalités sophistiquées."""
    published_at = item.get("published_at")
    return _calculate_penalties_with_date(item, scoring_config, reference_date, published_at)


def _create_default_scoring_result() -> Dict[str, Any]:
    """Crée un résultat de scoring par défaut."""
    return {
        "base_score": 0.0,
        "bonuses": {},
        "penalties": {},
        "final_score": 0.0,
        "score_breakdown": {
            "event_type_weight": 0.0,
            "domain_relevance": 0.0,
            "recency_factor": 0.0,
            "total_bonus": 0.0,
            "total_penalty": 0.0
        }
    }