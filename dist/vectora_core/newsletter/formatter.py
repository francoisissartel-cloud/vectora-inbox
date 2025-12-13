"""
Module formatter - Assemblage du Markdown final.

Ce module assemble le contenu éditorial généré par Bedrock
en un document Markdown structuré.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def assemble_markdown(
    editorial_content: Dict[str, Any],
    sections_data: List[Dict[str, Any]],
    client_profile: Dict[str, Any],
    newsletter_delivery: Dict[str, Any]
) -> str:
    """
    Assemble le Markdown final de la newsletter.
    
    Args:
        editorial_content: Contenu éditorial généré par Bedrock
        sections_data: Sections avec items sélectionnés
        client_profile: Profil du client
        newsletter_delivery: Configuration de livraison
    
    Returns:
        Newsletter complète en Markdown
    """
    logger.info("Assemblage du Markdown final")
    
    markdown_parts = []
    
    # Titre
    title = editorial_content.get('title', 'Newsletter')
    markdown_parts.append(f"# {title}\n\n")
    
    # Introduction
    intro = editorial_content.get('intro', '')
    if intro:
        markdown_parts.append(f"{intro}\n\n")
    
    # TL;DR
    include_tldr = newsletter_delivery.get('include_tldr', True)
    tldr = editorial_content.get('tldr', [])
    if include_tldr and tldr:
        markdown_parts.append("## TL;DR\n\n")
        for bullet in tldr:
            markdown_parts.append(f"- {bullet}\n")
        markdown_parts.append("\n---\n\n")
    
    # Sections
    sections = editorial_content.get('sections', [])
    for section in sections:
        section_title = section.get('section_title', 'Section')
        section_intro = section.get('section_intro', '')
        items = section.get('items', [])
        
        markdown_parts.append(f"## {section_title}\n\n")
        
        if section_intro:
            markdown_parts.append(f"{section_intro}\n\n")
        
        for item in items:
            item_title = item.get('title', 'Untitled')
            rewritten_summary = item.get('rewritten_summary', '')
            url = item.get('url', '#')
            
            markdown_parts.append(f"**{item_title}**  \n")
            if rewritten_summary:
                markdown_parts.append(f"{rewritten_summary}  \n")
            markdown_parts.append(f"[Read more]({url})\n\n")
        
        markdown_parts.append("---\n\n")
    
    # Footer
    markdown_parts.append("*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*\n")
    
    newsletter_md = "".join(markdown_parts)
    
    logger.info(f"Markdown assemblé : {len(newsletter_md)} caractères")
    
    return newsletter_md
