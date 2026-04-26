# Structure du Repository Vectora Inbox V2 - Vue d'Ensemble

**Date :** 18 décembre 2025  
**Version :** 2.0  
**Statut :** Post-nettoyage racine

---

## Vue d'Ensemble

Ce document décrit la structure organisationnelle du repository Vectora Inbox après le nettoyage de la racine effectué le 18 décembre 2025. La structure respecte les règles d'hygiène V4 et maintient la compatibilité avec le workflow V2 (ingest_v2 + normalize_score_v2).

---

## Structure Racine

### Dossiers Principaux

```
vectora-inbox/
├── .q-context/              # Contexte Amazon Q (blueprints, règles)
├── backup/                  # Sauvegardes et fichiers legacy
├── canonical/               # Configurations canoniques (scopes, events, prompts)
├── client-config-examples/  # Exemples de configurations client
├── contracts/               # Contrats d'API Lambda
├── docs/                    # Documentation complète
├── infra/                   # Infrastructure CloudFormation
├── layer_build/             # Construction de layers Lambda (ACTIF)
├── layer_inspection/        # Outils d'inspection de layers
├── layer_minimal/           # Layer minimale YAML (EXPÉRIMENTAL)
├── layer_rebuild/           # Reconstruction layers complètes (EXPÉRIMENTAL)
├── output/                  # Sorties de build et diagnostics
├── scripts/                 # Scripts de déploiement et test
├── src/                     # Code source V1 (legacy)
├── src_v2/                  # Code source V2 (ACTIF)
└── tests/                   # Tests unitaires et d'intégration
```

### Fichiers Racine

```
.gitignore                   # Configuration Git
AWS_DEPLOYMENT_SUMMARY.md    # Résumé des déploiements AWS
DEPLOY_INSTRUCTIONS.md       # Instructions de déploiement
global_prompts.yaml          # Prompts globaux (à évaluer destination)
```

---

## Détail des Dossiers

### .q-context/ - Contexte Amazon Q

**Rôle :** Configuration et règles pour Amazon Q Developer

**Contenu :**
- `blueprint-v2-current.yaml` : Blueprint architecture V2 actuelle
- `blueprint-draft-vectora-inbox.yaml` : Blueprint historique
- `src_lambda_hygiene_v4.md` : Règles d'hygiène Lambda V4
- `vectora-inbox-overview.md` : Vue d'ensemble du projet
- `vectora-inbox-q-rules.md` : Règles Q générales
- `vectora-inbox-v2-rules.md` : Règles spécifiques V2

**Statut :** ✅ ACTIF - Ne pas modifier

---

### backup/ - Sauvegardes

**Rôle :** Archivage de fichiers legacy et sauvegardes

**Structure :**
```
backup/
├── root_legacy/             # Fichiers déplacés de la racine (nettoyage 18/12)
├── scripts/                 # Scripts obsolètes
└── src_v2_before_restructure/  # Code V2 avant restructuration
```

**Contenu root_legacy/ :**
- `lai_weekly_v3.yaml` : Doublon de client-config-examples/
- `required_dependencies.txt` : Liste dépendances obsolète

**Statut :** ✅ ARCHIVÉ - Consultation uniquement

---

### canonical/ - Configurations Canoniques

**Rôle :** Définitions canoniques réutilisables (scopes, events, prompts)

**Structure :**
```
canonical/
├── events/                  # Types d'événements
├── imports/                 # Imports canoniques
├── ingestion/               # Profils d'ingestion
├── matching/                # Profils de matching
├── prompts/                 # Prompts Bedrock
├── scopes/                  # Scopes (companies, molecules, keywords)
├── scoring/                 # Règles de scoring
└── sources/                 # Catalogue de sources
```

**Statut :** ✅ ACTIF - Critique pour V2, ne pas modifier sans validation

---

### client-config-examples/ - Configurations Client

**Rôle :** Exemples de configurations client pour newsletters

**Contenu :**
- `client_config_template.yaml` : Template générique
- `client_template_v2.yaml` : Template V2
- `lai_weekly_v3.yaml` : Configuration LAI Weekly (RÉFÉRENCE)

**Statut :** ✅ ACTIF - Utilisé par le workflow V2

---

### docs/ - Documentation

**Rôle :** Documentation complète du projet

**Structure :**
```
docs/
├── architecture/            # Diagrammes et décisions d'architecture
├── design/                  # Documents de design
├── diagnostics/             # Diagnostics et analyses
│   └── raw/                 # Fichiers JSON de diagnostic (nettoyage 18/12)
├── guides/                  # Guides utilisateur
├── plans/                   # Plans de développement
└── reports/                 # Rapports d'exécution
```

**Nouveaux documents (18/12) :**
- `diagnostics/repo_root_cleanup_plan_v1.md` : Plan de nettoyage racine
- `diagnostics/repo_root_cleanup_execution_report_v1.md` : Rapport d'exécution
- `diagnostics/layer_folders_role_and_cleanup_options.md` : Diagnostic layers
- `design/repo_layout_v2_overview.md` : Ce document

