# Problématique Doublons & Perte d'Information - Newsletter V2

**Date :** 21 décembre 2025  
**Phase :** 3 - Problématique des doublons & perte d'information  
**Objectif :** Préparer la déduplication et évaluer la richesse éditoriale  

---

## 🔍 ANALYSE DES DOUBLONS SUR RUN RÉEL

### Doublons Identifiés dans curated_items_final.json

#### 1. Doublon Exact Détecté

**Nanexa-Moderna Partnership (2 items identiques) :**

```json
// Item 1
{
  "item_id": "press_corporate__nanexa_20251219_6f822c",
  "title": "Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products",
  "url": "https://nanexa.com/mfn_news/nanexa-and-moderna-enter-into-license-and-option-agreement-for-the-development-of-pharmashell-based-products/",
  "content_hash": "sha256:a6f60bd2b0d446163f5bee10d1c134f77d3228b27e0b3e62cef64f33d4208a2d",
  "content": "PRESSRELEASES10 December, 2025Nanexa and Moderna enter into license and option agreement... (71 words)"
}

// Item 2 (DOUBLON)
{
  "item_id": "press_corporate__nanexa_20251219_6f822c", // ❌ MÊME ITEM_ID
  "title": "Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products", // ❌ MÊME TITRE
  "url": "https://nanexa.com/mfn_news/nanexa-and-moderna-enter-into-license-and-option-agreement-for-the-development-of-pharmashell-based-products/", // ❌ MÊME URL
  "content_hash": "sha256:d9b83fe6cb94dcaa8e1245f54fd2e589b6cf48151c4b60378d8012a5e5a20125", // ✅ Hash différent (contenu légèrement différent)
  "content": "10 December, 2025Nanexa and Moderna enter into license and option agreement... (61 words)" // ⚠️ Contenu plus court
}
```

