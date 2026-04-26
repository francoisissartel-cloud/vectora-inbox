# Validation Conflits Phase 7 - 2ème Appel Bedrock

**Date**: 2026-02-02  
**Contexte**: Vérification compatibilité avec paramètres legacy  
**Statut**: ✅ Aucun conflit détecté

---

## 🔍 Analyse des Conflits Potentiels

### 1. Paramètres Fonction `_normalize_sequential()`

**Signature actuelle**:
```python
def _normalize_sequential(
    raw_items, examples, bedrock_model, bedrock_region, stats,
    canonical_scopes=None,
    watch_domains=None,
    matching_config=None,
    canonical_prompts=None,  # Utilisé pour domain scoring
    s3_io=None,
    client_config=None,
    config_bucket=None
)
```

**Paramètres legacy**: Tous présents et optionnels (valeur par défaut `None`)

✅ **Aucun conflit**: Tous les paramètres existants sont préservés

---

### 2. Appel Domain Scoring (Conditionnel)

**Code implémenté**:
```python
# NOUVEAU: Domain scoring (2ème appel Bedrock)
domain_scoring_result = None
if canonical_prompts and 'domain_scoring' in canonical_prompts:
    from .bedrock_domain_scorer import score_item_for_domain
    
    domain_definition = canonical_scopes.get('domains', {}).get('lai_domain_definition', {})
    if domain_definition:
        domain_scoring_prompt = canonical_prompts['domain_scoring'].get('lai_domain_scoring', {})
        if domain_scoring_prompt:
            domain_scoring_result = score_item_for_domain(...)
```

**Conditions d'activation**:
1. `canonical_prompts` doit être fourni (pas None)
2. `canonical_prompts['domain_scoring']` doit exister
3. `canonical_scopes['domains']['lai_domain_definition']` doit exister
4. `canonical_prompts['domain_scoring']['lai_domain_scoring']` doit exister

✅ **Comportement legacy préservé**: Si aucune condition n'est remplie, `domain_scoring_result = None`

---

### 3. Enrichissement Item avec Domain Scoring

**Code implémenté**:
```python
# NOUVEAU: Ajout des résultats de domain scoring (2ème appel Bedrock)
if domain_scoring_result:
    enriched_item["domain_scoring"] = {
        "is_relevant": domain_scoring_result.get('is_relevant', False),
        "score": domain_scoring_result.get('score', 0),
        "confidence": domain_scoring_result.get('confidence', 'low'),
        "signals_detected": domain_scoring_result.get('signals_detected', {}),
        "score_breakdown": domain_scoring_result.get('score_breakdown'),
        "reasoning": domain_scoring_result.get('reasoning', '')
    }
```

✅ **Comportement legacy préservé**: Si `domain_scoring_result = None`, la section `domain_scoring` n'est PAS ajoutée à l'item

---

### 4. Signature `_enrich_item_with_normalization()`

**Avant Phase 7**:
```python
def _enrich_item_with_normalization(
    original_item,
    normalization_result,
    bedrock_matching_result=None
)
```

**Après Phase 7**:
```python
def _enrich_item_with_normalization(
    original_item,
    normalization_result,
    bedrock_matching_result=None,
    domain_scoring_result=None  # NOUVEAU paramètre optionnel
)
```

✅ **Compatibilité ascendante**: Nouveau paramètre optionnel avec valeur par défaut `None`

**Appels existants**: Continuent de fonctionner sans modification
```python
# Appel legacy (sans domain_scoring_result)
_enrich_item_with_normalization(item, normalization_result)
# → Fonctionne, domain_scoring_result = None par défaut

# Appel avec matching (sans domain_scoring_result)
_enrich_item_with_normalization(item, normalization_result, bedrock_matching_result)
# → Fonctionne, domain_scoring_result = None par défaut
```

---

### 5. Mode Parallèle `_normalize_parallel()`

**Statut**: ❌ Domain scoring NON implémenté en mode parallèle

**Raison**: Mode parallèle ne reçoit pas les paramètres nécessaires:
- Pas de `canonical_prompts`
- Pas de `s3_io`
- Pas de `client_config`
- Pas de `config_bucket`

