# Architecture `src/` pour Vectora Inbox MVP

**Date** : 2025-01-15  
**Statut** : Proposition (Phase 1 - pas d'implémentation)

---

⚠️ **Dans cette étape je ne modifie aucun fichier, je propose uniquement une architecture src/.**

Ce document propose l'architecture du code Python pour Vectora Inbox MVP, basée sur :
- Les contrats métier des Lambdas (`contracts/lambdas/`)
- L'overview du projet (`.q-context/vectora-inbox-overview.md`)
- Les règles Q (`.q-context/vectora-inbox-q-rules.md`)
- Le diagnostic complet (`docs/diagnostics/vectora-inbox-deep-diagnostic.md`)
- Les configurations canonical et client

---

## 1. Arborescence proposée pour `src/`

```text
src/
├── lambdas/
│   ├── ingest_normalize/
│   │   └── handler.py                    # Handler AWS Lambda pour ingest-normalize
│   └── engine/
│       └── handler.py                    # Handler AWS Lambda pour engine
│
├── vectora_core/
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── loader.py                     # Chargement des configs depuis S3
│   │   └── resolver.py                   # Résolution des bouquets, scopes
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── fetcher.py                    # Appels HTTP (RSS, APIs)
│   │   └── parser.py                     # Parsing RSS/XML/JSON
│   │
│   ├── normalization/
│   │   ├── __init__.py
│   │   ├── bedrock_client.py             # Appels Bedrock pour normalisation
│   │   ├── entity_detector.py            # Détection d'entités (règles + Bedrock)
│   │   └── normalizer.py                 # Orchestration normalisation
│   │
│   ├── matching/
│   │   ├── __init__.py
│   │   └── matcher.py                    # Logique de matching (intersections)
│   │
│   ├── scoring/
│   │   ├── __init__.py
│   │   └── scorer.py                     # Calcul des scores (règles numériques)
│   │
│   ├── newsletter/
│   │   ├── __init__.py
│   │   ├── bedrock_client.py             # Appels Bedrock pour génération éditoriale
│   │   ├── assembler.py                  # Assemblage de la newsletter
│   │   └── formatter.py                  # Formatage Markdown
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── s3_client.py                  # Lecture/écriture S3
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py                     # Configuration logging
│       └── date_utils.py                 # Utilitaires dates/périodes
│
├── requirements.txt                       # Dépendances Python
└── README.md                              # Documentation du code
```

---

## 2. Explication détaillée de l'architecture

### 2.1 `lambdas/` – Entrypoints AWS minces

**Rôle** : contenir les handlers AWS Lambda, qui sont de simples points d'entrée.

**Responsabilités** :
- Parser l'événement d'entrée (JSON).
- Lire les variables d'environnement (buckets S3, modèle Bedrock, etc.).
- Appeler les fonctions de haut niveau de `vectora_core/`.
- Formater la réponse (statusCode, body JSON).
- Gérer les erreurs de haut niveau (try/except global).

**Fonctions principales** :
- `lambdas/ingest_normalize/handler.py` :
  - `lambda_handler(event, context)` : point d'entrée pour `vectora-inbox-ingest-normalize`.
  - Appelle `run_ingest_normalize_for_client(client_id, ...)` depuis `vectora_core`.

- `lambdas/engine/handler.py` :
  - `lambda_handler(event, context)` : point d'entrée pour `vectora-inbox-engine`.
  - Appelle `run_engine_for_client(client_id, ...)` depuis `vectora_core`.

**Handlers AWS attendus** :
- Pour `vectora-inbox-ingest-normalize` : `lambdas.ingest_normalize.handler.lambda_handler`
- Pour `vectora-inbox-engine` : `lambdas.engine.handler.lambda_handler`

**Principe clé** : les handlers ne contiennent AUCUNE logique métier. Ils délèguent tout à `vectora_core/`.

---

### 2.2 `vectora_core/` – Bibliothèque métier réutilisable

**Rôle** : contenir toute la logique métier de Vectora Inbox, indépendamment d'AWS Lambda.

**Avantages** :
- Code testable unitairement (sans simuler Lambda).
- Réutilisable dans d'autres contextes (CLI, notebooks, autres Lambdas).
- Séparation claire entre "plomberie AWS" et "logique métier".

---

### 2.3 `vectora_core/config/` – Chargement et résolution des configurations

**Rôle** : charger les configurations depuis S3 (canonical + client) et résoudre les références (bouquets, scopes).

**Modules** :

- **`loader.py`** :
  - `load_client_config(s3_client, bucket, client_id)` : charge le YAML client depuis S3.
  - `load_canonical_scopes(s3_client, bucket, scope_type)` : charge un fichier canonical (ex : `company_scopes.yaml`).
  - `load_source_catalog(s3_client, bucket)` : charge le catalogue de sources.
  - `load_scoring_rules(s3_client, bucket)` : charge les règles de scoring.

- **`resolver.py`** :
  - `resolve_source_bouquets(source_catalog, bouquets_enabled, sources_extra)` : résout les bouquets en liste de `source_key`.
  - `resolve_scopes_for_domain(canonical_scopes, domain_config)` : charge les listes canonical référencées par un `watch_domain`.

**Principe clé** : ces modules ne font QUE charger et résoudre. Ils ne contiennent pas de logique métier (matching, scoring, etc.).

---

### 2.4 `vectora_core/ingestion/` – Phase 1A (sans Bedrock)

**Rôle** : récupérer les contenus bruts depuis les sources externes (RSS, APIs).

**Modules** :

- **`fetcher.py`** :
  - `fetch_rss(url, timeout)` : effectue un appel HTTP GET vers un flux RSS.
  - `fetch_api(url, params, headers, timeout)` : effectue un appel HTTP vers une API (PubMed, ClinicalTrials.gov, etc.).
  - Gère les retries, les timeouts, les erreurs HTTP.

- **`parser.py`** :
  - `parse_rss(xml_content)` : parse un flux RSS/XML et extrait les items bruts (titre, description, URL, date).
  - `parse_json_api(json_content, api_type)` : parse une réponse JSON d'API (PubMed, ClinicalTrials.gov, etc.).
  - Retourne une liste d'items bruts (dictionnaires Python).

**Principe clé** : pas d'appel Bedrock ici. C'est de la "plomberie HTTP" pure.

---

### 2.5 `vectora_core/normalization/` – Phase 1B (avec Bedrock + règles)

**Rôle** : transformer les items bruts en items normalisés (extraction d'entités, classification d'événements, génération de résumés).

**Modules** :

- **`bedrock_client.py`** :
  - `invoke_bedrock_for_normalization(model_id, prompt, region)` : appelle Bedrock pour normaliser un item.
  - Construit le prompt avec le texte de l'item + les listes canonical + les instructions.
  - Parse la réponse de Bedrock (JSON ou texte structuré).

- **`entity_detector.py`** :
  - `detect_entities_with_rules(text, canonical_scopes)` : détection d'entités par mots-clés (règles déterministes).
  - `merge_entities(bedrock_entities, rule_entities)` : fusionne les entités détectées par Bedrock et par règles.

- **`normalizer.py`** :
  - `normalize_item(raw_item, canonical_scopes, bedrock_client, client_language)` : orchestration de la normalisation d'un item.
  - Appelle Bedrock, applique les règles, fusionne les résultats.
  - Retourne un item normalisé (dictionnaire Python avec tous les champs requis).

**Principe clé** : hybride Bedrock + règles. Bedrock pour la compréhension linguistique, règles pour la validation et le complément.

---

### 2.6 `vectora_core/matching/` – Phase 2 (sans Bedrock)

**Rôle** : déterminer quels items normalisés correspondent aux `watch_domains` du client.

**Modules** :

- **`matcher.py`** :
  - `match_items_to_domains(normalized_items, watch_domains, canonical_scopes)` : pour chaque item, calcule les intersections avec les scopes de chaque domaine.
  - `compute_intersection(item_entities, scope_entities)` : calcule l'intersection entre deux ensembles (set Python).
  - Retourne les items annotés avec leurs `matched_domains`.

**Principe clé** : logique déterministe (intersections d'ensembles). Pas d'IA, pas de boîte noire.

---

### 2.7 `vectora_core/scoring/` – Phase 3 (sans Bedrock)

**Rôle** : attribuer un score numérique à chaque item pour prioriser les plus importants.

**Modules** :

- **`scorer.py`** :
  - `score_items(matched_items, scoring_rules, watch_domains)` : calcule le score de chaque item.
  - `compute_score(item, scoring_rules, domain_priority)` : formule de calcul du score (event_type, récence, priorité domaine, compétiteurs clés, molécules clés, type de source).
  - `rank_items_by_score(items)` : trie les items par score décroissant.

**Principe clé** : règles numériques transparentes. Pas d'IA, tout est expliquable et ajustable.

---

### 2.8 `vectora_core/newsletter/` – Phase 4 (avec Bedrock)

**Rôle** : assembler une newsletter structurée, lisible et "premium" avec l'aide de Bedrock.

**Modules** :

- **`bedrock_client.py`** :
  - `invoke_bedrock_for_editorial(model_id, prompt, region)` : appelle Bedrock pour générer le contenu éditorial (titre, intro, TL;DR, reformulations).
  - Construit le prompt avec les items sélectionnés + le contexte de la semaine + les attentes sur le ton/voice.
  - Parse la réponse de Bedrock (Markdown ou JSON parsable).

- **`assembler.py`** :
  - `assemble_newsletter(ranked_items, newsletter_layout, client_profile, bedrock_client)` : orchestration de l'assemblage de la newsletter.
  - Sélectionne les top N items par section.
  - Appelle Bedrock pour générer les composants éditoriaux (titre, intro, TL;DR, intros de sections, reformulations).
  - Retourne un dictionnaire Python avec tous les composants de la newsletter.

- **`formatter.py`** :
  - `format_as_markdown(newsletter_components)` : assemble les composants en un document Markdown cohérent.
  - Gère les titres, les bullet points, les liens, le formatage.

**Principe clé** : Bedrock pour la qualité éditoriale, règles pour la structure et l'assemblage.

---

### 2.9 `vectora_core/storage/` – Lecture/écriture S3

**Rôle** : abstraire les opérations S3 (lecture/écriture de fichiers JSON, YAML, Markdown).

**Modules** :

- **`s3_client.py`** :
  - `read_yaml_from_s3(bucket, key)` : lit un fichier YAML depuis S3 et le parse.
  - `read_json_from_s3(bucket, key)` : lit un fichier JSON depuis S3 et le parse.
  - `write_json_to_s3(bucket, key, data)` : écrit un dictionnaire Python en JSON dans S3.
  - `write_text_to_s3(bucket, key, text)` : écrit du texte (Markdown, etc.) dans S3.
  - `list_objects_in_prefix(bucket, prefix)` : liste les objets S3 sous un préfixe (pour collecter les items normalisés sur plusieurs jours).

**Principe clé** : couche d'abstraction pour faciliter les tests (mock S3) et la maintenance.

---

### 2.10 `vectora_core/utils/` – Utilitaires transverses

**Rôle** : fonctions utilitaires réutilisables dans tout le projet.

**Modules** :

- **`logger.py`** :
  - `setup_logger(log_level)` : configure le logger Python (niveau, format, etc.).
  - Utilisé par tous les modules pour tracer l'exécution.

- **`date_utils.py`** :
  - `parse_iso_date(date_str)` : parse une date ISO8601 en objet Python.
  - `compute_date_range(period_days, target_date)` : calcule une fenêtre temporelle (from_date, to_date) à partir d'un nombre de jours.
  - `format_date_for_s3_path(date)` : formate une date en `YYYY/MM/DD` pour les chemins S3.

**Principe clé** : éviter la duplication de code, centraliser les utilitaires.

---

## 3. Fonctions publiques principales de `vectora_core/`

Voici les fonctions de haut niveau que les handlers Lambda appelleront :

### Pour `vectora-inbox-ingest-normalize`

- **`run_ingest_normalize_for_client(client_id, sources=None, period_days=None, from_date=None, to_date=None, env_vars=None)`**
  - Charge la config client + canonical.
  - Résout les bouquets de sources.
  - Pour chaque source : ingestion (Phase 1A) + normalisation (Phase 1B).
  - Écrit les items normalisés dans S3 (`normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`).
  - Optionnellement écrit les items bruts dans S3 (`raw/<client_id>/<source_key>/<YYYY>/<MM>/<DD>/raw.json`).
  - Retourne un dictionnaire avec les statistiques d'exécution (nombre d'items ingérés, normalisés, filtrés, etc.).

### Pour `vectora-inbox-engine`

- **`run_engine_for_client(client_id, period_days=None, from_date=None, to_date=None, target_date=None, env_vars=None)`**
  - Charge la config client + canonical.
  - Collecte les items normalisés depuis S3 (sur la fenêtre temporelle).
  - Matching (Phase 2) : détermine les items pertinents pour chaque `watch_domain`.
  - Scoring (Phase 3) : calcule les scores et trie les items.
  - Assemblage de la newsletter (Phase 4) : appelle Bedrock pour générer le contenu éditorial, assemble le Markdown.
  - Écrit la newsletter dans S3 (`newsletters/<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`).
  - Retourne un dictionnaire avec les statistiques d'exécution (nombre d'items analysés, matchés, sélectionnés, etc.).

