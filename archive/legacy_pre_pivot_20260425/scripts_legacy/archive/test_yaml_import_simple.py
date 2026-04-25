#!/usr/bin/env python3
"""
Test simple d'import yaml pour diagnostiquer le problème Lambda
"""

import json
import boto3

def create_simple_test_handler():
    """Crée un handler de test minimal pour vérifier l'import yaml"""
    
    test_handler_code = '''
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Handler de test pour vérifier l'import yaml"""
    try:
        logger.info("Test import yaml...")
        
        # Test 1: Import yaml
        try:
            import yaml
            logger.info("SUCCESS: import yaml réussi")
            yaml_version = getattr(yaml, '__version__', 'unknown')
            logger.info(f"Version PyYAML: {yaml_version}")
        except ImportError as e:
            logger.error(f"FAILED: import yaml échoué: {str(e)}")
            return {
                "statusCode": 500,
                "body": {"error": "ImportError", "message": str(e)}
            }
        
        # Test 2: Test fonctionnel yaml
        try:
            test_data = {"test": "value", "number": 42}
            yaml_str = yaml.dump(test_data)
            parsed_data = yaml.safe_load(yaml_str)
            logger.info("SUCCESS: yaml.dump et yaml.safe_load fonctionnent")
        except Exception as e:
            logger.error(f"FAILED: test fonctionnel yaml échoué: {str(e)}")
            return {
                "statusCode": 500,
                "body": {"error": "YAMLError", "message": str(e)}
            }
        
        # Test 3: Vérifier les paths Python
        import sys
        logger.info(f"Python paths: {sys.path}")
        
        return {
            "statusCode": 200,
            "body": {
                "message": "Tous les tests yaml réussis",
                "yaml_version": yaml_version,
                "python_paths": sys.path
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur générale: {str(e)}")
        return {
            "statusCode": 500,
            "body": {"error": "GeneralError", "message": str(e)}
        }
'''
    
    return test_handler_code

def create_test_lambda():
    """Crée une Lambda de test temporaire pour vérifier PyYAML"""
    
    print("[CREATE] Création Lambda de test yaml...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    iam_client = session.client('iam', region_name='eu-west-3')
    
    # Code du handler de test
    handler_code = create_simple_test_handler()
    
    # Création du ZIP
    import zipfile
    import tempfile
    from pathlib import Path
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Écriture du handler
        handler_path = Path(temp_dir) / "handler.py"
        with open(handler_path, 'w') as f:
            f.write(handler_code)
        
        # Création du ZIP
        zip_path = Path(temp_dir) / "test_lambda.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(handler_path, "handler.py")
        
        # Lecture du ZIP
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
    
    # Récupération du rôle IAM existant
    try:
        role_response = iam_client.get_role(RoleName='vectora-inbox-lambda-execution-role-dev')
        role_arn = role_response['Role']['Arn']
        print(f"[IAM] Utilisation du rôle existant: {role_arn}")
    except Exception as e:
        print(f"[ERROR] Impossible de récupérer le rôle IAM: {str(e)}")
        return None
    
    # Récupération des layers existants de normalize_score_v2
    try:
        config = lambda_client.get_function(FunctionName='vectora-inbox-normalize-score-v2-dev')
        existing_layers = [layer['Arn'] for layer in config['Configuration'].get('Layers', [])]
        print(f"[LAYERS] Réutilisation des layers: {len(existing_layers)} layers")
    except Exception as e:
        print(f"[ERROR] Impossible de récupérer les layers: {str(e)}")
        existing_layers = []
    
    # Création de la Lambda de test
    function_name = 'vectora-inbox-yaml-test-temp'
    
    try:
        # Suppression si existe déjà
        try:
            lambda_client.delete_function(FunctionName=function_name)
            print(f"[CLEANUP] Lambda existante supprimée")
        except:
            pass
        
        # Création
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': zip_content},
            Description='Test temporaire import PyYAML',
            Timeout=30,
            MemorySize=128,
            Layers=existing_layers
        )
        
        print(f"[OK] Lambda de test créée: {response['FunctionArn']}")
        return function_name
        
    except Exception as e:
        print(f"[ERROR] Erreur création Lambda: {str(e)}")
        return None

def test_yaml_import(function_name):
    """Test l'import yaml avec la Lambda de test"""
    
    print(f"[TEST] Test import yaml avec {function_name}...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps({"test": "yaml_import"})
        )
        
        # Lecture de la réponse
        response_payload = json.loads(response['Payload'].read())
        
        print(f"[RESPONSE] Status: {response_payload.get('statusCode')}")
        
        if response.get('FunctionError'):
            print(f"[ERROR] Erreur Lambda: {response['FunctionError']}")
            print(f"[DETAILS] {response_payload}")
            return False
        else:
            print(f"[SUCCESS] Test réussi")
            body = response_payload.get('body', {})
            if isinstance(body, dict):
                yaml_version = body.get('yaml_version', 'unknown')
                print(f"[YAML] Version PyYAML: {yaml_version}")
            return True
            
    except Exception as e:
        print(f"[ERROR] Erreur test: {str(e)}")
        return False

def cleanup_test_lambda(function_name):
    """Supprime la Lambda de test"""
    
    print(f"[CLEANUP] Suppression Lambda de test...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    
    try:
        lambda_client.delete_function(FunctionName=function_name)
        print(f"[OK] Lambda de test supprimée")
    except Exception as e:
        print(f"[WARNING] Erreur suppression: {str(e)}")

def main():
    """Fonction principale de test"""
    
    print("TEST IMPORT YAML - Lambda temporaire")
    print("=" * 50)
    
    # Création Lambda de test
    function_name = create_test_lambda()
    if not function_name:
        print("[ABORT] Impossible de créer la Lambda de test")
        return False
    
    # Test import
    success = test_yaml_import(function_name)
    
    # Nettoyage
    cleanup_test_lambda(function_name)
    
    # Résumé
    print("\n" + "=" * 50)
    if success:
        print("[CONCLUSION] ✅ PyYAML fonctionne - problème ailleurs")
        print("[NEXT] Vérifier les imports dans vectora_core")
    else:
        print("[CONCLUSION] ❌ PyYAML ne fonctionne pas")
        print("[NEXT] Corriger le layer PyYAML")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)