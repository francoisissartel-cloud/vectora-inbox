# Vectora Inbox

Moteur **local-first** d'alimentation d'un datalake de veille pharmaceutique. Ingère des sources web (corporate, presse sectorielle, FDA, PubMed) et produit deux dépôts d'items : un **raw** (brut) et un **curated** (enrichi par l'API Anthropic).

**Premier écosystème ciblé** : Long-Acting Injectables (LAI), 8 sources MVP.

> Le datalake est l'artefact produit. Les newsletters, rapports et RAG futurs sont des **consommateurs séparés**, hors scope V1.

## Documents de référence

| Tu veux comprendre... | Va voir... |
|---|---|
| L'**architecture** du datalake et du moteur | [docs/architecture/datalake_v1_design.md](docs/architecture/datalake_v1_design.md) |
| Les **règles de travail** Frank ↔ Claude | [CLAUDE.md](CLAUDE.md) |
| L'**état du projet** (vivant) | [STATUS.md](STATUS.md) |
| L'**historique des décisions** | [docs/decisions/](docs/decisions/) |

## État actuel

**Phase 2.0 (hygiène repo)** : terminée le 2026-04-24. Le repo est dans son état "V1 propre", prêt à recevoir le code du moteur.

**Prochaine étape** : Niveau 1 — Fondations (squelette de code dans `src_vectora_inbox_v1/`, première ingestion bout-en-bout).

## Structure du repo

```
vectora-inbox/
├── CLAUDE.md                    # règles de travail Frank ↔ Claude
├── STATUS.md                    # tableau de bord vivant
├── README.md                    # ce fichier
├── VERSION                      # version sémantique
├── .env.example                 # template des secrets
├── pyproject.toml               # dépendances Python
├── src_vectora_inbox_v1/        # code source (vide, peuplé en Niveau 1)
├── canonical/                   # gouvernance métier (sources, scopes, prompts)
├── config/clients/              # configs client
├── data/                        # produits du runtime (gitignored)
├── scripts/                     # entrées CLI
├── tests/                       # tests unitaires et d'intégration
├── docs/                        # design, runbooks, ADRs
└── archive/                     # legacy pré-pivot (commit one-shot)
```

## Démarrage

Pas encore de code en V1. Le runbook de démarrage rapide sera dans [docs/runbooks/](docs/runbooks/) au Niveau 2.

---

*Vectora Inbox V1 — pivot datalake local-first, avril 2026.*
