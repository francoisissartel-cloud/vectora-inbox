# Profils d'Ingestion Vectora Inbox

## Vue d'Ensemble

Les profils d'ingestion définissent les critères de pré-filtrage appliqués **avant** la normalisation Bedrock. Ils permettent d'économiser les ressources en évitant de normaliser du contenu non pertinent sur les sources très larges.

## Philosophie

### Ingestion vs Matching
- **Profils d'ingestion** : Garde-fou pour éviter de normaliser 90% de bruit
- **Règles de matching** : Source de vérité métier pour la pertinence finale
- **Principe** : L'ingestion filtre le bruit évident, le matching fait la sélection fine

### Stratégies d'Ingestion

1. **`broad_ingestion`** : Ingère tout sauf exclusions explicites
   - Usage : Pure players avec taux de signal élevé
   - Exemple : MedinCell, Camurus (sources corporate LAI)

2. **`signal_based_ingestion`** : Ingère uniquement si signaux requis détectés
   - Usage : Sources avec beaucoup de bruit
   - Exemple : Big pharma (AbbVie, Pfizer)

3. **`multi_signal_ingestion`** : Ingère si combinaison de signaux multiples
   - Usage : Presse sectorielle très large
   - Exemple : FierceBiotech, FiercePharma

4. **`no_filtering`** : Ingère tout (compatibilité ascendante)
   - Usage : Profil par défaut

## Structure des Profils

### Champs Principaux

```yaml
profile_name:
  description: "Description du profil"
  strategy: "broad_ingestion|signal_based_ingestion|multi_signal_ingestion|no_filtering"
  rationale: "Justification métier"
  
  signal_requirements:
    mode: "exclude_only|require_signals|require_multi_signals|ingest_all"
    # Configuration spécifique selon le mode
    
  applicable_contexts:
    source_types: ["press_corporate", "press_sector", "academic_database"]
    company_scopes: ["lai_companies_pure_players", ...]
    domains: ["tech_lai_ecosystem", ...]
    
  runtime_config:
    default_action: "ingest|filter_out"
    signal_detection_threshold: 0.6  # Seuil de confiance
```

### Modes de Signal Requirements

#### `exclude_only`
Ingère tout sauf contenus avec signaux d'exclusion.
```yaml
signal_requirements:
  mode: "exclude_only"
  exclusion_scopes:
    - "exclusion_scopes.hr_content"
    - "exclusion_scopes.esg_generic"
```

#### `require_signals`
Ingère uniquement si signaux requis détectés.
```yaml
signal_requirements:
  mode: "require_signals"
  required_signal_groups:
    - group_id: "technology_signals"
      scopes: ["lai_keywords.core_phrases"]
      min_matches: 1
      weight: 3.0
  combination_logic: "technology_signals"
  minimum_total_weight: 2.0
```

#### `require_multi_signals`
Ingère si combinaison de plusieurs types de signaux.
```yaml
signal_requirements:
  mode: "require_multi_signals"
  required_signal_groups:
    - group_id: "entity_signals"
      scopes: ["lai_companies_global"]
      min_matches: 1
      weight: 2.0
    - group_id: "technology_signals"
      scopes: ["lai_keywords.core_phrases"]
      min_matches: 1
      weight: 2.0
  combination_logic: "entity_signals AND technology_signals"
  minimum_total_weight: 3.0
```

## Profils Disponibles

### Profils Corporate

#### `corporate_pure_player_broad`
- **Usage** : Pure players LAI (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
- **Logique** : Ingère quasiment tout sauf bruit évident (RH, ESG généraliste)
- **Rationale** : Taux de signal très élevé chez les pure players

#### `corporate_hybrid_technology_focused`
- **Usage** : Big pharma/hybrid avec activité LAI (AbbVie, Pfizer, Sanofi, etc.)
- **Logique** : Ingère uniquement si signaux technologiques LAI forts
- **Rationale** : Éviter le bruit des activités non-LAI

### Profils Presse

#### `press_technology_focused`
- **Usage** : Presse sectorielle (FierceBiotech, FiercePharma, Endpoints)
- **Logique** : Ingère si entités LAI + signaux technologiques
- **Rationale** : Filtrer le bruit des articles non-LAI

### Profils Futurs

#### `pubmed_technology_focused`
- **Usage** : Publications académiques PubMed
- **Logique** : Signaux technologiques + entités avec seuil élevé
- **Rationale** : PubMed très large, besoin de filtrage strict

#### `pubmed_indication_focused`
- **Usage** : Publications PubMed par indication
- **Logique** : Signaux indication + signaux LAI
- **Rationale** : Surveillance ciblée par pathologie

## Utilisation

### 1. Assignment dans source_catalog.yaml
```yaml
sources:
  - source_key: "press_corporate__medincell"
    # ... autres champs ...
    ingestion_profile: "corporate_pure_player_broad"
    
  - source_key: "press_sector__fiercebiotech"
    # ... autres champs ...
    ingestion_profile: "press_technology_focused"
```

### 2. Compatibilité Ascendante
Si `ingestion_profile` absent → utilise `default_broad` (ingère tout).

### 3. Validation
Le système valide que :
- Le profil existe dans `ingestion_profiles.yaml`
- Les scopes référencés existent dans `canonical/scopes/`
- Le profil est applicable au type de source

## Implémentation Runtime (Phase Future)

### Workflow d'Ingestion
1. **Récupération du contenu** (RSS/HTML)
2. **Application du profil d'ingestion** ← NOUVEAU
   - Extraction des signaux du texte brut
   - Évaluation selon les critères du profil
   - Décision : ingérer ou filtrer
3. **Normalisation Bedrock** (si ingéré)
4. **Matching post-normalisation** (existant)

### Métriques Prévues
- Taux de filtrage par source
- Économies Bedrock réalisées
- Faux positifs/négatifs du filtrage

## Maintenance

### Ajout d'un Nouveau Profil
1. Définir le profil dans `ingestion_profiles.yaml`
2. Tester avec des données réelles
3. Assigner aux sources appropriées
4. Monitorer les métriques

### Modification d'un Profil Existant
1. Analyser l'impact sur les sources utilisant ce profil
2. Tester les changements
3. Déployer progressivement
4. Valider les métriques

## Exemples d'Usage

### Cas 1 : Pure Player LAI
Source : MedinCell corporate news
- Profil : `corporate_pure_player_broad`
- Résultat : Ingère 95% du contenu (filtre uniquement RH/ESG)

### Cas 2 : Big Pharma
Source : Pfizer corporate news
- Profil : `corporate_hybrid_technology_focused`
- Résultat : Ingère 15% du contenu (uniquement news avec signaux LAI)

### Cas 3 : Presse Sectorielle
Source : FierceBiotech RSS
- Profil : `press_technology_focused`
- Résultat : Ingère 25% du contenu (articles mentionnant entreprises LAI + technologie)

---

**Version** : 1.0.0  
**Dernière mise à jour** : 2024-12-19  
**Prochaine étape** : Implémentation runtime dans les Lambdas