# Vectora Inbox - Plan de Refactorisation Pipeline Ingestion + Normalisation Basé sur des Runs

## Executive Summary

**Objectif** : Refactoriser le pipeline ingestion + normalisation pour qu'un run ne normalise que le scraping du dernier run, avec une structure S3 par run, sans casser le workflow actuel.

**Problème actuel** : Risque de re-normaliser beaucoup trop d'items à chaque run (historique complet).

**Solution cible** : Logique centrée run avec structure S3 par run et normalisation uniquement du RAW du run courant.

## État Actuel

### Architecture Actuelle

**Lambda ingest-normalize** (`vectora-inbox-ingest-normalize-dev`) :
- Scrape plusieurs sources (bouquets) configurées dans `client_config.source_config`
- Normalise TOUS les items récupérés avec Bedrock (potentiellement historique)
- Écrit les items normalisés dans S3 : `normalized/{client_id}/YYYY/MM/DD/items.json`

**Lambda engine** (`vectora-inbox-engine-dev`) :
- Lit les items normalisés depuis S3 sur une fenêtre `period_days`
- Applique matching + scoring + génération newsletter
- Utilise `_collect_normalized_items()` pour lire plusieurs jours

### Structure S3 Actuelle

```
s3://vectora-inbox-data-dev/
├── normalized/
│   └── {client_id}/
│       └── YYYY/MM/DD/
│           └── items.json  # Items normalisés du jour
```

### Flux Actuel

1. **Ingestion** : Scrape sources → items RAW en mémoire
2. **Normalisation** : Normalise TOUS les items RAW → items normalisés
3. **Stockage** : Écrit items normalisés dans S3 par date
4. **Engine** : Lit items normalisés sur fenêtre temporelle

### Problèmes Identifiés

- **Re-normalisation** : Si sources retournent historique, on re-normalise des items déjà traités
- **Coût Bedrock** : Appels inutiles sur items déjà normalisés
- **Performance** : Temps d'exécution croissant avec l'historique
- **Pas de traçabilité** : Impossible de savoir quel run a produit quels items

## Design Cible

### Concept de Run

**Run ID** : Identifiant unique par exécution = `run_YYYYMMDDTHHMMSSZ` (timestamp ISO compact)

**Exemple** : `run_20250115T143022Z`

### Nouvelle Structure S3

```
s3://vectora-inbox-data-dev/
├── raw/
│   └── {client_id}/
│       └── YYYY/MM/DD/
│           └── {run_id}/
│               ├── source_metadata.json    # Métadonnées du run
│               └── sources/
│                   ├── {source_key_1}.json
│                   ├── {source_key_2}.json
│                   └── ...
└── normalized/
    └── {client_id}/
        └── YYYY/MM/DD/
            └── {run_id}/
                └── items.json              # Items normalisés de ce run uniquement
```

### Nouveau Flux par Run

1. **Génération Run ID** : `run_YYYYMMDDTHHMMSSZ`
2. **Ingestion** : Scrape sources → écriture RAW dans `raw/{client_id}/YYYY/MM/DD/{run_id}/`
3. **Normalisation** : Lit uniquement le RAW de ce run → normalise → écrit dans `normalized/{client_id}/YYYY/MM/DD/{run_id}/`
4. **Engine** : Lit TOUS les runs normalisés sur la fenêtre `period_days` (pas de changement)

### Avantages

- **Pas de re-normalisation** : Chaque run ne traite que son propre RAW
- **Traçabilité complète** : Chaque item normalisé est lié à un run spécifique
- **Coût optimisé** : Bedrock appelé uniquement sur nouveaux items
- **Parallélisation future** : Possibilité de runs concurrents
- **Debugging** : Possibilité de rejouer un run spécifique

## Impacts sur les Modules

### 1. Handler Lambda (`src/lambdas/ingest_normalize/handler.py`)

**Changements** : Aucun (délègue à `vectora_core`)

