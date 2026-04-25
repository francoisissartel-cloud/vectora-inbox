#!/usr/bin/env python3
"""
Script de Validation Automatique - Phase 1 Filtrage Précoce
Valide les optimisations en comparant les résultats avant/après modification.

Usage:
  python scripts/validation/validate_phase1_optimization.py
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Charge un fichier JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur lors du chargement de {file_path}: {e}")
        return {}

def find_latest_run(pattern: str) -> str:
    """Trouve le run le plus récent correspondant au pattern"""
    output_dir = Path("output/runs")
    if not output_dir.exists():
        return ""
    
    matching_runs = [d for d in output_dir.iterdir() if d.is_dir() and pattern in d.name]
    if not matching_runs:
        return ""
    
    # Trier par date de modification (le plus récent en premier)
    latest_run = max(matching_runs, key=lambda x: x.stat().st_mtime)
    return str(latest_run)

def analyze_run_results(run_dir: str) -> Dict[str, Any]:
    """Analyse les résultats d'un run"""
    if not run_dir or not os.path.exists(run_dir):
        return {}
    
    results = {
        "run_id": os.path.basename(run_dir),
        "run_dir": run_dir,
        "exists": True
    }
    
    # Charger ingested_items.json
    ingested_path = os.path.join(run_dir, "ingested_items.json")
    if os.path.exists(ingested_path):
        ingested_items = load_json_file(ingested_path)
        results["ingested_items"] = len(ingested_items)
        results["ingested_sources"] = len(set(item.get("source_key", "") for item in ingested_items))
        
        # Analyser par source
        source_stats = {}
        for item in ingested_items:
            source_key = item.get("source_key", "unknown")
            if source_key not in source_stats:
                source_stats[source_key] = 0
            source_stats[source_key] += 1
        results["source_breakdown"] = source_stats
    else:
        results["ingested_items"] = 0
        results["ingested_sources"] = 0
        results["source_breakdown"] = {}
    
    # Charger rejected_items.json
    rejected_path = os.path.join(run_dir, "rejected_items.json")
    if os.path.exists(rejected_path):
        rejected_items = load_json_file(rejected_path)
        results["rejected_items"] = len(rejected_items)
        
        # Analyser les raisons de rejet
        rejection_reasons = {}
        temporal_rejections = 0
        
        for item in rejected_items:
            filter_analysis = item.get("filter_analysis", {})
            period_filter = filter_analysis.get("period_filter", {})
            
            if not period_filter.get("passed", True):
                reason = period_filter.get("reason", "unknown")
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
                if reason == "too_old":
                    temporal_rejections += 1
        
        results["rejection_reasons"] = rejection_reasons
        results["temporal_rejections"] = temporal_rejections
    else:
        results["rejected_items"] = 0
        results["rejection_reasons"] = {}
        results["temporal_rejections"] = 0
    
    # Charger debug_report.json
    debug_path = os.path.join(run_dir, "debug_report.json")
    if os.path.exists(debug_path):
        debug_report = load_json_file(debug_path)
        performance = debug_report.get("performance_summary", {})
        results["total_sources"] = performance.get("total_sources", 0)
        results["avg_parse_time"] = performance.get("avg_parse_time", 0)
        results["content_extraction_rate"] = performance.get("content_extraction_rate", 0)
    else:
        results["total_sources"] = 0
        results["avg_parse_time"] = 0
        results["content_extraction_rate"] = 0
    
    return results

