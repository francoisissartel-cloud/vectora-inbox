"""
Package d'ingestion des sources externes pour Vectora Inbox.

Ce package contient les modules pour :
- Récupérer les contenus bruts (fetcher)
- Parser les contenus en items structurés (parser)
"""

from vectora_core.ingestion import fetcher, parser

__all__ = ['fetcher', 'parser']
