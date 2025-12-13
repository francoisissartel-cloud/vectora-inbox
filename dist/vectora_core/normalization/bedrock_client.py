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
    canonical_examples: Dict[str, List[str]],
    domain_contexts: List = None
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
    prompt = _build_normalization_prompt(item_text, canonical_examples, domain_contexts)
    
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
        # Retourner une structure vide en cas d'erreur avec champs LAI
        return {
            'summary': '',
            'event_type': 'other',
            'companies_detected': [],
            'molecules_detected': [],
            'technologies_detected': [],
            'trademarks_detected': [],
            'indications_detected': [],
            'lai_relevance_score': 0,
            'anti_lai_detected': False,
            'pure_player_context': False,
            'domain_relevance': []
        }


def _build_normalization_prompt(
    item_text: str,
    canonical_examples: Dict[str, List[str]],
    domain_contexts: List = None
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
    
    # Construire la section des domaines si fournie
    domain_section = ""
    if domain_contexts:
        domain_section = "\n\nDOMAINS TO EVALUATE:\n"
        for i, domain in enumerate(domain_contexts, 1):
            domain_section += f"{i}. {domain.domain_id} ({domain.domain_type}):\n"
            domain_section += f"   Description: {domain.description}\n"
            
            # Ajouter les exemples d'entités
            if domain.example_entities:
                for entity_type, examples in domain.example_entities.items():
                    if examples:
                        domain_section += f"   {entity_type.title()}: {', '.join(examples[:5])}\n"
            
            # Ajouter les phrases de contexte
            if domain.context_phrases:
                domain_section += f"   Context: {'; '.join(domain.context_phrases)}\n"
            domain_section += "\n"
    
    # Section LAI spécialisée simplifiée (Correction P0-1)
    lai_section = "\n\nLAI TECHNOLOGY FOCUS:\n"
    lai_section += "Detect these LAI (Long-Acting Injectable) technologies:\n"
    lai_section += "- Extended-Release Injectable\n"
    lai_section += "- Long-Acting Injectable\n"
    lai_section += "- Depot Injection\n"
    lai_section += "- Once-Monthly Injection\n"
    lai_section += "- Microspheres\n"
    lai_section += "- PLGA\n"
    lai_section += "- In-Situ Depot\n"
    lai_section += "- Hydrogel\n"
    lai_section += "- Subcutaneous Injection\n"
    lai_section += "- Intramuscular Injection\n"
    lai_section += "\nTRADEMARKS to detect:\n"
    lai_section += "- UZEDY, PharmaShell, SiliaShell, BEPO, Aristada, Abilify Maintena\n"
    lai_section += "\nNormalize: 'extended-release injectable' → 'Extended-Release Injectable'\n"
    
    # Tâches simplifiées avec focus LAI (Correction P0-1)
    tasks = [
        "1. Generate a concise summary (2-3 sentences) explaining the key information",
        "2. Classify the event type among: clinical_update, partnership, regulatory, scientific_paper, corporate_move, financial_results, safety_signal, manufacturing_supply, other",
        "3. Extract ALL pharmaceutical/biotech company names mentioned",
        "4. Extract ALL drug/molecule names mentioned (including brand names, generic names)",
        "5. Extract ALL technology keywords mentioned - FOCUS on LAI technologies listed above",
        "6. Extract ALL trademark names mentioned (especially those with ® or ™ symbols)",
        "7. Extract ALL therapeutic indications mentioned",
        "8. Evaluate LAI relevance (0-10 score): How relevant is this content to Long-Acting Injectable technologies?",
        "9. Detect anti-LAI signals: Does the content mention oral routes (tablets, capsules, pills)?",
        "10. Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?"
    ]
    
    if domain_contexts:
        tasks.append("7. For EACH domain listed above, evaluate:")
        tasks.append("   - is_on_domain: true if the article is relevant to this domain, false otherwise")
        tasks.append("   - relevance_score: 0.0-1.0 score indicating how relevant the article is to this domain")
        tasks.append("   - reason: Brief explanation (max 2 sentences) of why it is or isn't relevant")
    
    # Format JSON de réponse avec champs LAI (Correction P0-1)
    json_example = {
        "summary": "...",
        "event_type": "...",
        "companies_detected": ["...", "..."],
        "molecules_detected": ["...", "..."],
        "technologies_detected": ["...", "..."],
        "trademarks_detected": ["...", "..."],
        "indications_detected": ["...", "..."],
        "lai_relevance_score": 0,
        "anti_lai_detected": False,
        "pure_player_context": False
    }
    
    if domain_contexts:
        json_example["domain_relevance"] = [
            {
                "domain_id": "domain_id_here",
                "domain_type": "domain_type_here", 
                "is_on_domain": True,
                "relevance_score": 0.85,
                "reason": "Brief explanation (max 2 sentences)"
            }
        ]
    
    prompt = f"""Analyze the following biotech/pharma news item and extract structured information.

TEXT TO ANALYZE:
{item_text}

EXAMPLES OF ENTITIES TO DETECT:
- Companies: {', '.join(companies_ex)}
- Molecules/Drugs: {', '.join(molecules_ex)}
- Technologies: {', '.join(technologies_ex)}{lai_section}{domain_section}

TASK:
{chr(10).join(tasks)}

IMPORTANT:
- Extract the EXACT company names as they appear in the text (e.g., "WuXi AppTec", "Agios", "Pfizer")
- Include ALL companies mentioned, not just those in the examples
- Be comprehensive in entity extraction
- For domain evaluation, consider the overall context and relevance, not just keyword matching

RESPONSE FORMAT (JSON only):
{json.dumps(json_example, indent=2)}

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
            'domain_relevance': []
        }
