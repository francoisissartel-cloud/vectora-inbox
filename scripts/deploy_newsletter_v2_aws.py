#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de déploiement AWS pour Lambda newsletter-v2
Environnement: dev
"""
import os
import sys
import json
import boto3
from botocore.exceptions import ClientError

def get_lambda_role_arn():
    """Récupère l'ARN du rôle Lambda existant"""
    # Utiliser le rôle Engine existant de vectora-inbox
    return 'arn:aws:iam::786469175371:role/vectora-inbox-s0-iam-dev-EngineRole-x4yGG8dAutT9'

def create_or_update_lambda(package_path):
    """Crée ou met à jour la Lambda newsletter-v2"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    function_name = 'vectora-inbox-newsletter-v2'
    
    # Configuration Lambda
    config = {
        'FunctionName': function_name,
        'Runtime': 'python3.11',
        'Role': get_lambda_role_arn(),
        'Handler': 'handler.lambda_handler',
        'Timeout': 900,  # 15 minutes
        'MemorySize': 1024,
        'Environment': {
            'Variables': {
                'CONFIG_BUCKET': 'vectora-inbox-config-dev',
                'DATA_BUCKET': 'vectora-inbox-data-dev',
                'NEWSLETTERS_BUCKET': 'vectora-inbox-newsletters-dev',
                'BEDROCK_MODEL_ID': 'anthropic.claude-3-sonnet-20240229-v1:0',
                'BEDROCK_REGION': 'us-east-1'
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
            Environment=config['Environment']
        )
        
        print(f"[SUCCESS] Lambda created: {function_name}")
        print(f"[+] ARN: {response['FunctionArn']}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Deployment failed: {str(e)}")
        return False

def upload_config_to_s3():
    """Upload la configuration client vers S3"""
    
    s3 = boto3.client('s3')
    bucket = 'vectora-inbox-config-dev'
    key = 'clients/lai_weekly_v4.yaml'
    local_file = 'client-config-examples/lai_weekly_v4.yaml'
    
    try:
        print(f"[+] Uploading config to s3://{bucket}/{key}")
        s3.upload_file(local_file, bucket, key)
        print(f"[SUCCESS] Config uploaded successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Config upload failed: {str(e)}")
        return False

def upload_prompts_to_s3():
    """Upload les prompts vers S3"""
    
    s3 = boto3.client('s3')
    bucket = 'vectora-inbox-config-dev'
    key = 'canonical/prompts/global_prompts.yaml'
    local_file = 'canonical/prompts/global_prompts.yaml'
    
    try:
        print(f"[+] Uploading prompts to s3://{bucket}/{key}")
        s3.upload_file(local_file, bucket, key)
        print(f"[SUCCESS] Prompts uploaded successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Prompts upload failed: {str(e)}")
        return False

def test_lambda_invocation():
    """Test l'invocation de la Lambda"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    function_name = 'vectora-inbox-newsletter-v2'
    
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
        print(f"[+] Result: {json.dumps(result, indent=2)}")
        
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
    
    print("="*60)
    print("[AWS DEPLOYMENT - NEWSLETTER V2]")
    print("="*60)
    
    # Chemin du package
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    package_path = os.path.join(root_dir, 'output', 'lambda_packages', 'newsletter-v2-20251221-163704.zip')
    
    if not os.path.exists(package_path):
        print(f"[ERROR] Package not found: {package_path}")
        return False
    
    print(f"[+] Package: {package_path}")
    print(f"[+] Size: {os.path.getsize(package_path) / 1024:.2f} KB")
    
    # Étape 1: Upload config S3
    print("\n[STEP 1] Uploading configuration to S3...")
    if not upload_config_to_s3():
        print("[WARNING] Config upload failed, continuing anyway...")
    
    # Étape 2: Upload prompts S3
    print("\n[STEP 2] Uploading prompts to S3...")
    if not upload_prompts_to_s3():
        print("[WARNING] Prompts upload failed, continuing anyway...")
    
    # Étape 3: Déploiement Lambda
    print("\n[STEP 3] Deploying Lambda function...")
    if not create_or_update_lambda(package_path):
        print("[ERROR] Lambda deployment failed")
        return False
    
    # Étape 4: Test invocation
    print("\n[STEP 4] Testing Lambda invocation...")
    if not test_lambda_invocation():
        print("[WARNING] Lambda test failed, but deployment succeeded")
    
    print("\n" + "="*60)
    print("[DEPLOYMENT COMPLETED]")
    print("="*60)
    print("[+] Lambda: vectora-inbox-newsletter-v2")
    print("[+] Region: us-east-1")
    print("[+] Environment: dev")
    print("[+] Status: DEPLOYED")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {str(e)}")
        sys.exit(1)