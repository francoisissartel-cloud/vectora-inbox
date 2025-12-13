#!/usr/bin/env python3
"""
Script de validation complète des corrections Phases 1-3.

Ce script valide que toutes les corrections ont été appliquées correctement
avant le déploiement sur AWS.
"""

import json
import sys
from pathlib import Path

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def validate_all_corrections():
    """Validation complète des corrections Phases 1-3."""
    
    print("[VALIDATION] Validation complète des corrections Phases 1-3")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Vérifier les modifications bedrock_client.py
    print("\n[TEST 1] Validation corrections bedrock_client.py...")
    try:
        from vectora_core.normalization import bedrock_client
        
        # Vérifier que la fonction existe
        assert hasattr(bedrock_client, 'normalize_item_with_bedrock')
        print("  [OK] Fonction normalize_item_with_bedrock présente")
        
        # Tester la construction du prompt (simulation)
        test_prompt = bedrock_client._build_normalization_prompt(
            "Test UZEDY Extended-Release Injectable",
            {'companies': ['MedinCell'], 'molecules': ['risperidone'], 'technologies': ['Extended-Release Injectable']},
            None
        )
        
        # Vérifier que le prompt contient les éléments LAI
        assert "LAI TECHNOLOGY FOCUS" in test_prompt
        assert "Extended-Release Injectable" in test_prompt
        assert "TRADEMARKS to detect" in test_prompt
        assert "lai_relevance_score" in test_prompt
        print("  [OK] Prompt Bedrock contient les corrections LAI")
        
    except Exception as e:
        print(f"  [ERROR] Test bedrock_client échoué: {e}")
        all_tests_passed = False
    
    # Test 2: Vérifier les modifications normalizer.py
    print("\n[TEST 2] Validation corrections normalizer.py...")
    try:
        from vectora_core.normalization import normalizer
        
        # Vérifier que la fonction existe
        assert hasattr(normalizer, 'normalize_item')
        print("  [OK] Fonction normalize_item présente")
        
        # Vérifier que les nouveaux champs sont dans le code (inspection du code)
        import inspect
        source = inspect.getsource(normalizer.normalize_item)
        assert "trademarks_detected" in source
        assert "lai_relevance_score" in source
        assert "anti_lai_detected" in source
        assert "pure_player_context" in source
        print("  [OK] Nouveaux champs LAI présents dans normalize_item")
        
    except Exception as e:
        print(f"  [ERROR] Test normalizer échoué: {e}")
        all_tests_passed = False
    
    # Test 3: Vérifier les modifications matcher.py
    print("\n[TEST 3] Validation corrections matcher.py...")
    try:
        from vectora_core.matching import matcher
        
        # Vérifier que la fonction contextual_matching existe
        assert hasattr(matcher, 'contextual_matching')
        print("  [OK] Fonction contextual_matching présente")
        
        # Vérifier que le matching contextuel est activé
        import inspect
        source = inspect.getsource(matcher.match_items_to_domains)
        assert "contextual_matching(item)" in source
        assert "ACTIVÉ" in source or "accepté par matching contextuel" in source
        print("  [OK] Matching contextuel activé dans le code")
        
    except Exception as e:
        print(f"  [ERROR] Test matcher échoué: {e}")
        all_tests_passed = False
    
    # Test 4: Vérifier html_extractor_robust.py
    print("\n[TEST 4] Validation html_extractor_robust.py...")
    try:
        from vectora_core.ingestion import html_extractor_robust
        
        # Vérifier que les fonctions de fallback existent
        assert hasattr(html_extractor_robust, 'extract_content_with_fallback')
        assert hasattr(html_extractor_robust, 'create_minimal_item_from_title')
        print("  [OK] Fonctions de fallback HTML présentes")
        
    except Exception as e:
        print(f"  [ERROR] Test html_extractor_robust échoué: {e}")
        all_tests_passed = False
    
    # Test 5: Validation des configurations
    print("\n[TEST 5] Validation des configurations...")
    try:
        from vectora_core.config import loader
        
        # Charger les scopes pour vérifier qu'ils sont corrects
        scopes = loader.load_canonical_scopes_local()
        
        # Vérifier technology_scopes.yaml
        tech_scopes = scopes.get('technologies', {})
        lai_keywords = tech_scopes.get('lai_keywords', {})
        assert 'technology_terms_high_precision' in lai_keywords
        assert any('Extended-Release Injectable' in str(terms) for terms in lai_keywords.values())
        print("  [OK] Technology scopes LAI présents")
        
        # Vérifier trademark_scopes.yaml
        trademark_scopes = scopes.get('trademarks', {})
        lai_trademarks = trademark_scopes.get('lai_trademarks_global', [])
        assert 'Uzedy' in lai_trademarks or 'UZEDY' in str(lai_trademarks)
        print("  [OK] Trademark scopes LAI présents")
        
    except Exception as e:
        print(f"  [ERROR] Test configurations échoué: {e}")
        all_tests_passed = False
    
    # Résumé final
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("[SUCCESS] Toutes les corrections ont été validées avec succès!")
        print("\n[READY] Le code est prêt pour déploiement AWS")
        print("\n[NEXT STEPS]:")
        print("  1. Packager les Lambdas avec les corrections")
        print("  2. Déployer sur AWS dev")
        print("  3. Lancer un run de test end-to-end")
        print("  4. Valider les résultats")
        return True
    else:
        print("[FAILURE] Certaines validations ont échoué")
        print("\n[ACTION REQUIRED] Corriger les problèmes avant déploiement")
        return False

if __name__ == "__main__":
    success = validate_all_corrections()
    if not success:
        sys.exit(1)