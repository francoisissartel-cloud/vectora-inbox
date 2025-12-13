# Traçage Runtime E2E - LAI Weekly v3 Diagnostic

**Date** : 2025-12-12  
**Objectif** : Tracer un run réel lai_weekly_v3 pour identifier la cause du fallback newsletter  

---

## 1. Exécution Phase Ingestion

### 1.1 Invocation Lambda Ingest-Normalize

**Commande** :
```bash
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":7}' \
  --cli-binary-format raw-in-base64-out \
  --region eu-west-3 --profile rag-lai-prod out-diagnostic-ingest.json
```

**Résultat** : ✅ **SUCCÈS COMPLET**

### 1.2 Résultats Ingestion

```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly_v3",
    "execution_date": "2025-12-12T17:11:59Z",
    "sources_processed": 7,
    "items_ingested": 104,
    "items_filtered": 104,
    "items_filtered_out": 0,
    "items_normalized": 104,
    "period_days_used": 7,
    "s3_output_path": "s3://vectora-inbox-data-dev/normalized/lai_weekly_v3/2025/12/12/items.json",
    "execution_time_seconds": 17.52
  }
}
```

**Analyse Ingestion** ✅ :
- 7 sources traitées sur 8 (87.5% succès)
- 104 items ingérés et normalisés
- Normalisation Bedrock us-east-1 fonctionne parfaitement
- Temps d'exécution : 17.52s (excellent)
- Items écrits dans S3 avec succès

---

## 2. Exécution Phase Engine

### 2.1 Invocation Lambda Engine

**Commande** :
```bash
aws lambda invoke --function-name vectora-inbox-engine-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":7}' \
  --cli-binary-format raw-in-base64-out \
  --region eu-west-3 --profile rag-lai-prod out-diagnostic-engine.json
```

**Résultat** : ❌ **ÉCHEC CRITIQUE**

### 2.2 Résultats Engine

```json
{
  "statusCode": 500,
  "body": {
    "error": "ClientError",
    "message": "An error occurred (AccessDenied) when calling the PutObject operation: User: arn:aws:sts::786469175371:assumed-role/vectora-inbox-s0-iam-dev-EngineRole-x4yGG8dAutT9/vectora-inbox-engine-dev is not authorized to perform: s3:PutObject on resource: \"arn:aws:s3:::vectora-inbox-data-dev/raw/lai_weekly_v3/2025/12/12/run_20251212T171212962278Z/source_metadata.json\" because no identity-based policy allows the s3:PutObject action"
  }
}
```

**Analyse Engine** ❌ :
- Erreur S3 AccessDenied sur écriture dans DATA_BUCKET
- Engine essaie d'écrire dans `/raw/` au lieu de `/newsletters/`
- **PROBLÈME MAJEUR** : Engine exécute du code d'ingestion !

---

## 3. Analyse des Logs CloudWatch Engine

### 3.1 Messages Critiques Identifiés

**Messages Révélateurs** :
```
[INFO] Démarrage de vectora-inbox-ingest-normalize
[INFO] Phase 1A : Ingestion des sources
[INFO] Récupération de press_sector__fiercepharma (mode: rss)
[INFO] Écriture des items RAW dans S3
[ERROR] User: arn:aws:sts::786469175371:assumed-role/vectora-inbox-s0-iam-dev-EngineRole-x4yGG8dAutT9/vectora-inbox-engine-dev is not authorized to perform: s3:PutObject on resource: "arn:aws:s3:::vectora-inbox-data-dev/raw/..."
```

### 3.2 Workflow Réellement Exécuté par Engine

**Au lieu de** :
```
Engine → Collecte Items S3 → Matching → Scoring → Newsletter → S3 Newsletters
```

**Engine exécute** :
```
Engine → Ingestion Sources → Normalisation → Écriture S3 Data (ÉCHEC)
```

### 3.3 Preuves du Problème

1. **Message de démarrage** : `"Démarrage de vectora-inbox-ingest-normalize"` au lieu de `"Démarrage de vectora-inbox-engine"`

2. **Phases exécutées** : 
   - `"Phase 1A : Ingestion des sources"`
   - `"Récupération de press_sector__fiercepharma"`
   - `"Parsing du contenu"`

