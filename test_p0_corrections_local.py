#!/usr/bin/env python3
"""
Script de test local pour valider les corrections P0 avant déploiement.

Ce script teste les 3 corrections P0 :
- P0-1 : Détection technology LAI améliorée
- P0-2 : Exclusions HR/finance
- P0-3 : Extraction HTML robuste
"""

import json
import sys
import os
from typing import Dict, Any, List

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_p0_1_bedrock_technology_detection():
    """Test P0-1 : Amélioration détection technology LAI par Bedrock."""
    print("\n=== TEST P0-1 : Bedrock Technology Detection ===")
    
    try:
        from vectora_core.normalization.bedrock_client import _build_normalization_prompt
        
        # Mock canonical examples
        canonical_examples = {
            'companies': ['Nanexa', 'MedinCell', 'Moderna', 'Teva'],
            'molecules': ['risperidone', 'olanzapine'],
            'technologies': ['Extended-Release Injectable', 'PharmaShell®', 'LAI', 'depot injection']
        }
        
        # Test cases
        test_cases = [
            {
                'name': 'UZEDY Extended-Release Injectable',
                'text': 'FDA Approves Expanded Indication for UZEDY® (risperidone) Extended-Release Injectable Suspension',
                'expected_terms': ['Extended-Release Injectable', 'UZEDY®']
            },
            {
                'name': 'Nanexa PharmaShell®',
                'text': 'Nanexa and Moderna enter into license agreement for PharmaShell®-based products',
                'expected_terms': ['PharmaShell®']
            },
            {
                'name': 'LAI Generic',
                'text': 'Olanzapine LAI submission to FDA for regulatory approval',
                'expected_terms': ['LAI']
            }
        ]
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            
            # Construire le prompt amélioré
            prompt = _build_normalization_prompt(test_case['text'], canonical_examples)
            
            # Vérifier que les termes LAI sont dans le prompt
            lai_section_present = "SPECIAL FOCUS - LAI TECHNOLOGY DETECTION" in prompt
            expected_terms_in_prompt = all(term in prompt for term in test_case['expected_terms'])
            
            print(f"    LAI section present: {lai_section_present}")
            print(f"    Expected terms in prompt: {expected_terms_in_prompt}")
            
            if lai_section_present and expected_terms_in_prompt:
                print(f"    PASS: {test_case['name']}")
            else:
                print(f"    FAIL: {test_case['name']}")
                return False
        
        print("\n  P0-1 Bedrock Technology Detection - ALL TESTS PASS")
        return True
        
    except Exception as e:
        print(f"  P0-1 Test failed with error: {e}")
        return False


def test_p0_2_exclusions_hr_finance():
    """Test P0-2 : Exclusions HR/finance au runtime."""
    print("\n=== TEST P0-2 : Exclusions HR/Finance ===")
    
    try:
        # Import du module d'exclusion
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/lambdas/engine'))
        from exclusion_filter import apply_exclusion_filters
        
        # Mock exclusion scopes
        exclusion_scopes = {
            'hr_recruitment_terms': ['hiring', 'seeks', 'recruiting', 'process engineer', 'quality director'],
            'financial_reporting_terms': ['financial results', 'earnings', 'consolidated results', 'interim report']
        }
        
        # Test cases
        test_cases = [
            {
                'name': 'DelSiTech HR Hiring',
                'item': {'title': 'DelSiTech is Hiring a Process Engineer', 'summary': 'Join our team'},
                'expected_excluded': True,
                'expected_reason_contains': 'hiring'
            },
            {
                'name': 'DelSiTech Quality Director',
                'item': {'title': 'DelSiTech Seeks an Experienced Quality Director', 'summary': 'Leadership role'},
                'expected_excluded': True,
                'expected_reason_contains': 'seeks'
            },
            {
                'name': 'MedinCell Financial Results',
                'item': {'title': 'MedinCell Publishes Consolidated Financial Results', 'summary': 'Q3 earnings'},
                'expected_excluded': True,
                'expected_reason_contains': 'financial results'
            },
            {
                'name': 'MedinCell LAI Partnership',
                'item': {'title': 'MedinCell Partnership for LAI Development', 'summary': 'Long-acting injectable collaboration'},
                'expected_excluded': False,
                'expected_reason_contains': 'Not excluded'
            }
        ]
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            
            is_allowed, reason = apply_exclusion_filters(test_case['item'], exclusion_scopes)
            is_excluded = not is_allowed
            
            print(f"    Expected excluded: {test_case['expected_excluded']}")
            print(f"    Actually excluded: {is_excluded}")
            print(f"    Reason: {reason}")
            
            if (is_excluded == test_case['expected_excluded'] and 
                test_case['expected_reason_contains'].lower() in reason.lower()):
                print(f"    PASS: {test_case['name']}")
            else:
                print(f"    FAIL: {test_case['name']}")
                return False
        
        print("\n  P0-2 Exclusions HR/Finance - ALL TESTS PASS")
        return True
        
    except Exception as e:
        print(f"  P0-2 Test failed with error: {e}")
        return False


