# Migration Inventory — vectora-inbox → vectora

**Date** : 2026-04-26
**Sprint** : 0.A (Audit pré-migration)
**Auteur** : Claude (Sonnet/Opus selon phases)
**Statut** : 📝 Draft — à valider par Frank

---

## 1. Contexte

Décision actée le 26/04/2026 (à formaliser en ADR-011 pendant le Sprint 0.B) :

- Le projet pivote conceptuellement de "**vectora-inbox**" (générateur de newsletter) vers "**vectora**" (plateforme/moteur de datalake), dont la newsletter LAI ne sera qu'un consommateur aval.
- Création d'un **nouveau repo GitHub `vectora`** plutôt que rebadge en place.
- L'actuel repo `vectora-inbox - claude/` devient une archive historique (lecture seule).
- Le code legacy AWS/Q déjà archivé reste dans l'ancien repo et **ne migre pas**.

Cet inventaire catégorise chaque élément du repo actuel pour décider quoi migrer, quoi laisser, et quoi recréer dans le nouveau repo `vectora`.

---

## 2. Trois catégories

| Catégorie | Sens |
|---|---|
| ✅ **MIGRE** | Le fichier/dossier passe dans le nouveau repo. Adaptation possible (renommages "vectora-inbox" → "vectora") mais le fond ne change pas. |
| 🚫 **RESTE EN ARCHIVE** | Reste dans l'ancien repo `vectora-inbox - claude/`. Frank pourra toujours y référer. Ne migre pas dans Vectora. |
| ❓ **À DISCUTER** | Cas ambigu, à trancher avec Frank avant la migration physique. |
| 🆕 **À CRÉER NEUF** | Pas de migration directe : on rédige un fichier neuf dans le nouveau repo (souvent parce que l'existant est obsolète ou aurait besoin d'une réécriture totale). |

---

## 3. Inventaire par section

### 3.1 Racine du repo

| Élément | Catégorie | Adaptation requise | Notes |
|---|---|---|---|
| `CLAUDE.md` (V1.5) | ✅ MIGRE | Oui — replace "vectora-inbox" → "vectora" partout, adapter §1, §13, version → V1.6 | Cœur des règles de travail. Document vivant. |
| `STATUS.md` | 🆕 À CRÉER NEUF | — | Le STATUS actuel reflète la trajectoire pré-migration. Le nouveau STATUS du repo `vectora` doit refléter l'état post-migration : "ADR-011 acté, Niveau 1 à attaquer". On copie quand même les sections qui restent valables (vision, roadmap, décisions). |
| `README.md` | 🆕 À CRÉER NEUF | — | Le README actuel décrit "Vectora Inbox" comme moteur. Il faut le réécrire pour expliquer "Vectora = plateforme datalake, Vectora Inbox = futur produit aval". |
| `.env.example` | ✅ MIGRE | Non | Template, neutre vis-à-vis du nom. |
| `.gitignore` | ✅ MIGRE | Vérifier | Probablement neutre. À relire avant migration. |
| `.github/PULL_REQUEST_TEMPLATE.md` | ✅ MIGRE | Probablement à adapter | À relire pour vérifier les références "vectora-inbox". |
| `VERSION` (mentionné dans README) | ❓ À DISCUTER | — | Pas trouvé via Glob. Si existant : migrer en `0.0.1`. Si inexistant : à créer. |
| `pyproject.toml` (mentionné dans README) | ❓ À DISCUTER | — | Pas trouvé via Glob. Si existant : migrer avec `name="vectora"`. Sinon : à créer au Niveau 1. |

### 3.2 `canonical/` — Bibliothèque métier (cœur de valeur)

