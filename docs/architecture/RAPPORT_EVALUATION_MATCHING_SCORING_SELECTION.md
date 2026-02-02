# Rapport d'Évaluation Architecturale
## Système de Matching, Scoring et Sélection - Vectora Inbox

**Date**: 2026-01-31  
**Version**: 1.0  
**Client de référence**: lai_weekly_v7  
**Évaluateur**: Architecte Cloud AWS

---

## 🎯 Résumé Exécutif

### Vision du Moteur
**Ambition**: Moteur générique de veille sectorielle capable de s'adapter à différentes verticales (LAI, siRNA, cell therapy, gene therapy) via des configurations canonical pilotables par un humain.

### Verdict Global
**🟡 ARCHITECTURE SOLIDE AVEC OPTIMISATIONS NÉCESSAIRES**

**Points forts**:
- ✅ Séparation claire des responsabilités (matching → scoring → sélection)
- ✅ Configuration pilotée par canonical (scopes, prompts)
- ✅ Moteur générique avec spécialisation LAI réussie
- ✅ Traçabilité complète des décisions

**Points d'amélioration**:
- ⚠️ Complexité excessive dans le matching (2 systèmes parallèles)
- ⚠️ Scoring avec trop de règles imbriquées
- ⚠️ Manque de cohérence entre matching Bedrock et scoring déterministe
- ⚠️ Sélection avec logique de distribution fragile

---

## 🤖 Cartographie des Appels Bedrock

### Vue d'Ensemble du Workflow

```
Workflow E2E: ingest-v2 → normalize-score-v2 → newsletter-v2
                 ↓              ↓                    ↓
            Bedrock: 0      Bedrock: 2N          Bedrock: M
                            (N items)            (M sections)
```

### Lambda 1: ingest-v2

**Appels Bedrock**: **AUCUN**

**Rôle**: Ingestion brute
- Récupération contenus externes (RSS, APIs)
- Parsing HTML/XML
- Stockage S3 `ingested/`

**Fichiers impliqués**:
- `src_v2/vectora_core/ingest/source_fetcher.py`
- `src_v2/vectora_core/ingest/content_parser.py`

---

### Lambda 2: normalize-score-v2

**Appels Bedrock**: **2 appels par item** (normalisation + matching)

#### Appel 1: Normalisation (1 par item)

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonction**: `BedrockNormalizationClient.normalize_item()`

**Prompt**: `canonical/prompts/normalization/lai_normalization.yaml`

**Rôle**:
- Extraction entités (companies, molecules, technologies, trademarks)
- Classification événement (partnership, regulatory, clinical_update, etc.)
- Génération résumé (2-3 phrases)
- Extraction date publication
- Évaluation pertinence LAI (score 0-10)
- Détection anti-LAI
- Détection contexte pure player

**Input**: Texte brut (title + content)

**Output**:
```json
{
  "summary": "...",
  "extracted_date": "2025-12-09",
  "date_confidence": 0.95,
  "event_type": "partnership",
  "companies_detected": ["MedinCell", "Teva"],
  "molecules_detected": ["Olanzapine"],
  "technologies_detected": ["Extended-Release Injectable"],
  "trademarks_detected": ["UZEDY®"],
  "indications_detected": ["Schizophrenia"],
  "lai_relevance_score": 8,
  "anti_lai_detected": false,
  "pure_player_context": true
}
```

**Coût moyen**: ~$0.003 par appel

---

#### Appel 2: Matching (1 par item)

**Fichier**: `src_v2/vectora_core/normalization/bedrock_matcher.py`

**Fonction**: `match_item_to_domains_bedrock()`

**Prompt**: `canonical/prompts/matching/lai_matching.yaml`

**Rôle**:
- Évaluation pertinence pour chaque domaine de veille
- Matching sémantique (comprend nuances)
- Scoring de pertinence (0.0-1.0)
- Niveau de confiance (high/medium/low)
- Justification du matching

**Input**: Item normalisé + contexte domaines

