# Vectora Inbox – Règles d'hygiène /src et Lambdas (V4)

## 1. Objectifs

- Garder un moteur **simple, générique, évolutif**.
- Éviter les "usines à gaz" : code métier noyé dans des scripts de build, des hacks de dépendances, etc.
- Permettre à Amazon Q Developer de travailler **en sécurité** :
  - petits changements,
  - architecture stable,
  - packaging prévisible.
- **NOUVEAU V3** : Éviter la pollution massive par dépendances tierces observée dans le repository.
- **NOUVEAU V4** : Alignement strict sur l'environnement AWS de référence et les conventions établies.

---

### 1.1 Vision métier du moteur Vectora Inbox

- Le moteur est un **orchestrateur générique** :
  - aucune logique spécifique à un client ne doit être "hardcodée" dans le code.
  - le comportement par client est piloté par des fichiers **client_config** et par le **canonical** Vectora.
- Les 3 Lambdas métier principales sont stables :
  - `vectora-inbox-ingest` : ingestion brute vers S3 `raw/`.
  - `vectora-inbox-normalize-score` : normalisation, matching, scoring vers S3 `curated/`.
  - `vectora-inbox-newsletter` : agrégation + génération de newsletter vers S3 `outbox/`.
- Toute évolution future doit respecter ce schéma à 3 Lambdas :
  - pas de multiplication de petites Lambdas ad hoc sans contrat métier.
  - si une nouvelle Lambda métier est nécessaire, elle doit d'abord être décrite dans `/contracts/` puis validée.
- Les Lambdas restent **simples et lisibles** : 
  - le handler fait l'orchestration minimale (validation event, chargement config, appel des fonctions de `vectora_core`),
  - la logique détaillée vit dans `vectora_core`, réutilisable via layers.

### 1.2 Pilotage par config et canonical

