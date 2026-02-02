"""
Module de matching Bedrock pour les domaines de veille.

Ce module implémente le matching sémantique via Bedrock pour déterminer
quels domaines de veille correspondent aux items normalisés.
"""

import json
import logging
from typing import Dict, List, Any, Optional

from .bedrock_client import call_bedrock_with_retry

logger = logging.getLogger(__name__)


def match_item_to_domains_bedrock(
    normalized_item: Dict[str, Any],
    watch_domains: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any],
    matching_config: Dict[str, Any],
    canonical_prompts: Dict[str, Any],
    bedrock_model: str
) -> Dict[str, Any]:
    """
    Matche un item normalisé aux domaines de veille via Bedrock.
    
    Args:
        normalized_item: Item avec entités extraites
        watch_domains: Domaines de veille configurés
        canonical_scopes: Scopes canonical
        matching_config: Configuration matching
        canonical_prompts: Prompts canonical
        bedrock_model: Modèle Bedrock
    
    Returns:
        Résultats de matching avec domaines et scores
    """
    logger.info(f"DEBUG: watch_domains reçus: {len(watch_domains)} domaines")
    logger.info(f"DEBUG: watch_domains détail: {[d.get('id') for d in watch_domains]}")
    
    if not watch_domains:
        logger.debug("Aucun domaine de veille configuré")
        return {"matched_domains": [], "domain_relevance": {}}
    
    try:
        # Construction du contexte pour Bedrock
        item_context = _build_item_context(normalized_item)
        domains_context = _build_domains_context(watch_domains, canonical_scopes)
        
        # Appel Bedrock pour matching
        matching_result = _call_bedrock_matching(
            item_context, domains_context, canonical_prompts, bedrock_model
        )
        logger.info(f"DEBUG: Résultat Bedrock brut: {str(matching_result)[:200]}...")
        
        # Application des seuils configurés
        filtered_result = _apply_matching_thresholds(matching_result, matching_config)
        logger.info(f"DEBUG: Après seuils: {filtered_result}")
        
        logger.debug(f"Matching Bedrock: {len(filtered_result['matched_domains'])} domaines matchés")
        return filtered_result
        
    except Exception as e:
        logger.error(f"Erreur matching Bedrock: {str(e)}")
        return {"matched_domains": [], "domain_relevance": {}}


def _build_item_context(normalized_item: Dict[str, Any]) -> Dict[str, Any]:
    """Construit le contexte de l'item pour Bedrock."""
    normalized_content = normalized_item.get("normalized_content", {})
    
    return {
        "title": normalized_item.get("title", ""),
        "summary": normalized_content.get("summary", ""),
        "entities": normalized_content.get("entities", {}),
        "event_type": normalized_content.get("event_classification", {}).get("primary_type", "other")
        # REMOVED: "lai_relevance_score" (deprecated - now using domain_scoring)
    }


