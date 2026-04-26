# Plan Correctif SIMPLIFIÉ - Gestion Environnements Multi-Env Vectora Inbox

**Date**: 2026-01-30  
**Priorité**: HAUTE  
**Objectif**: Implémenter gestion environnements dev/stage/prod de manière MINIMALISTE  
**Durée totale estimée**: 2-3 semaines (au lieu de 4-6)

**SIMPLIFICATION**: AWS CLI direct au lieu de CloudFormation

---

## 🎯 OBJECTIFS

1. Sauvegarder moteur lai_weekly_v7 fonctionnel actuel
2. Mettre à jour règles développement avec gestion environnements
3. Créer premier environnement stage opérationnel (AWS CLI direct)
4. Établir workflow promotion dev → stage

---

## 📋 PHASES DU PLAN

### PHASE 0: Snapshot Sécurité (IMMÉDIAT - 30 min)

**Objectif**: Créer point de restauration avant toute modification

**Commandes**:
```powershell
cd "C:\Users\franc\OneDrive\Bureau\vectora-inbox"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$snapshot_dir = "backup\snapshots\lai_v7_stable_$timestamp"

# Exécuter commandes du plan_action_immediat_snapshot_lai_v7.md
```

**Validation**:
- [ ] Snapshot créé dans `backup/snapshots/`
- [ ] Test restauration partielle réussi

---

### PHASE 1: Mise à Jour Règles Développement (1 jour)

**Objectif**: Intégrer gestion environnements dans règles Q Developer

**Fichier**: `.q-context/vectora-inbox-development-rules.md`

**Ajouter après "🏗️ ENVIRONNEMENT AWS DE RÉFÉRENCE"**:

```markdown
## 🌍 GESTION DES ENVIRONNEMENTS

**dev**: Développement | **stage**: Pré-production | **prod**: Production

### RÈGLE CRITIQUE POUR Q DEVELOPER

Q Developer DOIT REFUSER tout déploiement AWS sans environnement explicite.

❌ INTERDIT: `aws s3 mb s3://vectora-inbox-config`
✅ OBLIGATOIRE: `aws s3 mb s3://vectora-inbox-config-stage`

Si environnement non clair, Q Developer DOIT demander: "Sur quel environnement? (dev/stage/prod)"
```

**Ajouter après "🔧 RÈGLES D'EXÉCUTION SCRIPTS"**:

```markdown
## 📸 SNAPSHOTS ET ROLLBACK

Obligatoire avant: déploiement stage/prod, modification canonical

```bash
python scripts/maintenance/create_snapshot.py --env dev --name "pre_deploy"
python scripts/maintenance/rollback_snapshot.py --snapshot "pre_deploy_YYYYMMDD"
```
```

**Validation**:
- [ ] Règle refus déploiement sans env ajoutée
- [ ] Section snapshots ajoutée

---

### PHASE 2: Refactoring Configuration Client (1 jour)

**Objectif**: Séparer version client et environnement

**Créer**: `client-config-examples/lai_weekly.yaml`

```yaml
client_profile:
  client_id: "lai_weekly"
  version: "7.0.0"

metadata:
  changelog:
    - version: "7.0.0"
      date: "2026-01-30"
      changes: "Extraction dates Bedrock"
```

**Tester**:
```bash
aws s3 cp client-config-examples/lai_weekly.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly.yaml \
  --profile rag-lai-prod --region eu-west-3

python scripts/invoke/invoke_ingest_v2.py --env dev --client-id lai_weekly
```

**Validation**:
- [ ] Config lai_weekly.yaml testée en dev
- [ ] Pas de régression

---

### PHASE 3: Création Environnement Stage (2-3 jours)

**Objectif**: Créer infrastructure stage avec AWS CLI direct

#### 3.1 Créer Buckets S3 Stage (5 min)

```bash
# Créer 4 buckets stage
for bucket in config data newsletters lambda-code; do
  aws s3 mb s3://vectora-inbox-$bucket-stage \
    --region eu-west-3 --profile rag-lai-prod
  
  # Activer versioning
  aws s3api put-bucket-versioning \
    --bucket vectora-inbox-$bucket-stage \
    --versioning-configuration Status=Enabled \
    --profile rag-lai-prod --region eu-west-3
  
  # Activer chiffrement
  aws s3api put-bucket-encryption \
    --bucket vectora-inbox-$bucket-stage \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
    --profile rag-lai-prod --region eu-west-3
done
```

#### 3.2 Copier Code Dev → Stage (10 min)

```bash
# Copier tout le contenu lambda-code dev → stage
aws s3 sync s3://vectora-inbox-lambda-code-dev/ \
  s3://vectora-inbox-lambda-code-stage/ \
  --profile rag-lai-prod --region eu-west-3
```

#### 3.3 Créer Lambda Layers Stage (5 min)

```bash
# Récupérer ARN layer dev pour copier config
VECTORA_CORE_ARN=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-vectora-core-dev \
  --max-items 1 --query 'LayerVersions[0].LayerVersionArn' \
  --output text --profile rag-lai-prod --region eu-west-3)

