# Plan de Design - Template Client Config v2

## Vue d'Ensemble

Ce document définit la structure et les spécifications du template v2 de configuration client pour Vectora Inbox. Le template v2 vise à résoudre les ambiguïtés identifiées dans le diagnostic et à fournir une interface plus explicite et documentée.

---

## 1. Principes de Design

### 1.1 Explicité vs Implicité

**v1 (actuel)** : Beaucoup de comportements implicites (profils déduits, trademarks non déclarés)
**v2 (cible)** : Comportements explicites et documentés dans le client_config

### 1.2 Séparation des Responsabilités

- **Canonical** : Définit les scopes, profils, et règles métier réutilisables
- **Client Config** : Déclare les choix spécifiques du client et les overrides
- **Runtime** : Exécute la logique selon la configuration

### 1.3 Extensibilité

Le template v2 doit être facilement extensible pour de nouveaux verticaux (oncologie, immunologie, etc.)

---

## 2. Structure du Template v2

### 2.1 Sections Principales

```yaml
# Template Client Config v2
client_profile:          # Métadonnées client
watch_domains:           # Domaines de veille (cœur de la config)
source_config:           # Configuration des sources
ingestion_overrides:     # Overrides des profils d'ingestion (optionnel)
matching_config:         # Configuration du matching (nouveau)
scoring_config:          # Configuration du scoring (nouveau)
newsletter_layout:       # Structure de la newsletter
newsletter_delivery:     # Configuration de livraison
```

### 2.2 Section client_profile

**Champs obligatoires** :
- `name` : Nom de la newsletter/client
- `client_id` : Identifiant unique
- `language` : Langue de la newsletter
- `frequency` : Fréquence de génération

**Champs optionnels** :
- `tone` : Ton de la newsletter (executive, technical, etc.)
- `voice` : Style rédactionnel (concise, detailed, etc.)
- `target_audience` : Audience cible (executives, researchers, etc.)

**Connexions** :
- Utilisé par le module newsletter pour adapter le style
- Référencé dans les logs et métadonnées

### 2.3 Section watch_domains (Cœur du Template)

**Structure** :
```yaml
watch_domains:
  - id: "domain_unique_id"
    type: "technology|indication|regulatory|custom"
    priority: "high|medium|low"
    
    # Scopes canonical (références aux fichiers canonical/scopes/)
    technology_scope: "scope_key"      # Obligatoire si type=technology
    company_scope: "scope_key"         # Recommandé
    molecule_scope: "scope_key"        # Recommandé
    trademark_scope: "scope_key"       # Nouveau - Optionnel mais recommandé
    indication_scope: "scope_key"      # Obligatoire si type=indication
    
    # Profils de matching (nouveau - explicite)
    technology_profile: "technology_complex|technology_simple"  # Optionnel, déduit de canonical si absent
    matching_profile: "strict|balanced|broad"                  # Optionnel, défaut=balanced
    
    # Configuration spécifique
    notes: "Description libre"
    enabled: true                      # Permet de désactiver temporairement
```

**Règles de validation** :
- `technology_scope` obligatoire si `type: "technology"`
- `indication_scope` obligatoire si `type: "indication"`
- Les clés de scopes doivent exister dans les fichiers canonical correspondants
- Au moins un scope d'entité (`company_scope` ou `molecule_scope`) recommandé

### 2.4 Section source_config

**Structure** :
```yaml
source_config:
  # Bouquets activés (comme v1)
  source_bouquets_enabled:
    - "bouquet_id_1"
    - "bouquet_id_2"
  
  # Sources supplémentaires (comme v1)
  sources_extra_enabled: []
  
  # Nouveau : Overrides de profils d'ingestion par bouquet
  bouquet_ingestion_overrides:
    "bouquet_id_1":
      profile: "custom_profile_name"
      rationale: "Raison du override"
```

**Connexions** :
- `source_bouquets_enabled` → `source_catalog.yaml`
- Profils d'ingestion → `ingestion_profiles.yaml`

### 2.5 Section ingestion_overrides (Nouveau - Optionnel)

**Objectif** : Permettre au client de personnaliser les profils d'ingestion sans modifier le canonical.

**Structure** :
```yaml
ingestion_overrides:
  profiles:
    custom_profile_name:
      base_profile: "press_technology_focused"  # Hérite d'un profil existant
      signal_requirements:
        # Override des requirements
        required_signal_groups:
          - group_id: "trademark_signals_priority"
            scopes: ["lai_trademarks_global"]
            min_matches: 1
            weight: 5.0  # Poids plus élevé que le profil de base
      rationale: "Priorité absolue aux trademarks pour ce client"
```

### 2.6 Section matching_config (Nouveau)

**Objectif** : Configuration explicite du comportement de matching.

