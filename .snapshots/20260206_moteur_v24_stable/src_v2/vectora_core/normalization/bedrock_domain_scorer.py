"""
Module de scoring de domaine via Bedrock.

Ce module gère le 2ème appel Bedrock pour évaluer la pertinence
d'un item normalisé par rapport à un domaine de veille (ex: LAI).
"""

import logging
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)


def score_item_for_domain(
    normalized_item: Dict[str, Any],
    domain_definition: Dict[str, Any],
    canonical_scopes: Dict[str, Any],
    bedrock_client,
    domain_scoring_prompt: Dict[str, Any],
    s3_io=None,
    config_bucket: str = None
) -> Dict[str, Any]:
    """
    Score un item normalisé pour un domaine de veille via Bedrock.
    
    Args:
        normalized_item: Item après normalisation générique
        domain_definition: Définition du domaine (DEPRECATED - non utilisé en v3)
        canonical_scopes: Scopes canonical (DEPRECATED - non utilisé en v3)
        bedrock_client: Client Bedrock initialisé
        domain_scoring_prompt: Prompt lai_domain_scoring.yaml OU string prompt flat v3
        s3_io: Module s3_io pour charger prompt flat depuis S3
        config_bucket: Bucket S3 de configuration
    
    Returns:
        Dict avec is_relevant, score, confidence, signals_detected, reasoning
    """
    try:
        # V3: Charger prompt flat depuis S3 si disponible
        prompt_flat = None
        if s3_io and config_bucket:
            try:
                prompt_flat_key = "canonical/prompts/generated/lai_scoring_bedrock_v3.txt"
                prompt_flat = s3_io.read_text_file(config_bucket, prompt_flat_key)
                logger.info(f"Loaded flat prompt v3 from S3: {len(prompt_flat)} chars")
            except Exception as e:
                logger.warning(f"Failed to load flat prompt v3, falling back to YAML template: {e}")
        
        # Extraction des données de l'item normalisé
        normalized_content = normalized_item.get('normalized_content', {})
        entities = normalized_content.get('entities', {})
        
        # Construction du contexte pour Bedrock
        item_context = {
            'item_title': normalized_item.get('title', ''),
            'item_summary': normalized_content.get('summary', ''),
            'item_event_type': normalized_content.get('event_classification', {}).get('primary_type', 'other'),
            'item_effective_date': normalized_item.get('effective_date', ''),
            'item_companies': ', '.join(entities.get('companies', [])),
            'item_molecules': ', '.join(entities.get('molecules', [])),
            'item_technologies': ', '.join(entities.get('technologies', [])),
            'item_trademarks': ', '.join(entities.get('trademarks', [])),
            'item_indications': ', '.join(entities.get('indications', [])),
            'item_dosing_intervals': ', '.join(entities.get('dosing_intervals', []))
        }
        
        # Appel Bedrock avec prompt flat v3 OU template YAML legacy
        if prompt_flat:
            response = bedrock_client.invoke_with_prompt(
                prompt_template=prompt_flat,  # String prompt flat
                context=item_context,
                domain_definition=None  # Non utilisé en v3
            )
        else:
            response = bedrock_client.invoke_with_prompt(
                prompt_template=domain_scoring_prompt,  # Dict YAML template
                context=item_context,
                domain_definition=domain_definition
            )
        
        # Parse réponse JSON
        result = json.loads(response)
        
        # Validation structure
        required_fields = ['is_relevant', 'score', 'confidence', 'signals_detected', 'reasoning']
        for field in required_fields:
            if field not in result:
                logger.warning(f"Missing field in domain scoring response: {field}")
                result[field] = _get_default_value(field)
        
        logger.info(f"Domain scoring: is_relevant={result['is_relevant']}, score={result['score']}, confidence={result['confidence']}")
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Bedrock response as JSON: {e}")
        return _create_fallback_scoring()
    except Exception as e:
        logger.error(f"Error in domain scoring: {e}")
        return _create_fallback_scoring()


def _get_default_value(field: str) -> Any:
    """Retourne valeur par défaut pour un champ manquant."""
    defaults = {
        'is_relevant': False,
        'score': 0,
        'confidence': 'low',
        'signals_detected': {'strong': [], 'medium': [], 'weak': [], 'exclusions': []},
        'reasoning': 'Incomplete response from Bedrock'
    }
    return defaults.get(field)


def _create_fallback_scoring() -> Dict[str, Any]:
    """Crée un résultat de scoring de fallback en cas d'échec."""
    return {
        'is_relevant': False,
        'score': 0,
        'confidence': 'low',
        'signals_detected': {
            'strong': [],
            'medium': [],
            'weak': [],
            'exclusions': []
        },
        'score_breakdown': None,
        'reasoning': 'Bedrock domain scoring failed - fallback to not relevant'
    }
