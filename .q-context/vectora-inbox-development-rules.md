# Règles de Développement Vectora Inbox - Guide Complet Q Developer

**Date :** 18 décembre 2025  
**Version :** Unifiée V4 + V2  
**Architecture de référence :** 3 Lambdas V2 validées E2E  
**Environnement AWS :** eu-west-3, compte 786469175371, profil rag-lai-prod

---

## 🚨 RÈGLES CRITIQUES

### 1. Format de Première Réponse Obligatoire

**Q Developer DOIT TOUJOURS commencer par un format standardisé lors de la première réponse à un prompt utilisateur.**

**Document de référence** : `.q-context/q-response-format.md`

### 2. Git Integration Obligatoire

**Q Developer DOIT TOUJOURS intégrer Git AVANT le build, pas après le déploiement.**

**Documents de référence** :
- `.q-context/vectora-inbox-git-workflow.md` - Workflows Git complets
- `.q-context/vectora-inbox-git-rules.md` - Règles Git obligatoires

### 3. Mode Assistant Guidé (NOUVEAU)

**Q Developer DOIT agir comme un mentor pour les développeurs débutants.**

**Document de référence** : `.q-context/vectora-inbox-assistant-guide.md`

**Q DOIT TOUJOURS**:
- ✅ Proposer proactivement le versioning après modifications
- ✅ Donner les commandes Git exactes à exécuter
- ✅ Expliquer POURQUOI chaque étape est importante
- ✅ Suggérer des tests avant déploiement
- ✅ Détecter les problèmes potentiels
- ✅ Proposer rollback si tests échouent
- ✅ Demander confirmation avant actions critiques
- ✅ Expliquer en termes simples pour débutants

### Objectif

Validation explicite du plan AVANT toute action pour :
- Éviter les dérives (mauvais environnement, mauvaises règles)
- Garantir l'alignement avec la gouvernance
- Permettre la validation humaine avant exécution
- Assurer la traçabilité des décisions

### Format Obligatoire

Chaque première réponse DOIT inclure :

1. **Analyse de la demande** : Reformulation claire du prompt
2. **Règles appliquées** : Références explicites aux fichiers de gouvernance
3. **Analyse technique** : Fichiers à lire/modifier/créer
4. **Environnement cible** : dev/stage/prod avec ressources AWS impactées
5. **Livrables prévus** : Documents, artefacts, modifications VERSION
6. **Points de vigilance** : Risques identifiés et mitigations
7. **Plan d'exécution** : Phases détaillées avec durées
8. **Validation** : Demande explicite de confirmation (OUI/MODIFIER/ANNULER)

### Exemple Concret

**Prompt utilisateur** :
```
Ajoute une fonction pour extraire les dates relatives.
```

**Réponse Q Developer** :
```markdown
## 🎯 ANALYSE DE VOTRE DEMANDE

**Votre demande** : Ajouter une fonction d'extraction de dates relatives...

**Type de tâche identifié** : Développement - Nouvelle fonctionnalité

---

## 📚 RÈGLES ET GOUVERNANCE APPLIQUÉES

**Règles de développement** :
- `.q-context/vectora-inbox-development-rules.md`
  - Architecture : 3 Lambdas V2
  - Code source : `src_v2/` uniquement
  ...

[Suite du format complet]

---

## ✅ VALIDATION AVANT EXÉCUTION

**Confirmez-vous que je peux procéder avec ce plan ?**

Options :
- ✅ **OUI** - Procéder
- ⚠️ **MODIFIER** - Ajuster [préciser]
- ❌ **ANNULER** - Ne pas exécuter
```

### Exceptions Autorisées

Le format peut être allégé pour :
- Questions simples de clarification
- Demandes de lecture seule (afficher un fichier)
- Continuation d'un plan déjà validé

### Non-Respect du Format

Si Q Developer ne suit pas ce format, rappeler :
```
Merci de commencer par le format de réponse initiale obligatoire défini dans 
.q-context/q-response-format.md avant de procéder.
```

---

## 🎯 RÈGLES PRIORITAIRES POUR Q DEVELOPER

### 1. Git Integration (CRITIQUE)

**✅ TOUJOURS créer branche avant modification :**
```bash
git checkout develop
git checkout -b feature/my-feature
# Modifier code...
git commit -m "feat: description"
# PUIS build et deploy
```

