# Script de déploiement de la stack s1-runtime en DEV
# Ce script déploie les Lambdas ingest-normalize et engine

$ErrorActionPreference = "Stop"

# Configuration
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"

Write-Host "=== Déploiement de la stack s1-runtime-dev ===" -ForegroundColor Cyan

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

# Déployer la stack runtime
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
    IngestNormalizeCodeKey=lambda/ingest-normalize/latest.zip `
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
  --query "Stacks[0]" > infra/outputs/s1-runtime-dev.json

Write-Host "Outputs sauvegardés dans infra/outputs/s1-runtime-dev.json" -ForegroundColor Green

Write-Host "=== Déploiement terminé ===" -ForegroundColor Cyan
