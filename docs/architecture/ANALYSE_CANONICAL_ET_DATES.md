# Analyse: Matière Canonical et Gestion des Dates

**Date**: 2026-01-31  
**Contexte**: Questions sur effective_date et complexité définition LAI

---

## 🗓️ Question 1: Gestion des Dates (effective_date)

### Oui, effective_date est Toujours dans la Proposition

**Dans l'architecture proposée**:

```
Appel 1: Normalisation Générique
├─ Extraction date publication ✅
├─ Date confidence (0.0-1.0) ✅
└─ Output: extracted_date + date_confidence

Post-Normalisation (dans normalizer.py):
├─ Calcul effective_date:
│   if extracted_date AND confidence > 0.7:
│       effective_date = extracted_date (Bedrock)
│   else:
│       effective_date = published_at (fallback)
├─ Ajout date_metadata pour traçabilité
└─ effective_date utilisé partout (scoring, newsletter)
```

### Rôle de la Lambda Normalisation sur les Dates

**Ce que Bedrock fait** (Appel 1):
- Cherche dates dans le texte ("27 January 2026", "December 9, 2025")
- Retourne format ISO: "2026-01-27"
- Donne confiance: 0.95 (certain), 0.5 (incertain), 0.0 (pas trouvé)

**Ce que normalizer.py fait** (après Bedrock):
```python
# Dans _enrich_item_with_normalization()
extracted_date = bedrock_result.get('extracted_date')
date_confidence = bedrock_result.get('date_confidence', 0.0)
published_at = original_item.get('published_at', '')

# Logique de sélection (UNIQUE)
if extracted_date and date_confidence > 0.7:
    effective_date = extracted_date
    date_source = 'bedrock'
else:
    effective_date = published_at[:10] if published_at else None
    date_source = 'published_at'

# Ajouter au niveau racine de l'item
enriched_item['effective_date'] = effective_date
enriched_item['date_metadata'] = {
    'source': date_source,
    'bedrock_date': extracted_date,
    'bedrock_confidence': date_confidence,
    'published_at': published_at
}
```

**Ensuite**:
- Scorer utilise `item['effective_date']` pour recency
- Assembler utilise `item['effective_date']` pour affichage
- **1 seule logique, 1 seul endroit**

### Réponse: effective_date Reste Identique

✅ **Aucun changement** sur la gestion des dates dans la proposition  
✅ **Toujours calculé** dans normalizer.py après Bedrock  
✅ **Toujours utilisé** partout (scoring, newsletter)

---

## 📚 Question 2: Analyse de la Matière Canonical LAI

### Inventaire de la Matière Actuelle

**Fichiers définissant "LAI"**:

1. **`canonical/scopes/technology_scopes.yaml`** (lai_keywords)
   - core_phrases: 13 expressions
   - technology_terms_high_precision: 60+ termes
   - technology_use: 10 termes
   - route_admin_terms: 13 routes
   - interval_patterns: 13 patterns
   - generic_terms: 13 termes
   - negative_terms: 11 exclusions
   - **Total: ~130 éléments**

2. **`canonical/scopes/company_scopes.yaml`**
   - lai_companies_mvp_core: Pure players LAI
   - lai_companies_hybrid: Big pharma avec LAI
   - lai_companies_global: Tous acteurs LAI
   - **Total: ~50-100 entreprises**

3. **`canonical/scopes/molecule_scopes.yaml`**
   - lai_molecules_global: Molécules LAI actives
   - **Total: ~30-50 molécules**

4. **`canonical/scopes/trademark_scopes.yaml`**
   - lai_trademarks_global: Marques LAI
   - **Total: ~20-30 trademarks**

5. **`canonical/imports/LAI_RATIONALE.md`**
   - Définition conceptuelle LAI
   - Différenciation LAI vs oral
   - Différenciation LAI vs LAI
   - Topics narratifs

6. **`canonical/prompts/normalization/lai_normalization.yaml`**
   - Références aux scopes ci-dessus
   - Instructions extraction

7. **`canonical/prompts/matching/lai_matching.yaml`**
   - Critères de matching
   - Références aux scopes

8. **`canonical/scoring/scoring_rules.yaml`**
   - Règles de scoring
   - Bonus/pénalités

---

## 🎯 Mon Avis: Trop Complexe et Fragmenté

### Problèmes Identifiés

#### 1. Trop de Fichiers pour 1 Concept

**8 fichiers** pour définir "LAI" → Confusion, maintenance difficile

**Exemple**:
- `technology_scopes.yaml` définit technologies LAI
- `LAI_RATIONALE.md` définit concept LAI
- `lai_normalization.yaml` référence les scopes
- `lai_matching.yaml` re-référence les scopes
- `scoring_rules.yaml` définit bonus

