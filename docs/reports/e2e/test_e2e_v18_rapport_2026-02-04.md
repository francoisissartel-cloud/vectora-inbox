# Test E2E V18 - Workflow Fresh Data

**Date**: 2026-02-04  
**Client**: lai_weekly_v18  
**Environnement**: dev  
**Objectif**: Valider workflow complet avec données RSS fraîches (7 derniers jours)  
**Durée**: ~2h (incluant attente normalize-score)  

---

## Résumé Exécutif

**Verdict**: ❌ **ÉCHEC CRITIQUE** - Domain scoring Bedrock défaillant

Test workflow complet avec données RSS fraîches du 2026-02-04.

**Résultats clés**:
- ✅ Ingest: 31 items (identique V17)
- ✅ Normalisation: 77% companies détectées (> 74% V17)
- ❌ **Domain scoring: 0% items relevant** (attendu 64%)
- ❌ **Score moyen: 0.0** (attendu 71.5)
- ❌ **Tous items rejetés** (fallback)

**Cause racine**: Erreur Bedrock `ValidationException: cache_control not permitted`

**Décision**: **CORRECTIONS APPLIQUÉES** - Re-test requis après redéploiement

---

## Métriques Comparatives

| Métrique | V17 (Baseline) | V18 | Evolution | Cible | Statut |
|----------|----------------|-----|-----------|-------|--------|
| Items ingérés | 31 | 31 | 0 | 25-35 | ✅ |
| Domain scoring | 100% | 100% | 0% | 100% | ✅ |
| Companies | 74% | 77% | +3% | ≥70% | ✅ |
| Items relevant | 64% | **0%** | **-64%** | ≥60% | ❌ |
| Score moyen | 71.5 | **0.0** | **-71.5** | 65-85 | ❌ |
| Faux négatifs | 0 | **31** | **+31** | ≤1 | ❌ |

---

## Distribution Sources

| Source | Items | % |
|--------|-------|---|
| press_corporate__medincell | 8 | 26% |
| press_corporate__nanexa | 6 | 19% |
| press_sector__fiercepharma | 5 | 16% |
| press_sector__endpoints_news | 4 | 13% |
| press_corporate__delsitech | 4 | 13% |
| press_sector__fiercebiotech | 3 | 10% |
| press_corporate__camurus | 1 | 3% |

**Total**: 31 items de 7 sources (identique V17)

---

## Distribution Scores

| Plage | Nombre | % |
|-------|--------|---|
| 80-100 | 0 | 0% |
| 60-79 | 0 | 0% |
| 40-59 | 0 | 0% |
| 20-39 | 0 | 0% |
| 0-19 | 0 | 0% |
| **Rejetés (0)** | **31** | **100%** |

**Items relevant**: 0/31 (0%)  
**Items rejetés**: 31/31 (100%)

---

## Analyse Détaillée - Item Rejeté #1

**Titre**: Medincells Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension (TEV-749 / mdc-TJK) for the Once-Monthly Treatment of Schizophrenia in Adults

**Source**: press_corporate__medincell  
**Date**: 2025-12-09

### Normalisation (✅ OK)
- **Event Type**: N/A (non détecté)
- **Companies**: Medincell, Teva Pharmaceuticals
- **Molecules**: olanzapine
- **Technologies**: extended-release injectable suspension
- **Trademarks**: TEV-'749, mdc-TJK
- **Dosing Intervals**: once-monthly

### Domain Scoring (❌ ÉCHEC)
- **Is Relevant**: False
- **Score**: 0
- **Confidence**: low
- **Reasoning**: "Bedrock domain scoring failed - fallback to not relevant"
- **Signals**: Aucun (tous vides)

**Analyse**: Item parfait pour LAI (pure player + trademark + technology + dosing) mais **rejeté par fallback** car appel Bedrock échoue.

---

## Cause Racine

### Erreur Bedrock Identifiée

**Logs CloudWatch** (31 occurrences identiques):
```
[ERROR] Erreur Bedrock non-throttling (ValidationException): 
An error occurred (ValidationException) when calling the InvokeModel operation: 
messages.0.content.0.text.cache_control: Extra inputs are not permitted

[ERROR] Error in domain scoring: 
An error occurred (ValidationException) when calling the InvokeModel operation: 
messages.0.content.0.text.cache_control: Extra inputs are not permitted
```

