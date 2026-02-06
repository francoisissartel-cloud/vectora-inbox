# DIAGNOSTIC - Filtrage d'Ingestion Vectora Inbox

**Date** : 2026-02-06  
**Contexte** : Échec du filtrage d'exclusion malgré ajout de keywords dans canonical  
**Objectif** : Identifier pourquoi le moteur n'utilise pas les fichiers canonical et proposer un plan correctif minimaliste

---

## 🔍 DÉCOUVERTES

### 1. Symptôme Initial

**Observation** : Ajout de keywords d'exclusion dans `canonical/scopes/exclusion_scopes.yaml` n'a AUCUN impact sur l'ingestion.

**Résultat attendu** : Réduction du nombre d'items ingérés (de 25 à ~18)  
**Résultat réel** : Toujours 25 items ingérés

**Items qui devraient être exclus** :
- "BIO International Convention 2025" → Contient "BIO International Convention"
- "Medincell to Join MSCI World Small Cap Index" → Contient "MSCI World"
- "Publication of the 2026 financial calendar" → Contient "financial calendar"
- "Medincell Appoints Dr Grace Kim, Chief Strategy Officer" → Contient "chief strategy officer"
- "Medincell Publishes its Consolidated Half-Year Financial Results" → Contient "consolidated half-year"

### 2. Investigation du Code

**Fichier** : `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Code présent** :
```python
# Ligne 20 : Variable cache
_exclusion_scopes_cache = None

# Ligne 22 : Fonction d'initialisation
def initialize_exclusion_scopes(s3_io, config_bucket: str):
    scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/exclusion_scopes.yaml')
    _exclusion_scopes_cache = scopes or {}

# Ligne 34 : Fonction de récupération
def _get_exclusion_terms() -> List[str]:
    if not _exclusion_scopes_cache:
        return EXCLUSION_KEYWORDS  # ← FALLBACK HARDCODÉ
    
    # Combine 4 scopes
    for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
        terms.extend(_exclusion_scopes_cache.get(scope_name, []))
    
    return terms if terms else EXCLUSION_KEYWORDS

# Ligne 80-92 : Fallback hardcodé
EXCLUSION_KEYWORDS = [
    "hiring", "recruitment", "job opening", "career",
    "conference", "webinar", "presentation", "meeting",
    "oral", "tablet", "capsule", "pill"
]
```

**Problème identifié** : `initialize_exclusion_scopes()` existe MAIS n'est PAS appelé.

### 3. Investigation du Workflow

**Fichier** : `src_v2/vectora_core/ingest/__init__.py`

**Code local (ligne 87)** :
```python
# Initialiser exclusion scopes depuis S3
logger.info("Étape 2.5 : Initialisation des exclusion scopes depuis S3")
initialize_exclusion_scopes(s3_io, config_bucket)
```

**Vérification CloudWatch** : Aucun log "Étape 2.5" trouvé dans les exécutions Lambda.

**Conclusion** : Le code déployé sur AWS **NE CONTIENT PAS** l'appel à `initialize_exclusion_scopes()`.

### 4. Analyse du Layer Déployé

**Layer actuel** : `vectora-inbox-vectora-core-dev:69`  
**Date de création** : 2026-02-06 11:20:46  
**SHA256** : `54a43a854c02174710f80856e16d772921260da27570f1b10347a8b28c265a0a`

**Vérification du layer local** :
```bash
# Layer local contient bien l'appel ligne 87
✅ initialize_exclusion_scopes présent
```

**Problème** : Le layer v69 a été créé AVANT l'ajout de l'appel à `initialize_exclusion_scopes()` dans `__init__.py`.

### 5. Comportement Actuel

**Flux d'exécution réel** :
```
Lambda démarre
  ↓
run_ingest_for_client()
  ↓
_exclusion_scopes_cache = None  (jamais initialisé)
  ↓
_get_exclusion_terms()
  ↓
if not _exclusion_scopes_cache:  ← TRUE
  return EXCLUSION_KEYWORDS  ← FALLBACK HARDCODÉ (20 termes)