**Problème**: Information dispersée, pas de vue d'ensemble

#### 2. Granularité Excessive dans technology_scopes.yaml

**130 éléments** dans lai_keywords avec 7 sous-catégories:
- core_phrases (13)
- technology_terms_high_precision (60+)
- technology_use (10)
- route_admin_terms (13)
- interval_patterns (13)
- generic_terms (13)
- negative_terms (11)

**Problème**: 
- Bedrock doit digérer 130 éléments dans le prompt
- Risque de confusion entre catégories
- Maintenance complexe (où ajouter un nouveau terme ?)

#### 3. Redondance entre Fichiers

**Exemple**:
- `technology_scopes.yaml` liste "long-acting injectable"
- `LAI_RATIONALE.md` explique "long-acting injectable"
- `lai_normalization.yaml` demande de détecter "long-acting injectable"

**Problème**: Même information répétée 3 fois

#### 4. Prompt Bedrock Surchargé

**Prompt actuel** (lai_normalization.yaml):
```yaml
LAI TECHNOLOGY FOCUS:
{{ref:lai_keywords.core_phrases}}
{{ref:lai_keywords.technology_terms_high_precision}}

EXAMPLES OF ENTITIES:
{{ref:lai_companies_global}}
{{ref:lai_molecules_global}}
{{ref:lai_trademarks_global}}

EXCLUDE:
{{ref:lai_keywords.negative_terms}}
```

**Résultat**: Prompt de ~2000 tokens juste pour les références

**Problème**: 
- Coût élevé
- Risque de confusion pour Bedrock
- Difficile de savoir ce qui influence vraiment le matching

---

## 💡 Recommandations: Simplifier Drastiquement

### Principe: "Less is More"

**Bedrock n'a PAS besoin de 130 termes pour comprendre "LAI"**

### Architecture Simplifiée Proposée

#### Fichier Unique: `canonical/domains/lai_domain_definition.yaml`

```yaml
# Définition complète du domaine LAI en 1 fichier
domain_id: lai
domain_name: "Long-Acting Injectables"

# Définition conceptuelle (pour Bedrock)
definition: |
  Long-Acting Injectables (LAI) are pharmaceutical formulations designed to 
  provide sustained drug release over extended periods (weeks to months) 
  after a single injection, improving patient adherence and therapeutic outcomes.

# Signaux FORTS (suffisants seuls pour matching)
strong_signals:
  core_technologies:
    - "long-acting injectable"
    - "extended-release injectable"
    - "depot injection"
    - "sustained-release injectable"
  
  pure_player_companies:
    scope: lai_companies_mvp_core
    # MedinCell, Camurus, DelSiTech, Nanexa, Peptron
  
  trademarks:
    scope: lai_trademarks_global
    # UZEDY®, BUVIDAL®, etc.

# Signaux MOYENS (nécessitent combinaison)
medium_signals:
  technology_families:
    - "microspheres"
    - "in-situ depot"
    - "hydrogel"
    - "PEGylation"
  
  dosing_intervals:
    - "once-monthly"
    - "once every 3 months"
    - "q4w"
    - "q12w"
  
  hybrid_companies:
    scope: lai_companies_hybrid
    # J&J, Teva, AbbVie avec activité LAI

# Signaux FAIBLES (contexte uniquement)
weak_signals:
  routes:
    - "subcutaneous"
    - "intramuscular"
  
  molecules:
    scope: lai_molecules_global

# Exclusions (anti-LAI)
exclusions:
  - "oral tablet"
  - "oral capsule"
  - "transdermal patch"
  - "nasal spray"

# Règles de matching
matching_rules:
  - rule: "1 strong signal → match automatique"
  - rule: "2+ medium signals → match probable"
  - rule: "3+ weak signals → match possible"
  - rule: "1 exclusion → reject"

# Scoring (intégré)
scoring:
  event_type_base:
    partnership: 60
    regulatory: 70
    clinical_update: 50
  
  entity_boosts:
    pure_player: +25
    trademark: +20
    key_molecule: +15
    hybrid_company: +10
  
  recency_boosts:
    0-7_days: +10
    8-30_days: +5
    91+_days: -10
```

**Avantages**:
- ✅ **1 fichier** = 1 vue complète du domaine
- ✅ **~50 éléments** vs 130 (simplification 60%)
- ✅ **Hiérarchie claire**: strong/medium/weak signals
- ✅ **Règles explicites**: Bedrock sait comment combiner
- ✅ **Scoring intégré**: Pas de fichier séparé
- ✅ **Maintenance facile**: Tout au même endroit

