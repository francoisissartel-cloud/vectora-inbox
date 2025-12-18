# Guide d'Invocation Lambda : Matching V2

**Lambda :** `vectora-inbox-normalize-score-v2-dev`  
**Région :** `eu-west-3`  
**Profil AWS :** `rag-lai-prod`

---

## 🎯 Objectif

Ce guide fournit les instructions pour invoquer la Lambda normalize_score_v2 depuis Windows, Linux ou Mac, en contournant les problèmes d'encodage JSON de l'AWS CLI sous Windows.

---

## 🚀 Méthode Recommandée : Script Python boto3

### Depuis Windows (PowerShell)

**1. Configurer les variables d'environnement**
```powershell
$env:AWS_PROFILE = "rag-lai-prod"
$env:AWS_DEFAULT_REGION = "eu-west-3"
```

**2. Exécuter le script**
```powershell
# Test avec lai_weekly_v3 (défaut)
python .\scripts\invoke_normalize_score_v2_lambda.py

# Test avec client spécifique
python .\scripts\invoke_normalize_score_v2_lambda.py --client-id lai_weekly_v3

# Test en mode diagnostic (logs détaillés)
python .\scripts\invoke_normalize_score_v2_lambda.py --diagnostic

# Auto-scan tous les clients actifs
python .\scripts\invoke_normalize_score_v2_lambda.py --auto-scan
```

**3. Interpréter les résultats**

Le script affiche :
- ✅ StatusCode (200 = succès)
- ✅ Présence/absence d'erreur Lambda
- ✅ Métriques clés : items_input, items_matched, items_scored
- ✅ Taux de matching (%)
- ✅ Distribution par domaine

**Exemple de sortie réussie :**
```
🚀 Invocation Lambda: vectora-inbox-normalize-score-v2-dev
📍 Région: eu-west-3
📦 Payload: {
  "client_id": "lai_weekly_v3"
}
------------------------------------------------------------
📊 StatusCode: 200
✅ Pas d'erreur Lambda
------------------------------------------------------------
📈 Métriques clés:
  • Items input: 15
  • Items matched: 12
  • Items scored: 15
  • Taux de matching: 80.0%

📊 Distribution par domaine:
  • tech_lai_ecosystem: 10 items
  • regulatory_lai: 5 items
------------------------------------------------------------
✅ SUCCÈS : Lambda exécutée avec succès
🎯 Matching opérationnel : 12 items matchés
```

---

### Depuis Linux/Mac (bash)

**1. Configurer les variables d'environnement**
```bash
export AWS_PROFILE=rag-lai-prod
export AWS_DEFAULT_REGION=eu-west-3
```

**2. Exécuter le script**
```bash
# Test avec lai_weekly_v3 (défaut)
python scripts/invoke_normalize_score_v2_lambda.py

# Test avec client spécifique
python scripts/invoke_normalize_score_v2_lambda.py --client-id lai_weekly_v3

# Test en mode diagnostic
python scripts/invoke_normalize_score_v2_lambda.py --diagnostic

# Auto-scan tous les clients
python scripts/invoke_normalize_score_v2_lambda.py --auto-scan
```

---

## 🔧 Méthode Alternative : AWS CLI avec Fichier Payload

### Depuis Windows (PowerShell)

**1. Créer le fichier payload (si pas déjà fait)**

Le fichier `scripts/payloads/normalize_score_lai_weekly_v3.json` contient :
```json
{
  "client_id": "lai_weekly_v3"
}
```

**2. Invoquer avec AWS CLI**
```powershell
aws lambda invoke `
  --function-name vectora-inbox-normalize-score-v2-dev `
  --cli-binary-format raw-in-base64-out `
  --payload fileb://scripts/payloads/normalize_score_lai_weekly_v3.json `
  --region eu-west-3 `
  --profile rag-lai-prod `
  response.json
```

**3. Afficher la réponse**
```powershell
Get-Content response.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

### Depuis Linux/Mac (bash)

**1. Invoquer avec AWS CLI**
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://scripts/payloads/normalize_score_lai_weekly_v3.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response.json
```

**2. Afficher la réponse**
```bash
cat response.json | jq .
```

---

## 📊 Analyse des Logs CloudWatch

### Accéder aux Logs

**Via Console AWS :**
1. Ouvrir CloudWatch : https://eu-west-3.console.aws.amazon.com/cloudwatch/
2. Aller dans "Log groups"
3. Chercher : `/aws/lambda/vectora-inbox-normalize-score-v2-dev`
4. Sélectionner le dernier log stream

**Via AWS CLI :**
```bash
# Lister les log streams récents
aws logs describe-log-streams \
  --log-group-name /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --order-by LastEventTime \
  --descending \
  --max-items 5 \
  --region eu-west-3 \
  --profile rag-lai-prod

