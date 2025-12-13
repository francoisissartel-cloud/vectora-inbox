# Script de déploiement : period_days dans ingest-normalize
# Déploie la Lambda vectora-inbox-ingest-normalize-dev avec la nouvelle logique

param(
    [string]$Profile = "rag-lai-prod",
    [string]$Region = "eu-west-3"
)

Write-Host "=== Déploiement period_days ingest-normalize ===" -ForegroundColor Green
Write-Host "Profil AWS: $Profile" -ForegroundColor Yellow
Write-Host "Région: $Region" -ForegroundColor Yellow

# Variables
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SrcDir = Join-Path $ProjectRoot "src"
$TempDir = Join-Path $ProjectRoot "temp"
$ZipFile = Join-Path $TempDir "ingest-normalize-period-days.zip"

# Nettoyer et créer le répertoire temporaire
if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

Write-Host "Packaging du code source..." -ForegroundColor Cyan

# Copier tout le contenu de src vers temp
Copy-Item -Path "$SrcDir\*" -Destination $TempDir -Recurse -Force

# Créer le ZIP
Write-Host "Création de l'archive ZIP..." -ForegroundColor Cyan
Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipFile -Force

# Vérifier la taille du ZIP
$ZipSize = (Get-Item $ZipFile).Length / 1MB
Write-Host "Taille de l'archive: $([math]::Round($ZipSize, 2)) MB" -ForegroundColor Yellow

if ($ZipSize -gt 50) {
    Write-Host "ATTENTION: Archive > 50MB, déploiement via S3 recommandé" -ForegroundColor Red
}

# Déployer la Lambda
Write-Host "Déploiement de vectora-inbox-ingest-normalize-dev..." -ForegroundColor Cyan

try {
    $UpdateResult = aws lambda update-function-code `
        --function-name "vectora-inbox-ingest-normalize-dev" `
        --zip-file "fileb://$ZipFile" `
        --profile $Profile `
        --region $Region `
        --output json | ConvertFrom-Json

    Write-Host "✅ Déploiement réussi!" -ForegroundColor Green
    Write-Host "Version: $($UpdateResult.Version)" -ForegroundColor Yellow
    Write-Host "Dernière modification: $($UpdateResult.LastModified)" -ForegroundColor Yellow
    Write-Host "Taille déployée: $($UpdateResult.CodeSize) bytes" -ForegroundColor Yellow

} catch {
    Write-Host "❌ Erreur lors du déploiement: $_" -ForegroundColor Red
    exit 1
}

# Vérifier la configuration de la Lambda
Write-Host "Vérification de la configuration Lambda..." -ForegroundColor Cyan

try {
    $LambdaConfig = aws lambda get-function-configuration `
        --function-name "vectora-inbox-ingest-normalize-dev" `
        --profile $Profile `
        --region $Region `
        --output json | ConvertFrom-Json

    Write-Host "Runtime: $($LambdaConfig.Runtime)" -ForegroundColor Yellow
    Write-Host "Timeout: $($LambdaConfig.Timeout)s" -ForegroundColor Yellow
    Write-Host "Memory: $($LambdaConfig.MemorySize)MB" -ForegroundColor Yellow
    
    # Vérifier les variables d'environnement importantes
    $EnvVars = $LambdaConfig.Environment.Variables
    Write-Host "Variables d'environnement:" -ForegroundColor Yellow
    Write-Host "  CONFIG_BUCKET: $($EnvVars.CONFIG_BUCKET)" -ForegroundColor Gray
    Write-Host "  DATA_BUCKET: $($EnvVars.DATA_BUCKET)" -ForegroundColor Gray
    Write-Host "  BEDROCK_MODEL_ID: $($EnvVars.BEDROCK_MODEL_ID)" -ForegroundColor Gray

} catch {
    Write-Host "⚠️ Impossible de récupérer la configuration Lambda: $_" -ForegroundColor Yellow
}

# Nettoyer
Write-Host "Nettoyage des fichiers temporaires..." -ForegroundColor Cyan
Remove-Item $TempDir -Recurse -Force

Write-Host "=== Déploiement terminé ===" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Cyan
Write-Host "1. Tester avec: aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev" -ForegroundColor Gray
Write-Host "2. Payload test: {`"client_id`": `"lai_weekly_v2`"}" -ForegroundColor Gray
Write-Host "3. Vérifier les logs CloudWatch pour period_days résolu" -ForegroundColor Gray