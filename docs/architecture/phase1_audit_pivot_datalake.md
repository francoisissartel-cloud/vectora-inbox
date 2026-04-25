# Phase 1 — Audit de l'existant pour le pivot "moteur datalake"

**Date** : 2026-04-24
**Auteur** : Claude (sur demande de Frank)
**Contexte** : Pivot du projet Vectora Inbox, de "moteur de newsletter" vers "moteur d'alimentation d'un datalake continu et propre". Cet audit lit le repo tel qu'il est pour préparer la remise à plat.

---

## 1. Synthèse en une page

**Ce qui est solide et à capitaliser**
- `canonical/` est une vraie gouvernance métier, riche, bien structurée, réutilisable telle quelle pour la cible datalake.
- Le moteur d'ingestion **V3** (`src_v3/vectora_core/ingest/`) fonctionne, il est modulaire, il a les bonnes abstractions (sources, profils, filtres, cache, parsers RSS/HTML, déduplication).
- Le **Warehouse local** existe déjà et fonctionne : `data/warehouse/ingested/profiles/tech_lai_ecosystem/`, 21 items LAI réels, format JSONL, indexes par date et par content_hash, stats à jour.
- Un `item_id` déterministe `{source_key}__{sha256(url)[:16]}` est déjà généré — bonne base pour le liant, avec une amélioration à faire sur la canonicalisation de l'URL.
- Le prompt `canonical/prompts/normalization/generic_normalization.yaml` est excellent : vertical-agnostic, extraction factuelle uniquement, explicitement découplé du scoring/matching.

**Ce qui est à écarter ou séparer**
- Toute la lambda `newsletter` V2 (sélection, assembler, editorial) — hors scope.
- Dans `normalize_score` V2 : la partie `matcher` (matching vers watch_domains) et `scorer` (score de pertinence) sont **de la logique newsletter déguisée**, à retirer du pipeline datalake.
- La partie `normalizer` **pure** (appel LLM pour extraire entités, dates, event type, summary) est par contre à récupérer — c'est exactement ce qu'il faut pour la zone curated.

**Points critiques à trancher avec Frank**
1. **LLM de normalisation** : le code V2 utilise **Bedrock (Anthropic Claude via AWS)**, pas OpenAI. Frank m'a parlé d'OpenAI. À clarifier : OpenAI prévu ? Bedrock déjà en place ? Les deux ?
2. **Canonicalisation URL** : le content_hash actuel mélange URL+titre+content. Les URLs non canonicalisées (tracking params, redirections) produisent des content_hash différents pour le même article. À stabiliser.
3. **Couplage AWS** : le code V2 normalize_score est très couplé à S3 (s3_io obligatoire, validation "pas de test" agressive). Pour du local-first, il faut une abstraction de stockage.
4. **Hygiène du repo** : dossiers " - Copie", "sauvegarde 2204...", 6 variantes de `source_catalog.yaml`, `backup_code/`, `backups/`, `snapshots/`, `build/`, `layer_build_temp/` → à ranger AVANT de créer `src_vectora_inbox/`.

---

## 2. Cartographie réelle du repo

