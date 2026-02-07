# Plan Correctif - Moteur Ingestion 100% Canonical

**Date**: 2026-02-06  
**Objectif**: Rendre le moteur d'ingestion 100% générique et piloté par canonical  
**Durée estimée**: 3h  
**Risque**: Faible  
**Environnements impactés**: dev

---

## 🎯 Contexte

**Problème**: Le moteur d'ingestion contient du code hardcodé (pure players, exclusions, LAI keywords) au lieu de charger depuis canonical.

**Root Cause**: 
- Listes hardcodées dans `ingestion_profiles.py`
- Logique hybrid players absente
- Seulement 4/8 scopes d'exclusion utilisés
- Fallback hardcodé si S3 échoue

**Impact**: 
- Modifications canonical sans effet (rebuild requis)
- Logique pure/hybrid players non différenciée
- Filtrage incomplet

---

## 📋 Plan d'Exécution

### Phase 1: Rebuild & Deploy ⏱️ 15 min

**Objectif**: Activer le chargement S3 existant

- [ ] Vérifier code local contient l'appel (ligne 87 `__init__.py`)
- [ ] Build layers
  ```bash
  python scripts/build/build_all.py
  ```
- [ ] Deploy dev
  ```bash
  python scripts/deploy/deploy_env.py --env dev
  ```
- [ ] Vérifier logs CloudWatch pour "Étape 2.5"

**Livrable**: Layer déployé avec chargement S3 actif

**✋ CHECKPOINT**: Validation logs avant Phase 2

---

### Phase 2: Supprimer Fallback Hardcodé ⏱️ 30 min

**Objectif**: Forcer utilisation S3, échouer si problème

**Fichier**: `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Modifications**:

```python
# Ligne 34-44: Remplacer _get_exclusion_terms()
def _get_exclusion_terms() -> List[str]:
    if not _exclusion_scopes_cache:
        logger.error("ERREUR: exclusion_scopes non chargé depuis S3")
        raise RuntimeError("Exclusion scopes non initialisés")
    
    terms = []
    for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
        terms.extend(_exclusion_scopes_cache.get(scope_name, []))
    
    if not terms:
        logger.error("ERREUR: Aucun terme d'exclusion trouvé dans S3")
        raise RuntimeError("Exclusion scopes vides")
    
    return terms

# Ligne 80-92: Supprimer EXCLUSION_KEYWORDS (fallback hardcodé)
```

- [ ] Modifier fonction
- [ ] Supprimer constante EXCLUSION_KEYWORDS
- [ ] Build + deploy dev
- [ ] Test avec lai_weekly_v24

**Livrable**: Moteur échoue explicitement si S3 inaccessible

**✋ CHECKPOINT**: Validation comportement avant Phase 3

---

### Phase 3: Lire Tous les Scopes ⏱️ 20 min

**Objectif**: Utiliser 9 scopes au lieu de 4

**Fichier**: `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Modification ligne 42**:

```python
# AVANT
for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
    terms.extend(_exclusion_scopes_cache.get(scope_name, []))

# APRÈS
excluded_keys = ['exclude_contexts', 'lai_exclusion_scopes', 'lai_exclude_noise']
for scope_name, scope_terms in _exclusion_scopes_cache.items():
    if scope_name not in excluded_keys and isinstance(scope_terms, list):
        terms.extend(scope_terms)
        logger.debug(f"Scope '{scope_name}': {len(scope_terms)} termes")
```

- [ ] Modifier boucle
- [ ] Build + deploy dev
- [ ] Vérifier logs: 9 scopes chargés

**Livrable**: Tous les scopes canonical utilisés

**✋ CHECKPOINT**: Validation logs avant Phase 4

---

### Phase 4: Externaliser Company Scopes (Pure + Hybrid) ⏱️ 45 min

**Objectif**: Piloter pure/hybrid players via `company_scopes.yaml`

**Fichier**: `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Modifications**:

```python
# Ligne 20: Ajouter caches
_pure_players_cache = None
_hybrid_players_cache = None

# Ligne 40: Ajouter fonction
def initialize_company_scopes(s3_io, config_bucket: str):
    global _pure_players_cache, _hybrid_players_cache
    scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/company_scopes.yaml')
    
    pure_players = scopes.get('lai_companies_pure_players', [])
    _pure_players_cache = [company.lower() for company in pure_players]
    
    hybrid_players = scopes.get('lai_companies_hybrid', [])
    _hybrid_players_cache = [company.lower() for company in hybrid_players]
    
    logger.info(f"Company scopes: {len(_pure_players_cache)} pure players, {len(_hybrid_players_cache)} hybrid players")