**Analyse du doublon :**
- **Même événement** : Partnership Nanexa-Moderna PharmaShell®
- **Même URL** : Identique
- **Même item_id** : Identique (problème d'ingestion)
- **Contenu différent** : Version longue (71 mots) vs courte (61 mots)
- **Score identique** : 14.9 pour les deux

#### 2. Doublons Sémantiques Potentiels

**Rapports financiers Nanexa (3 items similaires) :**

```json
// Item A - Rapport Q3 2025 (détaillé)
{
  "title": "Nanexa publishes interim report for January-September 2025",
  "content": "...progress in optimizing GLP-1 formulations, extended commercial partnership, PharmaShell patent...",
  "lai_relevance_score": 7,
  "final_score": 9.7
}

// Item B - Rapport Q3 2025 (générique)
{
  "title": "Nanexa publishes interim report for January-September 2025", // ❌ MÊME TITRE
  "content": "Nanexa published its interim financial report for the period January-September 2025.", // ⚠️ Contenu générique
  "lai_relevance_score": 0,
  "final_score": 0
}

// Item C - Rapport Q2 2025
{
  "title": "Nanexa publishes interim report for January-June 2025",
  "content": "Nanexa published its interim financial report for the first half of 2025.",
  "lai_relevance_score": 0,
  "final_score": 0
}
```

**Pattern identifié :**
- **Même entreprise + même type** : Nanexa + financial_results
- **Périodes différentes** : Q2 vs Q3 2025
- **Qualité variable** : Version détaillée vs générique

### Patterns de Doublons Observés

#### Type 1 : Doublons Exacts (Technique)
- **Cause** : Même item_id généré par l'ingestion
- **Détection** : `item_id` identique OU `url` identique
- **Action** : Garder la version la plus riche (plus de mots, score plus élevé)

#### Type 2 : Doublons Sémantiques (Métier)
- **Cause** : Même événement, sources différentes ou versions multiples
- **Détection** : `title` similaire + `companies[]` identiques + `published_at` proche
- **Action** : Fusionner ou garder la version corporate

#### Type 3 : Doublons Temporels (Série)
- **Cause** : Rapports périodiques de la même entreprise
- **Détection** : `companies[]` + `event_type` + période différente
- **Action** : Garder le plus récent ou le plus pertinent

---

## 🧠 STRATÉGIE DE DÉDUPLICATION PROPOSÉE

### Algorithme de Déduplication en 3 Étapes

#### Étape 1 : Déduplication Technique (Exacte)
```python
def deduplicate_exact(items):
    """Supprime les doublons exacts basés sur URL ou item_id."""
    seen_urls = set()
    seen_item_ids = set()
    deduplicated = []
    
    for item in items:
        url = item.get('url', '')
        item_id = item.get('item_id', '')
        
        # Vérification doublon exact
        if url in seen_urls or item_id in seen_item_ids:
            # Garder la version la plus riche
            existing = find_existing_item(deduplicated, url, item_id)
            if is_richer_version(item, existing):
                replace_item(deduplicated, existing, item)
        else:
            deduplicated.append(item)
            seen_urls.add(url)
            seen_item_ids.add(item_id)
    
    return deduplicated
```

#### Étape 2 : Déduplication Sémantique (Événement)
```python
def deduplicate_semantic(items):
    """Fusionne les items parlant du même événement."""
    groups = []
    
    for item in items:
        # Signature événement
        signature = create_event_signature(item)
        
        # Chercher groupe existant
        group = find_matching_group(groups, signature)
        if group:
            group.append(item)
        else:
            groups.append([item])
    
    # Fusionner chaque groupe
    deduplicated = []
    for group in groups:
        if len(group) == 1:
            deduplicated.append(group[0])
        else:
            merged = merge_event_items(group)
            deduplicated.append(merged)
    
    return deduplicated

def create_event_signature(item):
    """Crée une signature unique pour un événement."""
    companies = item.get('normalized_content', {}).get('entities', {}).get('companies', [])
    trademarks = item.get('normalized_content', {}).get('entities', {}).get('trademarks', [])
    event_type = item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', '')
    published_date = item.get('published_at', '')[:10]  # YYYY-MM-DD
    
    # Signature basée sur entités + type + date
    signature = f"{sorted(companies)}_{sorted(trademarks)}_{event_type}_{published_date}"
    return signature
```

#### Étape 3 : Déduplication Temporelle (Série)
```python
def deduplicate_temporal(items):
    """Gère les séries temporelles (rapports périodiques)."""
    company_series = {}
    
    for item in items:
        companies = item.get('normalized_content', {}).get('entities', {}).get('companies', [])
        event_type = item.get('normalized_content', {}).get('event_classification', {}).get('primary_type', '')
        
        if event_type == 'financial_results' and companies:
            key = f"{companies[0]}_{event_type}"
            if key not in company_series:
                company_series[key] = []
            company_series[key].append(item)
    
    # Garder le plus pertinent par série
    deduplicated = []
    processed_items = set()
    
    for series in company_series.values():
        if len(series) > 1:
            # Trier par pertinence (score LAI + score final)
            best_item = max(series, key=lambda x: (
                x.get('normalized_content', {}).get('lai_relevance_score', 0),
                x.get('scoring_results', {}).get('final_score', 0)
            ))
            deduplicated.append(best_item)
            processed_items.update(item['item_id'] for item in series)
        else:
            deduplicated.append(series[0])
            processed_items.add(series[0]['item_id'])
    
    # Ajouter les items non traités
    for item in items:
        if item['item_id'] not in processed_items:
            deduplicated.append(item)
    
    return deduplicated
```

### Critères de Fusion/Sélection

#### Garder la Version la Plus Riche
```python
def is_richer_version(item1, item2):
    """Détermine quelle version est la plus riche."""
    
    # 1. Score LAI plus élevé
    lai_score1 = item1.get('normalized_content', {}).get('lai_relevance_score', 0)
    lai_score2 = item2.get('normalized_content', {}).get('lai_relevance_score', 0)
    if lai_score1 != lai_score2:
        return lai_score1 > lai_score2
    
    # 2. Plus d'entités détectées
    entities1 = item1.get('normalized_content', {}).get('entities', {})
    entities2 = item2.get('normalized_content', {}).get('entities', {})
    
    count1 = sum(len(entities1.get(key, [])) for key in ['companies', 'molecules', 'technologies', 'trademarks'])
    count2 = sum(len(entities2.get(key, [])) for key in ['companies', 'molecules', 'technologies', 'trademarks'])
    
    if count1 != count2:
        return count1 > count2
    
    # 3. Contenu plus long
    word_count1 = item1.get('metadata', {}).get('word_count', 0)
    word_count2 = item2.get('metadata', {}).get('word_count', 0)
    if word_count1 != word_count2:
        return word_count1 > word_count2
    
    # 4. Source corporate privilégiée
    source1 = item1.get('source_key', '')
    source2 = item2.get('source_key', '')
    if 'corporate' in source1 and 'corporate' not in source2:
        return True
    if 'corporate' in source2 and 'corporate' not in source1:
        return False
    
    # 5. Score final plus élevé
    score1 = item1.get('scoring_results', {}).get('final_score', 0)
    score2 = item2.get('scoring_results', {}).get('final_score', 0)
    return score1 > score2
```

---

## 📝 ANALYSE DE LA PERTE D'INFORMATION

### Comparaison Ingestion → Normalisation

#### Informations Préservées ✅

**Métadonnées de base :**
- `title`, `content`, `url`, `published_at` → **CONSERVÉES**
- `source_key`, `language`, `content_hash` → **CONSERVÉES**
- `metadata.word_count`, `metadata.author` → **CONSERVÉES**

**Enrichissement Bedrock :**
- **Résumé généré** : `normalized_content.summary` (2-3 phrases)
- **Entités extraites** : Companies, molecules, technologies, trademarks, indications
- **Classification** : `event_classification.primary_type` + confidence
- **Score LAI** : `lai_relevance_score` (0-10)

#### Informations Potentiellement Perdues ⚠️

**Contenu brut détaillé :**
```json
// Exemple item Teva Olanzapine NDA
{
  "content": "Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension (TEV-'749 / mdc-TJK) for the Once-Monthly Treatment of Schizophrenia in AdultsDecember 9, 2025December 9, 2025",
  "word_count": 33,
  
  // ⚠️ INFORMATIONS MANQUANTES pour newsletter :
  // - Détails financiers ($X million deal)
  // - Timeline précise (Q4 2025 submission)
  // - Citations de dirigeants
  // - Contexte concurrentiel
  // - Données cliniques (efficacité, sécurité)
}
```

**Structure du texte :**
- **Paragraphes** : Perdus dans la normalisation
- **Citations importantes** : Non extraites spécifiquement
- **Données chiffrées** : Non structurées (montants, pourcentages, dates)
- **Contexte métier** : Non capturé systématiquement

### Évaluation pour Génération Newsletter

#### ✅ Suffisant pour Newsletter de Base

**Informations disponibles :**
- **Titre** : Base pour réécriture Bedrock
- **Résumé Bedrock** : 2-3 phrases cohérentes
- **Entités clés** : Companies, trademarks, technologies pour contexte
- **Type d'événement** : Partnership, regulatory, clinical_update
- **Score de pertinence** : Priorisation éditoriale

**Exemple de génération possible :**
```markdown
### 🔥 Nanexa-Moderna Partnership for PharmaShell® Technology
**Source:** Nanexa Press Release • **Score:** 14.9 • **Date:** Dec 19, 2025

Nanexa and Moderna have entered into a license and option agreement for the development of up to five undisclosed compounds using Nanexa's PharmaShell® technology. The partnership includes upfront payments and milestone-based royalties.

**Key Players:** Nanexa, Moderna  
**Technology:** PharmaShell®  
**Event Type:** Partnership  

[**Read more →**](https://nanexa.com/mfn_news/...)
```

#### ⚠️ Limitations pour Newsletter Premium

**Informations manquantes pour enrichissement :**
- **Montants financiers** : "$3M upfront + $500M milestones" (dans contenu mais non structuré)
- **Timeline précise** : "Q4 2025" (dans contenu mais non extrait)
- **Citations dirigeants** : Non disponibles
- **Contexte concurrentiel** : "Dans le contexte de la concurrence X/Y..." (non généré)
- **Analyse d'impact** : Non disponible

### Champs Supplémentaires Souhaitables

#### Pour Enrichissement Éditorial

**Extraction de données structurées :**
```json
{
  "financial_data": {
    "upfront_payment": "$3M",
    "milestone_payments": "$500M",
    "royalty_rate": "single-digit tiered"
  },
  "timeline_data": {
    "announcement_date": "2025-12-10",
    "expected_completion": "Q4 2025"
  },
  "quotes": [
    {
      "speaker": "CEO Name",
      "company": "Nanexa",
      "quote": "This partnership represents..."
    }
  ],
  "competitive_context": {
    "market_size": "$X billion",
    "key_competitors": ["Company A", "Company B"],
    "market_position": "leading technology"
  }
}
```

**Prompts Bedrock enrichis :**
```yaml
# Dans canonical/prompts/global_prompts.yaml
newsletter_enrichment:
  extract_financial_data:
    user_template: |
      Extract financial information from this biotech news:
      {{item_text}}
      
      Return JSON with:
      - upfront_payments
      - milestone_payments  
      - deal_value
      - royalty_rates
      - market_size_mentions
```

---

## 🎯 RECOMMANDATIONS POUR NEWSLETTER LAMBDA

### Stratégie de Déduplication Recommandée

#### Implémentation en 3 Phases

**Phase 1 : Déduplication Basique (MVP)**
```python
def basic_deduplication(items):
    """Déduplication simple par URL et item_id."""
    seen = set()
    deduplicated = []
    
    for item in items:
        key = (item.get('url', ''), item.get('item_id', ''))
        if key not in seen:
            deduplicated.append(item)
            seen.add(key)
    
    return deduplicated
```

**Phase 2 : Déduplication Sémantique (V2)**
- Signature événement basée sur entités + type + date
- Fusion des versions multiples du même événement
- Privilégier sources corporate vs presse

**Phase 3 : Déduplication Intelligente (V3)**
- Machine learning pour détection similarité
- Fusion contextuelle avec préservation d'informations
- Gestion des séries temporelles

### Enrichissement Éditorial Recommandé

#### Prompts Bedrock Spécialisés Newsletter

**Génération de contexte :**
```yaml
newsletter_context_generation:
  user_template: |
    Generate editorial context for this LAI news item:
    {{item_summary}}
    
    Entities: {{entities}}
    Event Type: {{event_type}}
    
    Provide:
    1. One-sentence market context
    2. Competitive positioning (if applicable)
    3. Strategic significance (1-2 sentences)
    4. Key takeaway for executives
```

**Extraction de données clés :**
```yaml
newsletter_data_extraction:
  user_template: |
    Extract key data points from this content:
    {{item_content}}
    
    Focus on:
    - Financial figures (deals, investments, revenues)
    - Timeline information (dates, milestones)
    - Quantitative data (patient numbers, success rates)
    - Market data (size, growth, share)
    
    Return structured JSON.
```

### Configuration Newsletter Layout

#### Gestion des Doublons par Section
```yaml
# Dans client_config newsletter_layout
newsletter_layout:
  deduplication:
    enabled: true
    strategy: "semantic"  # basic, semantic, intelligent
    preserve_corporate_sources: true
    max_items_per_event: 1
    
  sections:
    - id: "top_signals"
      deduplication_priority: "highest_score"
      max_items: 5
    - id: "partnerships_deals"
      deduplication_priority: "most_recent"
      max_items: 3
```

---

## 📋 CONCLUSION PHASE 3

### Réponses aux Questions Clés

#### "Comment la Lambda newsletter doit-elle gérer les doublons ?"

**✅ Stratégie recommandée :**
1. **Déduplication technique** : URL et item_id identiques
2. **Déduplication sémantique** : Signature événement (entités + type + date)
3. **Sélection intelligente** : Version la plus riche (score LAI + entités + contenu)
4. **Privilégier sources corporate** : Plus fiables que presse généraliste

#### "A-t-on assez d'information pour générer une belle newsletter ?"

**✅ OUI pour newsletter de base :**
- Titre, résumé, entités, score → Suffisant pour génération Bedrock
- Contexte métier disponible via entités structurées
- Priorisation possible via scoring

**⚠️ LIMITATIONS pour newsletter premium :**
- Données financières non structurées
- Citations dirigeants manquantes
- Contexte concurrentiel à générer

### Prochaines Étapes

**Phase 4 :** Analyser la stratégie de sélection et structuration pour définir le rôle exact de Bedrock dans l'assemblage newsletter.

---

**🎯 RÉSULTAT PHASE 3**

La problématique doublons est **identifiée et solvable** avec l'algorithme proposé. La richesse éditoriale est **suffisante pour MVP newsletter** avec possibilités d'enrichissement via prompts Bedrock spécialisés.