"""
Module client pour Amazon Bedrock.

Ce module fournit un wrapper simple pour appeler les modèles Bedrock
et obtenir des réponses structurées pour la normalisation d'items.
"""

import json
import logging
from typing import Dict, Any, List

import boto3

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """
    Retourne un client boto3 Bedrock Runtime.
    
    Returns:
        Client boto3 bedrock-runtime configuré
    """
    return boto3.client('bedrock-runtime', region_name='eu-west-3')


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
    logger.info("Appel à Bedrock pour normalisation d'item")
    
    # Construction du prompt
    prompt = _build_normalization_prompt(item_text, canonical_examples)
    
    try:
        client = get_bedrock_client()
        
        # Appel à Bedrock (format Claude)
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
        
        logger.info("Réponse Bedrock reçue")
        
        # Parser la réponse JSON de Bedrock
        result = _parse_bedrock_response(response_text)
        
        return result
    
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à Bedrock: {e}")
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
3. Extract mentioned companies (from the examples or similar)
4. Extract mentioned molecules/drugs (from the examples or similar)
5. Extract mentioned technologies (from the examples or similar)
6. Extract therapeutic indications mentioned (e.g., "opioid use disorder", "schizophrenia", "diabetes")

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
