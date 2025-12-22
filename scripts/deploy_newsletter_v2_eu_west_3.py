#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de déploiement AWS pour Lambda newsletter-v2 dans eu-west-3
Nom conforme: vectora-inbox-newsletter-v2-dev
"""
import os
import sys
import json
import boto3
import argparse
from botocore.exceptions import ClientError

def get_lambda_role_arn():
    """Récupère l'ARN du rôle Lambda existant"""
    return 'arn:aws:iam::786469175371:role/vectora-inbox-s0-iam-dev-EngineRole-x4yGG8dAutT9'

def get_layer_arn(region):
    """Récupère l'ARN du layer common-deps"""
    return f'arn:aws:lambda:{region}:786469175371:layer:vectora-inbox-common-deps-dev:4'

def create_or_update_lambda(package_path, function_name, region):
    """Crée ou met à jour la Lambda newsletter-v2"""
    
    lambda_client = boto3.client('lambda', region_name=region)
    
    # Configuration Lambda
    config = {
        'FunctionName': function_name,
        'Runtime': 'python3.11',
        'Role': get_lambda_role_arn(),
        'Handler': 'handler.lambda_handler',
        'Timeout': 900,  # 15 minutes
        'MemorySize': 1024,
        'Layers': [get_layer_arn(region)],
        'Environment': {
            'Variables': {
                'CONFIG_BUCKET': 'vectora-inbox-config-dev',
                'DATA_BUCKET': 'vectora-inbox-data-dev',
                'NEWSLETTERS_BUCKET': 'vectora-inbox-newsletters-dev',
                'BEDROCK_MODEL_ID': 'anthropic.claude-3-sonnet-20240229-v1:0',
                'BEDROCK_REGION': 'us-east-1'  # Cross-region pour Bedrock
            }
        }
    }
    
    # Lecture du package
    with open(package_path, 'rb') as f:
        zip_content = f.read()
    
    try:
        # Vérifier si la Lambda existe
        lambda_client.get_function(FunctionName=function_name)
        
        # Mise à jour du code
        print(f"[+] Updating existing Lambda: {function_name}")
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        # Mise à jour de la configuration
        print(f"[+] Updating Lambda configuration...")
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Runtime=config['Runtime'],
            Role=config['Role'],
            Handler=config['Handler'],
            Timeout=config['Timeout'],
            MemorySize=config['MemorySize'],
            Layers=config['Layers'],
            Environment=config['Environment']
        )
        
        print(f"[SUCCESS] Lambda updated: {function_name}")
        return True
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Création de la Lambda
        print(f"[+] Creating new Lambda: {function_name}")
        
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime=config['Runtime'],
            Role=config['Role'],
            Handler=config['Handler'],
            Code={'ZipFile': zip_content},
            Timeout=config['Timeout'],
            MemorySize=config['MemorySize'],
            Layers=config['Layers'],
            Environment=config['Environment']
        )
        
        print(f"[SUCCESS] Lambda created: {function_name}")
        print(f"[+] ARN: {response['FunctionArn']}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Deployment failed: {str(e)}")
        return False

def test_lambda_invocation(function_name, region):
    """Test l'invocation de la Lambda"""
    
    lambda_client = boto3.client('lambda', region_name=region)
    
    payload = {
        'client_id': 'lai_weekly_v4',
        'target_date': '2025-12-21',
        'force_regenerate': False
    }
    
    try:
        print(f"[+] Testing Lambda invocation...")
        print(f"[+] Payload: {json.dumps(payload)}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        print(f"[+] Status Code: {response['StatusCode']}")
        
        if response['StatusCode'] == 200:
            print(f"[SUCCESS] Lambda invocation successful!")
            return True
        else:
            print(f"[ERROR] Lambda returned error")
            return False
            
    except Exception as e:
        print(f"[ERROR] Lambda invocation failed: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    
    parser = argparse.ArgumentParser(description='Déployer Lambda newsletter-v2')
    parser.add_argument('--region', required=True, help='Région AWS')
    parser.add_argument('--function-name', required=True, help='Nom de la fonction Lambda')
    
    args = parser.parse_args()
    
    print("="*60)
    print(f"[AWS DEPLOYMENT - NEWSLETTER V2 - {args.region.upper()}]")
    print("="*60)
    
    # Chemin du package
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    package_path = os.path.join(root_dir, 'output', 'lambda_packages', 'newsletter-v2-20251221-175007.zip')
    
    if not os.path.exists(package_path):
        print(f"[ERROR] Package not found: {package_path}")
        return False
    
    print(f"[+] Package: {package_path}")
    print(f"[+] Size: {os.path.getsize(package_path) / 1024:.2f} KB")
    print(f"[+] Function: {args.function_name}")
    print(f"[+] Region: {args.region}")
    
    # Déploiement Lambda
    print(f"\\n[STEP 1] Deploying Lambda function...")
    if not create_or_update_lambda(package_path, args.function_name, args.region):
        print("[ERROR] Lambda deployment failed")
        return False
    
    # Test invocation
    print(f"\\n[STEP 2] Testing Lambda invocation...")
    if not test_lambda_invocation(args.function_name, args.region):
        print("[WARNING] Lambda test failed, but deployment succeeded")
    
    print("\\n" + "="*60)
    print("[DEPLOYMENT COMPLETED]")
    print("="*60)
    print(f"[+] Lambda: {args.function_name}")
    print(f"[+] Region: {args.region}")
    print(f"[+] Environment: dev")
    print(f"[+] Status: DEPLOYED")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\\n[INFO] Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n[ERROR] Unexpected error: {str(e)}")
        sys.exit(1)