**Output**:
```json
{
  "domain_evaluations": [
    {
      "domain_id": "tech_lai_ecosystem",
      "is_relevant": true,
      "relevance_score": 0.85,
      "confidence": "high",
      "reasoning": "Extended-release injectable formulation highly relevant to LAI domain",
      "matched_entities": {
        "companies": ["MedinCell"],
        "technologies": ["Extended-Release Injectable"]
      }
    }
  ]
}
```

**Coût moyen**: ~$0.004 par appel

---

#### Scoring: AUCUN Appel Bedrock

**Fichier**: `src_v2/vectora_core/normalization/scorer.py`

**Rôle**: Scoring 100% déterministe
- Utilise résultats normalisation + matching
- Applique règles métier (15+ règles)
- Calcule bonus/pénalités
- Génère score final (0-50)

**Pas d'appel Bedrock** - Tout est calculé localement

---

### Lambda 3: newsletter-v2

**Appels Bedrock**: **Variable selon sections** (génération éditoriale)

#### Appel 3: Génération Éditoriale (1 par section ou global)

**Fichier**: `src_v2/vectora_core/newsletter/editorial.py` (à implémenter)

**Prompt**: `canonical/prompts/editorial/lai_editorial.yaml`

**Rôle**:
- Génération TL;DR
- Génération introduction
- Synthèse par section (optionnel)
- Ton éditorial adapté

**Input**: Items sélectionnés par section

**Output**:
```json
{
  "tldr": "This week: 2 major regulatory approvals...",
  "introduction": "The LAI sector continues its momentum...",
  "section_summaries": {
    "regulatory_updates": "Key developments include..."
  }
}
```

**Coût moyen**: ~$0.005 par appel

**Note**: Actuellement non implémenté - Newsletter générée sans Bedrock

---

### Sélection: AUCUN Appel Bedrock

**Fichier**: `src_v2/vectora_core/newsletter/selector.py`

**Rôle**: Sélection 100% déterministe
- Filtrage par matching
- Déduplication
- Distribution en sections
- Trimming intelligent

**Pas d'appel Bedrock** - Tout est calculé localement

---

## 📊 Synthèse des Appels Bedrock

### Par Lambda

| Lambda | Appels Bedrock | Rôle |
|--------|----------------|------|
| **ingest-v2** | 0 | Ingestion brute uniquement |
| **normalize-score-v2** | 2N (N items) | Normalisation + Matching |
| **newsletter-v2** | M (sections) | Génération éditoriale (optionnel) |

### Workflow Complet (Exemple: 15 items)

**Scénario actuel (lai_weekly_v7)**:
- Ingest: 0 appels
- Normalize-Score: 30 appels (15 items × 2)
  - 15 appels normalisation
  - 15 appels matching
- Newsletter: 0 appels (génération éditoriale non implémentée)
- **Total: 30 appels Bedrock**

**Coût estimé**:
- Normalisation: 15 × $0.003 = $0.045
- Matching: 15 × $0.004 = $0.060
- **Total: ~$0.105 par run**

**Temps estimé**:
- Normalisation: 15 × 5s = 75s
- Matching: 15 × 5s = 75s
- **Total: ~150s (2.5 min) pour Bedrock**

---

### Scalabilité des Appels

**Formule**: `Total Bedrock Calls = 2 × N items + M sections`

**Limites identifiées**:
- **50 items**: 100 appels → ~8 min → OK
- **100 items**: 200 appels → ~17 min → Timeout Lambda (15 min)
- **Solution**: Parallélisation (max_workers=3-5)

**Avec parallélisation (max_workers=5)**:
- 100 items: 200 appels → ~4 min → OK
- 200 items: 400 appels → ~8 min → OK

---

### Points Clés

1. ✅ **Bedrock concentré dans normalize-score-v2** (100% des appels actuels)
2. ✅ **Scoring et sélection 100% déterministes** (pas de Bedrock)
3. ✅ **2 appels par item** (normalisation + matching)
4. ⚠️ **Séquentiel actuellement** (max_workers=1)
5. ⚠️ **Génération éditoriale non implémentée** (newsletter-v2)

---

## 📊 Analyse Détaillée par Composant

