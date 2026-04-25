#!/usr/bin/env python3
"""
Script de redéploiement du Lambda Layer vectora-core avec le code refactoré.
Phase 6 : Déployer le code matching configuration-driven.
"""

import os
import sys
import shutil
import zipfile
import tempfile
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Configuration AWS
AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"
LAYER_NAME = "vectora-inbox-vectora-core-dev"

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_aws_command(command, check=True):
    full_command = f"aws {command} --profile {AWS_PROFILE} --region {AWS_REGION}"
    log(f"Exécution: {full_command}")
    
    result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        log(f"[ERREUR] {result.stderr}")
        sys.exit(1)
    
    return result

def validate_refactored_code():
    """Valide que le code refactoré est présent et correct."""
    log("Validation du code refactoré...")
    
    # Vérifier que src/vectora_core existe
    src_core = Path("src/vectora_core")
    if not src_core.exists():
        log(f"[ERREUR] Code refactoré non trouvé: {src_core}")
        return False
    
    # Vérifier les modules critiques
    critical_files = [
        "src/vectora_core/matching/bedrock_matcher.py",
        "src/vectora_core/config/loader.py",
        "src/vectora_core/config/resolver.py",
        "src/vectora_core/normalization/normalizer.py"
    ]
    
    for file_path in critical_files:
        if not Path(file_path).exists():
            log(f"[ERREUR] Fichier critique manquant: {file_path}")
            return False
    
    # Vérifier que bedrock_matcher.py contient le code configuration-driven
    matcher_content = Path("src/vectora_core/matching/bedrock_matcher.py").read_text()
    if "match_watch_domains_with_bedrock" not in matcher_content:
        log("[ERREUR] bedrock_matcher.py ne contient pas la fonction refactorée")
        return False
    
    if "canonical_scopes" not in matcher_content:
        log("[ERREUR] bedrock_matcher.py ne supporte pas canonical_scopes")
        return False
    
    log("[OK] Code refactoré validé")
    return True

