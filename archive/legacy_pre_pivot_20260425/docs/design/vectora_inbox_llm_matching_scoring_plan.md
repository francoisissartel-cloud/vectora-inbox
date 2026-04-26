# Plan Vectora Inbox - LLM Matching/Scoring

**Date** : 2025-12-12  
**Objectif** : Plan détaillé pour introduire un vrai "LLM gating" dans le matching/scoring  
**Scope** : Architecture générique pilotée par client_config + canonical  

---

## 🎯 Vision Cible

### Principe Directeur
Introduire un **prompt de matching/scoring LLM** dédié qui évalue la pertinence contextuelle des items, en complément du matching déterministe existant, dans un système générique configurable par client.

### Architecture Cible
```
Ingestion → Normalisation (Bedrock) → LLM-Matching (Bedrock) → Matching Hybride → Scoring Enrichi → Newsletter
```

**Séparation des responsabilités** :
- **Normalisation** : Extraction d'entités + classification
- **LLM-Matching** : Évaluation de pertinence contextuelle
- **Matching Hybride** : Combinaison logique déterministe + LLM
- **Scoring Enrichi** : Intégration des signaux LLM dans le calcul de score

---

## 📐 Design Détaillé

### 1. Nouveau Prompt LLM-Matching

#### Structure dans `canonical/prompts/global_prompts.yaml`

```yaml
matching:
  domain_relevance_evaluation:
    system_instructions: |
      You are a domain relevance expert for biotech/pharma intelligence.
      Evaluate how relevant news items are to specific technology watch domains.
      Consider the overall context, not just keyword matching.
      Focus on business relevance and strategic importance.
      
    user_template: |
      Evaluate this biotech/pharma item's relevance to watch domains:
      
      ITEM SUMMARY:
      Title: {{item_title}}
      Summary: {{item_summary}}
      Event Type: {{event_type}}
      
      DETECTED ENTITIES:
      - Companies: {{companies_detected}}
      - Molecules/Drugs: {{molecules_detected}}
      - Technologies: {{technologies_detected}}
      - Indications: {{indications_detected}}
      
      WATCH DOMAINS TO EVALUATE:
      {{watch_domains_context}}
      
      For EACH domain above, evaluate:
      1. relevance_score (0.0-1.0): How strategically relevant is this item?
         - 0.0-0.3: Not relevant or tangentially related
         - 0.4-0.6: Moderately relevant, some strategic interest
         - 0.7-0.9: Highly relevant, significant strategic importance
         - 1.0: Critical relevance, major strategic impact
      
      2. is_relevant (true/false): Should this item be included for this domain?
         - true if relevance_score >= 0.4
         - false if relevance_score < 0.4
      
      3. confidence (high/medium/low): Confidence in your evaluation
         - high: Clear indicators and strong context
         - medium: Some indicators but ambiguous context
         - low: Limited information or unclear relevance
      
      4. reasoning (1-2 sentences): Brief explanation of your evaluation
      
      IMPORTANT:
      - Consider business context, not just technical keywords
      - Evaluate strategic importance for the domain
      - Account for company type (pure player vs diversified)
      - Consider event significance (regulatory, partnership, clinical)
      
      RESPONSE FORMAT (JSON only):
      {
        "domain_evaluations": [
          {
            "domain_id": "domain_id_here",
            "relevance_score": 0.85,
            "is_relevant": true,
            "confidence": "high",
            "reasoning": "Brief explanation of relevance assessment"
          }
        ]
      }
      
      Respond with ONLY the JSON, no additional text.
      
    bedrock_config:
      max_tokens: 800
      temperature: 0.1
      anthropic_version: "bedrock-2023-05-31"
```

#### Construction Dynamique du Contexte

**Fonction `_build_watch_domains_context()`** :
```python
def _build_watch_domains_context(watch_domains, canonical_scopes):
    context = ""
    for domain in watch_domains:
        context += f"\n{domain['id']} ({domain['type']}):\n"
        context += f"  Description: {domain.get('description', 'Technology domain')}\n"
        
        # Ajouter exemples d'entités depuis les scopes
        if domain.get('technology_scope'):
            tech_examples = canonical_scopes.get('technologies', {}).get(domain['technology_scope'], [])
            context += f"  Key Technologies: {', '.join(tech_examples[:5])}\n"
        
        if domain.get('company_scope'):
            company_examples = canonical_scopes.get('companies', {}).get(domain['company_scope'], [])
            context += f"  Key Companies: {', '.join(company_examples[:5])}\n"
        
        context += f"  Priority: {domain.get('priority', 'medium')}\n"
    
    return context
```

### 2. Intégration dans le Pipeline

#### Modification de `bedrock_client.py`

