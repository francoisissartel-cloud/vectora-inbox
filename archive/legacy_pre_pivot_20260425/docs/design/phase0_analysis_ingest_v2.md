# Phase 0 – Analyse & Cadrage : vectora-inbox-ingest-V2

## Résumé de l'analyse

L'analyse de l'existant V1 révèle une architecture solide et conforme aux règles d'hygiène V4. Le handler existant suit parfaitement le pattern attendu : orchestration minimale avec délégation à `vectora_core`. La structure modulaire de `vectora_core` est bien organisée et réutilisable.

## Analyse du handler existant V1

### Structure du handler (`/src/lambdas/ingest_normalize/handler.py`)

**✅ BONNES PRATIQUES OBSERVÉES :**
- Handler minimal avec logique déléguée à `vectora_core`
- Gestion d'erreurs propre avec try/catch
- Variables d'environnement bien structurées
- Logging approprié avec niveaux configurables
- Format de réponse standardisé (statusCode + body)

**Pattern d'orchestration :**
```python
def lambda_handler(event, context):
    # 1. Validation event (client_id obligatoire)
    # 2. Lecture variables d'environnement
    # 3. Appel fonction orchestratrice vectora_core
    # 4. Formatage réponse
    # 5. Gestion erreurs globales
```

**Variables d'environnement utilisées :**
- `ENV` : Environnement (dev/prod)
- `PROJECT_NAME` : Nom du projet
- `CONFIG_BUCKET` : Bucket de configuration S3
- `DATA_BUCKET` : Bucket de données S3
- `BEDROCK_MODEL_ID` : Modèle Bedrock (non utilisé en V2 ingest)
- `PUBMED_API_KEY_PARAM` : Clé API PubMed
- `LOG_LEVEL` : Niveau de logging

## Analyse de vectora_core V1

### Structure modulaire excellente

```
/src/vectora_core/
├── config/          # Chargement configurations
├── ingestion/       # Récupération contenus (fetcher, parser)
├── normalization/   # Normalisation Bedrock (non utilisé en V2)
├── matching/        # Matching domaines (non utilisé en V2)
├── scoring/         # Scoring items (non utilisé en V2)
├── newsletter/      # Génération newsletter (non utilisé en V2)
├── storage/         # Opérations S3
└── utils/           # Utilitaires transverses
```

**✅ MODULES RÉUTILISABLES POUR V2 :**
- `config/loader.py` : Chargement client_config et canonical
- `ingestion/fetcher.py` : Récupération contenus HTTP/RSS
- `ingestion/parser.py` : Parsing contenus en items
- `storage/s3_client.py` : Opérations S3
- `utils/` : Utilitaires dates, logging, config

**❌ MODULES NON UTILISÉS EN V2 :**
- `normalization/` : Délégué à normalize-score V2
- `matching/` : Délégué à normalize-score V2
- `scoring/` : Délégué à normalize-score V2
- `newsletter/` : Délégué à newsletter V2

### Fonction orchestratrice V1

La fonction `run_ingest_normalize_for_client()` dans `__init__.py` fait :
1. **Ingestion** (Phase 1A) : récupération + parsing
2. **Normalisation** (Phase 1B) : appels Bedrock

**Pour V2, on ne garde que la Phase 1A (ingestion brute).**

## Analyse des configurations

### Format des events d'entrée (compatible V2)

```json
{
  "client_id": "lai_weekly_v3",
  "sources": ["press_corporate__medincell"],
  "period_days": 7,
  "from_date": "2025-01-01",
  "to_date": "2025-01-07"
}
```

### Configuration client (`lai_weekly_v3.yaml`)

**✅ ÉLÉMENTS UTILISÉS PAR INGEST V2 :**
- `source_config.source_bouquets_enabled` : Bouquets de sources
- `source_config.sources_extra_enabled` : Sources supplémentaires
- `pipeline.default_period_days` : Fenêtre temporelle par défaut

**❌ ÉLÉMENTS NON UTILISÉS PAR INGEST V2 :**
- `watch_domains` : Utilisé par normalize-score V2
- `matching_config` : Utilisé par normalize-score V2
- `scoring_config` : Utilisé par scoring V2
- `newsletter_layout` : Utilisé par newsletter V2

### Catalogue des sources (`source_catalog.yaml`)

**✅ SOURCES MVP DISPONIBLES :**
- **Corporate LAI** (5 sources) : MedinCell, Camurus, DelSiTech, Nanexa, Peptron
- **Presse sectorielle** (3 sources) : FierceBiotech, FiercePharma, Endpoints News

**✅ BOUQUETS CONFIGURÉS :**
- `lai_corporate_mvp` : 5 sources corporate
- `lai_press_mvp` : 3 sources presse

