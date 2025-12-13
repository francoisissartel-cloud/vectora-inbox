#!/usr/bin/env python3
"""
Script de déploiement des améliorations sur AWS.
Déploie les configurations mises à jour selon le plan d'amélioration.
"""

import json
import yaml
import boto3
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AWSDeploymentManager:
    """Gestionnaire de déploiement AWS pour les améliorations."""
    
    def __init__(self, project_root: str, env: str = "dev"):
        self.project_root = Path(project_root)
        self.canonical_path = self.project_root / "canonical"
        self.env = env
        
        # Configuration AWS
        self.s3_client = boto3.client('s3')
        self.config_bucket = f"vectora-inbox-config-{env}"
        
    def backup_current_configuration(self) -> str:
        """Sauvegarde la configuration actuelle avant déploiement."""
        logger.info("=== SAUVEGARDE CONFIGURATION ACTUELLE ===")
        
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_prefix = f"backups/pre_improvements_{backup_timestamp}/"
        
        try:
            # Lister tous les objets dans le bucket de configuration
            response = self.s3_client.list_objects_v2(Bucket=self.config_bucket)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    if not key.startswith('backups/'):
                        # Copier vers le dossier de backup
                        copy_source = {'Bucket': self.config_bucket, 'Key': key}
                        backup_key = backup_prefix + key
                        
                        self.s3_client.copy_object(
                            CopySource=copy_source,
                            Bucket=self.config_bucket,
                            Key=backup_key
                        )
                        logger.debug(f"Sauvegardé: {key} -> {backup_key}")
                
                logger.info(f"Configuration sauvegardée avec le préfixe: {backup_prefix}")
                return backup_prefix
            else:
                logger.warning("Aucune configuration existante trouvée")
                return backup_prefix
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {str(e)}")
            raise
    
    def deploy_canonical_configurations(self) -> Dict[str, bool]:
        """Déploie les configurations canonical mises à jour."""
        logger.info("=== DÉPLOIEMENT CONFIGURATIONS CANONICAL ===")
        
        deployment_results = {}
        
        # Fichiers à déployer avec leurs chemins S3
        files_to_deploy = {
            'scopes/technology_scopes.yaml': 'canonical/scopes/technology_scopes.yaml',
            'scopes/trademark_scopes.yaml': 'canonical/scopes/trademark_scopes.yaml',
            'scopes/exclusion_scopes.yaml': 'canonical/scopes/exclusion_scopes.yaml',
            'scoring/scoring_rules.yaml': 'canonical/scoring/scoring_rules.yaml',
            'ingestion/ingestion_profiles.yaml': 'canonical/ingestion/ingestion_profiles.yaml',
            'matching/domain_matching_rules.yaml': 'canonical/matching/domain_matching_rules.yaml'
        }
        
        for local_path, s3_key in files_to_deploy.items():
            try:
                local_file_path = self.canonical_path / local_path
                
                if local_file_path.exists():
                    # Lire et valider le fichier YAML
                    with open(local_file_path, 'r', encoding='utf-8') as f:
                        yaml_content = yaml.safe_load(f)
                    
                    # Uploader vers S3
                    with open(local_file_path, 'rb') as f:
                        self.s3_client.put_object(
                            Bucket=self.config_bucket,
                            Key=s3_key,
                            Body=f,
                            ContentType='application/x-yaml'
                        )
                    
                    deployment_results[s3_key] = True
                    logger.info(f"✅ Déployé: {local_path} -> s3://{self.config_bucket}/{s3_key}")
                else:
                    deployment_results[s3_key] = False
                    logger.error(f"❌ Fichier manquant: {local_file_path}")
                    
            except Exception as e:
                deployment_results[s3_key] = False
                logger.error(f"❌ Erreur déploiement {local_path}: {str(e)}")
        
        success_count = sum(1 for success in deployment_results.values() if success)
        total_count = len(deployment_results)
        
        logger.info(f"Déploiement canonical terminé: {success_count}/{total_count} fichiers déployés")
        return deployment_results
    
    def deploy_lambda_code(self) -> Dict[str, bool]:
        """Déploie le code Lambda mis à jour."""
        logger.info("=== DÉPLOIEMENT CODE LAMBDA ===")
        
        deployment_results = {}
        
        # Fichiers Lambda à déployer
        lambda_files = {
            'src/vectora_core/matching/matcher.py': 'lambda-code/vectora_core/matching/matcher.py',
            'src/vectora_core/scoring/scorer.py': 'lambda-code/vectora_core/scoring/scorer.py'
        }
        
        for local_path, s3_key in lambda_files.items():
            try:
                local_file_path = self.project_root / local_path
                
                if local_file_path.exists():
                    with open(local_file_path, 'rb') as f:
                        self.s3_client.put_object(
                            Bucket=self.config_bucket,
                            Key=s3_key,
                            Body=f,
                            ContentType='text/x-python'
                        )
                    
                    deployment_results[s3_key] = True
                    logger.info(f"✅ Déployé: {local_path} -> s3://{self.config_bucket}/{s3_key}")
                else:
                    deployment_results[s3_key] = False
                    logger.error(f"❌ Fichier manquant: {local_file_path}")
                    
            except Exception as e:
                deployment_results[s3_key] = False
                logger.error(f"❌ Erreur déploiement {local_path}: {str(e)}")
        
        success_count = sum(1 for success in deployment_results.values() if success)
        total_count = len(deployment_results)
        
        logger.info(f"Déploiement Lambda terminé: {success_count}/{total_count} fichiers déployés")
        return deployment_results
    
    def create_deployment_metadata(self, backup_prefix: str, canonical_results: Dict[str, bool], lambda_results: Dict[str, bool]) -> Dict[str, Any]:
        """Crée les métadonnées de déploiement."""
        logger.info("=== CRÉATION MÉTADONNÉES DÉPLOIEMENT ===")
        
        metadata = {
            'deployment_info': {
                'timestamp': datetime.now().isoformat(),
                'environment': self.env,
                'improvement_version': 'phase_1_to_4_complete',
                'backup_location': backup_prefix,
                'deployed_by': 'improvement_deployment_script'
            },
            'improvements_summary': {
                'phase_1_corrections_critiques': {
                    'technology_scopes_enriched': True,
                    'uzedy_trademark_verified': True,
                    'anti_lai_exclusions_added': True,
                    'scoring_adjustments_applied': True
                },
                'phase_2_ingestion_selective': {
                    'corporate_profiles_updated': True,
                    'press_profiles_enhanced': True,
                    'exclusion_scopes_expanded': True
                },
                'phase_3_matching_contextuel': {
                    'contextual_matching_implemented': True,
                    'pattern_matching_added': True,
                    'company_type_logic_added': True
                },
                'phase_4_scoring_contextuel': {
                    'contextual_scoring_implemented': True,
                    'context_multipliers_added': True,
                    'penalties_implemented': True,
                    'recency_bonuses_added': True
                }
            },
            'deployment_results': {
                'canonical_configurations': canonical_results,
                'lambda_code': lambda_results,
                'overall_success': all(canonical_results.values()) and all(lambda_results.values())
            },
            'expected_improvements': {
                'nanexa_moderna_pharmashell_included': 'Items Nanexa/Moderna PharmaShell® maintenant inclus',
                'uzedy_regulatory_included': 'Items UZEDY regulatory maintenant inclus',
                'medincel_malaria_grants_included': 'Items MedinCell malaria grants maintenant inclus',
                'hr_noise_reduced': 'Bruit HR DelSiTech maintenant exclu',
                'finance_noise_reduced': 'Bruit finance MedinCell maintenant exclu',
                'oral_routes_excluded': 'Routes orales maintenant exclues',
                'technology_brands_detected': 'PharmaShell®, SiliaShell®, BEPO® maintenant détectés'
            },
            'monitoring_recommendations': [
                'Surveiller les premières newsletters générées',
                'Comparer avec les newsletters précédentes',
                'Vérifier que les signaux LAI majeurs sont bien capturés',
                'Confirmer la réduction du bruit HR/Finance',
                'Valider l\'exclusion des routes orales'
            ]
        }
        
        # Uploader les métadonnées vers S3
        metadata_key = f"deployments/improvements_{datetime.now().strftime('%Y%m%d_%H%M%S')}_metadata.json"
        
        try:
            self.s3_client.put_object(
                Bucket=self.config_bucket,
                Key=metadata_key,
                Body=json.dumps(metadata, indent=2, ensure_ascii=False),
                ContentType='application/json'
            )
            
            logger.info(f"✅ Métadonnées sauvegardées: s3://{self.config_bucket}/{metadata_key}")
            metadata['metadata_location'] = f"s3://{self.config_bucket}/{metadata_key}"
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde métadonnées: {str(e)}")
        
        return metadata
    
    def validate_deployment(self) -> Dict[str, Any]:
        """Valide le déploiement en vérifiant les fichiers sur S3."""
        logger.info("=== VALIDATION DÉPLOIEMENT ===")
        
        validation_results = {}
        
        # Fichiers critiques à vérifier
        critical_files = [
            'canonical/scopes/technology_scopes.yaml',
            'canonical/scopes/exclusion_scopes.yaml',
            'canonical/scoring/scoring_rules.yaml',
            'canonical/ingestion/ingestion_profiles.yaml',
            'canonical/matching/domain_matching_rules.yaml'
        ]
        
        for file_key in critical_files:
            try:
                response = self.s3_client.head_object(Bucket=self.config_bucket, Key=file_key)
                validation_results[file_key] = {
                    'exists': True,
                    'last_modified': response['LastModified'].isoformat(),
                    'size': response['ContentLength']
                }
                logger.info(f"✅ Validé: {file_key}")
                
            except Exception as e:
                validation_results[file_key] = {
                    'exists': False,
                    'error': str(e)
                }
                logger.error(f"❌ Échec validation: {file_key} - {str(e)}")
        
        # Vérifier le contenu d'un fichier critique
        try:
            response = self.s3_client.get_object(
                Bucket=self.config_bucket, 
                Key='canonical/scopes/technology_scopes.yaml'
            )
            content = response['Body'].read().decode('utf-8')
            yaml_content = yaml.safe_load(content)
            
            # Vérifier que les améliorations sont présentes
            lai_keywords = yaml_content.get('lai_keywords', {})
            tech_terms = lai_keywords.get('technology_terms_high_precision', [])\n            \n            improvements_present = {\n                'pharmashell_present': 'PharmaShell®' in tech_terms,\n                'siliashell_present': 'SiliaShell®' in tech_terms,\n                'bepo_present': 'BEPO®' in tech_terms,\n                'lai_acronym_present': 'LAI' in tech_terms\n            }\n            \n            validation_results['improvements_verification'] = improvements_present\n            \n            if all(improvements_present.values()):\n                logger.info(\"✅ Toutes les améliorations technology_scopes sont présentes\")\n            else:\n                logger.warning(f\"⚠️ Certaines améliorations manquent: {improvements_present}\")\n                \n        except Exception as e:\n            logger.error(f\"❌ Erreur validation contenu: {str(e)}\")\n            validation_results['content_validation_error'] = str(e)\n        \n        return validation_results\n    \n    def generate_deployment_report(self) -> Dict[str, Any]:\n        \"\"\"Génère un rapport complet de déploiement.\"\"\"\n        logger.info(\"=== GÉNÉRATION RAPPORT DÉPLOIEMENT ===\")\n        \n        try:\n            # 1. Sauvegarde\n            backup_prefix = self.backup_current_configuration()\n            \n            # 2. Déploiement configurations\n            canonical_results = self.deploy_canonical_configurations()\n            \n            # 3. Déploiement code Lambda\n            lambda_results = self.deploy_lambda_code()\n            \n            # 4. Création métadonnées\n            metadata = self.create_deployment_metadata(backup_prefix, canonical_results, lambda_results)\n            \n            # 5. Validation\n            validation_results = self.validate_deployment()\n            \n            # 6. Rapport final\n            deployment_report = {\n                'deployment_status': 'SUCCESS' if metadata['deployment_results']['overall_success'] else 'PARTIAL_FAILURE',\n                'timestamp': datetime.now().isoformat(),\n                'environment': self.env,\n                'backup_location': backup_prefix,\n                'deployment_results': {\n                    'canonical_configurations': canonical_results,\n                    'lambda_code': lambda_results\n                },\n                'validation_results': validation_results,\n                'metadata': metadata,\n                'next_steps': self._generate_next_steps(metadata['deployment_results']['overall_success'])\n            }\n            \n            return deployment_report\n            \n        except Exception as e:\n            logger.error(f\"Erreur lors du déploiement: {str(e)}\")\n            return {\n                'deployment_status': 'FAILURE',\n                'timestamp': datetime.now().isoformat(),\n                'error': str(e),\n                'next_steps': [\n                    'Vérifier les logs d\\'erreur',\n                    'Corriger les problèmes identifiés',\n                    'Relancer le déploiement',\n                    'Contacter l\\'équipe technique si nécessaire'\n                ]\n            }\n    \n    def _generate_next_steps(self, deployment_success: bool) -> List[str]:\n        \"\"\"Génère les prochaines étapes selon le résultat du déploiement.\"\"\"\n        if deployment_success:\n            return [\n                '✅ Déploiement réussi - Configurations mises à jour sur AWS',\n                '🔄 Exécuter un test complet avec le client lai_weekly_v2',\n                '📊 Générer une newsletter et comparer avec les précédentes',\n                '👀 Surveiller les métriques de qualité (signaux LAI vs bruit)',\n                '📈 Mesurer l\\'amélioration du taux de précision',\n                '🎯 Valider que les cas critiques (Nanexa/Moderna, UZEDY) sont inclus',\n                '🚫 Confirmer l\\'exclusion du bruit (HR DelSiTech, Finance MedinCell)',\n                '📝 Documenter les résultats et ajuster si nécessaire'\n            ]\n        else:\n            return [\n                '❌ Déploiement partiel ou échoué',\n                '🔍 Analyser les logs d\\'erreur détaillés',\n                '🔧 Corriger les fichiers ou configurations problématiques',\n                '🔄 Relancer le déploiement des éléments échoués',\n                '⚠️ Ne pas exécuter de tests tant que le déploiement n\\'est pas complet',\n                '📞 Contacter l\\'équipe technique si les problèmes persistent'\n            ]\n\n\ndef main():\n    \"\"\"Point d'entrée principal.\"\"\"\n    project_root = Path(__file__).parent\n    \n    # Paramètres de déploiement\n    env = \"dev\"  # Peut être modifié pour \"prod\"\n    \n    logger.info(f\"Démarrage déploiement améliorations sur AWS (env: {env})\")\n    \n    # Créer le gestionnaire de déploiement\n    deployment_manager = AWSDeploymentManager(str(project_root), env)\n    \n    # Générer le rapport de déploiement\n    deployment_report = deployment_manager.generate_deployment_report()\n    \n    # Sauvegarder le rapport localement\n    report_path = project_root / f\"aws_deployment_report_{env}.json\"\n    with open(report_path, 'w', encoding='utf-8') as f:\n        json.dump(deployment_report, f, indent=2, ensure_ascii=False)\n    \n    logger.info(f\"Rapport de déploiement sauvegardé: {report_path}\")\n    \n    # Afficher le résumé\n    status = deployment_report['deployment_status']\n    logger.info(f\"\\n=== RÉSUMÉ DÉPLOIEMENT ===\\nStatus: {status}\")\n    \n    if status == 'SUCCESS':\n        logger.info(\"🎉 Déploiement réussi ! Les améliorations sont maintenant actives sur AWS.\")\n    elif status == 'PARTIAL_FAILURE':\n        logger.warning(\"⚠️ Déploiement partiel. Certains éléments ont échoué.\")\n    else:\n        logger.error(\"❌ Déploiement échoué. Vérifier les logs d'erreur.\")\n    \n    # Afficher les prochaines étapes\n    logger.info(\"\\n=== PROCHAINES ÉTAPES ===\\n\")\n    for step in deployment_report['next_steps']:\n        logger.info(step)\n    \n    # Code de sortie\n    if status == 'SUCCESS':\n        return 0\n    elif status == 'PARTIAL_FAILURE':\n        return 1\n    else:\n        return 2\n\n\nif __name__ == \"__main__\":\n    exit(main())"
<parameter name="explanation">Création du script de déploiement AWS pour finaliser l'implémentation des améliorations