# Afficher les logs d'un stream
aws logs get-log-events \
  --log-group-name /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --log-stream-name <LOG_STREAM_NAME> \
  --region eu-west-3 \
  --profile rag-lai-prod
```

---

### Patterns de Succès à Rechercher

**1. Configuration chargée**
```
"Configuration matching chargée depuis client_config"
"matching_config trouvé pour client lai_weekly_v3"
```

**2. Seuils appliqués**
```
"Seuil appliqué pour domaine tech_lai_ecosystem: 0.30"
"Seuil appliqué pour domaine regulatory_lai: 0.20"
"Matching policy applied"
```

**3. Mode fallback activé**
```
"Mode fallback activé pour pure players"
"Fallback matching applied"
"Item matché via fallback: <item_id>"
```

**4. Métriques de matching**
```
"items_matched: 12"
"domain_statistics: {tech_lai_ecosystem: 10, regulatory_lai: 5}"
"matching_rate: 80.0%"
```

---

### Patterns d'Erreur à Surveiller

**1. Configuration non trouvée**
```
"Configuration matching non trouvée, utilisation des défauts"
"Fallback sur seuils par défaut (0.4)"
```
→ Vérifier que `s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml` existe

**2. Aucun item matché**
```
"items_matched: 0"
"Aucun domaine matché pour tous les items"
```
→ Vérifier les seuils dans la configuration

**3. Erreur Bedrock**
```
"Erreur appel Bedrock"
"ThrottlingException"
```
→ Vérifier les quotas Bedrock

---

## ✅ Critères de Validation

### Succès Attendu

**Métriques :**
- ✅ StatusCode: 200
- ✅ Pas de FunctionError
- ✅ items_matched >= 10 (66%+)
- ✅ Distribution équilibrée tech/regulatory
- ✅ Mode fallback utilisé pour pure players

**Logs :**
- ✅ "Configuration matching chargée"
- ✅ "Seuil appliqué pour domaine"
- ✅ "Mode fallback activé" (si applicable)
- ✅ "Matching policy applied"

---

### Échec Possible

**Métriques :**
- ❌ StatusCode != 200
- ❌ FunctionError présente
- ❌ items_matched = 0 (régression)
- ❌ Timeout Lambda

**Logs :**
- ❌ "Configuration matching non trouvée"
- ❌ "Erreur appel Bedrock"
- ❌ "Exception non gérée"

---

## 🔍 Troubleshooting

### Problème : "Unable to locate credentials"

**Cause :** Profil AWS non configuré

**Solution Windows :**
```powershell
$env:AWS_PROFILE = "rag-lai-prod"
```

**Solution Linux/Mac :**
```bash
export AWS_PROFILE=rag-lai-prod
```

---

### Problème : "items_matched = 0"

**Cause possible 1 :** Configuration non chargée

**Solution :**
1. Vérifier que `lai_weekly_v3.yaml` existe sur S3
2. Vérifier les logs : "Configuration matching chargée"

**Cause possible 2 :** Seuils trop élevés

**Solution :**
1. Baisser `min_domain_score` de 0.25 → 0.20
2. Activer `enable_fallback_mode: true`
3. Re-uploader la configuration sur S3
4. Re-tester

---

### Problème : "Too many items matched" (> 15)

**Cause :** Seuils trop bas

**Solution :**
1. Augmenter `min_domain_score` de 0.25 → 0.30
2. Désactiver `enable_fallback_mode` temporairement
3. Ajouter `require_high_confidence_for_multiple: true`
4. Re-uploader la configuration sur S3
5. Re-tester

---

### Problème : "ThrottlingException Bedrock"

**Cause :** Quotas Bedrock dépassés

**Solution :**
1. Attendre quelques minutes
2. Vérifier les quotas Bedrock dans la console AWS
3. Demander une augmentation de quota si nécessaire

---

## 📝 Résumé : Comment Tester en 3 Étapes

### Étape 1 : Configurer l'environnement (1 fois)

**Windows :**
```powershell
$env:AWS_PROFILE = "rag-lai-prod"
$env:AWS_DEFAULT_REGION = "eu-west-3"
```

**Linux/Mac :**
```bash
export AWS_PROFILE=rag-lai-prod
export AWS_DEFAULT_REGION=eu-west-3
```

---

### Étape 2 : Invoquer la Lambda

```bash
python scripts/invoke_normalize_score_v2_lambda.py
```

---

### Étape 3 : Vérifier les résultats

**Dans la sortie du script :**
- ✅ StatusCode: 200
- ✅ items_matched >= 10

**Dans CloudWatch (optionnel) :**
- ✅ "Configuration matching chargée"
- ✅ "Matching policy applied"

---

**C'est tout ! 🎉**

Si items_matched >= 10 et StatusCode = 200, le matching V2 configuration-driven fonctionne correctement.
