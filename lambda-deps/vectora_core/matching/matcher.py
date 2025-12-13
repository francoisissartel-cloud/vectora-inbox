"""
Module matcher - Logique de matching (intersections d'ensembles).

Ce module détermine quels items normalisés correspondent aux watch_domains du client
en calculant des intersections d'ensembles (déterministe, transparent).

Supporte les technology profiles pour matching avancé par catégories.
"""

from typing import Any, Dict, List, Set, Optional, Tuple


def match_items_to_domains(
    normalized_items: List[Dict[str, Any]],
    watch_domains: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any],
    matching_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Détermine quels items correspondent à quels watch_domains.
    Utilise les règles de matching définies dans canonical/matching/domain_matching_rules.yaml
    
    Args:
        normalized_items: Liste d'items normalisés
        watch_domains: Liste des watch_domains du client
        canonical_scopes: Scopes canonical chargés
        matching_rules: Règles de matching par type de domaine
    
    Returns:
        Liste d'items annotés avec le champ matched_domains (list[str])
    """
    import logging
    logger = logging.getLogger(__name__)
    
    for item in normalized_items:
        matched_domains = []
        
        # Extraire les entités détectées dans l'item
        item_companies = set(item.get('companies_detected', []))
        item_molecules = set(item.get('molecules_detected', []))
        item_technologies = set(item.get('technologies_detected', []))
        item_indications = set(item.get('indications_detected', []))
        
        # Pour chaque watch_domain
        for domain in watch_domains:
            domain_id = domain.get('id')
            
            # Charger les scopes référencés par ce domaine
            company_scope_key = domain.get('company_scope')
            molecule_scope_key = domain.get('molecule_scope')
            technology_scope_key = domain.get('technology_scope')
            indication_scope_key = domain.get('indication_scope')
            
            # Construire les ensembles de référence depuis les scopes canonical
            scope_companies = set()
            if company_scope_key:
                scope_companies = set(canonical_scopes.get('companies', {}).get(company_scope_key, []))
            
            scope_molecules = set()
            if molecule_scope_key:
                scope_molecules = set(canonical_scopes.get('molecules', {}).get(molecule_scope_key, []))
            
            scope_technologies = set()
            if technology_scope_key:
                scope_technologies = set(canonical_scopes.get('technologies', {}).get(technology_scope_key, []))
            
            scope_indications = set()
            if indication_scope_key:
                scope_indications = set(canonical_scopes.get('indications', {}).get(indication_scope_key, []))
            
            # Calculer les intersections
            companies_match = compute_intersection(item_companies, scope_companies)
            molecules_match = compute_intersection(item_molecules, scope_molecules)
            technologies_match = compute_intersection(item_technologies, scope_technologies)
            indications_match = compute_intersection(item_indications, scope_indications)
            
            # Appliquer les règles de matching pour ce type de domaine
            domain_type = domain.get('type', 'default')
            rule = matching_rules.get(domain_type, matching_rules.get('default'))
            
            # Vérifier si le technology_scope utilise un profile
            match_result, matching_details = _evaluate_domain_match(
                item=item,
                domain=domain,
                domain_type=domain_type,
                rule=rule,
                companies_match=companies_match,
                molecules_match=molecules_match,
                technologies_match=technologies_match,
                indications_match=indications_match,
                canonical_scopes=canonical_scopes,
                matching_rules=matching_rules
            )
            
            if match_result:
                matched_domains.append(domain_id)
                if matching_details:
                    item['matching_details'] = matching_details
                logger.debug(
                    f"Item '{item.get('title', '')[:50]}...' matché au domaine {domain_id} "
                    f"(type: {domain_type}, companies: {len(companies_match)}, molecules: {len(molecules_match)}, "
                    f"technologies: {len(technologies_match)}, indications: {len(indications_match)})"
                )
        
        # Annoter l'item avec les domaines matchés
        item['matched_domains'] = matched_domains
    
    return normalized_items


def compute_intersection(item_entities: Set[str], scope_entities: Set[str]) -> Set[str]:
    """
    Calcule l'intersection entre deux ensembles d'entités.
    
    Args:
        item_entities: Entités détectées dans l'item
        scope_entities: Entités du scope canonical
    
    Returns:
        Intersection des deux ensembles
    """
    return item_entities & scope_entities


def _evaluate_domain_match(
    item: Dict[str, Any],
    domain: Dict[str, Any],
    domain_type: str,
    rule: Dict[str, Any],
    companies_match: Set[str],
    molecules_match: Set[str],
    technologies_match: Set[str],
    indications_match: Set[str],
    canonical_scopes: Dict[str, Any],
    matching_rules: Dict[str, Any]
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Évalue si un item matche un domaine (avec support des technology profiles).
    
    Returns:
        Tuple (match_result, matching_details)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Vérifier si technology domain avec profile
    technology_scope_key = domain.get('technology_scope')
    logger.info(f"[MATCHING_DEBUG] Domain type: {domain_type}, Tech scope: {technology_scope_key}")
    
    if domain_type == 'technology' and technology_scope_key:
        profile_name = _get_technology_profile(technology_scope_key, canonical_scopes)
        logger.info(f"[MATCHING_DEBUG] Profile name: {profile_name}")
        logger.info(f"[MATCHING_DEBUG] Using profile matching: {profile_name is not None}")
        
        if profile_name:
            return _evaluate_technology_profile_match(
                item=item,
                domain=domain,
                profile_name=profile_name,
                companies_match=companies_match,
                molecules_match=molecules_match,
                technologies_match=technologies_match,
                canonical_scopes=canonical_scopes,
                matching_rules=matching_rules
            )
    
    # Fallback: règle classique
    match_result = _evaluate_matching_rule(
        rule=rule,
        companies_match=companies_match,
        molecules_match=molecules_match,
        technologies_match=technologies_match,
        indications_match=indications_match
    )
    return match_result, None


def _evaluate_matching_rule(
    rule: Dict[str, Any],
    companies_match: Set[str],
    molecules_match: Set[str],
    technologies_match: Set[str],
    indications_match: Set[str]
) -> bool:
    """
    Évalue si un item satisfait une règle de matching.
    
    Args:
        rule: Règle de matching (depuis domain_matching_rules.yaml)
        companies_match: Companies matchées
        molecules_match: Molecules matchées
        technologies_match: Technologies matchées
        indications_match: Indications matchées
    
    Returns:
        True si l'item satisfait la règle, False sinon
    """
    match_mode = rule.get('match_mode', 'any_required')
    dimensions = rule.get('dimensions', {})
    
    # Construire un dict des matches par dimension
    matches = {
        'company': companies_match,
        'molecule': molecules_match,
        'technology': technologies_match,
        'indication': indications_match
    }
    
    # Évaluer chaque dimension
    dimension_results = {}
    
    for dim_name, dim_config in dimensions.items():
        requirement = dim_config.get('requirement', 'optional')
        min_matches = dim_config.get('min_matches', 1)
        
        # Cas spécial : dimension "entity" = company OR molecule
        if dim_name == 'entity':
            sources = dim_config.get('sources', ['company', 'molecule'])
            entity_matches = set()
            for source in sources:
                entity_matches.update(matches.get(source, set()))
            
            has_match = len(entity_matches) >= min_matches
        else:
            # Dimension simple
            has_match = len(matches.get(dim_name, set())) >= min_matches
        
        dimension_results[dim_name] = {
            'has_match': has_match,
            'requirement': requirement
        }
    
    # Appliquer la logique de combinaison
    if match_mode == 'all_required':
        # Toutes les dimensions "required" doivent matcher
        for dim_name, result in dimension_results.items():
            if result['requirement'] == 'required' and not result['has_match']:
                return False
        return True
    
    elif match_mode == 'any_required':
        # Au moins une dimension doit matcher
        for dim_name, result in dimension_results.items():
            if result['has_match']:
                return True
        return False
    
    else:
        # Mode inconnu, fallback sur any_required
        for dim_name, result in dimension_results.items():
            if result['has_match']:
                return True
        return False


def _get_technology_profile(technology_scope_key: str, canonical_scopes: Dict[str, Any]) -> Optional[str]:
    """Récupère le profile d'un technology scope."""
    import logging
    logger = logging.getLogger(__name__)
    
    tech_scopes = canonical_scopes.get('technologies', {})
    scope_data = tech_scopes.get(technology_scope_key, {})
    
    logger.info(f"[PROFILE_DEBUG] Technology scope key: {technology_scope_key}")
    logger.info(f"[PROFILE_DEBUG] Scope data type: {type(scope_data)}")
    logger.info(f"[PROFILE_DEBUG] Scope data keys: {list(scope_data.keys()) if isinstance(scope_data, dict) else 'NOT_DICT'}")
    
    if isinstance(scope_data, dict):
        metadata = scope_data.get('_metadata', {})
        logger.info(f"[PROFILE_DEBUG] Metadata: {metadata if metadata else 'MISSING'}")
        profile = metadata.get('profile')
        logger.info(f"[PROFILE_DEBUG] Profile detected: {profile if profile else 'MISSING'}")
        return profile
    
    logger.warning(f"[PROFILE_DEBUG] Scope data is not dict, cannot extract profile")
    return None