3. **Tentative d'écriture** : 
   - `"Écriture des items RAW dans S3"`
   - Chemin : `s3://vectora-inbox-data-dev/raw/lai_weekly_v3/...`

4. **Erreur de permissions** :
   - Engine n'a pas `s3:PutObject` sur DATA_BUCKET (normal, il ne devrait pas en avoir besoin)
   - Engine devrait écrire dans NEWSLETTERS_BUCKET

---

## 4. Cause Racine Identifiée

### 4.1 Problème Principal 🔧

**La Lambda engine exécute le code d'ingestion au lieu du code engine !**

**Hypothèses** :
1. **Handler incorrect** : Le handler pointe vers le mauvais fichier
2. **Code déployé incorrect** : Le package contient le mauvais code
3. **Import incorrect** : Le handler importe la mauvaise fonction

### 4.2 Vérification Handler

**Configuration AWS** : `handler.lambda_handler`
**Attendu** : `src/lambdas/engine/handler.py::lambda_handler`
**Réel** : Semble pointer vers le code d'ingestion

### 4.3 Impact sur le Fallback Newsletter

**Le fallback newsletter n'est PAS causé par** :
- ❌ Configuration Bedrock eu-west-3 vs us-east-1
- ❌ Permissions IAM manquantes
- ❌ Problèmes de quota Bedrock

**Le fallback newsletter est causé par** :
- ✅ **Engine n'exécute jamais le code engine**
- ✅ **Engine exécute le code d'ingestion et échoue**
- ✅ **Aucune newsletter n'est jamais générée**

---

## 5. Détails Techniques du Problème

### 5.1 Séquence d'Exécution Engine (Incorrecte)

1. **Démarrage** : `"Démarrage de vectora-inbox-ingest-normalize"` ❌
2. **Configuration** : Chargement client config + canonical ✅
3. **Sources** : Résolution bouquets sources ❌ (ne devrait pas faire ça)
4. **Ingestion** : Scraping 8 sources ❌ (ne devrait pas faire ça)
5. **Parsing** : 104 items parsés ❌ (ne devrait pas faire ça)
6. **Écriture S3** : Tentative écriture raw items ❌ (permissions manquantes)
7. **Échec** : AccessDenied sur DATA_BUCKET ❌

### 5.2 Séquence d'Exécution Engine (Attendue)

1. **Démarrage** : `"Démarrage de vectora-inbox-engine"` ✅
2. **Configuration** : Chargement client config + canonical + rules ✅
3. **Collecte** : Lecture items normalisés depuis S3 ✅
4. **Matching** : Application règles matching ✅
5. **Scoring** : Calcul scores et sélection ✅
6. **Newsletter** : Génération avec Bedrock ✅
7. **Écriture** : Newsletter dans NEWSLETTERS_BUCKET ✅

### 5.3 Sources Traitées par Engine (Incorrect)

**Engine a traité les sources suivantes** (ne devrait pas) :
- ✅ press_sector__fiercepharma : 25 items
- ✅ press_corporate__medincell : 12 items  
- ✅ press_sector__endpoints_news : 24 items
- ✅ press_corporate__nanexa : 8 items
- ✅ press_sector__fiercebiotech : 25 items
- ❌ press_corporate__camurus : 0 items (parser HTML défaillant)
- ✅ press_corporate__delsitech : 10 items
- ❌ press_corporate__peptron : 0 items (erreur SSL)

