"""
Handler AWS Lambda pour vectora-inbox-engine.

Ce module est le point d'entrée AWS Lambda pour le moteur de newsletter :
matching, scoring et génération de la newsletter finale.

Responsabilités :
- Parser l'événement d'entrée (client_id, dates)
- Lire les variables d'environnement (buckets S3, modèle Bedrock)
- Appeler la fonction de haut niveau run_engine_for_client()
- Formater la réponse (statusCode, body JSON)
- Gérer les erreurs globales

Ce handler ne contient AUCUNE logique métier : tout est délégué à vectora_core.
"""

import json
import os
import logging
from typing import Any, Dict

# Import de la fonction de haut niveau depuis vectora_core
from vectora_core import run_engine_for_client

# Configuration du logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Point d'entrée AWS Lambda pour vectora-inbox-engine.
    
    Args:
        event: Événement Lambda contenant :
            - client_id (str, obligatoire) : identifiant du client
            - period_days (int, optionnel) : nombre de jours à analyser
            - from_date (str, optionnel) : date de début (ISO8601)
            - to_date (str, optionnel) : date de fin (ISO8601)
            - target_date (str, optionnel) : date de référence pour la newsletter
        context: Contexte d'exécution Lambda
    
    Returns:
        Dict contenant :
            - statusCode (int) : 200 si succès, 400/500 si erreur
            - body (dict) : résultat de l'exécution ou message d'erreur
    """
    try:
        logger.info("Démarrage de vectora-inbox-engine")
        logger.info(f"Event reçu : {json.dumps(event)}")
        
        # Lecture des paramètres de l'événement
        client_id = event.get("client_id")
        if not client_id:
            return {
                "statusCode": 400,
                "body": {
                    "error": "ConfigurationError",
                    "message": "Le paramètre 'client_id' est obligatoire"
                }
            }
        
        period_days = event.get("period_days")  # Optionnel
        from_date = event.get("from_date")  # Optionnel
        to_date = event.get("to_date")  # Optionnel
        target_date = event.get("target_date")  # Optionnel
        
        # Lecture des variables d'environnement
        env_vars = {
            "ENV": os.environ.get("ENV", "dev"),
            "PROJECT_NAME": os.environ.get("PROJECT_NAME", "vectora-inbox"),
            "CONFIG_BUCKET": os.environ.get("CONFIG_BUCKET"),
            "DATA_BUCKET": os.environ.get("DATA_BUCKET"),
            "NEWSLETTERS_BUCKET": os.environ.get("NEWSLETTERS_BUCKET"),
            "BEDROCK_MODEL_ID": os.environ.get("BEDROCK_MODEL_ID"),
            "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO"),
        }
        
        logger.info(f"Variables d'environnement chargées : ENV={env_vars['ENV']}, "
                   f"CONFIG_BUCKET={env_vars['CONFIG_BUCKET']}, "
                   f"DATA_BUCKET={env_vars['DATA_BUCKET']}, "
                   f"NEWSLETTERS_BUCKET={env_vars['NEWSLETTERS_BUCKET']}")
        
        # Appel de la fonction de haut niveau depuis vectora_core
        result = run_engine_for_client(
            client_id=client_id,
            period_days=period_days,
            from_date=from_date,
            to_date=to_date,
            target_date=target_date,
            env_vars=env_vars
        )
        
        logger.info(f"Exécution terminée avec succès : newsletter générée avec "
                   f"{result.get('items_selected', 0)} items sélectionnés")
        
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
