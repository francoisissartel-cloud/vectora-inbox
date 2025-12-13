# Plan d'Exécution - Runtime Trademark & Profile Enhancement

## Vue d'ensemble

Ce plan détaille l'implémentation des modifications runtime pour exploiter le client_config v2, les trademarks et les profils technologiques dans Vectora Inbox, tout en maintenant la compatibilité avec les configs v1.

**Objectifs principaux :**
- Traitement privilégié des trademarks (ingestion + matching + scoring)
- Exploitation du client_config v2 (lai_weekly_v2.yaml)
- Compatibilité ascendante avec configs v1
- Déploiement sur AWS DEV et test end-to-end

---

## Phase 1 – Analyse & Cadrage Runtime

### 1.1 Audit du code existant

**Modules à analyser :**
- `src/lambda/ingest_normalize/` - Pipeline d'ingestion
- `src/lambda/engine/` - Moteur de matching et scoring
- `src/shared/` - Utilitaires partagés
- `canonical/` - Configurations canoniques
- `client-config-examples/` - Exemples de configs client

**Points de vérification :**
- [ ] Localiser les modules d'ingestion runtime actuels
- [ ] Identifier l'implémentation du matching actuel
- [ ] Analyser le système de scoring existant
- [ ] Vérifier l'utilisation actuelle de client_config v1 vs v2
- [ ] Mapper les dépendances entre modules

### 1.2 Analyse des configurations

**Fichiers à examiner :**
- `canonical/ingestion/ingestion_profiles.yaml`
- `canonical/scopes/trademark_scopes.yaml`
- `canonical/scopes/technology_scopes.yaml`
- `canonical/matching/domain_matching_rules.yaml`
- `client-config-examples/lai_weekly_v2.yaml`

### 1.3 Livrables Phase 1
- [ ] Cartographie précise des modules à modifier
- [ ] Liste des points d'intégration trademark/profile
- [ ] Identification des risques de régression v1

---

## Phase 2 – Implémentation Ingestion : Trademark Priorities

### 2.1 Logique trademark_privileges.ingestion_priority

**Implémentation :**
```python
# Dans le module d'ingestion
def should_ingest_item(item, client_config, canonical_scopes):
    # 1. Vérifier si client_config v2 avec trademark_privileges
    if has_trademark_privileges(client_config):
        # 2. Extraire trademarks de l'item
        item_trademarks = extract_trademarks(item)
        # 3. Vérifier intersection avec trademark_scope du client
        if trademark_match_found(item_trademarks, client_config.trademark_scope):
            return True  # Ingestion forcée
    
    # 4. Fallback sur logique d'ingestion standard
    return standard_ingestion_logic(item, client_config, canonical_scopes)
```

### 2.2 Intégration avec configurations

**Modifications nécessaires :**
- Extension du parser de client_config pour v2
- Chargement des trademark_scopes depuis canonical/
- Mise à jour des ingestion_profiles pour supporter les trademarks

### 2.3 Compatibilité ascendante

**Stratégie :**
- Si `trademark_privileges` absent → comportement v1 inchangé
- Si `trademark_scope` vide → pas de traitement privilégié
- Logs détaillés pour debugging

### 2.4 Livrables Phase 2
- [ ] Module d'ingestion trademark-aware
- [ ] Tests unitaires ingestion avec/sans trademarks
- [ ] Documentation des nouveaux paramètres

---

## Phase 3 – Implémentation Matching : Trademark Priority + Technology Profile

### 3.1 Logique trademark_privileges.matching_priority

**Implémentation :**
```python
def match_domains_for_item(normalized_item, client_config, domain_rules):
    matched_domains = []
    
    # 1. Matching par trademarks (priorité haute)
    if has_trademark_matching_priority(client_config):
        trademark_matches = find_trademark_domain_matches(
            normalized_item, 
            client_config.watch_domains,
            client_config.trademark_scope
        )
        matched_domains.extend(trademark_matches)
    
    # 2. Matching par technology_profile
    tech_matches = find_technology_profile_matches(
        normalized_item,
        client_config.watch_domains,
        resolve_technology_profiles(client_config)
    )
    matched_domains.extend(tech_matches)
    
    # 3. Matching standard (règles existantes)
    standard_matches = standard_domain_matching(normalized_item, domain_rules)
    matched_domains.extend(standard_matches)
    
    return deduplicate_matches(matched_domains)
```

