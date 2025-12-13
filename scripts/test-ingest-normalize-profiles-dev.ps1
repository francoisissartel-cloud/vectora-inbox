# Script de test de la Lambda ingest-normalize avec profils d'ingestion
# Ce script lance un test complet sur le client lai_weekly et collecte les métriques

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$LAMBDA_NAME = "vectora-inbox-ingest-normalize-dev"
$CLIENT_ID = "lai_weekly"
$PERIOD_DAYS = 7

Write-Host "=== Test Lambda ingest-normalize avec profils d'ingestion ===" -ForegroundColor Cyan
Write-Host "Client : $CLIENT_ID" -ForegroundColor White
Write-Host "Période : $PERIOD_DAYS jours" -ForegroundColor White

# Préparer le payload de test
$payload = @{
    client_id = $CLIENT_ID
    period_days = $PERIOD_DAYS
} | ConvertTo-Json -Compress

Write-Host "Payload : $payload" -ForegroundColor Gray

# Lancer l'invocation
Write-Host "Lancement de l'invocation Lambda..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputFile = "output-ingest-profiles-$timestamp.json"

aws lambda invoke `
  --function-name $LAMBDA_NAME `
  --payload $payload `
  --cli-binary-format raw-in-base64-out `
  --profile $PROFILE `
  --region $REGION `
  $outputFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "Invocation terminée, résultats dans $outputFile" -ForegroundColor Green
    
    # Lire et afficher les résultats
    $result = Get-Content $outputFile | ConvertFrom-Json
    
    if ($result.statusCode -eq 200) {
        Write-Host "=== RÉSULTATS D'INGESTION AVEC PROFILS ===" -ForegroundColor Green
        
        $body = $result.body
        Write-Host "Client ID : $($body.client_id)" -ForegroundColor White
        Write-Host "Date d'exécution : $($body.execution_date)" -ForegroundColor White
        Write-Host "Sources traitées : $($body.sources_processed)" -ForegroundColor White
        Write-Host "" -ForegroundColor White
        
        Write-Host "=== MÉTRIQUES DE FILTRAGE ===" -ForegroundColor Cyan
        Write-Host "Items scrapés : $($body.items_scraped)" -ForegroundColor White
        Write-Host "Items filtrés (exclus) : $($body.items_filtered_out)" -ForegroundColor White
        Write-Host "Items retenus pour normalisation : $($body.items_retained_for_normalization)" -ForegroundColor White
        Write-Host "Items normalisés : $($body.items_normalized)" -ForegroundColor White
        
        $retentionRate = [math]::Round($body.filtering_retention_rate * 100, 1)
        Write-Host "Taux de rétention global : $retentionRate%" -ForegroundColor $(if ($retentionRate -lt 50) { "Yellow" } else { "Green" })
        
        Write-Host "" -ForegroundColor White
        Write-Host "=== DÉTAIL PAR SOURCE ===" -ForegroundColor Cyan
        
        foreach ($sourceKey in $body.filtering_metrics_by_source.PSObject.Properties.Name) {
            $sourceMetrics = $body.filtering_metrics_by_source.$sourceKey
            $sourceRetention = [math]::Round($sourceMetrics.retention_rate * 100, 1)
            
            Write-Host "Source : $sourceKey" -ForegroundColor White
            Write-Host "  - Scrapés : $($sourceMetrics.scraped)" -ForegroundColor Gray
            Write-Host "  - Filtrés : $($sourceMetrics.filtered_out)" -ForegroundColor Gray
            Write-Host "  - Retenus : $($sourceMetrics.retained)" -ForegroundColor Gray
            Write-Host "  - Taux de rétention : $sourceRetention%" -ForegroundColor $(if ($sourceRetention -lt 50) { "Yellow" } else { "Green" })
            Write-Host "" -ForegroundColor White
        }
        
        Write-Host "Temps d'exécution : $($body.execution_time_seconds) secondes" -ForegroundColor White
        Write-Host "Sortie S3 : $($body.s3_output_path)" -ForegroundColor White
        
        # Analyse des résultats
        Write-Host "" -ForegroundColor White
        Write-Host "=== ANALYSE ===" -ForegroundColor Magenta
        
        if ($body.items_scraped -eq 0) {
            Write-Host "⚠️  Aucun item scrapé - vérifier les sources" -ForegroundColor Red
        } elseif ($retentionRate -lt 10) {
            Write-Host "⚠️  Taux de rétention très faible ($retentionRate%) - risque de sur-filtrage" -ForegroundColor Red
        } elseif ($retentionRate -gt 90) {
            Write-Host "⚠️  Taux de rétention très élevé ($retentionRate%) - filtrage peu efficace" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Taux de rétention dans la plage attendue ($retentionRate%)" -ForegroundColor Green
        }
        
        $economiesBedrock = $body.items_scraped - $body.items_normalized
        if ($economiesBedrock -gt 0) {
            Write-Host "✅ Économies Bedrock : $economiesBedrock appels évités" -ForegroundColor Green
        }
        
    } else {
        Write-Host "=== ERREUR D'EXÉCUTION ===" -ForegroundColor Red
        Write-Host "Status Code : $($result.statusCode)" -ForegroundColor Red
        Write-Host "Erreur : $($result.body.error)" -ForegroundColor Red
        Write-Host "Message : $($result.body.message)" -ForegroundColor Red
    }
    
} else {
    Write-Host "Erreur lors de l'invocation Lambda" -ForegroundColor Red
    exit 1
}

Write-Host "=== Test terminé ===" -ForegroundColor Cyan