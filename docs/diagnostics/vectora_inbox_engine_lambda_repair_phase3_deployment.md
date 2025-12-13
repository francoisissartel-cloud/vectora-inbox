# Vectora Inbox Engine Lambda - Phase 3 Déploiement

**Date** : 2025-12-11  
**Phase** : 3 - Déploiement ENGINE uniquement  
**Status** : ✅ TERMINÉ

---

## Commandes Exécutées

### 1. Upload S3
```bash
aws s3 cp engine-only.zip s3://vectora-inbox-lambda-code-dev/lambda/engine/latest.zip \
  --profile rag-lai-prod --region eu-west-3
```
**Résultat** : ✅ Upload réussi (17.4 MB)

### 2. Mise à jour du code Lambda
```bash
aws lambda update-function-code \
  --function-name vectora-inbox-engine-dev \
  --s3-bucket vectora-inbox-lambda-code-dev \
  --s3-key lambda/engine/latest.zip \
  --profile rag-lai-prod --region eu-west-3
```
**Résultat** : ✅ Code mis à jour
- **CodeSize** : 18,257,990 bytes (~17.4 MB)
- **CodeSha256** : `VmPLEigNBIko/o8ka0NqrjDMgbPOZWyKMSbPYC7T534=`
- **LastModified** : 2025-12-11T21:42:58.000+0000

### 3. Mise à jour de la configuration
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-engine-dev \
  --handler src.lambdas.engine.handler.lambda_handler \
  --timeout 900 \
  --profile rag-lai-prod --region eu-west-3
```
**Résultat** : ✅ Configuration mise à jour
- **Handler** : `src.lambdas.engine.handler.lambda_handler` ✅
- **Timeout** : 900 secondes ✅
- **LastModified** : 2025-12-11T21:44:41.000+0000

---

## Configuration Finale Validée

### vectora-inbox-engine-dev
- **FunctionName** : vectora-inbox-engine-dev
- **Runtime** : python3.12
- **Handler** : `src.lambdas.engine.handler.lambda_handler` ✅ CORRECT
- **Timeout** : 900 secondes ✅ CORRECT
- **MemorySize** : 512 MB
- **CodeSize** : 18,257,990 bytes (~17.4 MB)
- **State** : Active
- **LastUpdateStatus** : InProgress → Successful

### Variables d'Environnement (Inchangées)
- **CONFIG_BUCKET** : vectora-inbox-config-dev
- **NEWSLETTERS_BUCKET** : vectora-inbox-newsletters-dev
- **DATA_BUCKET** : vectora-inbox-data-dev
- **ENV** : dev
- **BEDROCK_MODEL_ID** : eu.anthropic.claude-sonnet-4-5-20250929-v1:0
- **LOG_LEVEL** : INFO
- **PROJECT_NAME** : vectora-inbox

---

## Comparaison Avant/Après

### Avant (Problématique)
- **Handler** : `handler.lambda_handler` ❌ INCORRECT
- **CodeSize** : 18,323,202 bytes
- **CodeSha256** : `/AOGT0YqcrFX9rLHHpT+mTS36k56fxjP1YJ/CZL4ZOI=`
- **Contenu** : Code mixte (engine + ingest)

### Après (Correct)
- **Handler** : `src.lambdas.engine.handler.lambda_handler` ✅ CORRECT
- **CodeSize** : 18,257,990 bytes (-65,212 bytes)
- **CodeSha256** : `VmPLEigNBIko/o8ka0NqrjDMgbPOZWyKMSbPYC7T534=`
- **Contenu** : Code engine uniquement

---

## Validation Technique

### ✅ Code Déployé
- Package engine-only.zip uploadé avec succès
- Nouveau SHA256 confirme le changement de code
- Réduction de taille : -65,212 bytes (code ingest supprimé)

### ✅ Handler Corrigé
- **Ancien** : `handler.lambda_handler` (générique)
- **Nouveau** : `src.lambdas.engine.handler.lambda_handler` (spécifique engine)
- Point d'entrée correct vers le code engine

### ✅ Configuration Maintenue
- Timeout 900s maintenu (nécessaire pour engine)
- Variables d'environnement préservées
- Runtime et mémoire inchangés

### ✅ Lambda Ingest Non Modifiée
- vectora-inbox-ingest-normalize-dev non touchée
- Configuration ingest préservée
- Aucun impact sur l'ingestion

---

## Scripts Créés

### `scripts/package-engine-simple.ps1`
- Packaging engine uniquement
- Validation du contenu
- Génération engine-only.zip

### `scripts/deploy-engine-dev-simple.ps1`
- Upload S3 automatisé
- Mise à jour code + configuration
- Validation finale

---

## Critères de Succès Phase 3 ✅

- [x] Code engine uploadé en S3 : `s3://vectora-inbox-lambda-code-dev/lambda/engine/latest.zip`
- [x] Lambda engine mise à jour avec bon handler : `src.lambdas.engine.handler.lambda_handler`
- [x] Timeout configuré à 900s
- [x] Lambda ingest non modifiée
- [x] Nouveau CodeSha256 confirme le changement

---

## Prochaines Étapes Phase 4

1. **Invocation test** : `aws lambda invoke` avec payload lai_weekly_v3
2. **Analyse logs** : Vérifier logs engine (matching/scoring/newsletter)
3. **Validation** : Confirmer absence de logs ingestion
4. **Diagnostic** : Évaluer le succès de la réparation

---

**Phase 3 terminée - Lambda ENGINE déployée avec le bon code et handler**