```

**Résultat** : Le moteur utilise le fallback hardcodé au lieu de lire S3.

### 6. Test de Matching Local

**Test effectué** : Simulation du matching avec les keywords du fichier S3.

**Résultat** :
```
✅ "BIO International Convention" → MATCH trouvé
✅ "MSCI World" → MATCH trouvé
✅ "financial calendar" → MATCH trouvé
✅ "chief strategy officer" → MATCH trouvé
✅ "consolidated half-year" → MATCH trouvé
```

**Conclusion** : Le matching fonctionne PARFAITEMENT en local avec les keywords S3.

---

## 🎯 ROOT CAUSE

**Le code déployé (layer v69) utilise le fallback hardcodé au lieu de charger les exclusion scopes depuis S3.**

**Raison** : L'appel à `initialize_exclusion_scopes()` n'est pas présent dans le code déployé.

**Impact** : Impossible de piloter le filtrage via canonical sans rebuild.

---

## ❌ PROBLÈMES IDENTIFIÉS

### Problème 1 : Fallback Hardcodé Actif

**Localisation** : `ingestion_profiles.py` ligne 80-92

**Impact** : Le moteur utilise 20 keywords hardcodés au lieu des 114 keywords du fichier S3.

**Conséquence** : Ajout de keywords dans canonical n'a aucun effet.

### Problème 2 : Scopes Partiellement Lus

**Localisation** : `ingestion_profiles.py` ligne 42

**Code actuel** :
```python
for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
```

**Scopes IGNORÉS** :
- `esg_generic`
- `event_generic`
- `corporate_noise_terms`
- `anti_lai_routes`
- `lai_exclude_noise`

**Impact** : Seuls 4 scopes sur 9 sont utilisés.

### Problème 3 : Liste Pure Players Hardcodée

**Localisation** : `ingestion_profiles.py` ligne 133

**Code actuel** :
```python
lai_pure_players = ['medincell', 'camurus', 'delsitech', 'nanexa', 'peptron']
```

**Impact** : Impossible d'ajouter/retirer un pure player sans rebuild.

**Fichier canonical existant** : `canonical/scopes/company_scopes.yaml` contient déjà `lai_companies_pure_players` (14 entreprises).

### Problème 4 : Keywords LAI Hardcodés

**Localisation** : `ingestion_profiles.py` ligne 48-69

**Code actuel** :
```python
LAI_KEYWORDS = [
    "injectable", "injection", "long-acting", ...
]
```

**Impact** : Impossible d'ajuster les keywords LAI sans rebuild.

---

## ✅ PLAN CORRECTIF MINIMALISTE

### Objectif

**Rendre le moteur 100% pilotable via canonical SANS rebuild.**

### Principe

**Tout ce qui est métier (keywords, scopes, listes) doit être dans canonical.**  
**Le code Lambda ne doit contenir QUE la logique de traitement.**

---

## 📋 ACTIONS CORRECTIVES

### Action 1 : Activer le Chargement S3 (CRITIQUE)

**Statut** : ✅ Code présent localement, ❌ Pas déployé

**Fichier** : `src_v2/vectora_core/ingest/__init__.py` ligne 87

**Action** : Rebuild + redeploy pour activer l'appel existant.

**Commandes** :
```bash
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

**Impact** : Active le chargement des exclusion scopes depuis S3.

**Validation** :
```bash
# Vérifier logs CloudWatch
aws logs tail /aws/lambda/vectora-inbox-ingest-v2-dev --since 5m | findstr "Etape 2.5"
# Attendu: "Étape 2.5 : Initialisation des exclusion scopes depuis S3"
```

### Action 2 : Supprimer le Fallback Hardcodé

**Fichier** : `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Modification** :
```python
# AVANT (ligne 34-44)
def _get_exclusion_terms() -> List[str]:
    if not _exclusion_scopes_cache:
        return EXCLUSION_KEYWORDS  # ← SUPPRIMER
    
    terms = []
    for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
        terms.extend(_exclusion_scopes_cache.get(scope_name, []))
    
    return terms if terms else EXCLUSION_KEYWORDS  # ← SUPPRIMER