**Statut :** ✅ ACTIF - Documentation vivante

---

### infra/ - Infrastructure CloudFormation

**Rôle :** Templates CloudFormation pour déploiement AWS

**Contenu :**
- `s0-core.yaml` : Buckets S3 et ressources core
- `s0-iam.yaml` : Rôles et permissions IAM
- `s1-ingest-v2.yaml` : Lambda ingest-v2
- `s1-normalize-score-v2.yaml` : Lambda normalize-score-v2
- `s1-runtime.yaml` : Ressources runtime

**Statut :** ✅ ACTIF - Infrastructure V2 en production

---

### layer_build/ - Construction de Layers (ACTIF)

**Rôle :** Construction de la layer vectora-inbox-common-deps-v2

**Contenu :**
- `python/` : Dépendances (PyYAML, requests, feedparser, beautifulsoup4, etc.)
- `test_imports.py` : Tests d'imports
- `vectora-inbox-common-deps-v2.zip` : Package layer déployé

**Statut :** ✅ CRITIQUE - Layer utilisée par les Lambdas V2

---

### layer_inspection/ - Inspection de Layers

**Rôle :** Outils d'inspection et extraction de layers

**Contenu :**
- `yaml-minimal-extracted/` : Extraction layer YAML
- `yaml-minimal-layer.zip` : Package layer YAML minimal

**Statut :** ⚠️ UTILITAIRE - Utile pour debug, non critique

---

### layer_minimal/ - Layer Minimale (EXPÉRIMENTAL)

**Rôle :** Layer contenant uniquement PyYAML

**Contenu :**
- `python/` : PyYAML uniquement
- `yaml-minimal.zip` : Package layer minimal

**Statut :** ⚠️ EXPÉRIMENTAL - Non utilisée par V2, candidate à suppression

---

### layer_rebuild/ - Reconstruction Layers (EXPÉRIMENTAL)

**Rôle :** Reconstruction de layers avec boto3/botocore

**Contenu :**
- `python/` : Dépendances complètes incluant boto3

**Statut :** ⚠️ EXPÉRIMENTAL - Approche abandonnée, candidate à suppression

---

### output/ - Sorties de Build

**Rôle :** Sorties de build, packages Lambda, diagnostics

**Structure :**
```
output/
├── lambda_packages/         # Packages Lambda éphémères (nettoyage 18/12)
├── normalize_v2_evaluation_report.md
├── normalize_v2_metrics.json
├── normalized_items_local.json
└── real_ingested_items.json
```

**Contenu lambda_packages/ (20 fichiers déplacés 18/12) :**
- Packages bedrock-matching-patch-v2-*.zip
- Packages normalize-score-v2-*.zip
- Packages vectora-core-refactored-*.zip
- Autres packages éphémères

**Statut :** ✅ ACTIF - Dossier de sortie pour builds

---

### scripts/ - Scripts

**Rôle :** Scripts de déploiement, test, et analyse

**Structure :**
```
scripts/
├── analysis/                # Scripts d'analyse (nettoyage 18/12)
├── deploy/                  # Scripts de déploiement
├── events/                  # Événements de test
├── invoke/                  # Scripts d'invocation Lambda
├── layers/                  # Scripts de gestion layers
├── payloads/                # Payloads de test
└── test_data/               # Données de test
```

**Statut :** ✅ ACTIF - Scripts de maintenance et déploiement

---

### src/ - Code Source V1 (LEGACY)

**Rôle :** Code source V1 (architecture 2 Lambdas)

**Contenu :**
- Dépendances Python complètes
- `vectora_core/` : Core V1
- `lambdas/` : Lambdas V1

**Statut :** ⚠️ LEGACY - Maintenu pour compatibilité, V2 est la référence

---

### src_v2/ - Code Source V2 (ACTIF)

**Rôle :** Code source V2 (architecture 3 Lambdas)

**Structure :**
```
src_v2/
├── lambdas/
│   ├── ingest_v2/           # Lambda ingestion
│   ├── normalize_score_v2/  # Lambda normalisation + scoring
│   └── newsletter_v2/       # Lambda génération newsletter (à implémenter)
└── vectora_core/            # Core partagé V2
    ├── bedrock/             # Intégration Bedrock
    ├── config/              # Gestion configuration
    ├── ingestion/           # Moteur ingestion
    ├── matching/            # Moteur matching
    ├── normalization/       # Moteur normalisation
    ├── s3/                  # Utilitaires S3
    └── scoring/             # Moteur scoring
```

**Statut :** ✅ ACTIF - Code de référence V2

---

### tests/ - Tests

**Rôle :** Tests unitaires, intégration, et données de test

**Structure :**
```
tests/
├── data_snapshots/          # Snapshots de données réelles (nettoyage 18/12)
├── events/                  # Événements de test
├── fixtures/                # Fixtures de test
├── integration/             # Tests d'intégration
├── payloads/                # Payloads de test (nettoyage 18/12)
└── unit/                    # Tests unitaires
```