# Ligne 133: Utiliser caches
def _is_pure_player(company_id: str) -> bool:
    if not _pure_players_cache:
        raise RuntimeError("Company scopes non initialisés")
    return company_id.lower() in _pure_players_cache

def _is_hybrid_player(company_id: str) -> bool:
    if not _hybrid_players_cache:
        raise RuntimeError("Company scopes non initialisés")
    return company_id.lower() in _hybrid_players_cache
```

**Fichier**: `src_v2/vectora_core/ingest/__init__.py`

```python
# Ligne 89: Ajouter après initialize_exclusion_scopes()
from .ingestion_profiles import initialize_company_scopes
initialize_company_scopes(s3_io, config_bucket)
```

- [ ] Ajouter fonctions et caches
- [ ] Remplacer liste hardcodée par fonctions
- [ ] Ajouter appel dans `__init__.py`
- [ ] Build + deploy dev
- [ ] Test avec lai_weekly_v24

**Livrable**: Pure/hybrid players pilotables via canonical

**✋ CHECKPOINT**: Validation avant Phase 5

---

### Phase 5: Externaliser LAI Keywords ⏱️ 30 min

**Objectif**: Charger LAI keywords depuis canonical au lieu de hardcodé

**Fichier**: `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Modifications**:

```python
# Ligne 20: Ajouter cache
_lai_keywords_cache = None

# Ligne 40: Ajouter fonction
def initialize_lai_keywords(s3_io, config_bucket: str):
    global _lai_keywords_cache
    
    # Charger technology_scopes.yaml et trademark_scopes.yaml
    tech_scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/technology_scopes.yaml')
    trademark_scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/trademark_scopes.yaml')
    
    keywords = []
    # Ajouter core_phrases, technology_terms_high_precision, interval_patterns
    for scope in ['core_phrases', 'technology_terms_high_precision', 'interval_patterns']:
        keywords.extend(tech_scopes.get('lai_keywords', {}).get(scope, []))
    
    # Ajouter trademarks
    keywords.extend(trademark_scopes.get('lai_trademarks_global', []))
    
    _lai_keywords_cache = keywords
    logger.info(f"LAI keywords: {len(_lai_keywords_cache)} termes chargés")

# Ligne 52-70: Supprimer LAI_KEYWORDS hardcodé
# Ligne 220: Modifier _contains_lai_keywords()
def _contains_lai_keywords(text: str) -> bool:
    if not _lai_keywords_cache:
        raise RuntimeError("LAI keywords non initialisés")
    
    text_lower = text.lower()
    for keyword in _lai_keywords_cache:
        if keyword.lower() in text_lower:
            return True
    return False
```

**Fichier**: `src_v2/vectora_core/ingest/__init__.py`

```python
# Ligne 90: Ajouter après initialize_company_scopes()
from .ingestion_profiles import initialize_lai_keywords
initialize_lai_keywords(s3_io, config_bucket)
```

- [ ] Ajouter fonction et cache
- [ ] Supprimer LAI_KEYWORDS hardcodé
- [ ] Modifier _contains_lai_keywords()
- [ ] Ajouter appel dans `__init__.py`
- [ ] Build + deploy dev

**Livrable**: LAI keywords pilotables via canonical

**✋ CHECKPOINT**: Validation avant Phase 6

---

### Phase 6: Implémenter Logique Hybrid Players ⏱️ 30 min

**Objectif**: Différencier filtrage pure vs hybrid players

**Fichier**: `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Modification ligne 133-160**:

```python
def _apply_corporate_profile(items: List[Dict[str, Any]], source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    source_key = source_meta.get('source_key', '')
    company_id = source_meta.get('company_id', '')
    
    # Vérifier type d'entreprise
    is_pure = _is_pure_player(company_id)
    is_hybrid = _is_hybrid_player(company_id)
    
    if is_pure:
        logger.info(f"Pure player: {company_id} - exclusions seules (pas de filtrage LAI)")
        return _filter_by_exclusions_only(items, source_key)
    
    elif is_hybrid:
        logger.info(f"Hybrid player: {company_id} - exclusions + LAI keywords requis")
        return _filter_by_exclusions_and_lai(items, source_key)
    
    else:
        logger.info(f"Entreprise inconnue: {company_id} - filtrage strict")
        return _filter_by_exclusions_and_lai(items, source_key)

def _filter_by_exclusions_only(items: List[Dict[str, Any]], source_key: str) -> List[Dict[str, Any]]:
    filtered = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('content', '')}".lower()
        if not _contains_exclusion_keywords(text):
            filtered.append(item)
    logger.info(f"{source_key}: {len(filtered)}/{len(items)} items (exclusions seules)")
    return filtered

