"""
Client Bedrock spécialisé pour la normalisation des items.

Ce module fournit une interface robuste pour les appels Bedrock
avec gestion des erreurs, retry automatique et prompts canoniques.

CORRECTION BEDROCK V2 : Utilise exactement la même logique que V1 qui fonctionne.
"""

import json
import logging
import os
import time
import random
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

from ..shared import prompt_resolver

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """
    Retourne un client boto3 Bedrock Runtime (COPIE EXACTE DE V1).
    
    Returns:
        Client boto3 bedrock-runtime configuré
    """
    region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    return boto3.client('bedrock-runtime', region_name=region)


def call_bedrock_with_retry(
    model_id: str,
    request_body: Dict[str, Any],
    max_retries: int = 3,
    base_delay: float = 0.5
) -> str:
    """API Bedrock unifiée avec retry automatique (COPIE EXACTE DE LA LOGIQUE V1).
    
    Args:
        model_id: Identifiant du modèle Bedrock
        request_body: Corps de la requête (format Claude Messages API)
        max_retries: Nombre maximum de tentatives
        base_delay: Délai de base pour le backoff
    
    Returns:
        Texte de réponse de Bedrock
    """
    # Créer le client à chaque appel comme V1
    client = get_bedrock_client()
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Appel à Bedrock (tentative {attempt + 1}/{max_retries + 1})")
            
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extraction du texte de réponse exactement comme V1
            content = response_body.get('content', [])
            if content and len(content) > 0:
                response_text = content[0].get('text', '')
            else:
                response_text = ''
            
            logger.info("Réponse Bedrock reçue avec succès")
            return response_text
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            # Vérifier si c'est une erreur de throttling (exactement comme V1)
            if error_code == 'ThrottlingException' or 'throttl' in error_code.lower():
                if attempt < max_retries:
                    # Calculer le délai avec backoff exponentiel + jitter (comme V1)
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
                    logger.warning(
                        f"ThrottlingException détectée (tentative {attempt + 1}/{max_retries + 1}). "
                        f"Retry dans {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    logger.error(
                        f"ThrottlingException - Échec après {max_retries + 1} tentatives. "
                        f"Abandon de l'appel Bedrock."
                    )
                    raise
            else:
                # Autre type d'erreur : ne pas retry (comme V1)
                logger.error(f"Erreur Bedrock non-throttling ({error_code}): {e}")
                raise
        
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'appel Bedrock: {e}")
            raise
    
    # Ne devrait jamais arriver ici
    raise Exception("Échec de l'appel Bedrock après tous les retries")


# Alias pour compatibilité avec bedrock_matcher.py
_call_bedrock_with_retry = call_bedrock_with_retry


