"""
Lambda Handler pour vectora-inbox-newsletter-v2
Assemblage final de la newsletter à partir des items normalisés et scorés
"""
import json
import os
import logging
from datetime import datetime
from vectora_core.newsletter import run_newsletter_for_client

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event, context):
    """
    Handler principal pour la génération de newsletter
    """
    try:
        # 1. Validation paramètres
        client_id = event.get("client_id")
        if not client_id:
            return {
                "statusCode": 400, 
                "body": {"error": "ConfigurationError: client_id required"}
            }
        
        # 2. Variables d'environnement
        env_vars = {
            "CONFIG_BUCKET": os.environ.get("CONFIG_BUCKET"),
            "DATA_BUCKET": os.environ.get("DATA_BUCKET"),
            "NEWSLETTERS_BUCKET": os.environ.get("NEWSLETTERS_BUCKET"),
            "BEDROCK_MODEL_ID": os.environ.get("BEDROCK_MODEL_ID"),
            "BEDROCK_REGION": os.environ.get("BEDROCK_REGION"),
        }
        
        # Validation variables critiques
        for key, value in env_vars.items():
            if not value:
                return {
                    "statusCode": 500,
                    "body": {"error": f"Missing environment variable: {key}"}
                }
        
        # 3. Appel vectora_core
        result = run_newsletter_for_client(
            client_id=client_id,
            env_vars=env_vars,
            target_date=event.get("target_date"),
            force_regenerate=event.get("force_regenerate", False)
        )
        
        return {"statusCode": 200, "body": result}
    
    except Exception as e:
        logger.error(f"Newsletter generation failed: {str(e)}")
        return {
            "statusCode": 500, 
            "body": {"error": str(e)}
        }