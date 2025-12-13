# Vectora Inbox — LAI Runtime Matching Root Cause Analysis

**Date:** 2025-12-09  
**Auteur:** Amazon Q Developer  
**Statut:** 🔴 CRITICAL - Précision LAI à 0% après refactor canonical + adaptation runtime  
**Objectif:** Identifier les root causes et proposer un plan d'action priorisé

---

## 1. Contexte & Objectif

Le MVP LAI (Long-Acting Injectables) pour Vectora Inbox a pour objectif de fournir une veille sectorielle précise sur l'écosystème LAI avec les critères suivants :
- **Précision LAI ≥ 80%** : Au moins 80% des items sélectionnés doivent être des vrais LAI
- **Pure players ≥ 50%** : Au moins 50% des items doivent concerner des pure players LAI
- **0 faux positifs manifestes** : Aucun item manifestement non-LAI ne doit être sélectionné

Après le refactor canonical complet (restructuration des scopes en 7 catégories + séparation pure_players/hybrid) et l'adaptation du runtime (technology profiles + matching avancé), **la précision LAI reste à 0%** et aucun pure player n'est sélectionné.

---

## 2. Résumé des Symptômes Actuels

### Métriques du Dernier Run (lai_weekly - 09/12/2025)

| Métrique | Résultat | Objectif | Status |
|----------|----------|----------|--------|
| Items analyzed | 50 | - | ✅ |
| Items matched | 6 (12%) | - | 🟡 |
| Items selected | 5 | 5-10 | ✅ |
| **LAI precision** | **0%** | **≥80%** | ❌ |
| **Pure player %** | **0%** | **≥50%** | ❌ |
| **False positives** | **2/5 (40%)** | **0** | ❌ |

### Exemples d'Items Sélectionnés (Faux Positifs)

**❌ Item 1: Agios FDA Regulatory Tracker**
- Company: Agios (oncology company, NOT LAI)
- Technology: None detected
- **Problème:** Agios développe des thérapies oncologiques orales, pas des LAI

**❌ Item 2: WuXi AppTec Pentagon Security**
- Company: WuXi AppTec (CDMO chinois, NOT pure LAI)
- Technology: None detected  
- **Problème:** WuXi AppTec est un CDMO généraliste, pas spécialisé LAI

Ces exemples montrent que le système sélectionne des actualités pharma génériques sans vérifier la pertinence LAI.

---

## 3. Analyse Technique Détaillée

### 3.1. Chargement des Scopes (technology_scopes / company_scopes)

**État Actuel:**
- `technology_scopes.yaml` contient bien la structure hiérarchique à 7 catégories avec `_metadata.profile: technology_complex`
- `company_scopes.yaml` contient bien la séparation `lai_companies_pure_players` (14) vs `lai_companies_hybrid` (27)

**Questions Critiques:**

**Q1: Est-ce que lai_keywords est vu comme une structure hiérarchique avec 7 catégories ou comme une liste plate de strings ?**

**Analyse du code `loader.py`:**
```python
def load_canonical_scopes(config_bucket: str) -> Dict[str, Dict[str, Any]]:
    # ...
    scopes[scope_type] = s3_client.read_yaml_from_s3(config_bucket, key)
```

**PROBLÈME IDENTIFIÉ:** Le loader charge les scopes YAML tels quels, mais ne fait aucune validation de structure. Si `lai_keywords` est chargé comme dict avec 7 catégories, c'est correct. Mais le code ne vérifie pas si cette structure est préservée.

**Q2: Est-ce que generic_terms et negative_terms sont utilisés quelque part dans le code ?**

**Analyse du code `matcher.py`:**
```python
def _categorize_technology_keywords(technologies_match, technology_scope_key, canonical_scopes):
    # Parcourir chaque catégorie du scope
    for category_name, keywords in scope_data.items():
        if category_name == '_metadata':
            continue
        # ...
```

**PROBLÈME IDENTIFIÉ:** Le code parcourt bien toutes les catégories, MAIS il ne fait aucune distinction entre les catégories. `generic_terms` et `negative_terms` sont traités exactement comme `core_phrases`. Il n'y a aucune logique spéciale pour exclure ou filtrer ces catégories.

**Q3: Comment sont utilisés lai_companies_pure_players et lai_companies_hybrid ?**

**Analyse du code `matcher.py`:**
```python
def _identify_company_scope_type(companies_match, company_scope_modifiers, canonical_scopes):
    pure_player_scopes = company_scope_modifiers.get('pure_player_scopes', [])
    hybrid_scopes = company_scope_modifiers.get('hybrid_scopes', [])
```

