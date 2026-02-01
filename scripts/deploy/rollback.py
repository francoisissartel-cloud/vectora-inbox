#!/usr/bin/env python3
"""
Rollback vers version précédente avec validation Git
Usage: python scripts/deploy/rollback.py --env stage --to-version 1.2.3 --git-tag v1.2.3
"""
import argparse
import boto3
import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

def run_command(cmd, capture=True):
    """Exécuter commande shell"""
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if result.returncode != 0 and capture:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip() if capture else None

def verify_git_tag_exists(git_tag):
    """Vérifier que le tag Git existe"""
    try:
        run_command(f'git rev-parse {git_tag}')
        return True
    except:
        return False

def verify_version_in_tag(version, git_tag):
    """Vérifier que VERSION contient la bonne version dans le tag"""
    try:
        version_content = run_command(f'git show {git_tag}:VERSION')
        return f'VECTORA_CORE_VERSION={version}' in version_content
    except:
        return False

def get_current_lambda_config(session, function_name):
    """Récupérer configuration actuelle Lambda"""
    lambda_client = session.client('lambda')
    response = lambda_client.get_function_configuration(FunctionName=function_name)
    
    return {
        'function_name': function_name,
        'layers': response.get('Layers', []),
        'environment': response.get('Environment', {}),
        'timeout': response.get('Timeout'),
        'memory': response.get('MemorySize'),
        'runtime': response.get('Runtime')
    }

def create_snapshot(session, env):
    """Créer snapshot de l'état actuel"""
    print(f"📸 Creating snapshot of {env} environment...")
    
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'env': env,
        'lambdas': {}
    }
    
    lambda_functions = [
        f'vectora-inbox-ingest-v2-{env}',
        f'vectora-inbox-normalize-score-v2-{env}',
        f'vectora-inbox-newsletter-v2-{env}'
    ]
    
    for function_name in lambda_functions:
        try:
            config = get_current_lambda_config(session, function_name)
            snapshot['lambdas'][function_name] = config
            print(f"   ✅ Snapshot: {function_name}")
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

def verify_artifacts_exist(session, env, version):
    """Vérifier que les artefacts existent en S3"""
    s3 = session.client('s3')
    bucket = f'vectora-inbox-lambda-code-{env}'
    
    artifacts = [
        f'layers/vectora-core-{version}.zip',
        f'layers/common-deps-{version}.zip'
    ]
    
    for artifact in artifacts:
        try:
            s3.head_object(Bucket=bucket, Key=artifact)
            print(f"   ✅ Found: {artifact}")
        except:
            raise ValueError(f"Artifact not found: s3://{bucket}/{artifact}")

def rollback_layers(session, env, version):
    """Rollback layers vers version spécifique"""
    print(f"\n🔄 Rolling back layers to version {version}...")
    
    lambda_client = session.client('lambda')
    bucket = f'vectora-inbox-lambda-code-{env}'
    
    layer_configs = [
        {
            'name': f'vectora-inbox-vectora-core-{env}',
            'file': f'layers/vectora-core-{version}.zip'
        },
        {
            'name': f'vectora-inbox-common-deps-{env}',
            'file': f'layers/common-deps-{version}.zip'
        }
    ]
    
    layer_arns = []
    
    for layer_config in layer_configs:
        response = lambda_client.publish_layer_version(
            LayerName=layer_config['name'],
            Content={'S3Bucket': bucket, 'S3Key': layer_config['file']},
            CompatibleRuntimes=['python3.11', 'python3.12'],
            Description=f'Rollback to version {version}'
        )
        
        layer_arns.append(response['LayerVersionArn'])
        print(f"   ✅ Published: {response['LayerVersionArn']}")
    
    return layer_arns

def rollback_lambdas(session, env, layer_arns):
    """Rollback Lambdas avec nouveaux layers"""
    print(f"\n🔄 Updating Lambda functions...")
    
    lambda_client = session.client('lambda')
    
    lambda_functions = [
        f'vectora-inbox-ingest-v2-{env}',
        f'vectora-inbox-normalize-score-v2-{env}',
        f'vectora-inbox-newsletter-v2-{env}'
    ]
    
    for function_name in lambda_functions:
        try:
            response = lambda_client.update_function_configuration(
                FunctionName=function_name,
                Layers=layer_arns
            )
            print(f"   ✅ Updated: {function_name}")
        except Exception as e:
            raise RuntimeError(f"Failed to update {function_name}: {e}")

