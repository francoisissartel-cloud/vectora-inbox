# Script de test Phase 3 - Ingestion + Normalisation lai_weekly_v3
# Objectif : Run complet avec métriques détaillées pour banc d'essai

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$LAMBDA_NAME = "vectora-inbox-ingest-normalize-dev"
$CLIENT_ID = "lai_weekly_v3"

Write-Host "=== Phase 3 - Ingestion + Normalisation lai_weekly_v3 ===" -ForegroundColor Cyan

# Préparer le payload de test (utilise period_days de la config v3)
$testPayload = @{
    client_id = $CLIENT_ID
    period_days = 30
} | ConvertTo-Json -Compress

Write-Host "Configuration du test :" -ForegroundColor Yellow
Write-Host "  Lambda: $LAMBDA_NAME" -ForegroundColor White
Write-Host "  Client: $CLIENT_ID" -ForegroundColor White
Write-Host "  Period Days: 30 (config v3)" -ForegroundColor White
Write-Host "  Payload: $testPayload" -ForegroundColor White

# Créer un fichier temporaire pour le payload
$payloadFile = "test-lai-weekly-v3-phase3.json"
$testPayload | Out-File -FilePath $payloadFile -Encoding UTF8

Write-Host ""
Write-Host "Lancement de l'ingestion..." -ForegroundColor Yellow

# Invoquer la Lambda avec mesure du temps
$startTime = Get-Date
aws lambda invoke `
  --function-name $LAMBDA_NAME `
  --payload file://$payloadFile `
  --profile $PROFILE `
  --region $REGION `
  response-lai-weekly-v3-phase3.json

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Lambda invoquée avec succès" -ForegroundColor Green
    Write-Host "Durée d'exécution: $([math]::Round($duration, 2)) secondes" -ForegroundColor Green
} else {
    Write-Host "❌ Erreur lors de l'invocation de la Lambda" -ForegroundColor Red
    exit 1
}

# Analyser la réponse
Write-Host ""
Write-Host "Analyse des résultats..." -ForegroundColor Yellow

if (!(Test-Path "response-lai-weekly-v3-phase3.json")) {
    Write-Host "❌ Fichier de réponse non trouvé" -ForegroundColor Red
    exit 1
}

$response = Get-Content "response-lai-weekly-v3-phase3.json" -Raw | ConvertFrom-Json

if ($response.statusCode -eq 200) {
    Write-Host "✅ Status Code: 200 (Succès)" -ForegroundColor Green
    
    $body = $response.body
    
    # Métriques globales
    Write-Host ""
    Write-Host "📊 MÉTRIQUES GLOBALES" -ForegroundColor Yellow
    Write-Host "   Client ID: $($body.client_id)" -ForegroundColor White
    Write-Host "   Run ID: $($body.run_id)" -ForegroundColor White
    Write-Host "   Date d'exécution: $($body.execution_date)" -ForegroundColor White
    Write-Host "   Sources traitées: $($body.sources_processed)" -ForegroundColor White
    Write-Host "   Items ingérés: $($body.items_ingested)" -ForegroundColor White
    Write-Host "   Items normalisés: $($body.items_normalized)" -ForegroundColor White
    Write-Host "   Temps d'exécution: $($body.execution_time_seconds) secondes" -ForegroundColor White
    
    # Calculer les ratios
    if ($body.items_ingested -gt 0) {
        $normalizationRate = [math]::Round(($body.items_normalized / $body.items_ingested) * 100, 1)
        Write-Host "   Taux de normalisation: $normalizationRate%" -ForegroundColor White
    }
    
} else {
    Write-Host "❌ Status Code: $($response.statusCode)" -ForegroundColor Red
    if ($response.body.error) {
        Write-Host "Erreur: $($response.body.error)" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "=== Phase 3 Terminée ===" -ForegroundColor Green
Write-Host "Données prêtes pour Phase 4 (Engine)" -ForegroundColor Yellow

# Nettoyer
Remove-Item $payloadFile -Force -ErrorAction SilentlyContinue