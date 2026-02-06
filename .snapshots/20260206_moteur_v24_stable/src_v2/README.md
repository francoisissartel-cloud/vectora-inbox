# Vectora Inbox V2 - Architecture 3 Lambdas

## Vue d'ensemble

Ce projet implémente l'architecture V2 de Vectora Inbox avec 3 Lambdas spécialisées selon les règles d'hygiène V4 :

- **Lambda ingest V2** : Ingestion brute des contenus depuis sources externes
- **Lambda normalize-score V2** : Normalisation et scoring via Bedrock *(à implémenter)*
- **Lambda newsletter V2** : Assemblage final de la newsletter *(à implémenter)*

## Structure du Projet

```
src_v2/
├── lambdas/                           # Handlers AWS Lambda
│   ├── ingest/
│   │   ├── handler.py                 # ✅ Handler ingest V2 (fonctionnel)
│   │   └── requirements.txt
│   ├── normalize_score/
│   │   ├── handler.py                 # 🚧 Handler normalize-score V2 (squelette)
│   │   └── requirements.txt
│   └── newsletter/
│       ├── handler.py                 # 🚧 Handler newsletter V2 (squelette)
│       └── requirements.txt
├── vectora_core/                      # Bibliothèque métier
│   ├── shared/                        # ✅ Modules partagés entre Lambdas
│   │   ├── config_loader.py           # Chargement configurations S3
│   │   ├── s3_io.py                   # Opérations S3 standardisées
│   │   ├── models.py                  # Modèles de données communs
│   │   └── utils.py                   # Utilitaires transverses
│   ├── ingest/                        # ✅ Modules spécifiques ingest V2
│   │   ├── __init__.py                # Fonction run_ingest_for_client()
│   │   ├── source_fetcher.py          # Récupération contenus externes
│   │   ├── content_parser.py          # Parsing RSS/HTML/API
│   │   └── ingestion_profiles.py      # Profils d'ingestion canonical
│   ├── normalization/                 # 🚧 Modules spécifiques normalize-score V2
│   │   └── __init__.py                # (modules à implémenter)
│   └── newsletter/                    # 🚧 Modules spécifiques newsletter V2
│       └── __init__.py                # (modules à implémenter)
└── README.md
```

## État d'Avancement

### ✅ Phase 1 - Préparation et Sauvegarde
- Backup de l'état fonctionnel créé
- Analyse des dépendances documentée
- Tests de référence validés

### ✅ Phase 2 - Création de la Nouvelle Structure
- Structure de dossiers cible créée
- Modules existants déplacés vers nouveaux emplacements
- Squelettes des nouveaux modules créés
- Handlers squelettes pour normalize_score et newsletter
- Requirements.txt individuels créés

### ✅ Phase 3 - Mise à Jour des Imports et Intégration
- Tous les imports corrigés et fonctionnels
- Lambda ingest package et fonctionne correctement
- Aucune régression fonctionnelle détectée
- Tests d'intégration passent
- Packaging des 3 Lambdas validé

### 🚧 Phase 4 - Validation, Documentation et Finalisation
- Documentation de la nouvelle organisation *(en cours)*
- Scripts de build/deploy à adapter
- Validation conformité règles d'hygiène V4

## Lambdas Disponibles

### 🟢 Lambda ingest V2 (Fonctionnelle)

**Responsabilités :**
- Récupération des contenus bruts depuis sources externes (RSS, HTML, API)
- Parsing en items structurés
- Application des profils d'ingestion canonical
- Stockage dans S3 layer 'ingested/'

**Handler :** `lambdas/ingest/handler.py`
**Fonction principale :** `vectora_core.ingest.run_ingest_for_client()`

**Événement d'entrée :**
```json
{
  "client_id": "lai_weekly_v3",
  "sources": ["optional_source_filter"],
  "period_days": 7,
  "dry_run": false,
  "ingestion_mode": "balanced"
}
```

### 🟡 Lambda normalize-score V2 (Squelette)

**Responsabilités :** *(à implémenter)*
- Normalisation des items via Bedrock (extraction entités, classification)
- Matching des items aux domaines de veille du client
- Scoring de pertinence basé sur les règles métier
- Stockage dans S3 layer 'normalized/'

**Handler :** `lambdas/normalize_score/handler.py`
**Fonction principale :** `vectora_core.normalization.run_normalize_score_for_client()` *(à implémenter)*

### 🟡 Lambda newsletter V2 (Squelette)

**Responsabilités :** *(à implémenter)*
- Sélection des meilleurs items par section selon layout
- Génération de contenu éditorial via Bedrock (intro, TL;DR, résumés)
- Assemblage de la newsletter finale au format Markdown
- Calcul des métriques de veille et statistiques

**Handler :** `lambdas/newsletter/handler.py`
**Fonction principale :** `vectora_core.newsletter.run_newsletter_for_client()` *(à implémenter)*

## Tests et Validation

### Scripts de Test Disponibles

```bash
# Test des imports après restructuration
python test_imports.py

# Test du packaging des 3 Lambdas
python test_packaging.py

# Test d'exécution des handlers
python test_lambda_execution.py
```

### Résultats des Tests Phase 3

- ✅ **Imports** : Tous les modules importables sans erreur
- ✅ **Packaging** : Les 3 Lambdas peuvent être packagées (taille ~0.26 MB chacune)
- ✅ **Exécution** : Les handlers répondent correctement aux événements de test
- ✅ **Intégration** : Lambda ingest fonctionne sans régression

## Déploiements

### Séparation par Lambda

Chaque Lambda peut maintenant être déployée indépendamment :

- **ingest V2** : Prête pour déploiement production
- **normalize-score V2** : Squelette déployable (retourne "not_implemented")
- **newsletter V2** : Squelette déployable (retourne "not_implemented")

### Variables d'Environnement

#### Lambda ingest V2
```
ENV=prod
PROJECT_NAME=vectora-inbox
CONFIG_BUCKET=vectora-inbox-config-prod
DATA_BUCKET=vectora-inbox-data-prod
LOG_LEVEL=INFO
```

#### Lambda normalize-score V2
```
ENV=prod
PROJECT_NAME=vectora-inbox
CONFIG_BUCKET=vectora-inbox-config-prod
DATA_BUCKET=vectora-inbox-data-prod
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
LOG_LEVEL=INFO
```

#### Lambda newsletter V2
```
ENV=prod
PROJECT_NAME=vectora-inbox
CONFIG_BUCKET=vectora-inbox-config-prod
DATA_BUCKET=vectora-inbox-data-prod
NEWSLETTERS_BUCKET=vectora-inbox-newsletters-prod
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_REGION=us-east-1
LOG_LEVEL=INFO
```

## Prochaines Étapes

1. **Implémenter normalize-score V2** selon `docs/design/normalize_score_v2.md`
2. **Implémenter newsletter V2** selon `docs/design/newsletter_v2.md`
3. **Adapter les scripts de déploiement** pour les 3 Lambdas séparées
4. **Finaliser la documentation** de l'architecture V2

## Conformité Règles d'Hygiène V4

- ✅ **Séparation claire par Lambda** : Chaque Lambda a ses modules dédiés
- ✅ **Déploiements séparés** : Packaging individuel possible
- ✅ **Maintien de la clarté** : Organisation logique des modules
- ✅ **Éviter le code spaghetti** : Responsabilités bien définies
- ✅ **Modules partagés** : Code commun dans `vectora_core/shared/`