def _evaluate_technology_profile_match(
    item: Dict[str, Any],
    domain: Dict[str, Any],
    profile_name: str,
    companies_match: Set[str],
    molecules_match: Set[str],
    technologies_match: Set[str],
    canonical_scopes: Dict[str, Any],
    matching_rules: Dict[str, Any]
) -> Tuple[bool, Dict[str, Any]]:
    """\u00c9value matching avec technology profile."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Charger le profile
    profiles = matching_rules.get('technology_profiles', {})
    profile = profiles.get(profile_name)
    if not profile:
        logger.warning(f"Profile {profile_name} introuvable, fallback sur règle classique")
        return False, None
    
    # Catégoriser les keywords détectés
    technology_scope_key = domain.get('technology_scope')
    category_matches = _categorize_technology_keywords(
        technologies_match, technology_scope_key, canonical_scopes
    )
    
    # Vérifier negative terms
    negative_cats = profile.get('signal_requirements', {}).get('negative_filters', {}).get('categories', [])
    negative_detected = []
    for cat in negative_cats:
        if category_matches.get(cat):
            negative_detected.extend(category_matches[cat])
    
    if negative_detected:
        return False, {
            'domain_id': domain.get('id'),
            'rule_applied': profile_name,
            'categories_matched': category_matches,
            'negative_terms_detected': negative_detected,
            'match_confidence': 'rejected'
        }
    
    # Compter signaux par type
    signal_reqs = profile.get('signal_requirements', {})
    high_precision_cats = signal_reqs.get('high_precision_signals', {}).get('categories', [])
    supporting_cats = signal_reqs.get('supporting_signals', {}).get('categories', [])
    
    high_precision_count = sum(len(category_matches.get(cat, [])) for cat in high_precision_cats)
    supporting_count = sum(len(category_matches.get(cat, [])) for cat in supporting_cats)
    
    # Vérifier entités
    entity_count = len(companies_match) + len(molecules_match)
    entity_reqs = profile.get('entity_requirements', {})
    min_entities = entity_reqs.get('min_matches', 1)
    
    if entity_count < min_entities:
        return False, None
    
    # Identifier company scope type
    company_scope_type = _identify_company_scope_type(
        companies_match, entity_reqs.get('company_scope_modifiers', {}), canonical_scopes
    )
    
    # Évaluer combination logic
    match_result = False
    confidence = 'low'
    
    # Pure player + high precision signal
    if company_scope_type == 'pure_player' and high_precision_count >= 1:
        match_result = True
        confidence = 'high'
    # Hybrid + high precision + supporting
    elif company_scope_type == 'hybrid' and high_precision_count >= 1 and supporting_count >= 1:
        match_result = True
        confidence = 'medium'
    # Any entity + high precision
    elif high_precision_count >= 1 and entity_count >= 1:
        match_result = True
        confidence = 'medium'
    # Supporting signals (2+) + entity
    elif supporting_count >= 2 and entity_count >= 1:
        match_result = True
        confidence = 'low'
    
    matching_details = {
        'domain_id': domain.get('id'),
        'rule_applied': profile_name,
        'categories_matched': category_matches,
        'signals_used': {
            'high_precision': high_precision_count,
            'supporting': supporting_count
        },
        'scopes_hit': {
            'companies': list(companies_match),
            'company_scope_type': company_scope_type
        },
        'negative_terms_detected': [],
        'match_confidence': confidence
    }
    
    return match_result, matching_details


def _categorize_technology_keywords(
    technologies_match: Set[str],
    technology_scope_key: str,
    canonical_scopes: Dict[str, Any]
) -> Dict[str, List[str]]:
    """Mappe les keywords détectés vers leurs catégories."""
    import logging
    logger = logging.getLogger(__name__)
    
    tech_scopes = canonical_scopes.get('technologies', {})
    scope_data = tech_scopes.get(technology_scope_key, {})
    
    category_matches = {}
    
    if not isinstance(scope_data, dict):
        logger.warning(f"[CATEGORY_DEBUG] Scope data is not dict for {technology_scope_key}")
        return category_matches
    
    logger.info(f"[CATEGORY_DEBUG] Categories found in {technology_scope_key}: {[k for k in scope_data.keys() if k != '_metadata']}")
    
    # Parcourir chaque catégorie du scope
    for category_name, keywords in scope_data.items():
        if category_name == '_metadata':
            continue
        if not isinstance(keywords, list):
            logger.warning(f"[CATEGORY_DEBUG] Category {category_name} is not a list")
            continue
        
        logger.info(f"[CATEGORY_DEBUG] Category {category_name}: {len(keywords)} keywords defined")
        
        # Trouver les keywords matchés dans cette catégorie
        matched_in_category = []
        for kw in keywords:
            if kw in technologies_match:
                matched_in_category.append(kw)
        
        if matched_in_category:
            category_matches[category_name] = matched_in_category
            logger.info(f"[CATEGORY_DEBUG] Category {category_name}: {len(matched_in_category)} keywords matched")
    
    return category_matches


def _identify_company_scope_type(
    companies_match: Set[str],
    company_scope_modifiers: Dict[str, Any],
    canonical_scopes: Dict[str, Any]
) -> str:
    """Identifie si companies sont pure_player, hybrid ou other."""
    if not companies_match:
        return 'none'
    
    pure_player_scopes = company_scope_modifiers.get('pure_player_scopes', [])
    hybrid_scopes = company_scope_modifiers.get('hybrid_scopes', [])
    
    company_scopes = canonical_scopes.get('companies', {})
    
    # Vérifier pure players
    for scope_key in pure_player_scopes:
        scope_companies = set(company_scopes.get(scope_key, []))
        if companies_match & scope_companies:
            return 'pure_player'
    
    # Vérifier hybrid
    for scope_key in hybrid_scopes:
        scope_companies = set(company_scopes.get(scope_key, []))
        if companies_match & scope_companies:
            return 'hybrid'
    
    return 'other'