**PROBLÈME IDENTIFIÉ:** Cette fonction existe et fonctionne correctement, MAIS elle n'est appelée que si le technology profile est activé. Si le profile matching ne fonctionne pas, cette distinction n'est jamais utilisée.

### 3.2. Interprétation des domain_matching_rules

**État Actuel:**
- `domain_matching_rules.yaml` contient bien le profile `technology_complex` avec les règles avancées
- Le profile définit `high_precision_signals`, `supporting_signals`, `company_scope_modifiers`, etc.

**Questions Critiques:**

**Q1: Quel est exactement le profile utilisé pour tech_lai_ecosystem ?**

**Analyse du code `matcher.py`:**
```python
def _get_technology_profile(technology_scope_key, canonical_scopes):
    tech_scopes = canonical_scopes.get('technologies', {})
    scope_data = tech_scopes.get(technology_scope_key, {})
    if isinstance(scope_data, dict):
        metadata = scope_data.get('_metadata', {})
        return metadata.get('profile')
    return None
```

**PROBLÈME POTENTIEL:** Cette fonction devrait retourner `technology_complex` pour `lai_keywords`, mais si `scope_data` n'est pas un dict ou si `_metadata` est manquant, elle retourne `None`.

**Q2: Pour tech_lai_ecosystem, est-ce que le moteur applique bien une logique avancée ou est-ce qu'il se comporte encore comme un simple "keyword present / not present" ?**

**Analyse du flow:**
1. `_evaluate_domain_match()` vérifie si c'est un technology domain avec profile
2. Si oui, appelle `_evaluate_technology_profile_match()`
3. Si non, fallback sur `_evaluate_matching_rule()` (logique classique)

**PROBLÈME CRITIQUE:** Si `_get_technology_profile()` retourne `None`, le système utilise TOUJOURS la logique classique, ignorant complètement les 7 catégories et les règles avancées.

### 3.3. Logique de matcher.py

**Flow Exact pour un Item:**

1. **Extraction des entités:** `companies_detected`, `molecules_detected`, `technologies_detected`
2. **Construction des ensembles de référence:** Intersection avec les scopes canonical
3. **Évaluation du matching:** Appel à `_evaluate_domain_match()`
4. **Décision finale:** Match ou pas + `matching_details`

**Questions Critiques:**

**Q1: Le profile technology_complex est-il jamais utilisé pour LAI dans la version actuelle ?**

**DIAGNOSTIC:** Pour répondre à cette question, il faut vérifier :
- Si `_get_technology_profile('lai_keywords', canonical_scopes)` retourne `'technology_complex'`
- Si `_evaluate_technology_profile_match()` est appelée
- Si `matching_details` est généré avec `rule_applied: 'technology_complex'`

**HYPOTHÈSE PRINCIPALE:** Le profile n'est jamais activé à cause d'un problème dans `_get_technology_profile()`.

**Q2: Si non, pourquoi (erreur de config, bug de code, champ non peuplé, etc.) ?**

**Causes Possibles:**
1. **Structure YAML mal chargée:** `lai_keywords` chargé comme liste au lieu de dict
2. **Clé manquante:** `_metadata` ou `profile` manquant dans le scope chargé
3. **Type checking défaillant:** `isinstance(scope_data, dict)` échoue
4. **Scope key incorrect:** `technology_scope_key` ne correspond pas à `'lai_keywords'`

### 3.4. Logique de scoring / signal quality

**État Actuel:**
- `scorer.py` contient bien les nouvelles fonctions `_compute_signal_quality_score()` et `_compute_company_scope_bonus()`
- Les règles de scoring incluent les nouveaux paramètres (confidence multipliers, signal quality weights, etc.)

**Questions Critiques:**

**Q1: Un item pure player avec bon signal texte serait-il favorisé ?**

**Analyse du code:**
```python
def _compute_company_scope_bonus(item, canonical_scopes, other_factors, matching_details):
    scopes_hit = matching_details.get('scopes_hit', {})
    company_scope_type = scopes_hit.get('company_scope_type', 'other')
    
    if company_scope_type == 'pure_player':
        return other_factors.get('pure_player_bonus', 3)
```

**PROBLÈME IDENTIFIÉ:** Cette logique fonctionne correctement, MAIS elle dépend de `matching_details` qui n'est généré que si le profile matching est activé. Si le profile matching ne fonctionne pas, `matching_details` est `None` et le bonus pure player n'est jamais appliqué.

**Q2: Ou si tout le monde est traité quasiment pareil pour le moment ?**

