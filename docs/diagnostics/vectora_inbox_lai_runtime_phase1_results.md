# Vectora Inbox — LAI Runtime Adaptation Phase 1 Results

**Date:** 2025-01-XX  
**Phase:** Phase 1 - Domain Matching Rules Enhancement  
**Status:** ✅ COMPLETED

---

## 1. Executive Summary

Phase 1 a introduit les **technology profiles** dans le système de matching pour exploiter la structure à 7 catégories de `lai_keywords`.

**Changements implémentés:**
- ✅ Ajout de `technology_profiles` dans `domain_matching_rules.yaml`
- ✅ Création de 2 profiles: `technology_complex` (LAI) et `technology_simple` (futur)
- ✅ Annotation de `lai_keywords` avec `_metadata.profile: technology_complex`
- ✅ Documentation complète dans `canonical/matching/README.md`

**Impact attendu:**
- Matching par catégories (core_phrases, technology_terms_high_precision, etc.)
- Distinction pure players vs hybrid companies
- Filtrage des termes génériques et négatifs
- **Aucun changement de code runtime** (Phase 2)

---

## 2. Fichiers Modifiés

### 2.1 `canonical/matching/domain_matching_rules.yaml`

**Ajout de la section `technology_profiles`:**

```yaml
technology_profiles:
  technology_complex:
    description: "Technologies complexes nécessitant plusieurs types de signaux (ex: LAI)"
    signal_requirements:
      high_precision_signals:
        categories: [core_phrases, technology_terms_high_precision]
        min_matches: 1
        weight: 3.0
      supporting_signals:
        categories: [route_admin_terms, interval_patterns]
        min_matches: 1
        weight: 2.0
      context_signals:
        categories: [technology_use]
        min_matches: 0
        weight: 1.0
      excluded_categories: [generic_terms]
      negative_filters:
        categories: [negative_terms]
        action: reject_match
    entity_requirements:
      min_matches: 1
      sources: [company, molecule]
      company_scope_modifiers:
        pure_player_scopes: [lai_companies_pure_players, lai_companies_mvp_core]
        pure_player_rule: high_precision_signals_only
        hybrid_scopes: [lai_companies_hybrid]
        hybrid_rule: high_precision_plus_supporting
    combination_logic: |
      MATCH if:
        (high_precision_signal AND entity) OR
        (supporting_signal AND supporting_signal AND entity) OR
        (high_precision_signal AND pure_player_company)
      REJECT if:
        negative_term detected
  
  technology_simple:
    description: "Technologies simples avec signaux clairs (ex: oral tablets)"
    signal_requirements:
      high_precision_signals:
        categories: [core_phrases]
        min_matches: 1
        weight: 3.0
    entity_requirements:
      min_matches: 1
      sources: [company, molecule]
    combination_logic: |
      MATCH if:
        (high_precision_signal AND entity)
```

**Rationale:**
- **Category-based matching:** Référence des catégories (core_phrases, technology_terms_high_precision) au lieu de keywords individuels
- **Weighted signals:** Différents niveaux de confiance (3.0 pour high_precision, 2.0 pour supporting, 1.0 pour context)
- **Company scope modifiers:** Pure players nécessitent moins de signaux que hybrid companies
- **Negative filtering:** Rejet explicite si negative_terms détectés
- **Excluded categories:** generic_terms ne peuvent plus déclencher de match seuls

### 2.2 `canonical/scopes/technology_scopes.yaml`

**Ajout de `_metadata` à `lai_keywords`:**

```yaml
lai_keywords:
  _metadata:
    profile: technology_complex
    description: "Long-Acting Injectables - requires multiple signal types for matching"
  core_phrases:
    - "long-acting injectable"
    # ... (structure existante inchangée)
```

**Rationale:**
- Lie le scope `lai_keywords` au profile `technology_complex`
- Permet au matcher (Phase 2) de détecter automatiquement le profile à utiliser
- Pas de modification de la structure à 7 catégories (déjà en place)

### 2.3 `canonical/matching/README.md`

**Ajout de documentation complète sur les technology_profiles:**
- Structure d'un profile
- Profiles disponibles (technology_complex, technology_simple)
- Utilisation dans les scopes (_metadata)
- Exemples de matching avec profiles

---

## 3. Logique de Matching Définie

### 3.1 Profile `technology_complex` (LAI)

**Signaux haute précision (weight: 3.0):**
- `core_phrases`: "long-acting injectable", "extended-release injection", etc.
- `technology_terms_high_precision`: "PLGA microspheres", "Fc fusion", "PASylation", etc.

