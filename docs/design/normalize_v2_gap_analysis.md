# Analyse des Gaps V1→V2 : Lambda normalize_score

**Date** : 15 janvier 2025  
**Objectif** : Cartographie précise des dysfonctionnements V2 vs V1 fonctionnel  
**Base** : Audit détaillé des modules src_v2/vectora_core/normalization/

---

## 1. Résumé Exécutif

### 1.1 État Actuel V2
- **Structure** : ✅ Architecture V2 présente avec 5 modules
- **Fonctionnalités** : ❌ Implémentations incomplètes et régressives
- **Configuration** : ✅ Canonical scopes et prompts disponibles
- **Intégration** : ❌ Prompts canoniques non utilisés

### 1.2 Gaps Critiques Identifiés
1. **Client Bedrock** : Pas de retry automatique, gestion d'erreurs basique
2. **Normalisation** : Prompts canoniques ignorés, champs LAI manquants
3. **Matching** : Logique simplifiée, pas de privilèges trademarks
4. **Scoring** : Règles métier non implémentées, bonus LAI absents
5. **Orchestration** : Gestion d'erreurs insuffisante, pas de parallélisation

---

## 2. Analyse Module par Module

### 2.1 bedrock_client.py - Régression Critique

#### État Actuel V2
```python
class BedrockNormalizationClient:
    def normalize_item(self, item_text, prompt_template, examples, max_retries=3):
        # ❌ Retry non implémenté (boucle for sans logique)
        # ❌ Gestion throttling basique
        # ❌ Parsing JSON fragile
        # ❌ Pas de validation champs LAI
```

#### Fonctionnalités V1 Manquantes
- **Retry automatique** : Backoff exponentiel, gestion ThrottlingException
- **Prompts canoniques** : Intégration avec global_prompts.yaml
- **Champs LAI spécialisés** : lai_relevance_score, anti_lai_detected, pure_player_context
- **Validation robuste** : Vérification champs obligatoires, fallbacks

#### Actions Requises
1. Implémenter retry avec `time.sleep(2 ** attempt)`
2. Intégrer prompts depuis `canonical_prompts["normalization"]["lai_default"]`
3. Ajouter validation champs LAI dans `_parse_response()`
4. Gestion spécifique ThrottlingException et ValidationException

### 2.2 normalizer.py - Logique Simplifiée

#### État Actuel V2
```python
def normalize_items(raw_items, canonical_scopes, canonical_prompts, bedrock_model, bedrock_region):
    # ✅ Structure correcte
    # ❌ Pas de parallélisation
    # ❌ Exemples canoniques limités
    # ❌ Pas de gestion d'erreurs par item
```

#### Fonctionnalités V1 Manquantes
- **Parallélisation contrôlée** : ThreadPoolExecutor avec max_workers
- **Exemples enrichis** : Utilisation complète des scopes canoniques
- **Gestion d'erreurs robuste** : Continue si échec item individuel
- **Statistiques détaillées** : Compteurs success/failed/total

#### Actions Requises
1. Ajouter paramètre `max_workers=1` avec ThreadPoolExecutor
2. Enrichir `_prepare_entity_examples()` avec plus de scopes
3. Implémenter gestion d'erreurs par item avec try/catch
4. Ajouter logging statistiques détaillées

### 2.3 matcher.py - Matching Minimal

#### État Actuel V2
```python
def match_items_to_domains(normalized_items, client_config, canonical_scopes):
    # ✅ Structure de base présente
    # ❌ Logique de matching non implémentée
    # ❌ Pas de privilèges trademarks
    # ❌ Pas d'évaluation domain_relevance
```

#### Fonctionnalités V1 Manquantes
- **Privilèges trademarks** : boost_factor, auto_match_threshold
- **Règles par domaine** : require_entity_signals, min_technology_signals
- **Évaluation domain_relevance** : Scores et raisons par domaine
- **Exclusions** : Application règles d'exclusion depuis canonical

#### Actions Requises
1. Implémenter `trademark_privileges` depuis client_config
2. Ajouter `domain_type_overrides` par type de domaine
3. Implémenter `_evaluate_domain_relevance()` avec scores
4. Ajouter `_apply_exclusions()` avec scopes exclusion

### 2.4 scorer.py - Scoring Incomplet

#### État Actuel V2
```python
def score_items(matched_items, client_config, canonical_scopes, scoring_mode, target_date):
    # ✅ Structure de base présente
    # ❌ Règles de scoring non implémentées
    # ❌ Pas de bonus LAI spécialisés
    # ❌ Facteurs de récence basiques
```

#### Fonctionnalités V1 Manquantes
- **Bonus LAI spécialisés** : pure_player (5.0), trademark (4.0), molecule (2.5)
- **Poids par événement** : partnership (8.0), regulatory (7.0), clinical (6.0)
- **Facteurs de récence** : Dégradation progressive selon âge
- **Seuils de sélection** : min_score, max_items_total depuis client_config

#### Actions Requises
1. Implémenter `client_specific_bonuses` depuis client_config
2. Ajouter `event_type_weight_overrides` avec poids LAI
3. Améliorer `_get_recency_factor()` avec dégradation progressive
4. Implémenter seuils depuis `selection_overrides`

