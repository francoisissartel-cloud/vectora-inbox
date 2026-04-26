# Plan de Recentrage LAI – MVP lai_weekly
## Design pour Newsletter Strictement Centrée LAI

**Date** : 2025-12-08  
**Auteur** : Amazon Q Developer  
**Client** : lai_weekly (DEV)  
**Objectif** : Newsletter très centrée LAI, même si trop strict (préférer manquer des news plutôt qu'avoir du bruit)

---

## Résumé Exécutif

**Problème** : Newsletter actuelle contient 37.5% de faux positifs (Pfizer Hympavzi, AbbVie Skyrizi, etc.)

**Solution recommandée** : **Approche hybride** combinant :
1. Scope `lai_companies_mvp_core` (5 pure players LAI)
2. Matching avec ET logique pour `tech_lai_ecosystem`
3. Bonus scoring pour pure players LAI

**Impact attendu** : 80-90% des items retenus clairement LAI, pure players LAI ≥ 50% des items

---

## Options Évaluées

### Option A : Scope `lai_companies_mvp_core` Uniquement

**Description** : Remplacer `lai_companies_global` par `lai_companies_mvp_core` (5 pure players LAI) dans la config `lai_weekly`.

**Implémentation** :
```yaml
# canonical/scopes/company_scopes.yaml
lai_companies_mvp_core:
  - MedinCell
  - Camurus
  - DelSiTech
  - Nanexa
  - Peptron

# client-config-examples/lai_weekly.yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    company_scope: "lai_companies_mvp_core"  # ← Changement ici
    molecule_scope: "lai_molecules_global"
    technology_scope: "lai_keywords"
```

**Avantages** :
- ✅ Simple à implémenter (1 ligne de config)
- ✅ Élimine 100% des faux positifs big pharma
- ✅ Focus strict sur pure players LAI

**Inconvénients** :
- ❌ Perd les news LAI de big pharma (ex: Novo Nordisk semaglutide LAI, Pfizer cabotegravir LAI)
- ❌ Trop restrictif pour une veille sectorielle complète

**Verdict** : ⚠️ **Trop strict** pour le MVP (risque de manquer des signaux LAI importants)

---

### Option B : Matching avec ET Logique

**Description** : Pour `tech_lai_ecosystem`, exiger :
- **(company dans lai_companies_global OU molecule dans lai_molecules_global) ET**
- **au moins un mot-clé dans lai_keywords**

**Implémentation** :
```python
# src/vectora_core/matching/matcher.py

def match_items_to_domains(...):
    for domain in watch_domains:
        domain_type = domain.get('type')
        
        if domain_type == 'technology':
            # Pour les domaines technology, exiger un contexte technologique
            has_entity = companies_match or molecules_match
            has_technology = technologies_match
            
            if has_entity and has_technology:
                matched_domains.append(domain_id)
        else:
            # Pour les autres domaines, logique OU classique
            if companies_match or molecules_match or technologies_match:
                matched_domains.append(domain_id)
```

**Avantages** :
- ✅ Garantit un contexte LAI (technologie + entité)
- ✅ Élimine les faux positifs big pharma sans contexte LAI
- ✅ Conserve les news LAI de big pharma si contexte LAI

**Inconvénients** :
- ⚠️ Dépend de la qualité de la détection NLP des mots-clés LAI
- ⚠️ Risque de manquer des news LAI si NLP rate un mot-clé

**Verdict** : ✅ **Recommandé** (bon équilibre précision/rappel)

---

### Option C : Bonus/Malus dans le Scoring

**Description** : Ajouter des bonus/malus dans le scoring pour favoriser les pure players LAI.

**Implémentation** :
```yaml
# canonical/scoring/scoring_rules.yaml

other_factors:
  # Bonus pour les pure players LAI (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
  pure_player_lai_bonus: 5
  
  # Malus pour big pharma sans mot-clé LAI
  big_pharma_without_lai_keyword_malus: -3
  
  # Liste des pure players LAI
  pure_players_lai:
    - MedinCell
    - Camurus
    - DelSiTech
    - Nanexa
    - Peptron
```

```python
# src/vectora_core/scoring/scorer.py

def compute_score(item, scoring_rules, domain_priority):
    # ... (scoring actuel)
    
    # Bonus pure player LAI
    pure_players = scoring_rules.get('other_factors', {}).get('pure_players_lai', [])
    item_companies = item.get('companies_detected', [])
    
    if any(company in pure_players for company in item_companies):
        pure_player_bonus = scoring_rules.get('other_factors', {}).get('pure_player_lai_bonus', 0)
        final_score += pure_player_bonus
    
    # Malus big pharma sans mot-clé LAI
    has_lai_keyword = len(item.get('technologies_detected', [])) > 0
    if not has_lai_keyword and item_companies:
        malus = scoring_rules.get('other_factors', {}).get('big_pharma_without_lai_keyword_malus', 0)
        final_score += malus
    
    return round(final_score, 2)
```

**Avantages** :
- ✅ Favorise les pure players LAI
- ✅ Pénalise les faux positifs big pharma
- ✅ Conserve la flexibilité du matching

**Inconvénients** :
- ⚠️ Ne résout pas le problème à la racine (matching trop permissif)
- ⚠️ Complexifie le scoring

**Verdict** : ✅ **Complémentaire** (à combiner avec Option B)

---

## Solution Recommandée : Approche Hybride

### Combinaison Option A + B + C

**Stratégie** :
1. **Créer `lai_companies_mvp_core`** (5 pure players LAI) pour usage futur
2. **Implémenter matching avec ET logique** pour `tech_lai_ecosystem`
3. **Ajouter bonus scoring** pour pure players LAI

**Justification** :
- ✅ Garantit un contexte LAI (Option B)
- ✅ Favorise les pure players LAI (Option C)
- ✅ Conserve la flexibilité pour big pharma avec contexte LAI
- ✅ Permet de basculer vers Option A si besoin (scope déjà créé)

---

## Implémentation Détaillée

### 1. Créer Scope `lai_companies_mvp_core`

**Fichier** : `canonical/scopes/company_scopes.yaml`

```yaml
# Pure players LAI pour le MVP (focus strict)
lai_companies_mvp_core:
  - MedinCell
  - Camurus
  - DelSiTech
  - Nanexa
  - Peptron
```

**Justification** : Scope disponible pour usage futur ou basculement rapide si besoin.

---

### 2. Modifier Logique de Matching

**Fichier** : `src/vectora_core/matching/matcher.py`

**Changement** :
```python
def match_items_to_domains(...):
    for domain in watch_domains:
        domain_id = domain.get('id')
        domain_type = domain.get('type')
        
        # Calculer les intersections
        companies_match = compute_intersection(item_companies, scope_companies)
        molecules_match = compute_intersection(item_molecules, scope_molecules)
        technologies_match = compute_intersection(item_technologies, scope_technologies)
        indications_match = compute_intersection(item_indications, scope_indications)
        
        # Logique de matching selon le type de domaine
        if domain_type == 'technology':
            # Pour les domaines technology, exiger un contexte technologique
            has_entity = bool(companies_match or molecules_match)
            has_technology = bool(technologies_match)
            
            if has_entity and has_technology:
                matched_domains.append(domain_id)
                logger.debug(f"Item '{item.get('title', '')[:50]}...' matché au domaine {domain_id} (technology + entity)")
        else:
            # Pour les autres domaines (regulatory, indication), logique OU classique
            if companies_match or molecules_match or technologies_match or indications_match:
                matched_domains.append(domain_id)
                logger.debug(f"Item '{item.get('title', '')[:50]}...' matché au domaine {domain_id}")
        
        item['matched_domains'] = matched_domains
    
    return normalized_items
```

**Impact** :
- ✅ Élimine les faux positifs type "Pfizer Hympavzi" (Pfizer sans mot-clé LAI)
- ✅ Conserve les vrais LAI type "MedinCell UZEDY" (MedinCell + extended-release injectable)
- ✅ Conserve les news LAI de big pharma si contexte LAI (ex: Novo Nordisk + semaglutide + long-acting)

---

### 3. Ajouter Bonus Scoring pour Pure Players LAI

**Fichier** : `canonical/scoring/scoring_rules.yaml`

```yaml
other_factors:
  # ... (facteurs existants)
  
  # Bonus pour les pure players LAI (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
  pure_player_lai_bonus: 3
  
  # Liste des pure players LAI
  pure_players_lai:
    - MedinCell
    - Camurus
    - DelSiTech
    - Nanexa
    - Peptron
```

**Fichier** : `src/vectora_core/scoring/scorer.py`

```python
def compute_score(item, scoring_rules, domain_priority):
    # ... (scoring actuel)
    
    # Facteur 6 : Bonus pure player LAI
    pure_players = scoring_rules.get('other_factors', {}).get('pure_players_lai', [])
    item_companies = item.get('companies_detected', [])
    
    pure_player_bonus = 0
    if any(company in pure_players for company in item_companies):
        pure_player_bonus = scoring_rules.get('other_factors', {}).get('pure_player_lai_bonus', 0)
    
    # Formule de scoring (mise à jour)
    base_score = event_weight * priority_weight * recency_factor * source_weight
    final_score = base_score + signal_depth_bonus + pure_player_bonus
    
    return round(final_score, 2)
```

**Impact** :
- ✅ MedinCell, Camurus, DelSiTech, Nanexa, Peptron gagnent +3 points
- ✅ Favorise les pure players LAI dans le classement final

---

### 4. Nettoyer les Mots-Clés LAI (Faux Positifs)

**Fichier** : `canonical/scopes/technology_scopes.yaml`

**Problème** : Mots-clés trop génériques génèrent des faux positifs :
- `PAS` : détecte "passes" dans "target date passes"
- `DDS` : détecte "DDS" dans des contextes non-LAI

**Solution** : Retirer les mots-clés trop courts ou ambigus

```yaml
lai_keywords:
  # ... (mots-clés existants)
  
  # RETIRÉS (trop génériques) :
  # - PAS
  # - DDS
  
  # CONSERVÉS (spécifiques LAI) :
  - PASylation
  - drug delivery system
  - long-acting
  - extended-release
  - depot injection
  # ... etc.
```

**Impact** :
- ✅ Élimine les faux positifs type "PAS" dans "passes"
- ✅ Conserve les vrais mots-clés LAI

---

## Critères de Succès pour le MVP

Pour valider le recentrage LAI, la newsletter doit respecter :

| Critère | Objectif | Mesure |
|---------|----------|--------|
| **Précision LAI** | 80-90% des items retenus sont clairement LAI | Lecture humaine |
| **Représentation pure players** | Pure players LAI ≥ 50% des items | Comptage automatique |
| **Zéro faux positif big pharma** | Aucun item big pharma sans contexte LAI | Lecture humaine |
| **Couverture pure players** | 100% des news LAI de pure players capturées | Vérification manuelle |

---

## Plan de Test

### Test 1 : Re-run 7 jours avec Nouvelle Logique

**Payload** :
```json
{
  "client_id": "lai_weekly",
  "period_days": 7
}
```

**Validation** :
1. Vérifier que les items MedinCell UZEDY sont sélectionnés
2. Vérifier que les items Pfizer Hympavzi sont exclus
3. Vérifier que les items AbbVie Skyrizi sont exclus
4. Compter le % de pure players LAI dans la newsletter

---

### Test 2 : Analyse Avant/Après

**Métriques à comparer** :

| Métrique | Avant | Après | Objectif |
|----------|-------|-------|----------|
| Items matchés | 8 | ? | Stable ou légèrement inférieur |
| Vrai LAI | 3 (37.5%) | ? | ≥ 80% |
| Faux positifs | 3 (37.5%) | ? | 0% |
| Pure players LAI | 3 (37.5%) | ? | ≥ 50% |

---

## Rollback Plan

Si la nouvelle logique est trop stricte (< 3 items dans la newsletter) :

**Option 1** : Assouplir le matching
- Passer de ET logique à : (entity ET technology) OU (pure_player_lai)

**Option 2** : Basculer vers `lai_companies_mvp_core`
- Utiliser uniquement les 5 pure players LAI dans la config `lai_weekly`

**Option 3** : Ajuster les seuils de scoring
- Réduire `min_score` de 10 à 5 dans `scoring_rules.yaml`

---

## Documentation des Changements

### Fichiers Modifiés

1. `canonical/scopes/company_scopes.yaml` : Ajout de `lai_companies_mvp_core`
2. `canonical/scopes/technology_scopes.yaml` : Retrait de `PAS` et `DDS`
3. `canonical/scoring/scoring_rules.yaml` : Ajout de `pure_player_lai_bonus`
4. `src/vectora_core/matching/matcher.py` : Matching avec ET logique pour `technology`
5. `src/vectora_core/scoring/scorer.py` : Bonus pure player LAI

### Entrée CHANGELOG

```markdown
## [Unreleased] - 2025-12-08

### Added
- Scope `lai_companies_mvp_core` (5 pure players LAI) pour focus strict
- Bonus scoring `pure_player_lai_bonus` (+3 points) pour MedinCell, Camurus, DelSiTech, Nanexa, Peptron

### Changed
- Matching logic pour domaines `technology` : exige (entity ET technology) au lieu de (entity OU technology)
- Retrait des mots-clés LAI trop génériques (`PAS`, `DDS`) pour réduire les faux positifs

### Fixed
- Faux positifs big pharma (Pfizer Hympavzi, AbbVie Skyrizi) exclus de la newsletter LAI
- Newsletter lai_weekly désormais centrée à 80-90% sur LAI authentiques
```

---

## Prochaines Étapes

1. ✅ **Diagnostic sémantique** : Complété
2. ✅ **Plan de recentrage LAI** : Complété (ce document)
3. ⏳ **Implémentation** : Appliquer les changements (Phase 3)
4. ⏳ **Test & Validation** : Re-lancer un run 7 jours et valider les critères de succès (Phase 4)
5. ⏳ **Documentation résultats** : Créer `vectora_inbox_lai_mvp_focus_results.md`

---

**Auteur** : Amazon Q Developer  
**Date** : 2025-12-08  
**Version** : 1.0
