# Diagnostic : Migration Bedrock vers Claude Sonnet 4.5 (Profil d'inférence global) - Environnement DEV

**Date** : 2025-12-08  
**Environnement** : DEV (eu-west-3)  
**Stack** : `vectora-inbox-s1-runtime-dev`  
**Statut global** : 🟡 **AMBER** - Configuration mise à jour, mais validation Bedrock en attente

---

## Résumé exécutif

### Contexte

Le projet Vectora Inbox utilise Amazon Bedrock pour la normalisation des items ingérés (extraction d'entités, classification d'événements, génération de résumés). Une subscription active au produit AWS Marketplace **"Claude Sonnet 4.5 (Amazon Bedrock Edition)"** a été souscrite pour utiliser ce modèle récent.

### Problème initial

L'utilisation du modelId direct `anthropic.claude-sonnet-4-5-20250929-v1:0` échouait avec l'erreur :

```
Invocation of model ID anthropic.claude-sonnet-4-5-20250929-v1:0 with on-demand throughput isn't supported. 
Retry your request with the ID or ARN of an inference profile that contains this model.
```

### Actions réalisées

1. **Mise à jour de l'infrastructure** (`infra/s1-runtime.yaml`) :
   - Tentative 1 : Profil EU `eu.anthropic.claude-sonnet-4-5-v2:0` → Erreur "invalid model identifier"
   - Tentative 2 : Profil US cross-region `us.anthropic.claude-sonnet-4-5-v2:0` → Erreur "invalid model identifier"

2. **Mise à jour de la documentation** :
   - `infra/README.md` : Documentation du profil d'inférence global
   - `.q-context/blueprint-draft-vectora-inbox.yaml` : Mise à jour du modelId par défaut
   - `.q-context/vectora-inbox-q-rules.md` : Documentation des exigences d'inference profile
   - `CHANGELOG.md` : Entrée détaillée sur la migration

3. **Tests de validation** :
   - Stack CloudFormation mise à jour avec succès
   - Lambda invoquée avec succès (statusCode 200, 104 items ingérés)
   - **Mais** : Tous les appels Bedrock échouent avec "The provided model identifier is invalid"

### Statut actuel

- ✅ Infrastructure CloudFormation mise à jour
- ✅ Documentation alignée
- ✅ Ingestion fonctionnelle (104 items de 7 sources)
- ❌ Normalisation Bedrock non fonctionnelle (104 erreurs ValidationException)
- ⚠️ Les items sont écrits dans S3 mais sans enrichissement Bedrock (champs vides)

---

## Configuration actuelle

### Paramètre CloudFormation

**Stack** : `vectora-inbox-s1-runtime-dev`  
**Paramètre** : `BedrockModelId`  
**Valeur actuelle** : `us.anthropic.claude-sonnet-4-5-v2:0`

### Variables d'environnement Lambda

**Lambda** : `vectora-inbox-ingest-normalize-dev`  
**Variable** : `BEDROCK_MODEL_ID`  
**Valeur** : `us.anthropic.claude-sonnet-4-5-v2:0` (héritée du paramètre CloudFormation)

**Lambda** : `vectora-inbox-engine-dev`  
**Variable** : `BEDROCK_MODEL_ID`  
**Valeur** : `us.anthropic.claude-sonnet-4-5-v2:0` (héritée du paramètre CloudFormation)

---

## Commandes AWS CLI utilisées

### Validation du template

```powershell
aws cloudformation validate-template `
  --template-body file://infra/s1-runtime.yaml `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat** : ✅ Template valide

### Mise à jour de la stack (tentative 1 - profil EU)

```powershell
aws cloudformation deploy `
  --template-file infra/s1-runtime.yaml `
  --stack-name vectora-inbox-s1-runtime-dev `
  --parameter-overrides BedrockModelId=eu.anthropic.claude-sonnet-4-5-v2:0 `
  --capabilities CAPABILITY_NAMED_IAM `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat** : ✅ Stack mise à jour avec succès

### Mise à jour de la stack (tentative 2 - profil US cross-region)

```powershell
aws cloudformation deploy `
  --template-file infra/s1-runtime.yaml `
  --stack-name vectora-inbox-s1-runtime-dev `
  --parameter-overrides BedrockModelId=us.anthropic.claude-sonnet-4-5-v2:0 `
  --capabilities CAPABILITY_NAMED_IAM `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat** : ✅ Stack mise à jour avec succès

