# Plan de Correction Critique : Bedrock V2 & Chemins S3

**Date** : 16 janvier 2025  
**Objectif** : Fixer les problèmes P0 identifiés dans le diagnostic lai_weekly_v3  
**Scope** : Bedrock inaccessible + Chemins S3 incorrects  
**Contraintes** : Respecter src_lambda_hygiene_v4.md, architecture 3 Lambdas V2  

---

## Phase 0 – Analyse Comparative V1 vs V2

### 0.1 Différences Critiques Identifiées

**Bedrock V1 (fonctionnel) :**
- ✅ Utilise `anthropic_version: "bedrock-2023-05-31"`
- ✅ Format Messages API correct avec `messages[]`
- ✅ Gestion robuste des erreurs avec codes spécifiques
- ✅ Retry intelligent sur `ThrottlingException`
- ✅ Parsing JSON avec extraction `content[0].text`

**Bedrock V2 (défaillant) :**
- ❌ Erreur "Paramètres Bedrock invalides" systématique
- ❌ Possible problème de format de requête
- ❌ Bug de slicing dans préparation exemples canoniques
- ❌ Gestion d'erreurs moins robuste

**Chemins S3 V2 :**
- ❌ Écrit dans `ingested/` au lieu de `curated/`
- ❌ Écrase les données d'ingestion

### 0.2 Hypothèses de Causes Racines

1. **Format requête Bedrock** : V2 utilise un format différent de V1
2. **Modèle indisponible** : `anthropic.claude-3-5-sonnet-20241022-v2:0` n'existe pas
3. **Permissions IAM** : Lambda V2 n'a pas les bonnes permissions
4. **Bug technique** : Erreur de slicing empêche construction du prompt

---

## Phase 1 – Diagnostic Bedrock Approfondi

### 1.1 Vérification Modèle Disponible

**Objectif :** Confirmer si le modèle configuré existe en us-east-1

**Actions :**
```bash
# Lister les modèles Bedrock disponibles
aws bedrock list-foundation-models --region us-east-1 --profile rag-lai-prod \
  --query "modelSummaries[?contains(modelId, 'anthropic.claude')]" --output table

# Vérifier le modèle spécifique
aws bedrock get-foundation-model --model-identifier "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --region us-east-1 --profile rag-lai-prod
```

**Critères de succès :**
- Modèle existe et est `ACTIVE`
- Permissions suffisantes pour y accéder

**Si échec :** Identifier un modèle alternatif fonctionnel

### 1.2 Vérification Permissions IAM

**Objectif :** S'assurer que la Lambda V2 a accès à Bedrock

**Actions :**
```bash
# Récupérer le rôle IAM de la Lambda
aws lambda get-function --function-name vectora-inbox-normalize-score-v2-dev \
  --profile rag-lai-prod --region eu-west-3 \
  --query "Configuration.Role"

# Vérifier les politiques attachées
aws iam list-attached-role-policies --role-name [ROLE_NAME] \
  --profile rag-lai-prod

# Vérifier les permissions Bedrock
aws iam simulate-principal-policy --policy-source-arn [ROLE_ARN] \
  --action-names "bedrock:InvokeModel" \
  --resource-arns "arn:aws:bedrock:us-east-1::foundation-model/*" \
  --profile rag-lai-prod
```

**Critères de succès :**
- Rôle a `bedrock:InvokeModel` sur les modèles
- Pas de `Deny` explicite

### 1.3 Test Bedrock Minimal

**Objectif :** Tester l'accès Bedrock avec un appel minimal

**Actions :**
- Créer un script de test simple
- Utiliser le même format que V1 (fonctionnel)
- Tester depuis l'environnement Lambda

**Script de test :**
```python
import boto3
import json

def test_bedrock_minimal():
    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    
    # Format V1 (fonctionnel)
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "temperature": 0.0,
        "messages": [
            {
                "role": "user",
                "content": "Say hello in JSON format: {\"message\": \"hello\"}"
            }
        ]
    }
    
    try:
        response = client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            body=json.dumps(body)
        )
        print("SUCCESS:", response)
        return True
    except Exception as e:
        print("ERROR:", str(e))
        return False
```

---

## Phase 2 – Correction Bug Technique V2

### 2.1 Fix Bug de Slicing

**Problème identifié :**
```python
# Erreur dans normalizer.py ligne 222
technologies.extend(scope_technologies[:15])  # scope_technologies est un dict, pas une liste
```

**Correction :**
```python
# Convertir dict en liste avant slicing
if isinstance(scope_technologies, dict):
    scope_technologies = list(scope_technologies.values())
technologies.extend(scope_technologies[:15])
```

**Fichier à modifier :** `src_v2/vectora_core/normalization/normalizer.py`

### 2.2 Alignement Format Bedrock V1

**Objectif :** Utiliser exactement le même format que V1 (fonctionnel)

**Modifications dans `bedrock_client.py` :**
1. Copier la logique de `_call_bedrock_with_retry` de V1
2. Utiliser le même format de requête
3. Même parsing de réponse
4. Même gestion d'erreurs

**Changements spécifiques :**
- `anthropic_version: "bedrock-2023-05-31"` (obligatoire)
- Format `messages[]` exact
- Extraction `content[0].text` identique
- Codes d'erreur spécifiques (`ThrottlingException`, `ValidationException`)

### 2.3 Correction Chemins S3