# APRÈS
def _get_exclusion_terms() -> List[str]:
    if not _exclusion_scopes_cache:
        logger.error("ERREUR CRITIQUE: exclusion_scopes non chargé depuis S3")
        raise RuntimeError("Exclusion scopes non initialisés")
    
    terms = []
    for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
        terms.extend(_exclusion_scopes_cache.get(scope_name, []))
    
    if not terms:
        logger.error("ERREUR CRITIQUE: Aucun terme d'exclusion trouvé dans S3")
        raise RuntimeError("Exclusion scopes vides")
    
    return terms
```

**Impact** : Force le chargement S3, échoue explicitement si problème.

### Action 3 : Lire TOUS les Scopes

**Fichier** : `src_v2/vectora_core/ingest/ingestion_profiles.py` ligne 42

**Modification** :
```python
# AVANT
for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
    terms.extend(_exclusion_scopes_cache.get(scope_name, []))

# APRÈS
# Lire TOUS les scopes (sauf métadonnées)
excluded_keys = ['exclude_contexts', 'lai_exclusion_scopes', 'lai_exclude_noise']
for scope_name, scope_terms in _exclusion_scopes_cache.items():
    if scope_name not in excluded_keys and isinstance(scope_terms, list):
        terms.extend(scope_terms)
        logger.debug(f"Scope '{scope_name}': {len(scope_terms)} termes ajoutés")
```

**Impact** : Tous les scopes du YAML sont utilisés (9 scopes au lieu de 4).

### Action 4 : Externaliser Liste Pure Players

**Fichier** : `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Modification** :
```python
# Ligne 20 : Ajouter cache
_pure_players_cache = None

# Ligne 40 : Ajouter fonction d'initialisation
def initialize_pure_players(s3_io, config_bucket: str):
    global _pure_players_cache
    try:
        scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/company_scopes.yaml')
        pure_players = scopes.get('lai_companies_pure_players', [])
        _pure_players_cache = [company.lower() for company in pure_players]
        logger.info(f"Pure players chargés: {len(_pure_players_cache)} entreprises")
    except Exception as e:
        logger.error(f"ERREUR: Échec chargement pure players: {e}")
        raise

# Ligne 133 : Utiliser cache
# AVANT
lai_pure_players = ['medincell', 'camurus', 'delsitech', 'nanexa', 'peptron']

# APRÈS
lai_pure_players = _pure_players_cache
if not lai_pure_players:
    raise RuntimeError("Pure players non initialisés")
```

**Fichier** : `src_v2/vectora_core/ingest/__init__.py` ligne 89

**Modification** :
```python
# Ajouter après initialize_exclusion_scopes()
initialize_pure_players(s3_io, config_bucket)
```

**Impact** : Liste pure players pilotable via `company_scopes.yaml`.

### Action 5 : Externaliser Keywords LAI (OPTIONNEL)

**Fichier** : Créer `canonical/scopes/lai_keywords.yaml`

**Contenu** :
```yaml
lai_keywords:
  - injectable
  - injection
  - long-acting
  - extended-release
  - depot
  - sustained-release
  - controlled-release
  - implant
  - microsphere
  - LAI
  - long acting injectable
  - once-monthly
  - once-weekly
  - medincell
  - camurus
  - delsitech
  - nanexa
  - peptron
  - teva
  - uzedy
  - bydureon
  - invega
  - risperdal
  - abilify maintena
  - olanzapine
  - risperidone
  - paliperidone
  - aripiprazole
  - haloperidol
  - fluphenazine
  - exenatide
  - naltrexone
  - intramuscular
  - subcutaneous
  - im injection
  - sc injection
```

**Code** : Charger depuis S3 comme pour exclusion_scopes.

**Impact** : Keywords LAI pilotables via canonical.

---

## 🚀 PLAN D'EXÉCUTION

### Phase 1 : Quick Fix (30 min) - PRIORITAIRE

**Objectif** : Activer le chargement S3 existant

1. ✅ Vérifier que le code local contient l'appel (ligne 87 de `__init__.py`)
2. ⚠️ Rebuild layers
3. ⚠️ Redeploy sur dev
4. ⚠️ Tester avec lai_weekly_v24
5. ⚠️ Valider que les 5 items sont exclus (25 → 20 items)

**Commandes** :
```bash
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v24 --env dev
```

### Phase 2 : Suppression Fallback (1h)

