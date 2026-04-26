# 011 — Renommage et nouveau repo : `vectora-inbox` → `vectora`

**Statut** : ✅ Accepté
**Date** : 26/04/2026
**Contexte** : Phase de mise à niveau pré-Niveau 1 — ajustement du nom et du repo après stabilisation de la vision via les ADRs 001-010 et l'audit Opus du 25/04/2026

## Le problème

Le projet a connu un pivot conceptuel structurant le 24/04/2026 (ADR-001) : le moteur ne produit plus de newsletter, il alimente un datalake. Les consommateurs (newsletter, rapports, RAG) deviennent des produits **aval**, séparés.

Le nom du projet — **Vectora Inbox** — n'a pas été révisé à ce moment-là. Or :

1. **"Inbox"** évoque une boîte de réception, une consommation d'items prêts à lire. C'est cohérent avec un produit *newsletter*, mais incohérent avec un *moteur de datalake*.
2. La hiérarchie produit attendue est en réalité : **plateforme datalake → produits aval (newsletter, rapports, RAG…)**. Le nom "Vectora Inbox" devrait désigner *un* de ces produits aval (la verticale newsletter), pas la plateforme.
3. À chaque commit, doc, ADR ou conversation, le nom "Vectora Inbox" continue à induire en erreur sur la nature du projet.
4. Le repo actuel `vectora-inbox - claude/` (créé le 25/04/2026 comme dépôt de travail Cowork) est encore lourd de l'archive legacy AWS/Q (~150 Mo) et porte un historique git lié au pivot. Cette charge mentale et technique va peser sur le Niveau 1 et au-delà.

Le moment est doublement opportun :
- Avant le Niveau 1, **aucun code productif V1 n'existe** (squelette de dossiers vides uniquement). Le coût d'un changement de nom et de repo est minimal *maintenant*, et croît rapidement à mesure que le code arrive.
- Le Sprint 003 prévoyait déjà de sortir le repo de OneDrive, donc le déménagement physique du repo était déjà planifié.

## Options envisagées

1. **Status quo** — garder le nom `vectora-inbox` et le repo actuel, documenter mentalement le décalage de vocabulaire.
2. **Rename in place** — renommer le repo GitHub `vectora-inbox` → `vectora`, restructurer le contenu en local, garder l'historique git.
3. **Nouveau repo `vectora`** — créer un repo neuf, migrer uniquement ce qui a de la valeur (canonical, docs, ADRs, sprints, squelette), laisser l'archive legacy et l'historique pollué dans l'ancien repo qui devient lecture-seule.

## La décision

**Option 3 — Création d'un nouveau repo GitHub `vectora` (privé) à `C:\Users\franc\dev\vectora\`, avec migration sélective.**

L'ancien repo `vectora-inbox - claude/` est tagué `archive-pre-vectora` et passe en lecture-seule sur GitHub. Il n'est ni supprimé ni détruit : il sert de mémoire historique consultable.