**Signaux de support (weight: 2.0):**
- `route_admin_terms`: "subcutaneous", "intramuscular", "intravitreal", etc.
- `interval_patterns`: "q4w", "q8w", "once-monthly", "6-month", etc.

**Signaux de contexte (weight: 1.0):**
- `technology_use`: "injectable", "depot", "microsphere", etc.

**Catégories exclues:**
- `generic_terms`: "drug delivery system", "liposomes", "PEG", "subcutaneous" (seul), etc.

**Filtres négatifs:**
- `negative_terms`: "oral tablet", "topical cream", "transdermal patch", etc.

### 3.2 Règles de Combinaison

**Pour pure players (MedinCell, Camurus, DelSiTech, Nanexa, Peptron):**
```
MATCH if:
  high_precision_signal (1+) AND pure_player_company
```
**Exemple:** "MedinCell announces long-acting injectable" → MATCH ✅

**Pour hybrid companies (Pfizer, AbbVie, Novo Nordisk, etc.):**
```
MATCH if:
  (high_precision_signal (1+) AND supporting_signal (1+) AND hybrid_company) OR
  (high_precision_signal (2+) AND hybrid_company)
```
**Exemple:** "Pfizer develops extended-release injectable using PLGA microspheres" → MATCH ✅  
**Contre-exemple:** "Pfizer announces subcutaneous injection" → NO MATCH ❌ (signal insuffisant)

**Rejet systématique:**
```
REJECT if:
  negative_term detected (oral tablet, topical cream, etc.)
```
**Exemple:** "Camurus develops oral tablet formulation" → NO MATCH ❌

### 3.3 Exemples de Matching Attendus

| Item | Company Type | Signals Detected | Expected Result |
|------|--------------|------------------|-----------------|
| "MedinCell announces long-acting injectable formulation" | Pure player | core_phrases (1) | ✅ MATCH (high confidence) |
| "Camurus subcutaneous injection q4w" | Pure player | route_admin (1) + interval (1) | ✅ MATCH (supporting signals) |
| "Pfizer quarterly earnings report" | Hybrid | none | ❌ NO MATCH |
| "Pfizer subcutaneous injection" | Hybrid | route_admin (1) | ❌ NO MATCH (insufficient) |
| "AbbVie extended-release injectable PLGA" | Hybrid | core_phrases (1) + tech_high_precision (1) | ✅ MATCH (multiple high signals) |
| "Takeda drug delivery system" | Hybrid | generic_terms (1) | ❌ NO MATCH (excluded category) |
| "MedinCell oral tablet" | Pure player | negative_terms (1) | ❌ NO MATCH (negative filter) |

---

## 4. Backward Compatibility

### 4.1 Scopes Sans Profile

**Comportement:** Les scopes technologiques sans `_metadata.profile` continuent d'utiliser la règle `technology` classique (simple intersection).

**Exemple:**
```yaml
oncology_keywords:
  # Pas de _metadata → utilise règle technology classique
  - "chemotherapy"
  - "immunotherapy"
  # ...
```

**Impact:** Aucun changement pour les autres verticaux (si existants).

### 4.2 Règles Existantes

**Règles conservées sans modification:**
- `technology` (règle simple)
- `indication`
- `regulatory`
- `default`

**Impact:** Aucun breaking change pour les domaines existants.

---

## 5. Validation

### 5.1 YAML Syntax

**Test:** Chargement des fichiers YAML modifiés

```powershell
# Test de syntaxe YAML
python -c "import yaml; yaml.safe_load(open('canonical/matching/domain_matching_rules.yaml'))"
python -c "import yaml; yaml.safe_load(open('canonical/scopes/technology_scopes.yaml'))"
```

**Résultat:** ✅ Aucune erreur de syntaxe

### 5.2 Structure Validation

**Vérifications:**
- ✅ `technology_profiles` contient `technology_complex` et `technology_simple`
- ✅ `technology_complex` contient toutes les sections requises (signal_requirements, entity_requirements, combination_logic)
- ✅ `lai_keywords._metadata.profile` référence `technology_complex`
- ✅ Catégories référencées existent dans `lai_keywords` (core_phrases, technology_terms_high_precision, etc.)

**Résultat:** ✅ Structure valide

---

## 6. Prochaines Étapes (Phase 2)

### 6.1 Objectif Phase 2

Adapter `matcher.py` pour interpréter et appliquer les technology_profiles.

### 6.2 Fonctions à Implémenter

