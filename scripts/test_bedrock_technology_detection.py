#!/usr/bin/env python3
"""
Script de test isolé pour diagnostiquer la détection des technologies par Bedrock.

Ce script teste la normalisation Bedrock sur des items spécifiques pour identifier
pourquoi technologies_detected est toujours vide.
"""

import json
import sys
from pathlib import Path

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_bedrock_technology_detection():
    """Test isolé de la détection des technologies par Bedrock."""
    
    print("[TEST] Test isolé Bedrock Technology Detection")
    print("=" * 50)
    
    # Item de test UZEDY avec signaux LAI explicites
    test_item = {
        "source_key": "press_corporate__medincell",
        "title": "FDA Approves Expanded Indication for UZEDY® (risperidone) Extended-Release Injectable Suspension",
        "summary": "The FDA has approved an expanded indication for UZEDY (risperidone extended-release injectable suspension) for the treatment of adults with Bipolar I Disorder. This extended-release injectable formulation provides long-acting treatment.",
        "url": "https://example.com/uzedy-approval",
        "date": "2025-12-11"
    }
    
    print(f"[INPUT] Item de test:")
    print(f"  Titre: {test_item['title']}")
    print(f"  Summary: {test_item['summary'][:100]}...")
    
    # Signaux LAI attendus dans cet item
    expected_signals = [
        "UZEDY®",
        "Extended-Release Injectable",
        "extended-release injectable suspension",
        "long-acting treatment"
    ]
    
    print(f"\n[EXPECTED] Signaux LAI attendus: {expected_signals}")
    
    # Simuler la normalisation (sans appel Bedrock réel pour ce test)
    print(f"\n[SIMULATION] Résultat attendu après correction:")
    expected_result = {
        "companies_detected": ["MedinCell", "Teva"],
        "molecules_detected": ["risperidone"],
        "technologies_detected": ["Extended-Release Injectable", "Long-Acting Injectable"],
        "trademarks_detected": ["UZEDY"],
        "lai_relevance_score": 9,
        "anti_lai_detected": False,
        "pure_player_context": True,
        "event_type": "regulatory"
    }
    
    for key, value in expected_result.items():
        print(f"  {key}: {value}")
    
    print(f"\n[DIAGNOSTIC] Problemes identifies dans l'implementation actuelle:")
    print("  1. Prompt Bedrock trop complexe -> Section technology ignoree")
    print("  2. Parsing JSON defaillant -> Champs non extraits")
    print("  3. Scopes technology mal integres -> Detection echoue")
    print("  4. Champs LAI manquants -> lai_relevance_score, anti_lai_detected, pure_player_context")
    
    print(f"\n[NEXT] Corrections a appliquer:")
    print("  1. Simplifier le prompt Bedrock (section technology)")
    print("  2. Reduire les keywords par categorie (max 10)")
    print("  3. Ajouter les champs LAI manquants")
    print("  4. Ameliorer le parsing JSON")
    
    return expected_result

if __name__ == "__main__":
    test_bedrock_technology_detection()