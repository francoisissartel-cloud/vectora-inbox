#!/usr/bin/env python3
"""
Script de comparaison automatique tests E2E vs baseline V17
"""

import json
import sys
from pathlib import Path

# Baseline V17 (reference)
BASELINE = {
    "version": "V17",
    "items_ingeres": 31,
    "companies_pct": 74,
    "relevant_pct": 64,
    "score_moyen": 71.5,
    "faux_negatifs": 0,
    "domain_scoring_pct": 100
}

# Seuils (min/max acceptables)
SEUILS = {
    "items_ingeres": {"min": 25, "max": 40},
    "companies_pct": {"min": 70, "max": 100},
    "relevant_pct": {"min": 60, "max": 80},
    "score_moyen": {"min": 65, "max": 85},
    "faux_negatifs": {"min": 0, "max": 1},
    "domain_scoring_pct": {"min": 100, "max": 100}
}

def load_curated_items(filepath):
    """Charge items curated depuis JSON"""
    with open(filepath, encoding='utf-8') as f:
        return json.load(f)

def calculate_metrics(items):
    """Calcule metriques depuis items curated"""
    total = len(items)
    
    with_ds = sum(1 for i in items if i.get('has_domain_scoring'))
    relevant = sum(1 for i in items if i.get('domain_scoring',{}).get('is_relevant'))
    companies = sum(1 for i in items if i.get('normalized_content',{}).get('entities',{}).get('companies'))
    scores = [i.get('domain_scoring',{}).get('score',0) for i in items if i.get('has_domain_scoring')]
    
    return {
        "items_ingeres": total,
        "companies_pct": round(companies/total*100) if total > 0 else 0,
        "relevant_pct": round(relevant/with_ds*100) if with_ds > 0 else 0,
        "score_moyen": round(sum(scores)/len(scores), 1) if scores else 0,
        "faux_negatifs": 0,  # A analyser manuellement
        "domain_scoring_pct": round(with_ds/total*100) if total > 0 else 0
    }

def compare_metrics(current, baseline, seuils):
    """Compare metriques current vs baseline"""
    results = []
    warnings = 0
    
    for key in baseline.keys():
        if key == "version":
            continue
            
        curr_val = current[key]
        base_val = baseline[key]
        seuil = seuils[key]
        
        # Evolution
        if isinstance(curr_val, float):
            evolution = curr_val - base_val
            evolution_pct = (evolution / base_val * 100) if base_val != 0 else 0
            evolution_str = f"{evolution:+.1f} ({evolution_pct:+.1f}%)"
        else:
            evolution = curr_val - base_val
            evolution_pct = (evolution / base_val * 100) if base_val != 0 else 0
            evolution_str = f"{evolution:+d} ({evolution_pct:+.1f}%)"
        
        # Statut vs seuils
        if curr_val < seuil["min"]:
            statut = "FAIL"
            warnings += 1
        elif curr_val > seuil["max"]:
            statut = "WARN"
            warnings += 1
        else:
            statut = "OK"
        
        results.append({
            "metrique": key,
            "baseline": base_val,
            "current": curr_val,
            "evolution": evolution_str,
            "seuil": f"{seuil['min']}-{seuil['max']}",
            "statut": statut
        })
    
    return results, warnings

def print_comparison(results, warnings, current_version):
    """Affiche comparaison formatee"""
    print("\n" + "="*80)
    print(f"COMPARAISON E2E: V17 (baseline) vs {current_version} (current)")
    print("="*80)
    print()
    
    # Tableau
    print(f"{'Metrique':<25} {'V17':<10} {current_version:<10} {'Evolution':<15} {'Seuil':<12} {'Statut':<6}")
    print("-"*80)
    
    for r in results:
        statut_icon = {"OK": "[OK]", "WARN": "[!]", "FAIL": "[X]"}[r["statut"]]
        print(f"{r['metrique']:<25} {str(r['baseline']):<10} {str(r['current']):<10} {r['evolution']:<15} {r['seuil']:<12} {statut_icon}")
    
    print()
    print("="*80)
    
    # Verdict
    if warnings == 0:
        print("VERDICT: [OK] SUCCES - Toutes metriques dans les seuils")
        print()
        print("Recommandation: MERGE IMMEDIAT")
        return 0
    elif warnings <= 2:
        print(f"VERDICT: [!] ATTENTION - {warnings} warning(s) detecte(s)")
        print()
        print("Recommandation: Investiguer warnings avant merge")
        return 1
    else:
        print(f"VERDICT: [X] ECHEC - {warnings} probleme(s) detecte(s)")
        print()
        print("Recommandation: CORRIGER avant merge")
        return 2

def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_e2e.py <curated_items.json> [version]")
        print()
        print("Exemple:")
        print("  python scripts/test/compare_e2e.py .tmp/v18_curated.json V18")
        sys.exit(1)
    
    filepath = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else "VX"
    
    if not Path(filepath).exists():
        print(f"[ERREUR] Fichier introuvable: {filepath}")
        sys.exit(1)
    
    # Charger et calculer metriques
    items = load_curated_items(filepath)
    current = calculate_metrics(items)
    
    # Comparer
    results, warnings = compare_metrics(current, BASELINE, SEUILS)
    
    # Afficher
    exit_code = print_comparison(results, warnings, version)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
