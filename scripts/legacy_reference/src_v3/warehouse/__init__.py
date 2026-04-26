#!/usr/bin/env python3
"""
Module Warehouse - Système de stockage et reconstitution d'items ingérés
Résout le problème de perte d'items lors des cache hits
"""

from .ingested_warehouse import IngestedWarehouse
from .client_mappings import ClientMappingManager
from .deduplication import DeduplicationManager
from .reconstitution import ReconstitutionManager

__version__ = "1.0.0"

__all__ = [
    'IngestedWarehouse',
    'ClientMappingManager', 
    'DeduplicationManager',
    'ReconstitutionManager'
]

# Fonction utilitaire principale pour l'intégration
def create_warehouse_for_ecosystem(ecosystem: str) -> IngestedWarehouse:
    """Créer une instance de warehouse pour un écosystème"""
    return IngestedWarehouse(ecosystem)

def reconstitute_for_client(client_id: str, client_config: dict, reference_date=None) -> list:
    """Reconstituer les items pour un client (fonction de commodité)"""
    manager = ReconstitutionManager()
    return manager.reconstitute_items_for_client(client_id, client_config, reference_date)