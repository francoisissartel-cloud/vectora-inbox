# Script de déploiement de la Lambda ingest-normalize avec profils d'ingestion en DEV
# Ce script package et déploie la Lambda avec les nouvelles fonctionnalités

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$LAMBDA_NAME = "vectora-inbox-ingest-normalize-dev"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"

Write-Host "=== Déploiement Lambda ingest-normalize avec profils d'ingestion en DEV ===" -ForegroundColor Cyan

# Étape 1 : Packaging
Write-Host "Étape 1 : Packaging du code..." -ForegroundColor Yellow
& .\package-ingest-normalize.ps1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors du packaging" -ForegroundColor Red
    exit 1
}

# Étape 2 : Mise à jour de la Lambda
Write-Host "Étape 2 : Mise à jour de la Lambda $LAMBDA_NAME..." -ForegroundColor Yellow
aws lambda update-function-code `
  --function-name $LAMBDA_NAME `
  --s3-bucket $ARTIFACTS_BUCKET `
  --s3-key "lambda/ingest-normalize/profiles-latest.zip" `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "Lambda mise à jour avec succès" -ForegroundColor Green
} else {
    Write-Host "Erreur lors de la mise à jour de la Lambda" -ForegroundColor Red
    exit 1
}

# Étape 3 : Attendre que la Lambda soit prête
Write-Host "Étape 3 : Attente de la mise à jour..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Étape 4 : Vérifier le statut de la Lambda
Write-Host "Étape 4 : Vérification du statut..." -ForegroundColor Yellow
$lambdaInfo = aws lambda get-function --function-name $LAMBDA_NAME --profile $PROFILE --region $REGION | ConvertFrom-Json

Write-Host "Statut de la Lambda :" -ForegroundColor Cyan
Write-Host "  - Nom : $($lambdaInfo.Configuration.FunctionName)" -ForegroundColor White
Write-Host "  - Runtime : $($lambdaInfo.Configuration.Runtime)" -ForegroundColor White
Write-Host "  - Taille du code : $([math]::Round($lambdaInfo.Configuration.CodeSize / 1MB, 1)) MB" -ForegroundColor White
Write-Host "  - SHA256 : $($lambdaInfo.Configuration.CodeSha256)" -ForegroundColor White
Write-Host "  - Dernière modification : $($lambdaInfo.Configuration.LastModified)" -ForegroundColor White

Write-Host "=== Déploiement terminé avec succès ===" -ForegroundColor Green
Write-Host "La Lambda $LAMBDA_NAME est prête à être testée avec les profils d'ingestion" -ForegroundColor Green