"""
Vectora Core V2 - Bibliothèque métier pour Vectora Inbox V2.

Ce package contient la logique métier pour l'ingestion brute uniquement.
Version simplifiée de vectora_core V1 sans normalisation Bedrock.

Modules principaux :
- config_loader : chargement et résolution des configurations
- s3_io : opérations de lecture/écriture S3
- source_fetcher : récupération des contenus bruts (RSS, APIs)
- content_parser : transformation en items structurés
- models : modèles de données (Item, Source, Config)
- utils : utilitaires transverses (logging, dates, hashing)

Fonction publique principale :
- run_ingest_for_client() : orchestration complète de l'ingestion
"""

from typing import Any, Dict, List, Optional
import logging
import time
from datetime import datetime

from . import config_loader
from . import s3_io
from . import source_fetcher
from . import content_parser
from . import ingestion_profiles
from . import utils

logger = logging.getLogger(__name__)


def run_ingest_for_client(
    client_id: str,
    sources: Optional[List[str]] = None,
    period_days: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    force_refresh: bool = False,
    dry_run: bool = False,
    ingestion_mode: str = "balanced",
    env_vars: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Orchestration de l'ingestion brute pour un client.
    
    Cette fonction implémente uniquement la Phase 1A du workflow Vectora Inbox :
    - Récupération des contenus bruts depuis les sources externes
    - Parsing en items structurés
    - Stockage dans S3 layer 'ingested/'
    
    Processus :
    1. Charger la configuration client et les catalogues canonical depuis S3
    2. Résoudre les bouquets de sources (développer les source_key)
    3. Pour chaque source : récupérer le contenu brut (HTTP/RSS)
    4. Parser les contenus bruts en items structurés
    5. Appliquer le filtrage temporel
    6. Déduplication par content_hash
    7. Écrire les items dans S3 (DATA_BUCKET/ingested/)
    
    Args:
        client_id: Identifiant unique du client (ex: "lai_weekly_v3")
        sources: Liste optionnelle de source_key à traiter (surcharge la config)
        period_days: Nombre de jours à remonter dans le passé
        from_date: Date de début (ISO8601)
        to_date: Date de fin (ISO8601)
        force_refresh: Force la re-ingestion même si déjà fait
        dry_run: Mode simulation sans écriture S3
        env_vars: Variables d'environnement (buckets, etc.)
    
    Returns:
        Dict contenant les statistiques d'exécution :
            - client_id (str)
            - execution_date (str)
            - sources_processed (int)
            - items_ingested (int)
            - items_filtered_out (int)
            - items_deduplicated (int)
            - s3_output_path (str)
            - execution_time_seconds (float)
            - dry_run (bool)
    
    Raises:
        Exception: En cas d'erreur lors du chargement des configs ou de l'ingestion
    """
    logger.info(f"Démarrage de l'ingestion pour le client : {client_id}")
    start_time = time.time()
    
    # Validation des variables d'environnement
    env_vars = env_vars or {}
    config_bucket = env_vars.get('CONFIG_BUCKET')
    data_bucket = env_vars.get('DATA_BUCKET')
    
    if not config_bucket or not data_bucket:
        raise ValueError("Variables d'environnement manquantes : CONFIG_BUCKET, DATA_BUCKET")
    
    try:
        # Étape 1 : Charger les configurations
        logger.info("Chargement des configurations depuis S3")
        client_config = config_loader.load_client_config(client_id, config_bucket)
        source_catalog = config_loader.load_source_catalog(config_bucket)
        
        # Étape 2 : Résoudre les sources à traiter
        logger.info("Résolution des sources à traiter")
        resolved_sources = config_loader.resolve_sources_for_client(
            client_config, source_catalog, sources
        )
        
        logger.info(f"Nombre de sources à traiter : {len(resolved_sources)}")
        
        # Étape 3 : Résoudre period_days pour le filtre temporel
        logger.info("Résolution de la fenêtre temporelle pour l'ingestion")
        resolved_period_days = config_loader.resolve_period_days(period_days, client_config)
        logger.info(f"Period days résolu : {resolved_period_days} jours")
        
        # Calculer la date de coupure
        from_date_calc, to_date_calc = utils.compute_date_range(
            resolved_period_days, from_date, to_date
        )
        cutoff_date = from_date_calc
        logger.info(f"Filtre temporel : items antérieurs au {cutoff_date} seront ignorés")
        
        # Étape 4 : Ingestion et parsing
        logger.info("Phase 1A : Ingestion des sources")
        all_raw_items = []
        sources_processed = 0
        sources_failed = 0
        
        for source_meta in resolved_sources:
            source_key = source_meta.get('source_key')
            logger.info(f"Traitement de la source : {source_key}")
            
            try:
                # Récupérer le contenu brut
                raw_content = source_fetcher.fetch_source_content(source_meta)
                
                if raw_content and not raw_content.get('error'):
                    # Parser le contenu en items bruts
                    raw_items = content_parser.parse_source_content(raw_content, source_meta)
                    
                    # Appliquer le profil d'ingestion
                    filtered_items = ingestion_profiles.apply_ingestion_profile(raw_items, source_meta, ingestion_mode)
                    
                    all_raw_items.extend(filtered_items)
                    sources_processed += 1
                    
                    # Log des statistiques de profil
                    if len(raw_items) != len(filtered_items):
                        profile_stats = ingestion_profiles.get_profile_stats(len(raw_items), len(filtered_items), source_meta)
                        logger.info(f"Source {source_key} : {len(raw_items)} items parsés → {len(filtered_items)} items après profil ({profile_stats['retention_rate']}% rétention)")
                    else:
                        logger.info(f"Source {source_key} : {len(filtered_items)} items récupérés")
                else:
                    sources_failed += 1
                    error_msg = raw_content.get('error', 'Contenu vide') if raw_content else 'Échec récupération'
                    logger.warning(f"Source {source_key} : {error_msg}")
            
            except Exception as e:
                sources_failed += 1
                logger.error(f"Source {source_key} : erreur lors du traitement - {e}")
        
        logger.info(f"Total items après profils : {len(all_raw_items)} depuis {sources_processed} sources")
        if sources_failed > 0:
            logger.warning(f"Sources en échec : {sources_failed}")
        
        # Étape 5 : Filtre temporel AVANT déduplication (adapté selon le mode d'ingestion)
        temporal_mode = _get_temporal_mode(ingestion_mode, env_vars)
        logger.info(f"Application du filtre temporel sur les items bruts (mode: {temporal_mode}, ingestion: {ingestion_mode})")
        filtered_items = utils.apply_temporal_filter(all_raw_items, cutoff_date, temporal_mode)
        items_filtered_out = len(all_raw_items) - len(filtered_items)
        
        logger.info(f"Filtre temporel : {len(filtered_items)} items conservés, {items_filtered_out} items ignorés (trop anciens)")
        
        # Étape 6 : Déduplication
        logger.info("Déduplication des items par content_hash")
        deduplicated_items = utils.deduplicate_items(filtered_items)
        items_deduplicated = len(filtered_items) - len(deduplicated_items)
        
        logger.info(f"Déduplication : {len(deduplicated_items)} items uniques, {items_deduplicated} doublons supprimés")
        
        # Étape 7 : Validation des items
        valid_items = []
        for item in deduplicated_items:
            if utils.validate_item(item):
                valid_items.append(item)
            else:
                logger.warning(f"Item invalide ignoré : {item.get('title', '')[:50]}...")
        
        logger.info(f"Validation : {len(valid_items)} items valides sur {len(deduplicated_items)}")
        
        # Étape 8 : Écriture dans S3 (sauf si dry_run)
        current_date = utils.get_current_date_iso()
        s3_key = s3_io.build_s3_key_for_ingested_items(client_id, current_date)
        s3_output_path = f"s3://{data_bucket}/{s3_key}"
        
        if not dry_run:
            logger.info(f"Écriture des items dans {s3_output_path}")
            s3_io.write_json_to_s3(data_bucket, s3_key, valid_items)
        else:
            logger.info(f"Mode dry_run : écriture simulée vers {s3_output_path}")
        
        # Calculer le temps d'exécution
        execution_time = time.time() - start_time
        
        # Construire le résultat
        result = {
            'client_id': client_id,
            'execution_date': utils.get_current_datetime_iso(),
            'sources_processed': sources_processed,
            'sources_failed': sources_failed,
            'items_ingested': len(all_raw_items),
            'items_filtered_out': items_filtered_out,
            'items_deduplicated': items_deduplicated,
            'items_final': len(valid_items),
            'period_days_used': resolved_period_days,
            's3_output_path': s3_output_path,
            'execution_time_seconds': round(execution_time, 2),
            'dry_run': dry_run,
            'ingestion_mode': ingestion_mode,
            'temporal_mode': temporal_mode,
            'status': 'success'
        }
        
        logger.info(f"Ingestion terminée avec succès : {result}")
        return result
    
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Erreur lors de l'ingestion : {str(e)}", exc_info=True)
        
        # Retourner un résultat d'erreur
        return {
            'client_id': client_id,
            'execution_date': utils.get_current_datetime_iso(),
            'sources_processed': 0,
            'sources_failed': 0,
            'items_ingested': 0,
            'items_filtered_out': 0,
            'items_deduplicated': 0,
            'items_final': 0,
            'period_days_used': period_days or 7,
            's3_output_path': '',
            'execution_time_seconds': round(execution_time, 2),
            'dry_run': dry_run,
            'ingestion_mode': ingestion_mode,
            'status': 'error',
            'error': str(e)
        }


def _get_temporal_mode(ingestion_mode: str, env_vars: Dict[str, Any]) -> str:
    """
    Détermine le mode temporel selon le mode d'ingestion.
    
    Args:
        ingestion_mode: Mode d'ingestion (strict/balanced/broad)
        env_vars: Variables d'environnement
    
    Returns:
        Mode temporel (strict/flexible)
    """
    # Priorité : paramètre explicite > mode d'ingestion
    explicit_temporal = env_vars.get('temporal_mode')
    if explicit_temporal:
        return explicit_temporal
    
    # Mapping mode d'ingestion -> mode temporel
    if ingestion_mode == "strict":
        return "strict"
    elif ingestion_mode == "broad":
        return "flexible"
    else:  # balanced
        return "flexible"


__all__ = [
    "run_ingest_for_client",
]