**Problème :** normalize_score V2 écrit dans `ingested/` au lieu de `curated/`

**Correction dans `data_manager.py` :**
```python
# Ancien (incorrect)
output_path = f"ingested/{client_id}/{run_date}/items.json"

# Nouveau (correct)
output_path = f"curated/{client_id}/{run_date}/items.json"
```

**Impact :** Séparation claire des layers S3 selon l'architecture

---

## Phase 3 – Implémentation des Corrections

### 3.1 Ordre d'Exécution

1. **Fix bug de slicing** (bloquant)
2. **Alignement format Bedrock** (critique)
3. **Correction chemins S3** (important)
4. **Test intégration** (validation)

### 3.2 Modifications Minimales

**Principe :** Changer uniquement ce qui est nécessaire, pas de refactoring

**Fichiers à modifier :**
- `src_v2/vectora_core/normalization/normalizer.py` : Fix slicing
- `src_v2/vectora_core/normalization/bedrock_client.py` : Format V1
- `src_v2/vectora_core/normalization/data_manager.py` : Chemins S3

**Fichiers à NE PAS modifier :**
- Handlers Lambda (conformes)
- Architecture générale
- Configuration client_config/canonical

### 3.3 Validation Conformité Hygiène V4

**Vérifications obligatoires :**
- ✅ Aucune dépendance tierce ajoutée
- ✅ Imports relatifs respectés
- ✅ Généricité maintenue
- ✅ Variables d'environnement standardisées
- ✅ Taille handlers < 5MB

---

## Phase 4 – Tests et Validation

### 4.1 Tests Unitaires

**Test 1 : Bug de slicing corrigé**
```python
def test_canonical_examples_preparation():
    # Tester avec dict (cas problématique)
    scope_dict = {"key1": "value1", "key2": "value2"}
    result = prepare_canonical_examples({"technologies": scope_dict})
    assert isinstance(result["technologies"], list)
```

**Test 2 : Format Bedrock correct**
```python
def test_bedrock_request_format():
    client = BedrockNormalizationClient("test-model", "us-east-1")
    body = client._build_request_body("test prompt")
    assert body["anthropic_version"] == "bedrock-2023-05-31"
    assert "messages" in body
```

### 4.2 Test Intégration AWS

**Objectif :** Valider le fix end-to-end sur lai_weekly_v3

**Commande :**
```bash
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload '{"client_id": "lai_weekly_v3"}' \
  --profile rag-lai-prod --region eu-west-3 \
  response_fixed.json
```

**Critères de succès :**
- ✅ Aucune erreur "Paramètres Bedrock invalides"
- ✅ Au moins 1 item matché (matching_success_rate > 0)
- ✅ Scores > 0 pour items LAI pertinents
- ✅ Données écrites dans `curated/` pas `ingested/`

### 4.3 Métriques de Validation

**Seuils minimaux acceptables :**
- Taux de succès Bedrock : > 80%
- Taux de matching : > 20%
- Items avec score > 0 : > 30%
- Temps d'exécution : < 30s (vs 51.8s actuel)

---

## Phase 5 – Déploiement et Monitoring

### 5.1 Stratégie de Déploiement

**Approche :** Déploiement direct (pas de blue/green pour fix critique)

**Étapes :**
1. Package Lambda avec corrections
2. Update function code
3. Test immédiat post-déploiement
4. Rollback si échec critique

### 5.2 Monitoring Post-Déploiement

**Métriques à surveiller :**
- Taux d'erreur Lambda (< 5%)
- Latence moyenne (< 30s)
- Coût Bedrock (cohérent avec volume)
- Logs d'erreur CloudWatch

**Alertes :**
- Échec Bedrock > 50% → Investigation immédiate
- Timeout Lambda → Augmenter timeout ou optimiser
- Coût anormal → Vérifier retry loops

---

## Phase 6 – Validation Qualité

### 6.1 Audit Échantillon

**Objectif :** Valider la qualité des résultats après fix

**Méthode :**
1. Prendre 5-10 items du dernier run
2. Vérifier entités extraites vs contenu source
3. Valider matching aux domaines LAI
4. Contrôler cohérence des scores

**Critères qualité :**
- Entités cohérentes : > 80%
- Matching logique : > 70%
- Scores cohérents : > 70%

### 6.2 Comparaison Avant/Après

| Métrique | Avant Fix | Après Fix (Cible) |
|----------|-----------|-------------------|
| Succès Bedrock | 0% | > 80% |
| Items matchés | 0 | > 3 |
| Score moyen | 0.0 | > 5.0 |
| Temps exécution | 51.8s | < 30s |

---

## Résumé Exécutif du Plan

### Problèmes P0 Identifiés
1. **Bedrock inaccessible** : Format de requête incompatible + bug de slicing
2. **Chemins S3 incorrects** : Écrasement des données d'ingestion

### Solutions Minimales
1. **Alignement format V1** : Copier la logique Bedrock fonctionnelle
2. **Fix bug technique** : Conversion dict→list avant slicing
3. **Correction chemins** : Écriture dans `curated/` au lieu de `ingested/`

### Critères de Succès
- ✅ Bedrock accessible (> 80% succès)
- ✅ Matching fonctionnel (> 20% items)
- ✅ Scores cohérents (> 0 pour items LAI)
- ✅ Séparation S3 layers respectée

**Prochaine étape :** Exécution Phase 1 (Diagnostic Bedrock)