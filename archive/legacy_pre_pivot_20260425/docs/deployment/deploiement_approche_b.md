# Guide de Deploiement - Approche B: Prompts Pre-construits

**Date**: 2025-12-23
**Version**: 1.0
**Client POC**: lai_weekly_v5

---

## ETAPE 1: UPLOAD FICHIERS CANONICAL SUR S3

### 1.1 Upload prompts LAI

```bash
# Upload prompt normalisation LAI
aws s3 cp canonical/prompts/normalization/lai_prompt.yaml s3://vectora-inbox-config-dev/canonical/prompts/normalization/lai_prompt.yaml --profile rag-lai-prod --region eu-west-3

# Upload prompt matching LAI
aws s3 cp canonical/prompts/matching/lai_prompt.yaml s3://vectora-inbox-config-dev/canonical/prompts/matching/lai_prompt.yaml --profile rag-lai-prod --region eu-west-3
```

### 1.2 Upload client config lai_weekly_v5

```bash
# Upload configuration client avec bedrock_config
aws s3 cp client-config-examples/lai_weekly_v5.yaml s3://vectora-inbox-config-dev/clients/lai_weekly_v5.yaml --profile rag-lai-prod --region eu-west-3
```

### 1.3 Verification uploads

```bash
# Verifier prompts
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/normalization/ --profile rag-lai-prod --region eu-west-3

# Verifier client config
aws s3 ls s3://vectora-inbox-config-dev/clients/lai_weekly_v5.yaml --profile rag-lai-prod --region eu-west-3
```

---

## ETAPE 2: BUILD ET DEPLOY LAMBDA LAYERS

### 2.1 Build layer vectora-core (avec prompt_resolver)

```bash
# Creer repertoire de build
mkdir layer_vectora_core_approche_b
cd layer_vectora_core_approche_b

# Copier vectora_core avec prompt_resolver
xcopy /E /I ..\src_v2\vectora_core vectora_core

# Creer le zip
powershell Compress-Archive -Path vectora_core -DestinationPath ..\vectora-core-approche-b.zip -Force
cd ..
```

### 2.2 Upload layer sur AWS

```bash
# Upload layer
aws lambda publish-layer-version --layer-name vectora-inbox-vectora-core-approche-b-dev --description "Vectora Core avec Approche B" --zip-file fileb://vectora-core-approche-b.zip --compatible-runtimes python3.11 --profile rag-lai-prod --region eu-west-3
```

### 2.3 Update Lambda normalize-score-v2

```bash
# Update Lambda avec nouveau layer
aws lambda update-function-configuration --function-name vectora-inbox-normalize-score-v2-dev --layers <COMMON_DEPS_ARN> <VECTORA_CORE_APPROCHE_B_ARN> --profile rag-lai-prod --region eu-west-3
```

---

## ETAPE 3: TEST E2E

### 3.1 Test normalisation

```bash
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v5
```

### 3.2 Verification logs

```bash
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev --follow --profile rag-lai-prod --region eu-west-3
```

**Logs attendus**:
```
Approche B activee: prompt lai charge
Prompt construit via Approche B
```

---

## CHECKLIST DEPLOIEMENT

### Pre-deploiement
- [ ] Tests locaux passes (4/4)
- [ ] Backup client config existant

### Deploiement
- [ ] Prompts LAI uploades sur S3
- [ ] Client config lai_weekly_v5 uploade
- [ ] Layer vectora-core-approche-b cree
- [ ] Lambda mise a jour

### Post-deploiement
- [ ] Test E2E reussi
- [ ] Logs confirment Approche B
- [ ] Resultats valides

---

## ROLLBACK

```bash
# Revenir au layer precedent
aws lambda update-function-configuration --function-name vectora-inbox-normalize-score-v2-dev --layers <COMMON_DEPS_ARN> <PREVIOUS_VECTORA_CORE_ARN> --profile rag-lai-prod --region eu-west-3
```