**Objectif** : Forcer l'utilisation de S3

1. Modifier `_get_exclusion_terms()` pour supprimer fallback
2. Rebuild + redeploy
3. Tester que Lambda échoue si S3 inaccessible
4. Valider comportement nominal

### Phase 3 : Lecture Tous Scopes (30 min)

**Objectif** : Utiliser les 9 scopes au lieu de 4

1. Modifier boucle ligne 42
2. Rebuild + redeploy
3. Valider que tous les scopes sont lus

### Phase 4 : Externaliser Pure Players (1h)

**Objectif** : Piloter pure players via canonical

1. Ajouter `initialize_pure_players()`
2. Modifier ligne 133
3. Rebuild + redeploy
4. Tester ajout/retrait d'un pure player sans rebuild

### Phase 5 : Externaliser LAI Keywords (1h) - OPTIONNEL

**Objectif** : Piloter keywords LAI via canonical

1. Créer `lai_keywords.yaml`
2. Charger depuis S3
3. Rebuild + redeploy
4. Tester modification keywords sans rebuild

---

## ✅ CRITÈRES DE SUCCÈS

### Succès Phase 1 (Quick Fix)

- [ ] Log "Étape 2.5" visible dans CloudWatch
- [ ] Log "Exclusion scopes chargés: 9 catégories"
- [ ] Items ingérés : 20 (vs 25 avant)
- [ ] Items exclus : "BIO International Convention", "MSCI World Small Cap", "financial calendar", "chief strategy officer", "consolidated half-year"

### Succès Global

- [ ] Aucun fallback hardcodé actif
- [ ] Tous les scopes du YAML sont lus
- [ ] Liste pure players pilotable via canonical
- [ ] Modification canonical → Impact immédiat (sans rebuild)
- [ ] Lambda échoue explicitement si S3 inaccessible

---

## 📊 IMPACT ATTENDU

### Avant Correctif

- **Items ingérés** : 25
- **Keywords utilisés** : 20 (fallback hardcodé)
- **Scopes utilisés** : 0 (S3 non lu)
- **Pilotage canonical** : ❌ Impossible

### Après Phase 1 (Quick Fix)

- **Items ingérés** : 20 (-5)
- **Keywords utilisés** : 114 (depuis S3)
- **Scopes utilisés** : 4 (hr_content, financial_generic, etc.)
- **Pilotage canonical** : ✅ Partiel (exclusion keywords seulement)

### Après Phase 4 (Complet)

- **Items ingérés** : 18-20
- **Keywords utilisés** : 150+ (tous scopes)
- **Scopes utilisés** : 9 (tous)
- **Pilotage canonical** : ✅ Complet (keywords + pure players)

---

## 🎯 RECOMMANDATIONS

### Recommandation 1 : Exécuter Phase 1 IMMÉDIATEMENT

**Raison** : Un seul rebuild suffit pour débloquer le pilotage via canonical.

**Bénéfice** : Réduction immédiate du bruit (25 → 20 items).

### Recommandation 2 : Phases 2-3 en Batch

**Raison** : Suppression fallback + lecture tous scopes = 1 seul rebuild.

**Bénéfice** : Moteur robuste et complet.

### Recommandation 3 : Phase 4 Prioritaire

**Raison** : Liste pure players change rarement mais doit être pilotable.

**Bénéfice** : Ajout de nouveaux pure players sans rebuild.

### Recommandation 4 : Phase 5 Optionnelle

**Raison** : Keywords LAI changent très rarement.

**Bénéfice** : Flexibilité maximale mais faible ROI.

---

## 📝 NOTES IMPORTANTES

1. **Un seul rebuild suffit** pour activer le chargement S3 (Phase 1)
2. **Après Phase 1** : Modifications canonical → Impact immédiat
3. **Fallback hardcodé** : À supprimer pour forcer l'utilisation de S3
4. **Scopes ignorés** : 5 scopes sur 9 ne sont pas lus actuellement
5. **Pure players** : Déjà définis dans `company_scopes.yaml` (14 entreprises)

---

**Diagnostic créé le** : 2026-02-06  
**Auteur** : Amazon Q Developer  
**Statut** : ✅ Prêt pour exécution Phase 1
