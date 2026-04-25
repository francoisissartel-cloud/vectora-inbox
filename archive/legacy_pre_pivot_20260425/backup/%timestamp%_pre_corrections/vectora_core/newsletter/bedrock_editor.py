"""
Module bedrock_editor - Génération de contenu éditorial via Bedrock
Implémente les appels TL;DR et introduction selon le plan Phase 4
"""
import logging
import json
import boto3
from botocore.exceptions import ClientError
from ..shared import config_loader

logger = logging.getLogger(__name__)

def generate_editorial_content(selected_items, client_config, env_vars):
    """
    Génère le contenu éditorial via Bedrock
    
    Args:
        selected_items: Items sélectionnés par section
        client_config: Configuration client
        env_vars: Variables d'environnement (Bedrock config)
    
    Returns:
        dict: Contenu éditorial avec TL;DR et introduction
    """
    logger.info("Generating editorial content via Bedrock")
    
    try:
        # Chargement des prompts
        prompts = config_loader.load_canonical_prompts(env_vars["CONFIG_BUCKET"])
        
        # Initialisation client Bedrock
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=env_vars["BEDROCK_REGION"]
        )
        
        # Préparation des données pour les prompts
        items_summary = _prepare_items_summary(selected_items)
        sections_summary = _prepare_sections_summary(selected_items)
        
        editorial_content = {
            "bedrock_calls": {}
        }
        
        # 1. Génération TL;DR
        try:
            tldr = _generate_tldr(
                bedrock_client, prompts, items_summary, env_vars["BEDROCK_MODEL_ID"]
            )
            editorial_content["tldr"] = tldr
            editorial_content["bedrock_calls"]["tldr_generation"] = {"status": "success"}
        except Exception as e:
            logger.error(f"TL;DR generation failed: {str(e)}")
            editorial_content["tldr"] = "This week's LAI ecosystem shows continued innovation and partnership activity."
            editorial_content["bedrock_calls"]["tldr_generation"] = {"status": "failed", "error": str(e)}
        
        # 2. Génération Introduction
        try:
            introduction = _generate_introduction(
                bedrock_client, prompts, sections_summary, len(_get_all_items(selected_items)), env_vars["BEDROCK_MODEL_ID"]
            )
            editorial_content["introduction"] = introduction
            editorial_content["bedrock_calls"]["introduction_generation"] = {"status": "success"}
        except Exception as e:
            logger.error(f"Introduction generation failed: {str(e)}")
            editorial_content["introduction"] = "Executive intelligence on Long-Acting Injectable technologies and ecosystem."
            editorial_content["bedrock_calls"]["introduction_generation"] = {"status": "failed", "error": str(e)}
        
        return editorial_content
        
    except Exception as e:
        logger.error(f"Editorial content generation failed: {str(e)}")
        # Fallback content
        return {
            "tldr": "This week's LAI ecosystem shows continued innovation and partnership activity.",
            "introduction": "Executive intelligence on Long-Acting Injectable technologies and ecosystem.",
            "bedrock_calls": {
                "tldr_generation": {"status": "failed", "error": str(e)},
                "introduction_generation": {"status": "failed", "error": str(e)}
            }
        }

def _generate_tldr(bedrock_client, prompts, items_summary, model_id):
    """Génère le TL;DR via Bedrock"""
    
    prompt_config = prompts.get('newsletter', {}).get('tldr_generation', {})
    if not prompt_config:
        raise ValueError("TL;DR prompt not found in global_prompts.yaml")
    
    # Construction du prompt
    system_prompt = prompt_config.get('system_instructions', '')
    user_template = prompt_config.get('user_template', '')
    user_prompt = user_template.replace('{{items_summary}}', items_summary)
    
    # Appel Bedrock
    response = _call_bedrock(
        bedrock_client, model_id, system_prompt, user_prompt,
        max_tokens=prompt_config.get('bedrock_config', {}).get('max_tokens', 200),
        temperature=prompt_config.get('bedrock_config', {}).get('temperature', 0.1)
    )
    
    return response.strip()

def _generate_introduction(bedrock_client, prompts, sections_summary, total_items, model_id):
    """Génère l'introduction via Bedrock"""
    
    prompt_config = prompts.get('newsletter', {}).get('introduction_generation', {})
    if not prompt_config:
        raise ValueError("Introduction prompt not found in global_prompts.yaml")
    
    # Construction du prompt
    system_prompt = prompt_config.get('system_instructions', '')
    user_template = prompt_config.get('user_template', '')
    
    # Substitution des variables
    user_prompt = user_template.replace('{{week_start}}', 'December 16, 2025')
    user_prompt = user_prompt.replace('{{week_end}}', 'December 22, 2025')
    user_prompt = user_prompt.replace('{{sections_summary}}', sections_summary)
    user_prompt = user_prompt.replace('{{total_items}}', str(total_items))
    
    # Appel Bedrock
    response = _call_bedrock(
        bedrock_client, model_id, system_prompt, user_prompt,
        max_tokens=prompt_config.get('bedrock_config', {}).get('max_tokens', 300),
        temperature=prompt_config.get('bedrock_config', {}).get('temperature', 0.1)
    )
    
    return response.strip()

def _call_bedrock(bedrock_client, model_id, system_prompt, user_prompt, max_tokens=200, temperature=0.1):
    """Effectue un appel générique à Bedrock"""
    
    # Construction du payload pour Claude 3 Sonnet
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    }
    
    try:
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(payload),
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and response_body['content']:
            return response_body['content'][0]['text']
        else:
            raise ValueError("Invalid response format from Bedrock")
            
    except ClientError as e:
        logger.error(f"Bedrock API error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Bedrock call failed: {str(e)}")
        raise

def _prepare_items_summary(selected_items):
    """Prépare un résumé des items pour les prompts"""
    all_items = _get_all_items(selected_items)
    
    summaries = []
    for item in all_items[:8]:  # Limiter à 8 items pour le prompt
        normalized = item.get('normalized_content', {})
        title = normalized.get('summary', 'Untitled')[:80]
        score = item.get('scoring_results', {}).get('final_score', 0)
        companies = ', '.join(normalized.get('entities', {}).get('companies', [])[:2])
        
        summaries.append(f"- {title} (Score: {score:.1f}, Companies: {companies})")
    
    return '\n'.join(summaries)

def _prepare_sections_summary(selected_items):
    """Prépare un résumé des sections pour les prompts"""
    sections = []
    for section_id, section_data in selected_items.items():
        if section_data['items']:
            sections.append(f"{section_data['title']} ({len(section_data['items'])} items)")
    
    return ', '.join(sections)

def _get_all_items(selected_items):
    """Récupère tous les items de toutes les sections"""
    all_items = []
    for section_data in selected_items.values():
        all_items.extend(section_data['items'])
    
    # Tri par score décroissant
    all_items.sort(key=lambda x: x.get('scoring_results', {}).get('final_score', 0), reverse=True)
    
    return all_items