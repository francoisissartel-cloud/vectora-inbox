# DIAGNOSTIC PHASE INGESTION - Hardcoding & Fallbacks

**Date**: 2026-02-06  
**Scope**: src_v2/vectora_core/ingest/  
**Objectif**: Identifier tout hardcoding et fallbacks codés pour pilotage 100% canonical

---

## 🔴 HARDCODING IDENTIFIÉ

### 1. **ingestion_profiles.py** - CRITIQUE

#### 1.1 Liste Pure Players LAI (ligne 109-110)
```python
lai_pure_players = ['medincell', 'camurus', 'delsitech', 'nanexa', 'peptron']
is_lai_pure_player = company_id.lower() in lai_pure_players
```

**Problème**: Liste hardcodée dans le code  
**Impact**: Impossible d'ajouter/retirer pure players sans redéployer Lambda  
**Solution**: Charger depuis `canonical/scopes/company_scopes.yaml` → scope `lai_companies_pure_players`

---

#### 1.2 Mots-clés LAI (lignes 44-60)
```python
LAI_KEYWORDS = [
    # Technologies LAI
    "injectable", "injection", "long-acting", "extended-release", "depot", 
    "sustained-release", "controlled-release", "implant", "microsphere",
    "LAI", "long acting injectable", "once-monthly", "once-weekly",
    
    # Entreprises LAI
    "medincell", "camurus", "delsitech", "nanexa", "peptron", "teva",
    "uzedy", "bydureon", "invega", "risperdal", "abilify maintena",
    
    # Molécules LAI
    "olanzapine", "risperidone", "paliperidone", "aripiprazole", 
    "haloperidol", "fluphenazine", "exenatide", "naltrexone",
    
    # Routes d'administration
    "intramuscular", "subcutaneous", "im injection", "sc injection"
]
```

**Problème**: 60+ mots-clés hardcodés  
**Impact**: Maintenance difficile, pas de traçabilité des changements  
**Solution**: Charger depuis `canonical/scopes/technology_scopes.yaml` → scope `lai_keywords`

---

#### 1.3 Mots-clés d'exclusion (lignes 63-75)
```python
EXCLUSION_KEYWORDS = [
    # RH et recrutement
    "hiring", "recruitment", "job opening", "career", "seeks an experienced",
    "is hiring", "appointment of", "leadership change", "joins as",
    
    # Événements corporate génériques
    "conference", "webinar", "presentation", "meeting", "congress",
    "summit", "symposium", "event", "participate in", "to present at",
    
    # Routes non-LAI
    "oral", "tablet", "capsule", "pill", "topical", "nasal spray",
    "eye drops", "cream", "gel", "patch"
]
```

**Problème**: Fallback hardcodé utilisé si S3 échoue  
**Impact**: Comportement différent selon succès/échec S3  
**Solution**: Supprimer fallback, fail-fast si S3 indisponible

---

### 2. **Logique de décision hardcodée**

#### 2.1 Détection pure player (ligne 110)
```python
is_lai_pure_player = company_id.lower() in lai_pure_players
```

**Problème**: Logique de matching hardcodée (case-insensitive simple)  
**Impact**: Pas de flexibilité (alias, variations orthographiques)  
**Solution**: Utiliser structure canonical avec aliases

---

#### 2.2 Profils d'ingestion (lignes 95-105)
```python
if source_type == 'press_corporate':
    return _apply_corporate_profile(items, source_meta)
elif source_type == 'press_sector':
    return _apply_press_profile(items, source_meta)
else:
    # Profil par défaut : ingestion large
    logger.info(f"Profil par défaut appliqué pour {source_key}")
    return items
```

**Problème**: Mapping type → profil hardcodé  
**Impact**: Impossible de définir nouveaux profils sans code  
**Solution**: Charger mapping depuis `canonical/ingestion/ingestion_profiles.yaml`

---

## 📊 RÉSUMÉ HARDCODING

| Élément | Localisation | Type | Criticité |
|---------|--------------|------|-----------|
| Liste pure players | ingestion_profiles.py:109 | Liste hardcodée | 🔴 HAUTE |
| Mots-clés LAI | ingestion_profiles.py:44-60 | Liste hardcodée | 🔴 HAUTE |
| Mots-clés exclusion | ingestion_profiles.py:63-75 | Fallback hardcodé | 🟡 MOYENNE |
| Mapping type→profil | ingestion_profiles.py:95-105 | Logique hardcodée | 🟡 MOYENNE |
| Détection pure player | ingestion_profiles.py:110 | Logique hardcodée | 🟡 MOYENNE |

