"""
Module de matching Bedrock pour normalize_score V2.

Évalue la pertinence d'items normalisés par rapport aux watch_domains via Bedrock.
Respecte l'architecture src_v2 et les règles hygiene_v4.
"""

import json
import logging
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def match_watch_domains_with_bedrock(
    normalized_item: Dict[str, Any],
    watch_domains: List[Dict[str, Any]], 
    canonical_scopes: Dict[str, Any],
    matching_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Évalue la pertinence d'un item normalisé par rapport aux watch_domains via Bedrock.
    ALIGNÉ sur la même configuration Bedrock que la normalisation.
    
    Args:
        normalized_item: Item avec title, summary, entities, event_type
        watch_domains: Liste des domaines de veille configurés
        canonical_scopes: Scopes canonical chargés
    
    Returns:
        {
            "matched_domains": ["tech_lai_ecosystem"],
            "domain_relevance": {...}
        }
    
    Note:
        Utilise les mêmes variables d'environnement que la normalisation :
        - BEDROCK_MODEL_ID
        - BEDROCK_REGION (défaut: us-east-1)
    """
    logger.info(f"Matching Bedrock V2 pour item: {normalized_item.get('title', '')[:50]}...")
    
    try:
        # Lecture des variables d'environnement (ALIGNÉ sur normalisation)
        bedrock_model_id = os.environ.get('BEDROCK_MODEL_ID')
        bedrock_region = os.environ.get('BEDROCK_REGION', 'us-east-1')
        
        if not bedrock_model_id:
            logger.error("Variable BEDROCK_MODEL_ID non définie")
            return {"matched_domains": [], "domain_relevance": {}, "config_error": "BEDROCK_MODEL_ID manquant"}
        
        logger.debug(f"Config Bedrock matching alignée: modèle={bedrock_model_id}, région={bedrock_region}")
        
        # Validation des inputs
        if not watch_domains:
            logger.debug("Aucun watch_domain configuré, retour structure vide")
            return {"matched_domains": [], "domain_relevance": {}}
        
        # Construire le contexte des domaines
        domains_context = _build_domains_context(watch_domains, canonical_scopes)
        
        # Construire le prompt
        prompt = _build_matching_prompt(normalized_item, domains_context)
        
        # Appeler Bedrock avec la même config que normalisation
        response_text = _call_bedrock_matching(prompt, bedrock_model_id, bedrock_region)
        
        # Parser la réponse avec configuration
        result = _parse_bedrock_matching_response(response_text, matching_config, watch_domains)
        
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
    from .bedrock_client import call_bedrock_with_retry
    
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
    return call_bedrock_with_retry(bedrock_model_id, request_body)


def _parse_bedrock_matching_response(
    response_text: str, 
    matching_config: Dict[str, Any] = None,
    watch_domains: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Parse la réponse JSON de Bedrock et convertit au format attendu."""
    try:
        response_data = json.loads(response_text.strip())
        
        if not isinstance(response_data, dict) or 'domain_evaluations' not in response_data:
            raise ValueError("Structure de réponse invalide")
        
        evaluations = response_data['domain_evaluations']
        if not isinstance(evaluations, list):
            raise ValueError("domain_evaluations doit être une liste")
        
        # Appliquer la politique de matching configurée
        result = _apply_matching_policy(evaluations, matching_config, watch_domains)
        matched_domains = result['matched_domains']
        domain_relevance = result['domain_relevance']
        
        # Appliquer mode fallback si configuré et aucun domaine matché
        if not matched_domains and matching_config and matching_config.get('enable_fallback_mode', False):
            fallback_result = _apply_fallback_matching(evaluations, matching_config, watch_domains)
            if fallback_result['matched_domains']:
                matched_domains = fallback_result['matched_domains']
                domain_relevance.update(fallback_result['domain_relevance'])
                logger.info(f"Mode fallback activé: {len(matched_domains)} domaines récupérés")
        
        logger.info(f"Matching Bedrock V2: {len(matched_domains)} domaines matchés sur {len(evaluations)} évalués")
        
        # Ajouter informations de diagnostic si configuré
        result = {
            "matched_domains": matched_domains,
            "domain_relevance": domain_relevance
        }
        
        if matching_config and matching_config.get('enable_diagnostic_mode', False):
            result['diagnostic_info'] = {
                'config_applied': {
                    'min_domain_score': matching_config.get('min_domain_score', 0.4),
                    'domain_type_thresholds': matching_config.get('domain_type_thresholds', {}),
                    'enable_fallback_mode': matching_config.get('enable_fallback_mode', False)
                },
                'evaluations_count': len(evaluations),
                'matched_count': len(matched_domains)
            }
        
        return result
        
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"Erreur parsing réponse Bedrock V2: {e}")
        return {
            "matched_domains": [],
            "domain_relevance": {}
        }


