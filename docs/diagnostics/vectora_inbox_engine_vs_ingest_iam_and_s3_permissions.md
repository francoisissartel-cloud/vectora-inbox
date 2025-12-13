# Audit IAM & S3 - Permissions Engine vs Ingest-Normalize

**Date** : 2025-12-12  
**Objectif** : Vérifier les permissions S3 et IAM réelles des deux Lambdas  

---

## 1. Lambda Ingest-Normalize - Permissions IAM

### 1.1 Rôle IAM

| **Paramètre** | **Valeur** |
|---------------|------------|
| **Role Name** | vectora-inbox-s0-iam-dev-IngestNormalizeRole-aefpODOGz3Lx |
| **Politiques Attachées** | Aucune |
| **Politiques Inline** | IngestNormalizePolicy |

### 1.2 Politique Inline : IngestNormalizePolicy

#### 1.2.1 Permissions CloudWatch Logs ✅

```json
{
  "Action": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream", 
    "logs:PutLogEvents"
  ],
  "Resource": "*",
  "Effect": "Allow"
}
```

**Analyse** : ✅ Permissions logs complètes et correctes

#### 1.2.2 Permissions S3 - CONFIG_BUCKET ✅

```json
{
  "Action": [
    "s3:GetObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::vectora-inbox-config-dev",
    "arn:aws:s3:::vectora-inbox-config-dev/*"
  ],
  "Effect": "Allow"
}
```

**Analyse** : ✅ Lecture seule sur bucket config (correct pour ingestion)

#### 1.2.3 Permissions S3 - DATA_BUCKET ✅

```json
{
  "Action": [
    "s3:GetObject",
    "s3:PutObject", 
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::vectora-inbox-data-dev",
    "arn:aws:s3:::vectora-inbox-data-dev/*"
  ],
  "Effect": "Allow"
}
```

**Analyse** : ✅ Lecture/écriture sur bucket data (correct pour écriture items normalisés)

#### 1.2.4 Permissions SSM Parameter Store ✅

```json
{
  "Action": [
    "ssm:GetParameter"
  ],
  "Resource": [
    "arn:aws:ssm:eu-west-3:786469175371:parameter/rag-lai/dev/pubmed/api-key"
  ],
  "Effect": "Allow"
}
```

**Analyse** : ✅ Accès clé API PubMed (optionnel mais présent)

#### 1.2.5 Permissions Bedrock ⚠️

```json
{
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": [
    "arn:aws:bedrock:*::foundation-model/*",
    "arn:aws:bedrock:eu-west-3:786469175371:inference-profile/eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
  ],
  "Effect": "Allow"
}
```

**Analyse** : ⚠️ **PROBLÈME POTENTIEL**
- Permissions sur `*::foundation-model/*` (toutes régions) ✅
- Inference profile spécifique à `eu-west-3` ⚠️
- Lambda configurée pour `us-east-1` mais permissions inference profile en `eu-west-3`

---

## 2. Lambda Engine - Permissions IAM

### 2.1 Rôle IAM

| **Paramètre** | **Valeur** |
|---------------|------------|
| **Role Name** | vectora-inbox-s0-iam-dev-EngineRole-x4yGG8dAutT9 |
| **Politiques Attachées** | Aucune |
| **Politiques Inline** | EnginePolicy |

### 2.2 Politique Inline : EnginePolicy

#### 2.2.1 Permissions CloudWatch Logs ✅

```json
{
  "Action": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*",
  "Effect": "Allow"
}
```

**Analyse** : ✅ Permissions logs complètes et correctes

#### 2.2.2 Permissions S3 - CONFIG_BUCKET ✅

```json
{
  "Action": [
    "s3:GetObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::vectora-inbox-config-dev",
    "arn:aws:s3:::vectora-inbox-config-dev/*"
  ],
  "Effect": "Allow"
}
```

**Analyse** : ✅ Lecture seule sur bucket config (correct pour engine)

#### 2.2.3 Permissions S3 - DATA_BUCKET ✅

```json
{
  "Action": [
    "s3:GetObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::vectora-inbox-data-dev",
    "arn:aws:s3:::vectora-inbox-data-dev/*"
  ],
  "Effect": "Allow"
}
```

