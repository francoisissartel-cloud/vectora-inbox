"""
Package de gestion des configurations pour Vectora Inbox.

Ce package contient les modules pour :
- Charger les configurations depuis S3 (loader)
- Résoudre les bouquets de sources (resolver)
"""

from vectora_core.config import loader, resolver

__all__ = ['loader', 'resolver']
