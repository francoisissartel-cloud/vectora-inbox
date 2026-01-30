# Plan Correctif - Layer Stage Legacy & Amélioration Processus Promotion

**Date**: 2026-01-30 (Mis à jour avec gouvernance)  
**Priorité**: CRITIQUE  
**Objectif**: Corriger layer stage legacy + Établir processus promotion fiable  
**Durée totale estimée**: 3 heures (réduit grâce aux scripts gouvernance)

---

## ⚠️ IMPORTANT: GOUVERNANCE EN PLACE

**Ce plan a été mis à jour pour utiliser les scripts de gouvernance.**

**Scripts disponibles**:
- `scripts/build/build_layer_vectora_core.py` - Build layer vectora-core
- `scripts/build/build_layer_common_deps.py` - Build layer common-deps
- `scripts/build/build_all.py` - Build tous les artefacts
- `scripts/deploy/deploy_layer.py` - Deploy layer vers env
- `scripts/deploy/deploy_env.py` - Deploy complet vers env
- `scripts/deploy/promote.py` - Promouvoir version entre envs

**Fichier VERSION**: Versioning centralisé à la racine

**Principe**: Repo local = Source unique de vérité

---

## 🎯 CONTEXTE

### Problème Critique Identifié

**Symptôme**: Extraction dates absente en stage (présente en dev)

**Cause racine**: Layer `vectora-core-stage:1` créé depuis fichier LEGACY `vectora-core-v42.zip` au lieu du code récent

**Impact**:
- Champ `extracted_date` absent dans items curated stage
- Newsletter stage utilise dates génériques au lieu de dates réelles
- Environnement stage NON conforme à dev

---

## 🔍 ANALYSE POST-MORTEM: Pourquoi cette erreur ?

### 1. Cause Immédiate

**Timeline des événements**:
```
09:19 - Layer vectora-core-approche-b-dev:10 créé (AVEC extraction dates)
12:35 - Environnement stage créé
12:35 - Layer vectora-core-stage:1 publié depuis vectora-core-v42.zip (SANS extraction dates)
13:05 - Test stage → extraction dates ABSENTE
```

**Problème**: Le fichier `vectora-core-v42.zip` utilisé pour créer le layer stage était une **version antérieure** à l'ajout de l'extraction de dates.

---

### 2. Pourquoi la Copie Dev→Stage a Échoué ?

#### Demande Initiale
"Créer stage en copie exacte de dev"

#### Ce qui a été fait
```bash
# Commande exécutée
aws s3 sync s3://vectora-inbox-lambda-code-dev/ \
  s3://vectora-inbox-lambda-code-stage/
```

#### Pourquoi ça n'a pas fonctionné

**PROBLÈME #1: Bucket lambda-code-dev VIDE de layers**

Vérification effectuée:
```bash
aws s3 ls s3://vectora-inbox-lambda-code-dev/
# Résultat:
#   PRE lambda-packages/
#   PRE lambda/
# ❌ PAS de dossier layers/
```

**Explication**: Les layers dev ne sont PAS stockés dans `s3://vectora-inbox-lambda-code-dev/`. Ils sont publiés directement via `aws lambda publish-layer-version` et stockés dans un bucket AWS géré.

