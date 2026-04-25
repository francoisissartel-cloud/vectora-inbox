#!/usr/bin/env python3
"""
Script d'analyse de l'extraction des dates (version Windows sans emojis).
"""

import json
import sys
from collections import Counter

def analyze_date_extraction(items_file):
    """Analyse la distribution des sources d'extraction de dates"""
    
    with open(items_file, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    if not items:
        print("Aucun item trouve")
        return
    
    print(f"\n=== Analyse de {len(items)} items ===\n")
    
    # Analyser date_source
    sources = Counter()
    fallback_items = []
    
    for item in items:
        date_info = item.get('date_extraction', {})
        source = date_info.get('date_source', 'unknown')
        sources[source] += 1
        
        if source == 'ingestion_fallback':
            fallback_items.append(item)
    
    # Afficher distribution
    print("Distribution des sources d'extraction:")
    for source, count in sources.most_common():
        pct = count / len(items) * 100
        marker = "[OK]" if source != 'ingestion_fallback' else "[!!]"
        print(f"  {marker} {source:25s}: {count:3d} ({pct:5.1f}%)")
    
    # Taux de fallback
    fallback_rate = sources.get('ingestion_fallback', 0) / len(items) * 100
    print(f"\nTaux de fallback: {fallback_rate:.1f}%")
    
    if fallback_rate < 10:
        print("   [OK] EXCELLENT - Objectif atteint (<10%)")
    elif fallback_rate < 20:
        print("   [OK] BON - Objectif proche (<20%)")
    elif fallback_rate < 50:
        print("   [!!] MOYEN - Amelioration possible")
    else:
        print("   [!!] FAIBLE - Amelioration necessaire")
    
    # Items avec fallback
    if fallback_items:
        print(f"\nItems avec fallback ({len(fallback_items)}):")
        
        by_source = Counter(item['source_key'] for item in fallback_items)
        
        for source_key, count in by_source.most_common():
            print(f"\n  Source: {source_key} ({count} items):")
            source_items = [i for i in fallback_items if i['source_key'] == source_key]
            for item in source_items[:3]:
                title = item['title'][:60]
                date = item.get('published_at', 'N/A')
                print(f"     - [{date}] {title}...")
            
            if len(source_items) > 3:
                print(f"     ... et {len(source_items) - 3} autres")
    
    # Recommandations
    print("\nRecommandations:")
    
    if fallback_rate > 20:
        print("  1. Ajouter selectors HTML pour sources problematiques")
        print("  2. Verifier patterns regex dans parsing_config.yaml")
    
    if sources.get('url_extraction', 0) == 0:
        print("  3. Verifier que try_url_extraction() est appele")
    
    if sources.get('html_metadata', 0) == 0:
        print("  4. Verifier que try_structured_metadata() est appele")
    
    if fallback_rate < 10:
        print("  [OK] Aucune action necessaire - Performance optimale")
    
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_date_extraction_win.py <items_file.json>")
        sys.exit(1)
    
    items_file = sys.argv[1]
    analyze_date_extraction(items_file)
