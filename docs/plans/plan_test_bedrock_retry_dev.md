# Plan de test du mécanisme de retry Bedrock - Environnement DEV

**Date** : 2025-01-XX  
**Environnement** : DEV (eu-west-3)  
**Objectif** : Déployer et valider le mécanisme de retry Bedrock avec backoff exponentiel

---

## Résumé exécutif

Ce plan décrit les étapes pour déployer le nouveau code de la Lambda `ingest-normalize` avec le mécanisme de retry Bedrock, puis valider son fonctionnement en conditions réelles.

**Durée estimée** : 30-45 minutes

---

## Prérequis

### Variables d'environnement PowerShell

```powershell
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"
$FUNCTION_NAME = "vectora-inbox-ingest-normalize-dev"
```

### Vérifications préalables

```powershell
# Vérifier que le profil AWS est actif
aws sts get-caller-identity --profile $PROFILE --region $REGION

# Vérifier que la Lambda existe
aws lambda get-function --function-name $FUNCTION_NAME --profile $PROFILE --region $REGION --query "Configuration.FunctionName"

# Vérifier que le bucket d'artefacts existe
aws s3 ls s3://$ARTIFACTS_BUCKET --profile $PROFILE --region $REGION
```

**Résultat attendu** : Toutes les commandes retournent des résultats sans erreur.

---

## Phase 1 – Redéploiement de la Lambda avec retry

### Option A : Script automatisé (recommandé)

```powershell
# Exécuter le script de redéploiement
.\scripts\redeploy-ingest-normalize.ps1
```

**Résultat attendu** :
- Package créé (~17 MB)
- Upload vers S3 réussi
- Code Lambda mis à jour
- Test automatique exécuté

### Option B : Redéploiement manuel

```powershell
# 1. Créer le répertoire temporaire
$TEMP_DIR = "temp_lambda_package"
New-Item -ItemType Directory -Path $TEMP_DIR -Force

# 2. Copier le code source
Copy-Item -Recurse "src/lambdas/ingest_normalize/*" "$TEMP_DIR/"
Copy-Item -Recurse "src/vectora_core" "$TEMP_DIR/"

# 3. Installer les dépendances
pip install -r requirements.txt -t $TEMP_DIR --quiet

# 4. Créer le ZIP
Push-Location $TEMP_DIR
Compress-Archive -Path * -DestinationPath "..\ingest-normalize-retry.zip" -Force
Pop-Location

# 5. Nettoyer
Remove-Item -Recurse -Force $TEMP_DIR

# 6. Upload vers S3
aws s3 cp ingest-normalize-retry.zip "s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/latest.zip" `
  --profile $PROFILE --region $REGION

# 7. Mettre à jour la Lambda
aws lambda update-function-code `
  --function-name $FUNCTION_NAME `
  --s3-bucket $ARTIFACTS_BUCKET `
  --s3-key "lambda/ingest-normalize/latest.zip" `
  --profile $PROFILE --region $REGION

# 8. Attendre la mise à jour
Start-Sleep -Seconds 5

# 9. Nettoyer le ZIP local
Remove-Item ingest-normalize-retry.zip
```

**Résultat attendu** : Message de confirmation de mise à jour de la Lambda.

---

## Phase 2 – Test avec petit batch (2 sources, 1 jour)

### Invoquer la Lambda avec événement de test

```powershell
aws lambda invoke `
  --function-name $FUNCTION_NAME `
  --payload file://tests/events/test-ingest-small-batch.json `
  --cli-binary-format raw-in-base64-out `
  out-test-small-batch.json `
  --profile $PROFILE `
  --region $REGION
```

### Consulter le résultat

```powershell
Get-Content out-test-small-batch.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Résultat attendu** :
```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "sources_processed": 2,
    "items_ingested": 10-50,
    "items_normalized": 10-50,
    "execution_time_seconds": 30-60
  }
}
```

### Vérifier les items normalisés dans S3

```powershell
# Lister les fichiers récents
aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly/ --recursive `
  --profile $PROFILE --region $REGION | Select-Object -Last 5

# Télécharger le dernier fichier
$TODAY = Get-Date -Format "yyyy/MM/dd"
aws s3 cp "s3://vectora-inbox-data-dev/normalized/lai_weekly/$TODAY/items.json" items-test-small.json `
  --profile $PROFILE --region $REGION

