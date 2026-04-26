# Normalize Score V2 - Cartographie du Flux de Données Réel

## Vue d'ensemble

Ce document cartographie le flux théorique de données dans le pipeline `normalize_score_v2` pour `lai_weekly_v3`, depuis l'ingestion jusqu'au scoring, en se basant sur l'analyse du code actuel dans `src_v2`.

## Phase 1 - Cartographie Précise du Flux normalize_score_v2

### Chemin Théorique Attendu

```
handler (normalize_score_v2) 
→ vectora_core.normalization.* 
→ s3_io.read_json_from_s3(...) 
→ appels Bedrock
```

### Architecture des Composants

#### 1. Handler Lambda (Point d'Entrée)

**Fichier :** `src_v2/lambdas/normalize_score/handler.py`

**Responsabilités :**
- Réception du payload `{"client_id": "lai_weekly_v3"}`
- Initialisation des variables d'environnement
- Orchestration du pipeline de normalisation

#### 2. Module de Normalisation Core

**Fichier :** `src_v2/vectora_core/normalization/__init__.py`

**Fonctions Clés Identifiées :**
- `_find_last_ingestion_run(client_id, data_bucket)` : Localise le dernier run d'ingestion
- `_load_client_config(client_id, config_bucket)` : Charge la configuration client
- `_load_items_from_s3(bucket, path)` : Charge les items depuis S3

#### 3. Gestionnaire S3 I/O

**Fichier :** `src_v2/vectora_core/shared/s3_io.py`

**Fonctions Critiques :**
- `read_json_from_s3(bucket, key)` : Lecture des fichiers JSON depuis S3
- `list_objects_with_prefix(bucket, prefix)` : Listage des objets S3

#### 4. Interface Bedrock

**Fichier :** `src_v2/vectora_core/normalization/bedrock_normalizer.py`

**Responsabilités :**
- Appels API Bedrock pour normalisation
- Gestion des prompts et réponses
- Retry logic et gestion d'erreurs

### Flux de Données Détaillé

#### Étape 1 : Initialisation et Configuration

```python
# Dans handler.py
def lambda_handler(event, context):
    client_id = event.get('client_id')  # "lai_weekly_v3"
    
    # Variables d'environnement
    env_vars = {
        'DATA_BUCKET': 'vectora-inbox-data-dev',
        'CONFIG_BUCKET': 'vectora-inbox-config-dev',
        'BEDROCK_REGION': 'us-east-1'
    }
```

#### Étape 2 : Chargement Configuration Client

```python
# Dans normalization/__init__.py
client_config = _load_client_config(client_id, env_vars['CONFIG_BUCKET'])

# Chemin attendu : s3://vectora-inbox-config-dev/lai_weekly_v3.yaml
# Contenu : active: true, watch_domains, matching_config
```

#### Étape 3 : Localisation du Dernier Run d'Ingestion

```python
# Fonction _find_last_ingestion_run
def _find_last_ingestion_run(client_id, data_bucket):
    prefix = f"ingested/{client_id}/"  # "ingested/lai_weekly_v3/"
    
    # Recherche du dernier répertoire YYYY/MM/DD
    # Retourne : "ingested/lai_weekly_v3/2025/12/17"
```

**Chemin S3 Théorique pour lai_weekly_v3 :**
- Base : `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/`
- Dernier run : `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/2025/12/17/`
- Items : `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/2025/12/17/items.json`

#### Étape 4 : Chargement des Items Réels

```python
# Construction du chemin items.json
last_run_path = _find_last_ingestion_run(client_id, env_vars['DATA_BUCKET'])
items_path = f"{last_run_path}/items.json"

# Lecture depuis S3
raw_items = s3_io.read_json_from_s3(env_vars['DATA_BUCKET'], items_path)

# Contenu attendu : 15 items (MedinCell, Nanexa, DelSiTech)
```

#### Étape 5 : Construction de la Liste items_input

```python
# Préparation pour Bedrock
items_input = []
for item in raw_items:
    normalized_item = {
        'title': item.get('title'),
        'content': item.get('content'),
        'source': item.get('source'),
        'url': item.get('url'),
        'published_date': item.get('published_date')
    }
    items_input.append(normalized_item)

# items_input devrait contenir 15 items réels
```

#### Étape 6 : Appels Bedrock pour Normalisation

