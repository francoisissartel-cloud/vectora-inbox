# Diagnostic Détaillé : Dysfonctionnements Lambda normalize_score V2

**Date** : 15 janvier 2025  
**Scope** : Analyse comparative V1 vs V2 - Normalisation et Matching/Scoring  
**Objectif** : Identifier les causes racines des dysfonctionnements V2 et recommandations d'amélioration

---

## 1. Résumé Exécutif

### 1.1 Problème Principal
La lambda `normalize_score` V2 présente des dysfonctionnements critiques dans la normalisation et le scoring des items, contrastant avec la V1 qui fonctionnait correctement. L'analyse révèle des ruptures architecturales et une perte de fonctionnalités métier essentielles.

### 1.2 Impact Métier
- **Perte de qualité** : Normalisation Bedrock défaillante
- **Matching déficient** : Logique de matching aux domaines simplifiée à l'excès
- **Scoring inadéquat** : Règles métier non implémentées
- **Prompts dégradés** : Perte des optimisations LAI spécialisées

### 1.3 Causes Racines Identifiées
1. **Architecture fragmentée** : Séparation V2 mal exécutée avec perte de cohérence
2. **Prompts canoniques non utilisés** : Retour aux prompts hardcodés basiques
3. **Logique métier incomplète** : Modules V2 sous-développés vs V1 mature
4. **Gestion d'erreurs défaillante** : Pas de retry, pas de fallback robuste

---

## 2. Analyse Comparative Architecture V1 vs V2

### 2.1 Architecture V1 (Fonctionnelle)

**Structure monolithique cohérente** :
```
src/vectora_core/
├── normalization/
│   ├── normalizer.py           # Orchestration complète
│   ├── bedrock_client.py       # Client robuste avec retry
│   ├── entity_detector.py      # Détection par règles + Bedrock
│   └── domain_context_builder.py # Contextes de domaines
├── matching/
│   └── matcher.py              # Matching sophistiqué
├── scoring/
│   └── scorer.py               # Scoring métier complet
└── prompts/
    └── loader.py               # Prompts canoniques
```

**Points forts V1** :
- ✅ **Orchestration unifiée** : `run_ingest_normalize_for_client()` gère tout le pipeline
- ✅ **Client Bedrock robuste** : Retry automatique, gestion throttling, prompts canoniques
- ✅ **Logique métier mature** : Détection hybride (règles + IA), scoring LAI spécialisé
- ✅ **Gestion d'erreurs complète** : Fallbacks, logging détaillé, statistiques

### 2.2 Architecture V2 (Dysfonctionnelle)

**Structure fragmentée incomplète** :
```
src_v2/vectora_core/
├── normalization/
│   ├── __init__.py             # Orchestration basique
│   ├── normalizer.py           # Logique simplifiée
│   ├── bedrock_client.py       # Client basique sans retry
│   ├── matcher.py              # Matching minimal
│   └── scorer.py               # Scoring incomplet
└── shared/
    ├── config_loader.py        # Chargement config
    └── s3_io.py                # I/O S3
```

**Problèmes V2** :
- ❌ **Séparation artificielle** : Modules séparés sans cohérence fonctionnelle
- ❌ **Client Bedrock dégradé** : Pas de retry, gestion d'erreurs basique
- ❌ **Logique métier incomplète** : Modules sous-développés
- ❌ **Perte de fonctionnalités** : Prompts canoniques, détection hybride, scoring LAI

---

## 3. Analyse Détaillée des Dysfonctionnements

### 3.1 Normalisation Bedrock - Régression Critique

#### V1 : Normalisation Robuste et Spécialisée

**Fonctionnalités V1** :
```python
# src/vectora_core/normalization/bedrock_client.py
def normalize_item_with_bedrock(item_text, model_id, canonical_examples, domain_contexts):
    # ✅ Prompts canoniques avec fallback hardcodé
    prompt = _build_normalization_prompt_v1(item_text, canonical_examples, domain_contexts)
    
    # ✅ Retry automatique avec backoff exponentiel
    response_text = _call_bedrock_with_retry(model_id, request_body, max_retries=3)
    
    # ✅ Parsing robuste avec validation
    result = _parse_bedrock_response(response_text)
    
    # ✅ Champs LAI spécialisés
    return {
        'lai_relevance_score': result.get('lai_relevance_score', 0),
        'anti_lai_detected': result.get('anti_lai_detected', False),
        'pure_player_context': result.get('pure_player_context', False),
        'domain_relevance': result.get('domain_relevance', [])
    }
```

