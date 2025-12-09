#!/usr/bin/env python3
"""Script pour invoquer les Lambdas Vectora Inbox en DEV"""

import json
import boto3
import time
from datetime import datetime

# Configuration
PROFILE = "rag-lai-prod"
REGION = "eu-west-3"
CLIENT_ID = "lai_weekly"
PERIOD_DAYS = 7

# Créer le client Lambda avec timeout augmenté
from botocore.config import Config

config = Config(
    read_timeout=900,  # 15 minutes
    connect_timeout=60
)

session = boto3.Session(profile_name=PROFILE, region_name=REGION)
lambda_client = session.client('lambda', config=config)
s3_client = session.client('s3')

print("=== Test end-to-end : ingest-normalize -> engine ===")
print(f"Client: {CLIENT_ID}")
print(f"Période: {PERIOD_DAYS} jours")
print()

# Étape 1 : Invoquer ingest-normalize
print("=== Étape 1 : Invocation de ingest-normalize ===")
ingest_payload = {
    "client_id": CLIENT_ID,
    "period_days": PERIOD_DAYS
}

try:
    response = lambda_client.invoke(
        FunctionName='vectora-inbox-ingest-normalize-dev',
        InvocationType='RequestResponse',
        Payload=json.dumps(ingest_payload)
    )
    
    ingest_result = json.loads(response['Payload'].read())
    print("[OK] Ingest-normalize invoked successfully")
    print(json.dumps(ingest_result, indent=2))
    
    # Sauvegarder la réponse
    with open('out-ingest-lai-weekly.json', 'w') as f:
        json.dump(ingest_result, f, indent=2)
    
except Exception as e:
    print(f"[ERROR] Error invoking ingest-normalize: {e}")
    exit(1)

print()
print("Waiting 10 seconds before invoking engine...")
time.sleep(10)

# Étape 2 : Invoquer engine
print()
print("=== Étape 2 : Invocation de engine ===")
engine_payload = {
    "client_id": CLIENT_ID,
    "period_days": PERIOD_DAYS
}

try:
    response = lambda_client.invoke(
        FunctionName='vectora-inbox-engine-dev',
        InvocationType='RequestResponse',
        Payload=json.dumps(engine_payload)
    )
    
    engine_result = json.loads(response['Payload'].read())
    print("[OK] Engine invoked successfully")
    print(json.dumps(engine_result, indent=2))
    
    # Sauvegarder la réponse
    with open('out-engine-lai-weekly.json', 'w') as f:
        json.dump(engine_result, f, indent=2)
    
    # Extraire le chemin S3 de la newsletter
    if 'body' in engine_result and 's3_output_path' in engine_result['body']:
        s3_path = engine_result['body']['s3_output_path']
        print(f"\n[OK] Newsletter generated at: {s3_path}")
        
        # Extraire bucket et key
        s3_path_parts = s3_path.replace('s3://', '').split('/', 1)
        bucket = s3_path_parts[0]
        key = s3_path_parts[1]
        
        # Télécharger la newsletter
        print(f"Downloading newsletter from s3://{bucket}/{key}...")
        try:
            s3_client.download_file(bucket, key, 'newsletter-lai-weekly.md')
            print("[OK] Newsletter downloaded successfully: newsletter-lai-weekly.md")
            
            # Afficher un aperçu
            print("\n=== Aperçu de la newsletter ===")
            with open('newsletter-lai-weekly.md', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[:30]:
                    print(line.rstrip())
                if len(lines) > 30:
                    print("...")
        except Exception as e:
            print(f"[ERROR] Error downloading newsletter: {e}")
    else:
        print("[WARNING] No s3_output_path found in engine response")
    
except Exception as e:
    print(f"[ERROR] Error invoking engine: {e}")
    exit(1)

print()
print("=== Test terminé ===")
