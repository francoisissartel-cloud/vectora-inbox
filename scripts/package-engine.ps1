# Script de packaging de la Lambda engine
# Ce script crée un package ZIP du code de la Lambda engine et l'uploade dans S3

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"

Write-Host "=== Packaging Lambda engine ===" -ForegroundColor Cyan

# Créer le package ZIP
Write-Host "Création du package ZIP..." -ForegroundColor Yellow
Push-Location src
if (Test-Path "../engine-v2.zip") {
    Remove-Item "../engine-v2.zip" -Force
}
Compress-Archive -Path * -DestinationPath ../engine-v2.zip -Force
Pop-Location

Write-Host "Package créé : engine-v2.zip" -ForegroundColor Green

# Uploader dans S3
Write-Host "Upload du package dans S3..." -ForegroundColor Yellow
aws s3 cp engine-v2.zip s3://$ARTIFACTS_BUCKET/lambda/engine/v2-latest.zip `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "Package uploadé avec succès dans s3://$ARTIFACTS_BUCKET/lambda/engine/v2-latest.zip" -ForegroundColor Green
} else {
    Write-Host "Erreur lors de l'upload du package" -ForegroundColor Red
    exit 1
}

# Nettoyer
Remove-Item engine-v2.zip -Force

Write-Host "=== Packaging terminé ===" -ForegroundColor Cyan
