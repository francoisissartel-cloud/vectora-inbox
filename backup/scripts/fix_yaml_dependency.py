#!/usr/bin/env python3
"""
Script pour corriger la dépendance PyYAML manquante dans la lambda V2.

Ce script ajoute PyYAML au package Lambda en respectant les règles d'hygiène V4.
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path

# Configuration AWS
AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"
LAMBDA_NAME = "vectora-inbox-normalize-score-v2-dev"
CODE_BUCKET = "vectora-inbox-lambda-code-dev"

def log(message):
    """Log avec timestamp."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_aws_command(command, check=True):
    """Exécute une commande AWS CLI avec le profil correct."""
    full_command = f"aws {command} --profile {AWS_PROFILE} --region {AWS_REGION}"
    log(f"Exécution: {full_command}")
    
    result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        log(f"[ERREUR] {result.stderr}")
        sys.exit(1)
    
    return result

def create_lambda_package_with_yaml():
    """Crée le package Lambda avec PyYAML inclus."""
    log("Création du package Lambda avec PyYAML...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir) / "lambda_package"
        package_dir.mkdir()
        
        # Copier le handler
        src_handler = Path("src_v2/lambdas/normalize_score/handler.py")
        shutil.copy2(src_handler, package_dir / "handler.py")
        log(f"[OK] Handler copié: {src_handler}")
        
        # Copier vectora_core
        src_core = Path("src_v2/vectora_core")
        dest_core = package_dir / "vectora_core"
        shutil.copytree(src_core, dest_core)
        log(f"[OK] vectora_core copié: {src_core}")
        
        # Installer PyYAML dans le package
        log("Installation de PyYAML...")
        pip_command = f"pip install PyYAML -t {package_dir} --no-deps --platform linux_x86_64 --only-binary=:all:"
        result = subprocess.run(pip_command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            log("[ATTENTION] Installation binaire échouée, tentative installation pure Python...")
            pip_command = f"pip install PyYAML -t {package_dir} --no-deps"
            result = subprocess.run(pip_command, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                log(f"[ERREUR] Installation PyYAML échouée: {result.stderr}")
                sys.exit(1)
        
        log("[OK] PyYAML installé")
        
        # Nettoyer les fichiers inutiles
        for pattern in ["*.dist-info", "__pycache__", "*.pyc"]:
            for path in package_dir.rglob(pattern):
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        
        # Vérifier la taille
        package_size = sum(f.stat().st_size for f in package_dir.rglob('*') if f.is_file())
        package_size_mb = package_size / (1024 * 1024)
        log(f"[OK] Taille du package avec PyYAML: {package_size_mb:.1f}MB")
        
        # Créer le ZIP
        zip_path = Path(temp_dir) / f"{LAMBDA_NAME}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(package_dir)
                    zipf.write(file_path, arcname)
        
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
        log(f"[OK] Package ZIP créé: {zip_size_mb:.1f}MB")
        
        # Uploader vers S3
        s3_key = f"lambda-packages/{LAMBDA_NAME}.zip"
        run_aws_command(f"s3 cp {zip_path} s3://{CODE_BUCKET}/{s3_key}")
        log(f"[OK] Package uploadé: s3://{CODE_BUCKET}/{s3_key}")
        
        return s3_key

def update_lambda_code(s3_key):
    """Met à jour le code de la Lambda."""
    log(f"Mise à jour du code de la Lambda {LAMBDA_NAME}...")
    
    run_aws_command(f"lambda update-function-code --function-name {LAMBDA_NAME} --s3-bucket {CODE_BUCKET} --s3-key {s3_key}")
    log("[OK] Code Lambda mis à jour")

def test_lambda():
    """Teste la Lambda corrigée."""
    log("Test de la Lambda corrigée...")
    
    result = run_aws_command(f"lambda invoke --function-name {LAMBDA_NAME} --cli-binary-format raw-in-base64-out --payload '{{\"client_id\": \"lai_weekly_v3\"}}' response.json", check=False)
    
    if result.returncode == 0:
        if os.path.exists("response.json"):
            with open("response.json", 'r') as f:
                response = json.load(f)
            
            if "errorMessage" in response:
                log(f"[ERREUR] Lambda en erreur: {response['errorMessage']}")
                return False
            else:
                log("[OK] Lambda exécutée sans erreur")
                log(f"Réponse: {json.dumps(response, indent=2)}")
                return True
        else:
            log("[ERREUR] Pas de fichier de réponse")
            return False
    else:
        log(f"[ERREUR] Invocation échouée: {result.stderr}")
        return False

def main():
    """Fonction principale."""
    log("=== Correction dépendance PyYAML pour vectora-inbox-normalize-score-v2 ===")
    
    try:
        # 1. Créer le package avec PyYAML
        s3_key = create_lambda_package_with_yaml()
        
        # 2. Mettre à jour la Lambda
        update_lambda_code(s3_key)
        
        # 3. Tester
        success = test_lambda()
        
        if success:
            log("[SUCCES] Lambda corrigée et fonctionnelle!")
        else:
            log("[ATTENTION] Lambda déployée mais problème détecté")
        
        log(f"Lambda: {LAMBDA_NAME}")
        log(f"Région: {AWS_REGION}")
        
    except Exception as e:
        log(f"[ERREUR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()