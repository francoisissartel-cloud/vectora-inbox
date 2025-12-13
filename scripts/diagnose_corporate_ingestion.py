#!/usr/bin/env python3
"""
Script de diagnostic de l'ingestion corporate HTML.

Ce script teste les 5 sources corporate du MVP LAI et génère
un rapport de métriques détaillé.
"""

import sys
import os
import time
import yaml
from pathlib import Path

# Ajouter le répertoire src au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vectora_core.ingestion.fetcher import fetch_source
from vectora_core.ingestion.parser import parse_source_content
from vectora_core.ingestion.metrics_collector import IngestionMetrics


def load_source_catalog():
    """Charge le catalogue des sources."""
    catalog_path = Path(__file__).parent.parent / 'canonical' / 'sources' / 'source_catalog.yaml'
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = yaml.safe_load(f)
    
    return catalog['sources']


def get_corporate_sources():
    """Récupère les sources corporate HTML du MVP LAI."""
    sources = load_source_catalog()
    
    corporate_sources = []
    for source in sources:
        if (source.get('source_type') == 'press_corporate' and 
            source.get('ingestion_mode') == 'html' and 
            source.get('enabled', False)):
            corporate_sources.append(source)
    
    return corporate_sources


def test_source_ingestion(source_meta):
    """
    Teste l'ingestion d'une source et retourne les métriques.
    
    Args:
        source_meta: Métadonnées de la source
    
    Returns:
        Dict avec les résultats du test
    """
    source_key = source_meta['source_key']
    print(f"\\n🔍 Test de {source_key}...")
    
    start_time = time.time()
    
    # Étape 1: Fetch
    print(f"  📥 Récupération depuis {source_meta.get('html_url', 'URL manquante')}")
    raw_content = fetch_source(source_meta)
    
    fetch_success = raw_content is not None
    fetch_time = time.time() - start_time
    
    if not fetch_success:
        return {
            'source_key': source_key,
            'fetch_success': False,
            'parse_success': False,
            'items_found': 0,
            'items_valid': 0,
            'items_with_date': 0,
            'execution_time': fetch_time,
            'errors': ['Échec de la récupération HTTP'],
            'status': 'ERROR'
        }
    
    print(f"  ✅ Récupération réussie: {len(raw_content)} caractères")
    
    # Étape 2: Parse
    print(f"  🔧 Parsing HTML...")
    parse_start = time.time()
    
    metrics_collector = IngestionMetrics()
    items = parse_source_content(raw_content, source_meta, metrics_collector)
    
    parse_time = time.time() - parse_start
    total_time = time.time() - start_time
    
    # Calculer les métriques
    items_with_date = sum(1 for item in items if item.get('published_at') != time.strftime('%Y-%m-%d'))
    
    result = {
        'source_key': source_key,
        'fetch_success': True,
        'parse_success': len(items) > 0,
        'items_found': len(items),
        'items_valid': len(items),
        'items_with_date': items_with_date,
        'execution_time': total_time,
        'fetch_time': fetch_time,
        'parse_time': parse_time,
        'errors': [],
        'status': 'OK' if len(items) > 0 else 'ERROR',
        'sample_items': items[:3] if items else []  # Échantillon pour debug
    }
    
    # Récupérer les métriques détaillées du collecteur
    source_metrics = metrics_collector.get_source_metrics(source_key)
    if source_metrics:
        result['errors'] = source_metrics.get('errors', [])
        if source_metrics['errors']:
            result['status'] = 'WARNING' if len(items) > 0 else 'ERROR'
    
    print(f"  📊 Résultat: {result['status']} - {len(items)} items extraits")
    if result['errors']:
        print(f"  ⚠️  Erreurs: {', '.join(result['errors'])}")
    
    return result


def diagnose_corporate_sources():
    """Diagnostic complet des sources corporate HTML."""
    print("🚀 Diagnostic de l'ingestion corporate HTML - Vectora Inbox")
    print("=" * 60)
    
    # Charger les sources corporate
    corporate_sources = get_corporate_sources()
    print(f"📋 Sources corporate à tester: {len(corporate_sources)}")
    
    # Tester chaque source
    results = {}
    metrics_collector = IngestionMetrics()
    
    for source_meta in corporate_sources:
        result = test_source_ingestion(source_meta)
        results[result['source_key']] = result
        
        # Enregistrer dans le collecteur global
        metrics_collector.record_source_metrics(result['source_key'], {
            'pages_fetched': 1 if result['fetch_success'] else 0,
            'items_found': result['items_found'],
            'items_valid': result['items_valid'],
            'items_with_date': result['items_with_date'],
            'execution_time': result['execution_time'],
            'errors': result['errors'],
            'fetch_success': result['fetch_success'],
            'parse_success': result['parse_success']
        })
    
    # Générer le rapport
    print("\\n" + "=" * 60)
    print("📈 RAPPORT DE SYNTHÈSE")
    print("=" * 60)
    
    total_sources = len(results)
    sources_ok = sum(1 for r in results.values() if r['status'] == 'OK')
    sources_warning = sum(1 for r in results.values() if r['status'] == 'WARNING')
    sources_error = sum(1 for r in results.values() if r['status'] == 'ERROR')
    
    total_items = sum(r['items_valid'] for r in results.values())
    total_items_with_date = sum(r['items_with_date'] for r in results.values())
    
    print(f"Sources testées: {total_sources}")
    print(f"✅ Sources OK: {sources_ok} ({sources_ok/total_sources*100:.1f}%)")
    print(f"⚠️  Sources WARNING: {sources_warning}")
    print(f"❌ Sources ERROR: {sources_error}")
    print(f"📊 Taux de succès: {sources_ok/total_sources*100:.1f}%")
    print(f"📄 Items extraits: {total_items}")
    print(f"📅 Items avec date: {total_items_with_date} ({total_items_with_date/total_items*100 if total_items > 0 else 0:.1f}%)")
    
    print("\\n📋 DÉTAIL PAR SOURCE:")
    print("-" * 60)
    
    for source_key, result in results.items():
        status_emoji = {'OK': '🟢', 'WARNING': '🟡', 'ERROR': '🔴'}.get(result['status'], '❓')
        print(f"{status_emoji} {source_key}")
        print(f"   Items: {result['items_valid']}, Dates: {result['items_with_date']}, Temps: {result['execution_time']:.1f}s")
        if result['errors']:
            print(f"   Erreurs: {', '.join(result['errors'])}")
        print()
    
    # Sauvegarder le rapport
    report_path = Path(__file__).parent.parent / 'docs' / 'diagnostics' / 'vectora_inbox_corporate_ingestion_metrics_summary.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    metrics_collector.save_report_to_file(str(report_path), format='markdown')
    print(f"📄 Rapport détaillé sauvegardé: {report_path}")
    
    # Sauvegarder aussi en JSON pour analyse
    json_path = report_path.with_suffix('.json')
    metrics_collector.save_report_to_file(str(json_path), format='json')
    print(f"📊 Données JSON sauvegardées: {json_path}")
    
    return results


if __name__ == '__main__':
    try:
        results = diagnose_corporate_sources()
        
        # Code de sortie basé sur les résultats
        sources_error = sum(1 for r in results.values() if r['status'] == 'ERROR')
        if sources_error == 0:
            print("\\n🎉 Tous les tests sont passés avec succès!")
            sys.exit(0)
        else:
            print(f"\\n⚠️  {sources_error} source(s) en erreur détectée(s)")
            sys.exit(1)
    
    except Exception as e:
        print(f"\\n💥 Erreur lors du diagnostic: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)