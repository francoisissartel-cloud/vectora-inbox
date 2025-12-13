"""
Utilitaires pour la résolution de configuration dans Vectora Inbox.

Ce module fournit des fonctions pour :
- Résoudre la période temporelle selon la hiérarchie de priorité
- Extraire des paramètres de configuration client
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def resolve_period_days(
    payload_period_days: Optional[int],
    client_config: Dict[str, Any]
) -> int:
    """
    Résout la période à utiliser selon la hiérarchie de priorité.
    
    Hiérarchie (du plus prioritaire au moins prioritaire) :
    1. Payload Lambda explicite (event["period_days"])
    2. Configuration client (client_config.pipeline.default_period_days)
    3. Fallback global (7 jours)
    
    Args:
        payload_period_days: Valeur period_days du payload Lambda (peut être None)
        client_config: Configuration complète du client
    
    Returns:
        int: Nombre de jours à utiliser (toujours > 0)
    
    Examples:
        >>> resolve_period_days(14, {"pipeline": {"default_period_days": 30}})
        14  # Priorité au payload
        
        >>> resolve_period_days(None, {"pipeline": {"default_period_days": 30}})
        30  # Configuration client
        
        >>> resolve_period_days(None, {})
        7   # Fallback global
    """
    # 1. Priorité absolue au payload
    if payload_period_days is not None:
        if payload_period_days <= 0:
            logger.warning(f"period_days du payload invalide ({payload_period_days}), utilisation du fallback")
        else:
            logger.info(f"Utilisation period_days du payload : {payload_period_days} jours")
            return payload_period_days
    
    # 2. Configuration client
    pipeline_config = client_config.get('pipeline', {})
    client_period = pipeline_config.get('default_period_days')
    
    if client_period is not None:
        if isinstance(client_period, int) and client_period > 0:
            logger.info(f"Utilisation default_period_days du client : {client_period} jours")
            return client_period
        else:
            logger.warning(f"default_period_days du client invalide ({client_period}), utilisation du fallback")
    
    # 3. Fallback global
    logger.info("Utilisation du fallback global : 7 jours")
    return 7


def get_client_pipeline_config(client_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait la configuration pipeline du client avec des valeurs par défaut.
    
    Args:
        client_config: Configuration complète du client
    
    Returns:
        Dict contenant la configuration pipeline avec defaults
    """
    pipeline_config = client_config.get('pipeline', {})
    
    # Valeurs par défaut
    defaults = {
        'default_period_days': 7,
        'notes': 'Configuration pipeline par défaut'
    }
    
    # Merger avec les defaults
    result = {**defaults, **pipeline_config}
    
    return result