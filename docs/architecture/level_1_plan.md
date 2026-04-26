# Niveau 1 — Fondations : plan de palier

**Statut** : ⏸ À démarrer (après Phase 2.1 — Sprint 001 + Sprint 002)
**Date de démarrage prévue** : après validation Sprint 002 (exécution renommages Phase 2.1)
**Document parent** : `docs/architecture/datalake_v1_design.md` §13

---

## Objectif

Livrer un pipeline bout-en-bout sur **1 source RSS, 1 item LAI**, **entièrement piloté par les fichiers de configuration** : ingestion → détection → normalisation → item curated retrouvable.

C'est le squelette qui prouve deux choses à la fois :
1. L'architecture tient debout
2. Le moteur est **config-driven dès le départ** — aucune logique métier codée en dur

### Ce que "config-driven dès le Niveau 1" veut dire concrètement

Le moteur ne sait pas quelle source lancer, ni comment la fetcher, ni si elle est validée. Il apprend tout ça en chargeant les fichiers canonical au démarrage :

| Question | Répondu par |
|---|---|
| Quelles sources existent ? | `canonical/sources/source_catalog.yaml` |
| Cette source est-elle validée (active) ? | `canonical/ingestion/source_configs.yaml` → `validated: true/false` |
| Comment la fetcher ? (RSS, HTML, API) | `source_configs.yaml` → `fetch_mode` |
| Comment parser son contenu ? | `source_configs.yaml` → `parser_config` |
| Quels filtres d'ingestion appliquer ? | `source_configs.yaml` → `filter_config` |
| Quel écosystème cible ? | `canonical/ecosystems/tech_lai_ecosystem.yaml` |
| Quel prompt LLM utiliser ? | `canonical/prompts/normalization/generic_normalization.yaml` |
| Quel client fait tourner quelles sources ? | `config/clients/mvp_test_30days.yaml` → bouquet de sources |

**Conséquence** : ajouter une 2e source au Niveau 2 = ajouter des lignes YAML. Zéro modification Python.

**Anti-pattern à éviter** (cf. CLAUDE.md §5) :
```python
# ❌ Jamais ça
if source_key == "press_corporate__medincell":
    use_rss_parser()
```
```python
# ✅ Toujours ça
parser = load_parser(source_config["parser_type"])
parser.run(source_config["parser_config"])
```

---

## Critère de fin testable

```bash
python scripts/run_pipeline.py --client mvp_test_30days --source press_corporate__medincell
```

Doit produire :
- ≥ 1 item dans `data/datalake_v1/raw/`
- Le même item dans `data/datalake_v1/curated/` après normalisation LLM
- Un lookup `by_item_id` retourne l'item dans les deux stores

Pas de filtres canoniques (accept-all), pas de retry, pas de stats, pas de discovery. On prouve l'architecture, on n'optimise pas.

---

## Composants à livrer

### Groupe 1 — Datalake core (socle, aucune dépendance)

| Module | Description courte |
|---|---|
| `datalake/storage.py` | Read/write JSONL minimal (append, scan séquentiel) |
| `datalake/item_id.py` | Canonicalisation URL + calcul `item_id` (sha256 tronqué) |
| `datalake/raw.py` | `RawStore` : insert + lookup by_item_id |
| `datalake/curated.py` | `CuratedStore` symétrique à `RawStore` |
| `datalake/url_cache.py` | `UrlCache` : 3 états (ingested / rejected / absent) |

### Groupe 2 — Config + Canonical minimal (YAML, aucune dépendance code)

