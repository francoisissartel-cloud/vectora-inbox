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
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_bedrock_client():
    """
    Retourne un client boto3 Bedrock Runtime (backward compatibility).
    
    Returns:
        Client boto3 bedrock-runtime configuré
    """
    region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    return boto3.client('bedrock-runtime', region_name=region)


def get_bedrock_client_hybrid(service_type: str = 'newsletter') -> Tuple[Any, str]:
    """
    Client Bedrock hybride P1 selon le service.
    
    Args:
        service_type: 'normalization' ou 'newsletter'
    
    Returns:
        Tuple (client, model_id)
    """
    if service_type == 'normalization':
        region = os.environ.get('BEDROCK_REGION_NORMALIZATION', 'us-east-1')
        model_id = os.environ.get('BEDROCK_MODEL_ID_NORMALIZATION', 
                                 'us.anthropic.claude-sonnet-4-5-20250929-v1:0')
    elif service_type == 'newsletter':
        region = os.environ.get('BEDROCK_REGION_NEWSLETTER', 'eu-west-3')
        model_id = os.environ.get('BEDROCK_MODEL_ID_NEWSLETTER', 
                                 'eu.anthropic.claude-sonnet-4-5-20250929-v1:0')
    else:
        # Fallback vers configuration actuelle
        region = os.environ.get('BEDROCK_REGION', 'us-east-1')
        model_id = os.environ.get('BEDROCK_MODEL_ID', 
                                 'us.anthropic.claude-sonnet-4-5-20250929-v1:0')
    
    client = boto3.client('bedrock-runtime', region_name=region)
    logger.info(f"Client Bedrock hybride : {service_type} → {region}")
    
    return client, model_id