**✅ TOUJOURS commit AVANT build :**
```bash
git add src_v2/ VERSION
git commit -m "feat(vectora-core): add feature"
python scripts/build/build_all.py  # Après commit
```

**✅ TOUJOURS synchroniser VERSION avec Git tags :**
```bash
# Après validation en dev
git tag v1.3.0 -m "Release 1.3.0"
git push origin develop --tags
python scripts/deploy/promote.py --to stage --version 1.3.0 --git-sha $(git rev-parse HEAD)
```

**❌ NE JAMAIS commit direct sur main/develop :**
```bash
# ❌ INTERDIT
git checkout develop
git commit -m "add feature"
git push origin develop

# ✅ OBLIGATOIRE
git checkout -b feature/my-feature
git commit -m "feat: add feature"
git push origin feature/my-feature
# Créer PR
```

### 2. Architecture de Référence (OBLIGATOIRE)

**✅ TOUJOURS utiliser l'architecture 3 Lambdas V2 :**
```
src_v2/lambdas/
├── ingest/handler.py           # Lambda ingest-v2
├── normalize_score/handler.py  # Lambda normalize-score-v2
└── newsletter/handler.py       # Lambda newsletter-v2
```

**❌ NE JAMAIS proposer l'architecture 2 Lambdas (historique) :**
- ❌ `ingest-normalize` monolithique
- ❌ `engine` monolithique
- ❌ Références au blueprint historique

### 2. Code de Référence (OBLIGATOIRE)

**✅ TOUJOURS utiliser `src_v2/` comme base :**
- Code conforme aux règles d'hygiène V4 (100% validé)
- Architecture modulaire avec vectora_core
- Handlers minimalistes délégant à vectora_core

**❌ NE JAMAIS utiliser `archive/_src/` (architecture legacy archivée) :**
- Contient 180MB+ de dépendances tierces
- Violations massives des règles d'hygiène
- Stubs et contournements non conformes
- **STATUT** : Archivé pour référence historique uniquement

---

## 🏗️ ENVIRONNEMENT AWS DE RÉFÉRENCE

### Configuration AWS Établie

**Région AWS principale :** `eu-west-3` (Paris)
- Toutes les ressources principales (S3, Lambda, CloudWatch)
- **INTERDIT** de créer des ressources dans une autre région sans justification

**Région Bedrock :** `us-east-1` (Virginie du Nord)
- Configuration validée E2E
- Modèle de référence : `anthropic.claude-3-sonnet-20240229-v1:0`

**Profil CLI principal :** `rag-lai-prod`
- Compte AWS : `786469175371`
- **OBLIGATOIRE** dans tous les exemples de commandes CLI

### Conventions de Nommage Établies

**Lambdas V2 :**
```
vectora-inbox-ingest-v2-dev
vectora-inbox-normalize-score-v2-dev
vectora-inbox-newsletter-v2-dev
```

**Buckets S3 :**
```
vectora-inbox-config-dev
vectora-inbox-data-dev
vectora-inbox-newsletters-dev
vectora-inbox-lambda-code-dev
```

**Stacks CloudFormation :**
```
vectora-inbox-s0-core-dev
vectora-inbox-s0-iam-dev
vectora-inbox-s1-runtime-dev
```

---

## 🚫 RÈGLES GOUVERNANCE (CRITIQUE)

### Source Unique de Vérité

**Principe fondamental**: Repo local = SEULE source de vérité

Toute modification du code, des layers, ou des configurations DOIT:
1. Être faite dans le repo local
2. Être commitée dans Git
3. Passer par les scripts build/deploy

### Interdiction Modification Directe AWS

❌ **INTERDIT**:
- `aws lambda update-function-code` (manuel)
- `aws s3 cp fichier.zip s3://...` (manuel)
- Édition dans console AWS
- Copie dev→stage sans scripts
- Création layers sans versioning

✅ **OBLIGATOIRE**:
- Modifier code dans repo local
- `python scripts/build/build_all.py`
- `python scripts/deploy/deploy_env.py --env dev`
- `python scripts/deploy/promote.py --to stage`

**Exception**: Debugging urgent avec validation post-facto obligatoire.

### Versioning Obligatoire

Chaque artefact a une version explicite dans fichier `VERSION` à la racine.