---

## 4. Mapping avec les contrats métier

### Contrat `vectora-inbox-ingest-normalize`

- **Phase 1A (Ingestion)** → `vectora_core/ingestion/`
- **Phase 1B (Normalisation)** → `vectora_core/normalization/`
- **Résolution des bouquets** → `vectora_core/config/resolver.py`
- **Chargement des scopes canonical** → `vectora_core/config/loader.py`
- **Écriture S3** → `vectora_core/storage/s3_client.py`

### Contrat `vectora-inbox-engine`

- **Phase 2 (Matching)** → `vectora_core/matching/`
- **Phase 3 (Scoring)** → `vectora_core/scoring/`
- **Phase 4 (Newsletter)** → `vectora_core/newsletter/`
- **Chargement des items normalisés** → `vectora_core/storage/s3_client.py`
- **Chargement des configs** → `vectora_core/config/loader.py`

---

## 5. Handlers AWS Lambda (strings pour S1-runtime)

Les handlers AWS Lambda à référencer dans le template CloudFormation `s1-runtime.yaml` :

- **Pour `vectora-inbox-ingest-normalize`** :
  - Handler : `lambdas.ingest_normalize.handler.lambda_handler`
  - Package : `src/` zippé avec toutes les dépendances.

- **Pour `vectora-inbox-engine`** :
  - Handler : `lambdas.engine.handler.lambda_handler`
  - Package : `src/` zippé avec toutes les dépendances.

