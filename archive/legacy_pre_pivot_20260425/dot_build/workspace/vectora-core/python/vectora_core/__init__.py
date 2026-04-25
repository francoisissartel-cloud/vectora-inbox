"""
Vectora Core V2 - Bibliothèque métier restructurée pour 3 Lambdas V2.

Ce package contient maintenant la logique métier organisée par Lambda :
- shared/ : Modules partagés entre toutes les Lambdas
- ingest/ : Modules spécifiques à la Lambda ingest V2
- normalization/ : Modules spécifiques à la Lambda normalize-score V2
- newsletter/ : Modules spécifiques à la Lambda newsletter V2

Fonctions principales :
- ingest.run_ingest_for_client() : Orchestration ingestion
- normalization.run_normalize_score_for_client() : Orchestration normalisation + scoring (à implémenter)
- newsletter.run_newsletter_for_client() : Orchestration newsletter (à implémenter)
"""

# Redirection vers les nouveaux modules
# Pour compatibilité ascendante temporaire
from .ingest import run_ingest_for_client

__all__ = [
    "run_ingest_for_client",
]