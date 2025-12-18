"""
Handler AWS Lambda pour vectora-inbox-ingest-v2.

Ce module est le point d'entrée AWS Lambda pour l'ingestion brute des contenus
depuis les sources externes (RSS, APIs, sites web).

Responsabilités :
- Parser l'événement d'entrée (client_id, sources, dates)
- Lire les variables d'environnement (buckets S3)
- Appeler la fonction de haut niveau run_ingest_for_client()
- Formater la réponse (statusCode, body JSON)
- Gérer les erreurs globales

Ce handler ne contient AUCUNE logique métier : tout est délégué à vectora_core.
"""

import json
import os
import logging
from typing import Any, Dict

# Import de la fonction de haut niveau depuis vectora_core
from vectora_core import run_ingest_for_client

# Configuration du logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Point d'entrée AWS Lambda pour vectora-inbox-ingest-v2.
    
    Args:
        event: Événement Lambda contenant :
            - client_id (str, obligatoire) : identifiant du client
            - sources (list[str], optionnel) : liste des source_key à traiter
            - period_days (int, optionnel) : nombre de jours à remonter
            - from_date (str, optionnel) : date de début (ISO8601)
            - to_date (str, optionnel) : date de fin (ISO8601)
            - force_refresh (bool, optionnel) : force la re-ingestion
            - dry_run (bool, optionnel) : mode simulation
        context: Contexte d'exécution Lambda
    
    Returns:
        Dict contenant :
            - statusCode (int) : 200 si succès, 400/500 si erreur
            - body (dict) : résultat de l'exécution ou message d'erreur
    """
    try:
        logger.info("Démarrage de vectora-inbox-ingest-v2")
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
        sources = event.get("sources")
        period_days = event.get("period_days")
        from_date = event.get("from_date")
        to_date = event.get("to_date")
        force_refresh = event.get("force_refresh", False)
        dry_run = event.get("dry_run", False)
        temporal_mode = event.get("temporal_mode", "strict")
        ingestion_mode = event.get("ingestion_mode", "balanced")
        
        # Lecture des variables d'environnement
        env_vars = {
            "ENV": os.environ.get("ENV", "dev"),
            "PROJECT_NAME": os.environ.get("PROJECT_NAME", "vectora-inbox"),
            "CONFIG_BUCKET": os.environ.get("CONFIG_BUCKET"),
            "DATA_BUCKET": os.environ.get("DATA_BUCKET"),
            "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO"),
            "temporal_mode": temporal_mode,
        }
        
        # Validation des variables d'environnement critiques
        if not env_vars["CONFIG_BUCKET"] or not env_vars["DATA_BUCKET"]:
            return {
                "statusCode": 500,
                "body": {
                    "error": "ConfigurationError",
                    "message": "Variables d'environnement manquantes : CONFIG_BUCKET, DATA_BUCKET"
                }
            }
        
        # Configuration du niveau de log
        log_level = env_vars.get("LOG_LEVEL", "INFO")
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        logger.info(f"Variables d'environnement chargées : ENV={env_vars['ENV']}, "
                   f"CONFIG_BUCKET={env_vars['CONFIG_BUCKET']}, "
                   f"DATA_BUCKET={env_vars['DATA_BUCKET']}")
        
        # Appel de la fonction de haut niveau depuis vectora_core
        result = run_ingest_for_client(
            client_id=client_id,
            sources=sources,
            period_days=period_days,
            from_date=from_date,
            to_date=to_date,
            force_refresh=force_refresh,
            dry_run=dry_run,
            ingestion_mode=ingestion_mode,
            env_vars=env_vars
        )
        
        logger.info(f"Exécution terminée avec succès : {result.get('items_ingested', 0)} items ingérés")
        
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