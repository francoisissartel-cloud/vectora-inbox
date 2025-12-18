#!/usr/bin/env python3
"""
Script de déploiement pour l'alignement de configuration Bedrock V2.

Déploie la Lambda normalize_score_v2 avec la configuration Bedrock alignée
entre normalisation et matching.
"""

import os
import sys
import json
import zipfile
import tempfile
import shutil
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

def create_lambda_package():
    """Crée le package Lambda avec le code aligné."""
    
    print("Creation du package Lambda...")
    
    # Répertoire source
    src_dir = os.path.join(os.path.dirname(__file__), '..', 'src_v2')
    
    # Créer un répertoire temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = os.path.join(temp_dir, 'package')
        os.makedirs(package_dir)
        
        # Copier le handler
        handler_src = os.path.join(src_dir, 'lambdas', 'normalize_score', 'handler.py')
        handler_dst = os.path.join(package_dir, 'handler.py')
        shutil.copy2(handler_src, handler_dst)
        
        # Copier vectora_core
        vectora_core_src = os.path.join(src_dir, 'vectora_core')
        vectora_core_dst = os.path.join(package_dir, 'vectora_core')
        shutil.copytree(vectora_core_src, vectora_core_dst)
        
        # Créer le fichier ZIP
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        zip_filename = f"bedrock-alignment-patch-v2-{timestamp}.zip"
        zip_path = os.path.join(os.path.dirname(__file__), zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(package_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, package_dir)
                    zipf.write(file_path, arc_name)
        
        # Vérifier la taille
        zip_size = os.path.getsize(zip_path)
        zip_size_mb = zip_size / (1024 * 1024)
        
        print(f"Package créé: {zip_filename}")
        print(f"Taille: {zip_size_mb:.2f} MB")
        
        if zip_size_mb > 50:
            print("ATTENTION: Package > 50MB, pourrait poser problème")
        
        return zip_path

def deploy_lambda(zip_path):
    """Déploie la Lambda avec le nouveau package."""
    
    print("Déploiement de la Lambda...")
    
    # Configuration AWS
    profile = 'rag-lai-prod'
    region = 'eu-west-3'
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    # Créer le client Lambda
    session = boto3.Session(profile_name=profile)
    lambda_client = session.client('lambda', region_name=region)
    
    try:
        # Lire le package
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        # Mettre à jour le code de la fonction
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"Déploiement réussi:")
        print(f"  Function: {response['FunctionName']}")
        print(f"  Version: {response['Version']}")
        print(f"  LastModified: {response['LastModified']}")
        print(f"  CodeSize: {response['CodeSize']} bytes")
        
        # Attendre que la fonction soit mise à jour
        print("Attente de la mise à jour...")
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=function_name)
        
        # Vérifier le statut final
        function_info = lambda_client.get_function(FunctionName=function_name)
        config = function_info['Configuration']
        
        print(f"Statut final:")
        print(f"  State: {config['State']}")
        print(f"  LastUpdateStatus: {config['LastUpdateStatus']}")
        
        if config['State'] == 'Active' and config['LastUpdateStatus'] == 'Successful':
            print("OK Déploiement terminé avec succès")
            return True
        else:
            print(f"ATTENTION: Statut inattendu - State: {config['State']}, LastUpdateStatus: {config['LastUpdateStatus']}")
            return False
            
    except ClientError as e:
        print(f"ERREUR AWS: {e}")
        return False
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