**Prompts V1 - Spécialisés LAI** :
- Focus LAI explicite avec technologies spécialisées
- Exemples d'entités depuis canonical scopes
- Trademarks LAI privilégiés (UZEDY, BEPO, Aristada)
- Scoring LAI intégré (0-10)
- Détection anti-LAI (oral routes)

#### V2 : Normalisation Dégradée

**Problèmes V2** :
```python
# src_v2/vectora_core/normalization/bedrock_client.py
class BedrockNormalizationClient:
    def normalize_item(self, item_text, prompt_template, examples, max_retries=3):
        # ❌ Pas de retry automatique implémenté
        # ❌ Gestion d'erreurs basique
        # ❌ Prompts canoniques non utilisés
        # ❌ Pas de champs LAI spécialisés
```

**Régressions identifiées** :
1. **Pas de retry automatique** : Échecs sur throttling Bedrock
2. **Prompts génériques** : Perte de la spécialisation LAI
3. **Gestion d'erreurs basique** : Pas de fallback robuste
4. **Champs manquants** : `lai_relevance_score`, `domain_relevance` absents

### 3.2 Matching aux Domaines - Logique Simplifiée

#### V1 : Matching Sophistiqué

**Fonctionnalités V1** :
```python
# src/vectora_core/matching/matcher.py
def match_items_to_domains(items, watch_domains, canonical_scopes, matching_rules):
    # ✅ Matching multi-critères (entités + contexte)
    # ✅ Privilèges trademarks avec boost_factor
    # ✅ Évaluation domain_relevance par domaine
    # ✅ Règles métier par type de domaine
```

**Règles V1 sophistiquées** :
- `trademark_privileges` avec `boost_factor: 2.5`
- `require_entity_signals` par type de domaine
- `min_technology_signals` adaptatif
- Évaluation `domain_relevance` avec scores et raisons

#### V2 : Matching Minimal

**Problèmes V2** :
```python
# src_v2/vectora_core/normalization/matcher.py
def match_items_to_domains(normalized_items, client_config, canonical_scopes):
    # ❌ Logique de matching non implémentée
    # ❌ Pas de privilèges trademarks
    # ❌ Pas d'évaluation domain_relevance
    # ❌ Règles métier absentes
```

### 3.3 Scoring de Pertinence - Règles Métier Manquantes

#### V1 : Scoring LAI Spécialisé

**Fonctionnalités V1** :
```python
# src/vectora_core/scoring/scorer.py
def score_items(matched_items, scoring_rules, watch_domains, canonical_scopes):
    # ✅ Bonus pure players LAI (5.0)
    # ✅ Bonus trademarks LAI (4.0)
    # ✅ Poids par type d'événement
    # ✅ Facteurs de récence
    # ✅ Seuils de sélection configurables
```

**Configuration V1 dans lai_weekly_v3.yaml** :
```yaml
scoring_config:
  client_specific_bonuses:
    pure_player_companies:
      scope: "lai_companies_mvp_core"
      bonus: 5.0
    trademark_mentions:
      scope: "lai_trademarks_global"
      bonus: 4.0
  selection_overrides:
    min_score: 12
    max_items_total: 15
```

#### V2 : Scoring Incomplet

**Problèmes V2** :
```python
# src_v2/vectora_core/normalization/scorer.py
def score_items(matched_items, client_config, canonical_scopes, scoring_mode, target_date):
    # ❌ Règles de scoring non implémentées
    # ❌ Pas de bonus spécialisés LAI
    # ❌ Pas de facteurs de récence
    # ❌ Seuils de sélection ignorés
```

---

## 4. Analyse des Prompts Bedrock

### 4.1 Prompts V1 - Optimisés et Canoniques

**Système de prompts V1** :
```python
# Prompts canoniques avec fallback
use_canonical = os.environ.get('USE_CANONICAL_PROMPTS', 'false').lower() == 'true'
if use_canonical:
    canonical_prompt = _try_canonical_prompt(...)
    if canonical_prompt:
        return canonical_prompt
# Fallback vers prompt hardcodé optimisé
return _build_normalization_prompt_hardcoded(...)
```

**Prompt V1 - Spécialisé LAI** (canonical/prompts/global_prompts.yaml) :
```yaml
normalization:
  lai_default:
    user_template: |
      LAI TECHNOLOGY FOCUS:
      Detect these LAI (Long-Acting Injectable) technologies:
      - Extended-Release Injectable, Long-Acting Injectable
      - Depot Injection, Once-Monthly Injection
      - Microspheres, PLGA, In-Situ Depot, Hydrogel
      
      TRADEMARKS to detect:
      - UZEDY, PharmaShell, SiliaShell, BEPO, Aristada, Abilify Maintena
      
      8. Evaluate LAI relevance (0-10 score)
      9. Detect anti-LAI signals: oral routes (tablets, capsules, pills)
      10. Assess pure player context: LAI-focused company without explicit LAI mentions
```

