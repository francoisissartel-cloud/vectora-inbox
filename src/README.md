# Code source Vectora Inbox MVP

Ce répertoire contient le code Python pour Vectora Inbox MVP (newsletter LAI).

## Structure

```
src/
├── lambdas/                    # Points d'entrée AWS Lambda (très minces)
│   ├── ingest_normalize/       # Lambda pour ingestion + normalisation
│   │   └── handler.py
│   └── engine/                 # Lambda pour matching + scoring + newsletter
│       └── handler.py
│
└── vectora_core/               # Moteur métier réutilisable
    ├── config/                 # Chargement et résolution des configurations
    ├── ingestion/              # Récupération des contenus bruts (RSS, APIs)
    ├── normalization/          # Transformation en items structurés (avec Bedrock)
    ├── matching/               # Détermination des items pertinents par domaine
    ├── scoring/                # Calcul des scores de pertinence
    ├── newsletter/             # Assemblage de la newsletter finale (avec Bedrock)
    ├── storage/                # Lecture/écriture S3
    └── utils/                  # Utilitaires transverses (logging, dates)
```

## Différence entre `lambdas/` et `vectora_core/`

### `lambdas/` - Points d'entrée AWS très minces

Les modules dans `lambdas/` sont de simples points d'entrée AWS Lambda. Ils :
- Parsent l'événement d'entrée (JSON)
- Lisent les variables d'environnement
- Appellent les fonctions de haut niveau de `vectora_core/`
- Formatent la réponse (statusCode, body JSON)
- Gèrent les erreurs globales

**Ils ne contiennent AUCUNE logique métier.** Tout est délégué à `vectora_core/`.

### `vectora_core/` - Moteur métier réutilisable

Le package `vectora_core/` contient toute la logique métier de Vectora Inbox.
Il est :
- **Testable** : peut être testé unitairement sans simuler Lambda
- **Réutilisable** : peut être utilisé dans d'autres contextes (CLI, notebooks, tests)
- **Indépendant d'AWS Lambda** : séparation claire entre "plomberie AWS" et "logique métier"

## Les deux Lambdas principales

### 1. `vectora-inbox-ingest-normalize`

**Nom AWS de la fonction :**
- Défini dans `infra/s1-runtime.yaml` : `${ProjectName}-ingest-normalize-${Env}`
- Exemple en dev : `vectora-inbox-ingest-normalize-dev`

**Handler CloudFormation :**
- Propriété `Handler` dans S1-runtime.yaml : `"handler.lambda_handler"`
- AWS Lambda cherche `handler.py` à la racine du zip et appelle `lambda_handler(event, context)`

**Chemin du code Python :**
- Fichier source : `src/lambdas/ingest_normalize/handler.py`
- Fonction : `lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]`

**Rôle** : Ingestion et normalisation des contenus depuis les sources externes.

**Phases exécutées :**
- Phase 1A (Ingestion) : récupération des contenus bruts (RSS, APIs) sans Bedrock
- Phase 1B (Normalisation) : transformation en items structurés avec Bedrock

**Fonction de haut niveau appelée** : `vectora_core.run_ingest_normalize_for_client()`

**Variables d'environnement lues :**
- `ENV` : environnement (dev, stage, prod)
- `PROJECT_NAME` : nom du projet
- `CONFIG_BUCKET` : bucket S3 de configuration
- `DATA_BUCKET` : bucket S3 de données
- `BEDROCK_MODEL_ID` : modèle Bedrock pour normalisation
- `PUBMED_API_KEY_PARAM` : chemin SSM de la clé API PubMed
- `LOG_LEVEL` : niveau de log

### 2. `vectora-inbox-engine`

**Nom AWS de la fonction :**
- Défini dans `infra/s1-runtime.yaml` : `${ProjectName}-engine-${Env}`
- Exemple en dev : `vectora-inbox-engine-dev`

**Handler CloudFormation :**
- Propriété `Handler` dans S1-runtime.yaml : `"handler.lambda_handler"`
- AWS Lambda cherche `handler.py` à la racine du zip et appelle `lambda_handler(event, context)`

**Chemin du code Python :**
- Fichier source : `src/lambdas/engine/handler.py`
- Fonction : `lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]`

**Rôle** : Matching, scoring et génération de la newsletter finale.

**Phases exécutées :**
- Phase 2 (Matching) : détermination des items pertinents par watch_domain (sans Bedrock)
- Phase 3 (Scoring) : calcul des scores de pertinence (sans Bedrock)
- Phase 4 (Newsletter) : assemblage de la newsletter avec Bedrock

**Fonction de haut niveau appelée** : `vectora_core.run_engine_for_client()`

**Variables d'environnement lues :**
- `ENV` : environnement (dev, stage, prod)
- `PROJECT_NAME` : nom du projet
- `CONFIG_BUCKET` : bucket S3 de configuration
- `DATA_BUCKET` : bucket S3 de données
- `NEWSLETTERS_BUCKET` : bucket S3 de newsletters
- `BEDROCK_MODEL_ID` : modèle Bedrock pour génération éditoriale
- `LOG_LEVEL` : niveau de log

## Mapping entre infrastructure et code

Cette section explique comment les ressources AWS définies dans `infra/s1-runtime.yaml` sont câblées au code Python dans `src/`.

### Handlers Lambda : de CloudFormation au code Python

**Dans `infra/s1-runtime.yaml` :**
```yaml
IngestNormalizeFunction:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: !Sub "${ProjectName}-ingest-normalize-${Env}"
    Handler: "handler.lambda_handler"  # ← Chemin du handler
    # ...
```

