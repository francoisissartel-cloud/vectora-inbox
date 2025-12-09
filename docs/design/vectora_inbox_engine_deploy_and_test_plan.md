# Plan de Déploiement, Tests et Préparation Stage/Prod – Vectora Inbox Engine

**Date** : 2025-01-15  
**Auteur** : Amazon Q Developer  
**Statut** : ✅ PLAN CRÉÉ ET PRÉPARÉ – Prêt pour exécution manuelle  
**Version** : 1.0

---

## Contexte

La Lambda `vectora-inbox-engine` a été implémentée avec succès (Phases 2, 3, 4 : matching, scoring, newsletter). Ce document définit le plan pour :

1. **Déployer** la Lambda engine en DEV
2. **Tester** le workflow complet end-to-end (ingest-normalize → engine)
3. **Diagnostiquer** et documenter le premier run
4. **Préparer** la montée en puissance vers stage/prod

---

## Phase 1 – Wiring Infra & Déploiement DEV

### 1.1 État actuel de l'infrastructure

✅ **Déjà en place** :
- `infra/s0-core.yaml` : Buckets S3 (config, data, newsletters, lambda-code)
- `infra/s0-iam.yaml` : Rôles IAM pour ingest-normalize et engine
- `infra/s1-runtime.yaml` : Déclaration des deux Lambdas (ingest-normalize + engine)

✅ **Lambda engine déjà déclarée** dans `s1-runtime.yaml` :
- Nom : `vectora-inbox-engine-dev`
- Handler : `handler.lambda_handler`
- Variables d'environnement : CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_MODEL_ID
- Permissions IAM : Lecture S3 (config + data), Écriture S3 (newsletters), Bedrock InvokeModel

### 1.2 Vérifications nécessaires

**Permissions IAM** :
- ✅ Lecture S3 config bucket (pour charger client config, canonical scopes, scoring rules)
- ✅ Lecture S3 data bucket (pour charger les items normalisés)
- ✅ Écriture S3 newsletters bucket (pour écrire la newsletter Markdown)
- ✅ Bedrock InvokeModel (pour génération éditoriale)

**Variables d'environnement** :
- ✅ CONFIG_BUCKET
- ✅ DATA_BUCKET
- ✅ NEWSLETTERS_BUCKET
- ✅ BEDROCK_MODEL_ID (inference profile Sonnet 4.5)

**Concurrence** :
- ⚠️ Pas de limite de concurrence définie pour la Lambda engine dans `s1-runtime.yaml`
- **Recommandation DEV** : Ajouter `ReservedConcurrentExecutions: 1` pour éviter le throttling Bedrock (aligné sur ingest-normalize)

### 1.3 Actions à réaliser

#### 1.3.1 Ajuster la concurrence de la Lambda engine (optionnel mais recommandé)

**Fichier** : `infra/s1-runtime.yaml`

**Modification** : Ajouter une limite de concurrence pour la Lambda engine en DEV (similaire à ingest-normalize)

```yaml
EngineFunction:
  Type: AWS::Lambda::Function
  Properties:
    # ... (propriétés existantes)
    ReservedConcurrentExecutions: !If
      - IsDevEnvironment
      - 1
      - !Ref AWS::NoValue
```

**Justification** : En DEV, limiter la concurrence à 1 réduit le risque de throttling Bedrock lors des tests.

#### 1.3.2 Packager le code de la Lambda engine

**Script** : `scripts/package-engine.ps1` (à créer)

```powershell
# Package la Lambda engine et l'uploade dans S3
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"

# Créer le package ZIP
cd src
Compress-Archive -Path * -DestinationPath ../engine.zip -Force
cd ..

# Uploader dans S3
aws s3 cp engine.zip s3://$ARTIFACTS_BUCKET/lambda/engine/latest.zip `
  --profile $PROFILE `
  --region $REGION

Write-Host "Package engine uploadé avec succès dans s3://$ARTIFACTS_BUCKET/lambda/engine/latest.zip"
```

#### 1.3.3 Déployer la stack s1-runtime (mise à jour)

**Commande** :

```powershell
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"
$ARTIFACTS_BUCKET = "vectora-inbox-lambda-code-dev"

# Récupérer les ARNs des rôles IAM
$INGEST_ROLE_ARN = (aws cloudformation describe-stacks --stack-name vectora-inbox-s0-iam-dev --profile $PROFILE --region $REGION --query "Stacks[0].Outputs[?OutputKey=='IngestNormalizeRoleArn'].OutputValue" --output text)
$ENGINE_ROLE_ARN = (aws cloudformation describe-stacks --stack-name vectora-inbox-s0-iam-dev --profile $PROFILE --region $REGION --query "Stacks[0].Outputs[?OutputKey=='EngineRoleArn'].OutputValue" --output text)

# Déployer la stack runtime
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
```

