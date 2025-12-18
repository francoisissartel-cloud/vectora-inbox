#!/usr/bin/env python3
"""
Package et déploiement Lambda normalize_score V2 restaurée.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NormalizeScoreV2Deployer:
    """Déployeur pour la lambda normalize_score V2."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_v2_path = self.project_root / "src_v2"
        self.build_dir = self.project_root / "build" / "normalize_score_v2"
        self.package_name = f"normalize-score-v2-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
        
    def clean_build_dir(self):
        """Nettoie le répertoire de build."""
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        self.build_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Répertoire de build nettoyé: {self.build_dir}")
    
    def copy_lambda_code(self):
        """Copie le code de la lambda."""
        logger.info("Copie du code lambda normalize_score V2...")
        
        # Handler lambda
        handler_src = self.src_v2_path / "lambdas" / "normalize_score" / "handler.py"
        handler_dst = self.build_dir / "handler.py"
        shutil.copy2(handler_src, handler_dst)
        
        # Module vectora_core complet
        vectora_core_src = self.src_v2_path / "vectora_core"
        vectora_core_dst = self.build_dir / "vectora_core"
        shutil.copytree(vectora_core_src, vectora_core_dst)
        
        logger.info("Code lambda copié avec succès")
    
    def install_dependencies(self):
        """Installe les dépendances dans le build."""
        logger.info("Installation des dépendances...")
        
        requirements_file = self.src_v2_path / "requirements.txt"
        if requirements_file.exists():
            cmd = [
                sys.executable, "-m", "pip", "install",
                "-r", str(requirements_file),
                "-t", str(self.build_dir),
                "--no-deps"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Erreur installation dépendances: {result.stderr}")
                return False
            
            logger.info("Dépendances installées")
        
        return True
    
    def create_package(self):
        """Crée le package ZIP."""
        logger.info("Création du package ZIP...")
        
        package_path = self.project_root / self.package_name
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.build_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(self.build_dir)
                    zipf.write(file_path, arc_name)
        
        logger.info(f"Package créé: {package_path}")
        return package_path
    
    def deploy_to_aws(self, package_path: Path):
        """Déploie sur AWS Lambda."""
        logger.info("Déploiement sur AWS Lambda...")
        
        function_name = "vectora-inbox-normalize-score-v2-dev"
        
        # Mise à jour du code
        cmd = [
            "aws", "lambda", "update-function-code",
            "--function-name", function_name,
            "--zip-file", f"fileb://{package_path}",
            "--region", "eu-west-3",
            "--profile", "rag-lai-prod"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Erreur déploiement: {result.stderr}")
            return False
        
        logger.info("Code déployé avec succès")
        
        # Mise à jour de la configuration
        self.update_lambda_config(function_name)
        
        return True
    
    def update_lambda_config(self, function_name: str):
        """Met à jour la configuration de la lambda."""
        logger.info("Mise à jour configuration lambda...")
        
        # Variables d'environnement V2
        env_vars = {
            "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "BEDROCK_REGION": "us-east-1",
            "MAX_BEDROCK_WORKERS": "1",
            "CONFIG_BUCKET": "vectora-config-dev",
            "DATA_BUCKET": "vectora-data-dev",
            "PYTHONPATH": "/var/task"
        }
        
        cmd = [
            "aws", "lambda", "update-function-configuration",
            "--function-name", function_name,
            "--environment", f"Variables={json.dumps(env_vars)}",
            "--timeout", "900",
            "--memory-size", "1024",
            "--region", "eu-west-3",
            "--profile", "rag-lai-prod"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Erreur configuration: {result.stderr}")
            return False
        
        logger.info("Configuration mise à jour")
        return True
    
    def test_deployment(self, function_name: str):
        """Test le déploiement avec un événement de test."""
        logger.info("Test du déploiement...")
        
        test_event = {
            "client_id": "lai_weekly_v3",
            "scoring_mode": "balanced",
            "force_reprocess": False
        }
        
        event_file = self.project_root / "test_event.json"
        with open(event_file, 'w') as f:
            json.dump(test_event, f)
        
        cmd = [
            "aws", "lambda", "invoke",
            "--function-name", function_name,
            "--payload", f"file://{event_file}",
            "--region", "eu-west-3",
            "--profile", "rag-lai-prod",
            str(self.project_root / "response.json")
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Nettoyage
        event_file.unlink(missing_ok=True)
        
        if result.returncode != 0:
            logger.error(f"Erreur test: {result.stderr}")
            return False
        
        # Lecture de la réponse
        response_file = self.project_root / "response.json"
        if response_file.exists():
            with open(response_file) as f:
                response = json.load(f)
            logger.info(f"Réponse test: {response}")
            response_file.unlink()
        
        logger.info("Test de déploiement réussi")
        return True
    
    def deploy(self):
        """Processus complet de déploiement."""
        try:
            logger.info("Démarrage déploiement normalize_score V2")
            
            # 1. Nettoyage
            self.clean_build_dir()
            
            # 2. Copie du code
            self.copy_lambda_code()
            
            # 3. Installation dépendances
            if not self.install_dependencies():
                return False
            
            # 4. Création package
            package_path = self.create_package()
            
            # 5. Déploiement AWS
            if not self.deploy_to_aws(package_path):
                return False
            
            # 6. Test
            function_name = "vectora-inbox-normalize-score-v2-dev"
            if not self.test_deployment(function_name):
                logger.warning("Test de déploiement échoué, mais lambda déployée")
            
            logger.info("Déploiement terminé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur déploiement: {str(e)}", exc_info=True)
            return False


def main():
    """Point d'entrée principal."""
    deployer = NormalizeScoreV2Deployer()
    
    if deployer.deploy():
        print("Déploiement réussi")
        return 0
    else:
        print("Déploiement échoué")
        return 1


if __name__ == "__main__":
    sys.exit(main())