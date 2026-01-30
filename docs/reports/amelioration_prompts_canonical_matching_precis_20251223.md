# Amélioration des Prompts Canonical pour Matching Précis - Vectora Inbox
**Date d'analyse** : 2025-12-23  
**Objectif** : Simplifier et améliorer la précision du matching en restant générique et pilotable par configuration

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Problème Identifié
Le prompt de matching actuel est devenu **trop complexe et hardcodé**, avec des règles spécifiques qui devraient être **génériques et pilotables par configuration**. Le taux de matching de 80% (vs 50% attendu) indique une sur-permissivité due à des bidouillages successifs.

### Principe Directeur
**"Simplicité + Configuration > Complexité + Hardcoding"**

Les règles métier doivent être dans les fichiers canonical, pas dans les prompts Bedrock.

---

## 📊 ANALYSE DES PROBLÈMES ACTUELS

### 1. Prompt Bedrock Trop Complexe

**Problème dans `canonical/prompts/global_prompts.yaml`** :
```yaml
# PROBLÉMATIQUE : Règles hardcodées dans le prompt
LAI TECHNOLOGY FOCUS:
Detect these LAI (Long-Acting Injectable) technologies ONLY if explicitly mentioned:
- Extended-Release Injectable
- Long-Acting Injectable
- Three-Month Injectable      # NOUVEAU - hardcodé
- Extended Protection         # NOUVEAU pour malaria - hardcodé
```

**Impact** :
- Règles métier mélangées avec instructions Bedrock
- Difficile à maintenir et ajuster
- Bidouillages successifs (malaria grant)

### 2. Contexte Pure Player Hardcodé

**Problème actuel** :
```yaml
# Dans le prompt
"Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?"
```

**Impact** :
- Contourne les règles de matching strictes
- Génère des faux positifs (nominations, finances)
- Logique métier dans le prompt au lieu de la configuration

### 3. Event Types Mal Utilisés

**Problème identifié** :
- `corporate_move: 1` (nominations) → devrait être 0
- `financial_results: 0` (rapports financiers) → devrait être 0
- Mais ces règles ne sont pas appliquées correctement

**Cause** : Les event types sont classifiés mais pas utilisés pour filtrer

### 4. Fichier `event_type_patterns.yaml` Sous-Utilisé

**Constat** : Le fichier existe mais n'est **PAS utilisé** pour le matching
```yaml
# Dans event_type_patterns.yaml - INUTILISÉ
partnership:
  title_keywords:
    - "partnership"
    - "license and option agreement"  # Pattern Nanexa/Moderna
    - "grant"                         # SOLUTION pour malaria
```

---

## 🔧 SOLUTIONS PROPOSÉES

### 1. Simplifier le Prompt Bedrock

**Objectif** : Prompt générique focalisé sur l'extraction, pas sur les règles métier

**Nouveau prompt simplifié** :
```yaml
normalization:
  lai_default:
    user_template: |
      Analyze this biotech/pharma news item and extract structured information.

      CRITICAL: Only extract entities that are EXPLICITLY mentioned in the text.
      Do not invent, infer, or hallucinate entities not present.

      TEXT TO ANALYZE:
      {{item_text}}

      EXAMPLES OF ENTITIES TO DETECT:
      - Companies: {{companies_examples}}
      - Molecules/Drugs: {{molecules_examples}}
      - Technologies: {{technologies_examples}}

      TASK:
      1. Generate a concise summary (2-3 sentences)
      2. Classify the event type among: clinical_update, partnership, regulatory, corporate_move, financial_results, other
      3. Extract ALL pharmaceutical/biotech company names mentioned
      4. Extract ALL drug/molecule names mentioned
      5. Extract ALL technology keywords mentioned
      6. Extract ALL trademark names mentioned
      7. Extract ALL therapeutic indications mentioned
      8. Evaluate LAI relevance (0-10 score)

      RESPONSE FORMAT (JSON only):
      {
        "summary": "...",
        "event_type": "...",
        "companies_detected": ["...", "..."],
        "molecules_detected": ["...", "..."],
        "technologies_detected": ["...", "..."],
        "trademarks_detected": ["...", "..."],
        "indications_detected": ["...", "..."],
        "lai_relevance_score": 0
      }

      Respond with ONLY the JSON, no additional text.
```

**Changements** :
- ❌ Suppression des termes LAI hardcodés
- ❌ Suppression du contexte pure player
- ❌ Suppression des règles de classification spécifiques
- ✅ Focus sur l'extraction pure d'entités
- ✅ Classification event_type simple

