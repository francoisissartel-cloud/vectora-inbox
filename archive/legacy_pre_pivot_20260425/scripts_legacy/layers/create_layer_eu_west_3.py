#!/usr/bin/env python3
"""
Script de création du Lambda Layer common-deps pour eu-west-3.
"""

import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
import argparse
from pathlib import Path

def log(message):
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_aws_command(command, region, check=True):
    full_command = f"aws {command} --region {region}"
    log(f"Exécution: {full_command}")
    
    result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        log(f"[ERREUR] {result.stderr}")
        sys.exit(1)
    
    return result

def create_layer(layer_name, region):
    log(f"Création du layer {layer_name} dans {region}...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        layer_dir = Path(temp_dir) / "python"
        layer_dir.mkdir()
        
        # Utiliser le requirements.txt principal
        requirements_file = Path("src_v2/requirements.txt")
        if not requirements_file.exists():
            log(f"[ERREUR] requirements.txt non trouvé: {requirements_file}")
            sys.exit(1)
        
        log("Installation des dépendances...")
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
        
        # Créer le ZIP
        zip_path = Path(temp_dir) / f"{layer_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in layer_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(Path(temp_dir))
                    zipf.write(file_path, arcname)
        
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
        log(f"[OK] Layer ZIP créé: {zip_size_mb:.1f}MB")
        
        # Publier le layer
        publish_command = f"lambda publish-layer-version --layer-name {layer_name} --zip-file fileb://{zip_path} --compatible-runtimes python3.11"
        result = run_aws_command(publish_command, region)
        
        import json
        layer_info = json.loads(result.stdout)
        layer_arn = layer_info["LayerArn"]
        layer_version_arn = layer_info["LayerVersionArn"]
        
        log(f"[OK] Layer publié: {layer_arn}")
        log(f"[OK] Version ARN: {layer_version_arn}")
        
        return layer_version_arn

def main():
    parser = argparse.ArgumentParser(description='Créer un Lambda Layer')
    parser.add_argument('--layer-name', required=True, help='Nom du layer')
    parser.add_argument('--region', required=True, help='Région AWS')
    
    args = parser.parse_args()
    
    log(f"=== Création du Lambda Layer {args.layer_name} ===")
    
    try:
        layer_arn = create_layer(args.layer_name, args.region)
        log(f"[SUCCES] Layer créé: {layer_arn}")
        
        # Sauvegarder l'ARN
        with open(f"{args.layer_name}_arn.txt", "w") as f:
            f.write(layer_arn)
        
    except Exception as e:
        log(f"[ERREUR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()