# Script de redéploiement de la Lambda ingest-normalize avec le nouveau code de retry
# Usage: .\scripts\redeploy-ingest-normalize.ps1

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"
$FUNCTION_NAME = "vectora-inbox-ingest-normalize-dev"

Write-Host "=== Redéploiement de la Lambda ingest-normalize avec mécanisme de retry Bedrock ===" -ForegroundColor Cyan
Write-Host ""

# Étape 1 : Packaging
Write-Host "[1/4] Packaging de la Lambda..." -ForegroundColor Yellow

# Créer un répertoire temporaire
$TEMP_DIR = "temp_lambda_package"
if (Test-Path $TEMP_DIR) {
    Remove-Item -Recurse -Force $TEMP_DIR
}
New-Item -ItemType Directory -Path $TEMP_DIR | Out-Null

# Copier le code source
Write-Host "  - Copie du code source..."
Copy-Item -Recurse "src/lambdas/ingest_normalize/*" "$TEMP_DIR/"
Copy-Item -Recurse "src/vectora_core" "$TEMP_DIR/"

# Installer les dépendances
Write-Host "  - Installation des dépendances Python..."
pip install -r requirements.txt -t $TEMP_DIR --quiet

# Créer le ZIP
Write-Host "  - Création du fichier ZIP..."
$ZIP_FILE = "ingest-normalize-with-retry.zip"
if (Test-Path $ZIP_FILE) {
    Remove-Item $ZIP_FILE
}

# Utiliser Compress-Archive (PowerShell natif)
Push-Location $TEMP_DIR
Compress-Archive -Path * -DestinationPath "..\$ZIP_FILE"
Pop-Location

# Nettoyer le répertoire temporaire
Remove-Item -Recurse -Force $TEMP_DIR

$ZIP_SIZE_MB = [math]::Round((Get-Item $ZIP_FILE).Length / 1MB, 2)
Write-Host "  ✓ Package créé : $ZIP_FILE ($ZIP_SIZE_MB MB)" -ForegroundColor Green
Write-Host ""

# Étape 2 : Upload vers S3
Write-Host "[2/4] Upload vers S3..." -ForegroundColor Yellow
aws s3 cp $ZIP_FILE "s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/latest.zip" `
    --profile $PROFILE `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Upload réussi vers s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/latest.zip" -ForegroundColor Green
} else {
    Write-Host "  ✗ Erreur lors de l'upload vers S3" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Étape 3 : Mise à jour du code de la Lambda
Write-Host "[3/4] Mise à jour du code de la Lambda..." -ForegroundColor Yellow
aws lambda update-function-code `
    --function-name $FUNCTION_NAME `
    --s3-bucket $ARTIFACTS_BUCKET `
    --s3-key "lambda/ingest-normalize/latest.zip" `
    --profile $PROFILE `
    --region $REGION `
    --output json | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Code de la Lambda mis à jour" -ForegroundColor Green
} else {
    Write-Host "  ✗ Erreur lors de la mise à jour de la Lambda" -ForegroundColor Red
    exit 1
}

# Attendre que la Lambda soit prête
Write-Host "  - Attente de la mise à jour de la Lambda..."
Start-Sleep -Seconds 5
Write-Host ""

# Étape 4 : Test de la Lambda
Write-Host "[4/4] Test de la Lambda..." -ForegroundColor Yellow
Write-Host "  - Invocation avec l'événement de test..."

$TEST_EVENT = "tests/events/test-ingest-small-batch.json"
$OUTPUT_FILE = "out-test-retry-mechanism.json"

aws lambda invoke `
    --function-name $FUNCTION_NAME `
    --payload file://$TEST_EVENT `
    --cli-binary-format raw-in-base64-out `
    $OUTPUT_FILE `
    --profile $PROFILE `
    --region $REGION `
    --output json | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Lambda invoquée avec succès" -ForegroundColor Green
    Write-Host ""
    
    # Afficher le résultat
    Write-Host "=== Résultat de l'invocation ===" -ForegroundColor Cyan
    $result = Get-Content $OUTPUT_FILE | ConvertFrom-Json
    $result | ConvertTo-Json -Depth 10
    Write-Host ""
    
    # Vérifier le statut
    if ($result.statusCode -eq 200) {
        Write-Host "✓ Test réussi : statusCode = 200" -ForegroundColor Green
        Write-Host "  - Items ingérés : $($result.body.items_ingested)" -ForegroundColor Green
        Write-Host "  - Items normalisés : $($result.body.items_normalized)" -ForegroundColor Green
        Write-Host "  - Temps d'exécution : $($result.body.execution_time_seconds)s" -ForegroundColor Green
    } else {
        Write-Host "⚠ Test échoué : statusCode = $($result.statusCode)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ Erreur lors de l'invocation de la Lambda" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Prochaines étapes ===" -ForegroundColor Cyan
Write-Host "1. Consulter les logs CloudWatch pour vérifier les retries :"
Write-Host "   aws logs tail /aws/lambda/$FUNCTION_NAME --since 10m --filter-pattern 'Throttling' --profile $PROFILE --region $REGION"
Write-Host ""
Write-Host "2. Tester avec un batch complet (7 jours, toutes les sources) :"
Write-Host "   aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"client_id\":\"lai_weekly\",\"period_days\":7}' out.json --profile $PROFILE --region $REGION"
Write-Host ""
Write-Host "3. Monitorer les métriques pendant 1 semaine"
Write-Host ""

# Nettoyer le fichier ZIP
Remove-Item $ZIP_FILE

Write-Host "=== Redéploiement terminé ===" -ForegroundColor Green
