"""
Vectora Core - Bibliothèque métier pour Vectora Inbox MVP.

Ce package contient toute la logique métier de Vectora Inbox, indépendamment
d'AWS Lambda. Il est réutilisable dans d'autres contextes (CLI, notebooks, tests).

Modules principaux :
- config : chargement et résolution des configurations (canonical + client)
- ingestion : récupération des contenus bruts (RSS, APIs)
- normalization : transformation en items structurés (avec Bedrock)
- matching : détermination des items pertinents par domaine
- scoring : calcul des scores de pertinence
- newsletter : assemblage de la newsletter finale (avec Bedrock)
- storage : lecture/écriture S3
- utils : utilitaires transverses (logging, dates)

Fonctions publiques principales :
- run_ingest_normalize_for_client() : orchestration ingestion + normalisation
- run_engine_for_client() : orchestration matching + scoring + newsletter
"""

from typing import Any, Dict, List, Optional


def run_ingest_normalize_for_client(
    client_id: str,
    sources: Optional[List[str]] = None,
    period_days: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    env_vars: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Orchestration de l'ingestion et de la normalisation pour un client.
    
    Cette fonction implémente les Phases 1A et 1B du workflow Vectora Inbox :
    - Phase 1A (Ingestion) : récupération des contenus bruts depuis les sources externes
    - Phase 1B (Normalisation) : transformation en items structurés avec Bedrock
    
    Processus :
    1. Charger la configuration client et les scopes canonical depuis S3
    2. Résoudre les bouquets de sources (développer les source_key)
    3. Pour chaque source : récupérer le contenu brut (HTTP/RSS)
    4. Parser les contenus bruts en items structurés
    5. Normaliser chaque item (détection d'entités + classification + résumé)
    6. Écrire les items normalisés dans S3 (DATA_BUCKET)
    
    Args:
        client_id: Identifiant unique du client (ex: "lai_weekly")
        sources: Liste optionnelle de source_key à traiter (surcharge la config)
        period_days: Nombre de jours à remonter dans le passé
        from_date: Date de début (ISO8601)
        to_date: Date de fin (ISO8601)
        env_vars: Variables d'environnement (buckets, modèle Bedrock, etc.)
    
    Returns:
        Dict contenant les statistiques d'exécution :
            - client_id (str)
            - execution_date (str)
            - sources_processed (int)
            - items_ingested (int)
            - items_normalized (int)
            - s3_output_path (str)
            - execution_time_seconds (float)
    
    Raises:
        Exception: En cas d'erreur lors du chargement des configs ou de l'ingestion
    """
    import logging
    import time
    from vectora_core.config import loader, resolver
    from vectora_core.ingestion import fetcher, parser
    from vectora_core.normalization import normalizer
    from vectora_core.storage import s3_client
    from vectora_core.utils import date_utils
    
    logger = logging.getLogger(__name__)
    logger.info(f"Démarrage de l'ingestion + normalisation pour le client : {client_id}")
    
    start_time = time.time()
    
    # Récupérer les variables d'environnement
    env_vars = env_vars or {}
    config_bucket = env_vars.get('CONFIG_BUCKET')
    data_bucket = env_vars.get('DATA_BUCKET')
    bedrock_model_id = env_vars.get('BEDROCK_MODEL_ID')
    
    if not config_bucket or not data_bucket or not bedrock_model_id:
        raise ValueError("Variables d'environnement manquantes : CONFIG_BUCKET, DATA_BUCKET, BEDROCK_MODEL_ID")
    
    # Étape 1 : Charger les configurations
    logger.info("Chargement des configurations depuis S3")
    client_config = loader.load_client_config(client_id, config_bucket)
    canonical_scopes = loader.load_canonical_scopes(config_bucket)
    source_catalog = loader.load_source_catalog(config_bucket)
    
    # Étape 2 : Résoudre les sources à traiter
    logger.info("Résolution des sources à traiter")
    resolved_sources = resolver.resolve_sources_for_client(client_config, source_catalog)
    
    # Si des sources spécifiques sont demandées, filtrer
    if sources:
        logger.info(f"Filtrage sur les sources spécifiques : {sources}")
        resolved_sources = [s for s in resolved_sources if s.get('source_key') in sources]
    
    logger.info(f"Nombre de sources à traiter : {len(resolved_sources)}")
    
    # Étape 3 : Ingestion et parsing
    logger.info("Phase 1A : Ingestion des sources")
    all_raw_items = []
    sources_processed = 0
    
    for source_meta in resolved_sources:
        source_key = source_meta.get('source_key')
        
        # Récupérer le contenu brut
        raw_content = fetcher.fetch_source(source_meta)
        
        if raw_content:
            # Parser le contenu en items bruts
            raw_items = parser.parse_source_content(raw_content, source_meta)
            all_raw_items.extend(raw_items)
            sources_processed += 1
            logger.info(f"Source {source_key} : {len(raw_items)} items récupérés")
        else:
            logger.warning(f"Source {source_key} : aucun contenu récupéré")
    
    logger.info(f"Total items bruts récupérés : {len(all_raw_items)}")
    
    # Étape 4 : Normalisation
    logger.info("Phase 1B : Normalisation des items avec Bedrock")
    normalized_items = normalizer.normalize_items_batch(
        all_raw_items,
        canonical_scopes,
        bedrock_model_id
    )
    
    logger.info(f"Total items normalisés : {len(normalized_items)}")
    
    # Étape 5 : Écriture dans S3
    current_date = date_utils.get_current_date_iso()
    year, month, day = current_date.split('-')
    
    s3_key = f"normalized/{client_id}/{year}/{month}/{day}/items.json"
    
    logger.info(f"Écriture des items normalisés dans s3://{data_bucket}/{s3_key}")
    s3_client.write_json_to_s3(data_bucket, s3_key, normalized_items)
    
    # Calculer le temps d'exécution
    execution_time = time.time() - start_time
    
    # Construire le résultat
    result = {
        'client_id': client_id,
        'execution_date': date_utils.get_current_datetime_iso(),
        'sources_processed': sources_processed,
        'items_ingested': len(all_raw_items),
        'items_normalized': len(normalized_items),
        's3_output_path': f"s3://{data_bucket}/{s3_key}",
        'execution_time_seconds': round(execution_time, 2)
    }
    
    logger.info(f"Ingestion + normalisation terminée : {result}")
    
    return result


def run_engine_for_client(
    client_id: str,
    period_days: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    target_date: Optional[str] = None,
    env_vars: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Orchestration du moteur de newsletter pour un client.
    
    Cette fonction :
    1. Charge la config client + canonical depuis S3
    2. Collecte les items normalisés depuis S3 (sur la fenêtre temporelle)
    3. Matching (Phase 2) : détermine les items pertinents par watch_domain
    4. Scoring (Phase 3) : calcule les scores et trie les items
    5. Newsletter (Phase 4) : génère la newsletter avec Bedrock
    6. Écrit la newsletter dans S3
    
    Args:
        client_id: Identifiant unique du client (ex: "lai_weekly")
        period_days: Nombre de jours à analyser
        from_date: Date de début (ISO8601)
        to_date: Date de fin (ISO8601)
        target_date: Date de référence pour la newsletter (ISO8601)
        env_vars: Variables d'environnement (buckets, modèle Bedrock, etc.)
    
    Returns:
        Dict contenant les statistiques d'exécution :
            - client_id (str)
            - execution_date (str)
            - target_date (str)
            - items_analyzed (int)
            - items_matched (int)
            - items_selected (int)
            - sections_generated (int)
            - s3_output_path (str)
            - execution_time_seconds (float)
    """
    # TODO: Implémenter l'orchestration complète
    # 1. Charger config client + canonical
    # 2. Collecter les items normalisés depuis S3
    # 3. Matching : calculer les intersections avec les watch_domains
    # 4. Scoring : calculer les scores et trier
    # 5. Newsletter : appeler Bedrock + assembler + formater
    # 6. Écrire la newsletter dans S3
    raise NotImplementedError("run_engine_for_client() sera implémenté dans une étape suivante")


__all__ = [
    "run_ingest_normalize_for_client",
    "run_engine_for_client",
]