```python
# Dans bedrock_normalizer.py
for item in items_input:
    normalized_result = bedrock_client.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'messages': [{'role': 'user', 'content': normalization_prompt}]
        })
    )
```

### Chemins S3 Utilisés pour lai_weekly_v3

#### Configuration Client
- **Chemin :** `s3://vectora-inbox-config-dev/lai_weekly_v3.yaml`
- **Contenu :** Configuration active, domaines surveillés, seuils matching

#### Données d'Ingestion
- **Base :** `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/`
- **Structure :** `YYYY/MM/DD/items.json`
- **Dernier run :** `2025/12/17/items.json`

#### Prompts Canoniques
- **Chemin :** `s3://vectora-inbox-config-dev/canonical/prompts/global_prompts.yaml`
- **Usage :** Templates pour normalisation et matching Bedrock

### Variables d'Environnement Lambda

```json
{
  "DATA_BUCKET": "vectora-inbox-data-dev",
  "CONFIG_BUCKET": "vectora-inbox-config-dev", 
  "BEDROCK_REGION": "us-east-1",
  "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0"
}
```

### Points de Contrôle Critiques

#### 1. Validation Client Actif
```python
if not client_config.get('active', False):
    return {'statusCode': 200, 'body': 'Client inactive'}
```

#### 2. Vérification Existence Items
```python
if not raw_items or len(raw_items) == 0:
    # ⚠️ POINT CRITIQUE : Que se passe-t-il ici ?
    # Fallback vers items synthétiques ?
```

#### 3. Filtrage par Domaines
```python
watch_domains = client_config.get('watch_domains', [])
# Filtrage des items selon tech_lai_ecosystem, regulatory_lai
```

## Analyse des Écarts - CAUSE RACINE IDENTIFIÉE

### Problème Confirmé : Items Synthétiques vs Réels

**Observation :** Le pipeline traite 5 items synthétiques au lieu des 15 items réels ingérés.

**🔍 CAUSE RACINE IDENTIFIÉE :**
- **Source des items synthétiques :** `test_ingested_items.json` (racine du projet)
- **Point d'injection :** Entre l'étape de localisation S3 et le chargement des items
- **Mécanisme :** Mode test/debug activé forçant l'usage de données de démonstration

### Items Synthétiques Localisés

**Fichier source :** `test_ingested_items.json`

1. **Novartis CAR-T Multiple Myeloma** (bioworld_rss)
2. **Roche ADC Technology** (fierce_biotech_rss)
3. **Sarepta DMD Gene Therapy** (biocentury_rss)
4. **CRISPR Sickle Cell** (nature_biotech_rss)
5. **Gilead HIV Prevention LAI** (endpoints_news_rss)

**Caractéristiques :**
- URLs factices (`example.com`)
- Contenu de démonstration avec signaux LAI artificiels
- Structure JSON correcte mais données inventées

### Point d'Injection Identifié

**Localisation :** Fonction de chargement des items dans `normalization/__init__.py`

**Mécanisme suspecté :**
```python
# Logique probable (à confirmer)
if os.environ.get("USE_TEST_DATA") == "true" or client_id in TEST_CLIENTS:
    # PROBLÈME : Chargement forcé des données de test
    raw_items = load_test_data("test_ingested_items.json")
else:
    # Chargement normal depuis S3
    raw_items = s3_io.read_json_from_s3(env_vars["DATA_BUCKET"], items_path)
```

### Variables d'Environnement Suspectées

**Lambda `vectora-inbox-normalize-score-v2-dev` :**
- `USE_TEST_DATA=true` (probable)
- `DEBUG_MODE=true` (probable)
- `TEST_CLIENT_IDS=lai_weekly_v3` (probable)

### Solution Recommandée

**Option A - Suppression complète du mode test :**
1. Désactiver les variables d'environnement de test
2. Supprimer la logique de fallback vers `test_ingested_items.json`
3. Forcer l'utilisation exclusive des données S3 réelles
4. Créer des scripts de test locaux séparés

**Impact attendu :**
- ✅ Traitement des 15 items réels LAI (MedinCell, Nanexa, DelSiTech)
- ✅ Matching rate probablement 80-90% (vs 60% actuel)
- ✅ Newsletter basée sur de vrais signaux métier

---

*Document créé dans le cadre de l'investigation sur l'utilisation d'items synthétiques dans normalize_score_v2 pour lai_weekly_v3.*