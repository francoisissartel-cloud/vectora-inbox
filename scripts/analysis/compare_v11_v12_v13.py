#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse comparative v11 vs v12 vs v13.
Conforme CRITICAL_RULES #9 (temporaires dans .tmp/).
"""

import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_items(version):
    path = f'.tmp/e2e/lai_weekly_v{version}/curated_items.json'
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def analyze_version(items, version):
    total = len(items)
    matched = sum(1 for item in items if item.get('domain_scoring', {}).get('is_relevant'))
    match_rate = (matched / total * 100) if total > 0 else 0
    
    scores = [item.get('domain_scoring', {}).get('score', 0) 
              for item in items if item.get('domain_scoring', {}).get('is_relevant')]
    
    return {
        'version': version,
        'total': total,
        'matched': matched,
        'match_rate': match_rate,
        'score_avg': sum(scores)/len(scores) if scores else 0,
        'score_min': min(scores) if scores else 0,
        'score_max': max(scores) if scores else 0
    }

def main():
    print(f"\n{'='*70}")
    print(f"ANALYSE COMPARATIVE v11 vs v12 vs v13")
    print(f"{'='*70}\n")
    
    results = []
    for v in ['11', '12', '13']:
        try:
            items = load_items(v)
            result = analyze_version(items, v)
            results.append(result)
        except FileNotFoundError:
            print(f"⚠️ Fichier v{v} non trouvé, ignoré\n")
    
    # Tableau comparatif
    print(f"{'Version':<10} {'Total':<8} {'Matchés':<10} {'Taux':<10} {'Score Moy':<12} {'Min':<6} {'Max':<6}")
    print(f"{'-'*70}")
    
    for r in results:
        print(f"v{r['version']:<9} {r['total']:<8} {r['matched']:<10} "
              f"{r['match_rate']:.1f}%{'':<6} {r['score_avg']:.1f}{'':<8} "
              f"{r['score_min']:<6} {r['score_max']:<6}")
    
    # Évolution
    if len(results) >= 2:
        print(f"\n{'='*70}")
        print(f"ÉVOLUTION")
        print(f"{'='*70}\n")
        
        v11_rate = results[0]['match_rate']
        v12_rate = results[1]['match_rate']
        v13_rate = results[2]['match_rate'] if len(results) > 2 else 0
        
        print(f"v11 → v12: {v11_rate:.1f}% → {v12_rate:.1f}% ({v12_rate - v11_rate:+.1f} pts)")
        if len(results) > 2:
            print(f"v12 → v13: {v12_rate:.1f}% → {v13_rate:.1f}% ({v13_rate - v12_rate:+.1f} pts)")
            print(f"v11 → v13: {v11_rate:.1f}% → {v13_rate:.1f}% ({v13_rate - v11_rate:+.1f} pts)")
    
    # Items clés
    print(f"\n{'='*70}")
    print(f"ITEMS CLÉS (UZEDY®, MedinCell)")
    print(f"{'='*70}\n")
    
    for r in results:
        items = load_items(r['version'])
        print(f"v{r['version']}:")
        found_key_items = False
        for item in items:
            title = item.get('title', '')
            if 'UZEDY' in title or 'MedinCell' in title:
                found_key_items = True
                score = item.get('domain_scoring', {}).get('score', 0)
                is_relevant = item.get('domain_scoring', {}).get('is_relevant', False)
                print(f"  {title[:60]}: {score} ({'✅' if is_relevant else '❌'})")
        if not found_key_items:
            print(f"  Aucun item clé trouvé")
        print()

if __name__ == '__main__':
    main()
