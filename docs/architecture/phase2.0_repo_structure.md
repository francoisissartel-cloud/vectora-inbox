# Phase 2.0 — Structure cible du repo Vectora Inbox V1

**Version** : 1.0
**Date** : 2026-04-24
**Statut** : à valider par Frank

Ce document décrit l'organisation cible du repo après ménage. Il sert de référence pour la Phase 2.1 (ménage) et pour l'avenir.

---

## 1. Pourquoi cette refonte

### État actuel

22 dossiers à la racine. Mélange chronologique de plusieurs époques (V1 newsletter, V2 AWS, V3 datalake) avec du legacy partout. Difficile pour quelqu'un qui arrive de comprendre ce qui est actif vs archivé.

### Objectif

Une racine qui se lit en 30 secondes : **8 dossiers** au lieu de 22, séparation claire entre code, données, scripts, docs, et legacy.

---

## 2. Structure cible

```
vectora-inbox/
├── README.md                         # entrée du projet (à créer)
├── CLAUDE.md                         # règles de travail V1 (à réécrire)
├── VERSION                           # version sémantique
├── .gitignore                        # à ajuster pour V1
├── .env.example                      # template des secrets (à créer)
├── .env                              # secrets réels (gitignored)
├── pyproject.toml                    # dépendances Python (à créer)
│
├── src_vectora_inbox_v1/             # CODE — la nouvelle base V1
│   ├── config/
│   ├── datalake/
│   ├── ingest/
│   ├── normalize/
│   ├── detect/
│   ├── sources/                      # onboarding (discovery + validation)
│   └── stats/
│
├── canonical/                        # GOUVERNANCE MÉTIER (vraie source de vérité)
│   ├── ecosystems/
│   ├── ingestion/
│   ├── parsing/
│   ├── prompts/
│   ├── scopes/
│   └── sources/
│
├── config/
│   └── clients/                      # configs client_id.yaml
│
├── data/                             # PRODUITS DU MOTEUR (gitignored)
│   ├── datalake_v1/                  # le datalake qu'on alimente
│   ├── cache/                        # ex-/cache (caches URL par écosystème)
│   └── runs/                         # ex-/output/runs (manifests des runs)
│
├── scripts/                          # ENTRÉES CLI
│   ├── runtime/                      # run_pipeline, run_ingest, run_normalize
│   ├── onboarding/                   # discover_source, validate_source, promote_source
│   └── maintenance/                  # rebuild_indexes, validate_datalake, etc.
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── docs/
│   ├── architecture/                 # design docs (datalake_v1_design.md, future_optimizations.md)
│   ├── runbooks/                     # procédures opérationnelles ("comment ajouter une source")
│   └── decisions/                    # ADRs légers (Architecture Decision Records)
│
└── archive/                          # TOUT LE LEGACY (commité une fois, figé)
    └── legacy_pre_pivot_20260424/
        ├── src_v3/                   # le code V3 actuel (qu'on n'utilise plus tel quel mais qu'on a inspiré)
        ├── src_v2_snapshot/          # ex-snapshots/snapshot_2026-02-09/src_v2
        ├── backup_code/
        ├── backups/
        ├── build/                    # packages Lambda V1/V2
        ├── contracts/                # contrats Lambda V2
        ├── deployment/
        ├── infra/                    # CloudFormation
        ├── layer_build_temp/
        ├── layer_management/
        ├── monitoring/
        ├── snapshots/
        └── q_context/                # ex-.q-context (règles Q Developer historiques)
```

---

## 3. Justification de chaque choix

### Pourquoi 8 dossiers à la racine ?

Chacun a une responsabilité claire :

