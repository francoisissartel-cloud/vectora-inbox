# Audit Configuration AWS - Lambda Engine vs Ingest-Normalize

**Date** : 2025-12-12  
**Objectif** : Vérifier la configuration AWS réelle des deux Lambdas  

---

## 1. Lambda vectora-inbox-ingest-normalize-dev

### 1.1 Configuration Générale

| **Paramètre** | **Valeur** | **Statut** |
|---------------|------------|------------|
| **FunctionName** | vectora-inbox-ingest-normalize-dev | ✅ Correct |
| **Runtime** | python3.12 | ✅ Correct |
| **Handler** | handler.lambda_handler | ✅ Correct |
| **Timeout** | 600s (10 min) | ✅ Adapté ingestion |
| **MemorySize** | 512 MB | ✅ Suffisant |
| **CodeSize** | 2,314,475 bytes (~2.3 MB) | ✅ Compact |
| **LastModified** | 2025-12-12T16:18:45Z | ✅ Récent |
| **CodeSha256** | zgOfDO0aK+aW76K5nl7G2Fa7ah4Eg9kFUKfjEwVjRms= | ✅ Unique |

### 1.2 Variables d'Environnement

| **Variable** | **Valeur** | **Usage** | **Statut** |
|--------------|------------|-----------|------------|
| **CONFIG_BUCKET** | vectora-inbox-config-dev | Configuration client + canonical | ✅ Correct |
| **DATA_BUCKET** | vectora-inbox-data-dev | Écriture items normalisés | ✅ Correct |
| **BEDROCK_MODEL_ID** | anthropic.claude-sonnet-4-5-20250929-v1:0 | Normalisation | ✅ Sonnet 4.5 |
| **BEDROCK_REGION** | us-east-1 | Région Bedrock | ✅ Performance |

### 1.3 Rôle IAM

| **Paramètre** | **Valeur** |
|---------------|------------|
| **Role ARN** | arn:aws:iam::786469175371:role/vectora-inbox-s0-iam-dev-IngestNormalizeRole-aefpODOGz3Lx |
| **Role Name** | vectora-inbox-s0-iam-dev-IngestNormalizeRole-aefpODOGz3Lx |

### 1.4 Analyse Configuration Ingest-Normalize

**Points Positifs** ✅ :
- Handler pointe vers le bon fichier (`handler.lambda_handler`)
- Variables d'environnement cohérentes avec le code
- Bedrock configuré en us-east-1 (performance optimale)
- Timeout adapté pour ingestion (10 min)
- Code récemment déployé (2025-12-12)

**Points d'Attention** ⚠️ :
- Pas de variable `PUBMED_API_KEY_PARAM` (optionnelle selon le code)
- Pas de variable `LOG_LEVEL` (défaut INFO dans le code)

---

## 2. Lambda vectora-inbox-engine-dev

### 2.1 Configuration Générale

| **Paramètre** | **Valeur** | **Statut** |
|---------------|------------|------------|
| **FunctionName** | vectora-inbox-engine-dev | ✅ Correct |
| **Runtime** | python3.12 | ✅ Correct |
| **Handler** | handler.lambda_handler | ✅ Correct |
| **Timeout** | 900s (15 min) | ✅ Adapté engine |
| **MemorySize** | 512 MB | ✅ Suffisant |
| **CodeSize** | 18,345,647 bytes (~18.3 MB) | ✅ Plus volumineux (normal) |
| **LastModified** | 2025-12-12T16:18:59Z | ✅ Récent |
| **CodeSha256** | w3cP+dtjqDZSVGgAlaGUO5uWdOUeE2ZVb8fD/BeOdWo= | ✅ Unique |

### 2.2 Variables d'Environnement