**Conséquence**: Le `aws s3 sync` a copié un dossier `layers/` qui contenait des fichiers ANCIENS (probablement créés lors d'un test antérieur), dont `vectora-core-v42.zip`.

---

**PROBLÈME #2: Layers Dev Utilisent Nommage Différent**

Dev utilise:
- `vectora-inbox-vectora-core-approche-b-dev:10` (créé 09:19)

Stage a créé:
- `vectora-inbox-vectora-core-stage:1` (depuis v42.zip legacy)

**Explication**: Le layer dev actuel (`approche-b-dev`) n'a jamais été copié car il n'existe pas sous forme de fichier .zip accessible dans S3.

---

**PROBLÈME #3: Absence de Vérification de Contenu**

Lors de la création du layer stage, aucune vérification n'a été faite pour s'assurer que:
- Le fichier .zip contenait le code récent
- Le layer stage était identique au layer dev
- L'extraction de dates était présente

**Explication**: Le processus de promotion était basé sur la **présence de fichiers** (v42.zip existe → on l'utilise) au lieu de la **version du code** (layer dev actuel = approche-b:10).

---

### 3. Pourquoi l'Erreur N'a Pas Été Détectée Plus Tôt ?

#### Phase 0: Audit Infrastructure
✅ Vérifié: Buckets, Layers, Lambdas présents
❌ Non vérifié: Contenu des layers, versions du code

#### Phase 1: Comparaison Configurations
✅ Vérifié: Runtime, Memory, Timeout, Variables ENV
⚠️ Partiellement vérifié: Layers attachés (noms vérifiés, pas contenu)
❌ Non vérifié: Code source dans les layers

#### Phase 3: Tests E2E
✅ Détecté: Extraction dates absente
✅ Détecté: 0 items sélectionnés
❌ Non diagnostiqué immédiatement: Cause racine (layer legacy)

**Pourquoi le diagnostic a pris du temps ?**

1. **Complexité architecture**: Layers séparés du code Lambda
2. **Nommage différent**: `approche-b-dev` vs `vectora-core-stage` masquait le problème
3. **Prompts corrects**: Les prompts étaient alignés, donc le problème semblait être ailleurs
4. **Tests superficiels**: Vérification présence layers, pas contenu

---

### 4. Autres Anomalies Potentielles en Stage ?

**Analyse des risques**:

#### ✅ Confirmé Aligné
- Prompts canonical (lai_normalization.yaml identique)
- Config client (lai_weekly_v7.yaml identique)
- Buckets S3 (structure correcte)
- Permissions IAM (corrigées)

#### ⚠️ À Vérifier
1. **Layer common-deps-stage**: Taille différente (1.9 MB stage vs 778 KB dev)
   - Risque: Versions dépendances différentes
   - Action: Vérifier contenu

2. **Code Lambda handler**: Copié depuis S3, pas depuis layer dev actuel
   - Risque: Version handler différente
   - Action: Comparer checksums

3. **Lambda newsletter-v2-stage**: Utilise aussi vectora-core-stage:1
   - Risque: Même problème layer legacy
   - Action: Vérifier extraction dates newsletter

#### ❌ Anomalies Confirmées
1. **Layer vectora-core-stage:1**: Version legacy (CRITIQUE)
2. **Variables ENV**: Incohérences mineures (PROJECT_NAME, CACHE_BUST)

---

## 📋 PHASES DU PLAN

### PHASE 0: Cadrage (10 min)

**Objectif**: Définir périmètre et stratégie de correction

#### 0.1 Périmètre

**Corrections immédiates**:
- Layer vectora-core-stage (CRITIQUE)
- Layer common-deps-stage (vérification)
- Variables ENV (standardisation)

**Améliorations processus**:
- Système promotion fiable
- Validation automatique
- Documentation

#### 0.2 Stratégie

**Approche**: Reconstruire layers stage depuis repo local (source de vérité)

**Principe**: Repo local → Build → S3 → Lambda (pas de copie dev→stage)

**Validation**: Tests E2E + Comparaison métriques dev/stage

---

### PHASE 1: Diagnostics Approfondis (30 min)

**Objectif**: Identifier toutes les divergences repo/dev/stage

#### 1.1 Vérifier Layer common-deps

**Commandes**:
```bash
# Télécharger layer dev
aws lambda get-layer-version --layer-name vectora-inbox-common-deps-dev \
  --version-number 4 --profile rag-lai-prod --region eu-west-3 \
  --query "Content.Location" --output text > .tmp/layer_dev_url.txt

# Télécharger layer stage
aws lambda get-layer-version --layer-name vectora-inbox-common-deps-stage \
  --version-number 1 --profile rag-lai-prod --region eu-west-3 \
  --query "Content.Location" --output text > .tmp/layer_stage_url.txt

# Comparer tailles et dates
```

**Validation**:
- [ ] Tailles cohérentes
- [ ] Versions dépendances identiques
- [ ] Dates création cohérentes

#### 1.2 Vérifier Code Lambda Handlers

**Commandes**:
```bash
# Comparer checksums code Lambda
aws lambda get-function --function-name vectora-inbox-normalize-score-v2-dev \
  --query "Configuration.CodeSha256" --output text

aws lambda get-function --function-name vectora-inbox-normalize-score-v2-stage \
  --query "Configuration.CodeSha256" --output text
```

**Validation**:
- [ ] Checksums identiques ou différence expliquée
- [ ] Versions handler cohérentes

#### 1.3 Vérifier Newsletter Lambda

**Commandes**:
```bash
# Vérifier layers newsletter
aws lambda get-function --function-name vectora-inbox-newsletter-v2-dev \
  --query "Configuration.Layers[*].Arn"

aws lambda get-function --function-name vectora-inbox-newsletter-v2-stage \
  --query "Configuration.Layers[*].Arn"
```

**Validation**:
- [ ] Newsletter stage utilise aussi vectora-core-stage:1 (legacy)
- [ ] Même problème extraction dates potentiel

#### 1.4 Créer Rapport Divergences

**Fichier**: `.tmp/rapport_divergences_stage.md`

**Contenu**:
- Liste complète divergences
- Priorités correction
- Risques identifiés

---

### PHASE 2: Correctifs (1h)

**Objectif**: Aligner stage sur repo local (source de vérité)

#### 2.1 Reconstruire Layer vectora-core (AVEC GOUVERNANCE)

**✅ Utiliser scripts de gouvernance**:

```bash
cd c:\Users\franc\OneDrive\Bureau\vectora-inbox

# 1. Vérifier version actuelle
type VERSION
# VECTORA_CORE_VERSION=1.2.3

# 2. Build layer depuis repo local (source de vérité)
python scripts\build\build_layer_vectora_core.py

# 3. Vérifier output
dir .build\layers\vectora-core-*.zip
# Devrait afficher: vectora-core-1.2.3.zip (~260 KB)
```

**Validation build**:
- [ ] Layer vectora-core-1.2.3.zip créé
- [ ] Taille cohérente (~260 KB)
- [ ] Contient src_v2/vectora_core/ complet

#### 2.2 Déployer Layer en Stage (AVEC GOUVERNANCE)

**✅ Utiliser script deploy_layer.py**:

```bash
# Deploy layer vers stage
python scripts\deploy\deploy_layer.py \
  --layer-file .build\layers\vectora-core-1.2.3.zip \
  --env stage \
  --layer-name vectora-inbox-vectora-core

# Le script va:
# 1. Upload vers s3://vectora-inbox-lambda-code-stage/layers/
# 2. Publier layer vectora-inbox-vectora-core-stage
# 3. Retourner ARN du nouveau layer
```

**Validation deploy**:
- [ ] Layer publié en stage
- [ ] ARN récupéré
- [ ] Description: "Built from repo - version 1.2.3"

#### 2.3 Mettre à Jour Lambdas Stage

**Récupérer ARNs layers**:
```bash
# Vectora-core (nouveau)
VECTORA_CORE=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-vectora-core-stage \
  --max-items 1 --query 'LayerVersions[0].LayerVersionArn' \
  --output text --profile rag-lai-prod --region eu-west-3)

# Common-deps (existant)
COMMON_DEPS=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-common-deps-stage \
  --max-items 1 --query 'LayerVersions[0].LayerVersionArn' \
  --output text --profile rag-lai-prod --region eu-west-3)

echo "Vectora-core: $VECTORA_CORE"
echo "Common-deps: $COMMON_DEPS"
```

**Mettre à jour Lambdas**:
```bash
# Normalize-score-v2
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-stage \
  --layers "$VECTORA_CORE" "$COMMON_DEPS" \
  --profile rag-lai-prod --region eu-west-3

# Newsletter-v2
aws lambda update-function-configuration \
  --function-name vectora-inbox-newsletter-v2-stage \
  --layers "$VECTORA_CORE" "$COMMON_DEPS" \
  --profile rag-lai-prod --region eu-west-3

# Ingest-v2 (si nécessaire)
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-stage \
  --layers "$VECTORA_CORE" "$COMMON_DEPS" \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Lambdas mises à jour
- [ ] Nouveau layer attaché
- [ ] Aucune erreur configuration

#### 2.4 Standardiser Variables ENV (Optionnel)

**Ajouter PROJECT_NAME à stage**:
```bash
# Ingest
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-stage \
  --environment Variables="{ENV=stage,CONFIG_BUCKET=vectora-inbox-config-stage,DATA_BUCKET=vectora-inbox-data-stage,LOG_LEVEL=INFO,PROJECT_NAME=vectora-inbox}" \
  --profile rag-lai-prod --region eu-west-3

# Normalize-score
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-stage \
  --environment Variables="{ENV=stage,CONFIG_BUCKET=vectora-inbox-config-stage,DATA_BUCKET=vectora-inbox-data-stage,BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0,BEDROCK_REGION=us-east-1,LOG_LEVEL=INFO,PROJECT_NAME=vectora-inbox}" \
  --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Variables ENV cohérentes dev/stage
- [ ] Aucune régression

---

### PHASE 3: Tests Validation (30 min)

**Objectif**: Valider corrections

#### 3.1 Test Extraction Dates Stage

**✅ Utiliser script invoke existant**:

```bash
# Tester normalize-score-v2 en stage
python scripts\invoke\invoke_normalize_score_v2.py \
  --client-id lai_weekly_v7 \
  --env stage

# Le script va:
# 1. Invoquer Lambda stage
# 2. Afficher résultats
# 3. Sauvegarder response dans .tmp/
```

**Vérifier extracted_date présent**:
```bash
# Télécharger items curated stage
aws s3 cp s3://vectora-inbox-data-stage/curated/lai_weekly_v7/2026/01/30/items.json \
  .tmp/items_stage_corrected.json --profile rag-lai-prod --region eu-west-3

# Compter items avec extracted_date
powershell -Command "$items = Get-Content .tmp\items_stage_corrected.json | ConvertFrom-Json; $withDates = ($items | Where-Object { $_.normalized_content.extracted_date -ne `$null }).Count; $total = $items.Count; Write-Host `"Items avec dates: $withDates / $total (`$([math]::Round($withDates/$total*100, 2))%)`""
```

