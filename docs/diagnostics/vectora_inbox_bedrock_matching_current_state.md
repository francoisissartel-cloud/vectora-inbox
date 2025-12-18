# Diagnostic Complet - État Actuel de Bedrock dans Vectora Inbox

**Date** : 2025-12-12  
**Objectif** : Diagnostic précis de l'utilisation de Bedrock aujourd'hui et identification du "trou dans la raquette"  
**Scope** : Analyse complète du pipeline normalisation → matching → scoring  

---

## 🎯 Résumé Exécutif

### Constat Principal
**Bedrock est utilisé UNIQUEMENT pour la normalisation et la newsletter**, mais **PAS pour le matching/scoring** qui reste 100% déterministe. Il existe un **"trou dans la raquette"** entre ce que promet le prompt de normalisation (évaluation de pertinence LAI) et ce qui est effectivement exploité par le matching/scoring.

### Opportunité Identifiée
Le prompt de normalisation génère déjà des champs de pertinence (`lai_relevance_score`, `domain_relevance`) qui ne sont **pas exploités** par le matching/scoring. L'ajout d'un vrai "LLM gating" pourrait se faire en exploitant mieux ces signaux existants ou en ajoutant un prompt dédié.

---

## 📊 Phase 1 – Diagnostic Précis de l'État Actuel

### 1.1. Normalisation / Bedrock

#### Ce qui est décrit dans `canonical/prompts/global_prompts.yaml`

**Prompt de normalisation LAI** (`normalization.lai_default`) :
- **Extraction d'entités** : companies, molecules, technologies, trademarks, indications
- **Classification d'événements** : 9 types (clinical_update, partnership, regulatory, etc.)
- **Évaluation LAI** : Score 0-10 de pertinence LAI + détection anti-LAI + contexte pure player
- **Technologies LAI hardcodées** : 10 technologies spécifiques (Extended-Release Injectable, PLGA, etc.)
- **Trademarks hardcodées** : UZEDY, PharmaShell, SiliaShell, BEPO, etc.

#### Ce que construit `_build_normalization_prompt()` dans `bedrock_client.py`

**Version V1 avec prompts canonicalisés** :
```python
def _build_normalization_prompt_v1():
    # Feature flag USE_CANONICAL_PROMPTS=true/false
    if use_canonical:
        # Charge depuis canonical/prompts/global_prompts.yaml
        # Substitue {{item_text}}, {{companies_examples}}, {{molecules_examples}}
    else:
        # Fallback vers prompt hardcodé original
```

**Prompt hardcodé (fallback)** :
- **Section LAI spécialisée** : Technologies et trademarks hardcodés
- **10 tâches spécifiques** : Extraction + classification + évaluation LAI
- **Format JSON rigide** : Structure de réponse fixe
- **Support domaines** : Construction dynamique si `domain_contexts` fourni

#### Ce que Bedrock produit aujourd'hui pour chaque item

**Champs systématiques** :
```json
{
  "summary": "Résumé 2-3 phrases",
  "event_type": "clinical_update|partnership|regulatory|...",
  "companies_detected": ["Nanexa", "Moderna", ...],
  "molecules_detected": ["adalimumab", ...],
  "technologies_detected": ["Extended-Release Injectable", "PLGA", ...],
  "trademarks_detected": ["UZEDY", "PharmaShell", ...],
  "indications_detected": ["schizophrenia", "diabetes", ...],
  "lai_relevance_score": 8,           // ⚠️ GÉNÉRÉ MAIS NON EXPLOITÉ
  "anti_lai_detected": false,         // ⚠️ GÉNÉRÉ MAIS NON EXPLOITÉ
  "pure_player_context": true         // ⚠️ GÉNÉRÉ MAIS NON EXPLOITÉ
}
```

**Champs conditionnels** (si `domain_contexts` fourni) :
```json
{
  "domain_relevance": [               // ⚠️ GÉNÉRÉ MAIS NON EXPLOITÉ
    {
      "domain_id": "lai_psychiatry",
      "domain_type": "technology",
      "is_on_domain": true,
      "relevance_score": 0.85,
      "reason": "Article discusses long-acting antipsychotics"
    }
  ]
}
```

### 1.2. Matching (matcher.py)

#### Données du JSON normalisé lues par le matcher

**Entités utilisées** :
- `companies_detected` → intersections avec `company_scope`
- `molecules_detected` → intersections avec `molecule_scope`
- `technologies_detected` → intersections avec `technology_scope`
- `indications_detected` → intersections avec `indication_scope`