def _apply_matching_policy(
    evaluations: List[Dict[str, Any]], 
    matching_config: Dict[str, Any], 
    watch_domains: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Applique la politique de matching configurée aux évaluations Bedrock.
    
    Args:
        evaluations: Liste des évaluations Bedrock
        matching_config: Configuration de matching depuis client_config
        watch_domains: Domaines de veille configurés
    
    Returns:
        {
            "matched_domains": ["tech_lai_ecosystem"],
            "domain_relevance": {...}
        }
    """
    if not matching_config:
        matching_config = {}
    
    # Lecture des seuils avec fallback sur défauts
    min_domain_score = matching_config.get('min_domain_score', 0.4)
    domain_type_thresholds = matching_config.get('domain_type_thresholds', {})
    max_domains_per_item = matching_config.get('max_domains_per_item', 3)
    
    matched_domains = []
    domain_relevance = {}
    
    # Créer un mapping domain_id -> type pour lookup rapide
    domain_types = {}
    for domain in watch_domains or []:
        domain_types[domain.get('id')] = domain.get('type', 'technology')
    
    # Évaluer chaque domaine
    for eval_item in evaluations:
        domain_id = eval_item.get('domain_id')
        is_relevant = eval_item.get('is_relevant', False)
        relevance_score = eval_item.get('relevance_score', 0.0)
        
        if not domain_id:
            continue
        
        # Déterminer le seuil à appliquer
        domain_type = domain_types.get(domain_id, 'technology')
        threshold = domain_type_thresholds.get(domain_type, min_domain_score)
        
        # Décision de matching
        decision = "rejected"
        reason = ""
        
        if not is_relevant:
            reason = "Marqué non pertinent par Bedrock"
        elif relevance_score < threshold:
            reason = f"Score {relevance_score:.3f} < seuil {domain_type} {threshold}"
        else:
            decision = "matched"
            reason = f"Score {relevance_score:.3f} > seuil {domain_type} {threshold}"
            matched_domains.append(domain_id)
        
        # Stocker les détails de l'évaluation
        domain_relevance[domain_id] = {
            'score': relevance_score,
            'threshold': threshold,
            'threshold_source': f"domain_type_thresholds.{domain_type}" if domain_type in domain_type_thresholds else "min_domain_score",
            'decision': decision,
            'confidence': eval_item.get('confidence', 'low'),
            'reasoning': eval_item.get('reasoning', ''),
            'matched_entities': eval_item.get('matched_entities', {}),
            'policy_reason': reason
        }
    
    # Limiter le nombre de domaines matchés si configuré
    if len(matched_domains) > max_domains_per_item:
        # Garder les meilleurs scores
        scored_domains = [(d, domain_relevance[d]['score']) for d in matched_domains]
        scored_domains.sort(key=lambda x: x[1], reverse=True)
        matched_domains = [d for d, _ in scored_domains[:max_domains_per_item]]
        
        logger.info(f"Limitation à {max_domains_per_item} domaines: {matched_domains}")
    
    return {
        "matched_domains": matched_domains,
        "domain_relevance": domain_relevance
    }


def _apply_fallback_matching(
    evaluations: List[Dict[str, Any]], 
    matching_config: Dict[str, Any], 
    watch_domains: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Applique le mode fallback pour récupérer des domaines avec seuils très bas.
    Utilisé pour les pure players sans signaux tech explicites.
    
    Args:
        evaluations: Liste des évaluations Bedrock
        matching_config: Configuration de matching
        watch_domains: Domaines de veille
    
    Returns:
        {
            "matched_domains": ["tech_lai_ecosystem"],
            "domain_relevance": {...}
        }
    """
    fallback_min_score = matching_config.get('fallback_min_score', 0.15)
    fallback_max_domains = matching_config.get('fallback_max_domains', 1)
    
    # Trouver les candidats au-dessus du seuil fallback
    candidates = []
    for eval_item in evaluations:
        domain_id = eval_item.get('domain_id')
        relevance_score = eval_item.get('relevance_score', 0.0)
        
        if domain_id and relevance_score >= fallback_min_score:
            candidates.append((domain_id, relevance_score, eval_item))
    
    # Trier par score décroissant et prendre les meilleurs
    candidates.sort(key=lambda x: x[1], reverse=True)
    
    matched_domains = []
    domain_relevance = {}
    
    for domain_id, score, eval_item in candidates[:fallback_max_domains]:
        matched_domains.append(domain_id)
        
        domain_relevance[domain_id] = {
            'score': score,
            'threshold': fallback_min_score,
            'threshold_source': 'fallback_min_score',
            'decision': 'matched_fallback',
            'confidence': eval_item.get('confidence', 'low'),
            'reasoning': eval_item.get('reasoning', ''),
            'matched_entities': eval_item.get('matched_entities', {}),
            'policy_reason': f"Mode fallback: score {score:.3f} > seuil fallback {fallback_min_score}"
        }
    
    return {
        "matched_domains": matched_domains,
        "domain_relevance": domain_relevance
    }