"""
Utilities pour Vectora Inbox V2.

Ce module fournit des fonctions utilitaires transverses :
- Gestion des dates et timestamps
- Calcul de hashes pour la déduplication
- Filtrage temporel des items
- Validation des données
- Utilitaires de logging

Responsabilités :
- Fonctions utilitaires réutilisables par tous les modules
- Gestion cohérente des formats de dates
- Calculs de hashes standardisés
- Validation des données d'entrée
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging
import hashlib

logger = logging.getLogger(__name__)


def get_current_date_iso() -> str:
    """
    Retourne la date actuelle au format ISO8601 (YYYY-MM-DD).
    
    Returns:
        Date actuelle au format YYYY-MM-DD
    """
    return datetime.now().strftime('%Y-%m-%d')


def get_current_datetime_iso() -> str:
    """
    Retourne le timestamp actuel au format ISO8601.
    
    Returns:
        Timestamp actuel au format ISO8601
    """
    return datetime.now().isoformat()


def compute_date_range(period_days: int, from_date: Optional[str] = None, to_date: Optional[str] = None) -> tuple[str, str]:
    """
    Calcule une fenêtre temporelle pour l'ingestion.
    
    Args:
        period_days: Nombre de jours à remonter dans le passé
        from_date: Date de début optionnelle (YYYY-MM-DD)
        to_date: Date de fin optionnelle (YYYY-MM-DD)
    
    Returns:
        Tuple (from_date, to_date) au format YYYY-MM-DD
    """
    if from_date and to_date:
        # Utiliser les dates fournies
        logger.info(f"Utilisation de la fenêtre temporelle fournie : {from_date} à {to_date}")
        return from_date, to_date
    
    # Calculer la fenêtre basée sur period_days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    
    from_date_calc = start_date.strftime('%Y-%m-%d')
    to_date_calc = end_date.strftime('%Y-%m-%d')
    
    logger.info(f"Fenêtre temporelle calculée ({period_days} jours) : {from_date_calc} à {to_date_calc}")
    return from_date_calc, to_date_calc


def apply_temporal_filter(items: List[Dict[str, Any]], cutoff_date_str: str, temporal_mode: str = "strict") -> List[Dict[str, Any]]:
    """
    Filtre les items selon leur date de publication.
    
    Args:
        items: Liste d'items avec champ 'published_at'
        cutoff_date_str: Date de coupure au format YYYY-MM-DD
        temporal_mode: Mode de filtrage ("strict" ou "flexible")
    
    Returns:
        Liste d'items dont la date >= cutoff_date (strict) ou tous les items récents (flexible)
    """
    if not items:
        return []
    
    cutoff_date = datetime.strptime(cutoff_date_str, '%Y-%m-%d')
    filtered_items = []
    items_without_date = 0
    items_kept_without_date = 0
    
    for item in items:
        published_at = item.get('published_at')
        
        if not published_at:
            items_without_date += 1
            if temporal_mode == "flexible":
                # Mode flexible : conserver les items sans date (probablement récents)
                filtered_items.append(item)
                items_kept_without_date += 1
                logger.debug(f"Item sans date conservé (mode flexible) : {item.get('title', '')[:50]}...")
            else:
                logger.debug(f"Item sans date ignoré (mode strict) : {item.get('title', '')[:50]}...")
            continue
        
        try:
            # Parser la date de l'item (format YYYY-MM-DD)
            item_date = datetime.strptime(published_at, '%Y-%m-%d')
            
            # Conserver si date >= cutoff_date
            if item_date >= cutoff_date:
                filtered_items.append(item)
            else:
                if temporal_mode == "flexible":
                    # Mode flexible : conserver aussi les items légèrement anciens si récemment récupérés
                    ingested_at = item.get('ingested_at', '')
                    if ingested_at and _is_recently_ingested(ingested_at, hours=24):
                        filtered_items.append(item)
                        logger.debug(f"Item ancien conservé (récemment ingéré) : {item.get('title', '')[:50]}...")
                    else:
                        logger.debug(f"Item trop ancien ignoré ({published_at}) : {item.get('title', '')[:50]}...")
                else:
                    logger.debug(f"Item trop ancien ignoré ({published_at}) : {item.get('title', '')[:50]}...")
        
        except ValueError as e:
            items_without_date += 1
            if temporal_mode == "flexible":
                # Mode flexible : conserver les items avec dates invalides (probablement récents)
                filtered_items.append(item)
                items_kept_without_date += 1
                logger.debug(f"Item avec date invalide conservé (mode flexible) : {item.get('title', '')[:50]}... - {e}")
            else:
                logger.debug(f"Item avec date invalide ignoré (mode strict) : {item.get('title', '')[:50]}... - {e}")
    
    if items_without_date > 0:
        if temporal_mode == "flexible":
            logger.info(f"Items sans date valide : {items_without_date} (conservés: {items_kept_without_date})")
        else:
            logger.info(f"Items sans date valide ignorés : {items_without_date}")
    
    logger.info(f"Filtre temporel ({temporal_mode}) : {len(filtered_items)}/{len(items)} items conservés")
    return filtered_items


def _is_recently_ingested(ingested_at: str, hours: int = 24) -> bool:
    """
    Vérifie si un item a été ingéré récemment.
    
    Args:
        ingested_at: Timestamp d'ingestion ISO8601
        hours: Nombre d'heures pour considérer comme "récent"
    
    Returns:
        True si l'item a été ingéré dans les dernières heures
    """
    try:
        ingested_time = datetime.fromisoformat(ingested_at.replace('Z', '+00:00'))
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return ingested_time >= cutoff_time
    except (ValueError, AttributeError):
        return False


def deduplicate_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Déduplique les items basé sur leur content_hash.
    
    Args:
        items: Liste d'items avec champ 'content_hash'
    
    Returns:
        Liste d'items dédupliqués (garde le premier de chaque hash)
    """
    if not items:
        return []
    
    seen_hashes = set()
    deduplicated_items = []
    duplicates_count = 0
    
    for item in items:
        content_hash = item.get('content_hash')
        
        if not content_hash:
            # Item sans hash, on le garde mais on log un warning
            logger.warning(f"Item sans content_hash : {item.get('title', '')[:50]}...")
            deduplicated_items.append(item)
            continue
        
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            deduplicated_items.append(item)
        else:
            duplicates_count += 1
            logger.debug(f"Item dupliqué ignoré : {item.get('title', '')[:50]}...")
    
    if duplicates_count > 0:
        logger.info(f"Déduplication : {duplicates_count} doublons supprimés")
    
    logger.info(f"Déduplication : {len(deduplicated_items)}/{len(items)} items uniques conservés")
    return deduplicated_items


