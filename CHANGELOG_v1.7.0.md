# CHANGELOG v1.7.0 - Externalisation Scopes Ingestion

**Date**: 2026-02-06  
**Type**: Feature + Refactoring  
**Impact**: Breaking change (necessite rebuild layer)

---

## 🎯 Resume

Externalisation complete des scopes d'ingestion vers les fichiers YAML canoniques S3. Elimination de tout hardcoding dans `ingestion_profiles.py`. Implementation de la logique de differentiation pure players vs hybrid players.

---

## ✨ Nouvelles Fonctionnalites

### 1. Chargement Company Scopes depuis S3
```python
def initialize_company_scopes(s3_io, config_bucket: str)
```
- Charge `canonical/scopes/company_scopes.yaml`
- Cache: `_pure_players_cache` (14 entreprises)
- Cache: `_hybrid_players_cache` (27 entreprises)
- Echec strict si S3 inaccessible

### 2. Chargement LAI Keywords depuis S3
```python
def initialize_lai_keywords(s3_io, config_bucket: str)
```
- Charge `technology_scopes.yaml` (core_phrases, technology_terms_high_precision, interval_patterns)
- Charge `trademark_scopes.yaml` (lai_trademarks_global)
- Cache: `_lai_keywords_cache` (159 termes)
- Echec strict si S3 inaccessible

### 3. Logique Pure/Hybrid Players
```python
def _is_pure_player(company_id: str) -> bool
def _is_hybrid_player(company_id: str) -> bool
def _filter_by_exclusions_only(items, source_key) -> List
def _filter_by_exclusions_and_lai(items, source_key) -> List
```
- Pure players: Exclusions seules (ingestion large)
- Hybrid players: Exclusions + LAI keywords requis (filtrage strict)
- Entreprises inconnues: Filtrage strict par defaut

---

## 🔧 Modifications

### `src_v2/vectora_core/ingest/ingestion_profiles.py`

#### Ajouts
- Caches globaux: `_pure_players_cache`, `_hybrid_players_cache`, `_lai_keywords_cache`
- Fonction: `initialize_company_scopes()`
- Fonction: `initialize_lai_keywords()`
- Fonction: `_is_pure_player()`
- Fonction: `_is_hybrid_player()`
- Fonction: `_filter_by_exclusions_only()`
- Fonction: `_filter_by_exclusions_and_lai()`

#### Modifications
- `initialize_exclusion_scopes()`: Gestion erreur stricte (raise au lieu de fallback)
- `_get_exclusion_terms()`: Utilise 8 scopes au lieu de 4
- `_apply_corporate_profile()`: Logique pure/hybrid players
- `_contains_lai_keywords()`: Utilise cache S3 au lieu de liste hardcodee
- `_filter_by_lai_keywords()`: Delegue a `_filter_by_exclusions_and_lai()`

#### Suppressions
- Liste hardcodee: `LAI_KEYWORDS` (70 termes)
- Liste hardcodee: `EXCLUSION_KEYWORDS` (20 termes)
- Liste hardcodee: `lai_pure_players` (5 entreprises)

### `src_v2/vectora_core/ingest/__init__.py`

#### Ajouts
- Import: `initialize_company_scopes`, `initialize_lai_keywords`
- Etape 2.6: Appel `initialize_company_scopes(s3_io, config_bucket)`
- Etape 2.7: Appel `initialize_lai_keywords(s3_io, config_bucket)`

### `VERSION`

#### Modifications
- `VECTORA_CORE_VERSION`: 1.6.0 → 1.7.0
- `INGEST_VERSION`: 1.5.1 → 1.6.0

---

## 📊 Metriques

| Metrique | v1.6.0 | v1.7.0 | Delta |
|----------|--------|--------|-------|
| Listes hardcodees | 3 | 0 | -3 |
| Termes exclusion | 20 | 122 | +102 |
| Scopes exclusion | 4 | 8 | +4 |
| Pure players | 5 | 14 | +9 |
| Hybrid players | 0 | 27 | +27 |
| LAI keywords | 70 | 159 | +89 |
| Fonctions init | 1 | 3 | +2 |
| Fonctions helper | 0 | 4 | +4 |

---

## 🔍 Comportement

### Logs Attendus

