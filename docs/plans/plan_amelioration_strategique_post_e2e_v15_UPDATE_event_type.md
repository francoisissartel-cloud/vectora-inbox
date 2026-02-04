# Mise à Jour Plan - Problème 4: MedinCell Malaria Grant

**Date**: 2026-02-03  
**Découverte**: Le fichier `event_type_patterns.yaml` existe et définit les patterns d'événements

---

## 🔍 ANALYSE APPROFONDIE

### Fichier event_type_patterns.yaml

**Localisation**: `canonical/events/event_type_patterns.yaml`

**Contenu actuel pour "partnership"** (ligne 48-82):

```yaml
partnership:
  label: "Partnership / Deal"
  description: >
    Collaborations, licensing agreements, co-development deals, strategic alliances,
    option agreements, research partnerships.
  typical_sources:
    - press_corporate
    - press_sector
  title_keywords:
    - "partnership"
    - "collaboration"
    - "licensing agreement"
    - "license agreement"
    - "license and option agreement"
    - "strategic alliance"
    - "co-development"
    - "joint venture"
    - "option agreement"
    - "research collaboration"
    - "exclusive license"
    - "non-exclusive license"
    - "distribution agreement"
    - "commercialization agreement"
    - "announces deal"
    - "signs agreement"
    - "enters into agreement"
  body_keywords:
    - "upfront payment"
    - "milestone payments"
    - "royalties"
    - "development rights"
    - "commercialization rights"
    - "territory"
    - "exclusive rights"
    - "option to license"
    - "co-promote"
  negative_keywords:
    - "acquisition"
    - "merger"
```

**Observation**: ❌ **"grant" et "funding" ne sont PAS dans les keywords partnership**

---

## ❓ QUESTION CRITIQUE: Ce fichier est-il utilisé?

### Hypothèse 1: Fichier NON utilisé (probable)

**Indices**:
1. Le prompt `generic_normalization.yaml` ne référence PAS ce fichier
2. Le prompt demande à Bedrock de classifier "manuellement":
   ```yaml
   3. EVENT CLASSIFICATION
      - Classify into ONE primary type:
        * partnership (collaborations, licensing, M&A)
   ```
3. Aucune référence `{{ref:event_type_patterns}}` dans les prompts

**Conclusion**: Le fichier `event_type_patterns.yaml` est probablement **documentaire** mais **non utilisé** dans le workflow actuel.

### Hypothèse 2: Fichier utilisé dans Lambda (peu probable)

**Vérification nécessaire**: Chercher dans `src_v2/lambdas/` si ce fichier est chargé

---

## ✅ SOLUTION DOUBLE

### Solution A: Modifier event_type_patterns.yaml (si utilisé)

**Fichier**: `canonical/events/event_type_patterns.yaml`

**Modifications**:

```yaml
# AVANT (ligne 58-75)
  title_keywords:
    - "partnership"
    - "collaboration"
    - "licensing agreement"
    - "license agreement"
    - "license and option agreement"
    - "strategic alliance"
    - "co-development"
    - "joint venture"
    - "option agreement"
    - "research collaboration"
    - "exclusive license"
    - "non-exclusive license"
    - "distribution agreement"
    - "commercialization agreement"
    - "announces deal"
    - "signs agreement"
    - "enters into agreement"

# APRÈS
  title_keywords:
    - "partnership"
    - "collaboration"
    - "licensing agreement"
    - "license agreement"
    - "license and option agreement"
    - "strategic alliance"
    - "co-development"
    - "joint venture"
    - "option agreement"
    - "research collaboration"
    - "exclusive license"
    - "non-exclusive license"
    - "distribution agreement"
    - "commercialization agreement"
    - "announces deal"
    - "signs agreement"
    - "enters into agreement"
    # Funding & Grants (ajout 2026-02-03)
    - "grant"
    - "awarded grant"
    - "receives grant"
    - "funding"
    - "awarded funding"
    - "receives funding"
    - "research grant"
    - "development grant"
```

**ET modifier description**:

```yaml
# AVANT (ligne 50-52)
  description: >
    Collaborations, licensing agreements, co-development deals, strategic alliances,
    option agreements, research partnerships.

# APRÈS
  description: >
    Collaborations, licensing agreements, co-development deals, strategic alliances,
    option agreements, research partnerships, grants, and funding agreements.
```

