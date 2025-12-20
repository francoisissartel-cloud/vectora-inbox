# Phase 3 – Run Normalize_Score V2 Réel - lai_weekly_v4

**Date :** 19 décembre 2025  
**Durée :** 60 minutes  
**Objectif :** Exécuter normalize_score_v2 et analyser la normalisation/scoring

---

## ✅ Commande d'Invocation Utilisée

```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v4"}' \
  --cli-binary-format raw-in-base64-out \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --cli-read-timeout 300 \
  response_normalize_lai_v4.json
```

**Statut :** ✅ **SUCCÈS** (StatusCode: 200)

---

## 📊 Métriques d'Exécution

### Résultat Global
- **Durée totale :** 83,723 ms (1 minute 23 secondes)
- **Statut :** completed
- **Input path :** ingested/lai_weekly_v4/2025/12/19
- **Output path :** curated/lai_weekly_v4/2025/12/19/items.json

### Configuration Bedrock
- **Modèle :** anthropic.claude-3-sonnet-20240229-v1:0
- **Région :** us-east-1
- **Mode scoring :** balanced
- **Max workers :** 1
- **Bedrock matching :** enabled

### Statistiques de Traitement
- **Items input :** 15
- **Items normalisés :** 15 (100% succès)
- **Items matchés :** 0 (0% succès) ⚠️
- **Items scorés :** 15

---

## 🔍 Analyse des Résultats de Normalisation

### Taux de Succès
- **Normalisation :** 100% (15/15) ✅
- **Matching :** 0% (0/15) ⚠️ **PROBLÈME CRITIQUE**

### Distribution des Scores
- **Score minimum :** 2.2
- **Score maximum :** 14.9
- **Score moyen :** 11.23
- **High scores (>12) :** 5 items
- **Medium scores (8-12) :** 2 items
- **Low scores (<8) :** 1 item

### Statistiques d'Entités Extraites
- **Sociétés détectées :** 15
- **Molécules détectées :** 5
- **Technologies détectées :** 9
- **Marques détectées :** 5

---

## 🎯 Analyse Item par Item (Top 5)

### 1. **Nanexa-Moderna Partnership** (Score: 14.9) 🏆
- **Événement :** Accord de licence PharmaShell® avec Moderna
- **Entités :** Nanexa, Moderna, PharmaShell®
- **LAI relevance :** 8/10
- **Bonuses :** Pure player (5.0) + Trademark (4.0) + Partnership (3.0) + High LAI (2.5)
- **Type :** partnership

### 2. **Olanzapine NDA Submission** (Score: 13.8) 🥈
- **Événement :** Soumission NDA FDA Olanzapine LAI (Teva/MedinCell)
- **Entités :** MedinCell, Teva, olanzapine, Extended-Release Injectable
- **LAI relevance :** 10/10
- **Bonuses :** Pure player (5.0) + Molecule (2.5) + Regulatory (2.5) + High LAI (2.5)
- **Type :** regulatory

### 3. **UZEDY® Growth + Olanzapine Pipeline** (Score: 12.8) 🥉
- **Événement :** Croissance UZEDY® et préparation NDA Olanzapine
- **Entités :** Teva, UZEDY®, olanzapine, Long-Acting Injectable
- **LAI relevance :** 10/10
- **Bonuses :** Trademark (4.0) + Molecule (2.5) + Regulatory (2.5) + High LAI (2.5)
- **Type :** regulatory

### 4. **UZEDY® FDA Approval Bipolar** (Score: 12.8) 🥉
- **Événement :** Approbation FDA élargie UZEDY® pour Bipolar I
- **Entités :** UZEDY®, risperidone, Extended-Release Injectable
- **LAI relevance :** 10/10
- **Bonuses :** Trademark (4.0) + Molecule (2.5) + Regulatory (2.5) + High LAI (2.5)
- **Type :** regulatory

