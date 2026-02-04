# Rapport Promotion DEV → STAGE

**Date**: 2026-02-04  
**Statut**: ✅ **RÉUSSI**

---

## 🎯 RÉSULTAT FINAL

**STAGE fonctionne identiquement à DEV**

- ✅ 62% items relevant (identique à dev)
- ✅ Score moyen: 76 (identique à dev)
- ✅ Domain scoring activé
- ✅ Workflow E2E validé

---

## 🔍 PROBLÈME IDENTIFIÉ

**Variables d'environnement manquantes sur STAGE**

Les Lambdas stage n'avaient pas les variables :
- `ENV` (dev avait "dev", stage n'avait rien)
- `LOG_LEVEL` (dev avait "INFO", stage n'avait rien)
- `PROJECT_NAME` (dev avait "vectora-inbox", stage n'avait rien)

**Impact** : Le code ne s'exécutait pas correctement sans ces variables.

---

## ✅ ACTIONS RÉALISÉES

### 1. Suppression complète layers stage
- Suppression de toutes les versions existantes
- Nettoyage complet

### 2. Copie layers DEV → STAGE
- vectora-core:62 (dev) → vectora-core:9 (stage)
- common-deps:23 (dev) → common-deps:8 (stage)

### 3. Copie code Lambdas DEV → STAGE
- vectora-inbox-ingest-v2
- vectora-inbox-normalize-score-v2
- vectora-inbox-newsletter-v2

### 4. Synchronisation config S3
- canonical/ : DEV → STAGE (sync complet)
- clients/lai_weekly_v23.yaml : copié

### 5. Correction variables d'environnement
**Avant** :
```
STAGE: CONFIG_BUCKET, DATA_BUCKET, BEDROCK_REGION, BEDROCK_MODEL_ID
```

**Après** :
```
STAGE: CONFIG_BUCKET, DATA_BUCKET, BEDROCK_REGION, BEDROCK_MODEL_ID, 
       ENV=stage, LOG_LEVEL=INFO, PROJECT_NAME=vectora-inbox
```

---

## 📊 VALIDATION

### Test E2E lai_weekly_v23 sur STAGE

**Résultats** :
- Total items: 32
- Items relevant: 20 (62%)
- Score moyen: 76.0
- has_domain_scoring: True

**Comparaison DEV vs STAGE** :
| Métrique | DEV | STAGE | Statut |
|----------|-----|-------|--------|
| Items relevant | 20/32 (62%) | 20/32 (62%) | ✅ Identique |
| Score moyen | 76.0 | 76.0 | ✅ Identique |
| Domain scoring | Activé | Activé | ✅ Identique |

---

## 🔧 CONFIGURATION FINALE STAGE

### Layers
- `vectora-inbox-vectora-core-stage:9`
- `vectora-inbox-common-deps-stage:8`

### Lambdas
- `vectora-inbox-ingest-v2-stage`
- `vectora-inbox-normalize-score-v2-stage`
- `vectora-inbox-newsletter-v2-stage`

### Variables d'environnement (normalize-score-v2-stage)
```
CONFIG_BUCKET: vectora-inbox-config-stage
DATA_BUCKET: vectora-inbox-data-stage
BEDROCK_REGION: us-east-1
BEDROCK_MODEL_ID: anthropic.claude-3-sonnet-20240229-v1:0
ENV: stage
LOG_LEVEL: INFO
PROJECT_NAME: vectora-inbox
```

### Configuration S3
- `s3://vectora-inbox-config-stage/canonical/` : Synchronisé avec dev
- `s3://vectora-inbox-config-stage/clients/lai_weekly_v23.yaml` : Copié

---

## 📝 LEÇONS APPRISES

1. **Les variables d'environnement sont critiques** : Ne pas oublier de copier TOUTES les variables, pas seulement les buckets
2. **Les layers ne suffisent pas** : Il faut aussi copier le code des Lambdas elles-mêmes
3. **Vérifier l'identité complète** : Layers + Code Lambda + Variables env + Config S3

---

## 🚀 PROCHAINES ÉTAPES

1. ✅ Stage validé avec lai_weekly_v23
2. ⏳ Tester avec données fraîches sur stage
3. ⏳ Créer environnement prod
4. ⏳ Documenter procédure de promotion

---

**Promotion réussie** : DEV → STAGE opérationnel et validé
