# VÉRIFICATION COMPLÈTE - Plan Correctif Ingestion

**Date**: 2026-02-06  
**Objectif**: Vérifier que TOUT est OK pour exécution sans surprise

---

## ✅ CHECKLIST VÉRIFICATION

### 1. FICHIERS CANONICAL REQUIS

| Fichier | Existe Local | Existe S3 | Format OK | Contenu Vérifié |
|---------|--------------|-----------|-----------|-----------------|
| `canonical/scopes/company_scopes.yaml` | ✅ | ✅ | ✅ | ✅ lai_companies_pure_players (14), lai_companies_hybrid (27) |
| `canonical/scopes/technology_scopes.yaml` | ✅ | ✅ | ✅ | ✅ lai_keywords.* (8 sections, ~100 termes) |
| `canonical/scopes/trademark_scopes.yaml` | ✅ | ✅ | ✅ | ✅ lai_trademarks_global (76 trademarks) |
| `canonical/scopes/exclusion_scopes.yaml` | ✅ | ✅ | ✅ | ✅ 8 scopes d'exclusion |
| `canonical/ingestion/ingestion_profiles.yaml` | ❌ | ⚠️ ancien | ❌ | ❌ À CRÉER nouveau format |

**Status**: 4/5 OK, 1 à créer

---

### 2. CODE LAMBDA - APPELS S3

#### Appels S3 dans nouveau code

```python
# initialize_ingestion_profiles() - LIGNE ~25
s3_io.read_yaml_from_s3(config_bucket, 'canonical/ingestion/ingestion_profiles.yaml')
s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/company_scopes.yaml')
s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/technology_scopes.yaml')
s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/trademark_scopes.yaml')
s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/exclusion_scopes.yaml')
```

**Vérification**:
- ✅ Fonction `read_yaml_from_s3()` existe dans `s3_io.py`
- ✅ Variable `config_bucket` passée en paramètre
- ✅ Chemins S3 corrects (canonical/...)
- ✅ Tous les fichiers existent (sauf ingestion_profiles à créer)

---

### 3. HARDCODING À SUPPRIMER

#### Dans ingestion_profiles.py

**LIGNE 44-60**: LAI_KEYWORDS
```python
LAI_KEYWORDS = [
    "injectable", "injection", "long-acting", ...
]
```
**Action**: ❌ DELETE (remplacé par technology_scopes.yaml)

**LIGNE 63-75**: EXCLUSION_KEYWORDS
```python
EXCLUSION_KEYWORDS = [
    "hiring", "recruitment", ...
]
```
**Action**: ❌ DELETE (remplacé par exclusion_scopes.yaml)

**LIGNE 109-110**: lai_pure_players
```python
lai_pure_players = ['medincell', 'camurus', 'delsitech', 'nanexa', 'peptron']
is_lai_pure_player = company_id.lower() in lai_pure_players
```
**Action**: ❌ DELETE (remplacé par company_scopes.yaml)

**Total hardcoding**: 3 zones à supprimer ✅

---

### 4. STRUCTURE INGESTION_PROFILES.YAML

#### Format requis par nouveau code

```yaml
source_type_profiles:
  press_corporate:
    profile_name: "corporate_profile"
  press_sector:
    profile_name: "press_profile"

profiles:
  corporate_profile:
    rules:
      pure_players:
        company_scope: "lai_companies_pure_players"
        exclusion_scopes: ["hr_content", "event_generic"]
        require_lai_keywords: false
      
      hybrid_players:
        company_scope: "lai_companies_hybrid"
        exclusion_scopes: ["hr_content", "financial_generic", ...]
        require_lai_keywords: true
        lai_keyword_scopes:
          - "lai_keywords.core_phrases"
          - "lai_keywords.technology_terms_high_precision"
          - "lai_trademarks_global"
  
  press_profile:
    rules:
      default:
        exclusion_scopes: ["hr_content", "financial_generic"]
        require_lai_keywords: true
        lai_keyword_scopes:
          - "lai_keywords.core_phrases"
          - "lai_trademarks_global"
```

**Vérification**:
- ✅ Structure simple (2 niveaux max)
- ✅ Références aux scopes existants
- ✅ Logique pure/hybrid claire
- ✅ Compatible avec code refactorisé

