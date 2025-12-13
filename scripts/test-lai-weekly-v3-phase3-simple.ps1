# Script Phase 3 - Ingestion lai_weekly_v3
$ErrorActionPreference = "Stop"

$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$LAMBDA_NAME = "vectora-inbox-ingest-normalize-dev"
$CLIENT_ID = "lai_weekly_v3"

Write-Host "=== Phase 3 - Ingestion lai_weekly_v3 ===" -ForegroundColor Cyan

$testPayload = @{
    client_id = $CLIENT_ID
    period_days = 30
} | ConvertTo-Json -Compress

Write-Host "Client: $CLIENT_ID"
Write-Host "Period Days: 30"
Write-Host "Payload: $testPayload"

$payloadFile = "test-v3-phase3.json"
$testPayload | Out-File -FilePath $payloadFile -Encoding UTF8

Write-Host "Lancement ingestion..."

$startTime = Get-Date
aws lambda invoke --function-name $LAMBDA_NAME --payload file://$payloadFile --profile $PROFILE --region $REGION response-v3-phase3.json
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

if ($LASTEXITCODE -eq 0) {
    Write-Host "Lambda OK - Duree: $([math]::Round($duration, 2))s" -ForegroundColor Green
} else {
    Write-Host "Erreur Lambda" -ForegroundColor Red
    exit 1
}

if (Test-Path "response-v3-phase3.json") {
    $response = Get-Content "response-v3-phase3.json" -Raw | ConvertFrom-Json
    
    if ($response.statusCode -eq 200) {
        Write-Host "Status: 200 OK" -ForegroundColor Green
        $body = $response.body
        
        Write-Host "=== METRIQUES ===" -ForegroundColor Yellow
        Write-Host "Client: $($body.client_id)"
        Write-Host "Run ID: $($body.run_id)"
        Write-Host "Sources: $($body.sources_processed)"
        Write-Host "Items ingeres: $($body.items_ingested)"
        Write-Host "Items normalises: $($body.items_normalized)"
        Write-Host "Temps: $($body.execution_time_seconds)s"
        
        if ($body.items_ingested -gt 0) {
            $rate = [math]::Round(($body.items_normalized / $body.items_ingested) * 100, 1)
            Write-Host "Taux normalisation: $rate%"
        }
        
        Write-Host "=== Phase 3 TERMINEE ===" -ForegroundColor Green
        
    } else {
        Write-Host "Status: $($response.statusCode)" -ForegroundColor Red
        if ($response.body.error) {
            Write-Host "Erreur: $($response.body.error)"
        }
    }
}

Remove-Item $payloadFile -Force -ErrorAction SilentlyContinue