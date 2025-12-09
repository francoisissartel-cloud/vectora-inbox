# Vectora Inbox – Résumé MVP LAI Recentrage

**Client** : `lai_weekly`  
**Date** : 2025-12-08  
**Environnement** : DEV

---

## Résumé Exécutif

Le recentrage MVP LAI pour le client `lai_weekly` a été implémenté et testé en DEV. Le test a révélé un **problème critique de matching** : le système sélectionne des actualités pharma génériques mentionnant des big pharma (Pfizer, AbbVie, Takeda) sans vérifier que ces actualités concernent réellement les technologies LAI.

---

## Avant / Après Recentrage

### Avant Recentrage (Baseline)

**Problème identifié** : Pas de baseline disponible (premier test MVP LAI).

### Après Recentrage (Phase 4 – Test DEV)

**Résultats du test** :
- Items analysés : 50
- Items matchés : 8 (16%)
- Items sélectionnés : 5
- **Items LAI** : **0** (0%)
- **Items pure players LAI** : **0** (0%)
- **Faux positifs** : **5** (100%)

**Newsletter générée** : `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md`

**Contenu** :
1. Pfizer - Hympavzi Phase 3 data (hemophilia) ❌ Pas LAI
2. Agios - FDA regulatory tracker ❌ Pas LAI
3. AbbVie - Skyrizi TV advertising ❌ Pas LAI
4. Takeda/Otsuka - FDA safety probe / IgA nephropathy ❌ Pas LAI
5. Pfizer/GSK/Shionogi - Antimicrobial resistance musical ❌ Pas LAI

---

## Métriques Finales

| Métrique | Objectif MVP | Résultat | Statut |
|----------|--------------|----------|--------|
| **Précision LAI** | 80–90% | **0%** | ❌ ÉCHEC |
| **Proportion pure players LAI** | ≥ 50% | **0%** | ❌ ÉCHEC |
| **Faux positifs manifestes** | 0 | **5** | ❌ ÉCHEC |
| **Nombre d'items sélectionnés** | 5–10 | **5** | ✅ OK |

---

## Diagnostic

### Cause Racine

Le **matcher** sélectionne des items qui mentionnent des companies dans `lai_companies_global` (Pfizer, AbbVie, Takeda, GSK, Shionogi) **SANS vérifier** que l'item concerne réellement les technologies LAI.

### Exemple Concret

- Item : "AbbVie revs up Skyrizi spending to top TV ad totals in November"
- Company matchée : AbbVie (présente dans `lai_companies_global`)
- Technologie LAI mentionnée : **AUCUNE**
- Résultat : Item sélectionné ❌ (faux positif)

### Scopes Implémentés (Phase 3)

