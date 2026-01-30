#!/usr/bin/env python3
"""
Test configuration lai_weekly.yaml (sans v7)
Vérifie que le moteur peut charger et utiliser la nouvelle config
"""

import boto3
import yaml
import sys

def test_config_load():
    """Test chargement config lai_weekly depuis S3"""
    
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    try:
        # Télécharger config
        response = s3.get_object(
            Bucket='vectora-inbox-config-dev',
            Key='clients/lai_weekly.yaml'
        )
        
        config_content = response['Body'].read().decode('utf-8')
        config = yaml.safe_load(config_content)
        
        # Validations
        assert config['client_profile']['client_id'] == 'lai_weekly', "client_id incorrect"
        assert config['client_profile']['version'] == '7.0.0', "version incorrecte"
        assert config['metadata']['config_version'] == '7.0.0', "config_version incorrecte"
        
        print("[OK] Config lai_weekly.yaml chargee avec succes")
        print(f"   client_id: {config['client_profile']['client_id']}")
        print(f"   version: {config['client_profile']['version']}")
        print(f"   config_version: {config['metadata']['config_version']}")
        print(f"   watch_domains: {len(config['watch_domains'])}")
        print(f"   sections: {len(config['newsletter_layout']['sections'])}")
        
        return True
        
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False

if __name__ == "__main__":
    success = test_config_load()
    sys.exit(0 if success else 1)
