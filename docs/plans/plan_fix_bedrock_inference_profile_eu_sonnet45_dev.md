# Plan de correction - Inference Profile EU Bedrock Sonnet 4.5 (DEV)

## Contexte

**Problème** : Les appels Bedrock échouent avec l'erreur "The provided model identifier is invalid" lors de l'utilisation de Claude Sonnet 4.5.

**Solution** : Utiliser l'inference profile cross-region EU officiel pour Claude Sonnet 4.5.

**Environnement** : DEV uniquement  
**Région** : eu-west-3 (Paris)  
**Stack concernée** : vectora-inbox-s1-runtime-dev  
**Lambda testée** : vectora-inbox-ingest-normalize-dev

---

## Informations officielles Bedrock

**Label** : EU Anthropic Claude Sonnet 4.5  
**Model ID / Inference Profile ID** : `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`  
**ARN** : `arn:aws:bedrock:eu-west-3:786469175371:inference-profile/eu.anthropic.claude-sonnet-4-5-20250929-v1:0`  
**Région d'ancrage** : eu-west-3 (Europe/Paris)  
**Régions de routage** : eu-north-1, eu-west-3, eu-south-1, eu-south-2, eu-west-1, eu-central-1

---

## Étape 1 : Fichiers à modifier

### A. Infrastructure

**Fichier** : `infra/s1-runtime.yaml`

**Modification** :
- Paramètre `BedrockModelId` : changer la valeur par défaut de `anthropic.claude-3-sonnet-20240229-v1:0` vers `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
- Variable d'environnement `BEDROCK_MODEL_ID` de la Lambda ingest-normalize : utilise automatiquement le paramètre

### B. Documentation

**Fichiers à mettre à jour** :

1. `infra/README.md`
   - Section sur BedrockModelId : documenter le nouvel inference profile
   - Ajouter les informations sur l'ARN et les régions de routage

2. `.q-context/blueprint-draft-vectora-inbox.yaml`
   - Mettre à jour la référence au modèle Bedrock dans la section normalisation

3. `.q-context/vectora-inbox-q-rules.md`
   - Mettre à jour les références au modelId Sonnet 4.5

4. Tout autre fichier de diagnostic mentionnant l'ancien modelId

---

## Étape 2 : Mise à jour de l'infrastructure

### Valeur exacte à utiliser

```
BedrockModelId=eu.anthropic.claude-sonnet-4-5-20250929-v1:0
```

### Commandes de déploiement

#### Validation du template

```powershell
aws cloudformation validate-template `
  --template-body file://infra/s1-runtime.yaml `
  --profile rag-lai-prod `
  --region eu-west-3
```

#### Récupération des ARNs des rôles IAM

```powershell
$INGEST_ROLE_ARN = (aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-iam-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --query "Stacks[0].Outputs[?OutputKey=='IngestNormalizeRoleArn'].OutputValue" `
  --output text)

$ENGINE_ROLE_ARN = (aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-iam-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --query "Stacks[0].Outputs[?OutputKey=='EngineRoleArn'].OutputValue" `
  --output text)
```

#### Déploiement de la stack

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
    BedrockModelId=eu.anthropic.claude-sonnet-4-5-20250929-v1:0 `
  --profile rag-lai-prod `
  --region eu-west-3
```

---

## Étape 3 : Test de la Lambda

### Payload d'invocation

**Fichier** : `test-payload.json`

```json
{
  "client_id": "lai_weekly",
  "period_days": 7
}
```

### Commande d'invocation

```powershell
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload file://test-payload.json `
  --profile rag-lai-prod `
  --region eu-west-3 `
  response.json

# Afficher la réponse
Get-Content response.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Vérifications attendues

#### 1. Réponse Lambda

- `statusCode` = 200
- `items_ingested` > 0
- `items_normalized` > 0
- Pas d'erreur dans le champ `error`

#### 2. Logs CloudWatch

**Groupe de logs** : `/aws/lambda/vectora-inbox-ingest-normalize-dev`

**Commande pour consulter les logs** :

```powershell
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev `
  --follow `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Vérifications** :

- ✅ PLUS d'erreur "The provided model identifier is invalid"
- ✅ Présence de logs indiquant des appels Bedrock réussis
- ✅ Logs montrant la normalisation : "Normalizing item X/Y"
- ✅ Présence de données normalisées : summary, event_type, technologies_detected, companies_detected

#### 3. Fichiers S3 normalisés

**Chemin attendu** :

```
s3://vectora-inbox-data-dev/normalized/lai_weekly/YYYY-MM-DD_YYYY-MM-DD/items.json
```

**Commande pour lister** :

```powershell
aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly/ `
  --recursive `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Commande pour télécharger et inspecter** :

```powershell
# Identifier le dernier fichier
$LATEST_FILE = (aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly/ `
  --recursive `
  --profile rag-lai-prod `
  --region eu-west-3 | Sort-Object | Select-Object -Last 1)

