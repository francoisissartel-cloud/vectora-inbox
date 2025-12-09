# Script de redeploiement de la Lambda engine apres refactor matching generique
# Ce script :
# 1. Upload les nouvelles configs canonical (matching rules, scoring rules)
# 2. Re-package et upload le code engine
# 3. Met a jour la Lambda engine

$ErrorActionPreference = "Stop"

Write-Host "=== Redeploiement Lambda Engine - Refactor Matching Generique ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$AWS_PROFILE = "rag-lai-prod"
$AWS_REGION = "eu-west-3"
$CONFIG_BUCKET = "vectora-inbox-config-dev"
$LAMBDA_CODE_BUCKET = "vectora-inbox-lambda-code-dev"
$LAMBDA_FUNCTION_NAME = "vectora-inbox-engine-dev"

Write-Host "Configuration :" -ForegroundColor Yellow
Write-Host "  - Profil AWS : $AWS_PROFILE"
Write-Host "  - Region : $AWS_REGION"
Write-Host "  - Bucket config : $CONFIG_BUCKET"
Write-Host "  - Bucket code : $LAMBDA_CODE_BUCKET"
Write-Host "  - Lambda : $LAMBDA_FUNCTION_NAME"
Write-Host ""

# Etape 1 : Upload des nouvelles configs canonical
Write-Host "[1/4] Upload des nouvelles configs canonical dans S3..." -ForegroundColor Green

Write-Host "  - Upload de canonical/matching/domain_matching_rules.yaml"
aws s3 cp canonical/matching/domain_matching_rules.yaml `
    s3://$CONFIG_BUCKET/canonical/matching/domain_matching_rules.yaml `
    --profile $AWS_PROFILE --region $AWS_REGION

Write-Host "  - Upload de canonical/scoring/scoring_rules.yaml (mise a jour)"
aws s3 cp canonical/scoring/scoring_rules.yaml `
    s3://$CONFIG_BUCKET/canonical/scoring/scoring_rules.yaml `
    --profile $AWS_PROFILE --region $AWS_REGION

Write-Host "  OK Configs canonical uploadees" -ForegroundColor Green
Write-Host ""

# Etape 2 : Re-package du code engine
Write-Host "[2/4] Re-packaging du code engine..." -ForegroundColor Green

# Creer un repertoire temporaire pour le package
$TEMP_DIR = "temp_engine_package"
if (Test-Path $TEMP_DIR) {
    Remove-Item -Recurse -Force $TEMP_DIR
}
New-Item -ItemType Directory -Path $TEMP_DIR | Out-Null

# Copier le code source
Write-Host "  - Copie du code source..."
Copy-Item -Recurse -Path "src/vectora_core" -Destination "$TEMP_DIR/vectora_core"
Copy-Item -Path "src/lambdas/engine/handler.py" -Destination "$TEMP_DIR/handler.py"

# Installer les dependances
Write-Host "  - Installation des dependances..."
pip install -r requirements.txt -t $TEMP_DIR --quiet

# Creer le ZIP
Write-Host "  - Creation du fichier ZIP..."
$ZIP_FILE = "engine.zip"
if (Test-Path $ZIP_FILE) {
    Remove-Item -Force $ZIP_FILE
}

# Utiliser PowerShell pour creer le ZIP
Compress-Archive -Path "$TEMP_DIR/*" -DestinationPath $ZIP_FILE -Force

# Nettoyer le repertoire temporaire
Remove-Item -Recurse -Force $TEMP_DIR

$ZIP_SIZE_MB = [math]::Round((Get-Item $ZIP_FILE).Length / 1MB, 2)
Write-Host "  OK Package cree : $ZIP_FILE ($ZIP_SIZE_MB MB)" -ForegroundColor Green
Write-Host ""

# Etape 3 : Upload du package dans S3
Write-Host "[3/4] Upload du package dans S3..." -ForegroundColor Green

aws s3 cp $ZIP_FILE s3://$LAMBDA_CODE_BUCKET/lambda/engine/latest.zip `
    --profile $AWS_PROFILE --region $AWS_REGION

Write-Host "  OK Package uploade dans s3://$LAMBDA_CODE_BUCKET/lambda/engine/latest.zip" -ForegroundColor Green
Write-Host ""

# Etape 4 : Mise a jour de la Lambda
Write-Host "[4/4] Mise a jour de la fonction Lambda..." -ForegroundColor Green

aws lambda update-function-code `
    --function-name $LAMBDA_FUNCTION_NAME `
    --s3-bucket $LAMBDA_CODE_BUCKET `
    --s3-key "lambda/engine/latest.zip" `
    --profile $AWS_PROFILE `
    --region $AWS_REGION `
    --output json | ConvertFrom-Json | Select-Object FunctionName, LastModified, CodeSize, Runtime

Write-Host "  OK Lambda mise a jour" -ForegroundColor Green
Write-Host ""

# Nettoyage
Write-Host "Nettoyage..." -ForegroundColor Yellow
Remove-Item -Force $ZIP_FILE
Write-Host "  OK Fichier ZIP supprime" -ForegroundColor Green
Write-Host ""

Write-Host "=== Redeploiement termine avec succes ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prochaines etapes :" -ForegroundColor Yellow
Write-Host "  1. Tester la Lambda avec : .\scripts\test-engine-matching-refactor.ps1"
Write-Host "  2. Verifier les logs CloudWatch"
Write-Host "  3. Analyser les resultats dans docs/diagnostics/"
Write-Host ""
