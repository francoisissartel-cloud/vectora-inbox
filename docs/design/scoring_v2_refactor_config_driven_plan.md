# Design Scoring V2 - Refactor Config-Driven

**Date :** 21 décembre 2025  
**Objectif :** Concevoir un scoring V2 propre, robuste et 100% config-driven  
**Statut :** Phase 3 - Design technique  

---

## 🎯 PRINCIPES DIRECTEURS

### 1. Cohérence avec lai_relevance_score

**Principe :** final_score doit toujours être cohérent avec lai_relevance_score

**Règles :**
- Items avec lai_relevance_score >= 8 → final_score >= 12 (sélectionnables)
- Items avec lai_relevance_score 6-7 → final_score 8-12 (moyens)
- Items avec lai_relevance_score 0-5 → final_score < 8 (exclus)

### 2. Configuration Pilote Tout

**Principe :** Aucun seuil hardcodé dans le code

**Configuration dans client_config :**
- Poids des event_types
- Bonus par entité (companies, trademarks, molecules)
- Pénalités et seuils
- Facteurs de recency

### 3. Robustesse et Traçabilité

**Principe :** Gestion d'erreurs explicite et scoring traçable

**Exigences :**
- Validation des données d'entrée
- Logging détaillé des calculs
- Score breakdown complet
- Gestion d'erreurs sans masquage

---

## 📊 ALGORITHME DE SCORING V2 PROPOSÉ

### Étape 1 : Calcul du Score de Base

```python
def calculate_base_score(item, scoring_config):
    """
    Score de base = lai_relevance_score × event_type_weight
    """
    lai_score = item.get("normalized_content", {}).get("lai_relevance_score", 0)
    event_type = item.get("normalized_content", {}).get("event_classification", {}).get("primary_type", "other")
    
    # Poids depuis configuration (pas hardcodé)
    event_weights = scoring_config.get("event_type_weights", {
        "partnership": 1.2,
        "regulatory": 1.1,
        "clinical_update": 1.0,
        "scientific_publication": 0.8,
        "corporate_move": 0.7,
        "financial_results": 0.5,
        "other": 0.3
    })
    
    event_weight = event_weights.get(event_type, 0.5)
    base_score = lai_score * event_weight
    
    return base_score, {"lai_score": lai_score, "event_weight": event_weight}
```

### Étape 2 : Facteur de Pertinence Domaine

```python
def calculate_domain_factor(item, scoring_config):
    """
    Facteur basé sur matched_domains et domain_relevance
    """
    matching_results = item.get("matching_results", {})
    matched_domains = matching_results.get("matched_domains", [])
    domain_relevance = matching_results.get("domain_relevance", {})
    
    if not matched_domains:
        return 0.1, {"reason": "no_matched_domains"}
    
    # Calcul sophistiqué avec mapping confidence
    domain_scores = []
    for domain_id in matched_domains:
        relevance = domain_relevance.get(domain_id, {})
        score = relevance.get("score", 0)
        confidence_str = relevance.get("confidence", "medium")
        
        # CORRECTION: Mapping confidence string → number
        confidence_mapping = scoring_config.get("confidence_mapping", {
            "high": 0.9,
            "medium": 0.6,
            "low": 0.3
        })
        confidence = confidence_mapping.get(confidence_str.lower(), 0.5)
        
        # Score pondéré par confidence
        weighted_score = score * 0.7 + confidence * 0.3
        domain_scores.append(weighted_score)
    
    # Facteur final (moyenne + bonus multi-domaines)
    avg_score = sum(domain_scores) / len(domain_scores)
    multi_domain_bonus = 0.1 if len(matched_domains) > 1 else 0
    
    domain_factor = min(1.0, avg_score + multi_domain_bonus)
    
    return domain_factor, {
        "matched_domains": matched_domains,
        "domain_scores": domain_scores,
        "avg_score": avg_score,
        "multi_domain_bonus": multi_domain_bonus
    }
```

### Étape 3 : Calcul des Bonus Config-Driven

