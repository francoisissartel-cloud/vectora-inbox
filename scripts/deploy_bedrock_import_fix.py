#!/usr/bin/env python3
"""
Déploiement de la correction d'import Bedrock V2.
Package et déploie vectora-inbox-normalize-score-v2-dev avec la correction.
"""

import os
import sys
import json
import zipfile
import tempfile
import shutil
from datetime import datetime
import subprocess

def create_lambda_package():
    """Crée le package Lambda avec la correction d'import."""
    print("=== Création du package Lambda ===")
    
    # Timestamp pour le nom du fichier
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    package_name = f"bedrock-import-fix-v2-{timestamp}.zip"
    
    # Créer un répertoire temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Répertoire temporaire: {temp_dir}")
        
        # Copier le handler
        handler_src = os.path.join("src_v2", "lambdas", "normalize_score", "handler.py")
        handler_dst = os.path.join(temp_dir, "handler.py")
        shutil.copy2(handler_src, handler_dst)
        print(f"Handler copié: {handler_src} -> handler.py")
        
        # Copier vectora_core
        vectora_core_src = os.path.join("src_v2", "vectora_core")
        vectora_core_dst = os.path.join(temp_dir, "vectora_core")
        shutil.copytree(vectora_core_src, vectora_core_dst)
        print(f"vectora_core copié: {vectora_core_src} -> vectora_core/")
        
        # Créer le zip
        with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arc_name)
        
        # Vérifier la taille
        size_mb = os.path.getsize(package_name) / (1024 * 1024)
        print(f"Package créé: {package_name} ({size_mb:.2f} MB)")
        
        if size_mb > 50:
            print(f"ATTENTION: Package trop volumineux ({size_mb:.2f} MB > 50 MB)")
            return None
        
        return package_name

def deploy_lambda(package_name):
    """Déploie le package sur AWS Lambda."""
    print("\n=== Déploiement AWS Lambda ===")
    
    function_name = "vectora-inbox-normalize-score-v2-dev"
    region = "eu-west-3"
    profile = "rag-lai-prod"
    
    try:
        # Mettre à jour le code de la fonction
        cmd = [
            "aws", "lambda", "update-function-code",
            "--function-name", function_name,
            "--zip-file", f"fileb://{package_name}",
            "--region", region,
            "--profile", profile
        ]
        
        print(f"Commande: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        response = json.loads(result.stdout)
        print(f"Déploiement réussi:")
        print(f"  Function: {response.get('FunctionName')}")
        print(f"  Version: {response.get('Version')}")
        print(f"  State: {response.get('State')}")
        print(f"  CodeSize: {response.get('CodeSize')} bytes")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERREUR lors du déploiement: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except json.JSONDecodeError as e:
        print(f"ERREUR parsing réponse AWS: {e}")
        return False

def verify_deployment():
    """Vérifie que le déploiement est réussi."""
    print("\n=== Vérification du déploiement ===")
    
    function_name = "vectora-inbox-normalize-score-v2-dev"
    region = "eu-west-3"
    profile = "rag-lai-prod"
    
    try:
        cmd = [
            "aws", "lambda", "get-function",
            "--function-name", function_name,
            "--region", region,
            "--profile", profile
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        response = json.loads(result.stdout)
        
        config = response.get('Configuration', {})
        print(f"Status de la Lambda:")
        print(f"  State: {config.get('State')}")
        print(f"  LastUpdateStatus: {config.get('LastUpdateStatus')}")
        print(f"  Runtime: {config.get('Runtime')}")
        print(f"  CodeSize: {config.get('CodeSize')} bytes")
        
        # Vérifier les variables d'environnement critiques
        env_vars = config.get('Environment', {}).get('Variables', {})
        critical_vars = ['BEDROCK_MODEL_ID', 'BEDROCK_REGION', 'CONFIG_BUCKET', 'DATA_BUCKET']
        
        print(f"Variables d'environnement critiques:")
        for var in critical_vars:
            value = env_vars.get(var, 'NON DEFINIE')
            print(f"  {var}: {value}")
        
        # Vérifier que la Lambda est active
        if config.get('State') == 'Active' and config.get('LastUpdateStatus') == 'Successful':
            print("OK Lambda active et mise à jour réussie")
            return True
        else:
            print(f"ATTENTION: Lambda pas complètement active")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"ERREUR lors de la vérification: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"ERREUR parsing réponse AWS: {e}")
        return False

def main():
    """Déploiement principal de la correction d'import."""
    print("Déploiement correction import Bedrock V2")
    print("=" * 50)
    
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists("src_v2"):
        print("ERREUR: Répertoire src_v2 non trouvé")
        print("Exécuter depuis la racine du projet vectora-inbox")
        return False
    
    success = True
    
    # Étape 1: Créer le package
    package_name = create_lambda_package()
    if not package_name:
        print("ERREUR: Échec création du package")
        return False
    
    try:
        # Étape 2: Déployer
        if not deploy_lambda(package_name):
            success = False
        
        # Étape 3: Vérifier
        if success and not verify_deployment():
            success = False
        
        print("\n" + "=" * 50)
        if success:
            print("DEPLOIEMENT REUSSI")
            print("OK Correction d'import déployée")
            print("OK Lambda active et fonctionnelle")
            print(f"Package: {package_name}")
        else:
            print("ECHEC DU DEPLOIEMENT")
            print("Vérifier les logs AWS et les permissions")
        
        return success
        
    finally:
        # Nettoyer le package temporaire
        if os.path.exists(package_name):
            os.remove(package_name)
            print(f"Package temporaire supprimé: {package_name}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)