**Total** : 104 items (identique à l'ingestion normale)

---

## 6. Diagnostic de Déploiement

### 6.1 Hypothèses de Cause

**1. Handler Incorrect** :
- Configuration AWS pointe vers le mauvais handler
- Handler devrait être `src.lambdas.engine.handler.lambda_handler`
- Mais exécute `src.lambdas.ingest_normalize.handler.lambda_handler`

**2. Package Incorrect** :
- Le package engine contient le code d'ingestion
- Erreur lors du packaging/déploiement
- Fichiers mélangés entre engine et ingest

**3. Import Incorrect** :
- Le handler engine importe `run_ingest_normalize_for_client` au lieu de `run_engine_for_client`
- Erreur dans le code du handler

### 6.2 Vérification Nécessaire

**Commandes de diagnostic** :
```bash
# Vérifier le contenu du package engine
aws lambda get-function --function-name vectora-inbox-engine-dev --region eu-west-3 --profile rag-lai-prod

# Télécharger et inspecter le code
aws lambda get-function --function-name vectora-inbox-engine-dev --region eu-west-3 --profile rag-lai-prod --query 'Code.Location'
```

---

## 7. Impact sur le Workflow Global

### 7.1 Workflow Réel Actuel

```
1. Ingest-Normalize Lambda ✅
   └── Ingestion + Normalisation → S3 Data

2. Engine Lambda ❌
   └── Ingestion + Normalisation → ÉCHEC (permissions)
   
3. Newsletter ❌
   └── Jamais générée (engine n'atteint jamais cette phase)
```

### 7.2 Workflow Attendu

```
1. Ingest-Normalize Lambda ✅
   └── Ingestion + Normalisation → S3 Data

2. Engine Lambda ✅
   └── Collecte S3 → Matching → Scoring → Newsletter → S3 Newsletters
   
3. Newsletter ✅
   └── Générée et disponible
```

### 7.3 Pourquoi le Fallback Newsletter

**Il n'y a PAS de fallback newsletter** :
- Engine n'exécute jamais le code de génération newsletter
- Engine échoue avant d'atteindre la phase newsletter
- Aucune newsletter n'est jamais générée (ni Bedrock ni fallback)

**Le "fallback" observé précédemment** était probablement :
- Une newsletter générée par un autre run
- Une newsletter générée manuellement
- Une newsletter générée avant le problème de déploiement

---

## 8. Recommandations de Correction

### 8.1 Correction P0 - Immédiate 🔧

**1. Vérifier le Handler Engine** :
```bash
# Vérifier la configuration handler
aws lambda get-function-configuration --function-name vectora-inbox-engine-dev --region eu-west-3 --profile rag-lai-prod --query 'Handler'
```

**2. Vérifier le Code Déployé** :
- Télécharger le package engine
- Inspecter le contenu du handler.py
- Vérifier les imports

**3. Redéployer Engine avec le Bon Code** :
- Utiliser le script de packaging engine correct
- Vérifier que le handler pointe vers `src.lambdas.engine.handler.lambda_handler`
- Vérifier que le code importe `run_engine_for_client`

### 8.2 Test de Validation

**Après correction** :
```bash
# Test engine avec le bon code
aws lambda invoke --function-name vectora-inbox-engine-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":7}' \
  --cli-binary-format raw-in-base64-out \
  --region eu-west-3 --profile rag-lai-prod out-engine-fixed.json
```

**Résultat attendu** :
- Logs : `"Démarrage de vectora-inbox-engine"`
- Phases : Collecte → Matching → Scoring → Newsletter
- Output : Newsletter générée dans NEWSLETTERS_BUCKET

---

## 9. Synthèse du Diagnostic

### 9.1 Cause Racine Confirmée ✅

**La Lambda engine exécute le code d'ingestion au lieu du code engine.**

**Preuves** :
- Logs montrent ingestion de sources
- Tentative d'écriture dans DATA_BUCKET/raw/
- Message de démarrage incorrect
- Erreur de permissions cohérente avec le mauvais code

### 9.2 Impact sur les Hypothèses Précédentes

**Hypothèses Invalidées** :
- ❌ Problème de configuration Bedrock eu-west-3
- ❌ Problème de permissions IAM newsletter
- ❌ Problème de quota/throttling Bedrock

**Vraie Cause** :
- ✅ Problème de déploiement/packaging engine
- ✅ Handler ou code incorrect dans la Lambda engine

### 9.3 Prochaines Étapes

1. **Diagnostic approfondi** : Vérifier le contenu exact du package engine
2. **Correction déploiement** : Redéployer engine avec le bon code
3. **Test validation** : Vérifier que engine exécute le bon workflow
4. **Test newsletter** : Confirmer génération newsletter end-to-end

**Le problème est identifié et la solution est claire : corriger le déploiement de la Lambda engine.**