- Toute logique métier (scopes, règles de scoring, structure des sections de newsletter, filtres d'intérêt) doit :
  - être définie dans des fichiers `client_config/*` ou `canonical/*`,
  - **ne jamais** être câblée directement dans le code Python.
- Lorsqu'Amazon Q Developer propose d'ajouter une règle ou un paramètre métier, il doit :
  - proposer le champ dans le fichier client_config ou canonical approprié,
  - ajuster le code uniquement pour lire et appliquer cette config, pas pour la coder en dur.

---

## 2. Environnement AWS de référence (NOUVEAU V4)

### 2.1 Configuration AWS établie

**Région AWS principale** : `eu-west-3` (Paris)
- Toutes les ressources principales (S3, Lambda, CloudWatch) sont dans cette région
- **INTERDIT** de créer des ressources dans une autre région sans justification explicite

**Région Bedrock** : `us-east-1` (Virginie du Nord) - **OBSERVÉ DANS LE CODE**
- Région par défaut dans le code : `us-east-1` (voir `vectora_core/*/bedrock_client.py`)
- Configuration hybride supportée :
  - Newsletter : `BEDROCK_REGION_NEWSLETTER` (défaut: `us-east-1`)
  - Normalisation : `BEDROCK_REGION_NORMALIZATION` (défaut: `us-east-1`)
- Modèles par défaut :
  - US : `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
  - EU : `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`

**Profil CLI principal** : `rag-lai-prod`
- Compte AWS : `786469175371`
- **OBLIGATOIRE** dans tous les exemples de commandes CLI

### 2.2 Conventions de nommage établies

**Préfixe projet** : `vectora-inbox`

**Stacks CloudFormation** :
- `vectora-inbox-s0-core-{env}` : Buckets S3 core
- `vectora-inbox-s0-iam-{env}` : Rôles IAM
- `vectora-inbox-s1-runtime-{env}` : Lambdas runtime

**Buckets S3** (pattern : `vectora-inbox-{type}-{env}`) :
- `vectora-inbox-config-dev` : Configuration et canonical
- `vectora-inbox-data-dev` : Données (raw/, normalized/, curated/)
- `vectora-inbox-newsletters-dev` : Newsletters finales
- `vectora-inbox-lambda-code-dev` : Code des Lambdas

**Lambdas** (pattern : `vectora-inbox-{function}-{env}`) :
- `vectora-inbox-ingest-normalize-dev` : Ingestion + normalisation (existante)
- `vectora-inbox-engine-dev` : Matching + scoring + newsletter (existante)
- **FUTUR** : `vectora-inbox-ingest-dev`, `vectora-inbox-normalize-score-dev`, `vectora-inbox-newsletter-dev`

**Groupes de logs CloudWatch** :
- `/aws/lambda/vectora-inbox-ingest-normalize-dev`
- `/aws/lambda/vectora-inbox-engine-dev`

### 2.3 Bonnes pratiques AWS pour Amazon Q Developer

**AVANT d'écrire du code ou de la config, Q doit :**

1. **Relire cette section** pour vérifier les conventions
2. **Utiliser EXCLUSIVEMENT** :
   - Profil : `--profile rag-lai-prod`
   - Région : `--region eu-west-3`
   - Compte : `786469175371`
3. **Détecter les ressources existantes** via les fichiers d'infra ou les outputs CloudFormation
4. **Réutiliser les noms établis** : buckets, Lambdas, rôles IAM

**Q ne doit JAMAIS** :
- Introduire une nouvelle région sans alignement avec les fichiers existants
- Créer des ressources dans une autre région que `eu-west-3`
- Changer les conventions de nommage sans justification et plan de migration
- Inventer de nouveaux noms de buckets ou de Lambdas
- Utiliser un autre profil CLI que `rag-lai-prod`

**Exemples de commandes CLI correctes** :
```bash
# Déploiement d'une stack
aws cloudformation deploy --template-file s0-core.yaml --stack-name vectora-inbox-s0-core-dev --profile rag-lai-prod --region eu-west-3

# Invocation d'une Lambda
aws lambda invoke --function-name vectora-inbox-engine-dev --payload file://event.json response.json --profile rag-lai-prod --region eu-west-3

# Lecture d'un bucket S3
aws s3 ls s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod --region eu-west-3
```

---

## 3. Organisation du code dans /src

### 3.1. Structure OBLIGATOIRE (V4) - Basée sur src_v2

**Architecture 3 Lambdas V2 VALIDÉE** :
```
src_v2/
├── lambdas/                           # Handlers AWS Lambda UNIQUEMENT
│   ├── ingest/
│   │   ├── handler.py                 # Point d'entrée Lambda ingest
│   │   └── requirements.txt           # Documentation des dépendances
│   ├── normalize_score/
│   │   ├── handler.py                 # Point d'entrée Lambda normalize-score
│   │   └── requirements.txt
│   └── newsletter/
│       ├── handler.py                 # Point d'entrée Lambda newsletter
│       └── requirements.txt
├── vectora_core/                      # Bibliothèque métier UNIQUEMENT
│   ├── shared/                        # Modules partagés entre TOUTES les Lambdas
│   │   ├── __init__.py
│   │   ├── config_loader.py           # Chargement configurations S3
│   │   ├── s3_io.py                   # Opérations S3 standardisées
│   │   ├── models.py                  # Modèles de données communs
│   │   └── utils.py                   # Utilitaires transverses
│   ├── ingest/                        # Modules spécifiques Lambda ingest
│   │   ├── __init__.py                # run_ingest_for_client()
│   │   ├── source_fetcher.py          # Récupération contenus externes
│   │   ├── content_parser.py          # Parsing RSS/HTML/API
│   │   └── ingestion_profiles.py      # Profils d'ingestion canonical
│   ├── normalization/                 # Modules spécifiques Lambda normalize-score
│   │   ├── __init__.py                # run_normalize_score_for_client()
│   │   ├── normalizer.py              # Appels Bedrock normalisation
│   │   ├── matcher.py                 # Matching aux domaines de veille
│   │   ├── scorer.py                  # Calcul scores pertinence
│   │   └── bedrock_client.py          # Client Bedrock spécialisé
│   └── newsletter/                    # Modules spécifiques Lambda newsletter
│       ├── __init__.py                # run_newsletter_for_client()
│       ├── assembler.py               # Assemblage newsletter finale
│       ├── editorial.py               # Génération contenu Bedrock
│       ├── layout.py                  # Gestion sections et formats
│       └── metrics.py                 # Calcul statistiques veille
└── README.md                          # Documentation architecture
```

**RÈGLES STRICTES** :
- **1 handler par Lambda** : Chaque Lambda a UN SEUL fichier `handler.py`
- **Séparation par responsabilité** : Chaque Lambda a ses modules dédiés dans `vectora_core/`
- **Modules partagés centralisés** : Code commun UNIQUEMENT dans `vectora_core/shared/`
- **Aucune duplication** : Un module = un emplacement unique
- **Déploiements séparés** : Chaque Lambda peut être packagée indépendamment

### 3.2. État actuel observé dans /src (DIAGNOSTIC V4)

**⚠️ VIOLATIONS CRITIQUES DÉTECTÉES** :

- **Pollution massive par dépendances tierces** : boto3/, requests/, yaml/, feedparser/, bs4/, etc. directement dans `/src/`
- **Stubs de contournement** : `_yaml/` avec `__init__.py` vide
- **Extensions binaires** : `_yaml.cp314-win_amd64.pyd`, `md.cp314-win_amd64.pyd`
- **Métadonnées de packages** : `*-dist-info/` partout dans `/src/`
- **Fichiers de libs à la racine** : `sgmllib.py`, `six.py`, `typing_extensions.py`
- **Package monolithique** : `src/lambdas/engine/package/` avec dépendances

**✅ BONNES PRATIQUES OBSERVÉES** :

- **Handlers propres** : `src/lambdas/*/handler.py` avec logique minimale
- **Vectora_core bien structuré** : modules séparés (config, ingestion, matching, etc.)
- **Variables d'environnement cohérentes** : CONFIG_BUCKET, DATA_BUCKET, BEDROCK_MODEL_ID
- **Nommage des Lambdas conforme** : `vectora-inbox-ingest-normalize-dev`, `vectora-inbox-engine-dev`

### 3.2. Règles d'imports et d'organisation (NOUVEAU V4)

**Imports OBLIGATOIRES dans les handlers** :
```python
# Dans lambdas/ingest/handler.py
from vectora_core.ingest import run_ingest_for_client

# Dans lambdas/normalize_score/handler.py  
from vectora_core.normalization import run_normalize_score_for_client

# Dans lambdas/newsletter/handler.py
from vectora_core.newsletter import run_newsletter_for_client
```

**Imports OBLIGATOIRES dans vectora_core** :
```python
# Dans vectora_core/ingest/__init__.py
from ..shared import config_loader, s3_io, utils, models
from . import source_fetcher, content_parser, ingestion_profiles

# Dans vectora_core/shared/config_loader.py
from . import s3_io  # Import relatif pour modules shared
```

**Fonction d'orchestration OBLIGATOIRE** :
- Chaque package `vectora_core/{lambda}/` doit exporter UNE fonction principale
- Signature standardisée avec `client_id`, `env_vars`, options métier
- Retour standardisé avec statistiques d'exécution

### 3.3. Interdictions RENFORCÉES (V4)

#### 3.3.1. Pollution par Dépendances Tierces (CRITIQUE)

- **INTERDIT ABSOLU** de copier des libs tierces dans `/src` :
  - **Aucun dossier** : `src/boto3/`, `src/yaml/`, `src/requests/`, `src/feedparser/`, `src/bs4/`, `src/certifi/`, `src/charset_normalizer/`, `src/dateutil/`, `src/idna/`, `src/jmespath/`, `src/s3transfer/`, `src/urllib3/`, `src/soupsieve/`, `src/typing_extensions/`
  - **Aucun fichier** : `src/sgmllib.py`, `src/six.py`, `src/typing_extensions.py`
  - **Aucune extension** : `src/*.pyd`, `src/*.so`, `src/*.dll`
  - **Aucun métadata** : `src/*-dist-info/`, `src/*.egg-info/`

#### 3.3.2. Stubs et Contournements (CRITIQUE)

- **INTERDIT ABSOLU** de créer des stubs pour contourner les imports :
  - pas de `src/_yaml/` avec `__init__.py` vide
  - pas de `src/cyaml.py` ou équivalent
  - pas de modification de libs tierces pour les "hacker"

#### 3.3.3. Packages Lambda Monolithiques (CRITIQUE)

- **INTERDIT ABSOLU** de créer des dossiers `package/` dans `/src/lambdas/` :
  - pas de `src/lambdas/engine/package/`
  - pas de `src/lambdas/*/package/` contenant toutes les dépendances
  - **Taille max d'un handler Lambda** : 5MB (code source uniquement)

#### 3.3.4. Scripts de Build dans /src (MAJEUR)

- **INTERDIT** de mettre des scripts de build/test dans `/src` :
  - tout ce qui est `build_*.ps1`, `debug_*.py`, `test_yaml_*.py` va dans `/scripts` ou `/tools`
  - **NOUVEAU** : pas de scripts à la racine du projet (sauf `/scripts/`)

#### 3.3.5. Duplication de Code Métier (MAJEUR)

- **INTERDIT** de dupliquer `vectora_core` :
  - une seule version dans `src/vectora_core/`
  - pas de copie dans `lambda-deps/`, `layers/`, ou `packages/`
  - utiliser les Lambda Layers pour la distribution

---

## 4. Design fonctionnel des Lambdas (NOUVEAU V4)

### 4.1. Principe de généricité absolue

**Les Lambdas doivent rester GÉNÉRIQUES** :
- **INTERDIT** : logique "client A vs client B" codée en dur dans le code
- **INTERDIT** : `if client_id == 'lai_weekly'` dispersés partout
- **INTERDIT** : paramètres métier hardcodés (seuils, règles, sections)

**Tout ce qui est spécifique à un client doit venir de** :
- **`client_config/*.yaml`** : configuration spécifique au client (sections newsletter, seuils scoring, domaines de veille)
- **`canonical/*.yaml`** : scopes métier partagés (entreprises, molécules, technologies, règles de scoring)

### 4.2. Code "piloté par config"

**Le code doit appliquer les règles, pas les définir** :
- Les sections de newsletter viennent de `client_config.newsletter_layout.sections[]`
- Les priorités et seuils viennent de `client_config.scoring_config`
- Les domaines surveillés viennent de `client_config.watch_domains[]`
- Les scopes métier viennent de `canonical/scopes/*.yaml`
- Les prompts Bedrock viennent de `canonical/prompts/*.yaml`

**Exemple CORRECT** :
```python
# Dans vectora_core/newsletter/assembler.py
def generate_newsletter(items, client_config, ...):
    sections = client_config.get('newsletter_layout', {}).get('sections', [])
    for section_config in sections:
        max_items = section_config.get('max_items', 5)
        # Appliquer la config, ne pas la redéfinir
```

**Exemple INCORRECT** :
```python
# ANTI-PATTERN : logique métier hardcodée
def generate_newsletter(items, client_id, ...):
    if client_id == 'lai_weekly':
        sections = ['top_signals', 'partnerships']
        max_items = 5
    elif client_id == 'oncology_monthly':
        sections = ['clinical_trials', 'approvals']
        max_items = 8
```

### 4.3. Éviter les "usines à gaz"

**Q ne doit pas créer d'architecture sur-complexe** :
- **Privilégier** : modules simples et testables
- **Éviter** : classes sur-architecturées inutiles
- **Éviter** : couches d'abstraction superflues
- **Éviter** : patterns de design complexes sans justification

**Exemple de simplicité** :
```python
# CORRECT : fonction simple et claire
def load_client_config(client_id: str, bucket: str) -> Dict[str, Any]:
    key = f"clients/{client_id}.yaml"
    return s3_client.read_yaml_from_s3(bucket, key)

# INCORRECT : sur-architecture inutile
class ClientConfigLoaderFactory:
    def create_loader(self, strategy: str) -> AbstractConfigLoader:
        # Complexité inutile pour un cas simple
```

---

## 5. Lambda : principes de base (BASÉS SUR src_v2)

### 5.1. Granularité STRICTE (Architecture 3 Lambdas V2)

**3 Lambdas EXACTEMENT** :
- **`vectora-inbox-ingest-v2`** : Ingestion brute → S3 `ingested/`
- **`vectora-inbox-normalize-score-v2`** : Normalisation + scoring → S3 `normalized/`  
- **`vectora-inbox-newsletter-v2`** : Assemblage newsletter → S3 `newsletters/`

**INTERDIT** :
- Créer des Lambdas supplémentaires sans contrat métier validé
- Mélanger les responsabilités (ex: ingest + scoring dans la même Lambda)
- Dupliquer la logique entre Lambdas

### 5.2. Handler STANDARDISÉ (Pattern src_v2)

**Structure OBLIGATOIRE du handler** :
```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # 1. Validation paramètres obligatoires
        client_id = event.get("client_id")
        if not client_id:
            return {"statusCode": 400, "body": {"error": "ConfigurationError", "message": "..."}}
        
        # 2. Lecture variables d'environnement
        env_vars = {
            "CONFIG_BUCKET": os.environ.get("CONFIG_BUCKET"),
            "DATA_BUCKET": os.environ.get("DATA_BUCKET"),
            # ...
        }
        
        # 3. Validation variables critiques
        required_vars = ["CONFIG_BUCKET", "DATA_BUCKET"]
        missing_vars = [var for var in required_vars if not env_vars.get(var)]
        if missing_vars:
            return {"statusCode": 500, "body": {"error": "ConfigurationError", "message": f"Variables manquantes : {missing_vars}"}}
        
        # 4. Appel fonction d'orchestration
        result = run_xxx_for_client(
            client_id=client_id,
            # paramètres métier...
            env_vars=env_vars
        )
        
        return {"statusCode": 200, "body": result}
    
    except Exception as e:
        return {"statusCode": 500, "body": {"error": type(e).__name__, "message": str(e)}}
```

**Le handler ne contient AUCUNE logique métier** - tout est délégué à `vectora_core`.

### 5.3. Variables d'environnement standardisées (V4)

**Variables obligatoires** (observées dans les handlers existants) :
- `ENV` : Environnement (dev, stage, prod)
- `PROJECT_NAME` : "vectora-inbox"
- `CONFIG_BUCKET` : "vectora-inbox-config-{env}"
- `DATA_BUCKET` : "vectora-inbox-data-{env}"
- `NEWSLETTERS_BUCKET` : "vectora-inbox-newsletters-{env}"
- `BEDROCK_MODEL_ID` : "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"

**Variables optionnelles** :
- `PUBMED_API_KEY_PARAM` : "/rag-lai/dev/pubmed/api-key"
- `LOG_LEVEL` : "INFO"
- `BEDROCK_REGION_NEWSLETTER` : "eu-west-3"
- `BEDROCK_REGION_NORMALIZATION` : "eu-west-3"

---

## 6. Dépendances & packaging

### 6.1. Dépendances Python

- Les dépendances tierces (boto3, requests, PyYAML, etc.) doivent être :
  - soit fournies par l'environnement AWS (boto3 déjà présent),
  - soit packagées via **Lambda Layers uniquement**,
  - soit installées via un process **standard** (pip + docker Linux / CodeCatalyst),
  - **jamais** copiées manuellement dans `/src`.

### 6.2. Règle PyYAML RENFORCÉE (V4)

- On utilise **uniquement le mode Python pur** de PyYAML :
  - pas de `.pyd` ni d'extensions C `_yaml` dans le package ou `/src`.
- **NOUVEAU** : Si PyYAML pose problème :
  - on corrige le **process de build** (docker Linux, layer, etc.),
  - on n'ajoute **JAMAIS** de stub `_yaml/` ou `cyaml.py` dans `/src`,
  - on n'installe **JAMAIS** PyYAML directement dans `/src`,
  - on utilise **exclusivement** les Lambda Layers.

### 6.3. Lambda Layers OBLIGATOIRES (V4)

- **Layer vectora-core** : contient uniquement `vectora_core/`
- **Layer common-deps** : contient toutes les dépendances tierces
- **Handlers Lambda** : contiennent uniquement `handler.py` + `requirements.txt` (documentation)
- **Taille max par layer** : 50MB compressé
- **Taille max handler** : 5MB compressé

### 6.4. Packaging des Lambda Layers PyYAML (NOUVEAU V4)

#### Règles de Construction
- Utiliser `--no-binary PyYAML` pour éviter les extensions C
- Inclure TOUTES les dépendances transitives dans un seul layer
- Structure obligatoire : `python/` à la racine du zip
- Tester les imports avant déploiement

#### Dépendances Standard Vectora Inbox
- PyYAML==6.0.1 (parsing configuration)
- requests==2.31.0 (HTTP calls)  
- boto3==1.34.0 (AWS SDK)
- feedparser==6.0.10 (RSS parsing)

#### Validation Layer
```bash
# Test structure
unzip -l layer.zip | grep "python/"
# Test imports locaux
cd python && python3 -c "import yaml, requests; print('OK')"
```

#### Commandes de Construction Type
```bash
# Environnement compatible Lambda
mkdir layer_build && cd layer_build
mkdir python

# Installation toutes dépendances (mode pur Python)
pip install --target python --no-binary PyYAML \
  PyYAML==6.0.1 \
  boto3==1.34.0 \
  requests==2.31.0 \
  feedparser==6.0.10

# Création du zip avec structure correcte
zip -r ../vectora-common-deps.zip python/
```

#### Checklist Validation Layer
- [ ] Structure `python/` à la racine
- [ ] Toutes dépendances présentes
- [ ] Pas d'extensions C (.so)
- [ ] Test import local réussi
- [ ] Taille layer < 50MB
- [ ] Runtime compatible (python3.11)

---

## 7. Config métier (canonical YAML, clients, scoring)

- Les fichiers YAML métiers doivent résider dans des buckets S3 dédiés **ou** dans `/canonical/`, **jamais** dans `/src` comme "données de prod".
- Toute lecture de config YAML passe par :
  - `vectora_core.config.loader`  
  - `vectora_core.storage.s3_client`.
- Les scopes (companies, molecules, technologies, indications, exclusions…) sont :
  - centralisés dans `/canonical/scopes/` sur S3,
  - jamais dupliqués dans `/src`.

---

## 8. Tests, scripts, diagnostics

- Tous les scripts de build, tests locaux, diagnostics :
  - vont dans `/scripts/` ou `/tools/` :
    - `scripts/build_*`
    - `scripts/test_*`
    - `scripts/debug_*`
- **NOUVEAU** : Ils ne doivent **JAMAIS** :
  - modifier le contenu de `/src/`
  - copier des libs dans `/src/`
  - créer des stubs dans `/src/`
  - dupliquer `vectora_core`

---

## 9. Validation automatique (V4)

### 9.1. Checks pré-commit obligatoires

Avant chaque commit, valider automatiquement :

- **Taille de `/src/`** : < 50MB
- **Aucune lib tierce** dans `/src/` (liste noire : boto3, yaml, requests, etc.)
- **Aucun fichier .pyd/.so/.dll** dans `/src/`
- **Aucun dossier package/** dans `/src/lambdas/`
- **Aucun script build/test** dans `/src/`
- **NOUVEAU V4** : Conformité aux conventions de nommage AWS

### 9.2. Métriques de qualité

- **Pollution par dépendances** : 0 fichier
- **Duplication vectora_core** : 1 seule version
- **Taille handlers Lambda** : < 5MB chacun
- **Nombre de layers** : exactement 2 (vectora-core + common-deps)
- **Structure layers** : `python/` à la racine, pas d'extensions C
- **NOUVEAU V4** : Conformité environnement AWS (région, profil, buckets)

---

## 10. Checklist pour Q avant toute nouvelle Lambda / refactor (NOUVEAU V4)

**AVANT de proposer du code, Q doit vérifier :**

### 10.1. Environnement AWS
- [ ] Région utilisée : `eu-west-3` uniquement
- [ ] Profil CLI : `--profile rag-lai-prod`
- [ ] Compte AWS : `786469175371`
- [ ] Buckets existants : `vectora-inbox-{type}-dev`

### 10.2. Conventions de nommage
- [ ] Lambda : `vectora-inbox-{function}-{env}`
- [ ] Stack : `vectora-inbox-s{n}-{type}-{env}`
- [ ] Logs : `/aws/lambda/vectora-inbox-{function}-{env}`

### 10.3. Architecture et config
- [ ] Client_config et canonical existent pour la logique métier
- [ ] Pas de logique hardcodée spécifique à un client
- [ ] Handler minimal (< 5MB)
- [ ] Vectora_core utilisé via layer

### 10.4. Dépendances
- [ ] Aucune lib tierce dans `/src/`
- [ ] Layers utilisés pour les dépendances
- [ ] Pas de stubs ou contournements
- [ ] Layer PyYAML en mode pur Python (--no-binary)
- [ ] Toutes dépendances transitives incluses

### 10.5. Bedrock
- [ ] Région par défaut : `us-east-1` (observé dans le code)
- [ ] Configuration hybride si nécessaire (newsletter EU, normalisation US)
- [ ] Variables d'environnement : `BEDROCK_MODEL_ID`, `BEDROCK_REGION`
- [ ] Modèles : `us.anthropic.claude-sonnet-4-5-*` ou `eu.anthropic.claude-sonnet-4-5-*`

---

## 11. Règles spécifiques pour Amazon Q Developer (RENFORCÉES V4)

Quand Q propose du code, il doit respecter les règles suivantes :

### 11.1. Avant tout changement

1. **Lire obligatoirement** ce fichier `src_lambda_hygiene_v4.md`
2. **Vérifier la checklist** de la section 10
3. **Résumer en 3–5 bullet points** les règles qu'il va appliquer
4. **Vérifier l'état actuel** de `/src/` (taille, contenu, structure)
5. **NOUVEAU V4** : Confirmer l'alignement avec l'environnement AWS de référence

### 11.2. Interdictions absolues (RENFORCÉES src_v2)

Il ne doit **JAMAIS** :
- ajouter de packages tiers dans `/src/` (même temporairement)
- créer ou modifier des stubs `_yaml`, `cyaml.py` ou équivalents
- mélanger scripts de build et code métier
- dupliquer `vectora_core` où que ce soit
- créer des dossiers `package/` dans `/src/lambdas/`
- copier des extensions `.pyd/.so/.dll` dans `/src/`
- **NOUVEAU V4** : utiliser une autre région que `eu-west-3` (sauf Bedrock qui utilise `us-east-1` par défaut)
- **NOUVEAU V4** : inventer de nouveaux noms de ressources AWS
- **NOUVEAU V4** : hardcoder de la logique métier spécifique à un client
- **NOUVEAU src_v2** : créer plus de 3 Lambdas sans justification métier
- **NOUVEAU src_v2** : mettre de la logique métier dans les handlers
- **NOUVEAU src_v2** : créer des imports directs entre modules de Lambdas différentes
- **NOUVEAU src_v2** : dupliquer du code au lieu d'utiliser `vectora_core/shared/`

### 11.3. Obligations V4 (ENRICHIES src_v2)

Il doit **TOUJOURS** :
- utiliser le profil `rag-lai-prod` dans les exemples CLI
- respecter les conventions de nommage établies
- vérifier l'existence des buckets et ressources avant d'en créer
- privilégier la configuration via `client_config` et `canonical`
- maintenir la généricité des Lambdas
- **NOUVEAU src_v2** : respecter l'architecture 3 Lambdas V2 exacte
- **NOUVEAU src_v2** : utiliser les imports relatifs corrects dans `vectora_core`
- **NOUVEAU src_v2** : créer une fonction d'orchestration par Lambda dans `vectora_core/{lambda}/__init__.py`
- **NOUVEAU src_v2** : séparer clairement modules partagés vs spécifiques
- **NOUVEAU src_v2** : valider que chaque Lambda peut être packagée indépendamment
- **NOUVEAU src_v2** : maintenir la compatibilité avec les déploiements séparés

---

## 12. Guide d'implémentation pour Q Developer (NOUVEAU src_v2)

### 12.1. Quand créer un nouveau module

**Pour ajouter une fonctionnalité à une Lambda existante** :
1. **Identifier la Lambda concernée** : ingest, normalize_score, ou newsletter
2. **Vérifier si c'est partagé** : Si utilisé par plusieurs Lambdas → `vectora_core/shared/`
3. **Sinon, module spécifique** : `vectora_core/{lambda}/nouveau_module.py`
4. **Importer dans `__init__.py`** : Ajouter à la fonction d'orchestration

**Exemple - Ajouter un nouveau parser** :
```python
# Nouveau fichier : vectora_core/ingest/api_parser.py
def parse_api_response(response_data, source_meta):
    # Logique de parsing API
    pass

# Mise à jour : vectora_core/ingest/__init__.py
from . import source_fetcher, content_parser, ingestion_profiles, api_parser

# Utilisation dans run_ingest_for_client()
if source_meta.get('ingestion_mode') == 'api':
    items = api_parser.parse_api_response(raw_content, source_meta)
```

### 12.2. Quand modifier un module existant

**Règles de modification** :
- **Modules shared** : Impact sur TOUTES les Lambdas → tester toutes
- **Modules spécifiques** : Impact sur UNE Lambda → tester celle-ci
- **Handlers** : Modifications minimales → déléguer à `vectora_core`

**Pattern de modification sûre** :
1. Identifier les modules impactés
2. Vérifier les imports et dépendances
3. Tester le packaging de la/des Lambda(s) concernée(s)
4. Valider aucune régression fonctionnelle

### 12.3. Comment ajouter une nouvelle Lambda (EXCEPTIONNEL)

**ATTENTION** : Ajouter une 4ème Lambda viole l'architecture 3 Lambdas V2

**Si absolument nécessaire** :
1. **Justifier métier** : Nouvelle responsabilité ne rentrant dans aucune des 3
2. **Créer le contrat** : Documenter dans `/docs/design/`
3. **Suivre le pattern** :
   ```
   lambdas/nouvelle_lambda/
   ├── handler.py
   └── requirements.txt
   vectora_core/nouvelle_lambda/
   ├── __init__.py  # run_nouvelle_lambda_for_client()
   └── modules spécifiques...
   ```
4. **Valider l'architecture** : Pas de duplication avec les 3 existantes

## 13. Migration progressive du /src actuel (NOUVEAU V4)

### 13.1. État de référence : src_v2 VALIDÉ

**Le dossier `src_v2/` est l'implémentation de référence** :
- Architecture 3 Lambdas V2 complète et fonctionnelle
- Aucune violation des règles d'hygiène V4
- Tests de packaging et d'intégration validés
- Conformité aux règles d'hygiène V4 atteinte

**Q Developer doit utiliser `src_v2/` comme modèle** pour tout nouveau code.

### 13.2. Exemples concrets pour Q Developer

#### Exemple 1 : Ajouter une nouvelle fonction de parsing

**CORRECT** :
```python
# Nouveau fichier : src_v2/vectora_core/ingest/json_parser.py
def parse_json_feed(json_data, source_meta):
    """Parse un feed JSON en items structurés."""
    items = []
    # Logique de parsing...
    return items

# Mise à jour : src_v2/vectora_core/ingest/__init__.py
from . import source_fetcher, content_parser, ingestion_profiles, json_parser

# Utilisation dans run_ingest_for_client()
if content_type == 'application/json':
    items = json_parser.parse_json_feed(raw_content, source_meta)
```

**INCORRECT** :
```python
# ANTI-PATTERN : Dupliquer dans chaque Lambda
src_v2/lambdas/ingest/json_parser.py  # ❌ INTERDIT
src_v2/lambdas/normalize_score/json_parser.py  # ❌ INTERDIT
```

#### Exemple 2 : Ajouter un client Bedrock spécialisé

**CORRECT** :
```python
# Nouveau fichier : src_v2/vectora_core/normalization/bedrock_client.py
class BedrockNormalizationClient:
    def __init__(self, model_id, region):
        # Initialisation...
        pass
    
    def normalize_item(self, item_data):
        # Appel Bedrock pour normalisation
        pass

# Import dans : src_v2/vectora_core/normalization/__init__.py
from . import normalizer, matcher, scorer, bedrock_client
```

**INCORRECT** :
```python
# ANTI-PATTERN : Mettre dans shared alors que spécifique à normalization
src_v2/vectora_core/shared/bedrock_client.py  # ❌ INTERDIT si spécifique
```

#### Exemple 3 : Ajouter une fonction utilitaire commune

**CORRECT** :
```python
# Ajout dans : src_v2/vectora_core/shared/utils.py
def format_date_for_display(iso_date):
    """Formate une date ISO pour affichage."""
    # Utilisé par ingest, normalize_score ET newsletter
    pass

# Import depuis n'importe quelle Lambda
from vectora_core.shared import utils
formatted_date = utils.format_date_for_display(item['date'])
```

#### Exemple 4 : Créer un nouveau handler Lambda

**CORRECT** (si absolument nécessaire) :
```python
# Nouveau fichier : src_v2/lambdas/monitoring/handler.py
def lambda_handler(event, context):
    try:
        client_id = event.get("client_id")
        if not client_id:
            return {"statusCode": 400, "body": {"error": "ConfigurationError"}}
        
        # Déléguer à vectora_core
        from vectora_core.monitoring import run_monitoring_for_client
        result = run_monitoring_for_client(client_id=client_id, ...)
        
        return {"statusCode": 200, "body": result}
    except Exception as e:
        return {"statusCode": 500, "body": {"error": str(e)}}

# Nouveau dossier : src_v2/vectora_core/monitoring/
# Nouveau fichier : src_v2/vectora_core/monitoring/__init__.py
def run_monitoring_for_client(client_id, ...):
    """Fonction d'orchestration pour monitoring."""
    pass
```

### 13.3. Checklist avant écriture de code

**Q Developer doit TOUJOURS vérifier** :

1. **Architecture** :
   - [ ] Le code va dans `src_v2/` (pas dans l'ancien `/src/`)
   - [ ] Respect de la structure 3 Lambdas + vectora_core
   - [ ] Pas de duplication entre modules

2. **Emplacement du nouveau code** :
   - [ ] Spécifique à une Lambda → `vectora_core/{lambda}/`
   - [ ] Partagé entre Lambdas → `vectora_core/shared/`
   - [ ] Handler Lambda → `lambdas/{lambda}/handler.py`

3. **Imports** :
   - [ ] Imports relatifs dans vectora_core : `from ..shared import`, `from . import`
   - [ ] Import depuis handler : `from vectora_core.{lambda} import run_xxx_for_client`
   - [ ] Pas d'imports directs entre modules de Lambdas différentes

4. **Fonctions d'orchestration** :
   - [ ] Une fonction principale par Lambda dans `vectora_core/{lambda}/__init__.py`
   - [ ] Signature standardisée avec `client_id`, `env_vars`
   - [ ] Retour standardisé avec statistiques

5. **Tests et validation** :
   - [ ] Le code peut être importé sans erreur
   - [ ] La Lambda concernée peut être packagée
   - [ ] Aucune régression sur les autres Lambdas

---

## 14. Résumé pour Q Developer

### 📝 Avant d'écrire du code, Q doit :

1. **Lire cette section** et la checklist 13.3
2. **Utiliser `src_v2/` comme référence** (pas l'ancien `/src/`)
3. **Respecter l'architecture 3 Lambdas V2** exacte
4. **Placer le code au bon endroit** : shared vs spécifique
5. **Utiliser les imports relatifs** corrects
6. **Tester le packaging** de la Lambda concernée

### ⚠️ Interdictions absolues :

- ❌ Modifier l'ancien `/src/` (utiliser `src_v2/`)
- ❌ Créer plus de 3 Lambdas sans justification
- ❌ Dupliquer du code entre modules
- ❌ Mettre de la logique métier dans les handlers
- ❌ Ajouter des dépendances tierces dans `/src/`

### ✅ Bonnes pratiques :

- ✅ Suivre les exemples de la section 13.2
- ✅ Utiliser la checklist 13.3 avant chaque modification
- ✅ Déléguer toute logique à `vectora_core`
- ✅ Maintenir la séparation claire des responsabilités
- ✅ Tester l'impact sur les déploiements séparés

---

**Version** : V4 + src_v2 (Décembre 2025)
**Environnement de référence** : AWS eu-west-3, compte 786469175371, profil rag-lai-prod
**Architecture de référence** : `src_v2/` - 3 Lambdas V2 + vectora_core + config-driven
**Implémentation validée** : Phase 3 terminée avec succès, tests d'intégration OK