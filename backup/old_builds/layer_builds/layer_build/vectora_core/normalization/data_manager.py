"""
Gestionnaire de données pour la normalisation V2.

Ce module fournit des fonctions robustes pour la gestion des données
d'ingestion et de curation avec validation et gestion d'erreurs.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from ..shared import s3_io

logger = logging.getLogger(__name__)


def find_last_ingestion_run(client_id: str, data_bucket: str) -> Optional[str]:
    """
    Trouve le dernier run d'ingestion pour un client donné avec validation robuste.
    
    Args:
        client_id: Identifiant du client
        data_bucket: Nom du bucket de données
    
    Returns:
        Chemin S3 du dernier run ou None si aucun trouvé
    """
    try:
        prefix = f"ingested/{client_id}/"
        
        # Lister tous les préfixes de dates
        date_prefixes = s3_io.list_s3_prefixes(data_bucket, prefix)
        
        if not date_prefixes:
            logger.warning(f"Aucun préfixe trouvé pour {prefix}")
            return None
        
        logger.debug(f"Préfixes trouvés: {len(date_prefixes)}")
        
        # Parser et valider les runs
        valid_runs = []
        for date_prefix in date_prefixes:
            run_info = _validate_ingestion_run(data_bucket, date_prefix)
            if run_info:
                valid_runs.append(run_info)
        
        if not valid_runs:
            logger.warning(f"Aucun run valide trouvé pour le client {client_id}")
            return None
        
        # Trier par date décroissante et prendre le plus récent
        valid_runs.sort(key=lambda x: x[0], reverse=True)
        latest_run = valid_runs[0]
        
        logger.info(
            f"Dernier run trouvé: {latest_run[1]} "
            f"({latest_run[2]} items, {latest_run[0].strftime('%Y-%m-%d')})"
        )
        
        return latest_run[1]
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche du dernier run : {str(e)}")
        return None


def find_ingestion_runs_in_period(
    client_id: str, 
    data_bucket: str, 
    period_days: int
) -> List[str]:
    """
    Trouve tous les runs d'ingestion dans une période donnée.
    
    Args:
        client_id: Identifiant du client
        data_bucket: Nom du bucket de données
        period_days: Nombre de jours à analyser
    
    Returns:
        Liste des chemins S3 des runs dans la période
    """
    try:
        prefix = f"ingested/{client_id}/"
        
        # Date limite
        cutoff_date = datetime.now() - timedelta(days=period_days)
        
        # Lister tous les préfixes de dates
        date_prefixes = s3_io.list_s3_prefixes(data_bucket, prefix)
        
        if not date_prefixes:
            return []
        
        # Filtrer les runs dans la période
        valid_runs = []
        for date_prefix in date_prefixes:
            run_info = _validate_ingestion_run(data_bucket, date_prefix)
            if run_info and run_info[0] >= cutoff_date:
                valid_runs.append(run_info[1])  # Chemin seulement
        
        # Trier par date décroissante
        valid_runs.sort(reverse=True)
        
        logger.info(f"Runs trouvés dans les {period_days} derniers jours: {len(valid_runs)}")
        return valid_runs
        
    except Exception as e:
        logger.error(f"Erreur recherche runs période: {str(e)}")
        return []


def load_ingested_items(data_bucket: str, run_path: str) -> List[Dict]:
    """
    Charge les items ingérés depuis S3 avec validation complète.
    
    Args:
        data_bucket: Nom du bucket de données
        run_path: Chemin du run d'ingestion
    
    Returns:
        Liste des items validés
    """
    try:
        items_path = f"{run_path}/items.json"
        logger.debug(f"Chargement items depuis: {items_path}")
        
        # Chargement depuis S3
        raw_data = s3_io.read_json_from_s3(data_bucket, items_path)
        
        if not raw_data:
            raise ValueError(f"Aucune donnée trouvée dans {items_path}")
        
        # Gestion des formats (avec ou sans metadata wrapper)
        if isinstance(raw_data, dict) and "items" in raw_data:
            items = raw_data["items"]
            metadata = raw_data.get("metadata", {})
            logger.debug(f"Format avec metadata: {metadata}")
        else:
            items = raw_data
        
        if not isinstance(items, list):
            raise ValueError(f"Format items invalide: {type(items)}")
        
        # Validation des items
        validated_items = []
        validation_stats = {"total": len(items), "valid": 0, "invalid": 0}
        
        for i, item in enumerate(items):
            validation_result = _validate_ingested_item(item, i)
            if validation_result["valid"]:
                validated_items.append(validation_result["item"])
                validation_stats["valid"] += 1
            else:
                validation_stats["invalid"] += 1
                logger.warning(f"Item {i} invalide: {validation_result['reason']}")
        
        logger.info(
            f"Items chargés: {validation_stats['valid']}/{validation_stats['total']} valides "
            f"({validation_stats['invalid']} invalides)"
        )
        
        return validated_items
        
    except Exception as e:
        logger.error(f"Erreur chargement items depuis {run_path}: {str(e)}")
        raise


def save_curated_items(
    data_bucket: str, 
    client_id: str, 
    items: List[Dict], 
    run_date: str,
    source_run_path: Optional[str] = None
) -> str:
    """
    Sauvegarde les items curés avec métadonnées complètes.
    
    Args:
        data_bucket: Nom du bucket de données
        client_id: Identifiant du client
        items: Items curés à sauvegarder
        run_date: Date du run (ISO format)
        source_run_path: Chemin du run source (optionnel)
    
    Returns:
        Chemin S3 de sauvegarde
    """
    try:
        # Construction du chemin de sortie
        if "T" in run_date:
            date_obj = datetime.fromisoformat(run_date.replace("Z", ""))
        else:
            date_obj = datetime.strptime(run_date, "%Y-%m-%d")
        
        output_path = f"curated/{client_id}/{date_obj.year:04d}/{date_obj.month:02d}/{date_obj.day:02d}"
        output_key = f"{output_path}/items.json"
        
        # Calcul des statistiques
        stats = _calculate_curation_statistics(items)
        
        # Construction des métadonnées complètes
        metadata = {
            "client_id": client_id,
            "processing_date": datetime.now().isoformat() + "Z",
            "source_run_date": run_date,
            "source_run_path": source_run_path,
            "pipeline_version": "v2.0",
            "items_count": len(items),
            "statistics": stats
        }
        
        # Données finales
        curated_data = {
            "metadata": metadata,
            "items": items
        }
        
        # Écriture S3
        s3_io.write_json_to_s3(data_bucket, output_key, curated_data)
        
        logger.info(
            f"Items curés sauvegardés: {output_key} "
            f"({len(items)} items, score moyen: {stats.get('avg_score', 0):.1f})"
        )
        
        return output_key
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde items curés: {str(e)}")
        raise


def _validate_ingestion_run(data_bucket: str, date_prefix: str) -> Optional[Tuple[datetime, str, int]]:
    """
    Valide un run d'ingestion et retourne ses informations.
    
    Args:
        data_bucket: Nom du bucket
        date_prefix: Préfixe de date à valider
    
    Returns:
        Tuple (date, chemin, nombre_items) ou None si invalide
    """
    try:
        # Extraction de la date depuis le préfixe
        # Format attendu: ingested/client_id/YYYY/MM/DD/
        parts = date_prefix.strip("/").split("/")
        if len(parts) < 5:  # ingested, client_id, YYYY, MM, DD
            return None
        
        year, month, day = int(parts[-3]), int(parts[-2]), int(parts[-1])
        date_obj = datetime(year, month, day)
        
        # Vérification que le fichier items.json existe
        items_key = f"{date_prefix}/items.json"
        if not s3_io.object_exists(data_bucket, items_key):
            return None
        
        # Vérification de la validité du fichier
        try:
            items_data = s3_io.read_json_from_s3(data_bucket, items_key)
            if not items_data:
                return None
            
            # Comptage des items
            if isinstance(items_data, dict) and "items" in items_data:
                items_count = len(items_data["items"])
            elif isinstance(items_data, list):
                items_count = len(items_data)
            else:
                return None
            
            if items_count == 0:
                return None
            
            return (date_obj, date_prefix.rstrip("/"), items_count)
            
        except Exception:
            return None
        
    except (ValueError, IndexError):
        return None


def _validate_ingested_item(item: Any, index: int) -> Dict[str, Any]:
    """
    Valide un item ingéré individuel.
    
    Args:
        item: Item à valider
        index: Index de l'item
    
    Returns:
        Dictionnaire avec résultat de validation
    """
    if not isinstance(item, dict):
        return {
            "valid": False,
            "reason": f"Item {index} n'est pas un dictionnaire",
            "item": None
        }
    
    # Champs obligatoires
    required_fields = ["title", "content", "published_at"]
    missing_fields = [field for field in required_fields if field not in item or not item[field]]
    
    if missing_fields:
        return {
            "valid": False,
            "reason": f"Champs manquants: {missing_fields}",
            "item": None
        }
    
    # Validation de la date
    try:
        published_at = item["published_at"]
        if "T" in published_at:
            datetime.fromisoformat(published_at.replace("Z", ""))
        else:
            datetime.strptime(published_at, "%Y-%m-%d")
    except (ValueError, TypeError):
        return {
            "valid": False,
            "reason": f"Date invalide: {item.get('published_at')}",
            "item": None
        }
    
    # Validation du contenu
    title = item["title"].strip()
    content = item["content"].strip()
    
    if len(title) < 5 or len(content) < 10:
        return {
            "valid": False,
            "reason": "Titre ou contenu trop court",
            "item": None
        }
    
    # Item valide - nettoyage optionnel
    cleaned_item = item.copy()
    cleaned_item["title"] = title
    cleaned_item["content"] = content
    
    # Ajout d'un ID si manquant
    if "item_id" not in cleaned_item:
        cleaned_item["item_id"] = f"item_{index}_{hash(title) % 10000}"
    
    return {
        "valid": True,
        "reason": "Item valide",
        "item": cleaned_item
    }


def _calculate_curation_statistics(items: List[Dict]) -> Dict[str, Any]:
    """
    Calcule les statistiques de curation.
    
    Args:
        items: Items curés
    
    Returns:
        Dictionnaire de statistiques
    """
    if not items:
        return {}
    
    stats = {
        "total_items": len(items),
        "normalized_items": 0,
        "matched_items": 0,
        "scored_items": 0,
        "avg_score": 0.0,
        "max_score": 0.0,
        "min_score": float('inf'),
        "entity_counts": {"companies": 0, "molecules": 0, "technologies": 0, "trademarks": 0},
        "event_types": {},
        "domain_matches": {}
    }
    
    scores = []
    
    for item in items:
        # Statistiques de normalisation
        if "normalized_content" in item:
            stats["normalized_items"] += 1
            
            # Comptage des entités
            entities = item["normalized_content"].get("entities", {})
            for entity_type in stats["entity_counts"]:
                entity_list = entities.get(entity_type, [])
                stats["entity_counts"][entity_type] += len(entity_list)
            
            # Types d'événements
            event_type = item["normalized_content"].get("event_classification", {}).get("primary_type", "unknown")
            stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
        
        # Statistiques de matching
        if "matching_results" in item:
            matching_results = item["matching_results"]
            matched_domains = matching_results.get("matched_domains", [])
            if matched_domains:
                stats["matched_items"] += 1
                for domain in matched_domains:
                    stats["domain_matches"][domain] = stats["domain_matches"].get(domain, 0) + 1
        
        # Statistiques de scoring
        if "scoring_results" in item:
            stats["scored_items"] += 1
            score = item["scoring_results"].get("final_score", 0)
            if score > 0:
                scores.append(score)
                stats["max_score"] = max(stats["max_score"], score)
                stats["min_score"] = min(stats["min_score"], score)
    
    # Calcul des moyennes
    if scores:
        stats["avg_score"] = sum(scores) / len(scores)
    
    if stats["min_score"] == float('inf'):
        stats["min_score"] = 0.0
    
    return stats