### 1. MATCHING - Détermination de la Pertinence

#### 1.1 Architecture Actuelle

**Fichiers impliqués**:
- `normalizer.py` (orchestration)
- `bedrock_matcher.py` (matching sémantique Bedrock)
- `matcher.py` (matching déterministe - LEGACY)

**Flux actuel**:
```
Item normalisé → Bedrock Matching → Seuils configurés → Domaines matchés
```

#### 1.2 Fonctionnement

**Appels Bedrock**:
- **1 appel par item** pour matching sémantique
- Prompt: `canonical/prompts/matching/lai_matching.yaml`
- Évalue la pertinence pour chaque domaine de veille
- Retourne: `domain_evaluations` avec scores 0.0-1.0

**Configuration pilotée**:
```yaml
# Dans lai_weekly_v7.yaml
matching_config:
  min_domain_score: 0.25  # Seuil global
  domain_type_thresholds:
    technology: 0.30      # Plus strict pour tech
```

**Résultat**:
```json
{
  "matched_domains": ["tech_lai_ecosystem"],
  "domain_relevance": {
    "tech_lai_ecosystem": {
      "score": 0.85,
      "confidence": "high",
      "reasoning": "Extended-release injectable...",
      "matched_entities": {...}
    }
  }
}
```

#### 1.3 Principes Directeurs

✅ **Points forts**:
1. **Matching sémantique Bedrock** - Comprend le contexte au-delà des mots-clés
2. **Seuils configurables** - Ajustables sans redéploiement
3. **Traçabilité** - Reasoning explicite pour chaque décision
4. **Généricité** - Prompts adaptables à d'autres verticales

⚠️ **Problèmes identifiés**:
1. **Double système** - `bedrock_matcher.py` ET `matcher.py` coexistent (confusion)
2. **Manque de validation** - Pas de vérification anti-hallucination post-matching
3. **Seuils arbitraires** - min_domain_score=0.25 sans justification métier
4. **Pas de fallback** - Si Bedrock échoue, item perdu

#### 1.4 Partis Pris Architecturaux

**Choix 1: Bedrock pour matching sémantique**
- ✅ Avantage: Comprend nuances ("pure player context")
- ❌ Inconvénient: Coût, latence, dépendance externe

**Choix 2: Matching par domaine (vs matching binaire)**
- ✅ Avantage: Granularité, multi-domaines possibles
- ❌ Inconvénient: Complexité si 10+ domaines

**Choix 3: Seuils configurables**
- ✅ Avantage: Ajustable par client
- ❌ Inconvénient: Nécessite expertise pour calibrer

---

### 2. SCORING - Calcul de la Pertinence

#### 2.1 Architecture Actuelle

**Fichier impliqué**:
- `scorer.py` (logique complète de scoring)

**Flux actuel**:
```
Item matché → Score de base (event_type) → Facteurs multiplicatifs → Bonus → Pénalités → Score final
```

#### 2.2 Fonctionnement

**Formule de scoring**:
```python
weighted_base = base_score * domain_relevance_factor * recency_factor
raw_score = weighted_base + total_bonus + total_penalty
final_score = max(0, min(50, raw_score * scoring_mode_factor))
```

**Appels Bedrock**: **AUCUN** (scoring 100% déterministe)

**Configuration pilotée**:
```yaml
# Dans lai_weekly_v7.yaml
scoring_config:
  event_type_weight_overrides:
    partnership: 8
    clinical_update: 6
    regulatory: 7
  
  client_specific_bonuses:
    pure_player_companies:
      scope: "lai_companies_mvp_core"
      bonus: 5.0
    trademark_mentions:
      bonus: 4.0
```

#### 2.3 Composants du Score

**1. Score de base (event_type)**:
- Partnership: 8.0
- Regulatory: 7.0
- Clinical: 6.0
- Other: 2.0

**2. Facteur de pertinence domaine** (0.05-1.0):
```python
# Utilise les résultats du matching Bedrock
avg_relevance = 0.6 * score + 0.3 * confidence + trademark_boost
```

