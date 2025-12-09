# Plan de déploiement CLI - MVP LAI (Environnement DEV)

## Vue d'ensemble

Ce document décrit le processus complet de déploiement du MVP Vectora Inbox pour l'environnement **DEV** sur AWS, en utilisant AWS CLI.

**Objectif** : Déployer l'infrastructure complète (buckets S3, rôles IAM, fonctions Lambda) et tester le workflow d'ingestion-normalisation pour le client `lai_weekly`.

**Environnement cible** :
- Compte AWS : `786469175371`
- Région : `eu-west-3` (Paris)
- Profil AWS CLI : `rag-lai-prod`
- Environnement logique : `dev`

---

## Phase 0 – Prérequis locaux

### Vérifier l'installation d'AWS CLI

```powershell
# Vérifier la version d'AWS CLI
aws --version
```

**Résultat attendu** : `aws-cli/2.x.x` ou supérieur.

Si AWS CLI n'est pas installé, téléchargez-le depuis : https://aws.amazon.com/cli/

### Vérifier le profil AWS

```powershell
# Lister les profils configurés
aws configure list-profiles
```

**Résultat attendu** : Le profil `rag-lai-prod` doit apparaître dans la liste.

### Vérifier l'identité AWS

```powershell
# Vérifier l'identité du profil
aws sts get-caller-identity --profile rag-lai-prod --region eu-west-3
```

**Résultat attendu** :
```json
{
    "UserId": "...",
    "Account": "786469175371",
    "Arn": "arn:aws:sts::786469175371:assumed-role/AWSReservedSSO_RAGLai-Admin_..."
}
```

**Pourquoi cette étape est importante** : Elle confirme que vous avez accès au compte AWS et que vos credentials sont valides.

---

## Phase 1 – Validation des templates CloudFormation

Avant de déployer, il est essentiel de valider la syntaxe des templates CloudFormation.

### Valider s0-core.yaml

```powershell
aws cloudformation validate-template `
  --template-body file://infra/s0-core.yaml `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat attendu** : Un JSON décrivant les paramètres du template (pas d'erreur).

### Valider s0-iam.yaml

```powershell
aws cloudformation validate-template `
  --template-body file://infra/s0-iam.yaml `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat attendu** : Un JSON décrivant les paramètres du template (pas d'erreur).

### Valider s1-runtime.yaml

```powershell
aws cloudformation validate-template `
  --template-body file://infra/s1-runtime.yaml `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat attendu** : Un JSON décrivant les paramètres du template (pas d'erreur).

**Pourquoi cette étape est importante** : La validation détecte les erreurs de syntaxe YAML avant le déploiement, ce qui évite des échecs coûteux en temps.

---

## Phase 2 – Packaging du code Lambda

Les fonctions Lambda nécessitent que le code Python soit packagé avec ses dépendances dans des fichiers ZIP.

### Créer le dossier de build

```powershell
# Créer le dossier build s'il n'existe pas
mkdir build -ErrorAction SilentlyContinue
```

### Packager la Lambda ingest-normalize

```powershell
# Variables
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$BUILD_DIR = "build/ingest-normalize"

# Créer le dossier de build pour ingest-normalize
mkdir $BUILD_DIR -ErrorAction SilentlyContinue

# Copier le handler
Copy-Item src/lambdas/ingest_normalize/handler.py $BUILD_DIR/handler.py

# Copier le package vectora_core
Copy-Item -Recurse src/vectora_core $BUILD_DIR/vectora_core

# Installer les dépendances
pip install -r requirements.txt -t $BUILD_DIR --upgrade

# Créer le ZIP
Compress-Archive -Path $BUILD_DIR/* -DestinationPath build/ingest-normalize.zip -Force
```

### Packager la Lambda engine

```powershell
# Variables
$BUILD_DIR = "build/engine"

# Créer le dossier de build pour engine
mkdir $BUILD_DIR -ErrorAction SilentlyContinue

# Copier le handler
Copy-Item src/lambdas/engine/handler.py $BUILD_DIR/handler.py

# Copier le package vectora_core
Copy-Item -Recurse src/vectora_core $BUILD_DIR/vectora_core

# Installer les dépendances
pip install -r requirements.txt -t $BUILD_DIR --upgrade

# Créer le ZIP
Compress-Archive -Path $BUILD_DIR/* -DestinationPath build/engine.zip -Force
```

### Créer un bucket S3 pour les artefacts Lambda (si nécessaire)

