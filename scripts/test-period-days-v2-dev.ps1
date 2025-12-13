# Script de test de la nouvelle logique period_days v2
# Ce script teste les différents cas d'usage de la résolution de période

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$CLIENT_ID = "lai_weekly_v2"

Write-Host "=== Test de la logique period_days v2 ===" -ForegroundColor Cyan
Write-Host "Client: $CLIENT_ID" -ForegroundColor Yellow
Write-Host ""

# Test 1 : Sans period_days (doit utiliser la config client : 30 jours)
Write-Host "=== Test 1 : Configuration client (30 jours attendus) ===" -ForegroundColor Cyan

$payload1 = @{
    client_id = $CLIENT_ID
} | ConvertTo-Json

$payload1 | Out-File -FilePath test-event-config-client.json -Encoding utf8

Write-Host "Payload: $payload1" -ForegroundColor Gray
Write-Host "Invocation de la Lambda engine..." -ForegroundColor Yellow

aws lambda invoke `
  --function-name vectora-inbox-engine-dev `
  --payload file://test-event-config-client.json `
  --profile $PROFILE `
  --region $REGION `
  out-engine-config-client.json

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors de l'invocation" -ForegroundColor Red
    exit 1
}

$response1 = Get-Content out-engine-config-client.json | ConvertFrom-Json
Write-Host "Réponse:" -ForegroundColor Green
$response1 | ConvertTo-Json -Depth 5

Write-Host ""
Write-Host "Attente de 3 secondes..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Test 2 : Avec period_days override (doit utiliser 7 jours)
Write-Host "=== Test 2 : Override payload (7 jours attendus) ===" -ForegroundColor Cyan

$payload2 = @{
    client_id = $CLIENT_ID
    period_days = 7
} | ConvertTo-Json

$payload2 | Out-File -FilePath test-event-override.json -Encoding utf8

Write-Host "Payload: $payload2" -ForegroundColor Gray
Write-Host "Invocation de la Lambda engine..." -ForegroundColor Yellow

aws lambda invoke `
  --function-name vectora-inbox-engine-dev `
  --payload file://test-event-override.json `
  --profile $PROFILE `
  --region $REGION `
  out-engine-override.json

if ($LASTEXITCODE -ne 0) {
    Write-Host "Erreur lors de l'invocation" -ForegroundColor Red
    exit 1
}

$response2 = Get-Content out-engine-override.json | ConvertFrom-Json
Write-Host "Réponse:" -ForegroundColor Green
$response2 | ConvertTo-Json -Depth 5

# Analyse des résultats
Write-Host ""
Write-Host "=== Analyse des résultats ===" -ForegroundColor Magenta

# Extraire les périodes des réponses (depuis les logs ou la structure)
$period1 = $response1.body.period
$period2 = $response2.body.period

if ($period1 -and $period2) {
    Write-Host "Test 1 - Période utilisée:" -ForegroundColor White
    Write-Host "  From: $($period1.from_date)" -ForegroundColor Gray
    Write-Host "  To: $($period1.to_date)" -ForegroundColor Gray
    
    Write-Host "Test 2 - Période utilisée:" -ForegroundColor White
    Write-Host "  From: $($period2.from_date)" -ForegroundColor Gray
    Write-Host "  To: $($period2.to_date)" -ForegroundColor Gray
    
    # Calculer les durées
    $date1From = [DateTime]::Parse($period1.from_date)
    $date1To = [DateTime]::Parse($period1.to_date)
    $duration1 = ($date1To - $date1From).Days
    
    $date2From = [DateTime]::Parse($period2.from_date)
    $date2To = [DateTime]::Parse($period2.to_date)
    $duration2 = ($date2To - $date2From).Days
    
    Write-Host ""
    Write-Host "Durées calculées:" -ForegroundColor White
    Write-Host "  Test 1 (config client): $duration1 jours" -ForegroundColor $(if ($duration1 -eq 30) { "Green" } else { "Red" })
    Write-Host "  Test 2 (override): $duration2 jours" -ForegroundColor $(if ($duration2 -eq 7) { "Green" } else { "Red" })
    
    # Validation
    $test1Success = $duration1 -eq 30
    $test2Success = $duration2 -eq 7
    
    Write-Host ""
    if ($test1Success -and $test2Success) {
        Write-Host "✅ Tous les tests sont réussis !" -ForegroundColor Green
        Write-Host "  - Configuration client (30j) : OK" -ForegroundColor Green
        Write-Host "  - Override payload (7j) : OK" -ForegroundColor Green
    } else {
        Write-Host "❌ Certains tests ont échoué :" -ForegroundColor Red
        if (-not $test1Success) {
            Write-Host "  - Configuration client : attendu 30j, obtenu ${duration1}j" -ForegroundColor Red
        }
        if (-not $test2Success) {
            Write-Host "  - Override payload : attendu 7j, obtenu ${duration2}j" -ForegroundColor Red
        }
    }
} else {
    Write-Host "⚠️  Impossible d'extraire les périodes des réponses" -ForegroundColor Yellow
    Write-Host "Vérifiez manuellement les logs des Lambdas" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Test terminé ===" -ForegroundColor Cyan
Write-Host "Fichiers générés:" -ForegroundColor Yellow
Write-Host "  - test-event-config-client.json" -ForegroundColor Gray
Write-Host "  - test-event-override.json" -ForegroundColor Gray
Write-Host "  - out-engine-config-client.json" -ForegroundColor Gray
Write-Host "  - out-engine-override.json" -ForegroundColor Gray