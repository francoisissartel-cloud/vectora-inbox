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
    import logging
    import time
    from datetime import datetime, timedelta
    from vectora_core.config import loader
    from vectora_core.matching import matcher
    from vectora_core.scoring import scorer
    from vectora_core.newsletter import assembler
    from vectora_core.storage import s3_client
    from vectora_core.utils import date_utils
    
    logger = logging.getLogger(__name__)
    logger.info(f"Démarrage du moteur de newsletter pour le client : {client_id}")
    
    start_time = time.time()
    
    # Récupérer les variables d'environnement
    env_vars = env_vars or {}
    config_bucket = env_vars.get('CONFIG_BUCKET')
    data_bucket = env_vars.get('DATA_BUCKET')
    newsletters_bucket = env_vars.get('NEWSLETTERS_BUCKET')
    bedrock_model_id = env_vars.get('BEDROCK_MODEL_ID')
    
    if not config_bucket or not data_bucket or not newsletters_bucket or not bedrock_model_id:
        raise ValueError("Variables d'environnement manquantes : CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_MODEL_ID")
    
    # Déterminer la target_date (date de référence pour la newsletter)
    if not target_date:
        target_date = date_utils.get_current_date_iso()
    
    # Étape 1 : Charger les configurations
    logger.info("Chargement des configurations depuis S3")
    client_config = loader.load_client_config(client_id, config_bucket)
    canonical_scopes = loader.load_canonical_scopes(config_bucket)
    scoring_rules = loader.load_scoring_rules(config_bucket)
    
    # Étape 2 : Calculer la fenêtre temporelle et collecter les items normalisés
    logger.info("Calcul de la fenêtre temporelle")
    from_date_calc, to_date_calc = date_utils.compute_date_range(period_days, from_date, to_date)
    
    logger.info(f"Collecte des items normalisés du {from_date_calc} au {to_date_calc}")
    all_items = _collect_normalized_items(data_bucket, client_id, from_date_calc, to_date_calc)
    
    logger.info(f"Total items collectés : {len(all_items)}")
    
    if len(all_items) == 0:
        logger.warning("Aucun item normalisé trouvé pour la période demandée")
        # Générer une newsletter minimale
        newsletter_md = _generate_empty_newsletter(client_config, target_date)
        s3_path = _write_newsletter_to_s3(newsletters_bucket, client_id, target_date, newsletter_md)
        
        execution_time = time.time() - start_time
        return {
            'client_id': client_id,
            'execution_date': date_utils.get_current_datetime_iso(),
            'target_date': target_date,
            'period': {'from_date': from_date_calc, 'to_date': to_date_calc},
            'items_analyzed': 0,
            'items_matched': 0,
            'items_selected': 0,
            'sections_generated': 0,
            's3_output_path': s3_path,
            'execution_time_seconds': round(execution_time, 2),
            'message': 'Aucun item trouvé - newsletter minimale générée'
        }
    
    # Étape 3 : Matching (Phase 2)
    logger.info("Phase 2 : Matching des items aux watch_domains")
    watch_domains = client_config.get('watch_domains', [])
    matched_items = matcher.match_items_to_domains(all_items, watch_domains, canonical_scopes)
    
    items_matched = sum(1 for item in matched_items if item.get('matched_domains'))
    logger.info(f"Items matchés : {items_matched}/{len(matched_items)}")
    
    # Étape 4 : Scoring (Phase 3)
    logger.info("Phase 3 : Scoring des items matchés")
    scored_items = scorer.score_items(matched_items, scoring_rules, watch_domains)
    
    # Étape 5 : Génération de la newsletter (Phase 4)
    logger.info("Phase 4 : Génération de la newsletter avec Bedrock")
    newsletter_md, stats, editorial_content = assembler.generate_newsletter(
        scored_items,
        client_config,
        bedrock_model_id,
        target_date,
        from_date_calc,
        to_date_calc
    )
    
    # Étape 6 : Écriture dans S3
    s3_path = _write_newsletter_to_s3(newsletters_bucket, client_id, target_date, newsletter_md, editorial_content)
    
    # Calculer le temps d'exécution
    execution_time = time.time() - start_time
    
    # Construire le résultat
    result = {
        'client_id': client_id,
        'execution_date': date_utils.get_current_datetime_iso(),
        'target_date': target_date,
        'period': {'from_date': from_date_calc, 'to_date': to_date_calc},
        'items_analyzed': len(all_items),
        'items_matched': items_matched,
        'items_selected': stats.get('items_selected', 0),
        'sections_generated': stats.get('sections_generated', 0),
        's3_output_path': s3_path,
        'execution_time_seconds': round(execution_time, 2),
        'message': 'Newsletter générée avec succès'
    }
    
    logger.info(f"Génération de newsletter terminée : {result}")
    
    return result


