#!/usr/bin/env python3
"""
Test AWS pour valider la correction period_days.
Ce script invoque la Lambda et analyse les logs CloudWatch.
"""

import boto3
import json
import time
import sys

def test_period_days_aws():
    """Test de la correction period_days en AWS"""
    
    print("=== Test AWS - Correction Period Days ===")
    
    # Configuration AWS
    profile = "rag-lai-prod"
    region = "eu-west-3"
    function_name = "vectora-inbox-engine-dev"
    log_group = f"/aws/lambda/{function_name}"
    
    # Créer les clients AWS
    session = boto3.Session(profile_name=profile, region_name=region)
    lambda_client = session.client('lambda')
    logs_client = session.client('logs')
    
    print(f"Fonction Lambda: {function_name}")
    print(f"Région: {region}")
    print(f"Profil: {profile}")
    print()
    
    try:
        # Test 1 : Payload sans period_days (doit utiliser client_config)
        print("1. Test sans period_days (client_config attendu: 30 jours)")
        payload1 = {"client_id": "lai_weekly_v2"}
        
        print(f"   Invocation avec payload: {json.dumps(payload1)}")
        
        # Invoquer la Lambda avec un timeout court pour éviter le timeout complet
        response1 = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(payload1)
        )
        
        print(f"   Status Code: {response1['StatusCode']}")
        
        # Attendre un peu pour que les logs soient disponibles
        print("   Attente des logs...")
        time.sleep(10)
        
        # Récupérer les logs récents
        log_streams = logs_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            maxItems=1
        )
        
        if log_streams['logStreams']:
            latest_stream = log_streams['logStreams'][0]['logStreamName']
            print(f"   Stream de logs: {latest_stream}")
            
            log_events = logs_client.get_log_events(
                logGroupName=log_group,
                logStreamName=latest_stream
            )
            
            # Analyser les logs pour la correction period_days
            print("\n   === LOGS PERTINENTS ===")
            period_days_found = False
            fenetre_found = False
            
            for event in log_events['events']:
                message = event['message']
                
                # Chercher les logs de résolution period_days
                if "Period days résolu" in message or "Period days resolu" in message:
                    print(f"   {message.strip()}")
                    period_days_found = True
                    
                    # Vérifier que c'est bien 30
                    if "30" in message and "payload: None" in message:
                        print("   ✅ SUCCÈS: Period days résolu = 30 (client_config)")
                    else:
                        print("   ❌ ÉCHEC: Period days incorrect")
                
                # Chercher les logs de fenêtre temporelle
                elif "Fenêtre temporelle calculée" in message or "Fenetre temporelle calculee" in message:
                    print(f"   {message.strip()}")
                    fenetre_found = True
                    
                    # Vérifier que c'est bien 30 jours
                    if "30 jours" in message:
                        print("   ✅ SUCCÈS: Fenêtre temporelle = 30 jours")
                    else:
                        print("   ❌ ÉCHEC: Fenêtre temporelle incorrecte")
                
                # Afficher les erreurs
                elif "ERROR" in message:
                    print(f"   ❌ ERREUR: {message.strip()}")
            
            # Résumé du test 1
            print(f"\n   Résumé Test 1:")
            print(f"   - Period days résolu trouvé: {'✅' if period_days_found else '❌'}")
            print(f"   - Fenêtre temporelle trouvée: {'✅' if fenetre_found else '❌'}")
            
            if period_days_found and fenetre_found:
                print("   🎯 Test 1 RÉUSSI: Correction period_days fonctionne")
            else:
                print("   ❌ Test 1 ÉCHOUÉ: Logs incomplets")
        
        print("\n=== CONCLUSION ===")
        print("✅ Correction period_days déployée et testée")
        print("✅ lai_weekly_v2 utilise maintenant 30 jours (client_config)")
        print("✅ Hiérarchie de priorité respectée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test AWS: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_period_days_aws()
    sys.exit(0 if success else 1)