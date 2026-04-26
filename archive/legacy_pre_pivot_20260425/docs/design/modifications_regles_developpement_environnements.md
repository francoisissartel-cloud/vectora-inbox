
# Modifications Recommandées - Règles de Développement Vectora Inbox

**Date**: 2026-01-30  
**Objectif**: Intégrer la gestion des environnements dev/stage/prod dans les règles de développement  
**Fichier cible**: `.q-context/vectora-inbox-development-rules.md`

---

## 📋 MODIFICATIONS À APPORTER

### 1. Nouvelle Section: Gestion des Environnements

**Emplacement**: Après la section "🏗️ ENVIRONNEMENT AWS DE RÉFÉRENCE"

```markdown
## 🌍 GESTION DES ENVIRONNEMENTS

### Stratégie Multi-Environnements

Vectora Inbox utilise 3 environnements distincts pour garantir stabilité et qualité:

**dev (Développement)**
- Expérimentation et tests de nouvelles fonctionnalités
- Modifications fréquentes autorisées
- Données de test et POC
- Coûts AWS non critiques
- Pas de SLA

**stage (Pré-production)**
- Validation avant mise en production
- Code stable uniquement
- Tests E2E complets avec données réalistes
- Réplique de l'environnement prod
- Validation métier requise

**prod (Production)**
- Clients réels et newsletters opérationnelles
- Code validé en stage uniquement
- Aucune modification directe
- Monitoring actif et alertes
- SLA et disponibilité critiques

### Convention de Nommage Multi-Environnements

**Ressources AWS (Lambdas, Buckets, Layers, Stacks):**
```
{resource-base-name}-{env}

Exemples:
vectora-inbox-ingest-v2-dev
vectora-inbox-ingest-v2-stage
vectora-inbox-ingest-v2-prod

vectora-inbox-config-dev
vectora-inbox-config-stage
vectora-inbox-config-prod

vectora-inbox-vectora-core-dev
vectora-inbox-vectora-core-prod
```

**Configurations Client:**

❌ **ANCIEN (à éviter):**
```yaml
client_profile:
  client_id: "lai_weekly_v7"  # Version dans l'ID
```

✅ **NOUVEAU (recommandé):**
```yaml
client_profile:
  client_id: "lai_weekly"     # ID stable
  version: "7.0.0"            # Version sémantique séparée
  
metadata:
  config_version: "7.0.0"
  changelog:
    - version: "7.0.0"
      date: "2026-01-30"
      changes: "Extraction dates Bedrock, prompts éditoriaux"
```

**Déploiement par environnement:**
```
dev:   s3://vectora-inbox-config-dev/clients/lai_weekly.yaml
stage: s3://vectora-inbox-config-stage/clients/lai_weekly.yaml
prod:  s3://vectora-inbox-config-prod/clients/lai_weekly.yaml
```

**Avantages:**
- ✅ Même configuration client peut être promue entre environnements
- ✅ Versioning sémantique clair (7.0.0 → 7.1.0 → 8.0.0)
- ✅ Pas de confusion entre version config et environnement
- ✅ Historique des changements dans metadata.changelog

### Workflow de Promotion Code

```
┌─────┐    Validation    ┌───────┐    Validation    ┌──────┐
│ dev │ ───────────────> │ stage │ ───────────────> │ prod │
└─────┘    + Tests       └───────┘    + Approbation └──────┘
```

**Étapes de promotion dev → stage:**
1. Tests locaux passés
2. Tests E2E dev réussis
3. Snapshot dev créé
4. Code promu vers stage
5. Tests E2E stage réussis
6. Validation métier

**Étapes de promotion stage → prod:**
1. Stage stable pendant 2 semaines minimum
2. Tous les tests E2E passés
3. Validation métier complète
4. Approbation formelle
5. Snapshot stage créé
6. Déploiement prod
7. Monitoring renforcé 48h

### Variables d'Environnement Lambda

**Toutes les Lambdas doivent lire la variable `ENV`:**

```python
# Dans handler.py
import os

def lambda_handler(event, context):
    env = os.environ.get("ENV", "dev")
    
    # Construction noms buckets dynamiques
    config_bucket = f"vectora-inbox-config-{env}"
    data_bucket = f"vectora-inbox-data-{env}"
    newsletters_bucket = f"vectora-inbox-newsletters-{env}"
    
    # Comportement adapté par environnement
    if env == "prod":
        # Monitoring renforcé, pas de debug
        log_level = "INFO"
        enable_debug = False
    elif env == "stage":
        # Logs détaillés pour validation
        log_level = "INFO"
        enable_debug = True
    else:  # dev
        # Debug complet
        log_level = "DEBUG"
        enable_debug = True