### Prompt Bedrock Simplifié

```yaml
# lai_domain_scoring.yaml (NOUVEAU)
user_template: |
  Evaluate this item for LAI domain relevance and score it.
  
  ITEM:
  {{item_summary}}
  Entities: {{item_entities}}
  Event: {{item_event_type}}
  Date: {{item_date}}
  
  LAI DOMAIN DEFINITION:
  {{ref:lai_domain_definition}}
  
  TASK:
  1. Identify signals (strong/medium/weak)
  2. Apply matching rules
  3. Calculate score using scoring criteria
  4. Explain reasoning
  
  RESPONSE (JSON):
  {
    "is_relevant": true/false,
    "score": 0-100,
    "confidence": "high/medium/low",
    "signals_detected": {
      "strong": ["pure_player_company: MedinCell"],
      "medium": ["technology: microspheres"],
      "weak": ["route: subcutaneous"]
    },
    "score_breakdown": {
      "base": 60,
      "pure_player_boost": 25,
      "recency_boost": 5,
      "total": 90
    },
    "reasoning": "Pure player MedinCell + microsphere technology"
  }
```

**Avantages**:
- ✅ **Prompt ~500 tokens** vs 2000 (réduction 75%)
- ✅ **1 seule référence**: {{ref:lai_domain_definition}}
- ✅ **Bedrock comprend hiérarchie** (strong/medium/weak)
- ✅ **Traçabilité**: Signaux détectés explicites

---

## 🎯 Réponse à Tes Questions

### 1. Y a-t-il trop de fichiers canonical ?

**OUI, clairement trop**:
- 8 fichiers pour définir "LAI"
- Information dispersée
- Redondance entre fichiers
- Maintenance complexe

**Recommandation**: **1 fichier par domaine** (`lai_domain_definition.yaml`)

### 2. La matière est-elle trop complexe ?

**OUI, trop granulaire**:
- 130 éléments dans technology_scopes
- 7 sous-catégories
- Bedrock n'a pas besoin de tout ça

**Recommandation**: **Simplifier à ~50 éléments** avec hiérarchie claire (strong/medium/weak)

### 3. Peut-on continuer avec cette matière ?

**NON, il faut simplifier**:
- Prompt Bedrock surchargé (2000 tokens)
- Risque de confusion
- Difficile de savoir ce qui influence vraiment

**Recommandation**: **Refondre en 1 fichier** avec hiérarchie de signaux

### 4. L'architecture proposée est-elle compatible ?

**OUI, parfaitement compatible**:
- Architecture proposée = 1 appel Bedrock pour domain scoring
- Fichier `lai_domain_definition.yaml` = Input parfait pour cet appel
- Simplification matière = Prompt plus efficace

---

## 📋 Plan d'Action Recommandé

### Étape 1: Consolider la Matière (1 semaine)

1. Créer `canonical/domains/lai_domain_definition.yaml`
2. Migrer contenu depuis 8 fichiers actuels
3. Simplifier à ~50 éléments essentiels
4. Hiérarchiser: strong/medium/weak signals

### Étape 2: Tester Nouveau Prompt (1 semaine)

1. Créer `lai_domain_scoring.yaml` avec référence unique
2. Tester sur 20 items LAI connus
3. Comparer avec ancien système
4. Ajuster selon feedback

### Étape 3: Valider et Basculer (1 semaine)

1. Validation humaine sur 50 items
2. Corrélation >0.9 avec ancien système
3. Basculement progressif
4. Suppression anciens fichiers

**Durée totale**: 3 semaines

---

## 🎓 Conclusion

### Sur les Dates

✅ **effective_date reste identique** dans l'architecture proposée  
✅ **Calculé dans normalizer.py** après Bedrock  
✅ **Utilisé partout** (scoring, newsletter)

### Sur la Matière Canonical

❌ **Trop complexe actuellement**: 8 fichiers, 130 éléments, 2000 tokens  
✅ **Simplification nécessaire**: 1 fichier, ~50 éléments, 500 tokens  
✅ **Compatible avec architecture proposée**: Parfaitement aligné  
✅ **Bénéfices**: Maintenance facile, prompt efficace, traçabilité claire

### Recommandation Finale

**Adopter l'architecture proposée + Simplifier matière canonical en parallèle**

**Ordre**:
1. Simplifier matière canonical (3 semaines)
2. Implémenter architecture Bedrock repensée (6 semaines)
3. Valider E2E avec matière simplifiée

**Résultat**: Système cohérent, simple, pilotable, scalable