def _collect_normalized_items(data_bucket: str, client_id: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
    """
    Collecte tous les items normalisés depuis S3 pour une fenêtre temporelle.
    
    Args:
        data_bucket: Nom du bucket S3 de données
        client_id: Identifiant du client
        from_date: Date de début (YYYY-MM-DD)
        to_date: Date de fin (YYYY-MM-DD)
    
    Returns:
        Liste de tous les items normalisés
    """
    import logging
    from datetime import datetime, timedelta
    from vectora_core.storage import s3_client
    
    logger = logging.getLogger(__name__)
    all_items = []
    
    # Générer la liste des dates à parcourir
    from_dt = datetime.strptime(from_date, '%Y-%m-%d')
    to_dt = datetime.strptime(to_date, '%Y-%m-%d')
    
    current_dt = from_dt
    while current_dt <= to_dt:
        year = current_dt.strftime('%Y')
        month = current_dt.strftime('%m')
        day = current_dt.strftime('%d')
        
        key = f"normalized/{client_id}/{year}/{month}/{day}/items.json"
        
        try:
            items = s3_client.read_json_from_s3(data_bucket, key)
            if isinstance(items, list):
                all_items.extend(items)
                logger.info(f"Chargé {len(items)} items depuis {key}")
            else:
                logger.warning(f"Format inattendu pour {key} : attendu list, reçu {type(items)}")
        except Exception as e:
            logger.debug(f"Aucun fichier trouvé pour {key} : {e}")
        
        current_dt += timedelta(days=1)
    
    return all_items


def _generate_empty_newsletter(client_config: Dict[str, Any], target_date: str) -> str:
    """
    Génère une newsletter minimale quand aucun item n'est trouvé.
    
    Args:
        client_config: Configuration du client
        target_date: Date de référence
    
    Returns:
        Newsletter Markdown minimale
    """
    client_name = client_config.get('client_profile', {}).get('name', 'Intelligence Newsletter')
    language = client_config.get('client_profile', {}).get('language', 'en')
    
    if language == 'fr':
        title = f"# {client_name} – {target_date}\n\n"
        message = "Aucun signal critique cette semaine. Nous continuons de surveiller vos domaines d'intérêt.\n\n"
    else:
        title = f"# {client_name} – {target_date}\n\n"
        message = "No critical signals this week. We continue to monitor your domains of interest.\n\n"
    
    footer = "---\n\n*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*\n"
    
    return title + message + footer


def _write_newsletter_to_s3(
    newsletters_bucket: str,
    client_id: str,
    target_date: str,
    newsletter_md: str,
    editorial_content: Dict[str, Any] = None
) -> str:
    """
    Écrit la newsletter dans S3.
    
    Args:
        newsletters_bucket: Nom du bucket S3 de newsletters
        client_id: Identifiant du client
        target_date: Date de référence (YYYY-MM-DD)
        newsletter_md: Contenu Markdown de la newsletter
        editorial_content: Contenu éditorial JSON (optionnel)
    
    Returns:
        Chemin S3 complet (s3://bucket/key)
    """
    import logging
    from vectora_core.storage import s3_client
    
    logger = logging.getLogger(__name__)
    
    year, month, day = target_date.split('-')
    md_key = f"{client_id}/{year}/{month}/{day}/newsletter.md"
    
    logger.info(f"Écriture de la newsletter dans s3://{newsletters_bucket}/{md_key}")
    s3_client.write_text_to_s3(newsletters_bucket, md_key, newsletter_md, content_type='text/markdown')
    
    # Écrire aussi le JSON éditorial si fourni
    if editorial_content:
        json_key = f"{client_id}/{year}/{month}/{day}/newsletter.json"
        logger.info(f"Écriture du JSON éditorial dans s3://{newsletters_bucket}/{json_key}")
        s3_client.write_json_to_s3(newsletters_bucket, json_key, editorial_content)
    
    return f"s3://{newsletters_bucket}/{md_key}"


__all__ = [
    "run_ingest_normalize_for_client",
    "run_engine_for_client",
]
