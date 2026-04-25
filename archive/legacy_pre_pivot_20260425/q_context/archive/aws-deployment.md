# Déploiement AWS Vectora Inbox

**Date**: 2026-02-02  
**Version**: 1.0  
**Principe**: Un déploiement AWS = Code + Data + Validation

---

## 🚨 RÈGLE D'OR

**Déploiement AWS Complet = Code + Data + Test**

Ne JAMAIS dire "déploiement complété" sans vérifier S3 et test E2E.

---

## ✅ CHECKLIST COMPLÈTE

### 1. Code Lambda (Layers)

- [ ] Build layers: `python scripts/build/build_all.py`
- [ ] Deploy layers: `python scripts/deploy/deploy_env.py --env dev`
- [ ] Vérifier update Lambdas (automatique via deploy_env.py)

### 2. Fichiers Canonical S3 (SOUVENT OUBLIÉ!)

- [ ] Identifier fichiers modifiés: `git status canonical/`
- [ ] Upload vers S3:
```bash
aws s3 sync canonical/ s3://vectora-inbox-config-{env}/canonical/ \
  --profile rag-lai-prod --region eu-west-3
```
- [ ] Vérifier présence:
```bash
aws s3 ls s3://vectora-inbox-config-{env}/canonical/prompts/ \
  --recursive --profile rag-lai-prod
```

### 3. Client Configs

- [ ] Vérifier configs modifiés: `git status client-config-examples/`
- [ ] Upload si nécessaire (généralement auto-généré par runners)

### 4. Validation Post-Déploiement

