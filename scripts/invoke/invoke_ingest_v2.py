#!/usr/bin/env python3
"""
Script d'invocation pour ingest-v2.
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime

# Configuration AWS
AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"
LAMBDA_NAME_DEV = "vectora-inbox-ingest-v2-dev"
LAMBDA_NAME_STAGE = "vectora-inbox-ingest-v2-stage"

def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def invoke_lambda(client_id, env="dev"):
    """Invoque la Lambda ingest-v2."""
    lambda_name = LAMBDA_NAME_DEV if env == "dev" else LAMBDA_NAME_STAGE
    
    log(f"=== Invocation ingest-v2 ===")
    log(f"Lambda: {lambda_name}")
    log(f"Client: {client_id}")
    log(f"Environnement: {env}")
    
    # Créer l'event
    event = {
        "client_id": client_id
    }
    
    # Créer fichier temporaire
    event_file = "temp_ingest_event.json"
    response_file = "temp_ingest_response.json"
    
    try:
        with open(event_file, "w") as f:
            json.dump(event, f, indent=2)
        
        log(f"Event: {json.dumps(event, indent=2)}")
        
        # Invoquer la Lambda
        command = f"aws lambda invoke --function-name {lambda_name} --cli-binary-format raw-in-base64-out --payload file://{event_file} {response_file} --profile {AWS_PROFILE} --region {AWS_REGION}"
        
        log(f"Invocation en cours...")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            log(f"[ERREUR] {result.stderr}")
            return False
        
        # Lire la réponse
        if os.path.exists(response_file):
            with open(response_file, "r") as f:
                response = json.load(f)
            
            log(f"[OK] Invocation terminée")
            
            # Afficher le résultat
            if "statusCode" in response:
                status_code = response["statusCode"]
                body = response.get("body", {})
                
                if status_code == 200:
                    log(f"[SUCCÈS] StatusCode: 200")
                    if "statistics" in body:
                        stats = body["statistics"]
                        log(f"[STATS] Items ingérés: {stats.get('items_ingested', 'N/A')}")
                        log(f"[STATS] Sources scrapées: {stats.get('sources_scraped', 'N/A')}")
                    if "s3_path" in body:
                        log(f"[S3] Fichier: {body['s3_path']}")
                    return True
                else:
                    log(f"[ERREUR] StatusCode: {status_code}")
                    if "error" in body:
                        log(f"[ERREUR] {body.get('error')}: {body.get('message', 'N/A')}")
                    return False
            else:
                log(f"[RÉPONSE] {json.dumps(response, indent=2)}")
                return True
        else:
            log("[ERREUR] Pas de fichier de réponse")
            return False
    
    finally:
        # Nettoyer
        for f in [event_file, response_file]:
            if os.path.exists(f):
                os.remove(f)

def main():
    parser = argparse.ArgumentParser(description="Invocation ingest-v2")
    parser.add_argument("--client-id", required=True, help="ID du client (ex: lai_weekly_v9)")
    parser.add_argument("--env", default="dev", choices=["dev", "stage"], help="Environnement")
    
    args = parser.parse_args()
    
    success = invoke_lambda(args.client_id, args.env)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
