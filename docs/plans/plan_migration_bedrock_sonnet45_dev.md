# Plan de migration Bedrock vers Claude Sonnet 4.5 - Environnement DEV

## Vue d'ensemble

**Objectif** : Migrer le projet Vectora Inbox du modèle Bedrock actuel vers **Claude Sonnet 4.5 (Amazon Bedrock Edition)** comme modèle par défaut, tout en conservant une architecture pilotée par configuration via `BEDROCK_MODEL_ID`.

**Date de migration** : 2024-01-XX  
**Environnement cible** : DEV uniquement  
**Compte AWS** : 786469175371  
**Région** : eu-west-3 (Paris)  
**Profil CLI** : rag-lai-prod

---

## Contexte technique

### Modèle actuel
- **Avant** : `anthropic.claude-3-sonnet-20240229-v1:0` (Claude 3 Sonnet)

### Modèle cible
- **Après** : `anthropic.claude-sonnet-4-5-20250929-v1:0` (Claude Sonnet 4.5 - Amazon Bedrock Edition)
- **Région** : eu-west-3 (Paris)
- **Type** : Modèle serverless text
- **Note** : Model ID vérifié via AWS CLI (`aws bedrock list-foundation-models`)

### Stacks CloudFormation concernées
- `vectora-inbox-s0-core-dev` : Aucune modification
- `vectora-inbox-s0-iam-dev` : Aucune modification (permissions Bedrock déjà en place)
- `vectora-inbox-s1-runtime-dev` : **Mise à jour requise** (variable BEDROCK_MODEL_ID)

### Fonctions Lambda concernées
- `vectora-inbox-ingest-normalize-dev` : Utilise Bedrock pour normaliser les données
- `vectora-inbox-engine-dev` : Utilise Bedrock pour générer les newsletters

---

## Phase 1 – Analyse & identification du Model ID

### 1.1 Fichiers à analyser
- [x] `.q-context/blueprint-draft-vectora-inbox.yaml`
- [x] `.q-context/vectora-inbox-q-rules.md`
- [x] `.q-context/vectora-inbox-overview.md`
- [x] `infra/s1-runtime.yaml`
- [x] `infra/README.md`
- [x] `src/vectora_core/normalization/bedrock_client.py`
- [x] `src/vectora_core/newsletter/bedrock_client.py`

### 1.2 Model ID officiel AWS Bedrock
**Claude Sonnet 4.5 (Amazon Bedrock Edition)** :
- **Model ID** : `anthropic.claude-sonnet-4-5-20250929-v1:0`
- **Disponibilité** : eu-west-3 (Paris) ✓ (vérifié le 2025-12-08)
- **Type** : Serverless, optimisé pour la production
- **Documentation** : https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html
- **Autres modèles Claude 4.x disponibles** : Opus 4.5, Haiku 4.5, Sonnet 4, Sonnet 3.7, Sonnet 3.5

---

## Phase 2 – Mise à jour du repository

### 2.1 Infrastructure (infra/s1-runtime.yaml)

**Fichier** : `infra/s1-runtime.yaml`

**Modification** :
- Mettre à jour le paramètre `BedrockModelId` par défaut
- Vérifier que les deux Lambdas utilisent bien cette variable d'environnement

**Changement** :
```yaml
# AVANT
BedrockModelId:
  Type: String
  Default: anthropic.claude-3-sonnet-20240229-v1:0

# APRÈS
BedrockModelId:
  Type: String
  Default: anthropic.claude-sonnet-4-5-20250929-v1:0
```

### 2.2 Documentation infrastructure (infra/README.md)

**Fichier** : `infra/README.md`

**Modifications** :
- Mettre à jour la section décrivant le modèle Bedrock utilisé
- Clarifier que le modèle est configurable via `BEDROCK_MODEL_ID`
- Documenter le changement de Claude 3 Sonnet vers Claude Sonnet 4.5

### 2.3 Q-context & documentation projet

**Fichiers à mettre à jour** :
- `.q-context/blueprint-draft-vectora-inbox.yaml`
- `.q-context/vectora-inbox-q-rules.md`
- `.q-context/vectora-inbox-overview.md`
- `docs/diagnostics/vectora-inbox-deep-diagnostic.md` (si applicable)

**Règles de modification** :
- Remplacer toutes les mentions de l'ancien modèle par "Claude Sonnet 4.5 (Amazon Bedrock Edition)"
- Insister sur le fait que le modèle est piloté par `BEDROCK_MODEL_ID`
- Ne pas modifier l'architecture générale

### 2.4 Code Python (sanity check)

**Fichiers à vérifier** :
- `src/vectora_core/normalization/bedrock_client.py`
- `src/vectora_core/newsletter/bedrock_client.py`
- `src/lambdas/ingest_normalize/handler.py`
- `src/lambdas/engine/handler.py`