| Élément | Catégorie | Adaptation requise | Notes |
|---|---|---|---|
| `canonical/README.md` | ❓ À DISCUTER → recommandation 🆕 À CRÉER NEUF | — | **OBSOLÈTE** : mentionne "Lambdas", "client-config-examples/", structure qui ne reflète plus la réalité (manquent `parsing/`, `events/`, `ecosystems/`, `prompts/`). Reliquat Q-era. Ma reco : ne pas migrer, le réécrire à partir de zéro dans le nouveau repo. |
| `canonical/ecosystems/lai_ecosystem_definition.yaml` | ✅ MIGRE | Vérifier | Définition de l'écosystème LAI — précieux. |
| `canonical/events/event_type_definitions.yaml` | ✅ MIGRE | Vérifier | Types d'événements pour la normalisation. |
| `canonical/events/event_type_patterns.yaml` | ✅ MIGRE | Vérifier | Patterns associés. |
| `canonical/imports/` (tous fichiers) | ✅ MIGRE | Voir détails ↓ | CSVs et seeds. **Précieux**. |
| → `source-catalog.press.v1.json` | ✅ | Non | Catalogue presse importé. |
| → `technology_tag.csv`, `technology_type.csv`, `technology_family.csv` | ✅ | Non | Taxonomie technologique LAI. |
| → `route_admin.csv` | ✅ | Non | Voies d'administration. |
| → `company_seed_lai.csv` | ✅ | Non | Seed entreprises LAI. |
| → `narrative_topic.csv` | ✅ | Non | Topics narratifs. |
| → `glossary.md`, `LAI_RATIONALE.md` | ✅ | Non | Documentation métier. |
| → `vectora-inbox-lai-core-scopes.yaml` | ✅ MIGRE | **Renommer** → `vectora-lai-core-scopes.yaml` | Le nom contient encore "vectora-inbox". |
| `canonical/ingestion/README.md` | ✅ MIGRE | Vérifier | À relire pour cohérence avec nouveau nom. |
| `canonical/ingestion/ingestion_profiles.yaml` | ✅ MIGRE | Vérifier | Profils d'ingestion. |
| `canonical/parsing/parsing_config.yaml` | ✅ MIGRE | Non | Config de parsing. |
| `canonical/parsing/html_selectors.yaml` | ✅ MIGRE | Non | Sélecteurs HTML pour les sources. |
| `canonical/prompts/normalization/generic_normalization.yaml` | ✅ MIGRE | Non | Prompt de normalisation générique. |
| `canonical/scopes/company_scopes.yaml` | ✅ MIGRE | Non | **Cœur** des listes métier. |
| `canonical/scopes/exclusion_scopes.yaml` | ✅ MIGRE | Non | Filtres anti-bruit. |
| `canonical/scopes/indication_scopes.yaml` | ✅ MIGRE | Non | Indications thérapeutiques. |
| `canonical/scopes/molecule_scopes.yaml` | ✅ MIGRE | Non | Listes de molécules. |
| `canonical/scopes/technology_scopes.yaml` | ✅ MIGRE | Non | Mots-clés technologiques (LAI, etc.). |
| `canonical/scopes/trademark_scopes.yaml` | ✅ MIGRE | Non | Marques commerciales. |
| `canonical/sources/INGESTION_EXPLAINED.md` | ✅ MIGRE | Vérifier | Doc explicative. |
| `canonical/sources/source_candidates.yaml` | ✅ MIGRE | Non | Sources candidates en cours d'évaluation. |
| `canonical/sources/source_catalog.yaml` | ✅ MIGRE | **Bug regex à corriger** (cf. Sprint 003) | Catalogue principal des sources. |
| `canonical/sources/html_extractors.yaml` | ✅ MIGRE | Non | Extracteurs HTML par source. |

