#!/usr/bin/env python3
"""
Script de test local pour le matching Bedrock V2.

Valide que l'import _call_bedrock_with_retry fonctionne et que le matching
peut être appelé sans erreur d'import.
"""

import sys
import os
import json
from pathlib import Path

# Ajouter le répertoire src_v2 au path
project_root = Path(__file__).parent.parent
src_v2_path = project_root / "src_v2"
sys.path.insert(0, str(src_v2_path))

def test_imports():
    """Test 1 : Vérifier que tous les imports fonctionnent."""
    print("=== Test 1 : Imports ===")
    
    try:
        # Test import du matcher
        from vectora_core.normalization.bedrock_matcher import match_watch_domains_with_bedrock
        print("OK - Import bedrock_matcher réussi")
        
        # Test import de l'API Bedrock unifiée
        from vectora_core.normalization.bedrock_client import call_bedrock_with_retry
        print("OK - Import call_bedrock_with_retry réussi")
        
        # Test import de l'alias de compatibilité
        from vectora_core.normalization.bedrock_client import _call_bedrock_with_retry
        print("OK - Import _call_bedrock_with_retry (alias) réussi")
        
        # Test import du client normalization
        from vectora_core.normalization.bedrock_client import BedrockNormalizationClient
        print("OK - Import BedrockNormalizationClient réussi")
        
        return True
        
    except ImportError as e:
        print(f"ERREUR - Erreur d'import : {e}")
        return False
    except Exception as e:
        print(f"ERREUR - Erreur inattendue : {e}")
        return False

def test_function_signatures():
    """Test 2 : Vérifier les signatures des fonctions."""
    print("\n=== Test 2 : Signatures des fonctions ===")
    
    try:
        from vectora_core.normalization.bedrock_matcher import match_watch_domains_with_bedrock
        from vectora_core.normalization.bedrock_client import call_bedrock_with_retry
        
        # Vérifier que les fonctions sont callables
        assert callable(match_watch_domains_with_bedrock), "match_watch_domains_with_bedrock n'est pas callable"
        assert callable(call_bedrock_with_retry), "call_bedrock_with_retry n'est pas callable"
        
        print("OK - Toutes les fonctions sont callables")
        return True
        
    except Exception as e:
        print(f"ERREUR - Erreur de signature : {e}")
        return False

def test_mock_matching():
    """Test 3 : Simuler un appel de matching (sans vraie requête Bedrock)."""
    print("\n=== Test 3 : Simulation matching ===")
    
    try:
        # Données de test simulées
        normalized_item = {
            "title": "MedinCell's Partner Teva Pharmaceuticals Announces NDA Submission",
            "summary": "Teva submits NDA for olanzapine extended-release injectable",
            "entities": {
                "companies": ["MedinCell", "Teva Pharmaceuticals"],
                "molecules": ["olanzapine"],
                "technologies": ["Extended-Release Injectable", "Once-Monthly Injection"],
                "trademarks": ["TEV-'749", "mdc-TJK"],
                "indications": ["schizophrenia"]
            },
            "event_type": "regulatory"
        }
        
        watch_domains = [
            {
                "id": "tech_lai_ecosystem",
                "type": "technology",
                "priority": "high",
                "technology_scope": "lai_keywords",
                "company_scope": "lai_companies_global"
            },
            {
                "id": "regulatory_lai", 
                "type": "regulatory",
                "priority": "high",
                "company_scope": "lai_companies_global"
            }
        ]
        
        canonical_scopes = {
            "companies": {
                "lai_companies_global": ["MedinCell", "Camurus", "Teva Pharmaceutical", "DelSiTech"]
            },
            "technologies": {
                "lai_keywords": ["Extended-Release Injectable", "Long-Acting Injectable", "Depot Injection"]
            }
        }
        
        # Test de construction du contexte (sans appel Bedrock réel)
        from vectora_core.normalization.bedrock_matcher import _build_domains_context
        domains_context = _build_domains_context(watch_domains, canonical_scopes)
        
        print("OK - Construction du contexte des domaines réussie")
        print(f"   Contexte généré : {len(domains_context)} caractères")
        
        # Test de construction du prompt (sans appel Bedrock réel)
        from vectora_core.normalization.bedrock_matcher import _build_matching_prompt
        prompt = _build_matching_prompt(normalized_item, domains_context)
        
        print("OK - Construction du prompt réussie")
        print(f"   Prompt généré : {len(prompt)} caractères")
        
        # Test de parsing d'une réponse simulée
        mock_response = json.dumps({
            "domain_evaluations": [
                {
                    "domain_id": "tech_lai_ecosystem",
                    "is_relevant": True,
                    "relevance_score": 0.85,
                    "confidence": "high",
                    "reasoning": "Strong LAI technology signals with MedinCell and extended-release injectable",
                    "matched_entities": {
                        "companies": ["MedinCell", "Teva Pharmaceuticals"],
                        "technologies": ["Extended-Release Injectable"]
                    }
                },
                {
                    "domain_id": "regulatory_lai",
                    "is_relevant": True,
                    "relevance_score": 0.72,
                    "confidence": "medium", 
                    "reasoning": "NDA submission for LAI product",
                    "matched_entities": {
                        "companies": ["Teva Pharmaceuticals"]
                    }
                }
            ]
        })
        
        from vectora_core.normalization.bedrock_matcher import _parse_bedrock_matching_response
        parsed_result = _parse_bedrock_matching_response(mock_response)
        
        print("OK - Parsing de la réponse simulée réussi")
        print(f"   Domaines matchés : {parsed_result.get('matched_domains', [])}")
        print(f"   Nombre d'évaluations : {len(parsed_result.get('domain_relevance', {}))}")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Erreur de simulation : {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bedrock_client_integration():
    """Test 4 : Vérifier l'intégration avec le client Bedrock."""
    print("\n=== Test 4 : Intégration client Bedrock ===")
    
    try:
        from vectora_core.normalization.bedrock_client import BedrockNormalizationClient
        
        # Créer une instance du client (sans appel réel)
        client = BedrockNormalizationClient(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            region="us-east-1"
        )
        
        print("OK - Création du client Bedrock réussie")
        print(f"   Modèle : {client.model_id}")
        print(f"   Région : {client.region}")
        
        # Vérifier que les méthodes existent
        assert hasattr(client, 'normalize_item'), "Méthode normalize_item manquante"
        assert callable(client.normalize_item), "normalize_item n'est pas callable"
        
        print("OK - Méthodes du client validées")
        
        return True
        
    except Exception as e:
        print(f"ERREUR - Erreur d'intégration : {e}")
        return False

def main():
    """Fonction principale du test."""
    print("Test local du matching Bedrock V2")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_function_signatures, 
        test_mock_matching,
        test_bedrock_client_integration
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"ERREUR - Erreur dans {test_func.__name__} : {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Résultats des tests :")
    
    success_count = sum(results)
    total_count = len(results)
    
    for i, (test_func, result) in enumerate(zip(tests, results)):
        status = "PASS" if result else "FAIL"
        print(f"   {i+1}. {test_func.__name__}: {status}")
    
    print(f"\nScore final : {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("Tous les tests sont passés ! Le matching Bedrock V2 est prêt.")
        return 0
    else:
        print("Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)