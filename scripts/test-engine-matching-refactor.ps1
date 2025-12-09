# Script de test de la Lambda engine apres refactor matching generique
# Ce script invoque la Lambda engine pour generer une newsletter lai_weekly sur 7 jours

$ErrorActionPreference = "Stop"

Write-Host "=== Test Lambda Engine - Refactor Matching Generique ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$AWS_PROFILE = "rag-lai-prod"
$AWS_REGION = "eu-west-3"
$LAMBDA_FUNCTION_NAME = "vectora-inbox-engine-dev"

Write-Host "Configuration :" -ForegroundColor Yellow
Write-Host "  - Profil AWS : $AWS_PROFILE"
Write-Host "  - Region : $AWS_REGION"
Write-Host "  - Lambda : $LAMBDA_FUNCTION_NAME"
Write-Host ""

# Payload de test
$PAYLOAD_FILE = "engine_payload.json"
$PAYLOAD_JSON = '{"client_id":"lai_weekly","period_days":7}'
$PAYLOAD_JSON | Out-File -FilePath $PAYLOAD_FILE -Encoding utf8 -NoNewline

Write-Host "Payload de test :" -ForegroundColor Yellow
Write-Host $PAYLOAD_JSON
Write-Host ""

# Invocation de la Lambda
Write-Host "Invocation de la Lambda engine..." -ForegroundColor Green
Write-Host ""

$RESPONSE_FILE = "engine_response.json"

aws lambda invoke `
    --function-name $LAMBDA_FUNCTION_NAME `
    --payload file://$PAYLOAD_FILE `
    --profile $AWS_PROFILE `
    --region $AWS_REGION `
    $RESPONSE_FILE

Write-Host ""
Write-Host "Reponse de la Lambda :" -ForegroundColor Yellow
Get-Content $RESPONSE_FILE | ConvertFrom-Json | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "=== Test termine ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Prochaines etapes :" -ForegroundColor Yellow
Write-Host "  1. Consulter les logs CloudWatch"
Write-Host "  2. Verifier la newsletter generee dans S3 : s3://vectora-inbox-newsletters-dev/lai_weekly/"
Write-Host "  3. Creer le diagnostic dans docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md"
Write-Host ""

# Nettoyage
if (Test-Path $RESPONSE_FILE) { Remove-Item -Force $RESPONSE_FILE }
if (Test-Path $PAYLOAD_FILE) { Remove-Item -Force $PAYLOAD_FILE }
