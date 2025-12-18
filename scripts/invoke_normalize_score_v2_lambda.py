#!/usr/bin/env python3
"""
Script d'invocation Lambda : vectora-inbox-normalize-score-v2-dev

Contourne les problèmes d'encodage JSON de l'AWS CLI sous Windows.
Utilise boto3 pour invoquer la Lambda proprement avec un payload JSON.

Usage Windows (PowerShell):
    $env:AWS_PROFILE = "rag-lai-prod"
    $env:AWS_DEFAULT_REGION = "eu-west-3"
    python .\\scripts\\invoke_normalize_score_v2_lambda.py
    python .\\scripts\\invoke_normalize_score_v2_lambda.py --client-id lai_weekly_v3
    python .\\scripts\\invoke_normalize_score_v2_lambda.py --diagnostic
    python .\\scripts\\invoke_normalize_score_v2_lambda.py --auto-scan

Usage Linux/Mac (bash):
    export AWS_PROFILE=rag-lai-prod
    export AWS_DEFAULT_REGION=eu-west-3
    python scripts/invoke_normalize_score_v2_lambda.py
"""

import argparse
import json
import sys
import boto3
from datetime import datetime


# Configuration Lambda
LAMBDA_FUNCTION_NAME = "vectora-inbox-normalize-score-v2-dev"
LAMBDA_REGION = "eu-west-3"
DEFAULT_CLIENT_ID = "lai_weekly_v3"


def invoke_lambda(client_id=None, diagnostic=False, auto_scan=False):
    """
    Invoque la Lambda normalize_score_v2 avec le payload spécifié.
    
    Args:
        client_id: ID du client à traiter (None pour auto-scan)
        diagnostic: Active le mode diagnostic
        auto_scan: Mode auto-scan (tous les clients actifs)
    
    Returns:
        dict: Réponse de la Lambda
    """
    # Construire le payload
    if auto_scan:
        event = {}
    else:
        event = {"client_id": client_id or DEFAULT_CLIENT_ID}
    
    if diagnostic:
        event["diagnostic"] = True
    
    print(f"[INVOKE] Lambda: {LAMBDA_FUNCTION_NAME}")
    print(f"[REGION] {LAMBDA_REGION}")
    print(f"[PAYLOAD] {json.dumps(event, indent=2)}")
    print("-" * 60)
    
    # Créer le client Lambda
    try:
        lambda_client = boto3.client("lambda", region_name=LAMBDA_REGION)
    except Exception as e:
        print(f"[ERROR] Creation client boto3: {e}")
        print("[INFO] Verifiez que AWS_PROFILE et AWS_DEFAULT_REGION sont configures")
        sys.exit(1)
    
    # Invoquer la Lambda
    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
    except Exception as e:
        print(f"[ERROR] Invocation Lambda: {e}")
        sys.exit(1)
    
    return response


def parse_response(response):
    """
    Parse et affiche la réponse de la Lambda.
    
    Args:
        response: Réponse boto3 de l'invocation Lambda
    """
    # Statut de l'invocation
    status_code = response.get("StatusCode")
    function_error = response.get("FunctionError")
    
    print(f"[STATUS] StatusCode: {status_code}")
    
    if function_error:
        print(f"[ERROR] FunctionError: {function_error}")
    else:
        print("[OK] Pas d'erreur Lambda")
    
    print("-" * 60)
    
    # Payload de réponse
    payload_bytes = response["Payload"].read()
    
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Decodage JSON: {e}")
        print(f"Payload brut: {payload_bytes.decode('utf-8')}")
        return
    
    # Afficher le résumé
    print("[RESPONSE] Resume de la reponse:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("-" * 60)
    
    # Extraire les métriques clés si présentes
    if isinstance(payload, dict):
        body = payload.get("body")
        if body:
            try:
                body_data = json.loads(body) if isinstance(body, str) else body
                
                # Métriques de matching
                items_input = body_data.get("items_input", "N/A")
                items_matched = body_data.get("items_matched", "N/A")
                items_scored = body_data.get("items_scored", "N/A")
                
                print("[METRICS] Metriques cles:")
                print(f"  - Items input: {items_input}")
                print(f"  - Items matched: {items_matched}")
                print(f"  - Items scored: {items_scored}")
                
                # Taux de matching
                if isinstance(items_input, int) and isinstance(items_matched, int) and items_input > 0:
                    matching_rate = (items_matched / items_input) * 100
                    print(f"  - Taux de matching: {matching_rate:.1f}%")
                
                # Distribution par domaine
                domain_stats = body_data.get("domain_statistics", {})
                if domain_stats:
                    print("\n[DOMAINS] Distribution par domaine:")
                    for domain, count in domain_stats.items():
                        print(f"  - {domain}: {count} items")
                
                print("-" * 60)
                
            except (json.JSONDecodeError, AttributeError, KeyError) as e:
                print(f"[WARN] Impossible d'extraire les metriques: {e}")
    
    # Verdict final
    if function_error:
        print("[FAIL] La Lambda a retourne une erreur")
        sys.exit(1)
    elif status_code == 200:
        print("[SUCCESS] Lambda executee avec succes")
        
        # Verifier si matching a fonctionne
        if isinstance(payload, dict):
            body = payload.get("body")
            if body:
                try:
                    body_data = json.loads(body) if isinstance(body, str) else body
                    items_matched = body_data.get("items_matched", 0)
                    
                    if items_matched > 0:
                        print(f"[MATCHING] Operationnel : {items_matched} items matches")
                    else:
                        print("[WARN] Attention : 0 items matches (verifier configuration)")
                except:
                    pass
    else:
        print(f"[WARN] StatusCode inattendu: {status_code}")


def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Invoque la Lambda normalize_score_v2 pour tester le matching V2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Test avec lai_weekly_v3 (défaut)
  python scripts/invoke_normalize_score_v2_lambda.py
  
  # Test avec client spécifique
  python scripts/invoke_normalize_score_v2_lambda.py --client-id lai_weekly_v3
  
  # Test en mode diagnostic
  python scripts/invoke_normalize_score_v2_lambda.py --diagnostic
  
  # Auto-scan tous les clients
  python scripts/invoke_normalize_score_v2_lambda.py --auto-scan

Prérequis:
  Windows PowerShell:
    $env:AWS_PROFILE = "rag-lai-prod"
    $env:AWS_DEFAULT_REGION = "eu-west-3"
  
  Linux/Mac bash:
    export AWS_PROFILE=rag-lai-prod
    export AWS_DEFAULT_REGION=eu-west-3
        """
    )
    
    parser.add_argument(
        "--client-id",
        type=str,
        default=DEFAULT_CLIENT_ID,
        help=f"ID du client à traiter (défaut: {DEFAULT_CLIENT_ID})"
    )
    
    parser.add_argument(
        "--diagnostic",
        action="store_true",
        help="Active le mode diagnostic (logs détaillés)"
    )
    
    parser.add_argument(
        "--auto-scan",
        action="store_true",
        help="Mode auto-scan (tous les clients actifs, ignore --client-id)"
    )
    
    args = parser.parse_args()
    
    # Timestamp
    print(f"\n[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Invoquer la Lambda
    response = invoke_lambda(
        client_id=args.client_id,
        diagnostic=args.diagnostic,
        auto_scan=args.auto_scan
    )
    
    # Parser et afficher la réponse
    parse_response(response)
    
    print("=" * 60)
    print(f"[TIME] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    main()