---

## ✅ POINTS POSITIFS

### 1. Chargement S3 des exclusions (lignes 18-28)
```python
def initialize_exclusion_scopes(s3_io, config_bucket: str):
    """Charge les exclusion_scopes depuis S3 (appelé au démarrage)."""
    global _exclusion_scopes_cache
    
    try:
        scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/exclusion_scopes.yaml')
        _exclusion_scopes_cache = scopes or {}
        logger.info(f"Exclusion scopes chargés: {len(_exclusion_scopes_cache)} catégories")
    except Exception as e:
        logger.warning(f"Échec chargement exclusion_scopes: {e}. Utilisation fallback.")
        _exclusion_scopes_cache = {}
```

**Bon**: Tentative de charger depuis S3  
**Problème**: Fallback silencieux sur hardcoding si échec

---

### 2. Fonction _get_exclusion_terms() (lignes 30-42)
```python
def _get_exclusion_terms() -> List[str]:
    """Retourne la liste combinée des termes d'exclusion depuis S3."""
    if not _exclusion_scopes_cache:
        # Fallback sur keywords hardcodés
        return EXCLUSION_KEYWORDS
    
    # Combiner hr_content, financial_generic, hr_recruitment_terms, financial_reporting_terms
    terms = []
    for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
        scope_terms = _exclusion_scopes_cache.get(scope_name, [])
        terms.extend(scope_terms)
    
    return terms if terms else EXCLUSION_KEYWORDS
```

**Bon**: Combine plusieurs scopes S3  
**Problème**: Double fallback (cache vide → hardcoding, scopes vides → hardcoding)

---

## 🎯 PLAN DE CORRECTION

### Phase 1: Supprimer hardcoding pure players
1. Supprimer `lai_pure_players = [...]`
2. Charger depuis `canonical/scopes/company_scopes.yaml` → `lai_companies_pure_players`
3. Fail-fast si scope manquant

### Phase 2: Supprimer hardcoding mots-clés LAI
1. Supprimer `LAI_KEYWORDS = [...]`
2. Charger depuis `canonical/scopes/technology_scopes.yaml` → `lai_keywords`
3. Fail-fast si scope manquant

### Phase 3: Supprimer fallback exclusions
1. Supprimer `EXCLUSION_KEYWORDS = [...]`
2. Supprimer fallbacks dans `_get_exclusion_terms()`
3. Fail-fast si S3 échoue

### Phase 4: Externaliser mapping profils
1. Créer `canonical/ingestion/ingestion_profiles.yaml`
2. Définir mapping `source_type` → `profile_name`
3. Charger au démarrage, fail-fast si manquant

### Phase 5: Externaliser logique pure player
1. Ajouter champ `aliases` dans company_scopes
2. Matching flexible (case-insensitive, aliases)
3. Pilotage 100% canonical

---

## 📋 FICHIERS CANONICAL REQUIS

### Existants (à utiliser)
- ✅ `canonical/scopes/company_scopes.yaml` → `lai_companies_pure_players`
- ✅ `canonical/scopes/technology_scopes.yaml` → `lai_keywords`
- ✅ `canonical/scopes/exclusion_scopes.yaml` → `hr_content`, `financial_generic`, etc.

### À créer
- ❌ `canonical/ingestion/ingestion_profiles.yaml` → mapping type→profil

---

## 🚨 RÈGLES DE CORRECTION

1. **AUCUN fallback hardcodé** : Si S3 échoue → fail-fast avec erreur explicite
2. **AUCUNE liste hardcodée** : Toutes les listes depuis canonical
3. **AUCUNE logique métier hardcodée** : Mapping et règles depuis canonical
4. **Fail-fast** : Erreur claire si canonical manquant/invalide
5. **Traçabilité** : Logs explicites sur source des données (S3 path)

---

## 📈 IMPACT ATTENDU

### Avant (état actuel)
- 🔴 3 listes hardcodées (pure players, LAI keywords, exclusions)
- 🔴 2 fallbacks silencieux
- 🔴 Logique métier dans code
- 🔴 Maintenance = redéploiement Lambda

### Après (cible)
- ✅ 0 liste hardcodée
- ✅ 0 fallback
- ✅ Logique métier dans canonical
- ✅ Maintenance = upload S3 canonical

---

**Diagnostic complet - Prêt pour correction**
