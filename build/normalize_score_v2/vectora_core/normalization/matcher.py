"""
Module de matching des items aux domaines de veille.

Ce module détermine quels domaines de veille correspondent à chaque item
basé sur les entités détectées et les règles de matching configurées.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def match_items_to_domains(
    normalized_items: List[Dict[str, Any]],
    client_config: Dict[str, Any],
    canonical_scopes: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Matche les items normalisés aux domaines de veille du client.
    
    Args:
        normalized_items: Items normalisés avec entités extraites
        client_config: Configuration du client
        canonical_scopes: Scopes canonical
    
    Returns:
        Items avec résultats de matching
    """
    logger.info(f"Matching de {len(normalized_items)} items aux domaines de veille")
    
    # Récupération des domaines de veille
    watch_domains = client_config.get("watch_domains", [])
    if not watch_domains:
        logger.warning("Aucun domaine de veille configuré")
        return normalized_items
    
    # Configuration du matching
    matching_config = client_config.get("matching_config", {})
    
    matched_items = []
    stats = {"total": len(normalized_items), "matched": 0, "unmatched": 0}
    
    for item in normalized_items:
        try:
            # Matching de l'item aux domaines
            matching_results = _match_item_to_domains(
                item, watch_domains, canonical_scopes, matching_config
            )
            
            # Enrichissement de l'item
            item["matching_results"] = matching_results
            matched_items.append(item)
            
            if matching_results.get("matched_domains"):
                stats["matched"] += 1
            else:
                stats["unmatched"] += 1
                
        except Exception as e:
            logger.error(f"Erreur matching item {item.get('item_id', 'unknown')}: {str(e)}")
            # Ajout avec matching vide
            item["matching_results"] = _create_empty_matching_result()
            matched_items.append(item)
            stats["unmatched"] += 1
    
    logger.info(f"Matching terminé: {stats['matched']} matchés, {stats['unmatched']} non-matchés")
    return matched_items