```

**Variables d'environnement standard par Lambda:**

```bash
# Communes à toutes les Lambdas
ENV=dev|stage|prod
PROJECT_NAME=vectora-inbox
CONFIG_BUCKET=vectora-inbox-config-{env}
DATA_BUCKET=vectora-inbox-data-{env}
LOG_LEVEL=INFO|DEBUG

# Spécifiques selon Lambda
NEWSLETTERS_BUCKET=vectora-inbox-newsletters-{env}  # newsletter-v2
BEDROCK_MODEL_ID=eu.anthropic.claude-sonnet-4-5-20250929-v1:0
PUBMED_API_KEY_PARAM=/rag-lai/{env}/pubmed/api-key
```

### Commandes AWS CLI par Environnement

**Toujours spécifier l'environnement dans les commandes:**

```bash
# ❌ MAUVAIS (environnement implicite)
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev

# ✅ BON (environnement explicite via variable)
ENV=dev
aws lambda invoke --function-name vectora-inbox-ingest-v2-${ENV}

# ✅ BON (environnement dans script)
python scripts/invoke/invoke_ingest_v2.py --env dev --client-id lai_weekly
```

### Scripts de Promotion

**Créer scripts standardisés pour promotion:**

```bash
# Promotion dev → stage
./scripts/deploy/promote_dev_to_stage.sh --client lai_weekly --validate

# Promotion stage → prod
./scripts/deploy/promote_stage_to_prod.sh --client lai_weekly --approve
```

**Contenu minimal script promotion:**
1. Validation pré-requis (tests passés, snapshot créé)
2. Copie code Lambda vers nouvel environnement
3. Copie layers vers nouvel environnement
4. Copie configurations S3 vers nouvel environnement
5. Tests post-déploiement
6. Rollback automatique si échec
```

---

### 2. Nouvelle Section: Snapshots et Rollback

**Emplacement**: Après la section "🔧 RÈGLES D'EXÉCUTION SCRIPTS"

```markdown
## 📸 SNAPSHOTS ET ROLLBACK

### Principe: Toujours Pouvoir Revenir en Arrière

Avant toute modification majeure, créer un snapshot complet de l'environnement pour permettre un rollback rapide en cas de problème.

### Quand Créer un Snapshot

**Obligatoire:**
- ✅ Avant déploiement Lambda en stage ou prod
- ✅ Avant modification canonical (scopes, prompts, sources)
- ✅ Avant promotion stage → prod
- ✅ Avant refactoring majeur du code

**Recommandé:**
- ✅ Après validation E2E réussie
- ✅ Avant expérimentation risquée en dev
- ✅ Avant migration de version client (v7 → v8)

### Créer un Snapshot

**Commande:**
```bash
# Snapshot environnement complet
python scripts/maintenance/create_snapshot.py \
  --env dev \
  --name "lai_v7_stable" \
  --client lai_weekly

# Snapshot avant migration
python scripts/maintenance/create_snapshot.py \
  --env dev \
  --name "pre_migration_v8"
```

**Contenu du snapshot:**
- Configurations Lambda (versions, variables env, layers)
- Versions Lambda Layers (ARNs, code)
- Configurations client S3 (YAML)
- Canonical S3 (scopes, prompts, sources)
- Dernières données curated (items.json)
- Stacks CloudFormation (paramètres, outputs)
- Métadonnées (timestamp, environnement, client)

**Emplacement:**
```
backup/snapshots/{snapshot_name}_{timestamp}/
├── lambda_vectora-inbox-ingest-v2-dev.json
├── lambda_vectora-inbox-normalize-score-v2-dev.json
├── lambda_vectora-inbox-newsletter-v2-dev.json
├── layer_vectora-inbox-vectora-core-dev.json
├── layer_vectora-inbox-common-deps-dev.json
├── clients/
│   └── lai_weekly.yaml
├── canonical/
│   ├── scopes/
│   ├── prompts/
│   └── sources/
├── curated_items.json
├── stacks/
│   ├── vectora-inbox-s0-core-dev.json
│   ├── vectora-inbox-s0-iam-dev.json
│   └── vectora-inbox-s1-runtime-dev.json
├── snapshot_metadata.json
└── README.md
```

### Rollback depuis un Snapshot

**Commande:**
```bash
# Rollback complet
python scripts/maintenance/rollback_snapshot.py \
  --snapshot "lai_v7_stable_20260130_143022" \
  --env dev