def generate_editorial_content(
    sections_data: List[Dict[str, Any]],
    client_profile: Dict[str, Any],
    bedrock_model_id: str,
    target_date: str,
    from_date: str,
    to_date: str,
    total_items_analyzed: int,
    client_id: Optional[str] = None,
    newsletters_bucket: Optional[str] = None,
    force_regenerate: bool = False
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
    # P1: Tentative lecture cache
    if not force_regenerate and client_id and newsletters_bucket:
        cached = get_cached_newsletter(client_id, from_date, to_date, newsletters_bucket)
        if cached:
            logger.info("Newsletter récupérée depuis cache S3")
            return cached
    
    # P1: Client Bedrock hybride (eu-west-3 pour newsletter)
    client, model_id = get_bedrock_client_hybrid('newsletter')
    
    # P1: Prompt ultra-réduit (-80% tokens)
    prompt = _build_ultra_compact_prompt(sections_data, client_profile, target_date)
    
    # P1: Paramètres optimisés
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4000,  # Réduit pour prompt plus court
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2  # Plus déterministe pour JSON stable
    }
    
    try:
        response_text = _call_bedrock_with_retry(model_id, request_body, client)
        result = _parse_editorial_response(response_text)
        
        # P1: Sauvegarde cache
        if client_id and newsletters_bucket:
            save_editorial_to_cache(client_id, from_date, to_date, result, newsletters_bucket)
        
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
    Prompt original (backward compatibility).
    P1: Délègue au prompt ultra-compact.
    Phase 2A: Support prompts canonicalisés.
    """
    # P1: Déléguer au prompt ultra-compact (avec support canonicalisé)
    return _build_ultra_compact_prompt(sections_data, client_profile, target_date)


def _call_bedrock_with_retry(
    model_id: str,
    request_body: Dict[str, Any],
    client: Optional[Any] = None,
    max_retries: int = 4,
    base_delay: float = 2.0
) -> str:
    """
    Appelle Bedrock avec retry automatique sur ThrottlingException.
    """
    if client is None:
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


# ============================================================================
# P1: FONCTIONS CACHE S3
# ============================================================================

def get_cached_newsletter(client_id: str, period_start: str, period_end: str, 
                         newsletters_bucket: str) -> Optional[Dict[str, Any]]:
    """
    P1: Récupère newsletter depuis cache S3 si disponible.
    
    Args:
        client_id: ID du client
        period_start: Date de début période
        period_end: Date de fin période
        newsletters_bucket: Bucket S3 newsletters
    
    Returns:
        Contenu éditorial depuis cache ou None
    """
    cache_key = f"cache/{client_id}/{period_start}_{period_end}/newsletter.json"
    
    try:
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=newsletters_bucket, Key=cache_key)
        cached_content = json.loads(response['Body'].read())
        
        logger.info(f"Newsletter trouvée en cache : {cache_key}")
        return cached_content
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.info(f"Pas de cache pour : {cache_key}")
            return None
        else:
            logger.warning(f"Erreur lecture cache : {e}")
            return None
    except Exception as e:
        logger.warning(f"Erreur inattendue lecture cache : {e}")
        return None


def save_editorial_to_cache(client_id: str, period_start: str, period_end: str,
                           editorial_content: Dict[str, Any], newsletters_bucket: str) -> None:
    """
    P1: Sauvegarde contenu éditorial en cache S3.
    
    Args:
        client_id: ID du client
        period_start: Date de début période
        period_end: Date de fin période
        editorial_content: Contenu éditorial à cacher
        newsletters_bucket: Bucket S3 newsletters
    """
    cache_prefix = f"cache/{client_id}/{period_start}_{period_end}/"
    
    # Métadonnées
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "client_id": client_id,
        "period_start": period_start,
        "period_end": period_end,
        "version": "1.0",
        "generator": "vectora-inbox-p1"
    }
    
    try:
        s3_client = boto3.client('s3')
        
        # Sauvegarder contenu éditorial
        s3_client.put_object(
            Bucket=newsletters_bucket,
            Key=cache_prefix + "newsletter.json",
            Body=json.dumps(editorial_content, indent=2),
            ContentType='application/json'
        )
        
        # Sauvegarder métadonnées
        s3_client.put_object(
            Bucket=newsletters_bucket,
            Key=cache_prefix + "metadata.json",
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Newsletter sauvegardée en cache : {cache_prefix}")
    
    except Exception as e:
        logger.warning(f"Erreur sauvegarde cache : {e}")
        # Ne pas faire échouer la génération si le cache échoue


# ============================================================================
# P1: PROMPT ULTRA-RÉDUIT
# ============================================================================

def _build_ultra_compact_prompt(
    sections_data: List[Dict[str, Any]],
    client_profile: Dict[str, Any],
    target_date: str
) -> str:
    """
    P1: Prompt ultra-réduit (-80% tokens vs version initiale).
    Phase 2A: Support prompts canonicalisés avec fallback.
    
    Optimisations P1 :
    - Instructions minimales
    - 2 items max par section (vs 3)
    - Titres 60 chars (vs 100)
    - Résumés 80 chars (vs 200)
    - JSON inline compact
    """
    # Phase 2A: Tentative prompt canonicalisé
    if os.environ.get('USE_CANONICAL_PROMPTS', 'false').lower() == 'true':
        try:
            from ..prompts.loader import get_prompt_loader
            
            config_bucket = os.environ.get('CONFIG_BUCKET')
            prompt_loader = get_prompt_loader(config_bucket)
            canonical_prompt = prompt_loader.get_prompt("newsletter.editorial_generation")
            
            if canonical_prompt:
                logger.info("Utilisation du prompt newsletter canonicalisé")
                return _build_prompt_from_canonical(
                    canonical_prompt, sections_data, client_profile, target_date
                )
            else:
                logger.warning("Prompt newsletter canonicalisé non trouvé, fallback vers hardcodé")
        except Exception as e:
            logger.warning(f"Erreur chargement prompt canonicalisé: {e}, fallback vers hardcodé")
    
    # Fallback: Prompt hardcodé actuel (P1)
    logger.info("Utilisation du prompt newsletter hardcodé")
    return _build_hardcoded_prompt(sections_data, client_profile, target_date)


def _build_prompt_from_canonical(
    canonical_prompt: Dict[str, Any],
    sections_data: List[Dict[str, Any]],
    client_profile: Dict[str, Any],
    target_date: str
) -> str:
    """
    Construit le prompt depuis la version canonicalisée.
    
    Args:
        canonical_prompt: Prompt canonicalisé depuis YAML
        sections_data: Sections avec items sélectionnés
        client_profile: Profil du client
        target_date: Date de référence
    
    Returns:
        Prompt complet pour Bedrock
    """
    client_name = client_profile.get('name', 'LAI Weekly')
    
    # Items ultra-compacts (2 par section max)
    items_text = ""
    for section in sections_data:
        items_text += f"\n{section['title']}:\n"
        for item in section['items'][:2]:  # P1: Réduction 3→2 items
            title = item.get('title', '')[:60]  # P1: Réduction 100→60 chars
            summary = item.get('summary', '')[:80]  # P1: Réduction 200→80 chars
            items_text += f"• {title}: {summary}\n"
    
    # Substituer les placeholders dans le template
    user_template = canonical_prompt.get('user_template', '')
    prompt = user_template.replace('{{client_name}}', client_name)
    prompt = prompt.replace('{{target_date}}', target_date)
    prompt = prompt.replace('{{items_text}}', items_text)
    
    return prompt


def _build_hardcoded_prompt(
    sections_data: List[Dict[str, Any]],
    client_profile: Dict[str, Any],
    target_date: str
) -> str:
    """
    Prompt hardcodé original (fallback).
    """
    client_name = client_profile.get('name', 'LAI Weekly')
    
    # Items ultra-compacts (2 par section max)
    items_text = ""
    for section in sections_data:
        items_text += f"\n{section['title']}:\n"
        for item in section['items'][:2]:  # P1: Réduction 3→2 items
            title = item.get('title', '')[:60]  # P1: Réduction 100→60 chars
            summary = item.get('summary', '')[:80]  # P1: Réduction 200→80 chars
            items_text += f"• {title}: {summary}\n"
    
    # P1: Prompt ultra-minimal
    return f"""JSON newsletter for {client_name} - {target_date}:

{items_text}

Output:
{{"title":"{client_name} – {target_date}","intro":"1 sentence","tldr":["point1","point2"],"sections":[{{"section_title":"name","section_intro":"1 sentence","items":[{{"title":"title","rewritten_summary":"2 sentences","url":"#"}}]}}]}}

Rules: JSON only, concise, preserve names."""