def _match_item_to_domains(
    item: Dict[str, Any],
    watch_domains: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any],
    matching_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Matche un item individuel aux domaines de veille."""
    
    # Extraction des entités de l'item
    entities = item.get("normalized_content", {}).get("entities", {})
    companies = entities.get("companies", [])
    molecules = entities.get("molecules", [])
    technologies = entities.get("technologies", [])
    trademarks = entities.get("trademarks", [])
    
    matched_domains = []
    domain_relevance = {}
    
    for domain in watch_domains:
        domain_id = domain.get("id")
        if not domain_id:
            continue
        
        # Évaluation du matching pour ce domaine
        match_result = _evaluate_domain_match(
            domain, entities, canonical_scopes, matching_config
        )
        
        if match_result["is_match"]:
            matched_domains.append(domain_id)
            domain_relevance[domain_id] = match_result["relevance"]
    
    # Application des exclusions
    exclusion_applied = _apply_exclusions(item, canonical_scopes)
    if exclusion_applied:
        matched_domains = []
        domain_relevance = {}
    
    # Application des exclusions avec détails
    exclusion_result = _apply_exclusions(item, canonical_scopes)
    if exclusion_result["excluded"]:
        matched_domains = []
        domain_relevance = {}
    
    return {
        "matched_domains": matched_domains,
        "domain_relevance": domain_relevance,
        "exclusion_applied": exclusion_result["excluded"],
        "exclusion_reasons": exclusion_result["reasons"]
    }


def _evaluate_domain_match(
    domain: Dict[str, Any],
    entities: Dict[str, List[str]],
    canonical_scopes: Dict[str, Any],
    matching_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Évalue si un domaine matche avec les entités détectées avec logique sophistiquée."""
    
    domain_type = domain.get("type", "technology")
    domain_id = domain.get("id")
    
    # Récupération des scopes du domaine
    company_scope = domain.get("company_scope")
    molecule_scope = domain.get("molecule_scope")
    technology_scope = domain.get("technology_scope")
    trademark_scope = domain.get("trademark_scope")
    
    # Comptage des signaux avec pondération
    entity_signals = 0
    technology_signals = 0
    trademark_signals = 0
    matched_entities = {
        "companies": [],
        "molecules": [],
        "technologies": [],
        "trademarks": []
    }
    
    # Vérification des entreprises avec matching flexible
    if company_scope:
        scope_companies = canonical_scopes.get("companies", {}).get(company_scope, [])
        matched_companies = _match_entities_flexible(entities.get("companies", []), scope_companies)
        if matched_companies:
            entity_signals += len(matched_companies)
            matched_entities["companies"] = matched_companies
    
    # Vérification des molécules avec matching flexible
    if molecule_scope:
        scope_molecules = canonical_scopes.get("molecules", {}).get(molecule_scope, [])
        matched_molecules = _match_entities_flexible(entities.get("molecules", []), scope_molecules)
        if matched_molecules:
            entity_signals += len(matched_molecules)
            matched_entities["molecules"] = matched_molecules
    
    # Vérification des technologies avec matching flexible
    if technology_scope:
        scope_technologies = canonical_scopes.get("technologies", {}).get(technology_scope, [])
        matched_technologies = _match_entities_flexible(entities.get("technologies", []), scope_technologies)
        if matched_technologies:
            technology_signals += len(matched_technologies)
            matched_entities["technologies"] = matched_technologies
    
    # Vérification des trademarks avec traitement privilégié
    trademark_match = False
    if trademark_scope:
        scope_trademarks = canonical_scopes.get("trademarks", {}).get(trademark_scope, [])
        matched_trademarks = _match_entities_flexible(entities.get("trademarks", []), scope_trademarks)
        if matched_trademarks:
            trademark_signals = len(matched_trademarks)
            matched_entities["trademarks"] = matched_trademarks
            trademark_match = True
            
            # Application du boost_factor pour trademarks
            trademark_privileges = matching_config.get("trademark_privileges", {})
            boost_factor = trademark_privileges.get("boost_factor", 2.5)
            entity_signals += int(trademark_signals * boost_factor)
    
    # Application des règles de matching par type de domaine
    domain_overrides = matching_config.get("domain_type_overrides", {}).get(domain_type, {})
    
    require_entity_signals = domain_overrides.get("require_entity_signals", False)
    min_technology_signals = domain_overrides.get("min_technology_signals", 1)
    
    # Évaluation du match avec logique sophistiquée
    is_match = False
    reasons = []
    confidence = 0.0
    
    # Traitement privilégié des trademarks
    trademark_privileges = matching_config.get("trademark_privileges", {})
    if trademark_privileges.get("enabled", False) and trademark_match:
        auto_match_threshold = trademark_privileges.get("auto_match_threshold", 0.8)
        if trademark_signals >= 1:  # Au moins 1 trademark suffit
            is_match = True
            reasons.append("trademark_privilege")
            confidence = min(1.0, auto_match_threshold + (trademark_signals * 0.1))
    
    # Règles standard si pas de match par trademark
    if not is_match:
        # Vérification des exigences minimales
        meets_entity_requirement = not require_entity_signals or entity_signals > 0
        meets_technology_requirement = technology_signals >= min_technology_signals
        
        if meets_entity_requirement and meets_technology_requirement:
            is_match = True
            
            # Construction des raisons
            if entity_signals > 0:
                reasons.append("entity_match")
            if technology_signals > 0:
                reasons.append("technology_match")
            
            # Calcul de la confiance basé sur les signaux
            total_signals = entity_signals + technology_signals
            confidence = min(1.0, total_signals / 5.0)  # Normalisation sur 5 signaux max
    
    # Calcul du score de pertinence final
    relevance_score = confidence
    
    # Bonus pour combinaisons multiples
    if len([k for k, v in matched_entities.items() if v]) >= 2:
        relevance_score = min(1.0, relevance_score * 1.2)  # Bonus 20% pour multi-entités
        reasons.append("multi_entity_bonus")
    
    return {
        "is_match": is_match,
        "relevance": {
            "score": round(relevance_score, 3),
            "confidence": round(confidence, 3),
            "reasons": reasons,
            "entity_matches": matched_entities,
            "signal_breakdown": {
                "entity_signals": entity_signals,
                "technology_signals": technology_signals,
                "trademark_signals": trademark_signals,
                "total_signals": entity_signals + technology_signals + trademark_signals
            }
        }
    }


