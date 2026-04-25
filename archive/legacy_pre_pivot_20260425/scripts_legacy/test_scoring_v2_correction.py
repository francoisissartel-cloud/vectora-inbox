#!/usr/bin/env python3
"""
Script de test local pour valider la correction du scoring V2
Recalcule les scores sur test_curated_items.json et génère un rapport
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Ajout du chemin src_v2 pour les imports
script_dir = Path(__file__).parent
src_v2_path = script_dir / "src_v2"
sys.path.insert(0, str(src_v2_path))

try:
    from vectora_core.normalization.scorer import score_items, _calculate_item_score
    from vectora_core.shared.config_loader import load_client_config
except ImportError as e:
    print(f"Erreur import: {e}")
    print("Assurez-vous que le script est exécuté depuis la racine du projet")
    sys.exit(1)

def load_test_data():
    """Charge les données de test"""
    test_file = script_dir / "test_curated_items.json"
    
    if not test_file.exists():
        print(f"Fichier de test non trouvé: {test_file}")
        sys.exit(1)
    
    with open(test_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_mock_config():
    """Configuration de test simplifiée"""
    return {
        "scoring_config": {
            "event_type_weight_overrides": {
                "partnership": 8,
                "clinical_update": 6,
                "regulatory": 7,
                "scientific_publication": 4,
                "corporate_move": 5,
                "financial_results": 3,
                "other": 2
            },
            "client_specific_bonuses": {
                "pure_player_companies": {
                    "scope": "lai_companies_mvp_core",
                    "bonus": 5.0
                },
                "trademark_mentions": {
                    "scope": "lai_trademarks_global", 
                    "bonus": 4.0
                },
                "key_molecules": {
                    "scope": "lai_molecules_global",
                    "bonus": 2.5
                },
                "hybrid_companies": {
                    "scope": "lai_companies_hybrid",
                    "bonus": 1.5
                }
            }
        }
    }

def load_mock_canonical():
    """Scopes canonical simplifiés pour le test"""
    return {
        "companies": {
            "lai_companies_mvp_core": ["Nanexa", "Medincell", "Delsitech"],
            "lai_companies_hybrid": ["Teva", "Moderna", "Roche", "Novartis"]
        },
        "trademarks": {
            "lai_trademarks_global": ["PharmaShell®", "UZEDY®", "Aristada", "Abilify Maintena"]
        },
        "molecules": {
            "lai_molecules_global": ["risperidone", "olanzapine", "GLP-1", "UZEDY"]
        }
    }

def test_single_item_scoring():
    """Test du scoring sur un item individuel"""
    print("=== Test Scoring Item Individuel ===")
    
    # Item de test avec signaux LAI forts
    test_item = {
        "item_id": "test_nanexa_moderna",
        "normalized_content": {
            "lai_relevance_score": 8,
            "event_classification": {"primary_type": "partnership"},
            "entities": {
                "companies": ["Nanexa", "Moderna"],
                "trademarks": ["PharmaShell®"],
                "technologies": ["Long-Acting Injectable"]
            }
        },
        "matching_results": {
            "matched_domains": ["tech_lai_ecosystem"],
            "domain_relevance": {
                "tech_lai_ecosystem": {
                    "score": 0.7,
                    "confidence": "high",  # String (corrigé)
                    "reasoning": "PharmaShell technology match"
                }
            }
        }
    }
    
    config = load_mock_config()
    canonical = load_mock_canonical()
    reference_date = datetime.now()
    
    try:
        scoring_result = _calculate_item_score(
            test_item, 
            config["scoring_config"], 
            canonical, 
            reference_date, 
            "balanced"
        )
        
        print(f"✅ Scoring réussi!")
        print(f"   Base score: {scoring_result.get('base_score', 0)}")
        print(f"   Bonuses: {scoring_result.get('bonuses', {})}")
        print(f"   Penalties: {scoring_result.get('penalties', {})}")
        print(f"   Final score: {scoring_result.get('final_score', 0)}")
        print(f"   Score breakdown: {scoring_result.get('score_breakdown', {})}")
        
        return scoring_result.get('final_score', 0) > 0
        
    except Exception as e:
        print(f"❌ Erreur scoring: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_dataset():
    """Test du scoring sur le dataset complet"""
    print("\n=== Test Dataset Complet ===")
    
    items = load_test_data()
    config = load_mock_config()
    canonical = load_mock_canonical()
    
    print(f"Items chargés: {len(items)}")
    
    try:
        scored_items = score_items(
            items,
            config,
            canonical,
            "balanced",
            datetime.now().isoformat()
        )
        
        print(f"✅ Scoring dataset réussi!")
        
        # Analyse des résultats
        scores = []
        items_with_score = 0
        items_with_errors = 0
        
        for item in scored_items:
            scoring_results = item.get("scoring_results", {})
            final_score = scoring_results.get("final_score", 0)
            
            if "error" in scoring_results:
                items_with_errors += 1
                print(f"❌ Erreur item {item.get('item_id', 'unknown')}: {scoring_results.get('error')}")
            
            if final_score > 0:
                items_with_score += 1
                scores.append(final_score)
        
        print(f"\n📊 Résultats:")
        print(f"   Items avec score > 0: {items_with_score}/{len(scored_items)}")
        print(f"   Items avec erreurs: {items_with_errors}")
        
        if scores:
            print(f"   Score min: {min(scores):.1f}")
            print(f"   Score max: {max(scores):.1f}")
            print(f"   Score moyen: {sum(scores)/len(scores):.1f}")
            
            # Items sélectionnables (score >= 12)
            selectable = [s for s in scores if s >= 12]
            print(f"   Items sélectionnables (>= 12): {len(selectable)}")
        
        return items_with_score > 0 and items_with_errors == 0
        
    except Exception as e:
        print(f"❌ Erreur scoring dataset: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_detailed_report(items):
    """Génère un rapport détaillé des scores"""
    print("\n=== Rapport Détaillé par Item ===")
    
    config = load_mock_config()
    canonical = load_mock_canonical()
    
    try:
        scored_items = score_items(items, config, canonical, "balanced", datetime.now().isoformat())
        
        report_lines = []
        report_lines.append("# Rapport de Scoring V2 - Post Correction")
        report_lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"**Items analysés:** {len(scored_items)}")
        report_lines.append("")
        
        # Tableau des résultats
        report_lines.append("| Item | LAI Score | Event Type | Matched Domains | Final Score | Status |")
        report_lines.append("|------|-----------|------------|-----------------|-------------|--------|")
        
        for item in scored_items:
            item_id = item.get("item_id", "unknown")[:30]
            
            normalized = item.get("normalized_content", {})
            lai_score = normalized.get("lai_relevance_score", 0)
            event_type = normalized.get("event_classification", {}).get("primary_type", "unknown")
            
            matching = item.get("matching_results", {})
            matched_domains = len(matching.get("matched_domains", []))
            
            scoring = item.get("scoring_results", {})
            final_score = scoring.get("final_score", 0)
            
            if "error" in scoring:
                status = f"❌ Error: {scoring.get('error_type', 'Unknown')}"
            elif final_score >= 12:
                status = "✅ Sélectionnable"
            elif final_score > 0:
                status = "⚠️ Score faible"
            else:
                status = "❌ Exclu"
            
            report_lines.append(f"| {item_id} | {lai_score} | {event_type} | {matched_domains} | {final_score:.1f} | {status} |")
        
        # Statistiques
        scores = [item.get("scoring_results", {}).get("final_score", 0) for item in scored_items]
        non_zero_scores = [s for s in scores if s > 0]
        selectable_scores = [s for s in scores if s >= 12]
        
        report_lines.append("")
        report_lines.append("## Statistiques")
        report_lines.append(f"- **Items avec score > 0:** {len(non_zero_scores)}/{len(scores)} ({len(non_zero_scores)/len(scores)*100:.1f}%)")
        report_lines.append(f"- **Items sélectionnables (>= 12):** {len(selectable_scores)}/{len(scores)} ({len(selectable_scores)/len(scores)*100:.1f}%)")
        
        if non_zero_scores:
            report_lines.append(f"- **Score minimum:** {min(non_zero_scores):.1f}")
            report_lines.append(f"- **Score maximum:** {max(non_zero_scores):.1f}")
            report_lines.append(f"- **Score moyen:** {sum(non_zero_scores)/len(non_zero_scores):.1f}")
        
        # Sauvegarde du rapport
        report_file = script_dir / "docs" / "diagnostics" / "scoring_v2_post_fix_lai_weekly_v4.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"📄 Rapport sauvegardé: {report_file}")
        
        return len(non_zero_scores) > 0
        
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 Test de Correction Scoring V2")
    print("=" * 50)
    
    # Test 1: Item individuel
    success_individual = test_single_item_scoring()
    
    # Test 2: Dataset complet
    items = load_test_data()
    success_dataset = test_full_dataset()
    
    # Test 3: Rapport détaillé
    success_report = generate_detailed_report(items)
    
    # Résumé
    print("\n" + "=" * 50)
    print("🎯 RÉSUMÉ DES TESTS")
    print(f"   Test item individuel: {'✅ PASS' if success_individual else '❌ FAIL'}")
    print(f"   Test dataset complet: {'✅ PASS' if success_dataset else '❌ FAIL'}")
    print(f"   Génération rapport: {'✅ PASS' if success_report else '❌ FAIL'}")
    
    overall_success = success_individual and success_dataset and success_report
    print(f"\n🏆 RÉSULTAT GLOBAL: {'✅ CORRECTION VALIDÉE' if overall_success else '❌ CORRECTION INCOMPLÈTE'}")
    
    if overall_success:
        print("\n🎉 La correction du scoring V2 est fonctionnelle!")
        print("   → Les items LAI ont maintenant des final_score > 0")
        print("   → La newsletter V2 peut maintenant sélectionner les items")
        print("   → Prêt pour validation E2E")
    else:
        print("\n⚠️ La correction nécessite des ajustements supplémentaires")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())