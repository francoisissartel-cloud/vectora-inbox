"""
Utilitaires pour la gestion des dates dans Vectora Inbox.

Ce module fournit des fonctions pour :
- Calculer des fenêtres temporelles (from_date, to_date)
- Formater des dates en ISO8601
- Parser des dates depuis différents formats
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def compute_date_range(
    period_days: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
) -> Tuple[str, str]:
    """
    Calcule une fenêtre temporelle (from_date, to_date) en ISO8601.
    
    Logique :
    - Si from_date et to_date sont fournis : les utiliser directement
    - Sinon, si period_days est fourni : calculer from_date = aujourd'hui - period_days, to_date = aujourd'hui
    - Sinon : utiliser les 7 derniers jours par défaut
    
    Args:
        period_days: Nombre de jours à remonter dans le passé (optionnel)
        from_date: Date de début au format ISO8601 (optionnel)
        to_date: Date de fin au format ISO8601 (optionnel)
    
    Returns:
        Tuple (from_date, to_date) au format ISO8601 (YYYY-MM-DD)
    """
    if from_date and to_date:
        logger.info(f"Utilisation de la fenêtre temporelle explicite : {from_date} → {to_date}")
        return from_date, to_date
    
    if period_days:
        to_date_dt = datetime.now()
        from_date_dt = to_date_dt - timedelta(days=period_days)
        from_date = from_date_dt.strftime('%Y-%m-%d')
        to_date = to_date_dt.strftime('%Y-%m-%d')
        logger.info(f"Fenêtre temporelle calculée ({period_days} jours) : {from_date} → {to_date}")
        return from_date, to_date
    
    # Par défaut : 7 derniers jours
    to_date_dt = datetime.now()
    from_date_dt = to_date_dt - timedelta(days=7)
    from_date = from_date_dt.strftime('%Y-%m-%d')
    to_date = to_date_dt.strftime('%Y-%m-%d')
    logger.info(f"Fenêtre temporelle par défaut (7 jours) : {from_date} → {to_date}")
    return from_date, to_date


def get_current_date_iso() -> str:
    """
    Retourne la date actuelle au format ISO8601 (YYYY-MM-DD).
    
    Returns:
        Date actuelle en ISO8601
    """
    return datetime.now().strftime('%Y-%m-%d')


def get_current_datetime_iso() -> str:
    """
    Retourne la date et l'heure actuelles au format ISO8601 (YYYY-MM-DDTHH:MM:SSZ).
    
    Returns:
        Date et heure actuelles en ISO8601
    """
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
