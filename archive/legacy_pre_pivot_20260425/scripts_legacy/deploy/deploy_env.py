#!/usr/bin/env python3
"""
Deploy complet vers environnement
Usage: python scripts/deploy/deploy_env.py --env dev [--dry-run]
"""
import argparse
import subprocess
import sys
import json
import boto3
from pathlib import Path

def get_version(artifact):
    """Lire version depuis fichier VERSION"""
    with open('VERSION') as f:
        for line in f:
            if line.startswith(f'{artifact}_VERSION='):
                return line.split('=')[1].strip()
    raise ValueError(f"{artifact}_VERSION not found in VERSION file")

def get_latest_layer_version(layer_name, env):
    """Récupère la dernière version d'un layer"""
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    lambda_client = session.client('lambda')
    
    try:
        response = lambda_client.list_layer_versions(
            LayerName=f'{layer_name}-{env}',
            MaxItems=1
        )
        if response['LayerVersions']:
            return response['LayerVersions'][0]['LayerVersionArn']
    except Exception as e:
        print(f"[WARNING] Could not get layer version for {layer_name}: {e}")
    return None

def update_lambda_layers(lambda_name, layer_arns, dry_run=False):
    """Met à jour les layers d'une Lambda"""
    print(f"   Updating {lambda_name}...")
    
    if dry_run:
        print(f"      [DRY-RUN] Would update with {len(layer_arns)} layers")
        return
    
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    lambda_client = session.client('lambda')
    
    try:
        lambda_client.update_function_configuration(
            FunctionName=lambda_name,
            Layers=layer_arns
        )
        print(f"      [OK] Layers updated")
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"      [SKIP] Lambda not found")
    except Exception as e:
        print(f"      [ERROR] Failed: {e}")
        raise

def deploy_env(env, dry_run=False):
    """Deploy vers environnement"""
    print(f"[DEPLOY] Deploying to {env} environment")
    
    if dry_run:
        print("   Mode: DRY RUN (no changes)")
    
    # Récupérer versions
    vectora_core_version = get_version('VECTORA_CORE')
    common_deps_version = get_version('COMMON_DEPS')
    
    print(f"\n[INFO] Versions:")
    print(f"   vectora-core: {vectora_core_version}")
    print(f"   common-deps: {common_deps_version}")
    
    # Deploy vectora-core layer
    print(f"\n{'='*60}")
    print("Deploying vectora-core layer...")
    print('='*60)
    
    vectora_core_file = f'.build/layers/vectora-core-{vectora_core_version}.zip'
    if not Path(vectora_core_file).exists():
        raise FileNotFoundError(f"Layer file not found: {vectora_core_file}. Run 'python scripts/build/build_all.py' first.")
    
    cmd = [
        sys.executable, 'scripts/deploy/deploy_layer.py',
        '--layer-file', vectora_core_file,
        '--env', env,
        '--layer-name', 'vectora-inbox-vectora-core'
    ]
    if dry_run:
        cmd.append('--dry-run')
    
    subprocess.run(cmd, check=True)
    
    # Deploy common-deps layer
    print(f"\n{'='*60}")
    print("Deploying common-deps layer...")
    print('='*60)
    
    common_deps_file = f'.build/layers/common-deps-{common_deps_version}.zip'
    if not Path(common_deps_file).exists():
        raise FileNotFoundError(f"Layer file not found: {common_deps_file}. Run 'python scripts/build/build_all.py' first.")
    
    cmd = [
        sys.executable, 'scripts/deploy/deploy_layer.py',
        '--layer-file', common_deps_file,
        '--env', env,
        '--layer-name', 'vectora-inbox-common-deps'
    ]
    if dry_run:
        cmd.append('--dry-run')
    
    subprocess.run(cmd, check=True)
    
    # Update Lambda layers
    print(f"\n{'='*60}")
    print("Updating Lambda layers...")
    print('='*60)
    
    if not dry_run:
        # Récupérer ARNs des layers publiés
        vectora_core_arn = get_latest_layer_version('vectora-inbox-vectora-core', env)
        common_deps_arn = get_latest_layer_version('vectora-inbox-common-deps', env)
        
        if vectora_core_arn and common_deps_arn:
            layer_arns = [vectora_core_arn, common_deps_arn]
            print(f"   Layer ARNs:")
            print(f"      vectora-core: {vectora_core_arn}")
            print(f"      common-deps: {common_deps_arn}")
            
            # Mettre à jour les 3 Lambdas
            lambdas = [
                f'vectora-inbox-ingest-v2-{env}',
                f'vectora-inbox-normalize-score-v2-{env}',
                f'vectora-inbox-newsletter-v2-{env}'
            ]
            
            for lambda_name in lambdas:
                update_lambda_layers(lambda_name, layer_arns, dry_run)
        else:
            print("   [WARNING] Could not retrieve layer ARNs - skipping Lambda updates")
    else:
        print("   [DRY-RUN] Would update 3 Lambdas with new layers")
    
    print(f"\n{'='*60}")
    print(f"[SUCCESS] Deployment to {env} completed successfully!")
    print('='*60)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deploy to environment')
    parser.add_argument('--env', required=True, choices=['dev', 'stage', 'prod'], help='Environment')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    try:
        deploy_env(args.env, args.dry_run)
    except Exception as e:
        print(f"\n[ERROR] Deployment failed: {e}")
        exit(1)
