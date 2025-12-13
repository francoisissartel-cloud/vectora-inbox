# Package Engine Lambda P1 - Newsletter Hybride et Cache
# Usage: .\scripts\package-engine-p1-fixed.ps1

Write-Host "🚀 Packaging Engine Lambda P1..." -ForegroundColor Green
Write-Host "============================================================"

# Configuration
$ENGINE_DIR = "src\lambdas\engine"
$PACKAGE_NAME = "engine-p1-newsletter-optimized.zip"
$TEMP_DIR = "temp-engine-p1"

# Nettoyage préalable
Write-Host "🧹 Nettoyage..." -ForegroundColor Yellow
if (Test-Path $TEMP_DIR) {
    Remove-Item -Recurse -Force $TEMP_DIR
}
if (Test-Path $PACKAGE_NAME) {
    Remove-Item -Force $PACKAGE_NAME
}

# Création répertoire temporaire
Write-Host "📁 Création répertoire temporaire..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $TEMP_DIR | Out-Null

# Copie des dépendances Lambda
Write-Host "📦 Copie dépendances Lambda..." -ForegroundColor Yellow
Copy-Item -Recurse -Path "lambda-deps\*" -Destination $TEMP_DIR

# Copie du code source vectora_core avec modifications P1
Write-Host "📝 Copie vectora_core P1..." -ForegroundColor Yellow
Copy-Item -Recurse -Path "src\vectora_core" -Destination $TEMP_DIR

# Copie du handler engine avec modifications P1
Write-Host "🔧 Copie handler engine P1..." -ForegroundColor Yellow
Copy-Item -Path "$ENGINE_DIR\handler.py" -Destination "$TEMP_DIR\handler.py"

# Vérification fichiers critiques P1
Write-Host "✅ Vérification fichiers P1..." -ForegroundColor Yellow

$critical_files = @(
    "$TEMP_DIR\handler.py",
    "$TEMP_DIR\vectora_core\newsletter\bedrock_client.py",
    "$TEMP_DIR\vectora_core\newsletter\assembler.py"
)

foreach ($file in $critical_files) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        Write-Host "  ✅ $file ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ MANQUANT: $file" -ForegroundColor Red
        exit 1
    }
}

# Vérification modifications P1 dans bedrock_client.py
Write-Host "🔍 Vérification modifications P1..." -ForegroundColor Yellow
$bedrock_content = Get-Content "$TEMP_DIR\vectora_core\newsletter\bedrock_client.py" -Raw

$p1_features = @(
    "get_bedrock_client_hybrid",
    "get_cached_newsletter", 
    "save_editorial_to_cache",
    "_build_ultra_compact_prompt"
)

foreach ($feature in $p1_features) {
    if ($bedrock_content -match $feature) {
        Write-Host "  ✅ P1 Feature: $feature" -ForegroundColor Green
    } else {
        Write-Host "  ❌ MANQUANT P1: $feature" -ForegroundColor Red
        exit 1
    }
}

# Création du package ZIP
Write-Host "📦 Création package ZIP..." -ForegroundColor Yellow
Push-Location $TEMP_DIR
try {
    Compress-Archive -Path "*" -DestinationPath "..\$PACKAGE_NAME" -CompressionLevel Optimal
    Write-Host "  ✅ Package créé: $PACKAGE_NAME" -ForegroundColor Green
} finally {
    Pop-Location
}

# Vérification package final
if (Test-Path $PACKAGE_NAME) {
    $package_size = (Get-Item $PACKAGE_NAME).Length
    $package_size_mb = [math]::Round($package_size / 1MB, 2)
    Write-Host "📊 Taille package: $package_size_mb MB" -ForegroundColor Cyan
    
    if ($package_size_mb -lt 50) {
        Write-Host "  ✅ Taille acceptable pour AWS Lambda" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ Taille élevée (limite 50MB)" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Échec création package" -ForegroundColor Red
    exit 1
}

# Nettoyage
Write-Host "🧹 Nettoyage final..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $TEMP_DIR

# Résumé
Write-Host "============================================================"
Write-Host "✅ PACKAGING P1 TERMINÉ" -ForegroundColor Green
Write-Host ""
Write-Host "📦 Package: $PACKAGE_NAME ($package_size_mb MB)" -ForegroundColor Cyan
Write-Host "🎯 Fonctionnalités P1 incluses:" -ForegroundColor Cyan
Write-Host "  • Client Bedrock hybride (eu-west-3 newsletter)" -ForegroundColor White
Write-Host "  • Cache S3 newsletter" -ForegroundColor White
Write-Host "  • Prompt ultra-réduit (-80% tokens)" -ForegroundColor White
Write-Host "  • Handler mis à jour avec paramètres P1" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Prêt pour déploiement AWS DEV" -ForegroundColor Green