**Conséquence sur le vocabulaire** :
- **Vectora** = la plateforme / le moteur de datalake / le repo (ce qu'on construit)
- **Vectora Inbox** = un *produit aval* à venir, vertical newsletter LAI (à construire plus tard, dans un projet séparé qui consomme le datalake `vectora`)

**Conséquence sur le repo cible** :
- Nom GitHub : `vectora` (privé)
- Chemin local : `C:\Users\franc\dev\vectora\` (déjà hors OneDrive)
- Dossier source Python : `src_vectora/` (sans suffixe de version dans le nom — la version vit dans `VERSION`, les tags git, et les en-têtes de doc)

**Conséquence sur le séquencement** :
- Le Sprint 003 (sortie OneDrive de l'ancien repo) est **superseded** par le Sprint 006 (migration vers Vectora) : on saute le déménagement intermédiaire et on crée directement le nouveau repo au bon endroit.
- Les Sprints 004 et 005 (ADRs 011-015 + refonte design + plans + CLAUDE.md V1.6) restent valables mais sont **renumérotés et exécutés dans le nouveau repo**.
- L'ADR-011 prévue initialement pour SQLite devient ADR-012, l'ADR-012 (CLI Typer) devient ADR-013, etc. L'ADR-011 actuelle (ce document) est la seule à porter ce numéro.

## Justification

- **Cohérence sémantique** : aligner le nom sur la nature réelle du projet supprime une source permanente de confusion. Frank, Claude, et toute personne qui découvrira le projet plus tard auront immédiatement la bonne représentation.
- **Repo propre** : un nouveau repo permet d'écarter d'un coup l'archive legacy (~150 Mo) et l'historique git lié à la phase AWS. Le nouveau repo pèse ~2 Mo, son `git log` est lisible.
- **Coût minimal maintenant** : ~3-4h d'exécution, ~140 fichiers à migrer, valeur ajoutée des 2 derniers mois entièrement préservée (canonical, docs, ADRs, sprints, design doc, audit Opus, runbook OneDrive, scripts/legacy_reference). Aucun code productif à reprendre.
- **Coût explosif après Niveau 1** : une fois le moteur en cours d'écriture, le renommage devient un refactor risqué qui touche tous les fichiers source, les imports Python, les configs, les tests, les chemins du datalake. Plus on tarde, plus c'est cher.
- **Zéro perte de mémoire** : ADRs immutables migrent tels quels, sprints exécutés sont conservés en historique, ancien repo en archive consultable. La traçabilité reste intacte.
- **Préservation de la portabilité produit** : avoir "Vectora" comme racine prépare l'arborescence de produits ultérieure (`vectora-inbox` pour la newsletter, éventuellement `vectora-rag`, `vectora-reports`…), chacun pouvant être un repo séparé qui consomme le datalake `vectora`.

L'option 1 (status quo) a été écartée car elle laisse une dette de clarté permanente. L'option 2 (rename in place) a été écartée car elle conserve l'historique pollué et l'archive legacy lourde — bénéfice marginal pour un coût comparable.

## Conséquences

### Sur le repo

- Création de `https://github.com/<frank>/vectora` (privé) le 26/04/2026 ou peu après
- Clone local à `C:\Users\franc\dev\vectora\`
- Premier commit : `chore(repo): initial scaffolding for vectora v1`
- L'ancien repo `vectora-inbox - claude` est tagué `archive-pre-vectora`, passé en lecture-seule sur GitHub, conservé pour mémoire

### Sur le code et les configs

- `src_vectora_inbox_v1/` → `src_vectora/` (renommage du dossier squelette)
- `canonical/imports/vectora-inbox-lai-core-scopes.yaml` → `canonical/imports/vectora-lai-core-scopes.yaml` (renommage du fichier)
- Aucun autre renommage de fichier dans `canonical/`, `docs/`, `tests/`, `data/`, `scripts/`
- Convention de versionning des noms de fichier (à formaliser dans un sprint dédié post-migration) : pas de version dans les noms de modules/dossiers de code, version uniquement dans les noms de docs de design (`datalake_v1_design.md`) et les structures de données quand elles ont une rupture schéma (`data/datalake_v1/`)

### Sur la documentation

- `README.md` du nouveau repo : réécrit pour refléter la hiérarchie Vectora plateforme / Vectora Inbox produit aval
- `STATUS.md` du nouveau repo : nouvelle baseline post-migration
- `docs/README.md` : réécrit (l'ancien était un reliquat Q-era obsolète)
- `canonical/README.md` : réécrit (l'ancien mentionnait encore "Lambdas" et une structure incorrecte)
- `CLAUDE.md` : adapté de V1.5 vers V1.6 — remplacements "Vectora Inbox V1" → "Vectora V1" + clarification Vectora plateforme / Vectora Inbox produit
- `docs/architecture/datalake_v1_design.md` : adaptations sémantiques + bump de version interne (V1.4 ou V1.5 selon le sprint suivant)
- ADRs 001-010 : migrent **tels quels** (règle d'immutabilité §16.2). Ils mentionnent "Vectora Inbox V1" : c'est le vocabulaire d'époque, photographié à l'instant T de la décision.
- Sprints 000-005 : migrent tels quels comme historique. Sprint 003 est marqué "Superseded by Sprint 006" dans son entête.

### Sur la roadmap

- Sprint 003 (sortie OneDrive) : marqué superseded, archivé tel quel
- Sprint 006 — Migration vers Vectora : nouveau sprint, exécuté sur l'ancien repo (préparation des fichiers à copier) puis dans le nouveau (création + commit initial)
- Sprint 007 (ex-Sprint 004) : ADRs 012-016 (renumérotation des SQLite, CLI Typer, etc.) + refonte design doc — exécuté dans le nouveau repo
- Sprint 008 (ex-Sprint 005) : refonte plans + CLAUDE.md V1.6 — exécuté dans le nouveau repo
- Niveau 1 démarre dans le nouveau repo après Sprint 008

### Sur la portabilité conceptuelle

- Le datalake produit reste un artefact unique tagué (un seul `data/datalake_v1/`). Aucune fragmentation par produit aval.
- Quand le produit *Vectora Inbox* (newsletter LAI) sera construit plus tard, ce sera dans un repo séparé `vectora-inbox` qui consommera le datalake `vectora`.
- D'autres produits aval éventuels (`vectora-rag`, `vectora-reports`…) suivront le même pattern.

## Documents liés

- `docs/architecture/migration_inventory.md` (V1, 26/04/2026) : inventaire détaillé fichier par fichier, base d'exécution du Sprint 006
- `docs/sprints/sprint_006_migration_vers_vectora.md` (à créer) : plan d'exécution du sprint de migration
- ADR-001 (24/04) : pivot newsletter → datalake, dont la présente ADR est le prolongement sémantique
- ADR-008 (25/04) : construction par paliers — préserve la séquence Niveau 1 → 2 → 3, juste appliquée dans le nouveau repo
- `CLAUDE.md` §0 : rôle de Claude comme architecte du repo, autorisé à proposer ce type de changement structurant sous validation de Frank
- `STATUS.md` (à mettre à jour post-migration dans le nouveau repo)

---

*ADR-011 — Acceptée le 26/04/2026 par Frank, après inventaire détaillé et validation des 10 questions ouvertes (cf. `migration_inventory.md` §5).*
