# ANALYSE - Appels Canonical Lambda Ingestion

**Date**: 2026-02-06  
**Question**: La Lambda appelle-t-elle les bons canonical pour fonctionner après refactoring ?

---

## 📊 ÉTAT ACTUEL (CODE EXISTANT)

### Fichiers canonical appelés par ingestion_profiles.py

```python
# Ligne 21-28: initialize_exclusion_scopes()
scopes = s3_io.read_yaml_from_s3(
    config_bucket, 
    'canonical/scopes/exclusion_scopes.yaml'  # ✅ SEUL APPEL S3
)
```

**Total appels S3**: 1 fichier
- ✅ `canonical/scopes/exclusion_scopes.yaml`

### Données hardcodées (NON chargées depuis S3)

```python
# Ligne 44-60: LAI_KEYWORDS (hardcodé)
LAI_KEYWORDS = [...]  # 60+ mots-clés

# Ligne 63-75: EXCLUSION_KEYWORDS (fallback hardcodé)
EXCLUSION_KEYWORDS = [...]  # 20+ mots-clés

# Ligne 109: lai_pure_players (hardcodé)
lai_pure_players = ['medincell', 'camurus', 'delsitech', 'nanexa', 'peptron']
```

**Problème**: Lambda utilise hardcoding, PAS les canonical S3 !

---

## 🎯 ÉTAT FUTUR (APRÈS REFACTORING)

### Fichiers canonical requis par nouveau code

```python
# initialize_ingestion_profiles() - NOUVEAU
def initialize_ingestion_profiles(s3_io, config_bucket: str):
    # 1. Profils d'ingestion
    profiles = s3_io.read_yaml_from_s3(
        config_bucket, 
        'canonical/ingestion/ingestion_profiles.yaml'  # ❓ À CRÉER
    )
    
    # 2. Company scopes
    scopes['companies'] = s3_io.read_yaml_from_s3(
        config_bucket, 
        'canonical/scopes/company_scopes.yaml'  # ✅ EXISTE
    )
    
    # 3. Technology scopes
    scopes['technologies'] = s3_io.read_yaml_from_s3(
        config_bucket, 
        'canonical/scopes/technology_scopes.yaml'  # ✅ EXISTE
    )
    
    # 4. Trademark scopes
    scopes['trademarks'] = s3_io.read_yaml_from_s3(
        config_bucket, 
        'canonical/scopes/trademark_scopes.yaml'  # ✅ EXISTE
    )
    
    # 5. Exclusion scopes
    scopes['exclusions'] = s3_io.read_yaml_from_s3(
        config_bucket, 
        'canonical/scopes/exclusion_scopes.yaml'  # ✅ EXISTE
    )
```

**Total appels S3**: 5 fichiers

---

## ✅ FICHIERS CANONICAL - STATUT

### Sur S3 dev actuellement

```bash
aws s3 ls s3://vectora-inbox-data-dev/canonical/ --recursive
```

**Résultat**:
- ✅ `canonical/scopes/company_scopes.yaml` (existe)
- ✅ `canonical/scopes/technology_scopes.yaml` (existe)
- ✅ `canonical/scopes/trademark_scopes.yaml` (existe)
- ✅ `canonical/scopes/exclusion_scopes.yaml` (existe)
- ✅ `canonical/ingestion/ingestion_profiles.yaml` (existe - ANCIEN FORMAT)

### Dans repo local

- ✅ `canonical/scopes/company_scopes.yaml` (à jour)
- ✅ `canonical/scopes/technology_scopes.yaml` (à jour)
- ✅ `canonical/scopes/trademark_scopes.yaml` (à jour)
- ✅ `canonical/scopes/exclusion_scopes.yaml` (à jour)
- ❌ `canonical/ingestion/ingestion_profiles.yaml` (ANCIEN - à remplacer)

---

## 🔴 PROBLÈME IDENTIFIÉ

### Fichier S3 existant vs nouveau format

**S3 actuel** (`canonical/ingestion/ingestion_profiles.yaml`):
```yaml
profiles:
  corporate_pure_player_broad:
    strategy: "broad_ingestion"
    signal_requirements:
      mode: "exclude_only"
      exclusion_scopes:
        - "exclusion_scopes.hr_content"  # ❌ Format complexe
```

