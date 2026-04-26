# Sprint 000 — Remise en ordre méthodologique

**Statut** : ✅ Validé
**Palier** : Pré-Niveau 1 (méta — remise en ordre avant les paliers de fonctionnalité)
**Date prévue** : 2026-04-25
**Date effective** : 2026-04-25
**Estimation** : ~1h
**Durée réelle** : ~1h30
**Modèle recommandé** : 🟡 Sonnet (cf. CLAUDE.md §20)
**Justification du modèle** : restructuration de documentation existante, raisonnement structuré nécessaire mais pas d'invention architecturale. Pas Haiku (plus que de la lecture mécanique). Pas Opus (overkill, aucune décision ouverte à trancher).

---

## Objectif

Séparer proprement **l'architecture cible** (qui décrit le quoi/pourquoi, stable) des **plans d'exécution** (qui décrivent le comment, vivants). Aujourd'hui le `datalake_v1_design.md` §13 mélange les deux. On corrige ça avant d'exécuter Sprint 001 (Phase 2.1 audit nommage), pour appliquer concrètement notre format sprint à Sprint 001.

C'est un sprint **méta** : on remet en ordre la documentation elle-même, pour pouvoir avancer proprement sur la suite.

---

## Critère de fin testable

- [ ] `docs/architecture/datalake_v1_design.md` §13 ne contient plus de détails d'exécution. Il renvoie vers les docs dédiés (`level_X_plan.md` et `docs/sprints/`).
- [ ] `docs/architecture/level_1_plan.md` existe et donne la vue d'ensemble du palier Fondations (composants à livrer, séquencement, dépendances, sans détailler chaque sprint individuel — ça vient en cours d'exécution).
- [ ] `docs/architecture/level_2_plan.md` existe avec un squelette minimal (sera étoffé après le Niveau 1).
- [ ] `docs/architecture/level_3_plan.md` existe avec un squelette minimal (sera étoffé après le Niveau 2).
- [ ] `docs/sprints/sprint_001_audit_nommage_canonical.md` existe, suit fidèlement le format de `_TEMPLATE.md`, est prêt à être exécuté.
- [ ] `STATUS.md` est mis à jour : roadmap référence les bons fichiers, table de navigation enrichie.
- [ ] Aucun document ne contredit un autre (cohérence STATUS ↔ design ↔ plans ↔ sprints).
- [ ] Tout est commité avec un message conventionnel et pushé sur la branche en cours.

---

## Tâches détaillées (dans l'ordre d'exécution)

### Étape 1 — Lire le contexte (5 min)
- Lire `STATUS.md`
- Lire `CLAUDE.md` §17, §18, §20 (méthode incrémentale, sprints, modèles)
- Lire `docs/sprints/_TEMPLATE.md` (format à suivre)
- Lire `docs/architecture/datalake_v1_design.md` §13 (la section à refactorer)

**Point de validation 1** ⏸ : faire un point à Frank — *"J'ai lu le contexte, voici ma compréhension de ce qu'il faut faire, voici comment je propose de procéder, est-ce OK ?"*

### Étape 2 — Créer level_1_plan.md (15 min)
Créer `docs/architecture/level_1_plan.md` avec :
- En-tête : objectif, critère de fin du palier (cf. design doc §13.3)
- Vue d'ensemble : composants à livrer (datalake/, ingest/, normalize/, detect/, config/)
- Séquencement par groupes (qui dépend de quoi)
- Liste des **mini-sprints prévus** (sans les détailler — juste un titre et un objectif court chacun)
- Critère de fin : `python run_pipeline.py --client mvp_test_30days --source press_corporate__medincell` produit 1 item curated bout-en-bout

**Point de validation 2** ⏸ : Frank valide la structure du level_1_plan avant de continuer.

