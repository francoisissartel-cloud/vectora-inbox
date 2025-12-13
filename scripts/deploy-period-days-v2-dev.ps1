# Script de déploiement de la fonctionnalité period_days v2 sur AWS DEV
# Ce script déploie la nouvelle logique de résolution de période temporelle

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$CONFIG_BUCKET = "vectora-inbox-config-dev"

Write-Host "=== Déploiement period_days v2 sur AWS DEV ===" -ForegroundColor Cyan
Write-Host "Profile: $PROFILE" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host "Config Bucket: $CONFIG_BUCKET" -ForegroundColor Yellow
Write-Host ""

# Phase A : Sync des configurations vers S3
Write-Host "=== Phase A : Sync des configurations vers S3 ===" -ForegroundColor Cyan

Write-Host "Sync du canonical..." -ForegroundColor Yellow
aws s3 sync canonical/ s3://$CONFIG_BUCKET/canonical/ `
  --profile $PROFILE `
  --region $REGION `
  --delete

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors du sync canonical" -ForegroundColor Red
    exit 1
}

Write-Host "Sync des client configs..." -ForegroundColor Yellow
aws s3 sync client-config-examples/ s3://$CONFIG_BUCKET/clients/ `
  --profile $PROFILE `
  --region $REGION `
  --delete

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors du sync client configs" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Phase A terminée : Configurations synchronisées" -ForegroundColor Green
Write-Host ""

# Vérification des configurations
Write-Host "=== Vérification des configurations ===" -ForegroundColor Cyan

Write-Host "Vérification de lai_weekly_v2.yaml..." -ForegroundColor Yellow
aws s3 cp s3://$CONFIG_BUCKET/clients/lai_weekly_v2.yaml lai_weekly_from_s3.yaml `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -eq 0) {
    $content = Get-Content lai_weekly_from_s3.yaml -Raw
    if ($content -match "default_period_days:\s*30") {
        Write-Host "✅ lai_weekly_v2.yaml contient default_period_days: 30" -ForegroundColor Green
    } else {
        Write-Host "⚠️  lai_weekly_v2.yaml ne contient pas default_period_days: 30" -ForegroundColor Yellow
        Write-Host "Contenu pipeline trouvé:" -ForegroundColor Gray
        $content | Select-String -Pattern "pipeline:" -Context 5
    }
} else {
    Write-Host "❌ Impossible de télécharger lai_weekly_v2.yaml" -ForegroundColor Red
}

Write-Host ""

# Phase B : Re-package et update des Lambdas
Write-Host "=== Phase B : Re-package et update des Lambdas ===" -ForegroundColor Cyan

Write-Host "Package de la Lambda engine..." -ForegroundColor Yellow
& .\scripts\package-engine.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors du package engine" -ForegroundColor Red
    exit 1
}

Write-Host "Package de la Lambda ingest-normalize..." -ForegroundColor Yellow
& .\scripts\package-ingest-normalize.ps1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors du package ingest-normalize" -ForegroundColor Red
    exit 1
}

Write-Host "Update de vectora-inbox-engine-dev..." -ForegroundColor Yellow
aws lambda update-function-code `
  --function-name vectora-inbox-engine-dev `
  --zip-file fileb://engine-v2.zip `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors de l'update engine" -ForegroundColor Red
    exit 1
}

Write-Host "Update de vectora-inbox-ingest-normalize-dev..." -ForegroundColor Yellow
aws lambda update-function-code `
  --function-name vectora-inbox-ingest-normalize-dev `
  --zip-file fileb://ingest-normalize-v2.zip `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors de l'update ingest-normalize" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Phase B terminée : Lambdas mises à jour" -ForegroundColor Green
Write-Host ""

# Vérification des Lambdas
Write-Host "=== Vérification des Lambdas ===" -ForegroundColor Cyan

Write-Host "Vérification de vectora-inbox-engine-dev..." -ForegroundColor Yellow
$engineInfo = aws lambda get-function --function-name vectora-inbox-engine-dev --profile $PROFILE --region $REGION | ConvertFrom-Json
$engineLastModified = $engineInfo.Configuration.LastModified
Write-Host "  LastModified: $engineLastModified" -ForegroundColor Gray

Write-Host "Vérification de vectora-inbox-ingest-normalize-dev..." -ForegroundColor Yellow
$ingestInfo = aws lambda get-function --function-name vectora-inbox-ingest-normalize-dev --profile $PROFILE --region $REGION | ConvertFrom-Json
$ingestLastModified = $ingestInfo.Configuration.LastModified
Write-Host "  LastModified: $ingestLastModified" -ForegroundColor Gray

Write-Host ""

# Phase C : Test rapide
Write-Host "=== Phase C : Test rapide ===" -ForegroundColor Cyan

Write-Host "Test de base avec lai_weekly_v2 (sans period_days)..." -ForegroundColor Yellow

$testPayload = @{
    client_id = "lai_weekly_v2"
} | ConvertTo-Json

$testPayload | Out-File -FilePath test-deploy-validation.json -Encoding utf8

aws lambda invoke `
  --function-name vectora-inbox-engine-dev `
  --payload file://test-deploy-validation.json `
  --profile $PROFILE `
  --region $REGION `
  out-deploy-validation.json

if ($LASTEXITCODE -eq 0) {
    $response = Get-Content out-deploy-validation.json | ConvertFrom-Json
    if ($response.statusCode -eq 200) {
        Write-Host "✅ Test rapide réussi" -ForegroundColor Green
        $period = $response.body.period
        if ($period) {
            Write-Host "  Période utilisée: $($period.from_date) → $($period.to_date)" -ForegroundColor Gray
        }
    } else {
        Write-Host "⚠️  Test rapide échoué (statusCode: $($response.statusCode))" -ForegroundColor Yellow
        Write-Host "  Erreur: $($response.body.error)" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Erreur lors du test rapide" -ForegroundColor Red
}

Write-Host ""

# Résumé
Write-Host "=== Résumé du déploiement ===" -ForegroundColor Magenta
Write-Host "✅ Configurations synchronisées vers S3" -ForegroundColor Green
Write-Host "✅ Lambdas mises à jour avec le nouveau code" -ForegroundColor Green
Write-Host "✅ Test rapide effectué" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Yellow
Write-Host "  1. Exécuter .\scripts\test-period-days-v2-dev.ps1 pour tests complets" -ForegroundColor Gray
Write-Host "  2. Vérifier les logs CloudWatch pour validation" -ForegroundColor Gray
Write-Host "  3. Documenter les résultats" -ForegroundColor Gray

Write-Host ""
Write-Host "=== Déploiement terminé ===" -ForegroundColor Cyan