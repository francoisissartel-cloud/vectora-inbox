"""
Module de gestion des opérations S3 pour Vectora Inbox.

Ce module fournit des wrappers simples autour de boto3 pour :
- Lire des fichiers YAML et JSON depuis S3
- Écrire des fichiers JSON et texte dans S3

Toutes les fonctions gèrent les erreurs de manière explicite et loguent
les opérations importantes.
"""

import json
import logging
from typing import Any, Dict

import boto3
import yaml
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_s3_client():
    """
    Retourne un client boto3 S3.
    
    Returns:
        Client boto3 S3 configuré
    """
    return boto3.client('s3')


def read_yaml_from_s3(bucket: str, key: str) -> Dict[str, Any]:
    """
    Lit un fichier YAML depuis S3 et le parse en dictionnaire Python.
    
    Args:
        bucket: Nom du bucket S3
        key: Clé S3 du fichier (chemin dans le bucket)
    
    Returns:
        Dictionnaire Python contenant les données YAML
    
    Raises:
        ClientError: Si le fichier n'existe pas ou n'est pas accessible
        yaml.YAMLError: Si le fichier n'est pas un YAML valide
    """
    try:
        s3 = get_s3_client()
        logger.info(f"Lecture du fichier YAML depuis s3://{bucket}/{key}")
        
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        data = yaml.safe_load(content)
        
        logger.info(f"Fichier YAML chargé avec succès : {len(content)} caractères")
        return data
    
    except ClientError as e:
        logger.error(f"Erreur lors de la lecture de s3://{bucket}/{key}: {e}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Erreur de parsing YAML pour s3://{bucket}/{key}: {e}")
        raise


def read_json_from_s3(bucket: str, key: str) -> Dict[str, Any]:
    """
    Lit un fichier JSON depuis S3 et le parse en dictionnaire Python.
    
    Args:
        bucket: Nom du bucket S3
        key: Clé S3 du fichier
    
    Returns:
        Dictionnaire Python contenant les données JSON
    
    Raises:
        ClientError: Si le fichier n'existe pas ou n'est pas accessible
        json.JSONDecodeError: Si le fichier n'est pas un JSON valide
    """
    try:
        s3 = get_s3_client()
        logger.info(f"Lecture du fichier JSON depuis s3://{bucket}/{key}")
        
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        data = json.loads(content)
        
        logger.info(f"Fichier JSON chargé avec succès")
        return data
    
    except ClientError as e:
        logger.error(f"Erreur lors de la lecture de s3://{bucket}/{key}: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Erreur de parsing JSON pour s3://{bucket}/{key}: {e}")
        raise


def write_json_to_s3(bucket: str, key: str, data: Any) -> None:
    """
    Écrit des données Python en JSON dans S3.
    
    Args:
        bucket: Nom du bucket S3
        key: Clé S3 du fichier de destination
        data: Données Python à sérialiser en JSON (dict, list, etc.)
    
    Raises:
        ClientError: Si l'écriture échoue
    """
    try:
        s3 = get_s3_client()
        logger.info(f"Écriture du fichier JSON vers s3://{bucket}/{key}")
        
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json_content.encode('utf-8'),
            ContentType='application/json'
        )
        
        logger.info(f"Fichier JSON écrit avec succès : {len(json_content)} caractères")
    
    except ClientError as e:
        logger.error(f"Erreur lors de l'écriture vers s3://{bucket}/{key}: {e}")
        raise


def write_text_to_s3(bucket: str, key: str, text: str, content_type: str = 'text/plain') -> None:
    """
    Écrit du texte brut dans S3.
    
    Args:
        bucket: Nom du bucket S3
        key: Clé S3 du fichier de destination
        text: Contenu texte à écrire
        content_type: Type MIME du contenu (par défaut: text/plain)
    
    Raises:
        ClientError: Si l'écriture échoue
    """
    try:
        s3 = get_s3_client()
        logger.info(f"Écriture du fichier texte vers s3://{bucket}/{key}")
        
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=text.encode('utf-8'),
            ContentType=content_type
        )
        
        logger.info(f"Fichier texte écrit avec succès : {len(text)} caractères")
    
    except ClientError as e:
        logger.error(f"Erreur lors de l'écriture vers s3://{bucket}/{key}: {e}")
        raise
