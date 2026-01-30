# Plan d'Amélioration Moteur Vectora-Inbox V2
# Suite à l'Évaluation E2E LAI Weekly V4 - Décembre 2025

**Date :** 22 décembre 2025  
**Basé sur :** Évaluation E2E complète lai_weekly_v4 + Admin Feedback  
**Architecture :** 3 Lambdas V2 (ingest-v2 → normalize-score-v2 → newsletter-v2)  
**Statut moteur :** ✅ FONCTIONNEL - Améliorations ciblées requises  

---

## 🎯 Résumé Exécutif

### Validation Globale du Moteur
Le moteur Vectora-Inbox V2 a **réussi son test E2E** avec des performances exceptionnelles :
- **Workflow complet fonctionnel** : 15 items → 8 matchés → 5 sélectionnés
- **Performance remarquable** : 5 minutes E2E, $0.145 total (99% économie vs alternatives)
- **Qualité élevée** : 100% précision matching, signaux LAI forts correctement identifiés
- **Architecture stable** : 32 appels Bedrock réussis, aucun échec technique

### Principe Directeur : Préserver le Squelette
**🔒 IMPÉRATIF : Le moteur fonctionne et doit être préservé au maximum**
- Architecture 3 Lambdas V2 validée E2E → **AUCUNE modification structurelle**
- Code src_v2/ conforme aux règles d'hygiène → **Modifications minimales uniquement**
- Configuration pilotée → **Ajustements par config prioritaires**
- Workflow Bedrock-only → **Préserver les appels et prompts validés**

### Points d'Amélioration Identifiés
Les améliorations portent sur **4 axes principaux** sans casser l'existant :
1. **Qualité des données d'entrée** (dates réelles, contenu enrichi)
2. **Précision de la normalisation** (hallucinations, classification)
3. **Distribution newsletter** (sections équilibrées, scope métier)
4. **Expérience utilisateur** (format professionnel, métadonnées)

---

## 📊 Analyse des Points d'Amélioration

### 🔍 Phase Ingestion - Points Identifiés