**Vérifications** :
- ✓ Le model ID est récupéré depuis `os.environ["BEDROCK_MODEL_ID"]`
- ✓ Aucun model ID hardcodé dans le code
- ✓ Pas de logique conditionnelle basée sur le nom du modèle

---

## Phase 3 – Validation & déploiement CloudFormation

### 3.1 Validation du template

```powershell
aws cloudformation validate-template `
  --template-body file://infra/s1-runtime.yaml `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat attendu** : Validation réussie sans erreur.

### 3.2 Récupération des paramètres existants

```powershell
# Récupérer les paramètres actuels de la stack
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s1-runtime-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --query "Stacks[0].Parameters"
```

### 3.3 Mise à jour de la stack DEV

```powershell
# Variables
$PROFILE = "rag-lai-prod"
$REGION = "eu-west-3"

# Récupérer les ARNs des rôles IAM
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

# Déployer la stack avec le nouveau modèle
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
    BedrockModelId=anthropic.claude-sonnet-4-5-20250929-v1:0 `
  --capabilities CAPABILITY_NAMED_IAM `
  --profile $PROFILE `
  --region $REGION
```

**Résultat attendu** : `Successfully created/updated stack - vectora-inbox-s1-runtime-dev`

---

## Phase 4 – Test end-to-end avec Lambda ingest-normalize

### 4.1 Invocation de la Lambda

```powershell
# Test avec le client lai_weekly
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload "{\"client_id\":\"lai_weekly\",\"period_days\":7}" `
  --cli-binary-format raw-in-base64-out `
  out_ingest_lai_weekly_sonnet45.json `
  --profile rag-lai-prod `
  --region eu-west-3
```

### 4.2 Vérification des logs CloudWatch

```powershell
# Récupérer les derniers logs
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev `
  --follow `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Points à vérifier** :
- ✓ Pas d'erreur `AccessDeniedException` Bedrock
- ✓ Model ID affiché = `anthropic.claude-sonnet-4-5-v2:0`
- ✓ Items normalisés avec succès
- ✓ Temps de réponse acceptable

### 4.3 Analyse du résultat

```powershell
# Afficher le résultat de l'invocation
Get-Content out_ingest_lai_weekly_sonnet45.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## Phase 5 – Documentation & traçabilité

### 5.1 Fichier de diagnostic

**Créer** : `docs/diagnostics/bedrock_sonnet45_activation_dev.md`

**Contenu** :
- Date/heure du test
- Model ID utilisé
- Résumé des résultats (items ingested/normalized)
- Logs pertinents
- Problèmes éventuels et solutions

### 5.2 Mise à jour du CHANGELOG

**Fichier** : `CHANGELOG.md`

**Section** : `[Unreleased]`

**Entrée** :
```markdown
### Changed
- Migration du modèle Bedrock par défaut vers Claude Sonnet 4.5 (Amazon Bedrock Edition) - `anthropic.claude-sonnet-4-5-v2:0`
- Mise à jour de l'infrastructure DEV (stack `vectora-inbox-s1-runtime-dev`)
- Alignement de la documentation (infra, Q-context, diagnostics)
- Aucun changement du contrat métier : le modèle reste configurable via `BEDROCK_MODEL_ID`
```

---

## Checklist de validation finale

- [ ] Template CloudFormation validé
- [ ] Stack DEV mise à jour avec succès
- [ ] Lambda ingest-normalize testée avec succès
- [ ] Logs CloudWatch vérifiés (pas d'erreur Bedrock)
- [ ] Model ID confirmé dans les logs
- [ ] Documentation mise à jour (infra, Q-context, diagnostics)
- [ ] CHANGELOG mis à jour
- [ ] Fichier de diagnostic créé
- [ ] Repository dans un état propre

---

## Rollback (si nécessaire)

En cas de problème, revenir au modèle précédent :

```powershell
aws cloudformation deploy `
  --template-file infra/s1-runtime.yaml `
  --stack-name vectora-inbox-s1-runtime-dev `
  --parameter-overrides BedrockModelId=anthropic.claude-3-sonnet-20240229-v1:0 `
  --capabilities CAPABILITY_NAMED_IAM `
  --profile rag-lai-prod `
  --region eu-west-3
```

---

## Notes importantes

1. **Pas de hard-coding** : Le code Python ne doit jamais contenir de model ID en dur
2. **Configuration centralisée** : Tout passe par `BEDROCK_MODEL_ID` dans CloudFormation
3. **Compatibilité** : Claude Sonnet 4.5 est compatible avec l'API Claude 3 (pas de changement de code requis)
4. **Coûts** : Surveiller les coûts Bedrock après migration (tarification différente possible)
5. **Performance** : Claude Sonnet 4.5 peut avoir des temps de réponse différents

---

## Prochaines étapes (après validation DEV)

1. Tester la Lambda `engine` avec le nouveau modèle
2. Valider la qualité des newsletters générées
3. Planifier la migration en PROD (si applicable)
4. Documenter les différences de comportement observées
