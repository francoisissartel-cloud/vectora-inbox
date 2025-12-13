#!/usr/bin/env python3
"""
Script de déploiement simplifié des améliorations sur AWS.
"""

import json
import yaml
import boto3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def deploy_to_aws():
    """Déploie les améliorations sur AWS."""
    
    project_root = Path(__file__).parent
    canonical_path = project_root / "canonical"
    env = "dev"
    
    # Configuration AWS
    s3_client = boto3.client('s3')
    config_bucket = f"vectora-inbox-config-{env}"
    
    logger.info(f"=== DÉPLOIEMENT AWS AMÉLIORATIONS (env: {env}) ===")
    
    # Sauvegarde
    backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_prefix = f"backups/pre_improvements_{backup_timestamp}/"
    
    try:
        # Lister et sauvegarder la configuration existante
        response = s3_client.list_objects_v2(Bucket=config_bucket)
        if 'Contents' in response:
            for obj in response['Contents']:
                key = obj['Key']
                if not key.startswith('backups/'):
                    copy_source = {'Bucket': config_bucket, 'Key': key}
                    backup_key = backup_prefix + key
                    s3_client.copy_object(CopySource=copy_source, Bucket=config_bucket, Key=backup_key)
        
        logger.info(f"✅ Configuration sauvegardée: {backup_prefix}")
        
    except Exception as e:
        logger.warning(f"⚠️ Erreur sauvegarde: {str(e)}")
    
    # Déploiement des fichiers de configuration
    files_to_deploy = {
        'scopes/technology_scopes.yaml': 'canonical/scopes/technology_scopes.yaml',
        'scopes/trademark_scopes.yaml': 'canonical/scopes/trademark_scopes.yaml', 
        'scopes/exclusion_scopes.yaml': 'canonical/scopes/exclusion_scopes.yaml',
        'scoring/scoring_rules.yaml': 'canonical/scoring/scoring_rules.yaml',
        'ingestion/ingestion_profiles.yaml': 'canonical/ingestion/ingestion_profiles.yaml',
        'matching/domain_matching_rules.yaml': 'canonical/matching/domain_matching_rules.yaml'
    }
    
    deployment_results = {}
    
    for local_path, s3_key in files_to_deploy.items():
        try:
            local_file_path = canonical_path / local_path
            
            if local_file_path.exists():
                # Valider YAML
                with open(local_file_path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                
                # Uploader vers S3
                with open(local_file_path, 'rb') as f:
                    s3_client.put_object(
                        Bucket=config_bucket,
                        Key=s3_key,
                        Body=f,
                        ContentType='application/x-yaml'
                    )
                
                deployment_results[s3_key] = True
                logger.info(f"✅ Déployé: {local_path}")
            else:
                deployment_results[s3_key] = False
                logger.error(f"❌ Fichier manquant: {local_path}")
                
        except Exception as e:
            deployment_results[s3_key] = False
            logger.error(f"❌ Erreur {local_path}: {str(e)}")
    
    # Déploiement code Lambda
    lambda_files = {
        'src/vectora_core/matching/matcher.py': 'lambda-code/vectora_core/matching/matcher.py',
        'src/vectora_core/scoring/scorer.py': 'lambda-code/vectora_core/scoring/scorer.py'
    }
    
    for local_path, s3_key in lambda_files.items():
        try:
            local_file_path = project_root / local_path
            
            if local_file_path.exists():
                with open(local_file_path, 'rb') as f:
                    s3_client.put_object(
                        Bucket=config_bucket,
                        Key=s3_key,
                        Body=f,
                        ContentType='text/x-python'
                    )
                
                deployment_results[s3_key] = True
                logger.info(f"✅ Déployé: {local_path}")
            else:
                deployment_results[s3_key] = False
                logger.error(f"❌ Fichier manquant: {local_path}")
                
        except Exception as e:
            deployment_results[s3_key] = False
            logger.error(f"❌ Erreur {local_path}: {str(e)}")
    
    # Validation
    try:
        response = s3_client.get_object(Bucket=config_bucket, Key='canonical/scopes/technology_scopes.yaml')
        content = response['Body'].read().decode('utf-8')
        yaml_content = yaml.safe_load(content)
        
        lai_keywords = yaml_content.get('lai_keywords', {})
        tech_terms = lai_keywords.get('technology_terms_high_precision', [])
        
        improvements_present = {
            'pharmashell_present': 'PharmaShell®' in tech_terms,
            'siliashell_present': 'SiliaShell®' in tech_terms,
            'bepo_present': 'BEPO®' in tech_terms,
            'lai_acronym_present': 'LAI' in tech_terms
        }
        
        if all(improvements_present.values()):
            logger.info("✅ Toutes les améliorations technology_scopes sont présentes")
        else:
            logger.warning(f"⚠️ Certaines améliorations manquent: {improvements_present}")
            
    except Exception as e:
        logger.error(f"❌ Erreur validation: {str(e)}")
    
    # Métadonnées de déploiement
    metadata = {
        'deployment_info': {
            'timestamp': datetime.now().isoformat(),
            'environment': env,
            'improvement_version': 'phase_1_to_4_complete',
            'backup_location': backup_prefix
        },
        'deployment_results': deployment_results,
        'overall_success': all(deployment_results.values())
    }
    
    # Sauvegarder métadonnées
    metadata_key = f"deployments/improvements_{backup_timestamp}_metadata.json"
    try:
        s3_client.put_object(
            Bucket=config_bucket,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2, ensure_ascii=False),
            ContentType='application/json'
        )
        logger.info(f"✅ Métadonnées sauvegardées: {metadata_key}")
    except Exception as e:
        logger.error(f"❌ Erreur métadonnées: {str(e)}")
    
    # Résumé
    success_count = sum(1 for success in deployment_results.values() if success)
    total_count = len(deployment_results)
    
    logger.info(f"\n=== RÉSUMÉ DÉPLOIEMENT ===")
    logger.info(f"Fichiers déployés: {success_count}/{total_count}")
    logger.info(f"Status: {'SUCCESS' if metadata['overall_success'] else 'PARTIAL_FAILURE'}")
    
    if metadata['overall_success']:
        logger.info("🎉 Déploiement réussi ! Les améliorations sont actives sur AWS.")
        logger.info("\n=== PROCHAINES ÉTAPES ===")
        logger.info("✅ Exécuter un test complet avec le client lai_weekly_v2")
        logger.info("📊 Générer une newsletter et comparer avec les précédentes")
        logger.info("🎯 Valider que les cas critiques (Nanexa/Moderna, UZEDY) sont inclus")
        logger.info("🚫 Confirmer l'exclusion du bruit (HR DelSiTech, Finance MedinCell)")
        return 0
    else:
        logger.error("❌ Déploiement partiel ou échoué")
        return 1

if __name__ == "__main__":
    exit(deploy_to_aws())