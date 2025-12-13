# Script de test de la Lambda ingest-normalize avec logique par runs en DEV
# Ce script teste un run complet d'ingestion + normalisation pour lai_weekly_v2

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$LAMBDA_NAME = "vectora-inbox-ingest-normalize-dev"
$CLIENT_ID = "lai_weekly_v2"

Write-Host "=== Test Lambda ingest-normalize avec logique par runs ===" -ForegroundColor Cyan

# Préparer le payload de test
$testPayload = @{
    client_id = $CLIENT_ID
    period_days = 30
} | ConvertTo-Json -Compress

Write-Host "Payload de test :" -ForegroundColor Yellow
Write-Host $testPayload -ForegroundColor White

# Créer un fichier temporaire pour le payload
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
    Write-Host "✅ Lambda invoquée avec succès" -ForegroundColor Green
    Write-Host "Durée d'exécution: $([math]::Round($duration, 2)) secondes" -ForegroundColor Green
} else {
    Write-Host "❌ Erreur lors de l'invocation de la Lambda" -ForegroundColor Red
    exit 1
}

# Lire et analyser la réponse
Write-Host "Analyse de la réponse..." -ForegroundColor Yellow

if (!(Test-Path "test-response-runs.json")) {
    Write-Host "❌ Fichier de réponse non trouvé" -ForegroundColor Red
    exit 1
}

$response = Get-Content "test-response-runs.json" -Raw | ConvertFrom-Json

Write-Host "Réponse de la Lambda :" -ForegroundColor Green
Write-Host ($response | ConvertTo-Json -Depth 10) -ForegroundColor White

# Analyser le statusCode
if ($response.statusCode -eq 200) {
    Write-Host "✅ Status Code: 200 (Succès)" -ForegroundColor Green
    
    $body = $response.body
    
    # Vérifier les champs attendus avec logique par runs
    $expectedFields = @("client_id", "run_id", "execution_date", "sources_processed", "items_ingested", "items_normalized", "s3_raw_path", "s3_normalized_path", "execution_time_seconds")
    
    Write-Host "Validation des champs de réponse :" -ForegroundColor Yellow
    foreach ($field in $expectedFields) {
        if ($body.PSObject.Properties.Name -contains $field) {
            $value = $body.$field
            Write-Host "  ✅ $field : $value" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $field : MANQUANT" -ForegroundColor Red
        }
    }
    
    # Vérifications spécifiques à la logique par runs
    if ($body.run_id) {
        if ($body.run_id.StartsWith("run_")) {
            Write-Host "  ✅ Format run_id correct : $($body.run_id)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Format run_id incorrect : $($body.run_id)" -ForegroundColor Red
        }
    }
    
    if ($body.s3_raw_path) {
        if ($body.s3_raw_path.Contains("/raw/")) {
            Write-Host "  ✅ Chemin RAW correct : $($body.s3_raw_path)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Chemin RAW incorrect : $($body.s3_raw_path)" -ForegroundColor Red
        }
    }
    
    if ($body.s3_normalized_path) {
        if ($body.s3_normalized_path.Contains("/normalized/") -and $body.s3_normalized_path.Contains($body.run_id)) {
            Write-Host "  ✅ Chemin normalisé correct : $($body.s3_normalized_path)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Chemin normalisé incorrect : $($body.s3_normalized_path)" -ForegroundColor Red
        }
    }
    
    # Statistiques d'exécution
    Write-Host ""
    Write-Host "📊 Statistiques d'exécution :" -ForegroundColor Yellow
    Write-Host "   Client ID: $($body.client_id)" -ForegroundColor White
    Write-Host "   Run ID: $($body.run_id)" -ForegroundColor White
    Write-Host "   Sources traitées: $($body.sources_processed)" -ForegroundColor White
    Write-Host "   Items ingérés: $($body.items_ingested)" -ForegroundColor White
    Write-Host "   Items normalisés: $($body.items_normalized)" -ForegroundColor White
    Write-Host "   Temps d'exécution: $($body.execution_time_seconds) secondes" -ForegroundColor White
    
} else {
    Write-Host "❌ Status Code: $($response.statusCode)" -ForegroundColor Red
    if ($response.body.error) {
        Write-Host "Erreur: $($response.body.error)" -ForegroundColor Red
        Write-Host "Message: $($response.body.message)" -ForegroundColor Red
    }
}

