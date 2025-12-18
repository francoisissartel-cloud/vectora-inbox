# Plan de Test End-to-End : lai_weekly_v3 Workflow Complet

**Date :** 17 décembre 2025  
**Objectif :** Test end-to-end réel du workflow Vectora Inbox V2 sur lai_weekly_v3  
**Périmètre :** Ingestion V2 → Normalize + Matching + Scoring V2  
**Environnement :** AWS dev (buckets *-dev)  

---

## Contexte & Objectif

### Rappel lai_weekly_v3
**lai_weekly_v3** est le client MVP pour l'intelligence LAI (Long-Acting Injectables) :
- **Domaines surveillés** : tech_lai_ecosystem (technology) + regulatory_lai (regulatory)
- **Sources** : 8 sources (5 corporate LAI + 3 presse sectorielle)
- **Scopes** : 180+ entreprises LAI, 90+ molécules, 80+ technologies, 70+ trademarks
- **Configuration** : Matching V2 config-driven avec seuils ajustés (0.25/0.30/0.20)

### Objectif du Test
Vérifier le pipeline réel **ingest V2 → normalize+match+score V2** sur données de production :
- Validation fonctionnelle complète du workflow
- Métriques quantitatives détaillées (items, scores, coûts)
- Analyse qualitative item par item
- Estimation coûts Bedrock et performance

---

## Environnement

### Configuration AWS
- **Profil AWS** : `rag-lai-prod`
- **Région Lambda** : `eu-west-3` (Paris)
- **Région Bedrock** : `us-east-1` (Virginie du Nord)
- **Compte AWS** : `786469175371`

### Buckets Utilisés
- **CONFIG_BUCKET** : `vectora-inbox-config-dev`
- **DATA_BUCKET** : `vectora-inbox-data-dev`

### Lambdas Utilisées
- **Ingestion V2** : `vectora-inbox-ingest-v2-dev` (handler ingest_v2)
- **Normalize Score V2** : `vectora-inbox-normalize-score-v2-dev` (handler normalize_score_v2)

---

## Cartographie S3 du Workflow

### Où l'ingestion écrit (chemins S3 raw)
```
s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/2025/12/17/items.json
```
**Structure attendue :**
- Items parsés depuis 8 sources (lai_corporate_mvp + lai_press_mvp)
- Format JSON avec item_id, source_key, title, content, url, published_at
- Métadonnées : content_hash, word_count, language

### Où normalize_score V2 écrit (chemins S3 curated)
```
s3://vectora-inbox-data-dev/curated/lai_weekly_v3/2025/12/17/items.json
```
**Structure attendue :**
- Items enrichis avec normalized_content (entités, classification)
- matching_results avec matched_domains et domain_relevance
- scoring_results avec scores finaux et breakdown détaillé

### Identification lai_weekly_v3
- **client_id** : "lai_weekly_v3"
- **Date** : YYYY/MM/DD (2025/12/17)
- **Run ID** : Timestamp d'exécution dans les métadonnées

---

## Scénario de Test

### Client Unique
**lai_weekly_v3** uniquement (isolation complète)

### Cycle Complet
1. **Trigger ingestion V2** avec payload `{"client_id": "lai_weekly_v3"}`
2. **Puis trigger normalize_score V2** sur le dernier run ingest avec même payload
3. **Hypothèse** : Lambdas détectent automatiquement les configs actives

### Méthode d'Activation
**Script Python boto3** (contournement AWS CLI Windows) :
```bash
python scripts/invoke_normalize_score_v2_lambda.py
```

---

## Checks et Métriques Attendues

### Pour Ingestion V2
**Métriques fonctionnelles :**
- **Nombre d'items ingérés** : 15-25 items (estimation basée sur 8 sources)
- **Répartition par source** : 
  - Corporate (5 sources) : 8-15 items
  - Presse (3 sources) : 7-10 items
- **Items filtrés vs conservés** : Ratio signal/bruit par source
- **Types de contenus** : RSS feeds, corporate news, press articles

