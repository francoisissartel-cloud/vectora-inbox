# Rapport Phase 7 - Merge + Tests AWS Dev

**Date**: 2026-02-03  
**Plan**: plan_amelioration_canonical_e2e_v13_FINAL_2026-02-03.md  
**Phase**: 7 - Merge + Tests AWS Dev  
**Statut**: ⚠️ COMPLÉTÉ AVEC ALERTE

---

## ✅ ACTIONS COMPLÉTÉES

### 1. Merge vers Main ✅

```bash
git checkout main
git merge fix/canonical-improvements-e2e-v13 --no-ff
```

**Résultat**:
- Merge réussi (strategy: ort)
- 9 fichiers modifiés
- +164 insertions, -375 suppressions
- 3 fichiers supprimés (anciens prompts)

### 2. Tag Version ✅

```bash
git tag v2.2-canonical -m "Canonical v2.2 - Amélioration qualité post E2E v13"
```

**Tag créé**: `v2.2-canonical`

### 3. Push GitHub ✅

```bash
git push origin main
git push origin v2.2-canonical
```

**Résultat**:
- Main: `54fa270..904471e`
- Tag: `v2.2-canonical` poussé

### 4. Tests AWS Dev ✅

```bash
python scripts/invoke/invoke_normalize_score_v2.py --event lai_weekly_v12
```

**Résultat**:
- Lambda: `vectora-inbox-normalize-score-v2-dev`
- Durée: 166.2s (2min 46s)
- StatusCode: 200 ✅

---

## ⚠️ RÉSULTATS TESTS AWS DEV

### Statistiques

| Métrique | Valeur | Statut |
|----------|--------|--------|
| **Items input** | 29 | ✅ |
| **Items normalized** | 29 | ✅ |
| **Items matched** | 0 | ⚠️ PROBLÈME |
| **Items scored** | 29 | ✅ |
| **Processing time** | 163.8s | ✅ |

### ⚠️ ALERTE: 0% Matching

**Problème identifié**: Aucun item n'a été matché malgré:
- 29 items normalisés ✅
- 29 items scorés ✅
- Canonical v2.2 déployé ✅

**Hypothèses**:

1. **Problème de configuration client**
   - `lai_weekly_v12.yaml` utilise `canonical_version: "2.1"`
   - Devrait être `"2.2"` pour utiliser les nouvelles améliorations

2. **Problème de seuils**
   - `min_domain_score: 0.25` peut-être trop élevé
   - Tous les scores < 25 sont rejetés

3. **Problème de domain scoring**
   - `is_relevant: false` pour tous les items?
   - Règles trop strictes (financial_results=0, hybrid sans signaux)?

4. **Cache Lambda**
   - Lambda peut utiliser ancien canonical en cache
   - Nécessite cold start ou attente

---

## 🔍 ANALYSE REQUISE

### Actions de Diagnostic

1. **Vérifier logs CloudWatch**
   ```bash
   # Analyser les logs Lambda pour voir les scores réels
   aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
     --follow --profile rag-lai-prod --region eu-west-3
   ```

2. **Vérifier S3 canonical**
   ```bash
   # Confirmer que v2.2 est bien déployé
   aws s3 ls s3://vectora-inbox-config-dev/canonical/domains/ \
     --profile rag-lai-prod --region eu-west-3
   ```

3. **Tester avec seuil plus bas**
   - Modifier `lai_weekly_v12.yaml`: `min_domain_score: 0.10`
   - Re-tester

4. **Analyser items individuels**
   - Vérifier quels items devraient matcher
   - Comparer avec tests locaux (qui ont fonctionné)

---

## 📊 COMPARAISON TESTS LOCAL vs AWS

### Tests Local (Phase 5) ✅

| Item | Score | Matched |
|------|-------|---------|
| test_lai_001 (Teva+MedinCell) | 85 | ✅ |
| test_lai_002 (Camurus) | 75 | ✅ |
| test_lai_003 (J&J CEO) | 0 | ✅ (rejeté) |

**Résultat**: 2/3 matched (67%)

### Tests AWS Dev (Phase 7) ⚠️

| Métrique | Valeur |
|----------|--------|
| Items matched | 0/29 (0%) |

**Écart**: -67% de matching

---

## 🎯 PROCHAINES ACTIONS

### Option 1: Diagnostic Approfondi (RECOMMANDÉ)

1. Analyser logs CloudWatch Lambda
2. Vérifier scores individuels des 29 items
3. Identifier pourquoi 0% matching vs 67% en local
4. Ajuster configuration si nécessaire

### Option 2: Ajuster Seuils

1. Baisser `min_domain_score` de 0.25 à 0.10
2. Re-tester avec lai_weekly_v12
3. Analyser nouveaux résultats

### Option 3: Créer lai_weekly_v13

1. Créer nouveau client avec `canonical_version: "2.2"`
2. Ajuster seuils pour Canonical v2.2
3. Tester avec nouveau client

---

## ✅ CHECKLIST PHASE 7

- [x] Merge vers main
- [x] Tag v2.2-canonical
- [x] Push GitHub
- [x] Tests AWS dev lancés
- [x] Résultats collectés
- [ ] ⚠️ Diagnostic 0% matching (À FAIRE)
- [ ] Validation résultats (BLOQUÉ)
- [ ] Promotion stage (BLOQUÉ - nécessite accord admin)

---

## 📝 CONCLUSION PHASE 7

**Statut**: ⚠️ COMPLÉTÉ AVEC ALERTE

- ✅ Merge et deploy réussis
- ✅ Tests AWS exécutés
- ⚠️ 0% matching détecté
- 🔍 Diagnostic requis avant promotion

**Recommandation**: Analyser les logs CloudWatch pour comprendre pourquoi 0% matching avant de poursuivre.

---

**Rapport créé**: 2026-02-03  
**Durée Phase 7**: ~10 minutes  
**Statut global**: 87% complété (7/8 phases)