```
vectora-inbox - claude/
├── CLAUDE.md                       # ✅ règles projet (post-pivot)
├── VERSION                         # vectora_core=1.8.7, common_deps=1.0.6
├── src_v3/                         # ✅ code actif — mais pollué
│   ├── vectora_core/               # ← VRAI code (à conserver)
│   │   ├── ingest/                 # pipeline d'ingestion V3, OK
│   │   ├── shared/                 # utils, s3_io, url_cache, client_url_cache
│   │   └── warehouse/              # gestionnaire Warehouse (fonctionne)
│   ├── lambdas/                    # vide → handlers non implémentés en V3
│   ├── "sauvegarde 2204 15h07..."  # ❌ copie manuelle datée
│   ├── "sauvegarde 2204 apres midi"# ❌ copie manuelle datée
│   └── "sauvegarde 2304 09h08..."  # ❌ copie manuelle datée
├── canonical/                      # ✅ gouvernance métier — riche
│   ├── domains/                    # 2 fichiers (v1 + v2.1) → choix à faire
│   ├── events/
│   ├── imports/                    # CSVs entités, glossaire, rationale
│   ├── ingestion/                  # filter_rules_v3, source_configs_v3, profiles
│   ├── parsing/                    # html_selectors, parsing_config
│   ├── prompts/
│   │   ├── normalization/          # generic_normalization.yaml (excellent)
│   │   ├── domain_scoring/         # orienté newsletter → à archiver
│   │   ├── editorial/              # orienté newsletter → à archiver
│   │   ├── backup/ + generated/    # résidus, à nettoyer
│   │   └── * " - Copie".yaml       # ❌ doublons de travail
│   ├── scopes/                     # 7 fichiers YAML — bien structuré
│   └── sources/                    # ❌ 6+ variantes de source_catalog
│       ├── source_catalog.yaml          (3205 lignes)
│       ├── source_catalog_backup.yaml   (1390)
│       ├── source_catalog_merged.yaml   (3202)
│       ├── source_catalog_new.yaml      (686)
│       ├── source_catalog_old.yaml      (181)
│       ├── source_catalog_v3.yaml       (172)  ← référence V3 ?
│       └── source_candidates_v3.yaml    (1782)
├── config/clients/                 # ✅ configs client — certaines à nettoyer
│   ├── mvp_test_30days.yaml        # pilote MVP
│   ├── mvp_test_100days.yaml
│   ├── lai_weekly_v2.4.yaml
│   ├── lai_weekly_v3.1_debug.yaml
│   └── test_*.yaml                 # (camurus, nanexa, medincell, taiwan, lidds)
├── data/warehouse/                 # ✅ datalake raw actuel — fonctionne
│   ├── warehouse_config.json
│   ├── client_mappings.json
│   └── ingested/profiles/tech_lai_ecosystem/
│       ├── ingested_items.jsonl    # 21 items réels
│       ├── indexes/by_date.json
│       ├── indexes/by_content_hash.json
│       ├── last_update.json
│       └── warehouse_stats.json
├── cache/                          # ✅ caches URL par client + cache global
│   ├── clients/{client_id}/url_cache.json + metadata.json
│   └── urls/url_cache_main.json
├── output/runs/                    # sorties par run (logs, manifests)
├── scripts/                        # très chargé, avec doublons et archive/
├── tests/                          # unit/integration/warehouse/ingestion…
├── snapshots/snapshot_2026-02-09/  # src_v2 complet (code legacy)
├── backup_code/                    # ❌ 2 backups lourds récents
├── backups/                        # ❌ 3 backups "pre_warehouse_deployment"
├── build/                          # ❌ packages Lambda V1/V2 avec deps gonflées
├── layer_build_temp/               # ❌ à dégager
├── layer_management/               # layers AWS (legacy V2)
├── infra/                          # CloudFormation legacy
├── deployment/, monitoring/, archive/
└── contracts/                      # contrats Lambda V2 (legacy)
```

**Verdict de cartographie** : il y a un vrai fonds technique solide (`src_v3/vectora_core/`, `canonical/`, `data/warehouse/`) noyé dans un empilement d'artefacts de plusieurs époques. La "remise à plat" est au moins autant un travail de tri que d'architecture.

---

## 3. Zoom : moteur d'ingestion V3

### Fichiers actifs (`src_v3/vectora_core/`)

```
ingest/
  __init__.py           IngestionOrchestratorV3 — pipeline complet
  config_loader_v3.py   charge canonical/ + client config
  source_router.py      résout bouquets → sources
  fetcher.py            HTTP fetcher
  parser_rss.py         profil rss_full / rss_with_fetch (avec prefetch_filter)
  parser_html.py        profil html_generic / html_pdf
  filter_engine.py      filtres période / LAI / exclusions
  content_extractor.py  extraction contenu
  date_extractor.py     extraction de dates (multi-sources)
  models.py             StructuredItem, SourceReport, RunManifest
  enhanced_models.py    + enhanced_run_reporter.py  (doublons à rationaliser)
  pagination_adaptive.py
shared/
  s3_io.py              I/O S3
  url_cache.py          cache URL global
  client_url_cache.py   cache URL par client (cleanup_expired_entries)
  utils.py              generate_run_id, calculate_content_hash, calculate_item_id
  watch_domain_resolver.py
warehouse/
  ingested_warehouse.py  IngestedWarehouse — écrit JSONL + indexes
  client_mappings.py     résout client_id → sources autorisées
  deduplication.py
  reconstitution.py      reconstitution par (sources client × période)
  reconstitution_cache.py
  memory_utils.py
```

### Pipeline orchestré