**Critères succès**:
- [ ] Champ `extracted_date` présent
- [ ] >90% items avec date extraite
- [ ] Format dates correct (YYYY-MM-DD)
- [ ] Pas de régression autres champs

#### 3.2 Comparaison Dev vs Stage

**Télécharger données dev pour comparaison**:
```bash
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v7/2026/01/30/items.json \
  .tmp/items_dev.json --profile rag-lai-prod --region eu-west-3
```

**Comparer métriques**:
```powershell
# Script comparaison
$dev = Get-Content .tmp\items_dev.json | ConvertFrom-Json
$stage = Get-Content .tmp\items_stage_corrected.json | ConvertFrom-Json

$dev_dates = ($dev | Where-Object { $_.normalized_content.extracted_date -ne $null }).Count
$stage_dates = ($stage | Where-Object { $_.normalized_content.extracted_date -ne $null }).Count

$dev_total = $dev.Count
$stage_total = $stage.Count

Write-Host "=== Comparaison Dev vs Stage ==="
Write-Host "Dev: $dev_dates/$dev_total dates extraites ($([math]::Round($dev_dates/$dev_total*100, 2))%)"
Write-Host "Stage: $stage_dates/$stage_total dates extraites ($([math]::Round($stage_dates/$stage_total*100, 2))%)"
Write-Host "Différence: $([math]::Abs($dev_dates - $stage_dates)) items"
```

