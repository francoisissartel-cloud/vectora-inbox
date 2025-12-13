# Contrat métier – Lambda `vectora-inbox-ingest-normalize` (Version Mise à Jour)

---

# 1. Rôle et objectif de la Lambda

La Lambda `vectora-inbox-ingest-normalize` est responsable des **Phases 1A, 1A-bis et 1B** du workflow Vectora Inbox.

Elle gère :
- l'**ingestion des sources externes** (flux RSS, APIs publiques) - Phase 1A
- le **pré-filtrage avec profils d'ingestion** pour optimiser les coûts Bedrock - Phase 1A-bis (NOUVEAU)
- la **normalisation open-world** avec Amazon Bedrock - Phase 1B (AMÉLIORÉ)

Cette Lambda **ne fait pas** :
- de matching avec les domaines d'intérêt (watch_domains),
- de scoring des items,
- de génération de newsletter,
- d'envoi d'e-mails.

Son rôle est de transformer des contenus hétérogènes (RSS, JSON d'APIs) en un format unifié et enrichi avec **normalisation open-world**, stocké dans S3, pour qu'un client donné puisse ensuite les analyser et les filtrer.

---

# 2. Contexte dans le workflow Vectora Inbox

La Lambda `vectora-inbox-ingest-normalize` intervient en **Phase 1**, qui se décompose maintenant en trois sous-phases :

- **Phase 1A – Ingestion** : récupération des données brutes depuis les sources externes (sans IA).
- **Phase 1A-bis – Profile Filtering** : pré-filtrage avec profils d'ingestion pour réduire les coûts Bedrock (NOUVEAU).
- **Phase 1B – Normalisation Open-World** : enrichissement et structuration des items avec Amazon Bedrock (AMÉLIORÉ).

## Nouveautés par rapport à la version précédente

### Profils d'Ingestion (Phase 1A-bis)
- **Objectif** : Réduire les coûts Bedrock de 60-80% en pré-filtrant le bruit évident
- **Stratégies** : 
  - `broad_ingestion` pour pure players (95% rétention)
  - `signal_based_ingestion` pour hybrid companies (15% rétention)
  - `multi_signal_ingestion` pour presse sectorielle (25% rétention)
- **Configuration** : Profils définis dans `canonical/ingestion/ingestion_profiles.yaml`

### Normalisation Open-World (Phase 1B)
- **Objectif** : Capturer toutes les entités (connues et inconnues) sans perte d'information
- **Approche** : Double couche `*_detected` (tout) vs `*_in_scopes` (canonical seulement)
- **Bénéfices** : Expansion des scopes, contrôle qualité, future-proofing

---

# 3. Phase 1A-bis – Profile Filtering (NOUVEAU)

## Objectif

Appliquer des profils d'ingestion pour pré-filtrer le contenu avant la normalisation Bedrock coûteuse.

## Processus

1. **Charger les profils d'ingestion** depuis `canonical/ingestion/ingestion_profiles.yaml`

2. **Pour chaque item brut** :
   - Déterminer le profil applicable basé sur `source_key` et `source_type`
   - Appliquer la logique de filtrage selon la stratégie du profil
   - Décider : ingérer ou filtrer

3. **Stratégies de profils** :

### `broad_ingestion` (Pure Players)
```yaml
corporate_pure_player_broad:
  strategy: "broad_ingestion"
  signal_requirements:
    mode: "exclude_only"
    exclusion_scopes:
      - "exclusion_scopes.hr_content"
      - "exclusion_scopes.esg_generic"
      - "exclusion_scopes.financial_generic"
```
- **Usage** : MedinCell, Camurus, DelSiTech, Nanexa, Peptron
- **Logique** : Ingère tout sauf exclusions explicites
- **Rétention** : ~95%

### `signal_based_ingestion` (Hybrid Companies)
```yaml
corporate_hybrid_technology_focused:
  strategy: "signal_based_ingestion"
  signal_requirements:
    mode: "require_signals"
    required_signal_groups:
      - group_id: "technology_signals_high_precision"
        scopes: ["lai_keywords.core_phrases", "lai_keywords.technology_terms_high_precision"]
        min_matches: 1
        weight: 3.0
    combination_logic: "technology_signals_high_precision"
    minimum_total_weight: 2.0
```
- **Usage** : AbbVie, Pfizer, Sanofi, etc.
- **Logique** : Ingère seulement si signaux technologiques LAI détectés
- **Rétention** : ~15%

### `multi_signal_ingestion` (Sector Press)
```yaml
press_technology_focused:
  strategy: "multi_signal_ingestion"
  signal_requirements:
    mode: "require_multi_signals"
    required_signal_groups:
      - group_id: "entity_signals"
        scopes: ["lai_companies_global", "lai_molecules_global"]
        min_matches: 1
        weight: 2.0
      - group_id: "technology_signals"
        scopes: ["lai_keywords.core_phrases", "lai_keywords.technology_terms_high_precision"]
        min_matches: 1
        weight: 2.0
    combination_logic: "entity_signals AND technology_signals"
    minimum_total_weight: 3.0
```
- **Usage** : FierceBiotech, FiercePharma, Endpoints News
- **Logique** : Ingère si entités LAI + signaux technologiques
- **Rétention** : ~25%

## Métriques de Filtrage

La Lambda doit tracker et retourner :
- `items_scraped` : Total items récupérés
- `items_filtered_out` : Items éliminés par profils
- `items_retained_for_normalization` : Items gardés pour Bedrock
- `filtering_retention_rate` : Taux de rétention global
- `filtering_metrics_by_source` : Détail par source

---

# 4. Phase 1B – Normalisation Open-World (AMÉLIORÉ)

## Objectif

Transformer chaque item filtré en **item normalisé open-world** avec détection complète des entités.

## Approche Open-World

### Principe
1. **Détection Open-World** : Bedrock détecte TOUTES les entités mentionnées
2. **Intersection Canonical** : Système identifie lesquelles existent dans nos scopes

### Schéma Open-World
```json
{
  // OPEN-WORLD: Toutes les entités détectées par Bedrock
  "companies_detected": ["Camurus", "Unknown Biotech Partner"],
  "molecules_detected": ["buprenorphine", "novel_compound_X"],
  "trademarks_detected": ["Brixadi", "Sublocade"],
  "technologies_detected": ["long acting", "depot", "nanotechnology"],
  "indications_detected": ["opioid use disorder", "addiction"],
  
  // CANONICAL INTERSECTION: Seulement les entités dans nos scopes
  "companies_in_scopes": ["Camurus"],
  "molecules_in_scopes": ["buprenorphine"],
  "trademarks_in_scopes": ["Brixadi"],
  "technologies_in_scopes": ["long acting"],
  "indications_in_scopes": ["opioid use disorder"]
}
```

### Séparation Molecules vs Trademarks
- **`molecules_detected`** : Substances actives (buprenorphine, olanzapine)
- **`trademarks_detected`** : Noms commerciaux (Brixadi, Zyprexa)
- **Scopes séparés** : `molecule_scopes.yaml` vs `trademark_scopes.yaml`

## Contrat métier avec Bedrock (normalisation open-world)

### Ce que la Lambda envoie à Bedrock

Un prompt enrichi contenant :
- **Le texte de l'item** (titre + description)
- **Exemples canonical** (50 companies, 30 molecules, 20 technologies)
- **Instructions open-world** :
  - Détecter TOUTES les entités sans contrainte de scope
  - Séparer molecules (substances) et trademarks (noms commerciaux)
  - Classifier l'événement parmi les types prédéfinis
  - Générer résumé dans la langue client
  - Ne pas halluciner, préserver les noms exacts

### Ce que la Lambda attend en retour de Bedrock

```json
{
  "summary": "Résumé factuel en langue client",
  "event_type": "clinical_update",
  "companies_detected": ["Camurus", "Partner Company"],
  "molecules_detected": ["buprenorphine", "compound_123"],
  "trademarks_detected": ["Brixadi", "ProductX"],
  "technologies_detected": ["long acting", "depot", "novel_delivery"],
  "indications_detected": ["opioid use disorder", "rare_disease"]
}
```

## Post-traitement : Intersection Canonical

Après réception de Bedrock, la Lambda :

1. **Charge les scopes canonical** via les clés de la config client
2. **Calcule les intersections** :
   ```python
   companies_in_scopes = set(companies_detected) & set(canonical_companies)
   molecules_in_scopes = set(molecules_detected) & set(canonical_molecules)
   # etc.
   ```
3. **Préserve les entités open-world** pour analyse future
4. **Génère l'item normalisé complet**

---

# 5. Schéma de l'item normalisé open-world

```json
{
  "source_key": "press_corporate__camurus",
  "source_type": "press_corporate",
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "summary": "Camurus reported positive results from Phase 3 trial...",
  "url": "https://example.com/article",
  "date": "2025-01-15",
  
  // OPEN-WORLD: All entities detected by Bedrock
  "companies_detected": ["Camurus", "Unknown Biotech Partner"],
  "molecules_detected": ["buprenorphine", "novel_compound_X"],
  "trademarks_detected": ["Brixadi", "Sublocade"],
  "technologies_detected": ["long acting", "depot", "nanotechnology"],
  "indications_detected": ["opioid use disorder", "addiction"],
  
  // CANONICAL INTERSECTION: Only entities in our scopes
  "companies_in_scopes": ["Camurus"],
  "molecules_in_scopes": ["buprenorphine"],
  "trademarks_in_scopes": ["Brixadi"],
  "technologies_in_scopes": ["long acting"],
  "indications_in_scopes": ["opioid use disorder"],
  
  "event_type": "clinical_update"
}
```

---

# 6. Gestion des erreurs et résilience

## Erreurs de profils d'ingestion
- **Profil manquant** : Utiliser `default_broad` (ingère tout)
- **Scope référencé inexistant** : Log erreur, continuer avec profil dégradé
- **Erreur de parsing des règles** : Fallback vers ingestion sans filtrage

## Erreurs Bedrock
- **Rate limiting** : Retry avec backoff exponentiel (3 tentatives)
- **Erreur de modèle** : Fallback vers normalisation rule-based basique
- **Timeout** : Marquer item comme `normalization_status: "timeout"`

## Monitoring et métriques
- Taux de rétention par profil d'ingestion
- Coûts Bedrock économisés
- Taux de succès normalisation open-world
- Entités détectées hors scopes (pour expansion)

---

# 7. Exemples d'événements (JSON)

## 7.1 Exemple de sortie réussie avec profils d'ingestion

```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T10:30:00Z",
    "sources_processed": 27,
    "items_scraped": 1247,
    "items_filtered_out": 1009,
    "items_retained_for_normalization": 238,
    "items_normalized": 235,
    "filtering_retention_rate": 0.19,
    "filtering_metrics_by_source": {
      "press_corporate__medincell": {
        "scraped": 45,
        "filtered_out": 2,
        "retained": 43,
        "retention_rate": 0.96
      },
      "press_corporate__abbvie": {
        "scraped": 156,
        "filtered_out": 132,
        "retained": 24,
        "retention_rate": 0.15
      },
      "press_sector__fiercebiotech": {
        "scraped": 89,
        "filtered_out": 67,
        "retained": 22,
        "retention_rate": 0.25
      }
    },
    "bedrock_costs_saved_estimate": "$42.30",
    "s3_output_path": "s3://vectora-inbox-data/normalized/lai_weekly/2025/01/15/items.json",
    "execution_time_seconds": 38.7,
    "message": "Ingestion avec profils + normalisation open-world terminées avec succès."
  }
}
```

## 7.2 Exemple d'item normalisé open-world

```json
{
  "source_key": "press_corporate__camurus",
  "source_type": "press_corporate",
  "title": "Camurus Receives FDA Approval for UZEDY (risperidone) Extended-Release Injectable",
  "summary": "Camurus announced FDA approval of UZEDY, a once-monthly extended-release injectable formulation of risperidone for schizophrenia treatment, representing a significant milestone for the company's LAI portfolio.",
  "url": "https://camurus.com/news/fda-approval-uzedy",
  "date": "2025-01-15",
  
  "companies_detected": ["Camurus", "FDA"],
  "molecules_detected": ["risperidone"],
  "trademarks_detected": ["UZEDY"],
  "technologies_detected": ["extended-release injectable", "once-monthly", "long-acting"],
  "indications_detected": ["schizophrenia"],
  
  "companies_in_scopes": ["Camurus"],
  "molecules_in_scopes": ["risperidone"],
  "trademarks_in_scopes": ["UZEDY"],
  "technologies_in_scopes": ["extended-release injectable", "long-acting"],
  "indications_in_scopes": ["schizophrenia"],
  
  "event_type": "regulatory"
}
```

---

**Fin du contrat métier mis à jour pour `vectora-inbox-ingest-normalize`.**

Cette version intègre les profils d'ingestion et la normalisation open-world pour optimiser les coûts et améliorer la capture d'information.