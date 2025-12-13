# Vectora Inbox - Newsletter P1 Phase 3 : Déploiement AWS DEV

**Date** : 2025-12-12  
**Phase** : Phase 3 - Déploiement AWS DEV  
**Statut** : ✅ **PACKAGE PRÊT POUR DÉPLOIEMENT**

---

## 🎯 Résumé Exécutif

### 📦 Package P1 Créé avec Succès

**Package Lambda P1** : `engine-p1-newsletter-optimized.zip` (18.3 MB)

**Contenu validé** :
- ✅ **Code P1** : Modifications newsletter hybride + cache
- ✅ **Handler mis à jour** : Paramètres P1 intégrés
- ✅ **Dépendances** : Toutes les librairies requises
- ✅ **Taille acceptable** : 18.3 MB (limite AWS 50 MB)

**Prêt pour déploiement AWS DEV** avec configuration hybride eu-west-3/us-east-1.

---

## 📋 Package P1 Détaillé

### Contenu Package

**Fichiers critiques P1** :
```
engine-p1-newsletter-optimized.zip
├── handler.py                           # Handler Lambda avec paramètres P1
├── vectora_core/
│   ├── newsletter/
│   │   ├── bedrock_client.py            # Client hybride + cache + prompt optimisé
│   │   ├── assembler.py                 # Intégration paramètres P1
│   │   └── formatter.py                 # Inchangé
│   └── [autres modules...]              # Modules existants
└── [dépendances Lambda...]              # boto3, requests, etc.
```

**Modifications P1 incluses** :
- ✅ `get_bedrock_client_hybrid()` : Client eu-west-3/us-east-1
- ✅ `get_cached_newsletter()` : Lecture cache S3
- ✅ `save_editorial_to_cache()` : Écriture cache S3
- ✅ `_build_ultra_compact_prompt()` : Prompt -83% tokens
- ✅ Handler avec `force_regenerate` et variables hybrides

### Taille et Performance

**Métriques package** :
- **Taille** : 18.3 MB (vs limite 50 MB AWS)
- **Compression** : Optimal
- **Fichiers** : ~2000+ (dépendances + code)
- **Compatibilité** : Python 3.14, AWS Lambda

**Performance attendue** :
- **Cold start** : ~3-5s (taille raisonnable)
- **Warm execution** : ~10-15s (validé localement 9.93s)
- **Memory usage** : ~200-300 MB (estimation)

---

## 🔧 Configuration AWS Requise

### Variables d'Environnement Lambda

**Configuration P1 hybride** :
```json
{
  "ENV": "dev",
  "PROJECT_NAME": "vectora-inbox",
  "CONFIG_BUCKET": "vectora-inbox-config-dev",
  "DATA_BUCKET": "vectora-inbox-data-dev",
  "NEWSLETTERS_BUCKET": "vectora-inbox-newsletters-dev",
  
  "BEDROCK_REGION_NEWSLETTER": "eu-west-3",
  "BEDROCK_MODEL_ID_NEWSLETTER": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "BEDROCK_REGION_NORMALIZATION": "us-east-1",
  "BEDROCK_MODEL_ID_NORMALIZATION": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  
  "BEDROCK_REGION": "us-east-1",
  "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  
  "LOG_LEVEL": "INFO"
}
```

**Nouvelles variables P1** :
- `BEDROCK_REGION_NEWSLETTER` : eu-west-3 (séparation quotas)
- `BEDROCK_MODEL_ID_NEWSLETTER` : Claude Sonnet 4.5 EU
- `BEDROCK_REGION_NORMALIZATION` : us-east-1 (performance)
- `BEDROCK_MODEL_ID_NORMALIZATION` : Claude Sonnet 4.5 US

### Permissions IAM Requises

**Bedrock cross-région** :
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1:*:model/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "arn:aws:bedrock:eu-west-3:*:model/eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
      ]
    }
  ]
}
```

**S3 cache newsletter** :
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::vectora-inbox-newsletters-dev/cache/*"
      ]
    }
  ]
}
```