### 4.2 Prompts V2 - Génériques et Incomplets

**Problèmes V2** :
1. **Prompts canoniques non utilisés** : Pas d'intégration avec global_prompts.yaml
2. **Prompts génériques** : Pas de spécialisation LAI
3. **Champs manquants** : `lai_relevance_score`, `anti_lai_detected` absents
4. **Pas de trademarks privilégiés** : Perte du focus marques LAI

---

## 5. Gestion des Données et Flux

### 5.1 V1 : Flux Intégré et Robuste

**Pipeline V1** :
```python
def run_ingest_normalize_for_client():
    # 1. Ingestion + parsing
    all_raw_items = []
    for source_meta in resolved_sources:
        raw_content = fetcher.fetch_source(source_meta)
        raw_items = parser.parse_source_content(raw_content, source_meta)
        all_raw_items.extend(raw_items)
    
    # 2. Filtre temporel AVANT normalisation
    filtered_items = _apply_temporal_filter(all_raw_items, cutoff_date_str)
    
    # 3. Normalisation batch avec parallélisation contrôlée
    normalized_items = normalizer.normalize_items_batch(
        filtered_items, canonical_scopes, bedrock_model_id, watch_domains
    )
    
    # 4. Écriture S3 avec path structuré
    s3_key = f"normalized/{client_id}/{year}/{month}/{day}/items.json"
    s3_client.write_json_to_s3(data_bucket, s3_key, normalized_items)
```

### 5.2 V2 : Flux Fragmenté et Incomplet

**Problèmes V2** :
```python
def run_normalize_score_for_client():
    # ❌ Identification "dernier run" fragile
    last_run_path = _find_last_ingestion_run(client_id, data_bucket)
    
    # ❌ Pas de filtre temporel
    # ❌ Pas de parallélisation contrôlée
    # ❌ Gestion d'erreurs basique
```

**Régressions identifiées** :
1. **Stratégie "dernier run" fragile** : Dépendance sur structure S3 rigide
2. **Pas de filtre temporel** : Traitement d'items obsolètes
3. **Pas de parallélisation** : Performance dégradée
4. **Gestion d'erreurs insuffisante** : Pas de statistiques détaillées

---

## 6. Configuration et Canonical

### 6.1 V1 : Configuration Riche et Utilisée

**Utilisation complète des scopes** :
```python
# Chargement complet
canonical_scopes = loader.load_canonical_scopes(config_bucket)
scoring_rules = loader.load_scoring_rules(config_bucket)
matching_rules = resolver.load_matching_rules(config_bucket)

# Utilisation effective
examples = _extract_canonical_examples_enhanced(canonical_scopes)
domain_contexts = domain_builder.build_domain_contexts(watch_domains)
```