**Champs IGNORÉS** :
- ❌ `lai_relevance_score` : **Jamais lu ni utilisé**
- ❌ `anti_lai_detected` : **Jamais lu ni utilisé**
- ❌ `pure_player_context` : **Jamais lu ni utilisé**
- ❌ `domain_relevance` : **Jamais lu ni utilisé**

#### Logique purement déterministe

**Algorithme de matching** :
1. **Extraction des scopes** : Charger les ensembles depuis `canonical_scopes`
2. **Calcul d'intersections** : `item_entities ∩ scope_entities`
3. **Application des règles** : Depuis `domain_matching_rules.yaml`
4. **Matching contextuel** : Fonction `contextual_matching()` basée sur le type de company

**Exemple de règle** :
```yaml
technology:
  match_mode: "any_required"
  dimensions:
    entity:
      sources: ["company", "molecule"]
      requirement: "required"
      min_matches: 1
    technology:
      requirement: "optional"
      min_matches: 1
```

#### Exploitation du jugement "relevance" de Bedrock

**Réponse : AUCUNE**
- Le matching ne lit jamais `lai_relevance_score`
- Le matching ne lit jamais `domain_relevance`
- Seule la fonction `contextual_matching()` utilise `lai_relevance_score` pour filtrer selon le type de company

### 1.3. Scoring (scorer.py)

#### Inputs exacts du scorer

**Champs utilisés** :
- `event_type` → poids selon l'importance (clinical_update=3, partnership=2.5, etc.)
- `matched_domains` → priorité du domaine (high/medium/low)
- `companies_detected` → bonus pure player
- `date` → facteur de récence (décroissance exponentielle)
- `source_type` → poids selon la source (corporate=2, sector=1.5, generic=1)
- Nombre d'entités → bonus profondeur du signal

**Champs IGNORÉS** :
- ❌ `lai_relevance_score` : **Jamais utilisé dans le scoring**
- ❌ `domain_relevance` : **Partiellement supporté mais non utilisé**
- ❌ `anti_lai_detected` : **Jamais utilisé**

#### Calcul du score final

**Formule actuelle** :
```python
base_score = event_weight * priority_weight * recency_factor * source_weight
final_score = (base_score * confidence_multiplier) + signal_depth_bonus + company_bonus
```

**Champ `domain_relevance` supporté mais non utilisé** :
```python
def score_items(use_domain_relevance: bool = True):
    if use_domain_relevance and item.get('domain_relevance'):
        # Nouveau système : utiliser domain_relevance
        score = compute_score_with_domain_relevance(item, ...)
    else:
        # Ancien système : utiliser matched_domains (UTILISÉ ACTUELLEMENT)
```

#### Moment de rejet/conservation

**Seuils de scoring** : Définis dans les règles de scoring, pas dans le code
**Rejet** : Items avec `score < seuil_minimum` (configuré par client)
**Conservation** : Items avec `score >= seuil_minimum` triés par score décroissant

### 1.4. Conclusion Diagnostic

#### Étapes utilisant réellement Bedrock

1. **Normalisation** : ✅ Utilise Bedrock pour extraction d'entités + évaluation LAI
2. **Newsletter** : ✅ Utilise Bedrock pour génération éditoriale

#### Étapes 100% déterministes

1. **Matching** : ❌ Intersections d'ensembles + règles YAML
2. **Scoring** : ❌ Formules numériques + poids configurés

#### Le "Trou dans la Raquette" Identifié

**Problème** : Le prompt de normalisation génère des signaux de pertinence LAI sophistiqués (`lai_relevance_score`, `domain_relevance`) qui ne sont **jamais exploités** par le matching/scoring.

**Conséquences** :
- **Perte d'information** : Évaluation LLM de la pertinence LAI ignorée
- **Matching rigide** : Basé uniquement sur des intersections d'entités
- **Scoring simpliste** : Ne tient pas compte du jugement contextuel du LLM
- **Faux positifs** : Items avec entités LAI mais contexte non pertinent
- **Faux négatifs** : Items pertinents LAI sans keywords explicites

