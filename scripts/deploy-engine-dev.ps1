# Script de déploiement ENGINE DEV uniquement
# Ce script uploade le package engine et met à jour la Lambda engine-dev

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"
$LAMBDA_NAME = "vectora-inbox-engine-dev"
$HANDLER = "src.lambdas.engine.handler.lambda_handler"
$TIMEOUT = 900

Write-Host "=== Déploiement Lambda ENGINE DEV ===" -ForegroundColor Cyan

# Vérifier que le package existe
if (-not (Test-Path "engine-only.zip")) {
    Write-Host "❌ Package engine-only.zip introuvable" -ForegroundColor Red
    Write-Host "Exécutez d'abord: scripts\package-engine-simple.ps1" -ForegroundColor Yellow
    exit 1
}

$zipSize = (Get-Item "engine-only.zip").Length / 1MB
Write-Host "📦 Package trouvé : engine-only.zip ($([math]::Round($zipSize, 1)) MB)" -ForegroundColor Green

# Upload du package dans S3
Write-Host "⬆️ Upload du package dans S3..." -ForegroundColor Yellow
aws s3 cp engine-only.zip s3://$ARTIFACTS_BUCKET/lambda/engine/latest.zip `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de l'upload S3" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Package uploadé : s3://$ARTIFACTS_BUCKET/lambda/engine/latest.zip" -ForegroundColor Green

# Mise à jour du code de la Lambda
Write-Host "🔄 Mise à jour du code Lambda..." -ForegroundColor Yellow
aws lambda update-function-code `
  --function-name $LAMBDA_NAME `
  --s3-bucket $ARTIFACTS_BUCKET `
  --s3-key lambda/engine/latest.zip `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la mise à jour du code" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Code Lambda mis à jour" -ForegroundColor Green

# Mise à jour de la configuration (handler + timeout)
Write-Host "⚙️ Mise à jour de la configuration Lambda..." -ForegroundColor Yellow
aws lambda update-function-configuration `
  --function-name $LAMBDA_NAME `
  --handler $HANDLER `
  --timeout $TIMEOUT `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la mise à jour de la configuration" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Configuration Lambda mise à jour" -ForegroundColor Green
Write-Host "   Handler: $HANDLER" -ForegroundColor Gray
Write-Host "   Timeout: $TIMEOUT secondes" -ForegroundColor Gray

# Vérification finale
Write-Host "🔍 Vérification de la configuration..." -ForegroundColor Yellow
$config = aws lambda get-function-configuration --function-name $LAMBDA_NAME --profile $PROFILE --region $REGION | ConvertFrom-Json

Write-Host "📋 Configuration finale:" -ForegroundColor Cyan
Write-Host "   Function: $($config.FunctionName)" -ForegroundColor Gray
Write-Host "   Handler: $($config.Handler)" -ForegroundColor Gray
Write-Host "   Timeout: $($config.Timeout)s" -ForegroundColor Gray
Write-Host "   Runtime: $($config.Runtime)" -ForegroundColor Gray
Write-Host "   CodeSize: $([math]::Round($config.CodeSize / 1MB, 1)) MB" -ForegroundColor Gray
Write-Host "   LastModified: $($config.LastModified)" -ForegroundColor Gray

# Validation
if ($config.Handler -eq $HANDLER -and $config.Timeout -eq $TIMEOUT) {
    Write-Host "✅ Déploiement ENGINE réussi" -ForegroundColor Green
} else {
    Write-Host "⚠️ Configuration partiellement mise à jour" -ForegroundColor Yellow
    Write-Host "   Handler attendu: $HANDLER, actuel: $($config.Handler)" -ForegroundColor Gray
    Write-Host "   Timeout attendu: $TIMEOUT, actuel: $($config.Timeout)" -ForegroundColor Gray
}

Write-Host "=== Déploiement ENGINE terminé ===" -ForegroundColor Cyan