```
load configs → init components → resolve sources (bouquets)
 → for each source: parse (RSS/HTML) + filter qualité
 → aggregate → filter engine (période/LAI/exclusions)
 → deduplicate (content_hash) → validate
 → write output/runs/{run_id}/{ingested_items,rejected_items,run_manifest}.json
 → action 1: feed Warehouse (JSONL append + indexes)
 → action 2: reconstitute normalize_input.json
            (Warehouse filtré sur sources_client × période)
```

### Points forts

- Pipeline **séquentiel lisible**, une étape = une méthode (`_load_configurations`, `_process_all_sources`, `_apply_filters`, `_deduplicate_and_validate`, `_feed_warehouse_and_reconstitute`).
- Cache URL au niveau client, nettoyable par TTL.
- `prefetch_filter` : pour les RSS volumineux, filtre LAI sur titre+résumé AVANT de fetcher l'article complet → économie d'HTTP.
- Le concept d'**écosystème** (`tech_lai_ecosystem`) mutualise le Warehouse entre clients — bonne architecture pour éviter de ré-extraire les mêmes items.
- `item_id = {source_key}__sha256(url)[:16]` : déterministe, réutilisable.
- `StructuredItem` inclut `content_hash` calculé sur le contenu → déduplication robuste.

### Points à challenger

- **Pollution `src_v3/`** : trois dossiers `sauvegarde …` côtoient le vrai code. Des parsers (`parser_rss.py`, etc.) existent dans chacun. Risque d'imports ambigus.
- **Couplage local/S3** : environment == "local" vs != partout dans l'orchestrateur. Ça fonctionne mais c'est fragile ; une abstraction de `Storage` rendrait le code plus clair.
- **URL non canonicalisée** : `calculate_item_id(source_key, url)` et `_calculate_content_hash` (Warehouse) utilisent l'URL brute. Un article avec `?utm_source=rss` et sans produit deux `item_id` et deux `content_hash`.
- **O(n) par insert** : `_count_lines_in_jsonl` re-scanne tout le JSONL à chaque ajout pour obtenir le numéro de ligne. Acceptable à 21 items, ingérable à 50k.
- **Logique bouquets dupliquée** : `_resolve_sources_from_bouquets` dans l'orchestrateur a un mapping en dur `{'lai_full_mvp': [...6 sources...]}` qui existe déjà dans `canonical/sources/source_catalog_v3.yaml` et dans `client_mappings.json`. Trois sources de vérité.
- **Fallbacks hardcodés client** : `_get_default_sources_for_client` fait du `if 'medincell' in client_id.lower()` → viole la règle config-driven.
- **Doublons de modèles** : `models.py` et `enhanced_models.py` ; `run_reporter.py` et `enhanced_run_reporter.py`. À consolider.
- **Écriture locale du `normalize_input.json`** : l'orchestrateur ingest écrit un fichier pensé pour le consommateur suivant. Couplage implicite. Dans la cible, la détection "qu'est-ce qui a changé dans le Warehouse depuis la dernière normalisation" devrait être à la charge du service de normalisation, pas de l'ingest.

---

## 4. Zoom : `normalize_score` V2

### État actuel

Le dossier **actif** `src_v3/lambdas/normalize_score/` est **vide**. Le seul code V2 complet se trouve dans `snapshots/snapshot_2026-02-09/src_v2/vectora_core/normalization/` et dans `build/normalize_score_v2/` (package Lambda). Donc `normalize_score` n'est pas intégré au pipeline V3 — il ne tourne pas aujourd'hui, même si Frank pense l'utiliser.

### Modules (snapshot 2026-02-09, 2787 lignes au total)

| Fichier | Lignes | Rôle | Verdict |
|---|---|---|---|
| `__init__.py` | 455 | Orchestration (load → normalize → match → score → write curated/) | Partiellement récupérable (séparer en 2) |
| `normalizer.py` | 594 | Boucle items → appels LLM séquentiels/parallèles + validation anti-hallucinations | ✅ **à récupérer** |
| `bedrock_client.py` | 375 | Appels Bedrock avec retry/backoff exponentiel, client invoke_model | ✅ **à récupérer**, à généraliser en `LLMClient` |
| `bedrock_matcher.py` | 236 | Matching items → watch_domains via LLM | ❌ logique newsletter |
| `bedrock_domain_scorer.py` | 130 | 2ème appel LLM pour scorer les domaines | ❌ logique newsletter |
| `scorer.py` | 573 | Score final (entities + domains + recency + boosts) | ❌ logique newsletter |
| `matcher.py` | — | Matching déterministe (keywords) | ❌ logique newsletter |
| `data_manager.py` | 424 | I/O S3 pour curated/ | Concept réutilisable, implémentation à refaire |