**Demarrage Lambda**:
```
INFO: Etape 2.5 : Initialisation des exclusion scopes depuis S3
INFO: Exclusion scopes charges: 8 categories
DEBUG: Scope 'hr_content': 21 termes
DEBUG: Scope 'financial_generic': 20 termes
...
INFO: Etape 2.6 : Initialisation des company scopes depuis S3
INFO: Company scopes: 14 pure players, 27 hybrid players
INFO: Etape 2.7 : Initialisation des LAI keywords depuis S3
INFO: LAI keywords: 159 termes charges
```

**Filtrage Items**:
```
INFO: Pure player: MedinCell - exclusions seules (pas de filtrage LAI)
INFO: medincell_rss: 18/20 items (exclusions seules)

INFO: Hybrid player: Teva - exclusions + LAI keywords requis
INFO: teva_rss: 5/20 items (exclusions + LAI)
```

### Gestion Erreurs

**Avant v1.6.0** (Fallback silencieux):
```python
except Exception as e:
    logger.warning(f"Echec chargement: {e}. Utilisation fallback.")
    _exclusion_scopes_cache = {}
```

**Apres v1.7.0** (Echec strict):
```python
except Exception as e:
    logger.error(f"Echec chargement: {e}")
    raise RuntimeError(f"Impossible de charger depuis S3: {e}")
```

---

## 🚨 Breaking Changes

### 1. Gestion Erreur S3
**Avant**: Fallback silencieux sur listes hardcodees  
**Apres**: Echec explicite si S3 inaccessible

**Impact**: Lambda echoue si canonical S3 inaccessible (comportement voulu)

### 2. Filtrage Hybrid Players
**Avant**: Tous traites comme pure players (ingestion large)  
**Apres**: Filtrage strict (exclusions + LAI keywords requis)

**Impact**: Reduction items ingeres pour hybrid players (comportement voulu)

### 3. Scopes Exclusion
**Avant**: 4 scopes utilises (hr_content, financial_generic, hr_recruitment_terms, financial_reporting_terms)  
**Apres**: 8 scopes utilises (+ esg_generic, event_generic, corporate_noise_terms, anti_lai_routes)

**Impact**: Filtrage plus exhaustif (comportement voulu)

---

## ✅ Tests

### Tests Locaux
```bash
python scripts/test/test_scopes_simple.py
```

**Resultats**:
- [PASS] exclusion_scopes (122 termes)
- [PASS] company_scopes (14 pure + 27 hybrid)
- [PASS] lai_keywords (159 termes)
- [PASS] module_import (7 fonctions)

### Tests E2E (A faire)
```bash
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v24 --env dev
```

**Verifications**:
- Items ingeres: ~20 (vs 25 avant)
- Logs: 3 etapes initialisation visibles
- Pure players: Exclusions seules
- Hybrid players: Exclusions + LAI keywords

---

## 📦 Migration

### Etape 1: Build Layer
```bash
python scripts/layers/build_vectora_core_layer.py --env dev
```

### Etape 2: Deploy Layer
```bash
python scripts/deploy/deploy_vectora_core_layer.py --env dev
```

### Etape 3: Update Lambda
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --layers <NEW_LAYER_ARN> \
  --profile rag-lai-prod --region eu-west-3
```

### Etape 4: Verification
- Verifier logs CloudWatch (3 etapes initialisation)
- Verifier items ingeres (reduction attendue)
- Verifier filtrage pure/hybrid players

---

## 🔄 Rollback

Si probleme critique:

```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:69 \
  --profile rag-lai-prod --region eu-west-3
```

---

## 📚 Documentation

- Rapport developpement: `docs/reports/development/rapport_correctif_filtrage_ingestion_v1.7.0.md`
- Resume execution: `docs/plans/EXECUTION_PLAN_CORRECTIF_FILTRAGE.md`
- Script test: `scripts/test/test_scopes_simple.py`
- Changelog: Ce document

---

## 👥 Contributeurs

- Q Developer (Implementation)

---

## 📅 Historique

- **2026-02-06**: v1.7.0 - Externalisation complete scopes ingestion
- **2026-02-05**: v1.6.0 - Ajout initialize_exclusion_scopes()
- **2026-01-XX**: v1.5.1 - Version precedente

---

**Version**: 1.7.0  
**Date**: 2026-02-06  
**Statut**: ✅ PRET POUR DEPLOYMENT
