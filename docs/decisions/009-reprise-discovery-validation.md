# 009 — Reprise du workflow legacy Discovery + Validation + Promotion

**Statut** : ✅ Accepté
**Date** : 25/04/2026
**Contexte** : Phase 1 cadrage — Frank m'a demandé d'inspecter ses scripts legacy d'onboarding de source

## Le problème

Comment qualifier une nouvelle source avant de la mettre en production ? Sans validation, le moteur risque d'ingérer des données mal extraites (selecteurs CSS qui ne marchent pas, dates mal parsées, contenus vides).

Frank a un workflow legacy V3 qu'il a investi du temps à construire : `scripts/discovery/source_discovery.py` et `source_validation.py`. Il demande si on doit le garder.

## Options envisagées

1. **Abandonner le legacy, repartir de zéro** : redévelopper un workflow d'onboarding V1 from scratch
2. **Reprendre tel quel** : copier/coller le code V3
3. **Reprendre et améliorer** : récupérer les concepts et le code utile, l'intégrer proprement dans la nouvelle architecture V1

## La décision

**Option 3 — Reprendre et améliorer.**

Le workflow Discovery + Validation + Promotion est conservé et réintégré dans `src_vectora_inbox_v1/sources/` (module dédié, distinct du runtime).

## Justification

Après inspection du code V3 (`scripts/discovery/source_discovery.py`, `source_validation.py`, `canonical/sources/source_candidates_v3.yaml`), je trouve :

**Ce qui est solide et à conserver** :
- Workflow à 3 étapes bien pensé : Discovery (analyse auto + recommandation config) → Validation (tests d'extraction + score) → Promotion (passage candidate → validated dans canonical)
- Distinction nette entre 3 niveaux d'engagement : `source_candidates` (à explorer) / `source_configs` validated (ingérables) / `source_catalog` (registre métier propre)
- Score de confiance et statut PASSED/FAILED (≥70) sur la validation
- Tests pertinents : extraction articles, titres, dates, qualité contenu
- Documentation détaillée par source dans `extraction_notes` (Frank a déjà payé le prix d'apprentissage des cas tordus, cf. note Camurus sur le risque des limitations temporelles dans les selectors)

**Ce qu'il faut améliorer** :
- Intégration dans la nouvelle architecture (module `sources/` séparé du runtime, parsers réutilisés depuis `ingest/parsers/`)
- Distinction explicite : Discovery + Validation = onboarding (une fois) vs Health check = monitoring (à chaque run runtime)
- Ajout d'un script `revalidate_all.py` pour la maintenance périodique des sources actives

L'option 1 (zéro) serait gaspilleuse : Frank a investi 8 mois à comprendre les cas tordus de chaque source, ne pas en bénéficier serait absurde.

L'option 2 (tel quel) ne convient pas : le code V3 a des dépendances vers V3 obsolètes, et l'architecture cible (module sources/, abstractions LLM, etc.) requiert une intégration propre.

## Trois concepts à ne pas confondre

Cette décision a clarifié 3 concepts distincts qui étaient mélangés en V3 :

| Concept | Quand | Sortie |
|---|---|---|
| **Discovery** | Une fois, à l'onboarding | Config technique proposée |
| **Validation** | Une fois, après discovery (et après modif) | PASSED/FAILED + score |
| **Health check** | À chaque run d'ingestion | `health.json` mis à jour |

Tous les trois sont nécessaires, aucun ne remplace les autres.

## Conséquences

- Création d'un module `src_vectora_inbox_v1/sources/` (distinct de `ingest/`) avec :
  - `candidates.py` : gestion du backlog `source_candidates.yaml`
  - `discovery.py` : repris/amélioré du legacy
  - `validation.py` : repris/amélioré du legacy
  - `promoters.py` : promotion candidate → validated
  - `revalidator.py` : revalidation périodique (Niveau 3)
- Scripts CLI dédiés : `discover_source.py`, `validate_source.py`, `promote_source.py`, `onboard_source.py`, `list_candidates.py`, `revalidate_all.py`
- Le module `sources/` partage les parsers avec `ingest/` (réutilisation), mais ne touche pas au datalake (sépare onboarding et runtime)
- Au Niveau 1 (Fondations) : pas encore de module sources, on travaille avec des sources déjà validées en V3
- Au Niveau 2 (Cœur) : module sources activé, premier onboarding test d'une 9e source LAI

## Documents liés

- `docs/architecture/datalake_v1_design.md` §6.5 (workflow d'onboarding détaillé)
- `docs/architecture/phase1_audit_pivot_datalake.md` (analyse du legacy V3)
- ADR 008 (paliers) — module sources arrive en Niveau 2
