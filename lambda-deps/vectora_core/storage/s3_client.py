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


def write_raw_items_to_s3(bucket: str, client_id: str, run_id: str, raw_items_by_source: Dict[str, Any]) -> str:
    """
    Écrit les items RAW d'un run dans S3 avec la structure par run.
    
    Structure créée :
    raw/{client_id}/YYYY/MM/DD/{run_id}/
    ├── source_metadata.json
    └── sources/
        ├── {source_key_1}.json
        ├── {source_key_2}.json
        └── ...
    
    Args:
        bucket: Nom du bucket S3
        client_id: Identifiant du client
        run_id: Identifiant du run
        raw_items_by_source: Dict {source_key: [items]} des items RAW par source
    
    Returns:
        Préfixe S3 du run (raw/{client_id}/YYYY/MM/DD/{run_id}/)
    
    Raises:
        ClientError: Si l'écriture échoue
    """
    from datetime import datetime
    
    # Extraire la date du run_id (format: run_YYYYMMDDTHHMMSS{microseconds}Z)
    date_part = run_id[4:12]  # YYYYMMDD
    year = date_part[:4]
    month = date_part[4:6]
    day = date_part[6:8]
    
    run_prefix = f"raw/{client_id}/{year}/{month}/{day}/{run_id}"
    
    logger.info(f"Écriture des items RAW pour le run {run_id} dans s3://{bucket}/{run_prefix}/")
    
    # Écrire les métadonnées du run
    metadata = {
        "run_id": run_id,
        "client_id": client_id,
        "execution_date": datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "sources_count": len(raw_items_by_source),
        "total_items": sum(len(items) for items in raw_items_by_source.values()),
        "sources": list(raw_items_by_source.keys())
    }
    
    metadata_key = f"{run_prefix}/source_metadata.json"
    write_json_to_s3(bucket, metadata_key, metadata)
    
    # Écrire chaque source dans un fichier séparé
    for source_key, items in raw_items_by_source.items():
        source_file_key = f"{run_prefix}/sources/{source_key}.json"
        write_json_to_s3(bucket, source_file_key, items)
        logger.info(f"Source {source_key} : {len(items)} items écrits")
    
    logger.info(f"Run {run_id} écrit avec succès : {len(raw_items_by_source)} sources, {metadata['total_items']} items")
    
    return run_prefix


def read_raw_items_from_s3(bucket: str, run_prefix: str) -> Dict[str, Any]:
    """
    Lit les items RAW d'un run depuis S3.
    
    Args:
        bucket: Nom du bucket S3
        run_prefix: Préfixe du run (raw/{client_id}/YYYY/MM/DD/{run_id}/)
    
    Returns:
        Dict {source_key: [items]} des items RAW par source
    
    Raises:
        ClientError: Si la lecture échoue
    """
    logger.info(f"Lecture des items RAW depuis s3://{bucket}/{run_prefix}/")
    
    # Lire les métadonnées pour connaître les sources
    metadata_key = f"{run_prefix}/source_metadata.json"
    metadata = read_json_from_s3(bucket, metadata_key)
    
    raw_items_by_source = {}
    
    # Lire chaque source
    for source_key in metadata.get('sources', []):
        source_file_key = f"{run_prefix}/sources/{source_key}.json"
        try:
            items = read_json_from_s3(bucket, source_file_key)
            raw_items_by_source[source_key] = items
            logger.info(f"Source {source_key} : {len(items)} items lus")
        except ClientError as e:
            logger.warning(f"Impossible de lire la source {source_key} : {e}")
    
    total_items = sum(len(items) for items in raw_items_by_source.values())
    logger.info(f"Items RAW lus avec succès : {len(raw_items_by_source)} sources, {total_items} items")
    
    return raw_items_by_source


def write_normalized_items_to_s3(bucket: str, client_id: str, run_id: str, normalized_items: list) -> str:
    """
    Écrit les items normalisés d'un run dans S3 avec la structure par run.
    
    Structure créée : normalized/{client_id}/YYYY/MM/DD/{run_id}/items.json
    
    Args:
        bucket: Nom du bucket S3
        client_id: Identifiant du client
        run_id: Identifiant du run
        normalized_items: Liste des items normalisés
    
    Returns:
        Clé S3 complète du fichier écrit
    
    Raises:
        ClientError: Si l'écriture échoue
    """
    # Extraire la date du run_id (format: run_YYYYMMDDTHHMMSS{microseconds}Z)
    date_part = run_id[4:12]  # YYYYMMDD
    year = date_part[:4]
    month = date_part[4:6]
    day = date_part[6:8]
    
    key = f"normalized/{client_id}/{year}/{month}/{day}/{run_id}/items.json"
    
    logger.info(f"Écriture des items normalisés pour le run {run_id} dans s3://{bucket}/{key}")
    write_json_to_s3(bucket, key, normalized_items)
    logger.info(f"Items normalisés écrits avec succès : {len(normalized_items)} items")
    
    return key


def list_normalized_runs_for_date_range(bucket: str, client_id: str, from_date: str, to_date: str) -> list:
    """
    Liste tous les runs normalisés pour un client sur une fenêtre temporelle.
    
    Args:
        bucket: Nom du bucket S3
        client_id: Identifiant du client
        from_date: Date de début (YYYY-MM-DD)
        to_date: Date de fin (YYYY-MM-DD)
    
    Returns:
        Liste des clés S3 des fichiers items.json trouvés
    
    Raises:
        ClientError: Si la liste échoue
    """
    from datetime import datetime, timedelta
    
    logger.info(f"Recherche des runs normalisés pour {client_id} du {from_date} au {to_date}")
    
    s3 = get_s3_client()
    all_keys = []
    
    # Générer la liste des dates à parcourir
    from_dt = datetime.strptime(from_date, '%Y-%m-%d')
    to_dt = datetime.strptime(to_date, '%Y-%m-%d')
    
    current_dt = from_dt
    while current_dt <= to_dt:
        year = current_dt.strftime('%Y')
        month = current_dt.strftime('%m')
        day = current_dt.strftime('%d')
        
        prefix = f"normalized/{client_id}/{year}/{month}/{day}/"
        
        try:
            response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    if key.endswith('/items.json'):
                        all_keys.append(key)
                        logger.debug(f"Trouvé : {key}")
        
        except ClientError as e:
            logger.debug(f"Aucun objet trouvé pour {prefix} : {e}")
        
        current_dt += timedelta(days=1)
    
    logger.info(f"Runs normalisés trouvés : {len(all_keys)}")
    return all_keys