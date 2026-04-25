#!/usr/bin/env python3
"""
Script d'analyse de l'extraction des dates.
Analyse les items ingérés pour mesurer l'efficacité de la cascade d'extraction.
"""

import json
import sys
from collections import Counter
from datetime import datetime

def analyze_date_extraction(items_file):
    """Analyse la distribution des sources d'extraction de dates"""
    
    # Charger items
    with open(items_file, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    if not items:
        print("❌ Aucun item trouvé")
        return
    
    print(f"📊 Analyse de {len(items)} items\n")
    
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
    print("📈 Distribution des sources d'extraction:")
    for source, count in sources.most_common():
        pct = count / len(items) * 100
        emoji = "✅" if source != 'ingestion_fallback' else "⚠️"
        print(f"  {emoji} {source:25s}: {count:3d} ({pct:5.1f}%)")
    
    # Taux de fallback
    fallback_rate = sources.get('ingestion_fallback', 0) / len(items) * 100
    print(f"\n📉 Taux de fallback: {fallback_rate:.1f}%")
    
    if fallback_rate < 10:
        print("   ✅ EXCELLENT - Objectif atteint (<10%)")
    elif fallback_rate < 20:
        print("   ✅ BON - Objectif proche (<20%)")
    elif fallback_rate < 50:
        print("   ⚠️  MOYEN - Amélioration possible")
    else:
        print("   ❌ FAIBLE - Amélioration nécessaire")
    
    # Items avec fallback
    if fallback_items:
        print(f"\n⚠️  Items avec fallback ({len(fallback_items)}):")
        
        # Grouper par source
        by_source = Counter(item['source_key'] for item in fallback_items)
        
        for source_key, count in by_source.most_common():
            print(f"\n  📍 {source_key} ({count} items):")
            source_items = [i for i in fallback_items if i['source_key'] == source_key]
            for item in source_items[:3]:
                title = item['title'][:60]
                date = item.get('published_at', 'N/A')
                print(f"     - [{date}] {title}...")
            
            if len(source_items) > 3:
                print(f"     ... et {len(source_items) - 3} autres")
    
    # Recommandations
    print("\n💡 Recommandations:")
    
    if fallback_rate > 20:
        print("  1. Ajouter selectors HTML pour sources problématiques")
        print("  2. Vérifier patterns regex dans parsing_config.yaml")
    
    if sources.get('url_extraction', 0) == 0:
        print("  3. Vérifier que try_url_extraction() est appelé")
    
    if sources.get('html_metadata', 0) == 0:
        print("  4. Vérifier que try_structured_metadata() est appelé")
    
    if fallback_rate < 10:
        print("  ✅ Aucune action nécessaire - Performance optimale")
    
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_date_extraction.py <items_file.json>")
        print("\nExemple:")
        print("  python analyze_date_extraction.py data/ingested/lai_weekly_v28/2026-02-09.json")
        sys.exit(1)
    
    items_file = sys.argv[1]
    analyze_date_extraction(items_file)
