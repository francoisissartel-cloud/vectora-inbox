"""
Module assembler - Génération de la newsletter finale.

Ce module orchestre la génération de la newsletter :
- Sélection des top N items par section
- Appel à Bedrock pour générer les textes éditoriaux
- Assemblage du Markdown final
"""

import logging
from typing import Any, Dict, List, Tuple

from vectora_core.newsletter import bedrock_client, formatter
from vectora_core.scoring import scorer

logger = logging.getLogger(__name__)


def generate_newsletter(
    scored_items: List[Dict[str, Any]],
    client_config: Dict[str, Any],
    bedrock_model_id: str,
    target_date: str,
    from_date: str,
    to_date: str
) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
    """
    Génère la newsletter complète.
    
    Args:
        scored_items: Items avec scores
        client_config: Configuration du client
        bedrock_model_id: ID du modèle Bedrock
        target_date: Date de référence
        from_date: Date de début de la période
        to_date: Date de fin de la période
    
    Returns:
        Tuple (newsletter_markdown, stats, editorial_content)
    """
    logger.info("Démarrage de la génération de newsletter")
    
    # Extraire la configuration de la newsletter
    newsletter_layout = client_config.get('newsletter_layout', {})
    sections_config = newsletter_layout.get('sections', [])
    client_profile = client_config.get('client_profile', {})
    newsletter_delivery = client_config.get('newsletter_delivery', {})
    
    # Sélectionner les items par section
    logger.info("Sélection des items par section")
    sections_data = _select_items_by_section(scored_items, sections_config)
    
    # Compter le nombre total d'items sélectionnés
    total_selected = sum(len(section['items']) for section in sections_data)
    logger.info(f"Total items sélectionnés : {total_selected}")
    
    if total_selected == 0:
        logger.warning("Aucun item sélectionné pour la newsletter")
        # Générer une newsletter minimale
        newsletter_md = _generate_minimal_newsletter(client_profile, target_date)
        return newsletter_md, {'items_selected': 0, 'sections_generated': 0}, {}
    
    # Générer les textes éditoriaux avec Bedrock
    logger.info("Génération des textes éditoriaux avec Bedrock")
    editorial_content = bedrock_client.generate_editorial_content(
        sections_data,
        client_profile,
        bedrock_model_id,
        target_date,
        from_date,
        to_date,
        len(scored_items)
    )
    
    # Assembler le Markdown final
    logger.info("Assemblage du Markdown final")
    newsletter_md = formatter.assemble_markdown(
        editorial_content,
        sections_data,
        client_profile,
        newsletter_delivery
    )
    
    stats = {
        'items_selected': total_selected,
        'sections_generated': len(sections_data)
    }
    
    logger.info(f"Newsletter générée : {len(newsletter_md)} caractères")
    
    return newsletter_md, stats, editorial_content


def _select_items_by_section(
    scored_items: List[Dict[str, Any]],
    sections_config: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Sélectionne les top N items pour chaque section.
    
    Args:
        scored_items: Items avec scores
        sections_config: Configuration des sections
    
    Returns:
        Liste de sections avec leurs items sélectionnés
    """
    sections_data = []
    
    for section_config in sections_config:
        section_id = section_config.get('id')
        section_title = section_config.get('title')
        source_domains = section_config.get('source_domains', [])
        max_items = section_config.get('max_items', 5)
        filter_event_types = section_config.get('filter_event_types')
        
        # Filtrer les items pour cette section
        section_items = []
        for item in scored_items:
            # Vérifier si l'item appartient à un des source_domains
            matched_domains = item.get('matched_domains', [])
            if any(domain in source_domains for domain in matched_domains):
                # Appliquer le filtre event_type si présent
                if filter_event_types:
                    if item.get('event_type') in filter_event_types:
                        section_items.append(item)
                else:
                    section_items.append(item)
        
        # Trier par score et prendre les top N
        section_items = scorer.rank_items_by_score(section_items)
        section_items = section_items[:max_items]
        
        sections_data.append({
            'id': section_id,
            'title': section_title,
            'items': section_items
        })
        
        logger.info(f"Section '{section_title}' : {len(section_items)} items sélectionnés")
    
    return sections_data


def _generate_minimal_newsletter(client_profile: Dict[str, Any], target_date: str) -> str:
    """
    Génère une newsletter minimale quand aucun item n'est sélectionné.
    
    Args:
        client_profile: Profil du client
        target_date: Date de référence
    
    Returns:
        Newsletter Markdown minimale
    """
    client_name = client_profile.get('name', 'Intelligence Newsletter')
    language = client_profile.get('language', 'en')
    
    if language == 'fr':
        title = f"# {client_name} – {target_date}\n\n"
        message = "Aucun signal critique cette semaine. Nous continuons de surveiller vos domaines d'intérêt.\n\n"
    else:
        title = f"# {client_name} – {target_date}\n\n"
        message = "No critical signals this week. We continue to monitor your domains of interest.\n\n"
    
    footer = "---\n\n*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*\n"
    
    return title + message + footer