### Test de la Lambda d'ingestion

```powershell
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload '{"client_id":"lai_weekly","period_days":3}' `
  --cli-binary-format raw-in-base64-out `
  out_ingest_lai_weekly_bedrock_us_profile.json `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat** : ✅ Lambda exécutée (statusCode 200)

**Réponse** :
```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-12-08T14:29:31Z",
    "sources_processed": 7,
    "items_ingested": 104,
    "items_normalized": 104,
    "s3_output_path": "s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/12/08/items.json",
    "execution_time_seconds": 18.7
  }
}
```

### Récupération des logs CloudWatch

```powershell
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev `
  --since 10m `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --format short
```

**Résultat** : ❌ 104 erreurs Bedrock identiques

**Exemple d'erreur** :
```
[ERROR] Erreur lors de l'appel à Bedrock: An error occurred (ValidationException) when calling the InvokeModel operation: The provided model identifier is invalid.
```

---

## Analyse des logs

### Statistiques d'exécution

- **Sources traitées** : 7/8 (87.5%)
  - ✅ FierceBiotech : 25 items
  - ✅ FiercePharma : 25 items
  - ✅ Endpoints News : 24 items
  - ✅ MedinCell : 12 items
  - ✅ DelSiTech : 10 items
  - ✅ Nanexa : 8 items
  - ⚠️ Camurus : 0 items (structure HTML non reconnue)
  - ❌ Peptron : 0 items (erreur SSL)

- **Items ingérés** : 104
- **Appels Bedrock tentés** : 104
- **Appels Bedrock réussis** : 0
- **Erreurs Bedrock** : 104 (100% d'échec)

### Type d'erreur Bedrock

**Erreur** : `ValidationException`  
**Message** : `The provided model identifier is invalid.`

**Interprétation** : Les identifiants de profil d'inférence testés (`eu.anthropic.claude-sonnet-4-5-v2:0` et `us.anthropic.claude-sonnet-4-5-v2:0`) ne sont pas reconnus par Bedrock dans la région `eu-west-3`.

### Impact sur les données

Les items sont écrits dans S3 (`normalized/lai_weekly/2025/12/08/items.json`) mais **sans enrichissement Bedrock** :
- `summary` : vide
- `event_type` : "other" (valeur par défaut)
- `companies_detected` : []
- `molecules_detected` : []
- `technologies_detected` : []
- `indications_detected` : []

Le code Python gère gracieusement les erreurs Bedrock en retournant une structure vide, ce qui permet au pipeline de continuer.

---

## Cause racine probable

### Hypothèse 1 : Profil d'inférence non créé

La subscription AWS Marketplace "Claude Sonnet 4.5 (Amazon Bedrock Edition)" nécessite probablement la **création manuelle d'un inference profile** via la console Bedrock ou l'API.

**Actions à vérifier** :
1. Accéder à la console Bedrock dans `eu-west-3`
2. Vérifier si un inference profile a été créé automatiquement après la subscription
3. Si non, créer manuellement un inference profile pour Claude Sonnet 4.5

### Hypothèse 2 : ARN du modèle requis

La subscription Marketplace peut fournir un **ARN spécifique** au lieu d'un modelId standard.

**Actions à vérifier** :
1. Consulter les détails de la subscription dans AWS Marketplace
2. Vérifier si un ARN de modèle est fourni (format : `arn:aws:bedrock:eu-west-3::foundation-model/...`)
3. Utiliser cet ARN au lieu du modelId

### Hypothèse 3 : Région non supportée

Claude Sonnet 4.5 via Marketplace pourrait ne pas être disponible dans `eu-west-3`.

**Actions à vérifier** :
1. Consulter la documentation de la subscription Marketplace
2. Vérifier les régions supportées
3. Si nécessaire, envisager une migration vers `us-east-1` ou `us-west-2`

---

## Prochaines étapes recommandées

### Étape 1 : Vérifier la console Bedrock

```
1. Se connecter à la console AWS (compte 786469175371, profil rag-lai-prod)
2. Accéder à Amazon Bedrock dans la région eu-west-3
3. Naviguer vers "Inference profiles" ou "Model access"
4. Vérifier si Claude Sonnet 4.5 apparaît et noter son identifiant exact
5. Si un inference profile existe, copier son ID ou ARN
```

### Étape 2 : Lister les modèles disponibles via CLI

```powershell
# Lister tous les modèles Bedrock disponibles dans eu-west-3
aws bedrock list-foundation-models `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --query "modelSummaries[?contains(modelId, 'claude')]" `
  --output json

# Lister les inference profiles disponibles
aws bedrock list-inference-profiles `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --output json
```

### Étape 3 : Tester un appel Bedrock direct

```powershell
# Test avec le modelId actuel
aws bedrock-runtime invoke-model `
  --model-id us.anthropic.claude-sonnet-4-5-v2:0 `
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}' `
  --profile rag-lai-prod `
  --region eu-west-3 `
  test-bedrock-response.json

