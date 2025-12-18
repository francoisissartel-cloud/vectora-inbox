"""
Module de matching Bedrock pour Vectora Inbox.

Ce module fournit une fonction pure pour évaluer la pertinence d'items normalisés
par rapport aux watch_domains configurés via un appel Bedrock dédié.

Respecte strictement les règles src_lambda_hygiene_v4.md :
- Fonction pure sans état
- Pas de logique métier hardcodée
- Pilotage par configuration (client_config + canonical)
- Gestion d'erreurs avec fallback
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
        bedrock_region: Région Bedrock (défaut: us-east-1)
    
    Returns:
        {
            "matched_domains": ["tech_lai_ecosystem"],
            "domain_relevance": {
                "tech_lai_ecosystem": {
                    "score": 0.85,
                    "confidence": "high",
                    "reasoning": "...",
                    "matched_entities": {...}
                }
            }
        }
    
    Raises:
        Exception: En cas d'erreur Bedrock non récupérable
    """
    logger.info(f"Matching Bedrock pour item: {normalized_item.get('title', '')[:50]}...")
    
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
        
        logger.info(f"Matching Bedrock réussi: {len(result.get('matched_domains', []))} domaines matchés")
        return result
        
    except Exception as e:
        logger.error(f"Erreur matching Bedrock: {e}")
        logger.debug(f"Détails erreur matching Bedrock", exc_info=True)
        # Fallback: retourner structure vide (matching déterministe prendra le relais)
        return {
            "matched_domains": [],
            "domain_relevance": {},
            "bedrock_error": str(e)  # Pour debugging
        }


def _build_domains_context(watch_domains: List[Dict[str, Any]], canonical_scopes: Dict[str, Any]) -> str:
    """
    Construit le contexte textuel des domaines pour le prompt Bedrock.
    Optimisé pour être concis et informatif.
    
    Args:
        watch_domains: Domaines de veille configurés
        canonical_scopes: Scopes canonical
    
    Returns:
        Contexte formaté pour le prompt
    """
    context_lines = []
    
    for i, domain in enumerate(watch_domains, 1):
        domain_id = domain.get('id', f'domain_{i}')
        domain_type = domain.get('type', 'unknown')
        priority = domain.get('priority', 'medium')
        
        context_lines.append(f"{i}. {domain_id} ({domain_type}, priority: {priority}):")
        
        # Ajouter une description si disponible
        if domain.get('description'):
            context_lines.append(f"   Description: {domain['description']}")
        
        # Ajouter les entités pertinentes depuis les scopes (limitées pour éviter surcharge)
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
                # Prioriser core_phrases puis technology_terms_high_precision
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
    """
    Construit le prompt pour l'appel Bedrock de matching.
    Utilise le prompt canonicalisé si disponible, sinon fallback hardcodé.
    
    Args:
        normalized_item: Item normalisé
        domains_context: Contexte des domaines
    
    Returns:
        Prompt formaté
    """
    # Essayer d'utiliser le prompt canonicalisé
    try:
        from vectora_core.prompts import get_prompt_loader
        
        loader = get_prompt_loader()
        prompt_config = loader.get_prompt('matching.matching_watch_domains_v2')
        
        if prompt_config:
            # Utiliser le prompt canonicalisé
            system_instructions = prompt_config.get('system_instructions', '')
            user_template = prompt_config.get('user_template', '')
            
            # Substituer les placeholders
            entities_str = json.dumps(normalized_item.get('entities', {}), indent=2)
            
            user_prompt = user_template.replace('{{item_title}}', normalized_item.get('title', ''))
            user_prompt = user_prompt.replace('{{item_summary}}', normalized_item.get('summary', ''))
            user_prompt = user_prompt.replace('{{item_entities}}', entities_str)
            user_prompt = user_prompt.replace('{{item_event_type}}', normalized_item.get('event_type', 'other'))
            user_prompt = user_prompt.replace('{{domains_context}}', domains_context)
            
            # Combiner system + user
            full_prompt = f"{system_instructions}\n\n{user_prompt}"
            logger.debug("Prompt canonicalisé utilisé pour matching")
            return full_prompt
            
    except Exception as e:
        logger.warning(f"Erreur chargement prompt canonicalisé: {e}, utilisation fallback")
    
    # Fallback: prompt hardcodé
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

RESPONSE FORMAT (JSON only):
{{
  "domain_evaluations": [
    {{
      "domain_id": "...",
      "is_relevant": true/false,
      "relevance_score": 0.0-1.0,
      "confidence": "high/medium/low",
      "reasoning": "...",
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

    logger.debug("Prompt hardcodé utilisé pour matching (fallback)")
    return prompt


def _call_bedrock_matching(prompt: str, bedrock_model_id: str, bedrock_region: str) -> str:
    """
    Appelle Bedrock pour le matching avec retry automatique.
    Réutilise l'infrastructure existante pour la cohérence.
    
    Args:
        prompt: Prompt formaté
        bedrock_model_id: Modèle à utiliser
        bedrock_region: Région Bedrock
    
    Returns:
        Réponse texte de Bedrock
    """
    # Réutiliser l'infrastructure Bedrock existante
    from vectora_core.normalization.bedrock_client import _call_bedrock_with_retry
    
    # Configuration optimisée pour le matching
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1500,  # Suffisant pour réponse JSON structurée
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1  # Faible pour cohérence
    }
    
    logger.debug(f"Appel Bedrock matching: modèle={bedrock_model_id}, région={bedrock_region}")
    logger.debug(f"Taille prompt: {len(prompt)} caractères")
    
    return _call_bedrock_with_retry(bedrock_model_id, request_body)


def _parse_bedrock_matching_response(response_text: str) -> Dict[str, Any]:
    """
    Parse la réponse JSON de Bedrock et convertit au format attendu.
    Applique des seuils de pertinence configurables.
    
    Args:
        response_text: Réponse brute de Bedrock
    
    Returns:
        {
            "matched_domains": [...],
            "domain_relevance": {...}
        }
    """
    try:
        # Parser le JSON
        response_data = json.loads(response_text.strip())
        
        # Valider la structure
        if not isinstance(response_data, dict) or 'domain_evaluations' not in response_data:
            raise ValueError("Structure de réponse invalide")
        
        evaluations = response_data['domain_evaluations']
        if not isinstance(evaluations, list):
            raise ValueError("domain_evaluations doit être une liste")
        
        # Convertir au format attendu avec seuils
        matched_domains = []
        domain_relevance = {}
        
        # Seuil minimum de pertinence (configurable)
        min_relevance_score = 0.4  # TODO: Rendre configurable via client_config
        
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
        
        logger.info(f"Matching Bedrock: {len(matched_domains)} domaines matchés sur {len(evaluations)} évalués")
        
        return {
            "matched_domains": matched_domains,
            "domain_relevance": domain_relevance
        }
        
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.warning(f"Erreur parsing réponse Bedrock: {e}")
        logger.debug(f"Réponse brute: {response_text[:500]}...")
        # Fallback: structure vide
        return {
            "matched_domains": [],
            "domain_relevance": {}
        }