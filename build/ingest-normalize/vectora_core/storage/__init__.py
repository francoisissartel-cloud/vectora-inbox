"""
Package de gestion du stockage S3 pour Vectora Inbox.

Ce package contient les wrappers boto3 pour lire/écrire dans S3.
"""

from vectora_core.storage import s3_client

__all__ = ['s3_client']
