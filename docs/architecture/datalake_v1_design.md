# Vectora Inbox — Design du Datalake V1

**Version** : 1.3
**Date** : 2026-04-24
**Auteurs** : Frank (produit) + Claude (architecte)
**Statut** : à valider par Frank avant Phase 2

Ce document consolide toutes les décisions architecturales prises pendant la Phase 1 d'audit. Il est la référence unique pour la Phase 2 (ménage + implémentation). Aucune ligne de code n'est écrite tant que ce document n'est pas validé.

**Optimisations différées** : voir `docs/architecture/future_optimizations.md`.

**Changements V1.2** : ajout du module `sources/` (Discovery + Validation + Promotion) — workflow d'onboarding de source distinct du runtime.

**Changements V1.3** : §13 (plan de transition) restructuré par paliers de fonctionnalité (Niveaux 1 Fondations / 2 Cœur / 3 Maquillage) plutôt que par phases techniques séquentielles. Chaque niveau produit quelque chose d'utilisable et testable.

**Note V1.3.1** : la **Phase 2.0** (hygiène complète du repo : Git + structure) a été détaillée dans un document dédié `docs/architecture/phase2.0_repo_structure.md` (V2.0 du 2026-04-25). Cette Phase 2.0 inclut désormais le volet Git (tag legacy, archive branch, merge des docs Phase 1, suppression des vieilles branches) en plus de la réorganisation des dossiers. À exécuter depuis Claude Code dans VS Code, avant Phase 2.1.bis.

---

## 1. Vision et principes

### 1.1 Objet

Vectora Inbox V1 est **un moteur d'alimentation d'un datalake thématique de veille compétitive**, à l'échelle locale (PC de Frank) pour commencer, conçu pour pouvoir être porté sur AWS plus tard sans réécriture majeure.

Le datalake est **l'artefact produit**, unique, versionné. Tout le reste (newsletters, rapports, RAG) est un consommateur en aval qui se sert dans le datalake.

### 1.2 Ce que le moteur fait

