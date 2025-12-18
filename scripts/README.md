# Scripts Vectora Inbox - Processus de Build Standard V4

## Vue d'Ensemble

Ce dossier contient les scripts standardisés pour le build, déploiement et test des Lambdas Vectora Inbox, conformes aux règles d'hygiène V4.

## Architecture Lambda Layers

### Layers Créés
- **vectora-inbox-vectora-core-dev** : Contient `vectora_core/` (0.4MB)
- **vectora-inbox-common-deps-dev** : Contient PyYAML, requests, feedparser, beautifulsoup4, python-dateutil (3.3MB)

### Bénéfices
- Handlers <2KB (vs >50MB avant)
- Réutilisation entre Lambdas
- Cold start optimisé
- Conformité règles V4

## Structure des Scripts

```
scripts/
├── layers/                    # Gestion des Lambda Layers
│   ├── create_vectora_core_layer.py
│   └── create_common_deps_layer.py
├── build/                     # Build des handlers
│   └── build_normalize_score_v2.py
├── deploy/                    # Déploiement
│   └── deploy_normalize_score_v2_layers.py
└── invoke/                    # Tests et invocation
    ├── invoke_normalize_score_v2.py
    └── test_events/
        ├── lai_weekly_v3.json
        └── minimal_test.json
```

## Processus Standard (4 étapes)

### 1. Création des Layers (une fois)
```bash
# Créer le layer vectora-core
python scripts/layers/create_vectora_core_layer.py

# Créer le layer common-deps
python scripts/layers/create_common_deps_layer.py
```

### 2. Build du Handler
```bash
python scripts/build/build_normalize_score_v2.py
```

### 3. Déploiement
```bash
python scripts/deploy/deploy_normalize_score_v2_layers.py
```

### 4. Test
```bash
# Test simple
python scripts/invoke/invoke_normalize_score_v2.py --event lai_weekly_v3

# Test de performance
python scripts/invoke/invoke_normalize_score_v2.py --performance

# Validation uniquement
python scripts/invoke/invoke_normalize_score_v2.py --validate-only
```

## Configuration AWS

### Prérequis
- Profil AWS : `rag-lai-prod`
- Région : `eu-west-3`
- Compte : `786469175371`

### Buckets S3
- `vectora-inbox-config-dev` : Configuration
- `vectora-inbox-data-dev` : Données
- `vectora-inbox-lambda-code-dev` : Code Lambda

## Métriques de Performance

| Métrique | Avant (Scripts Fix) | Après (Layers) | Amélioration |
|----------|---------------------|----------------|--------------|
| Taille handler | >50MB | 1.7KB | 99.997% |
| Layers | 0 | 2 | Architecture V4 |
| Déploiement | 3 scripts | 1 script | Simplifié |
| Conformité V4 | ❌ | ✅ | Conforme |

## Scripts Archivés

Les scripts suivants ont été archivés dans `/backup/scripts/` :
- `fix_yaml_dependency.py` : Hack PyYAML obsolète
- `fix_all_dependencies.py` : Installation manuelle obsolète
- `deploy_normalize_score_v2_old.py` : Ancien déploiement

## Règles d'Hygiène Respectées

- ✅ Handler <5MB (1.7KB)
- ✅ Dépendances via Lambda Layers
- ✅ Process de build reproductible
- ✅ Scripts organisés par fonction
- ✅ Events de test standardisés
- ✅ Validation automatique

## Prochaines Étapes

1. **Appliquer à ingest_v2** : Réutiliser les layers créés
2. **Créer newsletter_v2** : Même architecture layers
3. **Généraliser le processus** : Template pour futures Lambdas

## Support

Pour toute question sur ce processus, référez-vous aux règles d'hygiène V4 dans `.q-context/src_lambda_hygiene_v4.md`.