# Publier layers stage
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-stage \
  --content S3Bucket=vectora-inbox-lambda-code-stage,S3Key=layers/vectora-core-v42.zip \
  --compatible-runtimes python3.11 python3.12 \
  --profile rag-lai-prod --region eu-west-3

aws lambda publish-layer-version \
  --layer-name vectora-inbox-common-deps-stage \
  --content S3Bucket=vectora-inbox-lambda-code-stage,S3Key=layers/common-deps-v4.zip \
  --compatible-runtimes python3.11 python3.12 \
  --profile rag-lai-prod --region eu-west-3
```

#### 3.4 Créer Lambdas Stage (30 min)

**Option A: Réutiliser rôles IAM dev (PLUS SIMPLE)**

```bash
# Récupérer rôles dev
INGEST_ROLE=$(aws lambda get-function \
  --function-name vectora-inbox-ingest-v2-dev \
  --query 'Configuration.Role' --output text \
  --profile rag-lai-prod --region eu-west-3)

# Récupérer ARNs layers stage
VECTORA_CORE_STAGE=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-vectora-core-stage \
  --max-items 1 --query 'LayerVersions[0].LayerVersionArn' \
  --output text --profile rag-lai-prod --region eu-west-3)

COMMON_DEPS_STAGE=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-common-deps-stage \
  --max-items 1 --query 'LayerVersions[0].LayerVersionArn' \
  --output text --profile rag-lai-prod --region eu-west-3)

# Créer Lambda ingest-v2-stage
aws lambda create-function \
  --function-name vectora-inbox-ingest-v2-stage \
  --runtime python3.12 \
  --role $INGEST_ROLE \
  --handler handler.lambda_handler \
  --code S3Bucket=vectora-inbox-lambda-code-stage,S3Key=lambda/ingest-v2/latest.zip \
  --timeout 300 --memory-size 512 \
  --layers $VECTORA_CORE_STAGE $COMMON_DEPS_STAGE \
  --environment Variables="{ENV=stage,CONFIG_BUCKET=vectora-inbox-config-stage,DATA_BUCKET=vectora-inbox-data-stage,LOG_LEVEL=INFO}" \
  --profile rag-lai-prod --region eu-west-3

# Créer Lambda normalize-score-v2-stage
aws lambda create-function \
  --function-name vectora-inbox-normalize-score-v2-stage \
  --runtime python3.11 \
  --role $INGEST_ROLE \
  --handler handler.lambda_handler \
  --code S3Bucket=vectora-inbox-lambda-code-stage,S3Key=lambda/normalize-score-v2/latest.zip \
  --timeout 300 --memory-size 512 \
  --layers $VECTORA_CORE_STAGE $COMMON_DEPS_STAGE \
  --environment Variables="{ENV=stage,CONFIG_BUCKET=vectora-inbox-config-stage,DATA_BUCKET=vectora-inbox-data-stage,BEDROCK_MODEL_ID=eu.anthropic.claude-sonnet-4-5-20250929-v1:0,BEDROCK_REGION=us-east-1,LOG_LEVEL=INFO}" \
  --profile rag-lai-prod --region eu-west-3

# Créer Lambda newsletter-v2-stage
aws lambda create-function \
  --function-name vectora-inbox-newsletter-v2-stage \
  --runtime python3.11 \
  --role $INGEST_ROLE \
  --handler handler.lambda_handler \
  --code S3Bucket=vectora-inbox-lambda-code-stage,S3Key=lambda/newsletter-v2/latest.zip \
  --timeout 300 --memory-size 512 \
  --layers $VECTORA_CORE_STAGE $COMMON_DEPS_STAGE \
  --environment Variables="{ENV=stage,CONFIG_BUCKET=vectora-inbox-config-stage,DATA_BUCKET=vectora-inbox-data-stage,NEWSLETTERS_BUCKET=vectora-inbox-newsletters-stage,BEDROCK_MODEL_ID=eu.anthropic.claude-sonnet-4-5-20250929-v1:0,BEDROCK_REGION=us-east-1,LOG_LEVEL=INFO}" \
  --profile rag-lai-prod --region eu-west-3
```

#### 3.5 Copier Configurations Stage (5 min)

```bash
# Copier canonical
aws s3 sync s3://vectora-inbox-config-dev/canonical/ \
  s3://vectora-inbox-config-stage/canonical/ \
  --profile rag-lai-prod --region eu-west-3

# Copier config client
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly.yaml \
  s3://vectora-inbox-config-stage/clients/lai_weekly.yaml \
  --profile rag-lai-prod --region eu-west-3
