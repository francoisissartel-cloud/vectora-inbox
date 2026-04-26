# Plan de Validation Production : Matching Bedrock V2

**Date :** 17 décembre 2025  
**Objectif :** Valider en production le matching Bedrock V2 corrigé  
**Durée estimée :** 1h30 (5 phases de 15-20 min chacune)  
**Environnement :** eu-west-3, profil rag-lai-prod, compte 786469175371

---

## Phase 0 – Cadrage et prérequis

### 0.1 Contexte technique validé

**Correction terminée :**
- ✅ Erreur d'import `_call_bedrock_with_retry` résolue
- ✅ API Bedrock unifiée `call_bedrock_with_retry()` créée
- ✅ Tests locaux 4/4 réussis
- ✅ Architecture V2 respectée (hygiene_v4 compliant)

**État actuel :**
- **Pipeline** : vectora-inbox-ingest-v2 → vectora-inbox-normalize-score-v2 → newsletter
- **Problème résolu** : Import cassé dans bedrock_matcher.py
- **Résultat attendu** : Taux de matching 0% → >0% sur lai_weekly_v3

### 0.2 Workflow Vectora Inbox préservé

**Architecture 3 Lambdas maintenue :**
- `vectora-inbox-ingest-v2` : Ingestion → S3 `ingested/` (inchangée)
- `vectora-inbox-normalize-score-v2` : Normalisation + matching → S3 `normalized/` (corrigée)
- `vectora-inbox-newsletter-v2` : Newsletter → S3 `newsletters/` (inchangée)

**Aucune modification du workflow :**
- Même événements d'entrée
- Mêmes buckets S3
- Même configuration client lai_weekly_v3
- Même variables d'environnement

### 0.3 Règles d'hygiène respectées

**Conformité src_lambda_hygiene_v4.md :**
- ✅ Aucune nouvelle dépendance externe
- ✅ Code dans src_v2/ uniquement
- ✅ Pas de duplication de libs
- ✅ API unifiée réutilisable
- ✅ Fonctions < 80 lignes
- ✅ Région eu-west-3 + profil rag-lai-prod

---

## Phase 1 – Déploiement du patch (20 min)

### 1.1 Validation pré-déploiement

**Vérifications obligatoires :**
```bash
# 1. Tests locaux finaux
python scripts/test_bedrock_matching_local.py

# 2. Vérification structure src_v2
ls -la src_v2/vectora_core/normalization/
# Attendu : bedrock_client.py, bedrock_matcher.py, normalizer.py

# 3. Validation taille package
du -sh src_v2/
# Attendu : < 50MB
```

### 1.2 Exécution du déploiement

**Script automatisé :**
```bash
python scripts/deploy_bedrock_matching_patch.py
```

**Vérifications post-déploiement :**
- ✅ Package créé : `bedrock-matching-patch-v2-YYYYMMDD-HHMMSS.zip`
- ✅ Lambda mise à jour : `vectora-inbox-normalize-score-v2`
- ✅ Variables d'environnement : `BEDROCK_REGION=us-east-1`, `BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0`
- ✅ Taille déployée : < 50MB
- ✅ Status Code : 200

### 1.3 Validation déploiement

**Test de sanité immédiat :**
```bash
aws lambda get-function --function-name vectora-inbox-normalize-score-v2 \
  --region eu-west-3 --profile rag-lai-prod
```

**Métriques attendues :**
- State : Active
- LastUpdateStatus : Successful
- CodeSize : < 50MB
- Runtime : python3.11

---

## Phase 2 – Test d'exécution normalize_score_v2 (25 min)

### 2.1 Préparation du test

**Payload de test lai_weekly_v3 :**
```json
{
  "client_id": "lai_weekly_v3",
  "period_days": 30
}
```

**Fichier de test :**
```bash
echo '{"client_id":"lai_weekly_v3","period_days":30}' > test_normalize_payload.json
```

### 2.2 Exécution du test

**Invocation Lambda :**
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2 \
  --payload file://test_normalize_payload.json \
  --region eu-west-3 --profile rag-lai-prod \
  response_normalize_test.json
