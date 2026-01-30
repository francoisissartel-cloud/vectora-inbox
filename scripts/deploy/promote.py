#!/usr/bin/env python3
"""
Promouvoir version entre environnements
Usage: python scripts/deploy/promote.py --to stage --version 1.2.3
"""
import argparse
import boto3
from pathlib import Path

def get_layer_arn(session, layer_name, env):
    """Récupérer ARN du layer le plus récent"""
    lambda_client = session.client('lambda')
    
    response = lambda_client.list_layer_versions(
        LayerName=f'{layer_name}-{env}',
        MaxItems=1
    )
    
    if not response['LayerVersions']:
        raise ValueError(f"No layer found: {layer_name}-{env}")
    
    return response['LayerVersions'][0]['LayerVersionArn']

def update_lambda_layers(session, function_name, new_layer_arns):
    """Mettre à jour layers d'une Lambda"""
    lambda_client = session.client('lambda')
    
    print(f"   Updating {function_name}")
    
    response = lambda_client.update_function_configuration(
        FunctionName=function_name,
        Layers=new_layer_arns
    )
    
    return response

def promote(from_env, to_env, version, dry_run=False):
    """Promouvoir version entre environnements"""
    print(f"🚀 Promoting from {from_env} to {to_env}")
    print(f"   Version: {version}")
    
    if dry_run:
        print("   Mode: DRY RUN (no changes)")
        return
    
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    s3 = session.client('s3')
    lambda_client = session.client('lambda')
    
    # 1. Copier layers S3
    print("\n📦 Copying layers...")
    source_bucket = f'vectora-inbox-lambda-code-{from_env}'
    target_bucket = f'vectora-inbox-lambda-code-{to_env}'
    
    # Lister layers à copier
    layer_files = [
        f'layers/vectora-core-{version}.zip',
        f'layers/common-deps-{version}.zip'
    ]
    
    for layer_file in layer_files:
        print(f"   Copying {layer_file}")
        copy_source = {'Bucket': source_bucket, 'Key': layer_file}
        s3.copy_object(CopySource=copy_source, Bucket=target_bucket, Key=layer_file)
    
    # 2. Publier layers dans env cible
    print("\n📦 Publishing layers in target env...")
    
    layer_arns = []
    for layer_name in ['vectora-inbox-vectora-core', 'vectora-inbox-common-deps']:
        layer_file = f'layers/{layer_name.split("-")[-1]}-{version}.zip'
        
        response = lambda_client.publish_layer_version(
            LayerName=f'{layer_name}-{to_env}',
            Content={'S3Bucket': target_bucket, 'S3Key': layer_file},
            CompatibleRuntimes=['python3.11', 'python3.12'],
            Description=f'Promoted from {from_env} - version {version}'
        )
        
        layer_arns.append(response['LayerVersionArn'])
        print(f"   Published: {response['LayerVersionArn']}")
    
    # 3. Mettre à jour Lambdas
    print("\n🔄 Updating Lambdas...")
    
    lambdas = [
        f'vectora-inbox-ingest-v2-{to_env}',
        f'vectora-inbox-normalize-score-v2-{to_env}',
        f'vectora-inbox-newsletter-v2-{to_env}'
    ]
    
    for lambda_name in lambdas:
        update_lambda_layers(session, lambda_name, layer_arns)
    
    # 4. Copier canonical
    print("\n📄 Copying canonical...")
    
    # Sync canonical
    source_prefix = 'canonical/'
    
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=source_bucket, Prefix=source_prefix):
        for obj in page.get('Contents', []):
            source_key = obj['Key']
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            s3.copy_object(CopySource=copy_source, Bucket=target_bucket, Key=source_key)
            print(f"   Copied: {source_key}")
    
    print(f"\n✅ Promotion completed successfully!")
    print(f"   {from_env} → {to_env}")
    print(f"   Version: {version}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Promote version between environments')
    parser.add_argument('--from', dest='from_env', default='dev', choices=['dev', 'stage'], help='Source environment')
    parser.add_argument('--to', dest='to_env', required=True, choices=['stage', 'prod'], help='Target environment')
    parser.add_argument('--version', required=True, help='Version to promote')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    try:
        promote(args.from_env, args.to_env, args.version, args.dry_run)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
