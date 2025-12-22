# Diagnostic Détaillé - Bug "final_score = 0"

**Date :** 21 décembre 2025  
**Objectif :** Identifier la cause racine pourquoi tous les items ont final_score = 0.0  
**Statut :** Phase 2 - Diagnostic technique approfondi  

---

## 🎯 RÉSUMÉ DU PROBLÈME

**Symptôme critique :** Tous les 15 items curated ont `scoring_results.final_score = 0.0`

**Données disponibles :**
- ✅ Module scorer.py existe et semble complet
- ✅ scoring_config bien défini dans lai_weekly_v4.yaml
- ✅ Appel scorer.score_items() dans normalization/__init__.py
- ✅ Signaux LAI forts (lai_relevance_score 6-10, matched_domains remplis)

**Question :** Pourquoi le scoring ne fonctionne-t-il pas ?

---

## 📊 ANALYSE DES DONNÉES CURATED ACTUELLES

### Patterns Observés dans test_curated_items.json

**Groupe 1 : Items avec signaux LAI forts mais final_score = 0**
```json
// Nanexa/Moderna Partnership
{
  "lai_relevance_score": 8,
  "matched_domains": ["tech_lai_ecosystem"],
  "domain_relevance": {"tech_lai_ecosystem": {"score": 0.7}},
  "scoring_results": {
    "base_score": 0.0,        ← PROBLÈME
    "bonuses": {},            ← VIDE
    "penalties": {},          ← VIDE
    "final_score": 0.0        ← RÉSULTAT INCORRECT
  }
}

// UZEDY FDA Approval
{
  "lai_relevance_score": 10,
  "matched_domains": ["tech_lai_ecosystem"],
  "domain_relevance": {"tech_lai_ecosystem": {"score": 0.9}},
  "scoring_results": {
    "base_score": 0.0,        ← PROBLÈME
    "bonuses": {},            ← VIDE
    "penalties": {},          ← VIDE
    "final_score": 0.0        ← RÉSULTAT INCORRECT
  }
}
```

**Groupe 2 : Items avec pénalités calculées mais final_score = 0**
```json
// Item avec contenu faible
{
  "lai_relevance_score": 0,
  "matched_domains": [],
  "scoring_results": {
    "base_score": 3.0,        ← CALCULÉ
    "penalties": {            ← CALCULÉES
      "low_lai_score": -3.0,
      "low_relevance_event": -1.0
    },
    "final_score": 0,         ← ARRONDI À 0
    "score_breakdown": {      ← DÉTAILLÉ
      "raw_score": -3.85,
      "scoring_mode": "balanced"
    }
  }
}
```

### Observations Critiques

1. **Deux comportements différents :**
   - Items forts : Tout à 0.0 (pas de calcul)
   - Items faibles : Calcul détaillé mais final_score = 0

2. **Score breakdown présent uniquement pour items faibles**
   - Suggère que le scoring fonctionne partiellement

3. **Bonuses toujours vides pour items forts**
   - Malgré entities LAI pertinentes (PharmaShell®, UZEDY®, etc.)

---

## 🔍 HYPOTHÈSES TESTÉES

### Hypothèse 1 : Fonction de Scoring Non Appelée ❌

**Test :** Vérification des appels dans normalization/__init__.py

**Résultat :** ✅ Appel présent ligne 95
```python
scored_items = scorer.score_items(
    matched_items,
    client_config,
    canonical_scopes,
    scoring_mode,
    target_date
)
```

**Conclusion :** La fonction est bien appelée.

---

### Hypothèse 2 : Configuration scoring_config Manquante ❌

**Test :** Vérification lai_weekly_v4.yaml

**Résultat :** ✅ Configuration complète présente
```yaml
scoring_config:
  event_type_weight_overrides:
    partnership: 8
    regulatory: 7
  client_specific_bonuses:
    pure_player_companies:
      scope: "lai_companies_mvp_core"
      bonus: 5.0
    trademark_mentions:
      scope: "lai_trademarks_global"
      bonus: 4.0
```

**Conclusion :** La configuration est bien définie.

---

### Hypothèse 3 : Bug dans l'Algorithme de Scoring ⚠️

**Test :** Analyse de scorer.py

**Observations :**

1. **Calcul base_score :**
```python
def _get_event_type_score(event_type: str, scoring_config: Dict[str, Any]) -> float:
    default_weights = {
        "partnership": 8.0,
        "regulatory": 7.0,
        # ...
    }
    overrides = scoring_config.get("event_type_weight_overrides", {})
    return overrides.get(event_type, default_weights.get(event_type, 2.0))
```
✅ Logique correcte

