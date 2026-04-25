# Phase 2.0 — Hygiène complète du repo (Git + structure)

**Version** : 2.0
**Date** : 2026-04-25
**Statut** : à valider par Frank avant exécution
**Précédente version** : V1.0 du 2026-04-24, qui ne couvrait que la structure du repo. Cette version inclut désormais le volet Git (nettoyage GitHub) en plus.

Ce document décrit l'ensemble des opérations à exécuter **avant tout code** pour repartir sur des bases propres : à la fois côté Git (branches GitHub, historique, tags) et côté structure (organisation des dossiers du repo).

---

## 1. Pourquoi cette refonte

### État actuel

**Côté Git / GitHub** :
- 6 vieilles branches actives sur GitHub, héritage de l'époque Q Developer (`fix/v16-corrections-post-e2e-v15`, `governance-setup`, `refactor/unify-matching-dates`, `test/lai-weekly-v13-aws-dev`, `fix/canonical-improvements-e2e-v13`, `fix/matching-domain-definition-v12`)
- 1 branche test récente (`docs/phase1-design`) qui contient les 6 docs Phase 1 à intégrer dans main
- `main` contient l'historique complet legacy (8 mois Q Developer)
- 2 stashs locaux WIP en suspens

**Côté structure du repo** :
- 22 dossiers à la racine, mélange chronologique de plusieurs époques
- Des résidus (`temp_feed.xml`, `$null`, etc.)
- Du legacy AWS (`infra/`, `deployment/`, `monitoring/`, `layer_management/`, `build/`)
- Du code historique (`src_v3/` partiellement obsolète, `backup_code/`, `backups/`, `snapshots/`)

### Objectif

