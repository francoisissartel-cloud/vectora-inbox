#!/usr/bin/env python3
"""
Script de déploiement pour la lambda vectora-inbox-normalize-score-v2.

Ce script package et déploie la lambda V2 avec les corrections Bedrock
en respectant les règles d'hygiène V4.
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path

# Configuration AWS (règles d'hygiène V4)
AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"
AWS_ACCOUNT = "786469175371"

# Configuration Lambda
LAMBDA_NAME = "vectora-inbox-normalize-score-v2-dev"
LAMBDA_RUNTIME = "python3.11"
LAMBDA_TIMEOUT = 900  # 15 minutes
LAMBDA_MEMORY = 1024  # 1GB

# Buckets S3 (conventions V4)
CONFIG_BUCKET = "vectora-inbox-config-dev"
DATA_BUCKET = "vectora-inbox-data-dev"
CODE_BUCKET = "vectora-inbox-lambda-code-dev"

# Modèle Bedrock (observé dans le diagnostic)
BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
BEDROCK_REGION = "us-east-1"

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

def check_aws_environment():
    """Vérifie l'environnement AWS selon les règles V4."""
    log("Vérification de l'environnement AWS...")
    
    # Vérifier le profil
    result = run_aws_command("sts get-caller-identity", check=False)
    if result.returncode != 0:
        log(f"[ERREUR] Profil AWS {AWS_PROFILE} non configuré ou invalide")
        sys.exit(1)
    
    identity = json.loads(result.stdout)
    if identity["Account"] != AWS_ACCOUNT:
        log(f"[ERREUR] Mauvais compte AWS: {identity['Account']} (attendu: {AWS_ACCOUNT})")
        sys.exit(1)
    
    log(f"[OK] Profil AWS: {AWS_PROFILE}, Compte: {AWS_ACCOUNT}")
    
    # Vérifier les buckets
    for bucket in [CONFIG_BUCKET, DATA_BUCKET, CODE_BUCKET]:
        result = run_aws_command(f"s3 ls s3://{bucket}/", check=False)
        if result.returncode != 0:
            log(f"[ERREUR] Bucket {bucket} inaccessible")
            sys.exit(1)
    
    log("[OK] Buckets S3 accessibles")

def create_lambda_package():
    """Crée le package Lambda selon les règles d'hygiène V4."""
    log("Création du package Lambda...")
    
    # Répertoire de travail temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir) / "lambda_package"
        package_dir.mkdir()
        
        # Copier le handler
        src_handler = Path("src_v2/lambdas/normalize_score/handler.py")
        if not src_handler.exists():
            log(f"[ERREUR] Handler non trouvé: {src_handler}")
            sys.exit(1)
        
        shutil.copy2(src_handler, package_dir / "handler.py")
        log(f"[OK] Handler copié: {src_handler}")
        
        # Copier vectora_core
        src_core = Path("src_v2/vectora_core")
        if not src_core.exists():
            log(f"[ERREUR] vectora_core non trouvé: {src_core}")
            sys.exit(1)
        
        dest_core = package_dir / "vectora_core"
        shutil.copytree(src_core, dest_core)
        log(f"[OK] vectora_core copié: {src_core}")
        
        # Vérifier la taille (règle V4: < 5MB pour handler)
        package_size = sum(f.stat().st_size for f in package_dir.rglob('*') if f.is_file())
        package_size_mb = package_size / (1024 * 1024)
        
        if package_size_mb > 5:
            log(f"[ATTENTION] Package volumineux: {package_size_mb:.1f}MB (limite: 5MB)")
        else:
            log(f"[OK] Taille du package: {package_size_mb:.1f}MB")
        
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
        
        return f"s3://{CODE_BUCKET}/{s3_key}"

def get_lambda_role_arn():
    """Récupère l'ARN du rôle IAM pour la Lambda."""
    log("Recherche du rôle IAM Lambda...")
    
    # Chercher le rôle existant vectora-inbox
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

