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
from pathlib import Path
from datetime import datetime

# Ajouter src_v3 au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src_v3"))

def main():
    parser = argparse.ArgumentParser(description="Script universel d'ingestion V3")
    parser.add_argument("client_config", help="Nom du client config (ex: lai_weekly_v3.1)")
    parser.add_argument("--period-days", type=int, help="Nombre de jours à ingérer")
    parser.add_argument("--sources", nargs="+", help="Sources spécifiques à traiter")
    parser.add_argument("--bouquets", nargs="+", help="Bouquets de sources à traiter")
    parser.add_argument("--mode", choices=["strict", "balanced", "broad"], default="balanced", help="Mode d'ingestion")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("INGESTION VECTORA V3")
    print("=" * 70)
    print(f"Client: {args.client_config}")
    print(f"Debut: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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
        
        params = {
            "client_id": client_id,
            "local_mode": True,
            "canonical_base_path": "canonical",
            "client_config_path": client_config_path
        }
        
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
            params["ingestion_mode"] = args.mode
            print(f"Mode: {args.mode}")
        
        print()
        print("[RUN] Lancement ingestion...")
        
        # Exécuter l'ingestion
        result = run_ingestion_v3(**params)
        
        # Afficher les résultats
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
                
                # Afficher le chemin des résultats
                if "s3_paths" in manifest and manifest["s3_paths"]:
                    print("Fichiers generes:")
                    for key, path in manifest["s3_paths"].items():
                        print(f"  - {key}: {path}")
                
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
        
        print()
        print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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