**Critères succès**:
- [ ] Taux extraction dates similaire (±5%)
- [ ] Nombre items similaire (±10%)
- [ ] Pas de régression fonctionnelle

---

### PHASE 4: Documentation (30 min)

**Objectif**: Documenter corrections et commit

#### 4.1 Créer Rapport Corrections

**Fichier**: `.tmp/rapport_corrections_stage.md`

**Contenu**:
```markdown
# Rapport Corrections Layer Stage

**Date**: 2026-01-30
**Problème**: Layer stage legacy sans extraction dates
**Solution**: Rebuild depuis repo local avec scripts gouvernance

## Corrections Appliquées

1. Build vectora-core-1.2.3.zip depuis src_v2/ (source vérité)
2. Deploy layer en stage avec script deploy_layer.py
3. Mise à jour Lambdas stage (normalize, newsletter, ingest)

## Métriques Avant/Après

**Avant**:
- extracted_date: 0% items
- Layer: vectora-core-stage:1 (legacy v42.zip)

**Après**:
- extracted_date: >90% items
- Layer: vectora-core-stage:2 (repo local v1.2.3)

## Tests Validation

- ✅ Extraction dates fonctionnelle
- ✅ Dev/Stage alignés (±5%)
- ✅ Pas de régression

## Statut Final

✅ Stage aligné sur repo local
✅ Extraction dates opérationnelle
✅ Gouvernance appliquée
```