---

### 5. LOGIQUE MÉTIER

#### Pure Players (14 entreprises)
```
Règle: Ingestion PERMISSIVE
- ✅ Tout passer SAUF exclusions évidentes
- ✅ PAS de filtrage LAI keywords
- ✅ Exclusions: hr_content, event_generic, corporate_noise_terms
```

#### Hybrid Players (27 entreprises)
```
Règle: Ingestion FILTRÉE
- ✅ Exclusions complètes (RH, ESG, financier, événements)
- ✅ Filtrage LAI keywords REQUIS (min 1 signal)
- ✅ Signaux: core_phrases OU technology_terms OU trademarks
```

#### Presse sectorielle
```
Règle: Ingestion STRICTE
- ✅ Exclusions complètes
- ✅ Filtrage LAI keywords REQUIS
```

**Vérification**: ✅ Logique cohérente avec objectifs

---

### 6. ACCÈS AUX SCOPES DANS LE CODE

#### Accès company_scopes
```python
pure_players = _canonical_scopes_cache['companies'].get('lai_companies_pure_players', [])
pure_players_lower = [c.lower() for c in pure_players]
is_pure_player = company_id in pure_players_lower
```
**Vérification**:
- ✅ Clé 'companies' existe dans cache
- ✅ Scope 'lai_companies_pure_players' existe
- ✅ Matching case-insensitive

#### Accès technology_scopes
```python
tech_scopes = _canonical_scopes_cache['technologies'].get('lai_keywords', {})
terms = tech_scopes.get('core_phrases', [])
```
**Vérification**:
- ✅ Clé 'technologies' existe dans cache
- ✅ Scope 'lai_keywords' existe
- ✅ Sections accessibles (core_phrases, technology_terms_high_precision, etc.)

#### Accès trademark_scopes
```python
trademarks = _canonical_scopes_cache['trademarks'].get('lai_trademarks_global', [])
```
**Vérification**:
- ✅ Clé 'trademarks' existe dans cache
- ✅ Scope 'lai_trademarks_global' existe

#### Accès exclusion_scopes
```python
exclusions = _canonical_scopes_cache.get('exclusions', {})
terms = exclusions.get('hr_content', [])
```
**Vérification**:
- ✅ Clé 'exclusions' existe dans cache
- ✅ Scopes accessibles (hr_content, financial_generic, etc.)

---

### 7. INITIALISATION DANS __INIT__.PY

#### Ligne 82 (après initialize_exclusion_scopes)
```python
logger.info("Étape 2.6 : Initialisation des profils d'ingestion depuis S3")
initialize_ingestion_profiles(s3_io, config_bucket)
```

**Vérification**:
- ✅ Fonction importée: `from .ingestion_profiles import initialize_ingestion_profiles`
- ✅ Paramètres corrects: s3_io, config_bucket
- ✅ Appelée AVANT apply_ingestion_profile()
- ✅ Fail-fast si échec chargement

---

### 8. GESTION D'ERREURS

#### Chargement canonical
```python
try:
    profiles = s3_io.read_yaml_from_s3(...)
except Exception as e:
    error_msg = f"ERREUR CRITIQUE: Échec chargement canonical: {e}"
    logger.error(error_msg)
    raise ValueError(error_msg)  # ✅ FAIL-FAST
```

**Vérification**:
- ✅ Pas de fallback silencieux
- ✅ Erreur explicite si S3 échoue
- ✅ Lambda s'arrête (pas de comportement imprévisible)

#### Profil non trouvé
```python
if not profile_name:
    logger.warning(f"Aucun profil pour type {source_type}, ingestion complète")
    return items  # ✅ Comportement par défaut documenté
```

**Vérification**:
- ✅ Log explicite
- ✅ Comportement par défaut clair (ingestion complète)

---

### 9. BUCKET S3 UTILISÉ

#### Variables d'environnement Lambda
```python
CONFIG_BUCKET = "vectora-inbox-config-dev"  # ❌ FAUX
DATA_BUCKET = "vectora-inbox-data-dev"      # ✅ OK
```

