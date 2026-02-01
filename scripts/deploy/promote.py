#!/usr/bin/env python3
"""
Promouvoir version entre environnements avec validation Git
Usage: python scripts/deploy/promote.py --to stage --version 1.2.3 --git-sha <commit-sha>
"""
import argparse
import boto3
import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime

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

def run_command(cmd):
    """Exécuter commande shell"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip()

def verify_git_commit_exists(git_sha):
    """Vérifier que le commit existe"""
    try:
        run_command(f'git rev-parse {git_sha}')
        return True
    except:
        return False

def verify_version_in_commit(version, git_sha):
    """Vérifier que VERSION contient la bonne version dans le commit"""
    try:
        version_content = run_command(f'git show {git_sha}:VERSION')
        return f'VECTORA_CORE_VERSION={version}' in version_content
    except:
        return False

def create_snapshot(session, env):
    """Créer snapshot avant promotion"""
    print(f"📸 Creating snapshot of {env}...")
    
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'env': env,
        'lambdas': {}
    }
    
    lambda_client = session.client('lambda')
    lambda_functions = [
        f'vectora-inbox-ingest-v2-{env}',
        f'vectora-inbox-normalize-score-v2-{env}',
        f'vectora-inbox-newsletter-v2-{env}'
    ]
    
    for function_name in lambda_functions:
        try:
            response = lambda_client.get_function_configuration(FunctionName=function_name)
            snapshot['lambdas'][function_name] = {
                'layers': [layer['Arn'] for layer in response.get('Layers', [])]
            }
        except Exception as e:
            print(f"   ⚠️ Warning: Could not snapshot {function_name}: {e}")
    
    # Sauvegarder snapshot
    snapshot_dir = Path('.tmp/snapshots')
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot_file = snapshot_dir / f"snapshot_{env}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"   💾 Snapshot saved: {snapshot_file}")
    return snapshot_file

def rollback_to_snapshot(session, snapshot_file):
    """Rollback vers snapshot"""
    print(f"🔄 Rolling back to snapshot: {snapshot_file}")
    
    with open(snapshot_file) as f:
        snapshot = json.load(f)
    
    lambda_client = session.client('lambda')
    
    for function_name, config in snapshot['lambdas'].items():
        try:
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Layers=config['layers']
            )
            print(f"   ✅ Restored: {function_name}")
        except Exception as e:
            print(f"   ❌ Failed to restore {function_name}: {e}")

def run_smoke_tests(env):
    """Exécuter tests smoke"""
    print(f"🧪 Running smoke tests in {env}...")
    
    test_cmd = f'python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env {env}'
    
    try:
        result = run_command(test_cmd)
        if '"StatusCode": 200' in result or '"statusCode": 200' in result:
            print(f"   ✅ Smoke tests passed")
            return True
        else:
            print(f"   ❌ Smoke tests failed")
            return False
    except Exception as e:
        print(f"   ❌ Smoke tests error: {e}")
        return False

def promote(from_env, to_env, version, git_sha=None, dry_run=False):
    """Promouvoir version entre environnements avec validation Git"""
    print(f"🚀 PROMOTION INITIATED")
    print(f"   From: {from_env}")
    print(f"   To: {to_env}")
    print(f"   Version: {version}")
    if git_sha:
        print(f"   Git SHA: {git_sha}")
    
    if dry_run:
        print(f"   Mode: DRY RUN (no changes)")
        return
    
    # 1. Validation Git (si fourni)
    if git_sha:
        print(f"\n🔍 Validating Git commit...")
        if not verify_git_commit_exists(git_sha):
            raise ValueError(f"Git commit {git_sha} not found. Run: git log")
        print(f"   ✅ Git commit exists")
        
        if not verify_version_in_commit(version, git_sha):
            raise ValueError(f"Version {version} not found in commit {git_sha}")
        print(f"   ✅ Version matches commit")
    else:
        print(f"\n⚠️ Warning: No Git SHA provided, skipping Git validation")
    
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    s3 = session.client('s3')
    lambda_client = session.client('lambda')
    
    # 2. Créer snapshot avant promotion
    snapshot_file = create_snapshot(session, to_env)
    
    try:
        # 3. Copier layers S3
        print("\n📦 Copying layers...")
        source_bucket = f'vectora-inbox-lambda-code-{from_env}'
        target_bucket = f'vectora-inbox-lambda-code-{to_env}'
        
        # Vérifier que les layers existent en source
        layer_files = [
            f'layers/vectora-core-{version}.zip',
            f'layers/common-deps-{version}.zip'
        ]
        
        for layer_file in layer_files:
            try:
                s3.head_object(Bucket=source_bucket, Key=layer_file)
                print(f"   ✅ Found: {layer_file}")
            except:
                raise ValueError(f"Layer not found: s3://{source_bucket}/{layer_file}")
        
        # Copier layers
        for layer_file in layer_files:
            print(f"   Copying {layer_file}")
            copy_source = {'Bucket': source_bucket, 'Key': layer_file}
            s3.copy_object(CopySource=copy_source, Bucket=target_bucket, Key=layer_file)
        
        # 4. Publier layers dans env cible
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
        
        # 5. Mettre à jour Lambdas
        print("\n🔄 Updating Lambdas...")
        
        lambdas = [
            f'vectora-inbox-ingest-v2-{to_env}',
            f'vectora-inbox-normalize-score-v2-{to_env}',
            f'vectora-inbox-newsletter-v2-{to_env}'
        ]
        
        for lambda_name in lambdas:
            update_lambda_layers(session, lambda_name, layer_arns)
        
        # 6. Copier canonical
        print("\n📄 Copying canonical...")
        
        source_config_bucket = f'vectora-inbox-config-{from_env}'
        target_config_bucket = f'vectora-inbox-config-{to_env}'
        source_prefix = 'canonical/'
        
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=source_config_bucket, Prefix=source_prefix):
            for obj in page.get('Contents', []):
                source_key = obj['Key']
                copy_source = {'Bucket': source_config_bucket, 'Key': source_key}
                s3.copy_object(CopySource=copy_source, Bucket=target_config_bucket, Key=source_key)
                print(f"   Copied: {source_key}")
        
        # 7. Tests smoke
        if not run_smoke_tests(to_env):
            raise RuntimeError("Smoke tests failed after promotion")
        
        print(f"\n✅ PROMOTION SUCCESSFUL")
        print(f"   {from_env} → {to_env}")
        print(f"   Version: {version}")
        if git_sha:
            print(f"   Git SHA: {git_sha}")
        print(f"   Snapshot: {snapshot_file} (can rollback)")
        print(f"\n💡 To verify: python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env {to_env}")
        
    except Exception as e:
        print(f"\n❌ PROMOTION FAILED: {e}")
        print(f"\n🔄 Rolling back to snapshot...")
        
        try:
            rollback_to_snapshot(session, snapshot_file)
            print(f"   ✅ Rollback successful")
        except Exception as rollback_error:
            print(f"   ❌ Rollback failed: {rollback_error}")
            print(f"   ⚠️ MANUAL INTERVENTION REQUIRED")
            print(f"   Snapshot file: {snapshot_file}")
        
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Promote version between environments with Git validation')
    parser.add_argument('--from', dest='from_env', default='dev', choices=['dev', 'stage'], help='Source environment')
    parser.add_argument('--to', dest='to_env', required=True, choices=['stage', 'prod'], help='Target environment')
    parser.add_argument('--version', required=True, help='Version to promote (e.g., 1.2.3)')
    parser.add_argument('--git-sha', help='Git commit SHA (recommended for traceability)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    # Confirmation utilisateur
    if not args.dry_run:
        print(f"\n⚠️ WARNING: You are about to promote version {args.version} to {args.to_env}")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Promotion cancelled")
            sys.exit(0)
    
    try:
        promote(args.from_env, args.to_env, args.version, args.git_sha, args.dry_run)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
