# Stratégie de Sélection & Structuration Newsletter V2

**Date :** 21 décembre 2025  
**Phase :** 4 - Stratégie de sélection & structuration de la newsletter  
**Objectif :** Définir comment assembler la newsletter (choix + sections + génération)  

---

## 🎯 ANALYSE DES CONFIGURATIONS EXISTANTES

### Configuration lai_weekly_v3.yaml (Validée E2E)

#### Client Profile & Editorial
```yaml
client_profile:
  name: "LAI Intelligence Weekly v3 (Test Bench)"
  language: "en"
  tone: "executive"           # Ton professionnel pour dirigeants
  voice: "concise"           # Style concis et direct
  target_audience: "executives"  # Audience cible
```

#### Watch Domains & Mapping Sections
```yaml
watch_domains:
  - id: "tech_lai_ecosystem"     # Domaine principal
    type: "technology"
    priority: "high"
  - id: "regulatory_lai"         # Domaine secondaire
    type: "regulatory"
    priority: "high"

newsletter_layout:
  sections:
    - id: "top_signals"
      source_domains: ["tech_lai_ecosystem", "regulatory_lai"]  # Multi-domaines
      max_items: 5
      sort_by: "score_desc"
    
    - id: "partnerships_deals"
      source_domains: ["tech_lai_ecosystem"]                   # Domaine unique
      max_items: 5
      filter_event_types: ["partnership", "corporate_move"]
      sort_by: "date_desc"
    
    - id: "regulatory_updates"
      source_domains: ["regulatory_lai"]                       # Domaine spécialisé
      max_items: 5
      filter_event_types: ["regulatory"]
      sort_by: "score_desc"
    
    - id: "clinical_updates"
      source_domains: ["tech_lai_ecosystem"]
      max_items: 8
      filter_event_types: ["clinical_update"]
      sort_by: "date_desc"
```

#### Seuils de Sélection
```yaml
scoring_config:
  selection_overrides:
    min_score: 12                    # Seuil minimum pour inclusion
    min_items_per_section: 1         # Au moins 1 item par section
    max_items_total: 15              # Limite globale newsletter
```

### Utilisation Effective des Configurations

#### Mapping Domaines → Sections (Observé)
```
tech_lai_ecosystem → top_signals (5 items) + partnerships_deals (5) + clinical_updates (8) = 18 slots
regulatory_lai → top_signals (5 items) + regulatory_updates (5) = 10 slots
```

**Problème identifié :** Chevauchement possible entre sections (même domaine, critères différents)

#### Priorités et Seuils (Validés E2E)
- **Seuil min_score: 12** → 7 items retenus sur 15 (46.7% sélection)
- **Tri par score** → Items les plus pertinents en premier
- **Limite max_items** → Contrôle de la longueur newsletter

---

## 🔧 STRATÉGIE D'ASSEMBLAGE PROPOSÉE

### Étape 1 : Sélection des Items (Logique Déterministe)