**Nouvelle fonction** :
```python
def evaluate_domain_relevance_with_bedrock(
    item: Dict[str, Any],
    watch_domains: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any],
    model_id: str,
    config_bucket: str = None
) -> Dict[str, Any]:
    """
    Évalue la pertinence d'un item pour les watch_domains via LLM.
    
    Args:
        item: Item normalisé avec entités détectées
        watch_domains: Liste des domaines à évaluer
        canonical_scopes: Scopes canonical pour contexte
        model_id: Modèle Bedrock à utiliser
        config_bucket: Bucket S3 de configuration
    
    Returns:
        Dict avec domain_evaluations ajoutées
    """
    # Feature flag pour activer/désactiver
    use_llm_matching = os.environ.get('USE_LLM_MATCHING', 'false').lower() == 'true'
    if not use_llm_matching:
        return item
    
    # Préfiltre pour éviter appels inutiles
    if not _should_call_llm_matching(item):
        return item
    
    # Construire le prompt
    prompt = _build_llm_matching_prompt(item, watch_domains, canonical_scopes, config_bucket)
    
    # Appel Bedrock
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 800,
        "temperature": 0.1,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response_text = _call_bedrock_with_retry(model_id, request_body)
        llm_result = _parse_llm_matching_response(response_text)
        
        # Ajouter les évaluations à l'item
        item['domain_evaluations'] = llm_result.get('domain_evaluations', [])
        item['llm_matching_used'] = True
        
        return item
    
    except Exception as e:
        logger.error(f"Erreur LLM matching: {e}")
        item['llm_matching_used'] = False
        return item
```

**Préfiltre intelligent** :
```python
def _should_call_llm_matching(item: Dict[str, Any]) -> bool:
    """Détermine si l'item mérite un appel LLM-matching."""
    
    # Skip si aucune entité détectée
    total_entities = (
        len(item.get('companies_detected', [])) +
        len(item.get('molecules_detected', [])) +
        len(item.get('technologies_detected', []))
    )
    if total_entities == 0:
        return False
    
    # Skip si signaux anti-LAI évidents
    if item.get('anti_lai_detected', False):
        return False
    
    # Skip si event_type non pertinent
    irrelevant_events = ['financial_results', 'other']
    if item.get('event_type') in irrelevant_events:
        return False
    
    # Skip si LAI relevance très faible (si disponible)
    lai_score = item.get('lai_relevance_score', 5)
    if lai_score < 3:
        return False
    
    return True
```

#### Intégration dans `ingest-normalize`

**Modification du workflow** :
```python
def process_items_with_llm_matching(items, client_config, canonical_scopes):
    """Pipeline enrichi avec LLM-matching."""
    
    # 1. Normalisation existante
    normalized_items = []
    for item in items:
        normalized_item = normalize_item_with_bedrock(
            item_text=f"{item['title']} {item['content']}",
            model_id=NORMALIZATION_MODEL_ID,
            canonical_examples=build_canonical_examples(canonical_scopes),
            config_bucket=CONFIG_BUCKET
        )
        normalized_items.append({**item, **normalized_item})
    
    # 2. LLM-Matching (NOUVEAU)
    watch_domains = client_config.get('watch_domains', [])
    for item in normalized_items:
        item = evaluate_domain_relevance_with_bedrock(
            item=item,
            watch_domains=watch_domains,
            canonical_scopes=canonical_scopes,
            model_id=LLM_MATCHING_MODEL_ID,
            config_bucket=CONFIG_BUCKET
        )
    
    return normalized_items
```

### 3. Matching Hybride

#### Modification de `matcher.py`

**Nouvelle fonction principale** :
```python
def match_items_to_domains_hybrid(
    normalized_items: List[Dict[str, Any]],
    watch_domains: List[Dict[str, Any]],
    canonical_scopes: Dict[str, Any],
    matching_rules: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Matching hybride : déterministe + LLM.
    
    Args:
        normalized_items: Items avec domain_evaluations (si LLM utilisé)
        watch_domains: Watch domains du client
        canonical_scopes: Scopes canonical
        matching_rules: Règles de matching
    
    Returns:
        Items avec matched_domains enrichis
    """
    matching_mode = matching_rules.get('hybrid_matching', {}).get('mode', 'deterministic_or_llm')
    
    for item in normalized_items:
        # 1. Matching déterministe (existant)
        deterministic_matches = _compute_deterministic_matches(
            item, watch_domains, canonical_scopes, matching_rules
        )
        
        # 2. LLM matching (nouveau)
        llm_matches = _compute_llm_matches(item, watch_domains)
        
        # 3. Combinaison selon le mode configuré
        if matching_mode == 'llm_only':
            final_matches = llm_matches
        elif matching_mode == 'deterministic_and_llm':
            # ET logique : item doit matcher les deux systèmes
            final_matches = list(set(deterministic_matches) & set(llm_matches))
        elif matching_mode == 'deterministic_or_llm':
            # OU logique : item matche si au moins un système l'accepte
            final_matches = list(set(deterministic_matches) | set(llm_matches))
        else:  # 'deterministic_only' (fallback)
            final_matches = deterministic_matches
        
        # 4. Annoter l'item
        item['matched_domains'] = final_matches
        item['matching_details'] = {
            'deterministic_matches': deterministic_matches,
            'llm_matches': llm_matches,
            'mode_used': matching_mode,
            'final_matches': final_matches
        }
    
    return normalized_items

def _compute_llm_matches(item: Dict[str, Any], watch_domains: List[Dict[str, Any]]) -> List[str]:
    """Extrait les domaines matchés selon l'évaluation LLM."""
    domain_evaluations = item.get('domain_evaluations', [])
    
    llm_matches = []
    for evaluation in domain_evaluations:
        if evaluation.get('is_relevant', False):
            # Vérifier seuil de confiance si configuré
            confidence = evaluation.get('confidence', 'medium')
            relevance_score = evaluation.get('relevance_score', 0)
            
            # Critères d'acceptation
            if confidence == 'high' or relevance_score >= 0.6:
                llm_matches.append(evaluation['domain_id'])
    
    return llm_matches
```

