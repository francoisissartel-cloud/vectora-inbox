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
    # TODO: Implémenter le calcul des scores
    # 1. Pour chaque item :
    #    - Appeler compute_score()
    #    - Ajouter le champ score à l'item
    # 2. Retourner les items annotés
    raise NotImplementedError("score_items() sera implémenté dans une étape suivante")


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
    # TODO: Implémenter la formule de scoring
    # Facteurs : event_type, récence, priorité domaine, compétiteurs clés, molécules clés, type de source
    raise NotImplementedError("compute_score() sera implémenté dans une étape suivante")


def rank_items_by_score(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Trie les items par score décroissant.
    
    Args:
        items: Items avec scores
    
    Returns:
        Items triés par score décroissant
    """
    # TODO: Implémenter le tri (simple : sorted(items, key=lambda x: x["score"], reverse=True))
    raise NotImplementedError("rank_items_by_score() sera implémenté dans une étape suivante")
