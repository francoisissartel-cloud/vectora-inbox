# Script de déploiement Phase 2 - Filtrage des Catégories
# Usage: .\scripts\deploy_phase2.ps1

Write-Host "=== Phase 2: Filtrage des Catégories - Déploiement ===" -ForegroundColor Cyan
Write-Host ""

# 1. Repackager la Lambda
Write-Host "[1/3] Repackaging Lambda..." -ForegroundColor Yellow
python scripts/package_lambda.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du packaging" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Lambda packagée" -ForegroundColor Green
Write-Host ""

# 2. Déployer
Write-Host "[2/3] Déploiement sur AWS..." -ForegroundColor Yellow
python scripts/deploy_lambda.py --env dev
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du déploiement" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Lambda déployée" -ForegroundColor Green
Write-Host ""

# 3. Vérifier
Write-Host "[3/3] Vérification du déploiement..." -ForegroundColor Yellow
aws lambda get-function --function-name vectora-inbox-engine-dev --query 'Configuration.[FunctionName,LastModified,CodeSize]' --output table
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la vérification" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Déploiement vérifié" -ForegroundColor Green
Write-Host ""

Write-Host "=== Phase 2 déployée avec succès ===" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Cyan
Write-Host "1. Lancer l'engine: python scripts/run_engine.py --env dev --client lai_weekly"
Write-Host "2. Analyser les logs: aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern '[SIGNAL_SUMMARY]'"
Write-Host "3. Télécharger la newsletter: aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/latest/newsletter.json ."
Write-Host ""
