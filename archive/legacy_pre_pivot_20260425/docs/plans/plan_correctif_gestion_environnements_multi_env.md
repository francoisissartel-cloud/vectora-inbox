# Plan Correctif - Gestion Environnements Multi-Env Vectora Inbox

**Date**: 2026-01-30  
**Priorité**: HAUTE  
**Objectif**: Implémenter gestion environnements dev/stage/prod de manière minimaliste et efficace  
**Durée totale estimée**: 4-6 semaines

---

## 🎯 OBJECTIFS

1. Sauvegarder moteur lai_weekly_v7 fonctionnel actuel
2. Mettre à jour règles développement avec gestion environnements
3. Créer premier environnement stage opérationnel
4. Établir workflow promotion dev → stage

---

## 📋 PHASES DU PLAN

### PHASE 0: Snapshot Sécurité (IMMÉDIAT - 30 min)

**Objectif**: Créer point de restauration avant toute modification

**Actions**:
1. Exécuter script snapshot complet lai_v7
2. Valider snapshot restaurable
3. Documenter dans `docs/snapshots/`

**Livrables**:
- `backup/snapshots/lai_v7_stable_YYYYMMDD_HHMMSS/`
- `docs/snapshots/lai_v7_stable_YYYYMMDD.md`

**Validation**:
- [ ] Snapshot contient lambdas, layers, configs, canonical, data
- [ ] Test restauration partielle réussi
- [ ] Documentation complète

---

### PHASE 1: Mise à Jour Règles Développement (1-2 jours)

**Objectif**: Intégrer gestion environnements dans règles Q Developer

**Actions**:

#### 1.1 Ajouter Section Gestion Environnements

Fichier: `.q-context/vectora-inbox-development-rules.md`

Ajouter après "🏗️ ENVIRONNEMENT AWS DE RÉFÉRENCE":

```markdown
## 🌍 GESTION DES ENVIRONNEMENTS

### Environnements Disponibles

**dev**: Développement et expérimentation
**stage**: Pré-production et validation  
**prod**: Production clients réels

### Convention Nommage

Ressources AWS: `{nom}-{env}`
Config client: `client_id` stable + `version` sémantique

### RÈGLE CRITIQUE POUR Q DEVELOPER

**Q Developer DOIT REFUSER tout déploiement AWS si l'environnement cible n'est PAS explicitement spécifié.**

❌ **INTERDIT**:
```bash
aws cloudformation deploy --stack-name vectora-inbox-s0-core
```

✅ **OBLIGATOIRE**:
```bash
aws cloudformation deploy --stack-name vectora-inbox-s0-core-dev --parameter-overrides Env=dev
```

**Si environnement non clair, Q Developer DOIT**:
1. Refuser d'exécuter la commande
2. Demander à l'utilisateur: "Sur quel environnement souhaitez-vous déployer? (dev/stage/prod)"
3. Attendre confirmation explicite avant de procéder

**Exemples questions Q Developer**:
- "Je vois que vous voulez déployer une Lambda. Sur quel environnement? (dev/stage/prod)"
- "Cette commande CloudFormation ne spécifie pas d'environnement. Confirmez-vous dev, stage ou prod?"
- "Avant de créer ce bucket S3, précisez l'environnement cible."
```

#### 1.2 Ajouter Section Snapshots

Ajouter après "🔧 RÈGLES D'EXÉCUTION SCRIPTS":

```markdown
## 📸 SNAPSHOTS ET ROLLBACK

### Obligatoire Avant

- Déploiement Lambda stage/prod
- Modification canonical
- Promotion stage → prod

### Commandes

```bash
# Créer snapshot
python scripts/maintenance/create_snapshot.py --env dev --name "pre_deploy"

# Rollback
python scripts/maintenance/rollback_snapshot.py --snapshot "pre_deploy_YYYYMMDD"
```
```

#### 1.3 Modifier Section Configuration AWS

Remplacer par:

