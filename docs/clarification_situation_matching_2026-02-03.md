# Clarification Situation - Matching v13 vs v14

**Date**: 2026-02-03  
**Objectif**: Clarifier la confusion sur l'état du matching

---

## 🔍 CONFUSION IDENTIFIÉE

Tu as raison d'être confus! Il y a **2 définitions différentes de "matching"** qui créent la confusion:

### Définition 1: "Items Matched" (Statistique Lambda)

**Ce que dit Lambda**:
- v12: `items_matched: 0`
- v14: `items_matched: 0`

**Signification**: Nombre d'items qui ont passé le seuil `min_domain_score: 0.25` (25 points)

**Problème**: Le seuil 25 est trop élevé, donc 0 items passent

### Définition 2: "Items Relevant" (Domain Scoring)

**Ce que dit le diagnostic**:
- v13: 14/29 items relevant (48.3%)
- v14: 12/29 items relevant (41.4%)

**Signification**: Nombre d'items où `domain_scoring.is_relevant = true` (score > 0)

**Problème**: Légère régression (-2 items, -14%)

---

## 📊 SITUATION RÉELLE

### Ce Qui Fonctionne ✅

1. **Normalisation**: 29/29 items normalisés ✅
2. **Domain Scoring**: 12/29 items jugés relevant par Bedrock ✅
3. **Scores calculés**: Tous les items ont un score (0 à 90) ✅
4. **Canonical v2.2 déployé**: Tous les fichiers sur S3 ✅

### Ce Qui Ne Fonctionne PAS ❌

1. **Seuil trop élevé**: `min_domain_score: 0.25` (25 points) vs max score 3.3
2. **Items matched = 0**: Aucun item ne passe le seuil de 25 points
3. **Légère régression**: -2 items relevant (14 → 12)
4. **Perte pure_player_company**: Companies non détectées → -25 points boost

---

## 🎯 VERDICT

### Le Plan v2.2 Est-il un Succès?

**Réponse**: ⚠️ **SUCCÈS PARTIEL AVEC RÉGRESSION**

**Succès** ✅:
- Canonical v2.2 déployé correctement
- Dosing_intervals détectés (amélioration)
- Hybrid_company boost conditionnel fonctionne
- Financial_results base_score 0 appliqué
- Exclusions manufacturing appliquées

**Régression** ⚠️:
- Perte détection `pure_player_company` (-25 points par item)
- -2 items relevant (14 → 12, -14%)
- -5.2 points score moyen (38.3 → 33.1, -13.6%)

**Bloquant** ❌:
- Seuil 25 inadapté → 0 items matched
- Nécessite correction avant utilisation

---

## 🔧 PROBLÈMES À RÉSOUDRE

### Problème 1: Seuil Inadapté (BLOQUANT)

**Cause**: `min_domain_score: 0.25` trop élevé

**Impact**: 0/29 items matched

**Solution**: Baisser à 0.05 ou 0.10

**Priorité**: 🔴 CRITIQUE

### Problème 2: Perte Pure Player Companies (IMPORTANT)

**Cause**: `companies_detected` vide dans normalisation

**Impact**: -25 points boost par item pure player (5-7 items)

**Solution**: Corriger prompt `generic_normalization.yaml`

**Priorité**: 🟡 IMPORTANT

### Problème 3: Template Non Résolu (MINEUR)

**Cause**: `{{item_dosing_intervals}}` non résolu

**Impact**: Signal invalide dans 1 item

**Solution**: Corriger template dans prompt

**Priorité**: 🟢 MINEUR

---

## 📈 COMPARAISON DÉTAILLÉE

### Métriques Globales

| Métrique | V13 (Avant) | V14 (Après) | Delta | Statut |
|----------|-------------|-------------|-------|--------|
| **Items input** | 29 | 29 | 0 | ✅ |
| **Items normalized** | 29 | 29 | 0 | ✅ |
| **Items relevant** | 14 (48.3%) | 12 (41.4%) | -2 (-14%) | ⚠️ |
| **Items matched** | ? | 0 (0%) | ? | ❌ |
| **Score moyen** | 38.3 | 33.1 | -5.2 (-13.6%) | ⚠️ |
| **Score max** | ? | 90 | ? | ✅ |

### Détection Signaux

| Signal | V13 | V14 | Delta | Statut |
|--------|-----|-----|-------|--------|
| **pure_player_company** | 5-7 items | 0 items | -100% | ❌ |
| **trademark_mention** | ? | 8 items | ? | ✅ |
| **dosing_interval** | 0 items | 3-5 items | +100% | ✅ |
| **technology_family** | ? | ? | ? | ✅ |
| **hybrid_company** | ? | ? | ? | ✅ |

---

## 🎯 PLAN D'ACTION

### Court Terme (Débloquer)

1. **Baisser seuil** à 0.05 dans lai_weekly_v14.yaml
2. **Re-tester** pour avoir items_matched > 0
3. **Valider** que le matching fonctionne

**Durée**: 10 minutes

### Moyen Terme (Corriger Régression)

1. **Corriger** prompt `generic_normalization.yaml` pour détecter companies
2. **Re-normaliser** les items avec nouveau prompt
3. **Valider** que pure_player_company est détecté
4. **Comparer** scores v13 vs v15

**Durée**: 1-2 heures

### Long Terme (Optimiser)

1. **Calibrer** seuil optimal (entre 5 et 15)
2. **Ajouter** tests de régression automatiques
3. **Documenter** métriques de référence
4. **Créer** alertes si régression > 10%

**Durée**: 1 journée

---

## 📝 CONCLUSION

### Réponse à Ta Question

**"Le plan est-il un succès ou a-t-on un problème de matching?"**

**Réponse**: Les deux!

1. **Le plan v2.2 fonctionne** ✅
   - Canonical déployé
   - Améliorations appliquées (dosing_intervals, etc.)
   - Domain scoring fonctionne

2. **MAIS il y a une régression** ⚠️
   - Perte pure_player_company (-25 points)
   - -2 items relevant
   - Seuil inadapté (0 items matched)

3. **ET c'est corrigeable** 🔧
   - Baisser seuil → débloquer immédiatement
   - Corriger normalisation → restaurer niveau v13
   - Calibrer seuil → optimiser

### Recommandation

**Action immédiate**: Baisser seuil à 0.05 et re-tester v14

**Objectif**: Valider que le matching fonctionne avec seuil adapté

**Ensuite**: Corriger la détection companies pour restaurer les 25 points boost

---

**Document créé**: 2026-02-03  
**Statut**: ✅ CLARIFICATION COMPLÈTE