2. **Calcul domain_relevance_factor :**
```python
def _get_domain_relevance_factor(item: Dict[str, Any]) -> float:
    matching_results = item.get("matching_results", {})
    domain_relevance = matching_results.get("domain_relevance", {})
    
    if not domain_relevance:
        return 0.05  # Score très faible si pas de matching
```
🚨 **PROBLÈME POTENTIEL IDENTIFIÉ**

3. **Structure domain_relevance dans les données :**
```json
"domain_relevance": {
  "tech_lai_ecosystem": {
    "score": 0.7,
    "confidence": "high"
  }
}
```

4. **Logique de calcul dans scorer.py :**
```python
for domain_id, relevance in domain_relevance.items():
    score = relevance.get("score", 0)
    confidence = relevance.get("confidence", 0)  ← PROBLÈME !
```

**🎯 CAUSE RACINE IDENTIFIÉE :**
`confidence` est une string ("high", "medium", "low") mais le code attend un nombre !

---

### Hypothèse 4 : Bug de Conversion confidence ✅

**Analyse détaillée :**

**Dans les données curated :**
```json
"domain_relevance": {
  "tech_lai_ecosystem": {
    "confidence": "high"  ← STRING
  }
}
```

**Dans scorer.py ligne ~200 :**
```python
confidence = relevance.get("confidence", 0)  # Récupère "high"
confidence_scores.append(confidence)         # Ajoute "high" à la liste
avg_confidence = sum(confidence_scores) / len(confidence_scores)  # CRASH !
```

**Erreur :** `sum()` ne peut pas additionner des strings !

**Impact :** Exception dans `_get_domain_relevance_factor()` → domain_relevance_factor = 0.05 → final_score très faible

---

### Hypothèse 5 : Gestion d'Exception Masquée ✅

**Dans scorer.py ligne ~50 :**
```python
try:
    scoring_results = _calculate_item_score(...)
except Exception as e:
    logger.error(f"Erreur scoring item {item.get('item_id', 'unknown')}: {str(e)}")
    # Ajout avec score par défaut
    item["scoring_results"] = _create_default_scoring_result()
```

**Comportement :**
1. Exception dans `_get_domain_relevance_factor()` à cause de confidence string
2. Exception catchée silencieusement
3. `_create_default_scoring_result()` retourne tout à 0.0
4. Item ajouté avec scoring_results vide

**🎯 CAUSE RACINE CONFIRMÉE :**
Bug de type de données + gestion d'exception masquée = final_score = 0.0

---

## 📋 STATISTIQUES SUR LES 15 ITEMS

### Distribution lai_relevance_score
- **Score 10 :** 3 items (UZEDY, Olanzapine, Delsitech conference)
- **Score 8-9 :** 3 items (Nanexa/Moderna, Medincell grant)
- **Score 6 :** 1 item (Nanexa interim report)
- **Score 0-2 :** 8 items (rapports financiers, corporate moves)

### Distribution matched_domains
- **Avec domains :** 8 items (53%) - tous tech_lai_ecosystem
- **Sans domains :** 7 items (47%) - items non LAI

### Distribution final_score (actuel)
- **Score 0.0 :** 15 items (100%) ← PROBLÈME

### Distribution final_score (attendu après correction)
- **Score >= 12 :** 6-8 items (items LAI forts)
- **Score 8-12 :** 2-3 items (items LAI moyens)
- **Score < 8 :** 4-6 items (items non LAI, exclus newsletter)

---

## 🔧 CAUSE RACINE FINALE

### Bug Principal : Conversion confidence String → Number

**Localisation :** `src_v2/vectora_core/normalization/scorer.py` ligne ~200

**Code défaillant :**
```python
def _get_domain_relevance_factor(item: Dict[str, Any]) -> float:
    # ...
    for domain_id, relevance in domain_relevance.items():
        score = relevance.get("score", 0)
        confidence = relevance.get("confidence", 0)  # ← BUG: récupère "high"
        
        relevance_scores.append(score)
        confidence_scores.append(confidence)         # ← BUG: ajoute string
    
    # ...
    avg_confidence = sum(confidence_scores) / len(confidence_scores)  # ← CRASH
```

**Données reçues :**
```json
"confidence": "high"  // String au lieu de number
```

