# Phase 1 : Sanity Check Configuration & Canonical - lai_weekly_v2

**Date** : 2024-12-19  
**Client** : lai_weekly_v2  
**Objectif** : Vérifier la cohérence entre client_config et canonical, identifier les zones ambiguës

---

## Résumé Exécutif

✅ **Configuration globalement cohérente** : Tous les scopes référencés dans lai_weekly_v2.yaml existent dans le canonical  
⚠️ **Quelques zones d'optimisation** : Redondances dans les scopes, profils d'ingestion à affiner  
🔴 **Aucune incohérence critique** détectée

---

## 1. Analyse Client Config (lai_weekly_v2.yaml)

### 1.1 Watch Domains - ✅ COHÉRENT

**Domaine principal : tech_lai_ecosystem**
- `company_scope: "lai_companies_global"` → ✅ Existe dans canonical/scopes/company_scopes.yaml (200+ entreprises)
- `molecule_scope: "lai_molecules_global"` → ✅ Existe dans canonical/scopes/molecule_scopes.yaml (80+ molécules)
- `technology_scope: "lai_keywords"` → ✅ Existe dans canonical/scopes/technology_scopes.yaml
- `trademark_scope: "lai_trademarks_global"` → ✅ Existe dans canonical/scopes/trademark_scopes.yaml (80+ marques)
- `technology_profile: "technology_complex"` → ✅ Défini dans canonical/matching/domain_matching_rules.yaml
- `matching_profile: "balanced"` → ✅ Référencé dans matching_config

**Domaine secondaire : regulatory_lai**
- Même cohérence, scopes identiques au domaine principal

### 1.2 Source Config - ✅ COHÉRENT

**Bouquets activés :**
- `lai_corporate_mvp` → ✅ Défini dans source_catalog.yaml (5 sources corporate)
- `lai_press_mvp` → ✅ Défini dans source_catalog.yaml (3 sources presse)

**Sources couvertes (8 total) :**
- **Corporate (5)** : MedinCell, Camurus, DelSiTech, Nanexa, Peptron
- **Presse (3)** : FierceBiotech, FiercePharma, Endpoints

### 1.3 Matching Config - ✅ BIEN CONÇU

**Trademark privileges :**
- `enabled: true` avec `boost_factor: 2.5` → Logique cohérente avec lai_trademarks_global (80+ marques)
- `auto_match_threshold: 0.8` → Seuil raisonnable

**Domain type overrides :**
- Technology : `require_entity_signals: true`, `min_technology_signals: 2` → Règles strictes cohérentes avec technology_complex
- Regulatory : `require_entity_signals: false`, `min_technology_signals: 1` → Plus souple, logique

### 1.4 Scoring Config - ✅ BIEN CALIBRÉ

**Bonus hiérarchisés :**
- Pure players (5.0) > Trademarks (4.0) > Molécules (2.5) > Hybrid (1.5) → Logique métier cohérente
- Scopes référencés : tous existent dans canonical

---

## 2. Cross-Check avec Canonical

### 2.1 Scopes - ✅ TOUS COHÉRENTS

| Scope référencé | Fichier canonical | Contenu | Status |
|---|---|---|---|
| `lai_companies_global` | company_scopes.yaml | 200+ entreprises | ✅ |
| `lai_companies_mvp_core` | company_scopes.yaml | 5 pure players | ✅ |
| `lai_companies_hybrid` | company_scopes.yaml | 27 big pharma | ✅ |
| `lai_molecules_global` | molecule_scopes.yaml | 80+ molécules | ✅ |
| `lai_keywords` | technology_scopes.yaml | Structure complexe | ✅ |
| `lai_trademarks_global` | trademark_scopes.yaml | 80+ marques | ✅ |

### 2.2 Ingestion Profiles - ✅ BIEN MAPPÉS

**Profils utilisés par les sources :**
- `corporate_pure_player_broad` → Utilisé par les 5 sources corporate (MedinCell, Camurus, etc.)
- `press_technology_focused` → Utilisé par les 3 sources presse (FierceBiotech, etc.)

**Cohérence avec scopes :**
- corporate_pure_player_broad référence `lai_companies_pure_players` ✅
- press_technology_focused référence `lai_companies_global`, `lai_molecules_global`, `lai_trademarks_global` ✅

### 2.3 Matching Rules - ✅ TECHNOLOGY_COMPLEX BIEN DÉFINI

