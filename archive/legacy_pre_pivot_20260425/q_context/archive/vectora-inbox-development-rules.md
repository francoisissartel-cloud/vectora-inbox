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

### 3. Déploiement AWS Complet Obligatoire (CRITIQUE)

**Q Developer DOIT TOUJOURS vérifier TOUS les composants lors d'un déploiement AWS.**

**RÈGLE D'OR**: Un déploiement AWS = Code + Data + Validation

**Checklist complète**: Voir section "CHECKLIST DÉPLOIEMENT AWS COMPLET" dans development-rules.md

**Q DOIT TOUJOURS**:
- ✅ Identifier TOUS les fichiers modifiés (code + canonical + configs)
- ✅ Déployer layers SI code modifié
- ✅ Upload canonical/ vers S3 SI canonical/ modifié
- ✅ Upload client-configs vers S3 SI configs modifiés
- ✅ Vérifier présence fichiers sur S3 après upload
- ✅ Lancer test E2E AWS pour validation
- ✅ Consulter logs Lambda pour confirmer

**Q NE DOIT JAMAIS**:
- ❌ Assumer que fichiers canonical sont déjà sur S3
- ❌ Dire "déploiement complété" sans vérifier S3
- ❌ Oublier d'uploader fichiers canonical après modification
- ❌ Déployer code sans déployer data associée

**Phrase magique**: "Ai-je créé/modifié des fichiers dans canonical/? Sont-ils sur S3?"

### 4. Mode Assistant Guidé

### 4. Mode Assistant Guidé

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

### Workflow Standard (AVEC SYSTÈME DE CONTEXTES)

**Phase 1: Test Local (OBLIGATOIRE)**:
1. Créer contexte: `python tests/local/test_e2e_runner.py --new-context "Description test"`
2. Exécuter test local: `python tests/local/test_e2e_runner.py --run`
3. Vérifier succès: `python tests/local/test_e2e_runner.py --status`

**Phase 2: Build et Deploy Dev (SI LOCAL OK)**:
4. Modifier code dans `src_v2/`
5. Incrémenter version dans `VERSION`
6. Build: `python scripts/build/build_all.py`
7. Deploy dev: `python scripts/deploy/deploy_env.py --env dev`
8. **Upload canonical si modifié**: `aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod`

**Phase 3: Test AWS Dev (VALIDATION)**:
9. Promouvoir contexte: `python tests/aws/test_e2e_runner.py --promote "Validation E2E"`
10. Exécuter test AWS: `python tests/aws/test_e2e_runner.py --run`
11. Vérifier succès: `python tests/aws/test_e2e_runner.py --status`

**Phase 4: Promotion Stage (SI AWS DEV OK)**:
12. Promouvoir: `python scripts/deploy/promote.py --to stage --version X.Y.Z`
13. Test stage: `python tests/aws/test_e2e_runner.py --run` (avec client stage)

**Phase 5: Commit**:
14. `git add .`
15. `git commit -m "feat: description"`
16. `git push`

**🛡️ PROTECTIONS AUTOMATIQUES**:
- ❌ Impossible de promouvoir vers AWS sans succès local
- ❌ Impossible de promouvoir vers stage sans succès dev
- ✅ Traçabilité complète via registry.json

---

## 🚀 CHECKLIST DÉPLOIEMENT AWS COMPLET (CRITIQUE)

### RÈGLE D'OR

**Un déploiement AWS = Code + Data + Validation**

### Composants Obligatoires

**1. Code Lambda (Layers)**:
- [ ] Build layers: `python scripts/build/build_all.py`
- [ ] Deploy layers: `python scripts/deploy/deploy_env.py --env dev`
- [ ] Vérifier update Lambdas (automatique via deploy_env.py)

**2. Fichiers Canonical S3** (SOUVENT OUBLIÉ!):
- [ ] Identifier fichiers canonical modifiés: `git status canonical/`
- [ ] Upload vers S3: `aws s3 sync canonical/ s3://vectora-inbox-config-{env}/canonical/ --profile rag-lai-prod`
- [ ] Vérifier présence: `aws s3 ls s3://vectora-inbox-config-{env}/canonical/prompts/ --recursive --profile rag-lai-prod`

**3. Client Configs**:
- [ ] Vérifier configs modifiés: `git status client-config-examples/`
- [ ] Upload si nécessaire (généralement auto-généré par runners)

