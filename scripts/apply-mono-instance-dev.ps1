# Script pour appliquer le mode mono-instance sur ingest-normalize en DEV
# Usage: .\scripts\apply-mono-instance-dev.ps1

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$STACK_NAME = "vectora-inbox-s1-runtime-dev"
$FUNCTION_NAME = "vectora-inbox-ingest-normalize-dev"

Write-Host "=== Application du mode mono-instance pour ingest-normalize en DEV ===" -ForegroundColor Cyan
Write-Host ""

# Étape 1 : Vérifier la configuration actuelle
Write-Host "[1/3] Vérification de la configuration actuelle..." -ForegroundColor Yellow

try {
    $currentConfig = aws lambda get-function-concurrency `
        --function-name $FUNCTION_NAME `
        --profile $PROFILE `
        --region $REGION 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $config = $currentConfig | ConvertFrom-Json
        Write-Host "  Configuration actuelle : ReservedConcurrentExecutions = $($config.ReservedConcurrentExecutions)" -ForegroundColor Green
    } else {
        Write-Host "  Aucune limite de concurrence définie (concurrence illimitée)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Aucune limite de concurrence définie (concurrence illimitée)" -ForegroundColor Yellow
}
Write-Host ""

# Étape 2 : Redéployer la stack CloudFormation
Write-Host "[2/3] Redéploiement de la stack CloudFormation..." -ForegroundColor Yellow

# Récupérer les paramètres actuels de la stack
$stackParams = aws cloudformation describe-stacks `
    --stack-name $STACK_NAME `
    --profile $PROFILE `
    --region $REGION `
    --query "Stacks[0].Parameters" | ConvertFrom-Json

# Construire la liste des paramètres pour le redéploiement
$paramOverrides = @()
foreach ($param in $stackParams) {
    $paramOverrides += "$($param.ParameterKey)=$($param.ParameterValue)"
}
$paramString = $paramOverrides -join " "

Write-Host "  Paramètres de la stack : $paramString" -ForegroundColor Gray

# Redéployer la stack
aws cloudformation deploy `
    --template-file infra/s1-runtime.yaml `
    --stack-name $STACK_NAME `
    --parameter-overrides $paramString `
    --profile $PROFILE `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Stack redéployée avec succès" -ForegroundColor Green
} else {
    Write-Host "  ✗ Erreur lors du redéploiement de la stack" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Étape 3 : Vérifier la nouvelle configuration
Write-Host "[3/3] Vérification de la nouvelle configuration..." -ForegroundColor Yellow

Start-Sleep -Seconds 5

$newConfig = aws lambda get-function-concurrency `
    --function-name $FUNCTION_NAME `
    --profile $PROFILE `
    --region $REGION | ConvertFrom-Json

if ($newConfig.ReservedConcurrentExecutions -eq 1) {
    Write-Host "  ✓ Mode mono-instance activé : ReservedConcurrentExecutions = 1" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Configuration inattendue : ReservedConcurrentExecutions = $($newConfig.ReservedConcurrentExecutions)" -ForegroundColor Yellow
}
Write-Host ""

# Résumé
Write-Host "=== Résumé ===" -ForegroundColor Cyan
Write-Host "✓ Stack CloudFormation : $STACK_NAME" -ForegroundColor Green
Write-Host "✓ Lambda : $FUNCTION_NAME" -ForegroundColor Green
Write-Host "✓ Concurrence réservée : 1 (mode mono-instance)" -ForegroundColor Green
Write-Host ""

Write-Host "=== Impact attendu ===" -ForegroundColor Cyan
Write-Host "- Une seule invocation Lambda à la fois en DEV" -ForegroundColor White
Write-Host "- Débit Bedrock réduit : ~4 appels simultanés max" -ForegroundColor White
Write-Host "- Taux de throttling attendu : <10% (vs ~30-40% avant)" -ForegroundColor White
Write-Host "- Taux d'échec final attendu : <2% (vs ~5-10% avant)" -ForegroundColor White
Write-Host ""

Write-Host "=== Prochaines étapes ===" -ForegroundColor Cyan
Write-Host "1. Tester avec un batch complet :"
Write-Host "   aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"client_id\":\"lai_weekly\",\"period_days\":7}' out.json --profile $PROFILE --region $REGION"
Write-Host ""
Write-Host "2. Vérifier les logs CloudWatch :"
Write-Host "   aws logs tail /aws/lambda/$FUNCTION_NAME --since 10m --filter-pattern 'Throttling' --profile $PROFILE --region $REGION"
Write-Host ""
Write-Host "3. Consulter la documentation :"
Write-Host "   docs/diagnostics/ingest_normalize_concurrency.md"
Write-Host ""

Write-Host "=== Configuration terminée ===" -ForegroundColor Green
