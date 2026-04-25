"""
Analyse des dates extraites apres correctif
"""
import json
from collections import Counter
from datetime import datetime

def analyze_dates(filename='items_test_date_fix.json'):
    """Analyse les dates published_at dans le fichier items"""
    
    with open(filename, 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    print(f"\n{'='*70}")
    print(f"ANALYSE DES DATES EXTRAITES - Correctif Parsing Dates")
    print(f"{'='*70}")
    print(f"\nFichier: {filename}")
    print(f"Total items: {len(items)}")
    
    # Analyser les dates
    dates = [item.get('published_at') for item in items]
    date_counter = Counter(dates)
    
    print(f"\n--- Distribution des dates ---")
    for date, count in sorted(date_counter.items(), reverse=True):
        print(f"  {date}: {count} items")
    
    # Detecter les dates fallback (meme jour que l'ingestion)
    ingestion_date = '2026-01-29'
    fallback_count = sum(1 for d in dates if d == ingestion_date)
    
    print(f"\n--- Detection dates fallback ---")
    print(f"  Date ingestion: {ingestion_date}")
    print(f"  Items avec date fallback: {fallback_count}/{len(items)} ({fallback_count*100//len(items)}%)")
    print(f"  Items avec vraie date: {len(items)-fallback_count}/{len(items)} ({(len(items)-fallback_count)*100//len(items)}%)")
    
    # Afficher quelques exemples
    print(f"\n--- Exemples d'items avec vraies dates ---")
    real_date_items = [item for item in items if item.get('published_at') != ingestion_date][:5]
    for item in real_date_items:
        print(f"\n  Titre: {item.get('title', '')[:60]}...")
        print(f"  Date: {item.get('published_at')}")
        print(f"  Source: {item.get('source_key')}")
    
    # Afficher items avec date fallback
    if fallback_count > 0:
        print(f"\n--- Exemples d'items avec date fallback ---")
        fallback_items = [item for item in items if item.get('published_at') == ingestion_date][:3]
        for item in fallback_items:
            print(f"\n  Titre: {item.get('title', '')[:60]}...")
            print(f"  Date: {item.get('published_at')} (FALLBACK)")
            print(f"  Source: {item.get('source_key')}")
    
    # Statistiques temporelles
    print(f"\n--- Statistiques temporelles ---")
    cutoff_date = '2025-12-30'  # 30 jours
    old_items = [item for item in items if item.get('published_at', '') < cutoff_date]
    recent_items = [item for item in items if item.get('published_at', '') >= cutoff_date]
    
    print(f"  Cutoff date (30 jours): {cutoff_date}")
    print(f"  Items recents (>= cutoff): {len(recent_items)}")
    print(f"  Items anciens (< cutoff): {len(old_items)}")
    
    if old_items:
        print(f"\n  Items anciens qui auraient du etre filtres:")
        for item in old_items[:3]:
            print(f"    - {item.get('title', '')[:50]}... ({item.get('published_at')})")
    
    # Comparaison AVANT/APRES
    print(f"\n{'='*70}")
    print(f"IMPACT DU CORRECTIF")
    print(f"{'='*70}")
    print(f"\nAVANT (problematique):")
    print(f"  - Toutes dates = {ingestion_date} (date ingestion)")
    print(f"  - Filtre temporel: INEFFICACE")
    
    print(f"\nAPRES (corrige):")
    print(f"  - Vraies dates extraites: {len(items)-fallback_count}/{len(items)} ({(len(items)-fallback_count)*100//len(items)}%)")
    print(f"  - Dates fallback: {fallback_count}/{len(items)} ({fallback_count*100//len(items)}%)")
    print(f"  - Filtre temporel: {'EFFICACE' if len(old_items) == 0 else 'PARTIELLEMENT EFFICACE'}")
    
    print(f"\n{'='*70}\n")


if __name__ == '__main__':
    analyze_dates()
