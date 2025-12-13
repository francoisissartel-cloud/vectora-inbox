# Vectora Inbox — LAI Runtime Phase 2: Filtrage des Catégories

**Date:** 2025-01-XX  
**Phase:** 2/4 — Filtrage generic_terms / negative_terms  
**Statut:** ✅ IMPLÉMENTÉ

---

## Objectif de la Phase 2

Corriger le problème de faux positifs en :
1. **Excluant generic_terms du comptage des signaux** (PEG, liposomes, subcutaneous ne peuvent plus matcher seuls)
2. **Appliquant le veto negative_terms** (oral tablet, topical annulent le match)
3. **Loggant les signaux utilisés** pour traçabilité

---

## Modifications Implémentées

### Fichier: `src/vectora_core/matching/matcher.py`

#### 1. Exclusion de generic_terms du comptage

**Avant:**
```python
high_precision_count = sum(len(category_matches.get(cat, [])) for cat in high_precision_cats)
supporting_count = sum(len(category_matches.get(cat, [])) for cat in supporting_cats)
```

**Après:**
```python
excluded_categories = ['generic_terms', '_metadata']

high_precision_count = 0
for cat in high_precision_cats:
    if cat not in excluded_categories and cat in category_matches:
        count = len(category_matches[cat])
        high_precision_count += count
        logger.debug(f"[SIGNAL_COUNT] High precision: {cat} = {count}")

supporting_count = 0
for cat in supporting_cats:
    if cat not in excluded_categories and cat in category_matches:
        count = len(category_matches[cat])
        supporting_count += count
        logger.debug(f"[SIGNAL_COUNT] Supporting: {cat} = {count}")
```

#### 2. Veto negative_terms avec logging

**Avant:**
```python
if negative_detected:
    return False, {
        'match_confidence': 'rejected'
    }
```

**Après:**
```python
if negative_detected:
    logger.info(f"[NEGATIVE_VETO] Match rejected due to negative terms: {negative_detected}")
    return False, {
        'match_confidence': 'rejected_negative',
        'negative_terms_detected': negative_detected
    }
```

#### 3. Logging des signaux utilisés

**Ajouté:**
```python
logger.info(f"[SIGNAL_SUMMARY] High precision: {high_precision_count}, Supporting: {supporting_count}")
logger.info(f"[SIGNAL_SUMMARY] Categories used: {[c for c in category_matches.keys() if c not in excluded_categories]}")
```

---

## Impact Attendu

### Avant Phase 2
- Items avec seulement "PEG" ou "liposomes" → ✅ MATCH (faux positif)
- Items avec "oral tablet" → ✅ MATCH (faux positif)
- Pas de visibilité sur les signaux utilisés

### Après Phase 2
- Items avec seulement "PEG" ou "liposomes" → ❌ NO MATCH (generic_terms exclus)
- Items avec "oral tablet" → ❌ NO MATCH (negative_terms veto)
- Logs `[SIGNAL_COUNT]`, `[SIGNAL_SUMMARY]`, `[NEGATIVE_VETO]` disponibles

---

## Prochaines Étapes

### Déploiement
1. Repackager la Lambda : `python scripts/package_lambda.py`
2. Redéployer : `python scripts/deploy_lambda.py --env dev`
3. Vérifier : `aws lambda get-function --function-name vectora-inbox-engine-dev`

### Tests
1. Lancer engine : `python scripts/run_engine.py --env dev --client lai_weekly`
2. Analyser newsletter : `aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/latest/newsletter.json .`
3. Vérifier logs :
   ```powershell
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[NEGATIVE_VETO]"
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[SIGNAL_COUNT]"
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[SIGNAL_SUMMARY]"
   ```

### Critères de Succès
✅ generic_terms exclus du comptage  
✅ negative_terms appliqués comme veto  
✅ Logs détaillés disponibles  
✅ Réduction des faux positifs observée  

---

## Risques

🟡 **Risque de sur-filtrage:** Si trop de termes sont classés comme generic_terms, risque de manquer des vrais positifs  
→ Mitigation: Vérifier la configuration des catégories dans `lai_keywords.yaml`

🟢 **Pas de risque de régression:** Les modifications sont isolées dans la logique de profile matching

---

## Notes Techniques

- Les catégories `generic_terms` restent dans `category_matches` pour traçabilité, mais ne comptent plus dans les signaux
- Le veto `negative_terms` s'applique AVANT le comptage des signaux (early exit)
- Les logs utilisent des préfixes distincts pour faciliter le filtrage CloudWatch