def calculate_content_hash(content: str) -> str:
    """
    Calcule le hash SHA256 du contenu pour la déduplication.
    
    Args:
        content: Contenu textuel de l'item
    
    Returns:
        Hash SHA256 au format "sha256:..."
    """
    if not content:
        return "sha256:empty"
    
    # Normaliser le contenu (supprimer espaces en trop, convertir en minuscules)
    normalized_content = ' '.join(content.strip().lower().split())
    
    # Calculer le hash SHA256
    hash_object = hashlib.sha256(normalized_content.encode('utf-8'))
    hash_hex = hash_object.hexdigest()
    
    return f"sha256:{hash_hex}"


def validate_item(item: Dict[str, Any]) -> bool:
    """
    Valide qu'un item contient tous les champs requis.
    
    Args:
        item: Item à valider
    
    Returns:
        True si l'item est valide, False sinon
    """
    required_fields = [
        'item_id', 'source_key', 'source_type', 'title', 
        'content', 'url', 'ingested_at'
    ]
    
    for field in required_fields:
        if not item.get(field):
            logger.warning(f"Item invalide - champ manquant '{field}' : {item.get('title', '')[:50]}...")
            return False
    
    # Validation du format de date published_at (optionnel maintenant)
    published_at = item.get('published_at')
    if published_at:
        try:
            datetime.strptime(published_at, '%Y-%m-%d')
        except ValueError:
            logger.debug(f"Item avec date invalide mais conservé : {item.get('title', '')[:50]}...")
            # Ne pas rejeter l'item, juste logger
    
    return True


def validate_source(source: Dict[str, Any]) -> bool:
    """
    Valide qu'une source contient tous les champs requis.
    
    Args:
        source: Source à valider
    
    Returns:
        True si la source est valide, False sinon
    """
    required_fields = ['source_key', 'source_type', 'ingestion_mode', 'homepage_url']
    
    for field in required_fields:
        if not source.get(field):
            logger.warning(f"Source invalide - champ manquant '{field}' : {source.get('source_key', 'unknown')}")
            return False
    
    # Vérifier que l'URL d'ingestion correspondante existe
    ingestion_mode = source.get('ingestion_mode')
    if ingestion_mode == 'rss' and not source.get('rss_url'):
        logger.warning(f"Source RSS invalide - rss_url manquant : {source.get('source_key')}")
        return False
    elif ingestion_mode == 'html' and not source.get('html_url'):
        logger.warning(f"Source HTML invalide - html_url manquant : {source.get('source_key')}")
        return False
    elif ingestion_mode == 'api' and not source.get('api_url'):
        logger.warning(f"Source API invalide - api_url manquant : {source.get('source_key')}")
        return False
    
    return True


def safe_get_nested(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Récupère une valeur dans un dictionnaire imbriqué de manière sécurisée.
    
    Args:
        data: Dictionnaire source
        keys: Liste des clés pour naviguer dans l'imbrication
        default: Valeur par défaut si la clé n'existe pas
    
    Returns:
        Valeur trouvée ou valeur par défaut
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current