#### Configuration du Matching Hybride

**Dans `canonical/matching/domain_matching_rules.yaml`** :
```yaml
hybrid_matching:
  mode: "deterministic_or_llm"  # deterministic_only | llm_only | deterministic_and_llm | deterministic_or_llm
  
  llm_matching_config:
    confidence_threshold: "medium"  # low | medium | high
    relevance_threshold: 0.4        # 0.0-1.0
    
    # Poids pour la combinaison
    deterministic_weight: 0.6
    llm_weight: 0.4
```

### 4. Scoring Enrichi

#### Modification de `scorer.py`

**Nouvelle fonction de scoring** :
```python
def compute_score_with_llm_signals(
    item: Dict[str, Any],
    scoring_rules: Dict[str, Any],
    canonical_scopes: Dict[str, Any]
) -> float:
    """
    Calcule le score en intégrant les signaux LLM.
    
    Args:
        item: Item avec domain_evaluations
        scoring_rules: Règles de scoring enrichies
        canonical_scopes: Scopes canonical
    
    Returns:
        Score final (float)
    """
    # Facteurs de base (existants)
    event_type_weights = scoring_rules.get('event_type_weights', {})
    other_factors = scoring_rules.get('other_factors', {})
    
    event_type = item.get('event_type', 'other')
    event_weight = event_type_weights.get(event_type, 1)
    
    # Facteur de récence (existant)
    recency_factor = _compute_recency_factor(
        item.get('date'),
        other_factors.get('recency_decay_half_life_days', 7)
    )
    
    # NOUVEAU : Facteur de pertinence LLM
    llm_relevance_factor = _compute_llm_relevance_factor(
        item.get('domain_evaluations', []),
        scoring_rules.get('llm_scoring', {})
    )
    
    # NOUVEAU : Facteur de confiance LLM
    llm_confidence_bonus = _compute_llm_confidence_bonus(
        item.get('domain_evaluations', []),
        scoring_rules.get('llm_scoring', {})
    )
    
    # Facteurs existants
    source_weight = _compute_source_weight(item, other_factors)
    signal_depth_bonus = _compute_signal_depth_bonus(item, other_factors)
    company_bonus = _compute_company_bonus(item, canonical_scopes, other_factors)
    
    # Formule enrichie
    base_score = event_weight * llm_relevance_factor * recency_factor * source_weight
    final_score = base_score + llm_confidence_bonus + signal_depth_bonus + company_bonus
    
    return max(0, round(final_score, 2))

def _compute_llm_relevance_factor(
    domain_evaluations: List[Dict[str, Any]],
    llm_scoring_config: Dict[str, Any]
) -> float:
    """Calcule le facteur de pertinence basé sur les évaluations LLM."""
    if not domain_evaluations:
        return llm_scoring_config.get('no_llm_evaluation_penalty', 0.5)
    
    # Prendre le meilleur score de pertinence
    max_relevance = max([e.get('relevance_score', 0) for e in domain_evaluations])
    
    # Convertir 0-1 en multiplicateur 0.2-2.0
    if max_relevance >= 0.8:
        return 2.0  # Très pertinent
    elif max_relevance >= 0.6:
        return 1.5  # Pertinent
    elif max_relevance >= 0.4:
        return 1.0  # Modérément pertinent
    else:
        return 0.3  # Peu pertinent

def _compute_llm_confidence_bonus(
    domain_evaluations: List[Dict[str, Any]],
    llm_scoring_config: Dict[str, Any]
) -> float:
    """Calcule le bonus basé sur la confiance des évaluations LLM."""
    if not domain_evaluations:
        return 0
    
    high_confidence_count = len([e for e in domain_evaluations if e.get('confidence') == 'high'])
    medium_confidence_count = len([e for e in domain_evaluations if e.get('confidence') == 'medium'])
    
    high_bonus = llm_scoring_config.get('high_confidence_bonus', 1.0)
    medium_bonus = llm_scoring_config.get('medium_confidence_bonus', 0.5)
    
    return (high_confidence_count * high_bonus) + (medium_confidence_count * medium_bonus)
```

#### Configuration du Scoring LLM

**Dans les règles de scoring** :
```yaml
llm_scoring:
  # Facteurs de pertinence LLM
  no_llm_evaluation_penalty: 0.5
  
  # Bonus de confiance
  high_confidence_bonus: 1.0
  medium_confidence_bonus: 0.5
  low_confidence_bonus: 0.0
  
  # Seuils de pertinence
  high_relevance_threshold: 0.8
  medium_relevance_threshold: 0.6
  low_relevance_threshold: 0.4
```

---

## 🌐 Généralisation Multi-Technologies