**DIAGNOSTIC:** Si le profile matching ne fonctionne pas, tous les items sont traités avec la logique classique et le scoring classique, sans distinction pure_player/hybrid.

---

## 4. Root Causes Probables (Numérotées)

### RC1 – Profile technology_complex jamais activé

**Symptôme:** Précision LAI à 0%, aucune distinction entre catégories de keywords
**Preuve:** Absence probable de `matching_details` avec `rule_applied: 'technology_complex'` dans les logs
**Impact:** Le système utilise la logique classique (keyword présent/absent) au lieu de la logique avancée par catégories

**Cause Racine Probable:**
- `_get_technology_profile('lai_keywords', canonical_scopes)` retourne `None`
- Soit `lai_keywords` n'est pas chargé comme dict avec `_metadata`
- Soit la clé `profile` est manquante dans `_metadata`

### RC2 – generic_terms et negative_terms non filtrés

**Symptôme:** Faux positifs sur des termes génériques (PEG, liposomes, subcutaneous)
**Preuve:** Items matchés sur des termes qui devraient être exclus ou nécessiter des signaux additionnels
**Impact:** Matching sur des signaux faibles qui déclenchent des faux positifs

**Cause Racine:**
- `_categorize_technology_keywords()` traite toutes les catégories de la même manière
- Aucune logique spéciale pour `generic_terms` (ne devraient pas matcher seuls)
- Aucune logique spéciale pour `negative_terms` (devraient rejeter le match)

### RC3 – Fallback sur règle classique systématique

**Symptôme:** Comportement identique à avant le refactor, pas d'amélioration de précision
**Preuve:** Logique de matching binaire (présent/absent) au lieu de combinaison de signaux
**Impact:** Tous les bénéfices du refactor canonical sont perdus

**Cause Racine:**
- Si RC1 est confirmé, `_evaluate_domain_match()` utilise toujours le fallback
- La règle classique `technology` dans `domain_matching_rules.yaml` est trop permissive
- `match_mode: all_required` avec `technology: required` + `entity: required` matche trop facilement

### RC4 – Distinction pure_player/hybrid non exploitée

**Symptôme:** 0% de pure players sélectionnés, pas de bonus de scoring différencié
**Preuve:** Tous les items ont le même type de scoring, pas de `company_scope_type` dans les résultats
**Impact:** Pas de priorisation des pure players LAI

**Cause Racine:**
- Dépend de RC1 : si le profile matching ne fonctionne pas, `matching_details` n'est pas généré
- Sans `matching_details`, `_compute_company_scope_bonus()` utilise le fallback (ancien système)
- Le fallback vérifie seulement `pure_player_scope: "lai_companies_mvp_core"` (5 entreprises) au lieu des 14 pure players

---

## 5. Recommandations de Corrections (P0 / P1 / P2)

### P0 (Bloquant) - Corrections Critiques

#### P0.1 - Diagnostiquer et corriger l'activation du profile technology_complex

**Description Métier:** Vérifier pourquoi le profile avancé n'est jamais utilisé et corriger le problème
**Description Technique:** Ajouter des logs dans `_get_technology_profile()` et `_evaluate_technology_profile_match()` pour tracer l'exécution

**Fichiers Impactés:**
- `src/vectora_core/matching/matcher.py` (ajout de logs)
- Potentiellement `src/vectora_core/config/loader.py` si problème de chargement

**Actions:**
1. Ajouter des logs debug dans `_get_technology_profile()` :
   ```python
   logger.debug(f"Technology scope key: {technology_scope_key}")
   logger.debug(f"Scope data type: {type(scope_data)}")
   logger.debug(f"Metadata: {scope_data.get('_metadata', 'MISSING')}")
   logger.debug(f"Profile: {metadata.get('profile', 'MISSING')}")
   ```

2. Ajouter des logs debug dans `_evaluate_domain_match()` :
   ```python
   logger.debug(f"Domain type: {domain_type}, Technology scope: {technology_scope_key}")
   logger.debug(f"Profile name: {profile_name}")
   ```

3. Redéployer et analyser les logs CloudWatch

**Risques:** Aucun (ajout de logs seulement)
**Comment Tester:** Exécuter lai_weekly et vérifier les logs pour voir si le profile est détecté

#### P0.2 - Implémenter la logique de filtrage pour generic_terms et negative_terms

**Description Métier:** S'assurer que les termes génériques ne matchent pas seuls et que les termes négatifs rejettent le match
**Description Technique:** Modifier `_evaluate_technology_profile_match()` pour implémenter la logique de filtrage