### 2. Utiliser `event_type_patterns.yaml` pour le Matching

**Objectif** : Règles métier dans la configuration, pas dans le code

**Amélioration du fichier `event_type_patterns.yaml`** :
```yaml
# Ajout de règles de matching par event_type
event_types:
  partnership:
    label: "Partnership / Deal"
    # Patterns existants...
    matching_rules:
      pure_player_auto_match: true        # Pure players matchent automatiquement
      hybrid_requires_signals: true       # Hybrid companies besoin signaux
      min_lai_relevance: 3                # Score LAI minimum
      
  regulatory:
    label: "Regulatory Event"
    matching_rules:
      pure_player_auto_match: true
      hybrid_requires_signals: false      # Regulatory important même sans signaux
      min_lai_relevance: 5
      
  corporate_move:
    label: "Corporate / Strategic Move"
    matching_rules:
      auto_exclude: true                  # Exclusion automatique
      reason: "HR/corporate noise"
      
  financial_results:
    label: "Financial Results"
    matching_rules:
      auto_exclude: true                  # Exclusion automatique
      reason: "Financial noise"
```

**Usage dans le code** :
```python
# Dans vectora_core/normalization/matcher.py
def should_match_item(item, domain, canonical_scopes):
    event_type = item.get('event_type')
    event_rules = canonical_scopes.get('event_type_patterns', {}).get(event_type, {}).get('matching_rules', {})
    
    # Exclusion automatique
    if event_rules.get('auto_exclude', False):
        return False, event_rules.get('reason', 'Excluded by event type')
    
    # Règles par type de company
    company = get_company_from_item(item)
    if is_pure_player(company, canonical_scopes):
        if event_rules.get('pure_player_auto_match', False):
            return True, 'Pure player auto-match'
    
    # Règles standard
    min_lai_relevance = event_rules.get('min_lai_relevance', 0)
    if item.get('lai_relevance_score', 0) < min_lai_relevance:
        return False, f'LAI relevance too low: {item.get("lai_relevance_score")}'
    
    return apply_standard_matching_rules(item, domain, canonical_scopes)
```

### 3. Règles Génériques par Type de Company

**Objectif** : Règles simples et génériques basées sur le type de company

**Nouveau fichier `canonical/matching/company_matching_rules.yaml`** :
```yaml
# Règles de matching par type de company
company_types:
  pure_players:
    scopes: ["lai_companies_mvp_core", "lai_companies_pure_players"]
    rules:
      partnership_events:
        auto_match: true
        reason: "Pure player partnerships always relevant"
      regulatory_events:
        auto_match: true
        reason: "Pure player regulatory always relevant"
      corporate_move_events:
        auto_match: false
        reason: "HR/corporate noise"
      financial_results_events:
        auto_match: false
        reason: "Financial noise"
      other_events:
        require_lai_signals: true
        min_lai_relevance: 3
        
  hybrid_companies:
    scopes: ["lai_companies_hybrid"]
    rules:
      partnership_events:
        require_lai_signals: true
        min_lai_relevance: 5
      regulatory_events:
        require_lai_signals: true
        min_lai_relevance: 7
      corporate_move_events:
        auto_match: false
      financial_results_events:
        auto_match: false
      other_events:
        require_lai_signals: true
        min_lai_relevance: 8
        
  unknown_companies:
    rules:
      all_events:
        require_strong_lai_signals: true
        min_lai_relevance: 8
        min_technology_signals: 2
```

### 4. Scoring Simplifié et Générique

**Objectif** : Scoring basé sur les event types et company types

**Amélioration `canonical/scoring/scoring_rules.yaml`** :
```yaml
# Scoring par event_type (simplifié)
event_type_weights:
  partnership: 8                    # Augmenté pour Nanexa/Moderna
  regulatory: 8                     # Augmenté pour UZEDY
  clinical_update: 6
  corporate_move: 0                 # ZÉRO - exclusion
  financial_results: 0              # ZÉRO - exclusion
  other: 2

# Scoring par company_type (générique)
company_type_bonuses:
  pure_players:
    base_bonus: 3.0                 # Réduit de 5.0
    event_multipliers:
      partnership: 2.0              # Pure player + partnership = important
      regulatory: 2.0               # Pure player + regulatory = important
  hybrid_companies:
    base_bonus: 1.0
    event_multipliers:
      partnership: 1.5
      regulatory: 1.5
  unknown_companies:
    base_bonus: 0.0
    penalty: -2.0                   # Pénalité pour inconnus

# Seuils ajustés
selection_thresholds:
  min_score: 12                     # Augmenté pour filtrer le bruit
  min_items_per_section: 1
```

