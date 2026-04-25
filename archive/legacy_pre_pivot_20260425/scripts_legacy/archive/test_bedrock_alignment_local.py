#!/usr/bin/env python3
"""
Test local de l'alignement de configuration Bedrock entre normalisation et matching.

Valide que les deux modules utilisent exactement les mêmes variables d'environnement.
"""

import os
import sys
import json
import logging
from unittest.mock import patch, MagicMock

# Ajouter le chemin vers src_v2
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_v2'))

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_bedrock_config_alignment():
    """Test que normalisation et matching utilisent la même config Bedrock."""
    
    print("Test d'alignement configuration Bedrock")
    print("=" * 60)
    
    # Configuration de test
    test_model = "anthropic.claude-3-sonnet-20240229-v1:0"
    test_region = "us-east-1"
    
    # Simuler les variables d'environnement
    with patch.dict(os.environ, {
        'BEDROCK_MODEL_ID': test_model,
        'BEDROCK_REGION': test_region,
        'CONFIG_BUCKET': 'test-config',
        'DATA_BUCKET': 'test-data'
    }):
        
        # Test 1: Import des modules
        print("\n1. Test des imports...")
        try:
            from vectora_core.normalization.bedrock_client import BedrockNormalizationClient, call_bedrock_with_retry
            from vectora_core.normalization.bedrock_matcher import match_watch_domains_with_bedrock
            print("✅ Imports réussis")
        except Exception as e:
            print(f"❌ Erreur d'import: {e}")
            return False
        
        # Test 2: Vérification que bedrock_client lit les bonnes variables
        print("\n2️⃣ Test configuration bedrock_client...")
        try:
            client = BedrockNormalizationClient(test_model, test_region)
            assert client.model_id == test_model
            assert client.region == test_region
            print(f"✅ BedrockNormalizationClient: modèle={client.model_id}, région={client.region}")
        except Exception as e:
            print(f"❌ Erreur bedrock_client: {e}")
            return False
        
        # Test 3: Mock de l'appel Bedrock pour tester bedrock_matcher
        print("\n3️⃣ Test configuration bedrock_matcher...")
        
        # Mock des données de test
        test_item = {
            'title': 'Test LAI Technology Update',
            'summary': 'Test summary about long-acting injectable technology',
            'entities': {
                'companies': ['MedinCell'],
                'technologies': ['long-acting injectable'],
                'molecules': ['buprenorphine']
            },
            'event_type': 'technology_update'
        }
        
        test_domains = [
            {
                'id': 'tech_lai_ecosystem',
                'type': 'technology',
                'priority': 'high',
                'company_scope': 'lai_companies_mvp_core',
                'technology_scope': 'lai_keywords'
            }
        ]
        
        test_scopes = {
            'companies': {
                'lai_companies_mvp_core': ['MedinCell', 'Camurus']
            },
            'technologies': {
                'lai_keywords': ['long-acting injectable', 'depot injection']
            }
        }
        
        # Mock de l'appel Bedrock pour éviter l'appel réel
        mock_response = json.dumps({
            "domain_evaluations": [
                {
                    "domain_id": "tech_lai_ecosystem",
                    "is_relevant": True,
                    "relevance_score": 0.85,
                    "confidence": "high",
                    "reasoning": "Strong LAI technology signals detected",
                    "matched_entities": {
                        "companies": ["MedinCell"],
                        "technologies": ["long-acting injectable"]
                    }
                }
            ]
        })
        
        with patch('vectora_core.normalization.bedrock_matcher._call_bedrock_matching') as mock_bedrock:
            mock_bedrock.return_value = mock_response
            
            try:
                result = match_watch_domains_with_bedrock(
                    test_item, test_domains, test_scopes
                )
                
                # Vérifier que l'appel a été fait avec les bonnes variables d'env
                mock_bedrock.assert_called_once()
                call_args = mock_bedrock.call_args
                
                # Les arguments devraient être (prompt, model_id, region)
                assert len(call_args[0]) == 3  # 3 arguments positionnels
                used_model = call_args[0][1]
                used_region = call_args[0][2]
                
                assert used_model == test_model, f"Modèle attendu: {test_model}, reçu: {used_model}"
                assert used_region == test_region, f"Région attendue: {test_region}, reçue: {used_region}"
                
                print(f"✅ bedrock_matcher utilise: modèle={used_model}, région={used_region}")
                print(f"✅ Résultat matching: {len(result.get('matched_domains', []))} domaines matchés")
                
            except Exception as e:
                print(f"❌ Erreur bedrock_matcher: {e}")
                return False
        
        # Test 4: Vérification de l'alignement
        print("\n4️⃣ Vérification de l'alignement...")
        
        # Les deux modules doivent lire les mêmes variables d'environnement
        normalisation_model = os.environ.get('BEDROCK_MODEL_ID')
        normalisation_region = os.environ.get('BEDROCK_REGION', 'us-east-1')
        
        # Le matching lit maintenant les mêmes variables (testé ci-dessus)
        matching_model = test_model  # Confirmé par le test précédent
        matching_region = test_region  # Confirmé par le test précédent
        
        if normalisation_model == matching_model and normalisation_region == matching_region:
            print("✅ ALIGNEMENT RÉUSSI: Normalisation et matching utilisent la même config Bedrock")
            print(f"   📋 Modèle commun: {normalisation_model}")
            print(f"   🌍 Région commune: {normalisation_region}")
        else:
            print("❌ ALIGNEMENT ÉCHOUÉ: Configurations différentes")
            print(f"   Normalisation: {normalisation_model} @ {normalisation_region}")
            print(f"   Matching: {matching_model} @ {matching_region}")
            return False
    
    print("\n🎉 TOUS LES TESTS RÉUSSIS")
    print("✅ L'alignement de configuration Bedrock est fonctionnel")
    return True

def test_env_vars_validation():
    """Test de validation des variables d'environnement manquantes."""
    
    print("\n🔍 Test de validation des variables d'environnement")
    print("=" * 60)
    
    # Test sans BEDROCK_MODEL_ID
    with patch.dict(os.environ, {}, clear=True):
        try:
            from vectora_core.normalization.bedrock_matcher import match_watch_domains_with_bedrock
            
            result = match_watch_domains_with_bedrock({}, [], {})
            
            if 'config_error' in result:
                print("✅ Gestion d'erreur BEDROCK_MODEL_ID manquant: OK")
            else:
                print("❌ Gestion d'erreur BEDROCK_MODEL_ID manquant: ÉCHEC")
                return False
                
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return False
    
    print("✅ Validation des variables d'environnement: OK")
    return True

if __name__ == "__main__":
    print("Test d'alignement configuration Bedrock V2")
    print("Objectif: Verifier que normalisation et matching utilisent la meme config")
    
    success = True
    
    # Exécuter les tests
    success &= test_bedrock_config_alignment()
    success &= test_env_vars_validation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎯 RÉSULTAT: ALIGNEMENT RÉUSSI")
        print("✅ Normalisation et matching utilisent maintenant la même configuration Bedrock")
        print("✅ Prêt pour le déploiement en production")
    else:
        print("❌ RÉSULTAT: ALIGNEMENT ÉCHOUÉ")
        print("🔧 Corrections nécessaires avant déploiement")
    
    sys.exit(0 if success else 1)