#!/usr/bin/env python3
"""
Analyse des résultats du test E2E Vectora Inbox MVP lai_weekly_v3
"""

import json
import sys
from collections import defaultdict, Counter
from datetime import datetime

def analyze_curated_items(file_path):
    """Analyse les items normalisés et scorés"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    print("=" * 80)
    print("ANALYSE DES RÉSULTATS E2E - VECTORA INBOX MVP LAI_WEEKLY_V3")
    print("=" * 80)
    print(f"Nombre total d'items: {len(items)}")
    print()
    
    # Analyse des scores
    scores = [item.get('final_score', 0) for item in items]
    scores.sort(reverse=True)
    
    print("DISTRIBUTION DES SCORES:")
    print(f"  Score max: {max(scores):.1f}")
    print(f"  Score min: {min(scores):.1f}")
    print(f"  Score moyen: {sum(scores)/len(scores):.1f}")
    print(f"  Scores > 12: {len([s for s in scores if s > 12])}")
    print(f"  Scores 8-12: {len([s for s in scores if 8 <= s <= 12])}")
    print(f"  Scores < 8: {len([s for s in scores if s < 8])}")
    print()
    
    # Analyse des entités
    all_companies = []
    all_molecules = []
    all_technologies = []
    all_trademarks = []
    
    for item in items:
        entities = item.get('normalized_entities', {})
        all_companies.extend(entities.get('companies', []))
        all_molecules.extend(entities.get('molecules', []))
        all_technologies.extend(entities.get('technologies', []))
        all_trademarks.extend(entities.get('trademarks', []))
    
    print("ENTITÉS DÉTECTÉES:")
    print(f"  Companies uniques: {len(set(all_companies))}")
    print(f"    Top companies: {Counter(all_companies).most_common(5)}")
    print(f"  Molecules uniques: {len(set(all_molecules))}")
    print(f"    Molecules: {set(all_molecules)}")
    print(f"  Technologies uniques: {len(set(all_technologies))}")
    print(f"    Top technologies: {Counter(all_technologies).most_common(3)}")
    print(f"  Trademarks uniques: {len(set(all_trademarks))}")
    print(f"    Trademarks: {set(all_trademarks)}")
    print()
    
    # Analyse du matching
    matched_domains = defaultdict(int)
    for item in items:
        domains = item.get('matched_domains', [])
        for domain in domains:
            matched_domains[domain] += 1
    
    print("MATCHING PAR DOMAINES:")
    if matched_domains:
        for domain, count in matched_domains.items():
            print(f"  {domain}: {count} items")
    else:
        print("  ⚠️  AUCUN ITEM MATCHÉ - PROBLÈME CRITIQUE")
    print()
    
    # Top 5 items par score
    items_sorted = sorted(items, key=lambda x: x.get('final_score', 0), reverse=True)
    
    print("TOP 5 ITEMS PAR SCORE:")
    for i, item in enumerate(items_sorted[:5], 1):
        score = item.get('final_score', 0)
        title = item.get('title', 'Sans titre')[:80]
        companies = item.get('normalized_entities', {}).get('companies', [])
        trademarks = item.get('normalized_entities', {}).get('trademarks', [])
        
        print(f"  {i}. Score: {score:.1f}")
        print(f"     Titre: {title}")
        print(f"     Companies: {companies[:3]}")
        print(f"     Trademarks: {trademarks}")
        print(f"     Domaines: {item.get('matched_domains', [])}")
        print()
    
    # Items avec trademarks LAI
    trademark_items = [item for item in items if item.get('normalized_entities', {}).get('trademarks')]
    
    print(f"ITEMS AVEC TRADEMARKS LAI: {len(trademark_items)}")
    for item in trademark_items:
        score = item.get('final_score', 0)
        title = item.get('title', 'Sans titre')[:60]
        trademarks = item.get('normalized_entities', {}).get('trademarks', [])
        print(f"  Score: {score:.1f} | {title} | Trademarks: {trademarks}")
    print()
    
    # Analyse des bonus appliqués
    bonus_stats = defaultdict(int)
    for item in items:
        scoring_details = item.get('scoring_details', {})
        bonuses = scoring_details.get('bonuses_applied', {})
        for bonus_type in bonuses.keys():
            bonus_stats[bonus_type] += 1
    
    print("BONUS APPLIQUÉS:")
    for bonus_type, count in bonus_stats.items():
        print(f"  {bonus_type}: {count} items")
    print()
    
    return {
        'total_items': len(items),
        'score_distribution': {
            'max': max(scores),
            'min': min(scores),
            'avg': sum(scores)/len(scores),
            'high_count': len([s for s in scores if s > 12])
        },
        'entities': {
            'companies': len(set(all_companies)),
            'molecules': len(set(all_molecules)),
            'technologies': len(set(all_technologies)),
            'trademarks': len(set(all_trademarks))
        },
        'matching_success': len(matched_domains) > 0,
        'trademark_items': len(trademark_items)
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_e2e_test_results.py <curated_items.json>")
        sys.exit(1)
    
    results = analyze_curated_items(sys.argv[1])
    
    print("SYNTHÈSE FINALE:")
    print(f"✅ Normalisation: {results['total_items']} items traités")
    print(f"✅ Entités: {results['entities']['companies']} companies, {results['entities']['trademarks']} trademarks")
    print(f"✅ Scores: {results['score_distribution']['high_count']} items > 12")
    print(f"{'✅' if results['matching_success'] else '❌'} Matching: {'OK' if results['matching_success'] else 'ÉCHEC CRITIQUE'}")
    print(f"✅ Trademarks LAI: {results['trademark_items']} items détectés")