#### 4.2 Commit Corrections

```bash
# Commit plan mis à jour
git add docs/plans/plan_correctif_layer_stage_et_amelioration_promotion.md
git add .tmp/rapport_corrections_stage.md
git commit -m "fix: correction layer stage legacy avec scripts gouvernance

- Layer vectora-core-stage:2 build depuis repo local
- Extraction dates fonctionnelle en stage
- Dev/Stage alignés
- Utilisation scripts gouvernance"

git push
```

**Validation**:
- [ ] Rapport créé
- [ ] Corrections commitées
- [ ] Documentation à jour

---

## 🚀 AMÉLIORATION PROCESSUS PROMOTION

### Analyse: Pourquoi le Processus Actuel a Échoué ?

#### Problèmes Identifiés

1. **Copie aveugle S3**: `aws s3 sync` copie fichiers sans validation contenu
2. **Layers non versionnés**: Pas de lien entre layer dev et fichier .zip
3. **Absence validation**: Pas de tests automatiques post-promotion
4. **Nommage incohérent**: `approche-b-dev` vs `vectora-core-stage` masque divergences
5. **Source de vérité floue**: Repo local vs Dev AWS vs Fichiers S3

---

### Système de Promotion Recommandé

#### Option 1: Promotion Basée Repo (RECOMMANDÉ)

**Principe**: Repo local = Source de vérité unique

**Workflow**:
```
Repo Local → Build → S3 Stage → Lambda Stage
     ↓
     → Build → S3 Dev → Lambda Dev
```

**Avantages**:
- Source unique de vérité
- Reproductible
- Versionné (Git)
- Testable localement

**Inconvénients**:
- Nécessite scripts build
- Plus long (rebuild à chaque fois)

**Implémentation**:
```bash
# Script: scripts/deploy/promote_to_stage.sh
#!/bin/bash
set -e

# 1. Build depuis repo
python scripts/build/build_all_layers.py
python scripts/build/build_all_lambdas.py

# 2. Upload vers S3 stage
aws s3 sync .build/layers/ s3://vectora-inbox-lambda-code-stage/layers/
aws s3 sync .build/lambdas/ s3://vectora-inbox-lambda-code-stage/lambda/

# 3. Publier layers stage
python scripts/deploy/publish_layers.py --env stage

# 4. Mettre à jour Lambdas stage
python scripts/deploy/update_lambdas.py --env stage

# 5. Copier configs
aws s3 sync canonical/ s3://vectora-inbox-config-stage/canonical/

# 6. Tests validation
python scripts/test/validate_environment.py --env stage
```

---

#### Option 2: Promotion Basée Artefacts

**Principe**: Dev produit artefacts versionnés → Stage consomme artefacts

**Workflow**:
```
Repo → Build → Artefacts Versionnés (S3)
                    ↓
              Dev consomme v1.2.3
                    ↓
         Stage consomme v1.2.3 (après validation)
```

**Avantages**:
- Artefacts testés en dev avant stage
- Promotion rapide (pas de rebuild)
- Versioning explicite

**Inconvénients**:
- Nécessite système versioning artefacts
- Plus complexe

**Implémentation**:
```bash
# 1. Build et version
python scripts/build/build_and_version.py --version 1.2.3

# 2. Deploy dev
python scripts/deploy/deploy.py --env dev --version 1.2.3

# 3. Tests dev
python scripts/test/validate_environment.py --env dev

# 4. Promotion stage (si tests OK)
python scripts/deploy/promote.py --from dev --to stage --version 1.2.3

# 5. Tests stage
python scripts/test/validate_environment.py --env stage
```

---

#### Option 3: Promotion Basée Snapshots Lambda

**Principe**: Utiliser versions Lambda AWS pour promotion

**Workflow**:
```
Dev Lambda → Publish Version → Alias "stable"
                                    ↓
                          Stage Lambda pointe vers version
```

**Avantages**:
- Natif AWS
- Rollback facile
- Pas de rebuild

**Inconvénients**:
- Ne gère pas configs/canonical
- Layers séparés
- Moins de contrôle

---

### Recommandation Finale: Système Hybride

**Approche**: Combiner Option 1 (repo) + Option 2 (versioning)

