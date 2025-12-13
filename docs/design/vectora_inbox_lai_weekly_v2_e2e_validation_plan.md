# Plan d'Audit End-to-End : Vectora Inbox avec lai_weekly_v2

## Contexte

### Client de référence : lai_weekly_v2
- **Vertical** : Long-Acting Injectables (LAI)
- **Scope** : Global, écosystème complet LAI
- **Sources** : 8 sources (5 corporate + 3 presse)
- **Nouveautés v2** : Traitement privilégié des trademarks, profils explicites, scoring différencié

### Configuration actuelle
- **Domaines surveillés** : tech_lai_ecosystem (principal) + regulatory_lai (secondaire)
- **Scopes** : companies (pure_players + hybrid), molecules, trademarks (80+), technology (complex)
- **Matching** : balanced avec privileges trademarks
- **Scoring** : bonus pure_players (5.0), trademarks (4.0), hybrid (1.5)
- **Newsletter** : 4 sections, 15 items max

## Objectifs de l'audit

1. **Photo complète du pipeline** : Ingestion → Normalisation → Matching → Scoring → Newsletter
2. **Analyse critique** : Bruit vs signal, pilotage par config, points fragiles
3. **Leviers d'action** : Recommandations concrètes par étape

---

## Phase 0 : SSO & Prérequis AWS

### Objectif
**CRITIQUE** : Toutes les phases utilisant AWS DEV nécessitent un token SSO valide. Aucune simulation n'est autorisée.

### Prérequis obligatoires
1. **Profil CLI valide** : `rag-lai-prod`
2. **Token SSO rafraîchi** pour eu-west-3
3. **Vérification de connectivité** AWS

### Commandes à exécuter (PowerShell)
```powershell
# 1) Vérifier les profils disponibles
aws configure list-profiles

# 2) Rafraîchir le SSO pour le profil utilisé par Vectora Inbox
aws sso login --profile rag-lai-prod

# 3) Vérifier que l'appel simple fonctionne
aws sts get-caller-identity --profile rag-lai-prod --region eu-west-3
```

### Règle de blocage
**Si `aws sts get-caller-identity` renvoie une erreur de token :**
- ❌ **AUCUNE simulation autorisée**
- ❌ **AUCUN diagnostic basé sur des fichiers historiques**
- ✅ **Blocage explicite** : "Token AWS SSO expiré, merci d'exécuter les commandes ci-dessus puis me dire quand c'est fait."

### Validation
Le token est valide quand la commande retourne :
```json
{
    "UserId": "...",
    "Account": "...",
    "Arn": "arn:aws:sts::..."
}
```

---

## Phase 1 : Sanity Check Configuration & Canonical

### Objectif
Vérifier la cohérence entre client_config et canonical, identifier les zones ambiguës.

### Actions
1. **Analyse client-config lai_weekly_v2.yaml**
   - Watch_domains : cohérence des scopes référencés
   - Source_config : bouquets activés vs source_catalog
   - Matching_config : trademark_privileges et overrides
   - Scoring_config : bonus et seuils

2. **Cross-check avec canonical**
   - `canonical/scopes/*` : vérifier existence des scopes référencés
   - `canonical/ingestion/ingestion_profiles.yaml` : profils utilisés
   - `canonical/sources/source_catalog.yaml` : bouquets lai_*_mvp
   - `canonical/matching/domain_matching_rules.yaml` : règles technology_complex
   - `canonical/scoring/scoring_rules.yaml` : bonus pure_players/trademarks

3. **Diagnostic de cohérence**
   - ✅ Éléments bien câblés
   - ⚠️ Zones ambiguës ou redondantes
   - 🔴 Incohérences détectées

### Livrable
`docs/diagnostics/vectora_inbox_lai_weekly_v2_phase1_sanity_check.md`

---

## Phase 2 : Ingestion DEV (Scraping + Ingestion Profiles)

### Objectif
Comprendre précisément l'ingestion pour lai_weekly_v2, mesurer bruit vs signal.

### Actions
1. **Lancement ingest-normalize en DEV** (⚠️ **REQUIS : SSO valide**)
   ```powershell
   aws lambda invoke `
     --function-name vectora-inbox-ingest-normalize-dev `
     --payload '{"client_id":"lai_weekly_v2","period_days":30}' `
     --cli-binary-format raw-in-base64-out `
     --profile rag-lai-prod `
     --region eu-west-3 `
     out_ingest_lai_weekly_v2_dev_$(Get-Date -Format 'yyyyMMdd-HHmmss').json
   ```

2. **Mesures quantitatives** (basées sur exécution réelle uniquement)
   - Par source (8 sources) : items bruts → filtrés → envoyés Bedrock
   - Par type : corporate_pure_player_broad, corporate_hybrid_*, press_technology_focused
   - Économies Bedrock réelles mesurées