#### Algorithme de Sélection
```python
def select_items_for_newsletter(curated_items, client_config):
    """Sélectionne les items pour la newsletter selon les règles métier."""
    
    # 1. Filtrage global
    selection_config = client_config.get('scoring_config', {}).get('selection_overrides', {})
    min_score = selection_config.get('min_score', 10)
    max_items_total = selection_config.get('max_items_total', 20)
    
    # Filtrer par score minimum
    eligible_items = [
        item for item in curated_items 
        if item.get('scoring_results', {}).get('final_score', 0) >= min_score
    ]
    
    # 2. Déduplication (Phase 3)
    deduplicated_items = deduplicate_items(eligible_items)
    
    # 3. Sélection par section
    newsletter_layout = client_config.get('newsletter_layout', {})
    sections = newsletter_layout.get('sections', [])
    
    selected_items = {}
    used_item_ids = set()
    
    for section in sections:
        section_items = select_items_for_section(
            deduplicated_items, section, used_item_ids
        )
        selected_items[section['id']] = section_items
        used_item_ids.update(item['item_id'] for item in section_items)
    
    # 4. Vérification limites globales
    total_selected = sum(len(items) for items in selected_items.values())
    if total_selected > max_items_total:
        selected_items = apply_global_limits(selected_items, max_items_total)
    
    return selected_items

def select_items_for_section(items, section_config, used_item_ids):
    """Sélectionne les items pour une section spécifique."""
    
    # Filtrage par domaines sources
    source_domains = section_config.get('source_domains', [])
    domain_filtered = [
        item for item in items
        if item['item_id'] not in used_item_ids and
        any(domain in item.get('matching_results', {}).get('matched_domains', []) 
            for domain in source_domains)
    ]
    
    # Filtrage par types d'événements
    event_types = section_config.get('filter_event_types', [])
    if event_types:
        event_filtered = [
            item for item in domain_filtered
            if item.get('normalized_content', {}).get('event_classification', {}).get('primary_type') in event_types
        ]
    else:
        event_filtered = domain_filtered
    
    # Tri selon configuration
    sort_by = section_config.get('sort_by', 'score_desc')
    if sort_by == 'score_desc':
        sorted_items = sorted(event_filtered, 
                            key=lambda x: x.get('scoring_results', {}).get('final_score', 0), 
                            reverse=True)
    elif sort_by == 'date_desc':
        sorted_items = sorted(event_filtered,
                            key=lambda x: x.get('published_at', ''),
                            reverse=True)
    else:
        sorted_items = event_filtered
    
    # Limitation du nombre d'items
    max_items = section_config.get('max_items', 5)
    return sorted_items[:max_items]
```

### Étape 2 : Génération Éditoriale (Bedrock)

#### Rôle de Bedrock dans la Newsletter

**✅ Bedrock DOIT faire :**
1. **Génération TL;DR** : Résumé exécutif des signaux principaux
2. **Génération introduction** : Contexte éditorial de la semaine
3. **Réécriture titres** : Optimisation éditoriale des titres d'items
4. **Génération résumés** : Expansion des résumés Bedrock existants
5. **Homogénéisation ton** : Style cohérent selon client_profile

**❌ Bedrock NE DOIT PAS faire :**
1. **Sélection des items** : Logique déterministe basée sur configuration
2. **Tri des items** : Algorithmes de scoring existants
3. **Structure des sections** : Définie par newsletter_layout
4. **Métriques** : Calculs statistiques déterministes

#### Prompts Bedrock Spécialisés Newsletter

**TL;DR Generation :**
```yaml
newsletter_tldr_generation:
  system_instructions: |
    You are an expert newsletter editor for biotech intelligence.
    Generate a concise TL;DR section highlighting the week's key themes and takeaways.
    
  user_template: |
    Generate a TL;DR for {{client_name}} newsletter covering {{period}}.
    
    TOP ITEMS THIS WEEK:
    {{#each top_items}}
    - {{title}} ({{event_type}}, score: {{score}})
      Companies: {{companies}}
      Key insight: {{summary}}
    {{/each}}
    
    CLIENT PROFILE:
    - Audience: {{target_audience}}
    - Tone: {{tone}}
    - Voice: {{voice}}
    - Focus: {{vertical}} technologies
    
    Generate a 2-3 sentence TL;DR that:
    1. Identifies the dominant themes this week
    2. Highlights strategic implications
    3. Uses executive language appropriate for {{target_audience}}
    
    Format: Plain text, no markdown.
```

**Item Title Rewriting :**
```yaml
newsletter_title_rewriting:
  user_template: |
    Rewrite this biotech news title for a newsletter:
    
    ORIGINAL: {{original_title}}
    CONTEXT: {{event_type}} involving {{companies}}
    AUDIENCE: {{target_audience}}
    TONE: {{tone}}
    
    Requirements:
    1. Keep under 80 characters
    2. Maintain factual accuracy
    3. Use {{tone}} tone for {{target_audience}}
    4. Highlight key companies/technologies
    5. Make it engaging but professional
    
    Return only the rewritten title.
```

**Section Summary Generation :**
```yaml
newsletter_section_summary:
  user_template: |
    Generate a 1-sentence summary for this newsletter section:
    
    SECTION: {{section_title}}
    ITEMS IN SECTION:
    {{#each section_items}}
    - {{title}} ({{companies}}, {{event_type}})
    {{/each}}
    
    CONTEXT: {{client_name}} newsletter for {{target_audience}}
    
    Generate a single sentence that:
    1. Summarizes the common theme across items
    2. Uses {{tone}} tone
    3. Provides strategic context
    
    Return only the summary sentence.
```