```powershell
# Nom du bucket d'artefacts
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"

# Créer le bucket
aws s3 mb s3://$ARTIFACTS_BUCKET --profile $PROFILE --region $REGION
```

**Note** : Si le bucket existe déjà, cette commande échouera (c'est normal).

### Uploader les packages Lambda vers S3

```powershell
# Upload ingest-normalize
aws s3 cp build/ingest-normalize.zip s3://$ARTIFACTS_BUCKET/lambda/ingest-normalize/latest.zip `
  --profile $PROFILE `
  --region $REGION

# Upload engine
aws s3 cp build/engine.zip s3://$ARTIFACTS_BUCKET/lambda/engine/latest.zip `
  --profile $PROFILE `
  --region $REGION
```

**Pourquoi cette étape est importante** : CloudFormation a besoin que le code Lambda soit disponible dans S3 avant de créer les fonctions.

---

## Phase 3 – Déploiement des stacks CloudFormation

Les stacks doivent être déployées dans l'ordre : **s0-core** → **s0-iam** → **s1-runtime**.

### Déployer s0-core (buckets S3)

```powershell
aws cloudformation deploy `
  --template-file infra/s0-core.yaml `
  --stack-name vectora-inbox-s0-core-dev `
  --parameter-overrides Env=dev ProjectName=vectora-inbox `
  --profile $PROFILE `
  --region $REGION
```

**Résultat attendu** : Message `Successfully created/updated stack - vectora-inbox-s0-core-dev`.

**Buckets créés** :
- `vectora-inbox-config-dev`
- `vectora-inbox-data-dev`
- `vectora-inbox-newsletters-dev`

### Sauvegarder les outputs de s0-core

```powershell
# Créer le dossier outputs
mkdir infra/outputs -ErrorAction SilentlyContinue

# Récupérer les outputs
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-core-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Stacks[0]" > infra/outputs/s0-core-dev.json
```

### Déployer s0-iam (rôles IAM)

```powershell
aws cloudformation deploy `
  --template-file infra/s0-iam.yaml `
  --stack-name vectora-inbox-s0-iam-dev `
  --parameter-overrides `
    Env=dev `
    ProjectName=vectora-inbox `
    ConfigBucketName=vectora-inbox-config-dev `
    DataBucketName=vectora-inbox-data-dev `
    NewslettersBucketName=vectora-inbox-newsletters-dev `
    PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key `
  --capabilities CAPABILITY_IAM `
  --profile $PROFILE `
  --region $REGION
```

**Résultat attendu** : Message `Successfully created/updated stack - vectora-inbox-s0-iam-dev`.

**Rôles créés** :
- Rôle pour `vectora-inbox-ingest-normalize`
- Rôle pour `vectora-inbox-engine`

### Sauvegarder les outputs de s0-iam

```powershell
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-iam-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Stacks[0]" > infra/outputs/s0-iam-dev.json
```

### Récupérer les ARNs des rôles IAM

```powershell
# Récupérer l'ARN du rôle ingest-normalize
$INGEST_ROLE_ARN = (aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-iam-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='IngestNormalizeRoleArn'].OutputValue" `
  --output text)

# Récupérer l'ARN du rôle engine
$ENGINE_ROLE_ARN = (aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-iam-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Stacks[0].Outputs[?OutputKey=='EngineRoleArn'].OutputValue" `
  --output text)

# Afficher les ARNs
Write-Host "IngestNormalizeRoleArn: $INGEST_ROLE_ARN"
Write-Host "EngineRoleArn: $ENGINE_ROLE_ARN"
```

### Déployer s1-runtime (fonctions Lambda)

```powershell
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
    IngestNormalizeCodeBucket=vectora-inbox-lambda-code-dev `
    IngestNormalizeCodeKey=lambda/ingest-normalize/latest.zip `
    EngineCodeBucket=vectora-inbox-lambda-code-dev `
    EngineCodeKey=lambda/engine/latest.zip `
    PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key `
    BedrockModelId=anthropic.claude-3-sonnet-20240229-v1:0 `
  --profile $PROFILE `
  --region $REGION
```

**Résultat attendu** : Message `Successfully created/updated stack - vectora-inbox-s1-runtime-dev`.

**Fonctions Lambda créées** :
- `vectora-inbox-ingest-normalize-dev`
- `vectora-inbox-engine-dev`

### Sauvegarder les outputs de s1-runtime

```powershell
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s1-runtime-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Stacks[0]" > infra/outputs/s1-runtime-dev.json
```

**Pourquoi cette étape est importante** : Les stacks CloudFormation créent toute l'infrastructure nécessaire de manière déclarative et reproductible.

