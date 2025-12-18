#!/usr/bin/env python3
"""
Script de déploiement pour normalize_score_v2 avec Lambda Layers.
Conforme aux règles d'hygiène V4.
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path

# Configuration AWS (règles V4)
AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"
AWS_ACCOUNT = "786469175371"

# Configuration Lambda
LAMBDA_NAME = "vectora-inbox-normalize-score-v2-dev"
LAMBDA_RUNTIME = "python3.11"
LAMBDA_TIMEOUT = 900
LAMBDA_MEMORY = 1024

# Buckets S3 (conventions V4)
CONFIG_BUCKET = "vectora-inbox-config-dev"
DATA_BUCKET = "vectora-inbox-data-dev"
CODE_BUCKET = "vectora-inbox-lambda-code-dev"

# Configuration Bedrock
BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
BEDROCK_REGION = "us-east-1"

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

def get_layer_arns():
    """Récupère les ARNs des layers depuis les fichiers."""
    log("Récupération des ARNs des layers...")
    
    try:
        with open("vectora_core_layer_arn.txt", "r") as f:
            vectora_core_arn = f.read().strip()
        with open("common_deps_layer_arn.txt", "r") as f:
            common_deps_arn = f.read().strip()
        
        log(f"[OK] Layer vectora-core: {vectora_core_arn}")
        log(f"[OK] Layer common-deps: {common_deps_arn}")
        
        return [vectora_core_arn, common_deps_arn]
    
    except FileNotFoundError as e:
        log(f"[ERREUR] Fichier ARN manquant: {e}")
        log("Exécutez d'abord les scripts de création des layers")
        sys.exit(1)

def upload_handler_package():
    """Upload le package handler vers S3."""
    log("Upload du package handler vers S3...")
    
    handler_zip = Path("vectora-inbox-normalize-score-v2-dev-handler-only.zip")
    if not handler_zip.exists():
        log(f"[ERREUR] Package handler non trouvé: {handler_zip}")
        log("Exécutez d'abord le script de build")
        sys.exit(1)
    
    s3_key = f"lambda-packages/{LAMBDA_NAME}-handler.zip"
    run_aws_command(f"s3 cp {handler_zip} s3://{CODE_BUCKET}/{s3_key}")
    log(f"[OK] Package uploadé: s3://{CODE_BUCKET}/{s3_key}")
    
    return s3_key

def get_lambda_role_arn():
    """Récupère l'ARN du rôle IAM pour la Lambda."""
    log("Recherche du rôle IAM Lambda...")
    
    role_name = "vectora-inbox-s0-iam-dev-IngestNormalizeRole-aefpODOGz3Lx"
    result = run_aws_command(f"iam get-role --role-name {role_name}", check=False)
    
    if result.returncode == 0:
        role_info = json.loads(result.stdout)
        role_arn = role_info["Role"]["Arn"]
        log(f"[OK] Rôle trouvé: {role_arn}")
        return role_arn
    else:
        log(f"[ERREUR] Rôle {role_name} non trouvé")
        sys.exit(1)

def deploy_lambda_with_layers(s3_key, layer_arns, role_arn):
    """Déploie ou met à jour la Lambda avec les layers."""
    log(f"Déploiement de la Lambda {LAMBDA_NAME} avec layers...")
    
    # Vérifier si la Lambda existe
    result = run_aws_command(f"lambda get-function --function-name {LAMBDA_NAME}", check=False)
    
    # Variables d'environnement
    env_vars = {
        "ENV": "dev",
        "PROJECT_NAME": "vectora-inbox",
        "CONFIG_BUCKET": CONFIG_BUCKET,
        "DATA_BUCKET": DATA_BUCKET,
        "BEDROCK_MODEL_ID": BEDROCK_MODEL_ID,
        "BEDROCK_REGION": BEDROCK_REGION,
        "LOG_LEVEL": "INFO"
    }
    
    if result.returncode == 0:
        # Mise à jour du code
        log("Lambda existante - mise à jour du code...")
        run_aws_command(f"lambda update-function-code --function-name {LAMBDA_NAME} --s3-bucket {CODE_BUCKET} --s3-key {s3_key}")
        
        # Mise à jour de la configuration avec layers
        log("Mise à jour de la configuration avec layers...")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"Variables": env_vars}, f)
            env_file = f.name
        
        try:
            layers_str = " ".join(layer_arns)
            update_config_command = f"lambda update-function-configuration --function-name {LAMBDA_NAME} --timeout {LAMBDA_TIMEOUT} --memory-size {LAMBDA_MEMORY} --environment file://{env_file} --layers {layers_str}"
            run_aws_command(update_config_command)
        finally:
            os.remove(env_file)
    
    else:
        # Création de la Lambda avec layers
        log("Création de la nouvelle Lambda avec layers...")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"Variables": env_vars}, f)
            env_file = f.name
        
        try:
            layers_str = " ".join(layer_arns)
            create_command = f"lambda create-function --function-name {LAMBDA_NAME} --runtime {LAMBDA_RUNTIME} --role {role_arn} --handler handler.lambda_handler --code S3Bucket={CODE_BUCKET},S3Key={s3_key} --timeout {LAMBDA_TIMEOUT} --memory-size {LAMBDA_MEMORY} --environment file://{env_file} --layers {layers_str}"
            run_aws_command(create_command)
        finally:
            os.remove(env_file)
    
    log(f"[OK] Lambda {LAMBDA_NAME} déployée avec layers")

def verify_deployment():
    """Vérifie le déploiement de la Lambda."""
    log("Vérification du déploiement...")
    
    result = run_aws_command(f"lambda get-function --function-name {LAMBDA_NAME}")
    function_info = json.loads(result.stdout)
    
    # Vérifier les layers
    layers = function_info["Configuration"].get("Layers", [])
    log(f"[OK] Layers configurés: {len(layers)}")
    for layer in layers:
        log(f"  - {layer['Arn']}")
    
    # Vérifier la taille du code
    code_size = function_info["Configuration"]["CodeSize"]
    code_size_kb = code_size / 1024
    log(f"[OK] Taille du code: {code_size_kb:.1f}KB")
    
    if code_size < 10000:  # <10KB
        log("[EXCELLENT] Handler très léger grâce aux layers")
    
    return True

def main():
    log("=== Déploiement normalize_score_v2 avec Lambda Layers ===")
    log(f"Environnement: {AWS_REGION}, Profil: {AWS_PROFILE}")
    
    try:
        # 1. Récupérer les ARNs des layers
        layer_arns = get_layer_arns()
        
        # 2. Upload du package handler
        s3_key = upload_handler_package()
        
        # 3. Récupération du rôle IAM
        role_arn = get_lambda_role_arn()
        
        # 4. Déploiement avec layers
        deploy_lambda_with_layers(s3_key, layer_arns, role_arn)
        
        # 5. Vérification
        verify_deployment()
        
        log("[SUCCES] Déploiement avec layers terminé!")
        log(f"Lambda: {LAMBDA_NAME}")
        log(f"Région: {AWS_REGION}")
        log(f"Layers: {len(layer_arns)} configurés")
        log("Architecture conforme aux règles V4")
        
    except Exception as e:
        log(f"[ERREUR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()