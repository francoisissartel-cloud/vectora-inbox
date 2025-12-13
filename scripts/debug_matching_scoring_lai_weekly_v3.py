#!/usr/bin/env python3
"""
Script de debug pour analyser le matching et scoring LAI Weekly v3.

Ce script exécute localement la logique de matching + scoring (hors Lambda)
pour diagnostiquer pourquoi matched_domains est vide et les scores sont faibles.

Usage:
    python scripts/debug_matching_scoring_lai_weekly_v3.py
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# Ajouter le répertoire src au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vectora_core.config import loader
from vectora_core.matching import matcher
from vectora_core.scoring import scorer
from vectora_core.utils import logger

def load_test_data() -> List[Dict[str, Any]]:
    """
    Charge les données d'items normalisés pour les tests.
    Cherche d'abord les données lai_weekly_v3, puis v2 en fallback.
    """
    # Essayer de charger les données v3 les plus récentes
    v3_files = [
        "items_normalized_lai_weekly_v3_latest.json",
        "items-normalized-migration-validation.json",
        "items-normalized-phase1.json"
    ]
    
    for filename in v3_files:
        filepath = Path(filename)
        if filepath.exists():
            print(f"[LOAD] Chargement des données depuis {filename}")
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    print(f"[OK] {len(data)} items chargés depuis {filename}")
                    return data
    
    # Fallback sur v2
    v2_file = "items_normalized_lai_weekly_v2_run2.json"
    if Path(v2_file).exists():
        print(f"[LOAD] Fallback: Chargement des données v2 depuis {v2_file}")
        with open(v2_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                print(f"[OK] {len(data)} items chargés depuis {v2_file}")
                return data
    
    print("[ERROR] Aucun fichier de données trouvé")
    return []

def load_configurations() -> Dict[str, Any]:
    """
    Charge les configurations nécessaires pour le matching et scoring.
    """
    print("[CONFIG] Chargement des configurations...")
    
    configs = {}
    
    # Charger les scopes canonical
    try:
        configs['canonical_scopes'] = loader.load_canonical_scopes_local()
        print("[OK] Canonical scopes chargés")
    except Exception as e:
        print(f"[ERROR] Erreur chargement canonical scopes: {e}")
        return {}
    
    # Charger les règles de matching
    try:
        configs['matching_rules'] = loader.load_matching_rules_local()
        print("[OK] Matching rules chargées")
    except Exception as e:
        print(f"[ERROR] Erreur chargement matching rules: {e}")
        return {}
    
    # Charger les règles de scoring
    try:
        configs['scoring_rules'] = loader.load_scoring_rules_local()
        print("[OK] Scoring rules chargées")
    except Exception as e:
        print(f"[ERROR] Erreur chargement scoring rules: {e}")
        return {}
    
    # Charger la config client lai_weekly_v3
    try:
        configs['client_config'] = loader.load_client_config_local('lai_weekly_v3')
        print("[OK] Client config lai_weekly_v3 chargée")
    except Exception as e:
        print(f"[ERROR] Erreur chargement client config: {e}")
        return {}
    
    return configs

def analyze_item_gold(item: Dict[str, Any], item_id: str) -> Dict[str, Any]:
    """
    Analyse détaillée d'un item gold pour comprendre pourquoi il échoue.
    """
    analysis = {
        'item_id': item_id,
        'title': item.get('title', ''),
        'source_key': item.get('source_key', ''),
        'date': item.get('date', ''),
        'summary_length': len(item.get('summary', '')),
        'entities': {
            'companies_detected': item.get('companies_detected', []),
            'molecules_detected': item.get('molecules_detected', []),
            'technologies_detected': item.get('technologies_detected', []),
            'trademarks_detected': item.get('trademarks_detected', [])
        },
        'lai_fields': {
            'lai_relevance_score': item.get('lai_relevance_score'),
            'anti_lai_detected': item.get('anti_lai_detected'),
            'pure_player_context': item.get('pure_player_context')
        },
        'matched_domains': item.get('matched_domains', []),
        'score': item.get('score', 0)
    }
    
    # Analyser pourquoi les technologies ne sont pas détectées
    title_lower = item.get('title', '').lower()
    summary_lower = item.get('summary', '').lower()
    content = f"{title_lower} {summary_lower}"
    
    # Chercher des signaux LAI dans le contenu
    lai_signals_found = []
    lai_keywords = [
        'extended-release injectable', 'long-acting injectable', 'lai', 'depot injection',
        'pharmashell', 'uzedy', 'once-monthly', 'extended-release', 'injectable'
    ]
    
    for keyword in lai_keywords:
        if keyword in content:
            lai_signals_found.append(keyword)
    
    analysis['lai_signals_in_content'] = lai_signals_found
    analysis['has_lai_signals'] = len(lai_signals_found) > 0
    
    return analysis

def debug_matching_scoring():
    """
    Fonction principale de debug du matching et scoring.
    """
    print("[DEBUG] VECTORA INBOX - DEBUG MATCHING & SCORING LAI WEEKLY V3")
    print("=" * 60)
    
    # Charger les données de test
    items = load_test_data()
    if not items:
        print("[ERROR] Impossible de charger les données de test")
        return
    
    # Charger les configurations
    configs = load_configurations()
    if not configs:
        print("[ERROR] Impossible de charger les configurations")
        return
    
    # Extraire les watch_domains
    watch_domains = configs['client_config'].get('watch_domains', [])
    print(f"[INFO] Watch domains configurés: {len(watch_domains)}")
    for domain in watch_domains:
        print(f"  - {domain.get('id')} (type: {domain.get('type')}, priority: {domain.get('priority')})")
    
    print("\n" + "=" * 60)
    print("[GOLD] ANALYSE DES ITEMS GOLD")
    print("=" * 60)
    
    # Items gold à analyser spécifiquement
    gold_items = {
        'nanexa_moderna': 'Nanexa and Moderna enter into license and option agreement for the development of PharmaShell',
        'uzedy_bipolar': 'FDA Approves Expanded Indication for UZEDY',
        'uzedy_growth': 'UZEDY® continues strong growth',
        'medincell_malaria': 'Medincell Awarded New Grant to Fight Malaria',
        'medincell_olanzapine': 'Medincell\'s Partner Teva Pharmaceuticals Announces the New Drug Application Submission'
    }
    
    gold_analyses = {}
    
    # Chercher et analyser chaque item gold
    for gold_id, title_pattern in gold_items.items():
        matching_items = [item for item in items if title_pattern.lower() in item.get('title', '').lower()]
        
        if matching_items:
            item = matching_items[0]  # Prendre le premier match
            analysis = analyze_item_gold(item, gold_id)
            gold_analyses[gold_id] = analysis
            
            print(f"\n[ANALYZE] {gold_id.upper()}")
            print(f"   Titre: {analysis['title'][:80]}...")
            print(f"   Source: {analysis['source_key']}")
            print(f"   Summary: {'[OK] Présent' if analysis['summary_length'] > 0 else '[EMPTY] Vide'} ({analysis['summary_length']} chars)")
            print(f"   Companies: {analysis['entities']['companies_detected']}")
            print(f"   Technologies: {analysis['entities']['technologies_detected']}")
            print(f"   Molecules: {analysis['entities']['molecules_detected']}")
            print(f"   Matched domains: {analysis['matched_domains']}")
            print(f"   Score: {analysis['score']}")
            print(f"   LAI signals trouvés: {analysis['lai_signals_in_content']}")
            print(f"   LAI relevance score: {item.get('lai_relevance_score', 'N/A')}")
            print(f"   Anti-LAI detected: {item.get('anti_lai_detected', 'N/A')}")
            print(f"   Pure player context: {item.get('pure_player_context', 'N/A')}")
            print(f"   Trademarks detected: {item.get('trademarks_detected', [])}")
            
            if not analysis['entities']['technologies_detected'] and analysis['has_lai_signals']:
                print("   [WARNING] PROBLÈME: Signaux LAI présents mais technologies non détectées par Bedrock")
                print("   [INFO] Corrections Phase 1 appliquées - à retester avec Bedrock réel")
            
            if not analysis['matched_domains']:
                print("   [WARNING] PROBLÈME: Aucun domaine matché")
                print("   [INFO] Corrections Phase 3 appliquées - matching contextuel activé")
        else:
            print(f"\n[ERROR] {gold_id.upper()}: Item non trouvé dans les données")
    
    print("\n" + "=" * 60)
    print("[TEST] TEST DU MATCHING LOCAL")
    print("=" * 60)
    
    # Tester le matching sur un échantillon d'items
    sample_items = items[:20]  # Prendre les 20 premiers items
    
    print(f"[TEST] Test du matching sur {len(sample_items)} items...")
    
    try:
        matched_items = matcher.match_items_to_domains(
            sample_items,
            watch_domains,
            configs['canonical_scopes'],
            configs['matching_rules']
        )
        
        items_with_matches = [item for item in matched_items if item.get('matched_domains')]
        print(f"[OK] Matching terminé: {len(items_with_matches)}/{len(sample_items)} items matchés")
        
        # Analyser les résultats
        for item in items_with_matches[:5]:  # Afficher les 5 premiers
            print(f"  [OK] {item.get('title', '')[:50]}... → {item.get('matched_domains')}")
        
    except Exception as e:
        print(f"[ERROR] Erreur lors du matching: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("[STATS] STATISTIQUES GLOBALES")
    print("=" * 60)
    
    # Statistiques sur tous les items
    total_items = len(items)
    items_with_summary = len([item for item in items if item.get('summary')])
    items_with_companies = len([item for item in items if item.get('companies_detected')])
    items_with_technologies = len([item for item in items if item.get('technologies_detected')])
    items_with_matched_domains = len([item for item in items if item.get('matched_domains')])
    
    print(f"[STATS] Total items: {total_items}")
    print(f"[STATS] Items avec summary: {items_with_summary} ({items_with_summary/total_items*100:.1f}%)")
    print(f"[STATS] Items avec companies: {items_with_companies} ({items_with_companies/total_items*100:.1f}%)")
    print(f"[STATS] Items avec technologies: {items_with_technologies} ({items_with_technologies/total_items*100:.1f}%)")
    print(f"[STATS] Items avec matched_domains: {items_with_matched_domains} ({items_with_matched_domains/total_items*100:.1f}%)")
    
    # Sauvegarder les résultats
    results = {
        'timestamp': '2025-12-12T14:00:00Z',
        'total_items_analyzed': total_items,
        'gold_items_analysis': gold_analyses,
        'statistics': {
            'items_with_summary': items_with_summary,
            'items_with_companies': items_with_companies,
            'items_with_technologies': items_with_technologies,
            'items_with_matched_domains': items_with_matched_domains
        }
    }
    
    output_file = "debug_matching_scoring_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVE] Résultats sauvegardés dans {output_file}")
    
    print("\n" + "=" * 60)
    print("[CONCLUSION] CONCLUSIONS PRÉLIMINAIRES")
    print("=" * 60)
    
    if items_with_technologies == 0:
        print("[CRITICAL] PROBLÈME CRITIQUE: Aucune technology détectée dans tous les items")
        print("   → Problème probable dans la normalisation Bedrock")
        print("   → Les scopes technology_scopes.yaml semblent corrects")
    
    if items_with_matched_domains == 0:
        print("[CRITICAL] PROBLÈME CRITIQUE: Aucun matched_domains dans tous les items")
        print("   → Conséquence directe du problème de détection technology")
        print("   → Le matching ne peut pas fonctionner sans signaux technology")
    
    print("\n[OK] Debug terminé. Consultez le fichier de résultats pour plus de détails.")

if __name__ == "__main__":
    debug_matching_scoring()