### Étape 3 — Créer level_2_plan.md et level_3_plan.md en squelette (5 min)
Squelettes minimaux (ils seront étoffés au moment d'attaquer chaque palier) :
- `docs/architecture/level_2_plan.md` : titre, objectif, critère de fin, "à étoffer après validation Niveau 1"
- `docs/architecture/level_3_plan.md` : idem pour Niveau 3

### Étape 4 — Créer sprint_001 (20 min)
Créer `docs/sprints/sprint_001_audit_nommage_canonical.md` à partir du template `_TEMPLATE.md`.

Contenu :
- **Objectif** : produire un rapport d'audit `docs/architecture/naming_audit_phase21.md` listant toutes les occurrences de vocabulaire à migrer/archiver (`domain`, `watch_domain`, `bedrock`, `newsletter`, `scoring`, `matching`, `lambda`, `aws`, `s3`) + les fichiers `*_v3.yaml` à consolider en `*.yaml`.
- **Modèle recommandé** : 🟢 Haiku (audit mécanique de lecture massive)
- **Critère de fin** : rapport produit, validé par Frank, prêt pour un Sprint 002 d'exécution des renommages.
- **Tâches** : scanner `canonical/`, `config/`, `src_v3/` (s'il reste, sinon les vestiges), produire le rapport selon un format tableau lisible.
- **Note importante** : Sprint 001 = audit uniquement. Le refactor effectif des renommages sera un Sprint 002 distinct.

**Point de validation 3** ⏸ : Frank valide le sprint_001 (objectif, critère, format).

### Étape 5 — Refactorer datalake_v1_design.md §13 (15 min)
Le §13 actuel contient :
- §13.0 Phase 2.0 (avec détail)
- §13.1 Phase 2.1 (avec détail)
- §13.2 Phase 2.1.bis (parfois)
- §13.3 Niveau 1 Fondations (avec détail des composants)
- §13.4 Niveau 2 Cœur (avec détail)
- §13.5 Niveau 3 Maquillage (avec détail)
- §13.6 Vue d'ensemble

À transformer en :
- §13 Plan de transition — vue d'ensemble (court, ~1 page) avec :
  - Tableau des paliers (objectif, critère de fin testable, doc de référence)
  - Référence aux plans détaillés (`docs/architecture/level_X_plan.md`)
  - Référence aux sprints (`docs/sprints/`)
  - **Pas de détail d'exécution** : tout déplacé dans les docs dédiés
- Mention spéciale : Phase 2.0 est historique (déjà exécutée), Phase 2.1 est dans `sprint_001`.

**Point de validation 4** ⏸ : Frank valide le diff du §13 avant que ça soit commité.

### Étape 6 — Mettre à jour STATUS.md (5 min)
- Roadmap : ajouter une colonne "Doc de référence" qui pointe vers `level_X_plan.md` ou `sprint_NNN.md`
- Table de navigation : ajouter `docs/architecture/level_X_plan.md` et `docs/sprints/sprint_NNN_*.md`
- Section "Où on en est" : refléter que Sprint 000 est en cours/fini selon l'avancée

### Étape 7 — Commit + push (5 min)
- Vérification finale : aucun document ne contredit un autre, cohérence globale
- Commit avec message conventionnel :
```
refactor(docs): split execution plans from architecture design

Sprint 000 — séparation entre architecture cible (datalake_v1_design.md)
et plans d'exécution (level_X_plan.md, sprint_NNN.md). Le §13 du design
doc devient une vue d'ensemble courte qui renvoie vers les docs dédiés.

Création de level_1_plan.md, level_2_plan.md, level_3_plan.md
(squelettes pour 2 et 3). Création de sprint_001_audit_nommage_canonical.md
prêt à exécuter.

STATUS.md mis à jour pour refléter la nouvelle structure.
```
- Push sur la branche en cours

**Point de validation 5** ⏸ : avant le push final, Frank valide le diff complet.

### Étape 8 — Bilan et préparation Sprint 001
- Remplir le bilan post-exécution de ce sprint 000
- Confirmer à Frank que Sprint 001 est prêt à être exécuté (avec Haiku cette fois)

---

## Fichiers créés / modifiés / supprimés

**✨ Créés** :
- `docs/architecture/level_1_plan.md`
- `docs/architecture/level_2_plan.md` (squelette)
- `docs/architecture/level_3_plan.md` (squelette)
- `docs/sprints/sprint_001_audit_nommage_canonical.md`

**📝 Modifiés** :
- `docs/architecture/datalake_v1_design.md` (§13 refactoré)
- `STATUS.md` (table de navigation + roadmap)

**🗑️ Supprimés** : aucun

---

## Règles à suivre (références CLAUDE.md)

- §3 (Plan → Validation → Exécution) : valider à chaque point de validation
- §5 (Conventions de code) : N/A (pas de code dans ce sprint)
- §6 (Conventions Git) : commit avec format `refactor(docs): ...`
- §17 (Small batches) : commit en fin de sprint, pas de mélange avec autre chose
- §18 (Plans de mini-sprints) : ce sprint suit lui-même le format
- §20 (Modèles) : Sonnet pour ce sprint

---

## Points de validation par Frank

| # | Quand | Quoi |
|---|---|---|
| 1 | Après lecture du contexte (étape 1) | Validation de la compréhension de la mission |
| 2 | Après création level_1_plan.md (étape 2) | Validation de la structure |
| 3 | Après création sprint_001 (étape 4) | Validation du sprint avant exécution future |
| 4 | Après refactor du design doc §13 (étape 5) | Validation du diff |
| 5 | Avant push final (étape 7) | Validation globale du sprint |

---

## Risques identifiés

| # | Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Perdre du contenu utile en refactorant le §13 | Moyenne | Élevé | Vérifier que tout le contenu détaillé est bien transféré dans les level_X_plan.md ou sprint_NNN.md, rien n'est juste "supprimé" |
| 2 | Incohérence entre STATUS.md et la nouvelle structure | Moyenne | Moyen | Vérifier la cohérence à l'étape 6, point de validation 5 |
| 3 | Sprint_001 mal cadré (manque de précision pour l'exécution) | Faible | Moyen | Frank valide à l'étape 4 (point de validation 3) |
| 4 | Conflit Git si la branche actuelle a des modifs non commitées | Faible | Faible | Vérifier `git status` avant de commencer |

---

## Dépendances

- ADR 008 (construction par paliers) : ✅ accepté
- Phase 2.0 (ménage repo) : ✅ exécutée hier
- CLAUDE.md V1.5 (règles méthodologiques) : ✅ en place
- `docs/sprints/_TEMPLATE.md` : ✅ disponible

Aucune dépendance bloquante.

---

## Bilan post-exécution

### Durée réelle vs estimation
- Estimé : ~1h
- Réel : ~1h30
- Écart : +50% — justifié par l'ajout du tableau config-driven dans `level_1_plan.md` (clarification demandée par Frank en cours de sprint) et le changement de modèle Haiku → Sonnet pour Sprint 001.

### Commits effectués
- `7faf3be` : `docs(workflow): add CLAUDE.md v1.5 section §20 model guidance and Sprint 000 plan` (preamble Cowork)
- `3cf27e1` : `refactor(docs): split execution plans from architecture design` (Sprint 000 exécution)

### Difficultés rencontrées
- Aucune difficulté technique. Un ajustement de contenu en cours de sprint : Frank a précisé que le principe config-driven devait être explicite dans `level_1_plan.md` dès le Niveau 1 — ajouté avec un tableau "qui répond quoi" et l'anti-pattern à éviter.

### Décisions prises en cours de route
- Modèle Sprint 001 : Sonnet (et non Haiku comme prévu initialement). Frank a estimé que la qualification des occurrences nécessite du jugement, pas seulement de la lecture mécanique. Mis à jour dans `sprint_001_audit_nommage_canonical.md`.

### Ce qui reste pour le prochain sprint
- Sprint 001 prêt à exécuter : `docs/sprints/sprint_001_audit_nommage_canonical.md`
- Ouvrir une nouvelle session (nouvelle fenêtre de conversation) avec modèle **Sonnet**
- Lire STATUS.md + sprint_001 → valider le plan → exécuter l'audit

### Validation Frank
- Date de validation : 2026-04-25
- Commentaires éventuels :

---

*Sprint 000 — fin du document.*
