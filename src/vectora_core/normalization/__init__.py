"""
Package de normalisation des items pour Vectora Inbox.

Ce package contient les modules pour :
- Appeler Bedrock (bedrock_client)
- Détecter les entités par règles (entity_detector)
- Orchestrer la normalisation (normalizer)
- Fonction de haut niveau pour Lambda (run_normalize_score_for_client)
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from vectora_core.normalization import bedrock_client, entity_detector, normalizer
from vectora_core.config import loader as config_loader
from vectora_core.storage import s3_client
from vectora_core.matching import matcher
from vectora_core.scoring import scorer

logger = logging.getLogger(__name__)


def run_normalize_score_for_client(
    client_id: str,
    period_days: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    target_date: Optional[str] = None,
    force_reprocess: bool = False,
    bedrock_model_override: Optional[str] = None,
    scoring_mode: str = "balanced",
    env_vars: Dict[str, str] = None
) -> Dict[str, Any]:
    """
    Fonction de haut niveau pour normaliser et scorer les items d'un client.
    
    Cette fonction :
    1. Charge la configuration client
    2. Récupère les items ingérés depuis S3
    3. Normalise les items via Bedrock
    4. Applique le matching par domaines
    5. Calcule les scores de pertinence
    6. Sauvegarde les résultats
    
    Args:
        client_id: Identifiant du client
        period_days: Nombre de jours à analyser (défaut: depuis config)
        from_date: Date de début (ISO8601)
        to_date: Date de fin (ISO8601)
        target_date: Date de référence pour le scoring
        force_reprocess: Force le retraitement même si déjà fait
        bedrock_model_override: Surcharge du modèle Bedrock
        scoring_mode: Mode de scoring (balanced, strict, permissive)
        env_vars: Variables d'environnement Lambda
    
    Returns:
        {
            "client_id": "lai_weekly_v3",
            "items_input": 15,
            "items_normalized": 15,
            "items_matched": 12,
            "items_scored": 15,
            "matching_rate": 80.0,
            "domain_statistics": {...},
            "execution_time_seconds": 45.2,
            "bedrock_calls": 15,
            "errors": []
        }
    """
    start_time = datetime.now()
    logger.info(f"Démarrage normalize_score pour client {client_id}")
    
    try:
        # Étape 1 : Charger la configuration
        config_bucket = env_vars.get('CONFIG_BUCKET')
        data_bucket = env_vars.get('DATA_BUCKET')
        bedrock_model_id = bedrock_model_override or env_vars.get('BEDROCK_MODEL_ID')
        
        if not all([config_bucket, data_bucket, bedrock_model_id]):
            raise ValueError("Variables d'environnement manquantes: CONFIG_BUCKET, DATA_BUCKET, BEDROCK_MODEL_ID")
        
        # Charger la configuration client
        client_config = config_loader.load_client_config(client_id, config_bucket)
        canonical_scopes = config_loader.load_canonical_scopes(config_bucket)
        
        logger.info(f"Configuration chargée pour {client_id}")
        
        # Étape 2 : Déterminer la période d'analyse
        if not period_days:
            period_days = client_config.get('period_days', 7)
        
        if not from_date:
            from_date = (datetime.now() - timedelta(days=period_days)).isoformat()
        if not to_date:
            to_date = datetime.now().isoformat()
        
        logger.info(f"Période d'analyse: {from_date} à {to_date}")
        
        # Étape 3 : Récupérer les items ingérés
        ingested_items = s3_client.load_ingested_items(
            data_bucket, client_id, from_date, to_date
        )
        
        if not ingested_items:
            logger.warning(f"Aucun item ingéré trouvé pour {client_id}")
            return {
                "client_id": client_id,
                "items_input": 0,
                "items_normalized": 0,
                "items_matched": 0,
                "items_scored": 0,
                "matching_rate": 0.0,
                "domain_statistics": {},
                "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
                "bedrock_calls": 0,
                "errors": ["Aucun item ingéré trouvé"]
            }
        
        logger.info(f"Items ingérés récupérés: {len(ingested_items)}")
        
        # Étape 4 : Normaliser les items
        watch_domains = client_config.get('watch_domains', [])
        
        normalized_items = normalizer.normalize_items_batch(
            ingested_items,
            canonical_scopes,
            bedrock_model_id,
            watch_domains
        )
        
        logger.info(f"Items normalisés: {len(normalized_items)}")
        
        # Étape 5 : Appliquer le matching par domaines
        matched_items = []
        matching_stats = {}
        
        for item in normalized_items:
            match_result = matcher.match_item_to_domains(
                item, watch_domains, canonical_scopes, client_config
            )
            
            # Fusionner les résultats de matching
            item.update(match_result)
            matched_items.append(item)
            
            # Statistiques par domaine
            for domain_id in match_result.get('matched_domains', []):
                matching_stats[domain_id] = matching_stats.get(domain_id, 0) + 1
        
        items_matched = sum(1 for item in matched_items if item.get('matched_domains'))
        matching_rate = (items_matched / len(matched_items) * 100) if matched_items else 0
        
        logger.info(f"Items matchés: {items_matched}/{len(matched_items)} ({matching_rate:.1f}%)")
        
        # Étape 6 : Calculer les scores
        scored_items = []
        for item in matched_items:
            score_result = scorer.score_item(
                item, client_config, target_date or to_date, scoring_mode
            )
            item.update(score_result)
            scored_items.append(item)
        
        logger.info(f"Items scorés: {len(scored_items)}")
        
        # Étape 7 : Sauvegarder les résultats
        output_key = f"clients/{client_id}/normalized/{datetime.now().strftime('%Y%m%d_%H%M%S')}_normalized_items.json"
        
        s3_client.save_json_to_s3(
            data_bucket, output_key, {
                "client_id": client_id,
                "processing_date": datetime.now().isoformat(),
                "period": {"from_date": from_date, "to_date": to_date},
                "items": scored_items,
                "statistics": {
                    "items_input": len(ingested_items),
                    "items_normalized": len(normalized_items),
                    "items_matched": items_matched,
                    "items_scored": len(scored_items),
                    "matching_rate": matching_rate,
                    "domain_statistics": matching_stats
                }
            }
        )
        
        logger.info(f"Résultats sauvegardés: {output_key}")
        
        # Résultat final
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "client_id": client_id,
            "items_input": len(ingested_items),
            "items_normalized": len(normalized_items),
            "items_matched": items_matched,
            "items_scored": len(scored_items),
            "matching_rate": matching_rate,
            "domain_statistics": matching_stats,
            "execution_time_seconds": execution_time,
            "bedrock_calls": len(normalized_items),  # Approximation
            "errors": [],
            "output_s3_key": output_key
        }
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"Erreur lors de normalize_score: {e}", exc_info=True)
        
        return {
            "client_id": client_id,
            "items_input": 0,
            "items_normalized": 0,
            "items_matched": 0,
            "items_scored": 0,
            "matching_rate": 0.0,
            "domain_statistics": {},
            "execution_time_seconds": execution_time,
            "bedrock_calls": 0,
            "errors": [str(e)]
        }


__all__ = ['bedrock_client', 'entity_detector', 'normalizer', 'run_normalize_score_for_client']
