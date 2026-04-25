# 004 — Structure du datalake : un seul datalake avec tags écosystème (vs datalakes multiples)

**Statut** : ✅ Accepté
**Date** : 25/04/2026
**Contexte** : Phase 1 cadrage — question soulevée par Frank en réaction à ma proposition initiale

## Le problème

Le datalake doit pouvoir contenir des items appartenant à plusieurs **écosystèmes** thématiques (LAI aujourd'hui, peut-être siRNA, cell therapy, regulatory FDA demain). Comment organiser physiquement le stockage ?

## Options envisagées

1. **Un datalake physique par écosystème** : `data/datalake_v1/tech_lai_ecosystem/raw/`, `data/datalake_v1/tech_sirna_ecosystem/raw/`, etc. Chaque écosystème a ses propres dossiers, indexes, retention.
2. **Un seul datalake avec tags multivalués** : une seule structure, chaque item porte une liste `ecosystems: [...]` qui le tague. Filtrage par écosystème via index `by_ecosystem`.
3. **Hybride** : stockage central + vues par écosystème (matérialisées ou virtuelles)

## La décision

**Option 2 — Un seul datalake avec tags écosystème multivalués.**

## Justification

Frank a soulevé un point décisif : **les requêtes futures seront souvent transversales aux écosystèmes**.

Exemple concret donné par Frank : *"trouver tous les items de type `deal` qui concernent LAI ET siRNA ET cell therapy"*.

Avec datalakes séparés (option 1), cette requête nécessite :
1. Ouvrir 3 datalakes
2. Filtrer chacun par `event_type=deal`
3. Unir + dédupliquer

Avec un datalake unique tagué (option 2) : un seul filtre `event_type=deal AND ecosystem IN [lai, sirna, cell]`. Plus rapide, plus simple, plus honnête architecturalement.

**Autre cas qui tranche pour option 2** : un même item peut appartenir à plusieurs écosystèmes (ex: un FDA label sur un produit LAI hybride avec siRNA). Avec option 1, on doit dupliquer l'item physiquement dans plusieurs datalakes. Avec option 2, on tague avec plusieurs valeurs : `ecosystems: [tech_lai_ecosystem, tech_sirna_ecosystem]`.

L'option 3 (hybride) a été écartée car trop complexe pour un MVP.

## Conséquences

- Structure physique : `data/datalake_v1/raw/items/YYYY/MM/items.jsonl` (et idem pour curated/), partition par mois de publication
- Chaque item porte un champ `ecosystems: List[str]`
- Indexes dédiés `by_ecosystem` dans `raw/indexes/` et `curated/indexes/`
- Retention et purges éventuelles se font par filtre, pas par dossier (légèrement plus complexe à implémenter mais OK pour MVP)
- Stats agrégées par écosystème via les indexes (pas de dossier séparé pour les stats par écosystème)
- Cache URL est par écosystème : `data/datalake_v1/_cache/url_cache_{ecosystem_id}.json` (séparé physiquement, car les filtres canoniques sont par écosystème)

## Tagging d'écosystème — Option A retenue (MVP)

Quand un item est ingéré via un bouquet, il reçoit le(s) tag(s) d'écosystème associé(s) au bouquet (déclaré dans `canonical/sources/source_catalog.yaml`). Si re-ingéré via un autre bouquet (item_id identique), les tags sont fusionnés.

Option B (LLM propose des écosystèmes additionnels lors de la normalisation) différée à plus tard (cf. `future_optimizations.md` §2).

## Documents liés

- `docs/architecture/datalake_v1_design.md` §3 (structure physique), §5 (règles de tagging)
- `future_optimizations.md` §2 (multi-tag par LLM)
- ADR 005 (item_id) — clé de liaison qui rend le multi-tagging possible
