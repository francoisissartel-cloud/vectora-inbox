# Phase 1 - Analyse & Cadrage Runtime - Résultats

## Vue d'ensemble

Analyse complète de l'architecture existante pour identifier les points d'intégration des trademarks et technology_profiles dans le runtime Vectora Inbox.

## Architecture Actuelle Identifiée

### Modules Lambda
- **ingest_normalize** : `src/lambdas/ingest_normalize/handler.py` → délègue à `vectora_core.run_ingest_normalize_for_client()`
- **engine** : `src/lambdas/engine/handler.py` → délègue à `vectora_core.run_engine_for_client()`

### Modules Vectora Core
- **config/loader.py** : Chargement configs client + canonical depuis S3
- **ingestion/profile_filter.py** : Filtrage intelligent pré-normalisation (DÉJÀ IMPLÉMENTÉ)
- **matching/matcher.py** : Matching items → domains avec support technology_profiles (DÉJÀ IMPLÉMENTÉ)
- **scoring/scorer.py** : Calcul scores avec bonus pure_player/hybrid (DÉJÀ IMPLÉMENTÉ)

### Configurations
- **client-config-examples/lai_weekly_v2.yaml** : Config v2 complète avec trademark_privileges
- **canonical/scopes/trademark_scopes.yaml** : 80+ marques LAI
- **canonical/scopes/technology_scopes.yaml** : Avec _metadata.profile
- **canonical/matching/domain_matching_rules.yaml** : Règles avec technology_profiles

## Points d'Intégration Identifiés

### ✅ DÉJÀ IMPLÉMENTÉ
1. **Technology Profiles** : Matching avec `technology_complex` vs `technology_simple` fonctionnel
2. **Company Scope Bonuses** : Scoring avec bonus pure_player/hybrid opérationnel
3. **Profile Filter** : Ingestion avec profils configurables actif

### 🔧 À IMPLÉMENTER
1. **Client Config v2 Parser** : Support des nouveaux champs v2 dans loader.py
2. **Trademark Ingestion Priority** : Logique `trademark_privileges.ingestion_priority = true`
3. **Trademark Matching Priority** : Logique `trademark_privileges.matching_priority = true`
4. **Client-Specific Scoring Bonuses** : Bonus depuis `scoring_config.client_specific_bonuses`

## Modules à Modifier

### 1. config/loader.py
**Modifications nécessaires :**
- Ajouter parsing des champs v2 : `matching_config`, `scoring_config`, `trademark_scope`
- Maintenir compatibilité v1 (fallback si champs absents)

### 2. ingestion/profile_filter.py
**Modifications nécessaires :**
- Intégrer `trademark_privileges.ingestion_priority` dans `apply_filter()`
- Détecter trademarks dans items bruts
- Forcer ingestion si trademark du client détecté

### 3. matching/matcher.py
**Modifications nécessaires :**
- Intégrer `trademark_privileges.matching_priority` dans `match_items_to_domains()`
- Forcer matching si trademark du scope détecté
- Utiliser `trademark_scope` depuis client_config v2

### 4. scoring/scorer.py
**Modifications nécessaires :**
- Intégrer `scoring_config.client_specific_bonuses` dans `compute_score()`
- Appliquer bonus trademarks depuis config client
- Maintenir logique existante pour pure_player/hybrid

## Stratégie de Compatibilité v1

### Principe
- Si champ v2 absent → comportement v1 inchangé
- Si champ v2 présent → nouvelles fonctionnalités activées
- Logs détaillés pour debugging

### Implémentation
```python
# Exemple pattern de compatibilité
def get_trademark_scope(client_config):
    # v2 : trademark_scope dans watch_domains
    for domain in client_config.get('watch_domains', []):
        if domain.get('trademark_scope'):
            return domain['trademark_scope']
    
    # v1 : pas de trademark_scope
    return None

def has_trademark_privileges(client_config):
    matching_config = client_config.get('matching_config', {})
    trademark_privileges = matching_config.get('trademark_privileges', {})
    return trademark_privileges.get('enabled', False)
```

## Risques Identifiés

### Faible Risque
- **Régression v1** : Pattern de compatibilité robuste
- **Performance** : Modifications légères, pas d'impact majeur

### Risque Moyen
- **Configuration S3** : Synchronisation canonical + client configs
- **Déploiement Lambda** : Re-packaging avec nouvelles dépendances

## Prochaines Étapes

### Phase 2 - Ingestion Trademarks
1. Modifier `config/loader.py` pour parser client_config v2
2. Étendre `ingestion/profile_filter.py` avec logique trademark_priority
3. Tests unitaires ingestion avec/sans trademarks

### Phase 3 - Matching Trademarks
1. Étendre `matching/matcher.py` avec trademark_privileges.matching_priority
2. Intégrer trademark_scope dans logique de matching
3. Tests matching avec trademarks

### Phase 4 - Scoring Client-Specific
1. Étendre `scoring/scorer.py` avec client_specific_bonuses
2. Intégrer bonus trademarks depuis config client
3. Tests scoring avec nouveaux bonus

## Conclusion Phase 1

✅ **Architecture bien comprise** : Points d'intégration identifiés précisément
✅ **Modules localisés** : Modifications ciblées dans 4 modules core
✅ **Compatibilité v1** : Stratégie de fallback définie
✅ **Risques maîtrisés** : Pas de refactoring majeur nécessaire

**Prêt pour Phase 2 - Implémentation Ingestion Trademarks**