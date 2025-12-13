# Vectora Inbox LAI Weekly v3 - Configuration Snapshot

**Date** : 2025-12-11  
**Client** : lai_weekly_v3  
**Base** : lai_weekly_v2.yaml (copie exacte + ajustements mineurs)  
**Objectif** : Banc d'essai pour run end-to-end avec observabilité maximale

---

## Vue d'Ensemble

**lai_weekly_v3** est une configuration expérimentale créée pour servir de banc d'essai pour un run end-to-end complet en DEV. Elle reprend intégralement la configuration lai_weekly_v2 avec des ajustements mineurs documentés.

**Mode** : Observabilité & calibration (pas de modification logique métier)

---

## Paramètres Clés

### Pipeline Configuration
- **default_period_days** : `30` (identique v2)
- **Justification** : Fenêtre étendue pour capturer signaux LAI sur cycle long
- **Impact** : Ingestion sur 30 jours glissants

### Watch Domains

#### Domaine Principal : tech_lai_ecosystem
- **Type** : `technology`
- **Priority** : `high`
- **Scopes** :
  - `technology_scope`: "lai_keywords"
  - `company_scope`: "lai_companies_global"
  - `molecule_scope`: "lai_molecules_global"
  - `trademark_scope`: "lai_trademarks_global"
- **Profils** :
  - `technology_profile`: "technology_complex"
  - `matching_profile`: "balanced"

#### Domaine Secondaire : regulatory_lai
- **Type** : `regulatory`
- **Priority** : `high`
- **Scopes** : technology + company + trademark (pas molecule)
- **Matching** : "broad" (plus souple que tech)

### Source Configuration

#### Bouquets Activés
1. **lai_corporate_mvp** : 5 sources corporate LAI
   - MedinCell, Camurus, DelSiTech, Nanexa, Peptron
2. **lai_press_mvp** : 3 sources presse sectorielle
   - FierceBiotech, FiercePharma, Endpoints

#### Profils d'Ingestion
- **Utilisation** : Profils canonical par défaut
- **Overrides** : Aucun (bouquet_ingestion_overrides: {})
- **Sources extra** : Aucune

### Matching Configuration

#### Règles par Type de Domaine
- **Technology** :
  - `require_entity_signals`: true
  - `min_technology_signals`: 2
- **Regulatory** :
  - `require_entity_signals`: false
  - `min_technology_signals`: 1

#### Trademark Privileges (Activé)
- **auto_match_threshold** : 0.8
- **boost_factor** : 2.5
- **ingestion_priority** : true
- **matching_priority** : true

### Scoring Configuration

#### Event Type Weights
- **partnership** : 8 (très important LAI)
- **regulatory** : 7 (approvals, CRL)
- **clinical_update** : 6 (résultats cruciaux)
- **scientific_publication** : 4

#### Bonus Spécifiques LAI
1. **Pure Players** : 5.0 (scope: lai_companies_mvp_core)
2. **Trademarks** : 4.0 (scope: lai_trademarks_global)
3. **Molecules** : 2.5 (scope: lai_molecules_global)
4. **Hybrid Companies** : 1.5 (scope: lai_companies_hybrid)

#### Seuils de Sélection
- **min_score** : 12 (strict pour qualité)
- **min_items_per_section** : 1
- **max_items_total** : 15 (newsletter concise)

### Newsletter Layout

#### 4 Sections Configurées
1. **Top Signals** : 5 items max, tri par score
2. **Partnerships & Deals** : 5 items max, tri par date
3. **Regulatory Updates** : 5 items max, tri par score
4. **Clinical Updates** : 8 items max, tri par date

---

## Ajustements v2 → v3

### Modifications Mineures
- **client_id** : "lai_weekly_v2" → "lai_weekly_v3"
- **client_profile.name** : Ajout "(Test Bench)"
- **notification_email** : "lai-weekly-v3@vectora.com"
- **template_version** : "2.0.0" → "3.0.0"
- **Dates** : Création/modification mises à jour (2025-12-11)
- **Notes** : Ajustées pour contexte v3 test bench

### Configuration Identique v2
✅ **watch_domains** : Scopes et profils identiques  
✅ **source_config** : Bouquets et overrides identiques  
✅ **matching_config** : Règles et privileges identiques  
✅ **scoring_config** : Bonus et seuils identiques  
✅ **newsletter_layout** : Structure et sections identiques  
✅ **pipeline.default_period_days** : 30 (inchangé)

---

**Phase 1 terminée, je passe à la Phase 2.**