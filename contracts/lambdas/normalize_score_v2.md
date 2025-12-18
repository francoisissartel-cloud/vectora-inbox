# Contrat métier Lambda : vectora-inbox-normalize-score V2

## 1. Rôle fonctionnel

La Lambda **vectora-inbox-normalize-score** est responsable de la **normalisation intelligente** des items bruts ingérés et de leur **scoring de pertinence** pour préparer la génération de newsletter.

**Responsabilités principales :**
- Normalisation des items via Bedrock (extraction d'entités, classification d'événements, résumés)
- Matching des items aux domaines de veille du client (technology, regulatory, etc.)
- Scoring de pertinence basé sur les règles métier et les scopes canonical
- Stockage des items normalisés et scorés dans S3 (`curated/` layer)
- Gestion des appels Bedrock avec retry et gestion d'erreurs

**Ce que cette Lambda NE fait PAS :**
- Ingestion des contenus bruts (délégué à ingest)
- Génération de newsletter ou contenu éditorial
- Envoi de notifications
- Stockage final des newsletters

## 2. Triggers

### Trigger principal : EventBridge (après ingest)
```json
{
  "source": ["vectora.inbox"],
  "detail-type": ["Ingestion Completed"],
  "detail": {
    "client_id": "lai_weekly",
    "ingestion_date": "2025-01-15",
    "items_count": 45
  }
}
```

### Trigger manuel : Invocation directe
```json
{
  "client_id": "lai_weekly",
  "period_days": 7,
  "from_date": "2025-01-01",
  "to_date": "2025-01-07"
}
```

### Trigger Step Functions (orchestration)
- Étape dans un workflow Step Functions
- Déclenchement automatique après succès de l'ingestion

## 3. Shape de l'event d'entrée

### Event minimal
```json
{
  "client_id": "lai_weekly"
}
```

### Event complet
```json
{
  "client_id": "lai_weekly",
  "period_days": 7,
  "from_date": "2025-01-01",
  "to_date": "2025-01-07",
  "target_date": "2025-01-15",
  "force_reprocess": false,
  "bedrock_model_override": "anthropic.claude-3-sonnet-20240229-v1:0",
  "scoring_mode": "balanced"
}
```

