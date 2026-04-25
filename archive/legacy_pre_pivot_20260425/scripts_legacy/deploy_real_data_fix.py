#!/usr/bin/env python3
"""
Script de déploiement du fix "real data only" pour normalize_score_v2.

Ce script redéploie la Lambda avec les validations anti-données synthétiques.
"""

import json
import os
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# Configuration
LAMBDA_NAME = "vectora-inbox-normalize-score-v2-dev"
REGION = "eu-west-3"
PROFILE = "rag-lai-prod"

def create_deployment_package():
    """Crée le package de déploiement avec le code modifié."""
    print("Creation du package de deploiement...")
    
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src_v2"
    
    # Nom du package avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    package_name = f"normalize-score-v2-real-data-fix-{timestamp}.zip"
    package_path = project_root / package_name
    
    # Création du zip
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Handler Lambda
        handler_file = src_dir / "lambdas" / "normalize_score" / "handler.py"
        if handler_file.exists():
            zipf.write(handler_file, "handler.py")
            print(f"   Ajoute: handler.py")
        
        # Vectora Core complet
        vectora_core_dir = src_dir / "vectora_core"
        if vectora_core_dir.exists():
            for file_path in vectora_core_dir.rglob("*.py"):
                # Chemin relatif dans le zip
                arc_name = f"vectora_core/{file_path.relative_to(vectora_core_dir)}"
                zipf.write(file_path, arc_name)
            print(f"   Ajoute: vectora_core/ (complet)")
    
    print(f"   Package cree: {package_name}")
    return package_path

def deploy_lambda(package_path):
    """Déploie le package sur AWS Lambda."""
    print(f"Deploiement sur {LAMBDA_NAME}...")
    
    cmd = [
        "aws", "lambda", "update-function-code",
        "--function-name", LAMBDA_NAME,
        "--zip-file", f"fileb://{package_path}",
        "--profile", PROFILE,
        "--region", REGION
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("   Deploiement reussi")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   Erreur de deploiement: {e.stderr}")
        return False

def test_deployment():
    """Test rapide du déploiement."""
    print("Test du deploiement...")
    
    # Payload de test
    test_payload = {"client_id": "lai_weekly_v3"}
    
    cmd = [
        "aws", "lambda", "invoke",
        "--function-name", LAMBDA_NAME,
        "--payload", json.dumps(test_payload),
        "--profile", PROFILE,
        "--region", REGION,
        "response_real_data_fix.json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Lire la réponse
        with open("response_real_data_fix.json", 'r') as f:
            response = json.load(f)
        
        if response.get("statusCode") == 200:
            body = response.get("body", {})
            items_processed = body.get("statistics", {}).get("items_input", 0)
            print(f"   Test reussi - {items_processed} items traites")
            
            # Vérifier que ce ne sont pas les 5 items synthétiques
            if items_processed == 5:
                print("   ATTENTION: Toujours 5 items - verifier si le fix fonctionne")
            elif items_processed >= 10:
                print("   SUCCESS: Plus de 10 items traites - donnees reelles utilisees!")
            
            return True
        else:
            print(f"   Erreur Lambda: {response}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"   Erreur d'invocation: {e.stderr}")
        return False

def main():
    """Fonction principale."""
    print("Deploiement du fix 'Real Data Only' pour normalize_score_v2")
    print("=" * 70)
    
    try:
        # 1. Créer le package
        package_path = create_deployment_package()
        
        # 2. Déployer
        if not deploy_lambda(package_path):
            return False
        
        # 3. Tester
        if not test_deployment():
            print("\nLe deploiement a reussi mais le test a echoue")
            print("   Verifier les logs CloudWatch pour plus de details")
            return False
        
        print("\nDeploiement et test reussis!")
        print("\nProchaines etapes:")
        print("   1. Verifier les logs CloudWatch")
        print("   2. Lancer un test E2E complet")
        print("   3. Valider que les 15 items reels sont traites")
        
        # Nettoyage
        os.remove(package_path)
        if os.path.exists("response_real_data_fix.json"):
            os.remove("response_real_data_fix.json")
        
        return True
        
    except Exception as e:
        print(f"Erreur fatale: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)