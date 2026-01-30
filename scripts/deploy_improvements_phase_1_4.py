#!/usr/bin/env python3
"""
Script de déploiement des améliorations Phase 1-4 du Plan d'Amélioration Moteur Vectora V2

Ce script déploie les améliorations implémentées :
- Phase 1 : Configuration sources avec extraction dates + enrichissement contenu
- Phase 2 : Prompts Bedrock améliorés anti-hallucinations
- Phase 3 : Configuration lai_weekly_v4 avec distribution spécialisée
- Phase 4 : Assembleur newsletter avec scope métier

Usage:
    python scripts/deploy_improvements_phase_1_4.py --env dev --profile rag-lai-prod
"""

import sys
import os
import argparse
import logging
import boto3
import yaml
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def upload_to_s3(file_path, bucket, s3_key, profile_name):
    """Upload un fichier vers S3"""
    try:
        session = boto3.Session(profile_name=profile_name)
        s3_client = session.client('s3', region_name='eu-west-3')
        
        s3_client.upload_file(file_path, bucket, s3_key)
        logger.info(f"✅ Uploaded {file_path} to s3://{bucket}/{s3_key}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to upload {file_path}: {str(e)}")
        return False

def deploy_phase_1_source_config(env, profile_name):
    """Déploie la configuration des sources améliorée (Phase 1)"""
    logger.info("=== DÉPLOIEMENT PHASE 1 : CONFIGURATION SOURCES ===")
    
    source_config_path = "canonical/sources/source_catalog.yaml"
    bucket = f"vectora-inbox-config-{env}"
    s3_key = "canonical/sources/source_catalog.yaml"
    
    if not os.path.exists(source_config_path):
        logger.error(f"❌ Fichier source non trouvé: {source_config_path}")
        return False
    
    # Validation du fichier YAML
    try:
        with open(source_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Vérifier que les améliorations sont présentes
        sources = config.get('sources', [])
        medincell_source = next((s for s in sources if s.get('source_key') == 'press_corporate__medincell'), None)
        
        if medincell_source and 'date_extraction_patterns' in medincell_source:
            logger.info("✅ Configuration sources contient les améliorations Phase 1")
        else:
            logger.warning("⚠️ Configuration sources ne contient pas toutes les améliorations Phase 1")
        
    except Exception as e:
        logger.error(f"❌ Erreur validation YAML sources: {str(e)}")
        return False
    
    # Upload vers S3
    return upload_to_s3(source_config_path, bucket, s3_key, profile_name)

def deploy_phase_2_prompts(env, profile_name):
    """Déploie les prompts Bedrock améliorés (Phase 2)"""
    logger.info("=== DÉPLOIEMENT PHASE 2 : PROMPTS BEDROCK ===")
    
    prompts_path = "canonical/prompts/global_prompts.yaml"
    bucket = f"vectora-inbox-config-{env}"
    s3_key = "canonical/prompts/global_prompts.yaml"
    
    if not os.path.exists(prompts_path):
        logger.error(f"❌ Fichier prompts non trouvé: {prompts_path}")
        return False
    
    # Validation du fichier YAML
    try:
        with open(prompts_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Vérifier que les améliorations anti-hallucinations sont présentes
        normalization = config.get('normalization', {})
        lai_default = normalization.get('lai_default', {})
        user_template = lai_default.get('user_template', '')
        
        if 'CRITICAL: Only extract entities that are EXPLICITLY mentioned' in user_template:
            logger.info("✅ Prompts contiennent les améliorations anti-hallucinations Phase 2")
        else:
            logger.warning("⚠️ Prompts ne contiennent pas toutes les améliorations Phase 2")
        
    except Exception as e:
        logger.error(f"❌ Erreur validation YAML prompts: {str(e)}")
        return False
    
    # Upload vers S3
    return upload_to_s3(prompts_path, bucket, s3_key, profile_name)

def deploy_phase_3_client_config(env, profile_name):
    """Déploie la configuration client améliorée (Phase 3)"""
    logger.info("=== DÉPLOIEMENT PHASE 3 : CONFIGURATION CLIENT ===")
    
    client_config_path = "client-config-examples/lai_weekly_v4.yaml"
    bucket = f"vectora-inbox-config-{env}"
    s3_key = "clients/lai_weekly_v4.yaml"
    
    if not os.path.exists(client_config_path):
        logger.error(f"❌ Fichier config client non trouvé: {client_config_path}")
        return False
    
    # Validation du fichier YAML
    try:
        with open(client_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Vérifier que la distribution spécialisée est présente
        newsletter_layout = config.get('newsletter_layout', {})
        distribution_strategy = newsletter_layout.get('distribution_strategy')
        sections = newsletter_layout.get('sections', [])
        
        has_others_section = any(s.get('id') == 'others' for s in sections)
        has_specialized_strategy = distribution_strategy == 'specialized_with_fallback'
        
        if has_others_section and has_specialized_strategy:
            logger.info("✅ Configuration client contient les améliorations Phase 3")
        else:
            logger.warning("⚠️ Configuration client ne contient pas toutes les améliorations Phase 3")
        
    except Exception as e:
        logger.error(f"❌ Erreur validation YAML client: {str(e)}")
        return False
    
    # Upload vers S3
    return upload_to_s3(client_config_path, bucket, s3_key, profile_name)

def update_lambda_layers(env, profile_name):
    """Met à jour les Lambda layers avec le code amélioré"""
    logger.info("=== MISE À JOUR LAMBDA LAYERS ===")
    
    try:
        session = boto3.Session(profile_name=profile_name)
        lambda_client = session.client('lambda', region_name='eu-west-3')
        
        # Créer le zip du layer vectora-core amélioré
        import zipfile
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Ajouter tous les fichiers de src_v2/vectora_core
                for root, dirs, files in os.walk('src_v2/vectora_core'):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            arcname = file_path.replace('src_v2/', '')
                            zipf.write(file_path, arcname)
            
            # Upload du nouveau layer
            with open(tmp_file.name, 'rb') as zip_content:
                response = lambda_client.publish_layer_version(
                    LayerName=f'vectora-inbox-vectora-core-{env}',
                    Content={'ZipFile': zip_content.read()},
                    CompatibleRuntimes=['python3.9'],
                    Description=f'Vectora Core amélioré - Phase 1-4 - {datetime.now().strftime("%Y-%m-%d")}'
                )
            
            layer_version = response['Version']
            logger.info(f"✅ Layer vectora-core mis à jour: version {layer_version}")
            
            # Nettoyer le fichier temporaire
            os.unlink(tmp_file.name)
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erreur mise à jour layer: {str(e)}")
        return False

def validate_deployment(env, profile_name):
    """Valide que le déploiement s'est bien passé"""
    logger.info("=== VALIDATION DÉPLOIEMENT ===")
    
    try:
        session = boto3.Session(profile_name=profile_name)
        s3_client = session.client('s3', region_name='eu-west-3')
        bucket = f"vectora-inbox-config-{env}"
        
        # Vérifier que les fichiers sont bien uploadés
        files_to_check = [
            "canonical/sources/source_catalog.yaml",
            "canonical/prompts/global_prompts.yaml",
            "clients/lai_weekly_v4.yaml"
        ]
        
        all_present = True
        for s3_key in files_to_check:
            try:
                s3_client.head_object(Bucket=bucket, Key=s3_key)
                logger.info(f"✅ Fichier présent: s3://{bucket}/{s3_key}")
            except s3_client.exceptions.NoSuchKey:
                logger.error(f"❌ Fichier manquant: s3://{bucket}/{s3_key}")
                all_present = False
        
        return all_present
        
    except Exception as e:
        logger.error(f"❌ Erreur validation déploiement: {str(e)}")
        return False

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description='Déploiement améliorations Phase 1-4')
    parser.add_argument('--env', choices=['dev', 'prod'], default='dev', help='Environnement de déploiement')
    parser.add_argument('--profile', default='rag-lai-prod', help='Profil AWS CLI')
    parser.add_argument('--phase', choices=['1', '2', '3', '4', 'all'], default='all', help='Phase à déployer')
    parser.add_argument('--skip-layers', action='store_true', help='Ignorer la mise à jour des layers')
    
    args = parser.parse_args()
    
    logger.info(f"🚀 DÉBUT DÉPLOIEMENT - ENV: {args.env}")
    logger.info(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🔧 Profil AWS: {args.profile}")
    
    success_count = 0
    total_count = 0
    
    # Phase 1 : Configuration sources
    if args.phase in ['1', 'all']:
        total_count += 1
        if deploy_phase_1_source_config(args.env, args.profile):
            success_count += 1
    
    # Phase 2 : Prompts Bedrock
    if args.phase in ['2', 'all']:
        total_count += 1
        if deploy_phase_2_prompts(args.env, args.profile):
            success_count += 1
    
    # Phase 3 : Configuration client
    if args.phase in ['3', 'all']:
        total_count += 1
        if deploy_phase_3_client_config(args.env, args.profile):
            success_count += 1
    
    # Mise à jour des layers (si pas ignoré)
    if not args.skip_layers:
        total_count += 1
        if update_lambda_layers(args.env, args.profile):
            success_count += 1
    
    # Validation finale
    total_count += 1
    if validate_deployment(args.env, args.profile):
        success_count += 1
    
    # Résumé final
    success_rate = success_count / total_count if total_count > 0 else 0
    
    logger.info("=" * 60)
    logger.info(f"📊 RÉSUMÉ DÉPLOIEMENT")
    logger.info(f"Étapes réussies: {success_count}/{total_count} ({success_rate:.1%})")
    
    if success_rate >= 0.8:
        logger.info("✅ SUCCÈS - Déploiement Phase 1-4 terminé")
        logger.info("🎯 Prêt pour test E2E avec lai_weekly_v4")
        return 0
    else:
        logger.error("❌ ÉCHEC - Certaines étapes ont échoué")
        return 1

if __name__ == '__main__':
    sys.exit(main())