def deploy_lambda(package_s3_uri, role_arn):
    """Déploie ou met à jour la Lambda."""
    log(f"Déploiement de la Lambda {LAMBDA_NAME}...")
    
    # Vérifier si la Lambda existe
    result = run_aws_command(f"lambda get-function --function-name {LAMBDA_NAME}", check=False)
    
    if result.returncode == 0:
        # Mise à jour du code
        log("Lambda existante - mise à jour du code...")
        run_aws_command(f"lambda update-function-code --function-name {LAMBDA_NAME} --s3-bucket {CODE_BUCKET.replace('s3://', '')} --s3-key lambda-packages/{LAMBDA_NAME}.zip")
        
        # Mise à jour de la configuration
        log("Mise à jour de la configuration...")
        
        # Créer un fichier temporaire pour les variables d'environnement
        env_vars = {
            "ENV": "dev",
            "PROJECT_NAME": "vectora-inbox",
            "CONFIG_BUCKET": CONFIG_BUCKET,
            "DATA_BUCKET": DATA_BUCKET,
            "BEDROCK_MODEL_ID": BEDROCK_MODEL_ID,
            "BEDROCK_REGION": BEDROCK_REGION,
            "LOG_LEVEL": "INFO"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"Variables": env_vars}, f)
            env_file = f.name
        
        try:
            update_config_command = f"lambda update-function-configuration --function-name {LAMBDA_NAME} --timeout {LAMBDA_TIMEOUT} --memory-size {LAMBDA_MEMORY} --environment file://{env_file}"
            run_aws_command(update_config_command)
        finally:
            os.remove(env_file)
        
    else:
        # Création de la Lambda
        log("Création de la nouvelle Lambda...")
        
        # Créer un fichier temporaire pour les variables d'environnement
        env_vars = {
            "ENV": "dev",
            "PROJECT_NAME": "vectora-inbox",
            "CONFIG_BUCKET": CONFIG_BUCKET,
            "DATA_BUCKET": DATA_BUCKET,
            "BEDROCK_MODEL_ID": BEDROCK_MODEL_ID,
            "BEDROCK_REGION": BEDROCK_REGION,
            "LOG_LEVEL": "INFO"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"Variables": env_vars}, f)
            env_file = f.name
        
        try:
            create_command = f"lambda create-function --function-name {LAMBDA_NAME} --runtime {LAMBDA_RUNTIME} --role {role_arn} --handler handler.lambda_handler --code S3Bucket={CODE_BUCKET.replace('s3://', '')},S3Key=lambda-packages/{LAMBDA_NAME}.zip --timeout {LAMBDA_TIMEOUT} --memory-size {LAMBDA_MEMORY} --environment file://{env_file}"
            run_aws_command(create_command)
        finally:
            os.remove(env_file)
    
    log(f"[OK] Lambda {LAMBDA_NAME} déployée avec succès")

def test_lambda_deployment():
    """Test rapide du déploiement."""
    log("Test du déploiement...")
    
    # Event de test
    test_event = {
        "client_id": "lai_weekly_v3"
    }
    
    # Créer le fichier d'event temporaire
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_event, f)
        event_file = f.name
    
    try:
        # Invoquer la Lambda
        result = run_aws_command(f"lambda invoke --function-name {LAMBDA_NAME} --payload file://{event_file} response.json", check=False)
        
        if result.returncode == 0:
            # Lire la réponse
            if os.path.exists("response.json"):
                with open("response.json", 'r') as f:
                    response = json.load(f)
                
                if response.get("statusCode") == 200:
                    log("[OK] Test de déploiement réussi")
                    log(f"Résultat: {json.dumps(response.get('body', {}), indent=2)}")
                else:
                    log(f"[ATTENTION] Lambda exécutée mais erreur: {response}")
                
                os.remove("response.json")
            else:
                log("[ATTENTION] Pas de fichier de réponse généré")
        else:
            log(f"[ERREUR] Échec de l'invocation: {result.stderr}")
    
    finally:
        # Nettoyer le fichier d'event
        if os.path.exists(event_file):
            os.remove(event_file)

def main():
    """Fonction principale de déploiement."""
    log("=== Déploiement vectora-inbox-normalize-score-v2 ===")
    log(f"Environnement: {AWS_REGION}, Profil: {AWS_PROFILE}")
    
    try:
        # 1. Vérifications préalables
        check_aws_environment()
        
        # 2. Création du package
        package_s3_uri = create_lambda_package()
        
        # 3. Récupération du rôle IAM
        role_arn = get_lambda_role_arn()
        
        # 4. Déploiement
        deploy_lambda(package_s3_uri, role_arn)
        
        # 5. Test
        test_lambda_deployment()
        
        log("[SUCCES] Déploiement terminé avec succès!")
        log(f"Lambda: {LAMBDA_NAME}")
        log(f"Région: {AWS_REGION}")
        log(f"Modèle Bedrock: {BEDROCK_MODEL_ID} ({BEDROCK_REGION})")
        
    except KeyboardInterrupt:
        log("[ERREUR] Déploiement interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        log(f"[ERREUR] Erreur inattendue: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()