**4. Validation Post-Déploiement**:
- [ ] Test E2E AWS: `python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_vX --env dev`
- [ ] Vérifier logs Lambda (pas d'erreurs FileNotFound)
- [ ] Confirmer résultats attendus

### Matrice Décision Rapide

| Changement | Build | Deploy Layer | Upload Canonical | Test E2E |
|------------|-------|--------------|------------------|----------|
| Code Python | ✅ | ✅ | ❌ | ✅ |
| Canonical prompts | ❌ | ❌ | ✅ | ✅ |
| Canonical domains | ❌ | ❌ | ✅ | ✅ |
| Code + Canonical | ✅ | ✅ | ✅ | ✅ |

### Détection Problèmes Canonical

**Symptômes**:
- Lambda logs: `FileNotFoundError: canonical/prompts/domain_scoring/...`
- Lambda logs: `No such key: canonical/domains/...`
- Tests locaux OK, tests AWS KO

**Diagnostic**:
```bash
# Vérifier fichiers locaux
ls canonical/prompts/domain_scoring/

# Vérifier S3
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ --profile rag-lai-prod

# Upload si manquant
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod
```

### Règles Q Developer

**AVANT de dire "Déploiement complété"**:
1. Ai-je créé/modifié des fichiers dans canonical/?
2. Ces fichiers existent-ils sur S3?
3. Le test E2E AWS passe-t-il?

**JAMAIS assumer**:
❌ "Le code est déployé donc c'est bon"
❌ "Les fichiers canonical sont déjà sur S3"
❌ "Ça marche en local donc ça marchera sur AWS"

**TOUJOURS vérifier**:
✅ "J'ai vérifié que TOUS les fichiers nécessaires sont sur S3"
✅ "J'ai lancé un test E2E AWS pour confirmer"
✅ "J'ai consulté les logs Lambda pour vérifier"

### Scripts de Gouvernance

**Build**:
- `scripts/build/build_layer_vectora_core.py` - Build layer vectora-core
- `scripts/build/build_layer_common_deps.py` - Build layer common-deps
- `scripts/build/build_all.py` - Build tous les artefacts

**Deploy**:
- `scripts/deploy/deploy_layer.py` - Deploy layer vers env
- `scripts/deploy/deploy_env.py` - Deploy complet vers env (layers + mise à jour Lambdas automatique)
- `scripts/deploy/promote.py` - Promouvoir version entre envs

**Comportement deploy_env.py** (depuis février 2026):
1. Publie vectora-core layer
2. Publie common-deps layer
3. Récupère ARNs des layers publiés
4. Met à jour automatiquement les 3 Lambdas avec nouveaux layers
5. Gestion erreurs: Lambda manquante = warning (continue)

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

## 🧪 RÈGLES DE TESTS E2E (SYSTÈME DE CONTEXTES)

### Organisation Rapports E2E (OBLIGATOIRE)

**Q Developer DOIT TOUJOURS créer les rapports E2E dans le dossier centralisé.**

**Emplacement obligatoire** : `docs/reports/e2e/`

**Convention de nommage** : `test_e2e_v{VERSION}_{TYPE}_{DATE}.md`

**Types de rapports** :
- `rapport` : Rapport complet du test E2E
- `resume` : Résumé exécutif
- `post_mortem` : Analyse post-mortem (si échec ou problème)

**Exemples** :
- `docs/reports/e2e/test_e2e_v11_rapport_2026-02-02.md`
- `docs/reports/e2e/test_e2e_v12_resume_2026-02-03.md`
- `docs/reports/e2e/test_e2e_v13_post_mortem_2026-02-04.md`

**Index** : `docs/reports/e2e/INDEX.md` (liste tous les rapports disponibles)

**Règles Q Developer** :
- ✅ Créer rapport dans `docs/reports/e2e/`
- ✅ Suivre convention de nommage
- ✅ Mettre à jour INDEX.md après création
- ❌ Ne jamais créer rapport E2E ailleurs (docs/reports/, docs/maintenance/, etc.)
- ❌ Ne jamais créer rapport sans version (v{X})

## 🤖 DÉTECTION AUTOMATIQUE TESTS E2E (CRITIQUE)

### Règle de Détection

**Q Developer DOIT détecter automatiquement une demande de test E2E si** :

**Triggers détection** :
- Prompt contient "test E2E" ou "test e2e" ou "E2E"
- Prompt contient "invoke_normalize_score_v2.py"
- Prompt contient "lai_weekly_vX" (pattern version)
- Prompt contient "tester" + nom client
- Prompt contient "@e2e" (prompt magique)

### Comportement Obligatoire Après Détection

**Si détection → Q DOIT** :

1. **STOP** : Ne pas exécuter immédiatement
2. **CONSULTER** : Lire section "RÈGLES DE TESTS E2E"
3. **PROPOSER** : Plan complet avec template standard
4. **DEMANDER** : "Voulez-vous A) Test technique simple OU B) Test E2E complet ?"
5. **ATTENDRE** : Validation utilisateur
6. **EXÉCUTER** : Workflow complet après validation

### Exemple Détection

**Prompt utilisateur** :
```
Teste lai_weekly_v11
```

**Q DOIT répondre** :
```
🔍 DÉTECTION : Test E2E

Je détecte une demande de test E2E pour lai_weekly_v11.

Selon Q Context, un test E2E peut être :

A) **Test technique simple**
   - Exécute workflow (ingest + normalize)
   - Vérifie StatusCode 200
   - Rapport basique
   - Durée : ~5 min

B) **Test E2E complet** (recommandé)
   - Utilise template standard
   - Analyse item par item
   - Métriques détaillées
   - Comparaison baseline
   - Coûts calculés
   - Rapport exploitable
   - Durée : ~15 min

Que souhaitez-vous ?
```

### Exception

**Si prompt contient "juste" ou "seulement" ou "quick"** :
```
Fais juste un test rapide de v11
```
→ Q peut exécuter test technique simple sans proposer plan

### Prompts Magiques

**Référence** : `.q-context/prompts-magiques.md`

**Si prompt contient "@e2e-complet"** :
- Q exécute automatiquement test E2E complet
- Utilise template standard
- Compare avec baseline spécifiée
- Génère rapport exploitable

**Si prompt contient "@analyse-s3"** :
- Q télécharge fichiers S3 existants
- Analyse sans re-exécuter workflow
- Génère rapport détaillé

### Système de Contextes Obligatoire

**Q Developer DOIT TOUJOURS utiliser le système de contextes pour les tests E2E.**

**Document de référence**: `.q-context/vectora-inbox-test-e2e-system.md`

### Système Client Config Automatisé

**Principe**: 1 contexte test = 1 client_config dédié = 1 dossier S3 isolé

**Mapping**:

| Contexte | Environnement | Client ID | Dossier S3 |
|----------|---------------|-----------|------------|
| test_context_001 | local | lai_weekly_test_001 | N/A (local) |
| test_context_001 | aws | lai_weekly_v1 | s3://.../lai_weekly_v1/ ✅ |
| test_context_002 | local | lai_weekly_test_002 | N/A (local) |
| test_context_002 | aws | lai_weekly_v2 | s3://.../lai_weekly_v2/ ✅ |

**Génération automatique**:
```bash
# Local: génère lai_weekly_test_001 + config
python tests/local/test_e2e_runner.py --new-context "Test X"

# AWS: génère lai_weekly_v1 + config + upload S3
python tests/aws/test_e2e_runner.py --promote "Validation"
```

**Isolation S3 garantie**: Chaque vX = nouveau dossier S3 = workflow E2E complet

### Workflow Test E2E Standard

**Étape 1: Test Local (OBLIGATOIRE)**
```bash
# Créer nouveau contexte
python tests/local/test_e2e_runner.py --new-context "Test domain scoring fix"

# Exécuter test local
python tests/local/test_e2e_runner.py --run

# Vérifier succès
python tests/local/test_e2e_runner.py --status
```

**Étape 2: Déploiement AWS Dev (SI LOCAL OK)**
```bash
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

**Étape 3: Test AWS Dev (VALIDATION)**
```bash
# Promouvoir contexte (vérifie automatiquement succès local)
python tests/aws/test_e2e_runner.py --promote "Validation E2E"

# Exécuter test AWS
python tests/aws/test_e2e_runner.py --run
```

**Étape 4: Promotion Stage (SI AWS DEV OK)**
```bash
python scripts/deploy/promote.py --to stage --version X.Y.Z
```

### Invocation Workflow E2E

**Script standardisé**: `scripts/invoke/invoke_e2e_workflow.py`

**Usage direct**:
```bash
python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_v1 --env dev
```

**Workflow exécuté**:
1. 📥 Ingest: `vectora-inbox-ingest-v2-{env}`
2. 🤖 Normalize: `vectora-inbox-normalize-score-v2-{env}`
3. 📰 Newsletter: `vectora-inbox-newsletter-v2-{env}`

**Intégration runner AWS**: Le runner AWS (`tests/aws/test_e2e_runner.py --run`) utilise automatiquement ce script pour exécuter le workflow E2E complet.

**Règles Q Developer**:
- ✅ Utiliser `invoke_e2e_workflow.py` pour tests E2E AWS
- ✅ Invoquer workflow complet (pas seulement normalize)
- ✅ Vérifier succès de chaque étape
- ❌ Ne jamais invoquer Lambdas individuellement pour test E2E
- ❌ Ne jamais bypasser une étape du workflow

### Protections Automatiques

**🛡️ BLOCAGE AWS sans succès local**:
- ❌ Impossible de promouvoir vers AWS sans test local réussi
- ❌ Impossible de promouvoir vers stage sans test AWS dev réussi
- ✅ Messages clairs avec actions requises

### Règles Critiques

1. **Jamais Réutiliser Contexte**: Créer nouveau contexte après chaque modification
2. **Jamais AWS Sans Local**: Test local obligatoire avant déploiement AWS
3. **Jamais Stage Sans Dev**: Test AWS dev obligatoire avant promotion stage
4. **Toujours Documenter Purpose**: Description claire du test
5. **Client Config Auto**: Génération automatique via runners (pas de création manuelle)
6. **Isolation S3**: Chaque test AWS = nouveau client_id vX = nouveau dossier S3

### Règles Client Config

**Q DOIT**:
- Générer client_config automatiquement via runners
- Utiliser naming: `lai_weekly_test_XXX` (local), `lai_weekly_vX` (AWS)
- Uploader config vers S3 avant test AWS
- Vérifier isolation S3 (nouveau dossier)

**Q NE DOIT JAMAIS**:
- Créer `lai_weekly_vX` manuellement
- Réutiliser client_id d'un test précédent
- Bypasser ingestion si données S3 existent

**Structure repo**:
```
client-config-examples/
├── production/          # Configs prod
├── test/
│   ├── local/          # lai_weekly_test_XXX
│   └── aws/            # lai_weekly_vX
├── templates/          # Template réutilisable
└── archive/            # Anciens configs
```

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
8. **Maintenir le blueprint à jour** (NOUVEAU)

**Résultat attendu :** Code conforme, maintenable et évolutif basé sur l'architecture V2 stabilisée, documentée et validée E2E.

---

## 📋 MAINTENANCE DU BLUEPRINT (CRITIQUE)

**Q Developer DOIT proposer la mise à jour du blueprint pour tout changement majeur.**

### Changements Majeurs Nécessitant Mise à Jour Blueprint

**Architecture** :
- ✅ Ajout/suppression/modification de Lambda
- ✅ Changement de structure S3 (buckets, paths)
- ✅ Modification des rôles IAM

**Bedrock** :
- ✅ Changement de modèle Bedrock
- ✅ Changement de région Bedrock
- ✅ Nouveau système de prompts

**Configuration** :
- ✅ Nouvelles variables d'environnement critiques
- ✅ Changement de client de référence
- ✅ Modification du système de versioning

### Workflow Q Developer

**Quand Q Developer fait un changement majeur** :

1. **Modifier le code** (src_v2/, infra/, etc.)
2. **Proposer automatiquement** : "Je vais aussi mettre à jour le blueprint pour refléter ce changement"
3. **Mettre à jour** `docs/architecture/blueprint-v2-ACTUAL-2026.yaml`
4. **Mettre à jour** la date `last_updated` dans le blueprint
5. **Ajouter** une entrée dans `metadata.changes`
6. **Commit ENSEMBLE** : code + blueprint dans le même commit

### Exemple de Prompt Q Developer

```
J'ai modifié [description].

Je vais aussi mettre à jour le blueprint docs/architecture/blueprint-v2-ACTUAL-2026.yaml
pour refléter ce changement dans la section [architecture/bedrock/etc.].

Voulez-vous que je procède ?
```

### Fichier de Référence

**Guide complet** : `docs/architecture/BLUEPRINT_MAINTENANCE.md`

---

*Règles de Développement Vectora Inbox - Version Unifiée*  
*Date : 18 décembre 2025*  
*Statut : ✅ ARCHITECTURE V2 VALIDÉE E2E - RÈGLES UNIFIÉES*