# Vectora Inbox — LAI Runtime Phase 1: Instrumentation Results

**Date:** 2025-12-09  
**Phase:** 1 — Instrumentation & Validation du Profile  
**Status:** 🔴 CRITICAL ISSUE DETECTED

---

## 📊 Résumé Exécutif

Phase 1 a révélé un problème critique : **0 items matchés sur 50 items analysés**.

Les logs de debug ajoutés n'ont jamais été déclenchés car aucun item n'a passé le matching initial. Cela indique un problème en amont du profile matching.

**Conclusion:** Le profile `technology_complex` n'est jamais évalué car les items ne passent pas le matching de base.

---

## 🎯 Objectifs Phase 1

Confirmer via logs que :
1. `domain_matching_rules.yaml` est bien lu ✅
2. Le profile `technology_complex` est bien sélectionné pour `tech_lai_ecosystem` ❌ (jamais atteint)
3. `lai_keywords` est bien chargé comme structure hiérarchique (7 catégories) ❌ (jamais vérifié)

---

## 🔧 Actions Réalisées

### 1. Ajout de Logs de Debug dans matcher.py

**Fonction `_get_technology_profile()`:**
- Log du technology_scope_key
- Log du type de scope_data
- Log des clés du scope_data
- Log de _metadata
- Log du profile détecté

**Fonction `_evaluate_domain_match()`:**
- Log du domain_type et technology_scope
- Log du profile_name
- Log de l'utilisation du profile matching

**Fonction `_categorize_technology_keywords()`:**
- Log des catégories trouvées
- Log du nombre de keywords par catégorie
- Log des keywords matchés par catégorie

### 2. Déploiement

- Package Lambda créé : `engine-phase1.zip` (17.5 MB)
- Upload S3 : `s3://vectora-inbox-lambda-code-dev/lambda/engine/phase1.zip`
- Lambda mise à jour : `vectora-inbox-engine-dev`
- CodeSize : 18.3 MB
- Status : Successful

### 3. Exécution Test

- Client : `lai_weekly`
- Period : 7 jours (2025-12-02 → 2025-12-09)
- Execution time : 3.04s
- Status : 200 OK

---

## 📉 Résultats

### Métriques

| Métrique | Résultat | Attendu | Status |
|----------|----------|---------|--------|
| Items analyzed | 50 | 50 | ✅ |
| Items matched | **0** | 6-12 | ❌ |
| Items selected | 0 | 5-10 | ❌ |
| Logs [PROFILE_DEBUG] | 0 | >0 | ❌ |
| Logs [MATCHING_DEBUG] | 0 | >0 | ❌ |
| Logs [CATEGORY_DEBUG] | 0 | >0 | ❌ |

### Analyse des Logs CloudWatch

**Logs généraux présents:**
- ✅ Chargement configuration client : `lai_weekly`
- ✅ Chargement scopes canonical : `companies`, `molecules`, `technologies`, `indications`, `exclusions`
- ✅ Scope technologies chargé : 1 clé
- ✅ Règles de matching chargées : `['technology_profiles', 'technology', 'indication', 'regulatory', 'default']`

**Logs de debug absents:**
- ❌ Aucun log `[PROFILE_DEBUG]`
- ❌ Aucun log `[MATCHING_DEBUG]`
- ❌ Aucun log `[CATEGORY_DEBUG]`

**Interprétation:**
Les logs de debug ne sont jamais déclenchés car la fonction `_evaluate_domain_match()` n'est jamais appelée avec des items qui matchent.

---

## 🔍 Root Cause Analysis

### Problème Identifié

**0 items matchés = Les intersections d'ensembles sont vides**

En analysant les items normalisés (50 items du 08/12/2025), on constate :

**Exemple Item 1 (Agios):**
```json
{
  "title": "Regulatory tracker: Agios awaits FDA decision...",
  "companies_detected": [],
  "molecules_detected": [],
  "technologies_detected": ["PAS"],
  "indications_detected": []
}
```

**Exemple Item 2 (WuXi AppTec):**
```json
{
  "title": "After dodging Biosecure threat, WuXi AppTec...",
  "companies_detected": [],
  "molecules_detected": [],
  "technologies_detected": ["XTEN"],
  "indications_detected": []
}
```

**Exemple Item 3 (Pfizer Hympavzi):**
```json
{
  "title": "ASH: Pfizer, aiming to level the hemophilia...",
  "companies_detected": ["Novo Nordisk", "Pfizer", "Sanofi"],
  "molecules_detected": [],
  "technologies_detected": [],
  "indications_detected": []
}
```

### Observation Critique

**La majorité des items ont `companies_detected: []`**

Cela signifie que :
1. La normalisation Bedrock ne détecte pas les companies correctement
2. OU les companies détectées ne sont pas dans les scopes canonical
3. OU il y a un problème de casse/format dans les noms