**3. Facteur de recency** (0.5-1.0):
- <24h: 1.0
- 1 semaine: 0.95
- 1 mois: 0.88
- 3 mois: 0.75
- 6+ mois: 0.5

**4. Bonus LAI** (0-10 points):
- Pure player: +5.0
- Trademark: +4.0
- Molécule clé: +2.5
- Technologie LAI: +1.0-2.0
- LAI relevance score élevé: +2.5

**5. Pénalités** (-5 à 0):
- Anti-LAI détecté: -5.0
- LAI score faible: -3.0
- Âge >6 mois: -2.0
- Pas d'entités: -2.0

#### 2.4 Principes Directeurs

✅ **Points forts**:
1. **Déterministe** - Reproductible, testable, debuggable
2. **Transparent** - score_breakdown détaillé
3. **Configurable** - Bonus/pénalités ajustables
4. **Métier-driven** - Reflète l'expertise pharma (pure players, trademarks)

⚠️ **Problèmes identifiés**:
1. **Complexité excessive** - 15+ règles imbriquées difficiles à maintenir
2. **Incohérence avec matching** - Utilise `domain_relevance_factor` mais recalcule tout
3. **Calibration manuelle** - Bonus/pénalités sans validation empirique
4. **Pas de machine learning** - Impossible d'apprendre des feedbacks humains
5. **Dates problématiques** - Extraction dates Bedrock pas fiable (v7 en test)

#### 2.5 Partis Pris Architecturaux

**Choix 1: Scoring déterministe (vs ML)**
- ✅ Avantage: Explicable, contrôlable, pas de training
- ❌ Inconvénient: Pas d'amélioration automatique

**Choix 2: Bonus additifs (vs multiplicatifs)**
- ✅ Avantage: Prévisible, linéaire
- ❌ Inconvénient: Peut créer des scores aberrants (cumul de bonus)

**Choix 3: Plafonnement à 50**
- ✅ Avantage: Évite les outliers
- ❌ Inconvénient: Arbitraire, peut masquer des signaux exceptionnels

---

### 3. SÉLECTION - Choix des Items Newsletter

#### 3.1 Architecture Actuelle

**Fichiers impliqués**:
- `selector.py` (logique complète de sélection)
- `assembler.py` (formatage Markdown/JSON)

**Flux actuel**:
```
Items scorés → Filtrage (matched only) → Déduplication → Distribution sections → Trimming → Newsletter
```

#### 3.2 Fonctionnement

**Étapes de sélection**:

**1. Filtrage par matching**:
```python
matched_items = [item for item in items 
                 if item['matching_results']['matched_domains']]
```

**2. Déduplication**:
- Signature: `(companies, molecules, indications, event_type, title_hash)`
- Stratégie: Garder meilleur score ou événement critique

**3. Distribution en sections**:
```yaml
# Stratégie: specialized_with_fallback
sections:
  - id: regulatory_updates
    filter_event_types: [regulatory]
    max_items: 6
    priority: 1
  
  - id: partnerships_deals
    filter_event_types: [partnership, corporate_move]
    max_items: 4
    priority: 2
  
  - id: others
    filter_event_types: ["*"]
    max_items: 8
    priority: 999  # Filet de sécurité
```

**4. Trimming intelligent**:
- Préserver événements critiques
- Compléter avec meilleurs scores
- Respecter `max_items_total: 20`

#### 3.3 Principes Directeurs

✅ **Points forts**:
1. **Déduplication intelligente** - Évite les doublons
2. **Sections spécialisées** - Structure éditoriale claire
3. **Filet de sécurité** - Section "others" pour items orphelins
4. **Préservation événements critiques** - Logique métier

⚠️ **Problèmes identifiés**:
1. **Distribution fragile** - Tous les items finissent en "others" (bug v4)
2. **Logique event_type complexe** - Filtres pas toujours respectés
3. **Pas de diversité forcée** - Peut avoir 10 items d'une seule source
4. **Trimming brutal** - Peut perdre des signaux importants

#### 3.4 Partis Pris Architecturaux