### Diagnostic

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`  
**Méthode**: `invoke_with_prompt()` (lignes 367-368, 373-374)  
**Problème**: Utilisation de `cache_control: {type: "ephemeral"}` non supporté par le modèle Bedrock actuel

**Code problématique**:
```python
{
    "type": "text",
    "text": system_instructions,
    "cache_control": {"type": "ephemeral"}  # ← NON SUPPORTÉ
}
```

**Impact**: 
- Tous les appels domain scoring échouent
- Fallback à `is_relevant: false, score: 0`
- 100% des items rejetés

---

## Problèmes Secondaires Identifiés

### 1. Référence Obsolète lai_matching.yaml

**Fichier**: `src_v2/vectora_core/shared/config_loader.py`  
**Ligne**: 380-390  
**Problème**: Code charge hardcodé `lai_matching.yaml` qui n'existe plus (remplacé par `lai_domain_scoring.yaml`)

**Log**:
```
[ERROR] Erreur lors de la lecture de s3://vectora-inbox-config-dev/canonical/prompts/matching/lai_matching.yaml: 
An error occurred (NoSuchKey) when calling the GetObject operation: The specified key does not exist.

[WARNING] Impossible de charger canonical/prompts/matching/lai_matching.yaml
```

**Impact**: WARNING seulement (n'empêche pas l'exécution) mais indique incohérence architecture

---

## Corrections Appliquées

### Correction #1: Suppression cache_control

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`  
**Changement**: Suppression de `cache_control` dans `invoke_with_prompt()`

**Avant**:
```python
{
    "type": "text",
    "text": system_instructions,
    "cache_control": {"type": "ephemeral"}
}
```

**Après**:
```python
{
    "type": "text",
    "text": system_instructions
}
```

### Correction #2: Suppression référence lai_matching.yaml

**Fichier**: `src_v2/vectora_core/shared/config_loader.py`  
**Changement**: Suppression de la section `matching` dans `load_canonical_prompts()`

**Avant**:
```python
"matching": {
    "lai_matching": "canonical/prompts/matching/lai_matching.yaml"
},
```

**Après**: Section supprimée (lai_matching obsolète, remplacé par lai_domain_scoring)

---

## Validation Workflow

### ✅ Ce qui fonctionne

1. **Ingest-v2**
   - 31 items ingérés (7 sources)
   - Temps: 18.34s
   - Déduplication: 1 item
   - Filtrage: 0 item

2. **Normalisation Bedrock (1er appel)**
   - Companies: 77% détectées (24/31)
   - Technologies: Détectées correctement
   - Trademarks: Détectées correctement
   - Dosing intervals: Détectés correctement

3. **Configuration**
   - Client config V18 chargée OK
   - Scopes canonical chargés OK (22 scopes)
   - Prompts chargés OK (normalization, domain_scoring, editorial)

4. **Infrastructure**
   - Lambdas déployées et opérationnelles
   - S3 buckets accessibles
   - IAM permissions OK

### ❌ Ce qui ne fonctionne pas

1. **Domain Scoring Bedrock (2ème appel)**
   - 100% échec avec ValidationException
   - Fallback à rejected pour tous les items
   - 0% items relevant (attendu 64%)

2. **Cohérence Architecture**
   - Référence obsolète lai_matching.yaml
   - Code cherche fichier qui n'existe plus

---

## Prochaines Étapes

### Étape 1: Redéploiement (URGENT)

```bash
# 1. Build avec corrections
python scripts/build/build_all.py

# 2. Deploy dev
python scripts/deploy/deploy_env.py --env dev

# 3. Vérifier version
aws lambda get-function --function-name vectora-inbox-normalize-score-v2-dev \
  --query 'Configuration.LastModified' --profile rag-lai-prod
```

### Étape 2: Re-test V18

```bash
# 1. Nouveau client_id pour test isolé
# lai_weekly_v19 (ou réutiliser v18 après nettoyage S3)

# 2. Relancer workflow E2E
python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_v19 --env dev

# 3. Analyser résultats
python .tmp/analyze_v19.py
```

### Étape 3: Validation Métriques