def verify_environment_variables():
    """Vérifie les variables d'environnement de la Lambda."""
    
    print("Vérification des variables d'environnement...")
    
    # Configuration AWS
    profile = 'rag-lai-prod'
    region = 'eu-west-3'
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    # Créer le client Lambda
    session = boto3.Session(profile_name=profile)
    lambda_client = session.client('lambda', region_name=region)
    
    try:
        # Récupérer la configuration
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        env_vars = response.get('Environment', {}).get('Variables', {})
        
        # Variables critiques pour Bedrock
        critical_vars = ['BEDROCK_MODEL_ID', 'BEDROCK_REGION', 'CONFIG_BUCKET', 'DATA_BUCKET']
        
        print("Variables d'environnement actuelles:")
        for var in critical_vars:
            value = env_vars.get(var, 'NON DEFINIE')
            print(f"  {var}: {value}")
        
        # Vérifications
        missing_vars = [var for var in critical_vars if var not in env_vars]
        if missing_vars:
            print(f"ATTENTION: Variables manquantes: {missing_vars}")
            return False
        
        # Vérifier le modèle Bedrock
        bedrock_model = env_vars.get('BEDROCK_MODEL_ID', '')
        if 'anthropic.claude' not in bedrock_model:
            print(f"ATTENTION: Modèle Bedrock suspect: {bedrock_model}")
            return False
        
        print("OK Variables d'environnement validées")
        return True
        
    except ClientError as e:
        print(f"ERREUR AWS: {e}")
        return False
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

def test_lambda_invocation():
    """Test rapide d'invocation de la Lambda."""
    
    print("Test d'invocation de la Lambda...")
    
    # Configuration AWS
    profile = 'rag-lai-prod'
    region = 'eu-west-3'
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    # Créer le client Lambda
    session = boto3.Session(profile_name=profile)
    lambda_client = session.client('lambda', region_name=region)
    
    # Payload de test minimal
    test_payload = {
        "client_id": "lai_weekly_v3",
        "period_days": 1  # Test minimal avec 1 jour
    }
    
    try:
        print("Invocation de test en cours...")
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        # Lire la réponse
        response_payload = json.loads(response['Payload'].read())
        status_code = response_payload.get('statusCode', 0)
        
        if status_code == 200:
            body = response_payload.get('body', {})
            print("OK Test d'invocation réussi")
            print(f"  Status: {body.get('status', 'unknown')}")
            
            # Vérifier les statistiques si disponibles
            stats = body.get('statistics', {})
            if stats:
                print(f"  Items normalisés: {stats.get('items_normalized', 0)}")
                print(f"  Items matchés: {stats.get('items_matched', 0)}")
            
            return True
        else:
            print(f"ERREUR Test d'invocation échoué - Status: {status_code}")
            error_body = response_payload.get('body', {})
            print(f"  Erreur: {error_body.get('error', 'unknown')}")
            print(f"  Message: {error_body.get('message', 'unknown')}")
            return False
            
    except ClientError as e:
        print(f"ERREUR AWS: {e}")
        return False
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

def main():
    """Fonction principale de déploiement."""
    
    print("Déploiement de l'alignement configuration Bedrock V2")
    print("=" * 60)
    
    success = True
    
    # Étape 1: Créer le package
    print("\n1. Création du package Lambda...")
    try:
        zip_path = create_lambda_package()
    except Exception as e:
        print(f"ERREUR Création package: {e}")
        return False
    
    # Étape 2: Déployer
    print("\n2. Déploiement...")
    success &= deploy_lambda(zip_path)
    
    # Étape 3: Vérifier les variables d'environnement
    print("\n3. Vérification configuration...")
    success &= verify_environment_variables()
    
    # Étape 4: Test d'invocation
    print("\n4. Test d'invocation...")
    success &= test_lambda_invocation()
    
    # Nettoyage
    try:
        os.remove(zip_path)
        print(f"Package temporaire supprimé: {os.path.basename(zip_path)}")
    except:
        pass
    
    # Résultat final
    print("\n" + "=" * 60)
    if success:
        print("RESULTAT: DEPLOIEMENT REUSSI")
        print("OK Lambda normalize_score_v2 mise à jour avec configuration Bedrock alignée")
        print("OK Normalisation et matching utilisent maintenant la même config")
        print("OK Prêt pour les tests en production")
    else:
        print("ERREUR RESULTAT: DEPLOIEMENT ECHOUE")
        print("Vérifications nécessaires avant utilisation en production")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)