### 2. Orchestrateur (`lambda-deps/vectora_core/__init__.py`)

**Fonction** : `run_ingest_normalize_for_client()`

**Changements** :
- Générer `run_id` au début
- Passer `run_id` aux modules ingestion/normalisation
- Adapter les chemins S3 pour inclure `run_id`

### 3. Module Ingestion (`lambda-deps/vectora_core/ingestion/`)

**Changements** :
- `fetcher.py` : Pas de changement (récupère toujours le contenu)
- `parser.py` : Pas de changement (parse toujours le contenu)
- **NOUVEAU** : Écriture RAW dans S3 avec structure par run

### 4. Module Normalisation (`lambda-deps/vectora_core/normalization/`)

**Changements** :
- `normalizer.py` : Lire RAW depuis S3 (au lieu de recevoir en mémoire)
- Écrire normalisé dans S3 avec structure par run

### 5. Module Storage (`lambda-deps/vectora_core/storage/`)

**Changements** :
- Nouvelles fonctions pour écriture/lecture avec `run_id`
- Fonctions existantes conservées pour compatibilité engine

### 6. Engine (`lambda-deps/vectora_core/__init__.py`)

**Fonction** : `run_engine_for_client()` et `_collect_normalized_items()`

**Changements** :
- `_collect_normalized_items()` doit lire TOUS les runs dans la fenêtre temporelle
- Parcourir `normalized/{client_id}/YYYY/MM/DD/*/items.json` (wildcard sur run_id)

## Roadmap par Phases

### Phase 0 – Design ✅

**Objectif** : Documenter l'état actuel et le design cible

**Livrables** :
- ✅ `docs/design/vectora_inbox_runs_based_ingestion_refactor_plan.md`

### Phase 1 – Refactor du schéma S3 + code ingest-normalize

**Objectif** : Implémenter la logique par run dans ingest-normalize

**Tâches** :
1. **Génération Run ID** : Ajouter fonction `generate_run_id()` dans `utils/`
2. **Écriture RAW** : Modifier ingestion pour écrire RAW dans S3 par run
3. **Lecture RAW** : Modifier normalisation pour lire RAW depuis S3
4. **Écriture Normalisé** : Adapter écriture normalisée avec structure par run
5. **Tests** : Vérifier que seul le RAW du run courant est normalisé

**Modules impactés** :
- `vectora_core/__init__.py` : Orchestration avec `run_id`
- `vectora_core/ingestion/` : Écriture RAW
- `vectora_core/normalization/` : Lecture RAW + écriture normalisée
- `vectora_core/storage/` : Nouvelles fonctions S3
- `vectora_core/utils/` : Génération `run_id`

**Livrable** :
- `docs/diagnostics/vectora_inbox_runs_based_ingestion_phase1_results.md`

### Phase 2 – Adaptation minimaliste de l'engine

**Objectif** : Adapter l'engine pour lire la nouvelle structure S3

**Tâches** :
1. **Analyser** : Comment `_collect_normalized_items()` lit actuellement S3
2. **Adapter** : Modifier pour lire `normalized/{client_id}/YYYY/MM/DD/*/items.json`
3. **Tester** : Vérifier que l'engine lit bien tous les runs sur `period_days`

**Modules impactés** :
- `vectora_core/__init__.py` : `_collect_normalized_items()`
- `vectora_core/storage/` : Fonctions de lecture avec wildcard

**Livrable** :
- `docs/diagnostics/vectora_inbox_runs_based_ingestion_phase2_engine_analysis.md`

### Phase 3 – Tests locaux

**Objectif** : Valider le comportement avec tests locaux

**Tâches** :
1. **Test unitaire** : 1 run ingestion+normalisation pour `lai_weekly_v2`
2. **Vérification** : Seule la dernière grappe RAW est normalisée
3. **Simulation S3** : Vérifier structure S3 simulée
4. **Test engine** : Vérifier lecture multi-runs