### Ce qui est vraiment utile pour la cible datalake

**Noyau LLM** (`bedrock_client.py` + `normalizer.py`) :
- Appel Bedrock avec retry ThrottlingException et backoff exponentiel + jitter
- Parallélisation optionnelle (`max_workers`)
- Validation post-LLM pour détecter les hallucinations (vérification que les entités extraites apparaissent vraiment dans le texte)
- Chargement du prompt canonical via `prompt_resolver`

**Prompt de normalisation** (`canonical/prompts/normalization/generic_normalization.yaml`) :
- Explicitement **vertical-agnostic** : "DO NOT evaluate domain relevance (LAI, siRNA, etc.) - just extract facts"
- Extraction structurée : summary détaillé, event_date + published_date + confidence, event classification (partnership / regulatory / clinical_update / business / corporate_move), entités (companies, molecules, technologies, trademarks)
- C'est exactement le cahier des charges de la zone **curated** du datalake.

### Ce qui doit sortir du pipeline d'ingestion

`bedrock_matcher` / `bedrock_domain_scorer` / `scorer` / `matcher` : tout ce qui produit `matched_domains`, `matching_results`, `domain_scores`, `final_score` relève du **consommateur newsletter**, pas du datalake. À archiver en tant que référence pour quand on fera le moteur de newsletter.

### Contradictions avec ce que Frank m'a dit

- Frank : « un moteur qui se connecte via API a **openai** pour normaliser »
- Réalité du code : **Bedrock** (AWS, modèle Anthropic Claude Sonnet 3)
- Il faut clarifier : est-ce qu'on reste sur Bedrock (infra AWS déjà en place) ou on bascule OpenAI (plus simple en local, pas de credentials AWS, payant via clé API) ?

---

## 5. Zoom : `canonical/`

### Solidité de la gouvernance

Le canonical est la partie la plus saine du repo. Il sépare proprement :
- **Quoi monitorer** (`sources/source_catalog_v3.yaml`, `sources/source_configs_v3.yaml`)
- **Comment ingérer** (`ingestion/ingestion_profiles_v3.yaml`, `ingestion/filter_rules_v3.yaml`)
- **Quoi filtrer / matcher** (`scopes/` : companies, molecules, technologies, trademarks, indications, exclusions)
- **Comment prompt** (`prompts/normalization/`, `prompts/domain_scoring/`, `prompts/editorial/`)
- **Quoi parser** (`parsing/html_selectors.yaml`, `parsing/parsing_config.yaml`)
- **Référentiels métier** (`imports/` : CSVs, glossary.md, LAI_RATIONALE.md)

Le `filter_rules_v3.yaml` est un exemple de document bien pensé : il décrit son rôle, ses articulations avec les autres canonical files, ses invariants ("Jamais de valeurs hardcodées dans le code Python"). Il documente `prefetch_filter`, `period_filter`, `actor_type_resolution`. C'est la vraie source de vérité du comportement du moteur.

### Ce qui doit être nettoyé

- **`source_catalog`** : 6+ variantes (`.yaml`, `_backup`, `_merged`, `_new`, `_old`, `_v3`, `_candidates_v3`). Un seul doit être "actif". Actuellement `source_catalog.yaml` fait 3205 lignes et `source_catalog_v3.yaml` 172 lignes. À trancher.
- **Doublons " - Copie"** : `canonical/prompts/domain_scoring/lai_domain_scoring - Copie.yaml`, `canonical/prompts/normalization/generic_normalization - Copie.yaml`.
- **`ingestion_profiles.yaml` (116 l.) vs `ingestion_profiles_v3.yaml` (88 l.)** : lequel est lu par le moteur ?
- **`domains/lai_domain_definition.yaml` vs `lai_domain_definition_v2.1.yaml`** : deux versions coexistent.
- **Prompts orientés newsletter** : `domain_scoring/` et `editorial/` ne sont pas utilisés par le pipeline datalake. À isoler.
- **`prompts/backup/`** et **`prompts/generated/`** : résidus à archiver.

### Config client MVP (`mvp_test_30days.yaml`)

Bonne structure : `client_profile`, `ingestion`, `watch_domains`, `bedrock_config`.

