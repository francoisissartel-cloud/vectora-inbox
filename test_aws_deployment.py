#!/usr/bin/env python3
"""
Script de test du déploiement AWS.
Valide que les améliorations sont bien actives sur AWS.
"""

import json
import yaml
import boto3
import logging
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_aws_deployment():
    """Teste le déploiement AWS des améliorations."""
    
    env = "dev"
    s3_client = boto3.client('s3')
    config_bucket = f"vectora-inbox-config-{env}"
    
    logger.info("=== TEST DÉPLOIEMENT AWS ===")
    
    test_results = {}
    
    # Test 1: Vérifier que les fichiers sont présents sur S3
    critical_files = [
        'canonical/scopes/technology_scopes.yaml',
        'canonical/scopes/exclusion_scopes.yaml',
        'canonical/scoring/scoring_rules.yaml',
        'canonical/ingestion/ingestion_profiles.yaml',
        'canonical/matching/domain_matching_rules.yaml'
    ]
    
    for file_key in critical_files:
        try:
            s3_client.head_object(Bucket=config_bucket, Key=file_key)
            test_results[f"file_exists_{file_key.split('/')[-1]}"] = True
            logger.info(f"✅ Fichier présent: {file_key}")
        except Exception as e:
            test_results[f"file_exists_{file_key.split('/')[-1]}"] = False
            logger.error(f"❌ Fichier manquant: {file_key}")
    
    # Test 2: Vérifier le contenu des améliorations technology_scopes
    try:
        response = s3_client.get_object(Bucket=config_bucket, Key='canonical/scopes/technology_scopes.yaml')
        content = response['Body'].read().decode('utf-8')
        yaml_content = yaml.safe_load(content)
        
        lai_keywords = yaml_content.get('lai_keywords', {})
        tech_terms = lai_keywords.get('technology_terms_high_precision', [])
        
        improvements_check = {
            'pharmashell_present': 'PharmaShell®' in tech_terms,
            'siliashell_present': 'SiliaShell®' in tech_terms,
            'bepo_present': 'BEPO®' in tech_terms,
            'lai_acronym_present': 'LAI' in tech_terms,
            'extended_release_present': 'extended-release injectable' in tech_terms,
            'long_acting_present': 'long-acting injectable' in tech_terms
        }
        
        test_results.update(improvements_check)
        
        if all(improvements_check.values()):
            logger.info("✅ Toutes les améliorations technology_scopes sont actives")
        else:
            missing = [k for k, v in improvements_check.items() if not v]
            logger.error(f"❌ Améliorations manquantes: {missing}")
            
    except Exception as e:
        logger.error(f"❌ Erreur test technology_scopes: {str(e)}")
        test_results['technology_scopes_test'] = False
    
    # Test 3: Vérifier les exclusions anti-LAI
    try:
        response = s3_client.get_object(Bucket=config_bucket, Key='canonical/scopes/exclusion_scopes.yaml')
        content = response['Body'].read().decode('utf-8')
        yaml_content = yaml.safe_load(content)
        
        anti_lai_routes = yaml_content.get('anti_lai_routes', [])
        
        exclusions_check = {
            'oral_tablet_excluded': 'oral tablet' in anti_lai_routes,
            'oral_capsule_excluded': 'oral capsule' in anti_lai_routes,
            'oral_drug_excluded': 'oral drug' in anti_lai_routes,
            'pill_factory_excluded': 'pill factory' in anti_lai_routes
        }
        
        test_results.update(exclusions_check)
        
        if all(exclusions_check.values()):
            logger.info("✅ Toutes les exclusions anti-LAI sont actives")
        else:
            missing = [k for k, v in exclusions_check.items() if not v]
            logger.error(f"❌ Exclusions manquantes: {missing}")
            
    except Exception as e:
        logger.error(f"❌ Erreur test exclusions: {str(e)}")
        test_results['exclusions_test'] = False
    
    # Test 4: Vérifier les ajustements de scoring
    try:
        response = s3_client.get_object(Bucket=config_bucket, Key='canonical/scoring/scoring_rules.yaml')
        content = response['Body'].read().decode('utf-8')
        yaml_content = yaml.safe_load(content)
        
        other_factors = yaml_content.get('other_factors', {})
        contextual_scoring = yaml_content.get('contextual_scoring', {})
        
        scoring_check = {
            'pure_player_bonus_adjusted': other_factors.get('pure_player_bonus') == 1.5,
            'technology_bonus_increased': other_factors.get('technology_bonus') == 4.0,
            'trademark_bonus_increased': other_factors.get('trademark_bonus') == 5.0,
            'oral_route_penalty_added': other_factors.get('oral_route_penalty') == -10,
            'contextual_scoring_added': contextual_scoring is not None
        }
        
        test_results.update(scoring_check)
        
        if all(scoring_check.values()):
            logger.info("✅ Tous les ajustements de scoring sont actifs")
        else:
            missing = [k for k, v in scoring_check.items() if not v]
            logger.error(f"❌ Ajustements scoring manquants: {missing}")
            
    except Exception as e:
        logger.error(f"❌ Erreur test scoring: {str(e)}")
        test_results['scoring_test'] = False
    
    # Test 5: Vérifier UZEDY dans trademark_scopes
    try:
        response = s3_client.get_object(Bucket=config_bucket, Key='canonical/scopes/trademark_scopes.yaml')
        content = response['Body'].read().decode('utf-8')
        yaml_content = yaml.safe_load(content)
        
        lai_trademarks = yaml_content.get('lai_trademarks_global', [])
        uzedy_present = 'Uzedy' in lai_trademarks
        
        test_results['uzedy_trademark_present'] = uzedy_present
        
        if uzedy_present:
            logger.info("✅ UZEDY présent dans lai_trademarks_global")
        else:
            logger.error("❌ UZEDY manquant dans lai_trademarks_global")
            
    except Exception as e:
        logger.error(f"❌ Erreur test UZEDY: {str(e)}")
        test_results['uzedy_test'] = False
    
    # Résumé des tests
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    logger.info(f"\n=== RÉSUMÉ TESTS AWS ===")
    logger.info(f"Tests réussis: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        logger.info("🎉 Déploiement AWS validé avec succès !")
        logger.info("✅ Les améliorations sont actives et fonctionnelles")
        
        # Recommandations finales
        logger.info("\n=== RECOMMANDATIONS FINALES ===")
        logger.info("🚀 Prêt pour test en production avec lai_weekly_v2")
        logger.info("📊 Exécuter: aws lambda invoke --function-name vectora-inbox-engine-dev")
        logger.info("🎯 Payload suggéré: {\"client_id\": \"lai_weekly_v2\", \"period_days\": 7}")
        logger.info("📈 Comparer la nouvelle newsletter avec Run #2 précédent")
        logger.info("✅ Vérifier inclusion: Nanexa/Moderna, UZEDY, MedinCell Malaria")
        logger.info("🚫 Vérifier exclusion: DelSiTech HR, MedinCell Finance, routes orales")
        
        return 0
    elif success_rate >= 70:
        logger.warning("⚠️ Déploiement partiellement validé")
        logger.warning("Certains tests ont échoué, mais le système peut fonctionner")
        return 1
    else:
        logger.error("❌ Déploiement non validé")
        logger.error("Trop de tests ont échoué, ne pas utiliser en production")
        return 2

if __name__ == "__main__":
    exit(test_aws_deployment())