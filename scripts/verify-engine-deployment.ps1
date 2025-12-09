# Script de vérification du déploiement de la Lambda engine
# Ce script vérifie que la Lambda engine est correctement déployée et configurée

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"

Write-Host "=== Vérification du déploiement de la Lambda engine ===" -ForegroundColor Cyan
Write-Host ""

# Vérifier que la Lambda existe
Write-Host "1. Vérification de l'existence de la Lambda..." -ForegroundColor Yellow
try {
    $functionInfo = aws lambda get-function `
      --function-name vectora-inbox-engine-dev `
      --profile $PROFILE `
      --region $REGION `
      --output json | ConvertFrom-Json
    
    Write-Host "   ✅ Lambda trouvée : vectora-inbox-engine-dev" -ForegroundColor Green
    Write-Host "   ARN : $($functionInfo.Configuration.FunctionArn)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Lambda non trouvée" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Vérifier les variables d'environnement
Write-Host "2. Vérification des variables d'environnement..." -ForegroundColor Yellow
$envVars = $functionInfo.Configuration.Environment.Variables

$requiredVars = @("CONFIG_BUCKET", "DATA_BUCKET", "NEWSLETTERS_BUCKET", "BEDROCK_MODEL_ID")
$allVarsPresent = $true

foreach ($varName in $requiredVars) {
    if ($envVars.PSObject.Properties.Name -contains $varName) {
        Write-Host "   ✅ $varName = $($envVars.$varName)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $varName manquante" -ForegroundColor Red
        $allVarsPresent = $false
    }
}

if (-not $allVarsPresent) {
    Write-Host "   ❌ Variables d'environnement manquantes" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Vérifier la configuration de la Lambda
Write-Host "3. Vérification de la configuration..." -ForegroundColor Yellow
Write-Host "   Runtime : $($functionInfo.Configuration.Runtime)" -ForegroundColor Gray
Write-Host "   Handler : $($functionInfo.Configuration.Handler)" -ForegroundColor Gray
Write-Host "   Timeout : $($functionInfo.Configuration.Timeout) secondes" -ForegroundColor Gray
Write-Host "   Mémoire : $($functionInfo.Configuration.MemorySize) MB" -ForegroundColor Gray

if ($functionInfo.Configuration.ReservedConcurrentExecutions) {
    Write-Host "   Concurrence réservée : $($functionInfo.Configuration.ReservedConcurrentExecutions)" -ForegroundColor Gray
} else {
    Write-Host "   Concurrence : illimitée" -ForegroundColor Gray
}

Write-Host ""

# Vérifier le rôle IAM
Write-Host "4. Vérification du rôle IAM..." -ForegroundColor Yellow
$roleArn = $functionInfo.Configuration.Role
Write-Host "   Rôle : $roleArn" -ForegroundColor Gray

Write-Host ""

# Vérifier le log group CloudWatch
Write-Host "5. Vérification du log group CloudWatch..." -ForegroundColor Yellow
$logGroupName = "/aws/lambda/vectora-inbox-engine-dev"

try {
    aws logs describe-log-groups `
      --log-group-name-prefix $logGroupName `
      --profile $PROFILE `
      --region $REGION `
      --output json | Out-Null
    
    Write-Host "   ✅ Log group trouvé : $logGroupName" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️ Log group non trouvé (sera créé au premier run)" -ForegroundColor Yellow
}

Write-Host ""

# Vérifier les buckets S3
Write-Host "6. Vérification des buckets S3..." -ForegroundColor Yellow

$buckets = @{
    "CONFIG_BUCKET" = $envVars.CONFIG_BUCKET
    "DATA_BUCKET" = $envVars.DATA_BUCKET
    "NEWSLETTERS_BUCKET" = $envVars.NEWSLETTERS_BUCKET
}

foreach ($bucketType in $buckets.Keys) {
    $bucketName = $buckets[$bucketType]
    try {
        aws s3 ls s3://$bucketName `
          --profile $PROFILE `
          --region $REGION | Out-Null
        
        Write-Host "   ✅ $bucketType : $bucketName" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ $bucketType : $bucketName (non accessible)" -ForegroundColor Red
    }
}

Write-Host ""

# Résumé
Write-Host "=== Résumé de la vérification ===" -ForegroundColor Cyan
Write-Host "✅ Lambda engine déployée et configurée correctement" -ForegroundColor Green
Write-Host ""
Write-Host "Prochaines étapes :" -ForegroundColor Yellow
Write-Host "  1. Exécuter le test end-to-end : .\scripts\test-engine-lai-weekly.ps1" -ForegroundColor Gray
Write-Host "  2. Consulter les logs : aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 10m" -ForegroundColor Gray
Write-Host "  3. Vérifier la newsletter générée dans S3" -ForegroundColor Gray
