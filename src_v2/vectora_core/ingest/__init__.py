"""
Vectora Core V2 - Modules Ingest

Ce package contient la logique métier spécifique à la Lambda ingest V2 :
- Récupération de contenus depuis sources externes
- Parsing RSS/HTML/API en items structurés
- Application des profils d'ingestion canonical
- Orchestration complète du workflow d'ingestion

Fonction principale exportée :
- run_ingest_for_client() : Orchestration complète de l'ingestion
"""

from typing import Any, Dict, List, Optional
import logging
import time
from datetime import datetime

from ..shared import config_loader
from ..shared import s3_io
from ..shared import utils
from . import source_fetcher
from . import content_parser
from . import ingestion_profiles
from .ingestion_profiles import initialize_exclusion_scopes, initialize_company_scopes, initialize_lai_keywords

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
    
    Args:
        client_id: Identifiant unique du client (ex: "lai_weekly_v3")
        sources: Liste optionnelle de source_key à traiter
        period_days: Nombre de jours à remonter dans le passé
        from_date: Date de début (ISO8601)
        to_date: Date de fin (ISO8601)
        force_refresh: Force la re-ingestion même si déjà fait
        dry_run: Mode simulation sans écriture S3
        ingestion_mode: Mode d'ingestion (strict/balanced/broad)
        env_vars: Variables d'environnement (buckets, etc.)
    
    Returns:
        Dict contenant les statistiques d'exécution
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
        
        # Initialiser exclusion scopes depuis S3
        logger.info("Étape 2.5 : Initialisation des exclusion scopes depuis S3")
        initialize_exclusion_scopes(s3_io, config_bucket)
        
        # Initialiser company scopes depuis S3
        logger.info("Étape 2.6 : Initialisation des company scopes depuis S3")
        initialize_company_scopes(s3_io, config_bucket)
        
        # Initialiser LAI keywords depuis S3
        logger.info("Étape 2.7 : Initialisation des LAI keywords depuis S3")
        initialize_lai_keywords(s3_io, config_bucket)
        
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


def run_ingest_for_active_clients(
    env_vars: Optional[Dict[str, Any]] = None,
    dry_run: bool = False,
    period_days: Optional[int] = None,
    force_refresh: bool = False,
    ingestion_mode: str = "balanced"
) -> Dict[str, Any]:
    """
    Orchestration de l'ingestion pour tous les clients actifs.
    
    Cette fonction découvre automatiquement les clients avec active: true
    et exécute l'ingestion pour chacun d'eux.
    
    Args:
        env_vars: Variables d'environnement (buckets, etc.)
        dry_run: Mode simulation sans écriture S3
        period_days: Nombre de jours à remonter (appliqué à tous les clients)
        force_refresh: Force la re-ingéstion même si déjà fait
        ingestion_mode: Mode d'ingéstion (strict/balanced/broad)
    
    Returns:
        Dict contenant les statistiques agrégées d'exécution
    """
    logger.info("Démarrage de l'ingéstion pour tous les clients actifs")
    start_time = time.time()
    
    # Validation des variables d'environnement
    env_vars = env_vars or {}
    config_bucket = env_vars.get('CONFIG_BUCKET')
    data_bucket = env_vars.get('DATA_BUCKET')
    
    if not config_bucket or not data_bucket:
        raise ValueError("Variables d'environnement manquantes : CONFIG_BUCKET, DATA_BUCKET")
    
    try:
        # Étape 1 : Découvrir les clients actifs
        logger.info("Découverte des clients actifs")
        all_configs = config_loader.load_all_client_configs(config_bucket)
        active_clients = config_loader.filter_active_clients(all_configs)
        
        if not active_clients:
            logger.warning("Aucun client actif trouvé")
            return {
                'execution_date': utils.get_current_datetime_iso(),
                'clients_discovered': len(all_configs),
                'clients_active': 0,
                'clients_processed': 0,
                'clients_succeeded': 0,
                'clients_failed': 0,
                'total_items_ingested': 0,
                'execution_time_seconds': round(time.time() - start_time, 2),
                'status': 'no_active_clients',
                'message': 'Aucun client actif trouvé'
            }
        
        logger.info(f"Clients actifs à traiter : {len(active_clients)} ({active_clients})")
        
        # Étape 2 : Traiter chaque client actif
        client_results = []
        clients_succeeded = 0
        clients_failed = 0
        total_items = 0
        
        for client_id in active_clients:
            logger.info(f"--- Traitement du client : {client_id} ---")
            
            try:
                # Exécuter l'ingéstion pour ce client
                result = run_ingest_for_client(
                    client_id=client_id,
                    sources=None,  # Utiliser toutes les sources du client
                    period_days=period_days,
                    from_date=None,
                    to_date=None,
                    force_refresh=force_refresh,
                    dry_run=dry_run,
                    ingestion_mode=ingestion_mode,
                    env_vars=env_vars
                )
                
                if result.get('status') == 'success':
                    clients_succeeded += 1
                    total_items += result.get('items_final', 0)
                    logger.info(f"Client {client_id} : succès - {result.get('items_final', 0)} items")
                else:
                    clients_failed += 1
                    logger.error(f"Client {client_id} : échec - {result.get('error', 'Erreur inconnue')}")
                
                client_results.append({
                    'client_id': client_id,
                    'status': result.get('status', 'unknown'),
                    'items_final': result.get('items_final', 0),
                    'execution_time': result.get('execution_time_seconds', 0),
                    'error': result.get('error')
                })
            
            except Exception as e:
                clients_failed += 1
                error_msg = str(e)
                logger.error(f"Client {client_id} : exception - {error_msg}")
                
                client_results.append({
                    'client_id': client_id,
                    'status': 'error',
                    'items_final': 0,
                    'execution_time': 0,
                    'error': error_msg
                })
        
        # Étape 3 : Agréger les résultats
        execution_time = time.time() - start_time
        
        result = {
            'execution_date': utils.get_current_datetime_iso(),
            'clients_discovered': len(all_configs),
            'clients_active': len(active_clients),
            'clients_processed': len(active_clients),
            'clients_succeeded': clients_succeeded,
            'clients_failed': clients_failed,
            'total_items_ingested': total_items,
            'execution_time_seconds': round(execution_time, 2),
            'dry_run': dry_run,
            'ingestion_mode': ingestion_mode,
            'status': 'success' if clients_failed == 0 else 'partial_success',
            'client_results': client_results
        }
        
        if clients_failed == 0:
            logger.info(f"Ingéstion multi-clients terminée avec succès : {clients_succeeded} clients, {total_items} items")
        else:
            logger.warning(f"Ingéstion multi-clients terminée avec erreurs : {clients_succeeded} succès, {clients_failed} échecs")
        
        return result
    
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Erreur lors de l'ingéstion multi-clients : {str(e)}", exc_info=True)
        
        return {
            'execution_date': utils.get_current_datetime_iso(),
            'clients_discovered': 0,
            'clients_active': 0,
            'clients_processed': 0,
            'clients_succeeded': 0,
            'clients_failed': 0,
            'total_items_ingested': 0,
            'execution_time_seconds': round(execution_time, 2),
            'dry_run': dry_run,
            'ingestion_mode': ingestion_mode,
            'status': 'error',
            'error': str(e)
        }


__all__ = [
    "run_ingest_for_client",
    "run_ingest_for_active_clients",
]