**Modules impactés** :
- `tests/` : Nouveaux tests pour logique par run

**Livrable** :
- `docs/diagnostics/vectora_inbox_runs_based_ingestion_phase3_local_tests.md`

### Phase 4 – Déploiement AWS DEV

**Objectif** : Déployer et tester en environnement AWS DEV

**Tâches** :
1. **Packaging** : Utiliser scripts existants (`package-ingest-normalize.ps1`)
2. **Déploiement** : Utiliser scripts existants (`deploy-runtime-dev.ps1`)
3. **Test E2E** : Run complet `lai_weekly_v2` avec `period_days=30`
4. **Validation** : Vérifier structure S3 réelle et performance

**Scripts utilisés** :
- `scripts/package-ingest-normalize.ps1`
- `scripts/deploy-runtime-dev.ps1`
- `scripts/test-ingest-normalize-profiles-dev.ps1`

**Livrable** :
- `docs/diagnostics/vectora_inbox_runs_based_ingestion_phase4_aws_dev_results.md`

### Phase 5 – Synthèse finale

**Objectif** : Documenter les changements et recommandations

**Tâches** :
1. **Synthèse** : Résumer ce qui a changé
2. **Documentation** : Comment fonctionne un run maintenant
3. **Tuning** : Leviers de performance (fréquence, sources, etc.)
4. **Risques** : Limites pour l'échelle (175 sources, PubMed, etc.)

**Livrable** :
- `docs/diagnostics/vectora_inbox_runs_based_ingestion_summary.md`

## Contraintes et Compatibilité

### Contraintes Respectées

1. **Pas de casse du workflow existant** :
   - Lambdas `vectora-inbox-ingest-normalize-dev` et `vectora-inbox-engine-dev` conservées
   - Scripts de déploiement réutilisés
   - Configuration client inchangée

2. **Une seule Lambda** :
   - Pas de split ingestion/normalisation
   - Code structuré en phases internes

3. **Compatibilité period_days** :
   - Engine continue à utiliser `period_days` pour sélection
   - Lecture de données déjà normalisées (pas de re-normalisation)

### Risques Identifiés

1. **Migration** : Période de transition où ancienne et nouvelle structure coexistent
2. **Storage** : Augmentation du nombre d'objets S3 (mais objets plus petits)
3. **Debugging** : Plus de complexité pour diagnostiquer les runs
4. **Concurrence** : Gestion des runs simultanés (hors scope MVP)

### Stratégie de Migration

1. **Déploiement progressif** : Tester d'abord sur `lai_weekly_v2`
2. **Coexistence** : Engine lit ancienne ET nouvelle structure pendant transition
3. **Monitoring** : Surveiller performance et coûts
4. **Rollback** : Possibilité de revenir à l'ancienne logique si problème

## Métriques de Succès

### Performance

- **Temps d'exécution** : Réduction attendue de 30-50% (pas de re-normalisation)
- **Coût Bedrock** : Réduction proportionnelle au taux de re-normalisation évité
- **Latence** : Temps de réponse stable même avec historique croissant

### Qualité

- **Traçabilité** : 100% des items normalisés liés à un run
- **Consistance** : Pas de doublons entre runs
- **Fiabilité** : Pas de régression sur qualité des newsletters

### Opérationnel

- **Monitoring** : Métriques par run (items RAW, normalisés, temps)
- **Debugging** : Capacité à rejouer un run spécifique
- **Maintenance** : Nettoyage automatique des anciens runs (futur)

## Conclusion

Cette refactorisation apporte une amélioration significative de l'architecture Vectora Inbox en introduisant une logique centrée run qui :

1. **Élimine la re-normalisation** inutile d'items historiques
2. **Optimise les coûts** Bedrock et les performances
3. **Améliore la traçabilité** et le debugging
4. **Prépare l'évolution** vers des architectures plus avancées

Le plan respecte toutes les contraintes métier et techniques, avec une approche progressive et des points de validation à chaque phase.