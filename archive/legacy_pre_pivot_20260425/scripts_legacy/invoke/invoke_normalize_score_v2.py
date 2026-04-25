#!/usr/bin/env python3
"""
Script d'invocation standardisé pour normalize_score_v2.
Conforme aux règles d'hygiène V4.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# Configuration AWS (règles V4)
AWS_PROFILE = "rag-lai-prod"
AWS_REGION = "eu-west-3"
LAMBDA_NAME = "vectora-inbox-normalize-score-v2-dev"

def log(message):
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_aws_command(command, check=True):
    full_command = f"aws {command} --profile {AWS_PROFILE} --region {AWS_REGION}"
    log(f"Exécution: {full_command}")
    
    result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        log(f"[ERREUR] {result.stderr}")
        sys.exit(1)
    
    return result

def get_test_event(event_name):
    """Récupère un event de test prédéfini."""
    events = {
        "lai_weekly_v3": {
            "client_id": "lai_weekly_v3"
        },
        "lai_weekly_v7": {
            "client_id": "lai_weekly_v7"
        },
        "lai_weekly_v8": {
            "client_id": "lai_weekly_v8"
        },
        "lai_weekly_v9": {
            "client_id": "lai_weekly_v9"
        },
        "lai_weekly_v10": {
            "client_id": "lai_weekly_v10"
        },
        "lai_weekly_v11": {
            "client_id": "lai_weekly_v11"
        },
        "lai_weekly_v12": {
            "client_id": "lai_weekly_v12"
        },
        "minimal": {
            "client_id": "lai_weekly_v3",
            "period_days": 1
        },
        "full": {
            "client_id": "lai_weekly_v3",
            "period_days": 7,
            "scoring_mode": "balanced",
            "force_reprocess": False
        }
    }
    
    if event_name not in events:
        log(f"[ERREUR] Event '{event_name}' non trouvé. Disponibles: {list(events.keys())}")
        sys.exit(1)
    
    return events[event_name]

def invoke_lambda(event_data, timeout=900):
    """Invoque la Lambda avec l'event donné."""
    log(f"Invocation de {LAMBDA_NAME}...")
    log(f"Event: {json.dumps(event_data, indent=2)}")
    log(f"Timeout CLI: {timeout}s")
    
    # Créer fichier d'event temporaire
    event_file = "temp_event.json"
    with open(event_file, "w") as f:
        json.dump(event_data, f)
    
    try:
        # Invoquer avec format CLI correct et timeout augmenté
        response_file = "temp_response.json"
        command = f"lambda invoke --function-name {LAMBDA_NAME} --cli-binary-format raw-in-base64-out --cli-read-timeout {timeout} --payload file://{event_file} {response_file}"
        
        import time
        start_time = time.time()
        result = run_aws_command(command)
        execution_time = time.time() - start_time
        
        # Lire la réponse
        if os.path.exists(response_file):
            with open(response_file, "r") as f:
                response = json.load(f)
            
            log(f"[OK] Invocation terminée en {execution_time:.1f}s")
            return response, execution_time
        else:
            log("[ERREUR] Pas de fichier de réponse")
            return None, execution_time
    
    finally:
        # Nettoyer les fichiers temporaires
        for f in [event_file, response_file]:
            if os.path.exists(f):
                os.remove(f)