def run_smoke_tests(env, version):
    """Exécuter tests smoke après rollback"""
    print(f"\n🧪 Running smoke tests in {env}...")
    
    test_cmd = f'python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env {env}'
    
    try:
        result = run_command(test_cmd, capture=True)
        
        # Vérifier StatusCode 200 dans la réponse
        if '"StatusCode": 200' in result or '"statusCode": 200' in result:
            print(f"   ✅ Smoke tests passed")
            return True
        else:
            print(f"   ❌ Smoke tests failed")
            print(f"   Response: {result[:200]}...")
            return False
    except Exception as e:
        print(f"   ❌ Smoke tests error: {e}")
        return False

def restore_snapshot(session, snapshot_file):
    """Restaurer depuis snapshot"""
    print(f"\n🔄 Restoring from snapshot: {snapshot_file}")
    
    with open(snapshot_file) as f:
        snapshot = json.load(f)
    
    lambda_client = session.client('lambda')
    
    for function_name, config in snapshot['lambdas'].items():
        try:
            layer_arns = [layer['Arn'] for layer in config['layers']]
            
            lambda_client.update_function_configuration(
                FunctionName=function_name,
                Layers=layer_arns
            )
            print(f"   ✅ Restored: {function_name}")
        except Exception as e:
            print(f"   ❌ Failed to restore {function_name}: {e}")

def rollback(env, to_version, git_tag, dry_run=False):
    """Rollback complet vers version précédente"""
    
    print(f"🔄 ROLLBACK INITIATED")
    print(f"   Environment: {env}")
    print(f"   Target version: {to_version}")
    print(f"   Git tag: {git_tag}")
    
    if dry_run:
        print(f"   Mode: DRY RUN (no changes)")
        return
    
    # 1. Validation Git
    print(f"\n🔍 Validating Git tag...")
    if not verify_git_tag_exists(git_tag):
        raise ValueError(f"Git tag {git_tag} not found. Run: git tag -l")
    print(f"   ✅ Git tag exists")
    
    if not verify_version_in_tag(to_version, git_tag):
        raise ValueError(f"Version {to_version} not found in tag {git_tag}")
    print(f"   ✅ Version matches tag")
    
    # 2. Session AWS
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    
    # 3. Vérifier artefacts
    print(f"\n🔍 Verifying artifacts in S3...")
    verify_artifacts_exist(session, env, to_version)
    
    # 4. Créer snapshot
    snapshot_file = create_snapshot(session, env)
    
    try:
        # 5. Rollback layers
        layer_arns = rollback_layers(session, env, to_version)
        
        # 6. Rollback Lambdas
        rollback_lambdas(session, env, layer_arns)
        
        # 7. Tests smoke
        if not run_smoke_tests(env, to_version):
            raise RuntimeError("Smoke tests failed after rollback")
        
        print(f"\n✅ ROLLBACK SUCCESSFUL")
        print(f"   Environment: {env}")
        print(f"   Version: {to_version}")
        print(f"   Git tag: {git_tag}")
        print(f"   Snapshot: {snapshot_file}")
        print(f"\n💡 To verify: python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env {env}")
        
    except Exception as e:
        print(f"\n❌ ROLLBACK FAILED: {e}")
        print(f"\n🔄 Attempting to restore from snapshot...")
        
        try:
            restore_snapshot(session, snapshot_file)
            print(f"   ✅ Restored from snapshot")
        except Exception as restore_error:
            print(f"   ❌ Restore failed: {restore_error}")
            print(f"   ⚠️ MANUAL INTERVENTION REQUIRED")
            print(f"   Snapshot file: {snapshot_file}")
        
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rollback to previous version')
    parser.add_argument('--env', required=True, choices=['dev', 'stage', 'prod'], 
                       help='Target environment')
    parser.add_argument('--to-version', required=True, 
                       help='Target version (e.g., 1.2.3)')
    parser.add_argument('--git-tag', required=True, 
                       help='Git tag corresponding to version (e.g., v1.2.3)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Dry run mode (no changes)')
    
    args = parser.parse_args()
    
    # Confirmation utilisateur
    if not args.dry_run:
        print(f"\n⚠️ WARNING: You are about to rollback {args.env} to version {args.to_version}")
        confirm = input("Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Rollback cancelled")
            sys.exit(0)
    
    try:
        rollback(args.env, args.to_version, args.git_tag, args.dry_run)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