---

## 🚀 Commandes de Déploiement

### Déploiement Lambda Engine

**Commande principale** :
```bash
aws lambda update-function-code \
  --function-name vectora-inbox-engine-dev \
  --zip-file fileb://engine-p1-newsletter-optimized.zip \
  --profile rag-lai-prod \
  --region eu-west-3
```

**Mise à jour configuration** :
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-engine-dev \
  --environment file://lambda-env-p1-hybrid.json \
  --timeout 900 \
  --memory-size 512 \
  --profile rag-lai-prod \
  --region eu-west-3
```

**Fichier configuration** (`lambda-env-p1-hybrid.json`) :
```json
{
  "Variables": {
    "ENV": "dev",
    "PROJECT_NAME": "vectora-inbox",
    "CONFIG_BUCKET": "vectora-inbox-config-dev",
    "DATA_BUCKET": "vectora-inbox-data-dev",
    "NEWSLETTERS_BUCKET": "vectora-inbox-newsletters-dev",
    "BEDROCK_REGION_NEWSLETTER": "eu-west-3",
    "BEDROCK_MODEL_ID_NEWSLETTER": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_REGION_NORMALIZATION": "us-east-1",
    "BEDROCK_MODEL_ID_NORMALIZATION": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_REGION": "us-east-1",
    "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "LOG_LEVEL": "INFO"
  }
}
```

### Vérification Déploiement

**Test invocation** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-engine-dev \
  --payload file://test-payload-p1.json \
  --cli-binary-format raw-in-base64-out \
  out-engine-p1-test.json \
  --profile rag-lai-prod \
  --region eu-west-3
```

**Payload test P1** (`test-payload-p1.json`) :
```json
{
  "client_id": "lai_weekly_v3",
  "period_days": 7,
  "force_regenerate": false
}
```

**Vérification logs** :
```bash
aws logs tail /aws/lambda/vectora-inbox-engine-dev \
  --since 10m \
  --profile rag-lai-prod \
  --region eu-west-3
```

---

## 🧪 Tests Post-Déploiement

### Test 1 : Invocation Basique

**Objectif** : Valider déploiement et configuration

**Commande** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-engine-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":1}' \
  --cli-binary-format raw-in-base64-out \
  out-test-p1-basic.json
```

**Résultat attendu** :
- ✅ StatusCode 200
- ✅ Logs "Client Bedrock hybride : newsletter → eu-west-3"
- ✅ Pas d'erreur configuration

### Test 2 : Cache Newsletter

**Objectif** : Valider fonctionnement cache S3

**Commande 1** (génération) :
```bash
aws lambda invoke \
  --function-name vectora-inbox-engine-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":7,"force_regenerate":true}' \
  --cli-binary-format raw-in-base64-out \
  out-test-p1-generate.json
```

**Commande 2** (cache hit) :
```bash
aws lambda invoke \
  --function-name vectora-inbox-engine-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":7,"force_regenerate":false}' \
  --cli-binary-format raw-in-base64-out \
  out-test-p1-cache.json
```

**Résultat attendu** :
- ✅ Run 1 : "Newsletter sauvegardée en cache"
- ✅ Run 2 : "Newsletter récupérée depuis cache S3"
- ✅ Temps Run 2 < Temps Run 1

### Test 3 : Client Hybride

**Objectif** : Valider séparation régions Bedrock

**Vérification logs** :
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/vectora-inbox-engine-dev \
  --filter-pattern "Client Bedrock hybride" \
  --start-time $(date -d '10 minutes ago' +%s)000
```

**Résultat attendu** :
- ✅ "Client Bedrock hybride : newsletter → eu-west-3"
- ✅ "Client Bedrock hybride : normalization → us-east-1"
- ✅ Pas d'erreur throttling newsletter

---

## 📊 Métriques de Validation

### Performance Attendue

