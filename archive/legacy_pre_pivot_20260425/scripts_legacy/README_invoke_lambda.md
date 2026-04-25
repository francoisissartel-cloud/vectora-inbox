# Script d'Invocation Lambda - Matching V2

## 🎯 Objectif

Script Python pour invoquer `vectora-inbox-normalize-score-v2-dev` sans les problèmes d'encodage JSON de l'AWS CLI sous Windows.

---

## 🚀 Usage Rapide

### Windows (PowerShell)
```powershell
$env:AWS_PROFILE = "rag-lai-prod"
$env:AWS_DEFAULT_REGION = "eu-west-3"
python .\scripts\invoke_normalize_score_v2_lambda.py
```

### Linux/Mac (bash)
```bash
export AWS_PROFILE=rag-lai-prod
export AWS_DEFAULT_REGION=eu-west-3
python scripts/invoke_normalize_score_v2_lambda.py
```

---

## 📋 Options

```bash
# Test avec lai_weekly_v3 (défaut)
python scripts/invoke_normalize_score_v2_lambda.py

# Test avec client spécifique
python scripts/invoke_normalize_score_v2_lambda.py --client-id lai_weekly_v3

# Mode diagnostic (logs détaillés)
python scripts/invoke_normalize_score_v2_lambda.py --diagnostic

# Auto-scan tous les clients
python scripts/invoke_normalize_score_v2_lambda.py --auto-scan
```

---

## 📊 Sortie Attendue

```
🚀 Invocation Lambda: vectora-inbox-normalize-score-v2-dev
📍 Région: eu-west-3
📦 Payload: {"client_id": "lai_weekly_v3"}
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

## 📚 Documentation Complète

Voir : `docs/diagnostics/matching_v2_lambda_invocation_howto.md`

---

## 🔧 Alternative : AWS CLI avec Fichier Payload

```powershell
# Windows PowerShell
aws lambda invoke `
  --function-name vectora-inbox-normalize-score-v2-dev `
  --cli-binary-format raw-in-base64-out `
  --payload fileb://scripts/payloads/normalize_score_lai_weekly_v3.json `
  --region eu-west-3 `
  --profile rag-lai-prod `
  response.json
```

---

## ✅ Prérequis

- Python 3.x
- boto3 (installé avec AWS CLI)
- Profil AWS `rag-lai-prod` configuré
- Accès Lambda dans `eu-west-3`