**Format**: MAJOR.MINOR.PATCH (ex: 1.2.3)

**Règles incrémentation**:
- MAJOR: Breaking changes
- MINOR: Nouvelles fonctionnalités
- PATCH: Corrections bugs

**Exemple**:
```
VECTORA_CORE_VERSION=1.2.3
# Nouvelle fonctionnalité → 1.3.0
# Correction bug → 1.2.4
# Breaking change → 2.0.0
```

### Workflow Standard

**Développement**:
1. Modifier code dans `src_v2/`
2. Incrémenter version dans `VERSION`
3. Build: `python scripts/build/build_all.py`
4. Deploy dev: `python scripts/deploy/deploy_env.py --env dev`
5. Test dev: `python scripts/test/test_e2e.py --env dev`

**Promotion**:
6. Promouvoir: `python scripts/deploy/promote.py --to stage --version X.Y.Z`
7. Test stage: `python scripts/test/test_e2e.py --env stage`

**Commit**:
8. `git add .`
9. `git commit -m "feat: description"`
10. `git push`

### Scripts de Gouvernance

**Build**:
- `scripts/build/build_layer_vectora_core.py` - Build layer vectora-core
- `scripts/build/build_layer_common_deps.py` - Build layer common-deps
- `scripts/build/build_all.py` - Build tous les artefacts

**Deploy**:
- `scripts/deploy/deploy_layer.py` - Deploy layer vers env
- `scripts/deploy/deploy_env.py` - Deploy complet vers env
- `scripts/deploy/promote.py` - Promouvoir version entre envs

---

## 🌍 GESTION DES ENVIRONNEMENTS

### Environnements Disponibles

**dev**: Développement et expérimentation  
**stage**: Pré-production et validation  
**prod**: Production clients réels

### Convention Nommage

**Ressources AWS**: `{nom}-{env}`  
**Config client**: `client_id` stable + `version` sémantique

### RÈGLE CRITIQUE POUR Q DEVELOPER

**Q Developer DOIT REFUSER tout déploiement AWS si l'environnement cible n'est PAS explicitement spécifié.**

❌ **INTERDIT**:
```bash
aws cloudformation deploy --stack-name vectora-inbox-s0-core
aws s3 mb s3://vectora-inbox-config
aws lambda create-function --function-name vectora-inbox-ingest-v2
```

✅ **OBLIGATOIRE**:
```bash
aws cloudformation deploy --stack-name vectora-inbox-s0-core-dev --parameter-overrides Env=dev
aws s3 mb s3://vectora-inbox-config-dev
aws lambda create-function --function-name vectora-inbox-ingest-v2-dev
```

**Si environnement non clair, Q Developer DOIT**:
1. Refuser d'exécuter la commande
2. Demander à l'utilisateur: "Sur quel environnement souhaitez-vous déployer? (dev/stage/prod)"
3. Attendre confirmation explicite avant de procéder

**Exemples questions Q Developer**:
- "Je vois que vous voulez déployer une Lambda. Sur quel environnement? (dev/stage/prod)"
- "Cette commande CloudFormation ne spécifie pas d'environnement. Confirmez-vous dev, stage ou prod?"
- "Avant de créer ce bucket S3, précisez l'environnement cible."

### Configuration AWS par Environnement

**Environnement DEV (Actuel)**:
```
Lambdas: vectora-inbox-{fonction}-v2-dev
Buckets: vectora-inbox-{type}-dev
Stacks: vectora-inbox-{stack}-dev
```

**Environnement STAGE (À créer)**:
```
Lambdas: vectora-inbox-{fonction}-v2-stage
Buckets: vectora-inbox-{type}-stage
Stacks: vectora-inbox-{stack}-stage
```

**Environnement PROD (Futur)**:
```
Lambdas: vectora-inbox-{fonction}-v2-prod
Buckets: vectora-inbox-{type}-prod
Stacks: vectora-inbox-{stack}-prod
```

---

## 📂 ORGANISATION FICHIERS ÉPHÉMÈRES (OBLIGATOIRE)

### Règle d'Or : Racine Propre

**✅ TOUJOURS stocker les fichiers temporaires dans `.tmp/` :**
```
.tmp/
├── events/          # Events de test Lambda
├── responses/       # Réponses Lambda (JSON)
├── items/           # Items temporaires (ingested, curated)
├── logs/            # Logs de debug locaux
└── README.md        # "Safe to delete anytime"
```

