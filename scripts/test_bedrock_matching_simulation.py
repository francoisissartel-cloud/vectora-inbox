#!/usr/bin/env python3
"""
Test de simulation du matching Bedrock end-to-end.

Simule un run complet avec le nouveau matching Bedrock sans appels AWS réels.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def simulate_bedrock_matching_response():
    """Simule une réponse Bedrock réaliste pour le matching."""
    return json.dumps({
        "domain_evaluations": [
            {
                "domain_id": "tech_lai_ecosystem",
                "is_relevant": True,
                "relevance_score": 0.85,
                "confidence": "high",
                "reasoning": "Article discusses MedinCell's BEPO technology partnership with Teva for LAI development",
                "matched_entities": {
                    "companies": ["MedinCell", "Teva Pharmaceuticals"],
                    "technologies": ["Extended-Release Injectable", "BEPO"],
                    "molecules": ["olanzapine"]
                }
            },
            {
                "domain_id": "regulatory_lai",
                "is_relevant": True,
                "relevance_score": 0.75,
                "confidence": "medium",
                "reasoning": "FDA submission mentioned for LAI formulation",
                "matched_entities": {
                    "companies": ["Teva Pharmaceuticals"],
                    "molecules": ["olanzapine"]
                }
            }
        ]
    })

def create_test_item():
    """Crée un item de test représentatif du MVP."""
    return {
        'source_key': 'press_corporate__medincell',
        'source_type': 'rss',
        'title': "MedinCell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension",
        'raw_text': "MedinCell (Euronext: MEDCL) today announced that its partner Teva Pharmaceuticals has submitted a New Drug Application (NDA) to the U.S. FDA for olanzapine extended-release injectable suspension using MedinCell's BEPO technology platform.",
        'url': 'https://www.medincell.com/news/teva-olanzapine-nda',
        'published_at': '2025-12-16'
    }

def create_test_config():
    """Crée une configuration de test."""
    watch_domains = [
        {
            'id': 'tech_lai_ecosystem',
            'type': 'technology',
            'priority': 'high',
            'company_scope': 'lai_companies_global',
            'technology_scope': 'lai_keywords',
            'molecule_scope': 'lai_molecules_global',
            'trademark_scope': 'lai_trademarks_global'
        },
        {
            'id': 'regulatory_lai',
            'type': 'regulatory',
            'priority': 'high',
            'company_scope': 'lai_companies_global',
            'technology_scope': 'lai_keywords',
            'trademark_scope': 'lai_trademarks_global'
        }
    ]
    
    canonical_scopes = {
        'companies': {
            'lai_companies_global': ['MedinCell', 'Teva Pharmaceutical', 'Camurus', 'Nanexa']
        },
        'technologies': {
            'lai_keywords': {
                'core_phrases': ['Extended-Release Injectable', 'Long-Acting Injectable', 'BEPO'],
                'technology_terms_high_precision': ['depot injection', 'once-monthly injection']
            }
        },
        'molecules': {
            'lai_molecules_global': ['olanzapine', 'risperidone', 'buprenorphine']
        },
        'trademarks': {
            'lai_trademarks_global': ['UZEDY', 'TEV-749', 'BEPO', 'PharmaShell']
        }
    }
    
    return watch_domains, canonical_scopes

@patch('vectora_core.matching.bedrock_matcher._call_bedrock_matching')
def test_bedrock_matching_integration(mock_bedrock_call):
    """Test d'intégration du matching Bedrock."""
    print("🧪 Test d'intégration du matching Bedrock")
    
    # Configuration du mock
    mock_bedrock_call.return_value = simulate_bedrock_matching_response()
    
    try:
        from vectora_core.matching import bedrock_matcher
        
        # Données de test
        test_item = {
            'title': create_test_item()['title'],
            'summary': "MedinCell partners with Teva for LAI development using BEPO technology",
            'entities': {
                'companies': ['MedinCell', 'Teva Pharmaceuticals'],
                'molecules': ['olanzapine'],
                'technologies': ['Extended-Release Injectable', 'BEPO'],
                'trademarks': ['TEV-749'],
                'indications': ['schizophrenia']
            },
            'event_type': 'regulatory'
        }
        
        watch_domains, canonical_scopes = create_test_config()
        
        # Test du matching
        result = bedrock_matcher.match_watch_domains_with_bedrock(
            test_item,
            watch_domains,
            canonical_scopes,
            'anthropic.claude-3-sonnet-20240229-v1:0'
        )
        
        # Vérifications
        print(f"✅ Matching réussi: {len(result['matched_domains'])} domaines matchés")
        print(f"📊 Domaines: {result['matched_domains']}")
        
        for domain_id, relevance in result['domain_relevance'].items():
            print(f"   - {domain_id}: score={relevance['score']}, confidence={relevance['confidence']}")
        
        # Vérifier que Bedrock a été appelé
        assert mock_bedrock_call.called, "Bedrock devrait être appelé"
        print("✅ Appel Bedrock simulé avec succès")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test intégration: {e}")
        return False