**Choix 1: Distribution par event_type (vs par score)**
- ✅ Avantage: Structure éditoriale cohérente
- ❌ Inconvénient: Peut créer des sections vides

**Choix 2: Déduplication par signature (vs ML similarity)**
- ✅ Avantage: Rapide, déterministe
- ❌ Inconvénient: Peut manquer des doublons subtils

**Choix 3: Trimming avec préservation critiques**
- ✅ Avantage: Garantit les signaux forts
- ❌ Inconvénient: Peut sacrifier la diversité

---

## 🔍 Analyse Transversale

### Cohérence du Système

#### ✅ Points de Cohérence

1. **Configuration centralisée** - Tout dans `lai_weekly_v7.yaml`
2. **Canonical comme source de vérité** - Scopes réutilisés partout
3. **Traçabilité E2E** - Chaque décision documentée
4. **Généricité validée** - Architecture LAI transposable à d'autres verticales

#### ⚠️ Incohérences Identifiées

1. **Matching vs Scoring**:
   - Matching Bedrock retourne `confidence: "high"` (string)
   - Scorer attend un float → Mapping hardcodé nécessaire
   - **Impact**: Fragilité, risque d'erreur

2. **Dates**:
   - Bedrock extrait `extracted_date` (v7)
   - Scorer utilise `effective_date` (fallback sur `published_at`)
   - Assembler utilise `effective_date` pour affichage
   - **Impact**: 3 logiques différentes, confusion

3. **Scores multiples**:
   - `lai_relevance_score` (Bedrock, 0-10)
   - `final_score` (Scorer, 0-50)
   - `effective_score` (Selector, calculé à la volée)
   - **Impact**: Quelle métrique fait foi ?

4. **Event types**:
   - Bedrock classifie en `event_type`
   - Selector filtre par `filter_event_types`
   - Pas de validation que les types matchent
   - **Impact**: Sections vides si types divergent

### Scalabilité

#### ✅ Scalable

1. **Ajout de clients** - Copier `lai_weekly_v7.yaml`, ajuster scopes
2. **Ajout de domaines** - Ajouter dans `watch_domains`
3. **Ajout de sources** - Modifier `source_bouquets_enabled`

#### ⚠️ Limites de Scalabilité

1. **Nombre de domaines** - Matching Bedrock linéaire (1 appel × N domaines)
   - **Limite**: ~10 domaines max avant timeout
   
2. **Volume d'items** - Scoring séquentiel
   - **Limite**: ~100 items max en <15min
   
3. **Complexité des règles** - Scorer avec 15+ règles
   - **Limite**: Maintenance difficile au-delà de 20 règles

### Pilotabilité Humaine

#### ✅ Facilement Ajustable

1. **Seuils de matching** - `min_domain_score: 0.25` → 0.30
2. **Bonus scoring** - `pure_player_bonus: 5.0` → 6.0
3. **Structure newsletter** - `max_items: 6` → 8
4. **Prompts Bedrock** - Éditer YAML, sync S3

#### ⚠️ Difficile à Ajuster

1. **Formule de scoring** - Nécessite comprendre 15+ règles imbriquées
2. **Logique de déduplication** - Signature hardcodée
3. **Distribution sections** - Logique `specialized_with_fallback` complexe
4. **Calibration empirique** - Pas d'outil pour tester impact des changements

---

## 🎯 Recommandations Stratégiques

### Priorité 1: SIMPLIFIER LE SCORING (Semaine 1-2)

**Problème**: 15+ règles imbriquées, difficile à maintenir et calibrer

**Solution proposée**: **Scoring en 3 niveaux**

```python
# Niveau 1: Score de base (event_type + matching)
base_score = event_type_weight * domain_relevance_score

# Niveau 2: Multiplicateurs métier (pure player, trademark)
business_multiplier = 1.0
if is_pure_player: business_multiplier *= 1.5
if has_trademark: business_multiplier *= 1.3

# Niveau 3: Ajustements temporels
temporal_factor = recency_factor * (1 - age_penalty)

# Score final
final_score = base_score * business_multiplier * temporal_factor
```