**Exception générée :**
```
TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

**Conséquence :**
1. Exception dans `_calculate_item_score()`
2. Catch silencieux dans `score_items()`
3. Retour de `_create_default_scoring_result()` (tout à 0.0)
4. final_score = 0.0 pour tous les items avec matched_domains

### Bug Secondaire : Gestion d'Exception Trop Large

**Localisation :** `src_v2/vectora_core/normalization/scorer.py` ligne ~50

**Problème :** Exception catchée silencieusement sans diagnostic

**Impact :** Masque le bug principal, difficile à diagnostiquer

---

## 🎯 PLAN DE CORRECTION

### Correction 1 : Mapping confidence String → Number

**Dans `_get_domain_relevance_factor()` :**
```python
def _map_confidence_to_score(confidence_str: str) -> float:
    """Convertit confidence string en score numérique"""
    mapping = {
        "high": 0.9,
        "medium": 0.6,
        "low": 0.3
    }
    return mapping.get(confidence_str.lower(), 0.5)

# Dans la boucle :
confidence_str = relevance.get("confidence", "medium")
confidence = _map_confidence_to_score(confidence_str)
```

### Correction 2 : Amélioration Gestion d'Exception

**Dans `score_items()` :**
```python
try:
    scoring_results = _calculate_item_score(...)
except Exception as e:
    logger.error(f"Erreur scoring item {item.get('item_id', 'unknown')}: {str(e)}")
    logger.error(f"Données item: {item.get('matching_results', {})}")  # Debug
    # Retour score par défaut avec diagnostic
    item["scoring_results"] = _create_default_scoring_result()
    item["scoring_results"]["error"] = str(e)  # Traçabilité
```

### Correction 3 : Validation des Données d'Entrée

**Ajout de validation :**
```python
def _validate_matching_results(item: Dict[str, Any]) -> bool:
    """Valide la structure des matching_results"""
    matching_results = item.get("matching_results", {})
    domain_relevance = matching_results.get("domain_relevance", {})
    
    for domain_id, relevance in domain_relevance.items():
        if not isinstance(relevance.get("score"), (int, float)):
            logger.warning(f"Score invalide pour {domain_id}: {relevance.get('score')}")
            return False
        if not isinstance(relevance.get("confidence"), str):
            logger.warning(f"Confidence invalide pour {domain_id}: {relevance.get('confidence')}")
            return False
    
    return True
```

---

## 📊 VALIDATION POST-CORRECTION

### Test sur Items Représentatifs

**Item 1 - Nanexa/Moderna Partnership :**
- lai_relevance_score: 8
- event_type: "partnership" → base_score: 8.0
- domain_relevance: 0.7 → domain_factor: ~0.7
- entities: ["Nanexa", "Moderna", "PharmaShell®"]
- **final_score attendu :** ~14-16 (base 8 × 0.7 + bonus partnership + bonus trademark)

**Item 2 - UZEDY FDA Approval :**
- lai_relevance_score: 10
- event_type: "regulatory" → base_score: 7.0
- domain_relevance: 0.9 → domain_factor: ~0.9
- entities: ["UZEDY®", "risperidone"]
- **final_score attendu :** ~15-18 (base 7 × 0.9 + bonus regulatory + bonus trademark)

**Item 3 - Rapport financier Nanexa :**
- lai_relevance_score: 0
- event_type: "financial_results" → base_score: 3.0
- matched_domains: [] → domain_factor: 0.05
- **final_score attendu :** ~0-2 (base 3 × 0.05 + pénalités)

---

## 🔄 TRANSITION VERS PHASE 3

**Diagnostic terminé - Cause racine identifiée :**
1. ✅ **Bug principal :** Conversion confidence string → number
2. ✅ **Bug secondaire :** Gestion d'exception masquée
3. ✅ **Impact :** final_score = 0.0 pour tous les items avec matched_domains

**Prochaines étapes :**
- **Phase 3 :** Design scoring V2 propre et config-driven
- **Phase 4 :** Implémentation des corrections
- **Phase 5 :** Validation E2E sur lai_weekly_v4

**Corrections prioritaires :**
1. Mapping confidence string → number
2. Amélioration logging des erreurs
3. Validation des données d'entrée
4. Tests unitaires sur le scoring

---

*Diagnostic Bug Scoring V2 - Cause Racine Identifiée*  
*Prêt pour Phase 3 : Design de la correction*