**Nouvelles fonctions:**
1. `_load_technology_profile()`: Charger le profile depuis domain_matching_rules
2. `_categorize_technology_keywords()`: Mapper keywords détectés vers catégories
3. `_evaluate_technology_profile_match()`: Évaluer si item satisfait le profile
4. `_detect_negative_terms()`: Détecter présence de negative_terms
5. `_identify_company_scope_type()`: Identifier si company est pure_player ou hybrid

**Fonction modifiée:**
- `match_items_to_domains()`: Intégrer logique profile-aware

### 6.3 Structure `matching_details`

**À ajouter à chaque item matché:**
```python
item['matching_details'] = {
    'domain_id': 'tech_lai_ecosystem',
    'rule_applied': 'technology_complex',
    'categories_matched': {
        'core_phrases': ['long-acting injectable'],
        'route_admin_terms': ['subcutaneous'],
        'technology_use': []
    },
    'signals_used': {
        'high_precision': 1,
        'supporting': 1,
        'context': 0
    },
    'scopes_hit': {
        'companies': ['MedinCell'],
        'company_scope': 'lai_companies_pure_players'
    },
    'negative_terms_detected': [],
    'match_confidence': 'high'
}
```

### 6.4 Tests à Créer

**Unit tests:**
- `test_load_technology_profile()`
- `test_categorize_technology_keywords()`
- `test_evaluate_technology_profile_match()`
- `test_detect_negative_terms()`

**Integration tests:**
- Test end-to-end avec corpus LAI (50 items)
- Vérifier matching_details populated
- Vérifier pure_player vs hybrid distinction

---

## 7. Métriques Phase 1

### 7.1 Changements Quantitatifs

| Métrique | Avant | Après |
|----------|-------|-------|
| Sections dans domain_matching_rules.yaml | 4 | 5 (+technology_profiles) |
| Profiles définis | 0 | 2 (technology_complex, technology_simple) |
| Scopes avec _metadata | 0 | 1 (lai_keywords) |
| Lignes de documentation ajoutées | 0 | ~80 (README.md) |

### 7.2 Complexité

**Règle technology classique:**
- 1 dimension technology (binaire: présent ou non)
- 1 dimension entity (binaire: présent ou non)
- Logique: technology AND entity

**Profile technology_complex:**
- 7 catégories de signaux (core_phrases, technology_terms_high_precision, route_admin_terms, interval_patterns, technology_use, generic_terms, negative_terms)
- 3 niveaux de poids (3.0, 2.0, 1.0)
- 2 types de companies (pure_player, hybrid)
- Logique: combinaisons multiples avec seuils différenciés

**Impact:** Complexité accrue mais nécessaire pour atteindre 80% de précision LAI.

---

## 8. Risques & Mitigations

### 8.1 Risque: Over-Engineering

**Description:** Les profiles deviennent trop complexes à maintenir

**Mitigation:**
- ✅ Documentation exhaustive dans README.md
- ✅ Exemples concrets de matching
- ✅ Validation YAML automatique
- ✅ Profiles limités à 2 pour l'instant (complex, simple)

### 8.2 Risque: Backward Compatibility

**Description:** Casser les domaines existants

**Mitigation:**
- ✅ Scopes sans _metadata utilisent règle classique
- ✅ Règles existantes (technology, indication, regulatory) inchangées
- ✅ Tests de régression à effectuer en Phase 2

### 8.3 Risque: Performance

**Description:** Matching par catégories plus lent

**Mitigation:**
- Phase 2: profiler le code
- Optimiser les lookups de catégories (dict au lieu de listes)
- Monitorer temps d'exécution Lambda

---

## 9. Conclusion Phase 1

### 9.1 Objectifs Atteints

✅ **Technology profiles définis** dans domain_matching_rules.yaml  
✅ **Profile technology_complex** créé avec logique 7 catégories  
✅ **Profile technology_simple** créé pour futur usage  
✅ **lai_keywords annoté** avec profile reference  
✅ **Documentation complète** dans README.md  
✅ **Validation YAML** réussie  
✅ **Backward compatibility** préservée

### 9.2 Prêt pour Phase 2

**Status:** ✅ READY

Les règles de matching sont maintenant définies de manière déclarative. Phase 2 peut commencer l'implémentation dans `matcher.py`.

**Durée Phase 1:** ~1 heure (estimation: 3 heures)

---

**Document Status:** ✅ PHASE 1 COMPLETED  
**Next Action:** START PHASE 2 (Matching Engine Adaptation)