### 1. Architecture Générique

#### Configuration par Client

**Structure `client_config/{client_id}.yaml`** :
```yaml
# LAI Weekly
client_id: "lai_weekly_v3"
vertical: "long_acting_injectables"

watch_domains:
  - id: "lai_psychiatry"
    type: "technology"
    description: "Long-acting injectable antipsychotics and CNS treatments"
    technology_scope: "lai_technologies_psychiatry"
    company_scope: "lai_companies_pure_players"
    indication_scope: "psychiatry_indications"
    priority: "high"
    
  - id: "lai_diabetes"
    type: "technology"
    description: "Long-acting injectable diabetes and metabolic treatments"
    technology_scope: "lai_technologies_diabetes"
    company_scope: "lai_companies_hybrid"
    indication_scope: "diabetes_indications"
    priority: "medium"

llm_matching_config:
  mode: "deterministic_or_llm"
  confidence_threshold: "medium"
  relevance_threshold: 0.4
```

#### Support Multi-Vertical

**Oncologie** :
```yaml
client_id: "oncology_weekly"
vertical: "oncology"

watch_domains:
  - id: "car_t_therapy"
    type: "technology"
    description: "CAR-T cell therapy and cellular immunotherapy"
    technology_scope: "car_t_technologies"
    company_scope: "cell_therapy_companies"
    indication_scope: "oncology_indications"
    
  - id: "immunotherapy"
    type: "technology"
    description: "Cancer immunotherapy and checkpoint inhibitors"
    technology_scope: "immunotherapy_technologies"
    company_scope: "immunotherapy_companies"
```

**Cell Therapy** :
```yaml
client_id: "cell_therapy_weekly"
vertical: "cell_therapy"

watch_domains:
  - id: "stem_cell_therapy"
    type: "technology"
    description: "Stem cell therapy and regenerative medicine"
    technology_scope: "stem_cell_technologies"
    
  - id: "gene_therapy"
    type: "technology"
    description: "Gene therapy and genetic engineering"
    technology_scope: "gene_therapy_technologies"
```

### 2. Template Générique du Prompt

**Prompt adaptatif par vertical** :
```yaml
matching:
  domain_relevance_evaluation:
    user_template: |
      Evaluate this {{client_vertical}} item's relevance to watch domains:
      
      ITEM: {{item_summary}}
      ENTITIES: {{detected_entities}}
      
      {{client_vertical_context}}
      
      DOMAINS TO EVALUATE:
      {{watch_domains_context}}
      
      Evaluate each domain for {{client_vertical}} relevance...
```

**Construction dynamique du contexte vertical** :
```python
def _build_vertical_context(client_config, canonical_scopes):
    vertical = client_config.get('vertical', 'biotech')
    
    contexts = {
        'long_acting_injectables': """
        FOCUS: Long-Acting Injectable (LAI) technologies and sustained-release drug delivery.
        KEY CONCEPTS: Extended-release, depot injection, microspheres, PLGA, subcutaneous delivery.
        BUSINESS CONTEXT: Evaluate strategic importance for LAI market and technology development.
        """,
        
        'oncology': """
        FOCUS: Cancer treatment technologies and oncology therapeutics.
        KEY CONCEPTS: Immunotherapy, targeted therapy, precision medicine, biomarkers.
        BUSINESS CONTEXT: Evaluate strategic importance for cancer treatment advancement.
        """,
        
        'cell_therapy': """
        FOCUS: Cellular and gene therapy technologies.
        KEY CONCEPTS: CAR-T, stem cells, gene editing, regenerative medicine.
        BUSINESS CONTEXT: Evaluate strategic importance for cellular therapy development.
        """
    }
    
    return contexts.get(vertical, contexts['long_acting_injectables'])
```

---

## 💰 Coût et Performances

### 1. Estimation Détaillée des Coûts

#### Coûts Actuels (Baseline)

**Run lai_weekly_v3 typique** :
- Items ingérés : ~400
- Items normalisés : ~150 (après filtrage)
- Appels normalisation : ~150
- Coût normalisation : ~$2.50 (Claude Sonnet)
- Appels newsletter : ~1
- Coût newsletter : ~$0.30
- **Total actuel : ~$2.80 par run**

#### Coûts avec LLM-Matching

**Scénario conservateur** (préfiltre efficace) :
- Items pour LLM-matching : ~100 (67% des normalisés)
- Appels LLM-matching : ~100
- Coût LLM-matching : ~$1.50
- **Total avec LLM : ~$4.30 par run (+54%)**

**Scénario pessimiste** (pas de préfiltre) :
- Items pour LLM-matching : ~150 (100% des normalisés)
- Appels LLM-matching : ~150
- Coût LLM-matching : ~$2.25
- **Total avec LLM : ~$5.05 par run (+80%)**

#### Optimisations de Coût

**Batch Processing** :
```python
def batch_llm_matching(items_batch, max_batch_size=5):
    """Traite plusieurs items en un seul appel Bedrock."""
    # 5 items par appel = -80% d'appels
    # Coût réduit : ~$1.50 → ~$0.30
```