| **Métrique** | **Objectif P1** | **Validation** |
|--------------|-----------------|----------------|
| **Cold start** | <10s | Mesurer 1ère invocation |
| **Warm execution** | <30s | Mesurer 2ème invocation |
| **Cache hit** | <5s | Mesurer avec cache |
| **Memory usage** | <400 MB | CloudWatch metrics |
| **Timeout** | 0% | Pas d'erreur timeout |

### Fonctionnalités P1

| **Fonctionnalité** | **Test** | **Validation** |
|-------------------|----------|----------------|
| **Client hybride** | Logs régions | eu-west-3 + us-east-1 |
| **Cache S3** | Double invocation | Hit/Miss détecté |
| **Prompt optimisé** | Tokens logs | <1000 tokens |
| **Force regenerate** | Flag test | Bypass cache |
| **Backward compatibility** | Sans paramètres P1 | Fonctionne |

---

## 🔄 Plan de Rollback

### Rollback Immédiat

**Si problème critique** :
```bash
# Rollback vers package précédent
aws lambda update-function-code \
  --function-name vectora-inbox-engine-dev \
  --zip-file fileb://engine-v2-complete.zip \
  --profile rag-lai-prod \
  --region eu-west-3

# Rollback configuration
aws lambda update-function-configuration \
  --function-name vectora-inbox-engine-dev \
  --environment file://lambda-env-eu-west-3-backup.json \
  --profile rag-lai-prod \
  --region eu-west-3
```

**Temps de rollback** : <5 minutes

### Validation Rollback

**Test post-rollback** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-engine-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":1}' \
  --cli-binary-format raw-in-base64-out \
  out-rollback-validation.json
```

---

## 📋 Checklist Déploiement

### Pré-Déploiement

- [x] **Package créé** : engine-p1-newsletter-optimized.zip (18.3 MB)
- [x] **Modifications P1 validées** : Tests locaux 100% réussis
- [x] **Configuration préparée** : lambda-env-p1-hybrid.json
- [x] **Permissions IAM** : Cross-région Bedrock + S3 cache
- [x] **Plan de rollback** : Package précédent disponible

### Déploiement

- [ ] **Upload package** : aws lambda update-function-code
- [ ] **Mise à jour config** : Variables d'environnement P1
- [ ] **Test invocation** : Payload basique
- [ ] **Vérification logs** : Client hybride + cache
- [ ] **Test cache** : Double invocation

### Post-Déploiement

- [ ] **Performance** : Temps d'exécution <30s
- [ ] **Fonctionnalités** : Cache + hybride opérationnels
- [ ] **Monitoring** : CloudWatch metrics
- [ ] **Documentation** : Résultats dans diagnostic Phase 3
- [ ] **Validation E2E** : Préparation Phase 4

---

## 🎯 Critères de Succès Phase 3

### Déploiement Technique

- [ ] **Package déployé** : Sans erreur AWS
- [ ] **Configuration appliquée** : Variables P1 actives
- [ ] **Invocation réussie** : StatusCode 200
- [ ] **Logs cohérents** : Client hybride détecté

### Fonctionnalités P1

- [ ] **Client hybride** : eu-west-3 newsletter, us-east-1 normalisation
- [ ] **Cache S3** : Lecture/écriture opérationnelle
- [ ] **Prompt optimisé** : <1000 tokens dans logs
- [ ] **Performance** : <30s exécution

### Préparation Phase 4

- [ ] **Tests post-déploiement** : Tous réussis
- [ ] **Monitoring actif** : CloudWatch configuré
- [ ] **Rollback testé** : Procédure validée
- [ ] **Documentation** : Commandes et résultats

---

## 🚀 Transition vers Phase 4

**Phase 3 prête pour exécution.** Le package P1 est créé et validé avec :

1. **Code P1 stable** : Tests locaux 100% réussis
2. **Configuration hybride** : eu-west-3/us-east-1 prête
3. **Déploiement documenté** : Commandes et tests définis
4. **Rollback préparé** : Procédure de sécurité

**Prochaine étape** : Exécution déploiement AWS DEV puis Phase 4 - Run E2E lai_weekly_v3.

---

**Phase 3 documentée - Package P1 prêt pour déploiement AWS DEV**