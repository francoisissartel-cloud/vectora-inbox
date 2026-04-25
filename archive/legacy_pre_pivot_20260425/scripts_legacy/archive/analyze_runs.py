#!/usr/bin/env python3
"""
Script d'analyse des runs pour identifier facilement
les configurations et résultats.
"""

import json
from pathlib import Path
from datetime import datetime

def analyze_runs():
    """Analyse tous les runs dans output/runs/"""
    
    runs_dir = Path("output/runs")
    if not runs_dir.exists():
        print("Aucun dossier de runs trouve")
        return
    
    runs = []
    
    for run_dir in runs_dir.iterdir():
        if run_dir.is_dir():
            debug_file = run_dir / "debug_report.json"
            
            if debug_file.exists():
                with open(debug_file, 'r', encoding='utf-8') as f:
                    debug_data = json.load(f)
                
                # Extraction des infos du nom du dossier
                run_name = run_dir.name
                parts = run_name.split('__')
                
                if len(parts) >= 2:
                    client_prefix = parts[0]
                    timestamp_hash = parts[1] if len(parts) == 2 else '__'.join(parts[1:])
                else:
                    client_prefix = run_name
                    timestamp_hash = "unknown"
                
                # Analyse des fichiers
                ingested_file = run_dir / "ingested_items.json"
                rejected_file = run_dir / "rejected_items.json"
                
                ingested_count = 0
                rejected_count = 0
                
                if ingested_file.exists():
                    with open(ingested_file, 'r', encoding='utf-8') as f:
                        ingested_items = json.load(f)
                        ingested_count = len(ingested_items)
                
                if rejected_file.exists():
                    with open(rejected_file, 'r', encoding='utf-8') as f:
                        rejected_items = json.load(f)
                        rejected_count = len(rejected_items)
                
                runs.append({
                    "run_id": debug_data.get("run_id", run_name),
                    "client_prefix": client_prefix,
                    "timestamp": debug_data.get("generated_at", "unknown"),
                    "ingested": ingested_count,
                    "rejected": rejected_count,
                    "total": ingested_count + rejected_count,
                    "success_rate": round(ingested_count / (ingested_count + rejected_count) * 100, 1) if (ingested_count + rejected_count) > 0 else 0,
                    "path": str(run_dir)
                })
    
    # Tri par timestamp decroissant
    runs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Affichage
    print("ANALYSE DES RUNS")
    print("=" * 100)
    print(f"{'RUN_ID':<50} {'INGERE':<8} {'REJETE':<8} {'TOTAL':<8} {'TAUX':<8}")
    print("-" * 100)
    
    for run in runs:
        print(f"{run['run_id']:<50} {run['ingested']:<8} {run['rejected']:<8} {run['total']:<8} {run['success_rate']:<7}%")
    
    print(f"\nTOTAL: {len(runs)} runs analyses")
    
    # Analyse par client_prefix
    print("\nANALYSE PAR CLIENT:")
    print("-" * 50)
    
    clients = {}
    for run in runs:
        prefix = run['client_prefix']
        if prefix not in clients:
            clients[prefix] = {'count': 0, 'total_ingested': 0, 'total_rejected': 0}
        
        clients[prefix]['count'] += 1
        clients[prefix]['total_ingested'] += run['ingested']
        clients[prefix]['total_rejected'] += run['rejected']
    
    for client, stats in clients.items():
        total = stats['total_ingested'] + stats['total_rejected']
        rate = round(stats['total_ingested'] / total * 100, 1) if total > 0 else 0
        print(f"{client:<30} {stats['count']:<8} runs, {stats['total_ingested']:<8} ingeres, {rate:<7}% taux")

if __name__ == "__main__":
    analyze_runs()