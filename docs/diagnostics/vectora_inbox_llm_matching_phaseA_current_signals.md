# Phase A1 - Diagnostic des signaux LLM existants

**Date** : 2025-12-12  
**Phase** : A1 - Diagnostic des signaux existants  
**Objectif** : Identifier les signaux LLM déjà présents dans les items normalisés  

---

## 🔍 Analyse des Items Normalisés Actuels

### Source d'analyse
- **Fichier analysé** : `items_normalized_lai_weekly_v3_latest.json`
- **Nombre d'items** : 100+ items récents
- **Date des items** : 2025-12-11 (données fraîches)

### Structure actuelle des items normalisés

Chaque item normalisé contient actuellement :

```json
{
  "source_key": "press_sector__endpoints_news",
  "source_type": "press_sector",
  "title": "...",
  "summary": "...",
  "url": "...",
  "date": "2025-12-11",
  "companies_detected": ["Company1", "Company2"],
  "molecules_detected": ["molecule1"],
  "technologies_detected": [],
  "indications_detected": [],
  "event_type": "other"
}
```

---

## 📊 Signaux LLM Identifiés

### ✅ Signaux LLM déjà présents et exploitables

#### 1. **Champs d'entités détectées** (signaux LLM indirects)
- **`companies_detected`** : Liste des sociétés identifiées par Bedrock
- **`molecules_detected`** : Liste des molécules/médicaments identifiés
- **`technologies_detected`** : Liste des technologies détectées
- **`indications_detected`** : Liste des indications thérapeutiques

**Exemple d'exploitation** :
```json
{
  "companies_detected": ["MedinCell", "Teva"],
  "molecules_detected": ["olanzapine", "risperidone"],
  "technologies_detected": [],
  "indications_detected": []
}
```

#### 2. **`event_type`** (classification LLM)
- **Valeur actuelle** : Principalement `"other"` dans les données analysées
- **Valeurs possibles** : `clinical_update`, `partnership`, `regulatory`, `scientific_paper`, `corporate_move`, `financial_results`, `safety_signal`, `manufacturing_supply`, `other`
- **Potentiel** : Signal de qualité pour le scoring (partnerships > financial_results)

#### 3. **`summary`** (résumé LLM)
- **Format** : Résumé structuré de 2-3 phrases généré par Bedrock
- **Qualité** : Variable, parfois tronqué ou avec artefacts JSON
- **Potentiel** : Indicateur de complexité/richesse du contenu

---

## ❌ Signaux LLM manquants mais attendus

### Signaux LAI spécifiques non trouvés

D'après le code de `bedrock_client.py`, le prompt de normalisation devrait produire :

#### 1. **`lai_relevance_score`** (0-10)
- **Attendu** : Score de pertinence LAI de 0 à 10
- **Statut** : **ABSENT** dans les items analysés
- **Impact** : Signal clé pour le scoring manquant

#### 2. **`anti_lai_detected`** (boolean)
- **Attendu** : Détection de signaux anti-LAI (oral routes)
- **Statut** : **ABSENT** dans les items analysés
- **Impact** : Pénalité importante manquante

#### 3. **`pure_player_context`** (boolean)
- **Attendu** : Contexte pure player LAI sans mentions explicites
- **Statut** : **ABSENT** dans les items analysés
- **Impact** : Bonus pure player manquant

#### 4. **`trademarks_detected`** (array)
- **Attendu** : Liste des trademarks détectées (UZEDY, PharmaShell, etc.)
- **Statut** : **ABSENT** dans les items analysés
- **Impact** : Signal privilégié manquant

#### 5. **`domain_relevance`** (array)
- **Attendu** : Évaluations par domaine si domain_contexts fourni
- **Statut** : **ABSENT** dans les items analysés
- **Impact** : Matching hybride impossible

---

## 🔧 Diagnostic Technique

### Problème identifié : Réponse Bedrock incomplète

#### Analyse du prompt actuel
Le prompt dans `canonical/prompts/global_prompts.yaml` demande bien :

```yaml
lai_relevance_score: 0,
anti_lai_detected: false,
pure_player_context: false
```

#### Hypothèses sur la cause
1. **Parsing JSON défaillant** : `_parse_bedrock_response()` ne récupère que les champs de base
2. **Réponse Bedrock tronquée** : Limite de tokens ou format de réponse
3. **Feature flag désactivé** : `USE_CANONICAL_PROMPTS=false` → prompt hardcodé utilisé
4. **Erreur de sérialisation** : Champs perdus lors de la sauvegarde S3

#### Vérification du code de parsing

Dans `bedrock_client.py::_parse_bedrock_response()` :

```python
# S'assurer que les champs obligatoires existent (avec champs LAI)
result.setdefault('lai_relevance_score', 0)
result.setdefault('anti_lai_detected', False)
result.setdefault('pure_player_context', False)
result.setdefault('trademarks_detected', [])
```

**Conclusion** : Le code prévoit ces champs mais ils ne sont pas présents dans les données réelles.

---

## 📈 Signaux Exploitables pour Phase A

### Quick wins identifiés

#### 1. **Profondeur des entités** (signal composite)
```python
entity_depth = (
    len(companies_detected) + 
    len(molecules_detected) + 
    len(technologies_detected) + 
    len(indications_detected)
)
```
- **Utilisation** : Multiplicateur de score (plus d'entités = plus pertinent)
- **Implémentation** : Déjà présent dans `scorer.py`

#### 2. **Type d'événement** (classification LLM)
```python
event_type_weights = {
    'partnership': 8,
    'regulatory': 7, 
    'clinical_update': 6,
    'other': 1
}
```
- **Utilisation** : Pondération directe du score
- **Implémentation** : Déjà présent dans `scorer.py`

#### 3. **Présence de sociétés LAI** (signal indirect)
```python
lai_companies = set(companies_detected) & set(lai_pure_players)
if lai_companies:
    score_bonus = 3.0
```
- **Utilisation** : Bonus pour sociétés LAI détectées
- **Implémentation** : Déjà présent dans `scorer.py`

---

## 🎯 Recommandations Phase A

### A1 → A2 : Actions immédiates

#### 1. **Exploiter les signaux existants**
- Utiliser `entity_depth` comme multiplicateur
- Pondérer par `event_type` (même si souvent "other")
- Appliquer bonus sociétés LAI détectées

#### 2. **Investiguer les signaux manquants**
- Vérifier si `USE_CANONICAL_PROMPTS=true` en DEV
- Analyser les logs Bedrock pour voir les réponses complètes
- Tester le parsing JSON avec un item réel

#### 3. **Feature flag pour Phase A**
```python
USE_LLM_RELEVANCE = os.environ.get('USE_LLM_RELEVANCE', 'false').lower() == 'true'
```

### Critères de succès Phase A1 ✅

- [x] **Signaux LLM existants identifiés** : `companies_detected`, `molecules_detected`, `event_type`
- [x] **Signaux manquants documentés** : `lai_relevance_score`, `anti_lai_detected`, `trademarks_detected`
- [x] **Cause probable identifiée** : Parsing incomplet ou feature flag désactivé
- [x] **Quick wins définis** : Entity depth, event type weighting, LAI company bonus

---

## 📋 Actions Phase A2

1. **Modifier `scorer.py`** pour exploiter les signaux existants
2. **Ajouter feature flag `USE_LLM_RELEVANCE`**
3. **Investiguer les signaux manquants** (logs Bedrock, feature flags)
4. **Tests locaux** avec/sans LLM relevance

**Condition pour passer à A2** : ✅ **Signaux LLM identifiés et documentés**