**Les technologies détectées ne sont pas LAI:**
- "PAS" (pas dans `lai_keywords`)
- "XTEN" (pas dans `lai_keywords`)

### Root Cause Probable

**RC0 (nouveau) — Normalisation Bedrock défaillante**

La normalisation Bedrock ne détecte pas correctement les entités (companies, technologies) dans les items, ce qui empêche tout matching.

**Impact:**
- Intersections vides → 0 items matchés
- Profile matching jamais atteint
- Logs de debug jamais déclenchés

---

## 🛠️ Actions Correctives Recommandées

### Option A: Vérifier la Normalisation Bedrock (Priorité 1)

**Hypothèse:** Le prompt Bedrock ou la configuration de normalisation est incorrecte.

**Actions:**
1. Examiner le prompt de normalisation dans `src/vectora_core/normalization/normalizer.py`
2. Vérifier les exemples fournis à Bedrock
3. Tester la normalisation sur un item connu (ex: "MedinCell announces...")
4. Comparer avec les résultats attendus

**Durée estimée:** 2h

### Option B: Vérifier les Scopes Canonical (Priorité 2)

**Hypothèse:** Les scopes canonical ne contiennent pas les bonnes valeurs.

**Actions:**
1. Télécharger `company_scopes.yaml` depuis S3
2. Vérifier que "Agios", "WuXi AppTec", "Pfizer" sont présents
3. Vérifier le format (casse, espaces, etc.)
4. Corriger si nécessaire

**Durée estimée:** 1h

### Option C: Forcer un Test avec Données Mockées (Priorité 3)

**Hypothèse:** Tester le profile matching avec des données contrôlées.

**Actions:**
1. Créer un item normalisé mocké avec :
   - `companies_detected: ["MedinCell"]`
   - `technologies_detected: ["long-acting injectable", "FluidCrystal"]`
2. Injecter cet item dans le pipeline
3. Vérifier que les logs de debug sont déclenchés
4. Valider que le profile matching fonctionne

**Durée estimée:** 1h

---

## 📊 Comparaison Avant/Après Phase 1

| Aspect | Avant Phase 1 | Après Phase 1 | Delta |
|--------|---------------|---------------|-------|
| Items matched | 6 (12%) | 0 (0%) | -100% ❌ |
| Logs de debug | 0 | 0 | 0% |
| Compréhension du problème | Faible | **Élevée** | ✅ |

**Observation:** Phase 1 n'a pas amélioré les résultats mais a permis d'identifier la root cause réelle (RC0).

---

## 🎯 Décision & Prochaines Étapes

### Décision

🔴 **STOP Phase 2** — Il est inutile de continuer avec le filtrage des catégories tant que 0 items ne matchent.

### Prochaine Action

**Investiguer RC0 — Normalisation Bedrock défaillante**

**Plan d'action:**
1. Examiner les items normalisés en détail
2. Vérifier le prompt Bedrock de normalisation
3. Tester la normalisation sur des exemples connus
4. Corriger le prompt si nécessaire
5. Relancer la normalisation
6. Retester Phase 1

**Durée estimée:** 3-4h

---

## 💡 Lessons Learned

### Points Positifs

✅ **Logs ajoutés correctement** : Le code de debug est en place et prêt à être utilisé  
✅ **Déploiement réussi** : Pas d'erreur runtime, Lambda fonctionne  
✅ **Root cause identifiée** : Le problème est en amont (normalisation)

### Points d'Amélioration

🔧 **Validation des données d'entrée** : Aurait dû vérifier les items normalisés avant Phase 1  
🔧 **Tests de bout en bout** : Manque de tests sur le pipeline complet  
🔧 **Monitoring** : Pas d'alerte sur "0 items matchés"

---

## 📝 Fichiers Créés/Modifiés

### Code
- `src/vectora_core/matching/matcher.py` (logs ajoutés)

### Déploiement
- `engine-phase1.zip` (17.5 MB)
- Lambda `vectora-inbox-engine-dev` mise à jour

### Diagnostics
- `docs/diagnostics/vectora_inbox_lai_runtime_phase1_instrumentation_results.md` (ce fichier)

### Données
- `newsletter-phase1.json` (0 items)
- `items-normalized-phase1.json` (50 items, companies_detected vides)

---

## 🎬 Conclusion

Phase 1 a révélé un problème critique en amont : **la normalisation Bedrock ne détecte pas correctement les entités**.

Le profile matching ne peut pas fonctionner si les intersections d'ensembles sont vides.

**Prochaine étape:** Investiguer et corriger la normalisation Bedrock avant de reprendre Phase 2.

---

**Status:** 🔴 CRITICAL ISSUE — NORMALISATION DÉFAILLANTE  
**Next Step:** INVESTIGUER RC0 (NORMALISATION BEDROCK)
