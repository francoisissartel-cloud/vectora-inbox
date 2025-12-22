"""
Module assembler - Assemblage des formats de sortie Markdown et JSON
Implémente les structures définies dans le plan Phase 3
"""
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def assemble_newsletter(selected_items, editorial_content, client_config, target_date):
    """
    Assemble la newsletter finale aux formats Markdown et JSON
    
    Args:
        selected_items: Items sélectionnés par section
        editorial_content: Contenu éditorial généré par Bedrock
        client_config: Configuration client
        target_date: Date cible de la newsletter
    
    Returns:
        dict: Newsletter aux formats Markdown et JSON avec métadonnées
    """
    logger.info("Assembling newsletter formats")
    
    # Génération du contenu Markdown
    markdown_content = _generate_markdown(selected_items, editorial_content, client_config, target_date)
    
    # Génération des métadonnées JSON
    json_metadata = _generate_json_metadata(selected_items, editorial_content, client_config, target_date)
    
    # Génération du manifest
    manifest = _generate_manifest(selected_items, target_date)
    
    return {
        "markdown": markdown_content,
        "json": json_metadata,
        "manifest": manifest
    }

def _generate_markdown(selected_items, editorial_content, client_config, target_date):
    """Génère le contenu Markdown de la newsletter"""
    
    # Header
    week_start = target_date  # Simplification pour MVP
    total_items = sum(len(section['items']) for section in selected_items.values())
    sections_count = len([s for s in selected_items.values() if s['items']])
    
    markdown = f"""# LAI Weekly Newsletter - Week of {week_start}

**Generated:** {datetime.now().strftime('%B %d, %Y')} | **Items:** {total_items} signals | **Coverage:** {sections_count} sections

## 🎯 TL;DR
{editorial_content.get('tldr', 'TL;DR content will be generated here.')}

## 📰 Introduction
{editorial_content.get('introduction', 'Introduction content will be generated here.')}

---

"""
    
    # Sections
    section_icons = {
        'top_signals': '🔥',
        'partnerships_deals': '🤝',
        'regulatory_updates': '📋',
        'clinical_updates': '🧬'
    }
    
    for section_id, section_data in selected_items.items():
        if not section_data['items']:
            continue
            
        icon = section_icons.get(section_id, '📊')
        title = section_data['title']
        items_count = len(section_data['items'])
        
        # Déterminer le tri pour l'affichage
        sort_info = _get_sort_info(section_id, client_config)
        
        markdown += f"""## {icon} {title}
*{items_count} items • {sort_info}*

"""
        
        # Items de la section
        for item in section_data['items']:
            item_markdown = _format_item_markdown(item)
            markdown += item_markdown + "\n---\n\n"
    
    # Footer avec métriques
    metrics = _calculate_metrics(selected_items)
    markdown += f"""## 📊 Newsletter Metrics
- **Total Signals:** {metrics['total_items']} items processed
- **Sources:** {metrics['unique_sources']} unique sources
- **Key Players:** {', '.join(metrics['key_companies'][:5])}
- **Technologies:** {', '.join(metrics['key_technologies'][:3])}
- **Generated:** {datetime.now().isoformat()}Z
"""
    
    return markdown

