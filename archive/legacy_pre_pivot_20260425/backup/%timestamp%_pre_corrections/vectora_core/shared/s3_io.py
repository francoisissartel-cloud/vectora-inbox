"""
S3 I/O Operations pour Vectora Inbox V2.

Ce module gère toutes les opérations de lecture et écriture avec S3 :
- Lecture de fichiers JSON/YAML depuis les buckets de configuration
- Écriture des items ingérés dans le bucket de données
- Gestion des erreurs S3 et retry automatique

Responsabilités :
- Opérations S3 avec gestion d'erreurs robuste
- Sérialisation/désérialisation JSON et YAML
- Gestion des chemins S3 selon les conventions Vectora
"""

from typing import Any, Dict, List, Optional
import logging
import json
import boto3
import yaml
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_s3_client():
    """Retourne un client boto3 S3."""
    return boto3.client('s3')


def read_json_from_s3(bucket: str, key: str) -> Any:
    """
    Lit un fichier JSON depuis S3.
    
    Args:
        bucket: Nom du bucket S3
        key: Clé S3 du fichier
    
    Returns:
        Contenu du fichier JSON désérialisé
    
    Raises:
        ClientError: Si le fichier n'existe pas ou n'est pas accessible
        json.JSONDecodeError: Si le fichier n'est pas un JSON valide
    """
    try:
        s3 = get_s3_client()
        logger.info(f"Lecture JSON depuis s3://{bucket}/{key}")
        
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


def read_yaml_from_s3(bucket: str, key: str) -> Any:
    """
    Lit un fichier YAML depuis S3.
    
    Args:
        bucket: Nom du bucket S3
        key: Clé S3 du fichier
    
    Returns:
        Contenu du fichier YAML désérialisé
    
    Raises:
        ClientError: Si le fichier n'existe pas ou n'est pas accessible
        yaml.YAMLError: Si le fichier n'est pas un YAML valide
    """
    try:
        s3 = get_s3_client()
        logger.info(f"Lecture YAML depuis s3://{bucket}/{key}")
        
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


def write_json_to_s3(bucket: str, key: str, data: Any, content_type: str = "application/json") -> None:
    """
    Écrit des données JSON vers S3.
    
    Args:
        bucket: Nom du bucket S3
        key: Clé S3 du fichier
        data: Données à sérialiser en JSON
        content_type: Type MIME du contenu
    
    Raises:
        ClientError: Si l'écriture échoue
    """
    try:
        s3 = get_s3_client()
        logger.info(f"Écriture JSON vers s3://{bucket}/{key}")
        
        json_content = json.dumps(data, ensure_ascii=False, indent=2)
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json_content.encode('utf-8'),
            ContentType=content_type
        )
        
        logger.info(f"Fichier JSON écrit avec succès : {len(json_content)} caractères")
    
    except ClientError as e:
        logger.error(f"Erreur lors de l'écriture vers s3://{bucket}/{key}: {e}")
        raise


def write_text_to_s3(bucket: str, key: str, text: str, content_type: str = "text/plain") -> None:
    """
    Écrit du texte brut vers S3.
    
    Args:
        bucket: Nom du bucket S3
        key: Clé S3 du fichier
        text: Contenu textuel à écrire
        content_type: Type MIME du contenu
    
    Raises:
        ClientError: Si l'écriture échoue
    """
    try:
        s3 = get_s3_client()
        logger.info(f"Écriture texte vers s3://{bucket}/{key}")
        
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


def build_s3_key_for_ingested_items(client_id: str, date_str: str) -> str:
    """
    Construit la clé S3 pour les items ingérés selon les conventions Vectora.
    
    Format : ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json
    
    Args:
        client_id: Identifiant du client
        date_str: Date au format YYYY-MM-DD
    
    Returns:
        Clé S3 formatée selon les conventions
    """
    year, month, day = date_str.split('-')
    return f"ingested/{client_id}/{year}/{month}/{day}/items.json"


def build_s3_key_for_raw_content(client_id: str, source_key: str, date_str: str) -> str:
    """
    Construit la clé S3 pour le contenu brut (debug optionnel).
    
    Format : raw/{client_id}/{source_key}/{YYYY}/{MM}/{DD}/raw.json
    
    Args:
        client_id: Identifiant du client
        source_key: Identifiant de la source
        date_str: Date au format YYYY-MM-DD
    
    Returns:
        Clé S3 formatée selon les conventions
    """
    year, month, day = date_str.split('-')
    return f"raw/{client_id}/{source_key}/{year}/{month}/{day}/raw.json"


def build_s3_key_for_curated_items(client_id: str, date_str: str) -> str:
    """
    Construit la clé S3 pour les items normalisés/scorés.
    
    Format : curated/{client_id}/{YYYY}/{MM}/{DD}/items.json
    
    Args:
        client_id: Identifiant du client
        date_str: Date au format YYYY-MM-DD
    
    Returns:
        Clé S3 formatée selon les conventions
    """
    year, month, day = date_str.split('-')
    return f"curated/{client_id}/{year}/{month}/{day}/items.json"


def list_objects_with_prefix(bucket: str, prefix: str) -> List[str]:
    """
    Liste tous les objets S3 avec un préfixe donné.
    
    Args:
        bucket: Nom du bucket S3
        prefix: Préfixe des objets à lister
    
    Returns:
        Liste des clés S3 trouvées
    
    Raises:
        ClientError: Si impossible de lister les objets
    """
    try:
        s3 = get_s3_client()
        logger.info(f"Listage des objets s3://{bucket}/{prefix}*")
        
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)
        
        object_keys = []
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    object_keys.append(obj['Key'])
        
        logger.info(f"Objets trouvés : {len(object_keys)}")
        return object_keys
    
    except ClientError as e:
        logger.error(f"Erreur lors du listage de s3://{bucket}/{prefix}: {e}")
        raise