**Exemple concret** :
```json
// Item normalisé par Bedrock
{
  "title": "Nanexa partners with Moderna for PharmaShell technology",
  "companies_detected": ["Nanexa", "Moderna"],
  "technologies_detected": ["PharmaShell"],
  "lai_relevance_score": 9,           // ⚠️ SIGNAL FORT IGNORÉ
  "pure_player_context": true         // ⚠️ CONTEXTE IGNORÉ
}

// Matching actuel : ✅ Match (Nanexa ∈ pure_players, PharmaShell ∈ lai_technologies)
// Scoring actuel : Score basé sur event_type + pure_player_bonus
// ❌ MAIS lai_relevance_score=9 jamais utilisé pour booster le score
```

---

## 🎯 Phase 2 – Design Cible : Ajout d'un Vrai Prompt de Matching/Scoring LLM

### 2.1. Architecture Cible Proposée

#### Option A : Enrichir le prompt de normalisation (MINIMALE)

**Principe** : Exploiter mieux les champs existants (`lai_relevance_score`, `domain_relevance`)

**Avantages** :
- ✅ Aucun appel Bedrock supplémentaire
- ✅ Signaux déjà disponibles
- ✅ Implémentation rapide

**Inconvénients** :
- ❌ Prompt de normalisation surchargé
- ❌ Moins de contrôle sur l'évaluation de pertinence
- ❌ Mélange extraction d'entités et évaluation de pertinence

#### Option B : Nouveau prompt dédié LLM-matching (RECOMMANDÉE)

**Principe** : Créer un deuxième prompt spécialisé dans l'évaluation de pertinence

**Insertion dans le pipeline** :
```
Ingestion → Normalisation (Bedrock) → LLM-Matching (Bedrock) → Matching déterministe → Scoring → Newsletter
```

**Emplacement** : Dans la Lambda `ingest-normalize` après la normalisation

**Input du prompt LLM-matching** :
```yaml
llm_matching:
  domain_relevance_evaluation:
    user_template: |
      Evaluate the relevance of this biotech/pharma item to specific watch domains.
      
      ORIGINAL TEXT:
      {{item_text_summary}}
      
      NORMALIZED ENTITIES:
      - Companies: {{companies_detected}}
      - Molecules: {{molecules_detected}}
      - Technologies: {{technologies_detected}}
      - Event Type: {{event_type}}
      
      WATCH DOMAINS TO EVALUATE:
      {{watch_domains_context}}
      
      For EACH domain, evaluate:
      1. domain_relevance (0.0-1.0): How relevant is this item to this domain?
      2. is_relevant (true/false): Should this item be included for this domain?
      3. confidence (high/medium/low): Confidence in the evaluation
      4. reasoning (1-2 sentences): Brief explanation
      
      RESPONSE FORMAT (JSON only):
      {
        "domain_evaluations": [
          {
            "domain_id": "lai_psychiatry",
            "domain_relevance": 0.85,
            "is_relevant": true,
            "confidence": "high",
            "reasoning": "Article discusses partnership for long-acting antipsychotic development"
          }
        ]
      }
```

**Output du prompt LLM-matching** :
```json
{
  "domain_evaluations": [
    {
      "domain_id": "lai_psychiatry",
      "domain_relevance": 0.85,
      "is_relevant": true,
      "confidence": "high",
      "reasoning": "Partnership between pure player and Big Pharma for LAI antipsychotic"
    },
    {
      "domain_id": "lai_diabetes",
      "domain_relevance": 0.1,
      "is_relevant": false,
      "confidence": "high",
      "reasoning": "No mention of diabetes or metabolic indications"
    }
  ]
}
```

### 2.2. Généralisation Multi-Technologies

#### Design générique

**Pas de hardcoding LAI** :
- Technologies depuis `canonical/scopes/technologies/`
- Watch domains depuis `client_config`
- Prompts adaptables par vertical

**Configuration par client** :
```yaml
# client_config/lai_weekly_v3.yaml
watch_domains:
  - id: "lai_psychiatry"
    type: "technology"
    technology_scope: "lai_technologies_psychiatry"
    company_scope: "lai_companies_pure_players"
    priority: "high"
  - id: "lai_diabetes"
    type: "technology"
    technology_scope: "lai_technologies_diabetes"
    company_scope: "lai_companies_hybrid"
    priority: "medium"
```

**Template générique** :
```yaml
llm_matching:
  domain_relevance_evaluation:
    user_template: |
      Evaluate relevance to {{client_vertical}} domains:
      
      DOMAINS: {{watch_domains_descriptions}}
      TECHNOLOGIES: {{technology_scopes_examples}}
      COMPANIES: {{company_scopes_examples}}
      
      Item: {{item_summary}}
      
      Evaluate each domain (0.0-1.0 relevance)...
```

