#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyse des résultats matching lai_weekly_v12.
Conforme CRITICAL_RULES #9 (temporaires dans .tmp/).
"""

import json
import sys
import io

# Forcer UTF-8 pour stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    # Charger items depuis .tmp/
    with open('.tmp/e2e/lai_weekly_v12/curated_items.json', encoding='utf-8') as f:
        items = json.load(f)
    
    # Métriques matching
    total = len(items)
    matched = sum(1 for item in items if item.get('domain_scoring', {}).get('is_relevant'))
    match_rate = (matched / total * 100) if total > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"ANALYSE MATCHING LAI_WEEKLY_V12")
    print(f"{'='*60}\n")
    print(f"Taux matching: {match_rate:.1f}% ({matched}/{total})")
    print(f"Objectif: >50%")
    print(f"Statut: {'✅ SUCCÈS' if match_rate > 50 else '❌ ÉCHEC'}\n")
    
    # Analyse par score
    scores = [item.get('domain_scoring', {}).get('score', 0) 
              for item in items if item.get('domain_scoring', {}).get('is_relevant')]
    if scores:
        print(f"Score moyen: {sum(scores)/len(scores):.1f}")
        print(f"Score min: {min(scores)}")
        print(f"Score max: {max(scores)}\n")
    
    # Items clés
    print(f"{'='*60}")
    print(f"ITEMS CLÉS (UZEDY®, MedinCell, Extended-Release)")
    print(f"{'='*60}\n")
    
    key_items_found = 0
    for item in items:
        title = item.get('title', '')
        if 'UZEDY' in title or 'MedinCell' in title or 'Extended-Release Injectable' in title:
            key_items_found += 1
            score = item.get('domain_scoring', {}).get('score', 0)
            is_relevant = item.get('domain_scoring', {}).get('is_relevant', False)
            reasoning = item.get('domain_scoring', {}).get('reasoning', 'N/A')
            
            print(f"{title[:80]}")
            print(f"  Relevant: {is_relevant}, Score: {score}")
            print(f"  Reasoning: {reasoning[:100]}...")
            print(f"  Objectif: Score >85")
            print(f"  Statut: {'✅' if score > 85 else '❌'}\n")
    
    if key_items_found == 0:
        print("⚠️ AUCUN item clé trouvé dans les résultats!\n")
    
    # Analyse détaillée des items non matchés
    print(f"{'='*60}")
    print(f"ANALYSE DES ITEMS NON MATCHÉS")
    print(f"{'='*60}\n")
    
    non_matched = [item for item in items if not item.get('domain_scoring', {}).get('is_relevant')]
    print(f"Items non matchés: {len(non_matched)}/{total}\n")
    
    # Afficher quelques exemples
    for i, item in enumerate(non_matched[:5]):
        print(f"{i+1}. {item.get('title', 'N/A')[:80]}")
        print(f"   Score: {item.get('domain_scoring', {}).get('score', 0)}")
        print(f"   Reasoning: {item.get('domain_scoring', {}).get('reasoning', 'N/A')[:100]}...\n")
    
    # Critères succès Phase 1
    success = match_rate > 50
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
