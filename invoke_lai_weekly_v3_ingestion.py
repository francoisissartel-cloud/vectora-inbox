#!/usr/bin/env python3
import boto3
import json
import time

# Configuration
profile = 'rag-lai-prod'
region = 'eu-west-3'
lambda_name = 'vectora-inbox-ingest-normalize-dev'
client_id = 'lai_weekly_v3'

print("=== Phase 3 - Ingestion lai_weekly_v3 ===")

# Créer le client Lambda
session = boto3.Session(profile_name=profile)
lambda_client = session.client('lambda', region_name=region)

# Payload
payload = {
    'client_id': client_id,
    'period_days': 30
}

print(f"Client: {client_id}")
print(f"Period Days: 30")
print(f"Payload: {json.dumps(payload)}")

print("\nLancement ingestion...")

# Invoquer la Lambda
start_time = time.time()
try:
    response = lambda_client.invoke(
        FunctionName=lambda_name,
        Payload=json.dumps(payload)
    )
    
    end_time = time.time()
    duration = round(end_time - start_time, 2)
    
    print(f"✅ Lambda invoquée avec succès - Durée: {duration}s")
    
    # Lire la réponse
    response_payload = json.loads(response['Payload'].read())
    
    print(f"\nStatus Code: {response_payload.get('statusCode', 'N/A')}")
    
    if response_payload.get('statusCode') == 200:
        body = response_payload.get('body', {})
        
        print("\n=== MÉTRIQUES ===")
        print(f"Client: {body.get('client_id', 'N/A')}")
        print(f"Run ID: {body.get('run_id', 'N/A')}")
        print(f"Sources traitées: {body.get('sources_processed', 'N/A')}")
        print(f"Items ingérés: {body.get('items_ingested', 'N/A')}")
        print(f"Items normalisés: {body.get('items_normalized', 'N/A')}")
        print(f"Temps d'exécution: {body.get('execution_time_seconds', 'N/A')}s")
        
        # Calculer le taux de normalisation
        items_ingested = body.get('items_ingested', 0)
        items_normalized = body.get('items_normalized', 0)
        if items_ingested > 0:
            rate = round((items_normalized / items_ingested) * 100, 1)
            print(f"Taux de normalisation: {rate}%")
        
        print("\n=== Phase 3 TERMINÉE ===")
        
        # Sauvegarder la réponse complète
        with open('response-v3-ingestion-complete.json', 'w') as f:
            json.dump(response_payload, f, indent=2)
        
        print("Réponse sauvegardée dans response-v3-ingestion-complete.json")
        
    else:
        print(f"❌ Erreur - Status: {response_payload.get('statusCode')}")
        if 'body' in response_payload and 'error' in response_payload['body']:
            print(f"Erreur: {response_payload['body']['error']}")
        
        # Sauvegarder la réponse d'erreur
        with open('response-v3-ingestion-error.json', 'w') as f:
            json.dump(response_payload, f, indent=2)

except Exception as e:
    print(f"❌ Erreur lors de l'invocation: {str(e)}")