**✅ MODES D'INGESTION :**
- `html` : Pour sources corporate (scraping pages news)
- `rss` : Pour sources presse (flux RSS)

### Profils d'ingestion (`ingestion_profiles.yaml`)

**✅ PROFILS DISPONIBLES :**
- `corporate_pure_player_broad` : Ingestion large pour pure players
- `press_technology_focused` : Ingestion focalisée pour presse sectorielle

## Spécifications techniques V2

### Différences V1 vs V2

| Aspect | V1 (ingest-normalize) | V2 (ingest seulement) |
|--------|----------------------|------------------------|
| **Phases** | 1A (ingest) + 1B (normalize) | 1A (ingest) seulement |
| **Bedrock** | Oui (normalisation) | Non |
| **Sortie S3** | `normalized/` | `ingested/` |
| **Taille** | Plus complexe | Plus simple |
| **Dépendances** | Bedrock SDK | Aucune (boto3 standard) |

### Format de sortie V2

**Chemin S3 :** `s3://vectora-inbox-data-dev/ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json`

**Structure des items :**
```json
[
  {
    "item_id": "press_corporate__medincell_20250115_001",
    "source_key": "press_corporate__medincell",
    "source_type": "rss",
    "title": "MedinCell Announces Partnership...",
    "content": "Full article content...",
    "url": "https://www.medincell.com/news/...",
    "published_at": "2025-01-15",
    "ingested_at": "2025-01-15T10:30:00Z",
    "language": "en",
    "content_hash": "sha256:abc123...",
    "metadata": {
      "author": "MedinCell Press Team",
      "tags": ["partnership"],
      "word_count": 450
    }
  }
]
```

## Alignement avec les règles d'hygiène V4

### ✅ CONFORMITÉ OBSERVÉE

1. **Environnement AWS de référence :**
   - Région : `eu-west-3` (Paris)
   - Profil : `rag-lai-prod`
   - Compte : `786469175371`

2. **Conventions de nommage :**
   - Buckets : `vectora-inbox-{type}-dev`
   - Lambda future : `vectora-inbox-ingest-v2-dev`

3. **Structure modulaire :**
   - Handler minimal
   - Logique dans `vectora_core`
   - Pas de dépendances tierces copiées

4. **Pilotage par configuration :**
   - Aucune logique métier hardcodée
   - Configuration via `client_config` et `canonical`

### ⚠️ POINTS D'ATTENTION POUR V2

1. **Simplification nécessaire :**
   - Retirer les appels Bedrock
   - Simplifier la sortie S3 (pas de normalisation)

2. **Nouveau naming :**
   - Lambda : `vectora-inbox-ingest-v2-dev`
   - Logs : `/aws/lambda/vectora-inbox-ingest-v2-dev`

3. **Variables d'environnement ajustées :**
   - Retirer `BEDROCK_MODEL_ID` (non utilisé)
   - Garder `CONFIG_BUCKET`, `DATA_BUCKET`

## Validation des spécifications V2

### Workflow métier simplifié

1. **Validation event** : Vérifier `client_id`
2. **Chargement configs** : Client + canonical depuis S3
3. **Résolution sources** : Développer bouquets en sources individuelles
4. **Calcul fenêtre temporelle** : Résoudre `period_days`
5. **Ingestion par source** : HTTP GET, parsing RSS/HTML
6. **Parsing contenus** : Transformer en items structurés
7. **Filtrage temporel** : Éliminer items trop anciens
8. **Déduplication** : Éviter doublons par `content_hash`
9. **Écriture S3** : Stocker dans `ingested/`
10. **Retour statistiques** : Sources traitées, items ingérés

### Critères de succès Phase 0

- [x] Analyse complète de l'existant V1 documentée
- [x] Spécifications techniques V2 validées
- [x] Structure `/src_v2` définie et approuvée
- [x] Variables d'environnement identifiées
- [x] Alignement avec règles d'hygiène V4 confirmé
- [x] Différences V1/V2 clarifiées
- [x] Format de sortie S3 spécifié

## Recommandations pour Phase 1

1. **Réutiliser au maximum** les modules `vectora_core` existants
2. **Simplifier** en retirant tout ce qui concerne la normalisation
3. **Adapter** les chemins S3 (`normalized/` → `ingested/`)
4. **Conserver** la même structure d'event d'entrée
5. **Maintenir** la compatibilité avec les configurations existantes

## Risques identifiés

1. **Compatibilité formats** : S'assurer que les items générés sont compatibles avec normalize-score V2
2. **Performance** : Vérifier que l'ingestion seule reste dans les limites Lambda (15min)
3. **Dépendances manquantes** : Identifier si des libs spécifiques sont nécessaires pour le parsing

La Phase 0 est **TERMINÉE** avec succès. Prêt pour la Phase 1.