**Critères de succès** (vs V17):
- ✅ Items ingérés: 25-40
- ✅ Companies: ≥70%
- ✅ Items relevant: ≥60%
- ✅ Score moyen: 65-85
- ✅ Faux négatifs: ≤1
- ✅ Domain scoring: 100%

---

## Recommandations

### Court Terme (Avant Merge)

1. **CRITIQUE**: Redéployer avec corrections cache_control
2. **CRITIQUE**: Re-tester workflow E2E complet
3. **IMPORTANT**: Valider métriques vs baseline V17
4. **IMPORTANT**: Vérifier logs CloudWatch (aucune erreur)

### Moyen Terme (Post-Merge)

1. **Nettoyage**: Supprimer tous les fichiers obsolètes lai_matching
2. **Documentation**: Mettre à jour blueprint avec corrections
3. **Tests**: Ajouter test unitaire pour invoke_with_prompt
4. **Monitoring**: Alertes CloudWatch sur ValidationException

### Long Terme

1. **Prompt Caching**: Évaluer support sur modèles futurs (économies coûts)
2. **Architecture**: Valider cohérence prompts canonical vs code
3. **Tests E2E**: Automatiser avec CI/CD
4. **Métriques**: Dashboard temps réel qualité domain scoring

---

## Annexes

### Fichiers Générés

- `.tmp/v18_ingested.json` - 31 items ingérés (27.9 KB)
- `.tmp/v18_curated.json` - 31 items normalisés (91.6 KB)
- `.tmp/v18_ingest_response.json` - Réponse Lambda ingest
- `.tmp/v18_normalize_response.json` - Réponse Lambda normalize (202)
- `.tmp/analyze_v18.py` - Script analyse métriques
- `.tmp/analyze_rejected.py` - Script analyse items rejetés

### Commandes Exécutées

```bash
# Préparation
aws sts get-caller-identity --profile rag-lai-prod
cp client-config-examples/production/lai_weekly_v17.yaml \
   client-config-examples/production/lai_weekly_v18.yaml
aws s3 cp client-config-examples/production/lai_weekly_v18.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v18.yaml \
  --profile rag-lai-prod --region eu-west-3

# Workflow E2E
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload file://.tmp/v18_payload.json \
  .tmp/v18_ingest_response.json \
  --profile rag-lai-prod --region eu-west-3

aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload file://.tmp/v18_payload.json \
  .tmp/v18_normalize_response.json \
  --profile rag-lai-prod --region eu-west-3

# Récupération résultats
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v18/2026/02/04/items.json \
  .tmp/v18_curated.json --profile rag-lai-prod
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v18/2026/02/04/items.json \
  .tmp/v18_ingested.json --profile rag-lai-prod

# Analyse
python .tmp/analyze_v18.py
python .tmp/analyze_rejected.py

# Logs
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 30m --filter-pattern "ERROR" \
  --profile rag-lai-prod --region eu-west-3
```

### Versions

- **vectora-core**: 1.4.3 (layer dev:XX)
- **canonical**: 2.3
- **client**: lai_weekly_v18
- **environnement**: dev
- **date**: 2026-02-04
- **bedrock_model**: anthropic.claude-3-sonnet-20240229-v1:0
- **bedrock_region**: us-east-1

### Corrections Code

**Fichiers modifiés**:
1. `src_v2/vectora_core/normalization/bedrock_client.py` (lignes 367-368, 373-374)
2. `src_v2/vectora_core/shared/config_loader.py` (lignes 380-390)

**Commit requis**: Avant redéploiement (règle critique #3)

---

## Conclusion

Le test V18 a permis d'identifier **2 bugs critiques** dans le code de production :

1. ❌ **cache_control non supporté** → 100% échec domain scoring
2. ⚠️ **Référence obsolète lai_matching.yaml** → WARNING logs

Les corrections ont été appliquées au code local. **Redéploiement et re-test requis** avant validation workflow.

**Temps investi**: ~2h  
**Valeur ajoutée**: Bugs critiques identifiés et corrigés avant impact production  
**Prochaine action**: Build + Deploy + Re-test V19

---

**Rapport créé**: 2026-02-04  
**Statut**: CORRECTIONS APPLIQUÉES - RE-TEST REQUIS  
**Priorité**: CRITIQUE