### 5. Configuration Client Simplifiée

**Objectif** : Configuration client plus simple et lisible

**Amélioration `lai_weekly_v5.yaml`** :
```yaml
# Configuration matching simplifiée
matching_config:
  strategy: "event_type_driven"     # Nouvelle stratégie
  min_domain_score: 0.35            # Augmenté de 0.25
  
  # Règles par event_type (référence event_type_patterns.yaml)
  event_type_rules:
    partnership:
      pure_player_auto_match: true
      hybrid_min_lai_score: 5
    regulatory:
      pure_player_auto_match: true
      hybrid_min_lai_score: 7
    corporate_move:
      auto_exclude: true
    financial_results:
      auto_exclude: true

# Scoring simplifié
scoring_config:
  strategy: "event_company_driven"  # Nouvelle stratégie
  
  # Bonus réduits
  pure_player_bonus: 3.0            # vs 5.0 avant
  trademark_bonus: 2.0              # vs 4.0 avant
  
  # Exclusions automatiques
  auto_exclude_events:
    - corporate_move
    - financial_results
```

---

## 🎯 CAS D'USAGE VALIDÉS

### Cas 1 : Malaria Grant MedinCell

**Avec les nouvelles règles** :
```
1. Event type: "partnership" (détecté par Bedrock)
2. Company: "MedinCell" (pure player)
3. Règle: pure_player + partnership = auto_match
4. Résultat: MATCHÉ ✅
```

**Avantage** : Pas besoin de "Extended Protection" hardcodé

### Cas 2 : Nomination MedinCell

**Avec les nouvelles règles** :
```
1. Event type: "corporate_move" (détecté par Bedrock)
2. Règle: corporate_move = auto_exclude
3. Résultat: NON MATCHÉ ✅
```

**Avantage** : Exclusion automatique du bruit RH

### Cas 3 : UZEDY Regulatory

**Avec les nouvelles règles** :
```
1. Event type: "regulatory" (détecté par Bedrock)
2. Company: "MedinCell" (pure player)
3. Trademark: "UZEDY" (détecté)
4. Règle: pure_player + regulatory = auto_match
5. Bonus: trademark_bonus = +2.0
6. Résultat: MATCHÉ avec score élevé ✅
```

### Cas 4 : Pfizer Corporate Move

**Avec les nouvelles règles** :
```
1. Event type: "corporate_move" (détecté par Bedrock)
2. Règle: corporate_move = auto_exclude
3. Résultat: NON MATCHÉ ✅
```

**Avantage** : Même règle pour tous, pas de logique spéciale

---

## 📈 IMPACT ATTENDU

### Réduction du Taux de Matching

**Avant (v5)** : 80% matching (12/15 items)
- Malaria Grant : MATCHÉ (contexte pure player)
- Nominations : MATCHÉES (contexte pure player)
- Finances : MATCHÉES (contexte pure player)

**Après (proposé)** : ~50% matching (7-8/15 items)
- Malaria Grant : MATCHÉ (partnership + pure player)
- Nominations : NON MATCHÉES (auto_exclude)
- Finances : NON MATCHÉES (auto_exclude)

### Amélioration de la Précision

**Faux positifs éliminés** :
- Nominations executives → auto_exclude
- Rapports financiers → auto_exclude
- Participations conférences → require_lai_signals

**Vrais positifs préservés** :
- Partnerships pure players → auto_match
- Regulatory pure players → auto_match
- Items avec signaux LAI forts → standard matching

### Simplification de la Maintenance

**Avant** :
- Règles dans 5 fichiers différents
- Prompts Bedrock complexes
- Bidouillages hardcodés

**Après** :
- Règles centralisées dans event_type_patterns.yaml
- Prompts Bedrock simples et génériques
- Configuration pilote tout

---

## 🔧 PLAN D'IMPLÉMENTATION

### Phase 1 : Simplification Prompt Bedrock

1. **Nettoyer `canonical/prompts/global_prompts.yaml`**
   - Supprimer termes LAI hardcodés
   - Supprimer contexte pure player
   - Focus sur extraction pure

2. **Tester avec items existants**
   - Vérifier que classification event_type fonctionne
   - Vérifier que extraction entités fonctionne

### Phase 2 : Enrichissement Event Type Patterns

1. **Ajouter matching_rules dans `event_type_patterns.yaml`**
   - Règles par event_type
   - Auto-exclusions
   - Seuils LAI

