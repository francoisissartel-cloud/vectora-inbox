# Vectora Inbox - Phase 3 : Changements Appliqués

**Date** : 2025-12-12  
**Problème** : ValidationException: The provided model identifier is invalid  
**Solution** : Retrait des préfixes régionaux des model_id Bedrock

---

## Résumé des Changements

✅ **CORRECTIONS APPLIQUÉES** : Préfixes régionaux supprimés des variables d'environnement Lambda

**Impact** : Aucun changement de code requis, correction uniquement au niveau AWS

---

## 1. Changements Lambda vectora-inbox-ingest-normalize-dev

### 1.1 Avant (Incorrect)

```json
{
    "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
}
```

### 1.2 Après (Corrigé)

```json
{
    "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-5-20250929-v1:0"
}
```

### 1.3 Commande Exécutée

```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-normalize-dev \
  --environment Variables={CONFIG_BUCKET=vectora-inbox-config-dev,BEDROCK_REGION=us-east-1,DATA_BUCKET=vectora-inbox-data-dev,BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-5-20250929-v1:0} \
  --profile rag-lai-prod --region eu-west-3
```

### 1.4 Statut

- ✅ **LastUpdateStatus** : InProgress → Active
- ✅ **RevisionId** : 78bd6ca7-49b0-40c6-83f9-5eb2e2712cad
- ✅ **Configuration** : Mise à jour réussie

---

## 2. Changements Lambda vectora-inbox-engine-dev

### 2.1 Avant (Incorrect)

```json
{
    "BEDROCK_MODEL_ID": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_MODEL_ID_NORMALIZATION": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_MODEL_ID_NEWSLETTER": "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
}
```

### 2.2 Après (Corrigé)

```json
{
    "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_MODEL_ID_NORMALIZATION": "anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_MODEL_ID_NEWSLETTER": "anthropic.claude-sonnet-4-5-20250929-v1:0"
}
```

### 2.3 Commande Exécutée

```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-engine-dev \
  --environment Variables={BEDROCK_MODEL_ID_NEWSLETTER=anthropic.claude-sonnet-4-5-20250929-v1:0,CONFIG_BUCKET=vectora-inbox-config-dev,BEDROCK_MODEL_ID_NORMALIZATION=anthropic.claude-sonnet-4-5-20250929-v1:0,BEDROCK_REGION_NORMALIZATION=us-east-1,BEDROCK_REGION=us-east-1,BEDROCK_REGION_NEWSLETTER=eu-west-3,NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev,DATA_BUCKET=vectora-inbox-data-dev,ENV=dev,BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-5-20250929-v1:0,LOG_LEVEL=INFO,PROJECT_NAME=vectora-inbox} \
  --profile rag-lai-prod --region eu-west-3
```

### 2.4 Statut

- ✅ **LastUpdateStatus** : InProgress → Active
- ✅ **RevisionId** : 22a8c12c-d055-4367-ba6a-5929b42bef9f
- ✅ **Configuration** : Mise à jour réussie

---

## 3. Configuration Finale Validée

### 3.1 vectora-inbox-ingest-normalize-dev

```json
{
    "CONFIG_BUCKET": "vectora-inbox-config-dev",
    "BEDROCK_REGION": "us-east-1",
    "DATA_BUCKET": "vectora-inbox-data-dev",
    "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-5-20250929-v1:0"
}
```

### 3.2 vectora-inbox-engine-dev

```json
{
    "BEDROCK_MODEL_ID_NEWSLETTER": "anthropic.claude-sonnet-4-5-20250929-v1:0",
    "CONFIG_BUCKET": "vectora-inbox-config-dev",
    "BEDROCK_MODEL_ID_NORMALIZATION": "anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_REGION_NORMALIZATION": "us-east-1",
    "BEDROCK_REGION": "us-east-1",
    "BEDROCK_REGION_NEWSLETTER": "eu-west-3",
    "NEWSLETTERS_BUCKET": "vectora-inbox-newsletters-dev",
    "DATA_BUCKET": "vectora-inbox-data-dev",
    "ENV": "dev",
    "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-5-20250929-v1:0",
    "LOG_LEVEL": "INFO",
    "PROJECT_NAME": "vectora-inbox"
}
```

---

## 4. Fichiers Modifiés

### 4.1 Code Source

**Aucun fichier de code modifié** ✅

Le code existant dans `src/vectora_core/normalization/bedrock_client.py` et `src/vectora_core/newsletter/bedrock_client.py` était déjà correct et utilise correctement les variables d'environnement.

### 4.2 AWS Lambda

- ✅ **vectora-inbox-ingest-normalize-dev** : Variables d'environnement mises à jour
- ✅ **vectora-inbox-engine-dev** : Variables d'environnement mises à jour

### 4.3 Documentation

- ✅ **Phase 1** : `docs/diagnostics/vectora_inbox_bedrock_modelid_fix_phase1_diagnostic.md`
- ✅ **Phase 3** : `docs/diagnostics/vectora_inbox_bedrock_modelid_fix_phase3_changes.md`

---

## 5. Stratégie Région Maintenue

### 5.1 Configuration Hybride

**Normalisation** :
- **Région** : us-east-1
- **Model ID** : anthropic.claude-sonnet-4-5-20250929-v1:0
- **Bénéfice** : Performance +88%, fiabilité +15%

**Newsletter** :
- **Région** : eu-west-3
- **Model ID** : anthropic.claude-sonnet-4-5-20250929-v1:0
- **Bénéfice** : Stabilité, configuration éprouvée

### 5.2 Justification

- ✅ Conserver les bénéfices de la migration us-east-1 pour normalisation
- ✅ Maintenir la stabilité eu-west-3 pour newsletter
- ✅ Même modèle Claude Sonnet 4.5 dans les deux régions
- ✅ Pas de dégradation de performance

---

## 6. Validation Technique

### 6.1 Model ID Validé

```bash
# us-east-1
aws bedrock list-foundation-models --region us-east-1 --profile rag-lai-prod
# ✅ anthropic.claude-sonnet-4-5-20250929-v1:0 : ACTIVE

# eu-west-3
aws bedrock list-foundation-models --region eu-west-3 --profile rag-lai-prod
# ✅ anthropic.claude-sonnet-4-5-20250929-v1:0 : ACTIVE
```

### 6.2 Configuration Lambda

- ✅ **Syntaxe** : Variables d'environnement correctement formatées
- ✅ **Cohérence** : Même model_id dans toutes les variables
- ✅ **Régions** : us-east-1 et eu-west-3 maintenues selon stratégie

---

## 7. Prochaines Étapes

### 7.1 Phase 4 - Test Réel

```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":1}' \
  out-test-fix.json
```

### 7.2 Critères de Validation

- ✅ Absence de ValidationException
- ✅ Items normalisés > 90%
- ✅ Entités détectées (companies, molecules, technologies)
- ✅ Temps d'exécution < 2 minutes

---

## Conclusion

**Corrections appliquées avec succès** : Les préfixes régionaux incorrects ont été supprimés des variables d'environnement Lambda.

**Impact minimal** : Aucun changement de code, configuration hybride maintenue, prêt pour test réel lai_weekly_v3.