def compare_runs(baseline: Dict[str, Any], optimized: Dict[str, Any]) -> Dict[str, Any]:
    """Compare deux runs et calcule les métriques de performance"""
    
    comparison = {
        "baseline_run": baseline.get("run_id", "unknown"),
        "optimized_run": optimized.get("run_id", "unknown"),
        "timestamp": datetime.now().isoformat()
    }
    
    # Métriques de base
    baseline_ingested = baseline.get("ingested_items", 0)
    optimized_ingested = optimized.get("ingested_items", 0)
    
    comparison["ingested_items"] = {
        "baseline": baseline_ingested,
        "optimized": optimized_ingested,
        "difference": optimized_ingested - baseline_ingested,
        "identical": baseline_ingested == optimized_ingested
    }
    
    # Rejets temporels
    baseline_temporal = baseline.get("temporal_rejections", 0)
    optimized_temporal = optimized.get("temporal_rejections", 0)
    
    comparison["temporal_rejections"] = {
        "baseline": baseline_temporal,
        "optimized": optimized_temporal,
        "reduction": baseline_temporal - optimized_temporal,
        "reduction_percent": ((baseline_temporal - optimized_temporal) / baseline_temporal * 100) if baseline_temporal > 0 else 0
    }
    
    # Performance
    baseline_parse_time = baseline.get("avg_parse_time", 0)
    optimized_parse_time = optimized.get("avg_parse_time", 0)
    
    comparison["performance"] = {
        "baseline_parse_time": baseline_parse_time,
        "optimized_parse_time": optimized_parse_time,
        "time_reduction": baseline_parse_time - optimized_parse_time,
        "time_reduction_percent": ((baseline_parse_time - optimized_parse_time) / baseline_parse_time * 100) if baseline_parse_time > 0 else 0
    }
    
    # Comparaison par source
    baseline_sources = baseline.get("source_breakdown", {})
    optimized_sources = optimized.get("source_breakdown", {})
    
    source_comparison = {}
    all_sources = set(baseline_sources.keys()) | set(optimized_sources.keys())
    
    for source in all_sources:
        baseline_count = baseline_sources.get(source, 0)
        optimized_count = optimized_sources.get(source, 0)
        source_comparison[source] = {
            "baseline": baseline_count,
            "optimized": optimized_count,
            "difference": optimized_count - baseline_count
        }
    
    comparison["source_comparison"] = source_comparison
    
    return comparison

def validate_optimization(comparison: Dict[str, Any]) -> Dict[str, Any]:
    """Valide si l'optimisation respecte les critères de succès"""
    
    validation = {
        "overall_success": True,
        "criteria_met": {},
        "warnings": [],
        "errors": []
    }
    
    # Critère 1: Items finaux identiques
    ingested_identical = comparison["ingested_items"]["identical"]
    validation["criteria_met"]["items_identical"] = ingested_identical
    
    if not ingested_identical:
        validation["overall_success"] = False
        validation["errors"].append(
            f"Items finaux différents: {comparison['ingested_items']['baseline']} vs {comparison['ingested_items']['optimized']}"
        )
    
    # Critère 2: Réduction des rejets temporels
    temporal_reduction = comparison["temporal_rejections"]["reduction_percent"]
    validation["criteria_met"]["temporal_reduction"] = temporal_reduction >= 50
    
    if temporal_reduction < 50:
        validation["warnings"].append(
            f"Réduction des rejets temporels insuffisante: {temporal_reduction:.1f}% (objectif: >50%)"
        )
    
    # Critère 3: Amélioration des performances
    time_reduction = comparison["performance"]["time_reduction_percent"]
    validation["criteria_met"]["performance_improvement"] = time_reduction >= 30
    
    if time_reduction < 30:
        validation["warnings"].append(
            f"Amélioration des performances insuffisante: {time_reduction:.1f}% (objectif: >30%)"
        )
    
    # Critère 4: Pas de régression par source
    source_regressions = []
    for source, data in comparison["source_comparison"].items():
        if data["difference"] < 0:
            source_regressions.append(f"{source}: {data['difference']}")
    
    validation["criteria_met"]["no_source_regression"] = len(source_regressions) == 0
    
    if source_regressions:
        validation["warnings"].append(f"Régressions par source: {', '.join(source_regressions)}")
    
    return validation

