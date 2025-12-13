# Plan de Refactorisation : period_days dans vectora-inbox-ingest-normalize

## État Actuel

### Lambda vectora-inbox-ingest-normalize-dev
- **Comportement actuel** : Scrappe et normalise TOUT le contenu disponible sur les sources RSS/HTML
- **Absence de filtre temporel** : Aucune limite de date appliquée avant l'appel Bedrock
- **Risques identifiés** :
  - Normalisation d'années d'historique → coût Bedrock inutile
  - Temps d'exécution long
  - Consommation excessive de tokens

### Extraction des dates
- **RSS** : Utilise `pubDate` des items RSS
- **HTML** : Dates extraites par les parsers HTML spécialisés (Camurus, Peptron, etc.)
- **Moment d'appel Bedrock** : Après extraction complète, sans filtre préalable

### Lambda vectora-inbox-engine-dev (référence)
- **Logique period_days fonctionnelle** :
  1. `payload["period_days"]` (priorité 1)
  2. `client_config["pipeline"]["default_period_days"]` (priorité 2)
  3. Fallback global (ex: 7 jours) (priorité 3)

## Objectif Cible

### Alignement des deux Lambdas
- **Même hiérarchie de priorité** pour `period_days`
- **Même paramètre** `period_days`
- **Application différente** : 
  - Engine : filtre les items normalisés
  - Ingest-normalize : filtre les items bruts AVANT normalisation

### Filtre temporel dans ingest-normalize
- **Point d'application** : Après extraction des dates, AVANT appel Bedrock
- **Logique** : `item_date >= (now - period_days)`
- **Économies** : Réduction drastique des appels Bedrock sur historique

## Questions Clés à Adresser

### 1. Items sans date fiable
- **Stratégie recommandée** : Skip par défaut pour périodes courtes (≤ 30 jours)
- **Configuration** : Flag `allow_undated_items` dans client_config
- **Comportement** : Loggé explicitement pour traçabilité

### 2. Compatibilité ascendante
- **Clients sans section pipeline** : Fallback global (7 jours)
- **Clients existants** : Aucun changement de comportement
- **Migration** : Transparente, pas de breaking change

### 3. Mutualisation de la logique
- **Module commun** : `src/vectora_core/config/config_utils.py`
- **Fonction** : `resolve_period_days(payload, client_config, fallback_days=7)`
- **Réutilisation** : Engine + Ingest-normalize

## Architecture Technique

### Flux modifié ingest-normalize
```
1. Extraction items bruts (RSS/HTML)
2. Extraction dates par item
3. Résolution period_days (payload > client_config > fallback)
4. NOUVEAU : Filtre temporel (item_date >= cutoff_date)
5. Normalisation Bedrock (items filtrés uniquement)
6. Stockage résultats
```

### Points d'intégration
- **Réutilisation parsers existants** : Pas de modification des extracteurs de dates
- **Logging enrichi** : Nombre d'items filtrés vs normalisés
- **Métriques** : Économies Bedrock mesurables

## Plan d'Implémentation

### Phase 1 : Mutualisation
- Factorisation `resolve_period_days()` dans module commun
- Migration engine vers fonction commune
- Tests unitaires fonction commune

### Phase 2 : Intégration ingest-normalize
- Ajout filtre temporel dans pipeline ingest
- Gestion items sans date
- Tests locaux avec différents period_days

### Phase 3 : Déploiement et validation
- Déploiement AWS DEV
- Tests end-to-end avec lai_weekly_v2 (30 jours)
- Validation économies Bedrock

## Critères de Succès

### Fonctionnels
- ✅ Même logique period_days entre engine et ingest-normalize
- ✅ Réduction significative des appels Bedrock sur historique
- ✅ Compatibilité ascendante préservée

### Techniques
- ✅ Code mutualisé sans duplication
- ✅ Logging et métriques appropriés
- ✅ Tests couvrant tous les cas d'usage

### Opérationnels
- ✅ Déploiement sans interruption de service
- ✅ Validation sur environnement DEV
- ✅ Documentation complète pour maintenance