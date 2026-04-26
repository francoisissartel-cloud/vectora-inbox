# Rapport d'analyse : Implémentation du matching Bedrock dans normalize_score_v2

**Date :** 16 décembre 2025  
**Objectif :** Exécution des phases 1-3 du plan `normalize_score_v2_matching_bedrock_plan.md`  
**Scope :** Analyse technique pour préparer l'implémentation du deuxième appel Bedrock

---

## 🔍 Phase 1 – Découvertes sur l'existant

### Architecture actuelle observée

**Lambda handler actuel :** `src/lambdas/ingest_normalize/handler.py`
- ✅ **Fonction d'orchestration :** `run_ingest_normalize_for_client()` dans `vectora_core/__init__.py`
- ✅ **Pattern conforme :** Handler minimal délégant à vectora_core
- ⚠️ **Limitation :** Combine ingestion + normalisation (pas séparé comme prévu dans l'architecture 3 Lambdas V2)

**Pipeline de normalisation actuel :**
```python
# Dans vectora_core/__init__.py, ligne ~100-120
normalized_items = normalizer.normalize_items_batch(
    filtered_items,
    canonical_scopes,
    bedrock_model_id,
    watch_domains  # ✅ Déjà passé à la normalisation
)
```

**Appel Bedrock existant :** `vectora_core/normalization/bedrock_client.py`
- ✅ **Client configuré :** `get_bedrock_client()` avec région `us-east-1`
- ✅ **Retry automatique :** `_call_bedrock_with_retry()` avec backoff exponentiel
- ✅ **Prompts canonicalisés :** Support des prompts depuis `global_prompts.yaml` (feature flag)
- ✅ **Output structuré :** JSON parsing avec champs LAI (`lai_relevance_score`, `domain_relevance`)

### Point d'insertion identifié

**Emplacement optimal :** Dans `vectora_core/normalization/normalizer.py`, fonction `normalize_item()`

```python
# Ligne ~85-95 actuelle
# Étape 4 : Fusionner les résultats
merged_entities = entity_detector.merge_entity_detections(bedrock_result, rules_result)

# 🎯 POINT D'INSERTION ICI
# Étape 4.5 : Matching Bedrock (NOUVEAU)
if watch_domains:
    bedrock_matching_result = bedrock_matcher.match_watch_domains_with_bedrock(
        normalized_item_partial, watch_domains, canonical_scopes, bedrock_model_id
    )
    # Fusionner avec les résultats existants

# Étape 5 : Construire l'item normalisé final
```

### Chargement des configurations

**Scopes canonical :** ✅ Correctement chargés dans `vectora_core/config/loader.py`
```python
# Structure confirmée
canonical_scopes = {
    "companies": {"lai_companies_global": ["MedinCell", "Teva Pharmaceutical", ...]},
    "technologies": {"lai_keywords": {"core_phrases": [...], "technology_terms_high_precision": [...]}},
    "molecules": {"lai_molecules_global": [...]},
    "trademarks": {"lai_trademarks_global": [...]}
}
```

**Watch domains :** ✅ Déjà disponibles dans le pipeline
```python
# Dans vectora_core/__init__.py, ligne ~95
watch_domains = client_config.get('watch_domains', [])
# Exemple lai_weekly_v3 :
# [{"id": "tech_lai_ecosystem", "company_scope": "lai_companies_global", ...}]
```

---

## 🛠️ Phase 2 – Design fonctionnel validé

### Input/Output du matching Bedrock

**Input validé :**
- ✅ Item normalisé partiel (titre, résumé, entités extraites)
- ✅ Watch domains avec scopes référencés
- ✅ Scopes canonical déjà chargés et structurés
- ✅ Modèle Bedrock et région configurés

**Output cible :**
```json
{
  "matched_domains": ["tech_lai_ecosystem"],
  "domain_relevance": {
    "tech_lai_ecosystem": {
      "score": 0.85,
      "confidence": "high", 
      "reasoning": "Article discusses MedinCell's BEPO technology...",
      "matched_entities": {
        "companies": ["MedinCell"],
        "technologies": ["BEPO", "long-acting injectable"]
      }
    }
  }
}
```

### Contexte des domaines

**Stratégie de contextualisation validée :**
```python
# Pour chaque watch_domain, construire le contexte
def _build_domain_context(domain, canonical_scopes):
    context = f"Domain: {domain['id']} (Type: {domain['type']})\n"
    
    # Ajouter les entités pertinentes depuis les scopes
    if domain.get('company_scope'):
        companies = canonical_scopes['companies'][domain['company_scope']]
        context += f"Relevant companies: {', '.join(companies[:20])}\n"
    
    # Répéter pour molecules, technologies, trademarks
    return context
```

### Gestion des seuils

**Seuils configurables identifiés :**
- Seuil minimum par défaut : `0.4` (40%)
- Seuils par niveau de confiance : `high` ≥0.7, `medium` 0.4-0.7, `low` <0.4
- Configuration dans `client_config` : `matching_config.bedrock_matching_thresholds`

---

## 🏗️ Phase 3 – Design technique détaillé

### Nouveau module à créer

**Fichier :** `src/vectora_core/matching/bedrock_matcher.py`

```python
def match_watch_domains_with_bedrock(
    normalized_item: Dict[str, Any],
    watch_domains: List[Dict[str, Any]], 
    canonical_scopes: Dict[str, Any],
    bedrock_model_id: str,
    bedrock_region: str = "us-east-1"
) -> Dict[str, Any]:
    """
    Évalue la pertinence d'un item normalisé par rapport aux watch_domains via Bedrock.
    
    Returns:
        {
            "matched_domains": ["tech_lai_ecosystem"],
            "domain_relevance": {...}
        }
    """
```

**Fonctions support :**
```python
def _build_domains_context(watch_domains, canonical_scopes) -> str
def _call_bedrock_matching(prompt, bedrock_model_id, bedrock_region) -> str  
def _parse_bedrock_matching_response(response_text) -> Dict[str, Any]
```

### Nouveau prompt canonicalisé

**Emplacement :** `canonical/prompts/global_prompts.yaml`

```yaml
matching:
  matching_watch_domains_v2:
    system_instructions: |
      You are a domain relevance expert for biotech/pharma intelligence.
      Evaluate how relevant a normalized news item is to specific watch domains.
      
    user_template: |
      Evaluate the relevance of this normalized item to the configured watch domains:

      ITEM TO EVALUATE:
      Title: {{item_title}}
      Summary: {{item_summary}}
      Entities: {{item_entities}}
      Event Type: {{item_event_type}}

      WATCH DOMAINS TO EVALUATE:
      {{domains_context}}

      RESPONSE FORMAT (JSON only):
      {
        "domain_evaluations": [
          {
            "domain_id": "...",
            "is_relevant": true/false,
            "relevance_score": 0.0-1.0,
            "confidence": "high/medium/low",
            "reasoning": "...",
            "matched_entities": {...}
          }
        ]
      }

    bedrock_config:
      max_tokens: 1500
      temperature: 0.1
```

### Intégration dans le pipeline

**Modification de :** `src/vectora_core/normalization/normalizer.py`

```python
# Ligne ~85 (après fusion des entités)
merged_entities = entity_detector.merge_entity_detections(bedrock_result, rules_result)

# NOUVEAU : Matching Bedrock si watch_domains fourni
bedrock_matching_result = {}
if watch_domains:
    from vectora_core.matching import bedrock_matcher
    
    # Construire l'item partiel pour le matching
    item_for_matching = {
        'title': raw_item.get('title'),
        'summary': bedrock_result.get('summary', ''),
        'entities': merged_entities,
        'event_type': bedrock_result.get('event_type', 'other')
    }
    
    # Appel Bedrock matching
    bedrock_matching_result = bedrock_matcher.match_watch_domains_with_bedrock(
        item_for_matching, watch_domains, canonical_scopes, bedrock_model_id
    )

# Construire l'item normalisé final avec résultats de matching
normalized_item = {
    # ... champs existants ...
    'matched_domains': bedrock_matching_result.get('matched_domains', []),
    'domain_relevance': bedrock_matching_result.get('domain_relevance', {})
}
```

---

## 📊 Découvertes critiques

### ✅ Points positifs identifiés

1. **Infrastructure Bedrock prête :** Client configuré, retry automatique, prompts canonicalisés supportés
2. **Pipeline d'intégration clair :** Point d'insertion optimal identifié dans `normalize_item()`
3. **Données disponibles :** Scopes canonical et watch_domains déjà chargés et structurés
4. **Architecture conforme :** Respect total des règles `src_lambda_hygiene_v4.md`

### ⚠️ Défis techniques identifiés

1. **Coût Bedrock :** ~800 tokens par item × 15 items = 12K tokens par run (~$0.036)
2. **Latence :** +1-2 secondes par item (15 items = +15-30s au total)
3. **Gestion d'erreurs :** Fallback sur matching déterministe si Bedrock échoue
4. **Parsing JSON :** Robustesse nécessaire pour réponses Bedrock malformées

### 🔧 Optimisations possibles

1. **Parallélisation :** Utiliser `ThreadPoolExecutor` comme dans `normalize_items_batch()`
2. **Cache :** Éviter les appels redondants pour items similaires
3. **Seuils adaptatifs :** Ajuster selon la performance observée
4. **Monitoring :** Logs détaillés pour debugging et optimisation

---

## 🎯 Recommandations pour l'implémentation

### Priorité 1 : Implémentation minimale

1. **Créer :** `vectora_core/matching/bedrock_matcher.py` avec fonction principale
2. **Ajouter :** Prompt `matching_watch_domains_v2` dans `global_prompts.yaml`
3. **Modifier :** `vectora_core/normalization/normalizer.py` pour intégrer l'appel
4. **Tester :** Sur 3-5 items du MVP lai_weekly_v3

### Priorité 2 : Robustesse

1. **Gestion d'erreurs :** Fallback sur matching déterministe
2. **Validation :** Schéma JSON strict pour parsing des réponses
3. **Logs :** Debugging détaillé pour monitoring
4. **Seuils :** Configuration par domaine dans `client_config`

### Priorité 3 : Performance

1. **Parallélisation :** Appels Bedrock concurrents (max 2-3 workers)
2. **Optimisation prompts :** Réduire la taille si possible
3. **Monitoring :** Métriques de coût et latence
4. **Cache :** Pour items identiques (future optimisation)

---

## 📋 Plan d'exécution recommandé

### Étape 1 : Préparation (30 min)
- Créer le fichier `bedrock_matcher.py` avec structure de base
- Ajouter le prompt dans `global_prompts.yaml`
- Créer des tests unitaires simples

### Étape 2 : Implémentation core (60 min)
- Implémenter `match_watch_domains_with_bedrock()`
- Implémenter les fonctions support (`_build_domains_context`, etc.)
- Intégrer dans `normalizer.py`

### Étape 3 : Tests locaux (30 min)
- Tester sur 3 items représentatifs du MVP
- Valider le format JSON de sortie
- Vérifier la gestion d'erreurs

### Étape 4 : Déploiement (15 min)
- Package et déployer la Lambda
- Tester sur un run complet lai_weekly_v3
- Analyser les logs et métriques

**Temps total estimé :** 2h15 pour une implémentation complète et testée

---

## 🚀 Conclusion

L'implémentation du matching Bedrock est **techniquement faisable** avec l'architecture existante. Le point d'insertion est optimal, l'infrastructure Bedrock est prête, et l'impact sur le code existant est minimal.

**Recommandation finale :** **GO pour l'implémentation** avec les priorités définies ci-dessus.

Le prochain plan d'exécution devra détailler les modifications exactes de code, les tests à effectuer, et la stratégie de déploiement pour patcher la Lambda normalize_score_v2 en respectant parfaitement les règles d'hygiène V4.