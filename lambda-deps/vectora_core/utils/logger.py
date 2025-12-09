"""
Module logger - Configuration du logging.

Ce module configure le logger Python pour tracer l'exécution.
"""

import logging


def setup_logger(log_level: str = "INFO") -> logging.Logger:
    """
    Configure et retourne un logger Python.
    
    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configuré
    """
    # TODO: Implémenter la configuration du logger
    # 1. Créer un logger
    # 2. Définir le niveau (log_level)
    # 3. Configurer le format (timestamp, niveau, message)
    # 4. Retourner le logger
    raise NotImplementedError("setup_logger() sera implémenté dans une étape suivante")
