# Script de packaging des Lambdas avec modifications trademark v2

param(
    [string]$Profile = "rag-lai-prod",
    [string]$Region = "eu-west-3"
)

$ErrorActionPreference = "Stop"

Write-Host "=== PACKAGING LAMBDAS TRADEMARK V2 ===" -ForegroundColor Cyan

$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot

# Package ingest-normalize
Write-Host "[INFO] Package ingest-normalize..." -ForegroundColor Yellow
$ingest_zip = "$PROJECT_ROOT\ingest-normalize-v2.zip"
if (Test-Path $ingest_zip) { Remove-Item $ingest_zip -Force }

Push-Location "$PROJECT_ROOT\src"
try {
    Compress-Archive -Path * -DestinationPath $ingest_zip -Force
    Write-Host "[OK] ingest-normalize package: $ingest_zip" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Echec package ingest-normalize: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

# Package engine
Write-Host "[INFO] Package engine..." -ForegroundColor Yellow
$engine_zip = "$PROJECT_ROOT\engine-v2.zip"
if (Test-Path $engine_zip) { Remove-Item $engine_zip -Force }

Push-Location "$PROJECT_ROOT\src"
try {
    Compress-Archive -Path * -DestinationPath $engine_zip -Force
    Write-Host "[OK] engine package: $engine_zip" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Echec package engine: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

Write-Host "=== PACKAGING TERMINE ===" -ForegroundColor Green