---

## Phase 4 – Chargement des configurations dans CONFIG_BUCKET

Les Lambdas ont besoin des fichiers canonical et des configurations clients pour fonctionner.

### Uploader les scopes canonical

```powershell
# Uploader le dossier canonical/scopes
aws s3 sync canonical/scopes s3://vectora-inbox-config-dev/canonical/scopes `
  --profile $PROFILE `
  --region $REGION

# Uploader le catalogue de sources
aws s3 cp canonical/sources/source_catalog.yaml s3://vectora-inbox-config-dev/canonical/sources/source_catalog.yaml `
  --profile $PROFILE `
  --region $REGION

# Uploader les règles de scoring
aws s3 cp canonical/scoring/scoring_rules.yaml s3://vectora-inbox-config-dev/canonical/scoring/scoring_rules.yaml `
  --profile $PROFILE `
  --region $REGION
```

### Uploader la configuration client lai_weekly

```powershell
aws s3 cp client-config-examples/lai_weekly.yaml s3://vectora-inbox-config-dev/clients/lai_weekly.yaml `
  --profile $PROFILE `
  --region $REGION
```

### Vérifier les uploads

```powershell
# Lister le contenu du bucket config
aws s3 ls s3://vectora-inbox-config-dev/ --recursive --profile $PROFILE --region $REGION
```

**Résultat attendu** : Vous devez voir les fichiers :
- `canonical/scopes/company_scopes.yaml`
- `canonical/scopes/molecule_scopes.yaml`
- `canonical/scopes/technology_scopes.yaml`
- `canonical/scopes/indication_scopes.yaml`
- `canonical/scopes/trademark_scopes.yaml`
- `canonical/scopes/exclusion_scopes.yaml`
- `canonical/sources/source_catalog.yaml`
- `canonical/scoring/scoring_rules.yaml`
- `clients/lai_weekly.yaml`

**Pourquoi cette étape est importante** : Sans ces fichiers, les Lambdas ne peuvent pas fonctionner car elles ne sauraient pas quelles entités surveiller ni quelles sources interroger.

---

## Phase 5 – Premier test de la Lambda ingest-normalize

### Créer un fichier d'événement de test

Créez un fichier `test-event-ingest.json` avec le contenu suivant :

```json
{
  "client_id": "lai_weekly",
  "period_days": 7
}
```

### Invoquer la Lambda

```powershell
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload file://test-event-ingest.json `
  --profile $PROFILE `
  --region $REGION `
  out-ingest-lai-weekly.json
```

**Résultat attendu** : Un fichier `out-ingest-lai-weekly.json` contenant la réponse de la Lambda.

### Consulter la réponse

```powershell
Get-Content out-ingest-lai-weekly.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Réponse attendue en cas de succès** :
```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T10:30:00Z",
    "sources_processed": 8,
    "items_ingested": 45,
    "items_normalized": 42,
    "s3_output_path": "s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/01/15/items.json",
    "execution_time_seconds": 23.5
  }
}
```

### Consulter les logs CloudWatch

```powershell
# Afficher les logs des 10 dernières minutes
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev `
  --since 10m `
  --format detailed `
  --profile $PROFILE `
  --region $REGION
```

**Pourquoi cette étape est importante** : Ce test valide que la Lambda peut s'exécuter, charger les configurations, et produire des items normalisés.

---

## Phase 6 – Vérification des sorties dans DATA_BUCKET

### Lister les items normalisés

```powershell
# Lister le contenu du bucket data
aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly/ --recursive `
  --profile $PROFILE `
  --region $REGION
```

**Résultat attendu** : Vous devez voir un fichier comme :
```
normalized/lai_weekly/2025/01/15/items.json
```

### Télécharger et inspecter les items normalisés

```powershell
# Télécharger le fichier
aws s3 cp s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/01/15/items.json items-normalized.json `
  --profile $PROFILE `
  --region $REGION

# Afficher le contenu
Get-Content items-normalized.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Contenu attendu** : Un tableau JSON d'items normalisés, chacun avec :
- `source_key`
- `source_type`
- `title`
- `summary`
- `url`
- `date`
- `companies_detected`
- `molecules_detected`
- `technologies_detected`
- `indications_detected`
- `event_type`

**Pourquoi cette étape est importante** : Cette vérification confirme que le workflow d'ingestion-normalisation fonctionne de bout en bout et produit des données exploitables.

---

## Résumé des commandes essentielles

### Variables d'environnement PowerShell

```powershell
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"
```

### Déploiement complet (après packaging)

```powershell
# 1. Déployer s0-core
aws cloudformation deploy --template-file infra/s0-core.yaml --stack-name vectora-inbox-s0-core-dev --parameter-overrides Env=dev ProjectName=vectora-inbox --profile $PROFILE --region $REGION

