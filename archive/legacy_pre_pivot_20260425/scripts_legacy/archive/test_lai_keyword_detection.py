#!/usr/bin/env python3
"""
Script de test pour vérifier la détection des mots-clés LAI
dans l'article Pfizer sur l'anticorps trispecifique.

Usage: python test_lai_keyword_detection.py
"""

import json
import re
import yaml
from pathlib import Path

def load_lai_keywords():
    """Charge les mots-clés LAI depuis la configuration"""
    config_path = Path("C:/Users/franc/OneDrive/Bureau/vectora-inbox/canonical/imports/vectora-inbox-lai-core-scopes.yaml")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    keywords = config['lai_scopes']['technologies']['lai_keywords']
    return keywords

def load_rejected_article():
    """Charge l'article rejeté spécifique"""
    rejected_path = Path("C:/Users/franc/OneDrive/Bureau/vectora-inbox/output/runs/lai_weekly__20260420_184149_2bcc04d5/rejected_items.json")
    
    with open(rejected_path, 'r', encoding='utf-8') as f:
        rejected_items = json.load(f)
    
    # Trouve l'article avec le hash spécifique
    target_hash = "sha256:41a2561b3026a6287d28406eb89460ed5a184666b060602b0f3745891a2ff33c"
    
    for item in rejected_items:
        if item.get('content_hash') == target_hash:
            return item
    
    return None

def test_keyword_detection(content, keywords, case_sensitive=False):
    """Teste la détection des mots-clés dans le contenu"""
    found_keywords = []
    
    # Prépare le contenu pour la recherche
    search_content = content if case_sensitive else content.lower()
    
    for keyword in keywords:
        search_keyword = keyword if case_sensitive else keyword.lower()
        
        # Test de correspondance exacte
        if search_keyword in search_content:
            # Trouve toutes les positions
            positions = []
            start = 0
            while True:
                pos = search_content.find(search_keyword, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
            
            found_keywords.append({
                'keyword': keyword,
                'positions': positions,
                'count': len(positions)
            })
    
    return found_keywords

def extract_context(content, keyword, position, context_length=100):
    """Extrait le contexte autour d'un mot-clé trouvé"""
    start = max(0, position - context_length)
    end = min(len(content), position + len(keyword) + context_length)
    
    context = content[start:end]
    # Marque le mot-clé
    keyword_start = position - start
    keyword_end = keyword_start + len(keyword)
    
    return {
        'before': context[:keyword_start],
        'keyword': context[keyword_start:keyword_end],
        'after': context[keyword_end:],
        'full_context': context
    }

def main():
    print("=== TEST DE DÉTECTION DES MOTS-CLÉS LAI ===\n")
    
    # Charge les données
    print("1. Chargement des mots-clés LAI...")
    keywords = load_lai_keywords()
    print(f"   -> {len(keywords)} mots-cles charges")
    
    print("\n2. Chargement de l'article rejeté...")
    article = load_rejected_article()
    
    if not article:
        print("   ERREUR Article non trouve!")
        return
    
    print(f"   -> Article trouve: {article['title']}")
    print(f"   -> Date: {article['published_at']}")
    print(f"   -> Hash: {article['content_hash']}")
    
    # Test de détection
    print("\n3. Test de détection des mots-clés...")
    
    # Test insensible à la casse
    found_keywords = test_keyword_detection(article['content'], keywords, case_sensitive=False)
    
    if found_keywords:
        print(f"   OK {len(found_keywords)} mots-cles LAI detectes!")
        
        for kw_info in found_keywords:
            print(f"\n   * Mot-cle: '{kw_info['keyword']}'")
            print(f"      Occurrences: {kw_info['count']}")
            
            # Montre le contexte pour la première occurrence
            if kw_info['positions']:
                context = extract_context(article['content'], kw_info['keyword'], kw_info['positions'][0])
                print(f"      Contexte: ...{context['before']}[{context['keyword']}]{context['after']}...")
    else:
        print("   ERREUR Aucun mot-cle LAI detecte!")
    
    # Test spécifique pour "once-monthly"
    print("\n4. Test spécifique pour 'once-monthly'...")
    
    content_lower = article['content'].lower()
    if 'once-monthly' in content_lower:
        print("   OK 'once-monthly' trouve dans le contenu!")
        
        # Trouve toutes les occurrences
        positions = []
        start = 0
        while True:
            pos = content_lower.find('once-monthly', start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        print(f"   -> {len(positions)} occurrence(s) trouvee(s)")
        
        for i, pos in enumerate(positions):
            context = extract_context(article['content'], 'once-monthly', pos)
            print(f"   Occurrence {i+1}: ...{context['before']}[{context['keyword']}]{context['after']}...")
    else:
        print("   ERREUR 'once-monthly' non trouve!")
    
    # Analyse du filtre original
    print("\n5. Analyse du filtre original...")
    filter_analysis = article.get('filter_analysis', {})
    lai_filter = filter_analysis.get('lai_keyword_filter', {})
    
    print(f"   Filtre LAI requis: {lai_filter.get('required', 'N/A')}")
    print(f"   Filtre LAI passé: {lai_filter.get('passed', 'N/A')}")
    print(f"   Mots-clés trouvés: {lai_filter.get('keywords_found', [])}")
    print(f"   Raison d'échec: {lai_filter.get('failure_reason', 'N/A')}")
    
    # Recommandations
    print("\n6. Recommandations:")
    if found_keywords:
        print("   OK Les mots-cles LAI sont detectables dans le contenu")
        print("   -> Le probleme vient probablement du filtre temporel qui elimine l'article avant l'analyse LAI")
        print("   -> Ou d'un probleme dans l'implementation du filtre LAI du systeme")
    else:
        print("   ERREUR Aucun mot-cle LAI detecte meme manuellement")
        print("   -> Verifier la liste des mots-cles LAI")
        print("   -> Verifier l'extraction du contenu")

if __name__ == "__main__":
    main()