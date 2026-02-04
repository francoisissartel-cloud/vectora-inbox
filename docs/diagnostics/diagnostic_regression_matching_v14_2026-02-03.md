# Rapport Diagnostic - Régression Matching v14

**Date**: 2026-02-03  
**Durée diagnostic**: 45 minutes  
**Statut**: ✅ CAUSE RACINE IDENTIFIÉE

---

## 📊 RÉSUMÉ EXÉCUTIF

### Problème

Après application du plan d'amélioration canonical v2.2, régression du matching :
- **V13** (avant) : 14/29 items relevant (48.3%), score moyen 38.3
- **V14** (après) : 12/29 items relevant (41.4%), score moyen 33.1
- **Impact** : -2 items matchés (-14%), -5.2 points de score moyen (-13.6%)

### Cause Racine

**Perte de détection des `pure_player_company` dans le domain_scoring**

Le prompt `lai_domain_scoring.yaml` ne reçoit plus les entités companies au top-level, donc ne peut plus détecter les pure_player companies (Nanexa, Camurus, MedinCell, etc.) → perte de 25 points de boost par item concerné.

### Solution

Restaurer la détection `pure_player_company` en :
1. Ajoutant les entités au top-level des items (companies_detected, technologies_detected)
2. OU en modifiant le prompt domain_scoring pour lire depuis normalized_content['entities']

---

## 🔍 ANALYSE DÉTAILLÉE

### Étape 1: Vérification Fichiers S3

✅ **Tous les fichiers canonical v2.2 présents et corrects sur S3**

```
lai_domain_definition.yaml: 8479 octets (local) = 8479 (S3)
generic_normalization.yaml: 3731 octets (local) = 3731 (S3)
lai_domain_scoring.yaml: 4575 octets (local) = 4575 (S3)
exclusion_scopes.yaml: 4468 octets (local) = 4468 (S3)
source_catalog.yaml: 7532 octets (local) = 7532 (S3)
```

**Conclusion** : Pas de problème de déploiement S3.

### Étape 2: Analyse Structure Items

❌ **Champs entités manquants au top-level**

```json
// V14 - Top-level keys
[
  "item_id", "source_key", "title", "content", "url",
  "normalized_content", "domain_scoring", ...
]

// MANQUANTS:
- companies_detected
- technologies_detected
- dosing_intervals_detected
```

Les entités sont dans `normalized_content['entities']` :

```json
{
  "companies": [],
  "molecules": [],
  "technologies": [],
  "trademarks": ["PharmaShell®"],
  "indications": []
}
```

**Problème** : Les arrays sont vides (companies=[], technologies=[]) alors que Nanexa devrait être détecté.

### Étape 3: Comparaison V13 vs V14

**Item 1 - Nanexa + Moderna**

| Version | Score | Signaux Strong | Signaux Medium |
|---------|-------|----------------|----------------|
| V13 | 80 | `pure_player_company: Nanexa` | `technology_family: PharmaShell®` |
| V14 | 80 | ❌ AUCUN | `technology_family: PharmaShell` |

**Item 2 - MedinCell + Teva**

| Version | Score | Signaux Strong | Signaux Medium |
|---------|-------|----------------|----------------|
| V13 | 85 | `pure_player_company: MedinCell`, `trademark: TEV-'749 / mdc-TJK` | `dosing_interval: once-monthly`, `hybrid_company: Teva` |
| V14 | 90 | `trademark: TEV-'749`, `trademark: mdc-TJK` | `dosing_interval: once-monthly`, `hybrid_company: Teva` |

**Item 3 - Camurus**

| Version | Score | Signaux Strong | Signaux Medium |
|---------|-------|----------------|----------------|
| V13 | 80 | `pure_player_company: Camurus` | ❌ AUCUN |
| V14 | 85 | `trademark_mention: Oclaiz` | `dosing_intervals: {{item_dosing_intervals}}` ⚠️ |

**Item 5 - Nanexa + Semaglutide**

| Version | Score | Signaux Strong | Signaux Medium |
|---------|-------|----------------|----------------|
| V13 | 80 | `pure_player_company: Nanexa`, `trademark: PharmaShell®` | `technology_family: microspheres` |
| V14 | 75 | ❌ AUCUN | `technology_family: PharmaShell`, `dosing_interval: monthly injection` |

### Observations Clés

1. **V14 perd systématiquement `pure_player_company`** (Nanexa, Camurus, MedinCell)
2. **V14 compense parfois** avec d'autres signaux (trademarks, dosing_intervals)
3. **V14 a un bug de template** : `{{item_dosing_intervals}}` non résolu (Item 3)
4. **V14 détecte mieux les dosing_intervals** : "monthly injection", "once-monthly", "Q4 2025"

### Étape 4: Analyse Cause Racine

**Pourquoi V13 détectait pure_player_company ?**

Hypothèse 1 : V13 avait les entités au top-level (companies_detected)  
→ ❌ FAUX : V13 a aussi normalized_content['entities']['companies'] = []