**Structure** :
```yaml
matching_config:
  # Comportement global
  default_matching_mode: "strict|balanced|broad"
  
  # Règles spécifiques par type de domaine
  domain_type_overrides:
    technology:
      require_entity_signals: true
      min_technology_signals: 2
    regulatory:
      require_entity_signals: false
  
  # Traitement privilégié des trademarks
  trademark_privileges:
    enabled: true
    auto_match_threshold: 0.8  # Seuil de confiance pour match automatique
    boost_factor: 2.0          # Facteur de boost pour le scoring
```

### 2.7 Section scoring_config (Nouveau)

**Objectif** : Personnalisation des règles de scoring au niveau client.

**Structure** :
```yaml
scoring_config:
  # Overrides des poids par type d'événement
  event_type_weight_overrides:
    partnership: 8  # Plus important que la valeur par défaut (6)
  
  # Bonus spécifiques au client
  client_specific_bonuses:
    pure_player_companies:
      scope: "lai_companies_mvp_core"
      bonus: 4.0
    trademark_mentions:
      scope: "lai_trademarks_global"
      bonus: 3.0
    key_molecules:
      scope: "lai_molecules_global"
      bonus: 2.0
  
  # Seuils de sélection personnalisés
  selection_overrides:
    min_score: 12  # Plus strict que le défaut (10)
    min_items_per_section: 2
```

### 2.8 Sections newsletter_layout et newsletter_delivery

**Conservées de v1** avec améliorations mineures :
- Ajout de `filter_domains` pour filtrer par watch_domain
- Ajout de `sort_by` pour personnaliser l'ordre de tri

---

## 3. Mécanismes de Résolution

### 3.1 Résolution des Profils

**Ordre de priorité** :
1. Profil explicite dans `watch_domains[].technology_profile`
2. Profil déduit de `canonical/scopes/technology_scopes.yaml._metadata.profile`
3. Profil par défaut (`technology_simple`)

### 3.2 Résolution des Scopes

**Validation** :
- Toutes les clés de scopes référencées doivent exister dans les fichiers canonical
- Warning si un scope référencé est vide
- Erreur si un scope obligatoire est manquant

### 3.3 Résolution des Overrides

**Ordre de priorité** :
1. `client_config.scoring_config.event_type_weight_overrides`
2. `canonical/scoring/scoring_rules.yaml.event_type_weights`

---

## 4. Exemples d'Usage

### 4.1 Configuration LAI Basique

```yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    type: "technology"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    trademark_scope: "lai_trademarks_global"  # Nouveau
    priority: "high"
```

### 4.2 Configuration Multi-Indication

```yaml
watch_domains:
  - id: "lai_addiction"
    type: "indication"
    indication_scope: "addiction_keywords"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    trademark_scope: "lai_trademarks_global"
    priority: "high"
    
  - id: "lai_psychiatry"
    type: "indication"
    indication_scope: "psychiatry_keywords"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    trademark_scope: "lai_trademarks_global"
    priority: "medium"
```

### 4.3 Configuration avec Overrides

```yaml
matching_config:
  trademark_privileges:
    enabled: true
    auto_match_threshold: 0.9
    boost_factor: 3.0

scoring_config:
  client_specific_bonuses:
    trademark_mentions:
      scope: "lai_trademarks_global"
      bonus: 5.0  # Bonus très élevé pour les trademarks
```

---

## 5. Migration v1 → v2

### 5.1 Compatibilité Ascendante

**Principe** : Les configs v1 doivent continuer à fonctionner avec le runtime v2.

**Mécanisme** : 
- Détection automatique de la version (présence de `matching_config` = v2)
- Mapping automatique des champs v1 vers v2
- Warnings pour les fonctionnalités v2 non utilisées

### 5.2 Guide de Migration

**Étapes recommandées** :
1. Ajouter `trademark_scope` aux watch_domains existants
2. Expliciter les `technology_profile` si différents du défaut
3. Ajouter `matching_config.trademark_privileges.enabled: true`
4. Personnaliser `scoring_config` selon les besoins métier

---

## 6. Validation et Tests

### 6.1 Validation Statique

**Règles à implémenter** :
- Validation YAML schema
- Vérification de l'existence des scopes référencés
- Cohérence entre watch_domains et source_config
- Validation des overrides (pas de cycles, valeurs dans les ranges acceptés)

### 6.2 Tests de Régression

**Scénarios** :
- Config v1 → comportement identique avec runtime v2
- Config v2 basique → amélioration mesurable vs v1
- Config v2 avec overrides → comportement personnalisé correct

---

## 7. Documentation et Maintenance

### 7.1 Template Commenté

Le template v2 sera livré avec :
- Commentaires YAML explicatifs pour chaque section
- Exemples concrets pour chaque type de configuration
- Références vers la documentation canonical

### 7.2 Outils de Support

**À développer** :
- Script de validation de config
- Script de migration v1 → v2
- Générateur de config à partir de questionnaire métier

---

*Plan de design v2 - Version 1.0 - 2024-12-19*