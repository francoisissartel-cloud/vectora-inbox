# Test E2E v12 - Phase 1 Correction Matching

**Date**: 2026-02-03  
**Client**: lai_weekly_v12  
**Branche**: fix/matching-domain-definition-v12  
**CANONICAL_VERSION**: 2.1

---

## 📊 Résultats

### Métriques Matching
- **Taux matching**: 48.3% (14/29 items)
- **Objectif**: >50%
- **Amélioration**: 0% → 48.3% (+48.3 points)
- **Score moyen**: 79.3/100
- **Score min**: 55
- **Score max**: 90

### Items Clés Détectés ✅
1. **UZEDY®** (Teva): Score 90 ✅
   - Trademark détecté
   - Événement réglementaire
   - Signaux LAI forts

2. **MedinCell** (Teva Partnership): Score 85 ✅
   - Pure player détecté
   - Hybrid company (Teva) détecté
   - Trademark TEV-'749

3. **UZEDY® Financial Results**: Score 80 ⚠️
   - Trademark détecté
   - Molécule OLANZAPINE détectée
   - Légèrement sous objectif (85)

### Statut Phase 1
⚠️ **AJUSTEMENTS REQUIS** (48.3% - proche mais sous 50%)

---

## 🔍 Analyse Détaillée

### Points Positifs ✅
1. **Architecture 2 appels Bedrock fonctionne**
   - Normalisation: 29/29 items (100%)
   - Domain scoring: 29/29 items (100%)
   - Pas d'erreurs techniques

2. **Détection des signaux forts**
   - Trademarks: UZEDY® détecté
   - Pure players: MedinCell détecté
   - Hybrid companies: Teva détecté
   - Molécules: OLANZAPINE détecté

3. **Scores cohérents**
   - Items pertinents: 55-90 points
   - Items non pertinents: 0 points
   - Pas de faux positifs évidents

### Points d'Amélioration 🔧
1. **Taux matching légèrement sous objectif**
   - 48.3% vs 50% objectif
   - Manque 1-2 items pour atteindre 50%

2. **Items non matchés à investiguer**
   - 15/29 items non matchés (51.7%)
   - Certains pourraient être des faux négatifs
   - Nécessite analyse manuelle

3. **Scores items clés**
   - UZEDY® Financial: 80 (objectif: >85)
   - Peut nécessiter ajustement boosts

---

## 🎯 Conformité Gouvernance

### Règles Respectées ✅
- ✅ Branche feature créée: `fix/matching-domain-definition-v12`
- ✅ VERSION incrémentée: CANONICAL_VERSION 2.0 → 2.1
- ✅ Commit AVANT sync S3
- ✅ Environnement explicite: `--env dev`
- ✅ Temporaires dans `.tmp/`
- ✅ Test E2E complet: ingest → normalize-score

### Fichiers Créés/Modifiés
1. `canonical/scopes/domain_definitions.yaml` (nouveau)
2. `VERSION` (CANONICAL_VERSION 2.0 → 2.1)
3. `client-config-examples/production/lai_weekly_v12.yaml` (nouveau)
4. `scripts/invoke/invoke_normalize_score_v2.py` (ajout lai_weekly_v12)
5. `scripts/analysis/analyze_matching_v12.py` (nouveau)

### Commit Git
```
fix: add lai_domain_definition for domain scoring

- Add canonical/scopes/domain_definitions.yaml v1.0.0
- Increment CANONICAL_VERSION 2.0 -> 2.1
- Add lai_weekly_v12.yaml client config
- Fix: 0% matching issue (missing domain definition)

Refs: diagnostic_matching_lai_weekly_v11_2026-02-03.md
Test: lai_weekly_v12 (to be executed)
```

---

## 📈 Comparaison v11 vs v12

| Métrique | v11 | v12 | Évolution |
|----------|-----|-----|-----------|
| Taux matching | 0% | 48.3% | +48.3 pts |
| Items matchés | 0/29 | 14/29 | +14 items |
| Score UZEDY® | N/A | 90 | ✅ |
| Score MedinCell | N/A | 85 | ✅ |
| Architecture | 2 appels | 2 appels | Stable |

---

## 🚀 Prochaines Actions

### Option A: Ajustements Mineurs (Recommandé)
**Objectif**: Passer de 48.3% à 50%+

1. **Analyser les 15 items non matchés**
   - Identifier 1-2 faux négatifs potentiels
   - Vérifier si signaux LAI manqués

2. **Ajuster domain_definitions.yaml**
   - Ajouter signaux détectés dans faux négatifs
   - Incrémenter version 1.0.0 → 1.1.0
   - Re-sync S3 (pas de redéploiement code)

3. **Re-tester lai_weekly_v12**
   - Même données (pas de nouvelle ingestion)
   - Comparer métriques

4. **Si >50%**: Push + PR + Phase 2

### Option B: Valider État Actuel
**Objectif**: Accepter 48.3% comme baseline

1. **Push branche actuelle**
2. **Créer PR vers develop**
3. **Documenter baseline 48.3%**
4. **Planifier Phase 2 (amélioration continue)**

---

## 💡 Recommandation

**Choisir Option A** pour les raisons suivantes:
- Très proche de l'objectif (48.3% vs 50%)
- Ajustements mineurs suffisent
- Pas de redéploiement code nécessaire
- Validation rapide (1-2h)

**Critères de succès Option A**:
- Taux matching >50%
- Items clés (UZEDY®, MedinCell) toujours détectés
- Pas de régression sur items déjà matchés

---

## 📝 Notes Techniques

### Temps d'Exécution
- Ingestion: ~20s
- Normalize-score: ~161s (2min 41s)
- Total E2E: ~3min

### Fichiers S3
- Config: `s3://vectora-inbox-config-dev/clients/lai_weekly_v12.yaml`
- Domain def: `s3://vectora-inbox-config-dev/canonical/scopes/domain_definitions.yaml`
- Résultats: `s3://vectora-inbox-data-dev/curated/lai_weekly_v12/2026/02/03/items.json`

### Logs Lambda
- Fonction: `vectora-inbox-normalize-score-v2-dev`
- Région: `eu-west-3`
- Profil: `rag-lai-prod`

---

**Rapport généré**: 2026-02-03 10:30  
**Auteur**: Plan Correctif Matching v12  
**Statut**: ⚠️ Ajustements requis (48.3% - proche objectif)