3. **Analyse qualitative** (objets S3 réels)
   - Chemin S3 exact : `s3://vectora-inbox-data-dev/normalized/lai_weekly_v2/YYYY/MM/DD/`
   - 2-3 items pertinents LAI qui passent
   - 2-3 items bruit qui passent (faux positifs)
   - 2-3 items LAI rejetés à tort (si détectés)

### Livrable
`docs/diagnostics/vectora_inbox_lai_weekly_v2_phase2_ingestion_results.md`

---

## Phase 3 : Normalisation (Bedrock, Open-World, Entités)

### Objectif
Évaluer la qualité de la normalisation Bedrock sur échantillon représentatif.

### Actions (⚠️ **REQUIS : Exécution Phase 2 réussie**)
1. **Échantillonnage réel**
   - Lecture objets S3 : `s3://vectora-inbox-data-dev/normalized/lai_weekly_v2/YYYY/MM/DD/items.json`
   - Date/heure exacte du run Phase 2
   - Représentatif des 8 sources (pas de fichiers historiques)

2. **Analyse entités** (données fraîches uniquement)
   - *_detected vs *_in_scopes pour : companies, molecules, trademarks, technologies, indications
   - Cas open-world utiles vs entités LAI manquées
   - Exemples concrets : Brixadi vs buprenorphine vs LAI génériques

3. **Métriques qualité** (calculées sur run réel)
   - Taux détection entités clés LAI
   - Taux entités hors scopes pertinentes
   - Cohérence avec scopes canonical

### Livrable
`docs/diagnostics/vectora_inbox_lai_weekly_v2_phase3_normalization_results.md`

---

## Phase 4 : Matching + Scoring + Newsletter

### Objectif
Analyser ce qui survit jusqu'à la newsletter et comprendre les mécanismes.

### Actions (⚠️ **REQUIS : SSO valide + Phase 2 terminée**)
1. **Exécution engine complet** (commande réelle)
   ```powershell
   aws lambda invoke `
     --function-name vectora-inbox-engine-dev `
     --payload '{"client_id":"lai_weekly_v2"}' `
     --cli-binary-format raw-in-base64-out `
     --profile rag-lai-prod `
     --region eu-west-3 `
     out_engine_lai_weekly_v2_dev_$(Get-Date -Format 'yyyyMMdd-HHmmss').json
   ```

2. **Analyse quantitative** (résultats réels uniquement)
   - Items analysés → matchés → sélectionnés (chiffres exacts du run)
   - Répartition par domaine tech LAI (données fraîches)
   - % pure players vs hybrid, impact trademarks (mesuré réellement)

3. **Évaluation newsletter** (générée en DEV)
   - Chemin S3 : `s3://vectora-inbox-data-dev/newsletters/lai_weekly_v2/YYYY/MM/DD/`
   - Qualité métier : ressemble-t-elle à une vraie newsletter LAI ?
   - Items bons/borderline/mauvais par section
   - Sections bien/mal remplies

4. **Analyse des mécanismes** (basée sur exécution réelle)
   - Impact visible bonus trademarks (4.0)
   - Impact bonus pure_players (5.0) vs hybrid (1.5)
   - Rôle technology_complex dans matching

### Livrable
`docs/diagnostics/vectora_inbox_lai_weekly_v2_phase4_matching_scoring_newsletter_results.md`

---

## Phase 5 : Synthèse & Recommandations

### Objectif
Executive summary avec leviers d'action concrets.

### Actions
1. **Tableau de synthèse**
   - Par étape : Qualité → Problèmes → 3 leviers concrets
   - Ingestion, Normalisation, Matching, Scoring, Newsletter

2. **Conclusion métier**
   - Pipeline bien conçu et pilotable ?
   - 3 priorités pour : moins de bruit, plus de signal, produit vendable

3. **Relations de dépendance**
   - "Si je touche X → impact Y, Z"
   - Ordre d'intervention optimal

### Livrable
`docs/diagnostics/vectora_inbox_lai_weekly_v2_e2e_validation_executive_summary.md`

---

## Environnement d'exécution

- **AWS Profile** : rag-lai-prod (⚠️ **SSO requis**)
- **Région** : eu-west-3
- **Environnement** : DEV
- **Client** : lai_weekly_v2
- **Mode** : Audit uniquement (pas de modifications code/infra)
- **Exécutions réelles uniquement** : Aucune simulation autorisée

## Timeline estimée

- Phase 1 : 30 min (config analysis)
- Phase 2 : 45 min (ingestion + analysis)
- Phase 3 : 30 min (normalization analysis)
- Phase 4 : 45 min (engine + newsletter analysis)
- Phase 5 : 30 min (synthesis)

**Total** : ~3h d'audit complet

---

*Plan créé le 2024-12-19 pour audit lai_weekly_v2 end-to-end*