**Métriques techniques :**
- **Temps d'exécution** : 2-5 minutes (8 sources HTTP)
- **Erreurs réseau** : Timeouts, 404, parsing failures par source
- **Taille outputs S3** : 50-150KB JSON

### Pour Normalize + Matching + Scoring V2
**Métriques de pipeline :**
- **items_input** : Nombre d'items pris du dernier run ingest
- **items_normalized** : Items traités par Bedrock avec succès
- **items_matched** : Items matchés aux domaines (objectif 60-80%)
- **items_scored** : Items avec score final calculé

**Distribution par domaine :**
- **tech_lai_ecosystem** : 8-12 items (53-66%)
- **regulatory_lai** : 3-5 items (20-33%)
- **Overlap** : 2-3 items matchés aux 2 domaines

**Stats de scoring :**
- **Min/Max/Mean par domaine** : Distribution des scores 0-20
- **Min/Max/Mean par priorité** : High priority vs autres
- **Top items** : Items avec scores > 15 (signaux forts LAI)

**Métriques Bedrock :**
- **Nombre d'appels normalisation** : 1 par item (15-25 appels)
- **Nombre d'appels matching** : 2 par item (tech + regulatory)
- **Temps moyen par appel** : 2-4 secondes
- **Tokens consommés** : Input + output par appel

---

## Coût & Performance Approximatifs

### Temps d'Exécution des Lambdas
- **Ingestion V2** : 2-5 minutes (récupération HTTP + parsing)
- **Normalize Score V2** : 3-8 minutes (appels Bedrock séquentiels)
- **Total workflow** : 5-13 minutes

### Nombre d'Appels Bedrock
**Normalisation** : 1 appel par item
- Items attendus : 15-25
- Appels normalisation : 15-25

**Matching** : 2 appels par item (tech_lai_ecosystem + regulatory_lai)
- Appels matching : 30-50

**Total Bedrock** : 45-75 appels

### Estimation Coût Bedrock
**Modèle** : `anthropic.claude-3-sonnet-20240229-v1:0`
**Hypothèse prix** : $3/1M input tokens, $15/1M output tokens

**Par appel (estimation) :**
- Input : 2000 tokens (item + prompts + scopes)
- Output : 500 tokens (entités + classification)
- Coût par appel : ~$0.015

**Coût total run :**
- 45-75 appels × $0.015 = **$0.67 - $1.13**

**Extrapolation :**
- Run hebdomadaire : $0.67 - $1.13
- Run mensuel : $2.68 - $4.52
- Run annuel : $35 - $59

---

## Livrables de la Phase E2E

### Rapport Global
**Fichier** : `docs/diagnostics/lai_weekly_v3_e2e_workflow_observation_report.md`

