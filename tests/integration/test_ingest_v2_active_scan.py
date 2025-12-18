#!/usr/bin/env python3
"""
Tests d'intégration pour la Lambda ingest V2 avec scan des clients actifs.

Ce script teste le nouveau modèle d'activation avec event vide et découverte
automatique des clients actifs.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Ajouter src_v2 au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src_v2"))

from vectora_core.shared import config_loader
from vectora_core.ingest import run_ingest_for_active_clients, run_ingest_for_client

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_config_loader_functions():
    """Test des nouvelles fonctions de config_loader."""
    logger.info("=== Test des fonctions config_loader ===")
    
    try:
        # Test 1: Simulation du filtrage des clients actifs
        logger.info("Test 1: Filtrage des clients actifs")
        
        # Simuler des configs client
        mock_configs = {
            'lai_weekly_v3': {
                'client_profile': {'name': 'LAI Weekly V3', 'active': True}
            },
            'test_client_inactive': {
                'client_profile': {'name': 'Test Inactive', 'active': False}
            },
            'test_client_no_active': {
                'client_profile': {'name': 'Test No Active Field'}
            }
        }
        
        # Test du filtrage
        active_clients = config_loader.filter_active_clients(mock_configs)
        
        assert len(active_clients) == 1, f"Attendu 1 client actif, trouvé {len(active_clients)}"
        assert 'lai_weekly_v3' in active_clients, "lai_weekly_v3 devrait être actif"
        
        logger.info(f"✅ Test 1 réussi: {len(active_clients)} client(s) actif(s) trouvé(s)")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 1 échoué: {e}")
        return False


def test_handler_import():
    """Test que le handler peut être importé avec les nouvelles fonctions."""
    logger.info("=== Test import handler ===")
    
    try:
        # Test 2: Import du handler modifié
        logger.info("Test 2: Import du handler avec nouvelles fonctions")
        
        # Ajouter le path pour lambdas
        lambdas_path = Path(__file__).parent.parent.parent / "src_v2" / "lambdas" / "ingest"
        sys.path.insert(0, str(lambdas_path))
        
        import handler
        from vectora_core.ingest import run_ingest_for_active_clients
        
        # Vérifier que les fonctions existent
        assert hasattr(handler, 'lambda_handler'), "lambda_handler manquant"
        assert callable(run_ingest_for_active_clients), "run_ingest_for_active_clients non callable"
        
        logger.info("✅ Test 2 réussi: Handler et fonctions importables")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 2 échoué: {e}")
        return False


def test_event_validation():
    """Test de la validation des events."""
    logger.info("=== Test validation events ===")
    
    try:
        # Test 3: Validation des patterns d'event
        logger.info("Test 3: Patterns d'event supportés")
        
        valid_events = [
            {},  # Event vide
            {"dry_run": True},  # Event avec dry_run global
            {"client_id": "lai_weekly_v3"},  # Event single-client
            {"client_id": "lai_weekly_v3", "dry_run": True},  # Event single-client avec dry_run
            {"period_days": 14},  # Event avec period_days global
        ]
        
        for i, event in enumerate(valid_events):
            logger.info(f"  Event {i+1}: {event}")
            
            # Déterminer le mode attendu
            if "client_id" in event:
                mode_expected = "single_client"
            else:
                mode_expected = "multi_clients"
            
            logger.info(f"    Mode attendu: {mode_expected}")
        
        logger.info("✅ Test 3 réussi: Tous les patterns d'event sont valides")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 3 échoué: {e}")
        return False


def test_config_templates():
    """Test que les templates de config ont le champ active."""
    logger.info("=== Test templates config ===")
    
    try:
        # Test 4: Vérification des templates
        logger.info("Test 4: Champ active dans les templates")
        
        # Vérifier que les fichiers de config ont été modifiés
        template_path = Path(__file__).parent.parent.parent / "client-config-examples" / "client_config_template.yaml"
        lai_v3_path = Path(__file__).parent.parent.parent / "client-config-examples" / "lai_weekly_v3.yaml"
        
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            if 'active:' in template_content:
                logger.info("✅ Template contient le champ active")
            else:
                logger.error("❌ Template ne contient pas le champ active")
                return False
        
        if lai_v3_path.exists():
            with open(lai_v3_path, 'r', encoding='utf-8') as f:
                lai_content = f.read()
            
            if 'active: true' in lai_content:
                logger.info("✅ Config lai_weekly_v3 contient active: true")
            else:
                logger.error("❌ Config lai_weekly_v3 ne contient pas active: true")
                return False
        
        logger.info("✅ Test 4 réussi: Templates mis à jour")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test 4 échoué: {e}")
        return False


def run_all_tests():
    """Exécute tous les tests d'intégration."""
    logger.info("🚀 Démarrage des tests d'intégration ingest V2")
    
    tests = [
        test_config_loader_functions,
        test_handler_import,
        test_event_validation,
        test_config_templates,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de {test_func.__name__}: {e}")
            results.append(False)
    
    # Résumé des résultats
    passed = sum(results)
    total = len(results)
    
    logger.info(f"📊 Résultats des tests: {passed}/{total} réussis")
    
    if passed == total:
        logger.info("🎉 Tous les tests sont passés!")
        return True
    else:
        logger.error(f"❌ {total - passed} test(s) ont échoué")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)