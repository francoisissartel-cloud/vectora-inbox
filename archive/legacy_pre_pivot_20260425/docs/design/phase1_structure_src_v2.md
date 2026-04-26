# Phase 1 – Design de la structure /src_v2 : TERMINÉE ✅

## Structure créée

```
/src_v2/
├── lambdas/
│   └── ingest/
│       └── handler.py              # Handler Lambda avec orchestration minimale
└── vectora_core/
    ├── __init__.py                 # Fonction orchestratrice run_ingest_for_client()
    ├── config_loader.py            # Chargement configurations S3
    ├── s3_io.py                    # Opérations lecture/écriture S3
    ├── source_fetcher.py           # Récupération contenus HTTP/RSS/API
    ├── content_parser.py           # Parsing contenus en items structurés
    ├── models.py                   # Classes Item, Source, ClientConfig, IngestionResult
    └── utils.py                    # Utilitaires dates, hashes, validation
```

## Interfaces définies

### Handler Lambda (`lambdas/ingest/handler.py`)

**Responsabilités :**
- Validation event d'entrée (client_id obligatoire)
- Lecture variables d'environnement (CONFIG_BUCKET, DATA_BUCKET)
- Appel fonction orchestratrice `run_ingest_for_client()`
- Formatage réponse standardisée (statusCode + body)
- Gestion erreurs globales

**Variables d'environnement requises :**
- `ENV` : Environnement (dev/prod)
- `PROJECT_NAME` : Nom du projet
- `CONFIG_BUCKET` : Bucket de configuration S3
- `DATA_BUCKET` : Bucket de données S3
- `LOG_LEVEL` : Niveau de logging

### Fonction orchestratrice (`vectora_core/__init__.py`)

**Signature :**
```python
def run_ingest_for_client(
    client_id: str,
    sources: Optional[List[str]] = None,
    period_days: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    force_refresh: bool = False,
    dry_run: bool = False,
    env_vars: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

**Workflow prévu :**
1. Charger configurations (config_loader)
2. Résoudre sources (config_loader)
3. Calculer fenêtre temporelle (utils)
4. Ingestion par source (source_fetcher)
5. Parsing contenus (content_parser)
6. Filtrage temporel (utils)
7. Déduplication (utils)
8. Écriture S3 (s3_io)

### Modules vectora_core

#### config_loader.py
- `load_client_config()` : Charge config client depuis S3
- `load_source_catalog()` : Charge catalogue sources canonical
- `load_ingestion_profiles()` : Charge profils d'ingestion
- `resolve_sources_for_client()` : Développe bouquets en sources
- `resolve_period_days()` : Résout period_days selon hiérarchie

#### s3_io.py
- `read_json_from_s3()` / `read_yaml_from_s3()` : Lecture fichiers S3
- `write_json_to_s3()` / `write_text_to_s3()` : Écriture fichiers S3
- `build_s3_key_for_ingested_items()` : Construction clés S3 selon conventions
- `build_s3_key_for_raw_content()` : Construction clés S3 pour debug

#### source_fetcher.py
- `fetch_source_content()` : Récupération contenu selon type source
- `_fetch_rss_content()` : Récupération flux RSS
- `_fetch_html_content()` : Récupération pages HTML
- `_fetch_api_content()` : Récupération APIs REST
- `apply_rate_limiting()` : Gestion limites de débit

#### content_parser.py
- `parse_source_content()` : Parsing contenu selon type
- `_parse_rss_content()` : Parsing flux RSS en items
- `_parse_html_content()` : Parsing HTML en items
- `_parse_api_content()` : Parsing API JSON en items
- `generate_item_id()` : Génération identifiants uniques
- `calculate_content_hash()` : Calcul hashes déduplication
- `detect_language()` : Détection langue contenu

#### models.py
- `Item` : Dataclass pour items ingérés
- `Source` : Dataclass pour sources avec métadonnées
- `ClientConfig` : Dataclass pour configuration client
- `IngestionResult` : Dataclass pour résultats d'ingestion

#### utils.py
- `get_current_date_iso()` / `get_current_datetime_iso()` : Gestion dates
- `compute_date_range()` : Calcul fenêtres temporelles
- `apply_temporal_filter()` : Filtrage items par date
- `deduplicate_items()` : Déduplication par content_hash
- `validate_item()` / `validate_source()` : Validation données
- `safe_get_nested()` : Navigation dictionnaires imbriqués

## Conformité aux règles d'hygiène V4

### ✅ RESPECT DES INTERDICTIONS

1. **Aucune dépendance tierce copiée** dans `/src_v2`
2. **Aucun stub ou contournement** créé
3. **Aucun package monolithique** dans lambdas/
4. **Structure modulaire claire** avec séparation handler/core
5. **Taille handler < 5MB** (code source uniquement)

### ✅ PILOTAGE PAR CONFIGURATION

1. **Aucune logique métier hardcodée** dans le code
2. **Configuration via client_config et canonical** uniquement
3. **Variables d'environnement** pour paramètres infrastructure
4. **Résolution hiérarchique** des paramètres (event > config > défaut)

### ✅ PRÉPARATION LAMBDA LAYERS

1. **vectora_core séparé** du handler
2. **Interfaces bien définies** entre modules
3. **Aucune dépendance circulaire**
4. **Structure réutilisable** par futures Lambdas V2

## Format de sortie S3

### Chemin de sortie
`s3://vectora-inbox-data-dev/ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json`

