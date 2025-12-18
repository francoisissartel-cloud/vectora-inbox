# Plan de Redéploiement - Lambda ingest-normalize

**Date** : 2025-12-13  
**Objectif** : Redéployer la lambda `vectora-inbox-ingest-normalize-dev` supprimée par erreur  
**Profil AWS** : rag-lai-prod  
**Région** : eu-west-3  

---

## 🎯 Contexte

La lambda `vectora-inbox-ingest-normalize-dev` a été supprimée par erreur et doit être redéployée avec :
- L'infrastructure CloudFormation existante (stack s1-runtime-dev)
- Les permissions IAM correctes (rôle IngestNormalizeRole)
- Le code source actuel du repo
- Les variables d'environnement appropriées

---

## 📋 Plan d'Exécution

### Phase 1 : Vérification de l'Infrastructure

#### 1.1 Vérifier l'état de la stack CloudFormation
```powershell
aws cloudformation describe-stacks --stack-name vectora-inbox-s1-runtime-dev --profile rag-lai-prod --region eu-west-3
```

#### 1.2 Vérifier les rôles IAM
```powershell
aws iam get-role --role-name vectora-inbox-s0-iam-dev-IngestNormalizeRole-* --profile rag-lai-prod
```

#### 1.3 Vérifier les buckets S3
- `vectora-inbox-config-dev` (lecture)
- `vectora-inbox-data-dev` (lecture/écriture)
- `vectora-inbox-lambda-code-dev` (stockage du code)

### Phase 2 : Préparation du Code

#### 2.1 Structure du package Lambda
```
ingest-normalize-redeploy.zip
├── handler.py                    # Point d'entrée Lambda
├── vectora_core/                 # Code métier
│   ├── __init__.py
│   ├── config/
│   ├── ingestion/
│   ├── normalization/
│   └── ...
├── boto3/                        # Dépendances AWS
├── yaml/                         # Parser YAML
├── requests/                     # HTTP client
├── feedparser/                   # Parser RSS
├── bs4/                          # BeautifulSoup
└── ...                          # Autres dépendances
```

#### 2.2 Handler Lambda
- Point d'entrée : `handler.lambda_handler`
- Import : `from vectora_core import run_ingest_normalize_for_client`
- Gestion des erreurs et logging

### Phase 3 : Packaging et Upload

#### 3.1 Créer le package
```powershell
# Utiliser le script existant adapté
.\scripts\package-ingest-normalize-redeploy.ps1
```

#### 3.2 Upload vers S3
```powershell
aws s3 cp ingest-normalize-redeploy.zip s3://vectora-inbox-lambda-code-dev/lambda/ingest-normalize/redeploy.zip
```

### Phase 4 : Redéploiement CloudFormation

#### 4.1 Paramètres de la stack
```yaml
Parameters:
  IngestNormalizeCodeKey: "lambda/ingest-normalize/redeploy.zip"
  BedrockModelId: "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
  LambdaTimeout: 300
  LambdaMemorySize: 512
```

#### 4.2 Mise à jour de la stack
```powershell
aws cloudformation update-stack \
  --stack-name vectora-inbox-s1-runtime-dev \
  --template-body file://infra/s1-runtime.yaml \
  --parameters file://infra/params-s1-runtime-dev.json \
  --capabilities CAPABILITY_IAM \
  --profile rag-lai-prod \
  --region eu-west-3
```

### Phase 5 : Configuration des Variables d'Environnement

#### 5.1 Variables requises
```json
{
  "ENV": "dev",
  "PROJECT_NAME": "vectora-inbox",
  "CONFIG_BUCKET": "vectora-inbox-config-dev",
  "DATA_BUCKET": "vectora-inbox-data-dev",
  "BEDROCK_MODEL_ID": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "PUBMED_API_KEY_PARAM": "/rag-lai/dev/pubmed/api-key",
  "LOG_LEVEL": "INFO"
}
```

#### 5.2 Vérification de la configuration
```powershell
aws lambda get-function --function-name vectora-inbox-ingest-normalize-dev --profile rag-lai-prod --region eu-west-3
```

### Phase 6 : Tests de Validation

#### 6.1 Test de smoke (invocation simple)
```json
{
  "client_id": "lai_weekly_v3",
  "period_days": 1,
  "sources": ["press_corporate__medincell"]
}
```