2. **Créer `company_matching_rules.yaml`**
   - Règles par company_type
   - Pure players vs hybrid vs unknown

### Phase 3 : Modification du Code Matching

1. **Modifier `vectora_core/normalization/matcher.py`**
   - Utiliser event_type_patterns pour matching
   - Appliquer company_matching_rules
   - Simplifier la logique

2. **Tester sur lai_weekly_v5**
   - Vérifier taux matching ~50%
   - Vérifier cas Malaria Grant
   - Vérifier exclusion nominations/finances

### Phase 4 : Ajustement Scoring

1. **Simplifier `canonical/scoring/scoring_rules.yaml`**
   - Scoring par event_type
   - Bonus par company_type
   - Seuils ajustés

2. **Validation finale**
   - Test E2E complet
   - Métriques de qualité
   - Feedback utilisateur

---

## 📋 FICHIERS À MODIFIER

### 1. `canonical/prompts/global_prompts.yaml`
```yaml
# SIMPLIFIER le prompt de normalisation
# - Supprimer termes LAI hardcodés
# - Supprimer contexte pure player
# - Focus extraction + classification event_type
```

### 2. `canonical/events/event_type_patterns.yaml`
```yaml
# AJOUTER section matching_rules pour chaque event_type
# - partnership: pure_player_auto_match: true
# - corporate_move: auto_exclude: true
# - financial_results: auto_exclude: true
```

### 3. `canonical/matching/company_matching_rules.yaml` (NOUVEAU)
```yaml
# CRÉER règles par company_type
# - pure_players: règles permissives
# - hybrid_companies: règles strictes
# - unknown_companies: règles très strictes
```

### 4. `canonical/scoring/scoring_rules.yaml`
```yaml
# SIMPLIFIER scoring
# - event_type_weights avec 0 pour corporate_move/financial_results
# - company_type_bonuses génériques
# - Seuils ajustés
```

### 5. `src_v2/vectora_core/normalization/matcher.py`
```python
# MODIFIER logique matching
# - Utiliser event_type_patterns
# - Appliquer company_matching_rules
# - Simplifier les conditions
```

---

## 🎯 AVANTAGES DE L'APPROCHE

### 1. Simplicité
- Prompt Bedrock générique et simple
- Règles métier dans la configuration
- Code plus lisible et maintenable

### 2. Généricité
- Règles applicables à toutes les verticales
- Pas de hardcoding spécifique LAI
- Extensible à d'autres domaines

### 3. Pilotabilité
- Ajustements par configuration uniquement
- Pas besoin de modifier le code
- Tests et validation simplifiés

### 4. Précision
- Exclusion automatique du bruit
- Règles claires par type d'événement
- Matching basé sur la logique métier

### 5. Maintenabilité
- Règles centralisées
- Documentation claire
- Évolution facile

---

## 📊 MÉTRIQUES DE VALIDATION

### Objectifs Quantitatifs
- **Taux de matching** : 80% → 50%
- **Faux positifs** : -70% (nominations, finances)
- **Vrais positifs** : 100% préservés (partnerships, regulatory)
- **Temps de maintenance** : -50% (règles centralisées)

### Tests de Validation
1. **Malaria Grant** : MATCHÉ (partnership + pure player)
2. **UZEDY Items** : MATCHÉS (regulatory + pure player)
3. **Nominations** : NON MATCHÉS (auto_exclude)
4. **Finances** : NON MATCHÉS (auto_exclude)
5. **Nanexa/Moderna** : MATCHÉ (partnership + signaux)

---

## 🔚 CONCLUSION

### Principe Directeur Validé
**"Configuration > Code"** - Les règles métier doivent être dans les fichiers canonical, pas dans les prompts Bedrock ou le code Python.

### Solution Recommandée
1. **Simplifier** le prompt Bedrock (extraction pure)
2. **Enrichir** event_type_patterns.yaml (règles matching)
3. **Créer** company_matching_rules.yaml (règles par type)
4. **Modifier** le code matching (utiliser configuration)
5. **Ajuster** le scoring (event_type + company_type)

### Résultat Attendu
- **Taux de matching** : retour à 50% (équilibré)
- **Précision** : élimination des faux positifs
- **Simplicité** : maintenance facilitée
- **Généricité** : applicable à toutes verticales

Cette approche respecte la philosophie Vectora Inbox : **simple, configurable, et maintenable par un solo founder**.

---

*Rapport d'amélioration réalisé le 2025-12-23*  
*Basé sur l'analyse complète du projet et des règles de développement*  
*Objectif : Matching précis et générique pilotable par configuration*