def _filter_by_exclusions_and_lai(items: List[Dict[str, Any]], source_key: str) -> List[Dict[str, Any]]:
    filtered = []
    for item in items:
        text = f"{item.get('title', '')} {item.get('content', '')}".lower()
        if not _contains_exclusion_keywords(text) and _contains_lai_keywords(text):
            filtered.append(item)
    logger.info(f"{source_key}: {len(filtered)}/{len(items)} items (exclusions + LAI)")
    return filtered
```

- [ ] Modifier _apply_corporate_profile()
- [ ] Ajouter _filter_by_exclusions_only()
- [ ] Ajouter _filter_by_exclusions_and_lai()
- [ ] Supprimer ancien code ligne 133-160
- [ ] Build + deploy dev

**Livrable**: Logique pure/hybrid opérationnelle

**✋ CHECKPOINT**: Validation avant Phase 7

---

### Phase 7: Test E2E & Validation ⏱️ 20 min

**Objectif**: Valider filtrage fonctionne

- [ ] Invoke ingest-v2 avec lai_weekly_v24
  ```bash
  python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v24 --env dev
  ```
- [ ] Vérifier items ingérés: 20 (vs 25 avant)
- [ ] Vérifier items exclus:
  - "BIO International Convention"
  - "MSCI World Small Cap"
  - "financial calendar"
  - "chief strategy officer"
  - "consolidated half-year"
- [ ] Vérifier logs CloudWatch:
  - "Étape 2.5: Initialisation exclusion scopes"
  - "Exclusion scopes chargés: 8 catégories"
  - "Company scopes: 14 pure players, 27 hybrid players"
  - "LAI keywords: 150+ termes chargés"
  - "Pure player: MedinCell - exclusions seules"
  - "Hybrid player: Teva - exclusions + LAI keywords requis"

**Livrable**: Filtrage opérationnel via canonical

---

### Phase 8: Commit & Documentation ⏱️ 10 min

- [ ] Commit code
  ```bash
  git add src_v2/ VERSION
  git commit -m "fix: Activer chargement S3 exclusion scopes + pure players"
  git push
  ```
- [ ] Créer rapport final dans `docs/reports/development/`
- [ ] Mettre à jour blueprint si nécessaire

**Livrable**: Code commité, documenté

---

## ✅ Critères de Succès

- [ ] Log "Étape 2.5" visible dans CloudWatch
- [ ] Items ingérés: 20 (vs 25 avant)
- [ ] 5 items exclus correctement
- [ ] 8 scopes d'exclusion chargés depuis S3
- [ ] 14 pure players + 27 hybrid players chargés
- [ ] LAI keywords chargés depuis canonical (150+ termes)
- [ ] Lambda échoue si S3 inaccessible
- [ ] Modification canonical → Impact immédiat (sans rebuild)
- [ ] Pure players: exclusions seules
- [ ] Hybrid players: exclusions + LAI keywords requis
- [ ] AUCUN hardcoding dans ingestion_profiles.py

---

## 🚨 Plan de Rollback

**Si problème critique**:

```bash
# Rollback vers layer précédent
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:69 \
  --profile rag-lai-prod --region eu-west-3
```

---

## 📊 Métriques

**Avant correctif**:
- Items ingérés: 25
- Exclusions: 20 termes hardcodés
- Scopes utilisés: 4/8
- Pure players: 5 hardcodés
- Hybrid players: 0 (non géré)
- LAI keywords: 70 hardcodés
- Hardcoding: 3 listes

**Après correctif**:
- Items ingérés: 20 (-5)
- Exclusions: 150+ termes (S3)
- Scopes utilisés: 8/8
- Pure players: 14 (S3)
- Hybrid players: 27 (S3)
- LAI keywords: 150+ (S3)
- Hardcoding: 0 ✅

---

**Plan créé le**: 2026-02-06  
**Statut**: Prêt pour exécution
