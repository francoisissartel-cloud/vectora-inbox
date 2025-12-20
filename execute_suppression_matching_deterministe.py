#!/usr/bin/env python3
"""
Suppression radicale du matching déterministe.
"""

import os
import subprocess
import json
import boto3
import re

def phase1_analyse():
    """Phase 1: Analyse et préparation."""
    print("PHASE 1: ANALYSE ET PREPARATION")
    
    target_file = "src_v2/vectora_core/normalization/__init__.py"
    if not os.path.exists(target_file):
        print(f"ERREUR: {target_file} non trouvé")
        return False
    
    # Vérifier présence du code à supprimer
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "from . import normalizer, matcher, scorer" not in content:
        print("OK Import matcher deja supprime")
    else:
        print("WARN Import matcher trouve - a supprimer")
    
    if "matcher.match_items_to_domains" not in content:
        print("OK Appel matcher deja supprime")
    else:
        print("WARN Appel matcher trouve - a supprimer")
    
    if "Architecture Bedrock-Only Pure" in content:
        print("OK Architecture Bedrock-Only Pure deja implementee")
    else:
        print("WARN Architecture Bedrock-Only Pure a implementer")
    
    # Vérifier AWS
    try:
        session = boto3.Session(profile_name="rag-lai-prod")
        lambda_client = session.client('lambda', region_name="eu-west-3")
        lambda_client.get_function(FunctionName="vectora-inbox-normalize-score-v2-dev")
        print("OK Environnement AWS accessible")
    except Exception as e:
        print(f"ERROR Erreur AWS: {e}")
        return False
    
    print("OK Phase 1 terminee")
    return True

def phase3_validation():
    """Phase 3: Validation locale."""
    print("PHASE 3: VALIDATION LOCALE")
    
    target_file = "src_v2/vectora_core/normalization/__init__.py"
    
    # Test d'import
    try:
        import sys
        sys.path.insert(0, '.')
        from src_v2.vectora_core.normalization import run_normalize_score_for_client
        print("OK Import reussi")
    except Exception as e:
        print(f"ERROR Erreur import: {e}")
        return False
    
    # Vérifier suppression complète
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "matcher" in content:
        print("ERROR References a matcher encore presentes")
        return False
    else:
        print("OK Aucune reference a matcher trouvee")
    
    print("OK Phase 3 terminee")
    return True

def phase4_deploiement():
    """Phase 4: Déploiement AWS."""
    print("PHASE 4: DEPLOIEMENT AWS")
    
    try:
        # Création package layer
        print("Création package layer...")
        
        # Créer le répertoire layer_build s'il n'existe pas
        if not os.path.exists("layer_build"):
            os.makedirs("layer_build")
        
        # Supprimer et recréer vectora_core dans layer_build
        vectora_core_path = "layer_build/vectora_core"
        if os.path.exists(vectora_core_path):
            subprocess.run([
                "powershell", "-Command",
                f"Remove-Item '{vectora_core_path}' -Recurse -Force"
            ], check=True)
        
        # Copier src_v2/vectora_core vers layer_build/vectora_core
        subprocess.run([
            "powershell", "-Command",
            f"Copy-Item -Path 'src_v2\\vectora_core' -Destination 'layer_build\\vectora_core' -Recurse"
        ], check=True)
        
        # Créer le zip
        zip_name = "vectora-core-matching-supprime.zip"
        if os.path.exists(zip_name):
            os.remove(zip_name)
            
        subprocess.run([
            "powershell", "-Command",
            f"Compress-Archive -Path 'layer_build\\vectora_core' -DestinationPath '{zip_name}' -Force"
        ], check=True)
        
        print(f"OK Package layer cree: {zip_name}")
        
        # Publication layer
        print("Publication layer...")
        session = boto3.Session(profile_name="rag-lai-prod")
        lambda_client = session.client('lambda', region_name="eu-west-3")
        
        with open(zip_name, 'rb') as f:
            response = lambda_client.publish_layer_version(
                LayerName='vectora-inbox-vectora-core-dev',
                Content={'ZipFile': f.read()}
            )
        
        new_version = response['Version']
        print(f"OK Layer publie: version {new_version}")
        
        # Mise a jour Lambda
        print("Mise a jour Lambda...")
        lambda_client.update_function_configuration(
            FunctionName='vectora-inbox-normalize-score-v2-dev',
            Layers=[
                f'arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:{new_version}',
                'arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:3'
            ]
        )
        
        print("OK Lambda mise a jour")
        print("OK Phase 4 terminee")
        return True
        
    except Exception as e:
        print(f"ERROR Erreur deploiement: {e}")
        return False

def phase5_tests():
    """Phase 5: Tests données réelles."""
    print("PHASE 5: TESTS DONNEES REELLES")
    
    try:
        session = boto3.Session(profile_name="rag-lai-prod")
        lambda_client = session.client('lambda', region_name="eu-west-3")
        
        # Invocation Lambda
        print("Invocation Lambda...")
        payload = {"client_id": "lai_weekly_v3", "force_reprocess": True}
        
        response = lambda_client.invoke(
            FunctionName='vectora-inbox-normalize-score-v2-dev',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if result.get('statusCode') == 200:
            body = result.get('body', {})
            stats = body.get('statistics', {})
            items_matched = stats.get('items_matched', 0)
            items_total = stats.get('items_input', 0)
            
            print(f"OK Lambda executee avec succes")
            print(f"   Items traites: {items_total}")
            print(f"   Items matches: {items_matched}")
            
            if items_matched > 0:
                matching_rate = (items_matched / items_total * 100) if items_total > 0 else 0
                print(f"   Taux de matching: {matching_rate:.1f}%")
                print("SUPPRESSION REUSSIE - MATCHING BEDROCK FONCTIONNEL!")
                
                # Sauvegarder la reponse pour analyse
                with open('response.json', 'w') as f:
                    json.dump(result, f, indent=2)
                print("   Reponse sauvegardee dans response.json")
                
                return True
            else:
                print("WARN Aucun item matche - investigation requise")
                # Sauvegarder quand meme pour debug
                with open('response_debug.json', 'w') as f:
                    json.dump(result, f, indent=2)
                return False
        else:
            print(f"ERROR Erreur Lambda: {result}")
            with open('response_error.json', 'w') as f:
                json.dump(result, f, indent=2)
            return False
            
    except Exception as e:
        print(f"ERROR Erreur tests: {e}")
        return False

def main():
    """Exécution complète du plan."""
    print("SUPPRESSION RADICALE DU MATCHING DETERMINISTE")
    print("=" * 60)
    
    phases = [
        ("Phase 1 - Analyse", phase1_analyse),
        ("Phase 3 - Validation", phase3_validation),
        ("Phase 4 - Déploiement", phase4_deploiement),
        ("Phase 5 - Tests", phase5_tests)
    ]
    
    for phase_name, phase_func in phases:
        print(f"\n{phase_name}...")
        if not phase_func():
            print(f"ERROR {phase_name} echouee - arret")
            return False
    
    print("\n" + "=" * 60)
    print("SUPPRESSION RADICALE REUSSIE")
    print("Matching deterministe supprime - Matching Bedrock fonctionnel!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)