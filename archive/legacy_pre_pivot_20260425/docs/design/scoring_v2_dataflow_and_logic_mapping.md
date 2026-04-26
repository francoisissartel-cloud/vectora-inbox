# Cartographie Scoring V2 - Dataflow et Logique

**Date :** 21 décembre 2025  
**Objectif :** Cartographier complètement le système de scoring V2 pour identifier pourquoi final_score = 0.0  
**Statut :** Phase 1 - Investigation technique  

---

## 🎯 PROBLÈME À RÉSOUDRE

**Symptôme :** Tous les items curated ont `scoring_results.final_score = 0.0`

**Signaux disponibles :**
- `lai_relevance_score` : 0-10 (correctement calculé)
- `matched_domains` : Correctement remplis pour items pertinents
- `domain_relevance.score` : 0.6-0.9 (matching fonctionnel)
- `scoring_results` : Toutes les valeurs à 0.0

**Question centrale :** Où et comment final_score devrait-il être calculé ?

---

## 📋 MODULES DE SCORING IDENTIFIÉS

### Structure du Pipeline normalize_score_v2

```
src_v2/vectora_core/normalization/
├── __init__.py                 # run_normalize_score_for_client()
├── normalizer.py               # Appels Bedrock normalisation
├── matcher.py                  # Matching aux domaines
├── bedrock_client.py           # Client Bedrock
└── scorer.py                   # ← MODULE SCORING (à vérifier)
```

### Modules à Analyser

1. **src_v2/vectora_core/normalization/__init__.py**
   - Orchestration du pipeline normalize_score
   - Appels aux modules normalizer, matcher, scorer

2. **src_v2/vectora_core/normalization/scorer.py**
   - Logique de calcul de final_score
   - Utilisation de scoring_config du client

3. **src_v2/vectora_core/normalization/matcher.py**
   - Génération de matched_domains et domain_relevance
   - Interface avec le scoring

---

## 🔍 ANALYSE DU DATAFLOW SCORING

### Étapes Théoriques du Pipeline

```
1. NORMALISATION (normalizer.py)
   ├── Input: Raw content
   ├── Bedrock: Extraction entités + lai_relevance_score
   └── Output: normalized_content

2. MATCHING (matcher.py)
   ├── Input: normalized_content + canonical scopes
   ├── Bedrock: Domain matching
   └── Output: matching_results

3. SCORING (scorer.py) ← POINT CRITIQUE
   ├── Input: normalized_content + matching_results + scoring_config
   ├── Calcul: base_score + bonuses - penalties
   └── Output: scoring_results.final_score
```

### Données Disponibles pour le Scoring

**Depuis normalized_content :**
- `lai_relevance_score` : 0-10
- `event_classification.primary_type` : partnership, regulatory, etc.
- `entities` : companies, technologies, trademarks
- `pure_player_context` : boolean

**Depuis matching_results :**
- `matched_domains` : ["tech_lai_ecosystem"]
- `domain_relevance.tech_lai_ecosystem.score` : 0.6-0.9

**Configuration scoring (lai_weekly_v4.yaml) :**
```yaml
scoring_config:
  min_score: 12
  max_items_total: 15
  # Autres paramètres de scoring ?
```

---

## 📊 ANALYSE DES DONNÉES CURATED ACTUELLES

### Exemples d'Items avec Signaux Forts

**Item 1 - Nanexa/Moderna Partnership :**
```json
{
  "normalized_content": {
    "lai_relevance_score": 8,
    "event_classification": {"primary_type": "partnership"},
    "entities": {
      "companies": ["Nanexa", "Moderna"],
      "technologies": ["PharmaShell®"]
    }
  },
  "matching_results": {
    "matched_domains": ["tech_lai_ecosystem"],
    "domain_relevance": {
      "tech_lai_ecosystem": {"score": 0.7, "confidence": "high"}
    }
  },
  "scoring_results": {
    "base_score": 0.0,           ← PROBLÈME
    "bonuses": {},               ← VIDE
    "penalties": {},             ← VIDE
    "final_score": 0.0           ← RÉSULTAT INCORRECT
  }
}
```

**Item 2 - UZEDY FDA Approval :**
```json
{
  "normalized_content": {
    "lai_relevance_score": 10,
    "event_classification": {"primary_type": "regulatory"},
    "entities": {
      "molecules": ["risperidone", "UZEDY"],
      "technologies": ["Extended-Release Injectable"]
    }
  },
  "matching_results": {
    "matched_domains": ["tech_lai_ecosystem"],
    "domain_relevance": {
      "tech_lai_ecosystem": {"score": 0.9, "confidence": "high"}
    }
  },
  "scoring_results": {
    "base_score": 0.0,           ← PROBLÈME
    "final_score": 0.0           ← RÉSULTAT INCORRECT
  }
}
```

### Patterns Observés

**Items avec final_score = 0 mais signaux forts :**
- lai_relevance_score = 8-10
- matched_domains non vides
- domain_relevance.score = 0.7-0.9
- Entités LAI pertinentes extraites

**Items avec final_score = 0 et pénalités :**
```json
{
  "scoring_results": {
    "base_score": 3.0,
    "penalties": {
      "low_lai_score": -3.0,
      "low_relevance_event": -1.0
    },
    "final_score": 0,
    "score_breakdown": {
      "raw_score": -3.85,
      "scoring_mode": "balanced"
    }
  }
}
```

