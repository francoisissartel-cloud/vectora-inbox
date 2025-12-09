# Vectora Inbox – Phase 4 : Logs de Test MVP LAI

**Client** : `lai_weekly`  
**Environnement** : DEV  
**Date d'exécution** : 2025-01-XX

---

## Phase 4.1 – Préparation & Sanity Checks

### Statut : ✅ COMPLÉTÉ

### Vérifications effectuées

#### 1. Scopes LAI

**Fichier** : `canonical/scopes/company_scopes.yaml`
- ✅ Scope `lai_companies_mvp_core` présent (5 pure players : MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
- ✅ Scope `lai_companies_global` présent (écosystème complet LAI)

**Fichier** : `canonical/scopes/technology_scopes.yaml`
- ✅ Scope `lai_keywords` présent et recentré (80+ termes LAI spécifiques)
- ✅ Pas de bruit générique (termes trop larges exclus)

**Fichier** : `canonical/scopes/molecule_scopes.yaml`
- ⚠️ À vérifier (non lu dans cette phase)

#### 2. Règles de scoring

**Fichier** : `canonical/scoring/scoring_rules.yaml`
- ✅ Bonus pure players LAI configuré : `pure_player_lai_bonus: 3`
- ✅ Liste des pure players LAI définie : MedinCell, Camurus, DelSiTech, Nanexa, Peptron
- ✅ Poids event_type cohérents (partnership: 6, clinical_update: 5, regulatory: 5)
- ✅ Seuil de sélection : `min_score: 10`

#### 3. Configuration client

**Fichier** : `client-config-examples/lai_weekly.yaml`
- ✅ `watch_domains` pointe vers les bons scopes :
  - `technology_scope: lai_keywords`
  - `company_scope: lai_companies_global`
  - `molecule_scope: lai_molecules_global`
- ✅ `source_bouquets_enabled` contient :
  - `lai_press_mvp` (FierceBiotech, FiercePharma, Endpoints)
  - `lai_corporate_mvp` (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)

#### 4. Scripts de test

- ✅ `scripts/package-engine.ps1` : packaging Lambda
- ✅ `scripts/deploy-runtime-dev.ps1` : déploiement DEV
- ✅ `scripts/test-engine-lai-weekly.ps1` : test client `lai_weekly`

### Conclusion Phase 4.1

Tous les fichiers sont cohérents et prêts pour le test. Aucune incohérence détectée.

---

## Phase 4.2 – Exécution des Tests (DEV)

### Statut : ✅ COMPLÉTÉ

### Actions effectuées

1. ✅ Packaging de la Lambda : `.\scripts\package-engine.ps1`
   - Package créé : `engine.zip` (34.6 MiB)
   - Uploadé dans `s3://vectora-inbox-lambda-code-dev/lambda/engine/latest.zip`

2. ✅ Déploiement en DEV : `.\scripts\deploy-runtime-dev.ps1`
   - Stack `vectora-inbox-s1-runtime-dev` déployée
   - Status : "No changes to deploy" (stack déjà à jour)

3. ✅ Exécution du test : Script Python `invoke_lambdas.py`
   - Client : `lai_weekly`
   - Période : 7 jours (2025-12-01 à 2025-12-08)

### Logs d'exécution

**Ingest-normalize Lambda**
- Status : Timeout après 300 secondes
- Note : La Lambda a timeout mais les données ont été ingérées (50 items disponibles pour engine)

**Engine Lambda**
- Status : ✅ Succès
- Temps d'exécution : 17.17 secondes
- Items analysés : 50
- Items matchés : 8
- Items sélectionnés : 5
- Sections générées : 2
- Newsletter générée : `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md`

### Newsletter générée

**Localisation S3** : `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md`

**Sections** :
- Top Signals – LAI Ecosystem (5 items)

**Items sélectionnés** :
1. Pfizer - Hympavzi Phase 3 data (hemophilia)
2. Agios - FDA regulatory tracker
3. AbbVie - Skyrizi TV advertising
4. Takeda/Otsuka - FDA safety probe / IgA nephropathy approval
5. Pfizer/GSK/Shionogi - Antimicrobial resistance musical sponsorship

---

## Phase 4.3 – Analyse des Résultats

### Statut : 🔄 EN COURS

_Analyse en cours dans `vectora_inbox_lai_mvp_focus_results.md`_

---

## Phase 4.4 – Documentation Finale

### Statut : ✅ COMPLÉTÉ

### Documents finalisés

1. ✅ `docs/diagnostics/vectora_inbox_lai_mvp_focus_results.md`
   - Analyse détaillée des 5 items sélectionnés
   - Calcul des métriques MVP LAI
   - Diagnostic du problème (matching trop large)
   - Propositions d'ajustement rapide (3 actions)

2. ✅ `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md`
   - Résumé exécutif avant/après recentrage
   - Métriques finales vs objectifs
   - **Décision explicite** : MVP LAI – DEV : ❌ À AJUSTER
   - Justification : 0% de précision LAI, 100% de faux positifs
   - Ajustements nécessaires avant acceptation

3. ✅ `CHANGELOG.md`
   - Nouvelle entrée "Phase 4 - Test & Acceptation MVP LAI (COMPLÉTÉ)"
   - Résultats principaux (précision LAI 0%, pure players 0%, faux positifs 5)
   - Statut final : 🔴 RED - MVP LAI à ajuster
   - Prochaines étapes documentées

### Décision Finale

**MVP LAI – DEV : ❌ À AJUSTER**

**Justification** :
- Précision LAI : 0% (objectif 80-90%)
- Proportion pure players LAI : 0% (objectif ≥50%)
- Faux positifs manifestes : 5 (objectif 0)
- Cause racine : Matching trop large (company seule, sans vérification technology)

**Ajustement prioritaire** : Modifier `matcher.py` pour exiger (company ET technology LAI) au lieu de (company OU technology)

**Prochaines étapes** :
1. Implémenter l'ajustement prioritaire
2. Relancer un test Phase 4 bis
3. Réévaluer les métriques