**Format requis par nouveau code**:
```yaml
profiles:
  corporate_profile:
    rules:
      pure_players:
        company_scope: "lai_companies_pure_players"
        exclusion_scopes:
          - "hr_content"  # ✅ Format simple
          - "event_generic"
        require_lai_keywords: false
      
      hybrid_players:
        company_scope: "lai_companies_hybrid"
        exclusion_scopes:
          - "hr_content"
          - "financial_generic"
        require_lai_keywords: true
```

**Incompatibilité**: Structure différente !

---

## ✅ SOLUTION

### Étape 1: Créer NOUVEAU ingestion_profiles.yaml local

Créer fichier avec structure compatible nouveau code:
- `canonical/ingestion/ingestion_profiles.yaml` (NOUVEAU FORMAT)

### Étape 2: Supprimer ANCIEN sur S3

```bash
aws s3 rm s3://vectora-inbox-data-dev/canonical/ingestion/ingestion_profiles.yaml \
  --profile rag-lai-prod --region eu-west-3
```

### Étape 3: Upload NOUVEAU sur S3

```bash
aws s3 cp canonical/ingestion/ingestion_profiles.yaml \
  s3://vectora-inbox-data-dev/canonical/ingestion/ingestion_profiles.yaml \
  --profile rag-lai-prod --region eu-west-3
```

### Étape 4: Vérifier autres canonical à jour

```bash
# Upload tous les scopes (au cas où)
aws s3 sync canonical/scopes/ \
  s3://vectora-inbox-data-dev/canonical/scopes/ \
  --profile rag-lai-prod --region eu-west-3
```

---

## 📋 CHECKLIST FICHIERS CANONICAL

### Fichiers requis par Lambda (après refactoring)

| Fichier | Local | S3 dev | Format OK | Action |
|---------|-------|--------|-----------|--------|
| `canonical/ingestion/ingestion_profiles.yaml` | ❌ | ⚠️ ancien | ❌ | CRÉER + UPLOAD |
| `canonical/scopes/company_scopes.yaml` | ✅ | ✅ | ✅ | OK |
| `canonical/scopes/technology_scopes.yaml` | ✅ | ✅ | ✅ | OK |
| `canonical/scopes/trademark_scopes.yaml` | ✅ | ✅ | ✅ | OK |
| `canonical/scopes/exclusion_scopes.yaml` | ✅ | ✅ | ✅ | OK |

---

## 🎯 RÉPONSE À LA QUESTION

**Question**: La Lambda appelle-t-elle les bons canonical ?

**Réponse**: 
- ❌ **NON actuellement** : Lambda utilise hardcoding (LAI_KEYWORDS, pure_players)
- ✅ **OUI après refactoring** : Lambda chargera 5 fichiers canonical depuis S3
- ⚠️ **MAIS** : Fichier `ingestion_profiles.yaml` sur S3 est ANCIEN FORMAT
- ✅ **SOLUTION** : Créer NOUVEAU format + supprimer ancien + upload nouveau

---

## 🔧 ACTIONS REQUISES

### 1. Créer nouveau ingestion_profiles.yaml
```bash
# Créer fichier avec structure du plan correctif
# canonical/ingestion/ingestion_profiles.yaml
```

### 2. Nettoyer S3 dev
```bash
# Supprimer ancien
aws s3 rm s3://vectora-inbox-data-dev/canonical/ingestion/ingestion_profiles.yaml

# Upload nouveau
aws s3 cp canonical/ingestion/ingestion_profiles.yaml \
  s3://vectora-inbox-data-dev/canonical/ingestion/
```

### 3. Vérifier scopes à jour
```bash
# Sync tous les scopes
aws s3 sync canonical/scopes/ s3://vectora-inbox-data-dev/canonical/scopes/
```

---

## ✅ APRÈS CES ACTIONS

Lambda chargera:
1. ✅ `ingestion_profiles.yaml` (NOUVEAU FORMAT)
2. ✅ `company_scopes.yaml` → `lai_companies_pure_players`, `lai_companies_hybrid`
3. ✅ `technology_scopes.yaml` → `lai_keywords.*`
4. ✅ `trademark_scopes.yaml` → `lai_trademarks_global`
5. ✅ `exclusion_scopes.yaml` → `hr_content`, `financial_generic`, etc.

**Résultat**: Lambda 100% pilotée par canonical, 0 hardcoding !

---

**Conclusion**: Il faut créer le NOUVEAU `ingestion_profiles.yaml` et remplacer l'ancien sur S3.
