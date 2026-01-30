#!/usr/bin/env python3
"""
Deploy layer vers environnement AWS
Usage: python scripts/deploy/deploy_layer.py --layer-file .build/layers/vectora-core-1.2.3.zip --env dev --layer-name vectora-inbox-vectora-core
"""
import argparse
import boto3
from pathlib import Path

def deploy_layer(layer_file, env, layer_name, dry_run=False):
    """Deploy layer vers AWS"""
    print(f"[DEPLOY] Deploying layer to {env}")
    print(f"   Layer file: {layer_file}")
    print(f"   Layer name: {layer_name}-{env}")
    
    if dry_run:
        print("   Mode: DRY RUN (no changes)")
        return
    
    # AWS clients
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    s3 = session.client('s3')
    lambda_client = session.client('lambda')
    
    # Upload vers S3
    bucket = f'vectora-inbox-lambda-code-{env}'
    key = f'layers/{Path(layer_file).name}'
    
    print(f"[DEPLOY] Uploading to s3://{bucket}/{key}")
    s3.upload_file(layer_file, bucket, key)
    
    # Publier layer
    print(f"[DEPLOY] Publishing layer {layer_name}-{env}")
    
    # Extraire version du nom fichier
    version = Path(layer_file).stem.split('-')[-1]
    description = f"Built from repo - version {version}"
    
    response = lambda_client.publish_layer_version(
        LayerName=f'{layer_name}-{env}',
        Content={'S3Bucket': bucket, 'S3Key': key},
        CompatibleRuntimes=['python3.11', 'python3.12'],
        Description=description
    )
    
    arn = response['LayerVersionArn']
    layer_version = response['Version']
    
    print(f"\n[SUCCESS] Layer deployed successfully!")
    print(f"   ARN: {arn}")
    print(f"   Version: {layer_version}")
    
    return arn

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deploy layer to AWS')
    parser.add_argument('--layer-file', required=True, help='Path to layer ZIP file')
    parser.add_argument('--env', required=True, choices=['dev', 'stage', 'prod'], help='Environment')
    parser.add_argument('--layer-name', required=True, help='Layer name (without env suffix)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    try:
        deploy_layer(args.layer_file, args.env, args.layer_name, args.dry_run)
    except Exception as e:
        print(f"[ERROR] {e}")
        exit(1)
