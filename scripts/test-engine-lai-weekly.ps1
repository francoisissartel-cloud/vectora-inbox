# Script de test end-to-end pour la Lambda engine
# Ce script teste le workflow complet : ingest-normalize → engine

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$CLIENT_ID = "lai_weekly"
$PERIOD_DAYS = 7

Write-Host "=== Test end-to-end : ingest-normalize → engine ===" -ForegroundColor Cyan
Write-Host "Client: $CLIENT_ID" -ForegroundColor Yellow
Write-Host "Période: $PERIOD_DAYS jours" -ForegroundColor Yellow
Write-Host ""

# Étape 1 : Exécuter ingest-normalize
Write-Host "=== Étape 1 : Exécution de ingest-normalize ===" -ForegroundColor Cyan

$ingestPayload = @{
    client_id = $CLIENT_ID
    period_days = $PERIOD_DAYS
} | ConvertTo-Json

$ingestPayload | Out-File -FilePath test-event-ingest.json -Encoding utf8

Write-Host "Invocation de la Lambda ingest-normalize..." -ForegroundColor Yellow
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload file://test-event-ingest.json `
  --profile $PROFILE `
  --region $REGION `
  out-ingest-lai-weekly.json

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors de l'invocation de ingest-normalize" -ForegroundColor Red
    exit 1
}

Write-Host "Réponse de ingest-normalize:" -ForegroundColor Green
Get-Content out-ingest-lai-weekly.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "Attente de 5 secondes avant l'étape suivante..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Étape 2 : Exécuter engine
Write-Host "=== Étape 2 : Exécution de engine ===" -ForegroundColor Cyan

$enginePayload = @{
    client_id = $CLIENT_ID
    period_days = $PERIOD_DAYS
} | ConvertTo-Json

$enginePayload | Out-File -FilePath test-event-engine.json -Encoding utf8

Write-Host "Invocation de la Lambda engine..." -ForegroundColor Yellow
aws lambda invoke `
  --function-name vectora-inbox-engine-dev `
  --payload file://test-event-engine.json `
  --profile $PROFILE `
  --region $REGION `
  out-engine-lai-weekly.json

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors de l'invocation de engine" -ForegroundColor Red
    exit 1
}

Write-Host "Réponse de engine:" -ForegroundColor Green
Get-Content out-engine-lai-weekly.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

Write-Host ""

# Étape 3 : Vérifier la newsletter générée
Write-Host "=== Étape 3 : Vérification de la newsletter ===" -ForegroundColor Cyan

$engineResponse = Get-Content out-engine-lai-weekly.json | ConvertFrom-Json
$s3Path = $engineResponse.body.s3_output_path

if ($s3Path) {
    Write-Host "Newsletter générée : $s3Path" -ForegroundColor Green
    
    # Extraire le chemin S3
    $s3Path -match "s3://([^/]+)/(.+)" | Out-Null
    $bucket = $Matches[1]
    $key = $Matches[2]
    
    Write-Host "Téléchargement de la newsletter..." -ForegroundColor Yellow
    aws s3 cp s3://$bucket/$key newsletter-lai-weekly.md `
      --profile $PROFILE `
      --region $REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Newsletter téléchargée : newsletter-lai-weekly.md" -ForegroundColor Green
        Write-Host ""
        Write-Host "=== Aperçu de la newsletter ===" -ForegroundColor Cyan
        Get-Content newsletter-lai-weekly.md | Select-Object -First 30
        Write-Host "..." -ForegroundColor Gray
    } else {
        Write-Host "Erreur lors du téléchargement de la newsletter" -ForegroundColor Red
    }
} else {
    Write-Host "Aucun chemin S3 trouvé dans la réponse" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test terminé ===" -ForegroundColor Cyan
Write-Host "Fichiers générés:" -ForegroundColor Yellow
Write-Host "  - test-event-ingest.json" -ForegroundColor Gray
Write-Host "  - test-event-engine.json" -ForegroundColor Gray
Write-Host "  - out-ingest-lai-weekly.json" -ForegroundColor Gray
Write-Host "  - out-engine-lai-weekly.json" -ForegroundColor Gray
Write-Host "  - newsletter-lai-weekly.md" -ForegroundColor Gray
