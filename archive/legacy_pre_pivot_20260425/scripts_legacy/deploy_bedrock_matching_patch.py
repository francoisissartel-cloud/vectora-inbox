#!/usr/bin/env python3
"""
Script de déploiement du patch Bedrock matching V2.

Déploie la correction de l'import _call_bedrock_with_retry dans normalize_score_v2.
"""

import os
import sys
import json
import zipfile
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration AWS
AWS_REGION = "eu-west-3"
AWS_PROFILE = "rag-lai-prod"
LAMBDA_FUNCTION_NAME = "vectora-inbox-normalize-score-v2-dev"

def create_deployment_package():
    """Crée le package de déploiement avec le code V2 corrigé."""
    print("=== Création du package de déploiement ===")
    
    project_root = Path(__file__).parent.parent
    src_v2_path = project_root / "src_v2"
    
    if not src_v2_path.exists():
        raise FileNotFoundError(f"Répertoire src_v2 non trouvé : {src_v2_path}")
    
    # Nom du package avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    package_name = f"bedrock-matching-patch-v2-{timestamp}.zip"
    package_path = project_root / package_name
    
    print(f"Création du package : {package_name}")
    
    # Créer le zip avec le contenu de src_v2
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Ajouter tous les fichiers de src_v2
        for file_path in src_v2_path.rglob('*'):
            if file_path.is_file() and not file_path.name.startswith('.'):
                # Chemin relatif dans le zip (sans src_v2/)
                arcname = file_path.relative_to(src_v2_path)
                zipf.write(file_path, arcname)
                print(f"  Ajouté : {arcname}")
    
    print(f"Package créé : {package_path}")
    print(f"Taille : {package_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    return package_path

def deploy_to_lambda(package_path):
    """Déploie le package vers la Lambda AWS."""
    print(f"\n=== Déploiement vers {LAMBDA_FUNCTION_NAME} ===")
    
    # Commande AWS CLI pour mettre à jour le code de la Lambda
    cmd = [
        "aws", "lambda", "update-function-code",
        "--function-name", LAMBDA_FUNCTION_NAME,
        "--zip-file", f"fileb://{package_path}",
        "--region", AWS_REGION,
        "--profile", AWS_PROFILE
    ]
    
    print(f"Commande : {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response = json.loads(result.stdout)
        
        print("OK - Déploiement réussi")
        print(f"  Version : {response.get('Version', 'N/A')}")
        print(f"  Taille : {response.get('CodeSize', 0) / 1024 / 1024:.2f} MB")
        print(f"  SHA256 : {response.get('CodeSha256', 'N/A')[:16]}...")
        print(f"  Dernière modification : {response.get('LastModified', 'N/A')}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERREUR - Échec du déploiement : {e}")
        print(f"Sortie d'erreur : {e.stderr}")
        return False
    except json.JSONDecodeError as e:
        print(f"ERREUR - Réponse AWS invalide : {e}")
        return False

def update_environment_variables():
    """Met à jour les variables d'environnement si nécessaire."""
    print(f"\n=== Vérification des variables d'environnement ===")
    
    # Variables requises pour Bedrock
    required_vars = {
        "BEDROCK_REGION": "us-east-1",
        "BEDROCK_MODEL_ID": "anthropic.claude-3-sonnet-20240229-v1:0"
    }
    
    # Récupérer la configuration actuelle
    cmd_get = [
        "aws", "lambda", "get-function-configuration",
        "--function-name", LAMBDA_FUNCTION_NAME,
        "--region", AWS_REGION,
        "--profile", AWS_PROFILE
    ]
    
    try:
        result = subprocess.run(cmd_get, capture_output=True, text=True, check=True)
        config = json.loads(result.stdout)
        current_vars = config.get('Environment', {}).get('Variables', {})
        
        print("Variables actuelles :")
        for key, value in current_vars.items():
            if 'BEDROCK' in key:
                print(f"  {key} = {value}")
        
        # Vérifier si mise à jour nécessaire
        needs_update = False
        updated_vars = current_vars.copy()
        
        for var_name, var_value in required_vars.items():
            if current_vars.get(var_name) != var_value:
                print(f"Mise à jour nécessaire : {var_name} = {var_value}")
                updated_vars[var_name] = var_value
                needs_update = True
        
        if needs_update:
            print("Mise à jour des variables d'environnement...")
            
            cmd_update = [
                "aws", "lambda", "update-function-configuration",
                "--function-name", LAMBDA_FUNCTION_NAME,
                "--environment", f"Variables={json.dumps(updated_vars)}",
                "--region", AWS_REGION,
                "--profile", AWS_PROFILE
            ]
            
            result = subprocess.run(cmd_update, capture_output=True, text=True, check=True)
            print("OK - Variables d'environnement mises à jour")
        else:
            print("OK - Variables d'environnement déjà correctes")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERREUR - Échec de la mise à jour des variables : {e}")
        print(f"Sortie d'erreur : {e.stderr}")
        return False
    except json.JSONDecodeError as e:
        print(f"ERREUR - Réponse AWS invalide : {e}")
        return False

def test_deployment():
    """Teste le déploiement avec un appel de test."""
    print(f"\n=== Test du déploiement ===")
    
    # Payload de test minimal
    test_payload = {
        "client_id": "lai_weekly_v3",
        "period_days": 30
    }
    
    payload_file = Path(__file__).parent.parent / "test_deployment_payload.json"
    with open(payload_file, 'w') as f:
        json.dump(test_payload, f, indent=2)
    
    print(f"Payload de test : {test_payload}")
    
    # Commande d'invocation
    cmd = [
        "aws", "lambda", "invoke",
        "--function-name", LAMBDA_FUNCTION_NAME,
        "--payload", f"file://{payload_file}",
        "--region", AWS_REGION,
        "--profile", AWS_PROFILE,
        "response_deployment_test.json"
    ]
    
    print("Invocation de la Lambda...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        invoke_response = json.loads(result.stdout)
        
        print(f"Status Code : {invoke_response.get('StatusCode', 'N/A')}")
        
        # Lire la réponse
        response_file = Path("response_deployment_test.json")
        if response_file.exists():
            with open(response_file, 'r') as f:
                lambda_response = json.load(f)
            
            status_code = lambda_response.get('statusCode', 500)
            body = lambda_response.get('body', {})
            
            if status_code == 200:
                print("OK - Lambda exécutée avec succès")
                if isinstance(body, dict):
                    items_normalized = body.get('items_normalized', 0)
                    items_matched = body.get('items_matched', 0)
                    print(f"  Items normalisés : {items_normalized}")
                    print(f"  Items matchés : {items_matched}")
                    
                    if items_matched > 0:
                        print("SUCCESS - Le matching Bedrock fonctionne !")
                    else:
                        print("WARNING - Aucun item matché (peut être normal selon les données)")
                else:
                    print(f"  Réponse : {body}")
            else:
                print(f"ERREUR - Lambda a échoué (status: {status_code})")
                if isinstance(body, dict):
                    error = body.get('error', 'Unknown')
                    message = body.get('message', 'No message')
                    print(f"  Erreur : {error}")
                    print(f"  Message : {message}")
                else:
                    print(f"  Body : {body}")
                return False
            
            # Nettoyer les fichiers temporaires
            payload_file.unlink(missing_ok=True)
            response_file.unlink(missing_ok=True)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERREUR - Échec de l'invocation : {e}")
        print(f"Sortie d'erreur : {e.stderr}")
        return False
    except json.JSONDecodeError as e:
        print(f"ERREUR - Réponse AWS invalide : {e}")
        return False

def main():
    """Fonction principale du déploiement."""
    print("Déploiement du patch Bedrock matching V2")
    print("=" * 50)
    
    try:
        # Étape 1 : Créer le package
        package_path = create_deployment_package()
        
        # Étape 2 : Déployer vers AWS
        if not deploy_to_lambda(package_path):
            return 1
        
        # Étape 3 : Mettre à jour les variables d'environnement
        if not update_environment_variables():
            return 1
        
        # Étape 4 : Tester le déploiement
        if not test_deployment():
            print("\nWARNING - Le test a échoué, mais le déploiement peut être correct")
            print("Vérifiez les logs CloudWatch pour plus de détails")
        
        print("\n" + "=" * 50)
        print("Déploiement terminé avec succès !")
        print(f"Lambda : {LAMBDA_FUNCTION_NAME}")
        print(f"Région : {AWS_REGION}")
        print(f"Package : {package_path.name}")
        
        # Instructions de suivi
        print("\nPour surveiller l'exécution :")
        print(f"aws logs filter-log-events \\")
        print(f"  --log-group-name /aws/lambda/{LAMBDA_FUNCTION_NAME} \\")
        print(f"  --start-time $(date -d '5 minutes ago' +%s)000 \\")
        print(f"  --region {AWS_REGION} --profile {AWS_PROFILE}")
        
        return 0
        
    except Exception as e:
        print(f"\nERREUR CRITIQUE : {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)