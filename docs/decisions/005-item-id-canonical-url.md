# 005 — Clé de liaison : `item_id` basé sur URL canonicalisée + source_key

**Statut** : ✅ Accepté
**Date** : 25/04/2026
**Contexte** : Phase 1 cadrage — Frank a proposé l'URL comme liant, j'ai proposé une amélioration

## Le problème

Pour relier un item de bout en bout du pipeline (ingest → raw → curated) et pour faire la **gap analysis** (quels items du raw ne sont pas encore dans curated ?), il faut un **identifiant déterministe** stable dans le temps.

Frank a proposé l'URL comme identifiant (intuition naturelle). Mais l'URL brute pose plusieurs problèmes.

## Options envisagées

1. **URL brute** comme `item_id`
2. **URL canonicalisée + source_key**, hashé : `item_id = sha256(source_key + canonical_url)[:16]` (ou format `{source_key}__{hash16}`)
3. **UUID aléatoire** généré à l'ingestion

## La décision

**Option 2 — `item_id` déterministe basé sur l'URL canonicalisée et la source_key.**

Format retenu : `{source_key}__{sha256(canonical_url)[:16]}`.

Exemple : `press_corporate__medincell__a3f1c8d4e5b62a7f`

## Justification

L'option 1 (URL brute) a 4 défauts critiques :
- **Paramètres de tracking** : `?utm_source=rss` change l'URL sans changer le contenu → doublons
- **Fragments** : `#section-contact` change l'URL sans changer le contenu → doublons
- **Case du host** : `Medincell.com` vs `medincell.com` → doublons
- **Slash final** : `/article` vs `/article/` → doublons

Conséquences réelles : le Warehouse V3 actuel contient déjà 21 items, et certains seraient dupliqués si une URL avec/sans `?utm` arrivait deux fois.

L'option 3 (UUID aléatoire) a un défaut majeur : **non déterministe**. Si le moteur réingère un item, il ne sait pas qu'il l'a déjà vu (puisque l'UUID serait différent). On perd la déduplication naturelle.

L'option 2 (canonical URL + hash) résout tout :
- Déterministe : la même URL canonicalisée donne toujours le même hash
- Déduplication automatique : deux URLs avec/sans `utm` → même hash → même item
- Lisible : le préfixe `source_key` rend l'item_id lisible à l'œil
- Stable : pas dépendant du temps ou du run
- Court : 16 chars de hash suffisent pour l'unicité (collision quasi-impossible à notre échelle)

## Règles de canonicalisation URL

Définies dans `canonical/parsing/url_canonicalization.yaml` (à créer en Niveau 1) :

1. **Scheme** : forcer `https` si supporté
2. **Host** : lowercase
3. **Fragment** : retirer (`#...`)
4. **Paramètres de tracking** : retirer `utm_*`, `gclid`, `fbclid`, `mc_cid`, `mc_eid`, `_hsenc`, `_hsmi`, etc.
5. **Trailing slash** : convention "jamais" (sauf racine)
6. **Ordre des paramètres restants** : tri alphabétique pour stabilité

L'URL brute est conservée séparément (`url_raw`) pour audit.

## Conséquences

- L'`item_id` est l'unique clé de liaison entre raw et curated
- L'index `by_item_id` dans raw/ et curated/ permet le lookup O(1)
- La gap analysis devient triviale : `set(raw.item_ids) - set(curated.item_ids)`
- Si un site change ses URLs (rare, mais arrive), les anciens item_id deviennent obsolètes — on accepte ce risque pour le MVP
- Le `content_hash` (hash du contenu) est un champ séparé, utilisé pour détecter qu'un item a changé depuis son passage précédent (mise à jour d'article)

## Documents liés

- `docs/architecture/datalake_v1_design.md` §3.3 (format d'item raw), §5.3 (coordination cache + datalake)
- `src_v3/vectora_core/shared/utils.py` (la fonction `calculate_item_id` existante en V3 — partiellement à reprendre, mais URL non canonicalisée chez elle)
- ADR 004 (datalake unique) — l'item_id permet le multi-tagging d'écosystème