---

### Solution B: Modifier generic_normalization.yaml (recommandé)

**Fichier**: `canonical/prompts/normalization/generic_normalization.yaml`

**Modifications** (ligne 38-44):

```yaml
# AVANT
  3. EVENT CLASSIFICATION
     - Classify into ONE primary type:
       * partnership (collaborations, licensing, M&A)
       * regulatory (approvals, submissions, designations)
       * clinical_update (trial results, enrollments, milestones)
       * corporate_move (leadership, strategy, restructuring)
       * financial_results (earnings, funding, investments)
       * other (if none of above fit)

# APRÈS
  3. EVENT CLASSIFICATION
     - Classify into ONE primary type:
       * partnership (collaborations, licensing, M&A, grants, funding, research agreements)
       * regulatory (approvals, submissions, designations)
       * clinical_update (trial results, enrollments, milestones)
       * corporate_move (leadership appointments, strategy, restructuring)
       * financial_results (quarterly earnings, annual reports, financial calendars)
       * other (if none of above fit)
     
     CRITICAL DISTINCTIONS:
     - Grant/funding for R&D or projects → partnership (NOT financial_results)
     - Quarterly earnings report → financial_results
     - Leadership appointment → corporate_move
     - Manufacturing facility announcement → corporate_move
     
     EXAMPLES:
     - "Company awarded $5M grant for malaria research" → partnership
     - "Company receives funding from foundation" → partnership
     - "Company reports Q3 earnings" → financial_results
     - "Company raises $50M in Series B" → financial_results
```

---

## 🎯 RECOMMANDATION

### Approche Recommandée: **Solution B (Modifier generic_normalization.yaml)**

**Raisons**:

1. **Certitude**: Le prompt `generic_normalization.yaml` est **définitivement utilisé** (confirmé par les tests V15)

2. **Contrôle**: Bedrock reçoit les instructions directement dans le prompt

3. **Clarté**: Exemples explicites évitent les ambiguïtés

4. **Rapidité**: Pas besoin de vérifier si `event_type_patterns.yaml` est chargé dans le code

### Approche Complémentaire: **Solution A (Modifier event_type_patterns.yaml)**

**À faire AUSSI** pour:
- Cohérence documentaire
- Usage futur potentiel
- Référence pour développeurs

---

## 📝 PLAN D'ACTION RÉVISÉ

### Action 2.2 (RÉVISÉE): Améliorer Classification Event Type

**Fichiers à modifier**:

1. **`canonical/prompts/normalization/generic_normalization.yaml`** (PRIORITÉ 1)
   - Ajouter "grants, funding" à partnership
   - Ajouter section CRITICAL DISTINCTIONS
   - Ajouter EXAMPLES

2. **`canonical/events/event_type_patterns.yaml`** (PRIORITÉ 2)
   - Ajouter keywords "grant", "funding" à partnership
   - Mettre à jour description

**Durée**: 30 min (inchangé)

**Test**:
```bash
# Relancer normalisation sur item MedinCell malaria grant
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v16

# Vérifier dans items_normalized.json:
# - event_type: "partnership" (au lieu de "financial_results")
# - Puis vérifier scoring: score ≥60 (rule_7 appliquée)
```

---

## ✅ VALIDATION

### Critère de Succès

**Item**: "Medincell Awarded New Grant to Fight Malaria"

**Avant (V15)**:
- event_type: "financial_results" (ou "other")
- Score: 0 (rejeté par rule_5)

**Après (V16)**:
- event_type: "partnership" ✅
- Score: ≥60 ✅ (rule_7: pure_player + partnership)
- Reasoning: "MedinCell pure player + partnership event → auto-match"

---

## 📊 IMPACT

### Sur le Workflow

1. **Normalisation**: Bedrock classifie mieux les grants/funding
2. **Scoring**: Rule_7 s'applique correctement
3. **Résultat**: Pure players LAI captent tous leurs partnerships (grants inclus)

### Sur les Métriques V16

- Items relevant: +1 (MedinCell malaria grant)
- Faux négatifs: -1
- Précision pure players: +100% (tous les partnerships matchés)

---

**Mise à jour créée**: 2026-02-03  
**Statut**: ✅ SOLUTION IDENTIFIÉE - PRÊT POUR IMPLÉMENTATION