### 2.5 __init__.py - Orchestration Basique

#### État Actuel V2
```python
def run_normalize_score_for_client(client_id, env_vars, ...):
    # ✅ Pipeline de base présent
    # ❌ Identification "dernier run" fragile
    # ❌ Pas de filtre temporel
    # ❌ Gestion d'erreurs insuffisante
```

#### Fonctionnalités V1 Manquantes
- **Stratégie données robuste** : Gestion multiples runs même jour
- **Filtre temporel** : Application period_days avant normalisation
- **Parallélisation** : Contrôle workers Bedrock
- **Statistiques complètes** : Métriques détaillées par étape

#### Actions Requises
1. Améliorer `_find_last_ingestion_run()` avec validation robuste
2. Ajouter filtre temporel basé sur period_days
3. Passer max_workers à normalizer
4. Enrichir statistiques de retour

---

## 3. Configuration et Canonical

### 3.1 Prompts Canoniques - Non Utilisés

#### Disponible dans global_prompts.yaml
```yaml
normalization:
  lai_default:
    user_template: |
      LAI TECHNOLOGY FOCUS:
      Detect these LAI (Long-Acting Injectable) technologies:
      - Extended-Release Injectable, Long-Acting Injectable
      - Depot Injection, Once-Monthly Injection
      
      TRADEMARKS to detect:
      - UZEDY, PharmaShell, SiliaShell, BEPO, Aristada
      
      8. Evaluate LAI relevance (0-10 score)
      9. Detect anti-LAI signals: oral routes
      10. Assess pure player context
```

#### Problème V2
- Prompts canoniques chargés mais **non utilisés**
- Retour aux prompts hardcodés basiques
- Perte de spécialisation LAI

### 3.2 Scopes Canoniques - Sous-Utilisés

#### Scopes LAI Disponibles
- `lai_companies_mvp_core` : 5 pure players
- `lai_companies_hybrid` : Big pharma avec activité LAI
- `lai_trademarks_global` : 70+ marques LAI
- `lai_molecules_global` : 90+ molécules
- `lai_keywords` : 80+ mots-clés technologiques

#### Utilisation V2 Actuelle
- Exemples limités (5 premiers de chaque scope)
- Pas de privilèges trademarks
- Pas de bonus par scope

---

## 4. Client Config lai_weekly_v3.yaml - Non Exploité

### 4.1 Configuration Matching Disponible
```yaml
matching_config:
  trademark_privileges:
    enabled: true
    boost_factor: 2.5
  domain_type_overrides:
    technology:
      require_entity_signals: true
      min_technology_signals: 2
```

### 4.2 Configuration Scoring Disponible
```yaml
scoring_config:
  client_specific_bonuses:
    pure_player_companies:
      scope: "lai_companies_mvp_core"
      bonus: 5.0
    trademark_mentions:
      scope: "lai_trademarks_global"
      bonus: 4.0
```

### 4.3 Problème V2
- Configuration chargée mais **non utilisée**
- Règles métier ignorées
- Perte de spécialisation LAI

---

## 5. Priorisation des Corrections

### 5.1 P0 - Fonctionnalités Critiques (Phase 2.1)
1. **Client Bedrock robuste** : Retry + prompts canoniques
2. **Champs LAI spécialisés** : lai_relevance_score, anti_lai_detected
3. **Gestion d'erreurs** : Fallbacks et logging

### 5.2 P1 - Logique Métier (Phase 2.2-2.4)
1. **Matching sophistiqué** : Privilèges trademarks + domain_relevance
2. **Scoring LAI** : Bonus spécialisés + poids événements
3. **Parallélisation** : Contrôle workers Bedrock

### 5.3 P2 - Robustesse (Phase 3)
1. **Stratégie données** : Identification dernier run robuste
2. **Filtre temporel** : Application period_days
3. **Statistiques** : Métriques détaillées

---

## 6. Validation des Inputs Disponibles

### 6.1 Configurations ✅ Disponibles
- `canonical/prompts/global_prompts.yaml` : Prompts LAI spécialisés
- `canonical/scopes/` : 5 fichiers de scopes complets
- `client-config-examples/lai_weekly_v3.yaml` : Configuration LAI complète

### 6.2 Modules V2 ✅ Présents
- Structure architecture V2 complète
- Imports relatifs corrects
- Handlers lambda fonctionnels

### 6.3 Prêt pour Restauration
Tous les inputs nécessaires sont disponibles pour restaurer les fonctionnalités V1 dans l'architecture V2.

---

## 7. Conclusion

### 7.1 Gap Principal
**Architecture V2 présente mais logique métier V1 non migrée**

### 7.2 Stratégie de Restauration
1. **Conserver structure V2** (architecture 3 lambdas)
2. **Restaurer logique V1** (normalisation, matching, scoring)
3. **Utiliser configurations canoniques** (prompts + scopes + client_config)

### 7.3 Effort Estimé
- **Phase 2.1** (Client Bedrock) : 2h
- **Phase 2.2** (Normalisation) : 2h  
- **Phase 2.3** (Matching) : 2h
- **Phase 2.4** (Scoring) : 2h
- **Total** : 8h pour restauration complète

La restauration est **faisable** avec tous les inputs disponibles et une roadmap claire.