# Compter les items
$items = Get-Content items-test-small.json | ConvertFrom-Json
Write-Host "Nombre d'items normalisés : $($items.Count)"
```

**Résultat attendu** : Fichier JSON avec 10-50 items normalisés.

---

## Phase 3 – Analyse des logs CloudWatch (retries)

### Consulter les logs généraux

```powershell
aws logs tail /aws/lambda/$FUNCTION_NAME `
  --since 15m `
  --format short `
  --profile $PROFILE `
  --region $REGION
```

### Filtrer sur les retries Bedrock

```powershell
aws logs tail /aws/lambda/$FUNCTION_NAME `
  --since 15m `
  --filter-pattern "Throttling" `
  --format short `
  --profile $PROFILE `
  --region $REGION
```

**Logs attendus (si throttling)** :
```
[WARNING] ThrottlingException détectée (tentative 1/4). Retry dans 0.52s...
[WARNING] ThrottlingException détectée (tentative 2/4). Retry dans 1.03s...
[INFO] Réponse Bedrock reçue avec succès
```

**Logs attendus (si pas de throttling)** :
```
[INFO] Appel à Bedrock (tentative 1/4)
[INFO] Réponse Bedrock reçue avec succès
```

### Calculer le taux de retry

```powershell
# Compter les logs de retry
$retryLogs = aws logs filter-log-events `
  --log-group-name "/aws/lambda/$FUNCTION_NAME" `
  --start-time $((Get-Date).AddMinutes(-15).ToUniversalTime().ToString("o")) `
  --filter-pattern "ThrottlingException détectée" `
  --profile $PROFILE --region $REGION `
  --query "events[*].message" --output text

$retryCount = ($retryLogs -split "`n").Count
Write-Host "Nombre de retries détectés : $retryCount"
```

**Résultat attendu** : 0-5 retries (acceptable pour un petit batch).

---

## Phase 4 – Test avec batch complet (8 sources, 7 jours)

### Invoquer la Lambda avec batch complet

```powershell
aws lambda invoke `
  --function-name $FUNCTION_NAME `
  --payload '{"client_id":"lai_weekly","period_days":7}' `
  --cli-binary-format raw-in-base64-out `
  out-test-full-batch.json `
  --profile $PROFILE `
  --region $REGION
```

### Consulter le résultat

```powershell
Get-Content out-test-full-batch.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Résultat attendu** :
```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "sources_processed": 7-8,
    "items_ingested": 80-120,
    "items_normalized": 80-120,
    "execution_time_seconds": 120-300
  }
}
```

### Vérifier les items normalisés

```powershell
# Télécharger le fichier complet
$TODAY = Get-Date -Format "yyyy/MM/dd"
aws s3 cp "s3://vectora-inbox-data-dev/normalized/lai_weekly/$TODAY/items.json" items-test-full.json `
  --profile $PROFILE --region $REGION

# Analyser les items
$items = Get-Content items-test-full.json | ConvertFrom-Json
Write-Host "Nombre total d'items : $($items.Count)"
Write-Host "Items avec companies détectées : $(($items | Where-Object { $_.companies_detected.Count -gt 0 }).Count)"
Write-Host "Items avec summary : $(($items | Where-Object { $_.summary -ne '' }).Count)"
```

**Résultat attendu** :
- 80-120 items au total
- >50% avec companies détectées
- >90% avec summary généré

---

## Phase 5 – Analyse approfondie des logs (batch complet)

### Consulter les logs complets

```powershell
aws logs tail /aws/lambda/$FUNCTION_NAME `
  --since 30m `
  --format detailed `
  --profile $PROFILE `
  --region $REGION > logs-full-batch.txt

# Ouvrir le fichier
notepad logs-full-batch.txt
```

### Calculer les métriques de retry

```powershell
# Compter les retries
$retryLogs = aws logs filter-log-events `
  --log-group-name "/aws/lambda/$FUNCTION_NAME" `
  --start-time $((Get-Date).AddMinutes(-30).ToUniversalTime().ToString("o")) `
  --filter-pattern "ThrottlingException détectée" `
  --profile $PROFILE --region $REGION `
  --query "events[*].message" --output json | ConvertFrom-Json

$retryCount = $retryLogs.Count
Write-Host "Nombre de retries : $retryCount"

# Compter les échecs finaux
$failureLogs = aws logs filter-log-events `
  --log-group-name "/aws/lambda/$FUNCTION_NAME" `
  --start-time $((Get-Date).AddMinutes(-30).ToUniversalTime().ToString("o")) `
  --filter-pattern "Échec après" `
  --profile $PROFILE --region $REGION `
  --query "events[*].message" --output json | ConvertFrom-Json