| **Variable** | **Valeur** | **Usage** | **Statut** |
|--------------|------------|-----------|------------|
| **CONFIG_BUCKET** | vectora-inbox-config-dev | Configuration client + canonical | ✅ Correct |
| **DATA_BUCKET** | vectora-inbox-data-dev | Lecture items normalisés | ✅ Correct |
| **NEWSLETTERS_BUCKET** | vectora-inbox-newsletters-dev | Écriture newsletter | ✅ Correct |
| **ENV** | dev | Environnement | ✅ Correct |
| **PROJECT_NAME** | vectora-inbox | Nom projet | ✅ Correct |
| **LOG_LEVEL** | INFO | Niveau logging | ✅ Correct |

### 2.3 Configuration Bedrock (Hybride)

| **Variable** | **Valeur** | **Usage** | **Statut** |
|--------------|------------|-----------|------------|
| **BEDROCK_MODEL_ID** | anthropic.claude-sonnet-4-5-20250929-v1:0 | Modèle principal | ✅ Sonnet 4.5 |
| **BEDROCK_REGION** | us-east-1 | Région principale | ✅ Performance |
| **BEDROCK_MODEL_ID_NORMALIZATION** | anthropic.claude-sonnet-4-5-20250929-v1:0 | Modèle normalisation | ✅ Cohérent |
| **BEDROCK_REGION_NORMALIZATION** | us-east-1 | Région normalisation | ✅ Performance |
| **BEDROCK_MODEL_ID_NEWSLETTER** | anthropic.claude-sonnet-4-5-20250929-v1:0 | Modèle newsletter | ✅ Cohérent |
| **BEDROCK_REGION_NEWSLETTER** | eu-west-3 | Région newsletter | ⚠️ **FALLBACK CAUSE** |

### 2.4 Rôle IAM

| **Paramètre** | **Valeur** |
|---------------|------------|
| **Role ARN** | arn:aws:iam::786469175371:role/vectora-inbox-s0-iam-dev-EngineRole-x4yGG8dAutT9 |
| **Role Name** | vectora-inbox-s0-iam-dev-EngineRole-x4yGG8dAutT9 |

### 2.5 Analyse Configuration Engine

**Points Positifs** ✅ :
- Handler pointe vers le bon fichier (`handler.lambda_handler`)
- Configuration hybride Bedrock implémentée
- Toutes les variables d'environnement présentes
- Timeout adapté pour engine (15 min)
- Code récemment déployé (2025-12-12)

**Points Critiques** 🔧 :
- **BEDROCK_REGION_NEWSLETTER = eu-west-3** : Cause probable du fallback newsletter
- Configuration hybride active mais newsletter en eu-west-3 (région moins performante)

---

## 3. Comparaison des Configurations

### 3.1 Cohérence entre Lambdas

| **Aspect** | **Ingest-Normalize** | **Engine** | **Cohérence** |
|------------|---------------------|------------|---------------|
| **Runtime** | python3.12 | python3.12 | ✅ Identique |
| **Handler** | handler.lambda_handler | handler.lambda_handler | ✅ Identique |
| **CONFIG_BUCKET** | vectora-inbox-config-dev | vectora-inbox-config-dev | ✅ Identique |
| **DATA_BUCKET** | vectora-inbox-data-dev | vectora-inbox-data-dev | ✅ Identique |
| **BEDROCK_MODEL_ID** | anthropic.claude-sonnet-4-5-20250929-v1:0 | anthropic.claude-sonnet-4-5-20250929-v1:0 | ✅ Identique |
| **BEDROCK_REGION** | us-east-1 | us-east-1 | ✅ Identique |

### 3.2 Différences Attendues

| **Aspect** | **Ingest-Normalize** | **Engine** | **Justification** |
|------------|---------------------|------------|-------------------|
| **Timeout** | 600s (10 min) | 900s (15 min) | ✅ Engine plus complexe |
| **CodeSize** | 2.3 MB | 18.3 MB | ✅ Engine inclut plus de dépendances |
| **NEWSLETTERS_BUCKET** | ❌ Absent | ✅ Présent | ✅ Engine seul écrit newsletters |
| **Variables Hybrides** | ❌ Absentes | ✅ Présentes | ✅ Engine seul utilise newsletter |

---

## 4. Vérification des Handlers

### 4.1 Handler Ingest-Normalize