| Fichier | Description courte |
|---|---|
| `config/schemas.py` | Dataclasses : `SourceConfig`, `ClientConfig`, `EcosystemConfig` |
| `config/canonical_loader.py` | Chargement des fichiers `canonical/` |
| `config/client_loader.py` | Chargement des `config/clients/*.yaml` |
| `canonical/ecosystems/tech_lai_ecosystem.yaml` | Définition écosystème LAI |
| `canonical/sources/source_catalog.yaml` | **1 seule source** : `press_corporate__medincell` |
| `canonical/ingestion/source_configs.yaml` | Config medincell avec `validated: true` |
| `canonical/scopes/technology_scopes.yaml` | `lai_keywords` (pour l'avenir — accept-all au Niveau 1) |
| `canonical/scopes/exclusion_scopes.yaml` | Idem |
| `canonical/parsing/url_canonicalization.yaml` | Règles minimales de canonicalisation URL |
| `canonical/prompts/normalization/generic_normalization.yaml` | Prompt LLM de normalisation |

### Groupe 3 — Ingest RSS (dépend Groupes 1 + 2)

| Module | Description courte |
|---|---|
| `ingest/fetcher.py` | HTTP fetcher (simple, sans retry) |
| `ingest/parsers/rss.py` | Parser RSS |
| `ingest/source_runner.py` | `ingest_source()` — unité atomique |
| `ingest/orchestrator.py` | `ClientOrchestrator` basique (sans --resume ni --retry-failed) |

### Groupe 4 — Detect + Normalize (dépend Groupes 1 + 2)

| Module | Description courte |
|---|---|
| `detect/gap.py` | raw \ curated → liste des items pending |
| `normalize/llm/base.py` | Interface `LLMClient` (abstraction pour portabilité) |
| `normalize/llm/anthropic.py` | Implémentation Claude via API Anthropic directe |
| `normalize/orchestrator.py` | Boucle sur les items pending |
| `normalize/prompts.py` | Chargement du prompt depuis canonical |
| `normalize/parser.py` | Parse minimal de la réponse JSON LLM |

### Groupe 5 — Pipeline + smoke test (dépend Groupes 1 → 4)

| Fichier | Description courte |
|---|---|
| `scripts/run_pipeline.py` | Enchaîne Ingest → Detect → Normalize |
| `config/clients/mvp_test_30days.yaml` | Config client de test |
| `tests/unit/test_item_id.py` | Tests unitaires canonicalisation URL + calcul item_id |
| `tests/unit/test_raw_store.py` | Tests unitaires RawStore (insert, lookup) |

---

## Séquencement (ordre de livraison)

```
Groupe 1 (datalake core)
        ↓
Groupe 2 (config + canonical) ← en parallèle avec Groupe 1 possible
        ↓
Groupe 3 (ingest RSS) ──────┐
Groupe 4 (detect + normalize) ─┘  ← en parallèle entre eux
        ↓
Groupe 5 (pipeline + smoke test)
```

---

## Mini-sprints prévus

Les numéros exacts sont attribués au démarrage du Niveau 1 (après Phase 2.1). Estimation : **8 mini-sprints, ~8-12h total**.

| ID | Titre | Objectif court | Modèle |
|---|---|---|---|
| L1-S1 | Datalake storage + item_id | `storage.py`, `item_id.py`, tests unitaires | 🟡 Sonnet |
| L1-S2 | Datalake stores + cache | `raw.py`, `curated.py`, `url_cache.py`, tests unitaires | 🟡 Sonnet |
| L1-S3 | Config + Canonical YAML | `config/schemas.py`, loaders, 10 fichiers YAML | 🟡 Sonnet |
| L1-S4 | Ingest fetcher + RSS parser | `fetcher.py`, `parsers/rss.py` | 🟡 Sonnet |
| L1-S5 | Ingest orchestration | `source_runner.py`, `orchestrator.py` | 🟡 Sonnet |
| L1-S6 | Detect gap | `detect/gap.py` | 🟡 Sonnet |
| L1-S7 | Normalize LLM | `llm/base.py`, `llm/anthropic.py`, `orchestrator.py`, `prompts.py`, `parser.py` | 🟡 Sonnet |
| L1-S8 | Pipeline + smoke test | `run_pipeline.py`, test E2E 1 item medincell | 🟡 Sonnet |

> **Règle** : chaque mini-sprint a son fichier dans `docs/sprints/sprint_NNN_*.md` avant d'être exécuté. Les fichiers des sprints L1-S1 à L1-S8 seront créés au fil de l'exécution, pas à l'avance.

---

## Contraintes et principes

- **Pas de filtres actifs** : au Niveau 1, toutes les sources passent le filtre (accept-all). Les filtres LAI keywords / exclusions / période sont dans le code mais désactivés — activés au Niveau 2.
- **1 seule source** : medincell RSS. Les 7 autres sources MVP arrivent au Niveau 2.
- **Tests minimaux** : uniquement sur `item_id` et les stores (cf. CLAUDE.md §8). Pas de couverture exhaustive.
- **Coût LLM** : Sonnet pour la normalisation. Tracker le coût dans `curation_log.jsonl` dès le premier item.
- **Modèle unique par sprint** : tous les L1 sprints en Sonnet (écriture de code).

---

*Niveau 1 — Fondations — plan de palier. Créé lors de Sprint 000.*
