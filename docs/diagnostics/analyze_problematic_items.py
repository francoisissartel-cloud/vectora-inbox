#!/usr/bin/env python3
import json

def analyze_problematic_items():
    """Analyser en détail les items problématiques"""
    print("=== ANALYSE ITEMS PROBLÉMATIQUES ===\n")
    
    # Charger les données curées
    with open('curated_items.json', 'r', encoding='utf-8') as f:
        curated_22 = json.load(f)
    
    # 1. Item Drug Delivery Conference (hallucination persistante)
    delsitech_item = None
    for item in curated_22:
        if 'delsitech' in item['item_id'] and 'drug-delivery' in item.get('url', '').lower():
            delsitech_item = item
            break
    
    if delsitech_item:
        print("1. ITEM DRUG DELIVERY CONFERENCE (Hallucination persistante)")
        print(f"   ID: {delsitech_item['item_id']}")
        print(f"   Title: {delsitech_item['title']}")
        print(f"   Content: {delsitech_item['content'][:100]}...")
        
        entities = delsitech_item.get('normalized_content', {}).get('entities', {})
        print(f"   Technologies détectées: {entities.get('technologies', [])}")
        print(f"   Trademarks détectées: {entities.get('trademarks', [])}")
        
        # Vérifier si les entités sont dans le contenu
        content_lower = delsitech_item['content'].lower()
        for tech in entities.get('technologies', []):
            if tech.lower() not in content_lower:
                print(f"   [X] HALLUCINATION: '{tech}' non present dans le contenu")
        
        for tm in entities.get('trademarks', []):
            if tm.lower() not in content_lower:
                print(f"   [X] HALLUCINATION: '{tm}' non present dans le contenu")
        print()
    
    # 2. Item Grant Medincell (classification incorrecte)
    grant_item = None
    for item in curated_22:
        if 'medincell' in item['item_id'] and 'grant' in item.get('title', '').lower():
            grant_item = item
            break
    
    if grant_item:
        print("2. ITEM MEDINCELL GRANT (Classification incorrecte)")
        print(f"   ID: {grant_item['item_id']}")
        print(f"   Title: {grant_item['title']}")
        
        event_class = grant_item.get('normalized_content', {}).get('event_classification', {})
        print(f"   Classification actuelle: {event_class.get('primary_type', 'unknown')}")
        print(f"   Confidence: {event_class.get('confidence', 0)}")
        print(f"   [X] ERREUR: Grant devrait etre classifie comme 'partnership', pas 'financial_results'")
        print()
    
    # 3. Analyser les dates (toutes identiques à la date d'ingestion)
    print("3. ANALYSE EXTRACTION DATES")
    dates_analysis = {}
    for item in curated_22:
        published_at = item.get('published_at')
        ingested_at = item.get('ingested_at', '')[:10]
        
        if published_at not in dates_analysis:
            dates_analysis[published_at] = {'count': 0, 'is_fallback': published_at == ingested_at}
        dates_analysis[published_at]['count'] += 1
    
    for date, info in dates_analysis.items():
        status = "FALLBACK" if info['is_fallback'] else "EXTRACTED"
        print(f"   {date}: {info['count']} items ({status})")
    
    if all(info['is_fallback'] for info in dates_analysis.values()):
        print("   [X] ERREUR: Aucune date reelle extraite, 100% fallback sur date ingestion")
    print()
    
    # 4. Analyser l'enrichissement de contenu
    print("4. ANALYSE ENRICHISSEMENT CONTENU")
    word_counts = []
    for item in curated_22:
        wc = item.get('metadata', {}).get('word_count', 0)
        word_counts.append(wc)
    
    avg_wc = sum(word_counts) / len(word_counts) if word_counts else 0
    short_items = len([wc for wc in word_counts if wc < 30])
    
    print(f"   Word count moyen: {avg_wc:.1f} mots")
    print(f"   Items courts (<30 mots): {short_items}/{len(word_counts)} ({short_items/len(word_counts)*100:.1f}%)")
    
    if avg_wc < 35:
        print("   [X] ERREUR: Pas d'enrichissement significatif du contenu")
    print()

def analyze_newsletter_regression():
    """Analyser la régression de la newsletter"""
    print("5. ANALYSE RÉGRESSION NEWSLETTER")
    
    # Newsletter 21 décembre (avec améliorations)
    with open('newsletter_v4.json', 'r', encoding='utf-8') as f:
        n21 = json.load(f)
    
    # Newsletter 22 décembre (régression)
    with open('newsletter_22dec.json', 'r', encoding='utf-8') as f:
        n22 = json.load(f)
    
    print("   21 DEC (améliorations actives):")
    for section in n21['sections']:
        print(f"     {section['section_id']}: {len(section['items'])} items")
    
    print("   22 DEC (régression):")
    for section in n22['sections']:
        print(f"     {section['section_id']}: {len(section['items'])} items")
    
    print(f"   [X] REGRESSION: Retour au mode 'top_signals' uniquement")
    print(f"   Distribution spécialisée non stable en production")

if __name__ == "__main__":
    analyze_problematic_items()
    analyze_newsletter_regression()