**Architecture**:
```
┌─────────────┐
│ Repo Local  │ (Source de vérité)
└──────┬──────┘
       │
       ├─ Build Layers (versionnés)
       ├─ Build Lambdas (versionnés)
       ├─ Canonical (versionné Git)
       │
       ↓
┌──────────────────────────────┐
│ S3 Artefacts Versionnés      │
│ - layers/vectora-core-v12.zip│
│ - lambdas/ingest-v2-v1.5.zip │
│ - canonical/v1.1/            │
└──────┬───────────────────────┘
       │
       ├─→ Dev (version latest)
       │
       └─→ Stage (version validée)
```

**Scripts Nécessaires**:

1. **scripts/build/build_all.py**: Build layers + lambdas depuis repo
2. **scripts/deploy/deploy_env.py**: Deploy version vers env (dev/stage)
3. **scripts/deploy/promote.py**: Promouvoir version dev→stage
4. **scripts/test/validate_env.py**: Tests validation automatiques
5. **scripts/maintenance/rollback.py**: Rollback vers version précédente

**Workflow Quotidien**:
```bash
# Développement
git commit -m "feat: extraction dates"
python scripts/build/build_all.py --version 1.2.3
python scripts/deploy/deploy_env.py --env dev --version 1.2.3
python scripts/test/validate_env.py --env dev

# Promotion (si tests OK)
python scripts/deploy/promote.py --version 1.2.3 --from dev --to stage
python scripts/test/validate_env.py --env stage

# Rollback (si problème)
python scripts/maintenance/rollback.py --env stage --to-version 1.2.2
```

---

### Checklist Promotion Sécurisée

**Pré-Promotion**:
- [ ] Snapshot environnement source
- [ ] Tests E2E source réussis
- [ ] Changelog version documenté
- [ ] Validation code review

**Promotion**:
- [ ] Build depuis repo local (source vérité)
- [ ] Upload artefacts versionnés S3
- [ ] Publier layers avec description version
- [ ] Mettre à jour Lambdas avec nouveaux layers
- [ ] Copier canonical avec versioning
- [ ] Copier configs clients

**Post-Promotion**:
- [ ] Tests E2E cible réussis
- [ ] Comparaison métriques source/cible (±5%)
- [ ] Validation extraction dates
- [ ] Validation matching/scoring
- [ ] Rapport promotion généré
- [ ] Tag Git version déployée

---

### Validation Automatique

**Script**: `scripts/test/validate_env.py`

**Tests**:
1. **Infrastructure**: Buckets, Layers, Lambdas présents
2. **Configurations**: Variables ENV, Prompts, Canonical
3. **Code**: Checksums layers, versions handlers
4. **Fonctionnel**: Tests E2E, extraction dates, matching
5. **Performance**: Temps exécution, coûts Bedrock
6. **Comparaison**: Métriques vs environnement référence

**Output**: Rapport validation avec score global (0-100)

**Seuil acceptation**: >95% pour promotion stage→prod

---

## 📊 MÉTRIQUES SUCCÈS

### Corrections Immédiates

- [ ] Layer vectora-core-stage:2 avec extraction dates
- [ ] Tests E2E stage réussis
- [ ] Extraction dates >90% items
- [ ] Newsletter avec items sélectionnés >10
- [ ] Métriques dev/stage cohérentes (±5%)

### Améliorations Processus

- [ ] Script promotion automatisé créé
- [ ] Tests validation automatiques créés
- [ ] Documentation promotion complète
- [ ] Post-mortem rédigé
- [ ] Leçons apprises documentées

---

## 🎯 CONCLUSION

### Cause Racine Problème

**Technique**: Layer stage créé depuis fichier legacy au lieu de code récent

**Processus**: Absence de validation contenu lors de la promotion

**Humain**: Confiance aveugle dans `aws s3 sync` sans vérification

### Actions Préventives

1. **Court terme**: Corriger layer stage (ce plan)
2. **Moyen terme**: Créer scripts promotion automatisés
3. **Long terme**: Établir système versioning artefacts

### Engagement Qualité

**Objectif**: Promotion dev→stage sans risque, simple, efficace

**Moyens**:
- Source de vérité unique (repo local)
- Versioning explicite artefacts
- Validation automatique systématique
- Documentation complète processus

---

**Plan Correctif - Version 1.0**  
**Date**: 2026-01-30  
**Durée estimée**: 4 heures  
**Priorité**: CRITIQUE  
**Statut**: PRÊT POUR EXÉCUTION
