#!/usr/bin/env python3
"""
Test local de la fonction run_engine_for_client avec données réelles.
"""

import sys
import os
import json
from datetime import datetime

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import de la fonction engine
from vectora_core import run_engine_for_client

def test_engine_local():
    """Test de la fonction engine en local avec données réelles."""
    
    print("=== Test Engine Local ===")
    
    # Configuration des variables d'environnement simulées
    env_vars = {
        "ENV": "dev",
        "PROJECT_NAME": "vectora-inbox",
        "CONFIG_BUCKET": "vectora-inbox-config-dev",
        "DATA_BUCKET": "vectora-inbox-data-dev",
        "NEWSLETTERS_BUCKET": "vectora-inbox-newsletters-dev",
        "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-5-20250929-v1:0",
        "LOG_LEVEL": "INFO",
        "BEDROCK_REGION_NEWSLETTER": "eu-west-3",
        "BEDROCK_MODEL_ID_NEWSLETTER": "anthropic.claude-sonnet-4-5-20250929-v1:0",
        "BEDROCK_REGION_NORMALIZATION": "us-east-1",
        "BEDROCK_MODEL_ID_NORMALIZATION": "anthropic.claude-sonnet-4-5-20250929-v1:0",
    }
    
    # Paramètres du test
    client_id = "lai_weekly_v3"
    period_days = 2  # Utiliser 2 jours pour avoir les données du 11 et 12 décembre
    
    print(f"Client: {client_id}")
    print(f"Period: {period_days} jours")
    print(f"Buckets: {env_vars['CONFIG_BUCKET']}, {env_vars['DATA_BUCKET']}, {env_vars['NEWSLETTERS_BUCKET']}")
    
    try:
        # Appel de la fonction engine
        print("\n--- Exécution run_engine_for_client ---")
        result = run_engine_for_client(
            client_id=client_id,
            period_days=period_days,
            env_vars=env_vars
        )
        
        print("\n--- Résultat ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Vérifications
        if result.get('items_selected', 0) > 0:
            print(f"\n✅ Succès : {result.get('items_selected')} items sélectionnés")
        else:
            print(f"\n⚠️ Aucun item sélectionné")
            
        if 's3_output_path' in result:
            print(f"✅ Newsletter générée : {result['s3_output_path']}")
        else:
            print("❌ Pas de newsletter générée")
            
        return True
        
    except Exception as e:
        print(f"\nErreur : {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_engine_local()
    sys.exit(0 if success else 1)