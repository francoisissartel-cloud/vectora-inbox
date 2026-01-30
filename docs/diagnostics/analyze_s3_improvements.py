#!/usr/bin/env python3
import json
from collections import defaultdict

def analyze_hallucinations(filename):
    """Analyser les hallucinations dans un fichier curé"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    hallucinations = 0
    total_items = len(data)
    
    for item in data:
        content = item.get('content', '').lower()
        entities = item.get('normalized_content', {}).get('entities', {})
        
        # Vérifier les technologies suspectes
        technologies = entities.get('technologies', [])
        for tech in technologies:
            if 'uzedy' in tech.lower() and 'uzedy' not in content:
                hallucinations += 1
                print(f"Hallucination détectée: {tech} dans {item['item_id']}")
                break
            if 'extended-release injectable' in tech.lower() and 'extended-release' not in content and 'injectable' not in content:
                hallucinations += 1
                print(f"Hallucination détectée: {tech} dans {item['item_id']}")
                break
    
    return hallucinations, total_items

def analyze_event_classification(filename):
    """Analyser la classification des événements"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    classifications = defaultdict(int)
    grants_misclassified = 0
    
    for item in data:
        event_type = item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', 'unknown')
        classifications[event_type] += 1
        
        # Vérifier les grants mal classifiés
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        if 'grant' in title or 'grant' in content:
            if event_type != 'partnership':
                grants_misclassified += 1
                print(f"Grant mal classifié: {event_type} pour {item['item_id']}")
    
    return dict(classifications), grants_misclassified

def analyze_dates(filename):
    """Analyser l'extraction des dates"""
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    dates = set()
    ingestion_date_fallback = 0
    
    for item in data:
        published_at = item.get('published_at')
        ingested_at = item.get('ingested_at', '')[:10]  # YYYY-MM-DD
        
        dates.add(published_at)
        if published_at == ingested_at:
            ingestion_date_fallback += 1
    
    return len(dates), ingestion_date_fallback, len(data)

if __name__ == "__main__":
    print("=== ANALYSE S3 - AMÉLIORATIONS PHASE 1-4 ===\n")
    
    # Analyse 19 décembre (avant améliorations)
    print("[19 DEC] DONNEES 19 DECEMBRE 2025 (Reference)")
    hall_19, total_19 = analyze_hallucinations('curated_19dec.json')
    class_19, grants_19 = analyze_event_classification('curated_19dec.json')
    dates_19, fallback_19, total_dates_19 = analyze_dates('items_19dec.json')
    
    print(f"Hallucinations: {hall_19}/{total_19} ({hall_19/total_19*100:.1f}%)")
    print(f"Classifications: {class_19}")
    print(f"Grants mal classifiés: {grants_19}")
    print(f"Dates uniques: {dates_19}, Fallback: {fallback_19}/{total_dates_19} ({fallback_19/total_dates_19*100:.1f}%)")
    
    print("\n[22 DEC] DONNEES 22 DECEMBRE 2025 (Avec ameliorations)")
    hall_22, total_22 = analyze_hallucinations('curated_items.json')
    class_22, grants_22 = analyze_event_classification('curated_items.json')
    dates_22, fallback_22, total_dates_22 = analyze_dates('items.json')
    
    print(f"Hallucinations: {hall_22}/{total_22} ({hall_22/total_22*100:.1f}%)")
    print(f"Classifications: {class_22}")
    print(f"Grants mal classifiés: {grants_22}")
    print(f"Dates uniques: {dates_22}, Fallback: {fallback_22}/{total_dates_22} ({fallback_22/total_dates_22*100:.1f}%)")
    
    print("\n[RESULT] AMELIORATION MESUREE")
    print(f"Hallucinations: {hall_19} -> {hall_22} ({-100*(hall_19-hall_22)/max(hall_19,1):+.0f}%)")
    print(f"Grants mal classifies: {grants_19} -> {grants_22} ({-100*(grants_19-grants_22)/max(grants_19,1):+.0f}%)")
    print(f"Dates fallback: {fallback_19/total_dates_19*100:.1f}% -> {fallback_22/total_dates_22*100:.1f}% ({fallback_22/total_dates_22*100-fallback_19/total_dates_19*100:+.1f}pp)")