**Préfiltre Intelligent** :
```python
def smart_prefilter(item):
    # Skip 30-40% des items non pertinents
    # Économie : ~$0.45-0.60 par run
```

**Seuils Adaptatifs** :
```python
def adaptive_thresholds(item):
    # Skip items avec lai_relevance_score < 4
    # Skip items avec anti_lai_detected = true
    # Économie supplémentaire : ~$0.30 par run
```

### 2. Performances et Throttling

#### Limites Bedrock Actuelles

**us-east-1** (normalisation) :
- Limite : ~100 req/min
- Utilisation actuelle : ~50 req/min
- **Marge : 50 req/min disponibles**

**Avec LLM-matching** :
- Appels supplémentaires : +100 req/min
- **Total : ~150 req/min (DÉPASSEMENT)**

#### Stratégies de Mitigation

**Répartition géographique** :
```python
# Normalisation : us-east-1
# LLM-matching : eu-west-3
# Newsletter : eu-west-3 (existant)
```

**Retry avec Backoff** :
```python
def exponential_backoff_retry(max_retries=5):
    # Délai : 0.5s, 1s, 2s, 4s, 8s
    # Gestion automatique du throttling
```

**Processing Séquentiel** :
```python
def sequential_llm_matching(items):
    # Traiter 1 item à la fois avec délai
    # Éviter les pics de charge
    for item in items:
        result = call_llm_matching(item)
        time.sleep(0.1)  # 100ms entre appels
```

### 3. Monitoring et Alertes

#### Métriques CloudWatch

```python
# Métriques personnalisées
cloudwatch.put_metric_data(
    Namespace='VectoraInbox/LLMMatching',
    MetricData=[
        {
            'MetricName': 'LLMMatchingCalls',
            'Value': llm_calls_count,
            'Unit': 'Count'
        },
        {
            'MetricName': 'LLMMatchingCost',
            'Value': estimated_cost,
            'Unit': 'None'
        },
        {
            'MetricName': 'LLMMatchingLatency',
            'Value': avg_latency_ms,
            'Unit': 'Milliseconds'
        }
    ]
)
```

#### Alertes de Coût

```yaml
# CloudWatch Alarm
LLMMatchingCostAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: VectoraInbox-LLMMatching-HighCost
    MetricName: LLMMatchingCost
    Threshold: 10.0  # $10 par run
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref SNSTopicArn
```

---

## 🚀 Plan de Mise en Œuvre Détaillé

### Phase A : Enrichir le Prompt de Normalisation (OPTION MINIMALE)

**Durée** : 1-2 jours  
**Effort** : Faible  
**Impact** : Moyen  

#### Objectifs
- Exploiter mieux les champs `lai_relevance_score` et `domain_relevance` existants
- Amélioration rapide sans coût supplémentaire
- Validation de l'approche avant investissement plus important

#### Actions Détaillées

**A1 : Modifier le matcher (4h)**
```python
# Dans matcher.py
def match_items_with_lai_relevance(normalized_items, watch_domains, ...):
    for item in normalized_items:
        # Matching déterministe existant
        deterministic_matches = compute_deterministic_matches(item, ...)
        
        # Filtrage par LAI relevance
        lai_score = item.get('lai_relevance_score', 0)
        if lai_score < 5:  # Seuil configurable
            item['matched_domains'] = []  # Rejeter
            continue
        
        # Filtrage par domain_relevance si disponible
        domain_relevance = item.get('domain_relevance', [])
        if domain_relevance:
            relevant_domains = [
                d['domain_id'] for d in domain_relevance 
                if d.get('is_on_domain', False) and d.get('relevance_score', 0) >= 0.5
            ]
            # Intersection avec matching déterministe
            final_matches = list(set(deterministic_matches) & set(relevant_domains))
        else:
            final_matches = deterministic_matches
        
        item['matched_domains'] = final_matches
```

**A2 : Modifier le scorer (4h)**
```python
# Dans scorer.py
def compute_score_with_lai_signals(item, scoring_rules, ...):
    # Score de base existant
    base_score = compute_base_score(item, scoring_rules, ...)
    
    # Bonus LAI relevance
    lai_score = item.get('lai_relevance_score', 0)
    lai_bonus = (lai_score / 10) * scoring_rules.get('lai_relevance_multiplier', 1.5)
    
    # Bonus domain relevance
    domain_bonus = 0
    domain_relevance = item.get('domain_relevance', [])
    if domain_relevance:
        max_domain_score = max([d.get('relevance_score', 0) for d in domain_relevance])
        domain_bonus = max_domain_score * scoring_rules.get('domain_relevance_multiplier', 2.0)
    
    # Pénalité anti-LAI
    anti_lai_penalty = 0
    if item.get('anti_lai_detected', False):
        anti_lai_penalty = scoring_rules.get('anti_lai_penalty', -5.0)
    
    return base_score + lai_bonus + domain_bonus + anti_lai_penalty
```

**A3 : Tests et validation (4h)**
- Dataset de test : 20 items LAI-strong historiques
- Comparaison avant/après sur précision/rappel
- Ajustement des seuils selon les résultats

#### Critères de Succès Phase A
- ✅ +10% de précision sur items LAI-strong
- ✅ Pas de régression sur items LAI-weak
- ✅ Aucun coût Bedrock supplémentaire
- ✅ Temps d'implémentation < 2 jours

