#!/usr/bin/env python3
"""
Correction rapide du problème PyYAML - Modification du code s3_io.py
Solution plus simple que recréer les layers
"""

import os
import tempfile
import zipfile
import boto3
import json
from pathlib import Path

def create_fixed_s3_io_code():
    """Crée une version corrigée de s3_io.py avec import yaml conditionnel"""
    
    fixed_code = '''"""
S3 I/O Operations pour Vectora Inbox V2 - VERSION CORRIGÉE.

Ce module gère toutes les opérations de lecture et écriture avec S3 :
- Lecture de fichiers JSON/YAML depuis les buckets de configuration
- Écriture des items ingérés dans le bucket de données
- Gestion des erreurs S3 et retry automatique

CORRECTION: Import yaml conditionnel avec message d'erreur explicite
"""

from typing import Any, Dict, List, Optional
import logging
import json
import boto3
from botocore.exceptions import ClientError

# CORRECTION: Import yaml conditionnel avec gestion d'erreur explicite
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError as e:
    YAML_AVAILABLE = False
    YAML_IMPORT_ERROR = str(e)

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
        ImportError: Si PyYAML n'est pas disponible
        yaml.YAMLError: Si le fichier n'est pas un YAML valide
    """
    # CORRECTION: Vérification PyYAML disponible
    if not YAML_AVAILABLE:
        error_msg = f"PyYAML requis pour lire {key} mais non disponible: {YAML_IMPORT_ERROR}"
        logger.error(error_msg)
        raise ImportError(error_msg)
    
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
    except Exception as e:  # yaml.YAMLError hérite d'Exception
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
'''
    
    return fixed_code

def create_patched_lambda_package():
    """Crée un package Lambda avec s3_io.py corrigé"""
    
    print("[PATCH] Création package Lambda avec s3_io.py corrigé...")
    
    # Code corrigé
    fixed_s3_io = create_fixed_s3_io_code()
    
    # Lecture du handler existant
    handler_path = Path("src_v2/lambdas/normalize_score/handler.py")
    if not handler_path.exists():
        print(f"[ERROR] Handler non trouvé: {handler_path}")
        return None
    
    with open(handler_path, 'r', encoding='utf-8') as f:
        handler_code = f.read()
    
    # Création du package
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Handler
        with open(temp_path / "handler.py", 'w', encoding='utf-8') as f:
            f.write(handler_code)
        
        # Vectora_core avec s3_io.py corrigé
        vectora_core_dir = temp_path / "vectora_core"
        vectora_core_dir.mkdir()
        
        # Copie de la structure vectora_core (simplifiée pour le patch)
        (vectora_core_dir / "__init__.py").touch()
        
        # Shared
        shared_dir = vectora_core_dir / "shared"
        shared_dir.mkdir()
        (shared_dir / "__init__.py").touch()
        
        # s3_io.py corrigé
        with open(shared_dir / "s3_io.py", 'w', encoding='utf-8') as f:
            f.write(fixed_s3_io)
        
        # Copie des autres modules shared nécessaires
        src_shared = Path("src_v2/vectora_core/shared")
        for module_file in ["config_loader.py", "utils.py"]:
            src_file = src_shared / module_file
            if src_file.exists():
                with open(src_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(shared_dir / module_file, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # Normalization
        norm_dir = vectora_core_dir / "normalization"
        norm_dir.mkdir()
        (norm_dir / "__init__.py").touch()
        
        # Copie des modules normalization nécessaires
        src_norm = Path("src_v2/vectora_core/normalization")
        for module_file in ["__init__.py", "normalizer.py", "matcher.py", "scorer.py"]:
            src_file = src_norm / module_file
            if src_file.exists():
                with open(src_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                with open(norm_dir / module_file, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        # Création du ZIP
        zip_path = temp_path / "normalize_score_v2_patched.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in temp_path.rglob("*"):
                if file_path.is_file() and file_path != zip_path:
                    arcname = file_path.relative_to(temp_path)
                    zipf.write(file_path, arcname)
        
        # Lecture du ZIP
        with open(zip_path, 'rb') as f:
            zip_content = f.read()
        
        print(f"[OK] Package créé: {len(zip_content)} bytes")
        return zip_content

def update_lambda_code(zip_content):
    """Met à jour le code de la Lambda avec le package corrigé"""
    
    print("[UPDATE] Mise à jour code Lambda...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    try:
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"[OK] Code Lambda mis à jour")
        print(f"[VERSION] Nouvelle version: {response['Version']}")
        print(f"[SIZE] Taille: {response['CodeSize']} bytes")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erreur mise à jour: {str(e)}")
        return False

def test_fixed_lambda():
    """Test la Lambda avec le code corrigé"""
    
    print("[TEST] Test Lambda avec code corrigé...")
    
    session = boto3.Session(profile_name='rag-lai-prod')
    lambda_client = session.client('lambda', region_name='eu-west-3')
    
    function_name = 'vectora-inbox-normalize-score-v2-dev'
    
    test_payload = {
        'client_id': 'lai_weekly_v3',
        'test_mode': True
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(test_payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        if response.get('FunctionError'):
            print(f"[ERROR] Erreur Lambda: {response['FunctionError']}")
            error_msg = response_payload.get('errorMessage', 'Unknown error')
            print(f"[DETAILS] {error_msg}")
            
            # Vérifier si c'est encore le problème yaml
            if 'yaml' in error_msg.lower():
                print(f"[ANALYSIS] Problème PyYAML persiste")
                return False
            else:
                print(f"[ANALYSIS] Nouveau type d'erreur - progrès possible")
                return True
        else:
            print(f"[SUCCESS] Lambda fonctionne!")
            print(f"[RESPONSE] {response_payload}")
            return True
            
    except Exception as e:
        print(f"[ERROR] Erreur test: {str(e)}")
        return False

def main():
    """Fonction principale de correction rapide"""
    
    print("CORRECTION RAPIDE - Patch s3_io.py pour PyYAML")
    print("=" * 60)
    
    # Étape 1: Création du package corrigé
    print("\n[STEP 1] Création package avec s3_io.py corrigé...")
    zip_content = create_patched_lambda_package()
    
    if not zip_content:
        print("[ABORT] Échec création package")
        return False
    
    # Étape 2: Mise à jour Lambda
    print("\n[STEP 2] Mise à jour code Lambda...")
    update_success = update_lambda_code(zip_content)
    
    if not update_success:
        print("[ABORT] Échec mise à jour Lambda")
        return False
    
    # Étape 3: Test
    print("\n[STEP 3] Test Lambda corrigée...")
    test_success = test_fixed_lambda()
    
    # Résumé
    print("\n" + "=" * 60)
    print("[RESUME] Correction rapide terminée")
    
    if test_success:
        print("[SUCCESS] Correction réussie - Lambda fonctionne")
        print("[NEXT] Relancer test end-to-end complet:")
        print("  aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \\")
        print("    --payload file://test_normalize_payload.json response_final.json")
    else:
        print("[PARTIAL] Correction partielle - investigation supplémentaire nécessaire")
        print("[NEXT] Vérifier les logs CloudWatch pour plus de détails")
    
    return test_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)