```markdown
## 🔧 CONFIGURATION AWS PAR ENVIRONNEMENT

### Environnement DEV (Actuel)

Lambdas: vectora-inbox-{fonction}-v2-dev
Buckets: vectora-inbox-{type}-dev
Stacks: vectora-inbox-{stack}-dev

### Environnement STAGE (À créer)

Lambdas: vectora-inbox-{fonction}-v2-stage
Buckets: vectora-inbox-{type}-stage
Stacks: vectora-inbox-{stack}-stage

### Environnement PROD (Futur)

Lambdas: vectora-inbox-{fonction}-v2-prod
Buckets: vectora-inbox-{type}-prod
Stacks: vectora-inbox-{stack}-prod
```

**Livrables**:
- `.q-context/vectora-inbox-development-rules.md` mis à jour

**Validation**:
- [ ] Section environnements ajoutée
- [ ] Règle refus déploiement sans env explicite
- [ ] Section snapshots ajoutée
- [ ] Configuration AWS par env documentée

---

### PHASE 2: Refactoring Configuration Client (2-3 jours)

**Objectif**: Séparer version client et environnement

#### 2.1 Créer Template lai_weekly.yaml

Fichier: `client-config-examples/lai_weekly.yaml`

```yaml
client_profile:
  name: "LAI Intelligence Weekly"
  client_id: "lai_weekly"
  version: "7.0.0"
  active: true

metadata:
  config_version: "7.0.0"
  created_date: "2026-01-30"
  changelog:
    - version: "7.0.0"
      date: "2026-01-30"
      changes: "Extraction dates Bedrock, prompts éditoriaux"
```

#### 2.2 Tester en Dev

```bash
# Copier nouvelle config
aws s3 cp client-config-examples/lai_weekly.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly.yaml \
  --profile rag-lai-prod --region eu-west-3

# Tester moteur avec nouvelle config
python scripts/invoke/invoke_ingest_v2.py --env dev --client-id lai_weekly
python scripts/invoke/invoke_normalize_score_v2.py --env dev --client-id lai_weekly
```

**Livrables**:
- `client-config-examples/lai_weekly.yaml`
- Tests E2E passés avec nouvelle config

**Validation**:
- [ ] Config lai_weekly.yaml créée (sans v7)
- [ ] Moteur fonctionne avec nouvelle config
- [ ] Pas de régression fonctionnelle

---

### PHASE 3: Création Environnement Stage (1-2 semaines)

**Objectif**: Déployer infrastructure stage et promouvoir code dev validé

#### 3.1 Déployer Infrastructure Stage

```bash
# Stack S0-core-stage (crée buckets config, data, newsletters)
aws cloudformation deploy \
  --template-file infra/s0-core.yaml \
  --stack-name vectora-inbox-s0-core-stage \
  --parameter-overrides Env=stage ProjectName=vectora-inbox \
  --region eu-west-3 --profile rag-lai-prod

# Sauvegarder outputs
aws cloudformation describe-stacks \
  --stack-name vectora-inbox-s0-core-stage \
  --region eu-west-3 --profile rag-lai-prod \
  > infra/outputs/s0-core-stage.json

# Créer bucket lambda-code-stage (séparation complète dev/stage)
aws s3 mb s3://vectora-inbox-lambda-code-stage \
  --region eu-west-3 --profile rag-lai-prod

# Activer versioning
aws s3api put-bucket-versioning \
  --bucket vectora-inbox-lambda-code-stage \
  --versioning-configuration Status=Enabled \
  --profile rag-lai-prod --region eu-west-3

# Activer chiffrement
aws s3api put-bucket-encryption \
  --bucket vectora-inbox-lambda-code-stage \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}' \
  --profile rag-lai-prod --region eu-west-3

# Stack S0-iam-stage
aws cloudformation deploy \
  --template-file infra/s0-iam.yaml \
  --stack-name vectora-inbox-s0-iam-stage \
  --parameter-overrides Env=stage \
    ConfigBucketName=vectora-inbox-config-stage \
    DataBucketName=vectora-inbox-data-stage \
    NewslettersBucketName=vectora-inbox-newsletters-stage \
  --capabilities CAPABILITY_IAM \
  --region eu-west-3 --profile rag-lai-prod

# Sauvegarder outputs
aws cloudformation describe-stacks \
  --stack-name vectora-inbox-s0-iam-stage \
  --region eu-west-3 --profile rag-lai-prod \
  > infra/outputs/s0-iam-stage.json
```

#### 3.2 Copier Packages Lambda Dev → Stage