def _match_entities_flexible(detected_entities: List[str], scope_entities: List[str]) -> List[str]:
    """Matching flexible d'entités avec normalisation de casse et sous-chaînes."""
    if not detected_entities or not scope_entities:
        return []
    
    matched = []
    
    # Normalisation pour matching insensible à la casse
    scope_entities_lower = [entity.lower() for entity in scope_entities]
    
    for detected in detected_entities:
        detected_lower = detected.lower()
        
        # Match exact (insensible à la casse)
        if detected_lower in scope_entities_lower:
            matched.append(detected)
            continue
        
        # Match par sous-chaîne (pour gérer les variations)
        for scope_entity in scope_entities:
            scope_lower = scope_entity.lower()
            
            # Sous-chaîne dans les deux sens
            if (len(detected_lower) >= 3 and detected_lower in scope_lower) or \
               (len(scope_lower) >= 3 and scope_lower in detected_lower):
                matched.append(detected)
                break
    
    return list(set(matched))  # Dédoublonnage


def _apply_exclusions(item: Dict[str, Any], canonical_scopes: Dict[str, Any]) -> Dict[str, Any]:
    """Applique les règles d'exclusion sophistiquées pour filtrer le bruit."""
    
    # Récupération des termes d'exclusion depuis plusieurs scopes
    exclusion_terms = []
    exclusion_scopes = ["lai_exclude_noise", "general_noise_terms"]
    
    for scope_name in exclusion_scopes:
        scope_terms = canonical_scopes.get("exclusions", {}).get(scope_name, [])
        exclusion_terms.extend(scope_terms)
    
    if not exclusion_terms:
        return {"excluded": False, "reasons": []}
    
    # Textes à analyser
    title = item.get("title", "").lower()
    content = item.get("content", "").lower()
    summary = item.get("normalized_content", {}).get("summary", "").lower()
    
    exclusion_reasons = []
    
    # Vérification des termes d'exclusion
    for term in exclusion_terms:
        term_lower = term.lower()
        
        # Vérification dans le titre (poids plus fort)
        if term_lower in title:
            exclusion_reasons.append(f"title_contains_{term}")
        
        # Vérification dans le contenu
        elif term_lower in content:
            exclusion_reasons.append(f"content_contains_{term}")
        
        # Vérification dans le résumé normalisé
        elif term_lower in summary:
            exclusion_reasons.append(f"summary_contains_{term}")
    
    # Règles d'exclusion spécifiques LAI
    lai_exclusions = _check_lai_specific_exclusions(item)
    exclusion_reasons.extend(lai_exclusions)
    
    is_excluded = len(exclusion_reasons) > 0
    
    if is_excluded:
        logger.debug(f"Item exclu: {exclusion_reasons}")
    
    return {
        "excluded": is_excluded,
        "reasons": exclusion_reasons
    }


def _check_lai_specific_exclusions(item: Dict[str, Any]) -> List[str]:
    """Vérifie les exclusions spécifiques au domaine LAI."""
    exclusions = []
    
    normalized_content = item.get("normalized_content", {})
    
    # Exclusion si anti-LAI détecté
    if normalized_content.get("anti_lai_detected", False):
        exclusions.append("anti_lai_detected")
    
    # Exclusion si score LAI très faible
    lai_score = normalized_content.get("lai_relevance_score", 0)
    if lai_score <= 1:
        exclusions.append("lai_score_too_low")
    
    # Exclusion si aucune entité LAI pertinente
    entities = normalized_content.get("entities", {})
    has_lai_entities = (
        entities.get("companies", []) or 
        entities.get("molecules", []) or 
        entities.get("technologies", []) or 
        entities.get("trademarks", [])
    )
    
    if not has_lai_entities and lai_score < 3:
        exclusions.append("no_lai_entities_low_score")
    
    return exclusions


def _create_empty_matching_result() -> Dict[str, Any]:
    """Crée un résultat de matching vide."""
    return {
        "matched_domains": [],
        "domain_relevance": {},
        "exclusion_applied": False
    }