| Dossier | Responsabilité |
|---|---|
| `src_vectora_inbox_v1/` | Code source actif (le moteur) |
| `canonical/` | Gouvernance métier (sources, scopes, prompts, écosystèmes) |
| `config/` | Configurations client (qui surveille quoi, avec quels paramètres) |
| `data/` | Tout ce qui est produit au runtime (datalake, cache, manifests de runs) — gitignored |
| `scripts/` | Tous les points d'entrée CLI (ce qu'on tape dans le terminal) |
| `tests/` | Tests unitaires, d'intégration, fixtures |
| `docs/` | Toute la documentation (design, runbooks, décisions) |
| `archive/` | Tout le legacy, dans un dossier daté, pour mémoire |

Si tu rajoutes un dossier à la racine plus tard, demande-toi : **rentre-t-il dans une de ces 8 catégories** ? Si oui, il va dedans. Si non, c'est probablement que tu inventes une nouvelle responsabilité — moment d'en parler.

### Pourquoi rapatrier `cache/` et `output/` sous `data/` ?

Parce que ce sont des **produits du runtime**, pas des configurations ni du code. Ils sont :
- gitignored (jamais commités)
- supprimables et reconstructibles
- évolutifs (le datalake grossit, le cache grossit)

Les regrouper sous `data/` rend explicite ce qui est "produit par le moteur" vs "input du moteur". Et on n'a qu'un seul `.gitignore` à maintenir pour ça.

### Pourquoi sous-diviser `scripts/` ?

Quand tu auras 20 scripts CLI (et tu en auras), savoir lequel est runtime vs onboarding vs maintenance fait gagner du temps :
- `scripts/runtime/` → ce qu'on lance régulièrement (ingestion, normalisation)
- `scripts/onboarding/` → ce qu'on lance occasionnellement (ajouter une source)
- `scripts/maintenance/` → ce qu'on lance rarement (rebuild d'indexes, validation)

### Pourquoi un `archive/` daté commité ?

Parce que tu veux pouvoir revenir voir l'historique des décisions, du code V2/V3, des contrats Lambda — en deux clics, sans `git log`. C'est lourd dans le repo (~50-100 Mo probable), mais c'est commité **une seule fois** : après ce ménage, on n'y touche plus. Le poids ne grossit pas.

Alternative possible : créer un repo `vectora-inbox-archive` séparé pour décharger le repo principal. À considérer si le repo dépasse 200 Mo.

### Pourquoi un `pyproject.toml` ?

C'est le standard moderne Python pour déclarer les dépendances. À la place du vieux `requirements.txt`, il permet de :
- Lister proprement les dépendances (anthropic, requests, beautifulsoup4, feedparser, pyyaml, etc.)
- Définir des dépendances de dev séparées (pytest, black, mypy)
- Configurer les outils (formatter, linter) au même endroit
- Installer le projet en mode développement avec `pip install -e .`

---

## 4. Mouvements de fichiers prévus

### À déplacer (Phase 2.0)

| De | Vers |
|---|---|
| `cache/` | `data/cache/` |
| `output/runs/` | `data/runs/` |
| `output/` autres fichiers | `data/runs/` ou `archive/` selon nature |

### À archiver sous `archive/legacy_pre_pivot_20260424/`