### Phase B : Créer un Nouveau Prompt Dédié LLM-Matching (OPTION RECOMMANDÉE)

**Durée** : 5-7 jours  
**Effort** : Élevé  
**Impact** : Élevé  

#### Phase B1 : Design et Implémentation Core (3-4 jours)

**B1.1 : Créer le prompt LLM-matching (1 jour)**
- Ajouter le prompt dans `canonical/prompts/global_prompts.yaml`
- Définir la structure de réponse JSON
- Tester le prompt manuellement sur 5-10 items

**B1.2 : Étendre PromptLoader (0.5 jour)**
```python
# Dans prompts/loader.py
def get_llm_matching_prompt(self, prompt_key='matching.domain_relevance_evaluation'):
    """Charge le prompt LLM-matching depuis YAML."""
    return self.get_prompt(prompt_key)
```

**B1.3 : Implémenter la fonction Bedrock (1 jour)**
```python
# Dans bedrock_client.py
def evaluate_domain_relevance_with_bedrock(item, watch_domains, canonical_scopes, ...):
    # Construction du prompt avec contexte dynamique
    # Appel Bedrock avec retry
    # Parsing de la réponse JSON
    # Intégration dans l'item
```

**B1.4 : Intégrer dans ingest-normalize (0.5 jour)**
```python
# Dans la Lambda ingest-normalize
def enhanced_normalization_pipeline(items, client_config, ...):
    # 1. Normalisation existante
    normalized_items = normalize_items_batch(items, ...)
    
    # 2. LLM-matching (NOUVEAU)
    if os.environ.get('USE_LLM_MATCHING', 'false').lower() == 'true':
        for item in normalized_items:
            item = evaluate_domain_relevance_with_bedrock(item, ...)
    
    return normalized_items
```

**B1.5 : Tests locaux (1 jour)**
- Script de test : `scripts/test_llm_matching_local.py`
- Dataset : 30 items variés (LAI-strong, LAI-weak, LAI-irrelevant)
- Validation structure JSON et cohérence des évaluations

#### Phase B2 : Adapter le Matching (1-2 jours)

**B2.1 : Implémenter le matching hybride (1 jour)**
```python
# Dans matcher.py
def match_items_to_domains_hybrid(normalized_items, watch_domains, ...):
    matching_mode = get_matching_mode(client_config)
    
    for item in normalized_items:
        deterministic_matches = compute_deterministic_matches(item, ...)
        llm_matches = compute_llm_matches(item, ...)
        
        # Combinaison selon le mode
        final_matches = combine_matches(deterministic_matches, llm_matches, matching_mode)
        
        item['matched_domains'] = final_matches
        item['matching_details'] = {
            'deterministic': deterministic_matches,
            'llm': llm_matches,
            'mode': matching_mode
        }
```

**B2.2 : Configuration du matching hybride (0.5 jour)**
- Ajouter config dans `domain_matching_rules.yaml`
- Définir les modes de combinaison
- Paramètres de seuils de confiance

**B2.3 : Tests matching hybride (0.5 jour)**
- Validation des différents modes de combinaison
- Vérification de la cohérence des résultats

#### Phase B3 : Adapter le Scoring (1-2 jours)

**B3.1 : Implémenter le scoring enrichi (1 jour)**
```python
# Dans scorer.py
def compute_score_with_llm_signals(item, scoring_rules, ...):
    # Facteurs de base existants
    base_factors = compute_base_factors(item, ...)
    
    # Nouveaux facteurs LLM
    llm_relevance_factor = compute_llm_relevance_factor(item.get('domain_evaluations', []))
    llm_confidence_bonus = compute_llm_confidence_bonus(item.get('domain_evaluations', []))
    
    # Formule enrichie
    final_score = combine_scoring_factors(base_factors, llm_relevance_factor, llm_confidence_bonus)
    
    return final_score
```

**B3.2 : Configuration du scoring LLM (0.5 jour)**
- Ajouter paramètres dans les règles de scoring
- Définir les poids et bonus LLM
- Seuils de pertinence et confiance

**B3.3 : Tests scoring enrichi (0.5 jour)**
- Validation des nouveaux facteurs de scoring
- Comparaison des scores avant/après

### Phase C : Tests et Validation (2-3 jours)

#### C1 : Dataset de Référence (0.5 jour)

**Items LAI-strong** :
- Nanexa/Moderna partnership (PharmaShell technology)
- UZEDY regulatory approval (Teva antipsychotic)
- MedinCell malaria program (BEPO technology)
- Camurus Buvidal launch (CAM2038)
- Alkermes Aristada updates

**Items LAI-weak** :
- Pfizer quarterly financial results
- Generic biotech hiring announcements
- Non-LAI drug approvals
- Academic research papers (non-commercial)

**Items LAI-irrelevant** :
- Software/IT company news
- Non-pharma biotech (agriculture, industrial)
- Medical device news (non-drug delivery)

#### C2 : Métriques de Validation (1 jour)

