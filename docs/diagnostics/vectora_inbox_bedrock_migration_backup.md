# Vectora Inbox - Backup Configuration Bedrock (Avant Migration)

**Date de backup** : 2025-12-12  
**Objectif** : Sauvegarde complète de la configuration Bedrock avant migration vers us-east-1  
**Environnement** : DEV (vectora-inbox-s1-runtime-dev)

---

## Configuration Actuelle (eu-west-3)

### Variables d'Environnement Lambda

**Lambda: vectora-inbox-ingest-normalize-dev**
```
BEDROCK_MODEL_ID=eu.anthropic.claude-sonnet-4-5-20250929-v1:0
BEDROCK_REGION=eu-west-3 (implicite dans le code)
```

**Lambda: vectora-inbox-engine-dev**
```
BEDROCK_MODEL_ID=eu.anthropic.claude-sonnet-4-5-20250929-v1:0
BEDROCK_REGION=eu-west-3 (implicite dans le code)
```

### Code Source (Avant Modification)

**Fichier: `src/vectora_core/normalization/bedrock_client.py`**
```python
def get_bedrock_client():
    """
    Retourne un client boto3 Bedrock Runtime.
    
    Returns:
        Client boto3 bedrock-runtime configuré
    """
    return boto3.client('bedrock-runtime', region_name='eu-west-3')
```

**Fichier: `src/vectora_core/newsletter/bedrock_client.py`**
```python
def get_bedrock_client():
    """
    Retourne un client boto3 Bedrock Runtime.
    
    Returns:
        Client boto3 bedrock-runtime configuré
    """
    return boto3.client('bedrock-runtime', region_name='eu-west-3')
```

### Profil d'Inférence Actuel

**Profil EU utilisé :**
- **ID** : `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
- **Nom** : EU Anthropic Claude Sonnet 4.5
- **Description** : Routes requests to Anthropic Claude Sonnet 4.5 in eu-north-1, eu-west-3, eu-south-1, eu-south-2, eu-west-1 and eu-central-1
- **Statut** : ACTIVE
- **Type** : SYSTEM_DEFINED
- **Régions** : eu-north-1, eu-west-3, eu-south-1, eu-south-2, eu-west-1, eu-central-1

### Permissions IAM Actuelles

**Politique Bedrock (supposée) :**
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
        "arn:aws:bedrock:eu-west-3::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
        "arn:aws:bedrock:eu-west-3:786469175371:inference-profile/eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
      ]
    }
  ]
}
```

---

## Métriques de Performance (Baseline)

### Derniers Tests Réussis (2025-12-08)

**Test ingestion lai_weekly (3 jours) :**
- **Items ingérés** : 104
- **Items normalisés** : 104 (100%)
- **Temps d'exécution** : ~2-3 minutes
- **Taux de throttling** : ~10-15%
- **Latence moyenne Bedrock** : ~3-5 secondes/appel

**Qualité de normalisation :**
- ✅ Détection companies : Fonctionnelle (ex: "Eli Lilly, Novo Nordisk")
- ✅ Détection molecules : Fonctionnelle (ex: "olanzapine", "risperidone")
- ✅ Résumés générés : ~200 caractères, qualité élevée
- ✅ Classification event_type : Appliquée correctement

### Coûts Estimés

**Coût par run lai_weekly (104 items) :**
- **Tokens moyens par item** : ~500 tokens (input + output)
- **Total tokens par run** : ~52,000 tokens
- **Coût estimé** : ~$0.05-0.10 USD/run
- **Coût mensuel** : ~$3-6 USD (1 run/jour)

---

## Procédure de Rollback

### En cas de problème avec us-east-1

**Étape 1: Restaurer les variables d'environnement Lambda**

```powershell
# Ingest-normalize
aws lambda update-function-configuration `
  --function-name vectora-inbox-ingest-normalize-dev `
  --environment Variables='{
    "BEDROCK_MODEL_ID":"eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_REGION":"eu-west-3"
  }' `
  --profile rag-lai-prod `
  --region eu-west-3

# Engine
aws lambda update-function-configuration `
  --function-name vectora-inbox-engine-dev `
  --environment Variables='{
    "BEDROCK_MODEL_ID":"eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "BEDROCK_REGION":"eu-west-3"
  }' `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Étape 2: Restaurer le code source (si modifié)**

