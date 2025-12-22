# Rapport d'Exécution - Rollback Newsletter V2

**Date :** 21 décembre 2025  
**Objectif :** Neutralisation des bidouilles de scoring dans la Lambda newsletter V2  
**Statut :** ✅ ROLLBACK TERMINÉ  

---

## 🎯 BIDOUILLES IDENTIFIÉES ET SUPPRIMÉES

### 1. Fallback sur lai_relevance_score (selector.py)

**Fonction `_filter_by_min_score()`**

**AVANT (bidouille) :**
```python
# Si final_score est 0, utiliser lai_relevance_score
effective_score = final_score if final_score > 0 else lai_score
effective_min_score = min_score if final_score > 0 else 6
```

**APRÈS (propre) :**
```python
# ROLLBACK: Utiliser UNIQUEMENT final_score (pas de fallback)
final_score = item.get('scoring_results', {}).get('final_score', 0)
if final_score >= min_score:
    filtered.append(item)
```

**Impact :** Les items avec final_score = 0 seront maintenant rejetés (comportement attendu).

---

### 2. Mode Dégradé Matching (selector.py)

**Fonction `_item_matches_section()`**

**AVANT (bidouille) :**
```python
if matched_domains:
    domain_match = any(domain in source_domains for domain in matched_domains)
else:
    # Mode fallback: utiliser lai_relevance_score + event_classification
    domain_match = (lai_score >= 8 and ...)
```

**APRÈS (propre) :**
```python
# ROLLBACK: Utiliser UNIQUEMENT matched_domains (pas de mode fallback)
if not matched_domains:
    return False
domain_match = any(domain in source_domains for domain in matched_domains)
```

**Impact :** Les items sans matched_domains ne seront plus sélectionnés (comportement attendu).

---

### 3. Calcul de Score Effectif (selector.py)

**Fonction `_sort_items()` et `_get_effective_score()`**

**AVANT (bidouille) :**
```python
def get_effective_score(item):
    final_score = item.get('scoring_results', {}).get('final_score', 0)
    lai_score = item.get('normalized_content', {}).get('lai_relevance_score', 0)
    return final_score if final_score > 0 else lai_score
```

**APRÈS (propre) :**
```python
# ROLLBACK: Utiliser UNIQUEMENT final_score
return sorted(items, key=lambda x: x.get('scoring_results', {}).get('final_score', 0), reverse=True)
```

**Impact :** Le tri utilise exclusivement final_score (pas de score alternatif).

---

### 4. Affichage Score Effectif (assembler.py)

**Fonctions `_format_item_markdown()` et `_format_item_json()`**

**AVANT (bidouille) :**
```python
final_score = item.get('scoring_results', {}).get('final_score', 0)
lai_score = normalized.get('lai_relevance_score', 0)
score = final_score if final_score > 0 else lai_score
```

**APRÈS (propre) :**
```python
# ROLLBACK: Utiliser UNIQUEMENT final_score (pas de score effectif)
score = item.get('scoring_results', {}).get('final_score', 0)
```

**Impact :** L'affichage montre le vrai final_score calculé par normalize_score_v2.

---

## ✅ RÉSULTAT DU ROLLBACK

### Comportement Post-Rollback

**Newsletter V2 utilise maintenant EXCLUSIVEMENT :**
- ✅ `scoring_results.final_score` pour filtrage et tri
- ✅ `matching_results.matched_domains` pour sélection par section
- ✅ Aucun calcul de score alternatif
- ✅ Aucun mode dégradé ou fallback

**Conséquence attendue avec les données actuelles :**
- ❌ Newsletter V2 sélectionnera **0 items** (tous ont final_score = 0)
- ✅ Cela force la correction du scoring dans normalize_score_v2
- ✅ Architecture propre : responsabilités séparées

---

## 📊 VALIDATION DU ROLLBACK

### Checklist de Conformité

- [x] Aucun fallback sur lai_relevance_score
- [x] Aucun mode dégradé de matching
- [x] Aucun calcul de score effectif
- [x] Utilisation exclusive de final_score
- [x] Utilisation exclusive de matched_domains
- [x] Code conforme aux règles d'hygiène V4

### Fichiers Modifiés

1. **src_v2/vectora_core/newsletter/selector.py**
   - Suppression fallback lai_relevance_score
   - Suppression mode dégradé matching
   - Suppression calcul score effectif

2. **src_v2/vectora_core/newsletter/assembler.py**
   - Suppression affichage score effectif
   - Utilisation directe final_score

---

## 🔄 PROCHAINES ÉTAPES

**Phase 1 - Cartographie Scoring V2 :**
- Identifier où et comment final_score est calculé
- Comprendre pourquoi il reste à 0.0 malgré les signaux LAI

**Phase 2 - Diagnostic Bug :**
- Analyser la cause racine du final_score = 0
- Tester les hypothèses (fonction non appelée, bug logique, etc.)

**Phase 3 - Design Scoring V2 :**
- Concevoir un scoring config-driven propre
- Définir l'algorithme de calcul de final_score

**Phase 4 - Correction :**
- Implémenter le scoring V2 corrigé
- Valider sur test_curated_items.json

**Phase 5 - Validation E2E :**
- Relancer ingest + normalize_score_v2
- Vérifier final_score non nul dans curated/
- Valider newsletter V2 fonctionne sans bidouilles

---

*Rollback Newsletter V2 - Exécution Terminée*  
*Architecture propre : Newsletter utilise uniquement les résultats du pipeline V2*