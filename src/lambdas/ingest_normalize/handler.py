"""
Handler AWS Lambda pour vectora-inbox-ingest-normalize.

Ce module est le point d'entrée AWS Lambda pour l'ingestion et la normalisation
des contenus depuis les sources externes (RSS, APIs).

Responsabilités :
- Parser l'événement d'entrée (client_id, sources, dates)
- Lire les variables d'environnement (buckets S3, modèle Bedrock)
- Appeler la fonction de haut niveau run_ingest_normalize_for_client()
- Formater la réponse (statusCode, body JSON)
- Gérer les erreurs globales

Ce handler ne contient AUCUNE logique métier : tout est délégué à vectora_core.
"""

import json
import os
import logging
import sys
from typing import Any, Dict

# Import de la fonction de haut niveau depuis vectora_core
from vectora_core import run_ingest_normalize_for_client

# Configuration du logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Point d'entrée AWS Lambda pour vectora-inbox-ingest-normalize.
    
    Args:
        event: Événement Lambda contenant :
            - client_id (str, obligatoire) : identifiant du client
            - sources (list[str], optionnel) : liste des source_key à traiter
            - period_days (int, optionnel) : nombre de jours à remonter
            - from_date (str, optionnel) : date de début (ISO8601)
            - to_date (str, optionnel) : date de fin (ISO8601)
        context: Contexte d'exécution Lambda
    
    Returns:
        Dict contenant :
            - statusCode (int) : 200 si succès, 400/500 si erreur
            - body (dict) : résultat de l'exécution ou message d'erreur
    """
    try:
        logger.info("Démarrage de vectora-inbox-ingest-normalize")
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
        
        sources = event.get("sources")  # Optionnel
        period_days = event.get("period_days")  # Optionnel
        from_date = event.get("from_date")  # Optionnel
        to_date = event.get("to_date")  # Optionnel
        
        # Lecture des variables d'environnement
        env_vars = {
            "ENV": os.environ.get("ENV", "dev"),
            "PROJECT_NAME": os.environ.get("PROJECT_NAME", "vectora-inbox"),
            "CONFIG_BUCKET": os.environ.get("CONFIG_BUCKET"),
            "DATA_BUCKET": os.environ.get("DATA_BUCKET"),
            "BEDROCK_MODEL_ID": os.environ.get("BEDROCK_MODEL_ID"),
            "PUBMED_API_KEY_PARAM": os.environ.get("PUBMED_API_KEY_PARAM"),
            "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO"),
        }
        
        # Configurer le niveau de log
        log_level = env_vars.get("LOG_LEVEL", "INFO")
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        logger.info(f"Variables d'environnement chargées : ENV={env_vars['ENV']}, "
                   f"CONFIG_BUCKET={env_vars['CONFIG_BUCKET']}, "
                   f"DATA_BUCKET={env_vars['DATA_BUCKET']}")
        
        # Appel de la fonction de haut niveau depuis vectora_core
        result = run_ingest_normalize_for_client(
            client_id=client_id,
            sources=sources,
            period_days=period_days,
            from_date=from_date,
            to_date=to_date,
            env_vars=env_vars
        )
        
        logger.info(f"Exécution terminée avec succès : {result.get('items_normalized', 0)} items normalisés")
        
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