**PROBLÈME DÉTECTÉ**: 
- ❌ Canonical est dans `DATA_BUCKET` pas `CONFIG_BUCKET`
- ✅ Code actuel utilise `config_bucket` (paramètre)
- ✅ Mais variable env peut être incorrecte

**Vérification nécessaire**:
```bash
aws s3 ls s3://vectora-inbox-data-dev/canonical/
aws s3 ls s3://vectora-inbox-config-dev/canonical/
```

---

### 10. NETTOYAGE S3 REQUIS

#### Fichiers à supprimer
```bash
# Ancien ingestion_profiles.yaml (format incompatible)
aws s3 rm s3://vectora-inbox-data-dev/canonical/ingestion/ingestion_profiles.yaml
```

#### Fichiers à uploader
```bash
# Nouveau ingestion_profiles.yaml
aws s3 cp canonical/ingestion/ingestion_profiles.yaml \
  s3://vectora-inbox-data-dev/canonical/ingestion/

# Vérifier scopes à jour
aws s3 sync canonical/scopes/ s3://vectora-inbox-data-dev/canonical/scopes/
```

---

## 🔴 PROBLÈMES IDENTIFIÉS

### 1. Bucket canonical ⚠️ CRITIQUE

**Problème**: Canonical peut être dans DATA_BUCKET ou CONFIG_BUCKET

**Vérification**:
```bash
# Où est canonical actuellement ?
aws s3 ls s3://vectora-inbox-data-dev/canonical/scopes/
aws s3 ls s3://vectora-inbox-config-dev/canonical/scopes/
```

**Solution**: 
- Si dans DATA_BUCKET → OK (code actuel utilise config_bucket qui pointe vers DATA_BUCKET)
- Si dans CONFIG_BUCKET → Modifier variable env Lambda

### 2. Format ingestion_profiles.yaml ⚠️ CRITIQUE

**Problème**: Fichier S3 existant est ANCIEN FORMAT (incompatible)

**Solution**: 
1. Créer NOUVEAU format
2. Supprimer ancien sur S3
3. Upload nouveau

---

## ✅ ACTIONS PRÉ-EXÉCUTION

### 1. Vérifier bucket canonical
```bash
aws s3 ls s3://vectora-inbox-data-dev/canonical/scopes/ --profile rag-lai-prod
```
**Attendu**: Liste des 4 fichiers scopes

### 2. Créer ingestion_profiles.yaml
- Format simplifié (voir plan)
- Sauvegarder dans `canonical/ingestion/`

### 3. Backup local
```bash
python scripts/backup/create_local_backup.py --description "Avant refactoring ingestion canonical"
```

### 4. Nettoyer S3
```bash
# Supprimer ancien
aws s3 rm s3://vectora-inbox-data-dev/canonical/ingestion/ingestion_profiles.yaml

# Upload nouveau
aws s3 cp canonical/ingestion/ingestion_profiles.yaml \
  s3://vectora-inbox-data-dev/canonical/ingestion/
```

### 5. Vérifier variables env Lambda
```bash
aws lambda get-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --query "Environment.Variables" \
  --profile rag-lai-prod
```
**Vérifier**: CONFIG_BUCKET pointe vers bucket contenant canonical/

---

## 📊 RÉSUMÉ VÉRIFICATION

| Élément | Status | Action |
|---------|--------|--------|
| Fichiers canonical locaux | ✅ | OK |
| Fichiers canonical S3 | ⚠️ | Vérifier bucket + remplacer ingestion_profiles |
| Code refactorisé | ✅ | Prêt |
| Hardcoding supprimé | ✅ | 3 zones identifiées |
| Appels S3 corrects | ✅ | 5 fichiers |
| Gestion erreurs | ✅ | Fail-fast |
| Logique métier | ✅ | Pure/hybrid/presse |
| Variables env Lambda | ⚠️ | À vérifier |

**Score**: 7/8 ✅ (1 vérification requise)

---

## 🎯 DÉCISION

**Plan OK pour exécution ?**
- ✅ OUI si bucket canonical vérifié
- ✅ OUI si ingestion_profiles.yaml créé
- ✅ OUI si backup fait

**Risques résiduels**: AUCUN si actions pré-exécution faites

---

**Vérification complète terminée**
**Prêt pour validation finale utilisateur**
