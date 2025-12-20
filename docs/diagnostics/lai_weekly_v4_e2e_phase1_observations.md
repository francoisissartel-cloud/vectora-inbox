# Phase 1 – Préparation & Sanity Check - lai_weekly_v4

**Date :** 19 décembre 2025  
**Durée :** 30 minutes  
**Objectif :** Vérifier l'état de l'environnement sans rien modifier  

---

## Vérifications des Fichiers de Référence

### Code Source V2

#### ✅ src_v2/lambdas/ingest/handler.py
- **Statut :** Conforme et fonctionnel
- **Fonctionnalités :** Support single-client et multi-clients
- **Variables d'env requises :** CONFIG_BUCKET, DATA_BUCKET
- **Mode d'invocation :** `{"client_id": "lai_weekly_v4"}`

#### ✅ src_v2/lambdas/normalize_score/handler.py  
- **Statut :** Conforme et fonctionnel
- **Variables d'env requises :** CONFIG_BUCKET, DATA_BUCKET, BEDROCK_MODEL_ID, BEDROCK_REGION
- **Mode d'invocation :** `{"client_id": "lai_weekly_v4"}`
- **Validation :** client_id obligatoire

#### ✅ src_v2/vectora_core/ingest/__init__.py
- **Statut :** Architecture V2 complète
- **Fonctionnalités :** Ingestion multi-sources, déduplication, validation
- **Sortie :** S3 ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json

#### ✅ src_v2/vectora_core/normalization/__init__.py
- **Statut :** Architecture Bedrock-Only Pure ACTIVE
- **Corrections appliquées :** Matching systématique (ligne 95-96)
- **Validation :** Données réelles vs synthétiques
- **Sortie :** S3 curated/{client_id}/{YYYY}/{MM}/{DD}/items.json

### Configuration Client lai_weekly_v4

#### ✅ client-config-examples/lai_weekly_v4.yaml
- **Statut :** ✅ ACTIVE (active: true)
- **Version :** 4.0.0 (Tech Focus)
- **Watch domains :** 1 seul domaine `tech_lai_ecosystem`
- **Sources :** lai_corporate_mvp + lai_press_mvp
- **Matching config :** min_domain_score: 0.25, max_domains_per_item: 1
- **Newsletter layout :** 4 sections toutes pointant vers tech_lai_ecosystem

---

## Phase 2 – Run Ingestion V2 Réel

### Invocation Lambda Ingest

**Commande d'invocation :**
```powershell
$env:AWS_PROFILE = "rag-lai-prod"
$env:AWS_DEFAULT_REGION = "eu-west-3"

aws lambda invoke `
  --function-name vectora-inbox-ingest-v2-dev `
  --payload '{"client_id": "lai_weekly_v4"}' `
  --cli-binary-format raw-in-base64-out `
  response_ingest.json
```

### Exécution en cours...