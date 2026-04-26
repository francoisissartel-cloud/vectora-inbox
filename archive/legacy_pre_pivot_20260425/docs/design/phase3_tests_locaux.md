# Phase 3 – Tests locaux (sur le client lai_weekly_v3) : TERMINÉE ✅

## Scripts de test créés

### ✅ `scripts/test_ingest_v2_local.py`
**Script principal de test local** avec fonctionnalités complètes :

**Fonctionnalités :**
- Configuration automatique des variables d'environnement AWS
- Support de 3 types d'events : minimal, full, dry-run
- Arguments en ligne de commande pour personnalisation
- Logging détaillé avec timestamps
- Gestion d'erreurs robuste
- Rapport de résultats structuré

**Usage :**
```bash
# Test rapide avec 2 sources
python scripts/test_ingest_v2_local.py --event minimal

# Test complet avec toutes les sources
python scripts/test_ingest_v2_local.py --event full

# Test sans écriture S3
python scripts/test_ingest_v2_local.py --event dry-run

# Test personnalisé
python scripts/test_ingest_v2_local.py --sources "press_corporate__medincell" --period-days 14 --dry-run
```

### ✅ `scripts/validate_s3_output.py`
**Script de validation de la sortie S3** pour analyser la qualité :

**Fonctionnalités :**
- Vérification existence fichier S3
- Validation format JSON
- Analyse complétude des champs requis
- Répartition par source et langue
- Statistiques qualité du contenu
- Échantillon d'items pour inspection

**Usage :**
```bash
# Validation pour aujourd'hui
python scripts/validate_s3_output.py --client lai_weekly_v3

# Validation pour date spécifique
python scripts/validate_s3_output.py --client lai_weekly_v3 --date 2025-01-15
```

## Events de test créés

### ✅ `events/test_lai_weekly_minimal.json`
Event de test rapide avec 2 sources corporate :
- `press_corporate__medincell`
- `press_corporate__camurus`
- `period_days: 7`
- `dry_run: false`

### ✅ `events/test_lai_weekly_full.json`
Event de test complet :
- Toutes les sources configurées pour `lai_weekly_v3`
- `period_days: 30`
- `dry_run: false`

### ✅ `events/test_lai_weekly_dry_run.json`
Event de test simulation :
- 1 source corporate + 1 source presse
- `period_days: 7`
- `dry_run: true`

## Configuration des tests

### Variables d'environnement automatiques
Les scripts configurent automatiquement :
```bash
AWS_PROFILE=rag-lai-prod
AWS_REGION=eu-west-3
CONFIG_BUCKET=vectora-inbox-config-dev
DATA_BUCKET=vectora-inbox-data-dev
LOG_LEVEL=INFO
```

### Prérequis système
- **Profil AWS** `rag-lai-prod` configuré
- **Accès S3** aux buckets config et data
- **Dépendances Python** : boto3, yaml, requests, feedparser, beautifulsoup4

## Workflow de test recommandé

### 1. Test dry-run (validation rapide)
```bash
python scripts/test_ingest_v2_local.py --event dry-run
```
**Objectif :** Valider le code sans écriture S3

### 2. Test minimal (écriture S3)
```bash
python scripts/test_ingest_v2_local.py --event minimal
```
**Objectif :** Test avec 2 sources et écriture S3

### 3. Validation sortie S3
```bash
python scripts/validate_s3_output.py --client lai_weekly_v3
```
**Objectif :** Analyser la qualité des données écrites

### 4. Test complet (si précédents OK)
```bash
python scripts/test_ingest_v2_local.py --event full
```
**Objectif :** Test avec toutes les sources configurées

## Format de sortie attendu

### Chemin S3
`s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/{YYYY}/{MM}/{DD}/items.json`

### Structure des items
```json
[
  {
    "item_id": "press_corporate__medincell_20250115_abc123",
    "source_key": "press_corporate__medincell",
    "source_type": "press_corporate",
    "title": "Article title...",
    "content": "Full content...",
    "url": "https://source.com/article",
    "published_at": "2025-01-15",
    "ingested_at": "2025-01-15T10:30:00Z",
    "language": "en",
    "content_hash": "sha256:...",
    "metadata": {
      "author": "Author name",
      "tags": ["tag1"],
      "word_count": 450
    }
  }
]
```

## Validation des résultats

### Métriques de succès
- **Sources traitées** : > 0
- **Items ingérés** : > 0
- **Taux d'erreur sources** : < 50%
- **Complétude champs requis** : 100%
- **Format JSON** : Valide
- **Temps d'exécution** : < 5min pour test minimal

### Rapport de test type
```
✅ TEST RÉUSSI
Client : lai_weekly_v3
Sources traitées : 2
Sources en échec : 0
Items ingérés : 12
Items filtrés (anciens) : 3
Items dédupliqués : 1
Items finaux : 8
Temps d'exécution : 15.3s
Sortie S3 : s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/2025/01/15/items.json
```

## Gestion des erreurs

### Erreurs attendues (non bloquantes)
- **Sources temporairement indisponibles** : Normal, n'interrompt pas le traitement
- **Flux RSS malformés** : Gestion dégradée avec feedparser
- **HTML non parsable** : Fallback gracieux

### Erreurs critiques (bloquantes)
- **Profil AWS non configuré** : Vérifier `aws configure list --profile rag-lai-prod`
- **Permissions S3 manquantes** : Vérifier accès aux buckets
- **Dépendances Python manquantes** : Installer avec pip

## Documentation créée

### ✅ `scripts/README.md`
Documentation complète des scripts avec :
- Instructions d'usage détaillées
- Exemples de commandes
- Workflow de test recommandé
- Guide de dépannage
- Prérequis et configuration

## Critères de succès Phase 3

- [x] Script de test local fonctionnel créé
- [x] Events de test pour différents scénarios
- [x] Script de validation de sortie S3
- [x] Configuration automatique environnement AWS
- [x] Gestion d'erreurs et logging appropriés
- [x] Documentation complète des tests
- [x] Workflow de test structuré en 4 étapes
- [x] Validation format de sortie conforme
- [x] Support mode dry-run pour tests sécurisés

## Prochaine étape

**Phase 4 – Packaging & déploiement AWS** :
- Créer package de déploiement (ZIP)
- Mettre à jour infrastructure CloudFormation
- Déployer Lambda `vectora-inbox-ingest-v2-dev`
- Configurer variables d'environnement et permissions IAM
- Tester déploiement et logs CloudWatch

La Phase 3 est **TERMINÉE** avec succès. Scripts de test complets prêts pour validation locale avant déploiement AWS.