**✅ TOUJOURS stocker les artefacts de build dans `.build/` :**
```
.build/
├── layers/          # ZIPs de layers (vectora-core-*.zip)
├── packages/        # Packages Lambda
└── README.md        # "Regenerable artifacts"
```

**❌ NE JAMAIS laisser à la racine :**
- Events de test (`event_*.json`, `payload*.json`)
- Réponses Lambda (`response_*.json`)
- Items temporaires (`items_*.json`)
- Logs de debug (`logs_*.txt`)
- ZIPs de layers (`*.zip`)
- Scripts one-shot (`execute_*.py`)
- Configs temporaires (sauf dans `canonical/` ou `client-config-examples/`)

### Convention de Nommage Fichiers Temporaires

**Format obligatoire :**
```
.tmp/events/lai_weekly_v7_test_YYYYMMDD.json
.tmp/responses/normalize_v7_YYYYMMDD_HHMM.json
.tmp/items/curated_lai_v5_YYYYMMDD.json
.tmp/logs/debug_bedrock_YYYYMMDD.txt
```

**Avantages :**
- ✅ Tri chronologique automatique
- ✅ Identification rapide de l'origine
- ✅ Nettoyage facile (> 7 jours)

### Scripts de Nettoyage

**Créer `scripts/maintenance/cleanup_tmp.py` :**
```python
# Supprime fichiers .tmp/ > 7 jours
# Usage: python scripts/maintenance/cleanup_tmp.py
```

**Créer `scripts/maintenance/cleanup_build.sh` :**
```bash
# Supprime tous les artefacts .build/
# Usage: ./scripts/maintenance/cleanup_build.sh
```

### Checklist Avant Commit

- [ ] Aucun fichier `event_*.json` à la racine
- [ ] Aucun fichier `response_*.json` à la racine
- [ ] Aucun fichier `items_*.json` à la racine
- [ ] Aucun fichier `logs_*.txt` à la racine
- [ ] Aucun fichier `*.zip` à la racine
- [ ] Tous les temporaires dans `.tmp/`
- [ ] Tous les builds dans `.build/`

---

## 📁 STRUCTURE DE DONNÉES S3 (VALIDÉE)

**✅ TOUJOURS utiliser la structure V2 :**
```
s3://vectora-inbox-data-dev/
├── ingested/<client_id>/<YYYY>/<MM>/<DD>/items.json    # Sortie ingest-v2
├── curated/<client_id>/<YYYY>/<MM>/<DD>/items.json     # Sortie normalize-score-v2
└── raw/ (optionnel, debug uniquement)
```

**Configuration et canonical :**
```
s3://vectora-inbox-config-dev/
├── clients/<client_id>.yaml                            # Config client
├── canonical/scopes/*.yaml                             # Entités métier
├── canonical/prompts/global_prompts.yaml               # Prompts Bedrock
└── canonical/sources/source_catalog.yaml               # Sources d'ingestion
```

---

## 🔧 ORGANISATION DU CODE DANS SRC_V2

### Structure OBLIGATOIRE

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
│   │   ├── config_loader.py           # Chargement configurations S3
│   │   ├── s3_io.py                   # Opérations S3 standardisées
│   │   ├── models.py                  # Modèles de données communs
│   │   └── utils.py                   # Utilitaires transverses
│   ├── ingest/                        # Modules spécifiques Lambda ingest
│   │   ├── __init__.py                # run_ingest_for_client()
│   │   ├── source_fetcher.py          # Récupération contenus externes
│   │   └── content_parser.py          # Parsing RSS/HTML/API
│   ├── normalization/                 # Modules spécifiques Lambda normalize-score
│   │   ├── __init__.py                # run_normalize_score_for_client()
│   │   ├── normalizer.py              # Appels Bedrock normalisation
│   │   ├── matcher.py                 # Matching aux domaines de veille
│   │   └── bedrock_client.py          # Client Bedrock spécialisé
│   └── newsletter/                    # Modules spécifiques Lambda newsletter
│       ├── __init__.py                # run_newsletter_for_client()
│       ├── assembler.py               # Assemblage newsletter finale
│       └── editorial.py               # Génération contenu Bedrock
└── README.md
```

### Règles d'Imports OBLIGATOIRES

**Dans les handlers :**
```python
# Dans lambdas/ingest/handler.py
from vectora_core.ingest import run_ingest_for_client

