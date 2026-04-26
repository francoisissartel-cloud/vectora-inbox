# Plan de Recréation Propre Dev + Stage depuis Repo

**Date**: 2026-01-30  
**Chef de Projet**: Déploiement Vectora Inbox  
**Priorité**: CRITIQUE  
**Objectif**: Recréer Dev et Stage proprement depuis le repo (source de vérité unique)  
**Durée totale estimée**: 2h30

---

## 🎯 OBJECTIF STRATÉGIQUE

**Problème identifié**: Dev et Stage contiennent du legacy compromettant l'intégrité du système
- Layers avec nommages incohérents
- Fichiers obsolètes en S3
- Prompts legacy (lai_prompt.yaml)
- Tailles anormales (common-deps 2.5x plus gros en stage)

**Solution**: Recréer Dev et Stage depuis le repo local (source de vérité)

**Principe**: `Repo Local (Git) → Build → Deploy → Dev/Stage`

---

## 📋 INVENTAIRE COMPLET VECTORA INBOX

### Composants AWS à Déployer

#### 1. Buckets S3 (3 par env)
```
vectora-inbox-config-{env}      # Configurations, canonical, prompts
vectora-inbox-data-{env}        # Données ingérées, curated
vectora-inbox-newsletters-{env} # Newsletters générées
vectora-inbox-lambda-code-{env} # Code Lambda (optionnel)
```

#### 2. Lambda Layers (2 par env)
```
vectora-inbox-vectora-core-{env}  # Code métier (src_v2/vectora_core/)
vectora-inbox-common-deps-{env}   # Dépendances Python (requirements.txt)
```

#### 3. Lambda Functions (3 par env)
```
vectora-inbox-ingest-v2-{env}          # Ingestion sources
vectora-inbox-normalize-score-v2-{env} # Normalisation + Scoring
vectora-inbox-newsletter-v2-{env}      # Génération newsletter
```

#### 4. Configurations S3 (dans config bucket)
```
canonical/
  ├── scopes/           # Entités, keywords, companies
  ├── prompts/          # Prompts Bedrock (normalization, matching, editorial)
  ├── sources/          # Catalogues sources
  └── ingestion/        # Profils ingestion

clients/
  └── lai_weekly_v7.yaml  # Config client de référence
```

#### 5. IAM Roles (3 par env)
```
vectora-inbox-ingest-v2-role-{env}
vectora-inbox-normalize-score-v2-role-{env}
vectora-inbox-newsletter-v2-role-{env}
```

---

## 🗂️ STRUCTURE REPO (Source de Vérité)

### Artefacts à Builder
```
src_v2/
  ├── vectora_core/        → Layer vectora-core
  ├── lambdas/
  │   ├── ingest_v2/       → Lambda ingest-v2
  │   ├── normalize_score_v2/ → Lambda normalize-score-v2
  │   └── newsletter_v2/   → Lambda newsletter-v2
  └── requirements.txt     → Layer common-deps

canonical/                 → Upload vers S3 config
client-config-examples/    → Upload vers S3 config (clients/)
VERSION                    → Versioning centralisé
```

### Scripts Disponibles
```
scripts/build/
  ├── build_layer_vectora_core.py
  ├── build_layer_common_deps.py
  └── build_all.py (à créer si absent)

scripts/deploy/
  ├── deploy_layer.py
  ├── deploy_env.py (à créer si absent)
  └── promote.py
```

---

## 📊 PHASES DU PLAN

### PHASE 0: Préparation et Backup (15 min)

#### 0.1 Backup Données Critiques

**Objectif**: Sauvegarder données avant suppression

**Actions**:
```bash
# Backup données dev (si nécessaire)
aws s3 sync s3://vectora-inbox-data-dev/curated/ \
  s3://vectora-inbox-backup-20260130/dev/curated/ \
  --profile rag-lai-prod --region eu-west-3

# Backup données stage (si nécessaire)
aws s3 sync s3://vectora-inbox-data-stage/curated/ \
  s3://vectora-inbox-backup-20260130/stage/curated/ \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Backup dev créé
- [ ] Backup stage créé
- [ ] Tailles cohérentes

#### 0.2 Documenter État Actuel

**Objectif**: Capturer état avant suppression

**Actions**:
```bash
# Lister layers actuels
aws lambda list-layer-versions --layer-name vectora-inbox-vectora-core-dev \
  --profile rag-lai-prod --region eu-west-3 > .tmp/layers_dev_before.json

