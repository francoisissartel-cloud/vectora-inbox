#!/usr/bin/env python3
"""
Script universel d'ingestion - Moteur V3
Usage: python run_ingestion.py <client_config_name> [options]

Exemples:
  python run_ingestion.py lai_weekly_v3.1
  python run_ingestion.py test_medincell
  python run_ingestion.py lai_weekly_v3.1 --sources press_corporate__medincell

NOTE IMPORTANTE:
  La période d'ingestion (nombre de jours) DOIT être configurée dans le client config :
  
  ingestion:
    default_period_days: 200  # Nombre de jours à ingérer
  
  Le paramètre --period-days n'est plus autorisé pour garantir la cohérence.
"""

import sys
import argparse
import json
import yaml
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter src_v3 au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src_v3"))

def load_client_config(client_config_path):
    """Charge la configuration client pour l'affichage."""
    try:
        with open(client_config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[WARN] Impossible de charger le client config: {e}")
        return {}

def analyze_run_results(result, client_config, start_time, end_time):
    """Analyse détaillée des résultats du run."""
    manifest = result.get("run_manifest", {})
    run_id = result.get('run_id', 'unknown')
    
    # Charger les fichiers de résultats pour analyse détaillée
    try:
        base_path = Path("output/runs") / run_id
        
        ingested_items = []
        rejected_items = []
        
        if (base_path / "ingested_items.json").exists():
            with open(base_path / "ingested_items.json", 'r', encoding='utf-8') as f:
                ingested_data = json.load(f)
                # Vérifier si c'est une liste directe ou un objet avec des items
                if isinstance(ingested_data, list):
                    ingested_items = ingested_data
                elif isinstance(ingested_data, dict) and 'items' in ingested_data:
                    ingested_items = ingested_data['items']
        
        if (base_path / "rejected_items.json").exists():
            with open(base_path / "rejected_items.json", 'r', encoding='utf-8') as f:
                rejected_data = json.load(f)
                # Vérifier si c'est une liste directe ou un objet avec des items
                if isinstance(rejected_data, list):
                    rejected_items = rejected_data
                elif isinstance(rejected_data, dict) and 'items' in rejected_data:
                    rejected_items = rejected_data['items']
    except Exception as e:
        print(f"[WARN] Impossible de charger les fichiers de résultats: {e}")
        ingested_items = []
        rejected_items = []
    
    # Calculer les statistiques
    total_duration = end_time - start_time
    source_reports = manifest.get("source_reports", [])
    
    # Stats globales
    total_sources = len(source_reports)
    successful_sources = len([r for r in source_reports if r.status == "success"])
    failed_sources = total_sources - successful_sources
    
    total_items_found = sum(r.items_found or 0 for r in source_reports)
    total_ingested = len(ingested_items)
    total_rejected = len(rejected_items)
    
    # Analyser les raisons de rejet
    rejection_stats = {}
    period_filter_rejected = 0
    
    for item in rejected_items:
        filter_analysis = item.get('filter_analysis', {})
        
        # Compter les rejets par period_filter
        period_filter = filter_analysis.get('period_filter', {})
        if not period_filter.get('passed', True):
            period_filter_rejected += 1
        
        # Compter tous les types de rejets
        for filter_name, filter_data in filter_analysis.items():
            if filter_name == 'passed_all_filters':
                continue
            
            if isinstance(filter_data, dict) and not filter_data.get('passed', True):
                reason = filter_data.get('reason', 'unknown')
                key = f"{filter_name}:{reason}"
                rejection_stats[key] = rejection_stats.get(key, 0) + 1
    
    # Analyser par source
    source_stats = {}
    for item in ingested_items + rejected_items:
        source_key = item.get('source_key', 'unknown')
        if source_key not in source_stats:
            source_stats[source_key] = {'ingested': 0, 'rejected': 0}
        
        if item in ingested_items:
            source_stats[source_key]['ingested'] += 1
        else:
            source_stats[source_key]['rejected'] += 1
    
    return {
        'total_duration': total_duration,
        'total_sources': total_sources,
        'successful_sources': successful_sources,
        'failed_sources': failed_sources,
        'total_items_found': total_items_found,
        'total_ingested': total_ingested,
        'total_rejected': total_rejected,
        'period_filter_rejected': period_filter_rejected,
        'rejection_stats': rejection_stats,
        'source_stats': source_stats,
        'source_reports': source_reports
    }

def print_detailed_report(result, client_config, stats, args):
    """Affiche un rapport détaillé des résultats."""
    print("=" * 80)
    print("RAPPORT DETAILLE D'INGESTION")
    print("=" * 80)
    
    # Section 1: Configuration
    print("\n[CONFIG] CONFIGURATION DU RUN")
    print("-" * 40)
    print(f"Run ID: {result.get('run_id', 'unknown')}")
    print(f"Client: {args.client_config}")
    print(f"Duree totale: {stats['total_duration']}")
    
    # Informations du client config
    ingestion_config = client_config.get('ingestion', {})
    print(f"Mode d'ingestion: {ingestion_config.get('ingestion_mode', 'balanced')}")
    print(f"Periode (jours): {ingestion_config.get('default_period_days', 'non defini')}")
    
    # Informations de cache
    cache_enabled = ingestion_config.get('use_url_cache', False)
    if hasattr(args, 'no_cache') and args.no_cache:
        cache_enabled = False
    print(f"Cache URL: {'Activé' if cache_enabled else 'Désactivé'}")
    
    # Bouquets de sources
    source_bouquets = ingestion_config.get('source_bouquets', [])
    if source_bouquets:
        print(f"Bouquets: {', '.join(source_bouquets)}")
    
    # Watch domains
    watch_domains = client_config.get('watch_domains', [])
    if watch_domains:
        print(f"Watch domains: {len(watch_domains)} configures")
        for domain in watch_domains:
            print(f"  - {domain.get('id', 'unknown')}: {domain.get('type', 'unknown')} (priorite: {domain.get('priority', 'unknown')})")
    
    # Section 2: Statistiques globales
    print("\n[STATS] STATISTIQUES GLOBALES")
    print("-" * 40)
    print(f"Sources traitees: {stats['total_sources']} (OK: {stats['successful_sources']}, KO: {stats['failed_sources']})")
    print(f"Items trouves: {stats['total_items_found']}")
    print(f"Items ingeres: {stats['total_ingested']} ({stats['total_ingested']/max(stats['total_items_found'], 1)*100:.1f}%)")
    print(f"Items rejetes: {stats['total_rejected']} ({stats['total_rejected']/max(stats['total_items_found'], 1)*100:.1f}%)")
    
    if stats['period_filter_rejected'] > 0:
        print(f"Rejetes (trop anciens): {stats['period_filter_rejected']}")
    
    # Section 3: Analyse des rejets
    if stats['rejection_stats']:
        print("\n[REJETS] ANALYSE DES REJETS")
        print("-" * 40)
        for reason, count in sorted(stats['rejection_stats'].items(), key=lambda x: x[1], reverse=True):
            percentage = count / max(stats['total_rejected'], 1) * 100
            print(f"  {reason}: {count} items ({percentage:.1f}%)")
    
    # Section 4: Performance par source
    print("\n[SOURCES] PERFORMANCE PAR SOURCE")
    print("-" * 40)
    
    # Lister toutes les sources traitees
    all_sources = set(stats['source_stats'].keys())
    for report in stats['source_reports']:
        all_sources.add(report.source_key or 'unknown')
    
    for source_key in sorted(all_sources):
        source_data = stats['source_stats'].get(source_key, {'ingested': 0, 'rejected': 0})
        
        # Trouver le rapport correspondant
        source_report = next((r for r in stats['source_reports'] if r.source_key == source_key), None)
        
        total_items = source_data['ingested'] + source_data['rejected']
        status_icon = "[OK]" if source_report and source_report.status == "success" else "[KO]"
        
        if total_items > 0:
            ingestion_rate = source_data['ingested'] / total_items * 100
            print(f"  {status_icon} {source_key}: {total_items} items -> {source_data['ingested']} ingeres ({ingestion_rate:.1f}%), {source_data['rejected']} rejetes")
        else:
            print(f"  {status_icon} {source_key}: Aucun item trouve")
    
    # Section 5: Statistiques de Cache (si disponibles)
    manifest = result.get("run_manifest", {})
    cache_stats = manifest.get("cache_stats")
    if cache_stats:
        print("\n[CACHE] STATISTIQUES DE CACHE")
        print("-" * 40)
        total_urls = cache_stats.get('cache_hits', 0) + cache_stats.get('cache_misses', 0)
        if total_urls > 0:
            hit_rate = cache_stats.get('cache_hits', 0) / total_urls * 100
            print(f"URLs traitées: {total_urls}")
            print(f"Cache hits: {cache_stats.get('cache_hits', 0)} ({hit_rate:.1f}%)")
            print(f"Cache misses: {cache_stats.get('cache_misses', 0)} ({100-hit_rate:.1f}%)")
            print(f"URLs mises en cache: {cache_stats.get('urls_cached', 0)}")
            
            if cache_stats.get('cache_hits', 0) > 0:
                print(f"Temps économisé estimé: ~{cache_stats.get('cache_hits', 0) * 2}s")
        else:
            print("Aucune URL traitée avec le cache")
    
    # Section 6: Recommandations
    print("\n[RECOMMANDATIONS] ANALYSE ET CONSEILS")
    print("-" * 40)
    
    if stats['total_ingested'] == 0:
        print("  [WARN] Aucun item ingere - Verifier les filtres ou la periode")
    elif stats['total_ingested'] < 10:
        print("  [WARN] Peu d'items ingeres - Considerer le mode 'broad' ou augmenter la periode")
    
    if stats['failed_sources'] > 0:
        print(f"  [WARN] {stats['failed_sources']} sources en echec - Verifier la connectivite")
    
    if stats['period_filter_rejected'] > stats['total_ingested']:
        print("  [INFO] Beaucoup d'items trop anciens - Considerer augmenter default_period_days")
    
    # Identifier les filtres problematiques
    for reason, count in stats['rejection_stats'].items():
        if 'unknown' in reason and count > 5:
            print(f"  [ALERT] Probleme potentiel avec {reason} - {count} echecs")
    
    if stats['total_ingested'] > 0 and stats['failed_sources'] == 0:
        print("  [SUCCESS] Run reussi - Tous les systemes fonctionnent correctement")

def main():
    parser = argparse.ArgumentParser(description="Script universel d'ingestion V3")
    parser.add_argument("client_config", help="Nom du client config (ex: lai_weekly_v3.1)")
    parser.add_argument("--period-days", type=int, help="Nombre de jours à ingérer")
    parser.add_argument("--sources", nargs="+", help="Sources spécifiques à traiter")
    parser.add_argument("--bouquets", nargs="+", help="Bouquets de sources à traiter")
    parser.add_argument("--mode", choices=["strict", "balanced", "broad"], default="balanced", help="Mode d'ingestion")
    parser.add_argument("--simple", action="store_true", help="Affichage simple (sans rapport détaillé)")
    parser.add_argument("--no-cache", action="store_true", help="Désactiver le cache URL pour ce run")
    
    args = parser.parse_args()
    start_time = datetime.now()
    
    print("=" * 70)
    print("INGESTION VECTORA V3")
    print("=" * 70)
    print(f"Client: {args.client_config}")
    print(f"Début: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Importer le moteur V3
        from vectora_core.ingest import run_ingestion_v3
        
        # Préparer les paramètres
        # Déterminer le chemin du client config
        if args.client_config.endswith('.yaml') or '/' in args.client_config or '\\' in args.client_config:
            # Chemin direct fourni
            client_config_path = args.client_config
            client_id = Path(args.client_config).stem
        else:
            # Nom de config, chercher dans config/clients/
            client_config_path = f"config/clients/{args.client_config}.yaml"
            client_id = args.client_config
        
        # Charger le client config pour l'analyse
        client_config = load_client_config(client_config_path)
        
        # Appliquer l'option --no-cache
        config_overrides = {}
        if args.no_cache:
            config_overrides = {
                'ingestion': {
                    'use_url_cache': False
                }
            }
            print("[INFO] Cache URL désactivé pour ce run")
        
        params = {
            "client_id": client_id,
            "local_mode": True,
            "canonical_base_path": "canonical",
            "client_config_path": client_config_path
        }
        
        # Charger le client config pour l'analyse (avec overrides appliqués)
        final_client_config = client_config.copy()
        if config_overrides:
            for key, value in config_overrides.items():
                if key in final_client_config:
                    final_client_config[key].update(value)
                else:
                    final_client_config[key] = value
        
        # INTERDIRE le CLI override pour forcer l'utilisation du client config
        if args.period_days:
            print("[ERREUR] --period-days n'est plus autorisé.")
            print("La période doit être configurée dans le client config :")
            print(f"  ingestion.default_period_days: <nombre_de_jours>")
            print(f"Fichier: {client_config_path}")
            return 1
        
        if args.sources:
            params["specific_sources"] = args.sources
            print(f"Sources: {', '.join(args.sources)}")
        
        if args.bouquets:
            params["source_bouquets"] = args.bouquets
            print(f"Bouquets: {', '.join(args.bouquets)}")
        
        if args.mode != "balanced":
            if not config_overrides:
                config_overrides = {'ingestion': {}}
            elif 'ingestion' not in config_overrides:
                config_overrides['ingestion'] = {}
            config_overrides['ingestion']['ingestion_mode'] = args.mode
            print(f"Mode: {args.mode}")
        
        if config_overrides:
            params["config_overrides"] = config_overrides
        
        print()
        print("[RUN] Lancement ingestion...")
        
        # Exécuter l'ingestion
        result = run_ingestion_v3(**params)
        end_time = datetime.now()
        
        # Analyser les résultats
        stats = analyze_run_results(result, final_client_config, start_time, end_time)
        
        # Afficher les résultats
        if args.simple:
            # Affichage simple (ancien format)
            print()
            print("=" * 70)
            print("RESULTATS")
            print("=" * 70)
            
            if result["status"] == "success":
                print("[SUCCES] Ingestion terminee avec succes")
                print(f"Run ID: {result['run_id']}")
                
                manifest = result.get("run_manifest", {})
                if manifest:
                    print(f"Items ingeres: {manifest.get('total_items_ingested', 0)}")
                    print(f"Sources traitees: {len(manifest.get('source_reports', []))}")
                    
                    # Résumé par source
                    source_reports = manifest.get("source_reports", [])
                    if source_reports:
                        print()
                        print("Resume par source:")
                        for report in source_reports:
                            status_icon = "[OK]" if report.status == "success" else "[KO]"
                            items_count = report.items_found or 0
                            source_key = report.source_key or "unknown"
                            print(f"  {status_icon} {source_key}: {items_count} items")
            else:
                print("[ERREUR] Ingestion echouee")
                print(f"Erreur: {result.get('error', 'Erreur inconnue')}")
                return 1
        else:
            # Affichage détaillé (nouveau format)
            if result["status"] == "success":
                print_detailed_report(result, final_client_config, stats, args)
            else:
                print()
                print("=" * 70)
                print("ERREUR D'INGESTION")
                print("=" * 70)
                print(f"[ERREUR] Ingestion echouee")
                print(f"Erreur: {result.get('error', 'Erreur inconnue')}")
                return 1
        
        print(f"\nFin: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return 0
        
    except ImportError as e:
        print(f"[ERREUR] Impossible d'importer le moteur V3: {e}")
        print("Verifiez que src_v3/vectora_core est accessible")
        return 1
    except Exception as e:
        print(f"[ERREUR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())