# Dans lambdas/normalize_score/handler.py  
from vectora_core.normalization import run_normalize_score_for_client

# Dans lambdas/newsletter/handler.py
from vectora_core.newsletter import run_newsletter_for_client
```

**Dans vectora_core :**
```python
# Dans vectora_core/ingest/__init__.py
from ..shared import config_loader, s3_io, utils, models
from . import source_fetcher, content_parser

# Dans vectora_core/shared/config_loader.py
from . import s3_io  # Import relatif pour modules shared
```

---

## 🚫 INTERDICTIONS ABSOLUES

### NE JAMAIS proposer :

**Architecture historique :**
- ❌ 2 Lambdas (`ingest-normalize`, `engine`)
- ❌ Code dans `/src` (utiliser `src_v2/`)
- ❌ Références au blueprint historique

**Violations d'hygiène :**
- ❌ Dépendances tierces dans `/src` (boto3/, yaml/, requests/, etc.)
- ❌ Stubs ou contournements (`_yaml/`, `cyaml.py`)
- ❌ Extensions binaires (`.pyd`, `.so`, `.dll`)
- ❌ Métadonnées packages (`*-dist-info/`)
- ❌ Logique métier hardcodée dans handlers
- ❌ Duplication de vectora_core

**Configuration non validée :**
- ❌ Modèles Bedrock non testés
- ❌ Régions autres que us-east-1 pour Bedrock
- ❌ Nommage sans suffixes `-v2-dev`
- ❌ Autre profil CLI que `rag-lai-prod`

---

## 📦 GESTION DES LAMBDA LAYERS

### Layers Obligatoires

**Layer vectora-core :**
- Contient uniquement `vectora_core/`
- Nom : `vectora-inbox-vectora-core-dev`
- Taille max : 50MB compressé

**Layer common-deps :**
- Contient toutes les dépendances tierces
- Nom : `vectora-inbox-common-deps-dev`
- Structure obligatoire : `python/` à la racine du zip
- Dépendances standard : PyYAML, requests, feedparser, beautifulsoup4

### Organisation Dossiers Layers

**Structure obligatoire :**
```
layer_management/
├── active/              # Layers actuellement déployées
│   ├── vectora-core/    # Source vectora_core
│   └── common-deps/     # Source dépendances
├── archive/             # Anciennes versions
└── tools/               # Scripts de build
    ├── build_vectora_core.sh
    └── build_common_deps.sh
```

**❌ NE JAMAIS avoir à la racine :**
- `layer_build/` → Utiliser `.build/layers/`
- `layer_fix/` → Utiliser `layer_management/active/`
- `layer_vectora_core_approche_b/` → Utiliser `layer_management/active/vectora-core/`
- `python/` → Utiliser `.build/layers/python/`

### Règles de Construction

```bash
# Construction layer common-deps
mkdir .build/layers/python
cd .build/layers

# Installation (mode pur Python)
pip install --target python --no-binary PyYAML \
  PyYAML==6.0.1 \
  requests==2.31.0 \
  feedparser==6.0.10 \
  beautifulsoup4==4.14.3

# Création du zip
zip -r vectora-common-deps.zip python/
```

**Workflow de build :**
```bash
# 1. Build depuis layer_management/active/
cd layer_management/tools
./build_vectora_core.sh

# 2. Output dans .build/layers/
ls .build/layers/vectora-core-v12.zip

# 3. Upload vers S3
aws s3 cp .build/layers/vectora-core-v12.zip \
  s3://vectora-inbox-lambda-code-dev/layers/