### 3.2 Résolution des technology_profiles

**Logique :**
- Lecture de `technology_scopes.yaml` pour résoudre `_metadata.profile`
- Distinction `technology_complex` vs `technology_simple`
- Application des règles spécifiques (ex: lai_keywords → technology_complex)

### 3.3 Livrables Phase 3
- [ ] Module de matching étendu
- [ ] Résolveur de technology_profiles
- [ ] Tests matching trademark + technology
- [ ] Validation compatibilité v1

---

## Phase 4 – Implémentation Scoring : Client Specific Bonuses + Trademarks

### 4.1 Intégration scoring_config du client_config v2

**Nouveaux bonus à implémenter :**
```python
def calculate_item_score(item, client_config, base_score):
    final_score = base_score
    
    # 1. Bonus trademarks
    if has_trademark_mentions(item, client_config.trademark_scope):
        final_score += client_config.scoring_config.trademark_mentions.bonus
    
    # 2. Bonus pure players
    if is_pure_player_mention(item, client_config.company_scope.pure_players):
        final_score += client_config.scoring_config.company_scope.pure_players.bonus
    
    # 3. Autres bonus client-specific
    final_score += apply_client_specific_bonuses(item, client_config.scoring_config)
    
    return final_score
```

### 4.2 Gestion des fréquences (weekly vs monthly)

**Paramètres spécifiques :**
- `recency_factor = 1.0` pour weekly (neutralisé)
- Maintien des autres facteurs pour monthly/quarterly

### 4.3 Livrables Phase 4
- [ ] Module de scoring étendu
- [ ] Support des bonus client_config v2
- [ ] Tests scoring avec différents bonus
- [ ] Validation cohérence fréquences

---

## Phase 5 – Tests Locaux (Unitaires + Intégration)

### 5.1 Tests unitaires par module

**Ingestion :**
- Test avec trademark → ingestion forcée
- Test sans trademark → logique standard
- Test client v1 → comportement inchangé

**Matching :**
- Test trademark_priority → matching forcé
- Test technology_complex vs simple
- Test combinaison trademark + technology

**Scoring :**
- Test bonus trademarks
- Test bonus pure players
- Test neutralisation recency_factor

### 5.2 Script de simulation locale

**Fonctionnalités :**
```python
# simulate_lai_weekly_v2.py
def simulate_pipeline():
    # 1. Charger lai_weekly_v2.yaml
    # 2. Simuler items avec/sans trademarks
    # 3. Tester pipeline complet
    # 4. Générer rapport détaillé
```

### 5.3 Livrables Phase 5
- [ ] Suite de tests unitaires complète
- [ ] Script de simulation locale
- [ ] Rapport de tests avec métriques

---

## Phase 6 – Déploiement AWS DEV & Synchronisation S3

### 6.1 Synchronisation des configurations

**Fichiers à uploader :**
```bash
# Configurations canoniques
aws s3 sync canonical/ s3://vectora-inbox-dev-config/canonical/ --profile vectora-dev

# Configuration client lai_weekly_v2
aws s3 cp client-config-examples/lai_weekly_v2.yaml s3://vectora-inbox-dev-config/clients/lai_weekly_v2.yaml --profile vectora-dev
```

### 6.2 Déploiement des Lambdas

**Stacks concernées :**
- `vectora-inbox-runtime-stack` (ingest-normalize, engine)
- `vectora-inbox-config-stack` (si modifications)

**Commandes de déploiement :**
```bash
# Package et deploy des Lambdas
./scripts/deploy-lambda.sh ingest-normalize dev
./scripts/deploy-lambda.sh engine dev

# Mise à jour des stacks CloudFormation si nécessaire
aws cloudformation update-stack --stack-name vectora-inbox-runtime-dev --template-body file://infrastructure/runtime-stack.yaml --profile vectora-dev
```

