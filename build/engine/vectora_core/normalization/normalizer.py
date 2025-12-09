"""
Module principal de normalisation des items.

Ce module orchestre la normalisation d'un item brut en item structuré,
en combinant :
- Détection par règles (scopes canonical)
- Détection par Bedrock (IA)
- Validation et filtrage
"""

import logging
from typing import Dict, Any, List

from vectora_core.normalization import bedrock_client, entity_detector

logger = logging.getLogger(__name__)


def normalize_item(
    raw_item: Dict[str, Any],
    canonical_scopes: Dict[str, Any],
    bedrock_model_id: str
) -> Dict[str, Any]:
    """
    Normalise un item brut en item structuré.
    
    Processus :
    1. Construire le texte complet (titre + description)
    2. Détecter les entités par règles (scopes canonical)
    3. Appeler Bedrock pour extraction + classification + résumé
    4. Fusionner les résultats Bedrock + règles
    5. Retourner l'item normalisé
    
    Args:
        raw_item: Item brut contenant title, url, raw_text, source_key, etc.
        canonical_scopes: Scopes canonical chargés
        bedrock_model_id: Identifiant du modèle Bedrock
    
    Returns:
        Item normalisé contenant :
        - source_key: identifiant de la source
        - source_type: type de source
        - title: titre de l'item
        - summary: résumé généré par Bedrock
        - url: lien vers l'article original
        - date: date de publication
        - companies_detected: liste de sociétés
        - molecules_detected: liste de molécules
        - technologies_detected: liste de technologies
        - indications_detected: liste d'indications
        - event_type: type d'événement
    """
    logger.debug(f"Normalisation de l'item : {raw_item.get('title', '')[:50]}...")
    
    # Construire le texte complet pour analyse
    full_text = f"{raw_item.get('title', '')} {raw_item.get('raw_text', '')}"
    
    # Étape 1 : Détection par règles
    rules_result = entity_detector.detect_entities_by_rules(full_text, canonical_scopes)
    
    # Étape 2 : Préparer des exemples pour Bedrock depuis les scopes
    canonical_examples = _extract_canonical_examples(canonical_scopes)
    
    # Étape 3 : Appeler Bedrock
    bedrock_result = bedrock_client.normalize_item_with_bedrock(
        full_text,
        bedrock_model_id,
        canonical_examples
    )
    
    # Étape 4 : Fusionner les résultats
    merged_entities = entity_detector.merge_entity_detections(bedrock_result, rules_result)
    
    # Étape 5 : Construire l'item normalisé
    normalized_item = {
        'source_key': raw_item.get('source_key'),
        'source_type': raw_item.get('source_type'),
        'title': raw_item.get('title'),
        'summary': bedrock_result.get('summary', ''),
        'url': raw_item.get('url'),
        'date': raw_item.get('published_at'),
        'companies_detected': merged_entities['companies_detected'],
        'molecules_detected': merged_entities['molecules_detected'],
        'technologies_detected': merged_entities['technologies_detected'],
        'indications_detected': merged_entities['indications_detected'],
        'event_type': bedrock_result.get('event_type', 'other')
    }
    
    return normalized_item


def normalize_items_batch(
    raw_items: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any],
    bedrock_model_id: str
) -> List[Dict[str, Any]]:
    """
    Normalise un lot d'items bruts.
    
    Args:
        raw_items: Liste d'items bruts
        canonical_scopes: Scopes canonical
        bedrock_model_id: Identifiant du modèle Bedrock
    
    Returns:
        Liste d'items normalisés
    """
    logger.info(f"Normalisation de {len(raw_items)} items")
    
    normalized_items = []
    
    for raw_item in raw_items:
        try:
            normalized = normalize_item(raw_item, canonical_scopes, bedrock_model_id)
            normalized_items.append(normalized)
        except Exception as e:
            logger.error(f"Erreur lors de la normalisation de l'item {raw_item.get('title', '')}: {e}")
            # Continuer avec les autres items
    
    logger.info(f"{len(normalized_items)} items normalisés avec succès")
    
    return normalized_items


def _extract_canonical_examples(canonical_scopes: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Extrait des exemples d'entités depuis les scopes canonical pour Bedrock.
    
    Args:
        canonical_scopes: Scopes canonical complets
    
    Returns:
        Dictionnaire d'exemples par type d'entité
    """
    examples = {
        'companies': [],
        'molecules': [],
        'technologies': []
    }
    
    # Extraire des exemples de sociétés (limiter à 30 pour ne pas surcharger le prompt)
    company_scopes = canonical_scopes.get('companies', {})
    for scope_key, companies in company_scopes.items():
        if isinstance(companies, list):
            examples['companies'].extend(companies[:30])
            if len(examples['companies']) >= 30:
                break
    
    # Extraire des exemples de molécules
    molecule_scopes = canonical_scopes.get('molecules', {})
    for scope_key, molecules in molecule_scopes.items():
        if isinstance(molecules, list):
            examples['molecules'].extend(molecules[:30])
            if len(examples['molecules']) >= 30:
                break
    
    # Extraire des exemples de technologies
    tech_scopes = canonical_scopes.get('technologies', {})
    for scope_key, keywords in tech_scopes.items():
        if isinstance(keywords, list):
            examples['technologies'].extend(keywords[:20])
            if len(examples['technologies']) >= 20:
                break
    
    return examples