# Télécharger
aws s3 cp s3://vectora-inbox-data-dev/normalized/lai_weekly/[PATH]/items.json `
  normalized-items.json `
  --profile rag-lai-prod `
  --region eu-west-3

# Inspecter
Get-Content normalized-items.json | ConvertFrom-Json | Select-Object -First 2 | ConvertTo-Json -Depth 10
```

**Champs à vérifier dans items.json** :

- `summary` : résumé généré par Bedrock (non vide)
- `event_type` : type d'événement détecté
- `technologies_detected` : liste de technologies
- `companies_detected` : liste d'entreprises
- `therapeutic_areas_detected` : aires thérapeutiques
- `relevance_score` : score de pertinence

---

## Étape 4 : Documentation du résultat

### A. Créer le diagnostic

**Fichier** : `docs/diagnostics/bedrock_sonnet45_eu_profile_fix_dev.md`

**Contenu** :

- Date et heure du test
- Inference profile utilisé (ID + ARN)
- Paramètres du test (client_id, period_days)
- Résultats :
  - Nombre d'items ingérés
  - Nombre d'items normalisés
  - Durée d'exécution
  - Mémoire utilisée
- Extraits anonymisés d'items normalisés (2-3 exemples)
- Logs pertinents (sans PII)
- Conclusion : ✅ Succès ou ❌ Échec avec détails

### B. Mettre à jour le CHANGELOG

**Fichier** : `CHANGELOG.md`

**Section** : `[Unreleased]`

**Entrée à ajouter** :

```markdown
### Changed
- Migration vers l'inference profile EU pour Claude Sonnet 4.5 (`eu.anthropic.claude-sonnet-4-5-20250929-v1:0`)
- Résolution de l'erreur "The provided model identifier is invalid" dans l'environnement DEV
- Amélioration de la normalisation Bedrock avec routage cross-region EU (eu-north-1, eu-west-3, eu-south-1, eu-south-2, eu-west-1, eu-central-1)

### Fixed
- Correction du modelId Bedrock pour utiliser l'inference profile officiel EU Sonnet 4.5
- Normalisation Bedrock fonctionnelle pour le MVP LAI en environnement DEV
```

---

## Résumé des actions

1. ✅ Modifier `infra/s1-runtime.yaml` : BedrockModelId = `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
2. ✅ Mettre à jour la documentation (README, blueprint, q-rules)
3. ✅ Valider le template CloudFormation
4. ✅ Redéployer la stack s1-runtime-dev
5. ✅ Tester la Lambda ingest-normalize avec lai_weekly
6. ✅ Vérifier les logs CloudWatch (plus d'erreur)
7. ✅ Inspecter les fichiers S3 normalisés
8. ✅ Documenter le résultat dans diagnostics/
9. ✅ Mettre à jour CHANGELOG.md

---

## Critères de succès

- ✅ Stack s1-runtime-dev déployée sans erreur
- ✅ Lambda invoquée avec statusCode 200
- ✅ items_normalized > 0
- ✅ Logs CloudWatch sans "invalid model identifier"
- ✅ Fichiers S3 normalized/ contiennent des données enrichies (summary, event_type, etc.)
- ✅ Documentation complète et à jour
