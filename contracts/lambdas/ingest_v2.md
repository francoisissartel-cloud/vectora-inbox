# Contrat métier Lambda : vectora-inbox-ingest V2

## 1. Rôle fonctionnel

La Lambda **vectora-inbox-ingest** est responsable de l'**ingestion brute** des contenus depuis les sources externes (RSS, APIs, sites web) et de leur **stockage dans S3** pour traitement ultérieur.

**Responsabilités principales :**
- Récupération des contenus bruts depuis les sources configurées (flux RSS, APIs REST, scraping HTML)
- Parsing initial des contenus en items structurés
- Stockage des données brutes dans S3 (`raw/` layer)
- Gestion des erreurs de récupération et retry automatique
- Respect des limites de débit (rate limiting) par source

**Ce que cette Lambda NE fait PAS :**
- Normalisation des contenus (délégué à normalize-score)
- Matching ou scoring des items
- Génération de newsletter
- Appels à Bedrock (IA)

## 2. Triggers

### Trigger principal : EventBridge (Scheduled)
```json
{
  "source": ["aws.events"],
  "detail-type": ["Scheduled Event"],
  "detail": {
    "rule-name": "vectora-inbox-ingest-daily"
  }
}
```

### Trigger manuel : Invocation directe
```json
{
  "client_id": "lai_weekly",
  "sources": ["press_corporate__medincell", "press_sector__fiercebiotech"],
  "period_days": 7,
  "from_date": "2025-01-01",
  "to_date": "2025-01-07"
}
```

### Trigger API Gateway (futur)
- Endpoint REST pour déclencher l'ingestion à la demande
- Authentification via API Key

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
  "sources": [
    "press_corporate__medincell",
    "press_corporate__camurus",
    "press_sector__fiercebiotech"
  ],
  "period_days": 7,
  "from_date": "2025-01-01",
  "to_date": "2025-01-07",
  "force_refresh": false,
  "dry_run": false
}
```

### Paramètres
- **`client_id`** (string, obligatoire) : Identifiant unique du client (ex: "lai_weekly")
- **`sources`** (array[string], optionnel) : Liste des source_key à traiter. Si absent, utilise toutes les sources configurées pour le client
- **`period_days`** (int, optionnel) : Nombre de jours à remonter dans le passé. Surcharge la config client
- **`from_date`** (string, optionnel) : Date de début au format ISO8601 (YYYY-MM-DD)
- **`to_date`** (string, optionnel) : Date de fin au format ISO8601 (YYYY-MM-DD)
- **`force_refresh`** (bool, optionnel) : Force la re-ingestion même si déjà fait (défaut: false)
- **`dry_run`** (bool, optionnel) : Mode simulation sans écriture S3 (défaut: false)

## 4. Configurations lues

### Fichiers client_config
- **Chemin S3** : `s3://vectora-inbox-config/clients/{client_id}.yaml`
- **Contenu utilisé** :
  - `source_config.source_bouquets_enabled` : Liste des bouquets de sources à activer
  - `source_config.sources_extra_enabled` : Sources supplémentaires individuelles
  - `pipeline.default_period_days` : Fenêtre temporelle par défaut
  - `source_config.bouquet_ingestion_overrides` : Surcharges de paramètres d'ingestion

### Fichiers canonical
- **`canonical/sources/source_catalog.yaml`** :
  - Section `sources:` : Définitions complètes des sources (URL, type, headers, parsing rules)
  - Section `bouquets:` : Groupes de sources prédéfinis
- **`canonical/ingestion/ingestion_profiles.yaml`** :
  - Profils de récupération (timeout, retry, rate limiting)
  - Règles de parsing par type de source (RSS, HTML, API)

## 5. Données écrites

### S3 Raw Layer (optionnel, debug)
- **Chemin** : `s3://vectora-inbox-data/raw/{client_id}/{source_key}/{YYYY}/{MM}/{DD}/raw.json`
- **Format** : JSON array des contenus bruts par source
- **Exemple** :
```json
[
  {
    "source_key": "press_corporate__medincell",
    "source_type": "rss",
    "url": "https://www.medincell.com/feed/",
    "fetched_at": "2025-01-15T10:30:00Z",
    "raw_content": "<rss>...</rss>",
    "http_status": 200,
    "content_type": "application/rss+xml"
  }
]
```

### S3 Parsed Items (principal)
- **Chemin** : `s3://vectora-inbox-data/ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json`
- **Format** : JSON array des items parsés
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
    "ingested_at": "2025-01-15T10:30:00Z",
    "language": "en",
    "content_hash": "sha256:abc123...",
    "metadata": {
      "author": "MedinCell Press Team",
      "tags": ["partnership", "BEPO", "Teva"],
      "word_count": 450
    }
  }
]
```

## 6. Workflow métier

1. **Validation de l'event** : Vérifier que `client_id` est fourni et valide
2. **Chargement des configurations** : Lire la config client et les catalogues canonical depuis S3
3. **Résolution des sources** : Développer les bouquets en liste de sources individuelles, appliquer les filtres `sources` si fournis
4. **Calcul de la fenêtre temporelle** : Résoudre `period_days` selon la hiérarchie (event > client_config > défaut)
5. **Ingestion par source** : Pour chaque source, récupérer le contenu brut (HTTP GET, parsing RSS/HTML)
6. **Parsing des contenus** : Transformer les contenus bruts en items structurés selon les règles de parsing
7. **Filtrage temporel** : Éliminer les items antérieurs à la fenêtre temporelle
8. **Déduplication** : Éviter les doublons basés sur `content_hash` ou URL
9. **Écriture S3** : Stocker les items parsés dans le data bucket
10. **Retour des statistiques** : Nombre de sources traitées, items ingérés, erreurs rencontrées

## 7. Sources des spécifications

### Du blueprint (vision cible)
- **Architecture 3 Lambdas séparées** : ingest, normalize-score, newsletter
- **Stockage S3 en layers** : raw/, ingested/, normalized/, outbox/
- **Pas d'appel Bedrock** dans l'ingestion (réservé à la normalisation)
- **Gestion des bouquets de sources** via canonical

### Du code existant (observé dans /src)
- **Handler pattern** : `lambda_handler(event, context)` dans `/src/lambdas/ingest_normalize/handler.py`
- **Fonction orchestratrice** : `run_ingest_normalize_for_client()` dans `vectora_core`
- **Variables d'environnement** : `CONFIG_BUCKET`, `DATA_BUCKET`, `PUBMED_API_KEY_PARAM`
- **Structure des events** : `client_id`, `sources`, `period_days`, `from_date`, `to_date`
- **Gestion des erreurs** : Try/catch avec retour `statusCode` + `body`

### Des données canonical existantes
- **Source catalog** : 180+ sources corporate LAI + presse sectorielle dans `canonical/sources/source_catalog.yaml`
- **Bouquets prédéfinis** : `lai_corporate_mvp`, `lai_corporate_all`, `press_biotech_premium`
- **Profils d'ingestion** : Timeout, retry, rate limiting dans `canonical/ingestion/ingestion_profiles.yaml`
- **Client configs** : Structure des configs dans `client-config-examples/lai_weekly_v3.yaml`

---

**Note** : Ce contrat respecte l'esprit de `src_lambda_hygiene_v3.md` avec une Lambda simple et focalisée sur l'ingestion brute, sans logique métier complexe. La normalisation et le scoring sont délégués aux Lambdas suivantes.