```bash
# Copier layers vers bucket stage
aws s3 cp s3://vectora-inbox-lambda-code-dev/layers/vectora-core-v42.zip \
  s3://vectora-inbox-lambda-code-stage/layers/vectora-core-v42.zip \
  --profile rag-lai-prod --region eu-west-3

aws s3 cp s3://vectora-inbox-lambda-code-dev/layers/common-deps-v4.zip \
  s3://vectora-inbox-lambda-code-stage/layers/common-deps-v4.zip \
  --profile rag-lai-prod --region eu-west-3

# Copier packages Lambda vers bucket stage
aws s3 cp s3://vectora-inbox-lambda-code-dev/lambda/ingest-v2/latest.zip \
  s3://vectora-inbox-lambda-code-stage/lambda/ingest-v2/latest.zip \
  --profile rag-lai-prod --region eu-west-3

aws s3 cp s3://vectora-inbox-lambda-code-dev/lambda/normalize-score-v2/latest.zip \
  s3://vectora-inbox-lambda-code-stage/lambda/normalize-score-v2/latest.zip \
  --profile rag-lai-prod --region eu-west-3

aws s3 cp s3://vectora-inbox-lambda-code-dev/lambda/newsletter-v2/latest.zip \
  s3://vectora-inbox-lambda-code-stage/lambda/newsletter-v2/latest.zip \
  --profile rag-lai-prod --region eu-west-3
```

#### 3.3 Créer Lambda Layers Stage

```bash
# Publier layer vectora-core-stage (depuis bucket stage)
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-stage \
  --content S3Bucket=vectora-inbox-lambda-code-stage,S3Key=layers/vectora-core-v42.zip \
  --compatible-runtimes python3.11 python3.12 \
  --profile rag-lai-prod --region eu-west-3

# Publier layer common-deps-stage (depuis bucket stage)
aws lambda publish-layer-version \
  --layer-name vectora-inbox-common-deps-stage \
  --content S3Bucket=vectora-inbox-lambda-code-stage,S3Key=layers/common-deps-v4.zip \
  --compatible-runtimes python3.11 python3.12 \
  --profile rag-lai-prod --region eu-west-3
```

#### 3.4 Déployer Lambdas Stage

```bash
# Récupérer ARNs rôles IAM stage
INGEST_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name vectora-inbox-s0-iam-stage \
  --query 'Stacks[0].Outputs[?OutputKey==`IngestNormalizeRoleArn`].OutputValue' \
  --output text --profile rag-lai-prod --region eu-west-3)

ENGINE_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name vectora-inbox-s0-iam-stage \
  --query 'Stacks[0].Outputs[?OutputKey==`EngineRoleArn`].OutputValue' \
  --output text --profile rag-lai-prod --region eu-west-3)

# Stack S1-runtime-stage (AVEC bucket lambda-code-stage)
aws cloudformation deploy \
  --template-file infra/s1-runtime.yaml \
  --stack-name vectora-inbox-s1-runtime-stage \
  --parameter-overrides \
    Env=stage \
    ConfigBucketName=vectora-inbox-config-stage \
    DataBucketName=vectora-inbox-data-stage \
    NewslettersBucketName=vectora-inbox-newsletters-stage \
    IngestNormalizeRoleArn=$INGEST_ROLE_ARN \
    EngineRoleArn=$ENGINE_ROLE_ARN \
    IngestNormalizeCodeBucket=vectora-inbox-lambda-code-stage \
    EngineCodeBucket=vectora-inbox-lambda-code-stage \
  --region eu-west-3 --profile rag-lai-prod
```

#### 3.5 Copier Configurations Stage

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

#### 3.6 Tests E2E Stage

```bash
# Test ingest-v2-stage
python scripts/invoke/invoke_ingest_v2.py --env stage --client-id lai_weekly

# Test normalize-score-v2-stage
python scripts/invoke/invoke_normalize_score_v2.py --env stage --client-id lai_weekly

# Test newsletter-v2-stage
python scripts/invoke/invoke_newsletter_v2.py --env stage --client-id lai_weekly
```

