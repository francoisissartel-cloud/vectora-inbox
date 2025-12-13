"""
Module client pour Amazon Bedrock.

Ce module fournit un wrapper simple pour appeler les modèles Bedrock
et obtenir des réponses structurées pour la normalisation d'items.
"""

import json
import logging
import os
import time
import random
from typing import Dict, Any, List

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """
    Retourne un client boto3 Bedrock Runtime.
    
    Returns:
        Client boto3 bedrock-runtime configuré
    """
    region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    return boto3.client('bedrock-runtime', region_name=region)


def normalize_item_with_bedrock(
    item_text: str,
    model_id: str,
    canonical_examples: Dict[str, List[str]]
) -> Dict[str, Any]:
    """
    Appelle Bedrock pour normaliser un item : extraction d'entités, classification, résumé.
    
    Args:
        item_text: Texte de l'item à analyser (titre + description)
        model_id: Identifiant du modèle Bedrock (ex: anthropic.claude-3-sonnet...)
        canonical_examples: Exemples d'entités depuis les scopes canonical :
            - companies: liste d'exemples de sociétés
            - molecules: liste d'exemples de molécules
            - technologies: liste d'exemples de mots-clés technologiques
    
    Returns:
        Dictionnaire contenant :
        - summary: résumé court (2-3 phrases)
        - event_type: type d'événement détecté
        - companies_detected: liste de sociétés mentionnées
        - molecules_detected: liste de molécules mentionnées
        - technologies_detected: liste de technologies détectées
        - indications_detected: liste d'indications thérapeutiques
    """
    # Construction du prompt
    prompt = _build_normalization_prompt(item_text, canonical_examples)
    
    # Appel avec retry sur ThrottlingException
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
    
    try:
        response_text = _call_bedrock_with_retry(model_id, request_body)
        result = _parse_bedrock_response(response_text)
        return result
    
    except Exception as e:
        logger.error(f"Erreur finale lors de l'appel à Bedrock après tous les retries: {e}")
        # Retourner une structure vide en cas d'erreur
        return {
            'summary': '',
            'event_type': 'other',
            'companies_detected': [],
            'molecules_detected': [],
            'technologies_detected': [],
            'indications_detected': []
        }


def _build_normalization_prompt(
    item_text: str,
    canonical_examples: Dict[str, List[str]]
) -> str:
    """
    Construit le prompt pour Bedrock.
    
    Args:
        item_text: Texte à analyser
        canonical_examples: Exemples d'entités depuis les scopes
    
    Returns:
        Prompt formaté pour Bedrock
    """
    # Limiter les exemples pour ne pas surcharger le prompt
    companies_ex = canonical_examples.get('companies', [])[:20]
    molecules_ex = canonical_examples.get('molecules', [])[:20]
    technologies_ex = canonical_examples.get('technologies', [])[:15]
    
    prompt = f"""Analyze the following biotech/pharma news item and extract structured information.

TEXT TO ANALYZE:
{item_text}

EXAMPLES OF ENTITIES TO DETECT:
- Companies: {', '.join(companies_ex)}
- Molecules/Drugs: {', '.join(molecules_ex)}
- Technologies: {', '.join(technologies_ex)}

TASK:
1. Generate a concise summary (2-3 sentences) explaining the key information
2. Classify the event type among: clinical_update, partnership, regulatory, scientific_paper, corporate_move, financial_results, safety_signal, manufacturing_supply, other
3. Extract ALL pharmaceutical/biotech company names mentioned in the text (including those in examples and ANY others)
4. Extract ALL drug/molecule names mentioned (including brand names, generic names, and development codes)
5. Extract ALL technology keywords mentioned (e.g., "long-acting injectable", "microspheres", "PLGA", "subcutaneous", etc.)
6. Extract ALL therapeutic indications mentioned (e.g., "opioid use disorder", "schizophrenia", "diabetes")

IMPORTANT:
- Extract the EXACT company names as they appear in the text (e.g., "WuXi AppTec", "Agios", "Pfizer")
- Include ALL companies mentioned, not just those in the examples
- Be comprehensive in entity extraction

RESPONSE FORMAT (JSON only):
{{
  "summary": "...",
  "event_type": "...",
  "companies_detected": ["...", "..."],
  "molecules_detected": ["...", "..."],
  "technologies_detected": ["...", "..."],
  "indications_detected": ["...", "..."]
}}

Respond with ONLY the JSON, no additional text."""
    
    return prompt


def _call_bedrock_with_retry(
    model_id: str,
    request_body: Dict[str, Any],
    max_retries: int = 3,
    base_delay: float = 0.5
) -> str:
    """
    Appelle Bedrock avec retry automatique sur ThrottlingException.
    
    Args:
        model_id: Identifiant du modèle Bedrock
        request_body: Corps de la requête (format Claude Messages API)
        max_retries: Nombre maximum de tentatives (défaut: 3)
        base_delay: Délai de base en secondes pour le backoff (défaut: 0.5s)
    
    Returns:
        Texte de réponse de Bedrock
    
    Raises:
        Exception: Si tous les retries échouent ou si l'erreur n'est pas un throttling
    """
    client = get_bedrock_client()
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Appel à Bedrock (tentative {attempt + 1}/{max_retries + 1})")
            
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extraction du texte de réponse
            content = response_body.get('content', [])
            if content and len(content) > 0:
                response_text = content[0].get('text', '')
            else:
                response_text = ''
            
            logger.info("Réponse Bedrock reçue avec succès")
            return response_text
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            
            # Vérifier si c'est une erreur de throttling
            if error_code == 'ThrottlingException' or 'throttl' in error_code.lower():
                if attempt < max_retries:
                    # Calculer le délai avec backoff exponentiel + jitter
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
                # Autre type d'erreur : ne pas retry
                logger.error(f"Erreur Bedrock non-throttling ({error_code}): {e}")
                raise
        
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'appel Bedrock: {e}")
            raise
    
    # Ne devrait jamais arriver ici
    raise Exception("Échec de l'appel Bedrock après tous les retries")


def _parse_bedrock_response(response_text: str) -> Dict[str, Any]:
    """
    Parse la réponse JSON de Bedrock.
    
    Args:
        response_text: Texte de réponse de Bedrock
    
    Returns:
        Dictionnaire structuré
    """
    try:
        # Tenter de parser directement comme JSON
        result = json.loads(response_text)
        
        # Valider la structure
        if not isinstance(result, dict):
            raise ValueError("La réponse n'est pas un dictionnaire")
        
        # S'assurer que les champs obligatoires existent
        result.setdefault('summary', '')
        result.setdefault('event_type', 'other')
        result.setdefault('companies_detected', [])
        result.setdefault('molecules_detected', [])
        result.setdefault('technologies_detected', [])
        result.setdefault('indications_detected', [])
        
        return result
    
    except json.JSONDecodeError:
        logger.warning("Réponse Bedrock non-JSON, tentative d'extraction manuelle")
        # Fallback : retourner une structure vide
        return {
            'summary': response_text[:200] if response_text else '',
            'event_type': 'other',
            'companies_detected': [],
            'molecules_detected': [],
            'technologies_detected': [],
            'indications_detected': []
        }
