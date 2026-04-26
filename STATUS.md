# Vectora Inbox V1 — Project Status

**Dernière mise à jour** : 2026-04-26 (réconciliation post-Sprint 003 + pivot vers vectora acté en ADR-011)
**Version actuelle du chantier** : Phases 1, 2.0, 2.1 + Sprints 000-003 ✅. Audit Opus ✅. Sprint 0.A audit migration ✅. Sprint 0.B ADR-011 + plan Sprint 006 ✅. Pivot vers nouveau repo vectora validé. Sprint 006 (exécution migration) à attaquer depuis VS Code.

> Ce fichier est le **tableau de bord vivant** du projet. À ouvrir en premier quand on arrive sur le projet (Frank ou Claude). Mis à jour à chaque jalon validé.

---

## Vision en 3 phrases

Vectora Inbox V1 est un moteur **local-first** d'alimentation d'un datalake de veille pharmaceutique. Il ingère des sources web (corporate, presse sectorielle, FDA, PubMed) et produit deux dépôts : **raw** (brut) et **curated** (enrichi par l'API Anthropic). Les newsletters/rapports/RAG futurs sont des **consommateurs séparés** du datalake, hors scope V1.

**Premier écosystème ciblé** : Long-Acting Injectables (LAI), avec 8 sources MVP validées.

**Note de pivot 26/04/2026** : le projet est en cours de renommage vers **Vectora** (la plateforme/moteur de datalake), tandis que **Vectora Inbox** désignera désormais un produit aval (newsletter LAI), construit plus tard dans un repo séparé. La migration physique vers le nouveau repo `vectora` est planifiée en Sprint 006 (cf. ADR-011).

---

## Où on en est aujourd'hui

**Étape actuelle** : ⏸ Sprint 006 — Migration vers nouveau repo vectora (planifié, prêt à exécuter depuis VS Code Claude Code)

**Statut** :
- Sprint 003 ✅ done (26/04) — repo sorti d'OneDrive vers `C:\Users\franc\dev\vectora-inbox-claude\`, bug regex YAML corrigé
- Audit Opus ✅ done (25-26/04) — 9 tensions arbitrées, 5 décisions structurantes prises
- Sprint 0.A ✅ done (26/04) — `migration_inventory.md` produit (140 fichiers catégorisés, 10 questions tranchées)
- Sprint 0.B ✅ done (26/04) — ADR-011 + `sprint_006_migration_vers_vectora.md` rédigés et validés
- Sprint 006 ⏸ — exécution migration physique vers `C:\Users\franc\dev\vectora\`, à faire depuis VS Code

**Pivot du nom (ADR-011, 26/04/2026)** :
- **Vectora** = la plateforme / moteur / repo (ce qu'on construit)
- **Vectora Inbox** = futur produit aval (newsletter LAI), construit plus tard dans un repo séparé qui consommera le datalake vectora
- L'actuel repo `vectora-inbox-claude` deviendra archive lecture-seule (tag `archive-pre-vectora`) après Sprint 006

**Décisions Opus à matérialiser dans le nouveau repo vectora** (ADRs 012-016, à rédiger en Sprint 007) :
1. SQLite pour les indexes + cache (JSONL conservé pour les items) → ADR-012
2. CLI unifiée Typer (au lieu de 20+ scripts) → ADR-013
3. Onboarding source : Validation N2, Discovery N3+, Promotion supprimée → ADR-014
4. Signaux factuels dans le curated (pas de scoring) → ADR-015
5. Pydantic V2 pour tous les modèles → ADR-016
6. Niveau 1 en walking skeleton, source pilote = medincell HTML

**Sprints planifiés (post-pivot Vectora)** :
- **Sprint 006** ⏸ — Migration vers vectora (~3-4h, à exécuter depuis VS Code Claude Code)
- **Sprint 007** ⏸ (ex-Sprint 004) — ADRs 012-016 + refonte `datalake_v1_design.md` V1.5 (~3h, dans le nouveau repo, après Sprint 006)
- **Sprint 008** ⏸ (ex-Sprint 005) — Refonte `level_1_plan.md` V2 + CLAUDE.md V1.6 (~2h30, dans le nouveau repo, après Sprint 007)

**Précédents livrables** :
- ✅ Sprint 0.B (26/04) — ADR-011 + plan Sprint 006
- ✅ Sprint 0.A (26/04) — Inventaire migration (`migration_inventory.md`)
- ✅ Audit Opus (25-26/04) — `audit_opus_response_20260425.md`
- ✅ Sprint 003 (26/04) — Sortie OneDrive + correction bug regex
- ✅ Sprint 002 (25/04) — Renommages Phase 2.1
- ✅ Phase 2.0 (25/04) — Hygiène complète du repo

**Prochaine étape immédiate** : démarrer Sprint 006 (migration vers vectora) en nouvelle session VS Code Claude Code. Plan détaillé dans `docs/sprints/sprint_006_migration_vers_vectora.md`.

---

## Roadmap globale

| # | Jalon | Statut | Date validation | Doc de référence |
|---|---|---|---|---|
| 1 | **Phase 1** — Cadrage et design | ✅ Fait | 25/04/2026 | `docs/architecture/datalake_v1_design.md` |
| 2 | **Phase 2.0** — Hygiène repo | ✅ Fait | 25/04/2026 | `docs/architecture/phase2.0_repo_structure.md` |
| 3 | **Sprint 000** — Remise en ordre méthodologique | ✅ Fait | 25/04/2026 | `docs/sprints/sprint_000_remise_ordre_methodo.md` |
| 4 | **Phase 2.1** — Audit + renommages canonical | ✅ Fait | 25/04/2026 | `docs/sprints/sprint_001_audit_nommage_canonical.md` |
| 5 | **Sprint 002** — Exécution renommages | ✅ Fait | 25/04/2026 | `docs/sprints/sprint_002_execution_renommages.md` |
| 6 | **Sprint 003** — Sortie OneDrive + bug regex | ✅ Fait | 26/04/2026 | `docs/sprints/sprint_003_stabilisation_infrastructure.md` |
| 7 | **Audit Opus** — pré-code V1 | ✅ Fait | 26/04/2026 | `docs/architecture/audit_opus_response_20260425.md` |
| 8 | **Sprint 0.A** — Audit migration vers Vectora | ✅ Fait | 26/04/2026 | `docs/architecture/migration_inventory.md` |
| 9 | **Sprint 0.B** — ADR-011 + plan Sprint 006 | ✅ Fait | 26/04/2026 | `docs/decisions/011-pivot-vectora-inbox-vers-vectora.md` + `docs/sprints/sprint_006_migration_vers_vectora.md` |
| 10 | **Sprint 006** — Migration vers nouveau repo vectora | ⏸ À exécuter (VS Code) | - | `docs/sprints/sprint_006_migration_vers_vectora.md` |
| 11 | **Sprint 007** (ex-004) — ADRs 012-016 + design doc V1.5 | ⏸ Dans vectora | - | À recréer dans nouveau repo |
| 12 | **Sprint 008** (ex-005) — Plans V2 + CLAUDE.md V1.6 | ⏸ Dans vectora | - | À recréer dans nouveau repo |
| 13 | **Niveau 1** — Fondations (walking skeleton, medincell HTML) | ⏸ À venir | - | `docs/architecture/level_1_plan.md` (à passer V2 au Sprint 008) |
| 14 | **Niveau 2** — Cœur | ⏸ À venir | - | `docs/architecture/level_2_plan.md` |
| 15 | **Niveau 3** — Maquillage | ⏸ À venir | - | `docs/architecture/level_3_plan.md` |

**Légende** : ✅ Fait / 🔵 En cours / ⏸ À venir / ⛔ Superseded / ⚠️ Bloqué

---

## Critères de fin par jalon

| Jalon | Critère testable |
|---|---|
| Sprint 006 | Repo `vectora` cloné en `C:\Users\franc\dev\vectora\`, premier commit `chore(repo): initial scaffolding for vectora v1` poussé sur main, ancien repo tagué `archive-pre-vectora` et archivé sur GitHub |
| Niveau 1 | `python run_pipeline.py --source press_corporate__medincell` produit 1 item dans raw puis dans curated |
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
| 5 | item_id = sha256(url canonicalisée + source_key) | 25/04 | `005-item-id-canonical-url.md` |
| 6 | Format JSONL append-only avec partition mensuelle | 25/04 | `006-format-jsonl-append-only.md` |
| 7 | Cache URL permanent par écosystème | 25/04 | `007-cache-permanent-ecosystem.md` |
| 8 | Construction par paliers (Fondations / Cœur / Maquillage) | 25/04 | `008-construction-par-paliers.md` |
| 9 | Reprise du workflow legacy Discovery + Validation + Promotion | 25/04 | `009-reprise-discovery-validation.md` |
| 10 | Cowork pour cadrage, Claude Code pour code | 25/04 | `010-outils-cowork-vs-claudecode.md` |
| 11 | Pivot vectora-inbox → vectora (renommage + nouveau repo) | 26/04 | `011-pivot-vectora-inbox-vers-vectora.md` |

---

## Difficultés rencontrées et résolutions

| Date | Difficulté | Résolution |
|---|---|---|
| 25/04 | Lock `.git/index.lock` bloqué — Cowork ne peut pas le manipuler à cause du repo dans OneDrive | Bascule vers Claude Code dans VS Code (Windows natif). Recommandation long terme : déplacer le repo hors OneDrive (exécuté en Sprint 003). |
| 25/04 | Repo dédié à Claude avait un état partiel : sources .py des scripts d'ingestion/discovery/validation manquaient | Récupération via `cp -r` depuis le repo principal vers `scripts/legacy_reference/`. 10 fichiers conservés comme référence à adapter au Niveau 1. |
| 26/04 | Frank réalise que le nom Vectora Inbox ne correspond plus à la nature du projet (moteur de datalake, pas newsletter) | Décision : pivot du nom (vectora plateforme, Vectora Inbox produit aval futur) + création nouveau repo. ADR-011 + Sprint 006 actés. |
| 26/04 | Session Cowork démarrée par erreur sur la copie OneDrive de l'ancien chemin (au lieu du dev repo). Trois fichiers (migration_inventory, ADR-011, sprint_006) écrits au mauvais endroit. | Fichiers copiés depuis OneDrive vers le dev repo lors du commit 5 du paquet de réconciliation (26/04). VS Code Claude Code a pris le relais. |

---

## Backlog "pour plus tard"

Toutes les optimisations consciemment différées sont tracées dans `docs/architecture/future_optimizations.md`.

Récap des principales :
- Cache : invalidation automatique par signature de filtre
- Multi-tag écosystème suggéré par le LLM
- Re-curation lors d'un changement de prompt
- Parallélisation de l'ingestion / normalisation
- Migration vers AWS / S3
- Backend vectoriel pour RAG
- Politique de retention / purge
- Scheduler automatique (cron / APScheduler)
- Dashboard HTML pour stats

---

## Idées en cours de réflexion (non encore décidées)

- Convention de versionning intelligent dans les noms de fichiers (à formaliser dans un sprint dédié post-migration). Pistes : pas de version dans les noms de modules/dossiers de code, version uniquement dans les noms de docs de design (`datalake_v1_design.md`) et structures de données quand rupture schéma (`data/datalake_v1/`).

---

## Comment naviguer dans le projet

| Tu veux comprendre... | Va voir... |
|---|---|
| La vision business et le contexte produit V1 | `docs/business/contexte_business_v1.md` |
| L'architecture du datalake et du moteur | `docs/architecture/datalake_v1_design.md` |
| Les règles de travail Frank ↔ Claude | `CLAUDE.md` (à la racine) |
| Le plan d'action en cours d'exécution | Section "Où on en est" ci-dessus |
| Le mini-sprint en cours | `docs/sprints/sprint_NNN_*.md` (cf. roadmap) |
| Le template pour créer un sprint | `docs/sprints/_TEMPLATE.md` |
| Quel modèle (Haiku/Sonnet/Opus) utiliser pour quelle tâche | `CLAUDE.md §20` |
| La mémoire des décisions prises | `docs/decisions/` |
| L'audit Opus initial | `docs/architecture/audit_opus_response_20260425.md` |
| L'inventaire de migration vers vectora | `docs/architecture/migration_inventory.md` |
| Le plan d'exécution du Sprint 006 (migration) | `docs/sprints/sprint_006_migration_vers_vectora.md` |
| L'ADR du pivot vers vectora | `docs/decisions/011-pivot-vectora-inbox-vers-vectora.md` |
| Les optimisations différées | `docs/architecture/future_optimizations.md` |
| Le template des secrets | `.env.example` |

---

## Comment ce fichier évolue

Mis à jour à chaque :
- Jalon validé par Frank → mise à jour de la roadmap et de la section "Où on en est"
- Mini-sprint terminé → ligne ajoutée dans les précédents livrables
- Décision architecturale majeure → ajout dans le tableau des décisions + création de l'ADR
- Difficulté rencontrée et résolue → ligne dans le tableau des difficultés
- Idée "pour plus tard" → ajout dans `future_optimizations.md` + mention dans le backlog ci-dessus
- Idée en cours de réflexion → ajout dans la section "Idées en cours de réflexion"

**Responsable de la mise à jour** : Claude, à chaque fin de session ou de jalon. Frank peut éditer librement à tout moment.

**Discipline de résilience** (cf. CLAUDE.md §19) : STATUS.md est la mémoire externalisée du projet. Si Claude plante, Frank rouvre une nouvelle session, lui demande de lire STATUS.md et le sprint en cours, et on reprend.

---

*Project Status V1 — vivant, mis à jour au fil de l'eau.*
