# Diagnostic : Tentative d'activation de Claude Sonnet 4.5 - Environnement DEV

## Résumé exécutif

**Date/heure du test** : 2025-12-08 13:06 UTC  
**Environnement** : DEV (compte 786469175371, région eu-west-3)  
**Objectif** : Migrer vers Claude Sonnet 4.5 (Amazon Bedrock Edition) comme modèle par défaut  
**Statut** : ❌ **ÉCHEC - Model ID invalide**

---

## Contexte de la migration

### Modèle cible
- **Nom** : Claude Sonnet 4.5 (Amazon Bedrock Edition)
- **Model ID testé (incorrect)** : `anthropic.claude-sonnet-4-5-v2:0`  
**Model ID correct** : `anthropic.claude-sonnet-4-5-20250929-v1:0`
- **Région** : eu-west-3 (Paris)

### Modèle précédent
- **Nom** : Claude 3 Sonnet
- **Model ID** : `anthropic.claude-3-sonnet-20240229-v1:0`
- **Statut** : Fonctionnel mais nécessite une souscription AWS Marketplace

---

## Résultats du test

### Déploiement de l'infrastructure
✅ **Stack CloudFormation mise à jour avec succès**
- Stack : `vectora-inbox-s1-runtime-dev`
- Paramètre `BedrockModelId` : `anthropic.claude-sonnet-4-5-v2:0`
- Variable d'environnement `BEDROCK_MODEL_ID` : Correctement configurée dans les deux Lambdas

### Test de la Lambda ingest-normalize
✅ **Lambda invoquée avec succès** (StatusCode 200)
- Fonction : `vectora-inbox-ingest-normalize-dev`
- Payload : `{"client_id":"lai_weekly","period_days":7}`
- Temps d'exécution : 18.09 secondes
- Items ingérés : 104 items depuis 7 sources

❌ **Erreurs Bedrock : Model ID invalide**
- Erreur : `ValidationException: The provided model identifier is invalid`
- Nombre d'erreurs : 104 (une par item à normaliser)
- Impact : Aucune normalisation Bedrock effectuée

### Analyse des logs CloudWatch

**Erreur répétée 104 fois** :
```
[ERROR] Erreur lors de l'appel à Bedrock: An error occurred (ValidationException) 
when calling the InvokeModel operation: The provided model identifier is invalid.
```

**Comportement observé** :
- L'ingestion des sources fonctionne correctement (104 items récupérés)
- Chaque appel à Bedrock échoue avec la même erreur de validation
- Le pipeline continue malgré les erreurs (fallback sur normalisation sans Bedrock)
- Le fichier `normalized/lai_weekly/2025/12/08/items.json` est créé avec succès

---

## Diagnostic du problème

### Cause probable : Model ID incorrect

Le model ID `anthropic.claude-sonnet-4-5-v2:0` n'est **pas valide** pour Amazon Bedrock dans la région eu-west-3.

**Hypothèses** :
1. **Le modèle n'existe pas encore** : Claude Sonnet 4.5 n'est peut-être pas encore disponible sur Amazon Bedrock
2. **Nom de modèle incorrect** : Le format du model ID pourrait être différent (ex: `anthropic.claude-sonnet-4-5-20250101-v1:0`)
3. **Région non supportée** : Le modèle pourrait ne pas être disponible dans eu-west-3
4. **Accès non activé** : Le modèle pourrait nécessiter une activation préalable dans la console Bedrock

### Vérifications nécessaires

Pour identifier le bon model ID, il faut :

1. **Consulter la console AWS Bedrock** :
   - Aller dans AWS Console > Bedrock > Model access
   - Vérifier les modèles disponibles dans eu-west-3
   - Identifier le model ID exact pour Claude Sonnet 4.5 (si disponible)

2. **Vérifier la documentation AWS** :
   - https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html
   - Rechercher "Claude Sonnet 4.5" ou "Claude 4.5"
   - Vérifier la disponibilité régionale

3. **Tester avec AWS CLI** :
   ```powershell
   # Lister les modèles disponibles
   aws bedrock list-foundation-models --profile rag-lai-prod --region eu-west-3
   
   # Filtrer pour Claude Sonnet
   aws bedrock list-foundation-models --profile rag-lai-prod --region eu-west-3 --query "modelSummaries[?contains(modelId, 'claude-sonnet')]"
   ```

---

## Impact sur le système

### Fonctionnalités affectées
- ❌ **Normalisation Bedrock** : Extraction d'entités, classification d'événements, génération de résumés
- ✅ **Ingestion** : Fonctionne correctement (104 items récupérés)
- ✅ **Écriture S3** : Fichier normalized créé avec succès
- ⚠️ **Qualité des données** : Items normalisés sans enrichissement Bedrock (champs vides)

### Données produites
- **Fichier S3** : `s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/12/08/items.json`
- **Taille** : 60 188 caractères
- **Contenu** : 104 items avec structure de base mais sans enrichissement Bedrock

