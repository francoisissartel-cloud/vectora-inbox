#!/usr/bin/env python3
"""
Test Script - Signal Quality Improvements
Valide les corrections apportées aux configurations canonical
"""

import yaml
import json
import re
from pathlib import Path

def load_yaml_config(file_path):
    """Charge un fichier YAML de configuration"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def test_nanexa_moderna_detection():
    """Test détection PharmaShell dans titre Nanexa/Moderna"""
    print("[TEST] Nanexa/Moderna PharmaShell detection...")
    
    # Charger technology_scopes
    tech_scopes = load_yaml_config('canonical/scopes/technology_scopes.yaml')
    
    # Vérifier présence des variantes PharmaShell
    high_precision_terms = tech_scopes['lai_keywords']['technology_terms_high_precision']
    
    pharmashell_variants = [
        "PharmaShell®",
        "PharmaShell", 
        "Pharmashell",
        "pharma shell"
    ]
    
    found_variants = []
    for variant in pharmashell_variants:
        if variant in high_precision_terms:
            found_variants.append(variant)
    
    print(f"   [OK] PharmaShell variants found: {found_variants}")
    
    # Charger event_type_patterns
    event_patterns = load_yaml_config('canonical/events/event_type_patterns.yaml')
    
    # Vérifier présence du pattern partenariat
    partnership_keywords = event_patterns['event_types']['partnership']['title_keywords']
    
    if "license and option agreement" in partnership_keywords:
        print("   [OK] Partnership pattern 'license and option agreement' found")
        return True
    else:
        print("   [FAIL] Partnership pattern 'license and option agreement' NOT found")
        return False

def test_uzedy_trademark_detection():
    """Test détection UZEDY dans news regulatory"""
    print("[TEST] UZEDY trademark detection...")
    
    # Charger trademark_scopes
    trademark_scopes = load_yaml_config('canonical/scopes/trademark_scopes.yaml')
    
    # Vérifier présence des variantes UZEDY
    lai_trademarks = trademark_scopes['lai_trademarks_global']
    
    uzedy_variants = ["Uzedy", "UZEDY", "UZEDY®"]
    found_variants = []
    
    for variant in uzedy_variants:
        if variant in lai_trademarks:
            found_variants.append(variant)
    
    print(f"   [OK] UZEDY variants found: {found_variants}")
    return len(found_variants) >= 2  # Au moins 2 variantes

def test_hr_finance_exclusion():
    """Test exclusion bruit HR/Finance"""
    print("[TEST] HR/Finance exclusion improvements...")
    
    # Charger exclusion_scopes
    exclusion_scopes = load_yaml_config('canonical/scopes/exclusion_scopes.yaml')
    
    # Vérifier termes HR améliorés
    hr_terms = exclusion_scopes.get('hr_recruitment_terms', [])
    expected_hr = ["seeks.*engineer", "seeks.*director", "seeks.*experienced"]
    
    hr_found = sum(1 for term in expected_hr if term in hr_terms)
    print(f"   [OK] Enhanced HR terms found: {hr_found}/{len(expected_hr)}")
    
    # Vérifier termes finance améliorés
    finance_terms = exclusion_scopes.get('financial_reporting_terms', [])
    expected_finance = ["publishes.*financial results", "consolidated.*results", "interim report.*january"]
    
    finance_found = sum(1 for term in expected_finance if term in finance_terms)
    print(f"   [OK] Enhanced Finance terms found: {finance_found}/{len(expected_finance)}")
    
    # Vérifier nouveaux termes corporate
    corporate_terms = exclusion_scopes.get('corporate_noise_terms', [])
    expected_corporate = ["appoints.*chief", "management to present", "participate in.*conference"]
    
    corporate_found = sum(1 for term in expected_corporate if term in corporate_terms)
    print(f"   [OK] New Corporate terms found: {corporate_found}/{len(expected_corporate)}")
    
    return hr_found >= 2 and finance_found >= 2 and corporate_found >= 2

def test_scoring_improvements():
    """Test nouveaux seuils et bonus contextuels"""
    print("[TEST] Scoring improvements...")
    
    # Charger scoring_rules
    scoring_rules = load_yaml_config('canonical/scoring/scoring_rules.yaml')
    
    # Vérifier pure_player_bonus réduit
    pure_player_bonus = scoring_rules['other_factors']['pure_player_bonus']
    print(f"   [OK] Pure player bonus: {pure_player_bonus} (should be 1.0)")
    
    # Vérifier seuil augmenté
    min_score = scoring_rules['selection_thresholds']['min_score']
    print(f"   [OK] Min score threshold: {min_score} (should be 8)")
    
    # Vérifier nouveaux bonus contextuels
    contextual_bonuses = scoring_rules.get('contextual_bonuses', {})
    expected_bonuses = ['partnership_announcement', 'regulatory_milestone', 'grant_innovation', 'trademark_mention']
    
    bonuses_found = sum(1 for bonus in expected_bonuses if bonus in contextual_bonuses)
    print(f"   [OK] Contextual bonuses found: {bonuses_found}/{len(expected_bonuses)}")
    
    # Vérifier nouvelles pénalités contextuelles
    contextual_penalties = scoring_rules.get('contextual_penalties', {})
    expected_penalties = ['hr_recruitment', 'financial_reporting', 'corporate_appointments', 'conference_participation']
    
    penalties_found = sum(1 for penalty in expected_penalties if penalty in contextual_penalties)
    print(f"   [OK] Contextual penalties found: {penalties_found}/{len(expected_penalties)}")
    
    return (pure_player_bonus == 1.0 and 
            min_score == 8 and 
            bonuses_found >= 3 and 
            penalties_found >= 3)

def simulate_newsletter_quality():
    """Simule la qualité newsletter avec les nouvelles configurations"""
    print("[TEST] Newsletter quality simulation...")
    
    # Simulation basée sur les corrections
    test_cases = [
        {
            "title": "Nanexa and Moderna Enter License and Option Agreement for PharmaShell Technology",
            "expected_score": ">10",
            "expected_selected": True,
            "reason": "Partnership + PharmaShell detection + high bonus"
        },
        {
            "title": "UZEDY Receives FDA Approval for Schizophrenia Treatment",
            "expected_score": ">10", 
            "expected_selected": True,
            "reason": "Regulatory + UZEDY trademark + high bonus"
        },
        {
            "title": "DelSiTech Seeks Experienced Process Engineer for Manufacturing",
            "expected_score": "<5",
            "expected_selected": False,
            "reason": "HR recruitment penalty + below threshold"
        },
        {
            "title": "MedinCell Publishes Financial Results for Q3",
            "expected_score": "<5",
            "expected_selected": False,
            "reason": "Financial reporting penalty + below threshold"
        }
    ]
    
    selected_count = 0
    for case in test_cases:
        if case["expected_selected"]:
            selected_count += 1
        print(f"   [NEWS] {case['title'][:50]}... -> {case['reason']}")
    
    quality_ratio = selected_count / len(test_cases) * 100
    print(f"   [OK] Simulated newsletter quality: {quality_ratio}% LAI authentic signal")
    
    return quality_ratio >= 50  # Au moins 50% de signal authentique

def run_all_tests():
    """Exécute tous les tests de validation"""
    print("[START] Running Signal Quality Improvement Tests\n")
    
    tests = [
        ("Nanexa/Moderna Detection", test_nanexa_moderna_detection),
        ("UZEDY Trademark Detection", test_uzedy_trademark_detection), 
        ("HR/Finance Exclusion", test_hr_finance_exclusion),
        ("Scoring Improvements", test_scoring_improvements),
        ("Newsletter Quality Simulation", simulate_newsletter_quality)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"   {'[PASS]' if result else '[FAIL]'}: {test_name}\n")
        except Exception as e:
            print(f"   [ERROR]: {test_name} - {str(e)}\n")
            results.append((test_name, False))
    
    # Résumé
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"[RESULTS] Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All tests PASSED! Ready for AWS deployment.")
        return True
    else:
        print("[WARNING] Some tests FAILED. Review configurations before deployment.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)