**Fichiers Impactés:**
- `src/vectora_core/matching/matcher.py`

**Actions:**
1. Modifier la logique de comptage des signaux pour exclure `generic_terms` :
   ```python
   # Exclure generic_terms du comptage high_precision et supporting
   excluded_cats = profile.get('signal_requirements', {}).get('excluded_categories', [])
   for cat in excluded_cats:
       if cat in category_matches:
           logger.debug(f"Excluding {cat} from signal counting: {category_matches[cat]}")
           # Ne pas compter ces signaux
   ```

2. Améliorer la logique de negative_terms pour rejeter immédiatement :
   ```python
   if negative_detected:
       logger.debug(f"Match rejected due to negative terms: {negative_detected}")
       return False, {..., 'match_confidence': 'rejected'}
   ```

**Risques:** Peut réduire le recall (vrais positifs rejetés)
**Comment Tester:** Vérifier que les items avec "oral tablet" ou "PEG" seul sont rejetés

#### P0.3 - Corriger la règle de fallback classique

**Description Métier:** Rendre la règle classique plus restrictive pour éviter les faux positifs quand le profile ne fonctionne pas
**Description Technique:** Modifier `domain_matching_rules.yaml` pour durcir la règle `technology`

**Fichiers Impactés:**
- `canonical/matching/domain_matching_rules.yaml`

**Actions:**
1. Modifier la règle `technology` pour exiger plus de signaux :
   ```yaml
   technology:
     match_mode: all_required
     dimensions:
       technology:
         requirement: required
         min_matches: 2  # Au lieu de 1
       entity:
         requirement: required
         min_matches: 1
   ```

**Risques:** Peut réduire le recall si le profile matching ne fonctionne toujours pas
**Comment Tester:** Vérifier que moins de faux positifs sont générés avec la règle classique

### P1 (Important) - Améliorations de Robustesse

#### P1.1 - Enrichir les logs de matching pour diagnostic

**Description Métier:** Améliorer la visibilité sur les décisions de matching pour faciliter le debug
**Description Technique:** Ajouter des logs détaillés dans toutes les fonctions de matching

**Fichiers Impactés:**
- `src/vectora_core/matching/matcher.py`

**Actions:**
1. Logger les intersections calculées
2. Logger les catégories matchées
3. Logger les décisions de scoring
4. Logger le company_scope_type identifié

**Risques:** Augmentation du volume de logs
**Comment Tester:** Analyser les logs pour comprendre pourquoi certains items matchent

#### P1.2 - Valider la structure des scopes après chargement

**Description Métier:** S'assurer que les scopes canonical sont chargés avec la bonne structure
**Description Technique:** Ajouter une validation dans `loader.py`

**Fichiers Impactés:**
- `src/vectora_core/config/loader.py`

**Actions:**
1. Valider que `lai_keywords` est un dict avec `_metadata`
2. Valider que les 7 catégories sont présentes
3. Logger des warnings si la structure est incorrecte

**Risques:** Aucun (validation seulement)
**Comment Tester:** Vérifier les logs de validation au démarrage

#### P1.3 - Corriger le fallback de company bonus

**Description Métier:** S'assurer que le bonus pure player fonctionne même si le profile matching échoue
**Description Technique:** Améliorer `_compute_company_scope_bonus()` pour utiliser les nouveaux scopes

**Fichiers Impactés:**
- `src/vectora_core/scoring/scorer.py`
- `canonical/scoring/scoring_rules.yaml`

**Actions:**
1. Modifier le fallback pour vérifier `lai_companies_pure_players` au lieu de `lai_companies_mvp_core`
2. Ajouter un paramètre `pure_player_scope_fallback: "lai_companies_pure_players"`

**Risques:** Aucun (amélioration du fallback)
**Comment Tester:** Vérifier que MedinCell, Camurus, etc. reçoivent le bonus même sans profile matching

### P2 (Confort / Futur) - Tests et Tooling

#### P2.1 - Créer des tests unitaires pour profile matching

**Description Métier:** Valider le comportement du profile matching en isolation
**Description Technique:** Créer des tests avec des données mockées

**Fichiers Impactés:**
- `tests/test_matcher_profiles.py` (nouveau)

**Actions:**
1. Tester `_get_technology_profile()` avec différentes structures de scopes
2. Tester `_evaluate_technology_profile_match()` avec différents signaux
3. Tester `_categorize_technology_keywords()` avec les 7 catégories

**Risques:** Aucun
**Comment Tester:** Exécuter les tests unitaires

#### P2.2 - Créer un outil de diagnostic des scopes

