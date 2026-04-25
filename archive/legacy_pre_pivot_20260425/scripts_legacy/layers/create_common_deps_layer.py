#!/usr/bin/env python3
"""
Script de création du Lambda Layer common-deps.
Conforme aux règles d'hygiène V4.
"""

import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path

# Configuration AWS (règles V4)
AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"
LAYER_NAME = "vectora-inbox-common-deps-dev"

def log(message):
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_aws_command(command, check=True):
    full_command = f"aws {command} --profile {AWS_PROFILE} --region {AWS_REGION}"
    log(f"Exécution: {full_command}")
    
    result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        log(f"[ERREUR] {result.stderr}")
        sys.exit(1)
    
    return result

def create_common_deps_layer():
    log("Création du layer common-deps...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        layer_dir = Path(temp_dir) / "python"
        layer_dir.mkdir()
        
        # Installer les dépendances depuis requirements.txt
        requirements_file = Path("src_v2/lambdas/normalize_score/requirements.txt")
        if not requirements_file.exists():
            log(f"[ERREUR] requirements.txt non trouvé: {requirements_file}")
            sys.exit(1)
        
        log("Installation des dépendances...")
        pip_command = f"pip install -r {requirements_file} -t {layer_dir} --platform linux_x86_64 --only-binary=:all:"
        result = subprocess.run(pip_command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            log("[ATTENTION] Installation binaire échouée, tentative pure Python...")
            pip_command = f"pip install -r {requirements_file} -t {layer_dir}"
            result = subprocess.run(pip_command, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                log(f"[ERREUR] Installation dépendances échouée: {result.stderr}")
                sys.exit(1)
        
        log("[OK] Dépendances installées")
        
        # Nettoyer les fichiers inutiles
        log("Nettoyage des fichiers inutiles...")
        for pattern in ["*.dist-info", "__pycache__", "*.pyc", "*.pyo"]:
            for path in layer_dir.rglob(pattern):
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.is_file():
                    path.unlink()
        
        # Supprimer tests et docs
        for pattern in ["test*", "tests", "docs", "examples"]:
            for path in layer_dir.rglob(pattern):
                if path.is_dir():
                    shutil.rmtree(path)
        
        # Vérifier la taille
        layer_size = sum(f.stat().st_size for f in layer_dir.rglob('*') if f.is_file())
        layer_size_mb = layer_size / (1024 * 1024)
        log(f"[OK] Taille du layer: {layer_size_mb:.1f}MB")
        
        if layer_size_mb > 50:
            log(f"[ERREUR] Layer trop volumineux: {layer_size_mb:.1f}MB (limite: 50MB)")
            sys.exit(1)
        
        # Créer le ZIP
        zip_path = Path(temp_dir) / f"{LAYER_NAME}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in layer_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(Path(temp_dir))
                    zipf.write(file_path, arcname)
        
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
        log(f"[OK] Layer ZIP créé: {zip_size_mb:.1f}MB")
        
        # Publier le layer
        publish_command = f"lambda publish-layer-version --layer-name {LAYER_NAME} --zip-file fileb://{zip_path} --compatible-runtimes python3.11 python3.12"
        result = run_aws_command(publish_command)
        
        import json
        layer_info = json.loads(result.stdout)
        layer_arn = layer_info["LayerArn"]
        layer_version_arn = layer_info["LayerVersionArn"]
        
        log(f"[OK] Layer publié: {layer_arn}")
        log(f"[OK] Version ARN: {layer_version_arn}")
        
        return layer_version_arn

def main():
    log("=== Création du Lambda Layer common-deps ===")
    
    try:
        layer_arn = create_common_deps_layer()
        log(f"[SUCCES] Layer common-deps créé: {layer_arn}")
        
        # Sauvegarder l'ARN pour les autres scripts
        with open("common_deps_layer_arn.txt", "w") as f:
            f.write(layer_arn)
        
    except Exception as e:
        log(f"[ERREUR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()