# Script de promotion dev → stage (PowerShell)
# Usage: .\promote_dev_to_stage_simple.ps1 [client_id]

param(
    [string]$ClientId = "lai_weekly"
)

$ENV_SOURCE = "dev"
$ENV_TARGET = "stage"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Promotion $ENV_SOURCE -> $ENV_TARGET" -ForegroundColor Cyan
Write-Host "Client: $ClientId" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Snapshot
Write-Host ""
Write-Host "[1/5] Creation snapshot pre-promotion..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Write-Host "Snapshot: pre_promotion_$timestamp" -ForegroundColor Gray
# python scripts/maintenance/create_snapshot.py --env $ENV_SOURCE --name "pre_promotion_$timestamp"

# 2. Copier code Lambda
Write-Host ""
Write-Host "[2/5] Copie code Lambda $ENV_SOURCE -> $ENV_TARGET..." -ForegroundColor Yellow
aws s3 sync "s3://vectora-inbox-lambda-code-$ENV_SOURCE/" `
  "s3://vectora-inbox-lambda-code-$ENV_TARGET/" `
  --profile rag-lai-prod --region eu-west-3

# 3. Update Lambdas
Write-Host ""
Write-Host "[3/5] Update Lambdas $ENV_TARGET..." -ForegroundColor Yellow

$functions = @(
    @{name="ingest-v2"; key="lambda/ingest-v2/latest.zip"},
    @{name="normalize-score-v2"; key="lambda-packages/vectora-inbox-normalize-score-v2-dev.zip"},
    @{name="newsletter-v2"; key="lambda/newsletter-v2/latest.zip"}
)

foreach ($func in $functions) {
    Write-Host "  - Updating $($func.name)-$ENV_TARGET..." -ForegroundColor Gray
    
    aws lambda update-function-code `
        --function-name "vectora-inbox-$($func.name)-$ENV_TARGET" `
        --s3-bucket "vectora-inbox-lambda-code-$ENV_TARGET" `
        --s3-key $func.key `
        --profile rag-lai-prod --region eu-west-3 | Out-Null
    
    Write-Host "    [OK]" -ForegroundColor Green
}

# 4. Copier configs
Write-Host ""
Write-Host "[4/5] Copie configurations $ENV_SOURCE -> $ENV_TARGET..." -ForegroundColor Yellow

Write-Host "  - Canonical..." -ForegroundColor Gray
aws s3 sync "s3://vectora-inbox-config-$ENV_SOURCE/canonical/" `
  "s3://vectora-inbox-config-$ENV_TARGET/canonical/" `
  --profile rag-lai-prod --region eu-west-3 --quiet

Write-Host "  - Config client $ClientId..." -ForegroundColor Gray
aws s3 cp "s3://vectora-inbox-config-$ENV_SOURCE/clients/$ClientId.yaml" `
  "s3://vectora-inbox-config-$ENV_TARGET/clients/$ClientId.yaml" `
  --profile rag-lai-prod --region eu-west-3

# 5. Tests
Write-Host ""
Write-Host "[5/5] Tests E2E $ENV_TARGET..." -ForegroundColor Yellow
Write-Host "  - Test ingest-v2-$ENV_TARGET..." -ForegroundColor Gray
# python scripts/invoke/invoke_ingest_v2.py --env $ENV_TARGET --client-id $ClientId

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Promotion reussie!" -ForegroundColor Green
Write-Host "Environnement: $ENV_TARGET" -ForegroundColor Cyan
Write-Host "Client: $ClientId" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Green
