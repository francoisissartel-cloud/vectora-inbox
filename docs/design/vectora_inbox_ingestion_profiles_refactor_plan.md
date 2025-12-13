# Plan de Refactorisation : Profils d'Ingestion Vectora Inbox

## 1. Contexte et Objectifs

### 1.1 Problématique Actuelle
Actuellement, Vectora Inbox ingère et normalise tous les contenus des sources configurées sans distinction. Cette approche génère du bruit sur les sources très larges (presse sectorielle, big pharma) et consomme inutilement des ressources Bedrock.

### 1.2 Objectif de la Phase 1
Mettre en place une couche **d'ingestion profilée par source**, 100% pilotée par le canonical/config, SANS toucher au code runtime ni aux stacks AWS.

### 1.3 Philosophie : Ingestion vs Matching
- **Profils d'ingestion** : Garde-fou pour éviter de normaliser 90% de bruit sur des sources très larges
- **Règles de matching post-normalisation** : Source de vérité métier pour déterminer la pertinence finale
- **Principe** : Les profils d'ingestion ne remplacent PAS le matching, ils le complètent en amont

## 2. Architecture Cible

### 2.1 Structure Canonique Proposée
```
canonical/
├── ingestion/
│   ├── ingestion_profiles.yaml    # Nouveaux profils d'ingestion
│   └── README.md                  # Documentation des profils
├── sources/
│   └── source_catalog.yaml        # Enrichi avec ingestion_profile
└── scopes/                        # Existant, réutilisé
    ├── company_scopes.yaml
    ├── technology_scopes.yaml
    ├── trademark_scopes.yaml
    └── ...
```

### 2.2 Types de Profils d'Ingestion Identifiés

#### 2.2.1 Profils Corporate
- **`corporate_pure_player_broad`** : Pour pure players LAI (MedinCell, Camurus, etc.)
  - Logique : Ingérer quasiment tout (taux de signal très élevé)
  - Exclusions : RH, ESG ultra généraliste via exclusion_scopes
  
- **`corporate_hybrid_technology_focused`** : Pour big pharma/hybrid (AbbVie, Pfizer, etc.)
  - Logique : Ingérer uniquement si signaux forts du domaine surveillé
  - Signaux requis : core_phrases, technology_terms_high_precision, trademarks

#### 2.2.2 Profils Presse
- **`press_technology_focused`** : Pour presse sectorielle (FierceBiotech, etc.)
  - Logique : Ingérer si signaux LAI (entreprises + mots-clés + trademarks)
  - Signaux requis : Combinaison company_scope + technology_scope + trademark_scope

#### 2.2.3 Profils Futurs (Préparation)
- **`pubmed_technology_focused`** : Pour PubMed
- **`pubmed_indication_focused`** : Pour PubMed par indication
- **`clinicaltrials_indication_focused`** : Pour ClinicalTrials.gov
- **`dailymed_trademark_focused`** : Pour DailyMed

### 2.3 Mécanisme de Fonctionnement

1. **Source** → référence un `ingestion_profile` dans `source_catalog.yaml`
2. **Profil d'ingestion** → définit quels scopes utiliser et comment les combiner
3. **Runtime** (phase future) → applique la logique définie pour décider "ingérer ou pas"

## 3. Plan d'Exécution par Phases

### Phase A : Inventaire et Design Canonical
- [x] Analyser la structure existante
- [x] Définir l'architecture cible des profils d'ingestion
- [x] Identifier les types de profils nécessaires pour le MVP LAI

### Phase B : Création du Canonical d'Ingestion
- [ ] Créer `canonical/ingestion/ingestion_profiles.yaml`
- [ ] Définir les profils pour le MVP LAI
- [ ] Créer la documentation associée

### Phase C : Annotation des Sources Existantes
- [ ] Enrichir `canonical/sources/source_catalog.yaml` avec `ingestion_profile`
- [ ] Assigner les profils appropriés aux sources MVP LAI
- [ ] Maintenir la compatibilité ascendante

### Phase D : Mise à Jour des Configs Clients
- [ ] Adapter `client-config-examples/lai_weekly.yaml` si nécessaire
- [ ] Documenter l'articulation ingestion_profiles ↔ watch_domains

