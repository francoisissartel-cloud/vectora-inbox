#!/usr/bin/env python3
"""
Script de création du Lambda Layer vectora-core.
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
LAYER_NAME = "vectora-inbox-vectora-core-dev"

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

def create_vectora_core_layer():
    log("Création du layer vectora-core...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        layer_dir = Path(temp_dir) / "python"
        layer_dir.mkdir()
        
        # Copier vectora_core
        src_core = Path("src_v2/vectora_core")
        if not src_core.exists():
            log(f"[ERREUR] vectora_core non trouvé: {src_core}")
            sys.exit(1)
        
        dest_core = layer_dir / "vectora_core"
        shutil.copytree(src_core, dest_core)
        log(f"[OK] vectora_core copié: {src_core}")
        
        # Installer dépendances (pyyaml, requests, boto3)
        log("Installation dépendances...")
        dependencies = ["pyyaml", "requests", "boto3"]
        for dep in dependencies:
            pip_command = f"pip install {dep} -t {layer_dir} --quiet"
            result = subprocess.run(pip_command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                log(f"[ERREUR] Installation {dep}: {result.stderr}")
                sys.exit(1)
        log(f"[OK] Dépendances installées: {', '.join(dependencies)}")
        
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
    log("=== Création du Lambda Layer vectora-core ===")
    
    try:
        layer_arn = create_vectora_core_layer()
        log(f"[SUCCES] Layer vectora-core créé: {layer_arn}")
        
        # Sauvegarder l'ARN pour les autres scripts
        with open("vectora_core_layer_arn.txt", "w") as f:
            f.write(layer_arn)
        
    except Exception as e:
        log(f"[ERREUR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()