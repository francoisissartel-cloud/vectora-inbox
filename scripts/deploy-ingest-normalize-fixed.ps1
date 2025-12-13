# Script de déploiement corrigé : ingest-normalize avec structure Lambda correcte

param(
    [string]$Profile = "rag-lai-prod",
    [string]$Region = "eu-west-3"
)

Write-Host "=== Déploiement ingest-normalize (structure corrigée) ===" -ForegroundColor Green

# Variables
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SrcDir = Join-Path $ProjectRoot "src"
$TempDir = Join-Path $ProjectRoot "temp_lambda"
$ZipFile = Join-Path $TempDir "ingest-normalize-fixed.zip"

# Nettoyer et créer le répertoire temporaire
if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

Write-Host "Préparation de la structure Lambda..." -ForegroundColor Cyan

# Copier le handler à la racine
Copy-Item -Path "$SrcDir\lambdas\ingest_normalize\handler.py" -Destination $TempDir -Force

# Copier tout vectora_core
$VectoraCoreSource = Join-Path $SrcDir "vectora_core"
$VectoraCoreTarget = Join-Path $TempDir "vectora_core"
Copy-Item -Path $VectoraCoreSource -Destination $VectoraCoreTarget -Recurse -Force

# Copier les dépendances Python (tous les autres modules dans src)
$PythonModules = @("boto3", "botocore", "requests", "feedparser", "bs4", "yaml", "dateutil", "certifi", "charset_normalizer", "idna", "jmespath", "s3transfer", "six", "soupsieve", "urllib3", "typing_extensions")

foreach ($Module in $PythonModules) {
    $ModulePath = Join-Path $SrcDir $Module
    if (Test-Path $ModulePath) {
        Copy-Item -Path $ModulePath -Destination $TempDir -Recurse -Force
        Write-Host "  Copié: $Module" -ForegroundColor Gray
    }
}

# Copier les fichiers .py à la racine de src (si il y en a)
Get-ChildItem -Path $SrcDir -Filter "*.py" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $TempDir -Force
}

Write-Host "Structure Lambda préparée dans $TempDir" -ForegroundColor Yellow

# Créer le ZIP
Write-Host "Création de l'archive ZIP..." -ForegroundColor Cyan
Compress-Archive -Path "$TempDir\*" -DestinationPath $ZipFile -Force

# Vérifier la taille
$ZipSize = (Get-Item $ZipFile).Length / 1MB
Write-Host "Taille de l'archive: $([math]::Round($ZipSize, 2)) MB" -ForegroundColor Yellow

# Déployer
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

} catch {
    Write-Host "❌ Erreur lors du déploiement: $_" -ForegroundColor Red
    exit 1
}

# Nettoyer
Remove-Item $TempDir -Recurse -Force

Write-Host "=== Déploiement terminé ===" -ForegroundColor Green