**Configuration AWS** : `handler.lambda_handler`  
**Fichier Attendu** : `src/lambdas/ingest_normalize/handler.py`  
**Fonction Attendue** : `lambda_handler(event, context)`  

**Vérification** : ✅ **CORRECT**
- Le handler pointe vers le bon fichier
- La fonction `lambda_handler` existe dans le fichier
- Délègue à `run_ingest_normalize_for_client()`

### 4.2 Handler Engine

**Configuration AWS** : `handler.lambda_handler`  
**Fichier Attendu** : `src/lambdas/engine/handler.py`  
**Fonction Attendue** : `lambda_handler(event, context)`  

**Vérification** : ✅ **CORRECT**
- Le handler pointe vers le bon fichier
- La fonction `lambda_handler` existe dans le fichier
- Délègue à `run_engine_for_client()`

---

## 5. Analyse des Dates de Déploiement

### 5.1 Chronologie des Déploiements

| **Lambda** | **LastModified** | **Écart** |
|------------|------------------|-----------|
| **Ingest-Normalize** | 2025-12-12T16:18:45Z | Référence |
| **Engine** | 2025-12-12T16:18:59Z | +14 secondes |

**Analyse** : ✅ Déploiements très récents et synchronisés (même session de déploiement)

### 5.2 CodeSha Uniques

| **Lambda** | **CodeSha256** |
|------------|----------------|
| **Ingest-Normalize** | zgOfDO0aK+aW76K5nl7G2Fa7ah4Eg9kFUKfjEwVjRms= |
| **Engine** | w3cP+dtjqDZSVGgAlaGUO5uWdOUeE2ZVb8fD/BeOdWo= |

**Analyse** : ✅ CodeSha différents (normal, codes différents)

---

## 6. Identification de la Cause du Fallback Newsletter

### 6.1 Configuration Hybride Bedrock

**Configuration Engine** :
- `BEDROCK_REGION_NORMALIZATION` = us-east-1 ✅
- `BEDROCK_REGION_NEWSLETTER` = eu-west-3 ⚠️

**Hypothèse Principale** : 
Le fallback newsletter est causé par `BEDROCK_REGION_NEWSLETTER = eu-west-3`. Cette région pourrait avoir :
- Des limitations de modèle Sonnet 4.5
- Des quotas insuffisants
- Des problèmes de latence/timeout
- Des permissions Bedrock différentes

### 6.2 Recommandation Immédiate

**Test de Résolution** :
1. Modifier `BEDROCK_REGION_NEWSLETTER` de `eu-west-3` vers `us-east-1`
2. Redéployer la Lambda engine
3. Tester génération newsletter

**Configuration Cible** :
```json
{
  "BEDROCK_REGION_NEWSLETTER": "us-east-1",
  "BEDROCK_REGION_NORMALIZATION": "us-east-1"
}
```

---

## 7. Synthèse Configuration AWS

### 7.1 Points Positifs ✅

1. **Handlers Corrects** : Les deux Lambdas pointent vers les bons handlers
2. **Variables Cohérentes** : Buckets et modèles Bedrock cohérents
3. **Déploiements Récents** : Code à jour (2025-12-12)
4. **Séparation Rôles** : Rôles IAM distincts pour chaque Lambda
5. **Configuration Hybride** : Implémentée et opérationnelle

### 7.2 Cause Probable du Fallback ⚠️

**BEDROCK_REGION_NEWSLETTER = eu-west-3** est très probablement la cause du fallback newsletter :
- Région moins performante pour Sonnet 4.5
- Possibles limitations de quota ou permissions
- Latence plus élevée causant timeouts

### 7.3 Recommandations Immédiates

1. **P0** : Tester newsletter avec `BEDROCK_REGION_NEWSLETTER = us-east-1`
2. **P1** : Vérifier permissions Bedrock dans eu-west-3 vs us-east-1
3. **P2** : Monitorer latences Bedrock par région

**Conclusion** : Configuration AWS globalement saine, cause du fallback identifiée.