aws lambda list-layer-versions --layer-name vectora-inbox-vectora-core-stage \
  --profile rag-lai-prod --region eu-west-3 > .tmp/layers_stage_before.json

# Lister configs Lambda actuelles
aws lambda get-function --function-name vectora-inbox-normalize-score-v2-dev \
  --profile rag-lai-prod --region eu-west-3 > .tmp/lambda_normalize_dev_before.json
```

**Validation**:
- [ ] État dev documenté
- [ ] État stage documenté
- [ ] Fichiers sauvegardés dans .tmp/

#### 0.3 Vérifier Repo Propre

**Objectif**: S'assurer que le repo est la source de vérité

**Actions**:
```bash
cd c:\Users\franc\OneDrive\Bureau\vectora-inbox

# Vérifier hygiène repo
python scripts\maintenance\validate_repo_hygiene.py

# Vérifier VERSION
type VERSION

# Vérifier structure src_v2
dir src_v2\vectora_core
dir src_v2\lambdas
```

**Validation**:
- [ ] Repo propre (pas de fichiers temporaires à la racine)
- [ ] VERSION lisible
- [ ] src_v2/ complet
- [ ] canonical/ complet

---

### PHASE 1: Nettoyage Dev (30 min)

#### 1.1 Supprimer Layers Legacy Dev

**Objectif**: Éliminer layers incohérents

**Actions**:
```bash
# Lister toutes les versions vectora-core dev
aws lambda list-layer-versions --layer-name vectora-inbox-vectora-core-dev \
  --profile rag-lai-prod --region eu-west-3

aws lambda list-layer-versions --layer-name vectora-inbox-vectora-core-approche-b-dev \
  --profile rag-lai-prod --region eu-west-3

# Supprimer versions (garder dernière si besoin rollback)
# Exemple: supprimer vectora-core-dev:38
aws lambda delete-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --version-number 38 \
  --profile rag-lai-prod --region eu-west-3

# Supprimer vectora-core-approche-b-dev (toutes versions)
# Répéter pour chaque version
```

**Validation**:
- [ ] Layers legacy supprimés
- [ ] Seul common-deps-dev conservé (si réutilisable)

#### 1.2 Nettoyer S3 Lambda Code Dev

**Objectif**: Supprimer artefacts obsolètes

**Actions**:
```bash
# Supprimer dossier layers/ legacy
aws s3 rm s3://vectora-inbox-lambda-code-dev/layers/ --recursive \
  --profile rag-lai-prod --region eu-west-3

# Lister ce qui reste
aws s3 ls s3://vectora-inbox-lambda-code-dev/ --recursive \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Dossier layers/ supprimé
- [ ] Pas de fichiers .zip legacy

#### 1.3 Nettoyer Prompts Legacy Dev

**Objectif**: Supprimer prompts obsolètes

**Actions**:
```bash
# Supprimer lai_prompt.yaml (legacy)
aws s3 rm s3://vectora-inbox-config-dev/canonical/prompts/normalization/lai_prompt.yaml \
  --profile rag-lai-prod --region eu-west-3

# Vérifier ce qui reste
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/normalization/ \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] lai_prompt.yaml supprimé
- [ ] lai_normalization.yaml conservé

---

### PHASE 2: Nettoyage Stage (30 min)

#### 2.1 Supprimer Layers Legacy Stage

**Actions**:
```bash
# Lister versions
aws lambda list-layer-versions --layer-name vectora-inbox-vectora-core-stage \
  --profile rag-lai-prod --region eu-west-3

# Supprimer toutes versions
aws lambda delete-layer-version \
  --layer-name vectora-inbox-vectora-core-stage \
  --version-number 1 \
  --profile rag-lai-prod --region eu-west-3

