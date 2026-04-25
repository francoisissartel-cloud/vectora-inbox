# Vectora Inbox V1 — Project Status

**Dernière mise à jour** : 2026-04-25 (Claude — Phase 2.0 volet Structure terminé, prêt pour merge)
**Version actuelle du chantier** : Phase 1 cadrage validée. Phase 2.0 prête à exécuter.

> Ce fichier est le **tableau de bord vivant** du projet. À ouvrir en premier quand on arrive sur le projet (Frank ou Claude). Mis à jour à chaque jalon validé.

---

## Vision en 3 phrases

Vectora Inbox V1 est un moteur **local-first** d'alimentation d'un datalake de veille pharmaceutique. Il ingère des sources web (corporate, presse sectorielle, FDA, PubMed) et produit deux dépôts : **raw** (brut) et **curated** (enrichi par l'API Anthropic). Les newsletters/rapports/RAG futurs sont des **consommateurs séparés** du datalake, hors scope V1.

**Premier écosystème ciblé** : Long-Acting Injectables (LAI), avec 8 sources MVP validées.

---

## Où on en est aujourd'hui

**Étape actuelle** : 🔵 Phase 2.0 — Hygiène repo (terminée, en attente merge sur main)
**Statut** : Volets Git et Structure terminés sur la branche `refactor/v1-repo-cleanup`. PR à ouvrir pour merge final sur main.

**Dernier livrable validé** : ✅ Phase 1 — Cadrage complet (25/04/2026)
- Audit du repo existant (`docs/architecture/phase1_audit_pivot_datalake.md`)
- Design canonique du datalake V1.3 (`docs/architecture/datalake_v1_design.md`)
- Plan Phase 2.0 V2.0 (`docs/architecture/phase2.0_repo_structure.md`)
- Règles de travail CLAUDE.md V1.2 (`docs/CLAUDE_v1_proposal.md`)
- Template `.env.example`
- Optimisations différées tracées (`docs/architecture/future_optimizations.md`)
- 10 ADRs des décisions Phase 1 (`docs/decisions/`)

**Prochaine étape immédiate** : Merger la PR Phase 2.0 sur main, puis enchaîner sur Phase 2.1 — Audit nommage canonical
- Vérifier la PR `refactor/v1-repo-cleanup` → main sur GitHub
- Merger la PR (validation Frank)
- Mettre à jour STATUS.md (fin Phase 2.0)
- Enchaîner sur Phase 2.1 (audit nommage exhaustif dans `canonical/`)

---

## Roadmap globale

| # | Jalon | Statut | Date validation | Doc de référence |
|---|---|---|---|---|
| 1 | **Phase 1** — Cadrage et design | ✅ Fait | 25/04/2026 | `docs/architecture/datalake_v1_design.md` |
| 2 | **Phase 2.0** — Hygiène repo | 🔵 Volets Git et Structure faits, en attente merge | - | `docs/architecture/phase2.0_repo_structure.md` |
| 3 | **Phase 2.1** — Audit nommage canonical | ⏸ À venir | - | (à créer en Phase 2.1) |
| 4 | **Niveau 1** — Fondations | ⏸ À venir | - | `datalake_v1_design.md` §13.3 |
| 5 | **Niveau 2** — Cœur | ⏸ À venir | - | `datalake_v1_design.md` §13.4 |
| 6 | **Niveau 3** — Maquillage | ⏸ À venir | - | `datalake_v1_design.md` §13.5 |

**Légende** : ✅ Fait / 🔵 En cours / ⏸ À venir / ⚠️ Bloqué

### Critères de fin par jalon

| Jalon | Critère testable |
|---|---|
| Phase 2.0 | GitHub a uniquement `main` + `archive/legacy-pre-pivot` + tag. Repo local respecte la nouvelle arborescence. |
| Phase 2.1 | Tous les `domain*` / `watch_domain*` / `bedrock*` / `newsletter*` du repo sont renommés ou archivés. Naming cohérent partout. |
| Niveau 1 | `python run_pipeline.py --source press_corporate__medincell` produit 1 item dans raw puis dans curated. |
| Niveau 2 | `python run_pipeline.py --client mvp_test_30days` ingère/normalise les 8 sources LAI. `python onboard_source.py --source X` ajoute proprement une 9e source. |
| Niveau 3 | Rapport hebdo automatique généré. Moteur stable plusieurs semaines sans surveillance. Doc suffisante pour une reprise. |

---

## Décisions architecturales clés (déjà actées)

Chaque décision a son ADR (Architecture Decision Record) dans `docs/decisions/`. Pour comprendre le contexte et les alternatives envisagées, ouvrir l'ADR.

| # | Décision | Date | ADR |
|---|---|---|---|
| 1 | Pivot newsletter → datalake | 24/04 | `001-pivot-newsletter-vers-datalake.md` |
| 2 | Local-first, abandon AWS pour V1 | 24/04 | `002-local-first-abandon-aws.md` |
| 3 | Anthropic API direct (pas Bedrock) | 24/04 | `003-anthropic-api-vs-bedrock.md` |
| 4 | Datalake unique avec tags écosystème | 25/04 | `004-datalake-unique-tags.md` |
| 5 | `item_id = sha256(url canonicalisée + source_key)` | 25/04 | `005-item-id-canonical-url.md` |
| 6 | Format JSONL append-only avec partition mensuelle | 25/04 | `006-format-jsonl-append-only.md` |
| 7 | Cache URL permanent par écosystème | 25/04 | `007-cache-permanent-ecosystem.md` |
| 8 | Construction par paliers (Fondations / Cœur / Maquillage) | 25/04 | `008-construction-par-paliers.md` |
| 9 | Reprise du workflow legacy Discovery + Validation + Promotion | 25/04 | `009-reprise-discovery-validation.md` |
| 10 | Cowork pour cadrage, Claude Code pour code | 25/04 | `010-outils-cowork-vs-claudecode.md` |

---

## Difficultés rencontrées et résolutions

| Date | Difficulté | Résolution |
|---|---|---|
| 25/04 | Lock `.git/index.lock` bloqué — Cowork ne peut pas le manipuler à cause du repo dans OneDrive | Bascule vers Claude Code dans VS Code (Windows natif) — fonctionne. Recommandation long terme : déplacer le repo hors OneDrive. |
| 25/04 | Repo dédié à Claude (`vectora-inbox - claude/`) avait un état partiel : sources `.py` des scripts d'ingestion/discovery/validation manquaient (seulement `.pyc` compilés). Frank avait les `.py` dans son repo principal `vectora-inbox/`. | Récupération via `cp -r` depuis `vectora-inbox/scripts/` vers `scripts/legacy_reference/` du repo de travail. 10 fichiers conservés comme référence à adapter au Niveau 1. |

---

## Backlog "pour plus tard"

Toutes les optimisations consciemment différées sont tracées dans **`docs/architecture/future_optimizations.md`**. Elles sont reprises quand le contexte le justifie (volume, performance, besoin utilisateur).

Récap des principales :
1. Cache : invalidation automatique par signature de filtre
2. Multi-tag écosystème suggéré par le LLM (pour quand 2e écosystème actif)
3. Re-curation lors d'un changement de prompt
4. Parallélisation de l'ingestion / normalisation
5. Migration vers AWS / S3
6. Backend vectoriel pour RAG
7. Politique de retention / purge
8. Scheduler automatique (cron / APScheduler)
9. Dashboard HTML pour stats
10. Repo hors OneDrive (technique)

### Idées en cours de réflexion (non encore décidées)

*(vide pour l'instant)*

---

## Comment naviguer dans le projet

| Tu veux comprendre... | Va voir... |
|---|---|
| L'**architecture** du datalake et du moteur | `docs/architecture/datalake_v1_design.md` |
| Les **règles de travail** Frank ↔ Claude | `CLAUDE.md` (à la racine) |
| Le **plan d'action** en cours d'exécution | Section "Où on en est" ci-dessus |
| Le **mini-sprint en cours** | `docs/sprints/sprint_NNN_*.md` (cf. roadmap) |
| Le **template** pour créer un sprint | `docs/sprints/_TEMPLATE.md` |
| La **mémoire des décisions** prises | `docs/decisions/` |
| Les **optimisations différées** | `docs/architecture/future_optimizations.md` |
| Comment **structurer le repo** | `docs/architecture/phase2.0_repo_structure.md` |
| L'**audit initial** du repo legacy | `docs/architecture/phase1_audit_pivot_datalake.md` |
| Le template des **secrets** | `.env.example` |

---

## Comment ce fichier évolue

**Mis à jour à chaque** :
- Jalon validé par Frank → mise à jour de la roadmap (📋) et de la section "Où on en est"
- Mini-sprint terminé → ajout dans le tableau des sprints récents (à créer)
- Décision architecturale majeure → ajout dans le tableau des décisions + création de l'ADR
- Difficulté rencontrée et résolue → ligne dans le tableau des difficultés
- Idée "pour plus tard" → ajout dans `future_optimizations.md` + mention dans le backlog ci-dessus
- Idée en cours de réflexion → ajout dans la section "Idées en cours de réflexion"

**Responsable de la mise à jour** : Claude, à chaque fin de session ou de jalon. Frank peut éditer librement à tout moment.

**Discipline de résilience** (cf. `CLAUDE.md` §19) : `STATUS.md` est la mémoire externalisée du projet. Si Claude plante, Frank rouvre une nouvelle session, lui demande de lire `STATUS.md` et le sprint en cours, et on reprend.

---

*Project Status V1 — vivant, mis à jour au fil de l'eau.*
