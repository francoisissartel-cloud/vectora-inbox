# 007 — Cache URL permanent par écosystème (ingested + rejected)

**Statut** : ✅ Accepté
**Date** : 25/04/2026
**Contexte** : Phase 1 cadrage — Frank a insisté sur l'importance du cache après mesure pratique

## Le problème

Le moteur d'ingestion scanne régulièrement les sources web (RSS, HTML) et la majorité des items vus sont du **bruit** (n'ont pas de signal LAI, sont hors période, etc.). Sans cache, chaque run re-fetch et re-process tous ces items, ce qui est très coûteux.

Frank a mesuré sur V3 : **70% d'économie de temps grâce au cache existant**. Sans cache, un scan de 8 sources sur 200 jours peut prendre 5 heures. Avec, quelques minutes.

Question : quelle granularité, quelle politique d'invalidation, quel contenu ?

## Options envisagées

### Pour la granularité

1. **Cache global** : une seule table d'URLs partagée entre tous les clients/écosystèmes
2. **Cache par client** : un cache par client (V3 actuel)
3. **Cache par écosystème** : un cache par écosystème
4. **Cache par source** : un cache par source

### Pour l'invalidation

A. **TTL court** (30 jours) : entrées expirent automatiquement
B. **Cache permanent** : pas d'expiration automatique, rebuild manuel via `--rebuild-cache`
C. **Filter signature** : invalider quand les filtres canoniques changent (signature de hash des YAML de filtres)

### Pour le contenu

X. Cache uniquement des **rejets**
Y. Cache des **rejets ET ingested**

## Les décisions

- **Granularité** : option 3 — cache par écosystème (`data/datalake_v1/_cache/url_cache_{ecosystem_id}.json`)
- **Invalidation** : option B — cache permanent, rebuild manuel (option C différée — `future_optimizations.md` §1)
- **Contenu** : option Y — rejets ET ingested

## Justification

### Granularité par écosystème

- **Cache global** trop agressif : un rejet pour client A peut être un accept pour client B (filtres différents)
- **Cache par client** sous-optimal : deux clients sur le même écosystème (ex: deux clients LAI) ne mutualisent pas
- **Cache par écosystème** : juste milieu. Les filtres canoniques (lai_keywords, exclusions) sont définis au niveau écosystème → les rejets sont valables pour tout client de cet écosystème
- **Cache par source** : trop fragmenté, perd les bénéfices de mutualisation entre sources

### Cache permanent (option B)

Frank a fait un argument décisif : *"95% des items scannés sont du bruit, et c'est coûteux de re-tester (extraction, hash, filtres). Un item qui n'a aucun signal LAI au temps T n'aura quasiment jamais de signal LAI 6 mois plus tard."*

Argument quantitatif :
- TTL 30 jours = invalidation tous les mois → 70% économie perdue chaque mois
- Cache permanent = 70% économie maintenue indéfiniment

Risque (changement de filtres canoniques) traité par règle simple : `--rebuild-cache` après modification de `canonical/scopes/` ou `canonical/ingestion/filter_rules.yaml`. Solution future plus sophistiquée (filter_signature) différée.

### Contenu : rejected ET ingested

- **Cache des rejected** : évite de re-fetcher et re-tester un article rejeté précédemment
- **Cache des ingested** : évite de re-fetcher et re-tester un article déjà dans le datalake. L'index `by_item_id` du raw fait déjà ce travail mais nécessite de fetcher d'abord pour calculer l'item_id. Le cache URL court-circuite avant le fetch.

Bonus du cache `ingested` : permet la **fusion automatique des tags écosystème** lors de re-ingestion par un autre bouquet. L'item existe déjà → on ajoute juste le tag manquant via l'index `by_item_id`.

## Structure d'une entrée du cache

```json
{
  "url_canonical": "https://example.com/article",
  "status": "ingested",  // ou "rejected"
  "item_id": "press_corporate__example__a3f...",  // si ingested
  "rejection_reason": null,  // si rejected : "no_lai_signal" / "out_of_period" / etc.
  "rejection_stage": null,  // "prefetch_filter" / "post_extraction_filter"
  "source_key": "press_corporate__example",
  "first_seen": "2026-04-23T10:14:00Z",
  "last_seen": "2026-04-24T08:45:00Z",
  "scan_count": 12
}
```

## Conséquences

- Un fichier `url_cache_{ecosystem_id}.json` par écosystème dans `data/datalake_v1/_cache/`
- Le cache n'est **pas** versionné Git (gitignored avec le reste de `data/`)
- `client_config.ingestion.use_url_cache: true` (défaut) ou `false` pour désactiver
- Override CLI : `--no-cache` pour ignorer ponctuellement, `--rebuild-cache` pour reconstruire
- Le cache survit aux redémarrages
- Le cache **ne stocke pas** les rejets dépendants du client (période, content_filters min) — re-testés à chaque run, peu coûteux
- Les erreurs transitoires (timeout, 5xx) ne sont pas cachées
- Filter signature comme évolution future tracée dans `future_optimizations.md` §1

## Documents liés

- `docs/architecture/datalake_v1_design.md` §7 (stratégie de cache complète)
- ADR 004 (datalake unique) — pourquoi par écosystème
- ADR 005 (item_id) — clé du cache des ingested
- `future_optimizations.md` §1 (invalidation par filter signature)