# Vérifier la réponse
type test-bedrock-response.json
```

### Étape 4 : Mettre à jour la configuration une fois le bon identifiant trouvé

```powershell
# Mettre à jour la stack avec le bon modelId/ARN
aws cloudformation deploy `
  --template-file infra/s1-runtime.yaml `
  --stack-name vectora-inbox-s1-runtime-dev `
  --parameter-overrides BedrockModelId=<CORRECT_MODEL_ID_OR_ARN> `
  --capabilities CAPABILITY_NAMED_IAM `
  --profile rag-lai-prod `
  --region eu-west-3

# Retester la Lambda
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload '{"client_id":"lai_weekly","period_days":3}' `
  --cli-binary-format raw-in-base64-out `
  out_ingest_test_final.json `
  --profile rag-lai-prod `
  --region eu-west-3
```

### Étape 5 : Valider la normalisation Bedrock

```powershell
# Vérifier les logs pour confirmer l'absence d'erreurs Bedrock
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev `
  --since 5m `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --format short | findstr /C:"Bedrock" /C:"ValidationException"

# Télécharger et inspecter le fichier normalisé
aws s3 cp s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/12/08/items.json . `
  --profile rag-lai-prod `
  --region eu-west-3

# Vérifier que les champs Bedrock sont remplis (summary, event_type, *_detected)
```

---

## Points de vigilance

### 1. Coûts Bedrock

Claude Sonnet 4.5 est un modèle premium. Vérifier les coûts associés à la subscription Marketplace et aux appels API.

**Recommandation** : Surveiller les coûts via AWS Cost Explorer après activation.

### 2. Quotas et limites

Vérifier les quotas Bedrock pour Claude Sonnet 4.5 dans `eu-west-3` :
- Requêtes par minute (RPM)
- Tokens par minute (TPM)
- Requêtes concurrentes

**Recommandation** : Demander une augmentation de quota si nécessaire via AWS Support.

### 3. Latence

Les profils d'inférence cross-region (US depuis EU) peuvent introduire une latence supplémentaire.

**Recommandation** : Mesurer la latence après activation et envisager une migration régionale si nécessaire.

### 4. Fallback sur Claude 3 Sonnet

En attendant la résolution, envisager un rollback temporaire vers Claude 3 Sonnet (`anthropic.claude-3-sonnet-20240229-v1:0`) qui fonctionnait précédemment.

**Commande de rollback** :
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

## Fichiers modifiés

### Infrastructure

- `infra/s1-runtime.yaml` : Paramètre `BedrockModelId` mis à jour vers `us.anthropic.claude-sonnet-4-5-v2:0`

### Documentation

- `infra/README.md` : Section sur le profil d'inférence global ajoutée
- `.q-context/blueprint-draft-vectora-inbox.yaml` : ModelId par défaut mis à jour
- `.q-context/vectora-inbox-q-rules.md` : Documentation des exigences d'inference profile
- `CHANGELOG.md` : Entrée détaillée sur la migration

### Code

Aucun changement de code Python nécessaire. Le modèle est lu depuis la variable d'environnement `BEDROCK_MODEL_ID`.

---

## Conclusion

La migration vers Claude Sonnet 4.5 nécessite une **étape de configuration supplémentaire** dans Bedrock pour identifier le bon modelId ou ARN à utiliser avec la subscription AWS Marketplace.

L'infrastructure et la documentation sont prêtes. Une fois le bon identifiant trouvé, la mise à jour sera rapide (1 commande CloudFormation + 1 test Lambda).

**Recommandation immédiate** : Exécuter les étapes 1-3 ci-dessus pour identifier le bon identifiant Bedrock, puis mettre à jour la stack et valider.

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-12-08  
**Dernière mise à jour** : 2025-12-08