```

#### 3.6 Tests E2E Stage (10 min)

```bash
python scripts/invoke/invoke_ingest_v2.py --env stage --client-id lai_weekly
python scripts/invoke/invoke_normalize_score_v2.py --env stage --client-id lai_weekly
python scripts/invoke/invoke_newsletter_v2.py --env stage --client-id lai_weekly
```

**Validation**:
- [ ] 4 buckets S3 stage créés
- [ ] Code copié vers bucket stage
- [ ] 2 layers stage publiés
- [ ] 3 Lambdas stage créées
- [ ] Configurations copiées
- [ ] Tests E2E stage réussis

---

### PHASE 4: Scripts Promotion (1 jour)

**Objectif**: Automatiser promotion dev → stage

**Fichier**: `scripts/deploy/promote_dev_to_stage_simple.sh`

```bash
#!/bin/bash
set -e

ENV_SOURCE="dev"
ENV_TARGET="stage"
CLIENT_ID=${1:-"lai_weekly"}

echo "🚀 Promotion $ENV_SOURCE → $ENV_TARGET"

# 1. Snapshot
python scripts/maintenance/create_snapshot.py --env $ENV_SOURCE --name "pre_promotion_$(date +%Y%m%d_%H%M%S)"

# 2. Copier code Lambda
aws s3 sync s3://vectora-inbox-lambda-code-$ENV_SOURCE/ \
  s3://vectora-inbox-lambda-code-$ENV_TARGET/ \
  --profile rag-lai-prod --region eu-west-3

# 3. Update Lambdas
for func in ingest-v2 normalize-score-v2 newsletter-v2; do
  aws lambda update-function-code \
    --function-name vectora-inbox-$func-$ENV_TARGET \
    --s3-bucket vectora-inbox-lambda-code-$ENV_TARGET \
    --s3-key lambda/$func/latest.zip \
    --profile rag-lai-prod --region eu-west-3
done

# 4. Copier configs
aws s3 sync s3://vectora-inbox-config-$ENV_SOURCE/canonical/ \
  s3://vectora-inbox-config-$ENV_TARGET/canonical/ \
  --profile rag-lai-prod --region eu-west-3

aws s3 cp s3://vectora-inbox-config-$ENV_SOURCE/clients/$CLIENT_ID.yaml \
  s3://vectora-inbox-config-$ENV_TARGET/clients/$CLIENT_ID.yaml \
  --profile rag-lai-prod --region eu-west-3

# 5. Tests
python scripts/invoke/invoke_ingest_v2.py --env $ENV_TARGET --client-id $CLIENT_ID

echo "✅ Promotion réussie"
```

**Validation**:
- [ ] Script promotion exécutable
- [ ] Test promotion dev → stage réussi

---

## 📊 RÉCAPITULATIF

### Durées Estimées (SIMPLIFIÉES)

- Phase 0: 30 min (snapshot)
- Phase 1: 1 jour (règles développement)
- Phase 2: 1 jour (refactoring config)
- Phase 3: 2-3 jours (infrastructure stage - AWS CLI)
- Phase 4: 1 jour (scripts promotion)

**Total**: 2-3 semaines (au lieu de 4-6)

### Avantages Approche Simplifiée

✅ **Plus rapide**: 2-3 semaines au lieu de 4-6  
✅ **Plus simple**: AWS CLI direct, pas de CloudFormation  
✅ **Moins de dépendances**: Pas besoin de templates CFN  
✅ **Plus flexible**: Modifications rapides  
✅ **Même résultat**: Infrastructure stage identique

### Architecture Finale

**DEV:**
```
Lambdas: vectora-inbox-{fonction}-v2-dev
Buckets: vectora-inbox-{type}-dev
Code: s3://vectora-inbox-lambda-code-dev/
```

**STAGE (indépendant):**
```
Lambdas: vectora-inbox-{fonction}-v2-stage
Buckets: vectora-inbox-{type}-stage
Code: s3://vectora-inbox-lambda-code-stage/
```

### Validation Globale

- [ ] Moteur lai_v7 sauvegardé
- [ ] Q Developer refuse déploiement sans env
- [ ] Config client refactorisée
- [ ] Environnement stage opérationnel
- [ ] Workflow promotion validé

---

## 🎯 PROCHAINES ÉTAPES

1. **GO utilisateur**
2. **Phase 0**: Snapshot (30 min)
3. **Phase 1**: Règles (1 jour)
4. **Phase 2**: Config client (1 jour)
5. **Phase 3**: Infrastructure stage (2-3 jours)
6. **Phase 4**: Scripts promotion (1 jour)

---

## ⚠️ NOTES IMPORTANTES

**Réutilisation rôles IAM dev**:
- Les Lambdas stage utilisent les MÊMES rôles IAM que dev
- Plus simple mais moins isolé
- Pour isolation complète, créer nouveaux rôles stage (ajoute 1 jour)

**Chemins S3 à vérifier avant Phase 3.2**:
```bash
aws s3 ls s3://vectora-inbox-lambda-code-dev/lambda/ --recursive --profile rag-lai-prod
aws s3 ls s3://vectora-inbox-lambda-code-dev/layers/ --recursive --profile rag-lai-prod
```

**Variables environnement Lambdas**:
- Adapter selon besoins réels
- Vérifier variables dev actuelles avant copie

---

**PLAN SIMPLIFIÉ PRÊT - EN ATTENTE GO UTILISATEUR**