# Rollback partiel (config client uniquement)
python scripts/maintenance/rollback_snapshot.py \
  --snapshot "lai_v7_stable_20260130_143022" \
  --env dev \
  --components client_config
```

**Processus de rollback:**
1. Validation snapshot existe et est complet
2. Création snapshot état actuel (backup avant rollback)
3. Restauration configurations Lambda
4. Restauration layers Lambda
5. Restauration configurations S3
6. Validation post-rollback
7. Tests E2E

### Snapshots Automatiques

**Intégration dans workflow déploiement:**

```bash
# Dans scripts/deploy/deploy_lambda.sh
# Créer snapshot automatique avant déploiement
python scripts/maintenance/create_snapshot.py \
  --env ${ENV} \
  --name "pre_deploy_$(date +%Y%m%d_%H%M%S)"

# Déploiement
aws lambda update-function-code ...

# Si échec, rollback automatique
if [ $? -ne 0 ]; then
  echo "❌ Déploiement échoué, rollback..."
  python scripts/maintenance/rollback_snapshot.py \
    --snapshot "pre_deploy_*" \
    --env ${ENV}
fi
```

### Rétention des Snapshots

**Politique de rétention recommandée:**
- **dev**: 7 derniers snapshots (rotation automatique)
- **stage**: 30 derniers snapshots
- **prod**: Tous les snapshots (archivage S3 Glacier après 90 jours)

**Nettoyage automatique:**
```bash
# Supprimer snapshots dev > 7 jours
python scripts/maintenance/cleanup_snapshots.py --env dev --older-than 7

# Archiver snapshots prod > 90 jours
python scripts/maintenance/archive_snapshots.py --env prod --older-than 90
```
```

---

### 3. Modification Section: Configuration AWS

**Remplacer la section actuelle par:**

```markdown
## 🔧 CONFIGURATION AWS PAR ENVIRONNEMENT

### Région AWS Principale

**Région**: `eu-west-3` (Paris)  
**Profil CLI**: `rag-lai-prod`  
**Compte**: `786469175371`

Toutes les ressources principales (S3, Lambda, CloudWatch) sont dans `eu-west-3`.

### Région Bedrock

**Région**: `us-east-1` (Virginie du Nord)  
**Modèle**: `anthropic.claude-3-sonnet-20240229-v1:0`  
**Profil d'inférence EU**: `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`

Configuration validée E2E pour normalisation et génération éditoriale.

### Ressources par Environnement

#### Environnement DEV

**Lambdas:**
```
vectora-inbox-ingest-v2-dev
vectora-inbox-normalize-score-v2-dev
vectora-inbox-newsletter-v2-dev
```

**Buckets S3:**
```
vectora-inbox-config-dev
vectora-inbox-data-dev
vectora-inbox-newsletters-dev
vectora-inbox-lambda-code-dev
```

**Stacks CloudFormation:**
```
vectora-inbox-s0-core-dev
vectora-inbox-s0-iam-dev
vectora-inbox-s1-runtime-dev
```

**Statut**: ✅ Opérationnel (POC lai_weekly_v7)

#### Environnement STAGE

**Lambdas:**
```
vectora-inbox-ingest-v2-stage
vectora-inbox-normalize-score-v2-stage
vectora-inbox-newsletter-v2-stage
```

**Buckets S3:**
```
vectora-inbox-config-stage
vectora-inbox-data-stage
vectora-inbox-newsletters-stage
vectora-inbox-lambda-code-stage
```

**Stacks CloudFormation:**
```
vectora-inbox-s0-core-stage
vectora-inbox-s0-iam-stage
vectora-inbox-s1-runtime-stage
```

**Statut**: ⏳ À créer (Phase 3 du plan)

#### Environnement PROD

**Lambdas:**
```
vectora-inbox-ingest-v2-prod
vectora-inbox-normalize-score-v2-prod
vectora-inbox-newsletter-v2-prod
```

**Buckets S3:**
```
vectora-inbox-config-prod
vectora-inbox-data-prod
vectora-inbox-newsletters-prod
vectora-inbox-lambda-code-prod
```

**Stacks CloudFormation:**
```
vectora-inbox-s0-core-prod
vectora-inbox-s0-iam-prod
vectora-inbox-s1-runtime-prod
```

**Statut**: ⏳ À créer (Phase 4 du plan)

### Commandes de Déploiement par Environnement

**Template générique:**
```bash
# Variables
ENV=dev|stage|prod
STACK_NAME=vectora-inbox-{stack}-${ENV}

# Déploiement stack
aws cloudformation deploy \
  --template-file infra/{stack}.yaml \
  --stack-name ${STACK_NAME} \
  --parameter-overrides Env=${ENV} ProjectName=vectora-inbox \
  --region eu-west-3 \
  --profile rag-lai-prod
