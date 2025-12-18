#!/usr/bin/env python3
"""
Création de la lambda normalize_score V2 sur AWS.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_lambda_function():
    """Crée la fonction Lambda sur AWS."""
    
    function_name = "vectora-inbox-normalize-score-v2-dev"
    role_arn = "arn:aws:iam::786469175371:role/vectora-inbox-s0-iam-dev-IngestNormalizeRole-aefpODOGz3Lx"
    
    # Package minimal pour la création
    project_root = Path(__file__).parent.parent
    handler_file = project_root / "src_v2" / "lambdas" / "normalize_score" / "handler.py"
    
    # Création d'un ZIP minimal
    import zipfile
    import tempfile
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
        with zipfile.ZipFile(tmp_zip.name, 'w') as zipf:
            zipf.write(handler_file, 'handler.py')
            # Ajout d'un __init__.py vide pour vectora_core
            zipf.writestr('vectora_core/__init__.py', '')
            zipf.writestr('vectora_core/normalization/__init__.py', 
                         'def run_normalize_score_for_client(*args, **kwargs): return {"status": "placeholder"}')
        
        # Commande de création
        cmd = [
            "aws", "lambda", "create-function",
            "--function-name", function_name,
            "--runtime", "python3.11",
            "--role", role_arn,
            "--handler", "handler.lambda_handler",
            "--zip-file", f"fileb://{tmp_zip.name}",
            "--timeout", "900",
            "--memory-size", "1024",
            "--environment", json.dumps({
                "Variables": {
                    "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "BEDROCK_REGION": "us-east-1",
                    "MAX_BEDROCK_WORKERS": "1",
                    "CONFIG_BUCKET": "vectora-config-dev",
                    "DATA_BUCKET": "vectora-data-dev"
                }
            }),
            "--region", "eu-west-3",
            "--profile", "rag-lai-prod"
        ]
        
        logger.info(f"Création de la lambda: {function_name}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Erreur création lambda: {result.stderr}")
            return False
        
        logger.info("Lambda créée avec succès")
        logger.info(result.stdout)
        return True

def main():
    """Point d'entrée principal."""
    if create_lambda_function():
        print("Lambda créée avec succès")
        return 0
    else:
        print("Échec création lambda")
        return 1

if __name__ == "__main__":
    sys.exit(main())