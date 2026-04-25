#!/usr/bin/env python3
"""
Test MVP Sources - Script pour tester chaque source individuellement
Lance une ingestion pour chaque source MVP avec période 200 jours
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def test_single_source(source_name, source_key):
    """Teste une source individuelle"""
    print(f"[TEST] {source_name.upper()}")
    print("-" * 40)
    
    cmd = [
        "python", "run_ingestion.py",
        "lai_weekly_v3.1",
        "--sources", source_key,
        "--period-days", "200",
        "--mode", "balanced"
    ]
    
    print(f"Commande: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        if result.returncode == 0:
            print(f"[OK] {source_name} - SUCCES")
            return True
        else:
            print(f"[KO] {source_name} - ECHEC")
            return False
    except Exception as e:
        print(f"[ERREUR] {source_name} - {e}")
        return False

def main():
    print("=" * 70)
    print("TEST MVP SOURCES - VALIDATION INDIVIDUELLE")
    print("=" * 70)
    print(f"Debut: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Sources MVP à tester
    mvp_sources = [
        ("MedinCell", "press_corporate__medincell"),
        ("Camurus", "press_corporate__camurus"),
        ("Nanexa", "press_corporate__nanexa"),
        ("Pfizer", "press_corporate__pfizer"),
        ("Delsitech", "press_corporate__delsitech")
    ]
    
    results = {}
    
    for source_name, source_key in mvp_sources:
        success = test_single_source(source_name, source_key)
        results[source_name] = success
        print()
    
    # Résumé final
    print("=" * 70)
    print("RESUME FINAL")
    print("=" * 70)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for source_name, success in results.items():
        status = "[OK]" if success else "[KO]"
        print(f"{status} {source_name}")
    
    print()
    print(f"Resultat: {success_count}/{total_count} sources validees")
    
    if success_count == total_count:
        print("[SUCCES COMPLET] Toutes les sources MVP sont fonctionnelles")
        return 0
    else:
        print("[SUCCES PARTIEL] Certaines sources necessitent des ajustements")
        return 1

if __name__ == "__main__":
    sys.exit(main())