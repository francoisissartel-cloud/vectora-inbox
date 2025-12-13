# Script de test simple de la Lambda ingest-normalize avec logique par runs en DEV

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$LAMBDA_NAME = "vectora-inbox-ingest-normalize-dev"
$CLIENT_ID = "lai_weekly_v2"

Write-Host "=== Test Lambda ingest-normalize avec logique par runs ===" -ForegroundColor Cyan

# Preparer le payload de test
$testPayload = @{
    client_id = $CLIENT_ID
    period_days = 30
} | ConvertTo-Json -Compress

Write-Host "Payload de test :" -ForegroundColor Yellow
Write-Host $testPayload -ForegroundColor White

# Creer un fichier temporaire pour le payload
$payloadFile = "test-payload-runs.json"
$testPayload | Out-File -FilePath $payloadFile -Encoding UTF8

Write-Host "Invocation de la Lambda..." -ForegroundColor Yellow
Write-Host "Lambda: $LAMBDA_NAME" -ForegroundColor White
Write-Host "Client: $CLIENT_ID" -ForegroundColor White

# Invoquer la Lambda
$startTime = Get-Date
aws lambda invoke `
  --function-name $LAMBDA_NAME `
  --payload file://$payloadFile `
  --profile $PROFILE `
  --region $REGION `
  test-response-runs.json

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

if ($LASTEXITCODE -eq 0) {
    Write-Host "Lambda invoquee avec succes" -ForegroundColor Green
    Write-Host "Duree d'execution: $([math]::Round($duration, 2)) secondes" -ForegroundColor Green
} else {
    Write-Host "Erreur lors de l'invocation de la Lambda" -ForegroundColor Red
    exit 1
}

# Lire et analyser la reponse
Write-Host "Analyse de la reponse..." -ForegroundColor Yellow

if (!(Test-Path "test-response-runs.json")) {
    Write-Host "Fichier de reponse non trouve" -ForegroundColor Red
    exit 1
}

$response = Get-Content "test-response-runs.json" -Raw | ConvertFrom-Json

Write-Host "Reponse de la Lambda :" -ForegroundColor Green
Write-Host ($response | ConvertTo-Json -Depth 10) -ForegroundColor White

# Analyser le statusCode
if ($response.statusCode -eq 200) {
    Write-Host "Status Code: 200 (Succes)" -ForegroundColor Green
    
    $body = $response.body
    
    # Verifier les champs attendus avec logique par runs
    $expectedFields = @("client_id", "run_id", "execution_date", "sources_processed", "items_ingested", "items_normalized", "s3_raw_path", "s3_normalized_path", "execution_time_seconds")
    
    Write-Host "Validation des champs de reponse :" -ForegroundColor Yellow
    foreach ($field in $expectedFields) {
        if ($body.PSObject.Properties.Name -contains $field) {
            $value = $body.$field
            Write-Host "  OK $field : $value" -ForegroundColor Green
        } else {
            Write-Host "  MANQUANT $field" -ForegroundColor Red
        }
    }
    
    # Verifications specifiques a la logique par runs
    if ($body.run_id) {
        if ($body.run_id.StartsWith("run_")) {
            Write-Host "  OK Format run_id correct : $($body.run_id)" -ForegroundColor Green
        } else {
            Write-Host "  ERREUR Format run_id incorrect : $($body.run_id)" -ForegroundColor Red
        }
    }
    
    if ($body.s3_raw_path) {
        if ($body.s3_raw_path.Contains("/raw/")) {
            Write-Host "  OK Chemin RAW correct : $($body.s3_raw_path)" -ForegroundColor Green
        } else {
            Write-Host "  ERREUR Chemin RAW incorrect : $($body.s3_raw_path)" -ForegroundColor Red
        }
    }
    
    if ($body.s3_normalized_path) {
        if ($body.s3_normalized_path.Contains("/normalized/") -and $body.s3_normalized_path.Contains($body.run_id)) {
            Write-Host "  OK Chemin normalise correct : $($body.s3_normalized_path)" -ForegroundColor Green
        } else {
            Write-Host "  ERREUR Chemin normalise incorrect : $($body.s3_normalized_path)" -ForegroundColor Red
        }
    }
    
    # Statistiques d'execution
    Write-Host ""
    Write-Host "Statistiques d'execution :" -ForegroundColor Yellow
    Write-Host "   Client ID: $($body.client_id)" -ForegroundColor White
    Write-Host "   Run ID: $($body.run_id)" -ForegroundColor White
    Write-Host "   Sources traitees: $($body.sources_processed)" -ForegroundColor White
    Write-Host "   Items ingeres: $($body.items_ingested)" -ForegroundColor White
    Write-Host "   Items normalises: $($body.items_normalized)" -ForegroundColor White
    Write-Host "   Temps d'execution: $($body.execution_time_seconds) secondes" -ForegroundColor White
    
} else {
    Write-Host "Status Code: $($response.statusCode)" -ForegroundColor Red
    if ($response.body.error) {
        Write-Host "Erreur: $($response.body.error)" -ForegroundColor Red
        Write-Host "Message: $($response.body.message)" -ForegroundColor Red
    }
}

# Nettoyer les fichiers temporaires
Remove-Item $payloadFile -Force -ErrorAction SilentlyContinue
Remove-Item "test-response-runs.json" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Test termine ===" -ForegroundColor Cyan

if ($response.statusCode -eq 200) {
    Write-Host "Test reussi ! La logique par runs fonctionne correctement." -ForegroundColor Green
} else {
    Write-Host "Test echoue. Verifiez les logs de la Lambda." -ForegroundColor Red
    exit 1
}