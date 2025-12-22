# Cadrage Scoring V2 et Plan de Rollback Newsletter

**Date :** 21 décembre 2025  
**Objectif :** Identifier et neutraliser les bidouilles côté newsletter pour centraliser le scoring dans normalize_score_v2  
**Statut :** Phase 0 - Cadrage critique  

---

## 🎯 PROBLÈME IDENTIFIÉ

**Symptôme critique :** Tous les items curated ont `scoring_results.final_score = 0.0` alors que :
- `lai_relevance_score` : 0-10 (signaux forts détectés)
- `matched_domains` : Correctement remplis pour les items pertinents
- `domain_relevance.score` : 0.6-0.9 (matching de qualité)

**Impact métier :** La Lambda newsletter ne peut pas sélectionner/trier les items par pertinence.

---

## 📋 ANALYSE DES BIDOUILLES NEWSLETTER IDENTIFIÉES

### Dans newsletter_v2_investigation_and_design_plan.md

**Bidouilles détectées :**

1. **Contournement du scoring dans selector.py (hypothétique)**
   ```python
   # BIDOUILLE : Utiliser lai_relevance_score au lieu de final_score
   effective_score = item.get('scoring_results', {}).get('final_score', 0)
   if effective_score == 0:
       # Fallback sur lai_relevance_score
       effective_score = item.get('normalized_content', {}).get('lai_relevance_score', 0)
   ```

2. **Affichage de "score effectif" dans assembler.py (hypothétique)**
   ```python
   # BIDOUILLE : Afficher le score de contournement
   display_score = calculate_effective_score(item)  # Pas le vrai final_score
   ```

3. **Logique de sélection dégradée**
   ```python
   # BIDOUILLE : Mode fallback pour matched_domains vides
   if not item['matching_results']['matched_domains']:
       # Utiliser lai_relevance_score + event_classification au lieu du scoring V2
       domain_match = (item['normalized_content']['lai_relevance_score'] >= 8)
   ```

### Évaluation des Bidouilles