**Avantages**:
- ✅ 3 niveaux vs 15 règles
- ✅ Multiplicatif (effets composés naturels)
- ✅ Facile à expliquer et ajuster
- ✅ Pas de plafonnement arbitraire

**Effort**: 2-3 jours de refactoring + tests

---

### Priorité 2: UNIFIER MATCHING (Semaine 2-3)

**Problème**: 2 systèmes de matching coexistent (`bedrock_matcher.py` + `matcher.py`)

**Solution proposée**: **Supprimer `matcher.py` (legacy)**

```python
# Garder uniquement bedrock_matcher.py
# Ajouter fallback déterministe si Bedrock échoue

def match_item_to_domains(item, domains, config):
    try:
        # Matching Bedrock (prioritaire)
        return bedrock_matcher.match(item, domains, config)
    except BedrockError:
        # Fallback: matching par entités
        return deterministic_fallback_match(item, domains)
```

**Avantages**:
- ✅ 1 seul système, pas de confusion
- ✅ Fallback pour résilience
- ✅ Code plus simple (-500 lignes)

**Effort**: 1-2 jours de refactoring

---

### Priorité 3: COHÉRENCE DES DATES (Semaine 3)

**Problème**: 3 logiques différentes pour les dates

**Solution proposée**: **Date unique `effective_date`**

```python
# Dans normalizer.py (après Bedrock)
effective_date = (
    bedrock_result['extracted_date'] if confidence > 0.7
    else item['published_at']
)
item['effective_date'] = effective_date  # Champ unique

# Partout ailleurs: utiliser item['effective_date']
```

**Avantages**:
- ✅ 1 seule source de vérité
- ✅ Logique centralisée
- ✅ Pas de confusion

**Effort**: 1 jour de refactoring

---

### Priorité 4: OUTIL DE CALIBRATION (Mois 1)

**Problème**: Ajuster les paramètres nécessite tests E2E manuels

**Solution proposée**: **Script de simulation**

```bash
# Simuler l'impact d'un changement de paramètre
python scripts/tools/simulate_scoring.py \
  --config lai_weekly_v7.yaml \
  --param "pure_player_bonus" \
  --values "3.0,4.0,5.0,6.0" \
  --input .tmp/curated_items.json \
  --output .tmp/simulation_results.json
```

**Fonctionnalités**:
- Tester plusieurs valeurs de paramètres
- Comparer distributions de scores
- Identifier items impactés
- Générer rapport visuel

**Avantages**:
- ✅ Calibration data-driven
- ✅ Pas de déploiement pour tester
- ✅ Feedback rapide

**Effort**: 3-5 jours de développement

---

### Priorité 5: VALIDATION ANTI-HALLUCINATION (Mois 1)

**Problème**: Bedrock peut inventer des entités (cas Drug Delivery Conference v4)

**Solution proposée**: **Validation post-Bedrock**

```python
def validate_bedrock_entities(bedrock_result, original_text):
    validated = {}
    
    for entity_type, entities in bedrock_result['entities'].items():
        validated[entity_type] = [
            entity for entity in entities
            if entity_appears_in_text(entity, original_text)
        ]
    
    # Log des hallucinations détectées
    hallucinations = set(entities) - set(validated[entity_type])
    if hallucinations:
        logger.warning(f"Hallucinations: {hallucinations}")
    
    return validated
```

**Avantages**:
- ✅ Filtre les faux positifs
- ✅ Améliore la précision
- ✅ Traçabilité des hallucinations

**Effort**: 1-2 jours (déjà partiellement implémenté dans `normalizer.py`)

---

## 📋 Choix Stratégiques à Faire

### Choix 1: Scoring Déterministe vs ML

**Option A: Garder déterministe (recommandé court terme)**
- ✅ Explicable, contrôlable
- ✅ Pas de training data nécessaire
- ❌ Pas d'amélioration automatique

**Option B: Introduire ML (moyen terme)**
- ✅ Apprend des feedbacks humains
- ✅ S'améliore avec le temps
- ❌ Nécessite 100+ exemples labellisés
- ❌ Moins explicable