**Livrables**:
- Infrastructure stage complète (stacks, buckets, lambdas, layers)
- Bucket `vectora-inbox-lambda-code-stage` créé
- Packages Lambda copiés dev → stage
- Layers stage publiés depuis bucket stage
- Lambdas stage pointant vers bucket stage (indépendance totale)
- `infra/outputs/s0-core-stage.json`
- `infra/outputs/s0-iam-stage.json`
- Tests E2E stage passés

**Validation**:
- [ ] 3 stacks CloudFormation stage déployées
- [ ] 5 buckets S3 stage créés (config, data, newsletters, lambda-code)
- [ ] Packages Lambda copiés vers bucket stage
- [ ] 3 Lambdas stage opérationnelles (pointant vers bucket stage)
- [ ] 2 layers stage publiés (depuis bucket stage)
- [ ] Canonical copié vers stage
- [ ] Config client copié vers stage
- [ ] Tests E2E stage réussis
- [ ] **Indépendance totale dev/stage validée**

---

### PHASE 4: Scripts Promotion (3-5 jours)

**Objectif**: Automatiser promotion dev → stage

#### 4.1 Script Promotion Dev → Stage

Fichier: `scripts/deploy/promote_dev_to_stage.sh`

```bash
#!/bin/bash
set -e

ENV_SOURCE="dev"
ENV_TARGET="stage"
CLIENT_ID=${1:-"lai_weekly"}

echo "🚀 Promotion $ENV_SOURCE → $ENV_TARGET pour client: $CLIENT_ID"

# 1. Snapshot dev
echo "📸 Création snapshot $ENV_SOURCE..."
python scripts/maintenance/create_snapshot.py \
  --env $ENV_SOURCE \
  --name "pre_promotion_$(date +%Y%m%d_%H%M%S)" \
  --client $CLIENT_ID

# 2. Copier packages Lambda dev → stage
echo "📦 Copie packages Lambda..."
aws s3 cp s3://vectora-inbox-lambda-code-$ENV_SOURCE/lambda/ingest-v2/latest.zip \
  s3://vectora-inbox-lambda-code-$ENV_TARGET/lambda/ingest-v2/latest.zip \
  --profile rag-lai-prod --region eu-west-3

aws s3 cp s3://vectora-inbox-lambda-code-$ENV_SOURCE/lambda/normalize-score-v2/latest.zip \
  s3://vectora-inbox-lambda-code-$ENV_TARGET/lambda/normalize-score-v2/latest.zip \
  --profile rag-lai-prod --region eu-west-3

aws s3 cp s3://vectora-inbox-lambda-code-$ENV_SOURCE/lambda/newsletter-v2/latest.zip \
  s3://vectora-inbox-lambda-code-$ENV_TARGET/lambda/newsletter-v2/latest.zip \
  --profile rag-lai-prod --region eu-west-3

# 3. Mettre à jour code Lambdas stage
echo "🔄 Mise à jour code Lambdas $ENV_TARGET..."
aws lambda update-function-code \
  --function-name vectora-inbox-ingest-v2-$ENV_TARGET \
  --s3-bucket vectora-inbox-lambda-code-$ENV_TARGET \
  --s3-key lambda/ingest-v2/latest.zip \
  --profile rag-lai-prod --region eu-west-3

aws lambda update-function-code \
  --function-name vectora-inbox-normalize-score-v2-$ENV_TARGET \
  --s3-bucket vectora-inbox-lambda-code-$ENV_TARGET \
  --s3-key lambda/normalize-score-v2/latest.zip \
  --profile rag-lai-prod --region eu-west-3

aws lambda update-function-code \
  --function-name vectora-inbox-newsletter-v2-$ENV_TARGET \
  --s3-bucket vectora-inbox-lambda-code-$ENV_TARGET \
  --s3-key lambda/newsletter-v2/latest.zip \
  --profile rag-lai-prod --region eu-west-3

# 4. Copier canonical
echo "📦 Copie canonical..."
aws s3 sync s3://vectora-inbox-config-$ENV_SOURCE/canonical/ \
  s3://vectora-inbox-config-$ENV_TARGET/canonical/ \
  --profile rag-lai-prod --region eu-west-3

# 5. Copier config client
echo "📄 Copie config client..."
aws s3 cp s3://vectora-inbox-config-$ENV_SOURCE/clients/$CLIENT_ID.yaml \
  s3://vectora-inbox-config-$ENV_TARGET/clients/$CLIENT_ID.yaml \
  --profile rag-lai-prod --region eu-west-3

# 6. Tests E2E stage
echo "🧪 Tests E2E $ENV_TARGET..."
python scripts/invoke/invoke_ingest_v2.py --env $ENV_TARGET --client-id $CLIENT_ID
python scripts/invoke/invoke_normalize_score_v2.py --env $ENV_TARGET --client-id $CLIENT_ID

echo "✅ Promotion $ENV_SOURCE → $ENV_TARGET réussie"
```

