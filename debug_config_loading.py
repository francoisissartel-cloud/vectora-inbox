#!/usr/bin/env python3
"""
Debug du chargement de configuration pour identifier pourquoi bedrock_only n'est pas pris en compte.
"""

import yaml
import boto3
import json

def test_config_loading():
    """Test du chargement de configuration comme le fait la Lambda."""
    print("=== DEBUG CHARGEMENT CONFIGURATION ===")
    
    try:
        # Simulation du chargement comme dans config_loader.py
        session = boto3.Session(profile_name="rag-lai-prod")
        s3 = session.client('s3', region_name="eu-west-3")
        
        # Chargement depuis S3
        response = s3.get_object(
            Bucket='vectora-inbox-config-dev',
            Key='clients/lai_weekly_v3.yaml'
        )
        
        config_content = response['Body'].read().decode('utf-8')
        client_config = yaml.safe_load(config_content)
        
        print("Configuration chargée depuis S3:")
        print(f"  Taille: {len(config_content)} caractères")
        
        # Test de la condition exacte du code
        matching_config = client_config.get('matching_config', {})
        bedrock_only = matching_config.get('bedrock_only', False)
        
        print(f"\nTest condition exacte:")
        print(f"  client_config.get('matching_config', {{}}) = {matching_config}")
        print(f"  matching_config.get('bedrock_only', False) = {bedrock_only}")
        print(f"  Type de bedrock_only: {type(bedrock_only)}")
        
        # Test de la condition complète
        condition_result = client_config.get('matching_config', {}).get('bedrock_only', False)
        print(f"\nCondition complète:")
        print(f"  client_config.get('matching_config', {{}}).get('bedrock_only', False) = {condition_result}")
        print(f"  Évaluation booléenne: {bool(condition_result)}")
        
        # Vérification structure complète matching_config
        print(f"\nStructure matching_config complète:")
        for key, value in matching_config.items():
            print(f"  {key}: {value} (type: {type(value)})")
        
        # Test avec différentes variations
        print(f"\nTests variations:")
        print(f"  bedrock_only == True: {bedrock_only == True}")
        print(f"  bedrock_only is True: {bedrock_only is True}")
        print(f"  bool(bedrock_only): {bool(bedrock_only)}")
        
        return condition_result
        
    except Exception as e:
        print(f"Erreur: {e}")
        return False

def test_local_config():
    """Test de la configuration locale pour comparaison."""
    print("\n=== TEST CONFIGURATION LOCALE ===")
    
    try:
        with open('lai_weekly_v3.yaml', 'r', encoding='utf-8') as f:
            client_config = yaml.safe_load(f)
        
        matching_config = client_config.get('matching_config', {})
        bedrock_only = matching_config.get('bedrock_only', False)
        
        print(f"Configuration locale:")
        print(f"  bedrock_only: {bedrock_only} (type: {type(bedrock_only)})")
        
        condition_result = client_config.get('matching_config', {}).get('bedrock_only', False)
        print(f"  Condition: {condition_result}")
        
        return condition_result
        
    except Exception as e:
        print(f"Erreur: {e}")
        return False

def create_test_payload():
    """Créer un payload de test pour invoquer la Lambda avec debug."""
    print("\n=== CRÉATION PAYLOAD TEST DEBUG ===")
    
    payload = {
        "client_id": "lai_weekly_v3",
        "force_reprocess": True,
        "scoring_mode": "balanced",
        "debug_config": True  # Flag pour activer debug si supporté
    }
    
    print(f"Payload de test: {json.dumps(payload, indent=2)}")
    
    # Sauvegarder pour utilisation
    with open('debug_payload.json', 'w') as f:
        json.dump(payload, f, indent=2)
    
    print("Payload sauvegardé dans debug_payload.json")
    
    return payload

def check_yaml_parsing():
    """Vérifier le parsing YAML pour détecter des problèmes."""
    print("\n=== VÉRIFICATION PARSING YAML ===")
    
    try:
        # Test parsing local
        with open('lai_weekly_v3.yaml', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Recherche de la section matching_config
        lines = content.split('\n')
        in_matching_config = False
        matching_config_lines = []
        
        for i, line in enumerate(lines):
            if 'matching_config:' in line:
                in_matching_config = True
                matching_config_lines.append(f"{i+1}: {line}")
            elif in_matching_config:
                if line.startswith('  ') or line.strip() == '':
                    matching_config_lines.append(f"{i+1}: {line}")
                elif line.strip() and not line.startswith(' '):
                    break
        
        print("Section matching_config dans le fichier:")
        for line in matching_config_lines[:10]:  # Premières 10 lignes
            print(f"  {line}")
        
        # Test parsing YAML
        config = yaml.safe_load(content)
        bedrock_only = config.get('matching_config', {}).get('bedrock_only')
        
        print(f"\nRésultat parsing:")
        print(f"  bedrock_only trouvé: {bedrock_only}")
        print(f"  Type: {type(bedrock_only)}")
        
        return bedrock_only
        
    except Exception as e:
        print(f"Erreur parsing: {e}")
        return None

if __name__ == "__main__":
    print("DEBUG CONFIGURATION BEDROCK_ONLY")
    print("=" * 50)
    
    # Test 1: Configuration locale
    local_result = test_local_config()
    
    # Test 2: Configuration S3
    s3_result = test_config_loading()
    
    # Test 3: Parsing YAML
    yaml_result = check_yaml_parsing()
    
    # Test 4: Payload debug
    payload = create_test_payload()
    
    # Résumé
    print("\n" + "=" * 50)
    print("RÉSUMÉ DEBUG:")
    print(f"  Configuration locale bedrock_only: {local_result}")
    print(f"  Configuration S3 bedrock_only: {s3_result}")
    print(f"  Parsing YAML bedrock_only: {yaml_result}")
    
    if local_result == s3_result == yaml_result == True:
        print("\n✅ Configuration cohérente - problème ailleurs")
        print("   Vérifier le code dans le layer ou la logique de chargement")
    elif s3_result != local_result:
        print("\n❌ Incohérence local/S3 - problème d'upload")
    else:
        print("\n❌ Problème de configuration détecté")
    
    print(f"\nProchaine étape: Tester avec debug_payload.json")