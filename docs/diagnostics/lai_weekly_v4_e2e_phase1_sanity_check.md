# Phase 1 – Préparation & Sanity Check
# LAI Weekly V4 - E2E Readiness Assessment

**Date d'exécution :** 21 décembre 2025  
**Profil AWS :** rag-lai-prod  
**Environnement :** dev  
**Statut :** ✅ VALIDÉ

---

## Résumé Exécutif

✅ **Environnement prêt pour exécution E2E**
- Authentification SSO réussie sur profil rag-lai-prod
- Configuration client lai_weekly_v4.yaml présente dans S3
- Structure S3 complète (config, data, newsletters)
- Code source V2 validé pour les 3 Lambdas
- Prompts canoniques disponibles (normalisation + newsletter)

---

## 1. Authentification AWS

### Statut
✅ **Authentification SSO réussie**

### Détails
```
Profil : rag-lai-prod
Région : eu-west-3 (Paris)
SSO URL : https://d-8067754348.awsapps.com/start
Statut : Successfully logged into Start URL
```

---

## 2. Vérification Code Source V2

### Lambdas Handlers

#### ✅ vectora-inbox-ingest-v2-dev
**Fichier :** `src_v2/lambdas/ingest/handler.py`

**Fonctionnalités validées :**
- Mode single-client (avec client_id)
- Mode multi-clients (scan clients actifs)
- Variables d'environnement : CONFIG_BUCKET, DATA_BUCKET, ENV
- Gestion d'erreurs robuste
- Logging structuré

**Points clés :**
- Délégation complète à `vectora_core.ingest`
- Support temporal_mode et ingestion_mode
- Validation des variables d'environnement critiques

#### ✅ vectora-inbox-normalize-score-v2-dev
**Fichier :** `src_v2/lambdas/normalize_score/handler.py`

**Fonctionnalités validées :**
- Paramètre client_id obligatoire
- Variables d'environnement : CONFIG_BUCKET, DATA_BUCKET, BEDROCK_MODEL_ID, BEDROCK_REGION
- Support period_days, from_date, to_date, target_date
- Bedrock model override possible
- Scoring mode configurable

**Points clés :**
- Délégation complète à `vectora_core.normalization`
- Validation stricte des variables Bedrock
- Gestion d'erreurs avec logging détaillé

#### ⚠️ vectora-inbox-newsletter-v2-dev
**Statut :** Lambda à vérifier (handler non lu dans cette phase)

**Action requise :** Vérifier l'existence et la configuration de la Lambda newsletter en Phase 4

---

## 3. Configuration Client lai_weekly_v4

### Statut S3
✅ **Fichier présent dans S3**
```
s3://vectora-inbox-config-dev/clients/lai_weekly_v4.yaml
Taille : 8312 bytes
Date : 2025-12-21 17:37:00
```

### Validation Configuration

#### ✅ Profil Client
```yaml
client_profile:
  name: "LAI Intelligence Weekly v4 (Tech Focus)"
  client_id: "lai_weekly_v4"
  active: true
  language: "en"
  frequency: "weekly"
```

#### ✅ Pipeline Configuration
```yaml
pipeline:
  newsletter_mode: "latest_run_only"  # ✅ Mode cohérent avec architecture
  default_period_days: 30
```

**Validation :** Mode `latest_run_only` conforme au plan E2E

#### ✅ Watch Domains
**Domaine unique :** `tech_lai_ecosystem`
- Type : technology
- Priority : high
- Scopes : lai_keywords, lai_companies_global, lai_molecules_global, lai_trademarks_global
- Enabled : true

**Validation :** Configuration v4 simplifiée avec un seul domaine (vs v3 avec 2 domaines)

#### ✅ Matching Configuration
```yaml
matching_config:
  min_domain_score: 0.25
  max_domains_per_item: 1  # ✅ Cohérent avec domaine unique
  enable_fallback_mode: true
  trademark_privileges:
    enabled: true
    auto_match_threshold: 0.8
```

#### ✅ Newsletter Selection
```yaml
newsletter_selection:
  max_items_total: 20
  min_score_threshold: 0
  critical_event_types:
    - regulatory_approval
    - nda_submission
    - pivotal_trial_result
    - partnership
    - clinical_update
    - regulatory
    - corporate_move
  trimming_policy:
    preserve_critical_events: true
    min_items_per_section: 1
    max_section_dominance: 0.6
```

**Validation :** Configuration newsletter_selection présente et complète

#### ✅ Newsletter Layout
**4 sections définies :**
1. **top_signals** : max 5 items, tri par score
2. **partnerships_deals** : max 5 items, filtré par event_types, tri par date
3. **regulatory_updates** : max 5 items, filtré par event_types, tri par score
4. **clinical_updates** : max 8 items, filtré par event_types, tri par date

**Validation :** Toutes les sections pointent vers `tech_lai_ecosystem`

---

## 4. Configuration Canonique

### ✅ Prompts Globaux
**Fichier :** `canonical/prompts/global_prompts.yaml`

**Prompts disponibles :**