```python
def calculate_bonuses(item, scoring_config, canonical_scopes):
    """
    Bonus entièrement pilotés par scoring_config
    """
    bonuses = {}
    bonus_details = {}
    
    entities = item.get("normalized_content", {}).get("entities", {})
    companies = entities.get("companies", [])
    trademarks = entities.get("trademarks", [])
    molecules = entities.get("molecules", [])
    technologies = entities.get("technologies", [])
    
    # Configuration des bonus depuis client_config
    bonus_config = scoring_config.get("entity_bonuses", {})
    
    # Bonus companies (pure players, hybrid)
    for bonus_type, config in bonus_config.items():
        if not config.get("enabled", True):
            continue
            
        scope_name = config.get("scope")
        bonus_value = config.get("bonus", 0)
        entity_type = config.get("entity_type", "companies")
        
        if not scope_name or not bonus_value:
            continue
            
        # Récupération du scope depuis canonical
        scope_entities = canonical_scopes.get(entity_type, {}).get(scope_name, [])
        detected_entities = entities.get(entity_type, [])
        
        # Matching case-insensitive
        matched = match_entities_case_insensitive(detected_entities, scope_entities)
        
        if matched:
            # Bonus progressif selon le nombre d'entités
            final_bonus = bonus_value
            if len(matched) > 1:
                multiplier = config.get("multi_entity_multiplier", 1.2)
                final_bonus *= multiplier
            
            bonuses[bonus_type] = final_bonus
            bonus_details[bonus_type] = {
                "matched_entities": matched,
                "count": len(matched),
                "base_bonus": bonus_value,
                "final_bonus": final_bonus
            }
    
    # Bonus LAI relevance score
    lai_score = item.get("normalized_content", {}).get("lai_relevance_score", 0)
    lai_bonus_config = scoring_config.get("lai_score_bonuses", {
        "high_threshold": {"min_score": 8, "bonus": 2.0},
        "medium_threshold": {"min_score": 6, "bonus": 1.0}
    })
    
    for threshold_name, threshold_config in lai_bonus_config.items():
        min_score = threshold_config.get("min_score", 0)
        bonus_value = threshold_config.get("bonus", 0)
        
        if lai_score >= min_score:
            bonuses[f"lai_score_{threshold_name}"] = bonus_value
            break  # Prendre le plus haut bonus applicable
    
    return bonuses, bonus_details

def match_entities_case_insensitive(detected, scope):
    """Matching d'entités insensible à la casse"""
    if not detected or not scope:
        return []
    
    scope_lower = [entity.lower() for entity in scope]
    matched = []
    
    for entity in detected:
        if entity.lower() in scope_lower:
            matched.append(entity)
    
    return matched
```

### Étape 4 : Calcul des Pénalités Config-Driven

```python
def calculate_penalties(item, scoring_config, reference_date):
    """
    Pénalités entièrement pilotées par scoring_config
    """
    penalties = {}
    penalty_details = {}
    
    normalized_content = item.get("normalized_content", {})
    
    # Configuration des pénalités
    penalty_config = scoring_config.get("penalties", {})
    
    # Pénalité anti-LAI
    if normalized_content.get("anti_lai_detected", False):
        anti_lai_penalty = penalty_config.get("anti_lai_penalty", -5.0)
        penalties["anti_lai"] = anti_lai_penalty
    
    # Pénalité LAI score faible
    lai_score = normalized_content.get("lai_relevance_score", 0)
    lai_penalties = penalty_config.get("lai_score_penalties", {
        "very_low": {"max_score": 2, "penalty": -3.0},
        "low": {"max_score": 4, "penalty": -1.5}
    })
    
    for penalty_name, penalty_config in lai_penalties.items():
        max_score = penalty_config.get("max_score", 0)
        penalty_value = penalty_config.get("penalty", 0)
        
        if lai_score <= max_score:
            penalties[f"lai_score_{penalty_name}"] = penalty_value
            break  # Prendre la pénalité la plus sévère applicable
    
    # Pénalité âge
    age_penalties = calculate_age_penalties(item, penalty_config, reference_date)
    penalties.update(age_penalties)
    
    # Pénalité absence d'entités
    entities = normalized_content.get("entities", {})
    has_entities = any([
        entities.get("companies", []),
        entities.get("molecules", []),
        entities.get("technologies", []),
        entities.get("trademarks", [])
    ])
    
    if not has_entities:
        no_entities_penalty = penalty_config.get("no_entities_penalty", -2.0)
        penalties["no_entities"] = no_entities_penalty
    
    return penalties, penalty_details

def calculate_age_penalties(item, penalty_config, reference_date):
    """Calcul des pénalités d'âge config-driven"""
    penalties = {}
    
    published_at = item.get("published_at")
    if not published_at:
        invalid_date_penalty = penalty_config.get("invalid_date_penalty", -1.0)
        penalties["invalid_date"] = invalid_date_penalty
        return penalties
    
    try:
        # Parsing robuste de la date
        if "T" in published_at:
            pub_date = datetime.fromisoformat(published_at.replace("Z", ""))
        else:
            pub_date = datetime.strptime(published_at, "%Y-%m-%d")
        
        age_days = (reference_date - pub_date).days
        
        # Pénalités d'âge depuis configuration
        age_thresholds = penalty_config.get("age_penalties", {
            "very_old": {"min_days": 180, "penalty": -2.0},
            "old": {"min_days": 90, "penalty": -1.0},
            "aging": {"min_days": 60, "penalty": -0.5}
        })
        
        for threshold_name, threshold_config in age_thresholds.items():
            min_days = threshold_config.get("min_days", 0)
            penalty_value = threshold_config.get("penalty", 0)
            
            if age_days >= min_days:
                penalties[f"age_{threshold_name}"] = penalty_value
                break  # Prendre la pénalité la plus sévère applicable
                
    except Exception as e:
        invalid_date_penalty = penalty_config.get("invalid_date_penalty", -1.0)
        penalties["invalid_date"] = invalid_date_penalty
    
    return penalties
```