**Métriques de qualité** :
```python
def compute_validation_metrics(results, ground_truth):
    # Précision : % d'items pertinents dans les résultats
    precision = len(relevant_retrieved) / len(retrieved)
    
    # Rappel : % d'items pertinents détectés
    recall = len(relevant_retrieved) / len(relevant)
    
    # F1-score : Équilibre précision/rappel
    f1_score = 2 * (precision * recall) / (precision + recall)
    
    # Précision par domaine
    domain_precision = {domain: compute_domain_precision(domain, results) for domain in domains}
    
    return {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'domain_precision': domain_precision
    }
```

**Métriques de coût** :
```python
def compute_cost_metrics(run_stats):
    # Nombre d'appels Bedrock
    normalization_calls = run_stats['normalization_calls']
    llm_matching_calls = run_stats['llm_matching_calls']
    
    # Coût estimé
    normalization_cost = normalization_calls * COST_PER_NORMALIZATION_CALL
    llm_matching_cost = llm_matching_calls * COST_PER_LLM_MATCHING_CALL
    
    # Augmentation vs baseline
    cost_increase_pct = (llm_matching_cost / normalization_cost) * 100
    
    return {
        'total_cost': normalization_cost + llm_matching_cost,
        'cost_increase_pct': cost_increase_pct,
        'calls_per_item': (normalization_calls + llm_matching_calls) / run_stats['items_processed']
    }
```

#### C3 : Tests Comparatifs (1 jour)

**Scénarios de test** :
1. **Baseline** : Matching déterministe seul
2. **Phase A** : Matching avec lai_relevance_score
3. **Phase B** : Matching hybride avec LLM-matching

**Comparaison** :
```python
def run_comparative_test(test_items):
    results = {}
    
    # Test baseline
    results['baseline'] = run_matching_pipeline(test_items, mode='deterministic_only')
    
    # Test Phase A
    results['phase_a'] = run_matching_pipeline(test_items, mode='lai_relevance_enhanced')
    
    # Test Phase B
    results['phase_b'] = run_matching_pipeline(test_items, mode='hybrid_llm_matching')
    
    # Analyse comparative
    comparison = compare_results(results, ground_truth)
    
    return comparison
```

#### C4 : Optimisation des Seuils (0.5 jour)

**Optimisation automatique** :
```python
def optimize_thresholds(validation_data):
    best_f1 = 0
    best_params = {}
    
    # Grid search sur les paramètres clés
    for relevance_threshold in [0.3, 0.4, 0.5, 0.6, 0.7]:
        for confidence_threshold in ['low', 'medium', 'high']:
            params = {
                'relevance_threshold': relevance_threshold,
                'confidence_threshold': confidence_threshold
            }
            
            results = run_validation(validation_data, params)
            f1_score = results['f1_score']
            
            if f1_score > best_f1:
                best_f1 = f1_score
                best_params = params
    
    return best_params, best_f1
```

### Phase D : Déploiement AWS (1 jour)

#### D1 : Préparation du Déploiement (0.5 jour)

**Package Lambda** :
```bash
# Build et package
cd src/lambdas/ingest-normalize
pip install -r requirements.txt -t package/
cp -r ../../vectora_core package/
zip -r ingest-normalize-with-llm-matching.zip package/
```

**Synchronisation Config** :
```bash
# Upload prompts canonicalisés
aws s3 cp canonical/prompts/global_prompts.yaml s3://vectora-inbox-config-dev/canonical/prompts/

# Upload règles de matching
aws s3 cp canonical/matching/domain_matching_rules.yaml s3://vectora-inbox-config-dev/canonical/matching/
```

#### D2 : Déploiement et Configuration (0.5 jour)

**Déploiement Lambda** :
```bash
# Déployer la nouvelle version
aws lambda update-function-code \
  --function-name vectora-inbox-ingest-normalize-dev \
  --zip-file fileb://ingest-normalize-with-llm-matching.zip

# Configurer les variables d'environnement
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-normalize-dev \
  --environment Variables='{
    "USE_CANONICAL_PROMPTS": "true",
    "USE_LLM_MATCHING": "true",
    "LLM_MATCHING_MODEL_ID": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "CONFIG_BUCKET": "vectora-inbox-config-dev"
  }'
```

**Test End-to-End** :
```bash
# Test avec payload minimal
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id": "lai_weekly_v3", "period_days": 1}' \
  --cli-binary-format raw-in-base64-out \
  test-llm-matching-output.json

# Vérifier la réponse
cat test-llm-matching-output.json | jq '.items[0].domain_evaluations'
```

### Phase E : Validation et Optimisation (1-2 jours)

#### E1 : Run Réel et Monitoring (1 jour)

**Run lai_weekly_v3 complet** :
```bash
# Ingestion avec LLM-matching
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id": "lai_weekly_v3", "period_days": 7}' \
  --cli-binary-format raw-in-base64-out \
  ingest-llm-matching-output.json

# Engine et newsletter
aws lambda invoke \
  --function-name vectora-inbox-engine-dev \
  --payload '{"client_id": "lai_weekly_v3", "period_days": 7}' \
  --cli-binary-format raw-in-base64-out \
  engine-llm-matching-output.json
```