### Paramètres
- **`client_id`** (string, obligatoire) : Identifiant unique du client (ex: "lai_weekly")
- **`period_days`** (int, optionnel) : Nombre de jours à analyser. Surcharge la config client
- **`from_date`** (string, optionnel) : Date de début au format ISO8601 (YYYY-MM-DD)
- **`to_date`** (string, optionnel) : Date de fin au format ISO8601 (YYYY-MM-DD)
- **`target_date`** (string, optionnel) : Date de référence pour le scoring (défaut: aujourd'hui)
- **`force_reprocess`** (bool, optionnel) : Force le retraitement même si déjà fait (défaut: false)
- **`bedrock_model_override`** (string, optionnel) : Surcharge le modèle Bedrock configuré
- **`scoring_mode`** (string, optionnel) : Mode de scoring ("strict", "balanced", "broad")

## 4. Configurations lues

### Fichiers client_config
- **Chemin S3** : `s3://vectora-inbox-config/clients/{client_id}.yaml`
- **Contenu utilisé** :
  - `watch_domains[]` : Domaines de veille avec scopes associés (technology_scope, company_scope, etc.)
  - `matching_config` : Règles de matching (require_entity_signals, min_technology_signals, trademark_privileges)
  - `scoring_config` : Poids par type d'événement, bonus spécifiques, seuils de sélection
  - `pipeline.default_period_days` : Fenêtre temporelle par défaut

### Fichiers canonical
- **`canonical/scopes/company_scopes.yaml`** :
  - Listes d'entreprises par verticale (ex: `lai_companies_global`, `lai_companies_mvp_core`)
- **`canonical/scopes/molecule_scopes.yaml`** :
  - Listes de molécules par indication (ex: `lai_molecules_global`, `lai_molecules_addiction`)
- **`canonical/scopes/technology_scopes.yaml`** :
  - Mots-clés technologiques (ex: `lai_keywords`, `lai_delivery_systems`)
- **`canonical/scopes/trademark_scopes.yaml`** :
  - Noms de marque commerciaux (ex: `lai_trademarks_global`)
- **`canonical/scopes/exclusion_scopes.yaml`** :
  - Termes d'exclusion pour filtrer le bruit (ex: `lai_exclude_noise`)
- **`canonical/scoring/scoring_rules.yaml`** :
  - Poids par type d'événement, facteurs de recency, règles de bonus
- **`canonical/matching/domain_matching_rules.yaml`** :
  - Règles de matching par type de domaine
- **`canonical/prompts/global_prompts.yaml`** :
  - Prompts Bedrock pour normalisation et classification

## 5. Données écrites

### S3 Curated Layer (principal)
- **Chemin** : `s3://vectora-inbox-data/curated/{client_id}/{YYYY}/{MM}/{DD}/items.json`
- **Format** : JSON array des items normalisés et scorés
- **Exemple** :
```json
[
  {
    "item_id": "press_corporate__medincell_20250115_001",
    "source_key": "press_corporate__medincell",
    "source_type": "rss",
    "title": "MedinCell Announces Partnership with Teva for BEPO Technology",
    "content": "MedinCell (Euronext: MEDCL) today announced...",
    "url": "https://www.medincell.com/news/partnership-teva-bepo/",
    "published_at": "2025-01-15",
    "normalized_at": "2025-01-15T11:45:00Z",
    
    "normalized_content": {
      "summary": "MedinCell partners with Teva to develop long-acting injectable formulations using BEPO technology platform...",
      "entities": {
        "companies": ["MedinCell", "Teva Pharmaceutical"],
        "molecules": ["buprenorphine", "naloxone"],
        "technologies": ["BEPO", "long-acting injection", "subcutaneous delivery"],
        "trademarks": ["Suboxone"]
      },
      "event_classification": {
        "primary_type": "partnership",
        "secondary_types": ["technology_licensing", "product_development"],
        "confidence": 0.92
      },
      "language": "en",
      "sentiment": "positive"
    },
    
    "matching_results": {
      "matched_domains": ["tech_lai_ecosystem"],
      "domain_relevance": {
        "tech_lai_ecosystem": {
          "score": 0.89,
          "reasons": ["company_match", "technology_match", "trademark_match"],
          "entity_matches": {
            "companies": ["MedinCell"],
            "technologies": ["BEPO", "long-acting injection"],
            "trademarks": ["Suboxone"]
          }
        }
      },
      "exclusion_applied": false
    },
    
    "scoring_results": {
      "base_score": 8.5,
      "bonuses": {
        "pure_player_company": 5.0,
        "trademark_mention": 4.0,
        "partnership_event": 3.0
      },
      "penalties": {
        "age_penalty": -0.5
      },
      "final_score": 20.0,
      "score_breakdown": {
        "event_type_weight": 8.0,
        "domain_relevance": 0.89,
        "recency_factor": 0.95,
        "entity_bonus": 9.0,
        "total_bonus": 12.0,
        "total_penalty": -0.5
      }
    },
    
    "metadata": {
      "processing_version": "2.0.0",
      "bedrock_model": "anthropic.claude-3-sonnet-20240229-v1:0",
      "processing_time_ms": 1250,
      "quality_flags": ["high_confidence", "trademark_detected"]
    }
  }
]
```

### S3 Processing Logs (debug)
- **Chemin** : `s3://vectora-inbox-data/logs/{client_id}/{YYYY}/{MM}/{DD}/normalize_score.json`
- **Format** : Logs détaillés du traitement
- **Contenu** : Statistiques Bedrock, erreurs, temps de traitement

## 6. Workflow métier

1. **Validation de l'event** : Vérifier que `client_id` est fourni et valide
2. **Chargement des configurations** : Lire la config client et tous les scopes canonical depuis S3
3. **Collecte des items bruts** : Récupérer les items ingérés depuis S3 sur la fenêtre temporelle
4. **Filtrage d'exclusion** : Appliquer les scopes d'exclusion pour éliminer le bruit
5. **Normalisation Bedrock** : Pour chaque item, appeler Bedrock pour extraction d'entités, classification d'événements et résumé
6. **Matching aux domaines** : Déterminer quels watch_domains correspondent à chaque item basé sur les entités détectées
7. **Scoring de pertinence** : Calculer le score final basé sur les règles métier, bonus et pénalités
8. **Tri et sélection** : Trier les items par score et appliquer les seuils de sélection
9. **Écriture S3** : Stocker les items normalisés et scorés dans le data bucket
10. **Retour des statistiques** : Nombre d'items traités, scores moyens, temps de traitement Bedrock

## 7. Sources des spécifications

### Du blueprint (vision cible)
- **Bedrock comme "cerveau linguistique"** : Extraction d'entités, classification d'événements, résumés
- **Pas d'appel Bedrock pour** : Matching (intersections d'ensembles), scoring (règles numériques)
- **Stockage en layers** : curated/ pour les items normalisés et scorés
- **Modèle par défaut** : Claude Sonnet 4.5 via profil d'inférence EU

### Du code existant (observé dans /src)
- **Fonction orchestratrice** : `run_ingest_normalize_for_client()` dans `vectora_core` (actuellement combine ingest + normalize)
- **Modules vectora_core** : `normalization/normalizer.py`, `matching/matcher.py`, `scoring/scorer.py`
- **Variables d'environnement** : `BEDROCK_MODEL_ID`, `BEDROCK_REGION_NORMALIZATION`
- **Structure des items normalisés** : `normalized_content`, `matching_results`, `scoring_results`
- **Gestion des domaines** : `watch_domains` avec `technology_scope`, `company_scope`, etc.

### Des données canonical existantes
- **Scopes LAI** : 180+ entreprises, 90+ molécules, 80+ mots-clés technologiques, 70+ trademarks
- **Règles de scoring** : Poids par type d'événement, bonus pure players (5.0), bonus trademarks (4.0)
- **Règles de matching** : `trademark_privileges` avec boost_factor 2.5, `require_entity_signals`
- **Prompts Bedrock** : Templates pour normalisation dans `canonical/prompts/global_prompts.yaml`
- **Config client LAI** : `lai_weekly_v3.yaml` avec 2 domaines (tech_lai_ecosystem, regulatory_lai)

---

**Note** : Ce contrat sépare clairement la normalisation/scoring de l'ingestion brute et de la génération de newsletter, respectant l'architecture 3 Lambdas de `src_lambda_hygiene_v3.md`. La logique métier complexe reste dans `vectora_core` pour réutilisabilité.