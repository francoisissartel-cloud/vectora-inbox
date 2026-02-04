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
    domain_scoring_prompt: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Score un item normalisé pour un domaine de veille via Bedrock.
    
    Args:
        normalized_item: Item après normalisation générique
        domain_definition: Définition du domaine (lai_domain_definition.yaml)
        canonical_scopes: Scopes canonical pour résolution des références
        bedrock_client: Client Bedrock initialisé
        domain_scoring_prompt: Prompt lai_domain_scoring.yaml
    
    Returns:
        Dict avec is_relevant, score, confidence, signals_detected, reasoning
    """
    try:
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
            'item_indications': ', '.join(entities.get('indications', []))
        }
        
        # Appel Bedrock avec prompt domain scoring
        response = bedrock_client.invoke_with_prompt(
            prompt_template=domain_scoring_prompt,
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
