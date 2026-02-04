# Test E2E V15 - README

**Date**: 2026-02-03 | **Statut**: ✅ COMPLET | **Durée**: 1h30

---

## 🎯 VERDICT: SUCCÈS AVEC RÉSERVES (67%)

Pipeline E2E fonctionnel - Canonical v2.2 stable et reproductible

---

## 📊 RÉSULTATS EN 1 COUP D'ŒIL

```
Ingestion:      29 items ✅
Normalisation:  29 items ✅
Scoring:        12 items relevant (41.4%) ✅
Score moyen:    81.7/100 (+113% vs V13) ✅
Faux positifs:  1 (vs 5 en V13) ✅
Faux négatifs:  1 (Quince once-monthly) ❌
```

---

## 📁 LIVRABLES PRINCIPAUX

### 🌟 À LIRE EN PRIORITÉ

1. **[test_e2e_v15_resume_executif.md](test_e2e_v15_resume_executif.md)**
   - Résumé 1 page
   - Verdict + métriques + actions

2. **[test_e2e_v15_rapport_ingestion_normalisation_scoring.md](test_e2e_v15_rapport_ingestion_normalisation_scoring.md)**
   - Rapport technique complet
   - Validation objectifs canonical v2.2
   - Problèmes + solutions

### 📊 DONNÉES

3. **`.tmp/e2e_v15/items_normalized.json`**
   - 29 items avec scoring
   - 12 items relevant (score 65-90)

4. **`.tmp/e2e_v15/items_analysis.md`**
   - Analyse détaillée item par item
   - Template retour admin

### 📚 DOCUMENTATION

5. **[test_e2e_v15_INDEX.md](test_e2e_v15_INDEX.md)**
   - Index complet des livrables
   - Structure fichiers + liens S3

---

## ✅ SUCCÈS (4/6)

- ✅ Exclusion corporate_move sans tech
- ✅ Exclusion financial_results sans signaux
- ✅ Détection dosing_intervals (once-weekly, once-monthly, monthly)
- ✅ Scores cohérents (65-90)

---

## ❌ PROBLÈMES (3)

1. ❌ **Régression companies** - 0 détectées (vs V13)
2. ❌ **Faux négatif Quince** - once-monthly non détecté
3. ⚠️ **Faux positif Eli Lilly** - Manufacturing matché

---

## 🔧 ACTIONS V16 (3-4h)

1. Restaurer détection companies (2h)
2. Résoudre faux négatif Quince (1h)
3. Exclure Eli Lilly manufacturing (30min)

**Impact attendu**: Items relevant 12 → 13-14, Faux positifs 1 → 0

---

## 📈 COMPARAISON VERSIONS

| Métrique | V13 | V15 | Δ |
|----------|-----|-----|---|
| Items relevant | 14 (48%) | 12 (41%) | -14% |
| Score moyen | 38.3 | 81.7 | +113% ✅ |
| Faux positifs | 5 | 1 | -80% ✅ |

**V14 = V15** → Canonical v2.2 stable ✅

---

## 🚀 COMMANDES RAPIDES

### Relire les données

```bash
# Items normalisés
cat .tmp/e2e_v15/items_normalized.json | python -m json.tool

# Statistiques
python -c "import json; items=json.load(open('.tmp/e2e_v15/items_normalized.json', encoding='utf-8')); print(f'Relevant: {sum(1 for i in items if i.get(\"domain_scoring\", {}).get(\"is_relevant\"))}/29')"

# Analyse détaillée
cat .tmp/e2e_v15/items_analysis.md
```

### Télécharger depuis S3

```bash
# Items ingérés
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v15/2026/02/03/items.json . --profile rag-lai-prod --region eu-west-3

# Items normalisés
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v15/2026/02/03/items.json . --profile rag-lai-prod --region eu-west-3
```

---

## 📞 NAVIGATION

- **Résumé exécutif**: [test_e2e_v15_resume_executif.md](test_e2e_v15_resume_executif.md)
- **Rapport complet**: [test_e2e_v15_rapport_ingestion_normalisation_scoring.md](test_e2e_v15_rapport_ingestion_normalisation_scoring.md)
- **Index livrables**: [test_e2e_v15_INDEX.md](test_e2e_v15_INDEX.md)
- **Données brutes**: `.tmp/e2e_v15/`
- **Config client**: `client-config-examples/production/lai_weekly_v15.yaml`

---

**Créé**: 2026-02-03 | **Par**: Amazon Q Developer | **Statut**: ✅ PRÊT POUR V16
