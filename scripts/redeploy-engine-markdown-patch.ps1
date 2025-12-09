# Script de redéploiement de la Lambda engine avec le patch Markdown
# Ce script repackage et redéploie la Lambda vectora-inbox-engine-dev

$ErrorActionPreference = "Stop"

# Variables
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"
$LAMBDA_NAME = "vectora-inbox-engine-dev"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Redéploiement Lambda Engine - Patch Markdown" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Étape 1 : Créer le répertoire de build
Write-Host "[1/5] Préparation du répertoire de build..." -ForegroundColor Yellow
$BUILD_DIR = "build-engine-patch"
if (Test-Path $BUILD_DIR) {
    Remove-Item -Recurse -Force $BUILD_DIR
}
New-Item -ItemType Directory -Path $BUILD_DIR | Out-Null

# Étape 2 : Copier le code source
Write-Host "[2/5] Copie du code source..." -ForegroundColor Yellow
Copy-Item -Path "src\vectora_core" -Destination "$BUILD_DIR\vectora_core" -Recurse
Copy-Item -Path "src\lambdas\engine\handler.py" -Destination "$BUILD_DIR\handler.py"

# Étape 3 : Installer les dépendances
Write-Host "[3/5] Installation des dépendances..." -ForegroundColor Yellow
pip install -q -t $BUILD_DIR PyYAML boto3 requests --upgrade

# Étape 4 : Créer le package ZIP
Write-Host "[4/5] Création du package ZIP..." -ForegroundColor Yellow
$ZIP_FILE = "lambda-engine-patch.zip"
if (Test-Path $ZIP_FILE) {
    Remove-Item -Force $ZIP_FILE
}

# Créer le ZIP depuis le répertoire de build
Push-Location $BUILD_DIR
Compress-Archive -Path * -DestinationPath "..\$ZIP_FILE"
Pop-Location

$ZIP_SIZE = (Get-Item $ZIP_FILE).Length / 1MB
Write-Host "Package créé : $ZIP_FILE ($([math]::Round($ZIP_SIZE, 2)) MB)" -ForegroundColor Green

# Étape 5 : Uploader dans S3
Write-Host "[5/5] Upload vers S3..." -ForegroundColor Yellow
aws s3 cp $ZIP_FILE "s3://$ARTIFACTS_BUCKET/lambda/engine/latest.zip" `
    --profile $PROFILE `
    --region $REGION

Write-Host "Package uploadé dans s3://$ARTIFACTS_BUCKET/lambda/engine/latest.zip" -ForegroundColor Green

# Étape 6 : Mettre à jour la Lambda
Write-Host "[6/6] Mise à jour de la Lambda..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name $LAMBDA_NAME `
    --s3-bucket $ARTIFACTS_BUCKET `
    --s3-key "lambda/engine/latest.zip" `
    --profile $PROFILE `
    --region $REGION | Out-Null

Write-Host "Lambda mise à jour avec succès" -ForegroundColor Green

# Attendre que la Lambda soit prête
Write-Host "Attente de la mise à jour de la Lambda..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Nettoyage
Write-Host "Nettoyage..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $BUILD_DIR
Remove-Item -Force $ZIP_FILE

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Redéploiement terminé avec succès !" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaine étape : Tester la Lambda avec :" -ForegroundColor Cyan
Write-Host "  .\scripts\test-engine-lai-weekly.ps1" -ForegroundColor White
