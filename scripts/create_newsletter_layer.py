#!/usr/bin/env python3
"""
Script pour créer un layer minimal avec PyYAML pour la Lambda newsletter-v2
"""
import os
import sys
import subprocess
import zipfile
import boto3
from datetime import datetime

def create_minimal_layer():
    """Crée un layer minimal avec PyYAML"""
    
    print("[*] Creating minimal layer with PyYAML...")
    
    # Répertoire temporaire
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    temp_dir = f"temp_layer_{timestamp}"
    python_dir = os.path.join(temp_dir, "python")
    
    try:
        # Créer la structure
        os.makedirs(python_dir, exist_ok=True)
        
        # Installer les dépendances dans le répertoire python/
        print("[+] Installing dependencies...")
        dependencies = [
            "PyYAML==6.0.1",
            "requests==2.31.0",
            "urllib3<2.0",  # Compatibilité avec requests
            "certifi",
            "charset-normalizer",
            "idna"
        ]
        
        for dep in dependencies:
            print(f"    Installing {dep}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                dep, 
                "--target", python_dir,
                "--no-deps"
            ], check=True)
        
        # Créer le ZIP
        layer_zip = f"newsletter-layer-{timestamp}.zip"
        print(f"[+] Creating layer ZIP: {layer_zip}")
        
        with zipfile.ZipFile(layer_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arc_path)
        
        # Nettoyer
        import shutil
        shutil.rmtree(temp_dir)
        
        print(f"[SUCCESS] Layer created: {layer_zip}")
        return layer_zip
        
    except Exception as e:
        print(f"[ERROR] Failed to create layer: {str(e)}")
        return None

def upload_layer_to_aws(layer_zip):
    """Upload le layer vers AWS"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        print(f"[+] Uploading layer to AWS...")
        
        with open(layer_zip, 'rb') as f:
            zip_content = f.read()
        
        response = lambda_client.publish_layer_version(
            LayerName='newsletter-v2-deps',
            Description='Complete dependencies for newsletter-v2 Lambda (PyYAML, requests, etc.)',
            Content={'ZipFile': zip_content},
            CompatibleRuntimes=['python3.11'],
            CompatibleArchitectures=['x86_64']
        )
        
        layer_arn = response['LayerVersionArn']
        print(f"[SUCCESS] Layer uploaded: {layer_arn}")
        
        # Nettoyer le fichier local
        os.remove(layer_zip)
        
        return layer_arn
        
    except Exception as e:
        print(f"[ERROR] Failed to upload layer: {str(e)}")
        return None

def add_layer_to_lambda(layer_arn):
    """Ajoute le layer à la Lambda"""
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    function_name = 'vectora-inbox-newsletter-v2'
    
    try:
        print(f"[+] Adding layer to Lambda...")
        
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Layers=[layer_arn]
        )
        
        print(f"[SUCCESS] Layer added to Lambda")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to add layer to Lambda: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    
    print("="*60)
    print("[CREATE AND DEPLOY LAYER]")
    print("="*60)
    
    # Étape 1: Créer le layer
    layer_zip = create_minimal_layer()
    if not layer_zip:
        return False
    
    # Étape 2: Upload vers AWS
    layer_arn = upload_layer_to_aws(layer_zip)
    if not layer_arn:
        return False
    
    # Étape 3: Ajouter à la Lambda
    success = add_layer_to_lambda(layer_arn)
    
    if success:
        print("\n[SUCCESS] Layer configuration completed!")
        print(f"[+] Layer ARN: {layer_arn}")
        print("[INFO] Lambda should now have PyYAML available")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)