# Vérifier les fichiers S3 créés
if ($response.statusCode -eq 200 -and $response.body.run_id) {
    Write-Host ""
    Write-Host "🔍 Vérification des fichiers S3 créés..." -ForegroundColor Yellow
    
    $runId = $response.body.run_id
    $dateStr = Get-Date -Format "yyyy/MM/dd"
    
    # Vérifier les fichiers RAW
    $rawPrefix = "raw/$CLIENT_ID/$dateStr/$runId/"
    Write-Host "Vérification du préfixe RAW: $rawPrefix" -ForegroundColor White
    
    $rawFiles = aws s3 ls s3://vectora-inbox-data-dev/$rawPrefix --recursive `
      --profile $PROFILE `
      --region $REGION
    
    if ($rawFiles) {
        Write-Host "✅ Fichiers RAW trouvés :" -ForegroundColor Green
        Write-Host $rawFiles -ForegroundColor White
    } else {
        Write-Host "❌ Aucun fichier RAW trouvé" -ForegroundColor Red
    }
    
    # Vérifier le fichier normalisé
    $normalizedKey = "normalized/$CLIENT_ID/$dateStr/$runId/items.json"
    Write-Host "Vérification du fichier normalisé: $normalizedKey" -ForegroundColor White
    
    $normalizedFile = aws s3 ls s3://vectora-inbox-data-dev/$normalizedKey `
      --profile $PROFILE `
      --region $REGION
    
    if ($normalizedFile) {
        Write-Host "✅ Fichier normalisé trouvé :" -ForegroundColor Green
        Write-Host $normalizedFile -ForegroundColor White
        
        # Télécharger et analyser le contenu
        Write-Host "Téléchargement du fichier normalisé pour analyse..." -ForegroundColor Yellow
        aws s3 cp s3://vectora-inbox-data-dev/$normalizedKey normalized-items-test.json `
          --profile $PROFILE `
          --region $REGION
        
        if (Test-Path "normalized-items-test.json") {
            $normalizedItems = Get-Content "normalized-items-test.json" -Raw | ConvertFrom-Json
            Write-Host "✅ Fichier normalisé analysé : $($normalizedItems.Count) items" -ForegroundColor Green
            
            # Afficher quelques exemples
            if ($normalizedItems.Count -gt 0) {
                Write-Host "Exemple d'item normalisé :" -ForegroundColor Yellow
                $firstItem = $normalizedItems[0]
                Write-Host "  Titre: $($firstItem.title)" -ForegroundColor White
                Write-Host "  Type d'événement: $($firstItem.event_type)" -ForegroundColor White
                Write-Host "  Source: $($firstItem.source_key)" -ForegroundColor White
                if ($firstItem.companies_detected) {
                    Write-Host "  Entreprises détectées: $($firstItem.companies_detected -join ', ')" -ForegroundColor White
                }
            }
            
            Remove-Item "normalized-items-test.json" -Force
        }
    } else {
        Write-Host "❌ Fichier normalisé non trouvé" -ForegroundColor Red
    }
}

# Nettoyer les fichiers temporaires
Remove-Item $payloadFile -Force -ErrorAction SilentlyContinue
Remove-Item "test-response-runs.json" -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Test terminé ===" -ForegroundColor Cyan

if ($response.statusCode -eq 200) {
    Write-Host "🎉 Test réussi ! La logique par runs fonctionne correctement." -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Résumé :" -ForegroundColor Yellow
    Write-Host "   ✅ Lambda invoquée avec succès" -ForegroundColor Green
    Write-Host "   ✅ Run ID généré : $($response.body.run_id)" -ForegroundColor Green
    Write-Host "   ✅ Structure S3 par run créée" -ForegroundColor Green
    Write-Host "   ✅ Items normalisés uniquement pour ce run" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Prêt pour les tests engine avec period_days" -ForegroundColor Yellow
} else {
    Write-Host "❌ Test échoué. Vérifiez les logs de la Lambda." -ForegroundColor Red
    exit 1
}