```

### 2.3 Analyse de la réponse

**Vérifications obligatoires :**
```bash
# 1. Status Code de l'invocation
cat response_normalize_test.json | jq '.statusCode'
# Attendu : 200

# 2. Contenu de la réponse
cat response_normalize_test.json | jq '.body'
# Attendu : { items_normalized: X, items_matched: Y, ... }
```

**Métriques de succès :**
- `statusCode` : 200
- `items_normalized` : > 0
- `items_matched` : > 0 (OBJECTIF PRINCIPAL)
- `execution_time` : < 120 secondes
- Aucune erreur d'import dans les logs

---

## Phase 3 – Validation des logs CloudWatch (20 min)

### 3.1 Collecte des logs

**Commande de récupération :**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/vectora-inbox-normalize-score-v2 \
  --start-time $(date -d '10 minutes ago' +%s)000 \
  --region eu-west-3 --profile rag-lai-prod \
  --output table
```

### 3.2 Recherche de patterns critiques

**Patterns de succès à chercher :**
- `"Matching Bedrock V2"` - Logs du matching
- `"call_bedrock_with_retry"` - API unifiée utilisée
- `"matched_domains"` - Résultats de matching
- `"OK - Import"` - Pas d'erreur d'import

**Patterns d'erreur à éviter :**
- `"ImportError"` - Erreur d'import
- `"cannot import name"` - Import cassé
- `"_call_bedrock_with_retry"` suivi d'erreur
- `"ThrottlingException"` - Problème Bedrock

### 3.3 Analyse des métriques

**Métriques CloudWatch à vérifier :**
```bash
# Durée d'exécution
aws logs filter-log-events \
  --log-group-name /aws/lambda/vectora-inbox-normalize-score-v2 \
  --filter-pattern "Duration" \
  --start-time $(date -d '10 minutes ago' +%s)000 \
  --region eu-west-3 --profile rag-lai-prod
```

**Seuils acceptables :**
- Duration : < 120,000 ms
- Billed Duration : < 120,000 ms
- Memory Used : < 1024 MB
- Aucun timeout

---

## Phase 4 – Validation des résultats de matching (30 min)

### 4.1 Analyse des données S3

**Localisation des résultats :**
```bash
# Lister les fichiers normalisés récents
aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly_v3/ \
  --recursive --region eu-west-3 --profile rag-lai-prod
```

**Téléchargement du dernier run :**
```bash
# Identifier le fichier le plus récent
LATEST_FILE=$(aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly_v3/ \
  --recursive --region eu-west-3 --profile rag-lai-prod | \
  sort | tail -n 1 | awk '{print $4}')

# Télécharger
aws s3 cp s3://vectora-inbox-data-dev/$LATEST_FILE \
  latest_normalized_results.json \
  --region eu-west-3 --profile rag-lai-prod
```

### 4.2 Analyse du taux de matching

**Script d'analyse :**
```bash
# Compter les items avec matching
python -c "
import json
with open('latest_normalized_results.json', 'r') as f:
    data = json.load(f)
    
items = data.get('items', [])
total_items = len(items)
matched_items = 0

for item in items:
    matching_results = item.get('matching_results', {})
    matched_domains = matching_results.get('matched_domains', [])
    if len(matched_domains) > 0:
        matched_items += 1

print(f'Total items: {total_items}')
print(f'Matched items: {matched_items}')
print(f'Matching rate: {matched_items/total_items*100:.1f}%')
"
```

### 4.3 Validation qualitative

**Exemples d'items matchés :**
```bash
# Extraire les items matchés pour review
python -c "
import json
with open('latest_normalized_results.json', 'r') as f:
    data = json.load(f)

matched_examples = []
for item in data.get('items', []):
    matching_results = item.get('matching_results', {})
    if matching_results.get('matched_domains'):
        matched_examples.append({
            'title': item.get('title', '')[:100],
            'matched_domains': matching_results.get('matched_domains'),
            'entities': item.get('normalized_content', {}).get('entities', {})
        })

print(json.dumps(matched_examples[:3], indent=2))
"
```