### Étape 3 : Assemblage Final (Template Engine)

#### Structure Markdown Générée
```python
def assemble_newsletter_markdown(selected_items, editorial_content, client_config, metrics):
    """Assemble la newsletter finale en Markdown."""
    
    client_profile = client_config.get('client_profile', {})
    newsletter_layout = client_config.get('newsletter_layout', {})
    
    # Header
    markdown = f"""# {editorial_content['newsletter_title']}

*{editorial_content['introduction']}*

## TL;DR – Key Takeaways

{editorial_content['tldr']}

**Key Metrics:** {metrics['items_analyzed']} signals analyzed • {metrics['items_selected']} items selected • {metrics['sources_monitored']} sources monitored

---

"""
    
    # Sections
    for section_config in newsletter_layout.get('sections', []):
        section_id = section_config['id']
        section_title = section_config['title']
        section_items = selected_items.get(section_id, [])
        
        if not section_items:
            continue
            
        markdown += f"## {section_title}\n\n"
        
        # Section summary (optionnel)
        if section_id in editorial_content.get('section_summaries', {}):
            markdown += f"{editorial_content['section_summaries'][section_id]}\n\n"
        
        # Items de la section
        for item in section_items:
            markdown += format_newsletter_item(item, client_profile)
            markdown += "\n"
        
        markdown += "---\n\n"
    
    # Footer
    markdown += "*Newsletter generated by Vectora Inbox – Powered by Amazon Bedrock*\n"
    
    return markdown

def format_newsletter_item(item, client_profile):
    """Formate un item pour la newsletter."""
    
    # Icône selon le type d'événement
    event_icons = {
        'partnership': '🤝',
        'regulatory': '📋',
        'clinical_update': '🧪',
        'financial_results': '💰',
        'corporate_move': '🏢',
        'other': '📊'
    }
    
    event_type = item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', 'other')
    icon = event_icons.get(event_type, '📊')
    
    # Titre (réécrit par Bedrock)
    title = item.get('editorial_title', item.get('title', 'Untitled'))
    
    # Métadonnées
    source_key = item.get('source_key', '').replace('press_corporate__', '').replace('_', ' ').title()
    score = item.get('scoring_results', {}).get('final_score', 0)
    published_at = item.get('published_at', '')
    url = item.get('url', '#')
    
    # Résumé (enrichi par Bedrock)
    summary = item.get('editorial_summary', 
                      item.get('normalized_content', {}).get('summary', 'No summary available'))
    
    # Entités clés
    entities = item.get('normalized_content', {}).get('entities', {})
    companies = ', '.join(entities.get('companies', [])[:3])  # Max 3 companies
    technologies = ', '.join(entities.get('technologies', [])[:2])  # Max 2 technologies
    
    markdown = f"""### {icon} {title}
**Source:** {source_key} • **Score:** {score} • **Date:** {published_at}

{summary}

"""
    
    # Contexte entités (optionnel)
    if companies or technologies:
        context_parts = []
        if companies:
            context_parts.append(f"**Companies:** {companies}")
        if technologies:
            context_parts.append(f"**Technologies:** {technologies}")
        
        markdown += f"{' • '.join(context_parts)}  \n"
    
    markdown += f"[**Read more →**]({url})\n"
    
    return markdown
```

---

## 💰 COÛTS & SCALABILITÉ

### Estimation Coûts par Run