@patch('vectora_core.normalization.bedrock_client._call_bedrock_with_retry')
@patch('vectora_core.matching.bedrock_matcher._call_bedrock_matching')
def test_normalize_item_with_bedrock_matching(mock_matching_call, mock_normalization_call):
    """Test de la normalisation complète avec matching Bedrock."""
    print("\n🧪 Test normalisation complète avec matching Bedrock")
    
    # Configuration des mocks
    mock_normalization_call.return_value = json.dumps({
        "summary": "MedinCell partners with Teva for LAI development using BEPO technology",
        "event_type": "regulatory",
        "companies_detected": ["MedinCell", "Teva Pharmaceuticals"],
        "molecules_detected": ["olanzapine"],
        "technologies_detected": ["Extended-Release Injectable", "BEPO"],
        "trademarks_detected": ["TEV-749"],
        "indications_detected": ["schizophrenia"],
        "lai_relevance_score": 9,
        "anti_lai_detected": False,
        "pure_player_context": True
    })
    
    mock_matching_call.return_value = simulate_bedrock_matching_response()
    
    try:
        from vectora_core.normalization import normalizer
        
        # Données de test
        raw_item = create_test_item()
        watch_domains, canonical_scopes = create_test_config()
        
        # Test de normalisation avec matching
        result = normalizer.normalize_item(
            raw_item,
            canonical_scopes,
            'anthropic.claude-3-sonnet-20240229-v1:0',
            watch_domains
        )
        
        # Vérifications
        print("✅ Normalisation avec matching réussie")
        print(f"📊 Titre: {result['title'][:50]}...")
        print(f"📊 Entités companies: {result['companies_detected']}")
        print(f"📊 Entités technologies: {result['technologies_detected']}")
        
        # Vérifier les nouveaux champs de matching Bedrock
        if 'bedrock_matched_domains' in result:
            print(f"✅ Matching Bedrock: {result['bedrock_matched_domains']}")
            print(f"📊 Relevance: {list(result.get('bedrock_domain_relevance', {}).keys())}")
        else:
            print("⚠️ Champs matching Bedrock manquants")
        
        # Vérifier que les deux appels Bedrock ont été faits
        assert mock_normalization_call.called, "Normalisation Bedrock devrait être appelée"
        assert mock_matching_call.called, "Matching Bedrock devrait être appelé"
        print("✅ Double appel Bedrock (normalisation + matching) simulé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test normalisation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test de la gestion d'erreurs."""
    print("\n🧪 Test gestion d'erreurs matching Bedrock")
    
    try:
        from vectora_core.matching import bedrock_matcher
        
        # Test avec watch_domains vides
        result = bedrock_matcher.match_watch_domains_with_bedrock(
            {'title': 'test'},
            [],  # Pas de domaines
            {},
            'test-model'
        )
        
        assert result['matched_domains'] == [], "Devrait retourner liste vide"
        print("✅ Gestion watch_domains vides OK")
        
        # Test avec erreur Bedrock simulée
        with patch('vectora_core.matching.bedrock_matcher._call_bedrock_matching') as mock_call:
            mock_call.side_effect = Exception("Bedrock timeout")
            
            watch_domains, canonical_scopes = create_test_config()
            
            result = bedrock_matcher.match_watch_domains_with_bedrock(
                {'title': 'test', 'summary': 'test', 'entities': {}, 'event_type': 'other'},
                watch_domains,
                canonical_scopes,
                'test-model'
            )
            
            assert result['matched_domains'] == [], "Devrait fallback sur liste vide"
            assert 'bedrock_error' in result, "Devrait inclure l'erreur"
            print("✅ Gestion erreur Bedrock OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test gestion d'erreurs: {e}")
        return False

def main():
    """Exécution de tous les tests de simulation."""
    print("🚀 Tests de simulation du matching Bedrock")
    print("=" * 60)
    
    tests = [
        test_bedrock_matching_integration,
        test_normalize_item_with_bedrock_matching,
        test_error_handling
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Erreur dans {test_func.__name__}: {e}")
            results.append(False)
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 Résumé des tests de simulation")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("🎉 Tous les tests de simulation sont passés!")
        print("✅ Le matching Bedrock est prêt pour le déploiement")
        print("\n🚀 Prochaine étape: Exécuter le déploiement avec:")
        print("   python scripts/deploy_bedrock_matching_patch.py")
    else:
        print("⚠️ Certains tests ont échoué")
        print("❌ Corriger les erreurs avant le déploiement")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)