**Contenu** :
- Résumé du run (date, ID, temps d'exécution)
- Métriques ingestion (sources, items, filtres)
- Métriques normalisation & matching & scoring
- Coût Bedrock estimé et réel
- Utilisation config & canonical
- Synthèse qualitative (bruit, sélectivité, qualité)

### Breakdown Item par Item
**Fichier** : `docs/diagnostics/lai_weekly_v3_e2e_items_breakdown.md`

**Contenu** :
- Tableau détaillé de tous les items traités
- Pour chaque item : identité, normalisation, matching, scoring, décision
- Section "Questions pour l'analyste métier (François)"
- Recommandations d'ajustements (prompts, seuils, filtres)

---

## Préparation & Choix du Run

### Identification des Commandes
**Ingestion V2** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id": "lai_weekly_v3"}' \
  --profile rag-lai-prod \
  --region eu-west-3 \
  response_ingest.json
```

**Normalize Score V2** :
```bash
python scripts/invoke_normalize_score_v2_lambda.py
# Utilise payload: {"client_id": "lai_weekly_v3"}
```

### Vérification S3 Préalable
**Dernier run existant** :
```bash
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/ \
  --recursive --profile rag-lai-prod --region eu-west-3
```

**Structure des outputs** :
- Chemins : `ingested/lai_weekly_v3/YYYY/MM/DD/items.json`
- Noms de fichiers : `items.json` (standard)

### Run à Utiliser
**Nouveau run** que je vais déclencher pour ce test E2E :
- Date : 2025-12-17
- Ingestion fraîche depuis les 8 sources LAI
- Suivi immédiat par normalize_score V2

---

## Validation des Pré-requis

### Configuration Client
**Vérification** : `s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml`
- ✅ `active: true`
- ✅ `source_bouquets_enabled: [lai_corporate_mvp, lai_press_mvp]`
- ✅ `watch_domains` avec scopes LAI
- ✅ `matching_config` avec seuils ajustés (0.25/0.30/0.20)

### Canonical
**Vérification** : `s3://vectora-inbox-config-dev/canonical/`
- ✅ `sources/source_catalog.yaml` avec bouquets LAI
- ✅ `scopes/*.yaml` avec scopes LAI (companies, molecules, technologies, trademarks)
- ✅ `prompts/global_prompts.yaml` avec prompts Bedrock

### Lambdas
**Vérification** :
- ✅ `vectora-inbox-ingest-v2-dev` : Active, handler ingest_v2
- ✅ `vectora-inbox-normalize-score-v2-dev` : Active, handler normalize_score_v2, matching V2 config-driven déployé

---

## Critères de Succès

### Fonctionnels
1. **Ingestion réussie** : Items JSON créés dans S3 ingested/
2. **Normalisation réussie** : Items enrichis avec entités Bedrock
3. **Matching fonctionnel** : items_matched > 0 (objectif 60-80%)
4. **Scoring cohérent** : Distribution scores 0-20 avec top items LAI
5. **Configuration appliquée** : Seuils config-driven utilisés

### Techniques
1. **Pas d'erreurs Lambda** : StatusCode 200 pour les 2 invocations
2. **Temps acceptable** : < 15 minutes total
3. **Coût maîtrisé** : < $2 pour le run complet
4. **Outputs S3 valides** : JSON bien formé, métadonnées complètes

### Qualitatifs
1. **Signaux LAI détectés** : MedinCell, Camurus, UZEDY®, partnerships
2. **Bruit filtré** : Pas de sur-matching sur contenus génériques
3. **Distribution équilibrée** : Tech et regulatory représentés
4. **Pure players capturés** : Mode fallback fonctionnel

---

## Gestion des Risques

### Risques Identifiés
1. **AWS CLI Windows** : Problème d'encodage JSON → **Résolu** par script Python boto3
2. **Timeout Lambda** : Trop d'items ou appels Bedrock lents → Monitoring temps d'exécution
3. **Coût Bedrock** : Dépassement budget → Estimation préalable et alertes
4. **Configuration non appliquée** : Matching config ignorée → Vérification logs

### Mitigation
1. **Script de contournement** : `scripts/invoke_normalize_score_v2_lambda.py`
2. **Monitoring temps réel** : CloudWatch logs avec patterns
3. **Budget alerts** : Alertes si coût > $5
4. **Validation config** : Vérification lecture matching_config dans logs

---

## Planning d'Exécution

### Phase 1 : Ingestion V2 (5 min)
1. Déclencher ingestion lai_weekly_v3
2. Monitorer logs CloudWatch
3. Vérifier création S3 ingested/

### Phase 2 : Normalize Score V2 (10 min)
1. Déclencher normalize_score V2 via script Python
2. Monitorer appels Bedrock
3. Vérifier création S3 curated/

### Phase 3 : Analyse (30 min)
1. Télécharger outputs S3
2. Analyser métriques et items
3. Générer rapports détaillés

### Phase 4 : Synthèse (15 min)
1. Résumé métriques clés
2. Points forts et améliorations
3. Recommandations pour itération suivante

---

**Plan complet et prêt pour exécution**  
**Durée estimée totale** : 1 heure  
**Impact attendu** : Validation complète du workflow V2 sur données réelles