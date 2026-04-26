# Vectora Inbox – Phase 4 : Test & Acceptation MVP LAI

**Client cible** : `lai_weekly`  
**Environnement** : DEV uniquement (`vectora-inbox-engine-dev`)  
**Objectif** : Valider que le recentrage LAI produit une newsletter de qualité acceptable pour un MVP

---

## Contexte

Les phases précédentes ont produit :
- **Phase 1** : Diagnostic sémantique (`lai_weekly_mvp_semantic_gap_analysis.md`)
- **Phase 2** : Plan de recentrage (`vectora_inbox_lai_mvp_focus_plan.md`)
- **Phase 3** : Implémentation du recentrage
  - Scopes LAI recentrés (`company_scopes.yaml`, `technology_scopes.yaml`)
  - Règles de scoring avec bonus pure players (`scoring_rules.yaml`)
  - Matcher plus strict (`matcher.py`)
  - Scorer avec bonus pure players (`scorer.py`)

Cette Phase 4 valide l'ensemble en conditions réelles (DEV).

---

## Critères de succès MVP LAI

| Métrique | Objectif | Seuil d'acceptation |
|----------|----------|---------------------|
| **Précision LAI** | 80–90% | ≥ 75% |
| **Proportion pure players LAI** | ≥ 50% | ≥ 40% |
| **Faux positifs manifestes** | 0 | ≤ 1 |
| **Nombre d'items sélectionnés** | 5–10 | 3–15 |

---

## Phase 4.1 – Préparation & Sanity Checks

### Objectif
Vérifier la cohérence des configurations avant le test.

### Actions

1. **Vérifier les scopes LAI**
   - Fichier : `canonical/scopes/company_scopes.yaml`
     - Présence de `lai_companies_mvp_core` (pure players LAI)
     - Présence de `lai_companies_global` (écosystème complet)
   - Fichier : `canonical/scopes/technology_scopes.yaml`
     - Scope `lai_keywords` recentré (pas de bruit générique)
   - Fichier : `canonical/scopes/molecule_scopes.yaml`
     - Scope `lai_molecules_global` présent

2. **Vérifier les règles de scoring**
   - Fichier : `canonical/scoring/scoring_rules.yaml`
     - Bonus pure players LAI correctement configuré
     - Pas de règles contradictoires

3. **Vérifier la config client**
   - Fichier : `client-config-examples/lai_weekly.yaml`
     - `watch_domains` pointe vers les bons scopes
     - `source_bouquets_enabled` contient `lai_press_mvp` et `lai_corporate_mvp`

4. **Vérifier les scripts de test**
   - `scripts/package-engine.ps1` : packaging Lambda
   - `scripts/deploy-runtime-dev.ps1` : déploiement DEV
   - `scripts/test-engine-lai-weekly.ps1` : test client `lai_weekly`

### Critères de succès
- Tous les fichiers existent et sont cohérents
- Aucune référence à un scope inexistant
- Scripts de test opérationnels

### Plan B en cas d'échec
- Si incohérence mineure : corriger et documenter dans `CHANGELOG.md`
- Si incohérence majeure : stopper et documenter le blocage

---

## Phase 4.2 – Exécution des Tests (DEV)

### Objectif
Générer une newsletter `lai_weekly` en DEV avec les nouveaux scopes LAI.

### Actions

1. **Packaging de la Lambda**
   ```powershell
   .\scripts\package-engine.ps1
   ```
   - Vérifie que le code source est bien empaqueté
   - Produit : `lambda-package.zip`

2. **Déploiement en DEV**
   ```powershell
   .\scripts\deploy-runtime-dev.ps1
   ```
   - Déploie la Lambda sur `vectora-inbox-engine-dev`
   - Met à jour les configurations S3 (scopes, scoring, client config)

3. **Exécution du test `lai_weekly`**
   ```powershell
   .\scripts\test-engine-lai-weekly.ps1
   ```
   - Paramètres :
     - Environnement : DEV
     - Client : `lai_weekly`
     - Fenêtre : 7 jours (lookback)
   - Produit : newsletter dans `s3://vectora-inbox-newsletters-dev/lai_weekly/YYYY/MM/DD/newsletter.md`

4. **Collecte des logs et métriques**
   - Logs CloudWatch : temps d'exécution, nombre d'items analysés, matchés, sélectionnés
   - Localisation exacte de la newsletter dans S3
   - Sauvegarder dans `docs/diagnostics/vectora_inbox_lai_mvp_phase4_test_logs.md`

