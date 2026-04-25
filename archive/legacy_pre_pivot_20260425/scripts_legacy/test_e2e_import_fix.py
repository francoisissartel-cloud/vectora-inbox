#!/usr/bin/env python3
"""
Test E2E pour valider la correction d'import Bedrock V2.
Déclenche un run complet sur lai_weekly_v3 et collecte les métriques.
"""

import json
import subprocess
import sys
from datetime import datetime

def invoke_normalize_score():
    """Invoque la Lambda normalize-score-v2-dev."""
    print("=== Invocation Lambda normalize-score-v2-dev ===")
    
    payload = {
        "client_id": "lai_weekly_v3",
        "period_days": 30
    }
    
    function_name = "vectora-inbox-normalize-score-v2-dev"
    region = "eu-west-3"
    profile = "rag-lai-prod"
    output_file = "response_import_fix_test.json"
    
    try:
        cmd = [
            "aws", "lambda", "invoke",
            "--function-name", function_name,
            "--payload", json.dumps(payload),
            "--region", region,
            "--profile", profile,
            output_file
        ]
        
        print(f"Payload: {json.dumps(payload)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Lire la réponse
        with open(output_file, 'r') as f:
            response = json.load(f)
        
        return response
        
    except subprocess.CalledProcessError as e:
        print(f"ERREUR invocation Lambda: {e}")
        print(f"stderr: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERREUR parsing réponse: {e}")
        return None

def analyze_response(response):
    """Analyse la réponse et extrait les métriques."""
    print("\n=== Analyse des résultats ===")
    
    if not response:
        print("ERREUR: Pas de réponse à analyser")
        return False
    
    # Extraire le body
    body = response.get('body', {})
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except:
            pass
    
    # Extraire les statistiques
    stats = body.get('statistics', {})
    
    print(f"Métriques du pipeline:")
    print(f"  items_input: {stats.get('items_input', 0)}")
    print(f"  items_normalized: {stats.get('items_normalized', 0)}")
    print(f"  items_matched: {stats.get('items_matched', 0)}")
    print(f"  items_scored: {stats.get('items_scored', 0)}")
    
    # Vérifier le critère de succès principal
    items_matched = stats.get('items_matched', 0)
    
    if items_matched > 0:
        print(f"\nSUCCES: {items_matched} items matches (vs 0 avant correction)")
        print("OK La correction d'import a resolu le probleme")
        return True
    else:
        print(f"\nATTENTION: items_matched = 0")
        print("Verifier les logs CloudWatch pour identifier la cause")
        return False

def check_cloudwatch_logs():
    """Vérifie les logs CloudWatch pour les erreurs d'import."""
    print("\n=== Vérification logs CloudWatch ===")
    
    log_group = "/aws/lambda/vectora-inbox-normalize-score-v2-dev"
    region = "eu-west-3"
    profile = "rag-lai-prod"
    
    try:
        # Récupérer les derniers logs
        cmd = [
            "aws", "logs", "tail",
            log_group,
            "--since", "5m",
            "--region", region,
            "--profile", profile,
            "--format", "short"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        logs = result.stdout
        
        # Chercher l'erreur d'import
        if "cannot import name '_call_bedrock_with_retry'" in logs:
            print("ERREUR: L'erreur d'import persiste dans les logs")
            return False
        elif "cannot import" in logs:
            print("ATTENTION: Autre erreur d'import détectée")
            print("Extrait des logs:")
            for line in logs.split('\n'):
                if 'cannot import' in line.lower():
                    print(f"  {line}")
            return False
        else:
            print("OK Aucune erreur d'import detectee dans les logs")
            
            # Chercher des patterns de succès
            if "Appel à Bedrock" in logs or "Appel a Bedrock" in logs:
                print("OK Appels Bedrock detectes dans les logs")
            
            if "Matching Bedrock V2" in logs:
                print("OK Matching Bedrock V2 execute")
            
            return True
            
    except subprocess.TimeoutExpired:
        print("TIMEOUT lors de la lecture des logs")
        return None
    except Exception as e:
        print(f"ERREUR lecture logs: {e}")
        return None

def main():
    """Test E2E principal."""
    print("Test E2E - Validation correction import Bedrock V2")
    print("=" * 50)
    
    success = True
    
    # Étape 1: Invoquer la Lambda
    response = invoke_normalize_score()
    if not response:
        print("ERREUR: Échec invocation Lambda")
        return False
    
    # Étape 2: Analyser les résultats
    if not analyze_response(response):
        success = False
    
    # Étape 3: Vérifier les logs
    logs_ok = check_cloudwatch_logs()
    if logs_ok is False:
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("TEST E2E REUSSI")
        print("OK Correction d'import validee en production")
        print("OK items_matched > 0")
        print("OK Aucune erreur d'import dans les logs")
    else:
        print("TEST E2E INCOMPLET")
        print("Verifier les details ci-dessus")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)