def test_p0_3_html_extraction_robust():
    """Test P0-3 : Extraction HTML robuste."""
    print("\n=== TEST P0-3 : HTML Extraction Robust ===")
    
    try:
        from vectora_core.ingestion.html_extractor_robust import (
            _extract_companies_from_title,
            _extract_technologies_from_title,
            _extract_trademarks_from_title,
            create_minimal_item_from_title
        )
        
        # Test cases pour extraction depuis titre
        test_cases = [
            {
                'name': 'Nanexa/Moderna PharmaShell®',
                'title': 'Nanexa and Moderna enter into license agreement for PharmaShell®-based products',
                'expected_companies': ['Nanexa', 'Moderna'],
                'expected_technologies': ['PharmaShell®'],
                'expected_trademarks': ['PharmaShell®']
            },
            {
                'name': 'UZEDY Extended-Release Injectable',
                'title': 'FDA Approves UZEDY® Extended-Release Injectable Suspension',
                'expected_companies': [],
                'expected_technologies': ['Extended-Release Injectable'],
                'expected_trademarks': ['UZEDY®']
            },
            {
                'name': 'MedinCell LAI Development',
                'title': 'MedinCell announces LAI technology advancement',
                'expected_companies': ['MedinCell'],
                'expected_technologies': ['LAI'],
                'expected_trademarks': []
            }
        ]
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            
            companies = _extract_companies_from_title(test_case['title'])
            technologies = _extract_technologies_from_title(test_case['title'])
            trademarks = _extract_trademarks_from_title(test_case['title'])
            
            print(f"    Expected companies: {test_case['expected_companies']}")
            print(f"    Detected companies: {companies}")
            print(f"    Expected technologies: {test_case['expected_technologies']}")
            print(f"    Detected technologies: {technologies}")
            print(f"    Expected trademarks: {test_case['expected_trademarks']}")
            print(f"    Detected trademarks: {trademarks}")
            
            companies_match = set(companies) >= set(test_case['expected_companies'])
            technologies_match = set(technologies) >= set(test_case['expected_technologies'])
            trademarks_match = set(trademarks) >= set(test_case['expected_trademarks'])
            
            if companies_match and technologies_match and trademarks_match:
                print(f"    PASS: {test_case['name']}")
            else:
                print(f"    FAIL: {test_case['name']}")
                return False
        
        # Test création d'item minimal
        print(f"\n  Testing: Minimal Item Creation")
        raw_item = {
            'title': 'Nanexa and Moderna enter into license agreement for PharmaShell®-based products',
            'url': 'https://nanexa.com/news/moderna-partnership',
            'source_key': 'press_corporate__nanexa',
            'source_type': 'corporate_press',
            'published_at': '2025-12-11'
        }
        
        minimal_item = create_minimal_item_from_title(raw_item)
        
        has_companies = len(minimal_item.get('companies_detected', [])) > 0
        has_technologies = len(minimal_item.get('technologies_detected', [])) > 0
        has_extraction_status = minimal_item.get('extraction_status') == 'title_only_fallback'
        
        print(f"    Has companies detected: {has_companies}")
        print(f"    Has technologies detected: {has_technologies}")
        print(f"    Has extraction status: {has_extraction_status}")
        
        if has_companies and has_technologies and has_extraction_status:
            print(f"    PASS: Minimal Item Creation")
        else:
            print(f"    FAIL: Minimal Item Creation")
            return False
        
        print("\n  P0-3 HTML Extraction Robust - ALL TESTS PASS")
        return True
        
    except Exception as e:
        print(f"  P0-3 Test failed with error: {e}")
        return False


def main():
    """Exécute tous les tests P0."""
    print("VECTORA INBOX - TESTS CORRECTIONS P0")
    print("=" * 50)
    
    results = []
    
    # Test P0-1
    results.append(test_p0_1_bedrock_technology_detection())
    
    # Test P0-2
    results.append(test_p0_2_exclusions_hr_finance())
    
    # Test P0-3
    results.append(test_p0_3_html_extraction_robust())
    
    # Résumé
    print("\n" + "=" * 50)
    print("RESUME DES TESTS P0")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests réussis : {passed}/{total}")
    
    if passed == total:
        print("TOUS LES TESTS P0 SONT PASSES")
        print("Pret pour le deploiement AWS")
        return 0
    else:
        print("CERTAINS TESTS P0 ONT ECHOUE")
        print("Corrections necessaires avant deploiement")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)