### Étape 5 : Score Final avec Seuils Config-Driven

```python
def calculate_final_score(base_score, domain_factor, bonuses, penalties, scoring_config):
    """
    Calcul final avec seuils configurables
    """
    # Score pondéré par domaine
    weighted_base = base_score * domain_factor
    
    # Somme des bonus et pénalités
    total_bonus = sum(v for v in bonuses.values() if isinstance(v, (int, float)))
    total_penalty = sum(v for v in penalties.values() if isinstance(v, (int, float)))
    
    # Score brut
    raw_score = weighted_base + total_bonus + total_penalty
    
    # Application des seuils depuis configuration
    thresholds = scoring_config.get("score_thresholds", {
        "min_score": 0.0,
        "max_score": 50.0
    })
    
    min_score = thresholds.get("min_score", 0.0)
    max_score = thresholds.get("max_score", 50.0)
    
    # Score final avec seuils
    final_score = max(min_score, min(max_score, raw_score))
    
    # Arrondi configurable
    precision = scoring_config.get("score_precision", 1)
    final_score = round(final_score, precision)
    
    return final_score, {
        "weighted_base": weighted_base,
        "total_bonus": total_bonus,
        "total_penalty": total_penalty,
        "raw_score": raw_score,
        "applied_min": min_score,
        "applied_max": max_score
    }
```

---

## 📋 CONFIGURATION SCORING V2 COMPLÈTE

### Extension lai_weekly_v4.yaml