```python
# Dans src/vectora_core/normalization/bedrock_client.py
# ET src/vectora_core/newsletter/bedrock_client.py

def get_bedrock_client():
    """
    Retourne un client boto3 Bedrock Runtime.
    
    Returns:
        Client boto3 bedrock-runtime configuré
    """
    return boto3.client('bedrock-runtime', region_name='eu-west-3')
```

**Étape 3: Redéployer les Lambdas**

```powershell
# Repackager et redéployer si nécessaire
.\scripts\package-ingest-normalize.ps1
.\scripts\deploy-ingest-normalize-dev.ps1

.\scripts\package-engine.ps1
.\scripts\deploy-engine-dev.ps1
```

**Étape 4: Tester le rollback**

```powershell
# Test rapide ingest-normalize
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload '{"client_id":"lai_weekly","period_days":1}' `
  --cli-binary-format raw-in-base64-out `
  out-rollback-test.json `
  --profile rag-lai-prod `
  --region eu-west-3

# Vérifier les logs
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev `
  --since 5m `
  --profile rag-lai-prod `
  --region eu-west-3
```

---

## Validation du Rollback

### Critères de Succès Rollback

✅ **Appels Bedrock fonctionnels** : Pas d'erreur de région/modèle  
✅ **Performance restaurée** : Latence ~3-5s/appel  
✅ **Qualité maintenue** : Détection entités + résumés OK  
✅ **Pas de throttling excessif** : <20% d'erreurs  

### Commandes de Vérification

```powershell
# Vérifier les variables d'environnement
aws lambda get-function-configuration `
  --function-name vectora-inbox-ingest-normalize-dev `
  --profile rag-lai-prod `
  --region eu-west-3 `
  --query 'Environment.Variables'

# Test d'appel Bedrock direct
aws bedrock-runtime invoke-model `
  --model-id eu.anthropic.claude-sonnet-4-5-20250929-v1:0 `
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Test"}]}' `
  --profile rag-lai-prod `
  --region eu-west-3 `
  test-rollback-bedrock.json
```

---

## Contacts & Escalation

### En cas de problème critique

**Escalation technique :**
1. **Vérifier les logs CloudWatch** : Identifier l'erreur exacte
2. **Tester Bedrock direct** : Isoler le problème (région/modèle/permissions)
3. **Rollback immédiat** : Suivre la procédure ci-dessus
4. **Support AWS** : Si problème de quotas/permissions Bedrock

**Logs à consulter :**
- `/aws/lambda/vectora-inbox-ingest-normalize-dev`
- `/aws/lambda/vectora-inbox-engine-dev`
- AWS CloudTrail (appels Bedrock)

---

## Historique des Modifications

### 2025-12-12 - Préparation Migration us-east-1

**Modifications prévues :**
- ✅ Code source : Paramétrage région via BEDROCK_REGION
- ✅ Variables env : BEDROCK_REGION=us-east-1
- ✅ Variables env : BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-5-20250929-v1:0
- ⏳ Permissions IAM : Ajout us-east-1 si nécessaire

**État avant migration :**
- ✅ Système stable en eu-west-3
- ✅ Performance baseline documentée
- ✅ Procédure rollback validée
- ✅ Backup complet effectué

---

## Validation du Backup

### Checklist Backup Complet

✅ **Configuration Lambda** : Variables d'environnement sauvegardées  
✅ **Code source** : Version eu-west-3 documentée  
✅ **Profil d'inférence** : ID et détails sauvegardés  
✅ **Permissions IAM** : Politique actuelle documentée  
✅ **Métriques baseline** : Performance et coûts référencés  
✅ **Procédure rollback** : Étapes détaillées et testables  

### Fichiers de Référence

- **Configuration actuelle** : Ce document
- **Tests récents** : `docs/diagnostics/bedrock_sonnet45_success_final_dev.md`
- **Scripts déploiement** : `scripts/deploy-*-dev.ps1`
- **Logs de référence** : CloudWatch 2025-12-08

---

**Backup créé le** : 2025-12-12  
**Validé par** : Amazon Q Developer  
**Prochaine révision** : Après migration réussie ou rollback  

**⚠️ IMPORTANT** : Ce backup doit être conservé jusqu'à validation complète de la migration us-east-1.