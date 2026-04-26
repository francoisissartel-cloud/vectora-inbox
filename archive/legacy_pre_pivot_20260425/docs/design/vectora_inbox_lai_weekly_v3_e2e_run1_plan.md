# Vectora Inbox LAI Weekly v3 - Plan Run End-to-End #1

**Date** : 2025-12-11  
**Objectif** : Run complet lai_weekly_v3 en DEV avec métriques détaillées et estimation coûts  
**Mode** : Observabilité & calibration (pas de modification logique métier)

---

## Vue d'Ensemble

**lai_weekly_v3** est une copie expérimentale de lai_weekly_v2 pour servir de banc d'essai. Configuration identique (scopes, profils ingestion, pipeline) sauf ajustements mineurs documentés.

**Workflow complet** : Ingestion → Normalisation → Matching → Scoring → Newsletter

**Environnement** : vectora-inbox-dev (bucket/config standard)

---

## Phase 0 - Plan dans /docs ✅

**Objectif** : Structurer le run par phases avec points de reprise clairs

**Fichiers impliqués** :
- `docs/design/vectora_inbox_lai_weekly_v3_e2e_run1_plan.md` (ce fichier)

**Artefacts attendus** :
- Plan détaillé avec phases 0-6
- Points de reprise explicites
- Métriques attendues par phase

---

## Phase 1 - Création Client lai_weekly_v3 (Repo)

**Objectif** : Dupliquer lai_weekly_v2 → créer config lai_weekly_v3 côté repo

**Fichiers impliqués** :
- `client-config-examples/lai_weekly_v3.yaml` (nouveau)
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_config_snapshot.md` (nouveau)

**Actions** :
1. Copier lai_weekly_v2.yaml → lai_weekly_v3.yaml
2. Conserver tous paramètres v2 :
   - `watch_domains` (technology_scope, trademark_scope, etc.)
   - `source_config` (bouquets sources)
   - `pipeline.default_period_days`
   - `matching_config`, `scoring_config`
   - `trademark_privileges`
3. Ajustements mineurs si nécessaires (documentés)

**Artefacts attendus** :
- Config lai_weekly_v3.yaml fonctionnelle
- Diagnostic config avec résumé paramètres clés
- Comparaison v2 vs v3 (si différences)

**Point de reprise** : "Phase 1 terminée, je passe à la Phase 2."

---

## Phase 2 - Synchronisation S3 / Création Client AWS DEV

**Objectif** : Rendre lai_weekly_v3 disponible pour Lambdas en DEV

**Fichiers impliqués** :
- Bucket S3 vectora-inbox-dev
- Chemin client config (pattern standard)

**Actions** :
1. Synchroniser lai_weekly_v3.yaml vers S3 DEV
2. Vérifier accessibilité par Lambdas
3. Documenter chemin S3 exact et méthode sync

**Artefacts attendus** :
- Config lai_weekly_v3 présente en S3 DEV
- Documentation chemin S3 et commande sync
- Vérification droits d'accès Lambda

**Point de reprise** : "Phase 2 terminée, je passe à la Phase 3."

---

## Phase 3 - Run Ingestion + Normalisation

**Objectif** : Lancer ingestion+normalisation lai_weekly_v3 avec métriques détaillées

**Lambdas impliquées** :
- Lambda ingestion/normalisation (vectora-inbox-dev)

**Actions** :
1. Lancer Lambda avec period_days de la config v3
2. Collecter métriques par source et globalement
3. Analyser erreurs et patterns

**Métriques attendues** :
- **Par source** :
  - `source_key`
  - `ingestion_profile` utilisé
  - `items_raw` (récupérés)
  - `items_after_ingestion_filter` (post-profil)
  - `items_sent_to_bedrock`
  - `items_normalized_success`
  - Erreurs principales (HTML, SSL, Bedrock, timeouts)

- **Globalement** :
  - Nombre sources activées vs contactées
  - Taux de succès normalisation
  - Volume tokens Bedrock approximatif
  - Durée d'exécution

**Artefacts attendus** :
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_phase3_ingestion_and_normalization.md`
- Métriques détaillées par source
- Analyse erreurs et patterns