### 6.3 Livrables Phase 6
- [ ] Configurations synchronisées sur S3
- [ ] Lambdas déployées sur AWS DEV
- [ ] Validation déploiement (health checks)

---

## Phase 7 – Nouveau Client lai_weekly_v2 en DEV + Test End-to-End

### 7.1 Configuration du client lai_weekly_v2

**Vérifications :**
- [ ] Client config uploadé dans `s3://vectora-inbox-dev-config/clients/`
- [ ] Chemins S3 corrects pour outputs
- [ ] Paramètres trademark_privileges activés
- [ ] Technology_profiles correctement référencés

### 7.2 Exécution du workflow complet

**Étapes :**
1. **Ingestion :** `aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev --payload '{"client_id": "lai_weekly_v2"}' --profile vectora-dev`
2. **Engine :** `aws lambda invoke --function-name vectora-inbox-engine-dev --payload '{"client_id": "lai_weekly_v2", "time_window": "7d"}' --profile vectora-dev`
3. **Monitoring :** Vérification des logs CloudWatch

### 7.3 Diagnostic détaillé

**Métriques à collecter :**
- Nombre d'items ingérés vs filtrés
- Impact des trademarks sur l'ingestion (items "sauvés")
- Répartition matching par domaine
- Distribution des scores avec nouveaux bonus
- Comparaison pure players vs hybrid

### 7.4 Livrables Phase 7
- [ ] Client lai_weekly_v2 opérationnel
- [ ] Newsletter générée pour fenêtre 7 jours
- [ ] Rapport diagnostic détaillé dans `/docs/diagnostics/`

---

## Phase 8 – Synthèse & Recommandations

### 8.1 Documentation finale

**Fichiers à créer/mettre à jour :**
- `CHANGELOG.md` - Nouvelles fonctionnalités v2
- `docs/diagnostics/vectora_inbox_lai_weekly_v2_runtime_results.md` - Résultats détaillés
- `docs/diagnostics/vectora_inbox_runtime_trademark_and_profile_enhancement_executive_summary.md` - Synthèse exécutive

### 8.2 Recommandations d'amélioration

**Points d'attention identifiés :**
- Seuils de scoring à ajuster
- Nouveaux scopes trademark à ajouter
- Optimisations performance
- Monitoring et alerting

### 8.3 Livrables Phase 8
- [ ] Documentation complète mise à jour
- [ ] Executive summary avec ROI
- [ ] Roadmap des améliorations futures

---

## Critères de Succès

### Fonctionnels
- [ ] Trademarks correctement privilégiés dans tout le pipeline
- [ ] Client_config v2 entièrement exploité
- [ ] Compatibilité v1 préservée
- [ ] Newsletter lai_weekly_v2 générée avec qualité

### Techniques
- [ ] Tests unitaires > 90% coverage
- [ ] Performance pipeline maintenue
- [ ] Logs et monitoring opérationnels
- [ ] Déploiement AWS DEV stable

### Métiers
- [ ] Réduction faux négatifs grâce aux trademarks
- [ ] Amélioration précision grâce aux technology_profiles
- [ ] Scoring plus pertinent avec bonus client-specific
- [ ] Diagnostic actionnable pour optimisations futures

---

## Risques et Mitigations

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Régression clients v1 | Élevé | Faible | Tests exhaustifs compatibilité |
| Performance dégradée | Moyen | Moyen | Benchmarks et optimisations |
| Configurations S3 corrompues | Élevé | Faible | Backup avant déploiement |
| Permissions AWS insuffisantes | Moyen | Moyen | Validation préalable accès |

---

## Planning Estimé

- **Phase 1 :** 0.5 jour
- **Phase 2 :** 1 jour  
- **Phase 3 :** 1 jour
- **Phase 4 :** 0.5 jour
- **Phase 5 :** 0.5 jour
- **Phase 6 :** 0.5 jour
- **Phase 7 :** 0.5 jour
- **Phase 8 :** 0.5 jour

**Total estimé :** 4.5 jours