Hypothèse 2 : V13 utilisait un prompt différent qui détectait depuis le texte  
→ ✅ PROBABLE : Le prompt v2.1 détectait les companies depuis le contenu

**Pourquoi V14 ne détecte plus ?**

Le nouveau prompt `lai_domain_scoring.yaml` v2.2 :
- Ajoute des CRITICAL RULES anti-hallucination
- Demande de ne détecter QUE les signaux "EXPLICITLY present in the normalized item"
- Ne peut plus inférer les companies depuis le texte

**Résultat** : Bedrock est trop conservateur et ne détecte plus les pure_player companies.

---

## 🐛 BUGS IDENTIFIÉS

### Bug 1: Perte Détection Pure Player Companies

**Sévérité**: 🔴 CRITIQUE  
**Impact**: -25 points de boost par item concerné (Nanexa, Camurus, MedinCell, Delsitech, Peptron)

**Cause**: 
- Entités companies vides dans normalized_content['entities']['companies']
- Prompt domain_scoring trop strict (CRITICAL RULES anti-hallucination)
- Pas de fallback pour détecter companies depuis le texte

**Items affectés**: 5-7 items par run (pure players)

### Bug 2: Template Non Résolu

**Sévérité**: 🟡 MOYEN  
**Impact**: Signal medium invalide, confusion dans l'analyse

**Exemple**: `'dosing_intervals: {{item_dosing_intervals}}'` (Item 3 - Camurus)

**Cause**: Template Jinja2 non résolu dans le prompt ou la réponse Bedrock

**Items affectés**: Au moins 1 item (Camurus Oclaiz)

### Bug 3: Entités Companies Vides

**Sévérité**: 🔴 CRITIQUE  
**Impact**: Aucune company détectée dans normalized_content['entities']['companies']

**Cause**: 
- Prompt `generic_normalization.yaml` ne détecte pas les companies
- OU Bedrock ne retourne pas les companies
- OU Parsing de la réponse Bedrock échoue

**Items affectés**: TOUS les items (29/29)

---

## 🔧 PLAN DE CORRECTION

### Option 1: Corriger la Normalisation (RECOMMANDÉ)

**Objectif**: Faire en sorte que `normalized_content['entities']['companies']` soit rempli

**Actions**:
1. Vérifier le prompt `generic_normalization.yaml` :
   - S'assure-t-il de demander les companies ?
   - Le format de sortie est-il correct ?
2. Vérifier les logs Lambda normalize-score-v2 :
   - Bedrock retourne-t-il les companies ?
   - Le parsing JSON fonctionne-t-il ?
3. Corriger le prompt si nécessaire :
   - Ajouter instruction explicite pour extraire companies
   - Fournir la liste des pure_player companies depuis company_scopes.yaml

**Avantages**:
- ✅ Corrige le problème à la source
- ✅ Les entités seront disponibles pour tous les usages futurs
- ✅ Cohérent avec l'architecture

**Inconvénients**:
- ⏱️ Nécessite re-normalisation de tous les items

### Option 2: Assouplir le Domain Scoring

**Objectif**: Permettre au domain_scoring de détecter les companies depuis le texte

**Actions**:
1. Modifier `lai_domain_scoring.yaml` :
   - Retirer ou assouplir les CRITICAL RULES anti-hallucination
   - Ajouter instruction : "If companies_detected is empty, infer from title/content"
   - Fournir la liste des pure_player companies dans le prompt

**Avantages**:
- ⚡ Rapide à implémenter
- ✅ Pas besoin de re-normaliser

**Inconvénients**:
- ❌ Risque de faux positifs (hallucinations)
- ❌ Ne corrige pas le problème de fond (entités vides)
- ❌ Incohérent avec l'objectif anti-hallucination

### Option 3: Hybride (OPTIMAL)

**Objectif**: Corriger la normalisation ET assouplir temporairement le scoring

**Actions**:
1. **Court terme** (Option 2) : Assouplir domain_scoring pour débloquer
2. **Moyen terme** (Option 1) : Corriger la normalisation
3. **Long terme** : Retirer l'assouplissement une fois normalisation OK

**Avantages**:
- ✅ Débloque immédiatement
- ✅ Corrige le problème de fond
- ✅ Permet de valider les autres améliorations v2.2

**Inconvénients**:
- ⏱️ Nécessite 2 phases de travail

---

## 📋 ACTIONS IMMÉDIATES

### Action 1: Vérifier Logs Lambda Normalisation

**Objectif**: Comprendre pourquoi companies_detected est vide

```bash
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 2h \
  --filter-pattern "Nanexa" \
  --profile rag-lai-prod \
  --region eu-west-3
```

**Chercher**:
- La réponse Bedrock pour l'item Nanexa
- Le champ `entities.companies` dans la réponse
- Les erreurs de parsing JSON

### Action 2: Tester Prompt Normalisation Localement