**Analyse** : ✅ Lecture seule sur bucket data (correct pour lecture items normalisés)

#### 2.2.4 Permissions S3 - NEWSLETTERS_BUCKET ✅

```json
{
  "Action": [
    "s3:PutObject",
    "s3:ListBucket"
  ],
  "Resource": [
    "arn:aws:s3:::vectora-inbox-newsletters-dev",
    "arn:aws:s3:::vectora-inbox-newsletters-dev/*"
  ],
  "Effect": "Allow"
}
```

**Analyse** : ✅ Écriture seule sur bucket newsletters (correct pour engine)

#### 2.2.5 Permissions Bedrock ⚠️

```json
{
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": [
    "arn:aws:bedrock:*::foundation-model/*",
    "arn:aws:bedrock:eu-west-3:786469175371:inference-profile/eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
  ],
  "Effect": "Allow"
}
```

**Analyse** : ⚠️ **PROBLÈME MAJEUR IDENTIFIÉ**
- Permissions sur `*::foundation-model/*` (toutes régions) ✅
- Inference profile spécifique à `eu-west-3` ⚠️
- Lambda configurée pour newsletter en `eu-west-3` mais aussi normalisation en `us-east-1`
- **Manque inference profile us-east-1 pour normalisation hybride**

---

## 3. Analyse Comparative des Permissions

### 3.1 Permissions S3 par Lambda

| **Bucket** | **Ingest-Normalize** | **Engine** | **Cohérence** |
|------------|---------------------|------------|---------------|
| **CONFIG_BUCKET** | GetObject, ListBucket | GetObject, ListBucket | ✅ Identique |
| **DATA_BUCKET** | GetObject, PutObject, ListBucket | GetObject, ListBucket | ✅ Logique |
| **NEWSLETTERS_BUCKET** | ❌ Aucune | PutObject, ListBucket | ✅ Logique |

**Analyse** : ✅ Séparation des responsabilités S3 correcte

### 3.2 Permissions Bedrock par Lambda

