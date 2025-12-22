#!/usr/bin/env python3
"""
Analyse de la structure des données curated lai_weekly_v4
"""

import json
import sys

def analyze_curated_data():
    """Analyse la structure des données curated"""
    
    with open('test_curated_items.json', 'r', encoding='utf-8') as f:
        items = json.load(f)
    
    print(f"Nombre d'items: {len(items)}")
    
    if items:
        # Analyser le premier item
        first_item = items[0]
        print("\n=== STRUCTURE DU PREMIER ITEM ===")
        print(f"Clés principales: {list(first_item.keys())}")
        
        # Analyser scoring_results
        if 'scoring_results' in first_item:
            scoring = first_item['scoring_results']
            print(f"\nScoring results: {list(scoring.keys())}")
            print(f"Final score: {scoring.get('final_score', 'N/A')}")
        else:
            print("\nPas de scoring_results trouvé")
        
        # Analyser normalized_content
        if 'normalized_content' in first_item:
            normalized = first_item['normalized_content']
            print(f"\nNormalized content: {list(normalized.keys())}")
            
            if 'entities' in normalized:
                entities = normalized['entities']
                print(f"Entities: {list(entities.keys())}")
                print(f"Companies: {entities.get('companies', [])[:3]}")
            
            if 'event_classification' in normalized:
                event_class = normalized['event_classification']
                print(f"Event classification: {event_class.get('primary_type', 'N/A')}")
            
            print(f"LAI relevance score: {normalized.get('lai_relevance_score', 'N/A')}")
        
        # Analyser matching_results
        if 'matching_results' in first_item:
            matching = first_item['matching_results']
            print(f"\nMatching results: {list(matching.keys())}")
            print(f"Matched domains: {matching.get('matched_domains', [])}")
        
        # Afficher quelques scores
        print(f"\n=== SCORES DE TOUS LES ITEMS ===")
        for i, item in enumerate(items[:5]):
            score = item.get('scoring_results', {}).get('final_score', 0)
            title = item.get('normalized_content', {}).get('summary', 'No title')[:50]
            print(f"Item {i+1}: Score {score} - {title}...")

if __name__ == "__main__":
    analyze_curated_data()