```

**Validation obligatoire :**
- [ ] Structure `python/` à la racine
- [ ] Toutes dépendances présentes
- [ ] Pas d'extensions C (.so, .pyd)
- [ ] Test import local réussi
- [ ] Taille layer < 50MB

---

## ⚙️ CONFIGURATION BEDROCK

### Configuration Validée E2E

```bash
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
```

### Variables d'Environnement Standard

**Lambda ingest-v2 :**
```bash
ENV=dev
CONFIG_BUCKET=vectora-inbox-config-dev
DATA_BUCKET=vectora-inbox-data-dev
LOG_LEVEL=INFO
```

**Lambda normalize-score-v2 :**
```bash
ENV=dev
CONFIG_BUCKET=vectora-inbox-config-dev
DATA_BUCKET=vectora-inbox-data-dev
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
LOG_LEVEL=INFO
```

**Lambda newsletter-v2 :**
```bash
ENV=dev
CONFIG_BUCKET=vectora-inbox-config-dev
DATA_BUCKET=vectora-inbox-data-dev
NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
LOG_LEVEL=INFO
```

---

## 📋 RÈGLES DE CONFIGURATION CLIENT

### Emplacement et Structure

**Emplacement :** `s3://vectora-inbox-config-{env}/clients/{client_id}.yaml`

**Template de référence :** `client-config-examples/client_template_v2.yaml`

**Sections requises :**
```yaml
client_id: lai_weekly_v3
watch_domains:
  - domain_id: tech_lai_ecosystem
    min_domain_score: 0.25
  - domain_id: regulatory_lai
    min_domain_score: 0.20

newsletter_layout:
  sections:
    - section_id: top_signals
      max_items: 5
    - section_id: partnerships
      max_items: 3

scoring_config:
  enable_fallback_mode: true
  require_high_confidence_for_multiple: false
```

### Validation Configuration

- **Schema YAML** : Validation obligatoire avant upload
- **Domaines** : Doivent exister dans `canonical/scopes/`
- **Seuils** : Entre 0.1 et 0.9
- **Sections** : Cohérentes avec le layout newsletter

---

## 🏗️ RÈGLES DE DÉPLOIEMENT INFRASTRUCTURE

### Ordre Obligatoire

1. **S0-core** : Buckets S3
2. **S0-iam** : Rôles IAM
3. **S1-runtime** : Lambdas

### Commandes de Déploiement

```bash
# S0-core
aws cloudformation deploy \
  --template-file infra/s0-core.yaml \
  --stack-name vectora-inbox-s0-core-dev \
  --parameter-overrides Env=dev ProjectName=vectora-inbox \
  --region eu-west-3 \
  --profile rag-lai-prod

# S0-iam
aws cloudformation deploy \
  --template-file infra/s0-iam.yaml \
  --stack-name vectora-inbox-s0-iam-dev \
  --capabilities CAPABILITY_IAM \
  --region eu-west-3 \
  --profile rag-lai-prod

# S1-runtime
aws cloudformation deploy \
  --template-file infra/s1-runtime.yaml \
  --stack-name vectora-inbox-s1-runtime-dev \
  --region eu-west-3 \
  --profile rag-lai-prod
```

### Sauvegarde des Outputs

```bash
# Sauvegarder les outputs de chaque stack
aws cloudformation describe-stacks \
  --stack-name vectora-inbox-s0-core-dev \
  --region eu-west-3 \
  --profile rag-lai-prod \
  > infra/outputs/s0-core-dev.json
```

---

## 🔒 RÈGLES DE SÉCURITÉ

### Buckets S3

- **Chiffrement** : SSE-S3 obligatoire
- **Accès public** : Bloqué sur tous les buckets
- **Versioning** : Activé pour historique
- **Tags** : Projet et environnement obligatoires

### Rôles IAM

- **Permissions minimales** : Chaque Lambda a ses permissions strictes
- **Séparation** : Ingest ne peut pas écrire newsletters
- **Bedrock** : Accès limité à la région de déploiement
- **SSM** : Accès paramètres spécifiques uniquement

### Secrets et Clés

- **SSM Parameter Store** : Stockage obligatoire pour clés API
- **Pas de hardcoding** : Aucune clé dans le code
- **Rotation** : Planifiée pour clés critiques

---

## 📸 SNAPSHOTS ET ROLLBACK

### Obligatoire Avant

- Déploiement Lambda stage/prod
- Modification canonical
- Promotion stage → prod

### Commandes

```bash
# Créer snapshot
python scripts/maintenance/create_snapshot.py --env dev --name "pre_deploy"

# Rollback
python scripts/maintenance/rollback_snapshot.py --snapshot "pre_deploy_YYYYMMDD"
```

### Snapshots Disponibles

Consulter `docs/snapshots/` pour la liste des snapshots disponibles.

---

## 🔧 RÈGLES D'EXÉCUTION SCRIPTS

### Output Scripts de Test

