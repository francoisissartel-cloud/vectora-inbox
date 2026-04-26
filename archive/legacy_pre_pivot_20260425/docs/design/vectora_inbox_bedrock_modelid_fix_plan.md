# Vectora Inbox - Plan Correction Bedrock "Model Identifier Invalid"

**Date** : 2025-12-12  
**Problème** : ValidationException: The provided model identifier is invalid  
**Contexte** : lai_weekly_v3 - Normalisation échoue à 100%  
**Objectif** : Diagnostic + correction minimale + test réel

---

## Phase 1 – Diagnostic détaillé model_id / région

### Objectifs
- Identifier la cause racine du "model identifier invalid"
- Vérifier alignement code/env vars/région Bedrock

### Actions
1. **Inspection code Bedrock** :
   - `src/vectora_core/bedrock/bedrock_client.py` : région + model_id
   - Variables d'environnement lues (BEDROCK_MODEL_ID, BEDROCK_REGION)
   - Différences normalisation vs newsletter

2. **Vérification env vars Lambdas** :
   - `vectora-inbox-ingest-normalize-dev` : BEDROCK_MODEL_ID actuel
   - `vectora-inbox-engine-dev` : configuration Bedrock
   - Comparaison avec modèles disponibles

3. **Test disponibilité modèles** :
   ```bash
   aws bedrock list-foundation-models --region us-east-1 --profile rag-lai-prod
   aws bedrock list-foundation-models --region eu-west-3 --profile rag-lai-prod
   ```

### Fichiers touchés
- Lecture : `src/vectora_core/bedrock/bedrock_client.py`
- Documentation : `docs/diagnostics/vectora_inbox_bedrock_modelid_fix_phase1_diagnostic.md`

### Tests
- Vérification model_id dans liste modèles disponibles
- Validation région effective vs région configurée

---

## Phase 2 – Proposition modèle cible & stratégie

### ✅ SOLUTION IDENTIFIÉE

**Problème** : Préfixes régionaux incorrects (`us.` et `eu.`) dans les model_id
**Solution** : Utiliser le model_id standard sans préfixe

### Modèle Cible

**Model ID Standard** : `anthropic.claude-sonnet-4-5-20250929-v1:0`
- ✅ Disponible dans us-east-1
- ✅ Disponible dans eu-west-3
- ✅ Même modèle, performance identique
- ✅ Pas de préfixe régional requis

### Stratégie Région

**Configuration Hybride Maintenue** :
- **Normalisation** : us-east-1 (performance +88%)
- **Newsletter** : eu-west-3 (stabilité)
- **Justification** : Conserver bénéfices migration récente

### Changements Minimaux

1. **vectora-inbox-ingest-normalize-dev** :
   ```json
   {
     "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-5-20250929-v1:0"
   }
   ```

2. **vectora-inbox-engine-dev** :
   ```json
   {
     "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-5-20250929-v1:0",
     "BEDROCK_MODEL_ID_NORMALIZATION": "anthropic.claude-sonnet-4-5-20250929-v1:0",
     "BEDROCK_MODEL_ID_NEWSLETTER": "anthropic.claude-sonnet-4-5-20250929-v1:0"
   }
   ```

### Fichiers touchés
- ✅ **Code** : Aucun changement requis
- ✅ **AWS** : Variables d'environnement Lambda uniquement

### Tests
- ✅ Model_id validé dans us-east-1 et eu-west-3
- ✅ Même modèle Claude Sonnet 4.5 conservé

---

## Phase 3 – Application corrections (code + AWS)

### Objectifs
- Corriger code pour utiliser modèle valide
- Mettre à jour env vars Lambdas
- Déploiement sans impact métier

### Actions
1. **Modifications code** :
   - `src/vectora_core/bedrock/bedrock_client.py` : région + model_id
   - Centralisation configuration Bedrock
   - Pas de changement logique métier

2. **Mise à jour Lambdas** :
   ```bash
   aws lambda update-function-configuration \
     --function-name vectora-inbox-ingest-normalize-dev \
     --environment Variables='{BEDROCK_MODEL_ID="nouveau-modele"}' \
     --profile rag-lai-prod --region eu-west-3
   ```

3. **Validation déploiement** :
   - Test invocation simple Lambda
   - Vérification logs absence ValidationException

### Fichiers touchés
- Code : `src/vectora_core/bedrock/bedrock_client.py`
- AWS : env vars `vectora-inbox-ingest-normalize-dev`
- Documentation : `docs/diagnostics/vectora_inbox_bedrock_modelid_fix_phase3_changes.md`

### Tests
- Invocation Lambda sans payload métier
- Validation client Bedrock fonctionne

---

## Phase 4 – Test réel lai_weekly_v3

### Objectifs
- Valider correction avec workflow complet
- Confirmer normalisation fonctionne
- Mesurer performance

### Actions
1. **Test normalisation** :
   ```bash
   aws lambda invoke \
     --function-name vectora-inbox-ingest-normalize-dev \
     --payload '{"client_id":"lai_weekly_v3","period_days":1}' \
     --profile rag-lai-prod --region eu-west-3 \
     out-test-fix.json
   ```

2. **Validation résultats** :
   - Nombre items scrappés vs normalisés
   - Présence entités (companies, molecules, technologies)
   - Absence ValidationException
   - Temps d'exécution

### Fichiers touchés
- Documentation : `docs/diagnostics/vectora_inbox_bedrock_modelid_fix_phase4_results.md`

### Tests
- Run complet lai_weekly_v3 période courte
- Vérification qualité normalisation
- Mesure performance

---

## Phase 5 – Synthèse & recommandations

### Objectifs
- Documenter cause racine + solution
- Recommandations amélioration continue
- Impact MVP

### Actions
1. **Résumé exécutif** :
   - Cause racine ValidationException
   - Solution appliquée
   - Impact performance/coût

2. **Recommandations** :
   - Monitoring modèles Bedrock
   - Stratégie région long terme
   - Optimisations futures

### Fichiers touchés
- Documentation : `docs/diagnostics/vectora_inbox_bedrock_modelid_fix_executive_summary.md`

### Tests
- Validation solution durable
- Recommandations actionnables

---

## Critères de Succès

✅ **Technique** :
- Normalisation lai_weekly_v3 fonctionne
- 0% ValidationException
- Items normalisés > 90%

✅ **Business** :
- Entités détectées (Nanexa, UZEDY®)
- Workflow complet ingestion → normalisation
- Performance acceptable (<2 minutes)

✅ **Documentation** :
- Cause racine identifiée
- Solution documentée
- Recommandations P1/P2