def validate_response(response):
    """Valide la réponse de la Lambda."""
    log("Validation de la réponse...")
    
    if not response:
        log("[ERREUR] Réponse vide")
        return False
    
    # Vérifier la structure de base
    if "statusCode" not in response:
        log("[ERREUR] statusCode manquant")
        return False
    
    status_code = response["statusCode"]
    body = response.get("body", {})
    
    if status_code == 200:
        log("[OK] StatusCode: 200 (succès)")
        
        # Vérifier les champs obligatoires
        required_fields = ["client_id", "status", "processing_time_ms", "statistics"]
        missing_fields = [field for field in required_fields if field not in body]
        
        if missing_fields:
            log(f"[ATTENTION] Champs manquants: {missing_fields}")
        else:
            log("[OK] Tous les champs obligatoires présents")
        
        # Afficher les statistiques
        if "statistics" in body:
            stats = body["statistics"]
            log(f"[STATS] Items input: {stats.get('items_input', 'N/A')}")
            log(f"[STATS] Items normalized: {stats.get('items_normalized', 'N/A')}")
            log(f"[STATS] Items matched: {stats.get('items_matched', 'N/A')}")
            log(f"[STATS] Items scored: {stats.get('items_scored', 'N/A')}")
            log(f"[STATS] Processing time: {body.get('processing_time_ms', 'N/A')}ms")
        
        return True
    
    else:
        log(f"[ERREUR] StatusCode: {status_code}")
        if "error" in body:
            log(f"[ERREUR] {body['error']}: {body.get('message', 'N/A')}")
        return False

def measure_cold_start():
    """Mesure le cold start en invoquant 2 fois."""
    log("Mesure du cold start...")
    
    event_data = get_test_event("minimal")
    
    # Premier appel (cold start)
    log("Premier appel (cold start)...")
    _, cold_time = invoke_lambda(event_data)
    
    # Attendre un peu
    import time
    time.sleep(2)
    
    # Deuxième appel (warm start)
    log("Deuxième appel (warm start)...")
    _, warm_time = invoke_lambda(event_data)
    
    log(f"[PERF] Cold start: {cold_time:.1f}s")
    log(f"[PERF] Warm start: {warm_time:.1f}s")
    log(f"[PERF] Amélioration: {((cold_time - warm_time) / cold_time * 100):.1f}%")
    
    return cold_time, warm_time

def main():
    parser = argparse.ArgumentParser(description="Invocation standardisée normalize_score_v2")
    parser.add_argument("--event", default="lai_weekly_v3", 
                       choices=["lai_weekly_v3", "lai_weekly_v7", "lai_weekly_v8", "lai_weekly_v9", "lai_weekly_v10", "lai_weekly_v11", "lai_weekly_v12", "minimal", "full"],
                       help="Event de test à utiliser")
    parser.add_argument("--performance", action="store_true",
                       help="Mesurer les performances (cold/warm start)")
    parser.add_argument("--validate-only", action="store_true",
                       help="Validation uniquement (pas d'invocation)")
    
    args = parser.parse_args()
    
    log("=== Invocation normalize_score_v2 avec Lambda Layers ===")
    log(f"Lambda: {LAMBDA_NAME}")
    log(f"Région: {AWS_REGION}")
    
    try:
        if args.validate_only:
            log("Mode validation uniquement")
            # Vérifier que la Lambda existe
            result = run_aws_command(f"lambda get-function --function-name {LAMBDA_NAME}")
            function_info = json.loads(result.stdout)
            
            layers = function_info["Configuration"].get("Layers", [])
            code_size = function_info["Configuration"]["CodeSize"]
            
            log(f"[OK] Lambda trouvée, {len(layers)} layers, {code_size} bytes")
            return
        
        if args.performance:
            cold_time, warm_time = measure_cold_start()
            
            if cold_time < 10:  # <10s
                log("[EXCELLENT] Cold start très rapide grâce aux layers")
            elif cold_time < 30:  # <30s
                log("[BON] Cold start acceptable")
            else:
                log("[ATTENTION] Cold start lent")
        
        else:
            # Invocation simple
            event_data = get_test_event(args.event)
            response, exec_time = invoke_lambda(event_data)
            
            if validate_response(response):
                log("[SUCCES] Test d'invocation réussi")
                log(f"Temps d'exécution: {exec_time:.1f}s")
            else:
                log("[ECHEC] Test d'invocation échoué")
                sys.exit(1)
    
    except Exception as e:
        log(f"[ERREUR] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()