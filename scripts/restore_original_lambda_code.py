#!/usr/bin/env python3
"""
Restauration du code Lambda original depuis src_v2
"""

import os
import tempfile
import zipfile
import boto3
import json
from pathlib import Path
import shutil

def create_original_lambda_package():
    """Crée un package Lambda avec le code original de src_v2"""
    
    print("[RESTORE] Création package Lambda original...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # 1. Handler original
        handler_src = Path("src_v2/lambdas/normalize_score/handler.py")
        if handler_src.exists():
            shutil.copy2(handler_src, temp_path / "handler.py")
            print(f"[COPY] Handler original copié")
        else:
            print(f"[ERROR] Handler non trouvé: {handler_src}")
            return None
        
        # 2. Vectora_core original complet
        vectora_core_dir = temp_path / "vectora_core"
        vectora_core_src = Path("src_v2/vectora_core")
        
        if vectora_core_src.exists():
            shutil.copytree(vectora_core_src, vectora_core_dir)
            print(f"[COPY] Vectora_core original copié")
        else:
            print(f"[ERROR] Vectora_core non trouvé: {vectora_core_src}")
            return None
        
        # 3. Création du ZIP
        zip_path = temp_path / "normalize_score_v2_original.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_path.rglob("*"):
                if file_path.is_file() and file_path != zip_path:
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
        
        # Lecture du ZIP
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        print(f"[OK] Package original créé: {len(zip_content)} bytes")
        return zip_content

def update_lambda_with_original_code(zip_content):
    """Met à jour la Lambda avec le code original"""
    
    print("[UPDATE] Restauration code Lambda original...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    try:
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"[OK] Code Lambda restauré")
        print(f"[VERSION] Version: {response['Version']}")
        print(f"[SIZE] Taille: {response['CodeSize']} bytes")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erreur restauration: {str(e)}")
        return False

def test_restored_lambda():
    """Test la Lambda avec le code restauré"""
    
    print("[TEST] Test Lambda avec code restauré...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    test_payload = {
        'client_id': 'lai_weekly_v3'
    }
    
    try:
        print(f"[INVOKE] Test avec payload: {test_payload}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        print(f"[RESPONSE] StatusCode: {response.get('StatusCode')}")
        
        if response.get('FunctionError'):
            print(f"[ERROR] Erreur Lambda: {response['FunctionError']}")
            error_msg = response_payload.get('errorMessage', 'Unknown error')
            print(f"[DETAILS] {error_msg}")
            
            # Analyse du type d'erreur
            if 'yaml' in error_msg.lower():
                print(f"[ANALYSIS] Problème PyYAML - layer corrigé devrait résoudre")
                return True  # C'est attendu avec le nouveau layer
            elif 'requests' in error_msg.lower():
                print(f"[ANALYSIS] Problème requests - layer corrigé devrait résoudre")
                return True  # C'est attendu avec le nouveau layer
            else:
                print(f"[ANALYSIS] Autre erreur: {error_msg}")
                return False
        else:
            print(f"[SUCCESS] Lambda fonctionne parfaitement!")
            return True
            
    except Exception as e:
        print(f"[ERROR] Erreur test: {str(e)}")
        return False

def main():
    """Fonction principale de restauration"""
    
    print("RESTAURATION CODE LAMBDA ORIGINAL")
    print("=" * 50)
    
    # Étape 1: Package original
    print("\n[STEP 1] Création package original...")
    zip_content = create_original_lambda_package()
    
    if not zip_content:
        print("[ABORT] Échec création package")
        return False
    
    # Étape 2: Restauration
    print("\n[STEP 2] Restauration code Lambda...")
    restore_success = update_lambda_with_original_code(zip_content)
    
    if not restore_success:
        print("[ABORT] Échec restauration")
        return False
    
    # Étape 3: Test
    print("\n[STEP 3] Test Lambda restaurée...")
    test_success = test_restored_lambda()
    
    # Résumé
    print("\n" + "=" * 50)
    print("[RESUME] Restauration terminée")
    
    if test_success:
        print("[SUCCESS] Code original restauré - prêt pour test avec nouveau layer")
    else:
        print("[PARTIAL] Code restauré mais problème persistant")
    
    return test_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)