#### 6.2 Test d'ingestion complète
```json
{
  "client_id": "lai_weekly_v3",
  "period_days": 7
}
```

#### 6.3 Vérification des outputs S3
- Fichier normalisé : `s3://vectora-inbox-data-dev/normalized/lai_weekly_v3/2025/12/13/items.json`
- Logs CloudWatch : `/aws/lambda/vectora-inbox-ingest-normalize-dev`

---

## 🔧 Scripts de Déploiement

### Script Principal : `deploy-ingest-normalize-redeploy.ps1`

```powershell
# Redéploiement complet de la lambda ingest-normalize
param(
    [string]$Profile = "rag-lai-prod",
    [string]$Region = "eu-west-3"
)

Write-Host "=== Redéploiement ingest-normalize ===" -ForegroundColor Green

# 1. Package du code
.\scripts\package-ingest-normalize-redeploy.ps1 -Profile $Profile -Region $Region

# 2. Mise à jour CloudFormation
aws cloudformation update-stack \
  --stack-name vectora-inbox-s1-runtime-dev \
  --template-body file://infra/s1-runtime.yaml \
  --parameters ParameterKey=IngestNormalizeCodeKey,ParameterValue=lambda/ingest-normalize/redeploy.zip \
  --capabilities CAPABILITY_IAM \
  --profile $Profile \
  --region $Region

# 3. Attendre la fin du déploiement
aws cloudformation wait stack-update-complete \
  --stack-name vectora-inbox-s1-runtime-dev \
  --profile $Profile \
  --region $Region

# 4. Test de validation
.\scripts\test-ingest-normalize-redeploy.ps1 -Profile $Profile -Region $Region
```

### Script de Test : `test-ingest-normalize-redeploy.ps1`

```powershell
# Test de validation post-déploiement
param(
    [string]$Profile = "rag-lai-prod",
    [string]$Region = "eu-west-3"
)

$TestPayload = @{
    client_id = "lai_weekly_v3"
    period_days = 1
    sources = @("press_corporate__medincell")
} | ConvertTo-Json

Write-Host "Test d'invocation de la lambda..." -ForegroundColor Yellow

$Result = aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload $TestPayload \
  --output-file test-result.json \
  --profile $Profile \
  --region $Region

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Test réussi!" -ForegroundColor Green
    Get-Content test-result.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
} else {
    Write-Host "❌ Test échoué" -ForegroundColor Red
}
```

---

## 🚨 Points d'Attention

### Sécurité
- Vérifier que le rôle IAM a les permissions Bedrock
- Confirmer l'accès aux buckets S3
- Valider le paramètre SSM PubMed

### Performance
- Timeout : 300 secondes (5 minutes)
- Mémoire : 512 MB
- Taille du package : < 70 MB

### Monitoring
- Logs CloudWatch activés
- Rétention : 14 jours
- Métriques Lambda standard

---

## 📊 Critères de Succès

### Déploiement
- [ ] Stack CloudFormation UPDATE_COMPLETE
- [ ] Lambda créée avec le bon handler
- [ ] Variables d'environnement configurées
- [ ] Rôle IAM attaché

### Fonctionnel
- [ ] Test d'invocation réussi (statusCode 200)
- [ ] Fichier normalisé créé dans S3
- [ ] Logs sans erreur critique
- [ ] Temps d'exécution < 60 secondes pour 1 jour

### Opérationnel
- [ ] Monitoring CloudWatch actif
- [ ] Permissions S3 validées
- [ ] Accès Bedrock confirmé
- [ ] Configuration client lai_weekly_v3 chargée

---

## 🔄 Rollback Plan

En cas d'échec :

1. **Revenir à la version précédente**
   ```powershell
   aws cloudformation cancel-update-stack --stack-name vectora-inbox-s1-runtime-dev
   ```

2. **Utiliser un package de code antérieur**
   ```powershell
   aws lambda update-function-code \
     --function-name vectora-inbox-ingest-normalize-dev \
     --s3-bucket vectora-inbox-lambda-code-dev \
     --s3-key lambda/ingest-normalize/latest.zip
   ```

3. **Vérifier les logs d'erreur**
   ```powershell
   aws logs describe-log-streams \
     --log-group-name /aws/lambda/vectora-inbox-ingest-normalize-dev
   ```

---

**Prêt pour exécution** ✅