**✅ TOUJOURS rediriger les outputs vers `.tmp/` :**
```bash
# Scripts d'invocation
python scripts/invoke/invoke_normalize_score_v2.py \
  --client-id lai_weekly_v7 \
  --output .tmp/responses/normalize_v7_$(date +%Y%m%d_%H%M).json

# Scripts d'analyse
python scripts/analysis/analyze_items.py \
  --input .tmp/items/curated_lai_v7.json \
  --output .tmp/logs/analysis_$(date +%Y%m%d).txt
```

**❌ NE JAMAIS écrire directement à la racine :**
```bash
# ❌ INTERDIT
python scripts/invoke/invoke_normalize_score_v2.py > response.json

# ✅ CORRECT
python scripts/invoke/invoke_normalize_score_v2.py > .tmp/responses/response_$(date +%Y%m%d).json
```

### Scripts One-Shot

**Règle :** Scripts one-shot doivent être dans `scripts/maintenance/` ou supprimés après usage.

**Exemples à déplacer :**
- `execute_bedrock_only_fix.py` → `scripts/maintenance/` ou supprimer
- `phase6_detailed_comparison.py` → `scripts/analysis/` ou supprimer
- `phase7_metrics_analysis.py` → `scripts/analysis/` ou supprimer

---

## 🧪 RÈGLES DE TESTS

### Structure des Tests

```
tests/
├── unit/                              # Tests unitaires
│   ├── test_bedrock_matcher.py
│   └── test_normalization_open_world.py
├── integration/                       # Tests d'intégration
│   ├── test_bedrock_matching_integration.py
│   └── test_ingest_v2_active_scan.py
├── fixtures/                          # Données de test
│   └── lai_weekly_ingested_sample.json
└── data_snapshots/                    # Snapshots de validation
    └── real_ingested_items_17dec.json
```

### Template de Test E2E Standard

**✅ TOUJOURS utiliser le template standardisé pour tests E2E :**

**Template** : `docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`  
**Guide** : `docs/templates/GUIDE_UTILISATION_TEMPLATE_E2E.md`

**Avantages** :
- Comparabilité temporelle (v7 vs v8 vs v9)
- Métriques standardisées avec colonne "vs Baseline"
- Format cohérent pour Q Developer
- Traçabilité des améliorations

**Quand utiliser** :
- Test après modification (prompt, scope, seuil)
- Validation baseline nouvelle version
- Monitoring hebdomadaire/mensuel
- Décision GO/NO-GO production

**Prompt recommandé pour Q** :
```
Exécute un test E2E complet de lai_weekly_v8 en utilisant le template 
docs/templates/TEMPLATE_TEST_E2E_STANDARD.md

Baseline : docs/reports/rapport_e2e_complet_lai_weekly_v6_20260127.md

Remplis toutes les sections avec métriques quantitatives et comparaison vs baseline.
```

### Client de Référence E2E

**Client :** `lai_weekly_v3`

**Dernière validation (18 décembre 2025) :**
- ✅ 15 items LAI réels traités
- ✅ 30 appels Bedrock (100% succès)
- ✅ 36 entités extraites
- ✅ Configuration lai_weekly_v3.yaml appliquée
- ✅ Temps d'exécution : 163s
- ✅ Coût : $0.21/run

### Critères de Validation

**Métriques attendues :**
- ✅ StatusCode: 200
- ✅ items_matched >= 10 (66%+)
- ✅ Distribution équilibrée tech/regulatory
- ✅ Taux de matching > 60%

---

## 📊 RÈGLES DE MONITORING ET LOGS

### Configuration Logs

- **Rétention** : 7 jours par défaut
- **Niveau** : INFO en production, DEBUG en développement
- **Groupes** : `/aws/lambda/vectora-inbox-{function}-{env}`

### Métriques Clés

**Par Lambda :**
- Temps d'exécution
- Taux d'erreur
- Nombre d'invocations
- Coût Bedrock

**Métier :**
- Nombre d'items traités
- Taux de matching
- Distribution par domaine
- Qualité des scores

### Alertes Obligatoires

- Échecs Lambda (> 5%)
- Timeouts (> 2 par heure)
- Erreurs Bedrock (ThrottlingException)
- Coût quotidien > seuil

---

## 📋 CHECKLIST AVANT TOUTE PROPOSITION

### Avant de proposer du code, Q DOIT vérifier :