def _format_item_markdown(item):
    """Formate un item individuel en Markdown"""
    normalized = item.get('normalized_content', {})
    entities = normalized.get('entities', {})
    
    title = normalized.get('summary', 'Untitled')[:100]
    
    # ROLLBACK: Utiliser UNIQUEMENT final_score (pas de score effectif)
    score = item.get('scoring_results', {}).get('final_score', 0)
    
    source_key = item.get('source_key', 'Unknown Source')
    published_date = item.get('published_at', '')[:10]
    url = item.get('url', '#')
    
    # Extraction des entités clés
    companies = entities.get('companies', [])[:3]
    technologies = entities.get('technologies', [])[:2]
    
    # Formatage de la date
    try:
        date_obj = datetime.strptime(published_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%b %d, %Y')
    except:
        formatted_date = published_date
    
    markdown = f"""### {_get_item_icon(item)} {title}
**Source:** {source_key} • **Score:** {score:.1f} • **Date:** {formatted_date}

{normalized.get('summary', 'No summary available.')}

**Key Players:** {', '.join(companies)} • **Technology:** {', '.join(technologies)}

[**Read more →**]({url})

"""
    
    return markdown

def _get_item_icon(item):
    """Retourne l'icône appropriée pour un item selon son type"""
    event_type = item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', '')
    
    icons = {
        'partnership': '🤝',
        'clinical_update': '🧬',
        'regulatory': '📋',
        'corporate_move': '🏢',
        'financial_results': '💰',
        'scientific_publication': '📄'
    }
    
    return icons.get(event_type, '📊')

def _get_sort_info(section_id, client_config):
    """Retourne l'information de tri pour une section"""
    sections = client_config.get('newsletter_layout', {}).get('sections', [])
    
    for section in sections:
        if section.get('id') == section_id:
            sort_by = section.get('sort_by', 'score_desc')
            if sort_by == 'score_desc':
                return 'Sorted by score'
            elif sort_by == 'date_desc':
                return 'Sorted by date'
    
    return 'Sorted by relevance'

def _generate_json_metadata(selected_items, editorial_content, client_config, target_date):
    """Génère les métadonnées JSON de la newsletter"""
    
    client_id = client_config.get('client_profile', {}).get('client_id', 'unknown')
    
    # Calcul des métriques
    metrics = _calculate_metrics(selected_items)
    
    # Construction des sections JSON
    sections_json = []
    for section_id, section_data in selected_items.items():
        if not section_data['items']:
            continue
            
        section_json = {
            "section_id": section_id,
            "title": section_data['title'],
            "items": []
        }
        
        for item in section_data['items']:
            item_json = _format_item_json(item)
            section_json['items'].append(item_json)
        
        sections_json.append(section_json)
    
    json_metadata = {
        "newsletter_id": f"{client_id}_{target_date.replace('-', '_')}",
        "client_id": client_id,
        "generated_at": datetime.now().isoformat() + "Z",
        "period": {
            "start_date": target_date,
            "end_date": target_date
        },
        "metrics": {
            "total_items": metrics['total_items'],
            "items_by_section": {
                section_id: len(section_data['items']) 
                for section_id, section_data in selected_items.items()
            },
            "unique_sources": metrics['unique_sources'],
            "key_entities": {
                "companies": metrics['key_companies'][:10],
                "technologies": metrics['key_technologies'][:5],
                "trademarks": metrics['key_trademarks'][:5]
            }
        },
        "sections": sections_json,
        "bedrock_calls": editorial_content.get('bedrock_calls', {})
    }
    
    return json_metadata

def _format_item_json(item):
    """Formate un item pour le JSON"""
    normalized = item.get('normalized_content', {})
    entities = normalized.get('entities', {})
    
    # ROLLBACK: Utiliser UNIQUEMENT final_score (pas de score effectif)
    score = item.get('scoring_results', {}).get('final_score', 0)
    
    return {
        "item_id": item.get('item_id', ''),
        "title": normalized.get('summary', '')[:100],
        "score": score,
        "published_at": item.get('published_at', ''),
        "source_url": item.get('url', ''),
        "entities": {
            "companies": entities.get('companies', []),
            "technologies": entities.get('technologies', []),
            "trademarks": entities.get('trademarks', [])
        }
    }

def _calculate_metrics(selected_items):
    """Calcule les métriques de la newsletter"""
    all_items = []
    for section_data in selected_items.values():
        all_items.extend(section_data['items'])
    
    # Extraction des entités
    all_companies = []
    all_technologies = []
    all_trademarks = []
    all_sources = []
    
    for item in all_items:
        entities = item.get('normalized_content', {}).get('entities', {})
        all_companies.extend(entities.get('companies', []))
        all_technologies.extend(entities.get('technologies', []))
        all_trademarks.extend(entities.get('trademarks', []))
        all_sources.append(item.get('source_key', ''))
    
    # Décompte unique
    unique_companies = list(set(all_companies))
    unique_technologies = list(set(all_technologies))
    unique_trademarks = list(set(all_trademarks))
    unique_sources = len(set(all_sources))
    
    return {
        'total_items': len(all_items),
        'unique_sources': unique_sources,
        'key_companies': unique_companies,
        'key_technologies': unique_technologies,
        'key_trademarks': unique_trademarks
    }

def _generate_manifest(selected_items, target_date):
    """Génère le manifest de livraison"""
    total_items = sum(len(section['items']) for section in selected_items.values())
    
    return {
        "generation_date": datetime.now().isoformat() + "Z",
        "target_date": target_date,
        "status": "completed",
        "total_items": total_items,
        "files": {
            "newsletter.md": "Newsletter Markdown content",
            "newsletter.json": "Newsletter JSON metadata",
            "manifest.json": "Delivery manifest"
        }
    }