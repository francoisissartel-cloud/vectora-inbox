# Plan de Contournement : Blocage AWS CLI Windows - Matching V2

**Date :** 17 décembre 2025  
**Objectif :** Débloquer définitivement la validation production du matching V2

---

## Phase 1 – Analyse

### État Actuel des Tests

**Tests locaux :** ✅ Validés avec succès
- Script : `scripts/test_matching_v2_config_driven.py`
- Résultats : 100% matching rate avec configuration fallback
- Rapport : `docs/diagnostics/matching_v2_config_driven_local_tests.md`

**Déploiement AWS :** ✅ Réussi
- Lambda : `vectora-inbox-normalize-score-v2-dev`
- Package : 67KB, Status: Active
- Configuration : `s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml`

**Tests production :** ❌ Bloqués
- Problème : Encodage payload JSON AWS CLI sous Windows
- Tentatives échouées : Échappement guillemets, encodage UTF-8/UTF-16
- Impact : Impossible de valider le déploiement

### Problèmes d'Encodage Identifiés

**Windows PowerShell :**
```powershell
# ❌ Échoue : guillemets mal échappés
aws lambda invoke --payload '{"client_id": "lai_weekly_v3"}' ...

# ❌ Échoue : encodage UTF-16 par défaut
aws lambda invoke --payload "{\"client_id\": \"lai_weekly_v3\"}" ...
```

**Windows cmd.exe :**
```cmd
REM ❌ Échoue : échappement différent de Unix
aws lambda invoke --payload "{\"client_id\": \"lai_weekly_v3\"}" ...
```

---

## Phase 2 – Nouveau Chemin de Test

### Solution Recommandée : Script Python boto3

**Avantages :**
- ✅ Pas de problème d'encodage (JSON natif Python)
- ✅ Fonctionne sur Windows/Linux/Mac
- ✅ Paramétrable via arguments CLI
- ✅ Réutilisable pour tous les tests futurs
- ✅ Pas de nouvelle dépendance (boto3 standard AWS)

**Architecture :**
```
scripts/
  └── invoke_normalize_score_v2_lambda.py   # Script d'invocation
      ├── Utilise boto3.client("lambda")
      ├── Construit event JSON proprement
      ├── Affiche résultats lisibles
      └── Gère les erreurs AWS
```

**Fonctionnalités :**
1. Invocation Lambda avec boto3
2. Payload JSON configurable :
   - Par défaut : `{"client_id": "lai_weekly_v3"}`
   - Argument CLI : `--client-id <id>`
   - Mode diagnostic : `--diagnostic`
3. Affichage résultats :
   - StatusCode / FunctionError
   - Résumé payload réponse
   - Métriques clés (items_matched, etc.)

---

## Phase 3 – Intégration avec Configuration Existante

### Passage du client_id

**Mode 1 : Client spécifique (défaut)**
```python
event = {"client_id": "lai_weekly_v3"}
```

**Mode 2 : Auto-scan**
```python
event = {}  # Lambda scanne tous les clients actifs
```

**Mode 3 : Diagnostic**
```python
event = {
    "client_id": "lai_weekly_v3",
    "diagnostic": True
}
```

### Lecture de la Configuration

Le script **ne lit pas** la configuration YAML directement :
- Configuration déjà uploadée sur S3
- Lambda lit automatiquement depuis S3
- Script se contente de passer le client_id

---

## Phase 4 – Instructions d'Usage

### Depuis Windows (PowerShell)

**Prérequis :**
```powershell
# Configurer le profil AWS
$env:AWS_PROFILE = "rag-lai-prod"
$env:AWS_DEFAULT_REGION = "eu-west-3"
```

**Commandes :**
```powershell
# Test avec lai_weekly_v3 (défaut)
python .\scripts\invoke_normalize_score_v2_lambda.py

# Test avec client spécifique
python .\scripts\invoke_normalize_score_v2_lambda.py --client-id lai_weekly_v3

# Test en mode diagnostic
python .\scripts\invoke_normalize_score_v2_lambda.py --diagnostic

# Auto-scan tous les clients
python .\scripts\invoke_normalize_score_v2_lambda.py --auto-scan
```

### Depuis Linux/Mac (bash)

**Prérequis :**
```bash
export AWS_PROFILE=rag-lai-prod
export AWS_DEFAULT_REGION=eu-west-3
```

**Commandes :**
```bash
# Test avec lai_weekly_v3 (défaut)
python scripts/invoke_normalize_score_v2_lambda.py

# Test avec client spécifique
python scripts/invoke_normalize_score_v2_lambda.py --client-id lai_weekly_v3
```

---

## Phase 5 – Validation

### Métriques à Vérifier

**1. Invocation Lambda réussie**
- StatusCode: 200
- Pas de FunctionError

**2. Métriques de matching**
- `items_matched > 0` (attendu : 10-12)
- `items_input` : 15
- Distribution par domaine équilibrée

**3. Logs CloudWatch**
- Groupe : `/aws/lambda/vectora-inbox-normalize-score-v2-dev`
- Patterns de succès :
  - "Configuration matching chargée"
  - "Mode fallback activé"
  - "Matching policy applied"

### Critères de Succès

✅ **Succès si :**
- items_matched >= 10 (66%+)
- Aucune erreur Lambda
- Distribution tech/regulatory équilibrée
- Mode fallback utilisé pour pure players

❌ **Échec si :**
- items_matched = 0 (régression)
- FunctionError présente
- Timeout Lambda

