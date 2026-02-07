# Architecture Moteur Ingestion 100% Canonical

**Date**: 2026-02-06  
**Statut**: Design validé - En attente d'implémentation  
**Objectif**: Moteur d'ingestion générique piloté à 100% par fichiers canonical

---

## 🎯 Principe Fondamental

**Le moteur d'ingestion ne contient AUCUNE logique métier hardcodée.**

Toute la logique de filtrage est externalisée dans les fichiers canonical :
- `canonical/scopes/exclusion_scopes.yaml` → Termes à exclure
- `canonical/scopes/company_scopes.yaml` → Pure/hybrid players
- `canonical/scopes/technology_scopes.yaml` → LAI keywords
- `canonical/scopes/trademark_scopes.yaml` → LAI trademarks
- `canonical/ingestion/ingestion_profiles.yaml` → Règles de filtrage

---

## 📐 Architecture Cible

```
┌─────────────────────────────────────────────────────────────┐
│                    Lambda Ingest V2                         │
│                                                             │
│  ┌───────────────────────────────────────────────────┐    │
│  │  vectora_core/ingest/__init__.py                  │    │
│  │                                                     │    │
│  │  1. Chargement configurations                      │    │
│  │  2. Initialisation scopes depuis S3:               │    │
│  │     - initialize_exclusion_scopes()                │    │
│  │     - initialize_company_scopes()                  │    │
│  │     - initialize_lai_keywords()                    │    │
│  │  3. Ingestion sources                              │    │
│  │  4. Application profils                            │    │
│  └───────────────────────────────────────────────────┘    │
│                           │                                 │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────┐    │
│  │  vectora_core/ingest/ingestion_profiles.py        │    │
│  │                                                     │    │
│  │  Caches globaux (chargés au démarrage):            │    │
│  │  - _exclusion_scopes_cache                         │    │
│  │  - _pure_players_cache                             │    │
│  │  - _hybrid_players_cache                           │    │
│  │  - _lai_keywords_cache                             │    │
│  │                                                     │    │
│  │  Logique de filtrage:                              │    │
│  │  - _apply_corporate_profile()                      │    │
│  │    ├─ Pure player → exclusions seules              │    │
│  │    └─ Hybrid player → exclusions + LAI keywords    │    │
│  │  - _apply_press_profile()                          │    │
│  │    └─ Presse → exclusions + LAI keywords           │    │
│  └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    S3 Canonical Bucket                      │
│                                                             │
│  canonical/scopes/                                          │
│  ├─ exclusion_scopes.yaml (8 scopes, 150+ termes)          │
│  ├─ company_scopes.yaml (14 pure + 27 hybrid)              │
│  ├─ technology_scopes.yaml (LAI keywords)                   │
│  └─ trademark_scopes.yaml (LAI trademarks)                  │
│                                                             │
│  canonical/ingestion/                                       │
│  └─ ingestion_profiles.yaml (règles de filtrage)           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flux de Filtrage

### 1. Initialisation (au démarrage Lambda)

```python
# __init__.py ligne 87-91
initialize_exclusion_scopes(s3_io, config_bucket)
initialize_company_scopes(s3_io, config_bucket)
initialize_lai_keywords(s3_io, config_bucket)
```

**Résultat**: Caches globaux remplis avec données canonical

---

### 2. Filtrage Corporate (Pure Players)

**Exemple**: MedinCell, Camurus, DelSiTech

```yaml
# ingestion_profiles.yaml
pure_players:
  company_scope: "lai_companies_pure_players"
  ingestion_mode: "permissive"
  apply_exclusions: true
  exclusion_scopes: [hr_content, financial_generic, ...]
  require_lai_keywords: false  # ← Pas de filtrage LAI
```

**Logique**:
```python
if _is_pure_player(company_id):
    # Exclusions seules (bruit évident)
    return _filter_by_exclusions_only(items)
```

**Items conservés**: Tout sauf bruit RH/financier/événementiel

---

### 3. Filtrage Corporate (Hybrid Players)

**Exemple**: Teva, Pfizer, Novartis

```yaml
# ingestion_profiles.yaml
hybrid_players:
  company_scope: "lai_companies_hybrid"
  ingestion_mode: "filtered"
  apply_exclusions: true
  exclusion_scopes: [hr_content, financial_generic, ...]
  require_lai_keywords: true  # ← Filtrage LAI requis
  min_lai_signals: 1
```

**Logique**:
```python
if _is_hybrid_player(company_id):
    # Exclusions + LAI keywords obligatoires
    return _filter_by_exclusions_and_lai(items)