def print_validation_report(comparison: Dict[str, Any], validation: Dict[str, Any]):
    """Affiche le rapport de validation"""
    
    print("=" * 80)
    print("RAPPORT DE VALIDATION - PHASE 1 FILTRAGE PRÉCOCE")
    print("=" * 80)
    print()
    
    print(f"🔍 COMPARAISON DES RUNS")
    print(f"   Baseline:  {comparison['baseline_run']}")
    print(f"   Optimisé:  {comparison['optimized_run']}")
    print(f"   Date:      {comparison['timestamp']}")
    print()
    
    print(f"📊 MÉTRIQUES PRINCIPALES")
    print(f"   Items finaux:        {comparison['ingested_items']['baseline']} → {comparison['ingested_items']['optimized']} ({comparison['ingested_items']['difference']:+d})")
    print(f"   Rejets temporels:    {comparison['temporal_rejections']['baseline']} → {comparison['temporal_rejections']['optimized']} ({comparison['temporal_rejections']['reduction_percent']:+.1f}%)")
    print(f"   Temps de parsing:    {comparison['performance']['baseline_parse_time']:.1f}s → {comparison['performance']['optimized_parse_time']:.1f}s ({comparison['performance']['time_reduction_percent']:+.1f}%)")
    print()
    
    print(f"✅ CRITÈRES DE VALIDATION")
    for criterion, met in validation["criteria_met"].items():
        status = "✅" if met else "❌"
        print(f"   {status} {criterion.replace('_', ' ').title()}")
    print()
    
    if validation["warnings"]:
        print(f"⚠️  AVERTISSEMENTS")
        for warning in validation["warnings"]:
            print(f"   - {warning}")
        print()
    
    if validation["errors"]:
        print(f"❌ ERREURS CRITIQUES")
        for error in validation["errors"]:
            print(f"   - {error}")
        print()
    
    print(f"🎯 RÉSULTAT GLOBAL")
    if validation["overall_success"]:
        print("   ✅ OPTIMISATION RÉUSSIE - Critères respectés")
        print("   → Prêt pour Phase 2 (Cache)")
    else:
        print("   ❌ OPTIMISATION ÉCHOUÉE - Corrections nécessaires")
        print("   → Rollback recommandé")
    
    print()
    print("=" * 80)

def main():
    """Fonction principale"""
    print("🔍 Validation automatique Phase 1 - Filtrage Précoce")
    print()
    
    # Trouver le run baseline (référence)
    baseline_run = "output/runs/mvp_test_30days__20260421_223354_0997242d"
    if not os.path.exists(baseline_run):
        print(f"❌ Run baseline non trouvé: {baseline_run}")
        print("   Assurez-vous que le run de référence existe")
        return 1
    
    # Trouver le run optimisé le plus récent
    optimized_run = find_latest_run("mvp_test_30days")
    if not optimized_run or optimized_run == baseline_run:
        print(f"❌ Aucun nouveau run trouvé pour mvp_test_30days")
        print("   Exécutez d'abord: python scripts/ingestion/run_ingestion.py mvp_test_30days")
        return 1
    
    print(f"📁 Baseline:  {baseline_run}")
    print(f"📁 Optimisé:  {optimized_run}")
    print()
    
    # Analyser les résultats
    print("🔄 Analyse des résultats...")
    baseline_results = analyze_run_results(baseline_run)
    optimized_results = analyze_run_results(optimized_run)
    
    if not baseline_results.get("exists") or not optimized_results.get("exists"):
        print("❌ Impossible d'analyser les résultats")
        return 1
    
    # Comparer les runs
    comparison = compare_runs(baseline_results, optimized_results)
    
    # Valider l'optimisation
    validation = validate_optimization(comparison)
    
    # Afficher le rapport
    print_validation_report(comparison, validation)
    
    # Sauvegarder le rapport
    report_path = f"docs/validation/phase1_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    full_report = {
        "comparison": comparison,
        "validation": validation,
        "baseline_results": baseline_results,
        "optimized_results": optimized_results
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Rapport sauvegardé: {report_path}")
    
    return 0 if validation["overall_success"] else 1

if __name__ == "__main__":
    sys.exit(main())