**Point de reprise** : "Phase 3 terminée, je passe à la Phase 4."

---

## Phase 4 - Run Engine (Matching + Scoring + Newsletter)

**Objectif** : Exécuter Lambda engine avec traçage précis de chaque sous-phase

**Lambdas impliquées** :
- Lambda engine (vectora-inbox-dev)

**Actions** :
1. Lancer Lambda engine avec period_days cohérent
2. Tracer matching, scoring, newsletter séparément
3. Analyser distribution et patterns

**Métriques attendues** :

### 4.1 Matching
- `items_analyzed` (total items normalisés)
- `items_matched` par domaine (ex: tech_lai_ecosystem)
- Répartition par `event_type`
- Taux de match global (%)

### 4.2 Scoring
- Distribution scores (min, max, moyenne, médiane)
- Bonus appliqués :
  - `pure_player_bonus`
  - `trademark_bonus`
  - Autres bonus contextuels
- Items passant seuils finaux par niveau

### 4.3 Newsletter
- `items_selected` par section
- Titre newsletter généré
- Sections créées avec nombre d'items
- Items exclus et raisons

**Artefacts attendus** :
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_phase4_engine_and_newsletter.md`
- Analyse comportement observé
- Forces (calibrage correct)
- Faiblesses (sections vides, biais, seuils)

**Point de reprise** : "Phase 4 terminée, je passe à la Phase 5."

---

## Phase 5 - Estimation Coût Workflow

**Objectif** : Estimer coût complet run lai_weekly_v3 et projections scale

**Actions** :
1. Calculer coûts run actuel
2. Projeter coûts récurrents
3. Estimer scale-up LAI complet

**Métriques attendues** :

### 5.1 Coût Run Actuel
- Appels Bedrock (normalisation + newsletter)
- Volume tokens approximatif
- Coût estimé $ (modèles réels utilisés)
- Durée exécution globale

### 5.2 Projections
- Coût par run lai_weekly_v3
- Coût mensuel (4 runs/mois)
- Coût scale LAI complet (hypothèses documentées)

**Artefacts attendus** :
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_phase5_cost_estimate.md`
- Hypothèses explicites
- Formules de calcul
- Scénarios DEV vs PROD

**Point de reprise** : "Phase 5 terminée, je passe à la Phase 6."

---

## Phase 6 - Synthèse & Pistes d'Amélioration

**Objectif** : Executive summary et recommandations architecte

**Actions** :
1. Synthétiser toutes les phases
2. Identifier forces/faiblesses workflow
3. Proposer pistes d'amélioration priorisées

**Artefacts attendus** :
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_e2e_run1_executive_summary.md`

### 6.1 Contenu Executive Summary
- Résumé clair chaque phase
- Métriques principales (items, ratios, coûts)
- Forces workflow actuel
- Points faibles / risques
- Pistes d'amélioration :
  - **P0** : Rapides, impact fort
  - **P1** : Améliorations de fond
  - **P2** : Idées scalabilité

### 6.2 Recommandations Console
- Résumé très court (10 lignes max)
- Points prioritaires pour travail ensemble
- Focus : scopes tech, sections newsletter, profils ingestion, etc.

**Point de reprise** : "Phase 6 terminée - Run end-to-end complet."

---

## Notes Importantes

### Configuration lai_weekly_v3
- **Base** : Copie exacte lai_weekly_v2
- **Ajustements** : Uniquement si justifiés et documentés
- **Paramètres clés** : Conserver period_days, watch_domains, profils ingestion

### Mode Observabilité
- **Pas de modification** logique métier (canonical, scoring, matching)
- **Exception** : Bugs bloquants identifiés et documentés
- **Focus** : Mesurer et observer, pas retoucher

### Points de Reprise
- Chaque phase annoncée explicitement
- Structure permet reprise à n'importe quelle phase
- Artefacts documentés pour traçabilité

---

**Status** : Phase 0 terminée ✅