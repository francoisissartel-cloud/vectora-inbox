"""
Module assembler - Assemblage des formats de sortie Markdown et JSON
Implémente les structures définies dans le plan Phase 3
"""
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def generate_newsletter_scope(client_config: Dict[str, Any], items_metadata: Dict[str, Any]) -> str:
    """
    Génération automatique du scope métier
    """
    sources_summary = analyze_sources_used(items_metadata)
    temporal_window = get_temporal_window(client_config)
    
    scope_text = f"""
## Périmètre de cette newsletter

**Sources surveillées :**
- Veille corporate LAI : {sources_summary['corporate_count']} sociétés
- Presse sectorielle biotech : {sources_summary['press_count']} sources
- Période analysée : {temporal_window['days']} jours ({temporal_window['from']} - {temporal_window['to']})

**Domaines de veille :**
{format_watch_domains(client_config['watch_domains'])}
"""
    return scope_text


def analyze_sources_used(items_metadata: Dict[str, Any]) -> Dict[str, int]:
    """
    Analyse les sources utilisées dans la newsletter
    """
    corporate_count = 0
    press_count = 0
    
    # Compter les types de sources depuis les métadonnées
    for source_key in items_metadata.get('sources_used', []):
        if 'corporate' in source_key:
            corporate_count += 1
        elif 'press' in source_key:
            press_count += 1
    
    return {
        'corporate_count': corporate_count,
        'press_count': press_count
    }


