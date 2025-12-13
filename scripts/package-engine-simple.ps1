# Script de packaging ENGINE UNIQUEMENT - Version simplifiée
$ErrorActionPreference = "Stop"

Write-Host "=== Packaging Lambda ENGINE uniquement ===" -ForegroundColor Cyan

# Nettoyer et créer le dossier de build
if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
}
New-Item -ItemType Directory -Path "dist" -Force | Out-Null

# Copier vectora_core
Write-Host "Copie vectora_core..." -ForegroundColor Yellow
Copy-Item "src\vectora_core" -Destination "dist\vectora_core" -Recurse -Force

# Copier le handler engine
Write-Host "Copie handler engine..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "dist\src\lambdas\engine" -Force | Out-Null
Copy-Item "src\lambdas\engine\handler.py" -Destination "dist\src\lambdas\engine\handler.py" -Force

# Copier les dépendances essentielles
Write-Host "Copie dépendances..." -ForegroundColor Yellow
$deps = @("boto3", "botocore", "requests", "urllib3", "certifi", "charset_normalizer", "idna", "s3transfer", "jmespath", "dateutil", "feedparser", "bs4", "soupsieve", "yaml", "six.py", "typing_extensions.py", "sgmllib.py", "_yaml")

foreach ($dep in $deps) {
    if (Test-Path "lambda-deps\$dep") {
        Copy-Item "lambda-deps\$dep" -Destination "dist\$dep" -Recurse -Force
    }
}

# Copier les .dist-info
Get-ChildItem "lambda-deps" -Filter "*.dist-info" | ForEach-Object {
    Copy-Item $_.FullName -Destination "dist\$($_.Name)" -Recurse -Force
}

# Créer le ZIP
Write-Host "Création ZIP..." -ForegroundColor Yellow
Push-Location dist
if (Test-Path "..\engine-only.zip") {
    Remove-Item "..\engine-only.zip" -Force
}
Compress-Archive -Path * -DestinationPath ..\engine-only.zip -Force
Pop-Location

# Vérification simple
if (Test-Path "dist\src\lambdas\engine\handler.py") {
    Write-Host "✅ Handler engine présent dans dist/" -ForegroundColor Green
} else {
    Write-Host "❌ Handler engine manquant dans dist/" -ForegroundColor Red
    exit 1
}

if (Test-Path "engine-only.zip") {
    $zipSize = (Get-Item "engine-only.zip").Length / 1MB
    Write-Host "✅ Package créé : engine-only.zip ($([math]::Round($zipSize, 1)) MB)" -ForegroundColor Green
} else {
    Write-Host "❌ Échec création ZIP" -ForegroundColor Red
    exit 1
}

Write-Host "=== Packaging ENGINE terminé ===" -ForegroundColor Cyan