def create_vectora_core_layer():
    """Crée le layer vectora-core avec le code refactoré."""
    log("Création du layer vectora-core avec code refactoré...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        layer_dir = Path(temp_dir) / "python"
        layer_dir.mkdir()
        
        # Copier vectora_core refactoré depuis src/
        src_core = Path("src/vectora_core")
        dest_core = layer_dir / "vectora_core"
        shutil.copytree(src_core, dest_core)
        log(f"[OK] vectora_core refactoré copié: {src_core} -> {dest_core}")
        
        # Vérifier la structure copiée
        copied_files = list(dest_core.rglob("*.py"))
        log(f"[OK] {len(copied_files)} fichiers Python copiés")
        
        # Vérifier la taille
        layer_size = sum(f.stat().st_size for f in layer_dir.rglob('*') if f.is_file())
        layer_size_mb = layer_size / (1024 * 1024)
        log(f"[OK] Taille du layer: {layer_size_mb:.1f}MB")
        
        if layer_size_mb > 50:
            log(f"[ERREUR] Layer trop volumineux: {layer_size_mb:.1f}MB (limite: 50MB)")
            sys.exit(1)
        
        # Créer le ZIP avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        zip_filename = f"vectora-core-refactored-{timestamp}.zip"
        zip_path = Path(temp_dir) / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in layer_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(Path(temp_dir))
                    zipf.write(file_path, arcname)
        
        zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
        log(f"[OK] Layer ZIP créé: {zip_filename} ({zip_size_mb:.1f}MB)")
        
        # Sauvegarder une copie locale pour debug
        local_zip = Path(zip_filename)
        shutil.copy2(zip_path, local_zip)
        log(f"[OK] Copie locale sauvegardée: {local_zip}")
        
        # Publier le layer
        publish_command = f"lambda publish-layer-version --layer-name {LAYER_NAME} --zip-file fileb://{zip_path} --compatible-runtimes python3.11 python3.12"
        result = run_aws_command(publish_command)
        
        layer_info = json.loads(result.stdout)
        layer_arn = layer_info["LayerArn"]
        layer_version_arn = layer_info["LayerVersionArn"]
        layer_version = layer_info["Version"]
        
        log(f"[OK] Layer publié: {layer_arn}")
        log(f"[OK] Version ARN: {layer_version_arn}")
        log(f"[OK] Version: {layer_version}")
        
        return {
            "layer_arn": layer_arn,
            "layer_version_arn": layer_version_arn,
            "version": layer_version,
            "zip_filename": zip_filename
        }

def update_lambda_layer(layer_info):
    """Met à jour la Lambda normalize-score-v2 avec le nouveau layer."""
    log("Mise à jour de la Lambda avec le nouveau layer...")
    
    lambda_name = "vectora-inbox-normalize-score-v2-dev"
    
    # Obtenir la configuration actuelle
    get_config_command = f"lambda get-function-configuration --function-name {lambda_name}"
    result = run_aws_command(get_config_command)
    current_config = json.loads(result.stdout)
    
    # Préparer les nouveaux layers
    current_layers = current_config.get("Layers", [])
    new_layers = []
    
    # Remplacer le layer vectora-core par la nouvelle version
    for layer in current_layers:
        layer_arn = layer["Arn"]
        if "vectora-core" in layer_arn:
            # Remplacer par la nouvelle version
            new_layers.append(layer_info["layer_version_arn"])
            log(f"[OK] Layer vectora-core remplacé: {layer_arn} -> {layer_info['layer_version_arn']}")
        else:
            # Garder les autres layers
            new_layers.append(layer_arn)
            log(f"[OK] Layer conservé: {layer_arn}")
    
    # Mettre à jour la configuration
    if new_layers:
        layers_str = " ".join(new_layers)
        update_command = f"lambda update-function-configuration --function-name {lambda_name} --layers {layers_str}"
        result = run_aws_command(update_command)
        
        updated_config = json.loads(result.stdout)
        log(f"[OK] Lambda mise à jour avec {len(new_layers)} layers")
        
        return updated_config
    else:
        log("[ERREUR] Aucun layer à mettre à jour")
        return None

def verify_deployment():
    """Vérifie que le déploiement s'est bien passé."""
    log("Vérification du déploiement...")
    
    lambda_name = "vectora-inbox-normalize-score-v2-dev"
    
    # Vérifier la configuration Lambda
    get_config_command = f"lambda get-function-configuration --function-name {lambda_name}"
    result = run_aws_command(get_config_command)
    config = json.loads(result.stdout)
    
    layers = config.get("Layers", [])
    vectora_core_found = False
    
    for layer in layers:
        if "vectora-core" in layer["Arn"]:
            vectora_core_found = True
            log(f"[OK] Layer vectora-core actif: {layer['Arn']}")
    
    if not vectora_core_found:
        log("[ERREUR] Layer vectora-core non trouvé dans la Lambda")
        return False
    
    log(f"[OK] Lambda {lambda_name} configurée avec {len(layers)} layers")
    return True

def main():
    log("=== Redéploiement Layer vectora-core Refactoré ===")
    log("Phase 6 : Activation du matching configuration-driven")
    
    try:
        # Étape 1 : Valider le code refactoré
        if not validate_refactored_code():
            log("[ERREUR] Validation du code refactoré échouée")
            sys.exit(1)
        
        # Étape 2 : Créer le nouveau layer
        layer_info = create_vectora_core_layer()
        
        # Étape 3 : Mettre à jour la Lambda
        updated_config = update_lambda_layer(layer_info)
        if not updated_config:
            log("[ERREUR] Mise à jour de la Lambda échouée")
            sys.exit(1)
        
        # Étape 4 : Vérifier le déploiement
        if not verify_deployment():
            log("[ERREUR] Vérification du déploiement échouée")
            sys.exit(1)
        
        # Étape 5 : Sauvegarder les informations
        deployment_info = {
            "timestamp": datetime.now().isoformat(),
            "layer_info": layer_info,
            "lambda_name": "vectora-inbox-normalize-score-v2-dev",
            "status": "deployed"
        }
        
        with open("vectora_core_deployment_info.json", "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        log("[SUCCÈS] Redéploiement vectora-core terminé avec succès")
        log(f"[INFO] Layer version: {layer_info['version']}")
        log(f"[INFO] ZIP sauvegardé: {layer_info['zip_filename']}")
        log("")
        log("🎯 PROCHAINE ÉTAPE:")
        log("   Tester la Lambda avec le script d'invocation:")
        log("   python scripts/invoke_normalize_score_v2_lambda.py")
        log("")
        log("✅ RÉSULTAT ATTENDU:")
        log("   items_matched > 0 (configuration matching activée)")
        
    except Exception as e:
        log(f"[ERREUR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()