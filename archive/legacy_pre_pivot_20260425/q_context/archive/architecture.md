# Architecture Vectora Inbox V2

**Date**: 2026-02-02  
**Version**: 2.2  
**Architecture**: 3 Lambdas V2 validées E2E  
**Client référence**: lai_weekly_v3

---

## 🏗️ Architecture 3 Lambdas V2

```
ingest-v2 → normalize-score-v2 → newsletter-v2
```

### Pipeline de Données

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   INGEST V2     │───▶│ NORMALIZE/SCORE │───▶│  NEWSLETTER V2  │
│                 │    │      V2         │    │                 │
│ Sources externes│    │ Bedrock + Rules │    │ Editorial + S3  │
│ ──────▶ S3 raw/ │    │ ──────▶ S3 cur/ │    │ ──────▶ S3 out/ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Flux**:
1. **Ingest V2**: Sources → S3 `ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json`
2. **Normalize/Score V2**: S3 `ingested/` → Bedrock → S3 `curated/{client_id}/{YYYY}/{MM}/{DD}/items.json`
3. **Newsletter V2**: S3 `curated/` → Editorial → S3 `newsletters/{client_id}/{YYYY}/{MM}/{DD}/newsletter.md`

---

## 📁 Structure Repository

```
src_v2/                    # Code source V2 (RÉFÉRENCE)
├── lambdas/               # Handlers Lambda
│   ├── ingest/
│   ├── normalize_score/
│   └── newsletter/
└── vectora_core/          # Logique métier
    ├── shared/            # Modules partagés
    ├── ingest/
    ├── normalization/
    └── newsletter/

canonical/                 # Configurations métier
├── scopes/                # Entités (companies, molecules, tech)
├── prompts/               # Prompts Bedrock
└── sources/               # Sources d'ingestion

client-config-examples/    # Templates configs clients
scripts/                   # Scripts build/deploy
tests/                     # Tests unitaires/E2E
.tmp/                      # Fichiers temporaires
.build/                    # Artefacts build
```

---

## 🔧 Configuration AWS

**Région principale**: eu-west-3 (Paris)  
**Région Bedrock**: us-east-1 (Virginie)  
**Profil CLI**: rag-lai-prod  
**Compte**: 786469175371

### Buckets S3

```
vectora-inbox-config-{env}       # Configs client + canonical
vectora-inbox-data-{env}         # ingested/ + curated/
vectora-inbox-newsletters-{env}  # Newsletters finales
```

### Variables d'Environnement

**Communes**:
```bash
ENV={env}
CONFIG_BUCKET=vectora-inbox-config-{env}
DATA_BUCKET=vectora-inbox-data-{env}
LOG_LEVEL=INFO
```

**Normalize/Score V2**:
```bash
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
```

**Newsletter V2**:
```bash
NEWSLETTERS_BUCKET=vectora-inbox-newsletters-{env}
```

---

## 🌍 Environnements

| Env | Statut | Usage |
|-----|--------|-------|
| **dev** | ✅ Opérationnel | Développement et tests |
| **stage** | ✅ Opérationnel | Pré-production |
| **prod** | 🚧 À créer | Production clients |

**Convention nommage**:
- Lambdas: `vectora-inbox-{fonction}-v2-{env}`
- Buckets: `vectora-inbox-{type}-{env}`
- Stacks: `vectora-inbox-{stack}-{env}`

---

## 🤖 Bedrock Configuration

**Configuration validée E2E**:
```bash
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
```

**Appels dans Normalize/Score V2**:
1. **Normalisation** (1 appel/item): Extraction entités, classification, résumé
2. **Matching** (1 appel/item): Évaluation pertinence par domaine

**Métriques lai_weekly_v3**:
- 30 appels Bedrock pour 15 items
- Temps: 163s (5.4s/appel)
- Coût: ~$0.15/run

---

## ⚙️ Configuration Pilotée

### Client Configuration

**Emplacement**: `s3://vectora-inbox-config-{env}/clients/{client_id}.yaml`

**Exemple**:
```yaml
client_id: lai_weekly_v3
watch_domains:
  - domain_id: tech_lai_ecosystem
    min_domain_score: 0.25
  - domain_id: regulatory_lai
    min_domain_score: 0.20

scoring_config:
  client_specific_bonuses:
    pure_player_companies:
      bonus: 5.0

newsletter_layout:
  sections:
    - section_id: top_signals
      max_items: 5
```

### Canonical Configuration

**Scopes métier**:
- `canonical/scopes/company_scopes.yaml`: Entreprises surveillées
- `canonical/scopes/molecule_scopes.yaml`: Molécules LAI
- `canonical/scopes/technology_scopes.yaml`: Mots-clés tech
- `canonical/scopes/trademark_scopes.yaml`: Marques

**Prompts Bedrock**:
- `canonical/prompts/global_prompts.yaml`: Templates normalisation/matching

**Sources**:
- `canonical/sources/source_catalog.yaml`: 180+ sources

---

## 📦 Lambda Layers

**Layer vectora-core**:
- Contenu: `vectora_core/` uniquement
- Nom: `vectora-inbox-vectora-core-{env}`
- Taille max: 50MB

**Layer common-deps**:
- Contenu: Dépendances tierces (PyYAML, requests, feedparser, beautifulsoup4)
- Nom: `vectora-inbox-common-deps-{env}`
- Structure: `python/` à la racine

---

## 🏗️ Infrastructure

**Ordre déploiement obligatoire**:
1. S0-core (Buckets S3)
2. S0-iam (Rôles IAM)
3. S1-runtime (Lambdas)

**Commandes**:
```bash
# S0-core
aws cloudformation deploy \
  --template-file infra/s0-core.yaml \
  --stack-name vectora-inbox-s0-core-{env} \
  --parameter-overrides Env={env} \
  --region eu-west-3 \
  --profile rag-lai-prod

# S0-iam
aws cloudformation deploy \
  --template-file infra/s0-iam.yaml \
  --stack-name vectora-inbox-s0-iam-{env} \
  --capabilities CAPABILITY_IAM \
  --region eu-west-3 \
  --profile rag-lai-prod

# S1-runtime
aws cloudformation deploy \
  --template-file infra/s1-runtime.yaml \
  --stack-name vectora-inbox-s1-runtime-{env} \
  --region eu-west-3 \
  --profile rag-lai-prod
```

---

## ✅ Validation E2E

**Client référence**: lai_weekly_v3 (18 décembre 2025)

**Résultats**:
- ✅ 15 items LAI traités
- ✅ 30 appels Bedrock (100% succès)
- ✅ 36 entités extraites
- ✅ Temps: 163s
- ✅ Coût: $0.21/run

**Commandes test**:
```bash
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v3
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v3
python scripts/invoke/invoke_newsletter_v2.py --client-id lai_weekly_v3
```

---

## 🚀 Commandes Essentielles

```bash
# Build
python scripts/build/build_all.py

# Deploy dev
python scripts/deploy/deploy_env.py --env dev

# Test dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# Promote stage
python scripts/deploy/promote.py --to stage --version X.Y.Z

# Test stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage
```

---

**Architecture V2 - Version 2.2**  
**Date**: 2026-02-02  
**Statut**: ✅ Validée E2E et documentée
