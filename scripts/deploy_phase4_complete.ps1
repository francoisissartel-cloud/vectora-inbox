# Script de déploiement complet Phase 4 - Test End-to-End
# Usage: .\scripts\deploy_phase4_complete.ps1

Write-Host "=== Phase 4: Test End-to-End & Métriques - Déploiement Complet ===" -ForegroundColor Cyan
Write-Host ""

# 1. Upload config canonical
Write-Host "[1/5] Upload de la config canonical..." -ForegroundColor Yellow
aws s3 cp canonical/matching/domain_matching_rules.yaml s3://vectora-inbox-config-dev/canonical/matching/
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de l'upload de la config" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Config canonical uploadée" -ForegroundColor Green
Write-Host ""

# 2. Repackager la Lambda
Write-Host "[2/5] Repackaging Lambda avec toutes les corrections P2+P3..." -ForegroundColor Yellow
python scripts/package_lambda.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du packaging" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Lambda packagée" -ForegroundColor Green
Write-Host ""

# 3. Déployer
Write-Host "[3/5] Déploiement sur AWS..." -ForegroundColor Yellow
python scripts/deploy_lambda.py --env dev
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors du déploiement" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Lambda déployée" -ForegroundColor Green
Write-Host ""

# 4. Vérifier
Write-Host "[4/5] Vérification du déploiement..." -ForegroundColor Yellow
aws lambda get-function --function-name vectora-inbox-engine-dev --query 'Configuration.[FunctionName,LastModified,CodeSize]' --output table
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de la vérification" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Déploiement vérifié" -ForegroundColor Green
Write-Host ""

# 5. Lancer l'engine
Write-Host "[5/5] Lancement de l'engine lai_weekly..." -ForegroundColor Yellow
python scripts/run_engine.py --env dev --client lai_weekly
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erreur lors de l'exécution de l'engine" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Engine exécuté avec succès" -ForegroundColor Green
Write-Host ""

Write-Host "=== Phase 4 déployée et testée avec succès ===" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines étapes:" -ForegroundColor Cyan
Write-Host "1. Télécharger la newsletter: aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/latest/newsletter.json ."
Write-Host "2. Analyser les métriques: python scripts/analyze_newsletter_phase4.py newsletter.json"
Write-Host "3. Vérifier les logs Phase 2: aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern '[SIGNAL_SUMMARY]'"
Write-Host "4. Vérifier les logs Phase 3: aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern '[COMPANY_TYPE]'"
Write-Host "5. Validation manuelle des items pour calculer LAI precision et false positives"
Write-Host ""
Write-Host "📊 Métriques à valider:" -ForegroundColor Yellow
Write-Host "   - LAI precision ≥80% (validation manuelle)"
Write-Host "   - Pure player % ≥50% (calculé automatiquement)"
Write-Host "   - False positives = 0 (validation manuelle)"
Write-Host ""
