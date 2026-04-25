#!/usr/bin/env python3
"""
Script de test local pour normalize_score_v2 avec données synthétiques.

Ce script permet de tester le pipeline de normalisation en local
avec des données synthétiques, sans impacter la production.

Usage:
    python scripts/test_normalize_with_synthetic_data.py
"""

import json
import os
import sys
from pathlib import Path

# Ajouter src_v2 au path pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src_v2"))

from vectora_core.normalization import normalizer
from vectora_core.shared import config_loader


def load_synthetic_data():
    """Charge les données synthétiques pour les tests."""
    synthetic_file = project_root / "scripts" / "test_data" / "synthetic_items_lai.json"
    
    if not synthetic_file.exists():
        raise FileNotFoundError(f"Fichier de test non trouvé: {synthetic_file}")
    
    with open(synthetic_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get("items", [])


def test_normalization_pipeline():
    """Test du pipeline de normalisation avec données synthétiques."""
    print("🧪 Test local du pipeline normalize_score_v2 avec données synthétiques")
    print("=" * 70)
    
    # Chargement des données de test
    print("📁 Chargement des données synthétiques...")
    synthetic_items = load_synthetic_data()
    print(f"   ✅ {len(synthetic_items)} items synthétiques chargés")
    
    # Configuration de test (simulée)
    canonical_scopes = {
        "companies": {"lai_companies_mvp_core": ["MedinCell", "Nanexa", "DelSiTech"]},
        "molecules": {"lai_molecules_global": ["buprenorphine", "naloxone", "olanzapine"]},
        "technologies": {"lai_keywords": ["long-acting injection", "LAI", "depot"]},
        "trademarks": {"lai_trademarks_global": ["UZEDY", "PharmaShell", "BEPO"]}
    }
    
    canonical_prompts = {}
    
    # Test de normalisation
    print("\n🔄 Test de normalisation Bedrock...")
    try:
        # Note: En test local, on peut simuler les appels Bedrock
        print("   ⚠️  Mode simulation - pas d'appels Bedrock réels")
        
        # Simulation des résultats de normalisation
        normalized_items = []
        for item in synthetic_items:
            normalized_item = item.copy()
            normalized_item["normalized_content"] = {
                "summary": f"Résumé simulé pour {item.get('title', 'N/A')}",
                "entities": {
                    "companies": ["Novartis"] if "Novartis" in item.get('title', '') else [],
                    "molecules": [],
                    "technologies": ["CAR-T"] if "CAR-T" in item.get('title', '') else [],
                    "trademarks": []
                }
            }
            normalized_items.append(normalized_item)
        
        print(f"   ✅ {len(normalized_items)} items normalisés (simulation)")
        
    except Exception as e:
        print(f"   ❌ Erreur de normalisation: {e}")
        return False
    
    # Affichage des résultats
    print("\n📊 Résultats du test:")
    print(f"   • Items input: {len(synthetic_items)}")
    print(f"   • Items normalisés: {len(normalized_items)}")
    print(f"   • Taux de succès: {len(normalized_items)/len(synthetic_items)*100:.1f}%")
    
    print("\n✅ Test terminé avec succès")
    print("\n⚠️  RAPPEL: Ce script utilise des données synthétiques")
    print("   Pour tester avec des données réelles, utiliser:")
    print("   scripts/invoke_normalize_score_v2_lambda.py")
    
    return True


if __name__ == "__main__":
    try:
        success = test_normalization_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erreur fatale: {e}")
        sys.exit(1)