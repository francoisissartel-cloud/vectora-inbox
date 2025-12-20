"""
Handler AWS Lambda pour vectora-inbox-normalize-score-v2.

Ce module est le point d'entrée AWS Lambda pour la normalisation et le scoring
des items ingérés via Bedrock et les règles métier.
"""

import json
import os
import logging
from typing import Any, Dict

# Import de la fonction de haut niveau depuis vectora_core
from vectora_core.normalization import run_normalize_score_for_client

# Configuration du logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Point d'entrée AWS Lambda pour vectora-inbox-normalize-score-v2.
    """
    try:
        logger.info("Démarrage de vectora-inbox-normalize-score-v2")
        logger.info(f"Event reçu : {json.dumps(event)}")
        
        # Validation des paramètres obligatoires
        client_id = event.get("client_id")
        if not client_id:
            return {
                "statusCode": 400,
                "body": {
                    "error": "ConfigurationError",
                    "message": "Le paramètre 'client_id' est obligatoire"
                }
            }
        
        # Paramètres optionnels
        period_days = event.get("period_days")
        from_date = event.get("from_date")
        to_date = event.get("to_date")
        target_date = event.get("target_date")
        force_reprocess = event.get("force_reprocess", False)
        bedrock_model_override = event.get("bedrock_model_override")
        scoring_mode = event.get("scoring_mode", "balanced")
        
        # Lecture des variables d'environnement
        env_vars = {
            "ENV": os.environ.get("ENV", "dev"),
            "PROJECT_NAME": os.environ.get("PROJECT_NAME", "vectora-inbox"),
            "CONFIG_BUCKET": os.environ.get("CONFIG_BUCKET"),
            "DATA_BUCKET": os.environ.get("DATA_BUCKET"),
            "BEDROCK_MODEL_ID": os.environ.get("BEDROCK_MODEL_ID"),
            "BEDROCK_REGION": os.environ.get("BEDROCK_REGION", "us-east-1"),
            "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO"),
        }
        
        # Validation des variables d'environnement critiques
        required_vars = ["CONFIG_BUCKET", "DATA_BUCKET", "BEDROCK_MODEL_ID"]
        missing_vars = [var for var in required_vars if not env_vars.get(var)]
        if missing_vars:
            return {
                "statusCode": 500,
                "body": {
                    "error": "ConfigurationError",
                    "message": f"Variables d'environnement manquantes : {', '.join(missing_vars)}"
                }
            }
        
        # Configuration du niveau de log
        log_level = env_vars.get("LOG_LEVEL", "INFO")
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        logger.info(f"Variables d'environnement chargées : ENV={env_vars['ENV']}, "
                   f"CONFIG_BUCKET={env_vars['CONFIG_BUCKET']}, "
                   f"DATA_BUCKET={env_vars['DATA_BUCKET']}, "
                   f"BEDROCK_MODEL_ID={env_vars['BEDROCK_MODEL_ID']}")
        
        # Appel de la fonction de haut niveau depuis vectora_core
        result = run_normalize_score_for_client(
            client_id=client_id,
            period_days=period_days,
            from_date=from_date,
            to_date=to_date,
            target_date=target_date,
            force_reprocess=force_reprocess,
            bedrock_model_override=bedrock_model_override,
            scoring_mode=scoring_mode,
            env_vars=env_vars
        )
        
        logger.info(f"Exécution terminée : {result}")
        
        return {
            "statusCode": 200,
            "body": result
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution : {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": {
                "error": type(e).__name__,
                "message": str(e)
            }
        }