**Ce qui constitue une "bidouille" :**
- ✅ **Fallback sur lai_relevance_score** : Contourne le système de scoring centralisé
- ✅ **Calcul de "score effectif"** : Logique de scoring distribuée (violation d'architecture)
- ✅ **Mode dégradé matching** : Compense les défaillances du pipeline normalize_score_v2

**Ce qui est légitime côté newsletter :**
- ✅ **Filtrage par seuil** : `final_score >= min_score` (normal)
- ✅ **Tri par final_score** : Utilisation standard du scoring
- ✅ **Sélection par section** : Basée sur matched_domains (normal)

---

## 🔄 PLAN DE ROLLBACK MINIMAL

### Principe Directeur

**La Lambda newsletter NE DOIT PAS porter la logique cœur de scoring.**

Toute logique qui :
- Calcule un score alternatif
- Compense les défaillances du scoring V2
- Réimplémente une partie du matching/scoring

→ **DOIT être supprimée ou neutralisée**

### Actions de Rollback

#### 1. Neutralisation des Fallbacks de Scoring

**Dans selector.py (si existant) :**
```python
# AVANT (bidouille)
effective_score = item.get('scoring_results', {}).get('final_score', 0)
if effective_score == 0:
    effective_score = item.get('normalized_content', {}).get('lai_relevance_score', 0)

# APRÈS (propre)
final_score = item.get('scoring_results', {}).get('final_score', 0)
# Pas de fallback - si final_score = 0, l'item est rejeté
```

#### 2. Suppression des "Scores Effectifs"

**Dans assembler.py (si existant) :**
```python
# AVANT (bidouille)
display_score = calculate_effective_score(item)

# APRÈS (propre)
display_score = item['scoring_results']['final_score']
# Affichage du vrai score calculé par normalize_score_v2
```

#### 3. Suppression du Mode Dégradé Matching

**Dans selector.py (si existant) :**
```python
# AVANT (bidouille)
if not item['matching_results']['matched_domains']:
    domain_match = (item['normalized_content']['lai_relevance_score'] >= 8)

# APRÈS (propre)
matched_domains = item['matching_results']['matched_domains']
# Si matched_domains est vide, l'item n'est pas sélectionné pour cette section
```

#### 4. Centralisation de la Logique de Sélection

**Principe :**
```python
# La newsletter utilise UNIQUEMENT les résultats du pipeline V2
def select_items_for_section(items, section_config):
    # 1. Filtrage par final_score (pas de fallback)
    filtered = [item for item in items 
                if item['scoring_results']['final_score'] >= section_config.get('min_score', 0)]
    
    # 2. Filtrage par matched_domains (pas de mode dégradé)
    section_domains = section_config.get('source_domains', [])
    matched = [item for item in filtered 
               if any(domain in item['matching_results']['matched_domains'] 
                     for domain in section_domains)]
    
    # 3. Tri par final_score (pas de score alternatif)
    return sorted(matched, key=lambda x: x['scoring_results']['final_score'], reverse=True)
```

---

## 📁 FICHIERS À MODIFIER (si existants)

### Structure Newsletter V2 Actuelle

**Vérification nécessaire :**
```
src_v2/vectora_core/newsletter/
├── __init__.py                 # run_newsletter_for_client()
├── selector.py                 # ← Vérifier les bidouilles de scoring
├── assembler.py                # ← Vérifier l'affichage des scores
└── editorial.py                # Appels Bedrock (probablement propre)
```

### Modifications Requises

#### src_v2/vectora_core/newsletter/selector.py
```python
# SUPPRIMER toute logique de calcul de score alternatif
# SUPPRIMER les fallbacks sur lai_relevance_score
# SUPPRIMER les modes dégradés de matching
# GARDER uniquement l'utilisation directe de final_score et matched_domains
```

#### src_v2/vectora_core/newsletter/assembler.py
```python
# SUPPRIMER calculate_effective_score() ou équivalent
# UTILISER directement item['scoring_results']['final_score']
# AFFICHER le score réel calculé par normalize_score_v2
```

---

## ⚠️ CONTRAINTES DE ROLLBACK

### Ce qui NE DOIT PAS être modifié

**Lambdas stables :**
- ❌ `vectora-inbox-ingest-v2` : Ne pas toucher
- ❌ `vectora-inbox-normalize-score-v2` : Ne pas modifier (sauf correction du scoring)

**Configuration :**
- ❌ `lai_weekly_v4.yaml` : Ne pas changer à ce stade
- ❌ `canonical/` : Ne pas modifier les scopes

### Ce qui PEUT être modifié

**Newsletter V2 uniquement :**
- ✅ `src_v2/vectora_core/newsletter/` : Rollback des bidouilles
- ✅ `src_v2/lambdas/newsletter/` : Handler propre

---

## 🎯 RÉSULTAT ATTENDU DU ROLLBACK

### Comportement Cible Post-Rollback

**Newsletter V2 doit :**
1. **Utiliser final_score uniquement** : Pas de fallback sur lai_relevance_score
2. **Respecter matched_domains** : Pas de mode dégradé
3. **Échouer proprement** : Si scoring V2 est cassé, newsletter échoue (pas de contournement)

**Conséquence attendue :**
- Newsletter V2 ne sélectionnera AUCUN item (final_score = 0 pour tous)
- Cela forcera la correction du scoring dans normalize_score_v2
- Architecture propre : chaque Lambda a sa responsabilité

### Métriques de Validation

**Post-rollback :**
- ✅ Aucun calcul de score dans newsletter V2
- ✅ Utilisation exclusive de `scoring_results.final_score`
- ✅ Pas de logique de matching dans newsletter V2
- ✅ Échec propre si scoring V2 défaillant

---

## 📋 CHECKLIST D'IMPLÉMENTATION

### Phase 0.1 : Audit des Bidouilles
- [ ] Vérifier l'existence de `src_v2/vectora_core/newsletter/`
- [ ] Identifier les fonctions de calcul de score alternatif
- [ ] Lister les fallbacks sur lai_relevance_score
- [ ] Documenter les modes dégradés de matching

### Phase 0.2 : Rollback Minimal
- [ ] Supprimer les calculs de score effectif
- [ ] Neutraliser les fallbacks de scoring
- [ ] Éliminer les modes dégradés de matching
- [ ] Centraliser sur final_score et matched_domains

### Phase 0.3 : Validation du Rollback
- [ ] Test local : Newsletter échoue proprement avec final_score = 0
- [ ] Vérification : Aucune logique de scoring dans newsletter
- [ ] Documentation : Rollback documenté et justifié

---

## 🔄 TRANSITION VERS PHASES SUIVANTES

**Une fois le rollback terminé :**
1. **Phase 1** : Cartographie du scoring V2 (pourquoi final_score = 0)
2. **Phase 2** : Diagnostic détaillé du bug
3. **Phase 3** : Design scoring V2 propre
4. **Phase 4** : Correction du scoring dans normalize_score_v2
5. **Phase 5** : Validation E2E sans bidouilles newsletter

**Principe :** Newsletter V2 ne sera fonctionnelle qu'après correction du scoring V2. C'est volontaire et sain architecturalement.

---

*Cadrage Scoring V2 et Rollback Newsletter - Version 1.0*  
*Objectif : Architecture propre avec responsabilités séparées*