**Architecture :**
- [ ] Utilise l'architecture 3 Lambdas V2
- [ ] Code basé sur `src_v2/`
- [ ] Handlers délèguent à vectora_core
- [ ] Aucune référence à l'architecture historique

**Configuration :**
- [ ] Bedrock : us-east-1 + Sonnet 3 (validé)
- [ ] Nommage : suffixes `-v2-dev`
- [ ] Variables d'environnement standard
- [ ] Structure S3 : ingested/ + curated/

**Conformité :**
- [ ] Respecte les règles d'hygiène V4
- [ ] Configuration pilote le comportement
- [ ] Aucune logique hardcodée client-spécifique
- [ ] Modules partagés dans vectora_core/shared/

**Déploiement :**
- [ ] Ordre des stacks respecté
- [ ] Outputs sauvegardés
- [ ] Layers validées
- [ ] Tests E2E passés

---

## ✅ BONNES PRATIQUES RECOMMANDÉES

### Pattern Handler Standard

```python
def lambda_handler(event, context):
    try:
        # 1. Validation paramètres
        client_id = event.get("client_id")
        if not client_id:
            return {"statusCode": 400, "body": {"error": "ConfigurationError"}}
        
        # 2. Variables d'environnement
        env_vars = {
            "CONFIG_BUCKET": os.environ.get("CONFIG_BUCKET"),
            "DATA_BUCKET": os.environ.get("DATA_BUCKET"),
        }
        
        # 3. Appel vectora_core
        result = run_xxx_for_client(
            client_id=client_id,
            env_vars=env_vars
        )
        
        return {"statusCode": 200, "body": result}
    
    except Exception as e:
        return {"statusCode": 500, "body": {"error": str(e)}}
```

### Configuration Pilotée

```python
# Lire depuis client_config
client_config = config_loader.load_client_config(client_id, config_bucket)
watch_domains = client_config.get('watch_domains', [])

# Lire depuis canonical
canonical_scopes = config_loader.load_canonical_scopes(config_bucket)
```

---

## 🎯 VALIDATION E2E DE RÉFÉRENCE

### Flux Validé

```
Sources LAI → ingest-v2 → S3 ingested/ → normalize-score-v2 → S3 curated/ → newsletter-v2
```

### Commandes de Test

```bash
# Test ingest-v2
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v3

# Test normalize-score-v2
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v3

# Test newsletter-v2 (à implémenter)
python scripts/invoke/invoke_newsletter_v2.py --client-id lai_weekly_v3
```

---

## 📚 DOCUMENTATION DE RÉFÉRENCE

### Documents Techniques
- `docs/diagnostics/src_v2_hygiene_audit_v2.md` (conformité validée)
- `docs/design/vectora_inbox_v2_engine_overview.md` (architecture complète)
- `docs/design/vectora_inbox_v2_bedrock_calls_map_lai_weekly_v3.md` (appels détaillés)

### Contrats Métier
- `contracts/lambdas/ingest_v2.md` (synchronisé avec code réel)
- `contracts/lambdas/normalize_score_v2.md` (synchronisé avec code réel)
- `contracts/lambdas/newsletter_v2.md` (à implémenter)

### Configuration
- `client-config-examples/lai_weekly_v3.yaml` (validé E2E)
- `canonical/prompts/global_prompts.yaml` (prompts Bedrock)
- `canonical/scopes/*.yaml` (entités métier)

---

## 🎯 OBJECTIF FINAL POUR Q DEVELOPER

**Amazon Q Developer doit TOUJOURS :**

1. **Proposer l'architecture 3 Lambdas V2 validée**
2. **Utiliser le code de référence `src_v2/`**
3. **Respecter la configuration Bedrock validée**
4. **Maintenir la conformité aux règles d'hygiène V4**
5. **Préserver le pilotage par configuration**
6. **Suivre les conventions AWS établies**
7. **Valider avec le client de référence lai_weekly_v3**

**Résultat attendu :** Code conforme, maintenable et évolutif basé sur l'architecture V2 stabilisée, documentée et validée E2E.

---

*Règles de Développement Vectora Inbox - Version Unifiée*  
*Date : 18 décembre 2025*  
*Statut : ✅ ARCHITECTURE V2 VALIDÉE E2E - RÈGLES UNIFIÉES*