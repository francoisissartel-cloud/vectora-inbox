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
import os
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
    region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    return boto3.client('bedrock-runtime', region_name=region)


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
    
    # Appel avec retry sur ThrottlingException - Optimisé Phase 1
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 6000,  # Réduit de 8000 à 6000 pour éviter les timeouts
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2  # Plus déterministe pour JSON stable
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
    Construit le prompt optimisé pour Bedrock newsletter.
    
    Optimisations Phase 1 :
    - Prompt plus concis (-30% tokens)
    - Instructions simplifiées
    - Moins d'exemples verbeux
    """
    client_name = client_profile.get('name', 'Intelligence Newsletter')
    language = client_profile.get('language', 'en')
    tone = client_profile.get('tone', 'executive')
    
    # Construire la liste des items par section (format compact)
    sections_text = ""
    for section in sections_data:
        sections_text += f"\n## {section['title']}\n"
        for item in section['items'][:3]:  # Limiter à 3 items par section pour réduire la taille
            title = item.get('title', 'Untitled')[:100]  # Tronquer les titres longs
            summary = item.get('summary', 'No summary')[:200]  # Tronquer les résumés
            sections_text += f"- {title}: {summary}\n"
    
    # Prompt optimisé et plus court
    prompt = f"""Generate newsletter editorial content as JSON.

Context: {client_name}, {from_date} to {to_date}, {language}, {tone} tone

Items:
{sections_text}

Output ONLY valid JSON:
{{
  "title": "Newsletter title with {target_date}",
  "intro": "1-2 sentence summary",
  "tldr": ["key point 1", "key point 2"],
  "sections": [
    {{
      "section_title": "section name",
      "section_intro": "1 sentence",
      "items": [
        {{
          "title": "item title",
          "rewritten_summary": "2 sentences max",
          "url": "#"
        }}
      ]
    }}
  ]
}}

Rules: JSON only, no markdown, be concise, keep original names/terms."""
    
    return prompt


def _call_bedrock_with_retry(
    model_id: str,
    request_body: Dict[str, Any],
    max_retries: int = 4,
    base_delay: float = 2.0
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
                    # Backoff plus agressif pour newsletter (délais plus longs)
                    delay = base_delay * (3 ** attempt) + random.uniform(0.5, 1.5)
                    logger.warning(
                        f"Newsletter Bedrock ThrottlingException (tentative {attempt + 1}/{max_retries + 1}). "
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
        # Nettoyer la réponse : retirer les balises markdown si présentes
        cleaned_text = response_text.strip()
        
        # Si la réponse contient des balises ```json ... ```, les extraire
        if '```json' in cleaned_text:
            logger.info("Détection de balises markdown JSON, extraction...")
            start_idx = cleaned_text.find('```json') + 7
            end_idx = cleaned_text.rfind('```')
            if start_idx > 7 and end_idx > start_idx:
                cleaned_text = cleaned_text[start_idx:end_idx].strip()
        elif '```' in cleaned_text:
            logger.info("Détection de balises markdown génériques, extraction...")
            start_idx = cleaned_text.find('```') + 3
            end_idx = cleaned_text.rfind('```')
            if start_idx > 3 and end_idx > start_idx:
                cleaned_text = cleaned_text[start_idx:end_idx].strip()
        
        # Nettoyage supplémentaire : retirer les caractères de contrôle
        cleaned_text = cleaned_text.replace('\r', '').replace('\n', ' ').strip()
        
        # Si le texte commence par '{' et finit par '}', c'est probablement du JSON
        if cleaned_text.startswith('{') and cleaned_text.endswith('}'):
            # Restaurer les sauts de ligne pour un JSON valide
            cleaned_text = cleaned_text.replace(' {', '{').replace('} ', '}')
            # Essayer de reformater le JSON
            try:
                temp_json = json.loads(cleaned_text)
                cleaned_text = json.dumps(temp_json)
            except:
                pass  # Garder le texte original si le reformatage échoue
        
        # Tenter de parser comme JSON
        result = json.loads(cleaned_text)
        
        # Valider la structure
        if not isinstance(result, dict):
            raise ValueError("La réponse n'est pas un dictionnaire")
        
        # S'assurer que les champs obligatoires existent
        result.setdefault('title', 'Newsletter')
        result.setdefault('intro', '')
        result.setdefault('tldr', [])
        result.setdefault('sections', [])
        
        logger.info(f"JSON parsé avec succès : {len(result.get('sections', []))} sections")
        return result
    
    except json.JSONDecodeError as e:
        logger.warning(f"Réponse Bedrock non-JSON ({e}), tentative d'extraction manuelle")
        logger.debug(f"Réponse brute complète: {response_text}")
        logger.debug(f"Longueur de la réponse: {len(response_text)} caractères")
        
        # Tentative d'extraction plus agressive
        try:
            # Chercher le premier { et le dernier }
            start_brace = response_text.find('{')
            end_brace = response_text.rfind('}')
            
            if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                json_candidate = response_text[start_brace:end_brace + 1]
                result = json.loads(json_candidate)
                logger.info("Extraction JSON réussie avec méthode alternative")
                
                # S'assurer que les champs obligatoires existent
                result.setdefault('title', 'Newsletter')
                result.setdefault('intro', '')
                result.setdefault('tldr', [])
                result.setdefault('sections', [])
                
                return result
        except Exception as e2:
            logger.warning(f"Extraction alternative échouée: {e2}")
        
        # Fallback final : retourner une structure minimale
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