**Recommandation**: **Option A** pour 6-12 mois, puis évaluer Option B si volume suffisant

---

### Choix 2: Matching Multi-Domaines vs Domaine Unique

**Option A: Multi-domaines (actuel)**
- ✅ Flexibilité
- ❌ Complexité (item peut matcher 3+ domaines)

**Option B: Domaine unique (simplifié)**
- ✅ Simplicité
- ❌ Perte de granularité

**Recommandation**: **Option A** mais limiter à 3 domaines max par client

---

### Choix 3: Bedrock pour Tout vs Hybride

**Option A: Bedrock pour matching + normalisation (actuel)**
- ✅ Cohérence
- ❌ Coût, latence

**Option B: Bedrock normalisation only, matching déterministe**
- ✅ Coût réduit (-50%)
- ❌ Perte de nuance sémantique

**Recommandation**: **Option A** pour LAI (haute valeur), Option B pour verticales à plus gros volume

---

## 🎯 Plan d'Action Recommandé

### Phase 1: Stabilisation (Semaines 1-3)

**Objectif**: Corriger les incohérences critiques

1. ✅ Unifier matching (supprimer `matcher.py`)
2. ✅ Simplifier scoring (3 niveaux)
3. ✅ Cohérence dates (`effective_date`)
4. ✅ Validation anti-hallucination

**Livrable**: Architecture V2.1 stable et cohérente

---

### Phase 2: Pilotabilité (Mois 1)

**Objectif**: Faciliter l'ajustement des paramètres

1. ✅ Outil de simulation scoring
2. ✅ Dashboard de métriques (Grafana/CloudWatch)
3. ✅ Documentation des paramètres ajustables
4. ✅ Tests E2E automatisés

**Livrable**: Système ajustable sans expertise technique

---

### Phase 3: Scalabilité (Mois 2-3)

**Objectif**: Préparer l'ajout de nouvelles verticales

1. ✅ Parallélisation Bedrock (max_workers=3)
2. ✅ Cache Bedrock pour items similaires
3. ✅ Optimisation prompts (tokens réduits)
4. ✅ Tests de charge (100+ items)

**Livrable**: Système capable de gérer 3-5 clients simultanés

---

## 📊 Métriques de Succès

### Métriques Techniques

1. **Cohérence**: 0 incohérences entre composants
2. **Performance**: <10min pour 50 items
3. **Coût**: <$0.50 par run
4. **Fiabilité**: >95% succès Bedrock

### Métriques Qualité

1. **Précision matching**: >90% (validation humaine)
2. **Pertinence scores**: Corrélation >0.8 avec jugement humain
3. **Distribution sections**: <30% items en "others"
4. **Hallucinations**: <5% des entités

### Métriques Pilotabilité

1. **Temps ajustement paramètre**: <5min (sans redéploiement)
2. **Feedback loop**: <1h (changement → test → validation)
3. **Documentation**: 100% paramètres documentés
4. **Simulation**: Tester 10 valeurs en <2min

---

## 🎓 Conclusion

### Ce qui Fonctionne Bien

1. ✅ **Architecture modulaire** - Séparation claire matching/scoring/sélection
2. ✅ **Configuration pilotée** - Canonical comme source de vérité
3. ✅ **Généricité validée** - LAI transposable à d'autres verticales
4. ✅ **Traçabilité** - Chaque décision documentée

### Ce qui Nécessite Amélioration

1. ⚠️ **Complexité scoring** - 15+ règles → 3 niveaux
2. ⚠️ **Incohérences** - Dates, scores multiples, confidence mapping
3. ⚠️ **Pilotabilité** - Manque d'outils de simulation
4. ⚠️ **Scalabilité** - Limites à 10 domaines, 100 items

### Recommandation Finale

**Le système est BIEN CONSTRUIT dans ses fondations mais TROP COMPLEXE dans son exécution.**

**Action recommandée**: Simplifier avant d'étendre à d'autres verticales.

**Timeline**: 3 semaines de refactoring pour atteindre l'état optimal.

---

**Prochaine étape**: Valider les priorités avec vous et créer un plan d'exécution détaillé.