def _build_domains_context(
    watch_domains: List[Dict[str, Any]], 
    canonical_scopes: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Construit le contexte des domaines pour Bedrock."""
    domains_context = []
    
    for domain in watch_domains:
        domain_id = domain.get("id")
        domain_type = domain.get("type", "technology")
        
        # Récupération des scopes du domaine
        company_scope = domain.get("company_scope")
        technology_scope = domain.get("technology_scope")
        trademark_scope = domain.get("trademark_scope")
        
        # Construction du contexte du domaine
        domain_context = {
            "domain_id": domain_id,
            "domain_type": domain_type,
            "focus_areas": []
        }
        
        # Ajout des exemples d'entités
        if company_scope:
            companies = canonical_scopes.get(company_scope, [])[:10]  # Limite pour prompt
            if companies:
                domain_context["focus_areas"].append(f"Companies: {', '.join(companies)}")
        
        if technology_scope:
            technologies = canonical_scopes.get(technology_scope, [])
            if isinstance(technologies, list):
                tech_sample = technologies[:10]
            else:
                # Pour lai_keywords qui est complexe, prendre core_phrases
                tech_sample = technologies.get("core_phrases", [])[:10] if isinstance(technologies, dict) else []
            
            if tech_sample:
                domain_context["focus_areas"].append(f"Technologies: {', '.join(tech_sample)}")
        
        if trademark_scope:
            trademarks = canonical_scopes.get(trademark_scope, [])[:5]
            if trademarks:
                domain_context["focus_areas"].append(f"Trademarks: {', '.join(trademarks)}")
        
        domains_context.append(domain_context)
    
    return domains_context


def _call_bedrock_matching(
    item_context: Dict[str, Any],
    domains_context: List[Dict[str, Any]],
    canonical_prompts: Dict[str, Any],
    bedrock_model: str
) -> Dict[str, Any]:
    """Appelle Bedrock pour le matching sémantique."""
    
    # Récupération du prompt de matching
    matching_prompt_config = canonical_prompts.get("matching", {}).get("matching_watch_domains_v2", {})
    
    if not matching_prompt_config:
        logger.warning("Prompt matching non trouvé, utilisation du prompt par défaut")
        return {"domain_evaluations": []}
    
    # Construction du prompt
    user_template = matching_prompt_config.get("user_template", "")
    
    # Substitution des variables
    domains_context_text = "\n".join([
        f"- {d['domain_id']} ({d['domain_type']}): {'; '.join(d['focus_areas'])}"
        for d in domains_context
    ])
    
    entities_text = json.dumps(item_context["entities"], indent=2)
    
    prompt = user_template.replace("{{item_title}}", item_context["title"])
    prompt = prompt.replace("{{item_summary}}", item_context["summary"])
    prompt = prompt.replace("{{item_entities}}", entities_text)
    prompt = prompt.replace("{{item_event_type}}", item_context["event_type"])
    prompt = prompt.replace("{{domains_context}}", domains_context_text)
    
    logger.info(f"DEBUG: Prompt Bedrock (premiers 300 chars): {prompt[:300]}...")
    
    # Configuration Bedrock
    bedrock_config = matching_prompt_config.get("bedrock_config", {})
    
    request_body = {
        "anthropic_version": bedrock_config.get("anthropic_version", "bedrock-2023-05-31"),
        "max_tokens": bedrock_config.get("max_tokens", 1500),
        "temperature": bedrock_config.get("temperature", 0.1),
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    # Appel Bedrock avec retry
    response_text = call_bedrock_with_retry(bedrock_model, request_body)
    logger.info(f"DEBUG: Réponse Bedrock brute: {response_text[:200]}...")
    
    # Parse de la réponse
    return _parse_bedrock_matching_response(response_text)


def _parse_bedrock_matching_response(response_text: str) -> Dict[str, Any]:
    """Parse la réponse Bedrock de matching."""
    try:
        result = json.loads(response_text)
        
        if not isinstance(result, dict) or "domain_evaluations" not in result:
            logger.warning("Réponse Bedrock matching mal formatée")
            return {"domain_evaluations": []}
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"Erreur parsing réponse Bedrock matching: {str(e)}")
        return {"domain_evaluations": []}


def _apply_matching_thresholds(
    matching_result: Dict[str, Any],
    matching_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Applique les seuils de matching configurés."""
    
    domain_evaluations = matching_result.get("domain_evaluations", [])
    min_domain_score = matching_config.get("min_domain_score", 0.25)
    
    matched_domains = []
    domain_relevance = {}
    
    for evaluation in domain_evaluations:
        domain_id = evaluation.get("domain_id")
        is_relevant = evaluation.get("is_relevant", False)
        relevance_score = evaluation.get("relevance_score", 0.0)
        confidence = evaluation.get("confidence", "low")
        
        # Application des seuils
        if is_relevant and relevance_score >= min_domain_score:
            matched_domains.append(domain_id)
            domain_relevance[domain_id] = {
                "score": relevance_score,
                "confidence": confidence,
                "reasoning": evaluation.get("reasoning", ""),
                "matched_entities": evaluation.get("matched_entities", {})
            }
    
    return {
        "matched_domains": matched_domains,
        "domain_relevance": domain_relevance,
        "bedrock_matching_used": True
    }