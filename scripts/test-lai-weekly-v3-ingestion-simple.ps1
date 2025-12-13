# Script Phase 3 - Test ingestion lai_weekly_v3
$ErrorActionPreference = "Stop"

$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$CLIENT_ID = "lai_weekly_v3"
$PERIOD_DAYS = 30

Write-Host "=== Phase 3 - Ingestion lai_weekly_v3 ===" -ForegroundColor Cyan
Write-Host "Client: $CLIENT_ID" -ForegroundColor Yellow
Write-Host "Periode: $PERIOD_DAYS jours" -ForegroundColor Yellow
Write-Host ""

$ingestPayload = @{
    client_id = $CLIENT_ID
    period_days = $PERIOD_DAYS
} | ConvertTo-Json

$ingestPayload | Out-File -FilePath test-event-v3-ingest.json -Encoding utf8

Write-Host "Invocation de la Lambda ingest-normalize..." -ForegroundColor Yellow
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev --payload file://test-event-v3-ingest.json --profile $PROFILE --region $REGION out-ingest-v3.json

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors de l'invocation" -ForegroundColor Red
    exit 1
}

Write-Host "Reponse de ingest-normalize:" -ForegroundColor Green
$response = Get-Content out-ingest-v3.json | ConvertFrom-Json

if ($response.statusCode -eq 200) {
    Write-Host "Status: 200 OK" -ForegroundColor Green
    $body = $response.body
    
    Write-Host "=== METRIQUES PHASE 3 ===" -ForegroundColor Yellow
    Write-Host "Client: $($body.client_id)"
    Write-Host "Run ID: $($body.run_id)"
    Write-Host "Sources traitees: $($body.sources_processed)"
    Write-Host "Items ingeres: $($body.items_ingested)"
    Write-Host "Items normalises: $($body.items_normalized)"
    Write-Host "Temps execution: $($body.execution_time_seconds)s"
    
    if ($body.items_ingested -gt 0) {
        $rate = [math]::Round(($body.items_normalized / $body.items_ingested) * 100, 1)
        Write-Host "Taux normalisation: $rate%"
    }
    
    Write-Host ""
    Write-Host "=== Phase 3 TERMINEE ===" -ForegroundColor Green
    Write-Host "Donnees pretes pour Phase 4" -ForegroundColor Yellow
    
} else {
    Write-Host "Status: $($response.statusCode)" -ForegroundColor Red
    if ($response.body.error) {
        Write-Host "Erreur: $($response.body.error)"
    }
}