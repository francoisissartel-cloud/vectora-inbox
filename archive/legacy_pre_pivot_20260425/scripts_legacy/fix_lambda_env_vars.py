#!/usr/bin/env python3
"""
Script pour corriger les variables d'environnement de la Lambda normalize_score_v2.
"""

import boto3
from botocore.exceptions import ClientError

def fix_lambda_environment():
    """Corrige les variables d'environnement de la Lambda."""
    
    print("Correction des variables d'environnement Lambda...")
    
    # Configuration AWS
    profile = 'rag-lai-prod'
    region = 'eu-west-3'
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    # Variables d'environnement corrigées
    correct_env_vars = {
        'ENV': 'dev',
        'PROJECT_NAME': 'vectora-inbox',
        'CONFIG_BUCKET': 'vectora-inbox-config-dev',
        'DATA_BUCKET': 'vectora-inbox-data-dev',
        'BEDROCK_MODEL_ID': 'anthropic.claude-3-sonnet-20240229-v1:0',
        'BEDROCK_REGION': 'us-east-1',
        'LOG_LEVEL': 'INFO'
    }
    
    # Créer le client Lambda
    session = boto3.Session(profile_name=profile)
    lambda_client = session.client('lambda', region_name=region)
    
    try:
        # Récupérer la configuration actuelle
        print("Récupération de la configuration actuelle...")
        current_config = lambda_client.get_function_configuration(FunctionName=function_name)
        current_env = current_config.get('Environment', {}).get('Variables', {})
        
        print("Variables actuelles:")
        for key, value in current_env.items():
            print(f"  {key}: {value}")
        
        # Mettre à jour les variables d'environnement
        print("\nMise à jour des variables d'environnement...")
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                'Variables': correct_env_vars
            }
        )
        
        print("Variables mises à jour:")
        updated_env = response.get('Environment', {}).get('Variables', {})
        for key, value in updated_env.items():
            print(f"  {key}: {value}")
        
        # Attendre que la mise à jour soit terminée
        print("\nAttente de la mise à jour...")
        waiter = lambda_client.get_waiter('function_updated')
        waiter.wait(FunctionName=function_name)
        
        print("OK Variables d'environnement mises à jour avec succès")
        return True
        
    except ClientError as e:
        print(f"ERREUR AWS: {e}")
        return False
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

def test_lambda_with_correct_env():
    """Test la Lambda avec les variables d'environnement corrigées."""
    
    import json
    
    print("\nTest avec les variables corrigées...")
    
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
        "period_days": 1
    }
    
    try:
        print("Invocation de test...")
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        # Lire la réponse
        response_payload = json.loads(response['Payload'].read())
        status_code = response_payload.get('statusCode', 0)
        
        print(f"Status Code: {status_code}")
        
        if status_code == 200:
            body = response_payload.get('body', {})
            print("OK Test réussi")
            print(f"  Status: {body.get('status', 'unknown')}")
            
            # Vérifier les statistiques
            stats = body.get('statistics', {})
            if stats:
                print(f"  Items normalisés: {stats.get('items_normalized', 0)}")
                print(f"  Items matchés: {stats.get('items_matched', 0)}")
                print(f"  Items scorés: {stats.get('items_scored', 0)}")
            
            return True
        else:
            print(f"ERREUR Test échoué - Status: {status_code}")
            error_body = response_payload.get('body', {})
            print(f"  Erreur: {error_body.get('error', 'unknown')}")
            print(f"  Message: {error_body.get('message', 'unknown')}")
            return False
            
    except Exception as e:
        print(f"ERREUR: {e}")
        return False

if __name__ == "__main__":
    import json
    
    print("Correction des variables d'environnement Lambda normalize_score_v2")
    print("=" * 70)
    
    success = True
    
    # Étape 1: Corriger les variables d'environnement
    success &= fix_lambda_environment()
    
    # Étape 2: Tester avec les variables corrigées
    if success:
        success &= test_lambda_with_correct_env()
    
    print("\n" + "=" * 70)
    if success:
        print("RESULTAT: CORRECTION REUSSIE")
        print("OK Variables d'environnement corrigées")
        print("OK Lambda fonctionne avec la configuration alignée")
        print("OK Normalisation et matching utilisent maintenant la même config Bedrock")
    else:
        print("ERREUR RESULTAT: CORRECTION ECHOUEE")
        print("Vérifications supplémentaires nécessaires")
    
    exit(0 if success else 1)