**Verdict canonical/** : la quasi-totalité migre. Seul le `README.md` est obsolète (reliquat Q-era avec terminologie "Lambdas") et doit être réécrit.

### 3.3 `docs/` — Documentation

#### 3.3.1 Racine de docs/

| Élément | Catégorie | Notes |
|---|---|---|
| `docs/README.md` | 🆕 À CRÉER NEUF | **OBSOLÈTE** : signature "Amazon Q Developer", date 2025-01-15, réfère à `EXECUTION_SUMMARY.md`, `design/vectora_inbox_engine_lambda.md`, `diagnostics/`, `guides/`, `plans/` qui n'existent plus. Reliquat Q-era oublié au ménage. À réécrire. |

#### 3.3.2 `docs/architecture/`

| Élément | Catégorie | Adaptation |
|---|---|---|
| `datalake_v1_design.md` | ✅ MIGRE | Renommer titre/références "vectora-inbox" → "vectora" + version V1.4 ou V1.5 (au choix) |
| `future_optimizations.md` | ✅ MIGRE | Vérifier références |
| `level_1_plan.md` | ✅ MIGRE | À refondre au Sprint 005 (déjà prévu) |
| `level_2_plan.md` | ✅ MIGRE | Squelette |
| `level_3_plan.md` | ✅ MIGRE | Squelette |
| `audit_brief_opus.md` | ✅ MIGRE | Document historique de l'audit |
| `audit_opus_response_20260425.md` | ✅ MIGRE | Document historique de l'audit (cœur des décisions à venir) |
| `phase1_audit_pivot_datalake.md` | ✅ MIGRE | Trace historique du pivot AWS → local |
| `phase2.0_repo_structure.md` | ✅ MIGRE | Trace historique du ménage repo |
| `naming_audit_phase21.md` | ✅ MIGRE | Trace historique du nommage canonical |
| `migration_inventory.md` | ✅ MIGRE | **Ce document** — à migrer comme trace historique |

#### 3.3.3 `docs/business/`

| Élément | Catégorie | Adaptation |
|---|---|---|
| `contexte_business_v1.md` | ✅ MIGRE | À relire : si focus "newsletter LAI", à élargir pour expliquer la nouvelle hiérarchie Vectora plateforme / Vectora Inbox produit |

#### 3.3.4 `docs/decisions/` (ADRs)

| Élément | Catégorie | Notes |
|---|---|---|
| `README.md` | ✅ MIGRE | Référence "Vectora Inbox V1" ligne 3 → adapter en "Vectora V1" |
| `001-pivot-newsletter-vers-datalake.md` | ✅ MIGRE | Immutable — garder tel quel |
| `002-local-first-abandon-aws.md` | ✅ MIGRE | Immutable |
| `003-anthropic-api-vs-bedrock.md` | ✅ MIGRE | Immutable |
| `004-datalake-unique-tags.md` | ✅ MIGRE | Immutable |
| `005-item-id-canonical-url.md` | ✅ MIGRE | Immutable |
| `006-format-jsonl-append-only.md` | ✅ MIGRE | Immutable |
| `007-cache-permanent-ecosystem.md` | ✅ MIGRE | Immutable |
| `008-construction-par-paliers.md` | ✅ MIGRE | Immutable |
| `009-reprise-discovery-validation.md` | ✅ MIGRE | Immutable |
| `010-outils-cowork-vs-claudecode.md` | ✅ MIGRE | Immutable |

**Note** : la règle "ADR immutable" (CLAUDE.md §16.2) impose de ne pas réécrire le contenu pour cohérence "Vectora". On accepte que les ADRs 001-010 mentionnent "Vectora Inbox V1" (le nom du projet à leur date d'écriture). C'est précisément pour ça que les ADRs sont immutables : ce sont des photos historiques de décisions. La nouvelle ADR-011 ("rebrand vers Vectora") expliquera le glissement.

#### 3.3.5 `docs/runbooks/`

| Élément | Catégorie | Notes |
|---|---|---|
| `move_repo_out_of_onedrive.md` | ❓ À DISCUTER | **Décision potentielle** : si on crée le nouveau repo `vectora` directement à `C:\Users\franc\dev\vectora\`, on **supersede** Sprint 003 et ce runbook. Voir question §4.2 ci-dessous. |
| `.gitkeep` | ✅ MIGRE (implicite) | — |

#### 3.3.6 `docs/sprints/`

| Élément | Catégorie | Notes |
|---|---|---|
| `README.md` | ✅ MIGRE | Adapter ligne 1 : "Vectora Inbox V1" → "Vectora V1" |
| `_TEMPLATE.md` | ✅ MIGRE | Vérifier références au nom du projet |
| `sprint_000_remise_ordre_methodo.md` | ✅ MIGRE | Trace historique d'un sprint exécuté |
| `sprint_001_audit_nommage_canonical.md` | ✅ MIGRE | Trace historique |
| `sprint_002_execution_renommages.md` | ✅ MIGRE | Trace historique |
| `sprint_003_stabilisation_infrastructure.md` | ❓ À DISCUTER | Sprint planifié, en cours — pertinent uniquement si on conserve le déménagement OneDrive séparément. Voir question §4.2. |
| `sprint_004_adrs_et_refonte_design_doc.md` | ❓ À DISCUTER | Sprint planifié — la nouvelle migration vers `vectora` peut potentiellement se substituer au sprint 003 et décaler 004/005. |
| `sprint_005_refonte_plans_et_claudemd.md` | ❓ À DISCUTER | Idem |

### 3.4 `src_vectora_inbox_v1/` — Squelette de code

| Élément | Catégorie | Action |
|---|---|---|
| Le dossier entier (juste `.gitkeep` partout) | ✅ MIGRE | **Renommer** `src_vectora_inbox_v1/` → `src_vectora/` (ou `src_vectora_v1/` selon préférence Frank). Sous-dossiers `config/`, `datalake/`, `detect/`, `ingest/`, `normalize/`, `sources/`, `stats/` conservés à l'identique. |

### 3.5 `scripts/`

| Élément | Catégorie | Notes |
|---|---|---|
| `scripts/maintenance/.gitkeep`, `scripts/onboarding/.gitkeep`, `scripts/runtime/.gitkeep` | ✅ MIGRE | Squelette à conserver |
| `scripts/legacy_reference/` (60+ fichiers V3) | ✅ MIGRE | **Validé par documentation** : le `scripts/legacy_reference/README.md` indique explicitement que ce code est conservé comme référence fonctionnelle pour Niveaux 1 et 2. Cette intention reste valable dans le nouveau repo. À supprimer une fois Niveau 2 stable. |

### 3.6 `tests/`

| Élément | Catégorie | Notes |
|---|---|---|
| Squelette V1 : `tests/__init__.py`, `tests/unit/__init__.py`, `tests/unit/.gitkeep`, `tests/integration/.gitkeep`, `tests/fixtures/.gitkeep` | ✅ MIGRE | Structure cible du Niveau 1 |
| `tests/README.md` | ❓ À DISCUTER | À relire : si Q-era → réécrire, sinon migrer |
| Tests V2/V3 (tous les `test_*.py` à la racine et dans `unit/`, `integration/`, `local/`, `warehouse/`) | 🚫 RESTE EN ARCHIVE | Tests legacy : Bedrock, V2, V3, watch_domain, etc. Ne sont pas valables pour V1 (paradigme différent). On repart de zéro au Niveau 1. |
| `tests/contexts/`, `tests/data_snapshots/`, `tests/payloads/`, `tests/utils/`, `tests/events/`, `tests/local/`, `tests/warehouse/` | 🚫 RESTE EN ARCHIVE | Artefacts V2/V3 obsolètes |
| `tests/__pycache__/`, `*.cpython-*.pyc` | 🚫 RESTE EN ARCHIVE (et gitignore les exclura de toute façon) | — |

### 3.7 `data/`

| Élément | Catégorie | Notes |
|---|---|---|
| `data/cache/.gitkeep`, `data/datalake_v1/.gitkeep`, `data/runs/.gitkeep` | ✅ MIGRE | Squelette gitignored, à conserver. **Renommer** `datalake_v1/` ? À discuter si on veut versionner. Recommandation : garder `datalake_v1/` (le V1 est un palier, pas une référence au nom de projet). |

### 3.8 `archive/`

| Élément | Catégorie | Notes |
|---|---|---|
| `archive/legacy_pre_pivot_20260425/` (massif legacy AWS/Q, build artifacts, lambda layers, botocore, etc.) | 🚫 RESTE EN ARCHIVE | Reste dans l'ancien repo `vectora-inbox - claude/` (lui-même devenu archive). Ne migre pas. |
| `archive/canonical_v2_matching/` | 🚫 RESTE EN ARCHIVE | Idem |

### 3.9 Git

| Élément | Catégorie | Notes |
|---|---|---|
| `.git/` (historique) | 🚫 RESTE EN ARCHIVE | Le nouveau repo `vectora` aura son propre historique git neuf. Premier commit : `chore(repo): initial scaffolding for vectora v1`. |

---

## 4. Cas particuliers à trancher

### 4.1 Renommages systématiques requis lors de la migration

Lors de la copie des fichiers vers le nouveau repo, les remplacements suivants sont à appliquer (revue manuelle nécessaire pour éviter les remplacements abusifs) :

| Avant | Après | Périmètre |
|---|---|---|
| `vectora-inbox` (avec tiret) | `vectora` ou `vectora-inbox` selon contexte | Voir nuance ci-dessous |
| `Vectora Inbox V1` | `Vectora V1` | Titres, références au projet |
| `vectora_inbox_v1` (snake_case) | `vectora` ou `vectora_v1` (à choisir) | Modules Python, dossiers |
| `src_vectora_inbox_v1/` | `src_vectora/` | Dossier source |

**Nuance importante** : "Vectora Inbox" sera **conservé** comme nom du *futur produit aval* (newsletter). Donc tous les remplacements ne sont pas mécaniques. Quand on parle :
- de la **plateforme/moteur/repo** → `vectora`
- du **futur produit newsletter** (verticale LAI puis autres) → `Vectora Inbox`

→ Validation Frank requise sur ce point. Cf. question Q1 ci-dessous.

### 4.2 Sprint 003 (sortie OneDrive) — superseder ou enchaîner ?

**Contexte** : `STATUS.md` indique qu'on est en **Sprint 003 en cours**, dont le but est de déplacer le repo de OneDrive vers `C:\Users\franc\dev\vectora-inbox-claude\`. Avec la décision de migrer vers Vectora, on a deux options :

**Option α — Superseder Sprint 003** : on saute la sortie OneDrive du repo actuel (qui devient archive de toute façon), et on crée directement le nouveau repo `vectora` à `C:\Users\franc\dev\vectora\` (déjà hors OneDrive). Le runbook `move_repo_out_of_onedrive.md` est adapté (ou copié) pour décrire la **création** du nouveau repo hors OneDrive. Sprint 003 devient "obsolète, superseded by Sprint 006 (migration vers Vectora)".

**Option β — Enchaîner** : on finit Sprint 003 (déménagement de l'ancien repo hors OneDrive), puis on enchaîne sur la migration Vectora. Plus long, mais plus prudent.

**Recommandation Claude** : **Option α**. L'ancien repo va devenir lecture-seule, donc le déplacer hors OneDrive a peu de valeur. Mieux vaut investir l'effort dans la migration Vectora directement (vers un chemin propre hors OneDrive). Cela économise un demi-sprint et évite une étape intermédiaire qui ne sert plus à rien.

→ **Question Q2 pour Frank** ci-dessous.

### 4.3 Sprints 004 et 005 (déjà planifiés)

**Sprint 004** : ADRs 011-015 + refonte `datalake_v1_design.md` V1.5
**Sprint 005** : Refonte `level_1_plan.md` V2 + CLAUDE.md V1.6

Ces deux sprints restent **pertinents** post-migration, juste à renommer/recadrer dans le nouveau repo. ADR-011 (déjà prévu pour SQLite) doit être réordonné si on veut que ADR-011 soit "pivot vers Vectora" (mon avis : oui — c'est la décision la plus structurante). Renumérotation possible : ADR-011 = pivot Vectora, ADR-012 = SQLite, ADR-013 = CLI Typer, etc.

→ **Question Q3** : on renumérotage ou on garde 011 = SQLite et on met le pivot en ADR-016 ? Mon avis : renuméroter (ADR-011 = pivot Vectora) parce que les ADRs 011-015 ne sont pas encore écrites, donc aucune référence externe à casser.

### 4.4 Documents à créer neufs dans le nouveau repo

| Document | Pourquoi |
|---|---|
| `README.md` | Le README actuel est trop centré "newsletter LAI". Le nouveau doit refléter Vectora plateforme + Vectora Inbox produit aval. |
| `STATUS.md` | Nouvel état initial post-migration. Tableau de roadmap remis à plat (les sprints exécutés sur l'ancien repo restent référencés en historique). |
| `docs/README.md` | L'actuel est obsolète Q-era. Réécrire. |
| `canonical/README.md` | L'actuel est partiellement obsolète (mentionne Lambdas, structure incorrecte). Réécrire en cohérence avec la réalité du dossier. |
| `docs/decisions/011-pivot-vectora-inbox-vers-vectora.md` | ADR qui acte la décision actuelle (à rédiger en Sprint 0.B). |

### 4.5 Documents à actualiser pendant la migration

Lors de la copie, ces fichiers nécessitent une révision sémantique (pas juste un find/replace) :

- `CLAUDE.md` : mettre à jour §1 (vision), §13 (outils), §15 (coûts), bumper la version à V1.6
- `docs/architecture/datalake_v1_design.md` : titre, §0 contexte, références
- `docs/business/contexte_business_v1.md` : élargir au cadrage Vectora plateforme
- `.github/PULL_REQUEST_TEMPLATE.md` : à relire

---

## 5. Questions ouvertes pour Frank

| # | Question | Recommandation Claude |
|---|---|---|
| **Q1** | Confirmes-tu la nuance "Vectora" (plateforme/moteur/repo) vs "Vectora Inbox" (futur produit newsletter aval) ? | Oui, c'est cohérent avec ton message initial du 26/04 |
| **Q2** | Sprint 003 (sortie OneDrive) : Option α (superseder, on va direct sur le nouveau repo Vectora hors OneDrive) ou Option β (enchaîner) ? | **Option α** — économie d'un demi-sprint, ancien repo en lecture-seule de toute façon |
| **Q3** | Renumérotation ADRs 011+ pour mettre la décision Vectora en ADR-011 ? | **Oui** — aucun ADR 011-015 écrit pour l'instant, renumérotation indolore |
| **Q4** | `src_vectora_inbox_v1/` → renommer en `src_vectora/` ou `src_vectora_v1/` ? | **`src_vectora/`** — plus propre, le V1 est un palier interne, pas un composant du nom |
| **Q5** | `scripts/legacy_reference/` (60 fichiers Q V3) : on migre ou on laisse dans l'ancien repo ? | **Migre** — déjà documenté comme référence active pour Niveaux 1-2. À supprimer une fois Niveau 2 stable. |
| **Q6** | Tous les ADRs 001-010 mentionnent "Vectora Inbox V1". Règle d'immutabilité dit de ne pas les réécrire. Tu valides qu'on les migre tels quels ? | **Oui** — c'est précisément le rôle des ADRs : photographier une décision à un instant T, avec son vocabulaire d'époque |
| **Q7** | Nom du repo GitHub : `vectora` (privé) ou `vectora-platform`, `vectora-engine`, `vectora-core`, autre ? | **`vectora`** — court, mémorable, racine pour des éventuels `vectora-inbox`, `vectora-rag`, etc. |
| **Q8** | Chemin local cible : `C:\Users\franc\dev\vectora\` ? | Oui, hors OneDrive, cohérent avec la décision Sprint 003 |
| **Q9** | On garde `archive/canonical_v2_matching/` dans l'ancien repo ou on le supprime carrément ? | **Garde dans ancien repo** (qui devient archive) — coût zéro |
| **Q10** | Une fois la migration faite, l'ancien repo `vectora-inbox - claude/` : on le tag `archive-pre-vectora`, on le rend lecture-seule sur GitHub, on le supprime ? | **Tag + lecture-seule** (garder GitHub privé en archive). Pas de suppression — coût zéro et précieux pour mémoire. |

---

## 6. Plan de migration physique (esquisse, pour Sprint 0.B/0.C)

Si Frank valide cet inventaire, le sprint de migration physique se décomposera en :

1. **ADR-011** : Rédaction de la décision (Sprint 0.B, ~30 min, modèle Sonnet)
2. **Création repo GitHub `vectora`** privé + clone local à `C:\Users\franc\dev\vectora\` (~15 min, Frank depuis VS Code)
3. **Migration des fichiers MIGRE** avec adaptations (~1-2h, modèle Haiku/Sonnet selon nature)
   - Phase A : structure squelette (dossiers vides + .gitkeep)
   - Phase B : canonical/ (le plus précieux, en premier après squelette)
   - Phase C : docs/ (decisions + architecture + sprints)
   - Phase D : CLAUDE.md adapté + .env.example + .gitignore + .github/
   - Phase E : scripts/legacy_reference/ (gros volume, en dernier)
4. **Création des fichiers neufs** (~1h, modèle Sonnet)
   - README.md
   - STATUS.md (initial)
   - docs/README.md
   - canonical/README.md
5. **Premier commit + push** (Frank depuis VS Code) :
   - `chore(repo): initial scaffolding for vectora v1`
6. **Tag + lecture-seule de l'ancien repo** sur GitHub
7. **Mise à jour finale du STATUS.md** dans Vectora pour refléter "post-migration, prêt à attaquer le Niveau 1"

**Estimation totale** : 3-4h de travail effectif, étalé sur 1-2 sessions.

---

## 7. Volumes (ordre de grandeur)

| Section | Fichiers à migrer | Volume estimé |
|---|---|---|
| Racine | 4-6 | ~50 KB |
| `canonical/` | ~30 | ~500 KB |
| `docs/` | ~30 | ~1 MB |
| `src_vectora_inbox_v1/` (squelette) | ~10 (.gitkeep) | <1 KB |
| `scripts/legacy_reference/` | 60+ | ~500 KB |
| `tests/` (squelette V1 uniquement) | ~5 (.gitkeep) | <1 KB |
| `data/` (squelette gitignored) | ~3 (.gitkeep) | <1 KB |
| **Total** | **~140 fichiers** | **~2 MB** |

À comparer avec le repo actuel qui pèse ~150 MB (dominé par `archive/legacy_pre_pivot_20260425/` avec ses lambda layers et botocore data).

---

## 8. Bilan

**Verdict global** : la migration est **réalisable et de coût modéré**. La quasi-totalité de la valeur ajoutée des 2 derniers mois (canonical, docs, ADRs, sprints) migre proprement. Les coûts identifiés sont :
- ~3-4h de travail effectif
- Validation Frank sur 10 questions ouvertes
- 4 documents à réécrire (README, STATUS, docs/README, canonical/README)

**Bénéfice attendu** :
- Nom et vocabulaire alignés sur la nature réelle du projet
- Repo propre, sans legacy AWS/Q parasite
- Historique git neuf, lisible
- Mémoire historique préservée (ancien repo en archive)

---

## 9. Prochaines étapes (séquence proposée)

1. **Frank valide** ou amende cet inventaire (en particulier les 10 questions de §5)
2. **Claude rédige Sprint 0.B** : `docs/sprints/sprint_006_migration_vers_vectora.md` avec plan détaillé d'exécution
3. **Claude rédige ADR-011** : `docs/decisions/011-pivot-vectora-inbox-vers-vectora.md`
4. **Frank valide Sprint 0.B + ADR-011**
5. **Sprint 0.C — Exécution de la migration** (3-4h, à étaler sur 1-2 sessions)
6. Reprise du fil : Sprints équivalents 004 et 005 (refondus dans Vectora) avant Niveau 1

---

*Migration Inventory V1 — 2026-04-26 — à valider par Frank.*
