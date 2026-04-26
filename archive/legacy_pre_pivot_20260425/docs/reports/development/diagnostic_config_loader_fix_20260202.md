# Rapport Diagnostic - Fix Config Loader Domain Scoring

**Date**: 2026-02-02  
**Phase**: Phase 2 du plan_diagnostic_domain_scoring_local_20260202.md  
**Objectif**: Corriger le chargement des prompts domain_scoring et domain definitions  
**Statut**: ✅ RÉSOLU

---

## 🎯 PROBLÈME IDENTIFIÉ

### Symptômes
- `enable_domain_scoring: true` dans config lai_weekly_v9 ✅
- Flag `has_domain_scoring=False` dans tous les items ❌
- Temps exécution: 70s (1 appel Bedrock) au lieu de 200s+ (2 appels) ❌
- Erreur logs: "Impossible de charger les prompts canonical: argument of type 'NoneType' is not iterable"

### Cause Racine
**2 problèmes dans `src_v2/vectora_core/shared/config_loader.py`**:

#### Problème 1: load_canonical_prompts()
- Tentait de charger `canonical/prompts/global_prompts.yaml` (ancien fichier)
- Validait la structure avec `'normalization' in prompts and 'lai_default' in prompts['normalization']`
- Mais la nouvelle architecture v2.0 utilise:
  - `canonical/prompts/normalization/generic_normalization.yaml`
  - `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
- Résultat: Retournait un dict VIDE `{}` au lieu de la structure attendue

#### Problème 2: load_canonical_scopes()
- Ne chargeait QUE les scopes (companies, molecules, technologies, trademarks, exclusions)
- Ne chargeait PAS le dossier `canonical/domains/`
- Résultat: Pas de clé `'domains'` dans le dict retourné
- Le normalizer ne trouvait pas `canonical_scopes['domains']['lai_domain_definition']`

---

## 🔧 SOLUTION IMPLÉMENTÉE

### Fix 1: load_canonical_prompts()

**Avant**:
```python
def load_canonical_prompts(config_bucket: str) -> Dict[str, Any]:
    try:
        prompts = s3_io.read_yaml_from_s3(config_bucket, "canonical/prompts/global_prompts.yaml")
        
        # Validation présence prompts anti-hallucinations
        if 'normalization' in prompts and 'lai_default' in prompts['normalization']:
            # ...
        
        return prompts
    except Exception as e:
        logger.error(f"Impossible de charger les prompts canonical: {str(e)}")
        return {}
```

**Après**:
```python
def load_canonical_prompts(config_bucket: str) -> Dict[str, Any]:
    all_prompts = {}
    
    # Chargement des différents types de prompts
    prompt_files = {
        "normalization": {
            "generic_normalization": "canonical/prompts/normalization/generic_normalization.yaml"
        },
        "domain_scoring": {
            "lai_domain_scoring": "canonical/prompts/domain_scoring/lai_domain_scoring.yaml"
        },
        "matching": {
            "lai_matching": "canonical/prompts/matching/lai_matching.yaml"
        },
        "editorial": {
            "lai_editorial": "canonical/prompts/editorial/lai_editorial.yaml"
        }
    }
    
    for category, prompts_dict in prompt_files.items():
        category_prompts = {}
        for prompt_name, file_path in prompts_dict.items():
            try:
                prompt_data = s3_io.read_yaml_from_s3(config_bucket, file_path)
                category_prompts[prompt_name] = prompt_data
                logger.info(f"Prompt chargé : {category}/{prompt_name}")
            except Exception as e:
                logger.warning(f"Impossible de charger {file_path}: {str(e)}")
        
        if category_prompts:
            all_prompts[category] = category_prompts
    
    # Validation structure
    if 'normalization' in all_prompts and 'generic_normalization' in all_prompts['normalization']:
        logger.info("✅ Generic normalization prompt loaded")
    
    if 'domain_scoring' in all_prompts and 'lai_domain_scoring' in all_prompts['domain_scoring']:
        logger.info("✅ LAI domain scoring prompt loaded")
    
    return all_prompts
```

**Changements**:
- Charge chaque prompt individuellement depuis son fichier dédié
- Structure retournée: `{'normalization': {'generic_normalization': {...}}, 'domain_scoring': {'lai_domain_scoring': {...}}, ...}`
- Validation adaptée à la nouvelle structure
- Gestion d'erreur par fichier (pas de fail global)

---

### Fix 2: load_canonical_scopes()

**Avant**:
```python
def load_canonical_scopes(config_bucket: str) -> Dict[str, Any]:
    all_scopes = {}
    
    scope_files = {
        "companies": "canonical/scopes/company_scopes.yaml",
        "molecules": "canonical/scopes/molecule_scopes.yaml", 
        "technologies": "canonical/scopes/technology_scopes.yaml",
        "trademarks": "canonical/scopes/trademark_scopes.yaml",
        "exclusions": "canonical/scopes/exclusion_scopes.yaml"
    }
    
    for scope_type, file_path in scope_files.items():
        # Chargement et aplatissement...
        all_scopes.update(flattened_scopes)
    
    return all_scopes  # Retourne SEULEMENT les scopes aplatis