**Profile technology_complex :**
- Signal requirements : high_precision + supporting + context ✅
- Entity requirements : min 1 match company/molecule ✅
- Pure player vs hybrid logic : différenciation claire ✅
- Negative filters : exclusions explicites ✅

### 2.4 Scoring Rules - ✅ BONUS ALIGNÉS

**Bonus canonical vs client_config :**
- `pure_player_bonus: 3` (canonical) vs `5.0` (client) → Client override plus agressif ✅
- `pure_player_scope: "lai_companies_mvp_core"` → Cohérent avec client ✅

---

## 3. Zones d'Optimisation ⚠️

### 3.1 Redondances dans les Scopes

**lai_companies_global vs autres scopes :**
- `lai_companies_global` (200+) inclut `lai_companies_mvp_core` (5) et `lai_companies_hybrid` (27)
- Risque de double comptage dans le scoring
- **Recommandation** : Clarifier la hiérarchie des bonus (pure_player > hybrid > global)

### 3.2 Technology_scope lai_keywords - Structure Complexe

**Structure actuelle :**
- 6 catégories : core_phrases, technology_terms_high_precision, technology_use, route_admin_terms, interval_patterns, generic_terms
- Catégorie `generic_terms` marquée comme "ne matchent plus seuls"
- **Recommandation** : Valider que le runtime respecte bien cette logique

### 3.3 Profils d'Ingestion - Seuils à Valider

**press_technology_focused :**
- `combination_logic: "entity_signals AND (technology_signals OR trademark_signals)"`
- `minimum_total_weight: 3.0`
- **Recommandation** : Tester en DEV si ces seuils ne sont pas trop restrictifs

### 3.4 Newsletter Layout - Sections Potentiellement Redondantes

**4 sections définies :**
- top_signals (tech_lai_ecosystem + regulatory_lai)
- partnerships_deals (tech_lai_ecosystem uniquement)
- regulatory_updates (regulatory_lai uniquement)
- clinical_updates (tech_lai_ecosystem uniquement)

**Risque** : Items peuvent apparaître dans plusieurs sections
**Recommandation** : Clarifier la logique de déduplication

---

## 4. Points Forts ✅

### 4.1 Configuration v2 Bien Pensée

- **Trademark privileges** : Innovation v2 bien intégrée
- **Profils explicites** : technology_complex, matching balanced
- **Bonus différenciés** : Pure players vs hybrid vs global
- **4 sections newsletter** : Couverture complète LAI

### 4.2 Canonical Bien Structuré

- **Scopes exhaustifs** : 200+ entreprises, 80+ molécules, 80+ marques
- **Profils d'ingestion** : Différenciation corporate vs presse
- **Technology_complex** : Logique multi-signaux sophistiquée
- **Scoring rules** : Facteurs métier pertinents

### 4.3 Cohérence Globale

- Tous les scopes référencés existent
- Profils d'ingestion bien mappés aux sources
- Bonus scoring alignés avec la stratégie métier
- Configuration pilotable par canonical

---

## 5. Leviers d'Action Identifiés

### 5.1 Ingestion (Priorité 1)
- **Tester les seuils** press_technology_focused en DEV
- **Valider** que corporate_pure_player_broad n'est pas trop permissif
- **Mesurer** l'économie Bedrock réelle

### 5.2 Canonical (Priorité 2)
- **Clarifier** la hiérarchie des company_scopes (global > hybrid > pure_player)
- **Documenter** la logique technology_complex pour les futurs utilisateurs
- **Simplifier** les generic_terms si non utilisés

### 5.3 Client Config (Priorité 3)
- **Optimiser** les bonus scoring selon les résultats DEV
- **Ajuster** les seuils matching selon le bruit/signal observé
- **Clarifier** la déduplication entre sections newsletter

---

## Conclusion Phase 1

**Status** : ✅ Configuration lai_weekly_v2 prête pour les tests DEV

**Points forts** :
- Cohérence complète entre client_config et canonical
- Innovation v2 (trademarks, profils) bien intégrée
- Configuration pilotable et évolutive

**Prochaines étapes** :
- Phase 2 : Tester l'ingestion en DEV avec ces configurations
- Valider que les seuils théoriques fonctionnent en pratique
- Mesurer l'impact réel des profils d'ingestion sur le bruit/signal

---

*Diagnostic Phase 1 terminé - Prêt pour Phase 2 (Ingestion DEV)*