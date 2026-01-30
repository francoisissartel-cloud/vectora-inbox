# Rapport Final - Phase 5: Retour Users & Métriques
## Plan Correctif v4 - Extraction Dates Bedrock Hybride

**Date**: 2026-01-29  
**Client**: lai_weekly_v6  
**Objectif**: Atteindre >95% de vraies dates extraites via Bedrock

---

## RÉSUMÉ EXÉCUTIF

### ✅ Phases Complétées

1. **Phase 1: Cadrage** - ✅ TERMINÉE
2. **Phase 2: Correctifs Locaux** - ✅ TERMINÉE (5/5 correctifs appliqués)
3. **Phase 3: Tests Locaux** - ✅ TERMINÉE (100% tests passent)
4. **Phase 4: Déploiement AWS** - ✅ TERMINÉE (layer v4 déployé)
5. **Phase 5: Validation E2E** - ⚠️ EN COURS (extraction dates 0%)

### ⚠️ Problème Identifié

**Symptôme**: Extraction dates Bedrock = 0% (attendu: >95%)  
**Cause probable**: Prompt enrichi non pris en compte par Bedrock  
**Impact**: Dates fallback utilisées (date d'ingestion au lieu de vraies dates)

---

## DÉTAILS PHASE 5

### 5.1 Test E2E Exécuté

**Pipeline complet**:
1. ✅ Ingestion: 23 items ingérés (18.54s)
2. ✅ Normalisation: 23 items normalisés (timeout >15min)
3. ⏸️ Newsletter: Non exécutée (en attente validation normalisation)

### 5.2 Métriques Extraction Dates

**Résultats observés**:
```
Métrique                    | Avant  | Cible  | Actuel | Status
----------------------------|--------|--------|--------|--------
Vraies dates extraites      | 0%     | >95%   | 0%     | ❌ FAIL
Dates Bedrock fiables       | N/A    | >90%   | 0%     | ❌ FAIL
Dates fallback              | 100%   | <5%    | 100%   | ❌ FAIL
```

**Analyse 10 premiers items**:
- Items analysés: 10
- Dates Bedrock extraites: 0 (0%)
- Dates fallback utilisées: 10 (100%)
- Effective_date = published_at (fallback)

### 5.3 Fichiers Déployés

**✅ Prompt enrichi S3**:
- Path: `s3://vectora-inbox-config-dev/canonical/prompts/normalization/lai_prompt.yaml`
- Taille: 2.7 KB
- Modifications: Ajout extraction date + champs `extracted_date` et `date_confidence`

**✅ Layer vectora-core v4**:
- ARN: `arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-approche-b-dev:4`
- Taille: 290 KB
- Structure: `python/vectora_core/` (corrigée)

**✅ Lambdas mises à jour**:
- `vectora-inbox-normalize-score-v2-dev`: Layer v4 appliqué
- `vectora-inbox-newsletter-v2-dev`: Layer v4 appliqué

### 5.4 Items Curated Générés

**Path S3**: `s3://vectora-inbox-data-dev/curated/lai_weekly_v6/2026/01/29/items.json`

**Structure observée**:
```json
{
  "normalized_content": {
    "summary": "...",
    "entities": {...},
    "event_classification": {...},
    "lai_relevance_score": 9,
    "extracted_date": null,  // ❌ Devrait contenir "2026-01-27"
    "date_confidence": 0.0   // ❌ Devrait être > 0.7
  },
  "scoring_results": {
    "final_score": 12.2,
    "effective_date": "2026-01-29"  // ❌ Date fallback au lieu de vraie date
  }
}
```

---

## DIAGNOSTIC

### Causes Possibles

1. **Prompt non chargé**: Le prompt enrichi n'est pas lu par la Lambda
2. **Cache Bedrock**: Bedrock utilise une version cachée de l'ancien prompt
3. **Schéma JSON**: Le schéma de sortie Bedrock ne correspond pas au prompt
4. **Timeout**: La Lambda timeout avant de terminer l'extraction

### Actions de Diagnostic Recommandées

```bash
# 1. Vérifier les logs CloudWatch
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 30m --follow --region eu-west-3 --profile rag-lai-prod

# 2. Vérifier le prompt chargé
aws s3 cp s3://vectora-inbox-config-dev/canonical/prompts/normalization/lai_prompt.yaml - \
  --region eu-west-3 --profile rag-lai-prod

# 3. Tester avec un seul item
# Modifier event_normalize_v6_dates.json pour limiter à 1 item
```

---

## CORRECTIFS APPLIQUÉS (PHASE 2)

### ✅ Correctif 1: Prompt normalisation enrichi
**Fichier**: `canonical/prompts/normalization/lai_prompt.yaml`
- Ajout tâche #11: "Extract publication date from content"
- Ajout instructions extraction dates
- Ajout champs `extracted_date` et `date_confidence` dans schéma JSON

### ✅ Correctif 2: Parser réponse Bedrock
**Fichier**: `src_v2/vectora_core/normalization/normalizer.py`
- Extraction `extracted_date` et `date_confidence` depuis réponse Bedrock
- Validation format YYYY-MM-DD
- Ajout dans `normalized_content`

### ✅ Correctif 3: Utiliser date Bedrock dans scoring
**Fichier**: `src_v2/vectora_core/normalization/scorer.py`
- Détermination `effective_date`: prioriser `extracted_date` si confiance > 0.7
- Création `_get_recency_factor_with_date()`
- Création `_calculate_penalties_with_date()`
- Ajout `effective_date` dans résultats scoring

### ✅ Correctif 4: Afficher date réelle dans newsletter
**Fichier**: `src_v2/vectora_core/newsletter/assembler.py`
- Utilisation `effective_date` dans `_format_item_markdown()`
- Utilisation `effective_date` dans `_format_item_json()`

### ✅ Correctif 5: Tests locaux
**Fichiers**:
- `tests/unit/test_bedrock_date_extraction.py`: 8/8 tests passent
- `tests/integration/test_bedrock_date_integration.py`: 5/5 tests passent
- Taux de détection simulé: 100%

---

## PROCHAINES ÉTAPES

### Actions Immédiates

1. **Vérifier logs CloudWatch** pour identifier l'erreur exacte
2. **Valider chargement prompt** depuis S3
3. **Tester avec 1 item** pour isoler le problème
4. **Vérifier schéma Bedrock** (correspondance prompt ↔ code)

### Actions Correctives Potentielles

**Si prompt non chargé**:
- Vérifier path S3 dans `prompt_resolver.py`
- Vérifier permissions IAM Lambda → S3

**Si schéma incompatible**:
- Ajuster `bedrock_client.py` pour parser les nouveaux champs
- Vérifier que le prompt utilise le bon format JSON

**Si timeout Bedrock**:
- Augmenter timeout Lambda (actuellement 900s)
- Optimiser prompt pour réduire tokens

### Validation Finale

Une fois corrigé, valider avec:
```bash
# 1. Relancer normalisation
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --payload file://event_normalize_v6_dates.json \
  response_normalize_dates.json

# 2. Valider extraction
python scripts/validate_bedrock_dates.py

# 3. Générer newsletter
aws lambda invoke --function-name vectora-inbox-newsletter-v2-dev \
  --payload file://event_newsletter_v6_dates.json \
  response_newsletter_dates.json

# 4. Vérifier dates dans newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v6/2026/01/29/newsletter.md -
```

---

## CONCLUSION

### Travail Accompli

✅ **5 correctifs** appliqués dans le code  
✅ **Prompt enrichi** uploadé sur S3  
✅ **Layer v4** créé et déployé  
✅ **2 Lambdas** mises à jour  
✅ **Tests locaux** validés (100% succès)  

### Travail Restant

⚠️ **Diagnostic** extraction dates 0%  
⚠️ **Correction** problème prompt/Bedrock  
⚠️ **Validation** E2E complète  
⚠️ **Métriques** avant/après  

### Estimation

**Temps restant**: 1-2h  
**Complexité**: Moyenne (diagnostic + correction)  
**Risque**: Faible (fallback fonctionne)

---

## MÉTRIQUES FINALES (À COMPLÉTER)

```
Métrique                    | Avant  | Cible  | Après  | Delta
----------------------------|--------|--------|--------|-------
Vraies dates extraites      | 0%     | >95%   | [TBD]  | [TBD]
Dates Bedrock fiables       | N/A    | >90%   | [TBD]  | [TBD]
Dates fallback              | 100%   | <5%    | [TBD]  | [TBD]
Temps normalisation/item    | 4.9s   | <5.5s  | [TBD]  | [TBD]
Coût par run (23 items)     | $0.21  | <$0.25 | [TBD]  | [TBD]
```

**Note**: Métriques à compléter après correction du problème d'extraction.