```

**Après**:
```python
def load_canonical_scopes(config_bucket: str) -> Dict[str, Any]:
    all_scopes = {}
    
    # Chargement scopes (inchangé)
    scope_files = {...}
    for scope_type, file_path in scope_files.items():
        # ...
        all_scopes.update(flattened_scopes)
    
    # Chargement des domain definitions (NOUVEAU)
    domains = {}
    domain_files = {
        "lai_domain_definition": "canonical/domains/lai_domain_definition.yaml"
    }
    
    for domain_name, file_path in domain_files.items():
        try:
            domain_data = s3_io.read_yaml_from_s3(config_bucket, file_path)
            domains[domain_name] = domain_data
            logger.info(f"Domain definition chargée : {domain_name}")
        except Exception as e:
            logger.warning(f"Impossible de charger {file_path}: {str(e)}")
    
    # Structure finale: scopes aplatis + domains
    result = all_scopes.copy()
    if domains:
        result['domains'] = domains
        logger.info(f"Domains ajoutés : {len(domains)} domain(s)")
    
    return result
```

**Changements**:
- Charge les domain definitions depuis `canonical/domains/`
- Ajoute une clé `'domains'` dans le dict retourné
- Structure retournée: `{...scopes aplatis..., 'domains': {'lai_domain_definition': {...}}}`
- Extensible pour futurs domains (sirna, cell_therapy, etc.)

---

## ✅ VALIDATION

### Tests Unitaires
**Fichier**: `tests/unit/test_config_loader_domain_scoring.py`

**Résultats**:
```
TEST: load_canonical_prompts - Domain Scoring
✅ Prompts loaded successfully
   Top-level keys: ['normalization', 'domain_scoring', 'matching', 'editorial']
✅ 'domain_scoring' key found
   Keys: ['lai_domain_scoring']
✅ 'lai_domain_scoring' key found
   Type: <class 'dict'>
   Keys: ['metadata', 'system_instructions', 'user_template', 'bedrock_config', 'validation_rules']

TEST: load_canonical_scopes - Domains
✅ Scopes loaded successfully
   Top-level keys: [...22 scopes..., 'domains']
✅ 'domains' key found
   Keys: ['lai_domain_definition']
✅ 'lai_domain_definition' key found
   Type: <class 'dict'>
   Keys: ['domain_id', 'domain_name', 'version', 'created_date', 'definition']

TEST: Config Loader Structure
✅ TEST PASSED: Structure analysis complete
   Prompts keys: ['normalization', 'domain_scoring', 'matching', 'editorial']
   Domain scoring keys: ['lai_domain_scoring']
   Scopes keys: [...22 scopes..., 'domains']
   Domains keys: ['lai_domain_definition']
```

**Statut**: ✅ 3/3 tests passent

---

## 📊 IMPACT

### Fichiers Modifiés
1. `src_v2/vectora_core/shared/config_loader.py`
   - Fonction `load_canonical_prompts()` : Refactorée complètement
   - Fonction `load_canonical_scopes()` : Ajout chargement domains

### Fichiers Créés
1. `tests/unit/test_config_loader_domain_scoring.py` : Tests unitaires

### Version
- VECTORA_CORE: 1.4.0 → 1.4.1 (PATCH)
- Layer: v50 → v51 (à déployer)

---

## 🚀 PROCHAINES ÉTAPES

### Avant Déploiement AWS
- [x] Tests unitaires passent
- [x] Build layer v51 réussi
- [ ] Test E2E local (optionnel mais recommandé)
- [ ] Deploy dev + test E2E AWS

### Après Déploiement
- [ ] Exécuter plan_test_e2e_lai_weekly_v9_phase8_20260202.md
- [ ] Valider section domain_scoring dans items.json
- [ ] Comparer v8 (baseline) vs v9 (domain scoring)
- [ ] Créer rapport E2E complet

---

## 📝 LEÇONS APPRISES

### ✅ Bonnes Pratiques Validées
1. **Tests unitaires AVANT déploiement** : Le problème a été détecté en local
2. **Fail-fast** : Logs explicites ont permis d'identifier rapidement la cause
3. **Structure modulaire** : Chaque prompt dans son fichier facilite la maintenance

### ⚠️ Points d'Amélioration
1. **Tests d'intégration manquants** : Pas de test validant le chargement complet
2. **Documentation structure canonical** : Pas de schéma clair de l'arborescence attendue
3. **Validation au démarrage Lambda** : Devrait fail-fast si prompts/domains manquants

### 🎓 Recommandations Futures
1. Ajouter tests d'intégration pour config_loader
2. Documenter structure canonical dans blueprint
3. Ajouter validation stricte au démarrage des Lambdas
4. Créer script de validation canonical (pre-deploy check)

---

## ✅ CONCLUSION

**Problème**: Config loader ne chargeait pas les prompts domain_scoring ni les domain definitions

**Solution**: Refactoring complet de `load_canonical_prompts()` et `load_canonical_scopes()`

**Validation**: Tests unitaires passent, structure correcte retournée

**Statut**: ✅ RÉSOLU - Prêt pour déploiement et test E2E

**Version**: VECTORA_CORE 1.4.1 (layer v51)

---

**Rapport créé le**: 2026-02-02  
**Auteur**: Diagnostic automatisé  
**Fichier**: `docs/reports/development/diagnostic_config_loader_fix_20260202.md`