def list_s3_prefixes(bucket: str, prefix: str) -> List[str]:
    """
    Liste les préfixes S3 (dossiers) avec un préfixe donné.
    
    Args:
        bucket: Nom du bucket S3
        prefix: Préfixe des dossiers à lister
    
    Returns:
        Liste des préfixes trouvés
    """
    try:
        s3 = get_s3_client()
        logger.debug(f"Listage des préfixes s3://{bucket}/{prefix}")
        
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter='/')
        
        prefixes = []
        for page in page_iterator:
            if 'CommonPrefixes' in page:
                for common_prefix in page['CommonPrefixes']:
                    prefixes.append(common_prefix['Prefix'])
        
        return prefixes
    
    except ClientError as e:
        logger.error(f"Erreur lors du listage des préfixes s3://{bucket}/{prefix}: {e}")
        return []


def object_exists(bucket: str, key: str) -> bool:
    """
    Vérifie si un objet S3 existe.
    
    Args:
        bucket: Nom du bucket S3
        key: Clé S3 de l'objet
    
    Returns:
        True si l'objet existe, False sinon
    """
    try:
        s3 = get_s3_client()
        s3.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            logger.error(f"Erreur lors de la vérification de s3://{bucket}/{key}: {e}")
            return False


def build_s3_key_for_newsletter(client_id: str, date_str: str, file_type: str) -> str:
    """
    Construit la clé S3 pour les fichiers newsletter.

    Format : {client_id}/{YYYY}/{MM}/{DD}/newsletter.{ext}

    Args:
        client_id: Identifiant du client
        date_str: Date au format YYYY-MM-DD
        file_type: Type de fichier (md, json, manifest)

    Returns:
        Clé S3 formatée selon les conventions
    """
    year, month, day = date_str.split('-')
    if file_type == 'manifest':
        return f"{client_id}/{year}/{month}/{day}/manifest.json"
    else:
        return f"{client_id}/{year}/{month}/{day}/newsletter.{file_type}"


def load_curated_items_single_date(client_id: str, data_bucket: str, target_date: str) -> List[Dict]:
    """
    Charge les items curated pour une date unique (mode latest run).
    
    Args:
        client_id: Identifiant du client
        data_bucket: Bucket de données
        target_date: Date cible (YYYY-MM-DD)
    
    Returns:
        Liste des items curated pour cette date uniquement
    """
    try:
        key = build_s3_key_for_curated_items(client_id, target_date)
        items = read_json_from_s3(data_bucket, key)
        
        if isinstance(items, list):
            logger.info(f"Loaded {len(items)} items from single date {target_date}")
            return items
        else:
            logger.warning(f"Invalid items format for {target_date}")
            return []
            
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            logger.warning(f"No curated items found for {client_id} on {target_date}")
            return []
        else:
            logger.error(f"Error loading curated items for {target_date}: {e}")
            raise


def load_curated_items(client_id: str, data_bucket: str, from_date: str, to_date: str) -> List[Dict]:
    """
    Charge les items curated pour une période donnée.
    
    Args:
        client_id: Identifiant du client
        data_bucket: Bucket de données
        from_date: Date de début (YYYY-MM-DD)
        to_date: Date de fin (YYYY-MM-DD)
    
    Returns:
        Liste des items curated trouvés
    """
    from datetime import datetime, timedelta
    
    all_items = []
    current_date = datetime.strptime(from_date, '%Y-%m-%d')
    end_date = datetime.strptime(to_date, '%Y-%m-%d')
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        key = build_s3_key_for_curated_items(client_id, date_str)
        
        try:
            items = read_json_from_s3(data_bucket, key)
            if isinstance(items, list):
                all_items.extend(items)
            logger.info(f"Loaded {len(items) if isinstance(items, list) else 0} items from {date_str}")
        except ClientError as e:
            if e.response['Error']['Code'] != '404':
                logger.warning(f"Could not load items for {date_str}: {e}")
        
        current_date += timedelta(days=1)
    
    logger.info(f"Total curated items loaded: {len(all_items)}")
    return all_items


def save_newsletter(newsletter_data: Dict, client_id: str, target_date: str, newsletters_bucket: str) -> Dict[str, str]:
    """
    Sauvegarde la newsletter dans S3.
    
    Args:
        newsletter_data: Données de la newsletter (markdown, json, manifest)
        client_id: Identifiant du client
        target_date: Date cible (YYYY-MM-DD)
        newsletters_bucket: Bucket newsletters
    
    Returns:
        Dict avec les chemins S3 des fichiers sauvegardés
    """
    s3_paths = {}
    
    # Sauvegarde Markdown
    md_key = build_s3_key_for_newsletter(client_id, target_date, 'md')
    write_text_to_s3(newsletters_bucket, md_key, newsletter_data['markdown'], 'text/markdown')
    s3_paths['markdown'] = f"s3://{newsletters_bucket}/{md_key}"
    
    # Sauvegarde JSON
    json_key = build_s3_key_for_newsletter(client_id, target_date, 'json')
    write_json_to_s3(newsletters_bucket, json_key, newsletter_data['json'])
    s3_paths['json'] = f"s3://{newsletters_bucket}/{json_key}"
    
    # Sauvegarde Manifest
    manifest_key = build_s3_key_for_newsletter(client_id, target_date, 'manifest')
    write_json_to_s3(newsletters_bucket, manifest_key, newsletter_data['manifest'])
    s3_paths['manifest'] = f"s3://{newsletters_bucket}/{manifest_key}"
    
    logger.info(f"Newsletter saved to S3: {len(s3_paths)} files")
    return s3_paths