---

## Phase 6 – Optionnel : Commande AWS CLI Propre

### Fichier Payload

**Créer :** `scripts/payloads/normalize_score_lai_weekly_v3.json`
```json
{
  "client_id": "lai_weekly_v3"
}
```

### Commande AWS CLI Robuste

**Windows PowerShell :**
```powershell
aws lambda invoke `
  --function-name vectora-inbox-normalize-score-v2-dev `
  --cli-binary-format raw-in-base64-out `
  --payload fileb://scripts/payloads/normalize_score_lai_weekly_v3.json `
  --region eu-west-3 `
  --profile rag-lai-prod `
  response.json

# Afficher la réponse
Get-Content response.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Linux/Mac bash :**
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload fileb://scripts/payloads/normalize_score_lai_weekly_v3.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response.json

# Afficher la réponse
cat response.json | jq .
```

**Avantages :**
- Payload dans un fichier (pas d'échappement)
- `fileb://` lit le fichier en binaire
- `--cli-binary-format raw-in-base64-out` gère l'encodage proprement

---

## Synthèse d'Implémentation

### Fichiers à Créer

1. **Script Python :** `scripts/invoke_normalize_score_v2_lambda.py`
   - Invocation Lambda via boto3
   - Arguments CLI pour client_id, diagnostic, auto-scan
   - Affichage résultats lisibles

2. **Documentation :** `docs/diagnostics/matching_v2_lambda_invocation_howto.md`
   - Instructions Windows (PowerShell)
   - Instructions Linux/Mac (bash)
   - Exemples de commandes
   - Analyse des logs CloudWatch

3. **Payload optionnel :** `scripts/payloads/normalize_score_lai_weekly_v3.json`
   - Fichier JSON pour AWS CLI
   - Alternative au script Python

### Fichiers à Mettre à Jour

1. **Ce plan :** `docs/design/matching_v2_windows_cli_workaround_plan.md`
   - Section "Réalisation" avec ce qui a été fait
   - Différences par rapport au plan initial

2. **Rapport production :** `docs/diagnostics/matching_v2_config_driven_production_report.md`
   - Instructions pratiques pour tests Windows
   - Liste des fichiers créés
   - Résumé "comment tester en 3 étapes"

---

## Conformité

### Respect src_lambda_hygiene_v4.md

✅ **Aucune modification dans `/src` ou `/src_v2`**
- Moteur déployé et fonctionnel
- Pas de changement de code Lambda

✅ **Pas de nouvelle dépendance**
- boto3 déjà standard AWS
- Pas de lib exotique

✅ **Travail uniquement dans `/scripts` et `/docs`**
- Script d'invocation dans `/scripts`
- Documentation dans `/docs`

✅ **Simplicité et réutilisabilité**
- Script autonome < 150 lignes
- Bien commenté
- Réutilisable pour tous les clients

---

## Estimation

**Temps d'implémentation :** 30-40 minutes
- Phase 2 (Script Python) : 15 min
- Phase 4 (Documentation) : 10 min
- Phase 6 (Payload optionnel) : 5 min
- Synthèse finale : 10 min

**Temps de validation :** 5 minutes
- Exécution script : 1 min
- Analyse résultats : 2 min
- Vérification logs : 2 min

**Total :** 45 minutes pour déblocage définitif

---

## Réalisation

### Fichiers Créés

**1. Script Python d'invocation :** ✅
- `scripts/invoke_normalize_score_v2_lambda.py` (150 lignes)
- Invocation Lambda via boto3
- Arguments CLI : --client-id, --diagnostic, --auto-scan
- Affichage résultats lisibles avec métriques
- Gestion erreurs AWS

**2. Documentation complète :** ✅
- `docs/diagnostics/matching_v2_lambda_invocation_howto.md`
- Instructions Windows (PowerShell)
- Instructions Linux/Mac (bash)
- Analyse logs CloudWatch
- Troubleshooting complet

**3. Fichiers payload JSON :** ✅
- `scripts/payloads/normalize_score_lai_weekly_v3.json`
- `scripts/payloads/normalize_score_auto_scan.json`
- Pour usage AWS CLI alternatif

**4. Résumé du blocage :** ✅
- `docs/diagnostics/matching_v2_windows_cli_blocker_summary.md`
- Contexte, problème, contraintes, solution

**5. Ce plan :** ✅
- `docs/design/matching_v2_windows_cli_workaround_plan.md`
- Plan détaillé par phases
- Réalisation documentée

### Différences par Rapport au Plan Initial

**Aucune différence majeure :**
- ✅ Toutes les phases implémentées comme prévu
- ✅ Script Python autonome et bien commenté
- ✅ Documentation complète Windows/Linux/Mac
- ✅ Fichiers payload optionnels créés
- ✅ Respect strict des contraintes (pas de modification /src_v2)

**Ajouts mineurs :**
- ✅ Fichier payload auto-scan supplémentaire
- ✅ Section troubleshooting étendue dans la documentation
- ✅ Exemples de sortie du script dans le howto

### Conformité Finale

✅ **Aucune modification dans `/src` ou `/src_v2`**
✅ **Pas de nouvelle dépendance** (boto3 standard)
✅ **Travail uniquement dans `/scripts` et `/docs`**
✅ **Simplicité et réutilisabilité** (script < 150 lignes)
✅ **Respect src_lambda_hygiene_v4.md**

---

**Statut :** ✅ Implémentation complète - Prêt pour validation production