**Au runtime (cycle d'ingestion répété)** :
- Ingère en continu (ou à la demande) des sources **préalablement validées**
- Applique des filtres métier (période, scopes, exclusions) pilotés par `canonical/`
- Stocke les items bruts dans `datalake_v1/raw/`
- Détecte les nouveaux items à normaliser via une gap analysis `raw \ curated`
- Appelle un LLM (Anthropic Claude via API directe) pour normaliser chaque item : extraction d'entités, classification d'événement, dates, résumé
- Stocke les items normalisés dans `datalake_v1/curated/`
- Maintient en continu stats, health checks, et rapports de pilotage

**À l'onboarding (cycle distinct, manuel, occasionnel)** :
- Investigue une source candidate via Discovery (connectivité, RSS, sections news, articles)
- Génère une recommandation de configuration technique
- Valide la configuration via tests d'extraction (titres, dates, qualité contenu)
- Promeut la source de "candidate" à "validated" dans canonical/

Ces deux cycles sont **indépendants** : on n'onboard pas une source à chaque run d'ingestion. Une source validée peut tourner en runtime pendant des mois sans intervention.

### 1.3 Ce que le moteur NE fait PAS

- Pas de sélection éditoriale, pas de scoring newsletter, pas de rédaction
- Pas de matching vers des "watch_domains" de client (concept legacy abandonné)
- Pas de livraison de newsletter, pas d'envoi d'email
- Pas de RAG

Ces fonctions relèvent de **consommateurs du datalake**, implémentés séparément, sur une base de code distincte.

### 1.4 Principes de conception

1. **Local-first** : tout tourne sur le PC de Frank. Pas de dépendance AWS. Seul appel externe : l'API Anthropic (clé API utilisateur).
2. **Config-driven** : toute la logique métier (sources, filtres, scopes, écosystèmes) vit dans `canonical/` ou `config/clients/`. Le code est générique et agnostique du vertical.
3. **Datalake unique à tags multivalués** : un seul stockage plat, les écosystèmes sont des dimensions de filtrage.
4. **Item_id canonique comme liant** : identifiant déterministe dérivé de l'URL canonicalisée, stable dans le temps, identique pour raw et curated.
5. **Append-only sur JSONL** : les items ne sont jamais réécrits en place. Robuste, diffable, reprise facile. (Une exception : enrichissement des tags d'écosystème lors d'une ré-ingestion, voir §5.)
6. **Indexes dérivés et reconstructibles** : si un index est corrompu, un script le rebuild en full scan. Jamais de panique.
7. **Cycle de vie explicite** : un item passe de `raw` à `pending_curation` à `curated` (ou `failed`). Machine d'état claire.
8. **Observable par construction** : stats, health checks et gap reports sont des artefacts du datalake lui-même, pas un dashboard externe.
9. **Atomicité par source** : l'unité d'ingestion est la source. Un orchestrateur en boucle gère le client. Aucun run > 5 minutes par unité atomique.
10. **Cache agressif** : tout ce qui a déjà été vu (rejeté ou ingéré) est mémorisé pour éviter le re-processing. Cache simple en MVP, invalidation manuelle.

---

## 2. Vocabulaire (glossaire canonique)

| Terme | Définition |
|---|---|
| **Item** | Une unité de contenu ingérée (article, press release, FDA label, etc.) |
| **Source** | Un flux configurable d'items (ex : RSS Medincell, page FDA DailyMed) — identifiée par `source_key` |
| **Bouquet** | Un ensemble de sources, nommé, défini dans `canonical/sources/source_catalog.yaml` |
| **Écosystème** | Une dimension thématique/business — ex : `tech_lai_ecosystem`, `tech_sirna_ecosystem`. Un item porte un ou plusieurs tags d'écosystème. |
| **`ecosystem_id`** | Identifiant string d'un écosystème (ex: `"tech_lai_ecosystem"`). Singulier, scalaire. |
| **`ecosystems`** | Liste d'`ecosystem_id`. Utilisée pour le multi-tagging d'un item ou pour déclarer plusieurs écosystèmes cibles dans un client_config. |
| **Client** | Un utilisateur de la plateforme, défini dans `config/clients/{client_id}.yaml`. Il choisit ses bouquets, ses écosystèmes, sa période, ses paramètres. |
| **Raw** | Item tel qu'ingéré, avec son contenu brut et ses métadonnées de source, non enrichi. |
| **Curated** | Item enrichi par le LLM : entités extraites, event_type, dates normalisées, résumé. Stocké en parallèle du raw, avec les mêmes champs + enrichissements. |
| **`item_id`** | Identifiant déterministe : `{source_key}__{sha256(canonical_url)[:16]}` |
| **Canonical URL** | URL mise en forme standard (lowercase host, sans fragment, sans params de tracking). Règles dans `canonical/parsing/url_canonicalization.yaml`. |
| **Run** | Une exécution du pipeline (ingestion ou normalisation), tracée par `run_id`, avec un manifest. |
| **Source-run** | Une exécution d'ingestion sur **une seule source**. Unité atomique. |
| **Client-run** | Une exécution d'orchestrateur qui boucle sur toutes les sources d'un client. Compose plusieurs source-runs. |
| **Gap** | L'ensemble des `item_id` présents dans raw mais absents de curated. |
| **URL cache** | Registre par écosystème de toutes les URLs déjà vues, avec leur statut (`ingested` ou `rejected`). Permet de skipper le fetch et le parse. |
| **Source candidate** | Source identifiée mais non encore validée. Listée dans `canonical/sources/source_candidates.yaml`. Jamais ingérée par le moteur runtime. |
| **Source validated** | Source qui a passé le cycle Discovery + Validation. Listée dans `canonical/sources/source_catalog.yaml` et `canonical/ingestion/source_configs.yaml` avec `validated: true`. Ingérée par le runtime. |
| **Discovery** | Étape d'onboarding : investiguer automatiquement une source candidate (connectivité, RSS feeds, sections news, articles échantillon) pour proposer une configuration d'ingestion. Sortie : config technique recommandée + score de confiance. |
| **Validation** | Étape d'onboarding : tester la configuration générée par Discovery (extraction articles, titres, dates, qualité contenu). Sortie : score final + statut PASSED/FAILED, config affinée. |
| **Promotion** | Étape d'onboarding : si validation PASSED, copier la config validée dans `canonical/ingestion/source_configs.yaml` (`validated: true`) et ajouter la source au `source_catalog.yaml`. La source devient ingérable au runtime. |

**Vocabulaire abandonné** : `domain`, `watch_domain`, `watch_domains`, `domain_id`. Tout ce qui désignait l'ancien concept "domain" devient `ecosystem*`. Voir §13.2 (audit de renommage).

---

## 3. Structure physique du datalake

### 3.1 Arborescence

```
data/
└── datalake_v1/
    ├── raw/
    │   ├── items/
    │   │   └── YYYY/MM/items.jsonl
    │   └── indexes/
    │       ├── by_item_id.json
    │       ├── by_source_key.json
    │       ├── by_source_type.json
    │       ├── by_ecosystem.json
    │       ├── by_company_id.json
    │       ├── by_date.json
    │       └── _index_meta.json
    ├── curated/
    │   ├── items/
    │   │   └── YYYY/MM/items.jsonl
    │   ├── indexes/
    │   │   ├── by_item_id.json
    │   │   ├── by_source_key.json
    │   │   ├── by_source_type.json
    │   │   ├── by_ecosystem.json
    │   │   ├── by_event_type.json
    │   │   ├── by_company_id.json
    │   │   ├── by_molecule.json
    │   │   ├── by_technology.json
    │   │   ├── by_trademark.json
    │   │   ├── by_date.json
    │   │   └── _index_meta.json
    │   └── curation_log.jsonl
    ├── _cache/
    │   └── url_cache_{ecosystem_id}.json     # ex: url_cache_tech_lai_ecosystem.json
    ├── stats/
    │   ├── health.json             # état opérationnel des sources (live)
    │   ├── stats_daily.jsonl       # snapshot quotidien append-only
    │   ├── gap_report.json         # items en attente / en échec de curation
    │   └── reports/
    │       └── YYYY-MM-DD_{raw|curated|sources}.md
    └── ingestion_runs/
        ├── runs/
        │   └── YYYY/MM/{run_id}.json
        └── indexes/
            ├── by_client.json
            ├── by_ecosystem.json
            └── by_date.json
```

### 3.2 Partition temporelle par mois de publication

Les items sont placés dans `YYYY/MM/items.jsonl` où `YYYY/MM` correspond au **`published_at` de l'item**, pas à la date d'ingestion. Raison : la plupart des requêtes sont des fenêtres de publication ("les 7 derniers jours", "le mois dernier"). La date d'ingestion reste stockée dans l'item (`ingested_at`).

Cas limite : un item sans `published_at` (rare, normalement filtré) est placé dans `UNKNOWN/items.jsonl`. On le traite manuellement.

### 3.3 Format d'un item raw (JSONL, une ligne par item)

```json
{
  "item_id": "press_corporate__medincell__a3f1c8d4e5b62a7f",
  "schema_version": "raw/1.0",
  "url": "https://www.medincell.com/degroof-petercam-initiates-medincells-coverage-with-a-buy-recommendation",
  "url_raw": "https://www.medincell.com/degroof-petercam-initiates-medincells-coverage-with-a-buy-recommendation/?utm_source=rss",
  "source_key": "press_corporate__medincell",
  "source_type": "press_corporate",
  "ecosystems": ["tech_lai_ecosystem"],
  "actor_type": "pure_lai",
  "company_id_at_source": "medincell",
  "title": "Degroof Petercam Initiates Medincell Buy Rating",
  "content": "Full extracted content...",
  "content_hash": "sha256:7a3c4d...",
  "published_at": "2026-04-22",
  "ingested_at": "2026-04-23T16:35:19Z",
  "ingestion_run_id": "mvp_test_30days__20260423_123305_9875b3b1",
  "raw_metadata": {
    "parser": "rss_full",
    "rss_guid": "...",
    "fetch_status": 200,
    "fetch_ms": 840
  }
}
```

**Notes** :
- `url` est canonicalisée ; `url_raw` garde la forme brute pour audit.
- `ecosystems` est une **liste** (la porte ouverte au multi-tagging — voir §5).
- `company_id_at_source` est déduit du mapping `canonical/sources/source_catalog.yaml` (pour les sources corporate). Pour les sources sector, il est `null` au raw — c'est au curated d'extraire les companies mentionnées.
- `schema_version` permet de faire évoluer le format en gardant les anciens items lisibles.

### 3.4 Format d'un item curated

Un item curated contient **tous les champs du raw** plus :

```json
{
  // ... tous les champs raw ...
  "schema_version": "curated/1.0",
  "curation": {
    "status": "curated",
    "curated_at": "2026-04-23T17:02:11Z",
    "curation_run_id": "curation__20260423_170141_ab12cd34",
    "llm_provider": "anthropic",
    "llm_model": "claude-sonnet-4-x",
    "prompt_version": "generic_normalization@2.0",
    "cost_usd": 0.0042,
    "latency_ms": 2850,
    "attempts": 1
  },
  "summary": "Detailed factual summary (10-15 lines)...",
  "event": {
    "type": "partnership",
    "date_extracted": "2026-04-22",
    "date_extracted_confidence": 0.95,
    "date_published_llm": "2026-04-22"
  },
  "entities": {
    "companies": [
      {"name": "Medincell", "role": "subject", "canonical_id": "medincell"},
      {"name": "Degroof Petercam", "role": "mentioned"}
    ],
    "molecules": [],
    "technologies": ["Long-Acting Injectable"],
    "trademarks": []
  }
}
```

**Règles** :
- Le curated est **self-contained** : un consommateur qui a un item curated n'a jamais besoin de requêter le raw.
- `curation.status` est l'une de : `pending | curated | failed`.
- Les `canonical_id` pour les companies sont résolus post-LLM via `canonical/scopes/company_scopes.yaml` (matching fuzzy). Si pas de match, `canonical_id` est omis.

---

## 4. Indexes

### 4.1 Principes

- Tous les indexes sont des **fichiers JSON indépendants**, lisibles à l'œil, rebuildables.
- Chaque index est un mapping `{clé → [item_ids]}` sauf `by_item_id` qui est `{item_id → {year, month, line_number}}`.
- Ils sont mis à jour **incrémentalement** à chaque insert.
- Un script `rebuild_indexes.py` les reconstruit en full scan à la demande (maintenance ou après migration).
- `_index_meta.json` trace la version de chaque index et la date du dernier rebuild.

### 4.2 Indexes du raw

| Index | Clé | Usage principal |
|---|---|---|
| `by_item_id` | item_id | Lookup direct, gap analysis raw/curated |
| `by_source_key` | source_key | Filtre par source précise (ex: tous les items Medincell) |
| `by_source_type` | press_corporate / press_sector / scientific / regulatory | Filtre par nature de source |
| `by_ecosystem` | tech_lai_ecosystem / ... | Filtre par thème métier |
| `by_company_id` | company_id (quand dispo au source) | Focus entreprise (limité aux sources corporate) |
| `by_date` | YYYY-MM-DD | Fenêtre temporelle |

### 4.3 Indexes additionnels du curated

| Index | Clé | Usage principal |
|---|---|---|
| `by_event_type` | partnership / regulatory / clinical_update / business / corporate_move / other | Rapports thématiques, filtre event |
| `by_company_id` | canonical_id (issu des entities extraites par le LLM) | Focus entreprise étendu à toutes les mentions |
| `by_molecule` | molecule canonical name | Focus molécule |
| `by_technology` | technology label | Focus technologie |
| `by_trademark` | trademark | Focus trademark |

### 4.4 Exemple de requête composée

"Tous les items curés des 30 derniers jours, de type `partnership`, mentionnant Medincell, dans l'écosystème LAI" :

```
candidates = by_event_type["partnership"]
           ∩ by_company_id["medincell"]
           ∩ by_ecosystem["tech_lai_ecosystem"]
candidates = filter(candidates, date >= today - 30d)  # via by_date
items = load(candidates)  # via by_item_id → file + line
```

Complexité : lookup × 3 + intersection d'ensembles + chargement ponctuel. Rapide, même sur 100k items.

---

## 5. Règles de tagging d'écosystème

### 5.1 Attribution (Option A, MVP)

Quand un item est ingéré via un bouquet, il reçoit **le(s) tag(s) d'écosystème associé(s) au bouquet**. Le mapping bouquet → écosystème est déclaré dans `canonical/sources/source_catalog.yaml`.

Exemple :
- Bouquet `lai_full_mvp` → `ecosystems: [tech_lai_ecosystem]`
- Bouquet `regulatory_lai` → `ecosystems: [tech_lai_ecosystem, regulatory_fda_ecosystem]` (multi-tag natif)

### 5.2 Enrichissement à l'ingestion répétée

Si un item est re-ingéré via un autre bouquet (item_id identique grâce à la canonicalisation URL), ses tags d'écosystème sont **fusionnés** (union sans doublon). Le raw est mis à jour en place sur la ligne JSONL concernée — l'index `by_item_id` donne la localisation précise (year, month, line_number).

C'est la seule exception au principe append-only, et elle est ciblée et déterministe.

### 5.3 Coordination cache + datalake pour le multi-tagging

Quand l'ingestion rencontre une URL :

1. Lookup dans le cache de l'écosystème courant
2. Si `status: ingested` → l'item existe déjà dans le datalake
   - On lookup `by_item_id` dans `raw/`
   - Si l'écosystème courant est déjà dans `item.ecosystems` → skip total
   - Sinon → on ajoute le tag à l'item existant (mise à jour ciblée), pas de fetch
3. Si `status: rejected` → skip total, on incrémente `scan_count` du cache
4. Si absent du cache → flux normal (fetch, parse, filter, decide)

Voir §7 pour le détail du cache.

### 5.4 Futur (note hors scope MVP)

Voir `future_optimizations.md` §2 — proposition que le LLM suggère des écosystèmes additionnels lors de la normalisation.

---

## 6. Pipeline logique

### 6.1 Trois étapes séquentielles, lançables indépendamment

```
┌───────────────┐    ┌─────────────────┐    ┌───────────────────┐
│   INGEST      │    │   DETECT         │    │   NORMALIZE        │
│ sources → raw │ →  │ raw \ curated    │ →  │ LLM → curated      │
│  append-only  │    │ → pending queue  │    │ pending → curated  │
└───────────────┘    └─────────────────┘    └───────────────────┘
```

Un script d'orchestration `run_pipeline.py` les enchaîne :

```
python run_pipeline.py --client mvp_test_30days
```

Mais chaque étape peut être lancée indépendamment.

### 6.2 Étape INGEST — atomique par source, orchestrée par client

#### Architecture en deux niveaux

```
                        ┌──────────────────────────────────────┐
                        │   ClientOrchestrator                  │
                        │   (run_ingest.py --client X)          │
                        │                                       │
                        │   1. load client_config               │
                        │   2. resolve bouquets → sources       │
                        │   3. for each source: ────┐           │
                        │       call ingest_source()│           │
                        │   4. write client-run manifest        │
                        │   5. update health.json               │
                        └────────────────────────────┼──────────┘
                                                     ▼
                                          ┌──────────────────────────┐
                                          │  ingest_source()          │
                                          │  (atomique, 30s–5min)     │
                                          │                           │
                                          │  fetch → parse            │
                                          │  → check cache            │
                                          │  → filter (canonical+     │
                                          │     client)               │
                                          │  → write raw + indexes    │
                                          │  → update url_cache       │
                                          │  → return source-manifest │
                                          └──────────────────────────┘
```

#### Détail d'un source-run (ingest_source)

1. Charger les configs nécessaires (canonical + client) — déjà chargées par l'orchestrateur, passées en argument
2. Fetch RSS/HTML de la source (avec timeout)
3. Parse → liste d'items candidats avec URL et titre/résumé
4. Pour chaque candidat :
   a. Canonicaliser l'URL → calculer `item_id`
   b. **Lookup cache écosystème** (voir §7)
      - Si `ingested` et tag écosystème déjà présent → skip total
      - Si `ingested` et tag écosystème manquant → ajouter le tag à l'item existant
      - Si `rejected` → skip total
      - Si absent → continuer
   c. Pour les items qui doivent être traités :
      - Si profil RSS avec `prefetch_filter` → check titre+résumé contre les filtres canonical
        - Si rejet : enregistrer dans cache `{status: rejected, stage: prefetch_filter}`, skip
      - Sinon ou si prefetch passé : fetcher l'article complet
      - Extraction (titre, contenu, dates)
      - Filtres canonical (LAI keywords, exclusions, period_filter)
      - Filtres client (`content_filters`, `source_limits`)
      - Si rejet à n'importe quelle étape : enregistrer dans cache, skip
      - Si accepté : écrire dans `raw/items/YYYY/MM/items.jsonl`, mettre à jour les 6 indexes raw, enregistrer dans cache `{status: ingested, item_id}`
5. Retourner un `source_manifest` (statut, items ajoutés, durées, erreurs)

#### Détail d'un client-run (orchestrator)

1. Charger `config/clients/{client_id}.yaml`
2. Résoudre les bouquets via `canonical/sources/source_catalog.yaml` → liste de sources avec écosystème associé
3. Pour chaque source dans la liste :
   - Logger `[i/N] {source_key} ...`
   - Appeler `ingest_source(source_key, client_config, ...)`
   - Capturer le `source_manifest`
   - Logger le résultat (`✓ N nouveaux`, `✗ FAILED reason`, `⊝ skipped`)
   - **Continuer** même en cas d'échec (sauf flag `--fail-fast`)
4. Écrire le `client_run_manifest` dans `ingestion_runs/runs/YYYY/MM/{run_id}.json`
5. Mettre à jour `stats/health.json` (statut de chaque source)

#### Commandes CLI prévues

```bash
# Run complet pour un client
python run_ingest.py --client mvp_test_30days

# Reprendre après interruption (skip les sources déjà OK dans ce run)
python run_ingest.py --client mvp_test_30days --resume

# Re-tenter uniquement les sources qui ont échoué la dernière fois
python run_ingest.py --client mvp_test_30days --retry-failed

# Forcer une seule source (debug ciblé)
python run_ingest.py --client mvp_test_30days --source press_corporate__nanexa

# Forcer un seul bouquet
python run_ingest.py --client mvp_test_30days --bouquet lai_full_mvp

# Backfill long sans cache (pour récupérer des items précédemment rejetés)
python run_ingest.py --client mvp_test_30days --period-days 365 --no-cache

# Mode debug strict : s'arrêter au premier échec
python run_ingest.py --client mvp_test_30days --fail-fast

# Reconstruire le cache from scratch
python run_ingest.py --client mvp_test_30days --rebuild-cache

# Parallélisation (futur, voir future_optimizations.md §4)
python run_ingest.py --client mvp_test_30days --parallel 3
```

#### Sortie temps réel typique

```
[1/8] press_corporate__medincell      ✓ 2 nouveaux items (43s)
[2/8] press_corporate__camurus        ✓ 1 nouvel item (28s)
[3/8] press_corporate__nanexa         ✗ FAILED — RSS 503 (12s)
[4/8] press_corporate__pfizer         ⊝ skipped (cache 100% hit, 3s)
[5/8] press_corporate__taiwan_lipo    ✓ 0 nouveau (51s)
[6/8] press_sector__fiercepharma      ✓ 4 nouveaux items (3m12s)
[7/8] press_sector__endpoints_news    ✓ 2 nouveaux items (1m43s)
[8/8] press_corporate__delsitech      ✓ 1 nouvel item (37s)

Run completed: 7/8 sources OK, 1 failed.
Total: 10 new items in raw, 7m49s.
Failed sources to retry: press_corporate__nanexa
```

### 6.3 Étape DETECT (en détail)

```
pending = set(raw.by_item_id.keys()) − set(curated.by_item_id.keys()) − failed_items
```

Sortie : `stats/gap_report.json` mis à jour avec la liste des `item_ids` à curer.

### 6.4 Étape NORMALIZE (en détail)

Pour chaque `item_id` de la queue `pending` :

1. Charger l'item raw depuis `by_item_id` (O(1))
2. Charger le prompt `canonical/prompts/normalization/generic_normalization.yaml`
3. Construire la requête Anthropic (modèle choisi en config, max_tokens, temperature=0.1)
4. Appel API avec retry niveau 1 (3× backoff exponentiel)
5. Parser la réponse JSON ; valider les entités contre le contenu (anti-hallucination)
6. Résoudre les `canonical_id` des companies via `canonical/scopes/company_scopes.yaml`
7. Construire l'item curated (raw + curation + event + entities + summary)
8. Append à `curated/items/YYYY/MM/items.jsonl`, update indexes
9. Append une ligne à `curated/curation_log.jsonl`
10. Si échec : incrémenter `attempts` dans gap_report ; si `attempts >= 5`, marquer `failed`

### 6.5 Workflow d'onboarding de source (hors runtime)

L'onboarding d'une source suit un cycle dédié, **distinct du pipeline runtime**, lancé manuellement quand on veut ajouter une nouvelle source.

#### Trois étapes séquentielles

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   DISCOVERY       │    │   VALIDATION       │    │   PROMOTION       │
│                   │    │                    │    │                   │
│ candidate URL →   │ →  │ test extraction →  │ →  │ if PASSED:        │
│ → recommended     │    │ refined config +   │    │ → write to        │
│   config + score  │    │ PASSED/FAILED       │    │   source_configs  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
        ↑                          ↑                          ↑
source_candidates.yaml    output: validation report    source_catalog.yaml
```

#### Détail Discovery

Inputs :
- `source_key` (ex: `press_corporate__taiwan_liposome`)
- L'entrée correspondante dans `canonical/sources/source_candidates.yaml`

Actions :
1. Test connectivité de la homepage (status code, SSL, redirections)
2. Recherche de flux RSS (patterns courants : `/rss`, `/feed`, `/atom.xml`, etc.)
3. Recherche de sections news (patterns : `/news/`, `/press-releases/`, `/media/`, etc.)
4. Analyse d'articles échantillon (extraction de dates, titres, contenu)
5. Génération d'une config technique recommandée :
   - `news_url`
   - `ingestion_profile` (rss_full / rss_with_fetch / html_generic / html_pdf)
   - `listing_selectors` (CSS pour HTML)
   - `date_selectors` (CSS ou stratégie text_extraction)
   - Notes d'extraction
6. Score de confiance (0-100)

Sortie : rapport JSON dans `output/discovery/{source_key}_{timestamp}.json` + log lisible.

#### Détail Validation

Inputs :
- La config recommandée par Discovery (ou existante dans `source_configs.yaml`)

Actions :
1. Test extraction d'articles (avec la config) — le moteur doit trouver ≥ N articles
2. Test extraction des titres (qualité, non-vides, longueur cohérente)
3. Test extraction des dates (parseable, plausible, distribution sur la période)
4. Test qualité du contenu (longueur min, pas de placeholders type "Cookie consent")
5. Affinage de la config si nécessaire (ex: élargir un selector trop strict)
6. Score final + statut **PASSED** (≥70) ou **FAILED**

Sortie : rapport JSON dans `output/validation/{source_key}_{timestamp}.json` + log.

#### Détail Promotion

Si validation PASSED :
1. Écrire la config validée dans `canonical/ingestion/source_configs.yaml` :
   - `validated: true`
   - `validated_date: YYYY-MM-DD`
   - Tous les selectors et notes de discovery+validation
2. Ajouter la source dans `canonical/sources/source_catalog.yaml` (registre métier)
3. Mettre à jour `canonical/sources/source_candidates.yaml` :
   - `status: validated` (ou retirer l'entrée si on ne garde que les candidates en attente)

La source devient alors ingérable par tout client qui inclut le bouquet correspondant.

#### Maintenance : revalidation périodique

Une source validée aujourd'hui peut **devenir invalide demain** : changement de structure HTML du site, migration vers un nouveau CMS, changement d'URL pattern. Le script `revalidate_all.py` re-tourne la validation sur toutes les sources actives, à tourner périodiquement (mensuel ou trimestriel) ou à la demande.

Sortie : rapport listant les sources qui sont passées de PASSED à FAILED depuis la dernière validation. Action manuelle : re-discovery + re-validation sur les sources concernées.

#### Commandes CLI

```bash
# Discovery seule
python discover_source.py --source press_corporate__taiwan_liposome

# Validation seule (utilise la config existante ou celle de la dernière discovery)
python validate_source.py --source press_corporate__taiwan_liposome

# Discovery + Validation enchaînées
python validate_source.py --source press_corporate__taiwan_liposome --with-discovery

# Promotion (manuelle, après validation PASSED)
python promote_source.py --source press_corporate__taiwan_liposome

# Cycle complet automatisé (discovery → validation → si PASSED, promotion)
python onboard_source.py --source press_corporate__taiwan_liposome --auto-promote

# Lister le backlog des candidates
python list_candidates.py [--tag lai] [--priority high]

# Re-validation périodique de toutes les sources actives
python revalidate_all.py [--ecosystem tech_lai_ecosystem]
```

---

## 7. Stratégie de cache d'URL

### 7.1 Rôle

Le cache évite le **re-processing** des URLs déjà vues, qu'elles aient été ingérées ou rejetées. C'est l'optimisation la plus impactante du moteur d'ingestion : Frank a mesuré ~70% d'économie de temps sur ses runs MVP. Sans cache, un scan de 8 sources sur 200 jours peut prendre 5 heures ; avec, ça tombe à quelques minutes.

### 7.2 Granularité : par écosystème

Un fichier de cache par écosystème :

```
data/datalake_v1/_cache/url_cache_{ecosystem_id}.json
```

Pourquoi par écosystème : les filtres canoniques (LAI keywords, exclusions) sont définis au niveau de l'écosystème, donc les rejets sont valables pour tout client qui vise cet écosystème.

### 7.3 Structure d'une entrée

```json
{
  "url_canonical": "https://www.medincell.com/some-article",
  "status": "ingested",                    // "ingested" | "rejected"
  "item_id": "press_corporate__medincell__a3f1c8d4e5b62a7f",
  "rejection_reason": null,                // si status=rejected : "no_lai_signal" / "out_of_period" / "exclusion_match" / etc.
  "rejection_stage": null,                 // "prefetch_filter" / "post_extraction_filter"
  "source_key": "press_corporate__medincell",
  "first_seen": "2026-04-23T10:14:00Z",
  "last_seen": "2026-04-24T08:45:00Z",
  "scan_count": 12
}
```

### 7.4 Comportement à l'ingestion (les trois cas)

Quand le moteur traite une URL candidate :

**Cas 1 — URL absente du cache**
Flux normal : fetch → parse → filtres → décision → écriture (datalake si accepté + cache dans tous les cas).

**Cas 2 — URL en cache, `status: rejected`**
- Skip immédiat (pas de fetch, pas de parse)
- Update : `last_seen`, `scan_count++`

**Cas 3 — URL en cache, `status: ingested`**
- Lookup `by_item_id` dans le datalake raw
- Si `ecosystem_id` courant ∈ `item.ecosystems` → skip total
- Sinon → ajouter le tag écosystème à l'item raw existant (mise à jour ciblée sur la ligne JSONL via `by_item_id`), update `last_seen` du cache. **Pas de fetch.**

### 7.5 Ce qui n'est PAS dans le cache

- **Rejets dépendants du client** (période, `content_filters.min_word_count`) : ces critères changent par client/run, ils sont peu coûteux à re-tester (les filtres post-extraction tournent en mémoire après le fetch).
- **Erreurs transitoires de fetch** (timeout, 5xx) : on retentera, surtout pas de cache de l'erreur.

Tout le reste va dans le cache, même les rejets `out_of_period` au sens canonique (period_filter de canonical, pas du client).

### 7.6 Activation et contrôle

Dans le client_config :

```yaml
ingestion:
  use_url_cache: true     # défaut. false pour désactiver complètement.
```

En ligne de commande :

```bash
--no-cache              # ignore le cache pour ce run uniquement
--rebuild-cache         # vide le cache de l'écosystème et le reconstruit
```

### 7.7 Invalidation : simple en MVP

**Règle MVP** : pas d'invalidation automatique. Si tu modifies les filtres canoniques (`technology_scopes.yaml`, `exclusion_scopes.yaml`, `filter_rules.yaml`), tu lances :

```bash
python run_ingest.py --client X --rebuild-cache
```

C'est explicite, simple, et ça force à se rappeler que le cache reflète une version précise des filtres.

**Évolution future** : invalidation automatique par signature de filtre. Décrite dans `future_optimizations.md` §1, à implémenter quand le besoin sera réel.

### 7.8 Maintenance du cache

Scripts utilitaires :

```bash
python validate_cache.py --ecosystem tech_lai_ecosystem      # vérifie cohérence cache ↔ datalake
python rebuild_cache.py --ecosystem tech_lai_ecosystem       # rebuild from scratch (full scan datalake)
python cache_stats.py --ecosystem tech_lai_ecosystem         # taille, distribution ingested/rejected, top sources
```

---

## 8. Gestion des erreurs et retry (LLM)

### 8.1 Niveau 1 — Retry immédiat intra-run

- 3 tentatives maximum par appel LLM
- Backoff exponentiel avec jitter : 0.5s, 1.0s, 2.0s (+ jitter aléatoire ≤ 0.1s)
- Cas retryable : `ThrottlingException`, codes HTTP 5xx, timeout réseau
- Cas non-retryable : erreur de validation du prompt, format de réponse invalide, `AuthenticationError`

### 8.2 Niveau 2 — Remise en queue inter-run

Si le niveau 1 échoue, l'item :
- Reste dans `pending_curation` (via gap analysis au prochain run)
- Son `attempts` est incrémenté
- Son `last_error` est stocké dans `gap_report.json`
- Sera re-tenté automatiquement au prochain `run_normalize.py`

### 8.3 Niveau 3 — Marquage `failed` après 5 tentatives

Quand `attempts >= 5` :
- L'item passe de `pending` à `failed`
- Il n'est plus re-tenté automatiquement
- Il apparaît dans `gap_report.failed_items` avec historique complet des erreurs
- Pour le remettre en traitement : commande explicite `python run_normalize.py --retry-failed [--item-id XXX | --all]`

### 8.4 Visibilité

- `stats/gap_report.json` contient toujours les compteurs `pending` / `failed` et la liste détaillée des `failed_items`
- Les rapports Markdown (`stats/reports/`) incluent une section "Items en échec à traiter"
- Pas de notification silencieuse : toute panne est visible au prochain coup d'œil au gap_report

---

## 9. Outils de maintenance et stats

### 9.1 `stats/health.json` — état live des sources

Un seul fichier, rafraîchi par chaque `run_ingest.py`. Structure :

```json
{
  "updated_at": "2026-04-24T09:00:00Z",
  "sources": {
    "press_corporate__medincell": {
      "status": "healthy",
      "last_run_at": "2026-04-24T08:45:00Z",
      "last_success_at": "2026-04-24T08:45:00Z",
      "consecutive_failures": 0,
      "items_last_7d": 2,
      "items_last_30d": 9,
      "avg_fetch_ms_last_10_runs": 1240,
      "last_error": null
    }
  }
}
```

Status : `healthy` / `degraded` / `down` / `disabled`.

### 9.2 `stats/stats_daily.jsonl` — série temporelle

Une ligne append-only par jour, générée par `update_daily_stats.py` (idempotent) :

```json
{"date":"2026-04-24","raw_total":523,"curated_total":498,"curated_coverage":0.952,"new_raw_today":14,"new_curated_today":12,"pending":23,"failed":2,"by_ecosystem":{"tech_lai_ecosystem":{"raw":523,"curated":498}},"by_source_type":{"press_corporate":420,"press_sector":103},"llm_cost_today_usd":0.14,"llm_cost_cumulative_usd":18.63}
```

### 9.3 `stats/gap_report.json` — queue de normalisation

```json
{
  "generated_at": "2026-04-24T09:00:00Z",
  "raw_count": 523,
  "curated_count": 498,
  "pending_curation": 23,
  "failed_curation": 2,
  "pending_items": ["item_id_1", "item_id_2", "..."],
  "failed_items": [
    {
      "item_id": "...",
      "attempts": 5,
      "first_attempt_at": "2026-04-20T10:12:00Z",
      "last_attempt_at": "2026-04-24T08:45:00Z",
      "errors_history": [
        {"at": "...", "type": "LLMTimeout", "message": "..."}
      ]
    }
  ]
}
```

### 9.4 Rapports Markdown à la demande

Générés par `generate_report.py --type {raw|curated|sources|full}` et stockés dans `stats/reports/YYYY-MM-DD_{type}.md`.

**`report_raw.md`** : total items, croissance sur 30j, top 10 sources, top 10 companies, date range, alertes (sources silencieuses depuis > 7j, doublons suspects).

**`report_curated.md`** : coverage, latence moyenne de curation, distribution event_types, top entités extraites, coût LLM cumulé, taux de succès.

**`report_sources.md`** : tableau détaillé par source (statut, dernière ingestion, items 7j/30j, erreurs récentes).

**`report_full.md`** : tout ça combiné, format "rapport hebdo".

### 9.5 Maintenance curative

Scripts utilitaires :

```bash
python rebuild_indexes.py [--raw|--curated|--all]
python recompute_stats.py
python validate_datalake.py             # vérifie cohérence JSONL ↔ indexes
python validate_cache.py                # vérifie cohérence cache ↔ datalake
python rebuild_cache.py                 # rebuild from scratch
python retry_failed.py [--item-id XXX | --all]
python vacuum_duplicates.py             # détecte/supprime doublons (sécurité)
```

---

## 10. Configuration client

### 10.1 Emplacement

`config/clients/{client_id}.yaml`

### 10.2 Template V1 simplifié

```yaml
client_profile:
  client_id: "mvp_test_30days"
  name: "MVP Test — LAI 30 jours"
  active: true
  language: "en"

ingestion:
  default_period_days: 30
  ingestion_mode: "balanced"
  source_bouquets:
    - lai_full_mvp
  ecosystems:
    - tech_lai_ecosystem
  use_url_cache: true
  content_filters:
    min_word_count: 50
    min_content_length: 200
  source_limits:
    max_articles_per_source: 100
    timeout_per_article: 30
    force_all_articles: false

schedule:
  frequency: on_demand     # on_demand | daily | weekly | hourly
  preferred_time: "08:00"
  timezone: "Europe/Paris"
  active: false            # toujours false en MVP, le moteur l'ignore

normalization:
  enabled: true
  llm_provider: anthropic
  llm_model: claude-sonnet-4-x
  prompt_id: generic_normalization
  max_items_per_run: 100
  cost_cap_usd_per_run: 10.0

metadata:
  config_version: "1.0"
  created_date: "2026-04-24"
  notes: "Config MVP post-pivot, ingestion + normalisation uniquement"
```

### 10.3 Différences vs ancien client_config (V2/V3)

**Sections retirées** : `watch_domains`, `bedrock_config`, `newsletter_selection`, `newsletter_layout`, `newsletter_delivery`. Tout ce qui relève du consommateur newsletter sort du périmètre datalake.

**Renommages** :
- `watch_domains` → `ecosystems` (liste simple d'`ecosystem_id`)
- Plus de duplication des scopes dans le client_config : ils sont définis dans `canonical/ecosystems/{ecosystem_id}.yaml` une fois pour toutes.

### 10.4 Section `schedule` : déclarative mais inactive

`schedule.active: false` signifie : le moteur ignore ce bloc en MVP. Les ingestions sont lancées manuellement. Le bloc est là pour préparer la Phase 3 (cron, APScheduler, Airflow) sans toucher au schéma.

---

## 11. Configuration canonical

### 11.1 Structure cible (après ménage et audit nommage)

```
canonical/
├── ecosystems/
│   └── tech_lai_ecosystem.yaml       # définit description, bouquets, scopes utilisés, prompt
├── events/
│   └── event_type_patterns.yaml
├── imports/
│   ├── company_seed_lai.csv
│   ├── glossary.md
│   ├── LAI_RATIONALE.md
│   └── ...
├── ingestion/
│   ├── filter_rules.yaml             # version unique
│   ├── ingestion_profiles.yaml       # version unique
│   └── source_configs.yaml           # version unique
├── parsing/
│   ├── html_selectors.yaml
│   ├── parsing_config.yaml
│   └── url_canonicalization.yaml     # NOUVEAU — règles de canonicalisation URL
├── prompts/
│   └── normalization/
│       └── generic_normalization.yaml
│   (les prompts domain_scoring/ et editorial/ sont archivés — newsletter legacy)
├── scopes/
│   ├── company_scopes.yaml
│   ├── exclusion_scopes.yaml
│   ├── indication_scopes.yaml
│   ├── molecule_scopes.yaml
│   ├── technology_scopes.yaml
│   └── trademark_scopes.yaml
└── sources/
    └── source_catalog.yaml            # version unique, déclare bouquets et écosystèmes
```

### 11.2 Nouveaux fichiers à créer

**`canonical/ecosystems/tech_lai_ecosystem.yaml`** — déclare l'écosystème LAI : description, bouquets associés, scopes à utiliser pour les filtres, prompt de normalisation à utiliser.

```yaml
ecosystem_id: tech_lai_ecosystem
description: "Long-Acting Injectables ecosystem - pharma & biotech signals"
bouquets:
  - lai_full_mvp
  - regulatory_lai
scopes:
  technologies: technology_scopes.lai_keywords
  companies: company_scopes.lai_companies_global
  trademarks: trademark_scopes.lai_trademarks_global
  exclusions: exclusion_scopes.generic_exclusions
normalization:
  prompt: generic_normalization
  # optionnel pour le futur : prompt_override
```

**`canonical/parsing/url_canonicalization.yaml`** — règles de canonicalisation URL : paramètres de tracking à retirer, politique des trailing slashes, scheme, table de redirections connues (optionnelle).

### 11.3 Fichiers archivés (héritage newsletter)

- `canonical/domains/` (legacy V2)
- `canonical/scopes/domain_definitions.yaml` (legacy V2)
- `canonical/prompts/domain_scoring/` (legacy newsletter)
- `canonical/prompts/editorial/` (legacy newsletter)
- `canonical/prompts/backup/` (résidu)
- `canonical/prompts/generated/` (résidu)
- Tous les fichiers `* - Copie.yaml`
- Toutes les variantes secondaires de `source_catalog.*.yaml` après consolidation

Voir §13 pour le plan d'archivage.

---

## 12. Structure du code `src_vectora_inbox_v1/`

### 12.1 Arborescence cible

```
src_vectora_inbox_v1/
├── __init__.py
├── config/
│   ├── canonical_loader.py       # lit canonical/ → objets Python
│   ├── client_loader.py          # lit config/clients/ → objets Python
│   └── schemas.py                # dataclasses canonical des objets
├── datalake/
│   ├── __init__.py
│   ├── storage.py                # abstraction read/write JSONL
│   ├── indexes.py                # CRUD indexes
│   ├── item_id.py                # canonical URL + calcul item_id
│   ├── raw.py                    # RawStore : insert, lookup, list, update_tags
│   ├── curated.py                # CuratedStore : insert, lookup, list
│   └── url_cache.py              # UrlCache : lookup, insert, update, rebuild
├── ingest/                       # RUNTIME — pipeline d'ingestion répété
│   ├── __init__.py
│   ├── orchestrator.py           # ClientOrchestrator, boucle sur sources
│   ├── source_runner.py          # ingest_source() — unité atomique
│   ├── fetcher.py                # HTTP fetcher
│   ├── parsers/
│   │   ├── rss.py
│   │   ├── html.py
│   │   └── pdf.py                # plus tard
│   ├── filters/
│   │   ├── period.py
│   │   ├── lai_keywords.py
│   │   └── exclusions.py
│   └── source_router.py
├── detect/
│   ├── __init__.py
│   └── gap.py                    # raw \ curated → pending queue
├── normalize/
│   ├── __init__.py
│   ├── orchestrator.py           # pipeline normalize complet
│   ├── llm/
│   │   ├── base.py               # interface LLMClient
│   │   └── anthropic.py          # implémentation Claude
│   ├── prompts.py                # chargement + templating des prompts
│   ├── parser.py                 # parse la réponse LLM → structure
│   ├── validator.py              # anti-hallucination
│   └── entities.py               # résolution canonical_id
├── sources/                      # ONBOARDING — workflow d'ajout de source (hors runtime)
│   ├── __init__.py
│   ├── candidates.py             # gestion du backlog source_candidates.yaml
│   ├── discovery.py              # SourceDiscovery (repris/amélioré du legacy)
│   ├── validation.py             # SourceValidator (repris/amélioré du legacy)
│   ├── promoters.py              # promotion candidate → validated dans canonical/
│   └── revalidator.py            # revalidation périodique des sources actives
├── stats/
│   ├── __init__.py
│   ├── health.py                 # update health.json
│   ├── daily.py                  # append stats_daily.jsonl
│   ├── gap_report.py             # génère gap_report.json
│   └── reports.py                # génère reports/*.md
└── scripts/                      # entrées CLI
    │   # --- Runtime ---
    ├── run_ingest.py
    ├── run_detect.py
    ├── run_normalize.py
    ├── run_pipeline.py
    │   # --- Onboarding de source (hors runtime) ---
    ├── discover_source.py
    ├── validate_source.py
    ├── promote_source.py
    ├── onboard_source.py         # discovery + validation + auto-promotion
    ├── revalidate_all.py
    ├── list_candidates.py
    │   # --- Maintenance ---
    ├── rebuild_indexes.py
    ├── rebuild_cache.py
    ├── recompute_stats.py
    ├── validate_datalake.py
    ├── validate_cache.py
    ├── retry_failed.py
    └── generate_report.py
```

### 12.2 Principes d'organisation

- **Modules découplés** : `ingest/`, `detect/`, `normalize/`, `sources/`, `stats/` ne se connaissent pas. Ils parlent tous à `datalake/` ou à `config/` via des interfaces claires.
- **Scripts = I/O, modules = logique** : les scripts dans `scripts/` ne font que parser les arguments CLI et appeler les orchestrators. Toute la logique est testable unitairement.
- **`datalake/` est l'unique point de vérité I/O datalake** : ni `ingest/` ni `normalize/` ne touchent les fichiers du datalake directement.
- **Source-runner et orchestrator séparés** : `source_runner.py` (atomique) ≠ `orchestrator.py` (boucle). Permet de tester chaque source individuellement.
- **Runtime ≠ onboarding** : `ingest/` ne sait rien de `sources/`. `sources/` lit/écrit canonical/ et utilise les parsers (`ingest/parsers/`) pour ses tests, mais ne touche jamais au datalake. Onboarding = écrire dans canonical, jamais dans le datalake.

---

## 13. Plan de transition (Phase 2)

### 13.0 Phase 2.0 — Hygiène complète du repo (Git + structure)

**Document de référence dédié** : `docs/architecture/phase2.0_repo_structure.md` (V2.0).

Cette phase précède toute écriture de code. Elle traite **deux volets complémentaires** :

**Volet Git** (sur GitHub et localement) :
- Sécuriser l'historique : tag `legacy-pre-pivot-20260425` + branche `archive/legacy-pre-pivot`
- Merger les 6 docs Phase 1 (actuellement sur la branche `docs/phase1-design`) dans `main`
- Supprimer les 6 vieilles branches legacy + la branche `docs/phase1-design` une fois mergée
- Nettoyer les stashs locaux

**Volet Structure** (réorganisation du contenu du repo) :
- Création de l'arborescence cible (8 dossiers à la racine)
- Archivage du legacy sous `archive/legacy_pre_pivot_20260425/`
- Rapatriement de `cache/` et `output/` sous `data/`
- Swap de `CLAUDE.md` (ancien → archive, nouveau V1.2 → racine)
- Suppression des fichiers résidus
- Mise à jour de `.gitignore`

**Critère de fin** : le repo a uniquement `main` + `archive/legacy-pre-pivot` sur GitHub, l'arborescence locale respecte la structure cible, le legacy est archivé.

**Environnement d'exécution** : depuis Claude Code dans VS Code (Cowork rencontre des problèmes de permissions sur le `.git/` à cause de la synchronisation OneDrive du dossier).

---

### 13.1 Phase 2.1 — Audit nommage et consolidation canonical (anciennement appelé Phase 2.1.bis)

**Note** : ce qui était décrit ici (archivage des sauvegardes, des backups, des résidus) **a été déplacé dans Phase 2.0** (volet Structure). Voir `docs/architecture/phase2.0_repo_structure.md` §3.3.

Phase 2.1 se concentre désormais uniquement sur l'**audit de nommage exhaustif** et la **consolidation des fichiers canonical** qui n'ont pas pu être traités lors de Phase 2.0 (parce qu'ils nécessitent une analyse fine, pas juste un déplacement).

**Livrable Phase 2.1** : un rapport d'audit `docs/architecture/naming_audit_phase21.md` listant chaque entrée à renommer/garder/archiver dans `canonical/`, validé par Frank, suivi d'un commit `refactor: rename ecosystem vocabulary, consolidate canonical`.

**Détail de l'audit Phase 2.1**

Le rapport d'audit liste, après que Phase 2.0 a déjà déplacé l'essentiel :

1. Tous les fichiers résiduels du repo qui contiennent les mots `domain`, `watch_domain`, `bedrock`, `newsletter`, `scoring`, `matching`, `lambda`, `aws`, `s3` (vocabulaire à migrer)
2. Tous les noms de variables/fonctions/classes dans le code restant qui utilisent ce vocabulaire
3. Toutes les valeurs de configuration dans `canonical/` et `config/clients/` qui le référencent
4. Les noms de fichiers dont le nom ne reflète plus leur contenu après pivot

Pour chaque entrée, je propose : **garder tel quel / renommer en X / archiver / supprimer**.

Frank valide en bloc, j'exécute le refactor dans un commit dédié.

**Renommages clés déjà identifiés** :

| Avant | Après |
|---|---|
| `watch_domains` (client_config) | `ecosystems` |
| `domain_id` | `ecosystem_id` |
| `watch_domain_resolver` | `ecosystem_resolver` |
| `canonical/domains/` | `canonical/ecosystems/` (avec restructuration) |
| `canonical/scopes/domain_definitions.yaml` | fusionné dans `canonical/ecosystems/{eco}.yaml` |
| `canonical/sources/source_catalog_v3.yaml` | `canonical/sources/source_catalog.yaml` |
| `canonical/ingestion/ingestion_profiles_v3.yaml` | `canonical/ingestion/ingestion_profiles.yaml` |
| `canonical/ingestion/filter_rules_v3.yaml` | `canonical/ingestion/filter_rules.yaml` |
| `canonical/ingestion/source_configs_v3.yaml` | `canonical/ingestion/source_configs.yaml` |

### 13.3 Phase 2.2 — Niveau 1 : Fondations

**Objectif** : un seul item LAI ingéré, normalisé, retrouvable bout-en-bout. Le squelette qui prouve que l'architecture tient debout.

**Composants livrés**

*Datalake (essentiel)* :
- `datalake/storage.py` : read/write JSONL minimal (append, scan séquentiel)
- `datalake/item_id.py` : canonicalisation URL + calcul `item_id`. Règles minimales : strip params utm, fragment, lowercase host.
- `datalake/raw.py` : `RawStore` avec insert + lookup. **Un seul index `by_item_id`** suffit ici.
- `datalake/curated.py` : `CuratedStore` symétrique
- `datalake/url_cache.py` : `UrlCache` avec les 3 cas de comportement (ingested / rejected / absent)

*Ingest (RSS uniquement)* :
- `ingest/source_runner.py` : `ingest_source()` atomique
- `ingest/orchestrator.py` : `ClientOrchestrator` basique (sans `--resume` ni `--retry-failed`)
- `ingest/fetcher.py` : HTTP fetcher
- `ingest/parsers/rss.py` : parser RSS

*Detect* :
- `detect/gap.py` : raw \ curated → liste pending

*Normalize* :
- `normalize/llm/base.py` : interface `LLMClient`
- `normalize/llm/anthropic.py` : implémentation Claude (sans retry sophistiqué)
- `normalize/orchestrator.py` : boucle sur pending
- `normalize/prompts.py` : chargement du prompt
- `normalize/parser.py` : parse minimal de la réponse JSON LLM

*Config* :
- `config/canonical_loader.py`
- `config/client_loader.py`
- `config/schemas.py` (dataclasses)

*Canonical minimal* :
- `canonical/ecosystems/tech_lai_ecosystem.yaml`
- `canonical/prompts/normalization/generic_normalization.yaml`
- `canonical/sources/source_catalog.yaml` avec **1 seule source** : `press_corporate__medincell`
- `canonical/ingestion/source_configs.yaml` avec medincell `validated: true`
- `canonical/scopes/technology_scopes.yaml` (lai_keywords)
- `canonical/scopes/exclusion_scopes.yaml`
- `canonical/parsing/url_canonicalization.yaml` (règles minimales)

*Script* :
- `scripts/run_pipeline.py` : enchaîne Ingest → Detect → Normalize

**Critère de fin testable**

```bash
python run_pipeline.py --client mvp_test_30days --source press_corporate__medincell
```

Doit produire : ≥ 1 item dans `datalake_v1/raw/`, le même item dans `datalake_v1/curated/` après normalisation. Un lookup `by_item_id` retourne l'item dans les deux. Le pipeline tourne bout-en-bout sur 1 source RSS, 1 item.

À ce stade : pas de filtres canoniques (juste accept-all), pas de retry, pas de stats, pas de discovery, pas de cache invalidation. C'est volontaire — on prouve l'architecture, on n'optimise pas.

---

### 13.4 Phase 2.3 — Niveau 2 : Cœur

**Objectif** : moteur utilisable au quotidien sur les 8 sources MVP LAI, avec le workflow d'onboarding de source.

**Composants livrés (en plus du Niveau 1)**

*Ingest enrichi* :
- `ingest/parsers/html.py` : parser HTML (la majorité des sources LAI)
- `ingest/parsers/rss.py` : ajout du `prefetch_filter` (économie HTTP)
- `ingest/filters/period.py` : filtre période
- `ingest/filters/lai_keywords.py` : filtre LAI keywords (scopes canoniques)
- `ingest/filters/exclusions.py` : filtre exclusions
- `ingest/source_router.py` : résolution bouquets → sources
- Tous les indexes secondaires raw : `by_source_key`, `by_source_type`, `by_ecosystem`, `by_company_id`, `by_date`

*Normalize enrichi* :
- `normalize/validator.py` : anti-hallucinations LLM (logique récupérée de V2)
- `normalize/entities.py` : résolution `canonical_id` companies
- Retry LLM **complet** (3 niveaux : intra-run, inter-run, marquage failed à 5 tentatives)
- Tous les indexes secondaires curated : `by_event_type`, `by_company_id`, `by_molecule`, `by_technology`, `by_trademark`, `by_date`
- `curated/curation_log.jsonl` opérationnel

*Sources (module dédié, NOUVEAU)* :
- `sources/candidates.py` : gestion du backlog
- `sources/discovery.py` : repris/amélioré du legacy
- `sources/validation.py` : repris/amélioré du legacy
- `sources/promoters.py` : promotion candidate → validated
- Scripts CLI : `discover_source.py`, `validate_source.py`, `promote_source.py`, `onboard_source.py`, `list_candidates.py`

*Stats opérationnels* :
- `stats/health.py` : mise à jour `health.json` à chaque run
- `stats/gap_report.py` : génération automatique du `gap_report.json`

*Scripts runtime enrichis* :
- `run_ingest.py` avec : `--resume`, `--retry-failed`, `--source`, `--bouquet`, `--no-cache`, `--rebuild-cache`, `--fail-fast`
- `run_normalize.py` avec `--retry-failed`, `--max-items`

*Canonical complet* :
- 8 sources LAI MVP validées dans `source_configs.yaml` (medincell, camurus, delsitech, nanexa, pfizer, lidds, taiwan_liposome, fiercepharma + endpoints_news)
- Bouquet `lai_full_mvp` complet dans `source_catalog.yaml`
- Tous les scopes LAI : `company_scopes.yaml`, `molecule_scopes.yaml`, `technology_scopes.yaml`, `trademark_scopes.yaml`, `indication_scopes.yaml`

**Critère de fin testable**

```bash
# Run complet
python run_pipeline.py --client mvp_test_30days
# → ingère les 8 sources, normalise, produit gap_report.json + health.json
# → datalake_v1/raw/ et /curated/ remplis avec items réels LAI

# Onboarding d'une 9e source
python onboard_source.py --source press_corporate__taiwan_liposome
# → discovery + validation + promotion automatique si PASSED
# → la source est ensuite ingérable par tout client incluant son bouquet
```

À ce stade : le datalake LAI MVP est **vivant**, les 8 sources tournent, on peut ajouter de nouvelles sources via le workflow d'onboarding, on a une visibilité opérationnelle minimale (health, gap). C'est utilisable au quotidien.

---

### 13.5 Phase 2.4 — Niveau 3 : Maquillage

**Objectif** : moteur stable, observable en profondeur, robuste, documenté. Qualité de vie pour l'usage long terme.

**Composants livrés (en plus du Niveau 2)**

*Stats avancés* :
- `stats/daily.py` : append `stats_daily.jsonl` (snapshot quotidien)
- `stats/reports.py` : génération de `report_raw.md`, `report_curated.md`, `report_sources.md`, `report_full.md`
- `scripts/generate_report.py` : CLI rapports

*Maintenance et hygiène* :
- `scripts/recompute_stats.py`
- `scripts/rebuild_indexes.py`
- `scripts/rebuild_cache.py`
- `scripts/validate_datalake.py` : cohérence JSONL ↔ indexes
- `scripts/validate_cache.py` : cohérence cache ↔ datalake
- `scripts/revalidate_all.py` : revalidation périodique des sources actives
- `sources/revalidator.py` : module dédié à la revalidation périodique

*Robustesse* :
- Cost cap LLM par run (`cost_cap_usd_per_run` réellement appliqué, alerte si proche du seuil)
- Tests unitaires complets : canonicalisation URL, item_id, indexes, parsers, filters, validator anti-hallucinations
- Tests d'intégration sur le pipeline bout-en-bout
- `ingest/parsers/pdf.py` (si on en a besoin pour FDA labels — sinon différé)

*Documentation* :
- README dans `src_vectora_inbox_v1/` : guide utilisateur (commandes courantes, dépannage)
- Mise à jour de `CLAUDE.md` : remplace les règles V2/V3 par celles de V1
- Mise à jour de `docs/architecture/` : pointe vers ce design en référence
- Inventaire à jour des sources validées avec leurs configurations

**Critère de fin testable**

- Le rapport hebdomadaire `report_full.md` est généré automatiquement et lisible par un consommateur sans contexte
- Le moteur tourne sans surveillance pendant plusieurs semaines
- Les incidents sont diagnostiquables via les outils de validation/maintenance
- La documentation est suffisante pour qu'une autre personne reprenne le projet
- Les sources actives sont revalidées trimestriellement, les cassures sont détectées avant qu'elles n'affectent silencieusement l'ingestion

---

### 13.6 Vue d'ensemble des paliers

| Palier | Objectif | Livrable testable | Composants à ajouter |
|---|---|---|---|
| **Niveau 1 — Fondations** | 1 item bout-en-bout | `run_pipeline.py` produit 1 item curated | datalake/, ingest RSS minimal, normalize basique, canonical minimal |
| **Niveau 2 — Cœur** | 8 sources MVP utilisables au quotidien | `run_pipeline.py --client mvp_test_30days` ingère et normalise les 8 sources, `onboard_source.py` ajoute une 9e source | parsers HTML, filtres, retry complet, indexes secondaires, module sources/, stats minimaux |
| **Niveau 3 — Maquillage** | Moteur stable + observable + documenté | Rapports auto, revalidation périodique, maintenance complète, doc | reports, validations, tests, revalidator, cost cap |

**Principe clé** : on ne passe au niveau N+1 qu'après avoir validé que le critère de fin du niveau N est atteint. À tout moment, le moteur est dans un état stable et utilisable, juste plus ou moins riche fonctionnellement.

---

## 14. Points laissés en suspens

Tous les éléments différés sont listés dans `docs/architecture/future_optimizations.md`. Récap des principaux :

1. **Cache** : invalidation automatique par signature de filtre (futur §1)
2. **Multi-tag écosystème par LLM** (futur §2)
3. **Re-curation lors d'un changement de prompt** (futur §3)
4. **Parallélisation ingestion** (futur §4) et **normalisation** (futur §5)
5. **Migration AWS / S3** (futur §6)
6. **Backend vectoriel pour RAG** (futur §7)
7. **Politique de retention / purge** (futur §8)
8. **Scheduler automatique** (futur §9)
9. **Dashboard HTML pour stats** (futur §10)

---

## 15. Résumé ultra-condensé

| Aspect | Décision |
|---|---|
| Vision | Datalake thématique de veille, moteur d'alimentation uniquement |
| Local-first | Oui, PC de Frank. Seul appel externe : Anthropic API. |
| LLM | Claude via API directe Anthropic |
| Datalake | Unique, tags multivalués, écosystème = dimension |
| Vocabulaire | `ecosystem_id` (str) / `ecosystems` (list) — `domain*` abandonné |
| Clé de liaison | `item_id = {source_key}__{sha256(canonical_url)[:16]}` |
| Format | JSONL append-only, partition `YYYY/MM` par `published_at` |
| Indexes | JSON rebuildables, incrémentaux |
| Cycle de vie | `raw` → `pending` → `curated` (ou `failed` après 5 tentatives) |
| Retry LLM | 3× intra-run avec backoff, re-queue inter-run, failed à 5 tentatives |
| Ingest atomique | Par source ; orchestrateur en boucle pour le client |
| Continue par défaut | Échec d'une source n'arrête pas les autres ; `--fail-fast` optionnel |
| Cache | Permanent par écosystème, contient `ingested` + `rejected`, invalidation manuelle (`--rebuild-cache`) |
| Nouveau code | `src_vectora_inbox_v1/` |
| Nouveau datalake | `data/datalake_v1/` (vide au départ, on remplit ensemble) |
| Stats | health.json, stats_daily.jsonl, gap_report.json, reports/ |
| Onboarding sources | Workflow distinct du runtime : Discovery → Validation → Promotion (module `sources/`) |
| Revalidation | `revalidate_all.py` à tourner périodiquement pour détecter les sources cassées |
| Ancien datalake | `data/warehouse/` ignoré, pas de migration |
| Ménage repo | Oui, sous `archive/legacy_pre_pivot_20260424/` |
| Audit nommage | Phase 2.1.bis, exhaustif, pré-commit, validé par Frank |
| Optimisations futures | Tracées dans `future_optimizations.md` |

---

*Fin du document de design V1.1 — prêt pour validation finale.*