**Critères de validation :**
- Au moins 1 item matché (taux > 0%)
- Domaines matchés cohérents : `tech_lai_ecosystem`, `regulatory_lai`
- Entités détectées pertinentes : MedinCell, Teva, olanzapine, etc.

---

## Phase 5 – Synthèse et rapport final (15 min)

### 5.1 Collecte des métriques finales

**Métriques techniques :**
- ✅ Déploiement réussi : Oui/Non
- ✅ Exécution sans erreur : Oui/Non
- ✅ Temps d'exécution : X secondes
- ✅ Taux de matching : X% (objectif >0%)

**Métriques métier :**
- Items normalisés : X
- Items matchés : X
- Domaines alimentés : tech_lai_ecosystem, regulatory_lai
- Exemples de matching réussi : X

### 5.2 Création du rapport de validation

**Fichier :** `docs/diagnostics/bedrock_matching_v2_production_validation_report.md`

**Contenu obligatoire :**
```markdown
# Validation Production : Matching Bedrock V2

## Résultats de validation
- Taux de matching : AVANT 0% → APRÈS X%
- Items traités : X
- Temps d'exécution : X secondes
- Erreurs : Aucune/X erreurs

## Exemples de matching réussi
[Items avec entités → domaines matchés]

## Recommandations
[Optimisations futures si nécessaire]
```

### 5.3 Décision finale

**Critères de succès :**
- ✅ Taux de matching > 0%
- ✅ Aucune erreur d'import
- ✅ Temps d'exécution acceptable
- ✅ Pipeline fonctionnel end-to-end

**Décisions possibles :**
- 🟢 **VALIDATION RÉUSSIE** : Matching fonctionnel, déploiement confirmé
- 🟡 **VALIDATION PARTIELLE** : Matching fonctionne mais optimisations nécessaires
- 🔴 **VALIDATION ÉCHOUÉE** : Problèmes critiques, rollback nécessaire

---

## Critères de succès et métriques

### Critères techniques obligatoires

| Critère | Seuil | Validation |
|---------|-------|------------|
| Déploiement | Succès | ✅/❌ |
| Import bedrock | Aucune erreur | ✅/❌ |
| Exécution Lambda | Status 200 | ✅/❌ |
| Temps d'exécution | < 120s | ✅/❌ |
| Taux de matching | > 0% | ✅/❌ |

### Critères métier souhaités

| Critère | Objectif | Validation |
|---------|----------|------------|
| Items matchés | ≥ 1 item | ✅/❌ |
| Domaines alimentés | ≥ 1 domaine | ✅/❌ |
| Qualité matching | Cohérent avec entités | ✅/❌ |
| Pas de régression | Normalisation OK | ✅/❌ |

### Plan de rollback

**Si validation échoue :**
1. Identifier la cause (logs CloudWatch)
2. Restaurer version précédente Lambda
3. Analyser et corriger le problème
4. Re-tester en local avant nouveau déploiement

---

## Commandes de validation rapide

```bash
# Séquence complète de validation
echo "=== Phase 1: Déploiement ==="
python scripts/deploy_bedrock_matching_patch.py

echo "=== Phase 2: Test exécution ==="
echo '{"client_id":"lai_weekly_v3","period_days":30}' > test_payload.json
aws lambda invoke --function-name vectora-inbox-normalize-score-v2 \
  --payload file://test_payload.json --region eu-west-3 --profile rag-lai-prod response.json
cat response.json | jq '.statusCode, .body.items_matched'

echo "=== Phase 3: Logs ==="
aws logs filter-log-events \
  --log-group-name /aws/lambda/vectora-inbox-normalize-score-v2 \
  --filter-pattern "Matching Bedrock" \
  --start-time $(date -d '5 minutes ago' +%s)000 \
  --region eu-west-3 --profile rag-lai-prod

echo "=== Validation terminée ==="
```

---

**Plan prêt pour exécution**  
**Durée estimée :** 1h30  
**Objectif :** Confirmer que le matching Bedrock V2 fonctionne en production