**Résultat attendu** : Message `Successfully created/updated stack - vectora-inbox-s1-runtime-dev`

#### 1.3.4 Vérifier le déploiement

```powershell
# Vérifier que la Lambda engine existe
aws lambda get-function `
  --function-name vectora-inbox-engine-dev `
  --profile $PROFILE `
  --region $REGION

# Vérifier les variables d'environnement
aws lambda get-function-configuration `
  --function-name vectora-inbox-engine-dev `
  --profile $PROFILE `
  --region $REGION `
  --query "Environment.Variables"
```

**Validation** : La Lambda doit avoir les variables CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_MODEL_ID correctement configurées.

---

## Phase 2 – Scénario de test end-to-end en DEV

### 2.1 Objectif

Valider le workflow complet :
1. **ingest-normalize** : Génère des items normalisés dans S3
2. **engine** : Génère une newsletter à partir de ces items

### 2.2 Scénario de test

**Client** : `lai_weekly`  
**Période** : 7 jours (period_days: 7)  
**Date cible** : Date du jour (automatique)

### 2.3 Étape 1 : Exécuter ingest-normalize

**Fichier d'événement** : `test-event-ingest.json`

```json
{
  "client_id": "lai_weekly",
  "period_days": 7
}
```

**Commande** :

```powershell
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload file://test-event-ingest.json `
  --profile $PROFILE `
  --region $REGION `
  out-ingest-lai-weekly.json

# Consulter la réponse
Get-Content out-ingest-lai-weekly.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Validation** :
- ✅ `statusCode: 200`
- ✅ `items_normalized > 0`
- ✅ `s3_output_path` contient un chemin valide

**Vérifier les items normalisés dans S3** :

```powershell
# Lister les fichiers générés
aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly/ --recursive `
  --profile $PROFILE `
  --region $REGION

# Télécharger et inspecter
aws s3 cp s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/01/15/items.json items-normalized.json `
  --profile $PROFILE `
  --region $REGION

Get-Content items-normalized.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### 2.4 Étape 2 : Exécuter engine

**Fichier d'événement** : `test-event-engine.json`

```json
{
  "client_id": "lai_weekly",
  "period_days": 7
}
```

**Commande** :

```powershell
aws lambda invoke `
  --function-name vectora-inbox-engine-dev `
  --payload file://test-event-engine.json `
  --profile $PROFILE `
  --region $REGION `
  out-engine-lai-weekly.json

# Consulter la réponse
Get-Content out-engine-lai-weekly.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Validation** :
- ✅ `statusCode: 200`
- ✅ `items_analyzed > 0`
- ✅ `items_matched > 0`
- ✅ `items_selected > 0`
- ✅ `sections_generated > 0`
- ✅ `s3_output_path` contient un chemin valide

### 2.5 Étape 3 : Vérifier la newsletter générée

```powershell
# Lister les newsletters générées
aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly/ --recursive `
  --profile $PROFILE `
  --region $REGION

# Télécharger la newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/2025/01/15/newsletter.md newsletter.md `
  --profile $PROFILE `
  --region $REGION

# Afficher le contenu
Get-Content newsletter.md
```

**Validation** :
- ✅ Fichier Markdown valide
- ✅ Titre de la newsletter présent
- ✅ Introduction présente
- ✅ TL;DR présent (si configuré)
- ✅ Sections avec items présentes
- ✅ URLs des articles présentes
- ✅ Footer présent

### 2.6 Étape 4 : Consulter les logs CloudWatch

```powershell
# Logs de la Lambda engine
aws logs tail /aws/lambda/vectora-inbox-engine-dev `
  --since 10m `
  --format detailed `
  --profile $PROFILE `
  --region $REGION
```

**Validation** :
- ✅ Logs structurés présents
- ✅ Pas d'erreurs critiques
- ✅ Statistiques d'exécution (nb items, nb appels Bedrock, temps)

---

## Phase 3 – Diagnostics & Qualité

### 3.1 Fichier de diagnostic à créer

**Fichier** : `docs/diagnostics/vectora_inbox_engine_first_run.md`

**Contenu** :
- Contexte du test (client_id, period_days, date)
- Volume d'items (analysés, matchés, sélectionnés)
- Structure de la newsletter (nb sections, nb items par section)
- Temps d'exécution total
- Nombre d'appels Bedrock
- Taux de throttling (si applicable)
- Qualité éditoriale (évaluation subjective)
- Problèmes rencontrés et solutions
- Recommandations d'ajustement

### 3.2 Mise à jour du CHANGELOG

**Fichier** : `CHANGELOG.md`

**Entrée à ajouter** :

