#!/usr/bin/env python3
"""
Invocation workflow E2E complet: ingest → normalize → newsletter.
Conforme règles Q-Context.
"""

import boto3
import json
import argparse
import sys
from datetime import datetime

AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"

def log(message):
    """Log avec timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def invoke_lambda(function_name, payload, session):
    """Invoque Lambda et retourne résultat."""
    lambda_client = session.client('lambda', region_name=AWS_REGION)
    
    log(f"Invocation: {function_name}")
    log(f"Payload: {json.dumps(payload)}")
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        status_code = result.get('statusCode', 500)
        
        if status_code == 200:
            log(f"✅ {function_name}: SUCCESS")
            
            # Afficher stats si disponibles
            body = result.get('body', {})
            if 'statistics' in body:
                stats = body['statistics']
                log(f"   Items: {stats.get('items_input', 'N/A')} → {stats.get('items_output', 'N/A')}")
        else:
            log(f"❌ {function_name}: FAILED (status {status_code})")
            if 'body' in result and 'error' in result['body']:
                log(f"   Error: {result['body']['error']}")
        
        return result
    
    except Exception as e:
        log(f"❌ Exception: {str(e)}")
        return {"statusCode": 500, "error": str(e)}

def run_e2e_workflow(client_id, env="dev"):
    """Exécute workflow E2E complet."""
    
    log("="*80)
    log(f"WORKFLOW E2E - {client_id} (env: {env})")
    log("="*80)
    
    session = boto3.Session(profile_name=AWS_PROFILE)
    payload = {"client_id": client_id}
    
    # 1. Ingest
    log("\n📥 ÉTAPE 1/3: INGESTION")
    result_ingest = invoke_lambda(
        f"vectora-inbox-ingest-v2-{env}",
        payload,
        session
    )
    if result_ingest.get('statusCode') != 200:
        log("\n❌ Workflow arrêté: échec ingestion")
        return False
    
    # 2. Normalize
    log("\n🤖 ÉTAPE 2/3: NORMALISATION & SCORING")
    result_normalize = invoke_lambda(
        f"vectora-inbox-normalize-score-v2-{env}",
        payload,
        session
    )
    if result_normalize.get('statusCode') != 200:
        log("\n❌ Workflow arrêté: échec normalisation")
        return False
    
    # 3. Newsletter
    log("\n📰 ÉTAPE 3/3: GÉNÉRATION NEWSLETTER")
    result_newsletter = invoke_lambda(
        f"vectora-inbox-newsletter-v2-{env}",
        payload,
        session
    )
    if result_newsletter.get('statusCode') != 200:
        log("\n❌ Workflow arrêté: échec newsletter")
        return False
    
    log("\n" + "="*80)
    log("✅ WORKFLOW E2E COMPLÉTÉ AVEC SUCCÈS")
    log("="*80)
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Invocation workflow E2E complet"
    )
    parser.add_argument(
        "--client-id",
        required=True,
        help="Client ID (ex: lai_weekly_v1)"
    )
    parser.add_argument(
        "--env",
        default="dev",
        choices=["dev", "stage", "prod"],
        help="Environnement cible"
    )
    
    args = parser.parse_args()
    
    log(f"Configuration:")
    log(f"  Profile: {AWS_PROFILE}")
    log(f"  Region: {AWS_REGION}")
    log(f"  Client ID: {args.client_id}")
    log(f"  Environment: {args.env}")
    log("")
    
    success = run_e2e_workflow(args.client_id, args.env)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
