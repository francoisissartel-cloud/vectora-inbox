# Test E2E V15 - Résumé Exécutif

**Date**: 2026-02-03 | **Client**: lai_weekly_v15 | **Canonical**: v2.2 | **Durée**: 1h30

---

## ✅ VERDICT: SUCCÈS AVEC RÉSERVES (67%)

**Pipeline E2E fonctionnel et reproductible** - Résultats identiques à V14

---

## 📊 RÉSULTATS CLÉS

| Métrique | V13 (Avant) | V15 (Après) | Évolution |
|----------|-------------|-------------|-----------|
| Items ingérés | 29 | 29 | = |
| Items relevant | 14 (48%) | 12 (41%) | -14% |
| Score moyen | 38.3 | 81.7 | **+113%** ✅ |
| Faux positifs | 5 | 1 | **-80%** ✅ |
| Faux négatifs | 1 | 1 | = |

---

## ✅ SUCCÈS (4/6 objectifs)

1. ✅ **Exclusion corporate_move** - MedinCell RH rejeté (score 0)
2. ✅ **Exclusion financial_results** - 3 rapports financiers rejetés (rule_5)
3. ✅ **Détection dosing_intervals** - once-weekly, once-monthly, monthly détectés
4. ✅ **Scores cohérents** - 65-90 pour items relevant, bonne différenciation

---

## ❌ PROBLÈMES (3 critiques)

1. ❌ **Régression companies** - 0 companies détectées (vs V13 qui détectait)
   - Impact: Perte boost pure_player (+25 points)
   - Affecte: 5-7 items (Nanexa, MedinCell, Camurus)

2. ❌ **Faux négatif Quince** - "once-monthly" dans titre NON détecté
   - Item rejeté alors qu'il devrait matcher

3. ⚠️ **Faux positif Eli Lilly** - Manufacturing facility matché (score 65)
   - "injectables and devices" détecté comme signal LAI

---

## 🎯 TOP 5 ITEMS RELEVANT

1. **Teva/MedinCell NDA** (90) - Trademarks + once-monthly + hybrid
2. **UZEDY® Growth** (90) - Trademark + hybrid + dosing
3. **AstraZeneca Saphnelo** (85) - Self-injectable pen + subcutaneous
4. **Camurus Oclaiz™** (85) - Trademark + regulatory
5. **Pfizer GLP-1** (85) - Monthly injectable + technology

---

## 🔧 ACTIONS PRIORITAIRES (V16)

### Critique (Avant V16)

1. **Restaurer détection companies** - Modifier generic_normalization.yaml
2. **Résoudre faux négatif Quince** - Améliorer extraction dosing_intervals
3. **Exclure Eli Lilly manufacturing** - Ajouter "injectables and devices" aux exclusions

### Impact attendu V16

- Companies détectées: 0 → 5-7 ✅
- Items relevant: 12 → 13-14 ✅
- Faux positifs: 1 → 0 ✅

---

## 📈 ÉVOLUTION V13 → V14 → V15

| Aspect | V13 | V14 | V15 | Tendance |
|--------|-----|-----|-----|----------|
| Qualité scores | ⚠️ | ✅ | ✅ | 📈 |
| Faux positifs | ❌ 5 | ✅ 0 | ⚠️ 1 | 📈 |
| Companies | ✅ | ❌ | ❌ | 📉 |
| Dosing intervals | ❌ | ✅ | ✅ | 📈 |
| Exclusions | ⚠️ | ✅ | ✅ | 📈 |

**Conclusion**: Canonical v2.2 stable (V14 = V15) mais nécessite corrections

---

## 📁 LIVRABLES

- ✅ `items_ingested.json` - 29 items (26 KB)
- ✅ `items_normalized.json` - 29 items (92 KB)
- ✅ `items_analysis.md` - Analyse détaillée 12 items relevant
- ✅ `test_e2e_v15_rapport_ingestion_normalisation_scoring.md` - Rapport complet

---

**Recommandation**: Procéder à V16 avec corrections priorité 1 (2-3h)