**Description Métier:** Faciliter le debug des problèmes de scopes et de matching
**Description Technique:** Script Python pour analyser les scopes chargés

**Fichiers Impactés:**
- `tools/diagnose_scopes.py` (nouveau)

**Actions:**
1. Charger les scopes depuis S3
2. Valider leur structure
3. Tester le matching sur des exemples connus
4. Générer un rapport de diagnostic

**Risques:** Aucun
**Comment Tester:** Exécuter l'outil sur les scopes actuels

---

## 6. Plan de Test Après Corrections

### Phase 1: Validation Technique (P0.1)

**Objectif:** Confirmer que le profile technology_complex est activé

**Actions:**
1. Déployer les logs de diagnostic
2. Exécuter lai_weekly
3. Analyser les logs CloudWatch pour vérifier :
   - `_get_technology_profile('lai_keywords')` retourne `'technology_complex'`
   - `_evaluate_technology_profile_match()` est appelée
   - `matching_details` contient `rule_applied: 'technology_complex'`

**Critères de Succès:**
- Profile détecté dans les logs
- `matching_details` généré pour au moins 1 item
- Pas de fallback sur règle classique pour les items LAI

### Phase 2: Validation Fonctionnelle (P0.2 + P0.3)

**Objectif:** Confirmer que les corrections améliorent la précision LAI

**Actions:**
1. Déployer les corrections de filtrage
2. Exécuter lai_weekly
3. Analyser la nouvelle newsletter générée
4. Calculer les nouvelles métriques

**Critères de Succès:**
- Précision LAI > 0% (minimum 20% pour valider l'amélioration)
- Réduction des faux positifs (< 2/5 items)
- Au moins 1 pure player sélectionné

### Phase 3: Validation Complète (P1 + P2)

**Objectif:** Atteindre les objectifs MVP LAI

**Actions:**
1. Déployer toutes les améliorations
2. Exécuter lai_weekly plusieurs fois
3. Analyser la stabilité des résultats
4. Mesurer les KPIs finaux

**Critères de Succès MVP LAI:**
- **Précision LAI ≥ 80%**
- **Pure players ≥ 50%**
- **0 faux positifs manifestes**

### Types de Cas à Tester

**Pure Players avec Signaux Forts:**
- "MedinCell announces long-acting injectable partnership" → Doit matcher (haute confiance)
- "Camurus reports FluidCrystal depot results" → Doit matcher (haute confiance)

**Hybrid avec Signaux Multiples:**
- "Pfizer develops PLGA microspheres for once-monthly injection" → Doit matcher (confiance moyenne)
- "AbbVie announces subcutaneous injection" → Ne doit PAS matcher (signal insuffisant)

**Non-LAI à Rejeter:**
- "Agios reports oral tablet results" → Ne doit PAS matcher (negative term)
- "WuXi AppTec manufacturing services" → Ne doit PAS matcher (pas de signal LAI)

**KPIs à Suivre:**
- Précision LAI (% vrais positifs)
- Recall LAI (% vrais positifs détectés)
- % Pure players dans les résultats
- Nombre de faux positifs manifestes

---

## 7. Résumé des Root Causes Principales

### RC1 - Profile technology_complex jamais activé (CRITIQUE)
Le système n'utilise jamais la logique avancée par catégories, tombant systématiquement sur la règle classique binaire.

### RC2 - generic_terms et negative_terms non filtrés (CRITIQUE)  
Les termes génériques (PEG, liposomes) et négatifs (oral tablet) ne sont pas traités spécialement, causant des faux positifs.

### RC3 - Distinction pure_player/hybrid non exploitée (IMPORTANT)
Sans profile matching, la différenciation entre pure players et hybrid n'est jamais appliquée, perdant un avantage clé du refactor.

---

## 8. Corrections P0 Recommandées

### P0.1 - Diagnostiquer l'activation du profile (2h)
Ajouter des logs pour comprendre pourquoi `technology_complex` n'est jamais utilisé.

### P0.2 - Implémenter le filtrage des catégories (3h)  
Corriger la logique pour que `generic_terms` ne matchent pas seuls et `negative_terms` rejettent le match.

### P0.3 - Durcir la règle de fallback (1h)
Rendre la règle classique plus restrictive pour limiter les faux positifs en attendant que le profile fonctionne.

**Durée Totale Estimée:** 6 heures pour passer de 0% à >20% de précision LAI.

---

**Document Status:** ✅ DIAGNOSTIC COMPLET  
**Next Action:** IMPLÉMENTER LES CORRECTIONS P0 DANS L'ORDRE
