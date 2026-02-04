#!/usr/bin/env python3
"""
Vérifie la configuration SSO AWS et affiche les durées de session
"""

import json
import subprocess
from pathlib import Path

def get_aws_config():
    """Lit la config AWS"""
    config_file = Path.home() / ".aws" / "config"
    
    if not config_file.exists():
        print(f"[ERREUR] Fichier config non trouve: {config_file}")
        return None
    
    print(f"Configuration AWS: {config_file}\n")
    
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Extraire la section rag-lai-prod
    lines = content.split('\n')
    in_profile = False
    profile_config = {}
    
    for line in lines:
        if '[profile rag-lai-prod]' in line:
            in_profile = True
            continue
        
        if in_profile:
            if line.startswith('['):
                break
            
            if '=' in line:
                key, value = line.split('=', 1)
                profile_config[key.strip()] = value.strip()
    
    return profile_config

def check_role_duration():
    """Vérifie la durée max du rôle IAM"""
    cmd = "aws iam get-role --role-name AWSReservedSSO_AdministratorAccess_* --profile rag-lai-prod --region eu-west-3 2>&1"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            max_duration = data['Role'].get('MaxSessionDuration', 'N/A')
            return max_duration
        except:
            return None
    return None

def main():
    print("="*60)
    print("CONFIGURATION SSO AWS - rag-lai-prod")
    print("="*60)
    print()
    
    # Config locale
    config = get_aws_config()
    
    if config:
        print("Configuration locale:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        print()
    
    # Durée de session
    print("Durees de session:")
    print("  - Token SSO: 1-8 heures (configure par votre org)")
    print("  - Credentials temporaires: 1-12 heures (max)")
    print("  - Session 30 jours: NON POSSIBLE avec SSO")
    print()
    
    print("="*60)
    print("RECOMMANDATIONS")
    print("="*60)
    print()
    print("1. Utiliser scripts/renew_sso.bat avant chaque session")
    print("2. Configurer un alias shell:")
    print("   alias aws-login='aws sso login --profile rag-lai-prod'")
    print()
    print("3. Pour sessions longues, demander a votre admin AWS:")
    print("   - Augmenter MaxSessionDuration du role IAM (max 12h)")
    print("   - Configurer session_duration dans ~/.aws/config")
    print()

if __name__ == "__main__":
    main()
