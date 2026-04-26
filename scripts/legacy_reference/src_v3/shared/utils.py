"""
Utilities pour Vectora Inbox V3.

Ce module fournit des fonctions utilitaires transverses :
- Gestion des dates et timestamps
- Calcul de hashes pour la déduplication
- Génération de run_id uniques
- Validation des données
- Utilitaires de logging

Responsabilités :
- Fonctions utilitaires réutilisables par tous les modules V3
- Gestion cohérente des formats de dates
- Calculs de hashes standardisés
- Validation des données d'entrée
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging
import hashlib
import uuid
from contextlib import contextmanager
import time

logger = logging.getLogger(__name__)


class PerformanceTimer:
    """Context manager pour mesurer les performances"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time


def performance_timer(func=None):
    """
    Décorateur pour mesurer le temps d'exécution d'une fonction
    Peut être utilisé comme décorateur ou context manager
    """
    if func is None:
        # Utilisé comme context manager
        return PerformanceTimer()
    
    # Utilisé comme décorateur
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {duration:.3f}s")
    
    return wrapper


def get_current_date_iso() -> str:
    """
    Retourne la date actuelle au format ISO8601 (YYYY-MM-DD).
    
    Returns:
        Date actuelle au format YYYY-MM-DD
    """
    return datetime.now().strftime('%Y-%m-%d')


def get_current_datetime_iso() -> str:
    """
    Retourne le timestamp actuel au format ISO8601 UTC.
    
    Returns:
        Timestamp actuel au format ISO8601 UTC
    """
    return datetime.utcnow().isoformat() + "Z"


def generate_run_id(client_id: str) -> str:
    """
    Génère un run_id unique pour V3.
    
    Format : {client_id}__{YYYYMMDD}_{HHMMSS}_{suffix}
    
    Args:
        client_id: Identifiant du client
    
    Returns:
        Run ID unique
    """
    now = datetime.now()
    date_part = now.strftime('%Y%m%d')
    time_part = now.strftime('%H%M%S')
    suffix = str(uuid.uuid4())[:8]  # 8 premiers caractères d'un UUID
    
    return f"{client_id}__{date_part}_{time_part}_{suffix}"


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


def calculate_item_id(source_key: str, url: str) -> str:
    """
    Calcule un item_id stable et déterministe.
    
    Format : {source_key}__{hash_url}
    
    Args:
        source_key: Clé de la source
        url: URL de l'article
    
    Returns:
        Item ID unique et stable
    """
    # Hash de l'URL pour avoir un ID stable
    url_hash = hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]
    return f"{source_key}__{url_hash}"


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


def validate_item_v3(item) -> bool:
    """
    Valide qu'un item V3 contient tous les champs requis.
    
    Args:
        item: Item à valider (StructuredItem ou Dict)
    
    Returns:
        True si l'item est valide, False sinon
    """
    required_fields = [
        'item_id', 'run_id', 'source_key', 'source_type', 'actor_type',
        'title', 'content', 'url', 'ingested_at', 'content_hash'
    ]
    
    for field in required_fields:
        # Gérer les StructuredItem (attributs) et les dict (clés)
        if hasattr(item, field):
            value = getattr(item, field)
        elif hasattr(item, 'get'):
            value = item.get(field)
        else:
            logger.warning(f"Item invalide - impossible d'accéder au champ '{field}'")
            return False
            
        if not value:
            title = getattr(item, 'title', None) or item.get('title', '') if hasattr(item, 'get') else ''
            logger.warning(f"Item invalide - champ manquant '{field}' : {title[:50]}...")
            return False
    
    # Validation du format de date published_at (optionnel)
    published_at = getattr(item, 'published_at', None) if hasattr(item, 'published_at') else item.get('published_at') if hasattr(item, 'get') else None
    if published_at:
        try:
            datetime.strptime(published_at, '%Y-%m-%d')
        except ValueError:
            title = getattr(item, 'title', None) or item.get('title', '') if hasattr(item, 'get') else ''
            logger.debug(f"Item avec date invalide mais conservé : {title[:50]}...")
            # Ne pas rejeter l'item, juste logger
    
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


def measure_duration_ms(start_time: datetime) -> int:
    """
    Calcule la durée en millisecondes depuis un timestamp de début.
    
    Args:
        start_time: Timestamp de début
    
    Returns:
        Durée en millisecondes
    """
    end_time = datetime.now()
    duration = end_time - start_time
    return int(duration.total_seconds() * 1000)


def format_human_duration(duration_ms: int) -> str:
    """
    Formate une durée en millisecondes en format lisible.
    
    Args:
        duration_ms: Durée en millisecondes
    
    Returns:
        Durée formatée (ex: "2.5s", "1m 30s")
    """
    if duration_ms < 1000:
        return f"{duration_ms}ms"
    elif duration_ms < 60000:
        return f"{duration_ms / 1000:.1f}s"
    else:
        minutes = duration_ms // 60000
        seconds = (duration_ms % 60000) // 1000
        return f"{minutes}m {seconds}s"


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Tronque un texte à une longueur maximale.
    
    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
    
    Returns:
        Texte tronqué avec "..." si nécessaire
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."