aws lambda delete-layer-version \
  --layer-name vectora-inbox-vectora-core-stage \
  --version-number 2 \
  --profile rag-lai-prod --region eu-west-3

# Supprimer common-deps-stage (sera recréé)
aws lambda delete-layer-version \
  --layer-name vectora-inbox-common-deps-stage \
  --version-number 1 \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Tous layers stage supprimés

#### 2.2 Nettoyer S3 Lambda Code Stage

**Actions**:
```bash
# Supprimer tout le contenu legacy
aws s3 rm s3://vectora-inbox-lambda-code-stage/layers/ --recursive \
  --profile rag-lai-prod --region eu-west-3

aws s3 rm s3://vectora-inbox-lambda-code-stage/lambda/ --recursive \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] S3 lambda-code-stage nettoyé

#### 2.3 Nettoyer Prompts Legacy Stage

**Actions**:
```bash
# Supprimer lai_prompt.yaml
aws s3 rm s3://vectora-inbox-config-stage/canonical/prompts/normalization/lai_prompt.yaml \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Prompts legacy supprimés

---

### PHASE 3: Build depuis Repo (15 min)

#### 3.1 Build Layer vectora-core

**Objectif**: Créer layer depuis src_v2/vectora_core/

**Actions**:
```bash
cd c:\Users\franc\OneDrive\Bureau\vectora-inbox

# Build layer
python scripts\build\build_layer_vectora_core.py

# Vérifier output
dir .build\layers\vectora-core-*.zip
```

**Validation**:
- [ ] vectora-core-1.2.3.zip créé (~260 KB)
- [ ] Contient python/vectora_core/

#### 3.2 Build Layer common-deps

**Actions**:
```bash
# Build layer
python scripts\build\build_layer_common_deps.py

# Vérifier output
dir .build\layers\common-deps-*.zip
```

**Validation**:
- [ ] common-deps-1.0.5.zip créé (~800 KB)

#### 3.3 Build Lambda Packages

**Actions**:
```bash
# Si script build_all.py existe
python scripts\build\build_all.py

# Sinon, créer packages manuellement
# (voir section Scripts à Créer)
```

**Validation**:
- [ ] ingest-v2-1.5.0.zip créé
- [ ] normalize-score-v2-2.1.0.zip créé
- [ ] newsletter-v2-1.8.0.zip créé

---

### PHASE 4: Déploiement Dev (30 min)

#### 4.1 Deploy Layers Dev

**Actions**:
```bash
# Deploy vectora-core
python scripts\deploy\deploy_layer.py \
  --layer-file .build\layers\vectora-core-1.2.3.zip \
  --env dev \
  --layer-name vectora-inbox-vectora-core

# Deploy common-deps
python scripts\deploy\deploy_layer.py \
  --layer-file .build\layers\common-deps-1.0.5.zip \
  --env dev \
  --layer-name vectora-inbox-common-deps
```

**Validation**:
- [ ] vectora-core-dev:1 publié
- [ ] common-deps-dev:1 publié
- [ ] ARNs récupérés

#### 4.2 Upload Canonical Dev

**Actions**:
```bash
# Upload canonical complet
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --delete \
  --profile rag-lai-prod --region eu-west-3

# Upload configs clients
aws s3 cp client-config-examples/lai_weekly_v7.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Canonical uploadé
- [ ] Prompts présents (lai_normalization.yaml)
- [ ] Scopes présents
- [ ] Config client uploadée

#### 4.3 Update Lambda Functions Dev

**Actions**:
```bash
# Récupérer ARNs layers
VECTORA_CORE_ARN=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-vectora-core-dev \
  --max-items 1 --query 'LayerVersions[0].LayerVersionArn' \
  --output text --profile rag-lai-prod --region eu-west-3)

COMMON_DEPS_ARN=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-common-deps-dev \
  --max-items 1 --query 'LayerVersions[0].LayerVersionArn' \
  --output text --profile rag-lai-prod --region eu-west-3)