```

**Items conservés**: Seulement si contient LAI keywords ET pas de bruit

---

### 4. Filtrage Presse Sectorielle

**Exemple**: FierceBiotech, BioPharma Dive

```yaml
# ingestion_profiles.yaml
press_profile:
  ingestion_mode: "filtered"
  apply_exclusions: true
  require_lai_keywords: true
  min_lai_signals: 1
```

**Logique**:
```python
# Toujours filtrage strict
return _filter_by_exclusions_and_lai(items)
```

**Items conservés**: Seulement si contient LAI keywords ET pas de bruit

---

## 📊 Scopes Canonical Utilisés

### exclusion_scopes.yaml (8 scopes)

```yaml
hr_content: [job opening, hiring, ...]
hr_recruitment_terms: [seeks.*engineer, ...]
esg_generic: [sustainability report, ...]
financial_generic: [quarterly earnings, ...]
financial_reporting_terms: [publishes.*financial results, ...]
anti_lai_routes: [oral tablet, oral capsule, ...]
event_generic: [conference participation, ...]
corporate_noise_terms: [appoints.*chief, ...]
```

**Total**: ~150 termes d'exclusion

---

### company_scopes.yaml

```yaml
lai_companies_pure_players: [MedinCell, Camurus, ...]  # 14 entreprises
lai_companies_hybrid: [Teva, Pfizer, Novartis, ...]    # 27 entreprises
```

---

### technology_scopes.yaml + trademark_scopes.yaml

```yaml
lai_keywords:
  core_phrases: [long-acting injectable, depot, ...]
  technology_terms_high_precision: [microsphere, ...]
  interval_patterns: [once-monthly, once-weekly, ...]

lai_trademarks_global: [Uzedy, Bydureon, Invega, ...]
```

**Total**: ~150 LAI keywords

---

## ✅ Avantages Architecture Canonical

### 1. Zéro Hardcoding
- ❌ Avant: 3 listes hardcodées dans le code
- ✅ Après: 0 hardcoding, tout dans canonical

### 2. Modifications Sans Rebuild
- ❌ Avant: Modifier code → rebuild layer → redeploy
- ✅ Après: Modifier canonical → effet immédiat

### 3. Logique Métier Visible
- ❌ Avant: Logique enfouie dans le code Python
- ✅ Après: Logique lisible dans YAML

### 4. Testabilité
- ❌ Avant: Tester = modifier code + rebuild
- ✅ Après: Tester = modifier YAML + invoke

### 5. Gouvernance
- ❌ Avant: Changements nécessitent dev
- ✅ Après: Changements via canonical (versionné)

---

## 🚀 Déploiement

### Étape 1: Appliquer Plan Correctif
```bash
# Phases 1-7 du plan correctif
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

### Étape 2: Valider Logs
```
✅ Exclusion scopes chargés: 8 catégories
✅ Company scopes: 14 pure players, 27 hybrid players
✅ LAI keywords: 150+ termes chargés
✅ Pure player: MedinCell - exclusions seules
✅ Hybrid player: Teva - exclusions + LAI keywords requis
```

### Étape 3: Test E2E
```bash
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v24 --env dev
```

**Résultat attendu**: 20 items ingérés (vs 25 avant)

---

## 📝 Maintenance

### Ajouter un Pure Player
```yaml
# canonical/scopes/company_scopes.yaml
lai_companies_pure_players:
  - MedinCell
  - Camurus
  - NouvelleEntreprise  # ← Ajouter ici
```

**Effet**: Immédiat (sans rebuild)

### Ajouter un Terme d'Exclusion
```yaml
# canonical/scopes/exclusion_scopes.yaml
hr_content:
  - job opening
  - nouveau_terme_rh  # ← Ajouter ici
```

**Effet**: Immédiat (sans rebuild)

### Ajouter un LAI Keyword
```yaml
# canonical/scopes/technology_scopes.yaml
lai_keywords:
  core_phrases:
    - long-acting injectable
    - nouveau_terme_lai  # ← Ajouter ici
```

**Effet**: Immédiat (sans rebuild)

---

## 🎯 Conformité avec ingestion_profiles.yaml

Le moteur implémente exactement les règles définies dans `canonical/ingestion/ingestion_profiles.yaml` :

| Profil | Exclusions | LAI Keywords | Implémentation |
|--------|-----------|--------------|----------------|
| Pure players | ✅ 8 scopes | ❌ Non requis | `_filter_by_exclusions_only()` |
| Hybrid players | ✅ 8 scopes | ✅ Requis | `_filter_by_exclusions_and_lai()` |
| Presse | ✅ 5 scopes | ✅ Requis | `_filter_by_exclusions_and_lai()` |

---

**Statut**: Architecture validée - Prêt pour implémentation  
**Prochaine étape**: Exécuter plan correctif phases 1-7