### Phase E : Documentation et Diagnostics
- [ ] Créer le diagnostic de refactorisation
- [ ] Mettre à jour le CHANGELOG
- [ ] Créer le résumé exécutif

## 4. Spécifications Détaillées

### 4.1 Structure du Fichier `ingestion_profiles.yaml`

```yaml
# Profils d'ingestion pour Vectora Inbox
# Ces profils définissent les critères de pré-filtrage avant normalisation

profiles:
  corporate_pure_player_broad:
    description: "Profil large pour pure players LAI - ingère quasiment tout"
    strategy: "broad_ingestion"
    signal_requirements:
      mode: "exclude_only"
      exclusion_scopes:
        - "exclusion_scopes.hr_content"
        - "exclusion_scopes.esg_generic"
    applicable_source_types: ["press_corporate"]
    applicable_companies: 
      scopes: ["lai_companies_pure_players", "lai_companies_mvp_core"]
    
  corporate_hybrid_technology_focused:
    description: "Profil focalisé pour hybrid/big pharma - ingère si signaux technologiques forts"
    strategy: "signal_based_ingestion"
    signal_requirements:
      mode: "require_signals"
      required_signal_types:
        - type: "technology_signals"
          scopes: ["lai_keywords.core_phrases", "lai_keywords.technology_terms_high_precision"]
          min_matches: 1
        - type: "trademark_signals"
          scopes: ["lai_trademarks_global"]
          min_matches: 0
      combination_logic: "technology_signals OR trademark_signals"
    applicable_source_types: ["press_corporate"]
    applicable_companies:
      scopes: ["lai_companies_hybrid"]
```

### 4.2 Enrichissement du `source_catalog.yaml`

```yaml
sources:
  - source_key: "press_corporate__medincell"
    # ... champs existants ...
    ingestion_profile: "corporate_pure_player_broad"
    
  - source_key: "press_corporate__abbvie"  # Exemple futur
    # ... champs existants ...
    ingestion_profile: "corporate_hybrid_technology_focused"
    
  - source_key: "press_sector__fiercebiotech"
    # ... champs existants ...
    ingestion_profile: "press_technology_focused"
```

### 4.3 Compatibilité Ascendante
- Si `ingestion_profile` absent → comportement par défaut "ingérer tout"
- Aucun impact sur les clients existants
- Migration progressive possible

## 5. Critères de Réussite

### 5.1 Livrables Attendus
- [ ] Plan détaillé (ce document)
- [ ] `canonical/ingestion/ingestion_profiles.yaml` complet
- [ ] `canonical/sources/source_catalog.yaml` enrichi
- [ ] Documentation dans `/docs/diagnostics/`
- [ ] Entrée CHANGELOG
- [ ] Résumé exécutif

### 5.2 Validation
- [ ] Tous les sources MVP LAI ont un profil assigné
- [ ] Structure générique réutilisable pour autres verticales
- [ ] Compatibilité ascendante préservée
- [ ] Documentation complète

## 6. Prochaines Étapes (Phase 2 - Runtime)

### 6.1 Adaptations Code Python
- Modifier les Lambdas d'ingestion pour utiliser les profils
- Implémenter la logique de pré-filtrage basée sur les signaux
- Ajouter les métriques d'ingestion filtrée

### 6.2 Tests et Validation
- Tests unitaires des profils d'ingestion
- Tests d'intégration avec sources réelles
- Validation des économies Bedrock

### 6.3 Monitoring
- Métriques d'items filtrés vs ingérés
- Alertes sur taux de filtrage anormal
- Dashboard de performance d'ingestion

## 7. Risques et Mitigation

### 7.1 Risques Identifiés
- **Sur-filtrage** : Risque de manquer des signaux pertinents
- **Complexité** : Profils trop complexes à maintenir
- **Performance** : Impact sur temps d'ingestion

### 7.2 Stratégies de Mitigation
- Commencer par des profils simples et itérer
- Tests approfondis avant déploiement production
- Métriques de monitoring détaillées
- Possibilité de désactiver le filtrage par source

---

**Statut** : Phase A terminée, Phase B en cours
**Prochaine étape** : Création du fichier `ingestion_profiles.yaml`