# Infrastructure Vectora Inbox

## Introduction

Le dossier `infra/` contient les templates d'infrastructure CloudFormation pour Vectora Inbox.

L'objectif de la stack S0 (`s0-core`) est de créer les buckets S3 de base du projet, sans encore déployer de Lambdas ni de logique métier. C'est la première brique d'infrastructure à mettre en place avant de pouvoir déployer les composants applicatifs.

## Description de la stack S0-core

### Vue d'ensemble

- **Nom de la stack** : `vectora-inbox-s0-core-<Env>` (exemple : `vectora-inbox-s0-core-dev`)
- **Fichier de template** : `infra/s0-core.yaml`
- **Région AWS** : `eu-west-3` (Paris)

### Paramètres principaux

La stack accepte deux paramètres :

- **ProjectName** : nom du projet, utilisé comme préfixe pour tous les buckets (par défaut : `vectora-inbox`)
- **Env** : environnement cible, peut être `dev`, `stage` ou `prod` (par défaut : `dev`)

### Les trois buckets S3 créés

La stack crée trois buckets S3 essentiels pour le fonctionnement de Vectora Inbox :

#### 1. Bucket de configuration

- **Nom logique** : `ConfigBucket`
- **Nom physique** : `${ProjectName}-config-${Env}`
- **Exemple** : `vectora-inbox-config-dev`
- **Contenu prévu** : fichiers canonical (scopes, sources, règles de scoring), configurations clients, paramètres de bouquets

#### 2. Bucket de données

- **Nom logique** : `DataBucket`
- **Nom physique** : `${ProjectName}-data-${Env}`
- **Exemple** : `vectora-inbox-data-dev`
- **Contenu prévu** : données ingérées brutes (raw), données normalisées après traitement Bedrock, métadonnées d'ingestion

#### 3. Bucket de newsletters

- **Nom logique** : `NewslettersBucket`
- **Nom physique** : `${ProjectName}-newsletters-${Env}`
- **Exemple** : `vectora-inbox-newsletters-dev`
- **Contenu prévu** : newsletters finales générées (fichiers Markdown ou HTML prêts à être lus ou envoyés)

### Caractéristiques de sécurité

Tous les buckets sont configurés avec les meilleures pratiques de sécurité :

- **Accès public bloqué** : tous les flags de Block Public Access sont activés pour empêcher toute exposition accidentelle
- **Versioning activé** : permet de conserver l'historique des modifications et de faciliter les rollbacks en cas de problème
- **Chiffrement SSE-S3** : chiffrement côté serveur activé par défaut pour protéger les données au repos
- **Tags** : chaque bucket est tagué avec le nom du projet et l'environnement pour faciliter la gestion et la facturation

## Comment déployer la stack S0-core (exemple)

### Prérequis

- AWS CLI installé et configuré
- Profil AWS `rag-lai-prod` configuré avec les permissions nécessaires
- Accès à la région `eu-west-3` (Paris)

### Commande de déploiement

Depuis la racine du dépôt `vectora-inbox`, exécutez la commande suivante dans PowerShell :

```powershell
# Se placer à la racine du dépôt
cd "C:\Users\franc\OneDrive\Bureau\vectora-inbox"

# Déployer la stack S0-core en environnement de développement
aws cloudformation deploy `
  --template-file infra/s0-core.yaml `
  --stack-name vectora-inbox-s0-core-dev `
  --parameter-overrides Env=dev ProjectName=vectora-inbox `
  --region eu-west-3 `
  --profile rag-lai-prod
```

**Explications** :

- `Env=dev` permet de déployer en environnement de développement. Plus tard, vous pourrez utiliser `Env=stage` ou `Env=prod` pour déployer dans d'autres environnements.
- `ProjectName=vectora-inbox` définit le préfixe des buckets. Vous pouvez le modifier si nécessaire.
- La commande ne doit être lancée que lorsque vous êtes prêt à créer les ressources AWS (des coûts de stockage S3 s'appliqueront).

### Sauvegarder les outputs de la stack

Une fois la stack déployée, il est utile de sauvegarder les informations de sortie (noms des buckets, ARNs) dans un fichier pour référence future :

```powershell
# Créer le dossier outputs s'il n'existe pas
mkdir infra\outputs -ErrorAction SilentlyContinue

