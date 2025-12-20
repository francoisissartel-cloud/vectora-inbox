"""
Vectora Core V2 - Modules Normalization

Ce package contient la logique métier spécifique à la Lambda normalize-score V2.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..shared import config_loader, s3_io, utils
from . import normalizer, matcher, scorer

logger = logging.getLogger(__name__)


def run_normalize_score_for_client(
    client_id: str,
    env_vars: Dict[str, str],
    period_days: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    target_date: Optional[str] = None,
    force_reprocess: bool = False,
    bedrock_model_override: Optional[str] = None,
    scoring_mode: str = "balanced"
) -> Dict[str, Any]:
    """
    Orchestration complète de la normalisation et du scoring pour un client.
    
    Args:
        client_id: Identifiant du client
        env_vars: Variables d'environnement (buckets, modèle Bedrock)
        period_days: Nombre de jours à analyser (optionnel)
        from_date: Date de début (ISO8601, optionnel)
        to_date: Date de fin (ISO8601, optionnel) 
        target_date: Date de référence pour le scoring (optionnel)
        force_reprocess: Force le retraitement même si déjà fait
        bedrock_model_override: Surcharge du modèle Bedrock
        scoring_mode: Mode de scoring (strict, balanced, broad)
    
    Returns:
        Dict avec statistiques d'exécution
    """
    start_time = datetime.now()
    logger.info(f"Démarrage normalisation/scoring pour client {client_id}")
    
    try:
        # 1. Chargement des configurations
        logger.info("Chargement des configurations...")
        client_config = config_loader.load_client_config(client_id, env_vars["CONFIG_BUCKET"])
        canonical_scopes = config_loader.load_canonical_scopes(env_vars["CONFIG_BUCKET"])
        canonical_prompts = config_loader.load_canonical_prompts(env_vars["CONFIG_BUCKET"])
        
        # 2. Identification du dernier run d'ingestion
        logger.info("Identification du dernier run d'ingestion...")
        last_run_path = _find_last_ingestion_run(client_id, env_vars["DATA_BUCKET"])
        if not last_run_path:
            raise ValueError(f"Aucun run d'ingestion trouvé pour le client {client_id}")
        
        logger.info(f"Dernier run identifié : {last_run_path}")
        
        # 3. Chargement des items ingérés avec validation stricte
        logger.info("Chargement des items ingérés...")
        items_path = f"{last_run_path}/items.json"
        
        # VALIDATION CRITIQUE: Vérifier que le chemin est bien S3 réel
        if "test" in items_path.lower() or "synthetic" in items_path.lower():
            raise ValueError(f"Chemin de données de test détecté: {items_path}")
        
        raw_items = s3_io.read_json_from_s3(env_vars["DATA_BUCKET"], items_path)
        
        if not raw_items:
            raise ValueError(f"Aucun item trouvé dans {items_path} - Pipeline arrêté")
        
        # VALIDATION CRITIQUE: Vérifier que les items sont réels (pas synthétiques)
        _validate_real_data_items(raw_items, items_path)
        
        logger.info(f"Items réels chargés et validés: {len(raw_items)} depuis {items_path}")
        
        logger.info(f"Items chargés : {len(raw_items)}")
        
        # 4. Normalisation via Bedrock avec parallélisation contrôlée + matching Bedrock
        logger.info("Normalisation des items via Bedrock...")
        bedrock_model = bedrock_model_override or env_vars["BEDROCK_MODEL_ID"]
        
        # Contrôle de la parallélisation (1 worker par défaut pour éviter throttling)
        max_workers = int(env_vars.get("MAX_BEDROCK_WORKERS", "1"))
        
        # NOUVEAU: Récupération des watch_domains et matching_config pour le matching Bedrock
        watch_domains = client_config.get('watch_domains', [])
        matching_config = client_config.get('matching_config', {})
        logger.info(f"Watch domains configurés: {len(watch_domains)}")
        logger.info(f"Configuration matching chargée: {matching_config.get('min_domain_score', 'défaut')}")
        
        normalized_items = normalizer.normalize_items_batch(
            raw_items, 
            canonical_scopes, 
            canonical_prompts,
            bedrock_model,
            env_vars["BEDROCK_REGION"],
            max_workers=max_workers,
            watch_domains=watch_domains,  # NOUVEAU: Passage des watch_domains
            matching_config=matching_config  # NOUVEAU: Passage de la config matching
        )
        
        if not normalized_items:
            logger.warning("Aucun item normalisé avec succès")
            return {
                "client_id": client_id,
                "status": "completed",
                "items_processed": 0,
                "processing_time_ms": 0,
                "warning": "no_items_normalized"
            }
        
        # 5. Matching aux domaines de veille (mode Bedrock-only ou hybride)
        if client_config.get('matching_config', {}).get('bedrock_only', False):
            # Mode Bedrock-only : utiliser directement les résultats Bedrock
            matched_items = normalized_items
            logger.info("Mode Bedrock-only activé : matching déterministe ignoré")
        else:
            # Mode hybride existant (fallback)
            logger.info("Matching déterministe aux domaines de veille...")
            matched_items = matcher.match_items_to_domains(
                normalized_items,
                client_config,
                canonical_scopes
            )
        
        # Log des résultats de matching combinés
        bedrock_matched = sum(1 for item in matched_items if item.get('matching_results', {}).get('bedrock_matching_used', False))
        total_matched = sum(1 for item in matched_items if item.get('matching_results', {}).get('matched_domains', []))
        logger.info(f"Matching combiné: {total_matched} items matchés ({bedrock_matched} via Bedrock)")
        
        # 6. Scoring de pertinence
        logger.info("Calcul des scores de pertinence...")
        scored_items = scorer.score_items(
            matched_items,
            client_config,
            canonical_scopes,
            scoring_mode,
            target_date
        )
        
        # 7. Écriture des résultats
        logger.info("Écriture des résultats...")
        # Correction: remplacer ingested par curated (sans slash initial)
        output_path = last_run_path.replace("ingested/", "curated/")
        output_key = f"{output_path}/items.json"
        s3_io.write_json_to_s3(env_vars["DATA_BUCKET"], output_key, scored_items)
        
        # 8. Statistiques détaillées
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Calcul des statistiques avancées
        stats = _calculate_detailed_statistics(
            raw_items, normalized_items, matched_items, scored_items
        )
        
        result = {
            "client_id": client_id,
            "status": "completed",
            "last_run_path": last_run_path,
            "output_path": output_key,
            "processing_time_ms": int(processing_time),
            "statistics": stats,
            "configuration": {
                "bedrock_model": bedrock_model,
                "bedrock_region": env_vars["BEDROCK_REGION"],
                "scoring_mode": scoring_mode,
                "max_workers": max_workers,
                "watch_domains_count": len(watch_domains),  # NOUVEAU
                "bedrock_matching_enabled": len(watch_domains) > 0  # NOUVEAU
            }
        }
        
        logger.info(f"Normalisation/scoring terminée : {result}")
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la normalisation/scoring : {str(e)}", exc_info=True)
        raise


def _find_last_ingestion_run(client_id: str, data_bucket: str) -> Optional[str]:
    """
    Trouve le dernier run d'ingestion robuste pour un client donné.
    
    Args:
        client_id: Identifiant du client
        data_bucket: Nom du bucket de données
    
    Returns:
        Chemin S3 du dernier run ou None si aucun trouvé
    """
    try:
        prefix = f"ingested/{client_id}/"
        
        # Lister tous les objets avec ce préfixe pour trouver les items.json
        object_keys = s3_io.list_objects_with_prefix(data_bucket, prefix)
        
        if not object_keys:
            logger.warning(f"Aucun objet trouvé pour {prefix}")
            return None
        
        # Filtrer pour ne garder que les fichiers items.json
        items_files = [key for key in object_keys if key.endswith('/items.json')]
        
        if not items_files:
            logger.warning(f"Aucun fichier items.json trouvé pour {prefix}")
            return None
        
        logger.info(f"Fichiers items.json trouvés: {items_files}")
        
        # Parser et trier les dates avec validation robuste
        valid_runs = []
        for items_file in items_files:
            # Extraire le chemin du run: ingested/client_id/YYYY/MM/DD/items.json
            run_path = items_file.replace('/items.json', '')
            
            # Extraire YYYY/MM/DD
            path_parts = run_path.replace(prefix, "").split("/")
            if len(path_parts) >= 3:
                try:
                    year, month, day = int(path_parts[0]), int(path_parts[1]), int(path_parts[2])
                    date_obj = datetime(year, month, day)
                    
                    # Vérifier la taille du fichier (éviter les fichiers vides)
                    try:
                        items_data = s3_io.read_json_from_s3(data_bucket, items_file)
                        if items_data and len(items_data) > 0:
                            valid_runs.append((date_obj, run_path, len(items_data)))
                            logger.debug(f"Run valide trouvé: {run_path} ({len(items_data)} items)")
                    except Exception as e:
                        logger.warning(f"Fichier items.json invalide dans {items_file}: {str(e)}")
                        continue
                    
                except ValueError as e:
                    logger.debug(f"Chemin de date invalide {run_path}: {str(e)}")
                    continue
        
        if not valid_runs:
            logger.warning(f"Aucun run valide trouvé pour le client {client_id}")
            return None
        
        # Trier par date décroissante et prendre le plus récent
        valid_runs.sort(key=lambda x: x[0], reverse=True)
        latest_run = valid_runs[0]
        
        logger.info(f"Dernier run trouvé: {latest_run[1]} ({latest_run[2]} items, date: {latest_run[0].strftime('%Y-%m-%d')})")
        return latest_run[1]
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche du dernier run : {str(e)}")
        return None


def _calculate_detailed_statistics(
    raw_items: List[Dict],
    normalized_items: List[Dict],
    matched_items: List[Dict],
    scored_items: List[Dict]
) -> Dict[str, Any]:
    """Calcule des statistiques détaillées du pipeline."""
    
    stats = {
        "items_input": len(raw_items),
        "items_normalized": len(normalized_items),
        "items_matched": 0,
        "items_scored": len(scored_items),
        "normalization_success_rate": 0.0,
        "matching_success_rate": 0.0,
        "score_distribution": {},
        "entity_statistics": {},
        "domain_statistics": {}
    }
    
    if len(raw_items) > 0:
        stats["normalization_success_rate"] = len(normalized_items) / len(raw_items)
    
    # Statistiques de matching
    matched_count = 0
    domain_matches = {}
    
    for item in matched_items:
        matching_results = item.get("matching_results", {})
        matched_domains = matching_results.get("matched_domains", [])
        
        if matched_domains:
            matched_count += 1
            for domain in matched_domains:
                domain_matches[domain] = domain_matches.get(domain, 0) + 1
    
    stats["items_matched"] = matched_count
    if len(matched_items) > 0:
        stats["matching_success_rate"] = matched_count / len(matched_items)
    
    stats["domain_statistics"] = domain_matches
    
    # Distribution des scores
    if scored_items:
        scores = [item.get("scoring_results", {}).get("final_score", 0) for item in scored_items]
        scores = [s for s in scores if s > 0]  # Exclure les scores nuls
        
        if scores:
            stats["score_distribution"] = {
                "min_score": min(scores),
                "max_score": max(scores),
                "avg_score": sum(scores) / len(scores),
                "high_scores_count": len([s for s in scores if s >= 10]),
                "medium_scores_count": len([s for s in scores if 5 <= s < 10]),
                "low_scores_count": len([s for s in scores if 0 < s < 5])
            }
    
    # Statistiques d'entités
    entity_counts = {"companies": 0, "molecules": 0, "technologies": 0, "trademarks": 0}
    
    for item in normalized_items:
        entities = item.get("normalized_content", {}).get("entities", {})
        for entity_type in entity_counts.keys():
            entity_list = entities.get(entity_type, [])
            if entity_list:
                entity_counts[entity_type] += len(entity_list)
    
    stats["entity_statistics"] = entity_counts
    
    return stats


def _validate_real_data_items(items: List[Dict], source_path: str) -> None:
    """
    Valide que les items proviennent de données réelles (pas synthétiques).
    
    Args:
        items: Liste des items à valider
        source_path: Chemin source des données
    
    Raises:
        ValueError: Si des données synthétiques sont détectées
    """
    if not items:
        return
    
    # Vérification 1: URLs factices
    synthetic_urls = ["example.com", "test.com", "fake.com"]
    for item in items[:5]:  # Vérifier les 5 premiers items
        url = item.get("url", "")
        if any(synthetic_url in url for synthetic_url in synthetic_urls):
            raise ValueError(f"URL synthétique détectée: {url} dans {source_path}")
    
    # Vérification 2: Titres de test connus
    synthetic_titles = [
        "Novartis Advances CAR-T Cell Therapy",
        "Roche Expands Oncology Pipeline", 
        "FDA Approves First Gene Therapy",
        "CRISPR-Cas9 Breakthrough",
        "Gilead Sciences Reports Positive Data"
    ]
    
    for item in items:
        title = item.get("title", "")
        if any(synthetic_title in title for synthetic_title in synthetic_titles):
            raise ValueError(f"Titre synthétique détecté: {title} dans {source_path}")
    
    # Vérification 3: Nombre d'items suspect (exactement 5 = probable test)
    if len(items) == 5:
        logger.warning(f"Nombre d'items suspect (5) - vérification renforcée pour {source_path}")
        # Vérifier si tous les items ont des URLs example.com
        example_count = sum(1 for item in items if "example.com" in item.get("url", ""))
        if example_count >= 3:
            raise ValueError(f"Dataset synthétique détecté: {example_count}/5 items avec example.com")
    
    logger.info(f"Validation données réelles OK: {len(items)} items validés")


# Ajout d'un gestionnaire de données pour la Phase 3.2
def find_last_ingestion_run(client_id: str, data_bucket: str) -> Optional[str]:
    """Interface publique pour trouver le dernier run d'ingestion."""
    return _find_last_ingestion_run(client_id, data_bucket)