**Contenu ajouté (18/12) :**
- `payloads/ingest_payload.json` : Payload test ingestion
- `payloads/normalize_payload.json` : Payload test normalisation
- `data_snapshots/real_ingested_items_17dec.json` : Snapshot 17 déc
- `data_snapshots/final_test.json` : Test final

**Statut :** ✅ ACTIF - Tests pour V2

---

## Localisation des Artefacts

### Packages Lambda

**Avant nettoyage :** Racine (40 fichiers)  
**Après nettoyage :** `output/lambda_packages/` (20 fichiers ZIP)

**Packages déployés :**
- `layer_build/vectora-inbox-common-deps-v2.zip` : Layer commune
- `output/lambda_packages/normalize-score-v2-*.zip` : Packages Lambda

---

### JSON de Diagnostics

**Avant nettoyage :** Racine (9 fichiers)  
**Après nettoyage :** `docs/diagnostics/raw/`

**Fichiers :**
- `curated_items_*.json` : Analyses items curés
- `ingested_items_e2e.json` : Tests end-to-end
- `current_lambda_state.json` : État Lambda
- `normalize_lambda_diagnostic.json` : Diagnostics normalize

---

### Payloads de Test

**Avant nettoyage :** Racine (2 fichiers)  
**Après nettoyage :** `tests/payloads/`

**Fichiers :**
- `ingest_payload.json` : Payload test ingestion
- `normalize_payload.json` : Payload test normalisation

---

### Snapshots de Données

**Avant nettoyage :** Racine (2 fichiers)  
**Après nettoyage :** `tests/data_snapshots/`

**Fichiers :**
- `real_ingested_items_17dec.json` : Snapshot données réelles 17 déc
- `final_test.json` : Test final avec données réelles

---

### Fichiers Legacy

**Avant nettoyage :** Racine (2 fichiers)  
**Après nettoyage :** `backup/root_legacy/`

**Fichiers :**
- `lai_weekly_v3.yaml` : Doublon config client
- `required_dependencies.txt` : Liste dépendances obsolète

---

## Workflow V2 - Chemins Critiques

### Configuration Client

**Chemin :** `client-config-examples/lai_weekly_v3.yaml`  
**Déploiement S3 :** `s3://vectora-inbox-config-dev/client_configs/lai_weekly_v3.yaml`

### Configurations Canoniques

**Chemin :** `canonical/`  
**Déploiement S3 :** `s3://vectora-inbox-config-dev/canonical/`

### Code Lambda

**Chemin :** `src_v2/lambdas/`  
**Déploiement :** Packages dans `output/lambda_packages/`

### Layer Commune

**Chemin :** `layer_build/vectora-inbox-common-deps-v2.zip`  
**Déploiement AWS :** Layer Lambda `vectora-inbox-common-deps-v2`

---

## Règles de Maintenance

### Dossiers Protégés (Ne Jamais Supprimer)

- ✅ `.q-context/` : Contexte Amazon Q
- ✅ `canonical/` : Configurations canoniques
- ✅ `client-config-examples/` : Configs client
- ✅ `docs/` : Documentation
- ✅ `infra/` : Infrastructure CloudFormation
- ✅ `src_v2/` : Code source V2
- ✅ `layer_build/` : Layer de production

### Dossiers Modifiables avec Précaution

- ⚠️ `scripts/` : Scripts de maintenance
- ⚠️ `tests/` : Tests (ajouter, pas supprimer)
- ⚠️ `output/` : Sorties (nettoyage périodique OK)

### Dossiers Candidats à Nettoyage Futur

- 🔄 `layer_minimal/` : Non utilisée par V2
- 🔄 `layer_rebuild/` : Approche abandonnée
- 🔄 `src/` : Legacy V1 (après migration complète)

---

## Métriques Post-Nettoyage

### Réduction du Bazar Racine

**Avant :** 40 fichiers isolés à la racine  
**Après :** 4 fichiers essentiels à la racine  
**Amélioration :** 90% de réduction

### Organisation Structurée

- ✅ Packages Lambda centralisés
- ✅ Diagnostics organisés
- ✅ Tests structurés
- ✅ Legacy archivé

### Compatibilité V2

- ✅ Moteur V2 100% fonctionnel
- ✅ Déploiements non impactés
- ✅ Configurations préservées
- ✅ Historique conservé

---

## Conclusion

La racine du repo Vectora Inbox a été nettoyée sans suppression de fichiers. Les artefacts éphémères (zips, JSON de test) ont été déplacés dans des dossiers dédiés, en respect des règles d'hygiène V4 et sans impact sur le workflow ingest_v2 + normalize_score_v2.

**État actuel :** ✅ Repo organisé, V2 opérationnel, documentation à jour

**Prochaines étapes :**
1. Évaluer destination finale de `global_prompts.yaml`
2. Réévaluer `layer_minimal/` et `layer_rebuild/` après 1 mois
3. Documenter chaque dossier layer_* avec un README