class BedrockNormalizationClient:
    """Client Bedrock robuste pour la normalisation des items."""
    
    def __init__(self, model_id: str, region: str = "us-east-1", s3_io=None, 
                 client_config: Optional[Dict] = None, canonical_scopes: Optional[Dict] = None,
                 config_bucket: str = None):
        """
        Initialise le client Bedrock avec Approche B OBLIGATOIRE.
        
        Args:
            model_id: Identifiant du modèle Bedrock
            region: Région AWS pour Bedrock
            s3_io: Module s3_io pour charger prompts depuis S3 (REQUIS)
            client_config: Configuration client avec bedrock_config (REQUIS)
            canonical_scopes: Scopes canonical pour résolution références (REQUIS)
            config_bucket: Bucket S3 de configuration (REQUIS)
        
        Raises:
            ValueError: Si un paramètre requis est manquant
        """
        self.region = region
        self.model_id = model_id
        self.s3_io = s3_io
        self.client_config = client_config
        self.canonical_scopes = canonical_scopes
        self.config_bucket = config_bucket
        self.prompt_template = None
        
        # APPROCHE B OBLIGATOIRE - Validation stricte
        if not client_config:
            raise ValueError("client_config est requis pour Approche B")
        if not s3_io:
            raise ValueError("s3_io est requis pour Approche B")
        if not canonical_scopes:
            raise ValueError("canonical_scopes est requis pour Approche B")
        if not config_bucket:
            raise ValueError("config_bucket est requis pour Approche B")
        
        # Charger prompt template
        bedrock_config = client_config.get('bedrock_config', {})
        normalization_prompt = bedrock_config.get('normalization_prompt')
        
        if not normalization_prompt:
            raise ValueError(
                "client_config doit contenir 'bedrock_config.normalization_prompt' "
                "(ex: 'lai' pour charger lai_prompt.yaml)"
            )
        
        self.prompt_template = prompt_resolver.load_prompt_template(
            'normalization', normalization_prompt, s3_io, config_bucket
        )
        
        if not self.prompt_template:
            raise ValueError(
                f"Échec chargement prompt '{normalization_prompt}'. "
                f"Vérifier que canonical/prompts/normalization/{normalization_prompt}.yaml "
                f"existe sur S3."
            )
        
        logger.info(f"✅ Approche B activée: prompt {normalization_prompt} chargé")
        logger.info(f"Client Bedrock initialisé : modèle={self.model_id}, région={region}")
    
    def normalize_item(self, item_text: str, canonical_examples: Dict, 
                      domain_contexts: Optional[list] = None,
                      canonical_prompts: Dict[str, Any] = None,
                      item_source_key: str = None) -> Dict[str, Any]:
        """
        Normalise un item via Bedrock avec Approche B OBLIGATOIRE.
        
        Args:
            item_text: Texte de l'item à normaliser
            canonical_examples: Exemples depuis canonical scopes (non utilisé en Approche B)
            domain_contexts: Contextes de domaines (non utilisé en Approche B)
            canonical_prompts: Prompts canonical (non utilisé en Approche B)
            item_source_key: Source key pour détection pure player
        
        Returns:
            Résultat de normalisation avec champs LAI
        """
        try:
            # APPROCHE B OBLIGATOIRE - Validation
            if not self.prompt_template or not self.canonical_scopes:
                error_msg = (
                    "Approche B non activée. Vérifier que client_config contient "
                    "'bedrock_config.normalization_prompt' et que s3_io et canonical_scopes "
                    "sont passés au constructeur."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Construire prompt via Approche B
            prompt = self._build_prompt_approche_b(item_text, item_source_key)
            logger.info("Utilisation Approche B (prompt pré-construit)")
            
            # Appel Bedrock avec retry
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.0
            }
            
            response_text = call_bedrock_with_retry(self.model_id, request_body)
            result = self._parse_bedrock_response_v1(response_text)
            return result
            
        except Exception as e:
            logger.error(f"Erreur finale lors de l'appel à Bedrock: {e}")
            return self._create_fallback_result()
    

    

    

    
    def _call_bedrock_with_retry_v1(
        self,
        model_id: str,
        request_body: Dict[str, Any],
        max_retries: int = 3,
        base_delay: float = 0.5
    ) -> str:
        """Méthode de compatibilité - délègue vers l'API unifiée."""
        return call_bedrock_with_retry(model_id, request_body, max_retries, base_delay)
    
    def _parse_bedrock_response_v1(self, response_text: str) -> Dict[str, Any]:
        """COPIE EXACTE DE LA FONCTION V1 qui fonctionne."""
        try:
            # Tenter de parser directement comme JSON
            result = json.loads(response_text)
            
            # Valider la structure
            if not isinstance(result, dict):
                raise ValueError("La réponse n'est pas un dictionnaire")
            
            # S'assurer que les champs obligatoires existent (avec champs LAI)
            result.setdefault('summary', '')
            result.setdefault('event_type', 'other')
            result.setdefault('companies_detected', [])
            result.setdefault('molecules_detected', [])
            result.setdefault('technologies_detected', [])
            result.setdefault('trademarks_detected', [])
            result.setdefault('indications_detected', [])
            result.setdefault('lai_relevance_score', 0)
            result.setdefault('anti_lai_detected', False)
            result.setdefault('pure_player_context', False)
            result.setdefault('domain_relevance', [])
            result.setdefault('extracted_date', None)
            result.setdefault('date_confidence', 0.0)
            
            return result
        
        except json.JSONDecodeError:
            logger.warning("Réponse Bedrock non-JSON, tentative d'extraction manuelle")
            # Fallback : retourner une structure vide avec champs LAI
            return {
                'summary': response_text[:200] if response_text else '',
                'event_type': 'other',
                'companies_detected': [],
                'molecules_detected': [],
                'technologies_detected': [],
                'trademarks_detected': [],
                'indications_detected': [],
                'lai_relevance_score': 0,
                'anti_lai_detected': False,
                'pure_player_context': False,
                'domain_relevance': [],
                'extracted_date': None,
                'date_confidence': 0.0
            }
    
    def _build_prompt_approche_b(self, item_text: str, item_source_key: str = None) -> str:
        """
        Construit le prompt via Approche B (prompts pré-construits avec références).
        
        Args:
            item_text: Texte à analyser
            item_source_key: Source key pour contexte pure player
        
        Returns:
            Prompt final résolu
        """
        # Variables à substituer
        variables = {'item_text': item_text}
        
        # Ajouter contexte pure player si détecté (logique inline)
        if item_source_key:
            # Mapping inline
            company_mapping = {
                'medincell': 'MedinCell',
                'camurus': 'Camurus',
                'delsitech': 'DelSiTech',
                'nanexa': 'Nanexa',
                'peptron': 'Peptron'
            }
            
            source_lower = item_source_key.lower()
            company_name = None
            for key, name in company_mapping.items():
                if key in source_lower:
                    company_name = name
                    break
            
            # Pure players LAI
            pure_players = ['MedinCell', 'Camurus', 'DelSiTech', 'Nanexa', 'Peptron']
            
            if company_name and company_name in pure_players:
                pure_player_context = (
                    f"\n\nIMPORTANT CONTEXT: This content is from {company_name}, "
                    f"a LAI pure-player company specializing in long-acting injectable "
                    f"technologies. Even if LAI technologies are not explicitly mentioned, "
                    f"consider the LAI context and relevance given the company's "
                    f"specialization in this field."
                )
                variables['pure_player_context'] = pure_player_context
        
        # Construire le prompt avec résolution des références
        prompt = prompt_resolver.build_prompt(
            self.prompt_template,
            self.canonical_scopes,
            variables
        )
        
        logger.info("Prompt construit via Approche B")
        return prompt
    
    def _create_fallback_result(self) -> Dict[str, Any]:
        """Crée un résultat de fallback en cas d'échec total."""
        return {
            "summary": "",
            "event_type": "other",
            "companies_detected": [],
            "molecules_detected": [],
            "technologies_detected": [],
            "trademarks_detected": [],
            "indications_detected": [],
            "lai_relevance_score": 0,
            "anti_lai_detected": False,
            "pure_player_context": False,
            "extracted_date": None,
            "date_confidence": 0.0
        }