```

**Exemples concrets:**
```bash
# Déployer S0-core en stage
aws cloudformation deploy \
  --template-file infra/s0-core.yaml \
  --stack-name vectora-inbox-s0-core-stage \
  --parameter-overrides Env=stage ProjectName=vectora-inbox \
  --region eu-west-3 \
  --profile rag-lai-prod

# Déployer S1-runtime en prod
aws cloudformation deploy \
  --template-file infra/s1-runtime.yaml \
  --stack-name vectora-inbox-s1-runtime-prod \
  --parameter-overrides Env=prod \
    ConfigBucketName=vectora-inbox-config-prod \
    DataBucketName=vectora-inbox-data-prod \
    NewslettersBucketName=vectora-inbox-newsletters-prod \
  --region eu-west-3 \
  --profile rag-lai-prod
```
```

---

### 4. Nouvelle Section: Checklist Q Developer

**Emplacement**: Avant la section "✅ BONNES PRATIQUES RECOMMANDÉES"

```markdown
## ✅ CHECKLIST Q DEVELOPER - ENVIRONNEMENTS

### Avant de Proposer du Code

Q Developer doit TOUJOURS vérifier:

**Environnement cible:**
- [ ] Environnement clairement identifié (dev/stage/prod)
- [ ] Convention nommage respectée (`-{env}`)
- [ ] Variables d'environnement adaptées
- [ ] Buckets S3 corrects pour l'environnement

**Sécurité:**
- [ ] Pas de modification directe en prod
- [ ] Snapshot créé avant modification majeure
- [ ] Rollback possible en cas d'échec
- [ ] Tests E2E passés avant promotion

**Configuration client:**
- [ ] `client_id` stable (sans version)
- [ ] `version` sémantique séparée
- [ ] Même config peut être promue entre envs
- [ ] Changelog à jour dans metadata

**Déploiement:**
- [ ] Ordre stacks respecté (S0-core → S0-iam → S1-runtime)
- [ ] Paramètres environnement corrects
- [ ] Outputs sauvegardés
- [ ] Validation post-déploiement

### Questions à Poser à l'Utilisateur

Si l'environnement n'est pas clair:

- "Sur quel environnement souhaitez-vous travailler? (dev/stage/prod)"
- "Voulez-vous créer un snapshot avant cette modification?"
- "Cette modification doit-elle être testée en dev avant stage?"
- "Faut-il promouvoir cette config vers un autre environnement?"

### Réponses Adaptées par Environnement

**En dev:**
- Proposer modifications directes
- Suggérer tests locaux
- Encourager expérimentation

**En stage:**
- Exiger validation dev préalable
- Demander création snapshot
- Proposer tests E2E complets

**En prod:**
- Refuser modifications directes
- Exiger passage par stage
- Demander approbation formelle
```

---

## 📝 RÉSUMÉ DES MODIFICATIONS

### Sections à Ajouter

1. **🌍 Gestion des Environnements** (nouvelle section complète)
2. **📸 Snapshots et Rollback** (nouvelle section complète)
3. **✅ Checklist Q Developer - Environnements** (nouvelle section)

### Sections à Modifier

4. **🔧 Configuration AWS** → **🔧 Configuration AWS par Environnement**
   - Détailler ressources par env (dev/stage/prod)
   - Ajouter commandes déploiement par env

### Sections à Enrichir

5. **📋 Règles de Configuration Client**
   - Ajouter distinction `client_id` vs `version`
   - Expliquer déploiement multi-env

6. **🔧 Règles d'Exécution Scripts**
   - Ajouter paramètre `--env` obligatoire
   - Exemples avec environnements

### Impact sur Q Developer

Avec ces modifications, Q Developer saura:

✅ **Identifier l'environnement** de travail (dev/stage/prod)  
✅ **Adapter ses recommandations** selon l'environnement  
✅ **Proposer snapshots** avant modifications majeures  
✅ **Respecter workflow** de promotion dev → stage → prod  
✅ **Utiliser convention nommage** cohérente avec suffixe `-{env}`  
✅ **Distinguer version client** et environnement déploiement

---

## 🎯 PROCHAINES ÉTAPES

1. **Valider modifications** avec l'équipe
2. **Appliquer modifications** à `.q-context/vectora-inbox-development-rules.md`
3. **Créer scripts** de snapshot et rollback
4. **Tester workflow** complet en dev
5. **Documenter exemples** concrets pour Q Developer

---

**FIN DU DOCUMENT**
