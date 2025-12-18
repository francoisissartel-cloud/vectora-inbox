"""
Module de matching Bedrock pour normalize_score V2.

Évalue la pertinence d'items normalisés par rapport aux watch_domains via Bedrock.
Respecte l'architecture src_v2 et les règles hygiene_v4.
"""

import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def match_watch_domains_with_bedrock(
    normalized_item: Dict[str, Any],
    watch_domains: List[Dict[str, Any]], 
    canonical_scopes: Dict[str, Any],
    bedrock_model_id: str,
    bedrock_region: str = "us-east-1"
) -> Dict[str, Any]:
    """
    Évalue la pertinence d'un item normalisé par rapport aux watch_domains via Bedrock.
    
    Args:
        normalized_item: Item avec title, summary, entities, event_type
        watch_domains: Liste des domaines de veille configurés
        canonical_scopes: Scopes canonical chargés
        bedrock_model_id: Modèle Bedrock à utiliser
        bedrock_region: Région Bedrock
    
    Returns:
        {
            "matched_domains": ["tech_lai_ecosystem"],
            "domain_relevance": {...}
        }
    """
    logger.info(f"Matching Bedrock V2 pour item: {normalized_item.get('title', '')[:50]}...")
    
    try:
        # Validation des inputs
        if not watch_domains:
            logger.debug("Aucun watch_domain configuré, retour structure vide")
            return {"matched_domains": [], "domain_relevance": {}}
        
        # Construire le contexte des domaines
        domains_context = _build_domains_context(watch_domains, canonical_scopes)
        
        # Construire le prompt
        prompt = _build_matching_prompt(normalized_item, domains_context)
        
        # Appeler Bedrock
        response_text = _call_bedrock_matching(prompt, bedrock_model_id, bedrock_region)
        
        # Parser la réponse
        result = _parse_bedrock_matching_response(response_text)
        
        logger.info(f"Matching Bedrock V2 réussi: {len(result.get('matched_domains', []))} domaines matchés")
        return result
        
    except Exception as e:
        logger.error(f"Erreur matching Bedrock V2: {e}")
        # Fallback: retourner structure vide
        return {
            "matched_domains": [],
            "domain_relevance": {},
            "bedrock_error": str(e)
        }


def _build_domains_context(watch_domains: List[Dict[str, Any]], canonical_scopes: Dict[str, Any]) -> str:
    """Construit le contexte textuel des domaines pour le prompt Bedrock."""
    context_lines = []
    
    for i, domain in enumerate(watch_domains, 1):
        domain_id = domain.get('id', f'domain_{i}')
        domain_type = domain.get('type', 'unknown')
        priority = domain.get('priority', 'medium')
        
        context_lines.append(f"{i}. {domain_id} ({domain_type}, priority: {priority}):")
        
        # Ajouter les entités pertinentes depuis les scopes (limité pour concision)
        entities_added = 0
        
        if domain.get('company_scope') and entities_added < 4:
            companies = canonical_scopes.get('companies', {}).get(domain['company_scope'], [])
            if companies:
                context_lines.append(f"   Key companies: {', '.join(companies[:12])}")
                entities_added += 1
        
        if domain.get('technology_scope') and entities_added < 4:
            tech_scope = canonical_scopes.get('technologies', {}).get(domain['technology_scope'], {})
            tech_keywords = []
            
            if isinstance(tech_scope, dict):
                core_phrases = tech_scope.get('core_phrases', [])
                high_precision = tech_scope.get('technology_terms_high_precision', [])
                tech_keywords = core_phrases[:8] + high_precision[:4]
            elif isinstance(tech_scope, list):
                tech_keywords = tech_scope[:10]
            
            if tech_keywords:
                context_lines.append(f"   Key technologies: {', '.join(tech_keywords)}")
                entities_added += 1
        
        if domain.get('molecule_scope') and entities_added < 4:
            molecules = canonical_scopes.get('molecules', {}).get(domain['molecule_scope'], [])
            if molecules:
                context_lines.append(f"   Key molecules: {', '.join(molecules[:8])}")
                entities_added += 1
        
        if domain.get('trademark_scope') and entities_added < 4:
            trademarks = canonical_scopes.get('trademarks', {}).get(domain['trademark_scope'], [])
            if trademarks:
                context_lines.append(f"   Key trademarks: {', '.join(trademarks[:6])}")
                entities_added += 1
        
        context_lines.append("")  # Ligne vide entre domaines
    
    return "\n".join(context_lines)