| De | Vers |
|---|---|
| `src_v3/` (entier, après création de `src_vectora_inbox_v1/` qui en récupère le bon) | `archive/.../src_v3/` |
| `backup_code/` | `archive/.../backup_code/` |
| `backups/` | `archive/.../backups/` |
| `build/` | `archive/.../build/` |
| `contracts/` | `archive/.../contracts/` |
| `deployment/` | `archive/.../deployment/` |
| `infra/` | `archive/.../infra/` |
| `layer_build_temp/` | `archive/.../layer_build_temp/` |
| `layer_management/` | `archive/.../layer_management/` |
| `monitoring/` | `archive/.../monitoring/` |
| `snapshots/` | `archive/.../snapshots/` |
| `.q-context/` | `archive/.../q_context/` |
| `AMELIORATION_OUTPUTS_RAPPORT_FINAL.md` | `archive/.../` (rapport ponctuel obsolète) |
| `maintenance_warehouse_stats.py`, `warehouse_maintenance.py` | `archive/.../` (scripts liés à l'ancien Warehouse) |
| `archive/` actuel (s'il existe) | fusionné dans le nouveau `archive/legacy_pre_pivot_20260424/old_archive/` |

### À supprimer purement

| Fichier | Raison |
|---|---|
| `temp_feed.xml`, `temp_rss.xml` | Vides (0 octets), résidus |
| `$null` | Fichier vide créé par accident sous Windows |

### À créer

| Fichier/Dossier | Contenu |
|---|---|
| `README.md` | Présentation du projet, comment l'utiliser |
| `CLAUDE.md` (V1) | Règles de travail V1 (réécriture complète) |
| `.env.example` | Template des secrets |
| `pyproject.toml` | Dépendances Python |
| `data/` | Dossier vide (sera peuplé au runtime) |
| `tests/unit/`, `tests/integration/`, `tests/fixtures/` | Sous-dossiers tests |
| `docs/runbooks/` | Vide pour l'instant, peuplé en Phase 2.4 (Niveau 3) |
| `docs/decisions/` | Vide pour l'instant |
| `scripts/runtime/`, `scripts/onboarding/`, `scripts/maintenance/` | Sous-dossiers scripts |
| `src_vectora_inbox_v1/` | Arborescence vide (peuplée en Phase 2.2 / Niveau 1) |

### À garder intact

- `canonical/` (juste un nettoyage léger des doublons et fusion des variantes — voir Phase 2.1.bis audit nommage)
- `config/clients/` (juste un peu de tri)
- `tests/` (réorganisation interne)
- `.git/`, `.github/`
- `VERSION` (à incrémenter à 1.0.0 au début du Niveau 1)

---

## 5. Plan d'exécution Phase 2.0

Cette phase précède la Phase 2.1 (qui était initialement "ménage"). On la fait en **un seul commit** propre :

1. Créer la nouvelle arborescence vide (`data/`, `tests/unit/`, etc.)
2. Déplacer `cache/` → `data/cache/`, `output/runs/` → `data/runs/`
3. Créer `archive/legacy_pre_pivot_20260424/` et déplacer dedans tous les dossiers legacy listés
4. Supprimer les 3 fichiers résidus (`temp_feed.xml`, `temp_rss.xml`, `$null`)
5. Mettre à jour `.gitignore` pour la nouvelle structure (`data/cache/`, `data/runs/`, `data/datalake_v1/`)
6. Commit unique : `chore(repo): reorganize root structure for V1 — phase 2.0`
7. Push sur une branche `refactor/v1-repo-structure`

À ce stade :
- Aucun code V1 n'est encore écrit
- L'ancien repo est intact dans `archive/`
- La racine est propre, prête pour la suite

**Phase 2.1 (ménage du contenu interne)** vient ensuite : nettoyage de `canonical/` (doublons " - Copie", consolidation des `source_catalog.*.yaml`), nettoyage de `scripts/` (doublons), audit de nommage exhaustif.

---

## 6. Risques et mitigations

| Risque | Probabilité | Mitigation |
|---|---|---|
| Casser des chemins relatifs codés en dur dans des scripts | Moyenne | Tous les scripts qui restent actifs (V3 ingest qu'on va réutiliser) seront passés en revue avant déplacement |
| Le `.gitignore` rate quelque chose dans `data/` | Faible | Vérification explicite avant commit |
| Un fichier important confondu avec du legacy | Faible | Plan de mouvement validé par Frank avant exécution |
| Le repo grossit avec `archive/` commité | Élevée | Acceptée : c'est le but. Si > 200 Mo, on évaluera un repo séparé. |

---

## 7. Validation

À valider par Frank avant exécution. Quand validé, le commit est passé sur la branche `refactor/v1-repo-structure`, je propose la merge sur `main`, Frank accepte ou demande des modifications.
