"""
Module matcher - Logique de matching (intersections d'ensembles).

Ce module détermine quels items normalisés correspondent aux watch_domains du client
en calculant des intersections d'ensembles (déterministe, transparent).
"""

from typing import Any, Dict, List, Set


def match_items_to_domains(
    normalized_items: List[Dict[str, Any]],
    watch_domains: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Détermine quels items correspondent à quels watch_domains.
    
    Args:
        normalized_items: Liste d'items normalisés
        watch_domains: Liste des watch_domains du client
        canonical_scopes: Scopes canonical chargés
    
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
            
            # Si au moins une intersection est non vide → l'item appartient au domaine
            if companies_match or molecules_match or technologies_match or indications_match:
                matched_domains.append(domain_id)
                logger.debug(f"Item '{item.get('title', '')[:50]}...' matché au domaine {domain_id}")
        
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