#### Appels Bedrock Newsletter (Estimés)
```python
def estimate_newsletter_bedrock_costs(selected_items, client_config):
    """Estime les coûts Bedrock pour la génération newsletter."""
    
    costs = {
        'calls': 0,
        'input_tokens': 0,
        'output_tokens': 0,
        'estimated_cost_usd': 0.0
    }
    
    # 1. TL;DR generation (1 appel)
    costs['calls'] += 1
    costs['input_tokens'] += 1500  # Context des top items
    costs['output_tokens'] += 200  # TL;DR 2-3 phrases
    
    # 2. Introduction generation (1 appel)
    costs['calls'] += 1
    costs['input_tokens'] += 1000  # Context client + période
    costs['output_tokens'] += 150  # Introduction 1-2 phrases
    
    # 3. Title rewriting (1 appel par item sélectionné)
    total_items = sum(len(items) for items in selected_items.values())
    costs['calls'] += total_items
    costs['input_tokens'] += total_items * 300  # Titre + contexte par item
    costs['output_tokens'] += total_items * 80   # Titre réécrit par item
    
    # 4. Section summaries (1 appel par section non-vide)
    non_empty_sections = len([s for s in selected_items.values() if s])
    costs['calls'] += non_empty_sections
    costs['input_tokens'] += non_empty_sections * 800  # Items de la section
    costs['output_tokens'] += non_empty_sections * 100  # Résumé par section
    
    # 5. Calcul coût total (Claude Sonnet 3 pricing)
    input_cost_per_1k = 0.003   # $0.003 per 1K input tokens
    output_cost_per_1k = 0.015  # $0.015 per 1K output tokens
    
    costs['estimated_cost_usd'] = (
        (costs['input_tokens'] / 1000) * input_cost_per_1k +
        (costs['output_tokens'] / 1000) * output_cost_per_1k
    )
    
    return costs
```

#### Métriques Réelles lai_weekly_v3 (7 items sélectionnés)
```
Appels Bedrock estimés:
- TL;DR: 1 appel
- Introduction: 1 appel  
- Title rewriting: 7 appels (7 items)
- Section summaries: 4 appels (4 sections)
Total: 13 appels Bedrock

Tokens estimés:
- Input: ~8,900 tokens
- Output: ~1,260 tokens
Coût estimé: ~$0.045 par newsletter

Temps d'exécution estimé: 30-45 secondes
```

### Scalabilité Multi-Clients

#### Coûts Annuels Projetés
```
1 client (lai_weekly):
- 52 newsletters/an × $0.045 = $2.34/an

5 clients:
- 5 × 52 × $0.045 = $11.70/an

10 clients:
- 10 × 52 × $0.045 = $23.40/an

20 clients:
- 20 × 52 × $0.045 = $46.80/an
```

**Conclusion :** Coûts très maîtrisés, scalabilité excellente

#### Optimisations Possibles
1. **Batch processing** : Grouper les appels de réécriture de titres
2. **Caching** : Réutiliser les introductions similaires
3. **Template reuse** : Prompts optimisés pour réduire tokens
4. **Parallel calls** : Appels Bedrock en parallèle (attention throttling)

---

## 🎯 RECOMMANDATIONS STRATÉGIQUES

### Choix Stratégiques Avant Codage

#### 1. Rôle de Bedrock : Rédaction Uniquement ✅
**Décision :** La sélection des items est **déterministe** (configuration + scoring), Bedrock ne fait que la **rédaction éditoriale**.