# Update ingest-v2-dev
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --layers "$VECTORA_CORE_ARN" "$COMMON_DEPS_ARN" \
  --environment Variables="{ENV=dev,CONFIG_BUCKET=vectora-inbox-config-dev,DATA_BUCKET=vectora-inbox-data-dev,LOG_LEVEL=INFO,PROJECT_NAME=vectora-inbox}" \
  --profile rag-lai-prod --region eu-west-3

# Update normalize-score-v2-dev
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers "$VECTORA_CORE_ARN" "$COMMON_DEPS_ARN" \
  --environment Variables="{ENV=dev,CONFIG_BUCKET=vectora-inbox-config-dev,DATA_BUCKET=vectora-inbox-data-dev,BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0,BEDROCK_REGION=us-east-1,LOG_LEVEL=INFO,PROJECT_NAME=vectora-inbox}" \
  --profile rag-lai-prod --region eu-west-3

# Update newsletter-v2-dev
aws lambda update-function-configuration \
  --function-name vectora-inbox-newsletter-v2-dev \
  --layers "$VECTORA_CORE_ARN" "$COMMON_DEPS_ARN" \
  --environment Variables="{ENV=dev,CONFIG_BUCKET=vectora-inbox-config-dev,DATA_BUCKET=vectora-inbox-data-dev,NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev,BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0,BEDROCK_REGION=us-east-1,LOG_LEVEL=INFO,PROJECT_NAME=vectora-inbox}" \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] 3 Lambdas dev mises à jour
- [ ] Layers attachés
- [ ] Variables ENV standardisées

---

### PHASE 5: Déploiement Stage (30 min)

#### 5.1 Deploy Layers Stage

**Actions**:
```bash
# Deploy vectora-core
python scripts\deploy\deploy_layer.py \
  --layer-file .build\layers\vectora-core-1.2.3.zip \
  --env stage \
  --layer-name vectora-inbox-vectora-core

# Deploy common-deps
python scripts\deploy\deploy_layer.py \
  --layer-file .build\layers\common-deps-1.0.5.zip \
  --env stage \
  --layer-name vectora-inbox-common-deps
```

**Validation**:
- [ ] vectora-core-stage:1 publié
- [ ] common-deps-stage:1 publié

#### 5.2 Upload Canonical Stage

**Actions**:
```bash
# Upload canonical
aws s3 sync canonical/ s3://vectora-inbox-config-stage/canonical/ \
  --delete \
  --profile rag-lai-prod --region eu-west-3

# Upload config client
aws s3 cp client-config-examples/lai_weekly_v7.yaml \
  s3://vectora-inbox-config-stage/clients/lai_weekly_v7.yaml \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Canonical uploadé
- [ ] Config client uploadée

#### 5.3 Update Lambda Functions Stage

**Actions**:
```bash
# Récupérer ARNs
VECTORA_CORE_ARN=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-vectora-core-stage \
  --max-items 1 --query 'LayerVersions[0].LayerVersionArn' \
  --output text --profile rag-lai-prod --region eu-west-3)

COMMON_DEPS_ARN=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-common-deps-stage \
  --max-items 1 --query 'LayerVersions[0].LayerVersionArn' \
  --output text --profile rag-lai-prod --region eu-west-3)

# Update 3 Lambdas (même commandes que dev, remplacer dev par stage)
```

**Validation**:
- [ ] 3 Lambdas stage mises à jour

---

### PHASE 6: Tests Validation (20 min)

#### 6.1 Test E2E Dev

**Actions**:
```bash
# Test normalize-score-v2-dev
python scripts\invoke\invoke_normalize_score_v2.py \
  --client-id lai_weekly_v7 \
  --env dev

# Vérifier extracted_date
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v7/latest/items.json \
  .tmp/items_dev_clean.json \
  --profile rag-lai-prod --region eu-west-3