#### Support multi-vertical

**Oncologie** :
```yaml
watch_domains:
  - id: "car_t_therapy"
    technology_scope: "car_t_technologies"
  - id: "immunotherapy"
    technology_scope: "immunotherapy_technologies"
```

**Cell Therapy** :
```yaml
watch_domains:
  - id: "stem_cell_therapy"
    technology_scope: "stem_cell_technologies"
  - id: "gene_therapy"
    technology_scope: "gene_therapy_technologies"
```

### 2.3. Coût et Performances

#### Estimation des appels Bedrock supplémentaires

**Run lai_weekly_v3 typique** :
- Items ingérés : ~300-500
- Items normalisés : ~100-200 (après filtrage sources)
- **Appels LLM-matching supplémentaires : +100-200**

**Impact coût approximatif** :
- Coût normalisation actuel : ~$2-4 par run
- **Coût LLM-matching supplémentaire : +$1-2 par run**
- **Augmentation : +25-50% du coût Bedrock**

#### Risques de throttling

**Région us-east-1** (normalisation) :
- Limite actuelle : ~100 req/min
- Avec LLM-matching : ~200 req/min
- **Risque : MOYEN** (proche des limites)

**Mitigation** :
- Batch processing (5-10 items par appel)
- Retry avec backoff exponentiel
- Région eu-west-3 pour LLM-matching

#### Pistes pour contrôler le coût

**Préfiltre déterministe** :
```python
def should_call_llm_matching(item):
    # Appeler LLM-matching seulement si :
    # 1. Au moins 1 entité détectée
    # 2. Event type pertinent
    # 3. Pas de signaux anti-LAI évidents
    return (
        len(item.get('companies_detected', [])) > 0 or
        len(item.get('technologies_detected', [])) > 0
    ) and item.get('event_type') != 'financial_results'
```

**Seuils adaptatifs** :
- Items avec `lai_relevance_score < 3` : Skip LLM-matching
- Items avec `anti_lai_detected = true` : Skip LLM-matching
- Items avec event_type = 'financial_results' : Skip LLM-matching

**Batch processing** :
```python
# Traiter 5 items par appel Bedrock
def batch_llm_matching(items_batch):
    prompt = build_batch_matching_prompt(items_batch)
    # 1 appel pour 5 items = -80% d'appels
```

---

## 🚀 Phase 3 – Plan de Mise en Œuvre

### Phase A : Enrichir le prompt de normalisation (OPTION MINIMALE)

**Objectif** : Exploiter mieux les champs existants sans appels Bedrock supplémentaires

**Actions** :
1. **Modifier le matcher** : Lire `lai_relevance_score` et `domain_relevance`
2. **Modifier le scorer** : Utiliser `compute_score_with_domain_relevance()`
3. **Ajuster les seuils** : Filtrer items avec `lai_relevance_score < 5`

**Avantages** :
- ✅ Implémentation rapide (1-2 jours)
- ✅ Aucun coût supplémentaire
- ✅ Amélioration immédiate

**Inconvénients** :
- ❌ Amélioration limitée
- ❌ Prompt de normalisation surchargé

### Phase B : Créer un nouveau prompt dédié LLM-matching (OPTION RECOMMANDÉE)

**Objectif** : Vrai "LLM gating" avec prompt spécialisé

#### Phase B1 : Design et implémentation (3-4 jours)

**Actions** :
1. **Créer le prompt** : `canonical/prompts/global_prompts.yaml`
2. **Étendre PromptLoader** : Support du nouveau prompt
3. **Modifier bedrock_client** : Nouvelle fonction `evaluate_domain_relevance_with_bedrock()`
4. **Intégrer dans ingest-normalize** : Appel après normalisation

**Prompt LLM-matching** :
```yaml
matching:
  domain_relevance_evaluation:
    system_instructions: |
      You are a domain relevance expert for biotech/pharma intelligence.
      Evaluate how relevant news items are to specific technology domains.
      
    user_template: |
      Evaluate this item's relevance to watch domains:
      
      ITEM SUMMARY: {{item_summary}}
      ENTITIES: Companies={{companies}}, Technologies={{technologies}}
      EVENT TYPE: {{event_type}}
      
      DOMAINS TO EVALUATE:
      {{domains_context}}
      
      For each domain, provide:
      - relevance_score (0.0-1.0)
      - is_relevant (true/false)  
      - confidence (high/medium/low)
      - reasoning (1-2 sentences)
      
      JSON format only.
```

