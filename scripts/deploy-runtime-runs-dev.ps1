# Script de déploiement de la stack s1-runtime en DEV avec logique par runs
# Ce script déploie la Lambda ingest-normalize refactorisée avec logique par runs

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"

Write-Host "=== Déploiement de la stack s1-runtime-dev avec logique par runs ===" -ForegroundColor Cyan

# Vérifier que le package existe dans S3
Write-Host "Vérification du package dans S3..." -ForegroundColor Yellow
$packageExists = aws s3 ls s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/runs-latest.zip `
  --profile $PROFILE `
  --region $REGION

if (!$packageExists) {
    Write-Host "ERREUR: Package runs-latest.zip non trouvé dans S3" -ForegroundColor Red
    Write-Host "Exécutez d'abord : .\scripts\package-ingest-normalize-runs.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Package trouvé dans S3" -ForegroundColor Green

# Récupérer les ARNs des rôles IAM depuis la stack s0-iam
Write-Host "Récupération des ARNs des rôles IAM..." -ForegroundColor Yellow
$INGEST_ROLE_ARN = (aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-iam-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='IngestNormalizeRoleArn'].OutputValue" `
  --output text)

$ENGINE_ROLE_ARN = (aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-iam-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='EngineRoleArn'].OutputValue" `
  --output text)

Write-Host "IngestNormalizeRoleArn: $INGEST_ROLE_ARN" -ForegroundColor Green
Write-Host "EngineRoleArn: $ENGINE_ROLE_ARN" -ForegroundColor Green

# Déployer la stack runtime avec le nouveau package
Write-Host "Déploiement de la stack CloudFormation..." -ForegroundColor Yellow
aws cloudformation deploy `
  --template-file infra/s1-runtime.yaml `
  --stack-name vectora-inbox-s1-runtime-dev `
  --parameter-overrides `
    Env=dev `
    ProjectName=vectora-inbox `
    ConfigBucketName=vectora-inbox-config-dev `
    DataBucketName=vectora-inbox-data-dev `
    NewslettersBucketName=vectora-inbox-newsletters-dev `
    IngestNormalizeRoleArn=$INGEST_ROLE_ARN `
    EngineRoleArn=$ENGINE_ROLE_ARN `
    IngestNormalizeCodeBucket=$ARTIFACTS_BUCKET `
    IngestNormalizeCodeKey=lambda/ingest-normalize/runs-latest.zip `
    EngineCodeBucket=$ARTIFACTS_BUCKET `
    EngineCodeKey=lambda/engine/latest.zip `
    PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key `
    BedrockModelId=eu.anthropic.claude-sonnet-4-5-20250929-v1:0 `
  --profile $PROFILE `
  --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "Stack déployée avec succès" -ForegroundColor Green
} else {
    Write-Host "Erreur lors du déploiement de la stack" -ForegroundColor Red
    exit 1
}

# Sauvegarder les outputs
Write-Host "Sauvegarde des outputs de la stack..." -ForegroundColor Yellow
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s1-runtime-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Stacks[0]" > infra/outputs/s1-runtime-dev-runs.json

Write-Host "Outputs sauvegardés dans infra/outputs/s1-runtime-dev-runs.json" -ForegroundColor Green

# Récupérer les informations de la Lambda déployée
Write-Host "Récupération des informations de la Lambda..." -ForegroundColor Yellow
$LAMBDA_ARN = (aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s1-runtime-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='IngestNormalizeLambdaArn'].OutputValue" `
  --output text)

Write-Host "Lambda ARN: $LAMBDA_ARN" -ForegroundColor Green

# Vérifier la configuration de la Lambda
Write-Host "Vérification de la configuration de la Lambda..." -ForegroundColor Yellow
$lambdaConfig = aws lambda get-function `
  --function-name vectora-inbox-ingest-normalize-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Configuration.{Runtime:Runtime,Timeout:Timeout,MemorySize:MemorySize,LastModified:LastModified}" `
  --output table

Write-Host "Configuration de la Lambda:" -ForegroundColor Green
Write-Host $lambdaConfig

Write-Host "=== Déploiement terminé ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Lambda ingest-normalize avec logique par runs deployee !" -ForegroundColor Green
Write-Host ""
Write-Host "Informations de deploiement :" -ForegroundColor Yellow
Write-Host "   Lambda: vectora-inbox-ingest-normalize-dev" -ForegroundColor White
Write-Host "   Package: s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/runs-latest.zip" -ForegroundColor White
Write-Host "   ARN: $LAMBDA_ARN" -ForegroundColor White
Write-Host ""
Write-Host "Prochaine etape : Test avec lai_weekly_v2" -ForegroundColor Yellow
Write-Host "   .\scripts\test-ingest-normalize-runs-dev.ps1" -ForegroundColor White