# Notes de Déploiement - Trademark Runtime v2

## Script de Déploiement

### Utilisation
```bash
# Déploiement complet (configs + lambdas)
powershell -ExecutionPolicy Bypass -File "scripts\deploy-trademark-runtime-v2.ps1"

# Déploiement configs seulement
powershell -ExecutionPolicy Bypass -File "scripts\deploy-trademark-runtime-v2.ps1" -SkipLambdas

# Déploiement lambdas seulement  
powershell -ExecutionPolicy Bypass -File "scripts\deploy-trademark-runtime-v2.ps1" -SkipConfigs

# Avec paramètres personnalisés
powershell -ExecutionPolicy Bypass -File "scripts\deploy-trademark-runtime-v2.ps1" -Environment prod -Profile autre-profil -Region us-east-1
```

### Paramètres par Défaut
- **Profile :** `rag-lai-prod`
- **Region :** `eu-west-3`
- **Environment :** `dev`

### Buckets Utilisés
- **Config :** `vectora-inbox-config-{Environment}`
- **Data :** `vectora-inbox-data-{Environment}`

## Packaging des Lambdas

### Script Simplifié
Le script `package-lambdas-v2.ps1` crée les packages ZIP depuis `src/` :
- `ingest-normalize-v2.zip`
- `engine-v2.zip`

### Contenu des Packages
- Code source `src/vectora_core/` avec modifications v2
- Dépendances `lambda-deps/` (boto3, yaml, etc.)
- Handlers Lambda

## Commandes AWS Utilisées

### Synchronisation S3
```bash
aws s3 sync canonical s3://vectora-inbox-config-dev/canonical --profile rag-lai-prod --region eu-west-3 --delete
aws s3 cp client-config-examples/lai_weekly_v2.yaml s3://vectora-inbox-config-dev/clients/lai_weekly_v2.yaml --profile rag-lai-prod --region eu-west-3
```

### Déploiement Lambdas
```bash
aws lambda update-function-code --function-name vectora-inbox-ingest-normalize-dev --zip-file fileb://ingest-normalize-v2.zip --profile rag-lai-prod --region eu-west-3
aws lambda update-function-code --function-name vectora-inbox-engine-dev --zip-file fileb://engine-v2.zip --profile rag-lai-prod --region eu-west-3
```

## Validation

### Vérifications Automatiques
- Existence des buckets S3
- Présence des fichiers clés après sync
- Détection config v2 dans lai_weekly_v2.yaml
- Statut des fonctions Lambda

### Fichiers Clés Vérifiés
- `canonical/scopes/trademark_scopes.yaml`
- `canonical/scopes/technology_scopes.yaml`
- `canonical/scopes/company_scopes.yaml`
- `canonical/matching/domain_matching_rules.yaml`
- `canonical/scoring/scoring_rules.yaml`
- `clients/lai_weekly_v2.yaml`

## Troubleshooting

### Erreurs Communes
1. **Profile AWS introuvable**
   - Vérifier : `aws configure list-profiles`
   - Solution : `aws sso login --profile rag-lai-prod`

2. **Bucket S3 inaccessible**
   - Vérifier permissions IAM
   - Vérifier région (eu-west-3)

3. **Lambda update failed**
   - Vérifier taille du package (<50MB)
   - Vérifier permissions Lambda

### Logs de Debug
- CloudWatch Logs : `/aws/lambda/vectora-inbox-*-dev`
- Script logs : Sortie console avec codes couleur