**Important** : les deux Lambdas partagent le même code source (`vectora_core/`), seuls les handlers diffèrent.

---

## 6. Pourquoi cette architecture ?

### 6.1 Simplicité pour un solo founder

- **Pas de sur-ingénierie** : pas de frameworks complexes (FastAPI, Flask, etc.), pas de microservices, pas de Step Functions.
- **Code Python standard** : facile à lire, à déboguer, à tester.
- **Séparation claire** : handlers minces (AWS) + bibliothèque métier (testable).

### 6.2 Respect des contrats métier

- **Chaque phase du workflow a son module** : ingestion, normalisation, matching, scoring, newsletter.
- **Les responsabilités sont claires** : pas de mélange entre "plomberie AWS" et "logique métier".
- **Les contrats sont respectés** : les fonctions publiques (`run_ingest_normalize_for_client`, `run_engine_for_client`) correspondent exactement aux contrats des Lambdas.

### 6.3 Évite le hardcoding

- **Tout est piloté par les configurations** : canonical + client.
- **Les scopes sont chargés dynamiquement** : via les clés référencées dans les configs.
- **Les bouquets sont résolus dynamiquement** : via le catalogue de sources.
- **Pas de logique client-spécifique dans le code** : tout est dans les configs YAML.

### 6.4 Facilite l'ajout de nouvelles verticales

