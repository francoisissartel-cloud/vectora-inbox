#!/usr/bin/env python3
"""
Correction rapide du problème PyYAML dans normalize_score_v2
Crée un nouveau layer avec PyYAML et met à jour la Lambda
"""

import os
import subprocess
import tempfile
import zipfile
import boto3
import json
from pathlib import Path

def create_yaml_layer():
    """Crée un layer Lambda avec PyYAML pure Python"""
    
    print("[FIX] Creation du layer PyYAML...")
    
    # Création d'un répertoire temporaire
    with tempfile.TemporaryDirectory() as temp_dir:
        layer_dir = Path(temp_dir) / "python"
        layer_dir.mkdir()
        
        print(f"[INSTALL] Installation PyYAML dans {layer_dir}")
        
        # Installation PyYAML pure Python (sans extensions C)
        cmd = [
            "pip", "install", 
            "--no-binary", "PyYAML",
            "--target", str(layer_dir),
            "PyYAML==6.0.1"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[ERROR] Erreur installation PyYAML: {result.stderr}")
            return None
        
        print(f"[OK] PyYAML installé avec succès")
        
        # Vérification des fichiers installés
        yaml_files = list(layer_dir.rglob("*.py"))
        print(f"[FILES] {len(yaml_files)} fichiers Python trouvés")
        
        # Création du ZIP
        zip_path = Path(temp_dir) / "yaml_layer.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in layer_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)
        
        print(f"[ZIP] Layer créé: {zip_path} ({zip_path.stat().st_size} bytes)")
        
        # Lecture du contenu pour upload
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        return zip_content

def upload_yaml_layer(zip_content):
    """Upload le layer PyYAML sur AWS Lambda"""
    
    print("[UPLOAD] Upload du layer PyYAML...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    
    try:
        response = lambda_client.publish_layer_version(
            LayerName='vectora-inbox-yaml-fix-dev',
            Description='PyYAML pure Python pour correction normalize_score_v2',
            Content={'ZipFile': zip_content},
            CompatibleRuntimes=['python3.11', 'python3.12'],
            CompatibleArchitectures=['x86_64']
        )
        
        layer_arn = response['LayerArn']
        layer_version = response['Version']
        
        print(f"[OK] Layer uploadé: {layer_arn}:{layer_version}")
        
        return f"{layer_arn}:{layer_version}"
        
    except Exception as e:
        print(f"[ERROR] Erreur upload layer: {str(e)}")
        return None

def update_lambda_layers(yaml_layer_arn):
    """Met à jour la Lambda avec le nouveau layer PyYAML"""
    
    print("[UPDATE] Mise à jour Lambda avec layer PyYAML...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    try:
        # Récupération des layers actuels
        config = lambda_client.get_function(FunctionName=function_name)
        current_layers = [layer['Arn'] for layer in config['Configuration'].get('Layers', [])]
        
        print(f"[CURRENT] Layers actuels: {len(current_layers)}")
        for layer in current_layers:
            print(f"  - {layer}")
        
        # Ajout du nouveau layer PyYAML
        new_layers = current_layers + [yaml_layer_arn]
        
        print(f"[NEW] Nouveaux layers: {len(new_layers)}")
        for layer in new_layers:
            print(f"  - {layer}")
        
        # Mise à jour de la Lambda
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Layers=new_layers
        )
        
        print(f"[OK] Lambda mise à jour avec succès")
        print(f"[VERSION] Nouvelle version: {response['Version']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erreur mise à jour Lambda: {str(e)}")
        return False

def test_yaml_import():
    """Test l'import yaml avec un payload minimal"""
    
    print("[TEST] Test import yaml...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    # Payload de test minimal
    test_payload = {
        'client_id': 'lai_weekly_v3',
        'test_mode': True,
        'dry_run': True
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        # Lecture de la réponse
        response_payload = json.loads(response['Payload'].read())
        
        if response.get('FunctionError'):
            print(f"[ERROR] Erreur Lambda: {response['FunctionError']}")
            print(f"[DETAILS] {response_payload}")
            return False
        else:
            print(f"[OK] Test réussi - pas d'erreur import yaml")
            print(f"[RESPONSE] {response_payload}")
            return True
            
    except Exception as e:
        print(f"[ERROR] Erreur test: {str(e)}")
        return False

def main():
    """Fonction principale de correction"""
    
    print("CORRECTION Lambda normalize_score_v2 - Problème PyYAML")
    print("=" * 70)
    
    # Étape 1: Création du layer PyYAML
    print("\n[STEP 1] Création layer PyYAML...")
    zip_content = create_yaml_layer()
    
    if not zip_content:
        print("[ABORT] Échec création layer")
        return False
    
    # Étape 2: Upload du layer
    print("\n[STEP 2] Upload layer sur AWS...")
    yaml_layer_arn = upload_yaml_layer(zip_content)
    
    if not yaml_layer_arn:
        print("[ABORT] Échec upload layer")
        return False
    
    # Étape 3: Mise à jour Lambda
    print("\n[STEP 3] Mise à jour Lambda...")
    update_success = update_lambda_layers(yaml_layer_arn)
    
    if not update_success:
        print("[ABORT] Échec mise à jour Lambda")
        return False
    
    # Étape 4: Test
    print("\n[STEP 4] Test import yaml...")
    test_success = test_yaml_import()
    
    # Résumé
    print("\n" + "=" * 70)
    print("[RESUME] Correction terminée")
    
    if test_success:
        print("[SUCCESS] ✅ Problème PyYAML corrigé avec succès")
        print("[NEXT] Vous pouvez maintenant relancer le test end-to-end:")
        print("  aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \\")
        print("    --payload file://test_normalize_payload.json response_normalize_fixed.json")
    else:
        print("[PARTIAL] ⚠️ Layer créé mais test échoué - investigation supplémentaire nécessaire")
    
    return test_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)