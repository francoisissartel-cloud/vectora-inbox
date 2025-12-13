#!/usr/bin/env python3
"""
Test local pour diagnostiquer le problème period_days avec client_config.
Ce script simule le comportement AWS sans exécuter tout le pipeline.
"""

import sys
import os
import json
import logging

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vectora_core.config import loader
from vectora_core.utils.config_utils import resolve_period_days
from vectora_core.utils import date_utils

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_period_days_resolution():
    """Test de résolution period_days avec client_config lai_weekly_v2"""
    
    print("=== Test Diagnostic Period Days ===")
    
    # Simuler les variables d'environnement AWS
    env_vars = {
        'CONFIG_BUCKET': 'vectora-inbox-config-dev',
        'DATA_BUCKET': 'vectora-inbox-data-dev',
        'NEWSLETTERS_BUCKET': 'vectora-inbox-newsletters-dev',
        'BEDROCK_MODEL_ID': 'eu.anthropic.claude-sonnet-4-5-20250929-v1:0'
    }
    
    client_id = "lai_weekly_v2"
    config_bucket = env_vars['CONFIG_BUCKET']
    
    print(f"Client ID: {client_id}")
    print(f"Config Bucket: {config_bucket}")
    print()
    
    try:
        # Étape 1 : Charger le client_config depuis S3
        print("1. Chargement du client_config depuis S3...")
        client_config = loader.load_client_config(client_id, config_bucket)
        
        print(f"   [OK] Client config charge : {client_config.get('client_profile', {}).get('name', client_id)}")
        
        # Étape 2 : Examiner la section pipeline
        print("\n2. Analyse de la section pipeline...")
        pipeline_config = client_config.get('pipeline', {})
        print(f"   Pipeline config : {json.dumps(pipeline_config, indent=2)}")
        
        default_period_days = pipeline_config.get('default_period_days')
        print(f"   default_period_days : {default_period_days} (type: {type(default_period_days)})")
        
        # Étape 3 : Test de resolve_period_days
        print("\n3. Test de resolve_period_days...")
        
        # Test cas 1 : Pas de period_days dans le payload (None)
        payload_period_days = None
        resolved_period = resolve_period_days(payload_period_days, client_config)
        print(f"   resolve_period_days(None, client_config) = {resolved_period}")
        
        # Test cas 2 : period_days dans le payload (override)
        payload_period_days = 7
        resolved_period_override = resolve_period_days(payload_period_days, client_config)
        print(f"   resolve_period_days(7, client_config) = {resolved_period_override}")
        
        # Étape 4 : Test de compute_date_range
        print("\n4. Test de compute_date_range...")
        
        # Comportement actuel (problématique)
        from_date_old, to_date_old = date_utils.compute_date_range(None, None, None)
        print(f"   compute_date_range(None, None, None) = {from_date_old} -> {to_date_old}")
        
        # Comportement corrige
        from_date_new, to_date_new = date_utils.compute_date_range(resolved_period, None, None)
        print(f"   compute_date_range({resolved_period}, None, None) = {from_date_new} -> {to_date_new}")
        
        # Étape 5 : Résumé
        print("\n=== RÉSUMÉ DIAGNOSTIC ===")
        print(f"[OK] Client config charge correctement")
        print(f"[OK] Pipeline.default_period_days = {default_period_days}")
        print(f"[OK] resolve_period_days(None) = {resolved_period}")
        print(f"[PROBLEME] compute_date_range(None) utilise fallback 7 jours")
        print(f"[SOLUTION] compute_date_range({resolved_period}) utilise {resolved_period} jours")
        
        return True
        
    except Exception as e:
        print(f"[ERREUR] Erreur lors du test : {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_period_days_resolution()
    sys.exit(0 if success else 1)