**Analyse des résultats** :
```python
def analyze_real_run_results(ingest_output, engine_output):
    # Métriques de performance
    items_processed = len(ingest_output.get('items', []))
    items_with_llm = len([i for i in ingest_output['items'] if i.get('domain_evaluations')])
    items_matched = len([i for i in ingest_output['items'] if i.get('matched_domains')])
    
    # Métriques de coût
    bedrock_calls = ingest_output.get('bedrock_calls', {})
    normalization_calls = bedrock_calls.get('normalization', 0)
    llm_matching_calls = bedrock_calls.get('llm_matching', 0)
    
    # Métriques de qualité
    newsletter_items = len(engine_output.get('selected_items', []))
    lai_strong_items = len([i for i in engine_output['selected_items'] if i.get('lai_relevance_score', 0) >= 8])
    
    return {
        'performance': {
            'items_processed': items_processed,
            'llm_matching_coverage': items_with_llm / items_processed,
            'matching_rate': items_matched / items_processed
        },
        'cost': {
            'normalization_calls': normalization_calls,
            'llm_matching_calls': llm_matching_calls,
            'total_calls': normalization_calls + llm_matching_calls,
            'cost_increase': llm_matching_calls / normalization_calls
        },
        'quality': {
            'newsletter_items': newsletter_items,
            'lai_strong_ratio': lai_strong_items / newsletter_items if newsletter_items > 0 else 0
        }
    }
```

#### E2 : Optimisation Finale (1 jour)

**Ajustement des seuils** :
```python
# Basé sur les résultats du run réel
def adjust_thresholds_based_on_real_run(run_results):
    # Si trop d'items matchés : augmenter seuils
    if run_results['performance']['matching_rate'] > 0.8:
        new_relevance_threshold = 0.6  # Plus strict
        new_confidence_threshold = 'medium'
    
    # Si pas assez d'items LAI-strong : réduire seuils
    elif run_results['quality']['lai_strong_ratio'] < 0.6:
        new_relevance_threshold = 0.4  # Plus permissif
        new_confidence_threshold = 'low'
    
    return {
        'relevance_threshold': new_relevance_threshold,
        'confidence_threshold': new_confidence_threshold
    }
```

**Optimisation du préfiltre** :
```python
def optimize_prefilter_based_on_costs(run_results):
    # Si coût trop élevé : préfiltre plus strict
    if run_results['cost']['cost_increase'] > 0.6:  # +60%
        return {
            'min_lai_relevance_score': 4,  # Plus strict
            'skip_financial_results': True,
            'skip_anti_lai_items': True,
            'min_entities_count': 2
        }
    
    return current_prefilter_config
```

---

## 📋 Livrables et Documentation

### Documentation Technique

1. **`docs/design/vectora_inbox_llm_matching_architecture.md`**
   - Architecture détaillée du système LLM-matching
   - Diagrammes de flux et interactions
   - Spécifications techniques des interfaces

2. **`docs/design/vectora_inbox_llm_matching_prompts.md`**
   - Documentation complète des prompts LLM-matching
   - Exemples d'inputs/outputs
   - Guide de personnalisation par vertical

3. **`docs/operations/vectora_inbox_llm_matching_monitoring.md`**
   - Guide de monitoring et alertes
   - Métriques clés à surveiller
   - Procédures de troubleshooting

### Code et Configuration

1. **Prompts canonicalisés** : `canonical/prompts/global_prompts.yaml`
2. **Règles de matching** : `canonical/matching/domain_matching_rules.yaml`
3. **Configuration clients** : `client_config/{client_id}.yaml`
4. **Code LLM-matching** : `src/vectora_core/llm_matching/`
5. **Tests** : `tests/test_llm_matching.py`

### Scripts et Outils

1. **`scripts/test_llm_matching_local.py`** : Tests locaux
2. **`scripts/validate_llm_matching_quality.py`** : Validation qualité
3. **`scripts/optimize_llm_matching_thresholds.py`** : Optimisation seuils
4. **`scripts/monitor_llm_matching_costs.py`** : Monitoring coûts

---

## 🎯 Critères de Succès

### Métriques de Qualité

- **Précision** : +15-25% vs matching déterministe seul
- **Rappel** : Maintien à >90% pour items LAI-strong
- **F1-score** : >0.75 sur dataset de validation
- **Faux positifs** : <10% d'items non pertinents dans newsletter

### Métriques de Coût

- **Augmentation coût** : <+60% vs baseline actuel
- **Coût par item pertinent** : <$0.05
- **ROI** : Amélioration qualité justifie surcoût

### Métriques Opérationnelles

- **Latence** : <+50% vs pipeline actuel
- **Disponibilité** : >99% (avec fallback déterministe)
- **Monitoring** : Alertes automatiques sur dépassements

### Métriques Métier

- **Satisfaction client** : Feedback positif sur pertinence
- **Réduction bruit** : -20% d'items non pertinents
- **Détection signaux faibles** : +10% d'items pertinents sans keywords explicites

---

**Ce plan fournit une roadmap complète pour introduire un vrai "LLM gating" dans Vectora Inbox, avec une approche progressive, des métriques claires et une architecture évolutive supportant multiple verticaux.**