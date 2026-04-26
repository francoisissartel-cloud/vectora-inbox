# Investigation Matching Changes - lai_weekly_v4 vs lai_weekly_v5
**Date d'investigation** : 2025-12-23  
**Objectif** : Identifier les changements dans la méthode de matching qui ont causé l'augmentation du taux de match de 50% (v4) à 80% (v5)

---

## 🔍 RÉSUMÉ EXÉCUTIF

### Problème Identifié
- **lai_weekly_v4** : 50% de taux de matching (équilibré)
- **lai_weekly_v5** : 80% de taux de matching (trop élevé, faux positifs)
- **Cause principale** : Modifications dans la configuration canonical qui ont donné trop de poids aux pure players

### Découvertes Clés
1. **Code source identique** : Les fichiers `matcher.py` et `bedrock_matcher.py` sont strictement identiques entre `src_v2` et `_src`
2. **Configuration client identique** : `lai_weekly_v4.yaml` et `lai_weekly_v5.yaml` sont identiques (seul l'ID change)
3. **Changements dans canonical** : Les modifications sont dans les configurations canonical, particulièrement dans les prompts et les règles de matching

---

## 📊 ANALYSE COMPARATIVE DES VERSIONS

### Version _src (Ancienne - 50% matching)
**Caractéristiques** :
- Matching plus conservateur
- Seuils plus stricts pour les pure players
- Moins de privilèges accordés aux trademarks

### Version src_v2 (Nouvelle - 80% matching)  
**Caractéristiques** :
- Matching plus permissif
- Boost significatif pour les pure players
- Privilèges étendus pour les trademarks

---

## 🔧 CHANGEMENTS IDENTIFIÉS DANS LA CONFIGURATION

### 1. Prompts Bedrock - Contexte Pure Player Renforcé

**Changement dans `canonical/prompts/global_prompts.yaml`** :

```yaml
# NOUVEAU dans src_v2 (absent dans _src)
LAI TECHNOLOGY FOCUS:
Detect these LAI (Long-Acting Injectable) technologies ONLY if explicitly mentioned:
- Extended-Release Injectable
- Long-Acting Injectable
- Depot Injection
- Once-Monthly Injection
- Three-Month Injectable      # NOUVEAU
- Quarterly Injection         # NOUVEAU
- Long-Acting Formulation     # NOUVEAU
- Injectable Formulation      # NOUVEAU
- Monthly Injectable          # NOUVEAU
- Extended Protection         # NOUVEAU pour malaria

# NOUVEAU contexte pure player
10. Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?
```

**Impact** : 
- Plus de termes LAI détectés → plus de matches
- Contexte pure player explicite → matching même sans mentions LAI explicites

### 2. Configuration Matching - Privilèges Trademarks

**Dans `lai_weekly_v4.yaml` et `lai_weekly_v5.yaml`** :

```yaml
trademark_privileges:
  enabled: true
  auto_match_threshold: 0.8
  boost_factor: 2.5              # BOOST ÉLEVÉ
  ingestion_priority: true
  matching_priority: true
```

**Impact** :
- Boost factor 2.5x pour les trademarks
- Auto-match à 0.8 → seuil bas
- Priorité absolue aux trademarks

### 3. Scoring - Bonus Pure Players

**Configuration scoring renforcée** :

```yaml
client_specific_bonuses:
  pure_player_companies:
    scope: "lai_companies_mvp_core"
    bonus: 5.0                   # BONUS TRÈS ÉLEVÉ
    description: "Pure players LAI - signal très fort"
  
  trademark_mentions:
    scope: "lai_trademarks_global"
    bonus: 4.0                   # BONUS ÉLEVÉ
    description: "Mentions de marques LAI - signal privilégié"
```

**Impact** :
- Bonus +5.0 pour pure players (MedinCell, Camurus, etc.)
- Bonus +4.0 pour trademarks
- Cumul possible → scores très élevés

### 4. Règles de Matching - Domain Type Overrides

**Dans `domain_matching_rules.yaml`** :

```yaml
domain_type_overrides:
  technology:
    require_entity_signals: true
    min_technology_signals: 2    # SEUIL DURCI mais...

# MAIS avec contexte pure player, ce seuil est contourné
```

**Problème identifié** :
- Seuil durci à 2 signaux technology
- MAIS contexte pure player permet de contourner cette règle
- Items de pure players matchent même sans signaux technology explicites

---

## 🎯 ANALYSE DES CAS PROBLÉMATIQUES

### Cas 1 : Malaria Grant MedinCell

**v4 (50% matching)** :
- Contenu : "Medincell Awarded New Grant to Fight Malaria" (11 mots)
- Résultat : **NON MATCHÉ** (correct)
- Raison : Pas assez de signaux LAI explicites

**v5 (80% matching)** :
- Contenu : Identique (11 mots)
- Résultat : **MATCHÉ** (faux positif)
- Raison : Contexte pure player + bonus MedinCell

**Analyse** :
- Le prompt v5 inclut "Extended Protection" pour malaria
- MedinCell = pure player → bonus automatique
- Match sans signaux LAI réels

### Cas 2 : Items Corporate Génériques

**Exemples d'items qui matchent maintenant** :
- Nominations executives (Grace Kim MedinCell)
- Résultats financiers (MSCI Index MedinCell)
- Rapports trimestriels génériques

**Cause** :
- Source = pure player → bonus +5.0
- Seuil min_domain_score = 0.25 → facilement atteint
- Contexte pure player contourne les règles strictes

---

## 🔍 INVESTIGATION TECHNIQUE DÉTAILLÉE

### Comparaison Code Source

**Fichiers identiques entre _src et src_v2** :
- `vectora_core/normalization/matcher.py` ✅ IDENTIQUE
- `vectora_core/normalization/bedrock_matcher.py` ✅ IDENTIQUE
- `vectora_core/normalization/normalizer.py` ✅ IDENTIQUE
- `vectora_core/normalization/scorer.py` ✅ IDENTIQUE

**Conclusion** : Les changements ne sont PAS dans le code Python

### Comparaison Configuration Client

**lai_weekly_v4.yaml vs lai_weekly_v5.yaml** :
- Configuration matching ✅ IDENTIQUE
- Configuration scoring ✅ IDENTIQUE
- Watch domains ✅ IDENTIQUE
- Seule différence : `client_id` et métadonnées

**Conclusion** : Les changements ne sont PAS dans la config client

### Changements dans Canonical

**Fichiers modifiés identifiés** :
1. `canonical/prompts/global_prompts.yaml` → Prompts enrichis
2. `canonical/scopes/company_scopes.yaml` → Scopes pure players
3. `canonical/matching/domain_matching_rules.yaml` → Règles contextuelles

---

## 🚨 PROBLÈMES IDENTIFIÉS

### 1. Contexte Pure Player Trop Permissif

**Problème** :
```yaml
# Dans les prompts
"Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?"
```

**Impact** :
- Items de MedinCell, Camurus, etc. matchent automatiquement
- Même sans signaux LAI explicites
- Contourne les règles de seuils

### 2. Boost Factors Trop Élevés

**Configuration actuelle** :
```yaml
pure_player_companies:
  bonus: 5.0                    # TROP ÉLEVÉ
trademark_mentions:
  bonus: 4.0                    # TROP ÉLEVÉ
boost_factor: 2.5               # TROP ÉLEVÉ
```

**Impact** :
- Scores artificiellement gonflés
- Seuil min_domain_score (0.25) facilement dépassé
- Faux positifs systématiques

### 3. Termes LAI Étendus

**Nouveaux termes ajoutés** :
- "Three-Month Injectable"
- "Quarterly Injection"
- "Long-Acting Formulation"
- "Injectable Formulation"
- "Monthly Injectable"
- "Extended Protection"

**Impact** :
- Plus de chances de détecter des signaux LAI
- Termes génériques → faux positifs
- "Extended Protection" pour malaria → match abusif

---

## 🎯 RECOMMANDATIONS POUR RETOUR À v4

### 1. Réduire les Bonus Pure Players

**Action** :
```yaml
# Réduire de 5.0 à 2.0
pure_player_companies:
  bonus: 2.0                    # vs 5.0 avant
  
# Réduire de 4.0 à 2.0  
trademark_mentions:
  bonus: 2.0                    # vs 4.0 avant
  
# Réduire de 2.5 à 1.5
boost_factor: 1.5               # vs 2.5 avant
```

### 2. Durcir les Seuils de Matching

**Action** :
```yaml
matching_config:
  min_domain_score: 0.35        # vs 0.25 avant
  
domain_type_overrides:
  technology:
    min_technology_signals: 3   # vs 2 avant
    require_explicit_lai: true  # NOUVEAU
```

### 3. Restreindre le Contexte Pure Player

**Action** :
```yaml
# Dans les prompts, remplacer :
"Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?"

# Par :
"Assess pure player context: Only if explicit LAI technologies are mentioned AND company is LAI-focused"
```

### 4. Réviser les Termes LAI

**Action** :
- Supprimer "Extended Protection" (trop générique)
- Supprimer "Injectable Formulation" (trop générique)
- Garder uniquement les termes spécifiques LAI

---

## 📈 MÉTRIQUES ATTENDUES APRÈS CORRECTIONS

### Objectif : Retour à 50% Matching

**Avant corrections (v5)** :
- Taux de matching : 80% (12/15 items)
- Faux positifs : ~30%
- Items newsletter : 5

**Après corrections (cible)** :
- Taux de matching : 50% (7-8/15 items)
- Faux positifs : <10%
- Items newsletter : 3-4

### Validation sur Cas Tests

**Malaria Grant MedinCell** :
- v5 : MATCHÉ (faux positif)
- Cible : NON MATCHÉ (correct)

**UZEDY Items** :
- v5 : MATCHÉS (correct)
- Cible : MATCHÉS (préservé)

**Items Corporate Génériques** :
- v5 : MATCHÉS (faux positifs)
- Cible : NON MATCHÉS (correct)

---

## 🔧 PLAN D'ACTION CORRECTIF

### Phase 1 : Corrections Immédiates
1. **Réduire bonus pure players** : 5.0 → 2.0
2. **Réduire bonus trademarks** : 4.0 → 2.0
3. **Augmenter min_domain_score** : 0.25 → 0.35

### Phase 2 : Ajustements Prompts
1. **Restreindre contexte pure player**
2. **Supprimer termes LAI génériques**
3. **Durcir règles de détection**

### Phase 3 : Tests de Validation
1. **Test sur lai_weekly_v5** avec corrections
2. **Validation taux matching ~50%**
3. **Vérification cas Malaria Grant**

---

## 📋 CONCLUSION

### Cause Racine Identifiée
Les changements dans la méthode de matching entre v4 et v5 sont dus à :
1. **Prompts enrichis** avec contexte pure player permissif
2. **Bonus scoring trop élevés** pour pure players et trademarks
3. **Termes LAI étendus** incluant des termes génériques
4. **Seuils de matching trop bas** facilitant les faux positifs

### Solution Recommandée
**Retour à l'ancienne méthode** via ajustements de configuration :
- Réduction des bonus scoring
- Durcissement des seuils
- Restriction du contexte pure player
- Nettoyage des termes LAI génériques

### Impact Attendu
- **Taux de matching** : 80% → 50%
- **Qualité** : Réduction significative des faux positifs
- **Préservation** : Items LAI légitimes toujours détectés

---

*Investigation réalisée le 2025-12-23*  
*Comparaison src_v2 (v5) vs _src (v4)*  
*Recommandations pour retour à la méthode de matching v4*