### Critères de succès
- Newsletter générée sans erreur
- Au moins 3 items sélectionnés
- Temps d'exécution < 5 minutes

### Plan B en cas d'échec
- Si erreur Lambda : vérifier les logs CloudWatch, corriger le code, redéployer
- Si 0 items sélectionnés : vérifier les scopes (trop restrictifs ?), ajuster si nécessaire
- Si timeout : augmenter le timeout Lambda (actuellement 300s)

---

## Phase 4.3 – Analyse des Résultats & Métriques

### Objectif
Évaluer la qualité de la newsletter générée selon les critères MVP LAI.

### Actions

1. **Télécharger la newsletter depuis S3**
   - Localisation : `s3://vectora-inbox-newsletters-dev/lai_weekly/YYYY/MM/DD/newsletter.md`

2. **Analyser chaque item sélectionné**
   - Pour chaque item, déterminer :
     - **LAI ou non** : l'item concerne-t-il vraiment les LAI ?
     - **Pure player ou non** : la company est-elle dans `lai_companies_mvp_core` ?
     - **Faux positif** : l'item est-il clairement hors scope LAI ?

3. **Calculer les métriques**
   - **Précision LAI** = (nombre d'items LAI) / (nombre total d'items) × 100
   - **Proportion pure players** = (nombre d'items pure players) / (nombre total d'items) × 100
   - **Faux positifs** = nombre d'items clairement hors LAI

4. **Documenter dans `docs/diagnostics/vectora_inbox_lai_mvp_focus_results.md`**
   - Tableau synthétique des items sélectionnés
   - Métriques calculées
   - Comparaison avec les objectifs MVP

5. **Si objectifs non atteints**
   - Ajouter une section "Propositions d'ajustement rapide" (1–3 actions max)
   - Ne PAS implémenter ces ajustements dans cette phase

### Critères de succès
- Précision LAI ≥ 75%
- Proportion pure players ≥ 40%
- Faux positifs ≤ 1

### Plan B en cas d'échec
- Documenter les écarts dans `vectora_inbox_lai_mvp_focus_results.md`
- Proposer des ajustements rapides (ex : affiner les scopes, ajuster les règles de scoring)
- Ne pas itérer immédiatement (garder le scope de la Phase 4 sous contrôle)

---

## Phase 4.4 – Documentation Finale & Décision d'Acceptation

### Objectif
Produire une décision claire : MVP LAI accepté ou à ajuster.

### Actions

1. **Compléter `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md`**
   - Résumé exécutif avant/après recentrage
   - Métriques finales (précision LAI, pure players, faux positifs)
   - **Décision explicite** :
     - "MVP LAI – DEV : ACCEPTÉ" si tous les critères sont atteints
     - "MVP LAI – DEV : À AJUSTER" si au moins un critère n'est pas atteint
   - Justification courte, chiffrée

2. **Mettre à jour `CHANGELOG.md`**
   - Nouvelle entrée décrivant :
     - Exécution Phase 4
     - Résultats principaux (précision LAI, pure players, faux positifs)
     - Statut final du MVP `lai_weekly` en DEV

3. **Archiver les artefacts de test**
   - Newsletter générée (copie locale)
   - Logs CloudWatch (copie locale)
   - Métriques calculées

### Critères de succès
- Documentation complète et claire
- Décision d'acceptation explicite et justifiée

### Plan B en cas d'échec
- Si documentation incomplète : compléter avant de clore la Phase 4

---

## Contraintes et Limites

- **Environnement** : DEV uniquement, pas de déploiement STAGE/PROD
- **Client** : `lai_weekly` uniquement
- **Coûts** : 1 run de 7 jours, pas de boucles infinies
- **Scope** : Validation MVP, pas de refactoring majeur

---

## Livrables Attendus

1. `docs/design/vectora_inbox_lai_mvp_phase4_execution_plan.md` (ce fichier)
2. `docs/diagnostics/vectora_inbox_lai_mvp_phase4_test_logs.md` (logs de test)
3. `docs/diagnostics/vectora_inbox_lai_mvp_focus_results.md` (analyse des résultats)
4. `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md` (décision finale)
5. `CHANGELOG.md` (mise à jour)

---

## Timeline Estimée

- Phase 4.1 : 15 minutes
- Phase 4.2 : 30 minutes (packaging, déploiement, test)
- Phase 4.3 : 30 minutes (analyse, calcul métriques)
- Phase 4.4 : 15 minutes (documentation finale)

**Total** : ~1h30

---

**Prochaine étape** : Exécution de la Phase 4.1 – Préparation & Sanity Checks