def _build_matching_prompt(normalized_item: Dict[str, Any], domains_context: str) -> str:
    """Construit le prompt pour l'appel Bedrock de matching."""
    entities_str = json.dumps(normalized_item.get('entities', {}), indent=2)
    
    prompt = f"""You are a domain relevance expert for biotech/pharma intelligence.
Evaluate how relevant a normalized news item is to specific watch domains.

Evaluate the relevance of this normalized item to the configured watch domains:

ITEM TO EVALUATE:
Title: {normalized_item.get('title', '')}
Summary: {normalized_item.get('summary', '')}
Entities: {entities_str}
Event Type: {normalized_item.get('event_type', 'other')}

WATCH DOMAINS TO EVALUATE:
{domains_context}

For each domain, evaluate:
1. Is this item relevant to the domain's focus area?
2. What is the relevance score (0.0 to 1.0)?
3. What is your confidence level (high/medium/low)?
4. Which entities contributed to the match?
5. Brief reasoning for the evaluation

EVALUATION CRITERIA:
- Consider semantic context, not just keyword presence
- Technology domains require clear technology signals
- Regulatory domains focus on approvals, submissions, compliance
- Company relevance should match the domain's scope
- Be conservative: prefer false negatives over false positives

RESPONSE FORMAT (JSON only):
{{
  "domain_evaluations": [
    {{
      "domain_id": "...",
      "is_relevant": true/false,
      "relevance_score": 0.0-1.0,
      "confidence": "high/medium/low",
      "reasoning": "Brief explanation (max 2 sentences)",
      "matched_entities": {{
        "companies": [...],
        "molecules": [...],
        "technologies": [...],
        "trademarks": [...]
      }}
    }}
  ]
}}

Respond with ONLY the JSON, no additional text."""

    logger.debug("Prompt hardcodé utilisé pour matching V2 (fallback)")
    return prompt


def _call_bedrock_matching(prompt: str, bedrock_model_id: str, bedrock_region: str) -> str:
    """Appelle Bedrock pour le matching avec retry automatique."""
    # Réutiliser l'infrastructure Bedrock existante de src_v2
    from .bedrock_client import _call_bedrock_with_retry
    
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1500,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1
    }
    
    logger.debug(f"Appel Bedrock matching V2: modèle={bedrock_model_id}")
    return _call_bedrock_with_retry(bedrock_model_id, request_body)


def _parse_bedrock_matching_response(response_text: str) -> Dict[str, Any]:
    """Parse la réponse JSON de Bedrock et convertit au format attendu."""
    try:
        response_data = json.loads(response_text.strip())
        
        if not isinstance(response_data, dict) or 'domain_evaluations' not in response_data:
            raise ValueError("Structure de réponse invalide")
        
        evaluations = response_data['domain_evaluations']
        if not isinstance(evaluations, list):
            raise ValueError("domain_evaluations doit être une liste")
        
        # Convertir au format attendu avec seuils
        matched_domains = []
        domain_relevance = {}
        min_relevance_score = 0.4  # Seuil minimum
        
        for eval_item in evaluations:
            domain_id = eval_item.get('domain_id')
            is_relevant = eval_item.get('is_relevant', False)
            relevance_score = eval_item.get('relevance_score', 0.0)
            
            # Appliquer les seuils
            if domain_id and is_relevant and relevance_score >= min_relevance_score:
                matched_domains.append(domain_id)
                
                domain_relevance[domain_id] = {
                    'score': relevance_score,
                    'confidence': eval_item.get('confidence', 'low'),
                    'reasoning': eval_item.get('reasoning', ''),
                    'matched_entities': eval_item.get('matched_entities', {})
                }
            elif domain_id:
                # Stocker aussi les évaluations non-pertinentes pour debug
                domain_relevance[domain_id] = {
                    'score': relevance_score,
                    'confidence': eval_item.get('confidence', 'low'),
                    'reasoning': eval_item.get('reasoning', ''),
                    'matched_entities': eval_item.get('matched_entities', {}),
                    'rejected_reason': f"Score {relevance_score} < seuil {min_relevance_score}" if relevance_score < min_relevance_score else "Marqué non pertinent"
                }
        
        logger.info(f"Matching Bedrock V2: {len(matched_domains)} domaines matchés sur {len(evaluations)} évalués")
        
        return {
            "matched_domains": matched_domains,
            "domain_relevance": domain_relevance
        }
        
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"Erreur parsing réponse Bedrock V2: {e}")
        return {
            "matched_domains": [],
            "domain_relevance": {}
        }