```markdown
## [0.2.0] - 2025-01-15

### Added
- Lambda engine déployée en DEV
- Workflow complet ingest-normalize → engine testé avec succès
- Premier run end-to-end pour client lai_weekly (7 jours)

### Status
- ✅ GREEN : Newsletter générée avec succès
- Items analysés : [X]
- Items matchés : [Y]
- Items sélectionnés : [Z]
- Sections générées : [N]
- Temps d'exécution : [T] secondes
```

### 3.3 Stratégie d'itération

**Ajustement des prompts Bedrock** :
- Si le ton n'est pas adapté → ajuster les instructions dans `_build_editorial_prompt()`
- Si les reformulations sont trop longues/courtes → ajuster `max_tokens` ou les contraintes du prompt
- Si Bedrock hallucine → renforcer les contraintes "Do NOT hallucinate"

**Ajustement du scoring** :
- Si des items peu pertinents sont sélectionnés → augmenter les poids des facteurs importants
- Si des items importants sont exclus → réduire le score minimum ou ajuster les poids

**Gestion du throttling** :
- Si throttling fréquent → réduire la concurrence Lambda (déjà à 1 en DEV)
- Si throttling persiste → ajouter des délais entre les appels Bedrock
- Si throttling critique → demander une augmentation des quotas Bedrock

---

## Phase 4 – Préparation Stage / Prod

### 4.1 Duplication de l'infrastructure

**Principe** : Répliquer les stacks CloudFormation pour stage et prod

**Naming conventions** :
- **Stage** : `vectora-inbox-*-stage` (buckets, Lambdas, rôles)
- **Prod** : `vectora-inbox-*-prod` (buckets, Lambdas, rôles)

**Commandes de déploiement** :

```powershell
# Stage
aws cloudformation deploy --template-file infra/s0-core.yaml --stack-name vectora-inbox-s0-core-stage --parameter-overrides Env=stage ProjectName=vectora-inbox --profile $PROFILE --region $REGION

aws cloudformation deploy --template-file infra/s0-iam.yaml --stack-name vectora-inbox-s0-iam-stage --parameter-overrides Env=stage ProjectName=vectora-inbox ConfigBucketName=vectora-inbox-config-stage DataBucketName=vectora-inbox-data-stage NewslettersBucketName=vectora-inbox-newsletters-stage PubmedApiKeyParamPath=/rag-lai/stage/pubmed/api-key --capabilities CAPABILITY_IAM --profile $PROFILE --region $REGION

# Prod (similaire)
```

### 4.2 Quotas Bedrock à viser

**DEV** :
- Concurrence Lambda : 1
- Appels Bedrock : ~10-20 par run (1 client, 1 scope)
- Quota nécessaire : Minimal (quotas par défaut suffisants)

**Stage** :
- Concurrence Lambda : 2-3
- Appels Bedrock : ~50-100 par run (2-3 clients, tests de charge)
- Quota nécessaire : Vérifier les limites du profil d'inférence EU cross-region

**Prod** :
- Concurrence Lambda : 5-10
- Appels Bedrock : ~200-500 par run (10+ clients, multi-scopes)
- Quota nécessaire : Demander une augmentation si nécessaire (via AWS Support)

**Profil d'inférence utilisé** : `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
- Régions couvertes : eu-north-1, eu-west-3, eu-south-1, eu-south-2, eu-west-1, eu-central-1
- Avantage : Répartition automatique de la charge entre régions

### 4.3 Ajustement de la concurrence Lambda

**Recommandations** :

| Environnement | Concurrence Lambda | Justification |
|---------------|-------------------|---------------|
| DEV | 1 | Tests séquentiels, éviter throttling |
| Stage | 2-3 | Tests de charge modérés |
| Prod | 5-10 | Production multi-clients |

**Modification dans `s1-runtime.yaml`** :

```yaml
ReservedConcurrentExecutions: !If
  - IsDevEnvironment
  - 1
  - !If
    - IsStageEnvironment
    - 3
    - 10
```

### 4.4 Monitoring et alertes

**Métriques CloudWatch à surveiller** :

**Lambda engine** :
- `Invocations` : Nombre d'exécutions
- `Errors` : Nombre d'erreurs
- `Duration` : Temps d'exécution
- `Throttles` : Nombre de throttles Lambda
- `ConcurrentExecutions` : Concurrence actuelle

**Bedrock** :
- `ModelInvocationLatency` : Latence des appels Bedrock
- `ModelInvocationClientErrors` : Erreurs client (4xx)
- `ModelInvocationServerErrors` : Erreurs serveur (5xx)
- `ModelInvocationThrottles` : Throttles Bedrock

**Alertes à créer** :

1. **Erreur Lambda > 5% des invocations** → SNS notification
2. **Throttling Bedrock > 10% des appels** → SNS notification
3. **Durée d'exécution > 4 minutes** → SNS notification (proche du timeout)
4. **Aucune newsletter générée pendant 24h** → SNS notification (pour prod)

**Dashboard CloudWatch** :

