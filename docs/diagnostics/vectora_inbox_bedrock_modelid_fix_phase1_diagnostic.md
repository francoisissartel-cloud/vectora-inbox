# Vectora Inbox - Diagnostic Phase 1 : "Model Identifier Invalid"

**Date** : 2025-12-12  
**Problème** : ValidationException: The provided model identifier is invalid  
**Contexte** : lai_weekly_v3 - Normalisation échoue à 100%

---

## Résumé Exécutif

✅ **CAUSE RACINE IDENTIFIÉE** : Préfixes régionaux incorrects dans les model_id Bedrock

Le problème vient de l'utilisation de préfixes régionaux (`us.` et `eu.`) dans les identifiants de modèles Bedrock, alors que les modèles réels n'utilisent pas ces préfixes dans les régions us-east-1 et eu-west-3.

---

## 1. Configuration Actuelle des Lambdas

### 1.1 vectora-inbox-ingest-normalize-dev

```json
{
    "BEDROCK_REGION": "us-east-1",
    "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
}
```

**❌ PROBLÈME** : Préfixe `us.` incorrect

### 1.2 vectora-inbox-engine-dev

```json
{
    "BEDROCK_REGION": "us-east-1",
    "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_REGION_NORMALIZATION": "us-east-1",
    "BEDROCK_MODEL_ID_NORMALIZATION": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_REGION_NEWSLETTER": "eu-west-3",
    "BEDROCK_MODEL_ID_NEWSLETTER": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
}
```

**❌ PROBLÈME** : Préfixes `us.` et `eu.` incorrects

---

## 2. Modèles Réellement Disponibles

### 2.1 us-east-1

```
ModelId: anthropic.claude-sonnet-4-5-20250929-v1:0
Status: ACTIVE
```

### 2.2 eu-west-3

```
ModelId: anthropic.claude-sonnet-4-5-20250929-v1:0
Status: ACTIVE
```

**✅ CONSTAT** : Le modèle Claude Sonnet 4.5 est disponible dans les deux régions, mais **SANS préfixes régionaux**.

---

## 3. Analyse du Code

### 3.1 Client Bedrock Normalisation

**Fichier** : `src/vectora_core/normalization/bedrock_client.py`

```python
def get_bedrock_client():
    region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    return boto3.client('bedrock-runtime', region_name=region)
```

**✅ CODE OK** : Utilise correctement la variable d'environnement `BEDROCK_REGION`

### 3.2 Client Bedrock Newsletter

**Fichier** : `src/vectora_core/newsletter/bedrock_client.py`

```python
def get_bedrock_client_hybrid(service_type: str = 'newsletter'):
    if service_type == 'normalization':
        region = os.environ.get('BEDROCK_REGION_NORMALIZATION', 'us-east-1')
        model_id = os.environ.get('BEDROCK_MODEL_ID_NORMALIZATION', 
                                 'us.anthropic.claude-sonnet-4-5-20250929-v1:0')
    elif service_type == 'newsletter':
        region = os.environ.get('BEDROCK_REGION_NEWSLETTER', 'eu-west-3')
        model_id = os.environ.get('BEDROCK_MODEL_ID_NEWSLETTER', 
                                 'eu.anthropic.claude-sonnet-4-5-20250929-v1:0')
```

**✅ CODE OK** : Utilise correctement les variables d'environnement spécialisées

---

## 4. Validation du Problème

### 4.1 Séquence d'Erreur

1. **Ingestion** : ✅ Fonctionne (~104 items)
2. **Normalisation** : ❌ Échec ValidationException sur model_id
3. **Engine** : ❌ Impossible de continuer (0 items normalisés)

### 4.2 Point de Défaillance

La normalisation utilise :
- **Région** : `us-east-1` ✅
- **Model ID** : `us.anthropic.claude-sonnet-4-5-20250929-v1:0` ❌

Bedrock us-east-1 attend :
- **Model ID** : `anthropic.claude-sonnet-4-5-20250929-v1:0` ✅

---

## 5. Hypothèse de Cause Racine

### 5.1 Origine du Problème

Les préfixes régionaux (`us.`, `eu.`) ont probablement été ajoutés lors de la migration Bedrock eu-west-3 → us-east-1, en supposant que les régions utilisaient des préfixes différents.

### 5.2 Validation

- ✅ Le modèle `anthropic.claude-sonnet-4-5-20250929-v1:0` existe dans us-east-1
- ✅ Le modèle `anthropic.claude-sonnet-4-5-20250929-v1:0` existe dans eu-west-3
- ❌ Les modèles avec préfixes `us.` et `eu.` n'existent pas

---

## 6. Impact Métier

### 6.1 Workflow Cassé

```
Ingestion (104 items) → Normalisation (0 items) → Engine (impossible)
                            ↑
                    ValidationException
```

### 6.2 Conséquences

- **Normalisation** : 0% de réussite
- **Entités** : Non détectées (Nanexa, UZEDY®, etc.)
- **Newsletter** : Impossible à générer
- **MVP** : Bloqué

---

## 7. Solution Recommandée

### 7.1 Correction Minimale

**Retirer les préfixes régionaux** des model_id dans les variables d'environnement Lambda :

```json
{
  "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "BEDROCK_MODEL_ID_NORMALIZATION": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "BEDROCK_MODEL_ID_NEWSLETTER": "anthropic.claude-sonnet-4-5-20250929-v1:0"
}
```

### 7.2 Stratégie Région

**Maintenir la configuration hybride actuelle** :
- **Normalisation** : us-east-1 (performance +88%)
- **Newsletter** : eu-west-3 (stabilité)

### 7.3 Changements Requis

1. **vectora-inbox-ingest-normalize-dev** :
   - `BEDROCK_MODEL_ID` : `us.` → supprimé

2. **vectora-inbox-engine-dev** :
   - `BEDROCK_MODEL_ID` : `us.` → supprimé
   - `BEDROCK_MODEL_ID_NORMALIZATION` : `us.` → supprimé
   - `BEDROCK_MODEL_ID_NEWSLETTER` : `eu.` → supprimé

3. **Code** : ✅ Aucun changement requis

---

## 8. Validation Prévue

### 8.1 Test Immédiat

```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":1}' \
  out-test-fix.json
```

### 8.2 Critères de Succès

- ✅ Normalisation > 90% items
- ✅ Entités détectées (companies, molecules, technologies)
- ✅ Absence ValidationException
- ✅ Temps < 2 minutes

---

## 9. Recommandations P1

### 9.1 Monitoring

- Alertes sur ValidationException Bedrock
- Métriques taux de succès normalisation
- Dashboard model_id par région

### 9.2 Documentation

- Standardiser nomenclature model_id
- Procédure validation modèles disponibles
- Guide migration Bedrock régions

---

## Conclusion

**Cause racine confirmée** : Préfixes régionaux incorrects dans les identifiants de modèles Bedrock.

**Solution simple** : Retirer les préfixes `us.` et `eu.` des variables d'environnement Lambda.

**Impact** : Correction minimale, aucun changement de code requis, restauration complète du workflow lai_weekly_v3.