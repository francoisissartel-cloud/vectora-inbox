"""
Module matcher - Logique de matching (intersections d'ensembles).

Ce module détermine quels items normalisés correspondent aux watch_domains du client
en calculant des intersections d'ensembles (déterministe, transparent).
"""

from typing import Any, Dict, List, Set


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
            
            if _evaluate_matching_rule(
                rule=rule,
                companies_match=companies_match,
                molecules_match=molecules_match,
                technologies_match=technologies_match,
                indications_match=indications_match
            ):
                matched_domains.append(domain_id)
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
