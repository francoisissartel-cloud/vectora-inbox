# Script de packaging ENGINE UNIQUEMENT
# Ce script crée un package ZIP contenant SEULEMENT le code engine (pas ingest)

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"

Write-Host "=== Packaging Lambda ENGINE uniquement ===" -ForegroundColor Cyan

# Nettoyer le dossier de build précédent
if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
}
New-Item -ItemType Directory -Path "dist" -Force | Out-Null

# Copier uniquement les éléments nécessaires pour l'ENGINE
Write-Host "Copie du code engine..." -ForegroundColor Yellow

# Copier vectora_core (logique métier commune)
Copy-Item "src\vectora_core" -Destination "dist\vectora_core" -Recurse -Force

# Copier le handler engine spécifique
New-Item -ItemType Directory -Path "dist\src" -Force | Out-Null
New-Item -ItemType Directory -Path "dist\src\lambdas" -Force | Out-Null
Copy-Item "src\lambdas\engine" -Destination "dist\src\lambdas\engine" -Recurse -Force

# Copier les dépendances (depuis lambda-deps)
Write-Host "Copie des dépendances..." -ForegroundColor Yellow
$dependencies = @(
    "boto3", "botocore", "requests", "urllib3", "certifi", "charset_normalizer",
    "idna", "s3transfer", "jmespath", "dateutil", "python_dateutil-2.9.0.post0.dist-info",
    "feedparser", "bs4", "soupsieve", "yaml", "six.py", "typing_extensions.py",
    "sgmllib.py", "_yaml"
)

foreach ($dep in $dependencies) {
    if (Test-Path "lambda-deps\$dep") {
        Copy-Item "lambda-deps\$dep" -Destination "dist\$dep" -Recurse -Force
    }
}

# Copier les dist-info nécessaires
$distInfos = Get-ChildItem "lambda-deps" -Filter "*.dist-info"
foreach ($distInfo in $distInfos) {
    Copy-Item $distInfo.FullName -Destination "dist\$($distInfo.Name)" -Recurse -Force
}

# Créer le package ZIP
Write-Host "Création du package ZIP engine..." -ForegroundColor Yellow
Push-Location dist
if (Test-Path "..\engine-only.zip") {
    Remove-Item "..\engine-only.zip" -Force
}
Compress-Archive -Path * -DestinationPath ..\engine-only.zip -Force
Pop-Location

Write-Host "Package créé : engine-only.zip" -ForegroundColor Green

# Vérifier le contenu du package
Write-Host "Vérification du contenu du package..." -ForegroundColor Yellow
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead("engine-only.zip")
$engineHandlerFound = $false
$ingestHandlerFound = $false

foreach ($entry in $zip.Entries) {
    if ($entry.FullName -eq "src/lambdas/engine/handler.py") {
        $engineHandlerFound = $true
        Write-Host "✅ Handler engine trouvé : $($entry.FullName)" -ForegroundColor Green
    }
    if ($entry.FullName -like "*ingest_normalize*") {
        $ingestHandlerFound = $true
        Write-Host "❌ Code ingest trouvé : $($entry.FullName)" -ForegroundColor Red
    }
    # Debug: afficher quelques entrées pour vérification
    if ($entry.FullName -like "src/lambdas/*") {
        Write-Host "Debug: $($entry.FullName)" -ForegroundColor Gray
    }
}
$zip.Dispose()

if ($engineHandlerFound -and -not $ingestHandlerFound) {
    Write-Host "✅ Package validé : contient engine uniquement" -ForegroundColor Green
} else {
    Write-Host "❌ Package invalide : problème de contenu" -ForegroundColor Red
    if (-not $engineHandlerFound) {
        Write-Host "   - Handler engine manquant" -ForegroundColor Red
    }
    if ($ingestHandlerFound) {
        Write-Host "   - Code ingest présent (à supprimer)" -ForegroundColor Red
    }
    exit 1
}

Write-Host "=== Packaging ENGINE terminé ===" -ForegroundColor Cyan