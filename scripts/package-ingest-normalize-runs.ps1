# Script de packaging de la Lambda ingest-normalize avec logique par runs
# Ce script crée un package ZIP du code de la Lambda ingest-normalize refactorisée et l'uploade dans S3

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"

Write-Host "=== Packaging Lambda ingest-normalize avec logique par runs ===" -ForegroundColor Cyan

# Vérifier que les modifications sont présentes
Write-Host "Vérification des modifications..." -ForegroundColor Yellow

$dateUtilsPath = "lambda-deps\vectora_core\utils\date_utils.py"
if (!(Test-Path $dateUtilsPath)) {
    Write-Host "ERREUR: Fichier date_utils.py non trouvé" -ForegroundColor Red
    exit 1
}

$dateUtilsContent = Get-Content $dateUtilsPath -Raw
if (!$dateUtilsContent.Contains("generate_run_id")) {
    Write-Host "ERREUR: Fonction generate_run_id non trouvée dans date_utils.py" -ForegroundColor Red
    exit 1
}

$s3ClientPath = "lambda-deps\vectora_core\storage\s3_client.py"
if (!(Test-Path $s3ClientPath)) {
    Write-Host "ERREUR: Fichier s3_client.py non trouvé" -ForegroundColor Red
    exit 1
}

$s3ClientContent = Get-Content $s3ClientPath -Raw
if (!$s3ClientContent.Contains("write_raw_items_to_s3")) {
    Write-Host "ERREUR: Fonction write_raw_items_to_s3 non trouvée dans s3_client.py" -ForegroundColor Red
    exit 1
}

$initPath = "lambda-deps\vectora_core\__init__.py"
if (!(Test-Path $initPath)) {
    Write-Host "ERREUR: Fichier __init__.py non trouvé" -ForegroundColor Red
    exit 1
}

$initContent = Get-Content $initPath -Raw
if (!$initContent.Contains("run_id = date_utils.generate_run_id()")) {
    Write-Host "ERREUR: Logique run_id non trouvée dans __init__.py" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Toutes les modifications sont présentes" -ForegroundColor Green

# Créer le package ZIP depuis lambda-deps (qui contient le code mis à jour)
Write-Host "Création du package ZIP depuis lambda-deps/..." -ForegroundColor Yellow
$packagePath = "ingest-normalize-runs.zip"
Push-Location lambda-deps
if (Test-Path ../$packagePath) {
    Remove-Item ../$packagePath -Force
}
Compress-Archive -Path * -DestinationPath ../$packagePath -Force
Pop-Location

Write-Host "Package créé : ingest-normalize-runs.zip" -ForegroundColor Green

# Afficher la taille du package
$packageSize = (Get-Item $packagePath).Length / 1MB
Write-Host "Taille du package : $([math]::Round($packageSize, 2)) MB" -ForegroundColor Green

# Uploader dans S3
Write-Host "Upload du package dans S3..." -ForegroundColor Yellow
aws s3 cp ingest-normalize-runs.zip s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/runs-latest.zip `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "Package uploadé avec succès dans s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/runs-latest.zip" -ForegroundColor Green
} else {
    Write-Host "Erreur lors de l'upload du package" -ForegroundColor Red
    exit 1
}

# Créer aussi une version avec timestamp pour archivage
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$archivedPath = "runs-$timestamp.zip"
Write-Host "Création d'une version archivée..." -ForegroundColor Yellow
aws s3 cp ingest-normalize-runs.zip s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/$archivedPath `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "Version archivée créée : s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/$archivedPath" -ForegroundColor Green
}

# Nettoyer
Remove-Item ingest-normalize-runs.zip -Force

Write-Host "=== Packaging terminé ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Package pret pour deploiement :" -ForegroundColor Yellow
Write-Host "   s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/runs-latest.zip" -ForegroundColor White
Write-Host ""
Write-Host "Prochaine etape : Deploiement avec deploy-runtime-runs-dev.ps1" -ForegroundColor Yellow