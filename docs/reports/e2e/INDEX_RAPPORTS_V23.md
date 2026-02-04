# Index Rapports E2E - Golden Test V23

**Date**: 2026-02-04  
**Client**: lai_weekly_v23  
**Environnement**: dev  
**Statut**: ✅ Validé (62% relevant, score moyen 76)

---

## 📚 RAPPORTS DISPONIBLES

### 1. Guide d'analyse humaine ⭐ **COMMENCER ICI**
**Fichier**: `GUIDE_ANALYSE_HUMAINE_V23.md`

Guide complet pour analyser les décisions du système avec un œil humain :
- Comment valider la normalisation
- Comment valider le domain scoring
- Cas d'usage typiques
- Template d'analyse
- Métriques à calculer

### 2. Rapport enrichi avec JSON ⭐ **POUR ANALYSE DÉTAILLÉE**
**Fichier**: `test_e2e_v23_rapport_enrichi_avec_json_2026-02-04.md`

Analyse détaillée de 5 items relevant + 3 items non-relevant :
- Contenu brut de chaque item
- Sortie JSON complète de normalisation
- Sortie JSON complète de domain scoring
- Questions guidées pour analyse humaine
- Template de validation

**Utilisation** : Analyser item par item pour valider les décisions

### 3. Rapport détaillé complet
**Fichier**: `test_e2e_v23_rapport_detaille_item_par_item_2026-02-04.md` (47.6 KB)

Vue d'ensemble des 32 items :
- 20 items relevant (résumé de chacun)
- 12 items non-relevant (résumé de chacun)
- Statistiques par catégorie
- Analyse par type d'événement
- Analyse par signaux détectés

**Utilisation** : Vue d'ensemble rapide de tous les items

### 4. Données brutes
**Fichier**: `tests/data_snapshots/golden_test_v23_2026-02-04.json`

Données JSON complètes des 32 items curés.

**Utilisation** : Analyse programmatique, comparaison avec futurs runs

### 5. README Golden Test
**Fichier**: `tests/data_snapshots/GOLDEN_TEST_V23_README.md`

Documentation du golden test :
- Configuration utilisée
- Critères de validation
- Comment reproduire le test
- Comment comparer avec un nouveau run

---

## 🎯 WORKFLOW RECOMMANDÉ

### Pour analyse humaine complète

1. **Lire** `GUIDE_ANALYSE_HUMAINE_V23.md` (5 min)
   - Comprendre les critères de validation
   - Voir les cas d'usage typiques

2. **Analyser** `test_e2e_v23_rapport_enrichi_avec_json_2026-02-04.md` (30 min)
   - Examiner les 5 items détaillés
   - Valider normalisation + domain scoring
   - Noter tes observations

3. **Parcourir** `test_e2e_v23_rapport_detaille_item_par_item_2026-02-04.md` (15 min)
   - Vue d'ensemble des 32 items
   - Identifier patterns de problèmes
   - Vérifier cohérence globale

4. **Conclure** (10 min)
   - Calculer taux d'accord
   - Identifier améliorations
   - Documenter décisions

**Temps total** : ~1 heure

### Pour validation rapide

1. **Lire** `test_e2e_v23_rapport_enrichi_avec_json_2026-02-04.md` (20 min)
   - Focus sur les 5 items détaillés
   - Valider décisions clés

2. **Parcourir** statistiques dans rapport détaillé (5 min)
   - Vérifier cohérence globale

**Temps total** : ~25 minutes

---

## 📊 RÉSULTATS ATTENDUS

### Métriques de succès

- **Taux d'accord > 80%** : Système validé ✅
- **Taux d'accord 60-80%** : Ajustements mineurs ⚠️
- **Taux d'accord < 60%** : Révision nécessaire ❌

### Critères de validation

1. **Normalisation correcte** :
   - Entités bien extraites (companies, technologies, etc.)
   - Summary pertinent
   - Event type approprié

2. **Domain scoring justifié** :
   - Signaux LAI détectés correctement
   - Score reflète l'importance LAI
   - Reasoning convaincant

3. **Décision finale cohérente** :
   - Items relevant = signaux LAI forts/moyens
   - Items non-relevant = pas de signaux LAI
   - Pas de faux positifs évidents

---

## 🔧 FICHIERS TECHNIQUES

### Configuration utilisée

- **Client config**: `client-config-examples/production/lai_weekly_v23.yaml`
- **Layers**: vectora-core:62, common-deps:23
- **Prompts**:
  - `canonical/prompts/normalization/generic_normalization.yaml`
  - `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
- **Domain**: `canonical/domains/lai_domain_definition.yaml`
- **Scopes**: `canonical/scopes/*.yaml`

### Code source

- `src_v2/vectora_core/normalization/__init__.py` (orchestration)
- `src_v2/vectora_core/normalization/bedrock_client.py` (appels Bedrock)
- `src_v2/vectora_core/normalization/bedrock_domain_scorer.py` (domain scoring)
- `src_v2/vectora_core/shared/prompt_resolver.py` (résolution références)

---

## 📝 NOTES

### Points forts observés

- Domain scoring fonctionne (62% relevant vs 0% avant fix)
- Bonne détection des signaux LAI (pure players, trademarks, technologies)
- Reasoning détaillé et explicite
- Score breakdown transparent

### Points d'attention

- 12 items rejetés : vérifier faux négatifs potentiels
- Certains items avec technologies LAI mais score faible
- Items "borderline" (score 60-70) à analyser

### Améliorations futures possibles

- Affiner seuils de scoring
- Enrichir scopes de technologies LAI
- Améliorer détection dosing_intervals
- Ajouter plus d'exemples dans prompts

---

**Ce golden test sert de référence pour valider les futures modifications du moteur.**
