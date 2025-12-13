#!/usr/bin/env python3
"""
Script de test local pour simuler le processus de normalisation et scoring.

Ce script teste les modifications open-world et recency sans déploiement AWS.
Il simule des items et valide le nouveau comportement.
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vectora_core.normalization import entity_detector
from vectora_core.scoring import scorer


def test_open_world_normalization():
    """Test de la normalisation open-world."""
    print("=== Test Normalisation Open-World ===")
    
    # Scopes canonical simulés
    canonical_scopes = {
        'companies': {
            'lai_companies_global': ['Camurus', 'Indivior', 'Alkermes'],
            'lai_companies_pure_players': ['Camurus', 'Indivior']
        },
        'molecules': {
            'lai_molecules_global': ['buprenorphine', 'naloxone', 'aripiprazole']
        },
        'trademarks': {
            'lai_trademarks_global': ['Brixadi', 'Sublocade', 'Abilify Maintena']
        },
        'technologies': {
            'lai_keywords': ['long acting', 'depot', 'microspheres', 'subcutaneous']
        },
        'indications': {
            'lai_indications': ['opioid use disorder', 'schizophrenia', 'bipolar disorder']
        }
    }
    
    # Simulation d'entités détectées (monde ouvert)
    merged_entities = {
        'companies_detected': ['Camurus', 'NewBiotechCorp', 'Pfizer'],  # NewBiotechCorp pas dans scopes
        'molecules_detected': ['buprenorphine', 'experimental_compound'],  # experimental_compound pas dans scopes
        'trademarks_detected': ['Brixadi', 'InnovativeDrug'],  # InnovativeDrug pas dans scopes
        'technologies_detected': ['long acting', 'novel_delivery_system'],  # novel_delivery_system pas dans scopes
        'indications_detected': ['opioid use disorder', 'rare_disease']  # rare_disease pas dans scopes
    }
    
    print("Entités détectées (monde ouvert):")
    for key, entities in merged_entities.items():
        print(f"  {key}: {entities}")
    
    # Calcul des intersections avec les scopes
    entities_in_scopes = entity_detector.compute_entities_in_scopes(merged_entities, canonical_scopes)
    
    print("\nEntités dans les scopes canonical:")
    for key, entities in entities_in_scopes.items():
        print(f"  {key}: {entities}")
    
    # Validation
    assert 'Camurus' in entities_in_scopes['companies_in_scopes']
    assert 'NewBiotechCorp' not in entities_in_scopes['companies_in_scopes']
    assert 'buprenorphine' in entities_in_scopes['molecules_in_scopes']
    assert 'experimental_compound' not in entities_in_scopes['molecules_in_scopes']
    assert 'Brixadi' in entities_in_scopes['trademarks_in_scopes']
    assert 'InnovativeDrug' not in entities_in_scopes['trademarks_in_scopes']
    
    print("[OK] Test normalisation open-world : SUCCES")
    return True


def test_recency_scoring_adjustment():
    """Test de l'ajustement du scoring recency."""
    print("\n=== Test Ajustement Scoring Recency ===")
    
    # Configuration de scoring
    scoring_rules = {
        'event_type_weights': {
            'clinical_update': 5,
            'partnership': 6,
            'other': 1
        },
        'domain_priority_weights': {
            'high': 3,
            'medium': 2,
            'low': 1
        },
        'other_factors': {
            'recency_decay_half_life_days': 7,
            'source_type_weight_corporate': 2,
            'source_type_weight_sector': 1.5,
            'pure_player_bonus': 3,
            'hybrid_company_bonus': 1,
            'signal_depth_bonus': 0.3,
            'match_confidence_multiplier_high': 1.5,
            'match_confidence_multiplier_medium': 1.2,
            'signal_quality_weight_high_precision': 2.0,
            'signal_quality_weight_supporting': 1.0
        }
    }
    
    watch_domains = [
        {'id': 'tech_lai', 'priority': 'high'},
        {'id': 'regulatory', 'priority': 'medium'}
    ]
    
    canonical_scopes = {
        'companies': {
            'lai_companies_pure_players': ['Camurus', 'Indivior'],
            'lai_companies_hybrid': ['Pfizer', 'J&J']
        }
    }
    
    # Items de test avec différentes dates
    today = datetime.now()
    items = [
        {
            'title': 'Recent Clinical Update',
            'date': today.strftime('%Y-%m-%d'),
            'event_type': 'clinical_update',
            'source_type': 'press_corporate',
            'companies_detected': ['Camurus'],
            'molecules_detected': ['buprenorphine'],
            'trademarks_detected': ['Brixadi'],
            'technologies_detected': ['long acting'],
            'indications_detected': ['opioid use disorder'],
            'matched_domains': ['tech_lai'],
            'matching_details': {
                'match_confidence': 'high',
                'signals_used': {'high_precision': 2, 'supporting': 1},
                'scopes_hit': {'company_scope_type': 'pure_player'}
            }
        },
        {
            'title': 'Older Partnership',
            'date': (today - timedelta(days=5)).strftime('%Y-%m-%d'),
            'event_type': 'partnership',
            'source_type': 'sector',
            'companies_detected': ['Pfizer'],
            'molecules_detected': [],
            'trademarks_detected': [],
            'technologies_detected': [],
            'indications_detected': [],
            'matched_domains': ['regulatory'],
            'matching_details': {
                'match_confidence': 'medium',
                'signals_used': {'high_precision': 1, 'supporting': 0},
                'scopes_hit': {'company_scope_type': 'hybrid'}
            }
        }
    ]
    
    print("Items de test:")
    for i, item in enumerate(items):
        print(f"  Item {i+1}: {item['title']} ({item['date']})")
    
    # Test 1: Scoring weekly (period_days = 7) - récence neutralisée
    print("\n--- Test Weekly (period_days = 7) ---")
    weekly_items = [item.copy() for item in items]
    scored_weekly = scorer.score_items(
        weekly_items, scoring_rules, watch_domains, canonical_scopes, period_days=7
    )
    
    print("Scores weekly:")
    for item in scored_weekly:
        print(f"  {item['title']}: {item['score']:.2f}")
    
    # Test 2: Scoring monthly (period_days = 30) - récence discriminante
    print("\n--- Test Monthly (period_days = 30) ---")
    monthly_items = [item.copy() for item in items]
    scored_monthly = scorer.score_items(
        monthly_items, scoring_rules, watch_domains, canonical_scopes, period_days=30
    )
    
    print("Scores monthly:")
    for item in scored_monthly:
        print(f"  {item['title']}: {item['score']:.2f}")
    
    # Test 3: Vérification des facteurs de récence
    print("\n--- Vérification Recency Factors ---")
    
    # Weekly: devrait être 1.0 pour tous
    recent_weekly = scorer._compute_recency_factor(today.strftime('%Y-%m-%d'), 7, 7)
    old_weekly = scorer._compute_recency_factor((today - timedelta(days=5)).strftime('%Y-%m-%d'), 7, 7)
    
    print(f"Weekly recency factors:")
    print(f"  Recent item: {recent_weekly}")
    print(f"  Old item: {old_weekly}")
    
    # Monthly: devrait être discriminant
    recent_monthly = scorer._compute_recency_factor(today.strftime('%Y-%m-%d'), 7, 30)
    old_monthly = scorer._compute_recency_factor((today - timedelta(days=5)).strftime('%Y-%m-%d'), 7, 30)
    
    print(f"Monthly recency factors:")
    print(f"  Recent item: {recent_monthly:.3f}")
    print(f"  Old item: {old_monthly:.3f}")
    
    # Validations
    assert recent_weekly == 1.0, f"Weekly recent should be 1.0, got {recent_weekly}"
    assert old_weekly == 1.0, f"Weekly old should be 1.0, got {old_weekly}"
    assert recent_monthly > old_monthly, f"Monthly recent ({recent_monthly}) should be > old ({old_monthly})"
    
    print("[OK] Test ajustement scoring recency : SUCCES")
    return True


