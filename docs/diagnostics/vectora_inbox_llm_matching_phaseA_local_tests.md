# Phase A3 - Tests locaux

**Date** : 2025-12-12  
**Phase** : A3 - Tests locaux  
**Objectif** : Valider le comportement avec/sans LLM relevance  

---

## 🧪 Tests Exécutés

### Test automatisé : `test_llm_relevance_phase_a.py`

**Dataset de test** :
- 5 items avec différents profils de signaux LLM
- Sociétés LAI pure players : MedinCell, DelSiTech, Nanexa
- Molécules : risperidone, olanzapine
- Technologies : Extended-Release Injectable, Long-Acting Injectable, Depot Injection
- Event types : regulatory, partnership, clinical_update, financial_results, other

---

## 📊 Résultats des Tests

### Test 1: Scoring SANS LLM relevance (USE_LLM_RELEVANCE=false)

| Title | Score | Companies | Event Type |
|-------|-------|-----------|------------|
| MedinCell UZEDY approval | 37.54 | MedinCell | regulatory |
| Nanexa PharmaShell partnership | 32.95 | Nanexa, Moderna | partnership |
| DelSiTech clinical update | 28.35 | DelSiTech | clinical_update |
| Pfizer quarterly results | 14.67 | Pfizer | financial_results |
| Generic biotech news | 4.89 | - | other |

### Test 2: Scoring AVEC LLM relevance (USE_LLM_RELEVANCE=true)

| Title | Score | Companies | Event Type |
|-------|-------|-----------|------------|
| MedinCell UZEDY approval | 44.54 | MedinCell | regulatory |
| Nanexa PharmaShell partnership | 40.45 | Nanexa, Moderna | partnership |
| DelSiTech clinical update | 40.35 | DelSiTech | clinical_update |
| Pfizer quarterly results | 16.17 | Pfizer | financial_results |
| Generic biotech news | 4.89 | - | other |

---

## 🔍 Analyse des Résultats

### Impact LLM par item

| Title | Sans LLM | Avec LLM | Différence | Analyse |
|-------|----------|----------|------------|---------|
| Generic biotech news | 4.89 | 4.89 | +0.00 | ✅ Aucune entité → aucun bonus LLM |
| MedinCell UZEDY approval | 37.54 | 44.54 | +7.00 | ✅ Pure player + molécule + event_type |
| Nanexa PharmaShell partnership | 32.95 | 40.45 | +7.50 | ✅ Pure player + multiple companies + event_type |
| Pfizer quarterly results | 14.67 | 16.17 | +1.50 | ✅ Hybrid company + entity depth |
| DelSiTech clinical update | 28.35 | 40.35 | +12.00 | ✅ Pure player + molécule + technologies + event_type |

**Différence totale absolue** : 28.00 points

---

## ✅ Validation des Critères de Succès

### Critère 1: Scoring sans flag = comportement actuel inchangé
- ✅ **VALIDÉ** : Les scores sans `USE_LLM_RELEVANCE` sont identiques au comportement déterministe
- ✅ **Pas de régression** : Ordre de priorité préservé (regulatory > partnership > clinical_update)

### Critère 2: Scoring avec flag = intégration des signaux LLM
- ✅ **VALIDÉ** : Impact LLM détecté sur 4/5 items
- ✅ **Signaux exploités** :
  - Entity depth bonus (profondeur des entités)
  - Molecule bonus (molécules détectées)
  - Technology bonus (technologies détectées)
  - Pure player bonus (sociétés LAI)
  - Event classification bonus (event_type ≠ "other")

### Critère 3: Impact LLM mesurable et cohérent
- ✅ **VALIDÉ** : Différence totale de 28.00 points
- ✅ **Cohérence** : Plus de signaux LLM = plus de bonus
- ✅ **Logique métier** : DelSiTech (+12.00) > MedinCell (+7.00) car plus de technologies

---

## 🔧 Détail des Bonus LLM Appliqués

### Fonction `compute_score_with_llm_signals()`

#### 1. Entity Depth Bonus
```python
entity_depth = len(companies) + len(molecules) + len(technologies) + len(indications)
entity_bonus = min(entity_depth * 0.5, 3.0)  # Plafonné à +3.0
```

#### 2. Molecule Bonus
```python
molecule_bonus = len(molecules_detected) * 2.0  # 2.0 par molécule
```

#### 3. Technology Bonus
```python
tech_bonus = len(technologies_detected) * 2.0  # 2.0 par technologie
```

#### 4. Pure Player Bonus
```python
if companies_detected & lai_pure_players:
    pure_player_bonus = 3.0
```

#### 5. Event Classification Bonus
```python
if event_type != 'other':
    event_classification_bonus = 1.0
```

---

## 🎯 Validation Technique

### Feature Flag
- ✅ **Variable d'environnement** : `USE_LLM_RELEVANCE` correctement lue
- ✅ **Défaut sécurisé** : `false` par défaut
- ✅ **Isolation** : Aucun impact sur le code existant quand désactivé

### Logging
- ✅ **Traçabilité** : Logs `[LLM_RELEVANCE]` pour debugging
- ✅ **Détail** : Bonus individuels tracés
- ✅ **Résumé** : Score base + bonus LLM + final

### Performance
- ✅ **Pas de régression** : Même complexité algorithmique
- ✅ **Calculs additifs** : Bonus ajoutés au score de base existant

---

## 📋 Tests d'Intégration Validés

### 1. Compatibilité avec le scorer existant
- ✅ Fonction `score_items()` inchangée dans son interface
- ✅ Paramètres `scoring_rules`, `watch_domains`, `canonical_scopes` utilisés
- ✅ Structure de retour identique

### 2. Gestion des cas limites
- ✅ Items sans entités détectées : pas de bonus
- ✅ Sociétés non-LAI : pas de pure player bonus
- ✅ Event type "other" : pas de classification bonus

### 3. Configuration flexible
- ✅ Bonus configurables via `scoring_rules.yaml`
- ✅ Scopes LAI configurables via `canonical_scopes`
- ✅ Feature flag runtime sans redéploiement

---

## 🚀 Prêt pour Phase A4

### Critères Phase A3 ✅ VALIDÉS

- [x] **Tous les tests passent** : 5/5 items testés avec succès
- [x] **Comportement par défaut préservé** : Scores identiques sans flag
- [x] **Impact LLM mesurable et cohérent** : +28.00 points total
- [x] **Pas de régression** : Interface et performance préservées

### Actions Phase A4 - Déploiement AWS DEV

1. **Déployer les modifications** sur Lambda `engine` DEV
2. **Activer `USE_LLM_RELEVANCE=true`** pour `lai_weekly_v3` uniquement
3. **Lancer un run réel** complet
4. **Collecter métriques** avant/après
5. **Documenter l'impact** sur la sélection finale

**Condition pour passer à A4** : ✅ **Tests locaux validés et documentés**