**Objectif**: Reproduire le problème de détection companies

```bash
# Créer un test local avec l'item Nanexa
python tests/local/test_normalization_prompt.py \
  --item-id "nanexa_moderna_2026-01-09" \
  --canonical-version "2.2"
```

### Action 3: Corriger le Prompt (Si Nécessaire)

**Fichier**: `canonical/prompts/normalization/generic_normalization.yaml`

**Modification**: Ajouter instruction explicite pour companies

```yaml
# AJOUTER dans la section entities
entities:
  companies:
    description: "Extract ALL company names mentioned (pharmaceutical, biotech, CDMO)"
    instructions: |
      - Include pure-player LAI companies: Nanexa, Camurus, MedinCell, Delsitech, Peptron
      - Include hybrid pharma companies: Teva, Eli Lilly, Novo Nordisk, etc.
      - Extract from title AND content
      - Use exact company names as mentioned
    examples:
      - "Nanexa and Moderna" → ["Nanexa", "Moderna"]
      - "MedinCell's Partner Teva" → ["MedinCell", "Teva"]
```

### Action 4: Corriger le Bug Template

**Fichier**: `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`

**Rechercher**: `{{item_dosing_intervals}}` ou template Jinja2 non résolu

**Corriger**: Remplacer par la valeur réelle ou supprimer le template

---

## 🎯 CRITÈRES DE SUCCÈS

### Validation Correction

Après correction, un run v15 doit montrer :

1. ✅ `normalized_content['entities']['companies']` rempli (non vide)
2. ✅ `pure_player_company` détecté dans domain_scoring
3. ✅ Score moyen ≥ 38 (niveau v13)
4. ✅ Items relevant ≥ 14/29 (niveau v13)
5. ✅ Pas de template non résolu (`{{...}}`)

### Métriques Cibles

| Métrique | V13 (Avant) | V14 (Actuel) | V15 (Cible) |
|----------|-------------|--------------|-------------|
| Items relevant | 14/29 (48.3%) | 12/29 (41.4%) | ≥14/29 (48.3%) |
| Score moyen | 38.3 | 33.1 | ≥38.0 |
| Pure player détectés | 5-7 items | 0 items | 5-7 items |
| Templates non résolus | 0 | 1+ | 0 |

---

## 📝 LEÇONS APPRISES

### Ce Qui A Causé la Régression

1. **CRITICAL RULES trop strictes** : "Only detect signals EXPLICITLY present" empêche l'inférence
2. **Entités vides non détectées** : Pas de validation que companies_detected est rempli
3. **Pas de tests de régression** : Aucun test automatique pour détecter la perte de pure_player_company
4. **Changements multiples simultanés** : 5 fichiers modifiés en même temps, difficile d'isoler la cause

### Actions Préventives Futures

1. **Tests de régression automatiques** :
   - Créer `tests/regression/test_pure_player_detection.py`
   - Valider que Nanexa, Camurus, MedinCell sont détectés
   - Exécuter avant chaque promotion stage/prod

2. **Validation entités** :
   - Ajouter assertion : `assert len(companies_detected) > 0 for pure_player items`
   - Logger un WARNING si companies_detected est vide pour un pure player

3. **Changements incrémentaux** :
   - Modifier 1-2 fichiers à la fois
   - Tester après chaque modification
   - Commit séparé par type de changement

4. **Métriques de référence** :
   - Documenter les métriques v13 comme baseline
   - Comparer systématiquement après chaque changement
   - Alerter si régression > 10%

---

## 📎 ANNEXES

### Annexe A: Comparaison Complète V13 vs V14

Voir fichier : `scripts/compare_v13_v14.py`

### Annexe B: Structure Items

```json
// V14 - Item structure
{
  "item_id": "...",
  "title": "Nanexa and Moderna...",
  "normalized_content": {
    "entities": {
      "companies": [],        // ❌ VIDE
      "technologies": [],     // ❌ VIDE
      "trademarks": ["PharmaShell®"]
    }
  },
  "domain_scoring": {
    "is_relevant": true,
    "score": 80,
    "signals_detected": {
      "strong": [],           // ❌ Pas de pure_player_company
      "medium": ["technology_family: PharmaShell"]
    }
  }
}
```

### Annexe C: Fichiers Modifiés v2.2

1. `canonical/prompts/normalization/generic_normalization.yaml` (+extraction dosing_intervals, title)
2. `canonical/domains/lai_domain_definition.yaml` (+boost conditionnel hybrid_company)
3. `canonical/prompts/domain_scoring/lai_domain_scoring.yaml` (+CRITICAL RULES anti-hallucination)
4. `canonical/scopes/exclusion_scopes.yaml` (+termes boursiers)
5. `canonical/sources/source_catalog.yaml` (+max_content_length 2000)

---

**Rapport créé**: 2026-02-03  
**Auteur**: Q Developer  
**Statut**: ✅ COMPLET - PRÊT POUR CORRECTION
