#!/usr/bin/env python3
"""
Script de test local pour valider la détection de l'article Pfizer
avec la configuration lai_weekly_v3.1_debug (période étendue).

Usage: python test_lai_v3_1_debug_local.py
"""

import json
import boto3
from datetime import datetime, timedelta
import os
from pathlib import Path

def test_lai_v3_1_debug():
    """Test local de la configuration v3.1_debug avec période étendue"""
    
    print("=" * 80)
    print("TEST LAI WEEKLY v3.1 DEBUG - PERIODE ETENDUE")
    print("=" * 80)
    print()
    
    # Configuration
    client_id = "lai_weekly_v3.1_debug"
    lambda_name = "vectora-inbox-ingest-v2-dev"
    region = "eu-west-3"
    
    print(f"OBJECTIF: Tester si l'article Pfizer du 9 mars 2026 sera detecte")
    print(f"PERIODE: 60 jours (au lieu de 7)")
    print(f"MOTS-CLES ATTENDUS: 'once-monthly', 'subcutaneous'")
    print(f"CLIENT: {client_id}")
    print()
    
    # Payload pour l'invocation
    payload = {
        "client_id": client_id,
        "mode": "test",
        "environment": "dev",
        "force_refresh": True,
        "debug": True,
        "notes": f"Test periode etendue - Article Pfizer 9 mars - {datetime.now().isoformat()}"
    }
    
    print("PAYLOAD:")
    print(json.dumps(payload, indent=2))
    print()
    
    # Vérification de la configuration
    config_path = Path("config/clients/lai_weekly_v3.1_debug.yaml")
    if not config_path.exists():
        print(f"ERREUR: Configuration non trouvee: {config_path}")
        return False
    
    print(f"Configuration trouvee: {config_path}")
    print()
    
    # Test d'invocation
    print("INVOCATION LAMBDA...")
    
    try:
        # Client Lambda
        lambda_client = boto3.client('lambda', region_name=region)
        
        # Invocation
        print(f"   Invocation de {lambda_name}...")
        response = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        # Lecture de la réponse
        response_payload = json.loads(response['Payload'].read())
        
        print(f"Invocation reussie! Status: {response['StatusCode']}")
        print()
        
        # Analyse de la réponse
        print("ANALYSE DE LA REPONSE:")
        print("-" * 40)
        
        if 'run_id' in response_payload:
            run_id = response_payload['run_id']
            print(f"Run ID: {run_id}")
            
            # Sauvegarde de la réponse
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"output/lai_v3.1_debug_test_{timestamp}.json"
            
            os.makedirs("output", exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(response_payload, f, indent=2, ensure_ascii=False)
            
            print(f"Reponse sauvegardee: {output_file}")
            
            # Instructions pour vérifier les résultats
            print()
            print("VERIFICATION DES RESULTATS:")
            print("-" * 40)
            print(f"1. Verifier le dossier: output/runs/{run_id}/")
            print(f"2. Chercher l'article Pfizer dans ingested_items.json")
            print(f"3. Hash cible: sha256:41a2561b3026a6287d28406eb89460ed5a184666b060602b0f3745891a2ff33c")
            print(f"4. Verifier que lai_keyword_filter.passed = true")
            print(f"5. Verifier que lai_keyword_filter.keywords_found contient 'once-monthly'")
            
        else:
            print("Pas de run_id dans la reponse")
            print("Reponse complete:")
            print(json.dumps(response_payload, indent=2, ensure_ascii=False))
        
        return True
        
    except Exception as e:
        print(f"ERREUR lors de l'invocation: {str(e)}")
        print()
        print("ALTERNATIVES:")
        print("1. Verifier les credentials AWS")
        print("2. Verifier le nom de la lambda")
        print("3. Verifier la region")
        print("4. Tester en mode local si disponible")
        return False

def analyze_previous_run():
    """Analyse le run précédent pour comparaison"""
    
    print("=" * 80)
    print("ANALYSE DU RUN PRECEDENT (periode 7 jours)")
    print("=" * 80)
    
    previous_run_path = Path("output/runs/lai_weekly__20260420_184149_2bcc04d5")
    
    if not previous_run_path.exists():
        print("Run precedent non trouve")
        return
    
    # Analyse des items rejetés
    rejected_file = previous_run_path / "rejected_items.json"
    if rejected_file.exists():
        with open(rejected_file, 'r', encoding='utf-8') as f:
            rejected_items = json.load(f)
        
        target_hash = "sha256:41a2561b3026a6287d28406eb89460ed5a184666b060602b0f3745891a2ff33c"
        
        pfizer_article = None
        for item in rejected_items:
            if item.get('content_hash') == target_hash:
                pfizer_article = item
                break
        
        if pfizer_article:
            print("Article Pfizer trouve dans les rejets (periode 7 jours)")
            print(f"   Titre: {pfizer_article['title']}")
            print(f"   Date: {pfizer_article['published_at']}")
            
            filter_analysis = pfizer_article.get('filter_analysis', {})
            period_filter = filter_analysis.get('period_filter', {})
            lai_filter = filter_analysis.get('lai_keyword_filter', {})
            
            print(f"   Filtre periode: {period_filter.get('passed', 'N/A')} (raison: {period_filter.get('reason', 'N/A')})")
            print(f"   Filtre LAI: {lai_filter.get('passed', 'N/A')} (mots-cles: {lai_filter.get('keywords_found', [])})")
            print(f"   Jours d'age: {period_filter.get('days_ago', 'N/A')}")
        else:
            print("Article Pfizer non trouve dans les rejets")
    else:
        print("Fichier rejected_items.json non trouve")

if __name__ == "__main__":
    # Analyse du run précédent
    analyze_previous_run()
    
    # Test avec la nouvelle configuration
    success = test_lai_v3_1_debug()
    
    if success:
        print("\nTest lance avec succes!")
        print("\nPROCHAINES ETAPES:")
        print("1. Attendre la fin du run")
        print("2. Comparer les resultats avec le run precedent")
        print("3. Verifier si l'article Pfizer est maintenant ingere")
    else:
        print("\nEchec du test")