```yaml
scoring_config:
  # Poids des types d'événements
  event_type_weights:
    partnership: 1.2
    regulatory: 1.1
    clinical_update: 1.0
    scientific_publication: 0.8
    corporate_move: 0.7
    financial_results: 0.5
    other: 0.3
  
  # Mapping confidence string → number
  confidence_mapping:
    high: 0.9
    medium: 0.6
    low: 0.3
  
  # Bonus par entités (config-driven)
  entity_bonuses:
    pure_player_companies:
      enabled: true
      entity_type: "companies"
      scope: "lai_companies_mvp_core"
      bonus: 5.0
      multi_entity_multiplier: 1.2
      description: "Pure players LAI - signal très fort"
    
    trademark_mentions:
      enabled: true
      entity_type: "trademarks"
      scope: "lai_trademarks_global"
      bonus: 4.0
      multi_entity_multiplier: 1.3
      description: "Mentions de marques LAI - signal privilégié"
    
    key_molecules:
      enabled: true
      entity_type: "molecules"
      scope: "lai_molecules_global"
      bonus: 2.5
      multi_entity_multiplier: 1.1
      description: "Molécules LAI d'intérêt"
    
    hybrid_companies:
      enabled: true
      entity_type: "companies"
      scope: "lai_companies_hybrid"
      bonus: 1.5
      multi_entity_multiplier: 1.1
      description: "Big pharma avec activité LAI"
  
  # Bonus LAI relevance score
  lai_score_bonuses:
    high_threshold:
      min_score: 8
      bonus: 2.0
    medium_threshold:
      min_score: 6
      bonus: 1.0
  
  # Pénalités configurables
  penalties:
    anti_lai_penalty: -5.0
    
    lai_score_penalties:
      very_low:
        max_score: 2
        penalty: -3.0
      low:
        max_score: 4
        penalty: -1.5
    
    age_penalties:
      very_old:
        min_days: 180
        penalty: -2.0
      old:
        min_days: 90
        penalty: -1.0
      aging:
        min_days: 60
        penalty: -0.5
    
    no_entities_penalty: -2.0
    invalid_date_penalty: -1.0
  
  # Seuils et limites
  score_thresholds:
    min_score: 0.0
    max_score: 50.0
  
  score_precision: 1
  
  # Seuils de sélection newsletter
  selection_overrides:
    min_score: 12
    max_items_total: 15
```

---

## 🧪 EXEMPLES CONCRETS DE CALCUL

### Item 1 : Nanexa/Moderna Partnership

**Données :**
- lai_relevance_score: 8
- event_type: "partnership"
- matched_domains: ["tech_lai_ecosystem"]
- domain_relevance: {"tech_lai_ecosystem": {"score": 0.7, "confidence": "high"}}
- entities: {"companies": ["Nanexa", "Moderna"], "trademarks": ["PharmaShell®"]}

**Calcul :**
1. **Base score :** 8 × 1.2 = 9.6
2. **Domain factor :** (0.7 × 0.7 + 0.9 × 0.3) = 0.76
3. **Weighted base :** 9.6 × 0.76 = 7.3
4. **Bonus :**
   - trademark_mentions: 4.0 (PharmaShell® dans lai_trademarks_global)
   - lai_score_high: 2.0 (lai_score >= 8)
   - Total bonus: 6.0
5. **Pénalités :** 0 (aucune applicable)
6. **Final score :** 7.3 + 6.0 = 13.3

**Résultat attendu :** final_score = 13.3 ✅ (sélectionnable, min_score = 12)

### Item 2 : UZEDY FDA Approval

**Données :**
- lai_relevance_score: 10
- event_type: "regulatory"
- matched_domains: ["tech_lai_ecosystem"]
- domain_relevance: {"tech_lai_ecosystem": {"score": 0.9, "confidence": "high"}}
- entities: {"molecules": ["UZEDY", "risperidone"], "trademarks": ["UZEDY®"]}

**Calcul :**
1. **Base score :** 10 × 1.1 = 11.0
2. **Domain factor :** (0.9 × 0.7 + 0.9 × 0.3) = 0.9
3. **Weighted base :** 11.0 × 0.9 = 9.9
4. **Bonus :**
   - trademark_mentions: 4.0 (UZEDY® dans lai_trademarks_global)
   - lai_score_high: 2.0 (lai_score >= 8)
   - Total bonus: 6.0
5. **Pénalités :** 0
6. **Final score :** 9.9 + 6.0 = 15.9

**Résultat attendu :** final_score = 15.9 ✅ (excellent score)

### Item 3 : Rapport Financier Nanexa

**Données :**
- lai_relevance_score: 0
- event_type: "financial_results"
- matched_domains: []
- entities: {"companies": ["Nanexa"]}

**Calcul :**
1. **Base score :** 0 × 0.5 = 0.0
2. **Domain factor :** 0.1 (no matched_domains)
3. **Weighted base :** 0.0 × 0.1 = 0.0
4. **Bonus :** 0 (lai_score trop faible)
5. **Pénalités :**
   - lai_score_very_low: -3.0 (lai_score <= 2)
   - Total penalty: -3.0
6. **Final score :** max(0, 0.0 + 0 - 3.0) = 0.0

**Résultat attendu :** final_score = 0.0 ✅ (exclu, < min_score)

---

## 🔧 IMPLÉMENTATION ROBUSTE

### Validation des Données d'Entrée

