#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de création et packaging de la Lambda newsletter-v2
Phase 4 du plan d'implémentation newsletter V2
"""
import os
import sys
import shutil
import zipfile
from datetime import datetime

# Fix pour Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def create_newsletter_v2_lambda():
    """Crée et package la Lambda newsletter-v2"""
    
    print("[*] Creating newsletter-v2 Lambda package...")
    
    # Configuration
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    package_name = f"newsletter-v2-{timestamp}.zip"
    temp_dir = f"temp_newsletter_v2_{timestamp}"
    
    # Chemins
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_dir = os.path.join(root_dir, "src_v2")
    lambda_dir = os.path.join(src_dir, "lambdas", "newsletter")
    output_dir = os.path.join(root_dir, "output", "lambda_packages")
    
    try:
        # 1. Création du répertoire temporaire
        print(f"[+] Creating temporary directory: {temp_dir}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 2. Copie du handler Lambda
        print("[+] Copying Lambda handler...")
        handler_src = os.path.join(lambda_dir, "handler.py")
        handler_dst = os.path.join(temp_dir, "handler.py")
        shutil.copy2(handler_src, handler_dst)
        
        # 3. Copie du module vectora_core complet
        print("[+] Copying vectora_core module...")
        vectora_core_src = os.path.join(src_dir, "vectora_core")
        vectora_core_dst = os.path.join(temp_dir, "vectora_core")
        shutil.copytree(vectora_core_src, vectora_core_dst)
        
        # 4. Création du package ZIP
        print(f"[+] Creating ZIP package: {package_name}")
        os.makedirs(output_dir, exist_ok=True)
        package_path = os.path.join(output_dir, package_name)
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Ajout du handler
            zipf.write(handler_dst, "handler.py")
            
            # Ajout récursif de vectora_core
            for root, dirs, files in os.walk(vectora_core_dst):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arc_path)
        
        # 5. Nettoyage
        print("[+] Cleaning up temporary files...")
        shutil.rmtree(temp_dir)
        
        # 6. Vérification du package
        package_size = os.path.getsize(package_path) / (1024 * 1024)  # MB
        print(f"[SUCCESS] Package created successfully!")
        print(f"   Location: {package_path}")
        print(f"   Size: {package_size:.2f} MB")
        
        # 7. Affichage du contenu
        print("[+] Package contents:")
        with zipfile.ZipFile(package_path, 'r') as zipf:
            for name in sorted(zipf.namelist())[:10]:  # Premiers 10 fichiers
                print(f"   - {name}")
            if len(zipf.namelist()) > 10:
                print(f"   ... and {len(zipf.namelist()) - 10} more files")
        
        return package_path
        
    except Exception as e:
        print(f"[ERROR] Error creating package: {str(e)}")
        # Nettoyage en cas d'erreur
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise

def print_deployment_instructions(package_path):
    """Affiche les instructions de déploiement"""
    
    print("\n" + "="*60)
    print("[DEPLOYMENT INSTRUCTIONS]")
    print("="*60)
    
    print(f"""
[LAMBDA CONFIGURATION]
   Function Name: vectora-inbox-newsletter-v2
   Runtime: python3.11
   Handler: handler.lambda_handler
   Timeout: 15 minutes (900 seconds)
   Memory: 1024 MB

[PACKAGE LOCATION]
   {package_path}

[ENVIRONMENT VARIABLES]
   CONFIG_BUCKET=vectora-inbox-config-dev
   DATA_BUCKET=vectora-inbox-data-dev
   NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev
   BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
   BEDROCK_REGION=us-east-1

[LAYERS REQUIRED]
   - vectora-common-deps (PyYAML, requests, boto3)
   - Pas de layer vectora-core (inclus dans le package)

[AWS CLI DEPLOYMENT]
   aws lambda create-function \\
     --function-name vectora-inbox-newsletter-v2 \\
     --runtime python3.11 \\
     --role arn:aws:iam::ACCOUNT:role/vectora-inbox-lambda-role \\
     --handler handler.lambda_handler \\
     --zip-file fileb://{package_path} \\
     --timeout 900 \\
     --memory-size 1024 \\
     --environment Variables='{{
       "CONFIG_BUCKET":"vectora-inbox-config-dev",
       "DATA_BUCKET":"vectora-inbox-data-dev", 
       "NEWSLETTERS_BUCKET":"vectora-inbox-newsletters-dev",
       "BEDROCK_MODEL_ID":"anthropic.claude-3-sonnet-20240229-v1:0",
       "BEDROCK_REGION":"us-east-1"
     }}'

[TEST PAYLOAD]
   {{
     "client_id": "lai_weekly_v4",
     "target_date": "2025-12-21",
     "force_regenerate": false
   }}
""")

def main():
    """Point d'entrée principal"""
    try:
        package_path = create_newsletter_v2_lambda()
        print_deployment_instructions(package_path)
        
        print("\n[SUCCESS] Newsletter V2 Lambda package created successfully!")
        print("[NEXT] Ready for Phase 5 - AWS Deployment")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create newsletter V2 Lambda: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()