#### Phase B2 : Adapter le matching (1-2 jours)

**Modifier matcher.py** :
```python
def match_items_to_domains_with_llm(normalized_items, watch_domains, ...):
    for item in normalized_items:
        # 1. Matching déterministe (existant)
        deterministic_matches = compute_deterministic_matches(item, ...)
        
        # 2. LLM matching (nouveau)
        llm_evaluations = item.get('domain_evaluations', [])
        llm_matches = [e['domain_id'] for e in llm_evaluations if e['is_relevant']]
        
        # 3. Combinaison (ET logique ou OU logique selon config)
        if matching_mode == 'llm_only':
            item['matched_domains'] = llm_matches
        elif matching_mode == 'deterministic_and_llm':
            item['matched_domains'] = list(set(deterministic_matches) & set(llm_matches))
        else:  # 'deterministic_or_llm'
            item['matched_domains'] = list(set(deterministic_matches) | set(llm_matches))
```

#### Phase B3 : Adapter le scoring (1-2 jours)

**Modifier scorer.py** :
```python
def compute_score_with_llm_relevance(item, scoring_rules, ...):
    # Utiliser domain_evaluations pour le scoring
    domain_evaluations = item.get('domain_evaluations', [])
    
    # Prendre le meilleur score de pertinence
    max_relevance = max([e.get('relevance_score', 0) for e in domain_evaluations])
    
    # Bonus de confiance
    high_confidence_count = len([e for e in domain_evaluations if e.get('confidence') == 'high'])
    
    # Formule adaptée
    base_score = event_weight * max_relevance * recency_factor
    confidence_bonus = high_confidence_count * 0.5
    
    return base_score + confidence_bonus + other_bonuses
```

### Phase C : Tests et validation (2-3 jours)

**Dataset de référence** :
- Nanexa/Moderna partnership (LAI-strong)
- UZEDY regulatory updates (LAI-strong)
- MedinCell malaria program (LAI-strong)
- Pfizer financial results (LAI-weak)
- Generic biotech hiring (LAI-irrelevant)

**Métriques de validation** :
- **Précision** : % d'items pertinents dans les résultats
- **Rappel** : % d'items pertinents LAI détectés
- **F1-score** : Équilibre précision/rappel
- **Coût** : Nombre d'appels Bedrock supplémentaires

### Phase D : Déploiement AWS (1 jour)

**Actions** :
1. **Déploiement DEV** : Lambda ingest-normalize avec LLM-matching
2. **Configuration** : Feature flag `USE_LLM_MATCHING=true`
3. **Test E2E** : Run lai_weekly_v3 complet
4. **Monitoring** : Logs et métriques CloudWatch

### Phase E : Validation et optimisation (1-2 jours)

**Validation qualité** :
- Comparaison avant/après sur dataset historique
- Analyse des faux positifs/négatifs
- Ajustement des seuils de pertinence

**Optimisation coût** :
- Implémentation du préfiltre
- Batch processing si nécessaire
- Monitoring des coûts Bedrock

---

## 📋 Contraintes et Recommandations

### Contraintes Respectées

- ✅ **Aucune modification** du code ni des prompts à cette étape
- ✅ **Analyse basée** sur le code, canonical, clients et docs existants
- ✅ **Pas de simulation** de runs

### Recommandations Finales

#### Recommandation Principale : **Option B (Nouveau prompt LLM-matching)**

**Justification** :
- **Impact métier élevé** : Vrai "LLM gating" pour améliorer la pertinence
- **Architecture propre** : Séparation extraction d'entités / évaluation de pertinence
- **Évolutivité** : Support multi-vertical et personnalisation client
- **ROI acceptable** : +25-50% coût Bedrock pour amélioration qualité significative

#### Plan de Déploiement Recommandé

1. **Phase A (Quick Win)** : Exploiter `lai_relevance_score` existant (1-2 jours)
2. **Phase B (Solution cible)** : Nouveau prompt LLM-matching (1 semaine)
3. **Phase C (Optimisation)** : Préfiltre et batch processing (2-3 jours)

#### Métriques de Succès

- **Qualité** : +20% de précision sur items LAI-strong
- **Coût** : <+50% du budget Bedrock actuel
- **Performance** : <+30% de latence sur le pipeline complet

---

**Ce diagnostic révèle un potentiel d'amélioration significatif en exploitant mieux les capacités LLM pour le matching/scoring, avec un ROI favorable et une architecture évolutive.**