**Scopes LAI disponibles** :
- `lai_companies_mvp_core` : 5 pure players (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
- `lai_trademarks_global` : 70+ marques LAI
- `lai_molecules_global` : 90+ molécules par indication
- `lai_keywords` : 80+ mots-clés technologiques

### 6.2 V2 : Configuration Sous-Utilisée

**Problèmes V2** :
```python
# Chargement partiel
canonical_scopes = config_loader.load_canonical_scopes(env_vars["CONFIG_BUCKET"])
canonical_prompts = config_loader.load_canonical_prompts(env_vars["CONFIG_BUCKET"])

# ❌ Utilisation minimale des scopes
# ❌ Prompts canoniques non utilisés
# ❌ Règles de scoring ignorées
```

---

## 7. Recommandations d'Amélioration

### 7.1 Priorité P0 - Restauration Fonctionnalités Critiques

#### 7.1.1 Client Bedrock Robuste
```python
# À implémenter dans src_v2/vectora_core/normalization/bedrock_client.py
class BedrockNormalizationClient:
    def normalize_item(self, item_text, prompt_template, examples, max_retries=3):
        # ✅ Implémenter retry automatique avec backoff exponentiel
        # ✅ Gestion throttling Bedrock
        # ✅ Parsing robuste avec validation
        # ✅ Logging détaillé des appels
```

#### 7.1.2 Prompts LAI Spécialisés
```python
# À restaurer depuis V1
def _build_lai_specialized_prompt(item_text, canonical_examples):
    # ✅ Focus LAI explicite
    # ✅ Trademarks privilégiés
    # ✅ Champs LAI spécialisés (lai_relevance_score, anti_lai_detected)
    # ✅ Exemples depuis canonical scopes
```

#### 7.1.3 Matching Sophistiqué
```python
# À implémenter dans src_v2/vectora_core/normalization/matcher.py
def match_items_to_domains(normalized_items, client_config, canonical_scopes):
    # ✅ Privilèges trademarks avec boost_factor
    # ✅ Règles par type de domaine
    # ✅ Évaluation domain_relevance
    # ✅ Matching multi-critères
```

### 7.2 Priorité P1 - Scoring Métier Complet

#### 7.2.1 Règles de Scoring LAI
```python
# À implémenter dans src_v2/vectora_core/normalization/scorer.py
def score_items(matched_items, client_config, canonical_scopes, scoring_mode):
    # ✅ Bonus pure players LAI (5.0)
    # ✅ Bonus trademarks LAI (4.0)
    # ✅ Poids par type d'événement
    # ✅ Facteurs de récence
    # ✅ Seuils de sélection
```

#### 7.2.2 Configuration Scoring
```yaml
# À utiliser depuis lai_weekly_v3.yaml
scoring_config:
  client_specific_bonuses:
    pure_player_companies:
      scope: "lai_companies_mvp_core"
      bonus: 5.0
    trademark_mentions:
      scope: "lai_trademarks_global" 
      bonus: 4.0
```

### 7.3 Priorité P2 - Robustesse et Performance

#### 7.3.1 Gestion d'Erreurs Complète
```python
# À implémenter
def normalize_items_batch_robust(raw_items, ...):
    # ✅ Parallélisation contrôlée (MAX_BEDROCK_WORKERS)
    # ✅ Statistiques détaillées (success/failed/total)
    # ✅ Fallbacks robustes
    # ✅ Logging structuré
```

#### 7.3.2 Stratégie Données Robuste
```python
# À améliorer
def _find_last_ingestion_run_robust(client_id, data_bucket):
    # ✅ Gestion cas multiples runs même jour
    # ✅ Validation existence fichiers
    # ✅ Fallback sur période configurable
```

---

## 8. Plan d'Implémentation Recommandé

### Phase 1 : Restauration Normalisation (P0)
1. **Migrer client Bedrock V1 → V2** avec retry et gestion d'erreurs
2. **Restaurer prompts LAI spécialisés** depuis canonical/prompts/global_prompts.yaml
3. **Implémenter champs LAI** : lai_relevance_score, anti_lai_detected, pure_player_context
4. **Tests de régression** : Validation vs résultats V1

### Phase 2 : Matching et Scoring (P1)
1. **Implémenter matching sophistiqué** avec privilèges trademarks
2. **Restaurer règles de scoring LAI** depuis lai_weekly_v3.yaml
3. **Implémenter domain_relevance** avec scores et raisons
4. **Tests métier** : Validation scoring sur données réelles

### Phase 3 : Robustesse et Performance (P2)
1. **Parallélisation contrôlée** pour normalisation batch
2. **Stratégie données robuste** pour identification dernier run
3. **Monitoring et métriques** détaillés
4. **Tests de charge** : Validation performance

---

## 9. Conclusion

### 9.1 Diagnostic Final
La lambda `normalize_score` V2 souffre d'une **régression architecturale majeure** par rapport à la V1 fonctionnelle. La séparation des responsabilités, bien qu'architecturalement souhaitable, a été mal exécutée avec une **perte critique de fonctionnalités métier**.

### 9.2 Recommandation Stratégique
**Approche hybride recommandée** :
1. **Conserver l'architecture V2** (séparation des lambdas)
2. **Restaurer la logique métier V1** (normalisation, matching, scoring)
3. **Migrer progressivement** les bonnes pratiques V1 vers V2
4. **Maintenir la compatibilité** avec les règles d'hygiène V4

### 9.3 Risques et Mitigation
- **Risque** : Régression continue si migration incomplète
- **Mitigation** : Tests de régression systématiques vs V1
- **Risque** : Performance dégradée vs V1 monolithique
- **Mitigation** : Parallélisation et optimisations ciblées

La restauration de la lambda V2 nécessite une approche méthodique privilégiant la **restauration fonctionnelle** avant l'optimisation architecturale.

---

**Fin du Diagnostic**  
*Document de travail pour amélioration src_v2 lambda normalize_score*