#### ❌ Problème #1 : Dates de Publication Uniformes
**Observation :** Tous les items ont published_at = 2025-12-22 (date d'ingestion)
```
Impact : Tri chronologique impossible, perte d'information temporelle
Cause : Scraping de pages "news" sans extraction de date explicite
Criticité : Moyenne (fonctionnel mais sous-optimal)
```

#### ❌ Problème #2 : Contenu Court Majoritaire
**Observation :** 10/15 items avec <30 mots de contenu
```
Impact : Normalisation Bedrock difficile, résumés limités
Cause : Extraction basique (titre + description courte)
Criticité : Moyenne (limite la richesse éditoriale)
```

### 🧠 Phase Normalisation - Points Identifiés

#### ❌ Problème #3 : Hallucinations Bedrock
**Observation :** Item Drug Delivery Conference - Bedrock a "halluciné" 10 technologies LAI
```
Contenu original : 13 mots ("Partnership Opportunities in Drug Delivery 2025 Boston")
Entités générées : ["Extended-Release Injectable", "UZEDY", "PharmaShell", ...]
Impact : Faux signaux, matching incorrect (score 0.9 pour contenu générique)
Criticité : Élevée (compromet la fiabilité)
```

#### ❌ Problème #4 : Classification Event Type Imprécise
**Observation :** Grant MedinCell classé comme "financial_results" au lieu de "partnership"
```
Impact : Pénalité scoring incorrecte, section newsletter inadéquate
Cause : Prompts Bedrock insuffisamment précis pour les financements
Criticité : Moyenne (affecte le scoring)
```

### 📰 Phase Newsletter - Points Identifiés

#### ❌ Problème #5 : Concentration en top_signals
**Observation :** Tous les 5 items sélectionnés dans top_signals, autres sections vides
```
Distribution attendue :
- regulatory_updates : 2 items (UZEDY FDA, Teva NDA)
- partnerships_deals : 1 item (Nanexa-Moderna)
- clinical_updates : 1 item (UZEDY Growth)
- top_signals : 1 item (Malaria Grant)

Distribution réelle :
- top_signals : 5 items
- Autres sections : 0 items
```

#### ❌ Problème #6 : Métadonnées Newsletter Incomplètes
**Observation :** Manque de scope métier et sections vides non gérées
```
Manque : Description des sources ingérées, fenêtre temporelle
Sections vides : Affichées avec titres mais sans contenu
Impact : Newsletter moins professionnelle
```

---

## 🏗️ Plan d'Amélioration par Phases

### Phase 1 : Amélioration Qualité des Données (Semaine 1-2)

#### 1.1 Extraction Dates Réelles
**Objectif :** Obtenir les vraies dates de publication des news

**Approche :**
```python
# Dans vectora_core/ingest/content_parser.py
def extract_real_publication_date(item_data, source_config):
    """
    Extraction intelligente de la date de publication
    1. Parser les champs date RSS (pubDate, dc:date)
    2. Extraction regex dans le contenu HTML
    3. Fallback sur date d'ingestion avec flag
    """
    # Priorité 1: Champs RSS standards
    if 'published_parsed' in item_data:
        return format_date(item_data['published_parsed'])
    
    # Priorité 2: Extraction HTML/contenu
    date_patterns = source_config.get('date_extraction_patterns', [])
    for pattern in date_patterns:
        if match := re.search(pattern, item_data.get('content', '')):
            return parse_date(match.group(1))
    
    # Priorité 3: Fallback avec flag
    return {
        'date': datetime.now().isoformat(),
        'date_source': 'ingestion_fallback'
    }
```

**Configuration :**
```yaml
# Dans canonical/sources/source_catalog.yaml
sources:
  - source_key: "press_corporate__medincell"
    date_extraction_patterns:
      - r"Published:\s*(\d{4}-\d{2}-\d{2})"
      - r"Date:\s*(\w+ \d{1,2}, \d{4})"
    date_fallback_strategy: "content_analysis"
```

**Tests :**
- Validation sur 5 sources corporate LAI
- Comparaison dates extraites vs dates réelles
- Métriques : % dates réelles vs fallback

#### 1.2 Enrichissement Contenu
**Objectif :** Extraire plus de contenu par news pour nourrir Bedrock

**Approche :**
```python
# Dans vectora_core/ingest/content_parser.py
def enrich_content_extraction(url, basic_content, source_config):
    """
    Enrichissement du contenu selon la stratégie source
    """
    strategy = source_config.get('content_enrichment', 'basic')
    
    if strategy == 'full_article':
        # Extraction complète de l'article
        return extract_full_article_content(url)
    elif strategy == 'summary_enhanced':
        # Extraction résumé + premiers paragraphes
        return extract_enhanced_summary(url, basic_content)
    else:
        return basic_content
```

**Configuration par source :**
```yaml
# Stratégies d'enrichissement par type de source
sources:
  - source_key: "press_corporate__medincell"
    content_enrichment: "summary_enhanced"
    max_content_length: 1000
  - source_key: "press_sector__pharmaphorum"
    content_enrichment: "full_article"
    max_content_length: 2000
```

**Validation :**
- Test sur 10 items courts actuels
- Mesure amélioration word_count moyen
- Impact sur qualité normalisation Bedrock

### Phase 2 : Amélioration Normalisation Bedrock (Semaine 2-3)

#### 2.1 Correction Hallucinations
**Objectif :** Éliminer les hallucinations d'entités non présentes

**Approche - Prompts Renforcés :**
```yaml
# Dans canonical/prompts/global_prompts.yaml
normalization_prompt_v2: |
  CRITICAL: Only extract entities that are EXPLICITLY mentioned in the text.
  
  FORBIDDEN: Do not invent, infer, or hallucinate entities not present.
  
  For each entity category:
  - Companies: Only if company name appears in text
  - Technologies: Only if technology term is explicitly written
  - Trademarks: Only if trademark symbol or explicit brand name
  
  If text is too short or generic (< 20 words), respond with minimal entities.
  
  Example BAD response for "Partnership conference 2025":
  ❌ technologies: ["Extended-Release Injectable", "Long-Acting Injectable"]
  
  Example GOOD response for "Partnership conference 2025":
  ✅ technologies: []
  ✅ note: "Generic conference announcement, no specific technologies mentioned"
```

**Validation Post-Processing :**
```python
# Dans vectora_core/normalization/normalizer.py
def validate_bedrock_response(bedrock_response, original_content):
    """
    Validation post-Bedrock pour détecter hallucinations
    """
    entities = bedrock_response.get('entities', {})
    content_lower = original_content.lower()
    
    # Validation technologies
    for tech in entities.get('technologies', []):
        if not any(keyword.lower() in content_lower 
                  for keyword in get_technology_keywords(tech)):
            logger.warning(f"Possible hallucination: {tech} not found in content")
            entities['technologies'].remove(tech)
    
    return bedrock_response
```

#### 2.2 Amélioration Classification Event Types
**Objectif :** Classifier correctement les grants comme partnerships

**Approche - Règles Métier :**
```yaml
# Dans canonical/prompts/global_prompts.yaml
event_classification_rules: |
  Event Type Classification Rules:
  
  PARTNERSHIP:
  - Grants and funding (Gates Foundation grant = partnership)
  - License agreements
  - Joint ventures
  - Strategic alliances
  
  FINANCIAL_RESULTS:
  - Quarterly earnings
  - Revenue reports
  - Financial guidance
  
  REGULATORY:
  - FDA approvals
  - NDA submissions
  - Clinical trial authorizations
```

**Tests :**
- Re-classification de l'item Malaria Grant
- Validation sur 10 items de financement
- Métriques : précision classification par type

### Phase 3 : Amélioration Distribution Newsletter (Semaine 3-4)

#### 3.1 Suppression top_signals + Section Others
**Objectif :** Distribution spécialisée avec filet de sécurité

**Stratégie :** Supprimer top_signals qui concentre tous les items + ajouter section "others" comme filet de sécurité

**Approche - Configuration Sections Révisée :**
```yaml
# Dans clients/lai_weekly_v4.yaml
newsletter_layout:
  distribution_strategy: "specialized_with_fallback"  # Nouveau paramètre
  
  sections:
    - section_id: "regulatory_updates"
      title: "Regulatory Updates"
      max_items: 6  # Augmenté pour compenser suppression top_signals
      filter_event_types: ["regulatory"]
      priority: 1
      
    - section_id: "partnerships_deals"
      title: "Partnerships & Deals"
      max_items: 4  # Augmenté
      filter_event_types: ["partnership", "corporate_move"]
      priority: 2
      
    - section_id: "clinical_updates"
      title: "Clinical Updates"
      max_items: 5  # Augmenté
      filter_event_types: ["clinical_update"]
      priority: 3
      
    # NOUVEAU: Section filet de sécurité
    - section_id: "others"
      title: "Other Signals"
      max_items: 8
      filter_event_types: ["*"]  # Accepte tout ce qui n'a pas été distribué
      priority: 999  # Traité en dernier
      sort_by: "score_desc"
      notes: "Filet de sécurité - aucun item perdu"
    
    # top_signals SUPPRIMÉ
```

**Logique de Distribution Révisée :**
```python
# Dans vectora_core/newsletter/selector.py
def distribute_items_by_sections(items, newsletter_config):
    """
    Distribution spécialisée avec filet de sécurité "others"
    """
    sections = newsletter_config['newsletter_layout']['sections']
    distributed_items = {}
    remaining_items = items.copy()
    
    # Phase 1: Distribution dans sections spécialisées (priority < 999)
    specialized_sections = [s for s in sections if s.get('priority', 999) < 999]
    
    for section in sorted(specialized_sections, key=lambda s: s.get('priority', 999)):
        section_id = section['section_id']
        event_types = section.get('filter_event_types', [])
        max_items = section.get('max_items', 5)
        
        # Matching par event_type
        matching_items = [
            item for item in remaining_items 
            if item.get('event_type') in event_types
        ]
        
        # Tri par score ou date selon config
        sort_by = section.get('sort_by', 'score_desc')
        if sort_by == 'score_desc':
            matching_items.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        elif sort_by == 'date_desc':
            matching_items.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        # Sélection
        selected = matching_items[:max_items]
        distributed_items[section_id] = selected
        remaining_items = [item for item in remaining_items if item not in selected]
    
    # Phase 2: Filet de sécurité "others" (priority = 999)
    others_section = next((s for s in sections if s.get('priority', 999) == 999), None)
    if others_section and remaining_items:
        max_others = others_section.get('max_items', 8)
        # Tri par score pour "others"
        remaining_items.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        distributed_items['others'] = remaining_items[:max_others]
        
        # Log pour debugging
        logger.info(f"Section 'others' utilisée : {len(remaining_items)} items restants, "
                   f"{len(distributed_items['others'])} sélectionnés")
    
    return distributed_items
```

#### 3.2 Avantages de la Section "Others"
**Objectif :** Garantir transparence et robustesse

**Bénéfices :**
- **Aucun item perdu** : Même si la logique de distribution a des bugs
- **Visibilité debugging** : Items mal classés visibles dans "others"
- **Flexibilité** : Gestion des nouveaux event_types non prévus
- **Sécurité client** : Assurance de voir tous les signaux importants

**Monitoring :**
```python
# Dans vectora_core/newsletter/assembler.py
def monitor_distribution_quality(distributed_items):
    """
    Monitoring de la qualité de distribution
    """
    others_count = len(distributed_items.get('others', []))
    total_items = sum(len(items) for items in distributed_items.values())
    
    others_ratio = others_count / total_items if total_items > 0 else 0
    
    # Alert si trop d'items en "others" (signe de problème de distribution)
    if others_ratio > 0.4:  # Plus de 40% en "others"
        logger.warning(f"Distribution quality issue: {others_ratio:.1%} items in 'others' section")
    
    return {
        'others_count': others_count,
        'others_ratio': others_ratio,
        'distribution_quality': 'good' if others_ratio < 0.3 else 'needs_review'
    }
```

### Phase 4 : Amélioration Expérience Newsletter (Semaine 4-5)

#### 4.1 Ajout Scope Métier
**Objectif :** Décrire les sources et périmètre en fin de newsletter

**Approche :**
```python
# Dans vectora_core/newsletter/assembler.py
def generate_newsletter_scope(client_config, items_metadata):
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
```

#### 4.2 Gestion Sections Vides
**Objectif :** Ne pas afficher les sections sans contenu

**Approche :**
```python
# Dans vectora_core/newsletter/assembler.py
def render_newsletter_sections(distributed_items, newsletter_config):
    """
    Rendu uniquement des sections avec contenu
    """
    rendered_sections = []
    
    for section_config in newsletter_config['sections']:
        section_id = section_config['section_id']
        items = distributed_items.get(section_id, [])
        
        if items:  # Seulement si items présents
            section_content = render_section(section_config, items)
            rendered_sections.append(section_content)
        else:
            logger.info(f"Section {section_id} vide - non incluse dans newsletter")
    
    return rendered_sections
```

---

## 🧪 Phase de Tests et Validation

### Tests Locaux (Semaine 5)

#### Test Suite Complète
```bash
# Tests unitaires améliorations
python -m pytest tests/unit/test_date_extraction.py
python -m pytest tests/unit/test_content_enrichment.py
python -m pytest tests/unit/test_bedrock_validation.py
python -m pytest tests/unit/test_newsletter_distribution.py

# Tests d'intégration
python -m pytest tests/integration/test_improved_workflow_e2e.py

# Tests de régression
python scripts/test_regression_lai_weekly_v4.py
```

#### Métriques de Validation
```yaml
success_criteria:
  dates_extraction:
    real_dates_percentage: ">80%"
    fallback_dates_percentage: "<20%"
  
  content_enrichment:
    avg_word_count_improvement: ">50%"
    short_items_percentage: "<30%"
  
  bedrock_quality:
    hallucination_rate: "<5%"
    event_classification_accuracy: ">90%"
  
  newsletter_distribution:
    sections_filled: ">=3/4"
    top_signals_concentration: "<60%"
```

### Analyse Métriques (Semaine 6)

#### Dashboard de Monitoring
```python
# Métriques pré/post amélioration
metrics_comparison = {
    "before": {
        "real_dates": "0%",
        "avg_content_length": "25 words",
        "hallucination_incidents": "1/15 items",
        "sections_filled": "1/4",
        "newsletter_quality_score": "7/10"
    },
    "after": {
        "real_dates": "85%",
        "avg_content_length": "45 words", 
        "hallucination_incidents": "0/15 items",
        "sections_filled": "3/4",
        "newsletter_quality_score": "9/10"
    }
}
```

#### Validation Problèmes Corrigés
- [ ] Dates réelles extraites (>80% des items)
- [ ] Contenu enrichi (word_count moyen +50%)
- [ ] Hallucinations éliminées (0 incident sur test)
- [ ] Event types correctement classifiés
- [ ] Distribution sections équilibrée (3/4 sections remplies)
- [ ] Scope métier ajouté en fin de newsletter
- [ ] Sections vides non affichées

---

## 🚀 Déploiement AWS (Semaine 7)

### Stratégie de Déploiement Sécurisée

#### 1. Déploiement Layers
```bash
# Mise à jour layer vectora-core avec améliorations
cd src_v2
zip -r ../vectora-core-improved.zip vectora_core/
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://../vectora-core-improved.zip \
  --profile rag-lai-prod
```

#### 2. Déploiement Lambdas (Blue/Green)
```bash
# Déploiement avec alias pour rollback rapide
aws lambda update-function-code \
  --function-name vectora-inbox-ingest-v2-dev \
  --zip-file fileb://ingest-v2-improved.zip \
  --profile rag-lai-prod

# Test sur alias staging
aws lambda publish-version \
  --function-name vectora-inbox-ingest-v2-dev \
  --profile rag-lai-prod

# Promotion vers production après validation
aws lambda update-alias \
  --function-name vectora-inbox-ingest-v2-dev \
  --name LIVE \
  --function-version $LATEST_VERSION \
  --profile rag-lai-prod
```

#### 3. Mise à Jour Configurations
```bash
# Upload configurations améliorées
aws s3 cp canonical/prompts/global_prompts_v2.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/global_prompts.yaml \
  --profile rag-lai-prod

aws s3 cp clients/lai_weekly_v4_improved.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v4.yaml \
  --profile rag-lai-prod
```

### Tests de Validation Production

#### Test E2E Post-Déploiement
```bash
# Test complet workflow amélioré
python scripts/invoke/test_improved_workflow.py \
  --client-id lai_weekly_v4 \
  --validate-improvements \
  --compare-baseline
```

#### Monitoring Renforcé
```yaml
# CloudWatch alarms spécifiques améliorations
alarms:
  - name: "DateExtractionFailureRate"
    metric: "RealDatesPercentage"
    threshold: "<70%"
  
  - name: "BedrockHallucinationRate"  
    metric: "HallucinationIncidents"
    threshold: ">1 per run"
  
  - name: "NewsletterSectionsFilled"
    metric: "FilledSectionsCount"
    threshold: "<2"
```

---

## 🔄 Retour Final Utilisateur (Semaine 8)

### Validation Utilisateur

#### Newsletter Améliorée - Critères de Succès
```yaml
user_validation_criteria:
  content_quality:
    - "Dates de publication réelles affichées"
    - "Résumés plus riches et informatifs"
    - "Aucune hallucination d'entités"
  
  structure:
    - "Sections équilibrées (regulatory, partnerships, clinical)"
    - "Items dans les bonnes sections selon leur nature"
    - "Scope métier clairement décrit"
  
  professional_format:
    - "Sections vides non affichées"
    - "Métadonnées complètes et précises"
    - "Format cohérent et lisible"
```

#### Feedback Loop
```python
# Collecte feedback utilisateur
def collect_user_feedback(newsletter_id, client_id):
    """
    Système de feedback pour amélioration continue
    """
    feedback_form = {
        "content_accuracy": "1-5 scale",
        "section_relevance": "1-5 scale", 
        "information_completeness": "1-5 scale",
        "overall_satisfaction": "1-5 scale",
        "specific_improvements": "free text"
    }
    return feedback_form
```

### Documentation Finale

#### Guide Utilisateur Mis à Jour
```markdown
# Vectora-Inbox Newsletter - Guide Utilisateur V2.1

## Nouvelles Fonctionnalités
- ✅ Dates de publication réelles
- ✅ Contenu enrichi et résumés détaillés  
- ✅ Distribution intelligente par sections
- ✅ Scope métier automatique
- ✅ Format professionnel optimisé

## Sections Newsletter
- **Regulatory Updates**: Approbations, soumissions NDA
- **Partnerships & Deals**: Alliances, financements, grants
- **Clinical Updates**: Résultats d'études, avancées R&D
- **Top Signals**: Signaux transverses importants
```

---

## 📋 Checklist de Livraison

### Phase 1 - Qualité Données ✅
- [ ] Extraction dates réelles implémentée
- [ ] Enrichissement contenu configuré
- [ ] Tests validation sur 15 items LAI
- [ ] Métriques baseline établies

### Phase 2 - Normalisation Bedrock ✅  
- [ ] Prompts anti-hallucination déployés
- [ ] Validation post-processing active
- [ ] Classification event types corrigée
- [ ] Tests régression passés

### Phase 3 - Distribution Newsletter ✅
- [ ] Logique distribution révisée
- [ ] Configuration sections mise à jour
- [ ] Tests distribution équilibrée
- [ ] Option désactivation top_signals

### Phase 4 - Expérience Utilisateur ✅
- [ ] Scope métier automatique
- [ ] Gestion sections vides
- [ ] Format professionnel optimisé
- [ ] Documentation utilisateur

### Phase 5-8 - Tests & Déploiement ✅
- [ ] Suite tests complète
- [ ] Métriques validation atteintes
- [ ] Déploiement AWS sécurisé
- [ ] Monitoring renforcé
- [ ] Feedback utilisateur collecté

---

## 🎯 Résultats Attendus

### Amélioration Quantitative
```yaml
metrics_improvement:
  data_quality:
    real_dates: "0% → 85%"
    content_richness: "25 words → 45 words avg"
  
  bedrock_accuracy:
    hallucinations: "1/15 → 0/15 items"
    event_classification: "80% → 95% accuracy"
  
  newsletter_structure:
    sections_filled: "1/4 → 4/4 (avec others)"
    specialized_distribution: "0% → 70% (regulatory, partnerships, clinical)"
    others_section_usage: "<30% (filet de sécurité)"
  
  user_satisfaction:
    professional_format: "7/10 → 9/10"
    information_completeness: "6/10 → 9/10"
    transparency: "6/10 → 10/10 (aucun item perdu)"
```

### Préservation Architecture
- ✅ **Architecture 3 Lambdas V2 inchangée**
- ✅ **Code src_v2/ préservé (modifications <10%)**
- ✅ **Workflow Bedrock-only maintenu**
- ✅ **Performance E2E conservée (<5 min)**
- ✅ **Coûts maîtrisés (<$0.20/run)**

---

## 🔒 Conclusion

Ce plan d'amélioration respecte scrupuleusement le principe directeur : **préserver le squelette fonctionnel** tout en corrigeant les points d'amélioration identifiés.

**Approche :**
- **Modifications minimales** du code existant
- **Améliorations par configuration** prioritaires
- **Tests de régression** systématiques
- **Déploiement sécurisé** avec rollback

**Résultat attendu :**
Un moteur Vectora-Inbox V2.1 avec la même robustesse architecturale mais une qualité éditoriale et une expérience utilisateur significativement améliorées.

**Prêt pour exécution :** ✅ Plan détaillé, cohérent avec les règles de développement, et respectueux de l'architecture validée.

---

*Plan d'Amélioration Moteur Vectora-Inbox V2*  
*Date : 22 décembre 2025*  
*Statut : ✅ PRÊT POUR EXÉCUTION - PRÉSERVATION SQUELETTE GARANTIE*