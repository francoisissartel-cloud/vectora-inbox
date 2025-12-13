# Script de déploiement des corrections runtime matching/scoring
# Ce script package et déploie les corrections sur AWS dev

Write-Host "[DEPLOY] Déploiement des corrections runtime matching/scoring" -ForegroundColor Green
Write-Host "=" * 60

# Vérifier l'environnement AWS
Write-Host "`n[CHECK] Vérification de l'environnement AWS..."
try {
    $awsProfile = aws sts get-caller-identity --profile rag-lai-prod --query "Account" --output text
    Write-Host "[OK] AWS Profile rag-lai-prod actif (Account: $awsProfile)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Problème avec le profil AWS rag-lai-prod" -ForegroundColor Red
    exit 1
}

# Créer le package ingest-normalize avec corrections
Write-Host "`n[PACKAGE] Packaging ingest-normalize avec corrections..."
try {
    # Copier les fichiers sources avec corrections
    Remove-Item -Path "ingest-normalize-runtime-fixes.zip" -ErrorAction SilentlyContinue
    
    # Créer le package avec les corrections
    Compress-Archive -Path "src/*", "lambda-deps/*" -DestinationPath "ingest-normalize-runtime-fixes.zip" -Force
    
    Write-Host "[OK] Package ingest-normalize-runtime-fixes.zip créé" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Erreur lors du packaging ingest-normalize: $_" -ForegroundColor Red
    exit 1
}

# Créer le package engine avec corrections
Write-Host "`n[PACKAGE] Packaging engine avec corrections..."
try {
    # Copier les fichiers sources avec corrections
    Remove-Item -Path "engine-runtime-fixes.zip" -ErrorAction SilentlyContinue
    
    # Créer le package avec les corrections
    Compress-Archive -Path "src/*", "lambda-deps/*" -DestinationPath "engine-runtime-fixes.zip" -Force
    
    Write-Host "[OK] Package engine-runtime-fixes.zip créé" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Erreur lors du packaging engine: $_" -ForegroundColor Red
    exit 1
}

# Déployer ingest-normalize
Write-Host "`n[DEPLOY] Déploiement ingest-normalize sur AWS dev..."
try {
    aws lambda update-function-code `
        --function-name vectora-inbox-ingest-normalize-dev `
        --zip-file fileb://ingest-normalize-runtime-fixes.zip `
        --profile rag-lai-prod
    
    Write-Host "[OK] Lambda ingest-normalize-dev déployée avec corrections" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Erreur lors du déploiement ingest-normalize: $_" -ForegroundColor Red
    exit 1
}

# Déployer engine
Write-Host "`n[DEPLOY] Déploiement engine sur AWS dev..."
try {
    aws lambda update-function-code `
        --function-name vectora-inbox-engine-dev `
        --zip-file fileb://engine-runtime-fixes.zip `
        --profile rag-lai-prod
    
    Write-Host "[OK] Lambda engine-dev déployée avec corrections" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Erreur lors du déploiement engine: $_" -ForegroundColor Red
    exit 1
}

# Test smoke
Write-Host "`n[SMOKE] Test smoke des déploiements..."
try {
    # Test simple ingest-normalize
    $testPayload = @{
        client_id = "lai_weekly_v3"
        period_days = 1
        sources = @("press_corporate__medincell")
    } | ConvertTo-Json
    
    $testPayload | Out-File -FilePath "test-smoke-payload.json" -Encoding UTF8
    
    aws lambda invoke `
        --function-name vectora-inbox-ingest-normalize-dev `
        --payload file://test-smoke-payload.json `
        --profile rag-lai-prod `
        out-smoke-test.json
    
    $result = Get-Content "out-smoke-test.json" | ConvertFrom-Json
    if ($result.items_normalized -gt 0) {
        Write-Host "[OK] Test smoke ingest-normalize réussi ($($result.items_normalized) items)" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Test smoke ingest-normalize: 0 items normalisés" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "[ERROR] Erreur lors du test smoke: $_" -ForegroundColor Red
}

Write-Host "`n[SUCCESS] Déploiement des corrections terminé!" -ForegroundColor Green
Write-Host "`n[NEXT] Lancer un run end-to-end pour valider les corrections:" -ForegroundColor Cyan
Write-Host "  aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev --payload file://test-lai-weekly-v3.json out-test-fixes.json --profile rag-lai-prod"

# Nettoyer les fichiers temporaires
Remove-Item -Path "test-smoke-payload.json" -ErrorAction SilentlyContinue