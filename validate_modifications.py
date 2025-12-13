#!/usr/bin/env python3
"""
Script de validation rapide des modifications Vectora Inbox.
Exécute tous les tests et fournit un rapport de statut.
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Exécute une commande et retourne le résultat."""
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"[OK] {description} : SUCCES")
            return True
        else:
            print(f"[ERROR] {description} : ECHEC")
            print(f"Erreur: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] {description} : EXCEPTION - {e}")
        return False

def main():
    """Fonction principale de validation."""
    print("VALIDATION RAPIDE - Modifications Vectora Inbox")
    print("=" * 60)
    
    tests = [
        ("python tests/unit/test_normalization_open_world.py", "Tests Normalisation Open-World"),
        ("python tests/unit/test_scoring_recency.py", "Tests Scoring Recency"),
        ("python test_local_simulation.py", "Simulation Locale Bout-en-Bout")
    ]
    
    results = []
    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))
    
    # Résumé final
    print("\n" + "=" * 60)
    print("RÉSUMÉ DE VALIDATION")
    print("=" * 60)
    
    all_passed = True
    for desc, success in results:
        status = "[OK] SUCCES" if success else "[ERROR] ECHEC"
        print(f"{desc}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] TOUTES LES VALIDATIONS PASSENT")
        print("Les modifications sont prêtes pour déploiement DEV.")
        return 0
    else:
        print("[ERROR] CERTAINES VALIDATIONS ECHOUENT")
        print("Vérifiez les erreurs ci-dessus avant déploiement.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)