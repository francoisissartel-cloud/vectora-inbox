#!/usr/bin/env python3
"""
Créer snapshot de l'environnement actuel
Usage: python scripts/maintenance/create_snapshot.py --env dev --name "pre_deploy_v124"
"""
import argparse
import boto3
import json
from datetime import datetime
from pathlib import Path

def get_lambda_config(lambda_client, function_name):
    """Récupérer configuration complète Lambda"""
    try:
        response = lambda_client.get_function_configuration(FunctionName=function_name)
        
        return {
            'function_name': function_name,
            'function_arn': response['FunctionArn'],
            'runtime': response['Runtime'],
            'handler': response['Handler'],
            'memory_size': response['MemorySize'],
            'timeout': response['Timeout'],
            'layers': [
                {
                    'arn': layer['Arn'],
                    'code_size': layer.get('CodeSize', 0)
                }
                for layer in response.get('Layers', [])
            ],
            'environment': response.get('Environment', {}).get('Variables', {}),
            'last_modified': response['LastModified']
        }
    except Exception as e:
        return {'error': str(e)}

def get_s3_config_files(s3_client, bucket, prefix='canonical/'):
    """Lister fichiers de configuration S3"""
    files = []
    
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })
    except Exception as e:
        files.append({'error': str(e)})
    
    return files

def create_snapshot(env, name=None):
    """Créer snapshot complet de l'environnement"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    snapshot_name = name or f"snapshot_{env}_{timestamp}"
    
    print(f"📸 Creating snapshot: {snapshot_name}")
    print(f"   Environment: {env}")
    
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    lambda_client = session.client('lambda')
    s3_client = session.client('s3')
    
    snapshot = {
        'metadata': {
            'name': snapshot_name,
            'env': env,
            'timestamp': datetime.now().isoformat(),
            'created_by': 'create_snapshot.py'
        },
        'lambdas': {},
        's3_config': {},
        's3_data': {}
    }
    
    # 1. Snapshot Lambdas
    print(f"\n📦 Snapshotting Lambda functions...")
    lambda_functions = [
        f'vectora-inbox-ingest-v2-{env}',
        f'vectora-inbox-normalize-score-v2-{env}',
        f'vectora-inbox-newsletter-v2-{env}'
    ]
    
    for function_name in lambda_functions:
        config = get_lambda_config(lambda_client, function_name)
        snapshot['lambdas'][function_name] = config
        
        if 'error' in config:
            print(f"   ⚠️ {function_name}: {config['error']}")
        else:
            print(f"   ✅ {function_name}")
            print(f"      Layers: {len(config['layers'])}")
            print(f"      Memory: {config['memory_size']}MB")
            print(f"      Timeout: {config['timeout']}s")
    
    # 2. Snapshot S3 Config
    print(f"\n📄 Snapshotting S3 config bucket...")
    config_bucket = f'vectora-inbox-config-{env}'
    
    snapshot['s3_config']['bucket'] = config_bucket
    snapshot['s3_config']['canonical'] = get_s3_config_files(s3_client, config_bucket, 'canonical/')
    snapshot['s3_config']['clients'] = get_s3_config_files(s3_client, config_bucket, 'clients/')
    
    print(f"   ✅ Canonical files: {len(snapshot['s3_config']['canonical'])}")
    print(f"   ✅ Client configs: {len(snapshot['s3_config']['clients'])}")
    
    # 3. Snapshot S3 Data (metadata uniquement)
    print(f"\n💾 Snapshotting S3 data bucket (metadata)...")
    data_bucket = f'vectora-inbox-data-{env}'
    
    snapshot['s3_data']['bucket'] = data_bucket
    snapshot['s3_data']['ingested'] = get_s3_config_files(s3_client, data_bucket, 'ingested/')[:10]  # Limiter à 10
    snapshot['s3_data']['curated'] = get_s3_config_files(s3_client, data_bucket, 'curated/')[:10]
    
    print(f"   ✅ Data bucket metadata captured")
    
    # 4. Sauvegarder snapshot
    snapshot_dir = Path('docs/snapshots')
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot_file = snapshot_dir / f"{snapshot_name}.json"
    with open(snapshot_file, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"\n✅ SNAPSHOT CREATED")
    print(f"   File: {snapshot_file}")
    print(f"   Size: {snapshot_file.stat().st_size / 1024:.1f} KB")
    
    # 5. Créer index des snapshots
    update_snapshot_index(snapshot_dir, snapshot_name, env)
    
    return snapshot_file

def update_snapshot_index(snapshot_dir, snapshot_name, env):
    """Mettre à jour l'index des snapshots"""
    index_file = snapshot_dir / 'INDEX.md'
    
    # Lire index existant
    if index_file.exists():
        with open(index_file) as f:
            content = f.read()
    else:
        content = "# Snapshots Index\n\n"
        content += "Liste des snapshots disponibles pour rollback.\n\n"
        content += "## Snapshots\n\n"
        content += "| Date | Nom | Environnement | Fichier |\n"
        content += "|------|-----|---------------|----------|\n"
    
    # Ajouter nouvelle entrée
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    new_entry = f"| {timestamp} | {snapshot_name} | {env} | `{snapshot_name}.json` |\n"
    
    content += new_entry
    
    with open(index_file, 'w') as f:
        f.write(content)
    
    print(f"   📋 Index updated: {index_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create environment snapshot')
    parser.add_argument('--env', required=True, choices=['dev', 'stage', 'prod'],
                       help='Environment to snapshot')
    parser.add_argument('--name', help='Snapshot name (optional)')
    
    args = parser.parse_args()
    
    try:
        create_snapshot(args.env, args.name)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)
