# LAI KEYWORDS - Localisation et Utilisation

**Date**: 2026-02-06  
**Question**: Où seront les lai_keywords après refactoring ?

---

## ✅ RÉPONSE : DÉJÀ DANS TECHNOLOGY_SCOPES.YAML

Les LAI keywords sont **DÉJÀ consolidés** dans :
```
canonical/scopes/technology_scopes.yaml
```

### Structure existante (RICHE)

```yaml
lai_keywords:
  _metadata:
    profile: technology_complex
    description: "Long-Acting Injectables - requires multiple signal types"
  
  core_phrases:  # 13 phrases haute précision
    - "long-acting injectable"
    - "extended-release injection"
    - "depot injection"
    - ...
  
  technology_terms_high_precision:  # 56 termes DDS/HLE
    - "PharmaShell®"
    - "PLGA microspheres"
    - "PASylation"
    - "Fc fusion"
    - ...
  
  technology_use:  # 10 termes usage
    - "injectable"
    - "injection"
    - "depot"
    - ...
  
  route_admin_terms:  # 13 routes
    - "intramuscular"
    - "subcutaneous"
    - "intravitreal"
    - ...
  
  interval_patterns:  # 14 patterns dosage
    - "once-monthly"
    - "q4w"
    - "q8w"
    - ...
  
  generic_terms:  # Termes trop génériques
  negative_terms:  # Exclusions
```

**Total**: ~100 termes LAI structurés

---

## 📊 SOURCES ANALYSÉES

### 1. technology_scopes.yaml ✅
- **Contient**: lai_keywords avec 8 sections
- **Qualité**: Structure riche, bien organisée
- **Action**: UTILISER tel quel

### 2. trademark_scopes.yaml ✅
- **Contient**: lai_trademarks_global (76 trademarks)
- **Qualité**: Liste complète
- **Action**: UTILISER tel quel

### 3. route_admin.csv ❌
- **Status**: N'existe PAS dans canonical/
- **Contenu**: Déjà intégré dans `lai_keywords.route_admin_terms`
- **Action**: RIEN (déjà dans technology_scopes)

### 4. technology_family.csv ❌
- **Status**: N'existe PAS dans canonical/
- **Action**: RIEN (pas nécessaire pour ingestion)

### 5. technology_tag.csv ❌
- **Status**: N'existe PAS dans canonical/
- **Action**: RIEN (pas nécessaire pour ingestion)

### 6. technology_type.csv ❌
- **Status**: N'existe PAS dans canonical/
- **Action**: RIEN (pas nécessaire pour ingestion)

---

## 🎯 DÉCISION : PAS DE NOUVEAU FICHIER

### Pourquoi ?

1. **technology_scopes.yaml** contient DÉJÀ tout :
   - Core phrases LAI
   - Technologies DDS/HLE
   - Routes d'administration
   - Patterns de dosage

2. **trademark_scopes.yaml** contient les trademarks

3. Les CSV n'existent pas et ne sont pas nécessaires

### Structure finale

```
canonical/scopes/
├── technology_scopes.yaml  ← LAI keywords ICI (lai_keywords.*)
├── trademark_scopes.yaml   ← Trademarks ICI (lai_trademarks_global)
├── company_scopes.yaml     ← Pure/hybrid players
└── exclusion_scopes.yaml   ← Exclusions
```

---

## 💻 UTILISATION DANS LE CODE

### Nouveau code refactorisé

```python
def initialize_ingestion_profiles(s3_io, config_bucket: str):
    # Charger technology_scopes.yaml
    scopes['technologies'] = s3_io.read_yaml_from_s3(
        config_bucket, 
        'canonical/scopes/technology_scopes.yaml'
    )
    # Contient: lai_keywords.core_phrases, 
    #           lai_keywords.technology_terms_high_precision, etc.
    
    # Charger trademark_scopes.yaml
    scopes['trademarks'] = s3_io.read_yaml_from_s3(
        config_bucket, 
        'canonical/scopes/trademark_scopes.yaml'
    )
    # Contient: lai_trademarks_global
```

### Accès aux keywords

```python
def _contains_lai_keywords(text: str, keyword_scopes: List[str]) -> bool:
    for scope_path in keyword_scopes:
        # Exemple: "lai_keywords.core_phrases"
        if scope_path.startswith('lai_keywords.'):
            section = scope_path.split('.')[1]  # "core_phrases"
            tech_scopes = _canonical_scopes_cache['technologies']
            terms = tech_scopes['lai_keywords'][section]
            if any(term.lower() in text for term in terms):
                return True
        
        # Exemple: "lai_trademarks_global"
        elif scope_path == 'lai_trademarks_global':
            trademarks = _canonical_scopes_cache['trademarks']['lai_trademarks_global']
            if any(tm.lower() in text for tm in trademarks):
                return True
    
    return False
```

---

## 📋 CONFIGURATION INGESTION_PROFILES.YAML

### Référence aux LAI keywords

```yaml
profiles:
  corporate_profile:
    rules:
      hybrid_players:
        require_lai_keywords: true
        lai_keyword_scopes:
          - "lai_keywords.core_phrases"              # technology_scopes.yaml
          - "lai_keywords.technology_terms_high_precision"  # technology_scopes.yaml
          - "lai_keywords.interval_patterns"         # technology_scopes.yaml
          - "lai_trademarks_global"                  # trademark_scopes.yaml
        min_lai_signals: 1
```

**Explication**:
- `lai_keywords.*` → Cherche dans `technology_scopes.yaml`
- `lai_trademarks_global` → Cherche dans `trademark_scopes.yaml`

---

## ✅ CONCLUSION

**Où seront les LAI keywords ?**

1. ✅ **technology_scopes.yaml** → `lai_keywords.*` (100+ termes structurés)
2. ✅ **trademark_scopes.yaml** → `lai_trademarks_global` (76 trademarks)

**Actions requises**:
- ❌ PAS de nouveau fichier à créer
- ✅ Utiliser fichiers existants
- ✅ Code refactorisé charge ces 2 fichiers

**Fichiers canonical finaux**:
```
canonical/scopes/technology_scopes.yaml  ← LAI keywords
canonical/scopes/trademark_scopes.yaml   ← Trademarks
canonical/scopes/company_scopes.yaml     ← Pure/hybrid
canonical/scopes/exclusion_scopes.yaml   ← Exclusions
canonical/ingestion/ingestion_profiles.yaml  ← Profils (à créer)
```

**Total**: 5 fichiers canonical, TOUS existent sauf ingestion_profiles.yaml (à créer au nouveau format)
