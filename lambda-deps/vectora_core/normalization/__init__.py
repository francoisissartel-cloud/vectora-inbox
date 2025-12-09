"""
Package de normalisation des items pour Vectora Inbox.

Ce package contient les modules pour :
- Appeler Bedrock (bedrock_client)
- Détecter les entités par règles (entity_detector)
- Orchestrer la normalisation (normalizer)
"""

from vectora_core.normalization import bedrock_client, entity_detector, normalizer

__all__ = ['bedrock_client', 'entity_detector', 'normalizer']
