"""
Module bedrock_editor - Génération de contenu éditorial via Bedrock
Approche B: Utilise prompt_resolver pour chargement prompts canonical
"""
import logging
import json
import boto3
from botocore.exceptions import ClientError
from ..shared import prompt_resolver

logger = logging.getLogger(__name__)

def generate_editorial_content(selected_items, client_config, env_vars, s3_io, canonical_scopes, week_start, week_end):
    """
    Génère le contenu éditorial via Bedrock (Approche B)
    
    Args:
        selected_items: Items sélectionnés par section
        client_config: Configuration client
        env_vars: Variables d'environnement (Bedrock config)
        s3_io: Module s3_io pour accès S3
        canonical_scopes: Scopes canonical chargés
        week_start: Date début période (format: "Jan 27, 2026")
        week_end: Date fin période (format: "Feb 02, 2026")
    
    Returns:
        dict: Contenu éditorial avec TL;DR et introduction
    """
    logger.info("Generating editorial content via Bedrock (Approche B)")
    
    try:
        # Chargement prompt template via Approche B
        editorial_prompt = client_config.get('bedrock_config', {}).get('editorial_prompt', 'lai_editorial')
        
        prompt_template = prompt_resolver.load_prompt_template(
            'editorial',
            editorial_prompt,
            s3_io,
            env_vars["CONFIG_BUCKET"]
        )
        
        if not prompt_template:
            raise ValueError(f"Editorial prompt template not found: {editorial_prompt}")
        
        # Initialisation client Bedrock
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=env_vars["BEDROCK_REGION"]
        )
        
        # Préparation des données pour les prompts
        items_summary = _prepare_items_summary(selected_items)
        sections_summary = _prepare_sections_summary(selected_items)
        total_items = len(_get_all_items(selected_items))
        
        editorial_content = {
            "bedrock_calls": {}
        }
        
        # 1. Génération TL;DR
        try:
            tldr = _generate_tldr_approche_b(
                bedrock_client, prompt_template, canonical_scopes,
                items_summary, env_vars["BEDROCK_MODEL_ID"]
            )
            editorial_content["tldr"] = tldr
            editorial_content["bedrock_calls"]["tldr_generation"] = {"status": "success"}
        except Exception as e:
            logger.error(f"TL;DR generation failed: {str(e)}")
            editorial_content["tldr"] = "This week's LAI ecosystem shows continued innovation and partnership activity."
            editorial_content["bedrock_calls"]["tldr_generation"] = {"status": "failed", "error": str(e)}
        
        # 2. Génération Introduction
        try:
            introduction = _generate_introduction_approche_b(
                bedrock_client, prompt_template, canonical_scopes,
                week_start, week_end, sections_summary, total_items, env_vars["BEDROCK_MODEL_ID"]
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

def _generate_tldr_approche_b(bedrock_client, prompt_template, canonical_scopes, items_summary, model_id):
    """Génère le TL;DR via Bedrock (Approche B)"""
    
    tldr_config = prompt_template.get('tldr_generation', {})
    if not tldr_config:
        raise ValueError("tldr_generation not found in prompt template")
    
    # Construction du prompt via prompt_resolver
    user_prompt = prompt_resolver.build_prompt(
        tldr_config,
        canonical_scopes,
        {'items_summary': items_summary}
    )
    
    system_prompt = tldr_config.get('system_instructions', '')
    
    # Appel Bedrock
    response = _call_bedrock(
        bedrock_client, model_id, system_prompt, user_prompt,
        max_tokens=tldr_config.get('bedrock_config', {}).get('max_tokens', 200),
        temperature=tldr_config.get('bedrock_config', {}).get('temperature', 0.1)
    )
    
    return response.strip()

def _generate_introduction_approche_b(bedrock_client, prompt_template, canonical_scopes, 
                                      week_start, week_end, sections_summary, total_items, model_id):
    """Génère l'introduction via Bedrock (Approche B)"""
    
    intro_config = prompt_template.get('introduction_generation', {})
    if not intro_config:
        raise ValueError("introduction_generation not found in prompt template")
    
    # Construction du prompt via prompt_resolver
    user_prompt = prompt_resolver.build_prompt(
        intro_config,
        canonical_scopes,
        {
            'week_start': week_start,
            'week_end': week_end,
            'sections_summary': sections_summary,
            'total_items': str(total_items)
        }
    )
    
    system_prompt = intro_config.get('system_instructions', '')
    
    # Appel Bedrock
    response = _call_bedrock(
        bedrock_client, model_id, system_prompt, user_prompt,
        max_tokens=intro_config.get('bedrock_config', {}).get('max_tokens', 300),
        temperature=intro_config.get('bedrock_config', {}).get('temperature', 0.1)
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