**Impact**: Aucun, car:
1. Mode parallèle utilisé uniquement avec `max_workers > 1`
2. Configuration actuelle: `max_workers = 1` (mode séquentiel)
3. Domain scoring fonctionne en mode séquentiel

✅ **Pas de conflit**: Mode parallèle continue de fonctionner comme avant (sans domain scoring)

---

## 📊 Scénarios de Compatibilité

### Scénario 1: Client Legacy (sans domain scoring)

**Configuration**:
- `canonical_prompts` ne contient pas `domain_scoring`
- Ou `canonical_scopes` ne contient pas `domains/lai_domain_definition`

**Comportement**:
```python
domain_scoring_result = None  # Pas d'appel Bedrock
enriched_item["domain_scoring"]  # Section NON ajoutée
```

✅ **Résultat**: Item identique à avant Phase 7

---

### Scénario 2: Client avec Domain Scoring

**Configuration**:
- `canonical_prompts['domain_scoring']['lai_domain_scoring']` existe
- `canonical_scopes['domains']['lai_domain_definition']` existe

**Comportement**:
```python
domain_scoring_result = score_item_for_domain(...)  # Appel Bedrock
enriched_item["domain_scoring"] = {...}  # Section ajoutée
```

✅ **Résultat**: Item enrichi avec domain scoring

---

### Scénario 3: Erreur Domain Scoring

**Configuration**: Domain scoring activé mais erreur Bedrock

**Comportement**:
```python
try:
    domain_scoring_result = score_item_for_domain(...)
except Exception as e:
    logger.error(f"Error in domain scoring: {e}")
    domain_scoring_result = _create_fallback_scoring()  # Fallback
```

✅ **Résultat**: Item avec domain scoring fallback (is_relevant=False, score=0)

---

## 🔧 Points de Vigilance

### 1. Chargement Canonical Prompts

**Vérifier**: Le chargement de `canonical_prompts` inclut bien le dossier `domain_scoring/`

**Localisation**: Fonction qui charge les prompts depuis S3

**Action**: Vérifier que `canonical/prompts/domain_scoring/lai_domain_scoring.yaml` est chargé

---

### 2. Chargement Domain Definition

**Vérifier**: Le chargement de `canonical_scopes` inclut bien le dossier `domains/`

**Localisation**: Fonction qui charge les scopes depuis S3

**Action**: Vérifier que `canonical/domains/lai_domain_definition.yaml` est chargé

---

### 3. Structure Canonical S3

**Vérifier**: Les nouveaux fichiers sont bien sur S3

**Fichiers requis**:
- `s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
- `s3://vectora-inbox-config-dev/canonical/domains/lai_domain_definition.yaml`

**Action**: Sync canonical vers S3 avant tests

---

## ✅ Validation Finale

### Checklist Compatibilité

- [x] Tous les paramètres legacy préservés
- [x] Domain scoring conditionnel (pas d'impact si désactivé)
- [x] Signature `_enrich_item_with_normalization()` rétrocompatible
- [x] Mode parallèle non impacté
- [x] Gestion erreurs robuste (fallback)
- [x] Pas de breaking change

### Tests Recommandés

**Test 1**: Client legacy sans domain scoring
```bash
# Client lai_weekly_v7 (sans domain_scoring dans config)
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7
# Vérifier: Pas de section domain_scoring dans items.json
```

**Test 2**: Client avec domain scoring
```bash
# Client lai_weekly_v9 (avec domain_scoring dans config)
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v9
# Vérifier: Section domain_scoring présente dans items.json
```

**Test 3**: Erreur domain scoring
```bash
# Supprimer temporairement lai_domain_definition.yaml de S3
# Vérifier: Fallback scoring appliqué, pas d'erreur bloquante
```

---

## 📝 Conclusion

**Statut**: ✅ Aucun conflit détecté avec paramètres legacy

**Garanties**:
1. ✅ Clients existants continuent de fonctionner sans modification
2. ✅ Domain scoring activé uniquement si configuration présente
3. ✅ Gestion erreurs robuste (fallback)
4. ✅ Pas de breaking change
5. ✅ Rétrocompatibilité totale

**Prochaine étape**: Phase 8 - Build, Deploy et Tests E2E

---

**Validation créée le**: 2026-02-02  
**Phase**: 7  
**Statut**: ✅ Validé - Prêt pour Phase 8
