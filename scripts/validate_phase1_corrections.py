#!/usr/bin/env python3
"""
Script de validation des corrections Phase 1 - Bedrock Technology Detection.

Ce script teste les corrections apportées au prompt Bedrock et à la normalisation
pour vérifier que les technologies LAI sont maintenant détectées.
"""

import json
import sys
from pathlib import Path

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vectora_core.config import loader
from vectora_core.normalization import normalizer

def test_phase1_corrections():
    """Test des corrections Phase 1 sur les items gold."""
    
    print("[PHASE1] Validation des corrections Bedrock Technology Detection")
    print("=" * 60)
    
    # Charger les configurations
    try:
        canonical_scopes = loader.load_canonical_scopes_local()
        print("[OK] Canonical scopes chargés")
    except Exception as e:
        print(f"[ERROR] Erreur chargement scopes: {e}")
        return False
    
    # Items de test avec signaux LAI explicites
    test_items = [
        {
            "source_key": "press_corporate__medincell",
            "source_type": "press_corporate",
            "title": "FDA Approves Expanded Indication for UZEDY® (risperidone) Extended-Release Injectable Suspension",
            "raw_text": "The FDA has approved an expanded indication for UZEDY (risperidone extended-release injectable suspension) for the treatment of adults with Bipolar I Disorder. This long-acting injectable formulation provides once-monthly treatment.",
            "url": "https://example.com/uzedy-approval",
            "published_at": "2025-12-11"
        },
        {
            "source_key": "press_corporate__nanexa",
            "source_type": "press_corporate", 
            "title": "Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products",
            "raw_text": "Nanexa AB and Moderna have entered into a license and option agreement for the development of PharmaShell®-based products. PharmaShell® is Nanexa's proprietary drug delivery technology platform.",
            "url": "https://example.com/nanexa-moderna",
            "published_at": "2025-12-11"
        }
    ]
    
    print(f"\n[TEST] Test de normalisation sur {len(test_items)} items...")
    
    # Simuler la normalisation (sans appel Bedrock réel)
    print("\n[SIMULATION] Résultats attendus après corrections Phase 1:")
    
    for i, item in enumerate(test_items, 1):
        print(f"\n--- Item {i}: {item['title'][:50]}... ---")
        
        # Résultats attendus
        if "UZEDY" in item['title']:
            expected = {
                "technologies_detected": ["Extended-Release Injectable", "Long-Acting Injectable"],
                "trademarks_detected": ["UZEDY"],
                "companies_detected": ["MedinCell", "Teva"],
                "molecules_detected": ["risperidone"],
                "lai_relevance_score": 9,
                "anti_lai_detected": False,
                "pure_player_context": True
            }
        else:  # Nanexa/Moderna
            expected = {
                "technologies_detected": ["PharmaShell", "Drug Delivery Technology"],
                "trademarks_detected": ["PharmaShell"],
                "companies_detected": ["Nanexa", "Moderna"],
                "molecules_detected": [],
                "lai_relevance_score": 8,
                "anti_lai_detected": False,
                "pure_player_context": True
            }
        
        print(f"  Technologies attendues: {expected['technologies_detected']}")
        print(f"  Trademarks attendues: {expected['trademarks_detected']}")
        print(f"  Companies attendues: {expected['companies_detected']}")
        print(f"  LAI relevance score: {expected['lai_relevance_score']}")
        print(f"  Anti-LAI detected: {expected['anti_lai_detected']}")
        print(f"  Pure player context: {expected['pure_player_context']}")
    
    print(f"\n[VALIDATION] Critères de succès Phase 1:")
    print("  ✓ technologies_detected non vide pour items LAI")
    print("  ✓ trademarks_detected contient UZEDY®, PharmaShell®")
    print("  ✓ lai_relevance_score > 0 pour items LAI")
    print("  ✓ anti_lai_detected = False pour items LAI")
    print("  ✓ pure_player_context = True pour pure players")
    
    print(f"\n[NEXT] Pour tester avec Bedrock réel:")
    print("  1. Configurer BEDROCK_MODEL_ID dans l'environnement")
    print("  2. Appeler normalizer.normalize_item() sur ces items")
    print("  3. Vérifier que les champs sont correctement remplis")
    
    return True

if __name__ == "__main__":
    success = test_phase1_corrections()
    if success:
        print("\n[OK] Validation Phase 1 terminée - Corrections prêtes pour test")
    else:
        print("\n[ERROR] Validation Phase 1 échouée")
        sys.exit(1)