# Récupérer les outputs de la stack et les sauvegarder
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-core-dev `
  --region eu-west-3 `
  --profile rag-lai-prod `
  > infra/outputs/vectora-inbox-s0-core-dev.json
```

**Intérêt du fichier d'outputs** :

- Retrouver facilement les noms exacts des buckets créés
- Consulter les ARNs des ressources pour les utiliser dans d'autres stacks (IAM, Lambdas)
- Garder une trace de la configuration déployée pour chaque environnement
- Faciliter le débogage en cas de problème

## Stack S0-IAM : rôles IAM pour les Lambdas

### Vue d'ensemble

Cette stack crée les rôles IAM de base pour les deux Lambdas principales de Vectora Inbox :

- une Lambda d'ingestion + normalisation (`vectora-inbox-ingest-normalize-<Env>`),
- une Lambda d'orchestration / scoring / génération de newsletter (`vectora-inbox-engine-<Env>`).

### Nom de la stack et template

- **Nom de la stack** (exemple) : `vectora-inbox-s0-iam-dev`
- **Fichier de template** : `infra/s0-iam.yaml`
- **Paramètres principaux** :
  - `ProjectName` (par défaut : `vectora-inbox`)
  - `Env` (par défaut : `dev`)
  - `ConfigBucketName`, `DataBucketName`, `NewslettersBucketName`
  - `PubmedApiKeyParamPath` (chemin SSM de la clé API PubMed, utilisé plus tard par la Lambda d'ingestion)

### Permissions du rôle d'ingestion (IngestNormalizeRole)

Ce rôle sera utilisé par la Lambda `vectora-inbox-ingest-normalize` pour :

- **Lire le bucket de configuration** : charger les fichiers canonical (scopes, sources, règles de scoring) et les configurations clients
- **Lire et écrire dans le bucket de données** : stocker les items bruts (raw) et les items normalisés après traitement
- **Appeler Bedrock** : utiliser les modèles de langage pour comprendre et normaliser le texte des articles ingérés
- **Lire la clé API PubMed depuis SSM** : récupérer la clé d'API PubMed stockée dans AWS Systems Manager Parameter Store (via le chemin `PubmedApiKeyParamPath`)
- **Écrire des logs dans CloudWatch Logs** : tracer l'exécution de la Lambda pour faciliter le débogage

### Permissions du rôle engine (EngineRole)

Ce rôle sera utilisé par la Lambda `vectora-inbox-engine` pour :

- **Lire le bucket de données** : charger les items normalisés pour effectuer le matching et le scoring
- **Écrire dans le bucket de newsletters** : stocker les newsletters finales générées (fichiers Markdown ou HTML)
- **Appeler Bedrock** : utiliser les modèles de langage pour générer le contenu éditorial de la newsletter
- **Écrire des logs dans CloudWatch Logs** : tracer l'exécution de la Lambda pour faciliter le débogage

### Principe de sécurité : permissions minimales

Chaque rôle dispose uniquement des permissions strictement nécessaires à sa fonction :

- Le rôle d'ingestion ne peut pas écrire dans le bucket de newsletters
- Le rôle engine ne peut pas écrire dans le bucket de données
- Les deux rôles ne peuvent accéder qu'aux buckets spécifiés en paramètres
- Les appels Bedrock sont limités à la région de déploiement (eu-west-3)

### Comment déployer la stack S0-IAM (exemple)

**Important** : cette stack doit être déployée APRÈS la stack S0-core, car elle a besoin des noms exacts des buckets créés.

```powershell
# Se placer à la racine du dépôt
cd "C:\Users\franc\OneDrive\Bureau\vectora-inbox"

# Déployer la stack S0-IAM en environnement de développement
aws cloudformation deploy `
  --template-file infra/s0-iam.yaml `
  --stack-name vectora-inbox-s0-iam-dev `
  --parameter-overrides `
    Env=dev `
    ProjectName=vectora-inbox `
    ConfigBucketName=vectora-inbox-config-dev `
    DataBucketName=vectora-inbox-data-dev `
    NewslettersBucketName=vectora-inbox-newsletters-dev `
    PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key `
  --capabilities CAPABILITY_IAM `
  --region eu-west-3 `
  --profile rag-lai-prod
```

**Explications** :

- `--capabilities CAPABILITY_IAM` est obligatoire car cette stack crée des rôles IAM
- Les noms de buckets doivent correspondre exactement aux buckets créés par la stack S0-core
- Le paramètre `PubmedApiKeyParamPath` doit pointer vers un paramètre SSM existant (ou sera utilisé plus tard)
- Cette commande est un exemple : ne la lancez que lorsque vous êtes prêt à créer les rôles IAM

### Sauvegarder les outputs de la stack

Une fois la stack déployée, sauvegardez les ARNs des rôles pour les utiliser dans la stack S1-lambdas :

```powershell
# Récupérer les outputs de la stack et les sauvegarder
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s0-iam-dev `
  --region eu-west-3 `
  --profile rag-lai-prod `
  > infra/outputs/vectora-inbox-s0-iam-dev.json
```

**Intérêt du fichier d'outputs** :

- Retrouver facilement les ARNs des rôles IAM créés
- Utiliser ces ARNs comme paramètres d'entrée pour la stack S1-lambdas
- Garder une trace de la configuration IAM déployée pour chaque environnement

## Stack S1-runtime : fonctions Lambda principales

### Vue d'ensemble

Cette stack crée les deux fonctions Lambda principales de Vectora Inbox :

- une Lambda d'ingestion + normalisation (`vectora-inbox-ingest-normalize-<Env>`),
- une Lambda moteur (`vectora-inbox-engine-<Env>`).

Ces Lambdas implémentent le workflow complet de Vectora Inbox :

- **ingest-normalize** : lit la config client, résout les bouquets de sources, ingère les contenus depuis les sources externes (RSS, APIs), normalise les items avec Bedrock (extraction d'entités, classification d'événements, génération de résumés), et écrit les items normalisés dans le bucket `data`.

- **engine** : lit les items normalisés depuis le bucket `data`, applique la logique de matching (intersections d'ensembles avec les scopes canonical), calcule les scores de pertinence (règles numériques transparentes), appelle Bedrock pour rédiger la newsletter (intros, TL;DR, reformulations), et écrit la newsletter finale dans le bucket `newsletters`.

### Nom de la stack et template

- **Nom de la stack** (exemple) : `vectora-inbox-s1-runtime-dev`
- **Fichier de template** : `infra/s1-runtime.yaml`
- **Région AWS** : `eu-west-3` (Paris)

### Dépendances

Cette stack doit être déployée APRÈS les stacks S0-core et S0-iam, car elle a besoin :

- des noms exacts des trois buckets S3 (config, data, newsletters),
- des ARNs des deux rôles IAM créés par S0-iam,
- des emplacements S3 du code des Lambdas (buckets + clés).

### Paramètres principaux

La stack accepte plusieurs paramètres :

**Paramètres de base :**
- `ProjectName` : nom du projet (par défaut : `vectora-inbox`)
- `Env` : environnement cible (`dev`, `stage`, `prod`)

**Paramètres S3 (depuis S0-core) :**
- `ConfigBucketName` : nom du bucket de configuration
- `DataBucketName` : nom du bucket de données
- `NewslettersBucketName` : nom du bucket de newsletters

**Paramètres IAM (depuis S0-iam) :**
- `IngestNormalizeRoleArn` : ARN du rôle IAM pour la Lambda ingest-normalize
- `EngineRoleArn` : ARN du rôle IAM pour la Lambda engine

**Paramètres de code Lambda :**
- `IngestNormalizeCodeBucket` : bucket S3 contenant le code de la Lambda ingest-normalize
- `IngestNormalizeCodeKey` : clé S3 du package de code (par défaut : `lambda/ingest-normalize/latest.zip`)
- `EngineCodeBucket` : bucket S3 contenant le code de la Lambda engine
- `EngineCodeKey` : clé S3 du package de code (par défaut : `lambda/engine/latest.zip`)

**Paramètres de configuration métier :**
- `PubmedApiKeyParamPath` : chemin du paramètre SSM pour la clé API PubMed (par défaut : `/rag-lai/dev/pubmed/api-key`)
- `BedrockModelId` : identifiant du profil d'inférence Bedrock à utiliser (par défaut : `eu.anthropic.claude-sonnet-4-5-v2:0` - Claude Sonnet 4.5 via profil global EU)

**Note importante sur le modèle Bedrock :**
Le projet utilise **Claude Sonnet 4.5 (Amazon Bedrock Edition)** via un **profil d'inférence cross-region EU** comme modèle d'IA par défaut pour :
- La normalisation des items (extraction d'entités, classification d'événements, génération de résumés)
- La génération éditoriale des newsletters (intros, TL;DR, reformulations)

**Profil d'inférence cross-region EU :**
- Les modèles Anthropic récents (Claude Sonnet 4.5) nécessitent l'utilisation d'un **inference profile** au lieu du modelId direct
- Pour la région `eu-west-3`, le profil cross-region EU officiel est : `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
- ARN du profil : `arn:aws:bedrock:eu-west-3:786469175371:inference-profile/eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
- Ce profil route les requêtes vers : eu-north-1, eu-west-3, eu-south-1, eu-south-2, eu-west-1, eu-central-1
- Le modèle est configurable via le paramètre `BedrockModelId` et peut être changé sans modifier le code Python
- Les Lambdas lisent ce paramètre depuis la variable d'environnement `BEDROCK_MODEL_ID`

**Paramètres techniques Lambda :**
- `LambdaRuntime` : runtime Python (par défaut : `python3.12`)
- `LambdaTimeout` : timeout en secondes (par défaut : 300 = 5 minutes)
- `LambdaMemorySize` : mémoire en Mo (par défaut : 512)
- `LogRetentionDays` : durée de rétention des logs CloudWatch (par défaut : 7 jours)

### Variables d'environnement des Lambdas

Chaque Lambda reçoit des variables d'environnement pour accéder aux ressources et configurations.

#### Lambda ingest-normalize

| Variable d'environnement | Définie dans infra | Lue dans le code | Utilisation |
|--------------------------|-------------------|------------------|-------------|
| `ENV` | ✅ S1-runtime.yaml | ✅ handler.py | Environnement de déploiement (dev, stage, prod) |
| `PROJECT_NAME` | ✅ S1-runtime.yaml | ✅ handler.py | Nom du projet (vectora-inbox) |
| `CONFIG_BUCKET` | ✅ S1-runtime.yaml | ✅ handler.py | Bucket S3 contenant les configurations canonical et client |
| `DATA_BUCKET` | ✅ S1-runtime.yaml | ✅ handler.py | Bucket S3 pour stocker les items bruts (raw) et normalisés |
| `BEDROCK_MODEL_ID` | ✅ S1-runtime.yaml | ✅ handler.py | Modèle Bedrock pour normalisation (extraction d'entités, classification) |
| `PUBMED_API_KEY_PARAM` | ✅ S1-runtime.yaml | ✅ handler.py | Chemin SSM du paramètre contenant la clé API PubMed |
| `LOG_LEVEL` | ✅ S1-runtime.yaml | ✅ handler.py | Niveau de log CloudWatch (INFO par défaut) |

**Où ces variables sont utilisées dans le pipeline :**
- `CONFIG_BUCKET` : chargement des scopes canonical et de la config client au démarrage
- `DATA_BUCKET` : écriture des items normalisés dans `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`
- `BEDROCK_MODEL_ID` : appels à Bedrock pour extraire les entités et classifier les événements
- `PUBMED_API_KEY_PARAM` : récupération de la clé API PubMed depuis SSM pour interroger l'API PubMed

#### Lambda engine

| Variable d'environnement | Définie dans infra | Lue dans le code | Utilisation |
|--------------------------|-------------------|------------------|-------------|
| `ENV` | ✅ S1-runtime.yaml | ✅ handler.py | Environnement de déploiement (dev, stage, prod) |
| `PROJECT_NAME` | ✅ S1-runtime.yaml | ✅ handler.py | Nom du projet (vectora-inbox) |
| `CONFIG_BUCKET` | ✅ S1-runtime.yaml | ✅ handler.py | Bucket S3 contenant les configurations canonical et client |
| `DATA_BUCKET` | ✅ S1-runtime.yaml | ✅ handler.py | Bucket S3 pour lire les items normalisés |
| `NEWSLETTERS_BUCKET` | ✅ S1-runtime.yaml | ✅ handler.py | Bucket S3 pour écrire les newsletters finales |
| `BEDROCK_MODEL_ID` | ✅ S1-runtime.yaml | ✅ handler.py | Modèle Bedrock pour génération éditoriale (intros, TL;DR, reformulations) |
| `LOG_LEVEL` | ✅ S1-runtime.yaml | ✅ handler.py | Niveau de log CloudWatch (INFO par défaut) |

**Où ces variables sont utilisées dans le pipeline :**
- `CONFIG_BUCKET` : chargement des scopes canonical et de la config client au démarrage
- `DATA_BUCKET` : lecture des items normalisés depuis `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`
- `NEWSLETTERS_BUCKET` : écriture de la newsletter finale dans `<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`
- `BEDROCK_MODEL_ID` : appels à Bedrock pour rédiger les intros, TL;DR et reformuler les items

### Mapping entre infrastructure et code Python

Cette section explique comment les Lambdas définies dans `infra/s1-runtime.yaml` sont câblées au code Python dans `src/`.

#### Lambda 1 : vectora-inbox-ingest-normalize

**Nom AWS de la fonction :**
- Défini dans CloudFormation : `${ProjectName}-ingest-normalize-${Env}`
- Exemple en dev : `vectora-inbox-ingest-normalize-dev`

**Handler CloudFormation :**
- Propriété `Handler` dans S1-runtime.yaml : `"handler.lambda_handler"`
- Signification : AWS Lambda cherche un fichier `handler.py` à la racine du package zip, et appelle la fonction `lambda_handler(event, context)` qu'il contient

**Chemin du code Python :**
- Fichier source : `src/lambdas/ingest_normalize/handler.py`
- Fonction appelée : `lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]`
- Ce handler délègue toute la logique métier à : `vectora_core.run_ingest_normalize_for_client()`

**Rôle de ce handler :**
- Parser l'événement d'entrée (client_id, sources, dates)
- Lire les variables d'environnement (CONFIG_BUCKET, DATA_BUCKET, BEDROCK_MODEL_ID, etc.)
- Appeler la fonction de haut niveau `run_ingest_normalize_for_client()` depuis `vectora_core`
- Formater la réponse (statusCode 200/400/500, body JSON)
- Gérer les erreurs globales et logger les informations importantes

**Phases exécutées :**
- Phase 1A (Ingestion) : récupération des contenus bruts depuis les sources externes (RSS, APIs)
- Phase 1B (Normalisation) : transformation en items structurés avec Bedrock (extraction d'entités, classification d'événements, génération de résumés)

#### Lambda 2 : vectora-inbox-engine

**Nom AWS de la fonction :**
- Défini dans CloudFormation : `${ProjectName}-engine-${Env}`
- Exemple en dev : `vectora-inbox-engine-dev`

**Handler CloudFormation :**
- Propriété `Handler` dans S1-runtime.yaml : `"handler.lambda_handler"`
- Signification : AWS Lambda cherche un fichier `handler.py` à la racine du package zip, et appelle la fonction `lambda_handler(event, context)` qu'il contient

**Chemin du code Python :**
- Fichier source : `src/lambdas/engine/handler.py`
- Fonction appelée : `lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]`
- Ce handler délègue toute la logique métier à : `vectora_core.run_engine_for_client()`

**Rôle de ce handler :**
- Parser l'événement d'entrée (client_id, period_days, dates, target_date)
- Lire les variables d'environnement (CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_MODEL_ID, etc.)
- Appeler la fonction de haut niveau `run_engine_for_client()` depuis `vectora_core`
- Formater la réponse (statusCode 200/400/500, body JSON)
- Gérer les erreurs globales et logger les informations importantes

**Phases exécutées :**
- Phase 2 (Matching) : détermination des items pertinents par watch_domain (intersections d'ensembles, sans Bedrock)
- Phase 3 (Scoring) : calcul des scores de pertinence (règles numériques transparentes, sans Bedrock)
- Phase 4 (Newsletter) : assemblage de la newsletter avec Bedrock (intros, TL;DR, reformulations)

#### Principe architectural : handlers minces + logique métier dans vectora_core

Les handlers Lambda (`src/lambdas/*/handler.py`) sont volontairement **très minces** :
- Ils ne contiennent AUCUNE logique métier
- Ils se contentent de parser l'événement, lire les variables d'environnement, et appeler `vectora_core`
- Toute la logique métier (ingestion, normalisation, matching, scoring, newsletter) est dans `vectora_core/`

**Avantages de cette architecture :**
- **Testabilité** : on peut tester `vectora_core` sans simuler AWS Lambda
- **Réutilisabilité** : `vectora_core` peut être utilisé dans d'autres contextes (CLI, notebooks, tests)
- **Maintenabilité** : la séparation entre "plomberie AWS" et "logique métier" est claire
- **Indépendance** : `vectora_core` ne dépend pas d'AWS Lambda, seulement de boto3 pour S3 et Bedrock

### Structure du code Lambda attendue pour le packaging

Les Lambdas doivent être packagées avec un handler nommé `handler.lambda_handler` à la racine du zip :

**Pour ingest-normalize :**
- Fichier source : `src/lambdas/ingest_normalize/handler.py`
- Fonction : `lambda_handler(event, context)`
- Package zip : doit contenir `handler.py` à la racine + le package `vectora_core/` + les dépendances

**Pour engine :**
- Fichier source : `src/lambdas/engine/handler.py`
- Fonction : `lambda_handler(event, context)`
- Package zip : doit contenir `handler.py` à la racine + le package `vectora_core/` + les dépendances

**Important :** Le code doit être zippé et uploadé dans les buckets S3 spécifiés avant le déploiement de la stack S1-runtime.

### Comment déployer la stack S1-runtime (exemple)

**Important** : cette stack doit être déployée APRÈS S0-core et S0-iam, et le code des Lambdas doit être uploadé dans S3 au préalable.

```powershell
# Se placer à la racine du dépôt
cd "C:\Users\franc\OneDrive\Bureau\vectora-inbox"

# Déployer la stack S1-runtime en environnement de développement
aws cloudformation deploy `
  --template-file infra/s1-runtime.yaml `
  --stack-name vectora-inbox-s1-runtime-dev `
  --parameter-overrides `
    Env=dev `
    ProjectName=vectora-inbox `
    ConfigBucketName=vectora-inbox-config-dev `
    DataBucketName=vectora-inbox-data-dev `
    NewslettersBucketName=vectora-inbox-newsletters-dev `
    IngestNormalizeRoleArn=arn:aws:iam::786469175371:role/vectora-inbox-IngestNormalizeRole-dev `
    EngineRoleArn=arn:aws:iam::786469175371:role/vectora-inbox-EngineRole-dev `
    IngestNormalizeCodeBucket=vectora-inbox-lambda-code-dev `
    IngestNormalizeCodeKey=lambda/ingest-normalize/latest.zip `
    EngineCodeBucket=vectora-inbox-lambda-code-dev `
    EngineCodeKey=lambda/engine/latest.zip `
    PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key `
    BedrockModelId=eu.anthropic.claude-sonnet-4-5-20250929-v1:0 `
  --region eu-west-3 `
  --profile rag-lai-prod
```

**Explications** :

- Les ARNs des rôles IAM doivent être récupérés depuis les outputs de la stack S0-iam (voir `infra/outputs/vectora-inbox-s0-iam-dev.json`).
- Les buckets de code Lambda (`IngestNormalizeCodeBucket`, `EngineCodeBucket`) doivent exister et contenir les packages zippés du code.
- Les clés S3 (`IngestNormalizeCodeKey`, `EngineCodeKey`) doivent pointer vers les fichiers zip du code.
- Le modèle Bedrock spécifié doit être disponible dans la région `eu-west-3`.
- Cette commande est un exemple : adaptez les valeurs des paramètres selon votre environnement réel.

### Sauvegarder les outputs de la stack

Une fois la stack déployée, sauvegardez les informations de sortie (noms et ARNs des fonctions Lambda) :

```powershell
# Récupérer les outputs de la stack et les sauvegarder
aws cloudformation describe-stacks `
  --stack-name vectora-inbox-s1-runtime-dev `
  --region eu-west-3 `
  --profile rag-lai-prod `
  > infra/outputs/vectora-inbox-s1-runtime-dev.json
```

**Intérêt du fichier d'outputs** :

- Retrouver facilement les noms exacts des fonctions Lambda créées
- Consulter les ARNs des fonctions pour les invoquer ou les connecter à EventBridge
- Garder une trace de la configuration déployée pour chaque environnement

## Prochaines étapes

Une fois les stacks S0-core, S0-iam et S1-runtime déployées avec succès :

1. Uploader les fichiers canonical dans `s3://vectora-inbox-config-dev/canonical/`
2. Uploader les configurations clients dans `s3://vectora-inbox-config-dev/clients/`
3. Créer le paramètre SSM pour la clé API PubMed (si nécessaire)
4. Tester les Lambdas manuellement via la console AWS ou AWS CLI
5. Valider le workflow end-to-end avec la config client `lai_weekly`