powershell -Command "$items = Get-Content .tmp\items_dev_clean.json | ConvertFrom-Json; $withDates = ($items | Where-Object { $_.normalized_content.extracted_date -ne `$null }).Count; $total = $items.Count; Write-Host \"Dev: $withDates / $total dates\""
```

**Critères succès**:
- [ ] Lambda s'exécute sans erreur
- [ ] extracted_date présent (>90%)
- [ ] Pas d'erreur logs

#### 6.2 Test E2E Stage

**Actions**:
```bash
# Test normalize-score-v2-stage
python scripts\invoke\invoke_normalize_score_v2.py \
  --client-id lai_weekly_v7 \
  --env stage

# Vérifier extracted_date
aws s3 cp s3://vectora-inbox-data-stage/curated/lai_weekly_v7/latest/items.json \
  .tmp/items_stage_clean.json \
  --profile rag-lai-prod --region eu-west-3

powershell -Command "$items = Get-Content .tmp\items_stage_clean.json | ConvertFrom-Json; $withDates = ($items | Where-Object { $_.normalized_content.extracted_date -ne `$null }).Count; $total = $items.Count; Write-Host \"Stage: $withDates / $total dates\""
```

**Critères succès**:
- [ ] Lambda s'exécute sans erreur
- [ ] extracted_date présent (>90%)
- [ ] Résultats similaires à dev (±5%)

#### 6.3 Comparaison Dev vs Stage

**Actions**:
```bash
# Comparer métriques
powershell -Command "
$dev = Get-Content .tmp\items_dev_clean.json | ConvertFrom-Json
$stage = Get-Content .tmp\items_stage_clean.json | ConvertFrom-Json
Write-Host 'Dev items:' $dev.Count
Write-Host 'Stage items:' $stage.Count
Write-Host 'Différence:' ([math]::Abs($dev.Count - $stage.Count))
"
```

**Critères succès**:
- [ ] Nombre items similaire (±10%)
- [ ] Taux dates similaire (±5%)
- [ ] Pas de régression fonctionnelle

---

### PHASE 7: Documentation (10 min)

#### 7.1 Créer Rapport Final

**Fichier**: `.tmp/rapport_recreation_dev_stage.md`

**Contenu**:
- État avant/après
- Artefacts déployés
- Tests validation
- Métriques finales

#### 7.2 Commit Corrections

**Actions**:
```bash
git add docs/plans/plan_recreation_dev_stage_propre.md
git add .tmp/rapport_recreation_dev_stage.md
git commit -m "docs: plan et rapport recréation dev+stage propre

- Dev et Stage recréés depuis repo (source vérité)
- Legacy éliminé (layers incohérents, prompts obsolètes)
- Extraction dates fonctionnelle (>90%)
- Alignement total repo/dev/stage"

git push
```

**Validation**:
- [ ] Plan committé
- [ ] Rapport committé
- [ ] Documentation à jour

---

## ✅ CHECKLIST FINALE

### Infrastructure
- [ ] Layers dev: vectora-core-dev:1, common-deps-dev:1
- [ ] Layers stage: vectora-core-stage:1, common-deps-stage:1
- [ ] Lambdas dev: 3 fonctions mises à jour
- [ ] Lambdas stage: 3 fonctions mises à jour
- [ ] S3 canonical dev: uploadé sans legacy
- [ ] S3 canonical stage: uploadé sans legacy

### Tests
- [ ] Dev E2E: extracted_date >90%
- [ ] Stage E2E: extracted_date >90%
- [ ] Dev/Stage: métriques cohérentes (±5%)
- [ ] Logs: aucune erreur

### Gouvernance
- [ ] Repo = source de vérité unique
- [ ] Aucun legacy en dev/stage
- [ ] Process reproductible documenté
- [ ] Versioning centralisé (VERSION)

---

## 🎯 RÉSULTAT ATTENDU

**Après exécution du plan**:

✅ Dev propre, aligné repo  
✅ Stage propre, aligné repo  
✅ Extraction dates fonctionnelle (>90%)  
✅ Aucun legacy (layers, prompts, S3)  
✅ Process promotion fiable établi  
✅ Confiance 95%

**Durée totale**: 2h30  
**Statut**: PRÊT POUR EXÉCUTION

---

**Plan créé par**: Amazon Q  
**Date**: 2026-01-30  
**Version**: 1.0