| **Aspect** | **Ingest-Normalize** | **Engine** | **Problème** |
|------------|---------------------|------------|--------------|
| **Foundation Models** | arn:aws:bedrock:*::foundation-model/* | arn:aws:bedrock:*::foundation-model/* | ✅ Identique |
| **Inference Profile** | eu-west-3 uniquement | eu-west-3 uniquement | ⚠️ **PROBLÈME** |
| **Région Utilisée** | us-east-1 | us-east-1 + eu-west-3 | ⚠️ **INCOHÉRENCE** |

---

## 4. Problèmes Identifiés

### 4.1 Problème P0 : Permissions Bedrock Incohérentes 🔧

**Problème** :
- Les deux Lambdas ont uniquement des permissions sur l'inference profile `eu-west-3`
- Ingest-Normalize utilise `us-east-1` → **Permissions manquantes**
- Engine utilise `us-east-1` pour normalisation → **Permissions manquantes**

**Impact** :
- Ingest-Normalize pourrait échouer en us-east-1 (mais fonctionne via foundation model)
- Engine pourrait échouer pour normalisation en us-east-1
- Newsletter en eu-west-3 fonctionne (permissions présentes)

### 4.2 Problème P1 : Inference Profile us-east-1 Manquant ⚠️

**Ressource Manquante** :
```json
"arn:aws:bedrock:us-east-1:786469175371:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0"
```

**Lambdas Impactées** :
- Ingest-Normalize (normalisation us-east-1)
- Engine (normalisation hybride us-east-1)

### 4.3 Analyse de la Cause du Fallback Newsletter

**Hypothèse Révisée** :
Le fallback newsletter n'est **PAS** causé par les permissions IAM car :
- Engine a les permissions sur inference profile eu-west-3 ✅
- Newsletter configurée pour eu-west-3 ✅
- Permissions foundation model globales présentes ✅

**Nouvelle Hypothèse** :
- Problème de quota/throttling en eu-west-3
- Problème de latence/timeout
- Problème de configuration Bedrock spécifique

---

## 5. Permissions S3 Détaillées

### 5.1 Ingest-Normalize - Permissions S3

| **Action** | **CONFIG_BUCKET** | **DATA_BUCKET** | **NEWSLETTERS_BUCKET** |
|------------|-------------------|-----------------|------------------------|
| **s3:ListBucket** | ✅ Autorisé | ✅ Autorisé | ❌ Non requis |
| **s3:GetObject** | ✅ Autorisé | ✅ Autorisé | ❌ Non requis |
| **s3:PutObject** | ❌ Non requis | ✅ Autorisé | ❌ Non requis |

**Analyse** : ✅ Permissions parfaitement adaptées aux besoins

### 5.2 Engine - Permissions S3

| **Action** | **CONFIG_BUCKET** | **DATA_BUCKET** | **NEWSLETTERS_BUCKET** |
|------------|-------------------|-----------------|------------------------|
| **s3:ListBucket** | ✅ Autorisé | ✅ Autorisé | ✅ Autorisé |
| **s3:GetObject** | ✅ Autorisé | ✅ Autorisé | ❌ Non requis |
| **s3:PutObject** | ❌ Non requis | ❌ Non requis | ✅ Autorisé |

**Analyse** : ✅ Permissions parfaitement adaptées aux besoins

### 5.3 Permissions Manquantes Identifiées

**Aucune permission S3 manquante** ✅
- Ingest-Normalize peut lire config et écrire data
- Engine peut lire config/data et écrire newsletters
- Séparation des responsabilités respectée

---

## 6. Recommandations de Correction

### 6.1 Correction P0 : Ajout Inference Profile us-east-1

**Pour Ingest-Normalize** :
```json
{
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": [
    "arn:aws:bedrock:*::foundation-model/*",
    "arn:aws:bedrock:eu-west-3:786469175371:inference-profile/eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "arn:aws:bedrock:us-east-1:786469175371:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0"
  ],
  "Effect": "Allow"
}
```

**Pour Engine** :
```json
{
  "Action": [
    "bedrock:InvokeModel", 
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": [
    "arn:aws:bedrock:*::foundation-model/*",
    "arn:aws:bedrock:eu-west-3:786469175371:inference-profile/eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "arn:aws:bedrock:us-east-1:786469175371:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0"
  ],
  "Effect": "Allow"
}
```

### 6.2 Vérification Inference Profile us-east-1

**Commande de vérification** :
```bash
aws bedrock list-inference-profiles --region us-east-1 --profile rag-lai-prod
```

**Si inexistant, créer ou utiliser foundation model direct**

### 6.3 Test de Résolution Newsletter

**Après correction permissions** :
1. Tester newsletter avec `BEDROCK_REGION_NEWSLETTER = us-east-1`
2. Comparer performance eu-west-3 vs us-east-1
3. Identifier la vraie cause du fallback

---

## 7. Synthèse Permissions

### 7.1 Permissions S3 ✅

| **Aspect** | **Statut** | **Détail** |
|------------|------------|------------|
| **Séparation Responsabilités** | ✅ Parfaite | Ingest écrit data, Engine écrit newsletters |
| **Permissions Minimales** | ✅ Respectées | Aucune permission excessive |
| **Buckets Corrects** | ✅ Cohérents | Tous les buckets requis couverts |

### 7.2 Permissions Bedrock ⚠️

| **Aspect** | **Statut** | **Détail** |
|------------|------------|------------|
| **Foundation Models** | ✅ Correctes | Accès global toutes régions |
| **Inference Profile eu-west-3** | ✅ Présent | Newsletter fonctionne |
| **Inference Profile us-east-1** | ⚠️ **MANQUANT** | Normalisation pourrait échouer |

### 7.3 Cause du Fallback Newsletter

**Permissions IAM ne sont PAS la cause** :
- Engine a les permissions sur eu-west-3 ✅
- Foundation models accessibles globalement ✅

**Vraie cause probable** :
- Configuration `BEDROCK_REGION_NEWSLETTER = eu-west-3` (identifiée Phase 2)
- Problème de quota/performance en eu-west-3
- Pas un problème de permissions

**Recommandation** : Corriger les permissions us-east-1 ET tester newsletter en us-east-1.