---

## Actions correctives recommandées

### Option 1 : Identifier le bon model ID pour Claude Sonnet 4.5

**Si Claude Sonnet 4.5 existe sur Bedrock** :
1. Identifier le model ID exact via la console ou AWS CLI
2. Mettre à jour `infra/s1-runtime.yaml` avec le bon model ID
3. Redéployer la stack s1-runtime-dev
4. Retester la Lambda ingest-normalize

### Option 2 : Revenir temporairement à Claude 3 Sonnet

**Si Claude Sonnet 4.5 n'est pas encore disponible** :
1. Revenir au model ID `anthropic.claude-3-sonnet-20240229-v1:0`
2. Activer l'accès au modèle via AWS Marketplace (si nécessaire)
3. Redéployer la stack s1-runtime-dev
4. Planifier la migration vers Claude Sonnet 4.5 quand il sera disponible

### Option 3 : Utiliser un autre modèle Claude disponible

**Si un modèle Claude plus récent est disponible** :
1. Identifier les modèles Claude disponibles dans eu-west-3
2. Choisir le modèle le plus performant (ex: Claude 3.5 Sonnet si disponible)
3. Mettre à jour l'infrastructure et la documentation
4. Redéployer et tester

---

## Commandes de diagnostic

### Lister les modèles Bedrock disponibles

```powershell
# Tous les modèles
aws bedrock list-foundation-models --profile rag-lai-prod --region eu-west-3

# Modèles Claude uniquement
aws bedrock list-foundation-models --profile rag-lai-prod --region eu-west-3 --query "modelSummaries[?contains(modelId, 'claude')].[modelId, modelName]" --output table

# Modèles Claude Sonnet uniquement
aws bedrock list-foundation-models --profile rag-lai-prod --region eu-west-3 --query "modelSummaries[?contains(modelId, 'claude-sonnet')].[modelId, modelName]" --output table
```

### Vérifier l'accès aux modèles

```powershell
# Vérifier l'accès au modèle
aws bedrock get-foundation-model --model-identifier anthropic.claude-sonnet-4-5-v2:0 --profile rag-lai-prod --region eu-west-3
```

### Rollback vers Claude 3 Sonnet

```powershell
# Redéployer avec l'ancien modèle
aws cloudformation deploy `
  --template-file infra/s1-runtime.yaml `
  --stack-name vectora-inbox-s1-runtime-dev `
  --parameter-overrides BedrockModelId=anthropic.claude-3-sonnet-20240229-v1:0 `
  --capabilities CAPABILITY_NAMED_IAM `
  --profile rag-lai-prod `
  --region eu-west-3
```

---

## Résolution du problème

### Model ID correct identifié

Après vérification via AWS CLI, le bon model ID pour Claude Sonnet 4.5 est :
- **`anthropic.claude-sonnet-4-5-20250929-v1:0`**

### Modèles Claude disponibles dans eu-west-3

| Model ID | Nom | Disponibilité |
|----------|-----|---------------|
| `anthropic.claude-sonnet-4-5-20250929-v1:0` | Claude Sonnet 4.5 | ✅ Disponible |
| `anthropic.claude-opus-4-5-20251101-v1:0` | Claude Opus 4.5 | ✅ Disponible |
| `anthropic.claude-haiku-4-5-20251001-v1:0` | Claude Haiku 4.5 | ✅ Disponible |
| `anthropic.claude-sonnet-4-20250514-v1:0` | Claude Sonnet 4 | ✅ Disponible |
| `anthropic.claude-3-7-sonnet-20250219-v1:0` | Claude 3.7 Sonnet | ✅ Disponible |
| `anthropic.claude-3-5-sonnet-20240620-v1:0` | Claude 3.5 Sonnet | ✅ Disponible |
| `anthropic.claude-3-sonnet-20240229-v1:0` | Claude 3 Sonnet | ✅ Disponible |

## Prochaines étapes

1. ✅ **Model ID correct identifié** : `anthropic.claude-sonnet-4-5-20250929-v1:0`
2. ✅ **Documentation mise à jour** avec le model ID correct
3. ⏳ **Redéployer l'infrastructure** avec le bon model ID
4. ⏳ **Retester la Lambda ingest-normalize** pour valider la normalisation Bedrock
5. ⏳ **Mettre à jour le diagnostic** avec les résultats du test final

---

## Conclusion

La tentative de migration vers Claude Sonnet 4.5 a échoué en raison d'un **model ID invalide**. Le système continue de fonctionner (ingestion + écriture S3) mais sans l'enrichissement Bedrock (normalisation).

**Action immédiate requise** : Identifier le bon model ID pour Claude Sonnet 4.5 ou choisir un modèle Claude alternatif disponible dans eu-west-3.

**Recommandation** : Consulter la console AWS Bedrock et la documentation officielle pour identifier les modèles Claude disponibles dans la région eu-west-3 avant de poursuivre la migration.