Sections **à retirer** pour un client "datalake only" :
- `newsletter_selection` (max_items_total, min_domain_score)
- `newsletter_layout` (sections, distribution_strategy)
- `newsletter_delivery` (format, delivery_method)

Ces sections viendront dans une future config **consommateur**, séparée.

---

## 6. Zoom : Warehouse actuel

### État réel

- Chemin : `data/warehouse/ingested/profiles/tech_lai_ecosystem/`
- Format : **JSONL append-only** (156 Ko, 21 items aujourd'hui)
- Indexes :
  - `by_date.json` : date ISO → [line_numbers]
  - `by_content_hash.json` : content_hash → {line_number, item_id, first_seen, run_id, source_key}
- Stats : `warehouse_stats.json` (total_items, date_range, by_year, by_source_type, by_company, recent_activity)
- Métadonnées : `last_update.json`, `warehouse_config.json` (retention_days, ecosystems, deduplication_method)

### Schéma d'un item stocké

```json
{
  "item_id": "press_corporate__medincell__e047054bfcddea63",
  "run_id": "mvp_test_30days__20260423_123305_9875b3b1",
  "source_key": "press_corporate__medincell",
  "source_type": "press_corporate",
  "actor_type": "pure_lai",
  "title": "...",
  "url": "https://www.medincell.com/...",
  "published_at": "2026-04-22",
  "ingested_at": "2026-04-23T16:35:19.338566Z",
  "content": "...",
  "content_hash": "...",
  "warehouse_ingested_at": "...",
  "warehouse_run_id": "...",
  "warehouse_ecosystem": "tech_lai_ecosystem"
}
```

### Ce qui est bien

- **JSONL append-only** : parfait pour un raw store ; les nouveaux items ne modifient jamais les anciens, on peut tailer pour détecter les nouveaux.
- **Mutualisation par écosystème** : plusieurs clients (test_medincell, lai_weekly, mvp_test_30days) alimentent le même Warehouse — pas de duplication de contenu.
- **Indexes séparés** : ils sont rechargeables, rebuildables, et lookup rapides.
- **Enrichissement au stockage** : `warehouse_ingested_at` / `warehouse_run_id` donnent la traçabilité.

### Ce qui manque pour la cible

1. **Pas de zone `curated/`** dans `data/warehouse/`. La cible demande `raw/` + `curated/`.
2. **Pas de mécanisme de détection "nouveaux depuis la dernière normalisation"**. Aujourd'hui on reconstitue toute la fenêtre temporelle pour chaque run. On devrait pouvoir demander "items du raw qui ne sont pas encore dans le curated" (gap analysis via `item_id`).
3. **Content_hash fragile** : calculé sur `url + title + content`. Si l'URL a un paramètre de tracking qui change, le hash change → même article ingéré deux fois.
4. **Pas de statut de cycle de vie** par item : un item est-il `raw`, `curated`, `curation_failed`, `curated_then_updated` ? Pas de machine d'état explicite.

---

## 7. Recommandations concrètes (à valider avant Phase 2)

### A. Clé de liaison unique

```
item_id = sha256( canonical_url(item.url) + "|" + item.source_key )[:16]
```

avec `canonical_url` qui :
- lower-case l'host
- strip les fragments (`#...`)
- strip les paramètres de tracking connus (`utm_*`, `gclid`, `fbclid`, `mc_cid`, etc.) via liste blanche/noire dans `canonical/parsing/url_canonicalization.yaml`
- résout les redirections connues (table optionnelle)

L'URL brute reste conservée en `url_raw` pour affichage. Le `content_hash` (hash du contenu) reste un champ séparé, utilisé uniquement pour détecter qu'un item a **changé** (auteur a modifié l'article), pas pour l'identifier.

### B. Architecture cible des zones

```
data/datalake/
├── raw/
│   └── {ecosystem}/                    # ex: tech_lai_ecosystem
│       ├── items.jsonl                 # append-only, 1 ligne = 1 item canonicalisé
│       └── indexes/
│           ├── by_item_id.json         # lookup O(1)
│           ├── by_date.json
│           └── by_source.json
└── curated/
    └── {ecosystem}/
        ├── items.jsonl                 # idem, mais items enrichis par le LLM
        ├── indexes/
        │   └── by_item_id.json
        └── curation_log.jsonl          # trace des curations {item_id, status, at, prompt_version, cost}
```

La "gap analysis" devient :

```
items_to_curate = set(raw.item_ids) − set(curated.item_ids)
```

### C. Pipeline logique (le nouveau cœur)

```
ingest              : sources → raw (append-only)
detect-new          : diff raw\curated → queue d'item_ids à curer
normalize (LLM)     : pour chaque item_id, load raw → LLM → write curated
curate maintenance  : stats, retention, reindex, gap report
```

Le `detect-new` est trivial avec un index `by_item_id`. C'est un script (pas une Lambda) qui lit les deux indexes et retourne une liste.

### D. Nommage et vocabulaire — proposition

Terme Frank → terme cible :
- "Warehouse" → `datalake/raw/`
- "datalake curé" → `datalake/curated/`
- L'objet de stockage global → `datalake`
- L'unité fonctionnelle partagée entre clients → `ecosystem` (garder, c'est bien)

### E. Arbitrages à demander à Frank

1. **LLM** : Bedrock (existant) ou OpenAI (mentionné) ? Ou abstraction `LLMClient` qui supporte les deux avec un seul switch ?
2. **Storage local vs S3** : on garde `data/datalake/` en local et on synchronise S3 séparément ? Ou on fait une abstraction `Storage` dès le départ ?
3. **Ecosystem** : on garde le terme "ecosystem" ou on renomme "domain" / "scope" ?
4. **Retention** : retention_days=730 actuellement dans `warehouse_config.json` — OK pour la cible ?
5. **Item_id** : on modifie `calculate_item_id` pour canonicaliser l'URL ? Ça rendra les `item_id` existants obsolètes → migration one-shot nécessaire.

### F. Hygiène AVANT de créer `src_vectora_inbox/`

Avant tout code nouveau, nettoyer (dans un commit dédié) :
- Les trois dossiers `sauvegarde …` dans `src_v3/`
- Les doublons " - Copie" dans `canonical/`
- Les 6 variantes de `source_catalog.*.yaml` → garder le bon, archiver les autres
- Les deux `ingestion_profiles` → garder v3
- `backup_code/`, `backups/`, `layer_build_temp/` → déplacer dans un `archive/` unique
- `scripts/ingestion 2204 15h07 - Copie` et `scripts/sauvegarde 2304 09h08ingestion - Copie`

Ça va libérer énormément de bruit et rendre les diffs de la Phase 2 lisibles.

---

## 8. Ce que je propose comme Phase 2

Après validation de ce rapport et arbitrage des points §7.E :

**Phase 2.1 — Nettoyage hygiénique du repo** (pas de nouveau code)
1. Archiver les dossiers `sauvegarde …` de `src_v3/` dans un dossier `archive/src_v3_rolling_copies/`.
2. Trancher les variantes de `source_catalog` et `ingestion_profiles` ; archiver les rejetées.
3. Consolider `backup_code/`, `backups/`, `layer_build_temp/` sous `archive/`.

**Phase 2.2 — Création de la nouvelle base `src_vectora_inbox/`**
```
src_vectora_inbox/
├── datalake/
│   ├── raw/                    # gestion raw store (ex-Warehouse)
│   ├── curated/                # gestion curated store (nouveau)
│   ├── storage.py              # abstraction Local/S3
│   ├── indexes.py
│   └── url_canonical.py        # canonicalisation URL + item_id
├── ingest/                     # importé depuis src_v3/vectora_core/ingest/
│   └── …
├── normalize/                  # récupéré de V2, dépouillé du matching/scoring
│   ├── llm_client.py           # abstraction Bedrock | OpenAI
│   ├── normalizer.py           # boucle d'appels LLM
│   └── validator.py            # anti-hallucinations
├── detect/
│   └── gap.py                  # raw \ curated → queue
└── shared/
    └── …
```

**Phase 2.3 — Migration du pipeline**
1. Brancher ingest V3 sur le nouveau `raw/` (via `item_id` canonical).
2. Implémenter `detect/gap.py`.
3. Implémenter le `normalize` en mode local (LLM choisi en §7.E).
4. Valider bout en bout sur les 6 sources LAI du MVP avec le client `mvp_test_30days`.

**Phase 2.4 — Durcissement**
- Migration des `item_id` existants du Warehouse actuel vers le nouveau format canonicalisé (script one-shot).
- Rebuild des indexes.
- Rapport de couverture.

---

*Fin de l'audit Phase 1.*
