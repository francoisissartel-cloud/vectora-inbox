# Sprint 006 — Migration vers le repo `vectora`

**Statut** : ⏸ Planifié
**Palier** : Mise à niveau pré-Niveau 1 (suite du chantier "audit Opus + ajustements")
**Date prévue** : 26-27/04/2026
**Date effective** : (à remplir à l'exécution)
**Estimation** : ~3-4h de travail effectif, étalé sur 1-2 sessions
**Durée réelle** : (à remplir post-exécution)
**Modèle recommandé** : 🟡 Sonnet
**Justification du modèle** : mix de copy mécanique (Haiku suffirait) + adaptations sémantiques (renommages, réécritures de README) + rédaction de fichiers neufs (README, STATUS, ADR-011). La part adaptative justifie Sonnet.

---

## Objectif

Migrer le projet de l'actuel repo `vectora-inbox - claude/` (qui devient archive lecture-seule) vers un nouveau repo GitHub `vectora` (privé) cloné à `C:\Users\franc\dev\vectora\`. Préserver toute la valeur ajoutée (canonical, docs, ADRs, sprints, design doc, audit Opus, scripts/legacy_reference) en l'adaptant au nouveau vocabulaire. Laisser dans l'ancien repo l'archive legacy AWS/Q et les anciens tests V2/V3.

À la fin du sprint, le nouveau repo `vectora` est cloné, scaffoldé, peuplé, commité sur `main`, et `STATUS.md` y reflète "post-migration, prêt à attaquer Sprint 007 (ex-004)".

---

## Critère de fin testable

- [ ] Le repo `vectora` (privé) existe sur le compte GitHub de Frank
- [ ] Le repo est cloné en `C:\Users\franc\dev\vectora\` et `git status` est propre
- [ ] Le dossier `C:\Users\franc\dev\vectora\` contient une arborescence conforme à la cible (cf. §"Arborescence cible" ci-dessous)
- [ ] Tous les fichiers marqués ✅ MIGRE dans `migration_inventory.md` sont présents dans le nouveau repo, avec les adaptations spécifiées
- [ ] Tous les fichiers marqués 🆕 À CRÉER NEUF dans `migration_inventory.md` sont créés et cohérents
- [ ] L'ADR `docs/decisions/011-pivot-vectora-inbox-vers-vectora.md` est présente dans le nouveau repo (migrée depuis l'ancien)
- [ ] L'ADR-011 est référencée dans le nouveau `STATUS.md`
- [ ] Aucun chemin OneDrive et aucune occurrence "Vectora Inbox V1" n'apparaît dans le nouveau `README.md`, `STATUS.md`, `CLAUDE.md`, `docs/README.md`, `canonical/README.md` (vérifié par grep)
- [ ] Le premier commit `chore(repo): initial scaffolding for vectora v1` est poussé sur `main` du nouveau repo
- [ ] L'ancien repo `vectora-inbox - claude` est tagué `archive-pre-vectora` sur GitHub et passé en lecture-seule (settings GitHub → Archive)
- [ ] L'ancien repo conserve `migration_inventory.md`, ADR-011 et `sprint_006` (puisque tout y est rédigé avant migration) — c'est sa dernière trace utile
- [ ] `pytest --collect-only` (depuis `C:\Users\franc\dev\vectora\`) ne lève pas d'erreur (pas de fichier de test legacy importé)
- [ ] `grep -r "vectora-inbox" C:\Users\franc\dev\vectora\` ne renvoie que les références *intentionnelles* à l'ancien repo (dans ADR-011, dans CLAUDE.md historique éventuel, dans STATUS.md section migration). Aucune référence non historique.

Si toutes les cases sont cochées, le sprint est terminé.

---

## Arborescence cible (`C:\Users\franc\dev\vectora\`)

```
vectora/
├── .env.example                 (migré, vérifié)
├── .gitignore                   (migré, vérifié)
├── .github/
│   └── PULL_REQUEST_TEMPLATE.md (migré, adapté)
├── CLAUDE.md                    (migré, adapté V1.5 → V1.6)
├── README.md                    (NEUF, réécrit pour Vectora plateforme)
├── STATUS.md                    (NEUF, baseline post-migration)
├── canonical/
│   ├── README.md                (NEUF, structure correcte)
│   ├── ecosystems/
│   │   └── lai_ecosystem_definition.yaml
│   ├── events/
│   │   ├── event_type_definitions.yaml
│   │   └── event_type_patterns.yaml
│   ├── imports/
│   │   ├── source-catalog.press.v1.json
│   │   ├── technology_tag.csv
│   │   ├── route_admin.csv
│   │   ├── technology_type.csv
│   │   ├── technology_family.csv
│   │   ├── company_seed_lai.csv
│   │   ├── glossary.md
│   │   ├── LAI_RATIONALE.md
│   │   ├── narrative_topic.csv
│   │   └── vectora-lai-core-scopes.yaml   (renommé : retrait du "-inbox")
│   ├── ingestion/
│   │   ├── README.md            (migré, vérifié)
│   │   └── ingestion_profiles.yaml
│   ├── parsing/
│   │   ├── parsing_config.yaml
│   │   └── html_selectors.yaml
│   ├── prompts/
│   │   └── normalization/
│   │       └── generic_normalization.yaml
│   ├── scopes/
│   │   ├── company_scopes.yaml
│   │   ├── exclusion_scopes.yaml
│   │   ├── indication_scopes.yaml
│   │   ├── molecule_scopes.yaml
│   │   ├── technology_scopes.yaml
│   │   └── trademark_scopes.yaml
│   └── sources/
│       ├── INGESTION_EXPLAINED.md
│       ├── source_candidates.yaml
│       ├── source_catalog.yaml  (correctif bug regex appliqué — cf. note Sprint 003)
│       └── html_extractors.yaml
├── data/                        (gitignored runtime)
│   ├── cache/.gitkeep
│   ├── datalake_v1/.gitkeep
│   └── runs/.gitkeep
├── docs/
│   ├── README.md                (NEUF, propre)
│   ├── architecture/
│   │   ├── audit_brief_opus.md
│   │   ├── audit_opus_response_20260425.md
│   │   ├── datalake_v1_design.md   (migré, adapté terminologie)
│   │   ├── future_optimizations.md
│   │   ├── level_1_plan.md
│   │   ├── level_2_plan.md
│   │   ├── level_3_plan.md
│   │   ├── migration_inventory.md  (migré comme trace historique)
│   │   ├── naming_audit_phase21.md
│   │   ├── phase1_audit_pivot_datalake.md
│   │   └── phase2.0_repo_structure.md
│   ├── business/
│   │   └── contexte_business_v1.md (migré, élargi cadrage)
│   ├── decisions/
│   │   ├── README.md            (migré, ligne 3 adaptée)
│   │   ├── 001-pivot-newsletter-vers-datalake.md
│   │   ├── 002-local-first-abandon-aws.md
│   │   ├── 003-anthropic-api-vs-bedrock.md
│   │   ├── 004-datalake-unique-tags.md
│   │   ├── 005-item-id-canonical-url.md
│   │   ├── 006-format-jsonl-append-only.md
│   │   ├── 007-cache-permanent-ecosystem.md
│   │   ├── 008-construction-par-paliers.md
│   │   ├── 009-reprise-discovery-validation.md
│   │   ├── 010-outils-cowork-vs-claudecode.md
│   │   └── 011-pivot-vectora-inbox-vers-vectora.md  (la décision actuelle)
│   ├── runbooks/
│   │   ├── .gitkeep
│   │   └── (vide — le runbook OneDrive ne migre pas, le repo est déjà hors OneDrive)
│   └── sprints/
│       ├── README.md            (migré, ligne 1 adaptée)
│       ├── _TEMPLATE.md         (migré, vérifié)
│       ├── sprint_000_remise_ordre_methodo.md
│       ├── sprint_001_audit_nommage_canonical.md
│       ├── sprint_002_execution_renommages.md
│       ├── sprint_003_stabilisation_infrastructure.md  (entête modifié : "⏸ Superseded by Sprint 006")
│       ├── sprint_004_adrs_et_refonte_design_doc.md   (entête modifié : "⏸ Renuméroté en Sprint 007")
│       ├── sprint_005_refonte_plans_et_claudemd.md    (entête modifié : "⏸ Renuméroté en Sprint 008")
│       └── sprint_006_migration_vers_vectora.md        (le présent sprint, marqué ✅ Validé après exécution)
├── scripts/
│   ├── legacy_reference/        (migré tel quel, ~60 fichiers V3 référence)
│   ├── maintenance/.gitkeep
│   ├── onboarding/.gitkeep
│   └── runtime/.gitkeep
├── src_vectora/                 (renommé depuis src_vectora_inbox_v1)
│   ├── config/.gitkeep
│   ├── datalake/.gitkeep
│   ├── detect/.gitkeep
│   ├── ingest/.gitkeep
│   ├── normalize/.gitkeep
│   ├── sources/.gitkeep
│   └── stats/.gitkeep
└── tests/
    ├── README.md                (migré ou réécrit selon état actuel)
    ├── __init__.py              (à créer vide ou migré)
    ├── unit/.gitkeep
    ├── integration/.gitkeep
    └── fixtures/.gitkeep
```

**Note** : `archive/` du repo actuel **ne migre pas**. Le nouveau repo n'a pas d'`archive/` jusqu'à ce qu'on en ait besoin.

---

## Tâches détaillées (dans l'ordre d'exécution)

### Phase A — Préparation (Frank, ~15 min, depuis VS Code)

1. Frank crée le repo `vectora` (privé) sur GitHub via l'interface web :
   - Nom : `vectora`
   - Description courte : *"Local-first datalake engine for pharmaceutical intelligence — feeds downstream products (Vectora Inbox newsletter, RAG, reports)."*
   - Visibilité : privé
   - Initialisation : aucune (pas de README, pas de .gitignore, pas de licence — on les ajoute nous-mêmes)
2. Frank ouvre un terminal Windows (PowerShell ou Git Bash) et exécute :
   ```
   cd C:\Users\franc\dev\
   git clone <url-du-nouveau-repo> vectora
   cd vectora
   ```
3. Frank confirme à Claude que le repo est cloné, vide, et que `git status` répond "On branch main / nothing to commit".

⏸ **Validation Frank** : repo cloné, prêt à recevoir le contenu.

### Phase B — Création de la structure squelette (Claude, ~10 min)

4. Claude crée tous les dossiers vides avec leurs `.gitkeep` selon l'arborescence cible :
   - `canonical/`, `canonical/ecosystems/`, `canonical/events/`, `canonical/imports/`, `canonical/ingestion/`, `canonical/parsing/`, `canonical/prompts/normalization/`, `canonical/scopes/`, `canonical/sources/`
   - `data/cache/`, `data/datalake_v1/`, `data/runs/`
   - `docs/`, `docs/architecture/`, `docs/business/`, `docs/decisions/`, `docs/runbooks/`, `docs/sprints/`
   - `scripts/legacy_reference/`, `scripts/maintenance/`, `scripts/onboarding/`, `scripts/runtime/`
   - `src_vectora/`, `src_vectora/config/`, `src_vectora/datalake/`, `src_vectora/detect/`, `src_vectora/ingest/`, `src_vectora/normalize/`, `src_vectora/sources/`, `src_vectora/stats/`
   - `tests/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`
   - `.github/`
5. Vérification visuelle de la structure (Claude liste, Frank valide).

⏸ **Validation Frank** : structure conforme.

### Phase C — Migration `canonical/` (Claude, ~30 min)

6. Claude copie tous les fichiers ✅ MIGRE de `canonical/` depuis l'ancien repo vers le nouveau, à l'exception de :
   - `canonical/README.md` (sera réécrit en Phase F)
   - `canonical/imports/vectora-inbox-lai-core-scopes.yaml` (renommage requis : voir étape 7)
7. Claude copie `canonical/imports/vectora-inbox-lai-core-scopes.yaml` vers le nouveau repo en le **renommant** `canonical/imports/vectora-lai-core-scopes.yaml`.
8. Claude vérifie via grep qu'aucun fichier copié dans `canonical/` ne contient une référence non-historique à "vectora-inbox" qui devrait être adaptée. Liste les occurrences à Frank pour validation au cas par cas (probablement aucune dans les fichiers de données, peut-être dans des commentaires).
9. Optionnel — application du correctif bug regex dans `canonical/sources/source_catalog.yaml` si l'audit Opus l'avait identifié. Si pas certain, on diffère au Sprint 007.

⏸ **Validation Frank** : `canonical/` est complet et cohérent dans le nouveau repo.

### Phase D — Migration `docs/` (Claude, ~45 min)

10. Claude copie tels quels les ADRs 001-010 ainsi que leur `README.md` vers `docs/decisions/`.
11. Claude copie l'ADR-011 (déjà rédigée dans l'ancien repo en Sprint 0.B) vers `docs/decisions/`.
12. Claude copie le `README.md` de `docs/decisions/` et adapte la ligne 3 ("Vectora Inbox V1" → "Vectora V1").
13. Claude copie tous les fichiers de `docs/architecture/` listés ✅ MIGRE dans `migration_inventory.md`. Pour chaque fichier, applique les adaptations sémantiques minimales :
    - `datalake_v1_design.md` : titre + §0 + références
    - autres fichiers : revue rapide pour cohérence terminologique
14. Claude copie `docs/business/contexte_business_v1.md` et le **revoit** : si trop centré "newsletter LAI", élargit l'introduction pour expliquer la hiérarchie Vectora plateforme / Vectora Inbox produit (voir §"Adaptations sémantiques" ci-dessous).
15. Claude copie `docs/sprints/_TEMPLATE.md` et le `README.md`. Adapte le `README.md` ligne 1 ("Vectora Inbox V1" → "Vectora V1").
16. Claude copie les sprints 000, 001, 002 tels quels.
17. Claude copie le sprint 003 et **modifie son entête** pour ajouter au statut : `⏸ Superseded by Sprint 006`. Note ajoutée en début de fichier expliquant le supersedment.
18. Claude copie les sprints 004 et 005 et **modifie leurs entêtes** : statut `⏸ Renuméroté en Sprint 007` et `⏸ Renuméroté en Sprint 008` respectivement, avec note explicative.
19. Claude copie le sprint 006 (le présent) tel quel.
20. Claude **ne copie pas** `docs/runbooks/move_repo_out_of_onedrive.md` — il devient inutile une fois la migration faite (le nouveau repo est déjà hors OneDrive). Mais on garde `docs/runbooks/.gitkeep`.

⏸ **Validation Frank** : `docs/` est complet, ADR-011 référencée correctement.

### Phase E — Migration `scripts/legacy_reference/` et squelettes (Claude, ~20 min)

21. Claude copie tout `scripts/legacy_reference/` (60+ fichiers) tel quel vers le nouveau repo.
22. Claude crée les `.gitkeep` dans `scripts/maintenance/`, `scripts/onboarding/`, `scripts/runtime/`.
23. Claude crée les `.gitkeep` dans `src_vectora/{config,datalake,detect,ingest,normalize,sources,stats}/`.
24. Claude crée le squelette `tests/` :
    - `tests/__init__.py` (vide)
    - `tests/unit/.gitkeep`, `tests/integration/.gitkeep`, `tests/fixtures/.gitkeep`
    - `tests/README.md` : à migrer après lecture, ou à réécrire si Q-era

⏸ **Validation Frank** : structure complète, prête pour les fichiers racine et neufs.

### Phase F — Migration et adaptation des fichiers racine (Claude, ~30 min)

25. Claude copie `.env.example` tel quel.
26. Claude copie `.gitignore` après vérification qu'il est neutre.
27. Claude copie `.github/PULL_REQUEST_TEMPLATE.md` après vérification, adapte les références "vectora-inbox" si présentes.
28. Claude copie `CLAUDE.md` (V1.5) et applique les adaptations sémantiques :
    - Bump version V1.5 → V1.6 dans l'entête
    - Section "Changements V1.6" en haut : *"Renommage du projet en Vectora suite à ADR-011. Distinction Vectora plateforme / Vectora Inbox produit aval clarifiée."*
    - Remplacements "Vectora Inbox V1" → "Vectora V1" dans tout le texte courant
    - Remplacements `vectora-inbox` → `vectora` dans les chemins (sauf si historique)
    - §1 : reformuler la vision pour expliciter la nouvelle hiérarchie
    - §13 (outils) : adapter chemin de l'ancien repo si mentionné
    - Conserver les références aux ADRs immutables (qui mentionnent "Vectora Inbox V1" — c'est leur date d'origine)

⏸ **Validation Frank** : CLAUDE.md V1.6 cohérent, lisible.

### Phase G — Création des fichiers neufs (Claude, ~1h)

29. Claude crée `README.md` neuf qui :
    - Décrit Vectora comme moteur de datalake local-first
    - Explicite la hiérarchie : Vectora (plateforme) → produits aval (Vectora Inbox = newsletter, futurs Vectora RAG, Vectora Reports…)
    - Référence `STATUS.md`, `CLAUDE.md`, `docs/architecture/datalake_v1_design.md`, `docs/decisions/`
    - Décrit la structure du repo en cible
30. Claude crée `STATUS.md` neuf :
    - Vision en 3 phrases (Vectora plateforme + Vectora Inbox produit aval)
    - Section "Où on en est" : *"Migration vers vectora terminée le YYYY-MM-DD. Prêt à attaquer Sprint 007 (ADRs 012-016 + refonte design doc V1.5)."*
    - Roadmap globale (paliers Niveau 1/2/3 + sprints planifiés 007, 008)
    - Tableau des décisions (ADRs 001-011)
    - Tableau des difficultés rencontrées (importer celles de l'ancien STATUS qui restent pertinentes + ajouter "migration repo vectora-inbox → vectora" comme dernière ligne)
    - Backlog "pour plus tard" (référer à `future_optimizations.md`)
    - Comment naviguer dans le projet (table des liens)
    - Référence à l'ancien repo : *"Repo précédent (archive lecture-seule) : github.com/<frank>/vectora-inbox - claude, tag `archive-pre-vectora`."*
31. Claude crée `docs/README.md` neuf, court, qui :
    - Décrit l'organisation de `docs/` (architecture, business, decisions, runbooks, sprints)
    - Pointe vers `STATUS.md` et `datalake_v1_design.md`
    - Pas de signature obsolète "Amazon Q Developer"
32. Claude crée `canonical/README.md` neuf qui :
    - Décrit l'organisation réelle de `canonical/` (ecosystems, events, imports, ingestion, parsing, prompts, scopes, sources)
    - Explique le pattern de nommage des scopes
    - Aucune mention de "Lambdas" ou de `client-config-examples/`
    - Cohérent avec la terminologie V1 (datalake, écosystèmes, etc.)

⏸ **Validation Frank** : nouveaux fichiers cohérents et complets.

### Phase H — Premier commit + push (Frank depuis VS Code, ~10 min)

33. Frank vérifie `git status` : tous les fichiers sont en `untracked`.
34. Frank exécute :
    ```
    git add .
    git status                                  (revue rapide)
    git commit -m "chore(repo): initial scaffolding for vectora v1"
    git push origin main
    ```
35. Frank vérifie sur GitHub que le commit est bien là.

⏸ **Validation Frank** : repo en ligne, contenu visible.

### Phase I — Archivage de l'ancien repo (Frank depuis GitHub web + VS Code, ~10 min)

36. Frank ouvre l'ancien repo `vectora-inbox - claude` sur GitHub.
37. Frank crée un tag :
    - Soit via l'interface GitHub : Releases → Draft a new release → tag `archive-pre-vectora`, target `main`
    - Soit en local depuis VS Code : `git tag archive-pre-vectora && git push origin archive-pre-vectora`
38. Frank passe le repo en lecture-seule : Settings → Archive this repository → confirmer.
39. Frank confirme à Claude que c'est fait.

⏸ **Validation Frank** : ancien repo archivé.

### Phase J — Validation finale et update STATUS (Claude, ~10 min)

40. Claude exécute les vérifications du critère de fin :
    - Grep "vectora-inbox" dans le nouveau repo (uniquement références historiques attendues)
    - `pytest --collect-only` (depuis le nouveau repo) — pas d'erreur d'import
    - Structure conforme à l'arborescence cible
41. Claude met à jour `STATUS.md` du nouveau repo :
    - Date de fin de migration
    - Marque Sprint 006 comme ✅ Validé
    - Indique la prochaine étape : Sprint 007
42. Claude prépare le commit final pour Frank :
    - `git add STATUS.md`
    - `git commit -m "docs(status): mark sprint 006 migration as completed"`
    - `git push origin main`
43. Claude remplit la section "Bilan post-exécution" du présent sprint.

⏸ **Validation Frank** : sprint complet, prêt à enchaîner sur Sprint 007.

---

## Fichiers créés / modifiés / supprimés

**✨ Créés (dans le nouveau repo `vectora`)** :

- Tous les fichiers listés dans l'arborescence cible §"Arborescence cible"
- En particulier neufs (réécriture totale, pas une copie) :
  - `vectora/README.md`
  - `vectora/STATUS.md`
  - `vectora/docs/README.md`
  - `vectora/canonical/README.md`

**📝 Modifiés (lors de la copie)** :

- `vectora/CLAUDE.md` (V1.5 → V1.6)
- `vectora/canonical/imports/vectora-lai-core-scopes.yaml` (renommé depuis `vectora-inbox-lai-core-scopes.yaml`)
- `vectora/docs/architecture/datalake_v1_design.md` (adaptations sémantiques mineures)
- `vectora/docs/business/contexte_business_v1.md` (élargissement du cadrage)
- `vectora/docs/decisions/README.md` (ligne 3 adaptée)
- `vectora/docs/sprints/README.md` (ligne 1 adaptée)
- `vectora/docs/sprints/sprint_003_stabilisation_infrastructure.md` (statut superseded)
- `vectora/docs/sprints/sprint_004_adrs_et_refonte_design_doc.md` (statut renuméroté)
- `vectora/docs/sprints/sprint_005_refonte_plans_et_claudemd.md` (statut renuméroté)
- `vectora/.github/PULL_REQUEST_TEMPLATE.md` (si nécessaire après lecture)
- `vectora/STATUS.md` (mise à jour finale Phase J)

**🗑️ Supprimés** :

- Aucun fichier supprimé. Les fichiers non migrés *restent dans l'ancien repo* (qui n'est pas modifié).

**Côté ancien repo `vectora-inbox - claude`** :

- ADR-011 et `migration_inventory.md` et `sprint_006` y sont rédigés (avant migration). On les laisse en place ; ils sont également migrés vers le nouveau repo.
- Tag `archive-pre-vectora` créé sur le `main` actuel.
- Repo passé en lecture-seule sur GitHub (settings → Archive).

---

## Adaptations sémantiques (référence pour Phases C, D, F, G)

Lors de la copie/réécriture, voici les remplacements à appliquer (avec discernement, pas mécaniquement) :

| Avant | Après | Périmètre |
|---|---|---|
| `Vectora Inbox V1` | `Vectora V1` | Titres, descriptions, doc courante |
| `Vectora Inbox` (le projet) | `Vectora` | Doc courante (sauf citations historiques) |
| `vectora-inbox` (chemin/nom) | `vectora` | Chemins, identifiants techniques |
| `vectora_inbox_v1` (Python) | `vectora` | Modules / imports (pas pertinent ici car aucun code productif) |
| `src_vectora_inbox_v1/` | `src_vectora/` | Squelette source |
| `vectora-inbox-lai-core-scopes.yaml` | `vectora-lai-core-scopes.yaml` | Fichier `canonical/imports/` |

**Cas où on ne remplace PAS** :

- ADRs 001-010 : règle d'immutabilité (§16.2 CLAUDE.md). Le vocabulaire d'époque y est volontairement préservé.
- Sprints 000-005 (en tant que documents historiques) : on n'altère pas le corps, on adapte uniquement l'entête de statut quand pertinent.
- Citations dans STATUS.md ou ADR-011 qui font explicitement référence à l'ancien nom (par exemple "le repo précédent `vectora-inbox - claude`").
- Le futur produit aval **Vectora Inbox** (la newsletter) : ce nom est conservé pour ce produit aval. Il ne doit pas être confondu avec le projet "Vectora Inbox V1" (l'ancien nom de la plateforme).

---

## Règles à suivre (références CLAUDE.md)

- **§0** (rôle de Claude architecte) — autorité sur ce type de changement structurant validé par Frank
- **§3** (plan avant code) — le présent sprint est le plan, à valider avant exécution
- **§5** (conventions de code) — non applicable ici (pas de code productif), mais cohérence des noms de fichiers/dossiers (snake_case, pas de v1 dans les modules de code)
- **§6** (conventions Git) — branches feature, message de commit `chore(repo): initial scaffolding for vectora v1`
- **§7** (gestion des secrets) — `.env.example` migre, `.env` jamais commité (gitignored)
- **§14** (phrase d'introduction de session) — Claude lira `STATUS.md` et le présent sprint au début de chaque session liée à ce sprint
- **§16** (documentation vivante) — STATUS.md du nouveau repo à jour à chaque jalon, ADR-011 immutable une fois acceptée
- **§17** (small batches) — découpage en phases A→J permet des points de commit/validation toutes les ~30 min
- **§18** (plans de mini-sprints) — le présent fichier *est* le plan formel
- **§19** (résilience aux plantages) — STATUS.md et le présent sprint forment la mémoire externalisée. En cas de crash de session, on lit ces deux fichiers et on reprend.
- **§20** (gestion modèles) — Sonnet recommandé pour la durée du sprint

---

## Points de validation par Frank

- ⏸ **Avant Phase A** : valider le plan dans son ensemble (le présent fichier)
- ⏸ **Fin Phase A** : repo cloné vide, prêt
- ⏸ **Fin Phase B** : structure squelette complète
- ⏸ **Fin Phase C** : `canonical/` complet et cohérent
- ⏸ **Fin Phase D** : `docs/` complet, ADR-011 incluse
- ⏸ **Fin Phase E** : `scripts/legacy_reference/` migré, squelettes en place
- ⏸ **Fin Phase F** : fichiers racine + CLAUDE.md V1.6 OK
- ⏸ **Fin Phase G** : 4 fichiers neufs (README, STATUS, docs/README, canonical/README) cohérents
- ⏸ **Fin Phase H** : premier commit poussé sur GitHub
- ⏸ **Fin Phase I** : ancien repo archivé
- ⏸ **Fin Phase J** : sprint validé, prêt à enchaîner

---

## Risques identifiés

| # | Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|---|
| 1 | Cowork (sandbox Linux) ne peut pas écrire dans `C:\Users\franc\dev\vectora\` (problème de mount) | Moyenne | Élevé (bloquant) | Valider en début de Phase B que Claude peut écrire dans le nouveau dossier. Si non : Claude prépare tous les fichiers dans `C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude\_migration_staging\` puis Frank copie depuis VS Code. |
| 2 | Renommage du dossier `src_vectora_inbox_v1/` mal exécuté → fichiers `.gitkeep` perdus ou doublés | Faible | Faible | Création des `.gitkeep` directement dans la cible `src_vectora/`, pas un `git mv`. |
| 3 | Adaptations sémantiques de CLAUDE.md V1.6 incohérentes (oubli de remplacement, ajout de bug) | Moyenne | Moyen | Diff complet avant commit. Frank lit avant Phase H. |
| 4 | `canonical/sources/source_catalog.yaml` migre avec son bug regex (Sprint 003 prévoyait correction) | Moyenne | Faible | Soit on applique le correctif à l'étape 9, soit on note explicitement que Sprint 007 le traitera. À trancher avec Frank avant Phase C. |
| 5 | ADR-011 fait référence à un sprint 006 / sprint 007 / sprint 008 qui n'existent pas encore avec ces numéros dans le nouveau repo | Faible | Faible | ADR-011 est rédigée *avant* la migration ; elle anticipe la numérotation cible. À l'arrivée dans le nouveau repo, sprints 003 (superseded), 004→007, 005→008 sont marqués correctement. |
| 6 | Frank crée le repo GitHub avec un README/.gitignore initial → conflit avec notre push | Moyenne | Faible | Phase A point 1 : "Initialisation : aucune". À rappeler à Frank au moment de la création. |
| 7 | Push initial volumineux (scripts/legacy_reference = ~500 KB, plus le reste = ~2 MB total) | Faible | Faible | Acceptable, GitHub gère sans problème. |
| 8 | `pytest --collect-only` échoue sur des imports legacy résiduels | Faible | Faible | Aucun fichier de test V2/V3 ne migre, `pytest --collect-only` devrait juste ne trouver aucun test (ce qui est OK). À vérifier en Phase J. |

---

## Dépendances

- **ADR-011** (`docs/decisions/011-pivot-vectora-inbox-vers-vectora.md`) — accepté, rédigé en Sprint 0.B
- **Inventaire** (`docs/architecture/migration_inventory.md`) — V1, validé par Frank en Sprint 0.A
- **Sprint 003** — pas terminé (en cours), mais sa raison d'être disparaît avec ce sprint (superseded). Pas de blocage.
- **Disponibilité de Frank** pour les Phases A, H, I (création repo, commit/push, archivage GitHub) — ces étapes nécessitent l'accès à GitHub et au terminal Windows
- **Capacité d'écrire dans `C:\Users\franc\dev\vectora\`** depuis l'environnement Cowork — à vérifier en début de Phase B (Risque #1)

---

## Bilan post-exécution

À remplir UNE FOIS le sprint terminé. Ne pas pré-remplir.

### Durée réelle vs estimation

- Estimé : ~3-4h
- Réel : ~Yh
- Écart : (justifier si > 50%)

### Commits effectués

- `<sha>` : `chore(repo): initial scaffolding for vectora v1`
- `<sha>` : `docs(status): mark sprint 006 migration as completed`

### Difficultés rencontrées

(Description courte des problèmes inattendus et de leur résolution.)

### Décisions prises en cours de route

(Si des choix techniques non prévus ont été faits. Si majeurs → créer une ADR.)

### Ce qui reste pour le prochain sprint

(En particulier : confirmer que Sprint 007 démarre proprement dans le nouveau repo, runbooks complémentaires, etc.)

### Validation Frank

- Date de validation : YYYY-MM-DD
- Commentaires éventuels :

---

*Sprint 006 — fin du document.*
