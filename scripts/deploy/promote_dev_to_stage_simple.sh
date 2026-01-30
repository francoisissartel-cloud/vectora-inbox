#!/bin/bash
# Script de promotion dev → stage
# Usage: ./promote_dev_to_stage_simple.sh [client_id]

set -e

ENV_SOURCE="dev"
ENV_TARGET="stage"
CLIENT_ID=${1:-"lai_weekly"}

echo "=========================================="
echo "Promotion $ENV_SOURCE -> $ENV_TARGET"
echo "Client: $CLIENT_ID"
echo "=========================================="

# 1. Snapshot
echo ""
echo "[1/5] Creation snapshot pre-promotion..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
echo "Snapshot: pre_promotion_$TIMESTAMP"
# python scripts/maintenance/create_snapshot.py --env $ENV_SOURCE --name "pre_promotion_$TIMESTAMP"

# 2. Copier code Lambda
echo ""
echo "[2/5] Copie code Lambda $ENV_SOURCE -> $ENV_TARGET..."
aws s3 sync s3://vectora-inbox-lambda-code-$ENV_SOURCE/ \
  s3://vectora-inbox-lambda-code-$ENV_TARGET/ \
  --profile rag-lai-prod --region eu-west-3

# 3. Update Lambdas
echo ""
echo "[3/5] Update Lambdas $ENV_TARGET..."

for func in ingest-v2 normalize-score-v2 newsletter-v2; do
  echo "  - Updating $func-$ENV_TARGET..."
  
  # Determiner le chemin S3 du code
  if [ "$func" = "ingest-v2" ]; then
    S3_KEY="lambda/ingest-v2/latest.zip"
  elif [ "$func" = "newsletter-v2" ]; then
    S3_KEY="lambda/newsletter-v2/latest.zip"
  else
    S3_KEY="lambda-packages/vectora-inbox-normalize-score-v2-dev.zip"
  fi
  
  aws lambda update-function-code \
    --function-name vectora-inbox-$func-$ENV_TARGET \
    --s3-bucket vectora-inbox-lambda-code-$ENV_TARGET \
    --s3-key $S3_KEY \
    --profile rag-lai-prod --region eu-west-3 > /dev/null
  
  echo "    [OK]"
done

# 4. Copier configs
echo ""
echo "[4/5] Copie configurations $ENV_SOURCE -> $ENV_TARGET..."

echo "  - Canonical..."
aws s3 sync s3://vectora-inbox-config-$ENV_SOURCE/canonical/ \
  s3://vectora-inbox-config-$ENV_TARGET/canonical/ \
  --profile rag-lai-prod --region eu-west-3 --quiet

echo "  - Config client $CLIENT_ID..."
aws s3 cp s3://vectora-inbox-config-$ENV_SOURCE/clients/$CLIENT_ID.yaml \
  s3://vectora-inbox-config-$ENV_TARGET/clients/$CLIENT_ID.yaml \
  --profile rag-lai-prod --region eu-west-3

# 5. Tests
echo ""
echo "[5/5] Tests E2E $ENV_TARGET..."
echo "  - Test ingest-v2-$ENV_TARGET..."
# python scripts/invoke/invoke_ingest_v2.py --env $ENV_TARGET --client-id $CLIENT_ID

echo ""
echo "=========================================="
echo "Promotion reussie!"
echo "Environnement: $ENV_TARGET"
echo "Client: $CLIENT_ID"
echo "=========================================="