def get_temporal_window(client_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule la fenêtre temporelle de la newsletter
    """
    from datetime import datetime, timedelta
    
    days = client_config.get('pipeline', {}).get('default_period_days', 30)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return {
        'days': days,
        'from': start_date.strftime('%Y-%m-%d'),
        'to': end_date.strftime('%Y-%m-%d')
    }


def format_watch_domains(watch_domains: List[Dict[str, Any]]) -> str:
    """
    Formate les domaines de veille pour affichage
    """
    if not watch_domains:
        return "- Aucun domaine configuré"
    
    formatted = []
    for domain in watch_domains:
        domain_id = domain.get('id', 'unknown')
        domain_type = domain.get('type', 'unknown')
        formatted.append(f"- {domain_id} ({domain_type})")
    
    return '\n'.join(formatted)


def render_newsletter_sections(distributed_items: Dict[str, Any], newsletter_config: Dict[str, Any]) -> List[str]:
    """
    Rendu uniquement des sections avec contenu
    """
    rendered_sections = []
    
    for section_config in newsletter_config.get('sections', []):
        section_id = section_config.get('id')
        section_data = distributed_items.get(section_id, {})
        items = section_data.get('items', [])
        
        if items:  # Seulement si items présents
            section_content = render_section(section_config, items)
            rendered_sections.append(section_content)
        else:
            logger.info(f"Section {section_id} vide - non incluse dans newsletter")
    
    return rendered_sections


def render_section(section_config: Dict[str, Any], items: List[Dict[str, Any]]) -> str:
    """
    Rendu d'une section individuelle
    """
    title = section_config.get('title', 'Untitled Section')
    section_content = f"## {title}\n\n"
    
    for item in items:
        item_markdown = _format_item_markdown(item)
        section_content += item_markdown + "\n---\n\n"
    
    return section_content


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
    
    # Génération du contenu Markdown avec scope métier
    markdown_content = _generate_markdown_with_scope(selected_items, editorial_content, client_config, target_date)
    
    # Génération des métadonnées JSON
    json_metadata = _generate_json_metadata(selected_items, editorial_content, client_config, target_date)
    
    # Génération du manifest
    manifest = _generate_manifest(selected_items, target_date)
    
    return {
        "markdown": markdown_content,
        "json": json_metadata,
        "manifest": manifest
    }

def _generate_markdown_with_scope(selected_items, editorial_content, client_config, target_date):
    """Génère le contenu Markdown de la newsletter avec scope métier"""
    
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
    
    # Sections (uniquement celles avec contenu)
    section_icons = {
        'regulatory_updates': '📋',
        'partnerships_deals': '🤝',
        'clinical_updates': '🧬',
        'others': '📈'
    }
    
    for section_id, section_data in selected_items.items():
        if not section_data['items']:
            continue  # Ignorer les sections vides
            
        icon = section_icons.get(section_id, '📈')
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
    
    # Scope métier automatique
    items_metadata = _extract_items_metadata(selected_items)
    scope_content = generate_newsletter_scope(client_config, items_metadata)
    markdown += scope_content + "\n\n"
    
    # Footer avec métriques
    metrics = _calculate_metrics(selected_items)
    markdown += f"""## 📈 Newsletter Metrics
- **Total Signals:** {metrics['total_items']} items processed
- **Sources:** {metrics['unique_sources']} unique sources
- **Key Players:** {', '.join(metrics['key_companies'][:5])}
- **Technologies:** {', '.join(metrics['key_technologies'][:3])}
- **Generated:** {datetime.now().isoformat()}Z
"""
    
    return markdown


def _extract_items_metadata(selected_items: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrait les métadonnées des items pour le scope
    """
    all_items = []
    sources_used = set()
    
    for section_data in selected_items.values():
        for item in section_data.get('items', []):
            all_items.append(item)
            sources_used.add(item.get('source_key', ''))
    
    return {
        'total_items': len(all_items),
        'sources_used': list(sources_used)
    }
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

def format_item_title(item, max_length=120):  # Augmenté de 80 à 120
    """Formate titre item pour newsletter avec troncature intelligente"""
    original_title = item.get('title', '')
    
    # Si titre court, garder tel quel
    if len(original_title) <= max_length:
        return original_title
    
    # Utiliser summary Bedrock si plus court et pertinent
    summary = item.get('normalized_content', {}).get('summary', '')
    if summary and len(summary) <= max_length and len(summary) > 20:
        return summary
    
    # Troncature intelligente (phrases complètes)
    sentences = original_title.split('.')
    truncated = sentences[0]
    
    for sentence in sentences[1:]:
        if len(truncated + '.' + sentence) <= max_length - 3:  # -3 pour "..."
            truncated += '.' + sentence
        else:
            break
    
    # Ajouter "..." si tronqué
    if len(truncated) < len(original_title):
        truncated += "..."
    
    return truncated


def _format_item_markdown(item):
    """Formate un item individuel en Markdown"""
    normalized = item.get('normalized_content', {})
    entities = normalized.get('entities', {})
    scoring = item.get('scoring_results', {})
    
    # Utiliser la fonction de formatage améliorée pour le titre
    title = format_item_title(item, max_length=120)
    
    # Utiliser final_score
    score = scoring.get('final_score', 0)
    
    source_key = item.get('source_key', 'Unknown Source')
    
    # NOUVEAU: Utiliser effective_date (date Bedrock) si disponible, sinon published_at
    effective_date = scoring.get('effective_date') or item.get('published_at', '')[:10]
    url = item.get('url', '#')
    
    # Extraction des entités clés
    companies = entities.get('companies', [])[:3]
    technologies = entities.get('technologies', [])[:2]
    
    # Formatage de la date
    try:
        date_obj = datetime.strptime(effective_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%b %d, %Y')
    except:
        formatted_date = effective_date
    
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
    scoring = item.get('scoring_results', {})
    
    # Utiliser final_score
    score = scoring.get('final_score', 0)
    
    # NOUVEAU: Utiliser effective_date (date Bedrock) si disponible
    effective_date = scoring.get('effective_date') or item.get('published_at', '')
    
    return {
        "item_id": item.get('item_id', ''),
        "title": normalized.get('summary', '')[:100],
        "score": score,
        "published_at": effective_date,  # Utiliser effective_date
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