# Plan Correctif - Filtrage Ingestion Canonical

**Date**: 2026-02-06  
**Objectif**: Activer chargement S3 des exclusion scopes et pure players  
**Durée estimée**: 2h  
**Risque**: Faible  
**Environnements impactés**: dev

---

## 🎯 Contexte

**Problème**: Le code déployé utilise fallback hardcodé au lieu de charger canonical depuis S3.

**Root Cause**: `initialize_exclusion_scopes()` existe mais n'est pas appelé dans le code déployé.

**Impact**: Ajout de keywords dans canonical n'a aucun effet (25 items ingérés au lieu de 20).

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

### Phase 4: Externaliser Pure Players ⏱️ 45 min

**Objectif**: Piloter pure players via `company_scopes.yaml`

**Fichier**: `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Modifications**:

```python
# Ligne 20: Ajouter cache
_pure_players_cache = None

# Ligne 40: Ajouter fonction
def initialize_pure_players(s3_io, config_bucket: str):
    global _pure_players_cache
    scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/company_scopes.yaml')
    pure_players = scopes.get('lai_companies_pure_players', [])
    _pure_players_cache = [company.lower() for company in pure_players]
    logger.info(f"Pure players: {len(_pure_players_cache)} entreprises")

# Ligne 133: Utiliser cache
lai_pure_players = _pure_players_cache
if not lai_pure_players:
    raise RuntimeError("Pure players non initialisés")
```

**Fichier**: `src_v2/vectora_core/ingest/__init__.py`

```python
# Ligne 89: Ajouter après initialize_exclusion_scopes()
initialize_pure_players(s3_io, config_bucket)
```

- [ ] Ajouter fonction et cache
- [ ] Modifier ligne 133
- [ ] Ajouter appel dans `__init__.py`
- [ ] Supprimer liste hardcodée ligne 133
- [ ] Build + deploy dev
- [ ] Test avec lai_weekly_v24

**Livrable**: Pure players pilotables via canonical

**✋ CHECKPOINT**: Validation avant Phase 5

---

### Phase 5: Test E2E & Validation ⏱️ 20 min

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
  - "Exclusion scopes chargés: 9 catégories"
  - "Pure players: 14 entreprises"

**Livrable**: Filtrage opérationnel via canonical

---

### Phase 6: Commit & Documentation ⏱️ 10 min

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
- [ ] 9 scopes chargés depuis S3
- [ ] 14 pure players chargés depuis S3
- [ ] Lambda échoue si S3 inaccessible
- [ ] Modification canonical → Impact immédiat (sans rebuild)

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
- Keywords utilisés: 20 (hardcodé)
- Scopes utilisés: 0
- Pure players: 5 (hardcodé)

**Après correctif**:
- Items ingérés: 20 (-5)
- Keywords utilisés: 150+ (S3)
- Scopes utilisés: 9
- Pure players: 14 (S3)

---

**Plan créé le**: 2026-02-06  
**Statut**: Prêt pour exécution
