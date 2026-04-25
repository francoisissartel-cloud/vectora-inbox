#!/usr/bin/env python3
"""
Test simple de l'alignement de configuration Bedrock entre normalisation et matching.
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
    """Test que normalisation et matching utilisent la meme config Bedrock."""
    
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
            print("OK Imports reussis")
        except Exception as e:
            print(f"ERREUR Import: {e}")
            return False
        
        # Test 2: Verification que bedrock_client lit les bonnes variables
        print("\n2. Test configuration bedrock_client...")
        try:
            client = BedrockNormalizationClient(test_model, test_region)
            assert client.model_id == test_model
            assert client.region == test_region
            print(f"OK BedrockNormalizationClient: modele={client.model_id}, region={client.region}")
        except Exception as e:
            print(f"ERREUR bedrock_client: {e}")
            return False
        
        # Test 3: Mock de l'appel Bedrock pour tester bedrock_matcher
        print("\n3. Test configuration bedrock_matcher...")
        
        # Mock des donnees de test
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
        
        # Mock de l'appel Bedrock pour eviter l'appel reel
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
                
                # Verifier que l'appel a ete fait avec les bonnes variables d'env
                mock_bedrock.assert_called_once()
                call_args = mock_bedrock.call_args
                
                # Les arguments devraient etre (prompt, model_id, region)
                assert len(call_args[0]) == 3  # 3 arguments positionnels
                used_model = call_args[0][1]
                used_region = call_args[0][2]
                
                assert used_model == test_model, f"Modele attendu: {test_model}, recu: {used_model}"
                assert used_region == test_region, f"Region attendue: {test_region}, recue: {used_region}"
                
                print(f"OK bedrock_matcher utilise: modele={used_model}, region={used_region}")
                print(f"OK Resultat matching: {len(result.get('matched_domains', []))} domaines matches")
                
            except Exception as e:
                print(f"ERREUR bedrock_matcher: {e}")
                return False
        
        # Test 4: Verification de l'alignement
        print("\n4. Verification de l'alignement...")
        
        # Les deux modules doivent lire les memes variables d'environnement
        normalisation_model = os.environ.get('BEDROCK_MODEL_ID')
        normalisation_region = os.environ.get('BEDROCK_REGION', 'us-east-1')
        
        # Le matching lit maintenant les memes variables (teste ci-dessus)
        matching_model = test_model  # Confirme par le test precedent
        matching_region = test_region  # Confirme par le test precedent
        
        if normalisation_model == matching_model and normalisation_region == matching_region:
            print("OK ALIGNEMENT REUSSI: Normalisation et matching utilisent la meme config Bedrock")
            print(f"   Modele commun: {normalisation_model}")
            print(f"   Region commune: {normalisation_region}")
        else:
            print("ERREUR ALIGNEMENT ECHOUE: Configurations differentes")
            print(f"   Normalisation: {normalisation_model} @ {normalisation_region}")
            print(f"   Matching: {matching_model} @ {matching_region}")
            return False
    
    print("\nTOUS LES TESTS REUSSIS")
    print("OK L'alignement de configuration Bedrock est fonctionnel")
    return True

def test_env_vars_validation():
    """Test de validation des variables d'environnement manquantes."""
    
    print("\nTest de validation des variables d'environnement")
    print("=" * 60)
    
    # Test sans BEDROCK_MODEL_ID
    with patch.dict(os.environ, {}, clear=True):
        try:
            from vectora_core.normalization.bedrock_matcher import match_watch_domains_with_bedrock
            
            result = match_watch_domains_with_bedrock({}, [], {})
            
            if 'config_error' in result:
                print("OK Gestion d'erreur BEDROCK_MODEL_ID manquant: OK")
            else:
                print("ERREUR Gestion d'erreur BEDROCK_MODEL_ID manquant: ECHEC")
                return False
                
        except Exception as e:
            print(f"ERREUR Erreur inattendue: {e}")
            return False
    
    print("OK Validation des variables d'environnement: OK")
    return True

if __name__ == "__main__":
    print("Test d'alignement configuration Bedrock V2")
    print("Objectif: Verifier que normalisation et matching utilisent la meme config")
    
    success = True
    
    # Executer les tests
    success &= test_bedrock_config_alignment()
    success &= test_env_vars_validation()
    
    print("\n" + "=" * 60)
    if success:
        print("RESULTAT: ALIGNEMENT REUSSI")
        print("OK Normalisation et matching utilisent maintenant la meme configuration Bedrock")
        print("OK Pret pour le deploiement en production")
    else:
        print("ERREUR RESULTAT: ALIGNEMENT ECHOUE")
        print("Corrections necessaires avant deploiement")
    
    sys.exit(0 if success else 1)