✅ **Scopes créés et déployés** :
- `lai_companies_mvp_core` : 5 pure players LAI (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
- `lai_companies_global` : 170+ companies LAI (incluant big pharma)
- `lai_keywords` : 80+ mots-clés LAI spécifiques
- `pure_player_lai_bonus` : Bonus de scoring pour pure players

❌ **Problème** : Le matcher ne vérifie pas la présence de mots-clés LAI dans l'item avant de le sélectionner.

---

## Décision

### MVP LAI – DEV : 🔴 RED (Après Refactor Matching)

**Date du test** : 2025-12-09

**Statut précédent** : 🟡 EN COURS DE REFACTOR

**Action entreprise** : Refactor complet du matching déployé et testé

**Implémentation complétée** :
- ✅ Création de `canonical/matching/domain_matching_rules.yaml` avec règles déclaratives
- ✅ Adaptation du matcher pour utiliser les règles au lieu de logique codée en dur
- ✅ Adaptation du scorer pour utiliser un scope canonical au lieu d'une liste hardcodée
- ✅ Mise à jour de l'orchestration pour charger et passer les matching rules
- ✅ Documentation complète dans `canonical/matching/README.md`
- ✅ Correction bug d'import dans `__init__.py`
- ✅ Redéploiement complet avec dépendances (17.46 MB)

**Tests exécutés** :
- ✅ Script `redeploy-engine-matching-refactor.ps1` exécuté avec succès (2 fois)
- ✅ Script `test-engine-matching-refactor.ps1` exécuté avec succès
- ✅ Newsletter générée : `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/09/newsletter.md`

**Résultats** :
- Items analysés : 50
- Items matchés : 2 (4%, vs 16% avant)
- Items sélectionnés : 2 (vs 5 avant)
- **Précision LAI** : **0%** (0/2 items sont LAI)
- **Faux positifs** : 2 (Agios oncologie, WuXi AppTec CDMO)

**Diagnostic** : Le refactor de matching fonctionne correctement (technology AND entity), mais les **scopes canonical sont incorrects** :
- `lai_keywords` contient des termes trop génériques ("drug delivery system", "liposomes", "PEG", "subcutaneous", etc.)
- Ces termes matchent n'importe quelle news pharma/biotech, pas seulement les LAI

**Diagnostic complet** : `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md`

**Résumé exécutif** : `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_executive_summary.md`

---

## Refactor Implémenté : Matching Générique Piloté par Config/Canonical

### Solution Implémentée

**Principe** : Aucune logique métier LAI codée en dur. Tout est piloté par des règles déclaratives dans `canonical/matching/domain_matching_rules.yaml`.

**Règle pour domaine `technology`** (ex: `tech_lai_ecosystem`) :
```yaml
match_mode: all_required
dimensions:
  technology:
    requirement: required
    min_matches: 1
  entity:
    requirement: required
    min_matches: 1
    sources: [company, molecule]
```

**Impact attendu** :
- ✅ Item avec `MedinCell` + `extended-release injectable` → MATCH
- ❌ Item avec `Pfizer` seul (sans mot-clé technology) → NO MATCH
- ❌ Item avec `long-acting` seul (sans company/molecule) → NO MATCH

**Extensibilité** : Le même moteur est réutilisable pour d'autres verticaux (oncologie, diabète, etc.) sans modification du code.

---

## Refactor Canonical LAI (2025-01-XX) — Phase "Canonical Only"

### Contexte

Suite au diagnostic de précision LAI à 0%, un refactor complet des scopes canonical LAI a été entrepris pour améliorer la qualité du matching sans modifier le code runtime.

### Changements Implémentés

#### 1. Restructuration de `technology_scopes.yaml`

**Avant** : Liste plate de 78 termes non structurés

**Après** : Structure hiérarchique à 7 catégories (120+ termes classifiés)

**Nouvelles catégories** :
- `core_phrases` (13 termes) : expressions explicites LAI (haute précision)
- `technology_terms_high_precision` (38 termes) : DDS + HLE spécifiques
- `technology_use` (10 termes) : termes d'usage (combinaison requise)
- `route_admin_terms` (13 termes) : routes d'administration (contexte nécessaire)
- `interval_patterns` (14 termes) : patterns de dosage prolongé (signaux forts)
- `generic_terms` (12 termes) : termes trop larges (conservés pour mémoire, ne matchent plus seuls)
- `negative_terms` (11 termes) : exclusions explicites (signaux NON-LAI)

**Termes déplacés vers `generic_terms` (ne matchent plus seuls)** :
- drug delivery system
- liposomes, liposomal
- emulsion, lipid emulsion
- PEG, PEGylation, PEGylated
- subcutaneous (route seule)
- protein engineering
- hydrogel, nanosuspension

**Impact attendu** : Réduction drastique des faux positifs sur big pharma (AbbVie, Pfizer, etc.)

**Documentation** : `docs/diagnostics/vectora_inbox_lai_technology_scopes_refactor_results.md`

#### 2. Séparation des company scopes : pure players vs hybrid

**Nouveaux scopes créés** :

**`lai_companies_pure_players` (14 entreprises)** :
- MedinCell, Camurus, DelSiTech, Nanexa, Peptron
- Bolder BioTechnology, Cristal Therapeutics, Durect
- Eupraxia Pharmaceuticals, Foresee Pharmaceuticals, G2GBio
- Hanmi Pharmaceutical, LIDDS, Taiwan Liposome

**Usage prévu** : 1 signal fort LAI suffit pour déclencher un match haute confiance

**`lai_companies_hybrid` (27 entreprises)** :
- Big pharma : AbbVie, Pfizer, Novo Nordisk, Sanofi, Takeda, etc.
- Mid pharma : Alkermes, Ipsen, Jazz Pharmaceuticals, etc.

**Usage prévu** : signaux multiples requis pour déclencher un match LAI (éviter faux positifs)

**Principe métier** :
- Pure players : business model 100% LAI → 1 signal suffit
- Hybrid : portfolio diversifié → combinaison de signaux requise

**Documentation** : `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md`

#### 3. Principes de matching attendus (phase suivante — code runtime)

**Pour pure players** :
```
IF company IN lai_companies_pure_players:
    IF 1+ core_phrase OR 1+ technology_terms_high_precision:
        → match LAI haute confiance
```

**Pour hybrid** :
```
IF company IN lai_companies_hybrid:
    IF 2+ core_phrase OR (1+ core_phrase + 1+ technology_terms_high_precision):
        → match LAI haute confiance
    ELSE:
        → pas de match LAI
```

**Exemples concrets** :
- "MedinCell announces injectable formulation" → match LAI ✅ (pure player + injectable)
- "Pfizer announces injectable formulation" → pas de match LAI ✅ (hybrid + signal faible seul)
- "Pfizer announces long-acting injectable using PLGA microspheres" → match LAI ✅ (hybrid + signaux multiples)

### Impact Attendu

| Métrique | Avant refactor | Après refactor (attendu) |
|----------|----------------|--------------------------||
| Précision LAI | 0% | >50% |
| Faux positifs big pharma | ~80% des matches | <10% des matches |
| Vrais positifs pure players | ~100% | ~100% (conservé) |

### Prochaines Étapes

**Phase suivante : Adaptation du code runtime**

1. Adapter `domain_matching_rules.yaml` pour exploiter les 7 catégories de `lai_keywords`
2. Modifier `matcher.py` pour implémenter la logique de combinaison de signaux
3. Adapter `scorer.py` pour différencier pure_players vs hybrid
4. Tester sur le corpus existant et mesurer la nouvelle précision LAI

**Contrainte** : Cette phase actuelle (refactor canonical) ne modifie PAS le code runtime. Les fichiers `matcher.py`, `scorer.py`, etc. restent inchangés.

---

## Prochaines Étapes (Après Refactor Canonical)

### Actions Prioritaires

1. **✅ COMPLÉTÉ : Nettoyer `lai_keywords`** (Priorité 1)
   - ✅ Restructuration complète en 7 catégories
   - ✅ Termes génériques isolés dans `generic_terms`
   - ✅ Ajout de `negative_terms` pour exclusions
   - ✅ Documentation complète créée
   - **Statut** : Refactor canonical terminé
   - **Prochaine étape** : Adapter le code runtime pour exploiter cette nouvelle structure

2. **Enrichir les logs de matching** (Priorité 2)
   - Ajouter un champ `matching_details` dans la structure de sortie du matcher
   - Afficher les entités matchées pour chaque item
   - **Temps estimé** : 30 minutes
   - **Impact attendu** : Diagnostic précis des problèmes de matching

3. **Vérifier l'ingestion des sources corporate LAI** (Priorité 3)
   - Consulter les logs de la Lambda ingest-normalize
   - Vérifier que les 5 sources corporate LAI produisent des items
   - **Temps estimé** : 1 heure
   - **Impact attendu** : Augmentation du nombre d'items LAI authentiques disponibles

---

## Livrables Phase 4

✅ **Documents créés** :
- `docs/design/vectora_inbox_lai_mvp_phase4_execution_plan.md` (plan d'exécution)
- `docs/diagnostics/vectora_inbox_lai_mvp_phase4_test_logs.md` (logs de test)
- `docs/diagnostics/vectora_inbox_lai_mvp_focus_results.md` (analyse détaillée)
- `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md` (ce document)

✅ **Artefacts générés** :
- Newsletter : `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md`
- Logs Lambda : CloudWatch (ingest-normalize timeout, engine success)
- Scripts : `invoke_lambdas.py` (contournement problème encodage Windows)

---

## Conclusion

Le recentrage MVP LAI a été **partiellement réussi** :
- ✅ Scopes LAI créés et déployés
- ✅ Règles de scoring avec bonus pure players implémentées
- ✅ Newsletter générée avec succès (5 items)
- ❌ **Qualité des items sélectionnés : 0% de précision LAI**

**Décision finale** : **MVP LAI – DEV : À AJUSTER** (ajustements rapides nécessaires avant acceptation).

---

**Date de décision** : 2025-12-09  
**Responsable** : Amazon Q (Vectora Inbox Architect)  
**Statut actuel** : 🔴 RED - Refactor déployé et testé, scopes canonical à corriger