# 2. Déployer s0-iam
aws cloudformation deploy --template-file infra/s0-iam.yaml --stack-name vectora-inbox-s0-iam-dev --parameter-overrides Env=dev ProjectName=vectora-inbox ConfigBucketName=vectora-inbox-config-dev DataBucketName=vectora-inbox-data-dev NewslettersBucketName=vectora-inbox-newsletters-dev PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key --capabilities CAPABILITY_IAM --profile $PROFILE --region $REGION

# 3. Récupérer les ARNs des rôles
$INGEST_ROLE_ARN = (aws cloudformation describe-stacks --stack-name vectora-inbox-s0-iam-dev --profile $PROFILE --region $REGION --query "Stacks[0].Outputs[?OutputKey=='IngestNormalizeRoleArn'].OutputValue" --output text)
$ENGINE_ROLE_ARN = (aws cloudformation describe-stacks --stack-name vectora-inbox-s0-iam-dev --profile $PROFILE --region $REGION --query "Stacks[0].Outputs[?OutputKey=='EngineRoleArn'].OutputValue" --output text)

# 4. Déployer s1-runtime
aws cloudformation deploy --template-file infra/s1-runtime.yaml --stack-name vectora-inbox-s1-runtime-dev --parameter-overrides Env=dev ProjectName=vectora-inbox ConfigBucketName=vectora-inbox-config-dev DataBucketName=vectora-inbox-data-dev NewslettersBucketName=vectora-inbox-newsletters-dev IngestNormalizeRoleArn=$INGEST_ROLE_ARN EngineRoleArn=$ENGINE_ROLE_ARN IngestNormalizeCodeBucket=$ARTIFACTS_BUCKET IngestNormalizeCodeKey=lambda/ingest-normalize/latest.zip EngineCodeBucket=$ARTIFACTS_BUCKET EngineCodeKey=lambda/engine/latest.zip PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key BedrockModelId=anthropic.claude-3-sonnet-20240229-v1:0 --profile $PROFILE --region $REGION

# 5. Uploader les configurations
aws s3 sync canonical/scopes s3://vectora-inbox-config-dev/canonical/scopes --profile $PROFILE --region $REGION
aws s3 cp canonical/sources/source_catalog.yaml s3://vectora-inbox-config-dev/canonical/sources/source_catalog.yaml --profile $PROFILE --region $REGION
aws s3 cp canonical/scoring/scoring_rules.yaml s3://vectora-inbox-config-dev/canonical/scoring/scoring_rules.yaml --profile $PROFILE --region $REGION
aws s3 cp client-config-examples/lai_weekly.yaml s3://vectora-inbox-config-dev/clients/lai_weekly.yaml --profile $PROFILE --region $REGION
```

---

## Dépannage

### Erreur : "Stack already exists"

Si une stack existe déjà, CloudFormation la mettra à jour automatiquement avec `aws cloudformation deploy`.

### Erreur : "Insufficient permissions"

Vérifiez que le profil `rag-lai-prod` a les permissions nécessaires :
- `cloudformation:*`
- `s3:*`
- `lambda:*`
- `iam:*`
- `logs:*`

### Erreur : "Template validation error"

Vérifiez la syntaxe YAML du template avec :
```powershell
aws cloudformation validate-template --template-body file://infra/TEMPLATE.yaml --profile $PROFILE --region $REGION
```

### Lambda timeout ou erreur d'exécution

Consultez les logs CloudWatch :
```powershell
aws logs tail /aws/lambda/FUNCTION-NAME --since 10m --format detailed --profile $PROFILE --region $REGION
```

---

## Prochaines étapes

Une fois le déploiement DEV réussi :

1. **Tester la Lambda engine** : Invoquer `vectora-inbox-engine-dev` pour générer une newsletter
2. **Valider les outputs** : Vérifier que la newsletter est bien créée dans `s3://vectora-inbox-newsletters-dev/`
3. **Itérer sur les configurations** : Ajuster les scopes, les sources, les règles de scoring selon les retours
4. **Déployer en STAGE** : Répéter le processus avec `Env=stage`
5. **Déployer en PROD** : Répéter le processus avec `Env=prod`

---

**Document créé le** : 2025-01-15  
**Dernière mise à jour** : 2025-01-15  
**Version** : 1.0