def load_ingested_items(data_bucket: str, run_path: str) -> List[Dict]:
    """Charge les items ingérés depuis S3 avec validation."""
    try:
        items_path = f"{run_path}/items.json"
        items = s3_io.read_json_from_s3(data_bucket, items_path)
        
        if not items:
            raise ValueError(f"Aucun item trouvé dans {items_path}")
        
        # Validation des champs obligatoires
        validated_items = []
        for item in items:
            if not isinstance(item, dict):
                logger.warning("Item non-dict ignoré")
                continue
            
            # Vérification des champs minimums
            required_fields = ["title", "content", "published_at"]
            if all(field in item for field in required_fields):
                validated_items.append(item)
            else:
                logger.warning(f"Item avec champs manquants ignoré: {item.get('item_id', 'unknown')}")
        
        logger.info(f"Items chargés et validés: {len(validated_items)}/{len(items)}")
        return validated_items
        
    except Exception as e:
        logger.error(f"Erreur chargement items depuis {run_path}: {str(e)}")
        raise


def save_curated_items(data_bucket: str, client_id: str, items: List[Dict], run_date: str) -> str:
    """Sauvegarde les items curés avec métadonnées."""
    try:
        # Construction du chemin de sortie
        date_obj = datetime.fromisoformat(run_date.replace("Z", ""))
        output_path = f"curated/{client_id}/{date_obj.year:04d}/{date_obj.month:02d}/{date_obj.day:02d}"
        output_key = f"{output_path}/items.json"
        
        # Ajout de métadonnées
        curated_data = {
            "metadata": {
                "client_id": client_id,
                "processing_date": datetime.now().isoformat() + "Z",
                "source_run_date": run_date,
                "items_count": len(items),
                "pipeline_version": "v2.0"
            },
            "items": items
        }
        
        # Écriture S3
        s3_io.write_json_to_s3(data_bucket, output_key, curated_data)
        
        logger.info(f"Items curés sauvegardés: {output_key} ({len(items)} items)")
        return output_key
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde items curés: {str(e)}")
        raise


__all__ = [
    "run_normalize_score_for_client",
    "find_last_ingestion_run",
    "load_ingested_items",
    "save_curated_items"
]