**Côté Git** : un seul repo distant avec uniquement `main` (la nouvelle vision V1) + une branche `archive/legacy-pre-pivot` figée (la mémoire de l'ancien) + un tag `legacy-pre-pivot-20260425` permanent.

**Côté structure** : 8 dossiers à la racine, séparation claire entre code/data/config/scripts/tests/docs/archive, tout le legacy regroupé sous `archive/legacy_pre_pivot_20260425/`.

À la fin de la Phase 2.0, le repo est dans son état **V1 vraiment propre**, prêt pour l'écriture du code (Niveau 1 Fondations).

---

## 2. Volet Git — nettoyage GitHub

### 2.1 Étape Git-1 — Sécuriser l'historique (avant toute destruction)

**Avant** de toucher à quoi que ce soit, on **fige l'état actuel** dans un tag et une branche d'archive. Ainsi rien n'est perdu, quoi qu'on fasse derrière.

```bash
git checkout main
git pull origin main   # s'assurer d'être à jour avec le distant

# Tag permanent sur le commit actuel de main
git tag legacy-pre-pivot-20260425 -m "État du projet juste avant le pivot vers Vectora Inbox V1 (avril 2026)"

# Branche d'archive permanente
git branch archive/legacy-pre-pivot main

# Push tag et branche sur GitHub
git push origin legacy-pre-pivot-20260425
git push origin archive/legacy-pre-pivot
```

**Résultat** : sur GitHub, on a désormais un tag et une branche qui pointent sur l'état pré-pivot. Référence stable, accessible à jamais.

### 2.2 Étape Git-2 — Merger les docs Phase 1 sur main

Les 6 documents de cadrage Phase 1 sont actuellement sur la branche `docs/phase1-design`. On les ramène dans main.

**Modalité retenue** : Pull Request sur GitHub (laisse une trace officielle dans l'historique de qui a mergé quoi, quand).

1. Aller sur `https://github.com/francoisissartel-cloud/vectora-inbox/pulls`
2. "New Pull Request" → Base: `main` ← Compare: `docs/phase1-design`
3. Titre : `docs(architecture): add phase 1 design documents`
4. Description : référence à ce document et au design doc V1.3
5. "Create Pull Request" → "Merge pull request" → "Confirm merge"

**Alternative** (plus rapide, moins traçable) : merge direct depuis Claude Code.

```bash
git checkout main
git merge docs/phase1-design
git push origin main
```

**Résultat** : main contient les 6 docs Phase 1 (datalake_v1_design.md V1.3, future_optimizations.md, phase1_audit_pivot_datalake.md, phase2.0_repo_structure.md V2.0, CLAUDE_v1_proposal.md V1.2, .env.example) en plus de l'ancien contenu legacy.

### 2.3 Étape Git-3 — Supprimer les vieilles branches

À supprimer (Frank a validé la suppression de toutes ces branches) :

| Branche | Raison de suppression |
|---|---|
| `fix/v16-corrections-post-e2e-v15` | Legacy Q Developer V2/V3, contenu obsolète, 2700+ modifs WIP non commitées (perdues volontairement avec le pivot) |
| `governance-setup` | Legacy, gouvernance Q Developer remplacée par CLAUDE.md V1 |
| `refactor/unify-matching-dates` | Legacy, matching/scoring relèvent du newsletter (consommateur), hors scope V1 |
| `test/lai-weekly-v13-aws-dev` | Legacy, tests E2E AWS obsolètes |
| `fix/canonical-improvements-e2e-v13` | Legacy, fixes appliqués déjà mergés ou obsolètes |
| `fix/matching-domain-definition-v12` | Legacy, matching newsletter hors scope V1 |
| `docs/phase1-design` | Mergée dans main à l'étape Git-2, plus utile |

**Suppression locale** :
```bash
git branch -D fix/v16-corrections-post-e2e-v15
git branch -D governance-setup
git branch -D refactor/unify-matching-dates
git branch -D test/lai-weekly-v13-aws-dev
git branch -D fix/canonical-improvements-e2e-v13
git branch -D fix/matching-domain-definition-v12
git branch -D docs/phase1-design
```

**Suppression distante** :
```bash
git push origin --delete fix/v16-corrections-post-e2e-v15
git push origin --delete governance-setup
git push origin --delete refactor/unify-matching-dates
git push origin --delete test/lai-weekly-v13-aws-dev
git push origin --delete fix/canonical-improvements-e2e-v13
git push origin --delete fix/matching-domain-definition-v12
git push origin --delete docs/phase1-design
```

**Résultat** : sur GitHub, il ne reste que `main`, `archive/legacy-pre-pivot`, et le tag `legacy-pre-pivot-20260425`. C'est propre.

### 2.4 Étape Git-4 — Nettoyer les stashs locaux

```bash
git stash list                # voir ce qu'il y a
git stash drop stash@{0}      # supprimer le premier
# (répéter pour chaque stash existant)
```

**Résultat** : plus de WIP en attente sur le poste local. Repo dans un état propre.

---

## 3. Volet structure — réorganisation des dossiers

À ce stade, **main est sur le bon historique Git mais le contenu est encore l'ancien**. On va maintenant le restructurer.

### 3.1 Structure cible

```
vectora-inbox/
├── README.md                         # entrée du projet (à créer)
├── CLAUDE.md                         # règles de travail V1 (CLAUDE_v1_proposal.md déplacé ici)
├── VERSION                           # version sémantique
├── .gitignore                        # à ajuster pour V1
├── .env.example                      # template des secrets (déjà créé)
├── .env                              # secrets réels (gitignored)
├── pyproject.toml                    # dépendances Python (à créer)
│
├── src_vectora_inbox_v1/             # CODE — la nouvelle base V1 (vide pour l'instant)
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
│   ├── runbooks/                     # procédures opérationnelles
│   └── decisions/                    # ADRs légers
│
└── archive/                          # TOUT LE LEGACY (commité une fois, figé)
    └── legacy_pre_pivot_20260425/
        ├── src_v3/
        ├── src_v2_snapshot/
        ├── backup_code/
        ├── backups/
        ├── build/
        ├── contracts/
        ├── deployment/
        ├── infra/
        ├── layer_build_temp/
        ├── layer_management/
        ├── monitoring/
        ├── snapshots/
        ├── q_context/
        └── ancien_CLAUDE_v3.md
```

### 3.2 Justification des choix structurels

**Pourquoi 8 dossiers à la racine ?** Chacun a une responsabilité claire :

| Dossier | Responsabilité |
|---|---|
| `src_vectora_inbox_v1/` | Code source actif (le moteur) |
| `canonical/` | Gouvernance métier (sources, scopes, prompts, écosystèmes) |
| `config/` | Configurations client (qui surveille quoi, avec quels paramètres) |
| `data/` | Tout ce qui est produit au runtime — gitignored |
| `scripts/` | Tous les points d'entrée CLI |
| `tests/` | Tests unitaires, d'intégration, fixtures |
| `docs/` | Toute la documentation (design, runbooks, décisions) |
| `archive/` | Tout le legacy, dans un dossier daté, pour mémoire |

**Pourquoi rapatrier `cache/` et `output/` sous `data/`** : ce sont des **produits du runtime**, pas des configs ni du code. Ils sont gitignored, supprimables, reconstructibles.

**Pourquoi sous-diviser `scripts/`** : facilite la navigation dans 20+ scripts CLI à venir.

**Pourquoi un `archive/` daté commité** : permet de revenir voir l'historique des décisions sans `git log`. Commité une seule fois après ce ménage, ne grossit pas.

**Pourquoi un `pyproject.toml`** : standard moderne Python pour déclarer les dépendances et la configuration des outils (formatter, linter).

### 3.3 Mouvements de fichiers prévus

**À déplacer** :

| De | Vers |
|---|---|
| `cache/` | `data/cache/` |
| `output/runs/` | `data/runs/` |
| `output/` autres fichiers | `data/runs/` ou `archive/` selon nature |
| `docs/CLAUDE_v1_proposal.md` (V1.2) | `CLAUDE.md` (racine, en remplaçant l'ancien) |

**À archiver** sous `archive/legacy_pre_pivot_20260425/` :

| De | Vers |
|---|---|
| `src_v3/` (tout) | `archive/.../src_v3/` |
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
| `CLAUDE.md` (ancien V3) | `archive/.../ancien_CLAUDE_v3.md` |
| `AMELIORATION_OUTPUTS_RAPPORT_FINAL.md` | `archive/.../` |
| `maintenance_warehouse_stats.py`, `warehouse_maintenance.py` | `archive/.../` |
| `archive/` actuel (s'il existe) | fusionné dans le nouveau `archive/legacy_pre_pivot_20260425/old_archive/` |

**À supprimer purement** :

| Fichier | Raison |
|---|---|
| `temp_feed.xml`, `temp_rss.xml` | Vides (0 octets), résidus |
| `$null` | Fichier vide créé par accident sous Windows |

**À créer** :

| Fichier/Dossier | Contenu |
|---|---|
| `README.md` | Présentation du projet, comment l'utiliser |
| `pyproject.toml` | Dépendances Python (vide pour l'instant, sera peuplé en Niveau 1) |
| `data/` | Dossier vide (sera peuplé au runtime) |
| `tests/unit/`, `tests/integration/`, `tests/fixtures/` | Sous-dossiers tests |
| `docs/runbooks/` | Vide pour l'instant, peuplé en Phase 2.4 (Niveau 3) |
| `docs/decisions/` | Vide pour l'instant |
| `scripts/runtime/`, `scripts/onboarding/`, `scripts/maintenance/` | Sous-dossiers scripts |
| `src_vectora_inbox_v1/` | Arborescence vide (peuplée en Niveau 1) |

**À garder intact** (juste un nettoyage léger) :
- `canonical/` (le ménage canonical lui-même est en Phase 2.1.bis : audit nommage)
- `config/clients/` (juste un peu de tri)
- `tests/` (réorganisation interne)
- `.git/`, `.github/`
- `VERSION` (à incrémenter à 1.0.0 au début du Niveau 1)

---

## 4. Plan d'exécution Phase 2.0

L'exécution se fait depuis **Claude Code dans VS Code** (vu que Cowork rencontre des problèmes de permissions sur OneDrive — voir §6).

### Séquence

```
[Volet Git]
  Étape Git-1   Tag + branche d'archive (sécurise l'historique)
        ↓
  Étape Git-2   Merge docs/phase1-design dans main (via PR ou direct)
        ↓
  Étape Git-3   Suppression des vieilles branches (locale + distante)
        ↓
  Étape Git-4   Nettoyage des stashs locaux

[Volet structure — sur une branche dédiée refactor/v1-repo-cleanup]
        ↓
  Étape Struct-1   Création de l'arborescence cible vide (8 dossiers + sous-dossiers)
        ↓
  Étape Struct-2   Création archive/legacy_pre_pivot_20260425/
        ↓
  Étape Struct-3   Déplacements vers archive/legacy_pre_pivot_20260425/
        ↓
  Étape Struct-4   Rapatriement de cache/ et output/ sous data/
        ↓
  Étape Struct-5   Swap CLAUDE.md (ancien → archive, nouveau → racine)
        ↓
  Étape Struct-6   Suppression des fichiers résidus (temp_feed.xml, $null, etc.)
        ↓
  Étape Struct-7   Mise à jour de .gitignore pour la nouvelle structure
        ↓
  Étape Struct-8   Création des fichiers à créer (README.md, pyproject.toml minimal)
        ↓
  Étape Struct-9   Commit unique : chore(repo): phase 2.0 — full hygiene cleanup
        ↓
  Étape Struct-10  Push branche refactor/v1-repo-cleanup
        ↓
  Étape Struct-11  Pull Request → Merge sur main → Suppression de la branche
```

### Points de validation

À chaque transition entre étapes, Claude Code présente :
- Ce qu'il vient de faire
- Ce qu'il s'apprête à faire
- Demande explicite de confirmation pour les actions destructives (suppression de branches, suppression de fichiers, déplacement massif)

Frank valide ou demande des modifications. Aucune destruction sans validation explicite.

### Livrables attendus

1. **GitHub** : repo avec uniquement `main` + `archive/legacy-pre-pivot` + tag
2. **Repo local** : arborescence cible respectée, archive/ correctement peuplé, fichiers résidus supprimés
3. **Documentation** : `CLAUDE.md` V1.2 à la racine (ancien archivé)
4. **Commits** : historique propre, messages conventionnels, traçabilité

---

## 5. Risques et mitigations

| Risque | Probabilité | Mitigation |
|---|---|---|
| Suppression accidentelle de fichiers à conserver | Faible | Plan validé en amont. Archive (pas suppression). Tag de sauvegarde avant tout. |
| Suppression de branches contenant un travail à récupérer | Très faible | Tag `legacy-pre-pivot-20260425` capture l'état avant suppression. Tout commit sur ces branches reste dans l'historique Git. |
| Erreur de chemins relatifs dans des scripts | Moyenne | Aucun script n'est actif en V1 (tous archivés). Les nouveaux seront écrits depuis la nouvelle structure. |
| `.gitignore` rate quelque chose dans `data/` | Faible | Vérification explicite avant commit final. |
| Le repo grossit avec `archive/` commité | Élevée | Acceptée : c'est le but. Si > 200 Mo, on évaluera un repo séparé `vectora-inbox-archive`. |
| Conflit OneDrive pendant l'exécution | Moyenne | Exécution depuis Claude Code dans VS Code (Windows natif). Pause OneDrive recommandée pendant le commit final. |

---

## 6. Note sur l'environnement d'exécution

**Cowork (cette interface)** rencontre des blocages de permissions sur `.git/index.lock` parce que le repo est dans un dossier synchronisé OneDrive et que le sandbox Linux dans lequel Cowork tourne n'a pas le droit de manipuler ces fichiers verrouillés.

**Claude Code dans VS Code** tourne directement sur Windows et n'a pas ce problème. La Phase 2.0 est exécutée intégralement depuis Claude Code.

**À long terme** : il est recommandé de déplacer le repo hors du dossier OneDrive (par exemple vers `C:\Users\franc\Projects\vectora-inbox\`) pour éviter durablement les conflits Git/OneDrive. Ce déplacement est optionnel et indépendant de la Phase 2.0 — il peut se faire à tout moment.

---

## 7. Prochaine étape après Phase 2.0

Une fois Phase 2.0 mergée sur main, le repo est dans son état "V1 propre". On enchaîne avec la **Phase 2.1.bis (audit nommage exhaustif)** qui consolide les conventions de noms (`watch_domains` → `ecosystems`, etc.) sur le contenu de `canonical/` et tout fichier qui n'aurait pas été touché par Phase 2.0.

Puis vient le **Niveau 1 — Fondations** (création du squelette de code dans `src_vectora_inbox_v1/`).

---

## 8. Validation

À valider par Frank avant exécution.

Quand validé, j'exécute la Phase 2.0 depuis Claude Code dans VS Code, en présentant chaque étape pour validation au fil de l'eau. Aucune destruction sans accord explicite.

---

*Fin du document Phase 2.0 V2.0 — prêt pour validation et exécution.*