- [ ] Test E2E AWS:
```bash
python scripts/invoke/invoke_e2e_workflow.py \
  --client-id lai_weekly_vX --env dev
```
- [ ] Vérifier logs Lambda (pas d'erreurs FileNotFound)
- [ ] Confirmer résultats attendus

---

## 📊 Matrice Décision Rapide

| Changement | Build | Deploy Layer | Upload Canonical | Test E2E |
|------------|-------|--------------|------------------|----------|
| Code Python | ✅ | ✅ | ❌ | ✅ |
| Canonical prompts | ❌ | ❌ | ✅ | ✅ |
| Canonical domains | ❌ | ❌ | ✅ | ✅ |
| Code + Canonical | ✅ | ✅ | ✅ | ✅ |

---

## 🔧 Scripts de Déploiement

### Build

```bash
# Build tous les artefacts
python scripts/build/build_all.py

# Build layer spécifique
python scripts/build/build_layer_vectora_core.py
python scripts/build/build_layer_common_deps.py
```

### Deploy Dev

```bash
# Deploy complet dev (layers + update Lambdas automatique)
python scripts/deploy/deploy_env.py --env dev

# Comportement deploy_env.py (depuis février 2026):
# 1. Publie vectora-core layer
# 2. Publie common-deps layer
# 3. Récupère ARNs layers
# 4. Met à jour automatiquement 3 Lambdas:
#    - vectora-inbox-ingest-v2-dev
#    - vectora-inbox-normalize-score-v2-dev
#    - vectora-inbox-newsletter-v2-dev
```

### Promote Stage

```bash
# Promouvoir version vers stage
python scripts/deploy/promote.py \
  --to stage \
  --version X.Y.Z \
  --git-sha $(git rev-parse HEAD)
```

### Rollback

```bash
# Rollback vers version précédente
python scripts/deploy/rollback.py \
  --env stage \
  --to-version 1.2.3 \
  --git-tag v1.2.3
```

---

## 🏗️ Infrastructure CloudFormation

### Ordre Déploiement OBLIGATOIRE

1. **S0-core**: Buckets S3
2. **S0-iam**: Rôles IAM
3. **S1-runtime**: Lambdas

### Commandes

```bash
# S0-core
aws cloudformation deploy \
  --template-file infra/s0-core.yaml \
  --stack-name vectora-inbox-s0-core-{env} \
  --parameter-overrides Env={env} ProjectName=vectora-inbox \
  --region eu-west-3 \
  --profile rag-lai-prod

# S0-iam
aws cloudformation deploy \
  --template-file infra/s0-iam.yaml \
  --stack-name vectora-inbox-s0-iam-{env} \
  --capabilities CAPABILITY_IAM \
  --region eu-west-3 \
  --profile rag-lai-prod

# S1-runtime
aws cloudformation deploy \
  --template-file infra/s1-runtime.yaml \
  --stack-name vectora-inbox-s1-runtime-{env} \
  --region eu-west-3 \
  --profile rag-lai-prod
```

---

## 🔍 Détection Problèmes Canonical

### Symptômes

- Lambda logs: `FileNotFoundError: canonical/prompts/domain_scoring/...`
- Lambda logs: `No such key: canonical/domains/...`
- Tests locaux OK, tests AWS KO

### Diagnostic

```bash
# Vérifier fichiers locaux
ls canonical/prompts/domain_scoring/

# Vérifier S3
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ \
  --profile rag-lai-prod

# Upload si manquant
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3
```

---

## 🎯 Règles Q Developer

### AVANT de dire "Déploiement complété"

**Q DOIT se poser ces questions**:

1. Ai-je créé/modifié des fichiers dans `canonical/`?
2. Ces fichiers existent-ils sur S3?
3. Le test E2E AWS passe-t-il?

### JAMAIS assumer

❌ "Le code est déployé donc c'est bon"  
❌ "Les fichiers canonical sont déjà sur S3"  
❌ "Ça marche en local donc ça marchera sur AWS"

### TOUJOURS vérifier

✅ "J'ai vérifié que TOUS les fichiers nécessaires sont sur S3"  
✅ "J'ai lancé un test E2E AWS pour confirmer"  
✅ "J'ai consulté les logs Lambda pour vérifier"

### Phrase Magique

**"Ai-je créé/modifié des fichiers dans canonical/? Sont-ils sur S3?"**

---

## 📋 Workflow Déploiement Standard

```bash
# 1. Modifier code/canonical
# ...

# 2. Commit
git add src_v2/ canonical/ VERSION
git commit -m "feat: description"

# 3. Build
python scripts/build/build_all.py

# 4. Deploy dev (layers + Lambdas)
python scripts/deploy/deploy_env.py --env dev

# 5. Upload canonical (si modifié)
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3

# 6. Test E2E dev
python scripts/invoke/invoke_e2e_workflow.py \
  --client-id lai_weekly_vX --env dev

# 7. Vérifier logs
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --follow --profile rag-lai-prod

# 8. Si OK, promote stage
git tag v1.X.Y -m "Release 1.X.Y"
git push origin develop --tags
python scripts/deploy/promote.py \
  --to stage --version 1.X.Y --git-sha $(git rev-parse HEAD)

# 9. Upload canonical stage
aws s3 sync canonical/ s3://vectora-inbox-config-stage/canonical/ \
  --profile rag-lai-prod --region eu-west-3

# 10. Test E2E stage
python scripts/invoke/invoke_e2e_workflow.py \
  --client-id lai_weekly_vX --env stage
```

---

## 🚫 Anti-Patterns

### ❌ Déployer Code Sans Data

```bash
# ❌ MAUVAIS
python scripts/deploy/deploy_env.py --env dev
# Oublier canonical/ → FileNotFoundError sur AWS
```

```bash
# ✅ BON
python scripts/deploy/deploy_env.py --env dev
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3
```

### ❌ Assumer Fichiers sur S3

```bash
# ❌ MAUVAIS
# "Les fichiers canonical sont déjà sur S3"
# → Pas de vérification
```

```bash
# ✅ BON
# Vérifier présence
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/ \
  --recursive --profile rag-lai-prod
```

### ❌ Dire "Complété" Sans Test

```bash
# ❌ MAUVAIS
python scripts/deploy/deploy_env.py --env dev
# "Déploiement complété" → Pas de test E2E
```

```bash
# ✅ BON
python scripts/deploy/deploy_env.py --env dev
python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_vX --env dev
# "Déploiement complété ET validé"
```

---

## 📊 Validation Post-Déploiement

### Vérifications Obligatoires

```bash
# 1. Layers déployés
aws lambda list-layer-versions \
  --layer-name vectora-inbox-vectora-core-dev \
  --profile rag-lai-prod --region eu-west-3

# 2. Lambdas mises à jour
aws lambda get-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --profile rag-lai-prod --region eu-west-3 \
  | grep LayerArn

# 3. Canonical sur S3
aws s3 ls s3://vectora-inbox-config-dev/canonical/ \
  --recursive --profile rag-lai-prod

# 4. Test E2E
python scripts/invoke/invoke_e2e_workflow.py \
  --client-id lai_weekly_vX --env dev

# 5. Logs Lambda
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 5m --profile rag-lai-prod
```

---

## 🎯 Checklist Finale Q Developer

**Avant de dire "Déploiement AWS complété", Q DOIT**:

- [ ] Build layers réussi
- [ ] Deploy layers réussi
- [ ] Lambdas mises à jour (vérifier ARNs)
- [ ] Canonical uploadé sur S3 (si modifié)
- [ ] Présence fichiers S3 vérifiée
- [ ] Test E2E AWS exécuté
- [ ] Test E2E AWS réussi (StatusCode 200)
- [ ] Logs Lambda consultés (pas d'erreurs)
- [ ] Résultats conformes aux attentes

**Si UNE SEULE case non cochée → Déploiement INCOMPLET**

---

**Déploiement AWS - Version 1.0**  
**Date**: 2026-02-02  
**Statut**: RÈGLE CRITIQUE - Checklist obligatoire
