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
    # TODO: Implémenter le matching
    # 1. Pour chaque item :
    #    - Pour chaque watch_domain :
    #      - Calculer les intersections (companies, molecules, technologies, indications)
    #      - Si au moins une intersection non vide → ajouter domain_id à matched_domains
    # 2. Retourner les items annotés
    raise NotImplementedError("match_items_to_domains() sera implémenté dans une étape suivante")


def compute_intersection(item_entities: Set[str], scope_entities: Set[str]) -> Set[str]:
    """
    Calcule l'intersection entre deux ensembles d'entités.
    
    Args:
        item_entities: Entités détectées dans l'item
        scope_entities: Entités du scope canonical
    
    Returns:
        Intersection des deux ensembles
    """
    # TODO: Implémenter l'intersection (simple : item_entities & scope_entities)
    raise NotImplementedError("compute_intersection() sera implémenté dans une étape suivante")