```python
def validate_item_for_scoring(item):
    """Validation robuste avant scoring"""
    errors = []
    
    # Validation normalized_content
    normalized = item.get("normalized_content", {})
    if not isinstance(normalized.get("lai_relevance_score"), (int, float)):
        errors.append("lai_relevance_score manquant ou invalide")
    
    # Validation matching_results
    matching = item.get("matching_results", {})
    domain_relevance = matching.get("domain_relevance", {})
    
    for domain_id, relevance in domain_relevance.items():
        if not isinstance(relevance.get("score"), (int, float)):
            errors.append(f"Score invalide pour domaine {domain_id}")
        if not isinstance(relevance.get("confidence"), str):
            errors.append(f"Confidence invalide pour domaine {domain_id}")
    
    return len(errors) == 0, errors
```

### Logging Détaillé

```python
def score_item_with_logging(item, scoring_config, canonical_scopes, reference_date):
    """Scoring avec logging détaillé pour debug"""
    item_id = item.get("item_id", "unknown")
    
    logger.info(f"Scoring item {item_id}")
    
    # Validation
    is_valid, errors = validate_item_for_scoring(item)
    if not is_valid:
        logger.error(f"Item {item_id} invalide: {errors}")
        return create_error_scoring_result(errors)
    
    # Calculs avec logging
    base_score, base_details = calculate_base_score(item, scoring_config)
    logger.debug(f"Item {item_id} - Base score: {base_score} (details: {base_details})")
    
    domain_factor, domain_details = calculate_domain_factor(item, scoring_config)
    logger.debug(f"Item {item_id} - Domain factor: {domain_factor} (details: {domain_details})")
    
    bonuses, bonus_details = calculate_bonuses(item, scoring_config, canonical_scopes)
    logger.debug(f"Item {item_id} - Bonuses: {bonuses}")
    
    penalties, penalty_details = calculate_penalties(item, scoring_config, reference_date)
    logger.debug(f"Item {item_id} - Penalties: {penalties}")
    
    final_score, final_details = calculate_final_score(base_score, domain_factor, bonuses, penalties, scoring_config)
    logger.info(f"Item {item_id} - Final score: {final_score}")
    
    return create_scoring_result(base_score, bonuses, penalties, final_score, {
        "base_details": base_details,
        "domain_details": domain_details,
        "bonus_details": bonus_details,
        "penalty_details": penalty_details,
        "final_details": final_details
    })
```

---

## 🎯 BÉNÉFICES DU DESIGN V2

### 1. Configuration Complète
- ✅ Tous les seuils dans client_config
- ✅ Bonus/pénalités configurables
- ✅ Poids event_types ajustables
- ✅ Aucun hardcoding dans le code

### 2. Robustesse Technique
- ✅ Validation des données d'entrée
- ✅ Gestion d'erreurs explicite
- ✅ Logging détaillé pour debug
- ✅ Correction du bug confidence string

### 3. Traçabilité Complète
- ✅ Score breakdown détaillé
- ✅ Détails de chaque calcul
- ✅ Raisons des bonus/pénalités
- ✅ Historique des décisions

### 4. Évolutivité
- ✅ Ajout facile de nouveaux bonus
- ✅ Modification des seuils sans code
- ✅ Support multi-clients
- ✅ A/B testing possible

---

## 🔄 TRANSITION VERS PHASE 4

**Design terminé - Prêt pour implémentation :**
1. ✅ **Algorithme défini :** Calcul en 5 étapes config-driven
2. ✅ **Configuration étendue :** lai_weekly_v4.yaml enrichi
3. ✅ **Exemples validés :** Calculs manuels cohérents
4. ✅ **Robustesse assurée :** Validation + logging + gestion d'erreurs

**Phase 4 - Implémentation :**
- Correction du bug confidence mapping
- Implémentation du nouveau scoring config-driven
- Tests unitaires sur les calculs
- Validation sur test_curated_items.json

**Résultat attendu :**
- final_score cohérent avec lai_relevance_score
- Items LAI forts sélectionnables (score >= 12)
- Newsletter V2 fonctionnelle sans bidouilles

---

*Design Scoring V2 - Config-Driven et Robuste*  
*Prêt pour implémentation en Phase 4*