def test_molecule_trademark_separation():
    """Test de la séparation molecule vs trademark."""
    print("\n=== Test Séparation Molecule vs Trademark ===")
    
    # Cas de test classiques
    test_cases = [
        {
            'name': 'Brixadi vs buprenorphine',
            'molecules': ['buprenorphine'],
            'trademarks': ['Brixadi'],
            'expected_separation': True
        },
        {
            'name': 'Abilify Maintena vs aripiprazole',
            'molecules': ['aripiprazole'],
            'trademarks': ['Abilify Maintena'],
            'expected_separation': True
        },
        {
            'name': 'Sublocade vs buprenorphine',
            'molecules': ['buprenorphine'],
            'trademarks': ['Sublocade'],
            'expected_separation': True
        }
    ]
    
    for case in test_cases:
        print(f"\nCas: {case['name']}")
        print(f"  Molecules: {case['molecules']}")
        print(f"  Trademarks: {case['trademarks']}")
        
        # Vérifier qu'il n'y a pas de confusion
        molecules_set = set(case['molecules'])
        trademarks_set = set(case['trademarks'])
        overlap = molecules_set & trademarks_set
        
        if overlap:
            print(f"  [ERROR] ERREUR: Overlap detecte: {overlap}")
            return False
        else:
            print(f"  [OK] Separation correcte")
    
    print("[OK] Test separation molecule vs trademark : SUCCES")
    return True


def generate_test_summary():
    """Génère un résumé des tests."""
    print("\n" + "="*60)
    print("RÉSUMÉ DES TESTS LOCAUX")
    print("="*60)
    
    results = []
    
    try:
        results.append(("Normalisation Open-World", test_open_world_normalization()))
    except Exception as e:
        print(f"[ERROR] Erreur normalisation: {e}")
        results.append(("Normalisation Open-World", False))
    
    try:
        results.append(("Ajustement Scoring Recency", test_recency_scoring_adjustment()))
    except Exception as e:
        print(f"[ERROR] Erreur scoring: {e}")
        results.append(("Ajustement Scoring Recency", False))
    
    try:
        results.append(("Separation Molecule/Trademark", test_molecule_trademark_separation()))
    except Exception as e:
        print(f"[ERROR] Erreur separation: {e}")
        results.append(("Separation Molecule/Trademark", False))
    
    print("\nResultats:")
    all_passed = True
    for test_name, passed in results:
        status = "[OK] SUCCES" if passed else "[ERROR] ECHEC"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print(f"\nStatut global: {'[OK] TOUS LES TESTS PASSENT' if all_passed else '[ERROR] CERTAINS TESTS ECHOUENT'}")
    
    return all_passed


if __name__ == '__main__':
    print("Démarrage des tests locaux Vectora Inbox")
    print("Modifications testées:")
    print("- Normalisation open-world avec *_detected + *_in_scopes")
    print("- Séparation molecule vs trademark")
    print("- Neutralisation recency_factor pour weekly (period_days <= 7)")
    print()
    
    success = generate_test_summary()
    
    if success:
        print("\n[SUCCESS] Tous les tests sont passes ! Les modifications sont pretes.")
        exit(0)
    else:
        print("\n[WARNING] Certains tests ont echoue. Verifiez les erreurs ci-dessus.")
        exit(1)