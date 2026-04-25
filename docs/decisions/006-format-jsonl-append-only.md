# 006 — Format de stockage : JSONL append-only avec partition mensuelle

**Statut** : ✅ Accepté
**Date** : 25/04/2026
**Contexte** : Phase 1 cadrage — choix du format physique du datalake

## Le problème

Comment stocker les items du datalake (raw et curated) sur le disque local ? Le choix doit équilibrer simplicité, robustesse, et performance pour les volumes attendus (50-5000 items/mois en LAI).

## Options envisagées

1. **JSONL (un objet JSON par ligne)** dans des fichiers append-only
2. **Parquet** (format colonnaire compressé)
3. **SQLite** (base relationnelle locale)
4. **Un fichier JSON par item**

## La décision

**Option 1 — JSONL append-only, partition par mois de publication (`YYYY/MM/items.jsonl`).**

## Justification

**Pour JSONL (option 1)** :
- **Lisible à l'œil** : on peut `cat`, `grep`, voir le contenu sans outil
- **Robuste** : une ligne corrompue n'invalide pas les autres
- **Append bon marché** : pas de rewrite du fichier, ajout en fin
- **Diffable en git** : pas que le repo principal le commit, mais c'est utile pour les fixtures de test
- **Performance OK** : entre 100 et 100 000 items par partition, scan séquentiel reste rapide
- **Pas de dépendance** : Python lit du JSONL sans aucune lib externe

**Contre Parquet (option 2)** :
- Bibliothèque externe requise (pyarrow, polars, etc.)
- Pas lisible à l'œil sans outil
- Bénéfices (compression, scans rapides) inutiles à notre échelle MVP
- À reconsidérer si on dépasse 100 000 items par fichier (cf. `future_optimizations.md`)

**Contre SQLite (option 3)** :
- Schéma rigide, change avec chaque évolution du format d'item
- Lock contention sur écritures concurrentes
- L'aspect relationnel n'apporte rien : on n'a qu'une table d'items, pas de jointures complexes
- Plus de dépendance qu'utile

**Contre 1 fichier par item (option 4)** :
- Performance désastreuse (millions d'inodes pour rien)
- Difficile à scanner

## Partition par mois de publication

Les items sont placés dans `YYYY/MM/items.jsonl` selon leur **`published_at`** (pas leur date d'ingestion).

Pourquoi par mois et pas par jour ou par an :
- **Par jour** : trop granulaire, milliers de petits fichiers pour rien
- **Par an** : fichiers qui enflent, requêtes temporelles courantes (7 derniers jours, 30 derniers jours) deviennent inefficaces
- **Par mois** : équilibre. À 500 items/mois × 36 mois = 36 fichiers de taille raisonnable.

Cas limite : un item sans `published_at` (rare, normalement filtré) → `UNKNOWN/items.jsonl`, traité manuellement.

## Indexes

Comme JSONL n'a pas de lookup natif rapide, on maintient des **indexes dérivés** en JSON séparés :
- `by_item_id`, `by_source_key`, `by_ecosystem`, `by_date`, etc. dans `raw/indexes/`
- Indexes additionnels dans `curated/indexes/` (`by_event_type`, `by_company_id`, etc.)
- Reconstruction possible via `rebuild_indexes.py` en cas de corruption

## Conséquences

- Pas de dépendance à un format binaire ou à une lib externe pour lire le datalake
- Les fichiers grandissent par append, jamais réécrits
- Exception : enrichissement des tags écosystème lors d'une ré-ingestion (mise à jour ciblée d'une ligne via l'index `by_item_id`) — explicite et contrôlée
- Backup et migration triviales (copie de fichiers)
- **À reconsidérer plus tard** : passage à Parquet si on dépasse 100k items par fichier (cf. `future_optimizations.md`)

## Documents liés

- `docs/architecture/datalake_v1_design.md` §3 (structure physique), §4 (indexes)
- ADR 005 (item_id) — clé des indexes
- `future_optimizations.md` §1 (futurs format/perf)
