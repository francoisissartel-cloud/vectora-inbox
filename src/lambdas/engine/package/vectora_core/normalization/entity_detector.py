"""
Module de détection d'entités par règles déterministes.

Ce module complète la détection Bedrock avec des règles simples basées
sur les scopes canonical (recherche de mots-clés, validation).
"""

import logging
import re
from typing import List, Set

logger = logging.getLogger(__name__)


def detect_entities_by_rules(
    text: str,
    canonical_scopes: dict
) -> dict:
    """
    Détecte des entités dans le texte en utilisant des règles simples.
    
    Recherche par mots-clés dans les scopes canonical.
    Cette détection complète celle de Bedrock.
    
    Args:
        text: Texte à analyser (titre + description)
        canonical_scopes: Scopes canonical chargés
    
    Returns:
        Dictionnaire contenant :
        - companies_detected: set de sociétés détectées
        - molecules_detected: set de molécules détectées
        - technologies_detected: set de technologies détectées
        - indications_detected: set d'indications détectées
    """
    text_lower = text.lower()
    
    result = {
        'companies_detected': set(),
        'molecules_detected': set(),
        'technologies_detected': set(),
        'indications_detected': set()
    }
    
    # Détection des technologies (mots-clés)
    tech_scopes = canonical_scopes.get('technologies', {})
    for scope_key, keywords in tech_scopes.items():
        if isinstance(keywords, list):
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    result['technologies_detected'].add(keyword)
    
    # Détection des indications (mots-clés)
    indication_scopes = canonical_scopes.get('indications', {})
    for scope_key, keywords in indication_scopes.items():
        if isinstance(keywords, list):
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    result['indications_detected'].add(keyword)
    
    # Détection des sociétés (noms exacts, case-insensitive)
    company_scopes = canonical_scopes.get('companies', {})
    for scope_key, companies in company_scopes.items():
        if isinstance(companies, list):
            for company in companies:
                # Recherche du nom de société (mot entier)
                pattern = r'\b' + re.escape(company) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    result['companies_detected'].add(company)
    
    # Détection des molécules (noms exacts, case-insensitive)
    molecule_scopes = canonical_scopes.get('molecules', {})
    for scope_key, molecules in molecule_scopes.items():
        if isinstance(molecules, list):
            for molecule in molecules:
                pattern = r'\b' + re.escape(molecule) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    result['molecules_detected'].add(molecule)
    
    return result


def merge_entity_detections(
    bedrock_result: dict,
    rules_result: dict
) -> dict:
    """
    Fusionne les résultats de détection Bedrock et règles.
    
    Args:
        bedrock_result: Résultat de la détection Bedrock
        rules_result: Résultat de la détection par règles
    
    Returns:
        Dictionnaire fusionné avec toutes les entités détectées
    """
    merged = {
        'companies_detected': set(),
        'molecules_detected': set(),
        'technologies_detected': set(),
        'indications_detected': set()
    }
    
    # Fusionner les sociétés
    merged['companies_detected'].update(bedrock_result.get('companies_detected', []))
    merged['companies_detected'].update(rules_result.get('companies_detected', set()))
    
    # Fusionner les molécules
    merged['molecules_detected'].update(bedrock_result.get('molecules_detected', []))
    merged['molecules_detected'].update(rules_result.get('molecules_detected', set()))
    
    # Fusionner les technologies
    merged['technologies_detected'].update(bedrock_result.get('technologies_detected', []))
    merged['technologies_detected'].update(rules_result.get('technologies_detected', set()))
    
    # Fusionner les indications
    merged['indications_detected'].update(bedrock_result.get('indications_detected', []))
    merged['indications_detected'].update(rules_result.get('indications_detected', set()))
    
    # Convertir les sets en listes triées
    return {
        'companies_detected': sorted(list(merged['companies_detected'])),
        'molecules_detected': sorted(list(merged['molecules_detected'])),
        'technologies_detected': sorted(list(merged['technologies_detected'])),
        'indications_detected': sorted(list(merged['indications_detected']))
    }
