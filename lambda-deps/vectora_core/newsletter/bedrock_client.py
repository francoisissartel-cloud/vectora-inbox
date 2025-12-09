"""
Module client Bedrock pour la génération éditoriale de newsletters.

Ce module appelle Bedrock pour générer les textes éditoriaux :
- Titre de la newsletter
- Introduction
- TL;DR
- Textes d'introduction des sections
- Reformulations des items
"""

import json
import logging
import time
import random
from typing import Any, Dict, List

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """
    Retourne un client boto3 Bedrock Runtime.
    
    Returns:
        Client boto3 bedrock-runtime configuré
    """
    return boto3.client('bedrock-runtime', region_name='eu-west-3')


def generate_editorial_content(
    sections_data: List[Dict[str, Any]],
    client_profile: Dict[str, Any],
    bedrock_model_id: str,
    target_date: str,
    from_date: str,
    to_date: str,
    total_items_analyzed: int
) -> Dict[str, Any]:
    """
    Génère les textes éditoriaux avec Bedrock.
    
    Args:
        sections_data: Sections avec items sélectionnés
        client_profile: Profil du client (tone, voice, language)
        bedrock_model_id: ID du modèle Bedrock
        target_date: Date de référence
        from_date: Date de début
        to_date: Date de fin
        total_items_analyzed: Nombre total d'items analysés
    
    Returns:
        Dict contenant :
            - title: Titre de la newsletter
            - intro: Paragraphe d'introduction
            - tldr: Liste de bullet points
            - sections: Liste de sections avec intro et items reformulés
    """
    # Construire le prompt
    prompt = _build_editorial_prompt(
        sections_data,
        client_profile,
        target_date,
        from_date,
        to_date,
        total_items_analyzed
    )
    
    # Appel avec retry sur ThrottlingException
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 3000,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3
    }
    
    try:
        response_text = _call_bedrock_with_retry(bedrock_model_id, request_body)
        result = _parse_editorial_response(response_text)
        return result
    
    except Exception as e:
        logger.error(f"Erreur finale lors de l'appel à Bedrock après tous les retries: {e}")
        # Retourner une structure minimale en cas d'erreur
        return _generate_fallback_editorial(sections_data, client_profile, target_date)


def _build_editorial_prompt(
    sections_data: List[Dict[str, Any]],
    client_profile: Dict[str, Any],
    target_date: str,
    from_date: str,
    to_date: str,
    total_items_analyzed: int
) -> str:
    """
    Construit le prompt pour Bedrock.
    """
    client_name = client_profile.get('name', 'Intelligence Newsletter')
    language = client_profile.get('language', 'en')
    tone = client_profile.get('tone', 'executive')
    voice = client_profile.get('voice', 'concise')
    
    # Construire la liste des items par section
    sections_text = ""
    for section in sections_data:
        sections_text += f"\n### {section['title']}\n"
        for item in section['items']:
            sections_text += f"\n- **{item.get('title', 'Untitled')}**\n"
            sections_text += f"  Summary: {item.get('summary', 'No summary')}\n"
            sections_text += f"  Source: {item.get('source_key', 'Unknown')}\n"
            sections_text += f"  Date: {item.get('date', 'Unknown')}\n"
            sections_text += f"  URL: {item.get('url', '#')}\n"
    
    prompt = f"""You are an expert biotech/pharma intelligence analyst writing a premium newsletter.

CONTEXT:
- Newsletter: {client_name}
- Period: {from_date} to {to_date}
- Target date: {target_date}
- Total items analyzed: {total_items_analyzed}
- Language: {language}
- Tone: {tone}
- Voice: {voice}

SELECTED ITEMS BY SECTION:
{sections_text}

TASK:
Generate editorial content for this newsletter. You MUST respond with ONLY a JSON object (no additional text).

RESPONSE FORMAT (JSON only):
{{
  "title": "Newsletter title (e.g., 'Weekly Biotech Intelligence – {target_date}')",
  "intro": "2-4 sentences summarizing the week's context",
  "tldr": ["Bullet point 1", "Bullet point 2", "Bullet point 3"],
  "sections": [
    {{
      "section_title": "Section title from input",
      "section_intro": "1-2 sentences introducing this section",
      "items": [
        {{
          "title": "Item title from input",
          "rewritten_summary": "Concise rewrite of the summary (2-3 sentences)",
          "url": "URL from input"
        }}
      ]
    }}
  ]
}}

CONSTRAINTS:
- Do NOT hallucinate facts, dates, or names
- Keep company names, molecule names, and technology terms EXACTLY as provided
- Respect the language: write in {language}
- Respect the tone ({tone}) and voice ({voice})
- Be concise and factual

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


def _parse_editorial_response(response_text: str) -> Dict[str, Any]:
    """
    Parse la réponse JSON de Bedrock.
    """
    try:
        # Tenter de parser directement comme JSON
        result = json.loads(response_text)
        
        # Valider la structure
        if not isinstance(result, dict):
            raise ValueError("La réponse n'est pas un dictionnaire")
        
        # S'assurer que les champs obligatoires existent
        result.setdefault('title', 'Newsletter')
        result.setdefault('intro', '')
        result.setdefault('tldr', [])
        result.setdefault('sections', [])
        
        return result
    
    except json.JSONDecodeError:
        logger.warning("Réponse Bedrock non-JSON, tentative d'extraction manuelle")
        # Fallback : retourner une structure minimale
        return {
            'title': 'Newsletter',
            'intro': response_text[:500] if response_text else '',
            'tldr': [],
            'sections': []
        }


def _generate_fallback_editorial(
    sections_data: List[Dict[str, Any]],
    client_profile: Dict[str, Any],
    target_date: str
) -> Dict[str, Any]:
    """
    Génère un contenu éditorial minimal en cas d'échec Bedrock.
    """
    client_name = client_profile.get('name', 'Intelligence Newsletter')
    language = client_profile.get('language', 'en')
    
    if language == 'fr':
        title = f"{client_name} – {target_date}"
        intro = "Newsletter générée en mode dégradé (erreur Bedrock)."
    else:
        title = f"{client_name} – {target_date}"
        intro = "Newsletter generated in fallback mode (Bedrock error)."
    
    # Construire les sections sans réécriture
    sections = []
    for section in sections_data:
        section_items = []
        for item in section['items']:
            section_items.append({
                'title': item.get('title', 'Untitled'),
                'rewritten_summary': item.get('summary', 'No summary'),
                'url': item.get('url', '#')
            })
        
        sections.append({
            'section_title': section['title'],
            'section_intro': '',
            'items': section_items
        })
    
    return {
        'title': title,
        'intro': intro,
        'tldr': [],
        'sections': sections
    }
