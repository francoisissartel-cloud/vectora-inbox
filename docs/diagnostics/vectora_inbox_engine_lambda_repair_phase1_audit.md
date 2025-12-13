# Vectora Inbox Engine Lambda - Phase 1 Audit

**Date** : 2025-12-11  
**Phase** : 1 - Audit AWS & Repo  
**Status** : ✅ TERMINÉ

---

## Audit AWS Lambdas

### vectora-inbox-engine-dev
- **Handler** : `handler.lambda_handler`
- **Runtime** : python3.12
- **Timeout** : 900s (15 min) ✅
- **Memory** : 512 MB
- **CodeSize** : 18,323,202 bytes (~18.3 MB)
- **CodeSha256** : `/AOGT0YqcrFX9rLHHpT+mTS36k56fxjP1YJ/CZL4ZOI=`
- **LastModified** : 2025-12-11T21:01:24.000+0000
- **Environment Variables** :
  - CONFIG_BUCKET: vectora-inbox-config-dev
  - NEWSLETTERS_BUCKET: vectora-inbox-newsletters-dev
  - DATA_BUCKET: vectora-inbox-data-dev
  - ENV: dev
  - BEDROCK_MODEL_ID: eu.anthropic.claude-sonnet-4-5-20250929-v1:0
  - LOG_LEVEL: INFO
  - PROJECT_NAME: vectora-inbox

### vectora-inbox-ingest-normalize-dev
- **Handler** : `handler.lambda_handler`
- **Runtime** : python3.12
- **Timeout** : 600s (10 min)
- **Memory** : 512 MB
- **CodeSize** : 18,298,875 bytes (~18.3 MB)
- **CodeSha256** : `KhCQ9S2isQo8fVH1N6Ew8/6qqoXbepweNy6U7VIw0Ec=`
- **LastModified** : 2025-12-11T16:31:47.000+0000
- **Environment Variables** :
  - CONFIG_BUCKET: vectora-inbox-config-dev
  - PUBMED_API_KEY_PARAM: /rag-lai/dev/pubmed/api-key
  - DATA_BUCKET: vectora-inbox-data-dev
  - ENV: dev
  - BEDROCK_MODEL_ID: eu.anthropic.claude-sonnet-4-5-20250929-v1:0
  - LOG_LEVEL: INFO
  - PROJECT_NAME: vectora-inbox

---

## Audit Repo - Structure du Code

### Handlers Identifiés
1. **Engine Handler** : `src/lambdas/engine/handler.py`
   - Point d'entrée : `lambda_handler(event, context)`
   - Fonction appelée : `run_engine_for_client()` depuis `vectora_core`
   - Responsabilité : Matching, scoring, génération newsletter

2. **Ingest Handler** : `src/lambdas/ingest_normalize/handler.py`
   - Point d'entrée : `lambda_handler(event, context)`
   - Fonction appelée : `run_ingest_normalize_for_client()` depuis `vectora_core`
   - Responsabilité : Ingestion et normalisation des sources

### Scripts de Packaging
- **Engine** : `scripts/package-engine.ps1` ✅ EXISTE
  - Package : `engine-v2.zip`
  - Upload S3 : `s3://vectora-inbox-lambda-code-dev/lambda/engine/v2-latest.zip`
  - Source : Tout le dossier `src/`

---

## Analyse du Problème

### 🔴 Problème Identifié : Handler Identique
**Observation critique** : Les deux Lambdas utilisent le même handler `handler.lambda_handler`, mais :
- **CodeSize quasi-identique** : 18.3 MB vs 18.3 MB
- **Différence de SHA256** : Codes différents mais tailles similaires
- **Même structure** : Toutes deux pointent vers `handler.py` à la racine

### 🔍 Hypothèse du Problème
Le problème semble être que **les deux Lambdas contiennent le même code source complet** (tout le dossier `src/`) mais avec des handlers différents :
- **Engine** devrait pointer vers `src.lambdas.engine.handler.lambda_handler`
- **Ingest** devrait pointer vers `src.lambdas.ingest_normalize.handler.lambda_handler`

Actuellement, les deux pointent vers `handler.lambda_handler` (racine), ce qui explique pourquoi l'engine exécute du code d'ingestion.

### 🎯 Handler Correct pour Engine
Basé sur l'analyse du code, le handler correct pour l'engine devrait être :
**`src.lambdas.engine.handler.lambda_handler`**

---

## Structure Actuelle vs Attendue

### Structure Actuelle (Problématique)
```
Lambda engine-dev:
├── handler.py (MAUVAIS - handler générique)
├── src/
│   ├── lambdas/
│   │   ├── engine/handler.py (BON handler engine)
│   │   └── ingest_normalize/handler.py (BON handler ingest)
│   └── vectora_core/
└── dependencies/
```

### Structure Attendue (Correcte)
```
Lambda engine-dev:
├── src/
│   ├── lambdas/
│   │   └── engine/handler.py (POINT D'ENTRÉE)
│   └── vectora_core/
└── dependencies/

Handler configuré: src.lambdas.engine.handler.lambda_handler
```

---

## Recommandations Phase 2

1. **Modifier le script de packaging** pour créer un package engine-only
2. **Corriger le handler** vers `src.lambdas.engine.handler.lambda_handler`
3. **Vérifier l'absence de code ingest** dans le package engine
4. **Tester localement** l'intégrité du package

---

## Critères de Succès Phase 1 ✅

- [x] Configuration complète des 2 Lambdas documentée
- [x] Code source engine identifié dans le repo
- [x] Handler correct de l'engine déterminé : `src.lambdas.engine.handler.lambda_handler`
- [x] Scripts de packaging localisés
- [x] Problème de wiring identifié : handler incorrect + code mixte

---

**Phase 1 terminée - Problème identifié : Handler incorrect et code mixte dans les deux Lambdas**