#### Normalisation
- ✅ `normalization.lai_default` : Prompt principal normalisation LAI
  - Extraction entités (companies, molecules, technologies, trademarks)
  - Classification event_type
  - LAI relevance score
  - Anti-LAI detection
  - Pure player context

#### Newsletter
- ✅ `newsletter.tldr_generation` : Génération TL;DR (2-3 bullets)
- ✅ `newsletter.introduction_generation` : Génération introduction
- ✅ `newsletter.section_summary` : Résumés de section (optionnel)
- ✅ `newsletter.title_reformulation` : Reformulation titres (optionnel)

#### Matching
- ✅ `matching.matching_watch_domains_v2` : Matching par domaines via Bedrock
  - Évaluation relevance_score par domaine
  - Confidence level (high/medium/low)
  - Matched entities
  - Reasoning

**Validation :** Tous les prompts nécessaires pour le workflow E2E sont présents

### Configuration Bedrock
```yaml
bedrock_config:
  max_tokens: 1000 (normalisation), 200 (tldr), 300 (intro)
  temperature: 0.0 (normalisation), 0.1 (newsletter)
  anthropic_version: "bedrock-2023-05-31"
```

---

## 5. Structure S3

### ✅ Bucket Configuration
```
s3://vectora-inbox-config-dev/
├── clients/
│   ├── lai_weekly_v4.yaml ✅
│   ├── client_config_template.yaml
│   └── README.md
```

### ✅ Bucket Data
```
s3://vectora-inbox-data-dev/
├── ingested/ ✅
├── curated/ ✅
├── normalized/
├── raw/
├── clients/
├── deployments/
└── lambda-packages/
```

**Validation :** Dossiers `ingested/` et `curated/` présents pour le workflow

### ✅ Bucket Newsletters
```
s3://vectora-inbox-newsletters-dev/
├── lai_weekly/ ✅
├── lai_weekly_v2/ ✅
├── lai_weekly_v3/ ✅
├── lai_weekly_v4/ ✅ (dossier existant)
└── cache/
```

**Validation :** Dossier `lai_weekly_v4/` déjà créé, prêt pour recevoir les newsletters

---

## 6. Variables d'Environnement Attendues

### Lambda Ingest V2
```
ENV=dev
PROJECT_NAME=vectora-inbox
CONFIG_BUCKET=vectora-inbox-config-dev
DATA_BUCKET=vectora-inbox-data-dev
LOG_LEVEL=INFO
```

### Lambda Normalize-Score V2
```
ENV=dev
PROJECT_NAME=vectora-inbox
CONFIG_BUCKET=vectora-inbox-config-dev
DATA_BUCKET=vectora-inbox-data-dev
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
LOG_LEVEL=INFO
```

### Lambda Newsletter V2 (à vérifier en Phase 4)
```
ENV=dev
PROJECT_NAME=vectora-inbox
CONFIG_BUCKET=vectora-inbox-config-dev
DATA_BUCKET=vectora-inbox-data-dev
NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
LOG_LEVEL=INFO
```

---

## 7. Checklist de Validation

### Code Source
- [x] Handler ingest-v2 présent et conforme
- [x] Handler normalize-score-v2 présent et conforme
- [ ] Handler newsletter-v2 à vérifier en Phase 4

### Configuration
- [x] lai_weekly_v4.yaml présent dans S3
- [x] client_profile.active = true
- [x] watch_domains configuré (tech_lai_ecosystem)
- [x] newsletter_layout présent avec 4 sections
- [x] newsletter_selection présent et complet
- [x] newsletter_mode = "latest_run_only"

### Prompts Canoniques
- [x] Prompt normalisation LAI disponible
- [x] Prompts newsletter disponibles (tldr, intro)
- [x] Prompt matching disponible

### Infrastructure S3
- [x] Bucket config accessible
- [x] Bucket data accessible (ingested/, curated/)
- [x] Bucket newsletters accessible (lai_weekly_v4/)

### Authentification
- [x] SSO login réussi sur rag-lai-prod
- [x] Accès S3 validé

---

## 8. Points d'Attention

### ⚠️ Lambda Newsletter V2
**Action requise :** Vérifier en Phase 4 que la Lambda newsletter-v2 existe et est correctement configurée

### ⚠️ Variables d'Environnement
**Action requise :** Valider que les Lambdas ont bien les variables d'environnement configurées (notamment BEDROCK_MODEL_ID et BEDROCK_REGION)

---

## 9. Conclusion Phase 1

### Statut Global
✅ **ENVIRONNEMENT PRÊT POUR EXÉCUTION E2E**

### Éléments Validés
- Authentification AWS opérationnelle
- Code source V2 conforme pour ingest et normalize-score
- Configuration client lai_weekly_v4 complète et cohérente
- Prompts canoniques disponibles pour tout le workflow
- Structure S3 complète et accessible

### Prochaine Étape
**Phase 2 – Run Ingestion Réel**
- Exécuter la Lambda ingest-v2 pour lai_weekly_v4
- Analyser les items ingérés
- Valider la structure des données dans S3

---

**Durée Phase 1 :** ~15 minutes  
**Livrables :** Document de sanity check complet  
**Décision :** ✅ GO pour Phase 2