### Structure des items
```json
[
  {
    "item_id": "press_corporate__medincell_20250115_001",
    "source_key": "press_corporate__medincell",
    "source_type": "rss",
    "title": "Article title...",
    "content": "Full article content...",
    "url": "https://source.com/article",
    "published_at": "2025-01-15",
    "ingested_at": "2025-01-15T10:30:00Z",
    "language": "en",
    "content_hash": "sha256:abc123...",
    "metadata": {
      "author": "Author name",
      "tags": ["tag1", "tag2"],
      "word_count": 450
    }
  }
]
```

## Compatibilité avec V1

### ✅ RÉUTILISATION MAXIMALE
- **Format d'event identique** à V1
- **Variables d'environnement compatibles** (sauf BEDROCK_MODEL_ID)
- **Configurations existantes utilisables** (lai_weekly_v3.yaml)
- **Conventions S3 respectées**

### ✅ SIMPLIFICATION V2
- **Pas d'appels Bedrock** (délégué à normalize-score V2)
- **Sortie S3 simplifiée** (ingested/ au lieu de normalized/)
- **Workflow réduit** (Phase 1A uniquement)

## État actuel : Squelettes fonctionnels

Tous les modules contiennent :
- **Signatures de fonctions complètes** avec documentation
- **Imports et structure de base** préparés
- **Logging approprié** configuré
- **Squelettes temporaires** pour validation de l'architecture
- **TODO Phase 2** pour l'implémentation complète

## Critères de succès Phase 1

- [x] Structure `/src_v2` créée et conforme aux règles V4
- [x] Squelettes de tous les modules créés avec interfaces définies
- [x] Handler Lambda avec orchestration minimale
- [x] Fonction orchestratrice avec workflow documenté
- [x] Modèles de données avec validation
- [x] Utilitaires transverses préparés
- [x] Aucune violation des règles d'hygiène V4
- [x] Préparation Lambda Layers (structure séparée)
- [x] Compatibilité avec configurations existantes

## Prochaine étape

**Phase 2 – Implémentation du code de la Lambda** :
- Remplacer tous les squelettes par l'implémentation complète
- Intégrer avec boto3 pour les opérations S3
- Implémenter le parsing RSS/HTML avec les libs appropriées
- Ajouter la gestion d'erreurs robuste et retry automatique
- Tester chaque module individuellement

La Phase 1 est **TERMINÉE** avec succès. Structure propre et modulaire prête pour l'implémentation.