Créer un dashboard avec :
- Graphique des invocations Lambda (ingest-normalize + engine)
- Graphique des erreurs et throttles
- Graphique des durées d'exécution
- Graphique des appels Bedrock (latence, erreurs)

### 4.5 Scheduling (pour prod)

**Principe** : Déclencher automatiquement les Lambdas selon un calendrier

**EventBridge Rule** (à créer) :

```yaml
# Exemple : Déclencher lai_weekly tous les lundis à 8h UTC
WeeklyScheduleRule:
  Type: AWS::Events::Rule
  Properties:
    ScheduleExpression: "cron(0 8 ? * MON *)"
    State: ENABLED
    Targets:
      - Arn: !GetAtt IngestNormalizeFunction.Arn
        Id: "IngestNormalizeLaiWeekly"
        Input: |
          {
            "client_id": "lai_weekly",
            "period_days": 7
          }
```

**Workflow automatisé** :
1. EventBridge déclenche `ingest-normalize` (lundi 8h)
2. `ingest-normalize` génère les items normalisés
3. EventBridge déclenche `engine` (lundi 8h30)
4. `engine` génère la newsletter
5. (Optionnel) Lambda de distribution envoie la newsletter par email

---

## Résumé des livrables

### Phase 1 – Déploiement DEV
- ✅ Infra déjà en place (s0-core, s0-iam, s1-runtime)
- ✅ Ajustement de la concurrence Lambda engine (ReservedConcurrentExecutions: 1 en DEV)
- ✅ Ajout des permissions CONFIG_BUCKET pour le rôle IAM Engine
- ✅ Création du script `scripts/package-engine.ps1`
- ✅ Création du script `scripts/deploy-runtime-dev.ps1`
- ✅ Création du script `scripts/verify-engine-deployment.ps1`
- ⏳ Package et upload du code engine (à exécuter manuellement)
- ⏳ Déploiement de la stack s1-runtime (à exécuter manuellement)
- ⏳ Vérification du déploiement (à exécuter manuellement)

### Phase 2 – Tests end-to-end
- ✅ Création du script `scripts/test-engine-lai-weekly.ps1`
- ⏳ Exécution de ingest-normalize (à exécuter manuellement)
- ⏳ Vérification des items normalisés (à exécuter manuellement)
- ⏳ Exécution de engine (à exécuter manuellement)
- ⏳ Vérification de la newsletter générée (à exécuter manuellement)
- ⏳ Consultation des logs CloudWatch (à exécuter manuellement)

### Phase 3 – Diagnostics
- ✅ Création du template `docs/diagnostics/vectora_inbox_engine_first_run.md`
- ✅ Mise à jour de `CHANGELOG.md` (entrée pour le plan de déploiement)
- ⏳ Complétion du diagnostic avec les résultats du test (à exécuter après Phase 2)
- ⏳ Évaluation qualitative de la newsletter (à exécuter après Phase 2)
- ⏳ Recommandations d'ajustement (à exécuter après Phase 2)

### Phase 4 – Préparation Stage/Prod
- ✅ Design de la duplication d'infra (documenté)
- ✅ Stratégie de quotas Bedrock (documentée)
- ✅ Stratégie de monitoring (documentée)
- ✅ Stratégie de scheduling (documentée)

---

## Prochaines étapes (Exécution Manuelle)

### Commandes Rapides

**Déploiement complet** :
```powershell
# 1. Redéployer IAM
aws cloudformation deploy --template-file infra/s0-iam.yaml --stack-name vectora-inbox-s0-iam-dev --parameter-overrides Env=dev ProjectName=vectora-inbox ConfigBucketName=vectora-inbox-config-dev DataBucketName=vectora-inbox-data-dev NewslettersBucketName=vectora-inbox-newsletters-dev PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key --capabilities CAPABILITY_IAM --profile rag-lai-prod --region eu-west-3

# 2. Packager et déployer
.\scripts\package-engine.ps1
.\scripts\deploy-runtime-dev.ps1

# 3. Vérifier
.\scripts\verify-engine-deployment.ps1
```

**Test end-to-end** :
```powershell
.\scripts\test-engine-lai-weekly.ps1
```

**Documentation** :
1. Compléter `docs/diagnostics/vectora_inbox_engine_first_run.md`
2. Mettre à jour `CHANGELOG.md` avec le statut final

### Ressources

- **Guide d'exécution détaillé** : `docs/guides/guide_execution_deploiement_engine.md`
- **Statut du projet** : `docs/STATUS.md`
- **Résumé d'exécution** : `docs/EXECUTION_SUMMARY.md`
- **Documentation des scripts** : `scripts/README.md`

---

**Fin du plan de déploiement et tests.**

Ce plan a été structuré et préparé avec succès. Tous les scripts, documents et modifications d'infrastructure sont prêts pour l'exécution manuelle.