### 5. **Nanexa Q3 Report** (Score: 9.7)
- **Événement :** Rapport intermédiaire avec optimisation GLP-1
- **Entités :** Nanexa, GLP-1, PharmaShell
- **LAI relevance :** 7/10
- **Bonuses :** Pure player (5.0) + Trademark (4.0) + Medium LAI (1.5)
- **Type :** financial_results

---

## ⚠️ Problème Critique : Matching 0%

### Observation
**AUCUN item n'a été matché sur le domaine `tech_lai_ecosystem`** malgré :
- 15 items normalisés avec succès
- Signaux LAI forts détectés (scores 8-10/10)
- Technologies LAI explicites extraites
- Configuration lai_weekly_v4 avec domaine unique

### Hypothèses du Problème
1. **Problème de configuration matching :** Domaine `tech_lai_ecosystem` non reconnu
2. **Seuils trop élevés :** `min_domain_score: 0.25` trop restrictif
3. **Problème Bedrock matching :** Appels échoués ou réponses vides
4. **Problème de scopes :** Scopes LAI non chargés correctement

### Impact
- **Items exclus :** Plusieurs items avec `exclusion_applied: true`
- **Raisons d'exclusion :** 
  - `lai_score_too_low`
  - `no_lai_entities_low_score`
- **Score final 0 :** 8 items sur 15 ont un score final de 0

---

## 🔬 Analyse des Exclusions

### Items Exclus (Score Final = 0)
1. **DelSiTech Partnership Event** - Exclusion: `no_lai_entities_low_score`
2. **DelSiTech BIO Convention** - Exclusion: `lai_score_too_low`
3. **MedinCell Financial Results** - Exclusion: `lai_score_too_low`
4. **MedinCell MSCI Index** - Exclusion: `lai_score_too_low`
5. **Nanexa Q3 Report (duplicate)** - Exclusion: `lai_score_too_low`
6. **Nanexa Attachment** - Exclusion: `lai_score_too_low`
7. **Nanexa H1 Report** - Exclusion: `lai_score_too_low`

### Items Conservés (Score Final > 0)
- **7 items** avec scores entre 2.2 et 14.9
- Tous contiennent des signaux LAI forts
- Sociétés pure-player LAI bien représentées

---

## 💰 Estimation Coûts Bedrock

### Appels Bedrock Estimés
- **Normalisation :** 15 appels (1 par item)
- **Matching :** 15 appels (1 par item, même si échec)
- **Total :** ~30 appels Bedrock

### Coût Estimé (Claude-3-Sonnet)
- **Input tokens :** ~15,000 tokens (1,000 par item)
- **Output tokens :** ~7,500 tokens (500 par item)
- **Coût estimé :** ~$0.50-0.75 USD

---

## 🎯 Signaux LAI Détectés (Succès)

### Technologies LAI Extraites
- **Extended-Release Injectable** (3 occurrences)
- **Long-Acting Injectable** (2 occurrences)
- **PharmaShell®** (3 occurrences)
- **Once-Monthly Injection** (1 occurrence)

### Molécules LAI Identifiées
- **olanzapine** (2 occurrences)
- **risperidone** (1 occurrence)
- **UZEDY®** (3 occurrences)
- **GLP-1** (1 occurrence)

### Sociétés Pure-Player LAI
- **MedinCell** (7 items)
- **Nanexa** (6 items)
- **Teva** (partenaire LAI)

---

## 🔄 Prochaine Étape : Phase 4

**Phase 4 – Analyse S3 (Ingested + Curated)**

**Actions prioritaires :**
1. ✅ Télécharger et comparer fichiers ingested vs curated
2. ⚠️ **INVESTIGUER le problème de matching 0%**
3. ✅ Analyser la structure des données curated
4. ✅ Valider la préparation pour newsletter

**Fichiers disponibles :**
- `analysis/ingested_items_lai_v4.json` (12.6 KiB)
- `analysis/curated_items_lai_v4.json` (38.8 KiB)

---

**Phase 3 terminée avec SUCCÈS PARTIEL - Normalisation 100%, Matching 0% (problème critique à investiguer)**