**Observation :** Certains items ont des pénalités calculées, d'autres ont tout à 0.0.

---

## 🔧 HYPOTHÈSES SUR LA CAUSE RACINE

### Hypothèse 1 : Fonction de Scoring Non Appelée

**Symptôme :** scoring_results avec toutes valeurs à 0.0
**Cause possible :** scorer.py n'est pas invoqué dans le pipeline
**Test :** Vérifier les appels dans normalization/__init__.py

### Hypothèse 2 : Bug dans l'Algorithme de Scoring

**Symptôme :** Certains items ont des pénalités mais final_score = 0
**Cause possible :** Logique de calcul incorrecte (seuil minimum, arrondi, etc.)
**Test :** Analyser l'algorithme dans scorer.py

### Hypothèse 3 : Configuration Scoring Manquante

**Symptôme :** Pas de bonus/penalties pour items avec signaux forts
**Cause possible :** scoring_config incomplet dans lai_weekly_v4.yaml
**Test :** Vérifier la configuration de scoring

### Hypothèse 4 : Écrasement de final_score

**Symptôme :** Score calculé puis remis à 0
**Cause possible :** Étape ultérieure qui écrase final_score
**Test :** Tracer l'exécution complète du pipeline

### Hypothèse 5 : Champ JSON Incorrect

**Symptôme :** Score calculé mais écrit dans mauvaise clé
**Cause possible :** Erreur de mapping JSON
**Test :** Vérifier la structure de sortie

---

## 📁 FICHIERS À ANALYSER EN PRIORITÉ

### 1. Pipeline Principal
```
src_v2/vectora_core/normalization/__init__.py
└── run_normalize_score_for_client()
    ├── Appel normalizer.normalize_content()
    ├── Appel matcher.match_domains()
    └── Appel scorer.calculate_score() ← VÉRIFIER
```

### 2. Module Scoring
```
src_v2/vectora_core/normalization/scorer.py
├── calculate_score() ou équivalent
├── Algorithme base_score + bonuses - penalties
└── Utilisation de scoring_config
```

### 3. Configuration Client
```
client-config-examples/lai_weekly_v4.yaml
└── scoring_config:
    ├── Paramètres de scoring
    ├── Seuils et poids
    └── Règles de bonus/penalties
```

### 4. Handler Lambda
```
src_v2/lambdas/normalize_score/handler.py
└── Vérifier les variables d'environnement
└── Vérifier les appels à run_normalize_score_for_client()
```

---

## 🎯 PLAN D'INVESTIGATION DÉTAILLÉE

### Étape 1.1 : Analyse du Pipeline Principal
- [ ] Lire normalization/__init__.py
- [ ] Identifier les appels au module scoring
- [ ] Vérifier l'ordre d'exécution
- [ ] Tracer le flux de données

### Étape 1.2 : Analyse du Module Scoring
- [ ] Lire scorer.py (s'il existe)
- [ ] Identifier la fonction de calcul de final_score
- [ ] Analyser l'algorithme de scoring
- [ ] Vérifier l'utilisation de scoring_config

### Étape 1.3 : Analyse de la Configuration
- [ ] Examiner lai_weekly_v4.yaml
- [ ] Identifier les paramètres de scoring
- [ ] Vérifier la complétude de scoring_config
- [ ] Comparer avec les besoins du scorer

### Étape 1.4 : Test de Traçage
- [ ] Ajouter des logs dans le pipeline
- [ ] Exécuter sur un item test
- [ ] Tracer le calcul de final_score
- [ ] Identifier le point de défaillance

---

## 📊 MÉTRIQUES ATTENDUES POST-CORRECTION

### Scoring Fonctionnel

**Items avec signaux LAI forts (lai_relevance_score >= 8) :**
- final_score >= 12 (seuil min_score)
- Bonus pour matched_domains
- Bonus pour event_type pertinent (partnership, regulatory)

**Items avec signaux LAI moyens (lai_relevance_score 6-7) :**
- final_score 8-12
- Pénalités possibles selon contexte

**Items avec signaux LAI faibles (lai_relevance_score 0-5) :**
- final_score < 8
- Pénalités multiples
- Exclusion de la newsletter

### Distribution Attendue sur lai_weekly_v4

**15 items actuels :**
- 6-8 items avec final_score >= 12 (sélectionnables)
- 4-5 items avec final_score 8-12 (moyens)
- 3-4 items avec final_score < 8 (exclus)

---

## 🔄 TRANSITION VERS PHASE 2

**Une fois la cartographie terminée :**
1. **Cause racine identifiée** : Pourquoi final_score = 0
2. **Point de défaillance localisé** : Module/fonction responsable
3. **Configuration analysée** : Paramètres manquants ou incorrects
4. **Plan de correction défini** : Actions précises pour corriger

**Livrables Phase 1 :**
- Dataflow complet du scoring V2
- Identification du bug (fonction, config, logique)
- Exemples concrets d'items avec calcul attendu
- Plan de correction pour Phase 4

---

*Cartographie Scoring V2 - Phase 1 Investigation*  
*Objectif : Comprendre pourquoi final_score = 0.0 malgré les signaux LAI*