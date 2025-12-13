# Script de déploiement Phase 3 - Fallback & Pure_Player
# Usage: .\scripts\deploy_phase3.ps1

Write-Host "=== Phase 3: Fallback & Pure_Player - Déploiement ===" -ForegroundColor Cyan
Write-Host ""

# 1. Uploader la config canonical mise à jour
Write-Host "[1/4] Upload de la config canonical..." -ForegroundColor Yellow
aws s3 cp canonical/matching/domain_matching_rules.yaml s3://vectora-inbox-config-dev/canonical/matching/
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de l'upload de la config" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Config canonical uploadée" -ForegroundColor Green
Write-Host ""

# 2. Repackager la Lambda
Write-Host "[2/4] Repackaging Lambda..." -ForegroundColor Yellow
python scripts/package_lambda.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du packaging" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Lambda packagée" -ForegroundColor Green
Write-Host ""

# 3. Déployer
Write-Host "[3/4] Déploiement sur AWS..." -ForegroundColor Yellow
python scripts/deploy_lambda.py --env dev
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du déploiement" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Lambda déployée" -ForegroundColor Green
Write-Host ""

# 4. Vérifier
Write-Host "[4/4] Vérification du déploiement..." -ForegroundColor Yellow
aws lambda get-function --function-name vectora-inbox-engine-dev --query 'Configuration.[FunctionName,LastModified,CodeSize]' --output table
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la vérification" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Déploiement vérifié" -ForegroundColor Green
Write-Host ""

Write-Host "=== Phase 3 déployée avec succès ===" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Cyan
Write-Host "1. Lancer l'engine: python scripts/run_engine.py --env dev --client lai_weekly"
Write-Host "2. Analyser les logs: aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern '[COMPANY_TYPE]'"
Write-Host "3. Télécharger la newsletter: aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/latest/newsletter.json ."
Write-Host "4. Analyser les résultats: python scripts/analyze_newsletter.py newsletter.json --check-pure-players"
Write-Host ""