**Justification :**
- Configuration pilotée prévisible et debuggable
- Coûts maîtrisés (pas de sélection par LLM)
- Performance optimale (pas d'appels Bedrock pour tri)
- Cohérence avec architecture existante

#### 2. Déduplication : Avant Sélection ✅
**Décision :** Déduplication appliquée **avant** la sélection par section.

**Justification :**
- Évite les doublons entre sections
- Optimise l'utilisation des slots disponibles
- Simplifie la logique de sélection

#### 3. Gestion des Sections Vides : Flexible ✅
**Décision :** Les sections sans items sont **omises** de la newsletter finale.

**Justification :**
- Newsletter plus concise
- Évite les sections artificiellement remplies
- Respecte la qualité vs quantité

### Schéma Idéal Lambda newsletter-v2

#### Inputs Exacts
```python
# S3 Input
curated_items_path = f"s3://{DATA_BUCKET}/curated/{client_id}/{YYYY}/{MM}/{DD}/items.json"

# Configuration
client_config_path = f"s3://{CONFIG_BUCKET}/clients/{client_id}.yaml"
canonical_prompts_path = f"s3://{CONFIG_BUCKET}/canonical/prompts/global_prompts.yaml"

# Event
event = {
    "client_id": "lai_weekly_v3",
    "target_date": "2025-01-15",  # Optionnel
    "output_format": "markdown"   # Optionnel
}
```

#### Étapes Internes
```python
def run_newsletter_for_client(client_id, env_vars, **kwargs):
    """Orchestration complète génération newsletter."""
    
    # 1. Chargement données et configurations
    curated_items = load_curated_items(client_id, env_vars['DATA_BUCKET'])
    client_config = load_client_config(client_id, env_vars['CONFIG_BUCKET'])
    canonical_prompts = load_canonical_prompts(env_vars['CONFIG_BUCKET'])
    
    # 2. Sélection déterministe des items
    selected_items = select_items_for_newsletter(curated_items, client_config)
    
    # 3. Génération éditoriale Bedrock
    editorial_content = generate_editorial_content(
        selected_items, client_config, canonical_prompts, 
        env_vars['BEDROCK_MODEL_ID'], env_vars['BEDROCK_REGION']
    )
    
    # 4. Assemblage newsletter
    newsletter_markdown = assemble_newsletter_markdown(
        selected_items, editorial_content, client_config
    )
    
    # 5. Calcul métriques
    metrics = calculate_newsletter_metrics(curated_items, selected_items)
    
    # 6. Sauvegarde S3
    output_paths = save_newsletter_to_s3(
        newsletter_markdown, editorial_content, metrics,
        client_id, env_vars['NEWSLETTERS_BUCKET']
    )
    
    return {
        "status": "completed",
        "output_paths": output_paths,
        "metrics": metrics,
        "bedrock_costs": editorial_content.get('bedrock_costs', {})
    }
```

#### Outputs Exacts
```python
# S3 Outputs
newsletter_md_path = f"s3://{NEWSLETTERS_BUCKET}/{client_id}/{YYYY}/{MM}/{DD}/newsletter.md"
newsletter_json_path = f"s3://{NEWSLETTERS_BUCKET}/{client_id}/{YYYY}/{MM}/{DD}/newsletter.json"
manifest_path = f"s3://{NEWSLETTERS_BUCKET}/{client_id}/{YYYY}/{MM}/{DD}/manifest.json"

# Response
{
    "statusCode": 200,
    "body": {
        "client_id": "lai_weekly_v3",
        "newsletter_title": "LAI Intelligence Weekly – January 15, 2025",
        "items_selected": 7,
        "sections_generated": 4,
        "bedrock_calls": 13,
        "processing_time_ms": 42000,
        "estimated_cost_usd": 0.045,
        "output_paths": {
            "markdown": "s3://vectora-inbox-newsletters-dev/lai_weekly_v3/2025/01/15/newsletter.md",
            "json": "s3://vectora-inbox-newsletters-dev/lai_weekly_v3/2025/01/15/newsletter.json"
        }
    }
}
```

---

## 📋 CONCLUSION PHASE 4

### Réponses aux Questions Clés

#### "Comment choisir les items à inclure ?"
**✅ Stratégie validée :**
1. **Filtrage global** : Score ≥ min_score (12 pour lai_weekly_v3)
2. **Déduplication** : Algorithme 3 étapes (technique → sémantique → temporelle)
3. **Sélection par section** : Domaines + types d'événements + tri + limites
4. **Limite globale** : max_items_total (15 pour lai_weekly_v3)

#### "Dans quelles sections ?"
**✅ Mapping configuré :**
- **watch_domains** → **source_domains** (newsletter_layout)
- **event_classification.primary_type** → **filter_event_types**
- **Tri configurable** : score_desc, date_desc

#### "Quel rôle exact de Bedrock ?"
**✅ Rédaction uniquement :**
- TL;DR + Introduction + Réécriture titres + Résumés sections
- **PAS de sélection** (déterministe via configuration)
- **PAS de tri** (algorithmes de scoring existants)

#### "Coûts et scalabilité ?"
**✅ Très maîtrisés :**
- $0.045 par newsletter (7 items)
- $46.80/an pour 20 clients
- Scalabilité excellente

### Prochaine Étape

**Phase 5 :** Évaluer la pertinence du contrat newsletter_v2.md et faire des recommandations d'amélioration basées sur cette analyse stratégique.

---

**🎯 RÉSULTAT PHASE 4**

La stratégie d'assemblage newsletter est **définie et optimisée** avec un rôle clair pour chaque composant : configuration déterministe pour la sélection, Bedrock pour la rédaction, templates pour l'assemblage.