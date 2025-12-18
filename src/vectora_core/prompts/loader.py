"""
PromptLoader pour les prompts canonicalisés Vectora Inbox V1.

Ce module charge les prompts depuis canonical/prompts/global_prompts.yaml
avec cache en mémoire et fallback robuste.
"""

import json
import logging
import os
from typing import Any, Dict, Optional
import yaml
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Chargeur de prompts canonicalisés avec cache et fallback.
    
    V1: Charge depuis S3 ou local, cache en mémoire, fallback vers None.
    """
    
    def __init__(self, config_bucket: Optional[str] = None):
        """
        Initialise le PromptLoader.
        
        Args:
            config_bucket: Bucket S3 de configuration (optionnel)
        """
        self.config_bucket = config_bucket
        self._cache = {}  # Cache en mémoire
        self._loaded = False
        
    def get_prompt(self, prompt_key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un prompt canonicalisé par sa clé.
        
        Args:
            prompt_key: Clé du prompt (ex: "normalization.lai_default")
        
        Returns:
            Dict contenant system_instructions, user_template, bedrock_config
            ou None si prompt non trouvé ou erreur
        """
        try:
            # Charger les prompts si pas encore fait
            if not self._loaded:
                self._load_prompts()
            
            # Naviguer dans la structure YAML avec la clé
            keys = prompt_key.split('.')
            current = self._cache
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    logger.warning(f"Prompt non trouvé : {prompt_key}")
                    return None
            
            # Valider la structure du prompt
            if not isinstance(current, dict):
                logger.warning(f"Structure prompt invalide : {prompt_key}")
                return None
            
            required_fields = ['system_instructions', 'user_template', 'bedrock_config']
            for field in required_fields:
                if field not in current:
                    logger.warning(f"Champ manquant '{field}' dans prompt : {prompt_key}")
                    return None
            
            logger.info(f"Prompt canonicalisé chargé : {prompt_key}")
            return current
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement du prompt {prompt_key}: {e}")
            return None
    
    def _load_prompts(self) -> None:
        """
        Charge les prompts depuis S3 ou local avec fallback.
        """
        try:
            # Tentative 1: Chargement depuis S3 (runtime AWS)
            if self.config_bucket:
                logger.info("Tentative chargement prompts depuis S3...")
                if self._load_from_s3():
                    self._loaded = True
                    return
            
            # Tentative 2: Chargement depuis fichier local
            logger.info("Tentative chargement prompts depuis fichier local...")
            if self._load_from_local():
                self._loaded = True
                return
            
            # Échec: Aucune source disponible
            logger.error("Impossible de charger les prompts canonicalisés")
            self._cache = {}
            self._loaded = True
        
        except Exception as e:
            logger.error(f"Erreur lors du chargement des prompts: {e}")
            self._cache = {}
            self._loaded = True
    
    def _load_from_s3(self) -> bool:
        """
        Charge les prompts depuis S3.
        
        Returns:
            True si succès, False sinon
        """
        try:
            s3_client = boto3.client('s3')
            s3_key = 'canonical/prompts/global_prompts.yaml'
            
            response = s3_client.get_object(
                Bucket=self.config_bucket,
                Key=s3_key
            )
            
            yaml_content = response['Body'].read().decode('utf-8')
            self._cache = yaml.safe_load(yaml_content)
            
            logger.info(f"Prompts chargés depuis S3: s3://{self.config_bucket}/{s3_key}")
            return True
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchKey':
                logger.warning("Fichier prompts non trouvé en S3")
            else:
                logger.warning(f"Erreur S3 lors du chargement prompts: {e}")
            return False
        
        except Exception as e:
            logger.warning(f"Erreur inattendue lors du chargement S3: {e}")
            return False
    
    def _load_from_local(self) -> bool:
        """
        Charge les prompts depuis fichier local.
        
        Returns:
            True si succès, False sinon
        """
        try:
            # Chemins possibles pour le fichier local
            possible_paths = [
                'canonical/prompts/global_prompts.yaml',
                '../canonical/prompts/global_prompts.yaml',
                '../../canonical/prompts/global_prompts.yaml',
                '/opt/canonical/prompts/global_prompts.yaml'  # Lambda runtime
            ]
            
            for file_path in possible_paths:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self._cache = yaml.safe_load(f)
                    
                    logger.info(f"Prompts chargés depuis fichier local: {file_path}")
                    return True
            
            logger.warning("Aucun fichier prompts local trouvé")
            return False
        
        except Exception as e:
            logger.warning(f"Erreur lors du chargement local: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Vérifie si les prompts canonicalisés sont disponibles.
        
        Returns:
            True si prompts chargés, False sinon
        """
        if not self._loaded:
            self._load_prompts()
        
        return bool(self._cache)
    
    def get_available_prompts(self) -> Dict[str, Any]:
        """
        Retourne la liste des prompts disponibles.
        
        Returns:
            Dict avec structure des prompts chargés
        """
        if not self._loaded:
            self._load_prompts()
        
        return self._cache.copy()


# Instance globale pour éviter rechargements multiples
_global_loader = None


def get_prompt_loader(config_bucket: Optional[str] = None) -> PromptLoader:
    """
    Retourne l'instance globale du PromptLoader.
    
    Args:
        config_bucket: Bucket S3 de configuration
    
    Returns:
        Instance PromptLoader
    """
    global _global_loader
    
    if _global_loader is None:
        _global_loader = PromptLoader(config_bucket)
    
    return _global_loader