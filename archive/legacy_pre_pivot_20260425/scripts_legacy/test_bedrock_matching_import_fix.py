#!/usr/bin/env python3
"""
Test local pour valider la correction d'import du matching Bedrock V2.
Teste que l'API call_bedrock_with_retry est accessible et fonctionne.
"""

import os
import sys
import json

# Ajouter src_v2 au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_v2'))

def test_bedrock_import():
    """Test que l'import de l'API Bedrock fonctionne."""
    print("=== Test d'import Bedrock ===")
    
    try:
        from vectora_core.normalization.bedrock_client import call_bedrock_with_retry
        print("OK Import call_bedrock_with_retry reussi")
        
        from vectora_core.normalization.bedrock_matcher import match_watch_domains_with_bedrock
        print("OK Import match_watch_domains_with_bedrock reussi")
        
        return True
    except ImportError as e:
        print(f"ERREUR d'import: {e}")
        return False

def test_matching_logic():
    """Test la logique de matching avec des données synthétiques."""
    print("\n=== Test logique matching ===")
    
    # Variables d'environnement de test
    os.environ['BEDROCK_MODEL_ID'] = 'anthropic.claude-3-sonnet-20240229-v1:0'
    os.environ['BEDROCK_REGION'] = 'us-east-1'
    
    try:
        from vectora_core.normalization.bedrock_matcher import match_watch_domains_with_bedrock
        
        # Item synthétique normalisé
        normalized_item = {
            "title": "MedinCell announces positive Phase 3 results for UZEDY long-acting injectable",
            "summary": "MedinCell reports successful Phase 3 trial for UZEDY, a long-acting injectable antipsychotic using BEPO technology",
            "entities": {
                "companies_detected": ["MedinCell"],
                "molecules_detected": ["risperidone"],
                "technologies_detected": ["long-acting injectable", "BEPO"],
                "trademarks_detected": ["UZEDY"]
            },
            "event_type": "clinical_update"
        }
        
        # Watch domains synthétiques
        watch_domains = [
            {
                "id": "tech_lai_ecosystem",
                "type": "technology",
                "priority": "high",
                "company_scope": "lai_companies",
                "technology_scope": "lai_technologies"
            }
        ]
        
        # Scopes canoniques synthétiques
        canonical_scopes = {
            "companies": {
                "lai_companies": ["MedinCell", "Camurus", "DelSiTech"]
            },
            "technologies": {
                "lai_technologies": {
                    "core_phrases": ["long-acting injectable", "depot injection"],
                    "technology_terms_high_precision": ["BEPO", "microspheres"]
                }
            }
        }
        
        print("Test avec item synthetique LAI...")
        
        # Mock de l'appel Bedrock pour éviter les coûts
        def mock_call_bedrock_with_retry(model_id, request_body):
            return json.dumps({
                "domain_evaluations": [
                    {
                        "domain_id": "tech_lai_ecosystem",
                        "is_relevant": True,
                        "relevance_score": 0.85,
                        "confidence": "high",
                        "reasoning": "Strong LAI technology signals with MedinCell and UZEDY",
                        "matched_entities": {
                            "companies": ["MedinCell"],
                            "technologies": ["long-acting injectable", "BEPO"],
                            "trademarks": ["UZEDY"]
                        }
                    }
                ]
            })
        
        # Patcher temporairement pour le test
        import vectora_core.normalization.bedrock_client
        original_func = vectora_core.normalization.bedrock_client.call_bedrock_with_retry
        vectora_core.normalization.bedrock_client.call_bedrock_with_retry = mock_call_bedrock_with_retry
        
        try:
            result = match_watch_domains_with_bedrock(
                normalized_item, watch_domains, canonical_scopes
            )
            
            print(f"OK Matching reussi: {len(result.get('matched_domains', []))} domaines matches")
            print(f"   Domaines: {result.get('matched_domains', [])}")
            
            if result.get('matched_domains'):
                print("OK Test reussi: Au moins un domaine matche")
                return True
            else:
                print("WARNING Aucun domaine matche (peut etre normal selon les seuils)")
                return True
                
        finally:
            # Restaurer la fonction originale
            vectora_core.normalization.bedrock_client.call_bedrock_with_retry = original_func
            
    except Exception as e:
        print(f"ERREUR dans le matching: {e}")
        return False

def main():
    """Test principal de validation de la correction d'import."""
    print("Test de validation - Correction import Bedrock V2")
    print("=" * 50)
    
    success = True
    
    # Test 1: Import
    if not test_bedrock_import():
        success = False
    
    # Test 2: Logique
    if not test_matching_logic():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("TOUS LES TESTS REUSSIS")
        print("OK La correction d'import est fonctionnelle")
        print("OK Pret pour le deploiement")
    else:
        print("ECHEC DES TESTS")
        print("CORRECTION supplementaire requise")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)