- **Pour ajouter une nouvelle verticale** (ex : oncologie, thérapie génique) :
  1. Ajouter de nouvelles clés dans les fichiers canonical (ex : `oncology_companies_global`).
  2. Créer une nouvelle config client référençant ces clés.
  3. **Aucun changement de code nécessaire** : les Lambdas chargent simplement les nouvelles listes via les clés.

- **Le code est agnostique de la verticale** : il manipule des listes identifiées par leurs clés, sans "savoir" si c'est LAI, oncologie, ou autre chose.

---

## 7. Dépendances Python (`requirements.txt`)

Voici les dépendances minimales pour le MVP :

```text
boto3>=1.34.0          # SDK AWS (S3, Bedrock, SSM)
pyyaml>=6.0            # Parsing YAML (configs)
requests>=2.31.0       # Appels HTTP (RSS, APIs)
feedparser>=6.0.10     # Parsing RSS/Atom
python-dateutil>=2.8.2 # Manipulation de dates
```

**Pas de dépendances lourdes** : pas de pandas, pas de numpy, pas de frameworks web. Juste le strict nécessaire.

---

## 8. Résumé : comment cette architecture répond aux besoins

| Besoin | Comment l'architecture y répond |
|--------|--------------------------------|
| **Simplicité** | Handlers minces + bibliothèque métier claire, pas de sur-ingénierie |
| **Respect des contrats** | Chaque phase du workflow a son module dédié |
| **Pas de hardcoding** | Tout piloté par les configs (canonical + client) |
| **Testabilité** | `vectora_core/` testable unitairement (sans simuler Lambda) |
| **Réutilisabilité** | `vectora_core/` utilisable dans d'autres contextes (CLI, notebooks) |
| **Extensibilité** | Ajout de nouvelles verticales sans changer le code (juste les configs) |
| **Maintenabilité** | Séparation claire des responsabilités, code Python standard |

---

**Fin de la proposition d'architecture `src/`.**

Dans le prochain prompt, tu pourras me demander de créer les fichiers et les squelettes de code correspondants.