#### 4.2 Script Rollback Snapshot

Fichier: `scripts/maintenance/rollback_snapshot.py`

```python
#!/usr/bin/env python3
import argparse
import subprocess

def rollback_snapshot(snapshot_name, env):
    snapshot_dir = f"backup/snapshots/{snapshot_name}"
    
    print(f"🔄 Rollback depuis: {snapshot_dir}")
    
    # Restaurer config client
    subprocess.run([
        "aws", "s3", "cp",
        f"{snapshot_dir}/clients/lai_weekly.yaml",
        f"s3://vectora-inbox-config-{env}/clients/lai_weekly.yaml",
        "--profile", "rag-lai-prod",
        "--region", "eu-west-3"
    ], check=True)
    
    # Restaurer canonical
    subprocess.run([
        "aws", "s3", "sync",
        f"{snapshot_dir}/canonical/",
        f"s3://vectora-inbox-config-{env}/canonical/",
        "--profile", "rag-lai-prod",
        "--region", "eu-west-3"
    ], check=True)
    
    print("✅ Rollback réussi")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--env", required=True)
    args = parser.parse_args()
    
    rollback_snapshot(args.snapshot, args.env)
```

**Livrables**:
- `scripts/deploy/promote_dev_to_stage.sh`
- `scripts/maintenance/rollback_snapshot.py`

**Validation**:
- [ ] Script promotion exécutable
- [ ] Script rollback exécutable
- [ ] Tests promotion dev → stage réussis

---

## 📊 RÉCAPITULATIF

### Durées Estimées

- Phase 0: 30 min (snapshot)
- Phase 1: 1-2 jours (règles développement)
- Phase 2: 2-3 jours (refactoring config)
- Phase 3: 1-2 semaines (infrastructure stage)
- Phase 4: 3-5 jours (scripts promotion)

**Total**: 4-6 semaines

### Livrables Finaux

1. Snapshot lai_v7 sécurisé
2. Règles développement mises à jour (avec règle refus déploiement)
3. Config client refactorisée (lai_weekly.yaml)
4. Infrastructure stage complète avec **indépendance totale dev/stage**
5. Scripts promotion automatisés (avec copie packages Lambda)

### Architecture Finale

**Environnement DEV:**
```
Lambdas: vectora-inbox-{fonction}-v2-dev
Buckets: vectora-inbox-{type}-dev
Code: s3://vectora-inbox-lambda-code-dev/
```

**Environnement STAGE (indépendant):**
```
Lambdas: vectora-inbox-{fonction}-v2-stage
Buckets: vectora-inbox-{type}-stage
Code: s3://vectora-inbox-lambda-code-stage/
```

**Avantages:**
- ✅ Modification dev n'impacte pas stage
- ✅ Promotion explicite dev → stage
- ✅ Rollback indépendant par environnement
- ✅ Tests isolés par environnement

### Validation Globale

- [ ] Moteur lai_v7 sauvegardé et restaurable
- [ ] Q Developer refuse déploiement sans env explicite
- [ ] Config client sans version dans ID
- [ ] Environnement stage opérationnel
- [ ] Workflow promotion dev → stage validé

---

## 🎯 PROCHAINES ÉTAPES APRÈS PLAN

1. **Attendre GO utilisateur**
2. **Exécuter Phase 0** (snapshot immédiat)
3. **Exécuter Phase 1** (règles développement)
4. **Valider Phase 2** (refactoring config)
5. **Déployer Phase 3** (infrastructure stage)
6. **Automatiser Phase 4** (scripts promotion)

---

**PLAN PRÊT POUR EXÉCUTION - EN ATTENTE DE VALIDATION UTILISATEUR**