$failureCount = $failureLogs.Count
Write-Host "Nombre d'échecs finaux : $failureCount"

# Calculer les taux
$totalItems = (Get-Content out-test-full-batch.json | ConvertFrom-Json).body.items_normalized
$retryRate = [math]::Round(($retryCount / $totalItems) * 100, 2)
$failureRate = [math]::Round(($failureCount / $totalItems) * 100, 2)

Write-Host ""
Write-Host "=== Métriques de retry ===" -ForegroundColor Cyan
Write-Host "Items normalisés : $totalItems"
Write-Host "Taux de retry : $retryRate% (objectif <20%)"
Write-Host "Taux d'échec final : $failureRate% (objectif <5%)"
```

**Résultat attendu** :
- Taux de retry : <20%
- Taux d'échec final : <5%

---

## Phase 6 – Validation et décision

### Critères de succès

✅ **Lambda déployée** : Code mis à jour sans erreur  
✅ **Petit batch réussi** : 10-50 items normalisés, statusCode 200  
✅ **Batch complet réussi** : 80-120 items normalisés, statusCode 200  
✅ **Taux de retry acceptable** : <20%  
✅ **Taux d'échec final acceptable** : <5%  
✅ **Qualité de normalisation** : >90% des items avec summary

### Décision

**Si tous les critères sont remplis** :
- ✅ Mécanisme de retry validé
- ✅ Prêt pour utilisation en production
- ⏭️ Passer à la phase de monitoring continu

**Si taux de retry >20%** :
- ⚠️ Réduire MAX_BEDROCK_WORKERS à 2
- ⚠️ Ou augmenter les quotas Bedrock via AWS Support

**Si taux d'échec final >5%** :
- ⚠️ Augmenter max_retries à 5
- ⚠️ Augmenter base_delay à 1.0s

---

## Phase 7 – Monitoring continu (optionnel)

### Créer une alerte CloudWatch

```powershell
# Créer une métrique de filtre pour les retries
aws logs put-metric-filter `
  --log-group-name "/aws/lambda/$FUNCTION_NAME" `
  --filter-name "BedrockRetryCount" `
  --filter-pattern "ThrottlingException détectée" `
  --metric-transformations `
    metricName=BedrockRetries,metricNamespace=VectoraInbox,metricValue=1 `
  --profile $PROFILE --region $REGION

# Créer une alarme si taux de retry >20%
aws cloudwatch put-metric-alarm `
  --alarm-name "vectora-inbox-bedrock-retry-high" `
  --alarm-description "Taux de retry Bedrock élevé" `
  --metric-name BedrockRetries `
  --namespace VectoraInbox `
  --statistic Sum `
  --period 300 `
  --evaluation-periods 1 `
  --threshold 20 `
  --comparison-operator GreaterThanThreshold `
  --profile $PROFILE --region $REGION
```

---

## Résumé des commandes

```powershell
# Variables
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$FUNCTION_NAME = "vectora-inbox-ingest-normalize-dev"

# Phase 1 : Redéploiement
.\scripts\redeploy-ingest-normalize.ps1

# Phase 2 : Test petit batch
aws lambda invoke --function-name $FUNCTION_NAME `
  --payload file://tests/events/test-ingest-small-batch.json `
  --cli-binary-format raw-in-base64-out out-test-small.json `
  --profile $PROFILE --region $REGION

# Phase 3 : Logs retries
aws logs tail /aws/lambda/$FUNCTION_NAME --since 15m `
  --filter-pattern "Throttling" --profile $PROFILE --region $REGION

# Phase 4 : Test batch complet
aws lambda invoke --function-name $FUNCTION_NAME `
  --payload '{"client_id":"lai_weekly","period_days":7}' `
  --cli-binary-format raw-in-base64-out out-test-full.json `
  --profile $PROFILE --region $REGION

# Phase 5 : Analyse logs
aws logs tail /aws/lambda/$FUNCTION_NAME --since 30m `
  --format detailed --profile $PROFILE --region $REGION > logs-full.txt
```

---

## Prochaines étapes après validation

1. **Documenter les résultats** dans `docs/diagnostics/bedrock_retry_results_dev.md`
2. **Mettre à jour le CHANGELOG** avec les résultats des tests
3. **Planifier le déploiement STAGE** si validation réussie
4. **Configurer le monitoring continu** avec CloudWatch Alarms

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-01-XX  
**Version** : 1.0