**Signification du handler `"handler.lambda_handler"` :**
- AWS Lambda cherche un fichier `handler.py` à la racine du package zip
- Il appelle la fonction `lambda_handler(event, context)` dans ce fichier

**Dans le code Python (`src/lambdas/ingest_normalize/handler.py`) :**
```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Point d'entrée AWS Lambda pour vectora-inbox-ingest-normalize."""
    # Parser l'événement, lire les env vars, appeler vectora_core
    # ...
```

**Même logique pour la Lambda engine** : `handler.lambda_handler` → `src/lambdas/engine/handler.py`

### Variables d'environnement : de CloudFormation au code Python

**Dans `infra/s1-runtime.yaml` :**
```yaml
IngestNormalizeFunction:
  # ...
  Environment:
    Variables:
      ENV: !Ref Env
      CONFIG_BUCKET: !Ref ConfigBucketName
      DATA_BUCKET: !Ref DataBucketName
      BEDROCK_MODEL_ID: !Ref BedrockModelId
      # ...
```

**Dans le code Python (`src/lambdas/ingest_normalize/handler.py`) :**
```python
env_vars = {
    "ENV": os.environ.get("ENV", "dev"),
    "CONFIG_BUCKET": os.environ.get("CONFIG_BUCKET"),
    "DATA_BUCKET": os.environ.get("DATA_BUCKET"),
    "BEDROCK_MODEL_ID": os.environ.get("BEDROCK_MODEL_ID"),
    # ...
}
```

**Alignement parfait** : toutes les variables définies dans l'infra sont lues dans le code.

### Flux de données : de S3 aux Lambdas

**Lambda ingest-normalize :**
1. Lit depuis `CONFIG_BUCKET` : configurations canonical et client
2. Écrit dans `DATA_BUCKET` : items normalisés (`normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`)

**Lambda engine :**
1. Lit depuis `CONFIG_BUCKET` : configurations canonical et client
2. Lit depuis `DATA_BUCKET` : items normalisés
3. Écrit dans `NEWSLETTERS_BUCKET` : newsletter finale (`<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`)

**Cohérence avec l'architecture** : les buckets définis dans `infra/s0-core.yaml` sont référencés dans `infra/s1-runtime.yaml` et utilisés dans le code Python.

## État actuel : pipeline ingest-normalize implémenté

Le pipeline d'ingestion et de normalisation (`vectora-inbox-ingest-normalize`) est **implémenté et fonctionnel** :

**Modules implémentés :**
- `config.loader` : chargement des configurations depuis S3 (client, canonical, sources, scoring)
- `config.resolver` : résolution des bouquets de sources
- `storage.s3_client` : wrappers boto3 pour lire/écrire YAML et JSON dans S3
- `ingestion.fetcher` : récupération des contenus bruts via HTTP/RSS
- `ingestion.parser` : parsing des flux RSS en items bruts structurés
- `normalization.bedrock_client` : appels à Bedrock pour extraction d'entités et classification
- `normalization.entity_detector` : détection d'entités par règles (scopes canonical)
- `normalization.normalizer` : orchestration de la normalisation complète
- `utils.date_utils` : calcul des fenêtres temporelles

**Fonction principale implémentée :**
- `run_ingest_normalize_for_client()` : orchestration complète des Phases 1A et 1B

**À implémenter dans une étape suivante :**
- Pipeline engine (`vectora-inbox-engine`) : matching, scoring, génération de newsletter
- Modules `matching/`, `scoring/`, `newsletter/`

## Fonctions publiques principales

Les handlers Lambda appellent deux fonctions de haut niveau :

### `vectora_core.run_ingest_normalize_for_client()`

Orchestration de l'ingestion et de la normalisation pour un client.

**Paramètres** :
- `client_id` (str) : identifiant du client (ex: "lai_weekly")
- `sources` (list[str], optionnel) : liste de source_key à traiter
- `period_days` (int, optionnel) : nombre de jours à remonter
- `from_date` (str, optionnel) : date de début (ISO8601)
- `to_date` (str, optionnel) : date de fin (ISO8601)
- `env_vars` (dict, optionnel) : variables d'environnement

**Retourne** : Dict avec statistiques d'exécution (items ingérés, normalisés, etc.)

### `vectora_core.run_engine_for_client()`

Orchestration du moteur de newsletter pour un client.

**Paramètres** :
- `client_id` (str) : identifiant du client (ex: "lai_weekly")
- `period_days` (int, optionnel) : nombre de jours à analyser
- `from_date` (str, optionnel) : date de début (ISO8601)
- `to_date` (str, optionnel) : date de fin (ISO8601)
- `target_date` (str, optionnel) : date de référence pour la newsletter
- `env_vars` (dict, optionnel) : variables d'environnement

**Retourne** : Dict avec statistiques d'exécution (items analysés, sélectionnés, etc.)

## Dépendances

Voir `requirements.txt` à la racine du dépôt.

Dépendances minimales :
- `boto3` : SDK AWS (S3, Bedrock, SSM)
- `pyyaml` : parsing YAML (configurations)
- `requests` : appels HTTP (RSS, APIs)
- `feedparser` : parsing RSS/Atom
- `python-dateutil` : manipulation de dates

**Pas de dépendances lourdes** : pas de pandas, numpy, frameworks web.

## Prochaines étapes

1. Implémenter la logique métier dans les modules `vectora_core/`
2. Tester les fonctions unitairement
3. Packager le code pour déploiement Lambda
4. Déployer avec la stack S1-runtime

## Documentation de référence

- Architecture détaillée : `docs/architecture/src-architecture-proposal.md`
- Contrats métier des Lambdas : `contracts/lambdas/`
- Overview du projet : `.q-context/vectora-inbox-overview.md`
