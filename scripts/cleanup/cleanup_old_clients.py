#!/usr/bin/env python3
"""
Script de nettoyage des anciens clients (< lai_weekly_v13)
Supprime configs et donnees S3 pour liberer l'espace
"""

import boto3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"

def list_old_clients(min_version=13):
    """Liste les clients < vX a supprimer"""
    old_clients = []
    for v in range(1, min_version):
        old_clients.append(f"lai_weekly_v{v}")
    return old_clients

def cleanup_s3_configs(env="dev", dry_run=True):
    """Supprime les configs S3 des anciens clients"""
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    s3 = session.client('s3')
    
    bucket = f"vectora-inbox-config-{env}"
    old_clients = list_old_clients()
    
    print(f"\n{'='*80}")
    print(f"NETTOYAGE CONFIGS S3 - {env.upper()}")
    print(f"{'='*80}")
    print(f"Bucket: {bucket}")
    print(f"Clients a supprimer: {len(old_clients)}")
    print()
    
    deleted = 0
    for client_id in old_clients:
        key = f"clients/{client_id}.yaml"
        
        try:
            s3.head_object(Bucket=bucket, Key=key)
            
            if dry_run:
                print(f"[DRY-RUN] Supprimerait: s3://{bucket}/{key}")
            else:
                s3.delete_object(Bucket=bucket, Key=key)
                print(f"[DELETED] s3://{bucket}/{key}")
            deleted += 1
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                pass
            else:
                print(f"[ERROR] {key}: {e}")
    
    print(f"\n{'='*80}")
    if dry_run:
        print(f"[DRY-RUN] {deleted} configs seraient supprimees")
    else:
        print(f"[SUCCESS] {deleted} configs supprimees")
    print(f"{'='*80}\n")
    
    return deleted

def cleanup_s3_data(env="dev", dry_run=True):
    """Supprime les dossiers data/ des anciens clients"""
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
    s3 = session.client('s3')
    
    bucket = f"vectora-inbox-data-{env}"
    old_clients = list_old_clients()
    
    print(f"\n{'='*80}")
    print(f"NETTOYAGE DATA S3 - {env.upper()}")
    print(f"{'='*80}")
    print(f"Bucket: {bucket}")
    print(f"Clients a supprimer: {len(old_clients)}")
    print()
    
    total_deleted = 0
    for client_id in old_clients:
        prefix = f"clients/{client_id}/"
        
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
        
        objects_to_delete = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    objects_to_delete.append({'Key': obj['Key']})
        
        if objects_to_delete:
            if dry_run:
                print(f"[DRY-RUN] Supprimerait {len(objects_to_delete)} objets pour {client_id}")
                for obj in objects_to_delete[:3]:
                    print(f"  - s3://{bucket}/{obj['Key']}")
                if len(objects_to_delete) > 3:
                    print(f"  ... et {len(objects_to_delete) - 3} autres")
            else:
                for i in range(0, len(objects_to_delete), 1000):
                    batch = objects_to_delete[i:i+1000]
                    s3.delete_objects(
                        Bucket=bucket,
                        Delete={'Objects': batch}
                    )
                print(f"[DELETED] {len(objects_to_delete)} objets pour {client_id}")
            
            total_deleted += len(objects_to_delete)
    
    print(f"\n{'='*80}")
    if dry_run:
        print(f"[DRY-RUN] {total_deleted} objets seraient supprimes")
    else:
        print(f"[SUCCESS] {total_deleted} objets supprimes")
    print(f"{'='*80}\n")
    
    return total_deleted

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Nettoyage anciens clients S3")
    parser.add_argument("--env", default="dev", choices=["dev", "stage", "prod"], help="Environnement")
    parser.add_argument("--execute", action="store_true", help="Executer (sinon dry-run)")
    parser.add_argument("--configs-only", action="store_true", help="Nettoyer seulement configs")
    parser.add_argument("--data-only", action="store_true", help="Nettoyer seulement data")
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if dry_run:
        print("\n" + "="*80)
        print("MODE DRY-RUN - Aucune suppression reelle")
        print("Utilisez --execute pour supprimer reellement")
        print("="*80)
    
    old_clients = list_old_clients()
    print(f"\nClients a nettoyer (< v13): {', '.join(old_clients)}")
    
    if not args.data_only:
        cleanup_s3_configs(args.env, dry_run)
    
    if not args.configs_only:
        cleanup_s3_data(args.env, dry_run)
    
    if dry_run:
        print("\n[INFO] Pour executer reellement, ajoutez --execute")
    else:
        print("\n[SUCCESS] Nettoyage termine")

if __name__ == "__main__":
    main()
