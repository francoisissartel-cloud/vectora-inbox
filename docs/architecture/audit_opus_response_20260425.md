# Audit Stratégique Vectora Inbox V1 — Réponse à `audit_brief_opus.md`

**Auditeur** : Claude Opus
**Date** : 2026-04-25
**Statut** : à valider (et débattre) avec Frank
**Document parent** : `docs/architecture/audit_brief_opus.md`

> Cet audit est conduit avant le moindre commit de code V1. Il commence par les failles, comme demandé par le brief §8. Tout ce qui est validé l'est explicitement, après examen, pas par défaut.

---

## 0. Résumé exécutif

### Verdict global

L'architecture est **cohérente intellectuellement** mais **trop ambitieuse pour son auteur**. Le design est calibré pour une équipe de deux développeurs senior travaillant à temps plein. Frank est seul, non-développeur, et n'a que des soirées et des week-ends. Si on démarre Niveau 1 tel que planifié, je vois trois scénarios de panne probables (cf. Top 3 risques).

La bonne nouvelle : tout est encore en plans. Cinq décisions structurantes prises avant le premier `git commit` du code V1 changent radicalement la trajectoire.

### Top 3 risques si on démarre tel quel

1. **Corruption silencieuse du datalake** dans les 6 mois. Causes additionnées : 10 indexes JSON mis à jour à la main sans transaction, mutation in-place de lignes JSONL via `line_number` (impossible à faire proprement), OneDrive qui synchronise pendant les écritures. Le jour où ça pète, Frank ne le verra pas tout de suite — il verra 6 mois plus tard que `by_event_type` a perdu 12 items. Cf. tensions §5.1, §5.2, §5.9.
2. **Abandon avant la fin du Niveau 1**. Le séquencement bottom-up planifié (8 sprints, ~10h, ~15 composants) ne produit *rien d'observable* avant le sprint final. Pour un solo non-dev qui a besoin de feedback rapide, c'est une recette pour la démotivation. Cf. tension §5.8.
3. **Bug parser silencieux dès le premier run**. `source_catalog.yaml` contient des regex écrites en littéral Python (`r"..."`) qui ne sont pas du regex valide une fois chargées en YAML — c'est une chaîne `r"(\w+...)"` que `re.compile` rejettera. Le test n'a jamais été fait parce qu'aucun code ne tourne. Cf. tension §5.5.

### Top 3 quick wins (à faire avant de toucher au code V1)

1. **Sortir le repo de OneDrive** (1h). Cf. tension §5.9. Source de bugs garantis pour quasi-aucun bénéfice. À faire ce week-end.
2. **Adopter SQLite pour les indexes** (décision, pas de code). Cf. tension §5.1. Un appel à la stdlib Python qui supprime ~600 lignes de code maison à écrire et tester, et fournit ACID gratis.
3. **Pivoter Niveau 1 en walking skeleton** (décision, pas de code). Cf. tension §5.8. Sprint 1 = 1 item curated bout-en-bout avec mocks. Sprints suivants = remplacer un mock à la fois par du vrai. Frank voit quelque chose tourner dès la fin du Sprint 1.

### Questions à trancher par Frank avant Niveau 1 (cf. §10)

Six questions auxquelles l'audit ne peut pas répondre seul. Détaillées en §10.

---

## 1. Verdicts sur les 9 tensions du brief

### §5.1 — JSONL + JSON indexes vs SQLite

**Verdict** : **MODIFIER fortement**. Pivoter vers une architecture hybride : JSONL pour les items + SQLite pour tous les indexes et le cache.

**Analyse**.
Les arguments pro-JSONL du design ("diffable, lisible à l'œil, pas de dépendance externe") sont vrais pour un datalake de 50 items. À 5 000 items répartis sur 60 fichiers JSONL et 11 indexes JSON, plus personne ne lit ces fichiers à l'œil — c'est un fantasme d'ergonomie qui devient une dette technique. Le vrai problème est ailleurs : la mise à jour incrémentale de 10+ fichiers JSON par insert n'est pas atomique. Un crash entre l'écriture du JSONL et la mise à jour de `by_event_type.json` laisse le datalake incohérent. La parade prévue (`rebuild_indexes.py`) est un pansement qui demande à Frank de savoir détecter un état corrompu — il ne le saura pas.

SQLite résout tout ça : `import sqlite3` est dans la stdlib (zéro dépendance), ACID natif, requêtes composées triviales (`WHERE event_type = 'partnership' AND ecosystem = 'tech_lai_ecosystem'`), pas d'index à maintenir manuellement. Pour Frank, l'inspection à l'œil se fait avec `sqlite3 datalake.db ".tables"` puis `SELECT * FROM items WHERE ...` — c'est plus accessible, pas moins, qu'ouvrir un JSON de 800 Ko à la main. La portabilité AWS (argument du local-first) est préservée : SQLite est portable, et le jour où on migre, S3 + Athena ou DynamoDB acceptent un dump JSONL ; on convertit à ce moment-là.

L'option hybride (items en JSONL append-only, métadonnées+indexes+cache en SQLite) est un compromis défendable : on garde l'audit/diff sur les items bruts, on simplifie tout le reste. C'est ma recommandation par défaut.

**Recommandation concrète**.
- `data/datalake_v1/raw/items/YYYY/MM/items.jsonl` → garder tel quel.
- `data/datalake_v1/curated/items/YYYY/MM/items.jsonl` → garder tel quel.
- `data/datalake_v1/index.db` (SQLite unique) → remplace **tous** les fichiers `*/indexes/*.json`.
- Schéma SQLite minimum :
  ```sql
  CREATE TABLE items (
      item_id TEXT PRIMARY KEY,
      level TEXT NOT NULL,         -- 'raw' or 'curated'
      year INTEGER NOT NULL,
      month INTEGER NOT NULL,
      file_offset INTEGER NOT NULL,  -- byte offset, pas line number
      source_key TEXT, source_type TEXT,
      ecosystems TEXT,             -- JSON list
      published_at TEXT,
      ingested_at TEXT,
      event_type TEXT,             -- NULL pour raw
      data_json TEXT               -- snapshot indexable du curated (entities, etc.)
  );
  CREATE INDEX idx_source_key ON items(source_key);
  CREATE INDEX idx_event_type ON items(event_type) WHERE level = 'curated';
  -- etc.
  ```
- Cache d'URL : table `url_cache` dans la même DB, indexée par `(ecosystem, url_canonical)`.
- Impact code : `datalake/indexes.py` disparaît (~300 lignes économisées). `datalake/storage.py` se simplifie. `datalake/raw.py` et `curated.py` perdent toute la logique de mise à jour d'indexes JSON.
- Impact `datalake_v1_design.md` : §3.1 (arborescence), §4 (indexes), §7 (cache structure) à réécrire.
- ADR à créer : `011-sqlite-pour-indexes-et-cache.md`. **Supersede** ADR `006-format-jsonl-append-only.md` partiellement (les items restent JSONL, les indexes deviennent SQLite).

**Note d'humilité** : si Frank tient absolument au "tout fichier plat" pour des raisons de portabilité conceptuelle, l'alternative est d'accepter la complexité du JSONL+JSON et d'ajouter un script `validate_datalake.py` lancé automatiquement après chaque run d'ingestion qui vérifie la cohérence indexes ↔ JSONL. Mais ça reste un compromis inférieur à mon avis.

---

### §5.2 — Le `line_number` dans `by_item_id` (mutation in-place)

**Verdict** : **REJETER**. C'est un piège d'implémentation.

**Analyse**.
Trois problèmes cumulés rendent l'idée impossible à implémenter proprement :
1. Les lignes JSONL sont de longueur variable. Modifier une ligne (ajouter `"tech_sirna_ecosystem"` à la liste `ecosystems`) change sa taille en bytes. Tous les `line_number` des lignes suivantes deviennent faux.
2. Padding pour conserver une longueur fixe ? Impossible à garantir sans un schéma rigide qui ne survit pas à la première évolution (ajout d'un champ).
3. Pas de transaction au niveau du fichier. Crash en plein `seek+write` = ligne JSONL tronquée = fichier corrompu.

Le cas d'usage réel (multi-tagging d'écosystème lors de re-ingestion) est par ailleurs **prématuré pour MVP** : le MVP n'a qu'un seul écosystème (`tech_lai_ecosystem`). Le multi-tagging arrivera au mieux dans 6-12 mois. Concevoir une mécanique fragile pour un cas d'usage absent, c'est de la sur-anticipation classique.

**Recommandation concrète**.
- Cette tension est **automatiquement résolue** si on adopte la recommandation §5.1 (SQLite). Update d'un tag = `UPDATE items SET ecosystems = ... WHERE item_id = ?`. ACID. Trivial.
- Si on ne va pas vers SQLite, alors : retirer purement et simplement la mécanique d'update in-place du design. Pour MVP single-écosystème, l'item est immutable. Quand le multi-tagging deviendra réel (Niveau 3+), on écrira un sidecar `data/datalake_v1/raw/_overlays/tag_overlay.jsonl` (append-only) qui contient `{item_id, ecosystem_added, at}`. La lecture de l'item raw applique l'overlay à la volée. Plus complexe à interroger, mais robuste.
- Impact : §3 du design (note "exception update in-place") supprimée. §5.2 et §5.3 du design réécrits ("multi-tagging différé Niveau 3+").
- Impact `index by_item_id` : on ne stocke plus `line_number`, juste `{year, month}`. Le lookup se fait par scan séquentiel du fichier mensuel (toujours <100 items pour MVP).

---

### §5.3 — 20+ scripts CLI

**Verdict** : **MODIFIER**. Une CLI unifiée style `vectora <verb>` avec sous-commandes.

**Analyse**.
20 scripts séparés avec des flags chacun, c'est ingérable pour un solo non-dev. Scénario réel : un mardi soir, un run échoue à 23h. Frank doit décider : `--resume` ou `--retry-failed` ? `--rebuild-cache` ou `--no-cache` ? Lequel des 20 scripts suis-je censé lancer ? Avec une CLI unifiée, `vectora --help` affiche toutes les commandes en 5 lignes, `vectora ingest --help` affiche les flags de la commande. C'est le standard de tout outil moderne (git, docker, kubectl, pip, poetry). Frank est habitué à ce pattern depuis VS Code.

L'argument "20 fichiers courts sont plus lisibles qu'une CLI" tombe en pratique : Click et Typer (Python) permettent d'écrire chaque sous-commande dans son propre fichier, regroupées par registration. On a la lisibilité par commande **et** la cohérence d'usage.

**Recommandation concrète**.
- Une seule entrée : `python -m vectora <group> <verb> [options]` ou alias `vectora` via `pyproject.toml`.
- Trois groupes :
  - `vectora run ingest|normalize|pipeline` (runtime quotidien)
  - `vectora source discover|validate|promote|list|revalidate` (onboarding)
  - `vectora maintenance rebuild-indexes|rebuild-cache|validate|retry-failed|report` (maintenance)
- Dépendance : Typer (recommandé, plus moderne et type-safe que Click). Coût : ~50 Ko, zéro friction.
- Impact `datalake_v1_design.md` : §6 (commandes CLI prévues), §12.1 (`scripts/` arborescence) à réécrire.
- Impact code : `src_vectora_inbox_v1/cli.py` unique, ~150 lignes total, regroupe tous les entry points.
- ADR à créer : `012-cli-unifiee-typer.md`.

**Cas où je modèrerais** : si Frank trouve la CLI Typer plus opaque que des scripts séparés, alors fallback à 4 scripts (`run_pipeline.py`, `onboard_source.py`, `maintenance.py`, `report.py`) avec sous-commandes via `argparse`. Mais ne **pas** garder 20 scripts. C'est un piège opérationnel.

---

### §5.4 — Workflow Discovery/Validation/Promotion en V1

**Verdict** : **MODIFIER**. Garder seulement Validation au Niveau 2. Reporter Discovery + Promotion au Niveau 3 (ou plus tard).

**Analyse**.
Le brief note correctement que le Niveau 1 ne contient pas le module `sources/` (vérifié dans `level_1_plan.md`). Le vrai débat est sur le Niveau 2.

Décomposons les 3 sous-modules :
- **Validation** : nécessaire de toute façon. C'est le test "est-ce que ma config marche encore ?". Il faut le coder pour les 8 sources MVP, et le ré-utiliser ensuite. **Garder en Niveau 2.**
- **Discovery** : automatise la découverte de RSS/sections news/sélecteurs CSS pour une nouvelle source. C'est ~500 lignes de code complexes (heuristiques HTML, parsing fuzzy). Pour 8 sources qu'on connaît déjà, c'est inutile. Pour les 176 candidats, ça vaudrait la peine — mais Frank ajoutera 1-2 sources par mois en pratique, pas 176 d'un coup. **Reporter au Niveau 3 ou plus tard.**
- **Promotion** : copie de config de `candidates.yaml` → `source_catalog.yaml`. Trois lignes de Python. Pas un module, juste un script. Ou plus simple encore : Frank édite manuellement les YAML (il est habile avec VS Code). **Reporter ou supprimer.**

L'enjeu : la complexité du module `sources/` est probablement 30% du temps Niveau 2. Récupérer ce temps pour durcir l'ingestion + les filtres + le reporting (qui sont dans le chemin critique d'usage réel) a beaucoup plus de valeur.

**Recommandation concrète**.
- Niveau 2 : implémenter `sources/validation.py` uniquement. Pas de discovery, pas de promoters. Frank crée les configs sources à la main (avec l'aide de Claude Code en pair-programming pour rédiger le YAML).
- Pour ajouter une source en Niveau 2 : `vectora source validate --source X` teste la config nouvellement écrite. Si PASSED, Frank fait `enabled: true` dans le YAML. C'est tout.
- Niveau 3 : `sources/discovery.py` + `sources/revalidator.py` (revalidation périodique des sources actives — utile pour détecter les sources cassées).
- Hors scope V1 : `sources/promoters.py` automatisé. Si jamais nécessaire, ce sera Niveau 4 ou V2.
- Impact `datalake_v1_design.md` : §6.5 (workflow onboarding) à reformuler par paliers. §12.1 arborescence : `sources/discovery.py` et `sources/promoters.py` retirés du Niveau 2.
- Impact ADR : `009-reprise-discovery-validation.md` est superseded par un nouveau `013-onboarding-source-par-paliers.md`.

---

### §5.5 — `source_catalog.yaml` fait trop de choses

**Verdict** : **MODIFIER, mais pas comme prévu dans le design**. Et **un bug à corriger d'urgence**.

**Analyse**.
Lecture du fichier réel (`canonical/sources/source_catalog.yaml`) confirme tout ce que dit le brief, **plus une faille critique** : les `date_extraction_patterns` sont écrits comme `r"(\w+ \d{1,2}, \d{4})\w*"`. En Python, le `r` préfixe une string littérale comme raw string. **En YAML, c'est juste une chaîne dont les premiers caractères sont `r"` et qui se termine par `"`.** Une fois chargée par PyYAML, `re.compile()` recevra `'r"(\\w+ \\d{1,2}, \\d{4})\\w*"'` et lèvera une `re.error`. Aucun test ne l'a vu parce qu'aucun code ne tourne. **C'est un bug planté en attendant son premier run.**

Au-delà du bug : le fichier mélange effectivement 3 niveaux. Mais la solution proposée (split en 3 fichiers : `source_catalog.yaml`, `source_configs.yaml`, `parsing_config.yaml`) est elle aussi excessive pour 8 sources. Trois fichiers à maintenir cohérents pour Frank, c'est plus de risque d'erreur que un fichier bien organisé.

Observation supplémentaire : les 5 sources corporate ont **les mêmes 5 patterns de dates copiés-collés**. C'est de la duplication pure. Un set de patterns "press_corporate_default" appliqué par défaut à toutes les sources de ce type, surchargeable par source si besoin, élimine 25 lignes de duplication actuelles.

**Recommandation concrète**.
1. **Bug à corriger immédiatement** (avant tout code) : retirer le préfixe `r` de toutes les regex dans `source_catalog.yaml`. Ce sont des chaînes YAML, pas du Python. Format correct :
   ```yaml
   date_extraction_patterns:
     - "(\\w+ \\d{1,2}, \\d{4})\\w*"
     - "(\\d{1,2} \\w+ \\d{4})"
   ```
   (Note : double-backslash pour échapper le backslash en YAML, sauf si on utilise les blocs `|` ou `>` qui n'interprètent pas — à benchmark.)
2. **Refactor de `source_catalog.yaml`** sans split : déplacer les `date_extraction_patterns` par défaut dans `canonical/parsing/parsing_config.yaml`, indexés par `source_type`. Une source surcharge si elle a des patterns spécifiques.
3. **Garder un seul fichier `source_catalog.yaml`** pour MVP. Le split en 3 est un faux problème à 8 sources. Reconsidérer le split à 50+ sources.
4. **`source_configs.yaml` n'est pas créé** — le design ne le justifie plus. Tout vit dans `source_catalog.yaml`.
5. Impact `datalake_v1_design.md` : §11.1 (structure cible canonical) simplifiée, `source_configs.yaml` retiré.

**Note critique sur le fond** : avoir des **regex Python en clair dans un YAML maintenu par un non-développeur** est une mauvaise idée par principe. Si Frank doit ajouter une source dont les dates sont au format "12 janvier 2026 à 14h30", il faut qu'il puisse écrire ça dans une grammaire haut-niveau, pas en regex. Long terme : prévoir une bibliothèque de stratégies nommées (`date_strategy: "iso"`, `date_strategy: "english_long"`) avec les regex implémentées en Python testé. À mettre dans `future_optimizations.md`.

---

### §5.6 — Le curated est-il assez riche pour une newsletter ?

**Verdict** : **CONSERVER l'absence de scoring, mais ENRICHIR avec des "signaux factuels"**.

**Analyse**.
Le design a raison de séparer datalake (factuel) et consommateur (éditorial). Le scoring est une opinion ; il varie selon le consommateur (newsletter générique vs B2B sur-mesure vs rapport ponctuel). Mettre un `relevance_score` unique dans le curated, c'est imposer une opinion à tous les consommateurs futurs. Et Frank changera ces règles dans 6 mois — il faudra recurer tous les items.

MAIS : le brief identifie un vrai manque. Sans aucun signal de priorisation dans le curated, le consommateur newsletter doit re-charger tous les scopes canoniques pour calculer son propre score, à chaque génération. C'est lent et fragile.

La solution est de stocker dans le curated des **signaux factuels** (déterministes, calculés à la curation, sans LLM) que les consommateurs combineront ensuite selon leur logique éditoriale. Pas une opinion, des constats.

**Recommandation concrète**.
Ajouter une section `signals` dans l'item curated :
```json
"signals": {
  "is_pure_player_source": true,
  "is_corporate_source": true,
  "is_sector_press": false,
  "mentions_trademark": ["Sublocade", "Brixadi"],
  "mentions_regulatory_body": ["FDA"],
  "mentions_clinical_phase": ["Phase 3"],
  "title_length": 87,
  "content_word_count": 612,
  "days_since_published": 2
}
```
Tous ces champs sont **calculables sans LLM** à partir du raw + canonical scopes. Calcul fait dans `normalize/signals.py`, après le LLM, avant le write final. Coût : zéro USD, ~50 ms par item.

Le consommateur newsletter applique ses règles : "score = +2 si is_pure_player_source, +3 si mentions_regulatory_body, +1 si days_since_published <= 3, ...". Modifiable à volonté, sans recurer.

- Impact `datalake_v1_design.md` : §3.4 (format curated) à enrichir avec la section `signals`. §6.4 (étape NORMALIZE) à enrichir avec l'étape de calcul des signaux.
- Impact code : nouveau module `normalize/signals.py`. Léger.
- Niveau d'implémentation : **Niveau 2** (Cœur). Pas Niveau 1.
- ADR à créer : `014-signaux-factuels-curated.md`.

---

### §5.7 — CLAUDE.md est-il trop long et trop dense ?

**Verdict** : **CONSERVER, avec extraction de 2 sections vers des runbooks**.

**Analyse**.
1100 lignes, c'est long. Mais en lisant section par section, je n'identifie pas de bureaucratie inutile. Chaque règle a une raison documentée. La densité est justifiée parce que CLAUDE.md sert deux fonctions : (a) règles opérationnelles **chargées à chaque session** (donc présentes dans le contexte LLM, donc utilisées), et (b) contrat moral entre Frank et Claude (donc lu attentivement par Frank quand il l'a écrit, et utilisé comme référence quand un dérapage se produit).

Cela dit, deux sections ont une nature différente : §15 (gestion des coûts) et §20 (gestion des modèles) sont des **runbooks opérationnels** ("comment faire X"), pas des règles de comportement. Les déplacer libère ~280 lignes de CLAUDE.md sans perdre l'information — au contraire, ça clarifie.

L'argument "Claude oublie au-delà d'un certain volume" est faible : 1100 lignes, c'est ~30k tokens, soit <15% du contexte d'une session moderne. C'est confortablement dans la bande de bonne attention. Le vrai gaspillage de contexte, c'est la lecture de fichiers non nécessaires (cf. CLAUDE.md §19 — Discipline 4 — déjà présent).

Sur les règles potentiellement contre-productives :
- §17 "max 5 fichiers / 300 lignes par commit" : règle saine, mais doit être interprétée. Pour un sprint de bootstrap qui crée 8 fichiers `__init__.py` + 4 schémas Pydantic, on peut dépasser. Le texte le prévoit déjà ("Exceptions légitimes : ménage en bloc, génération de boilerplate"). OK.
- §14 "phrase d'introduction obligatoire en début de session" : utile en théorie, friction en pratique. À voir si Frank trouve ça pénible — sinon, garder.
- §18 "un fichier `.md` par sprint avant d'exécuter" : disciplinant. Pour un sprint de 30 min, écrire le `.md` ajoute 10 min. Compromis : sprints <1h peuvent être plus légers (juste objectif + critère de fin, pas tout le template).

**Recommandation concrète**.
1. Extraire CLAUDE.md §15 → `docs/runbooks/cost_management.md`. Laisser un §15 condensé de 20 lignes dans CLAUDE.md qui pose les règles essentielles ("aucun run sans estimation préalable", "alerter si > 50% du cap") et renvoie au runbook pour le détail.
2. Extraire CLAUDE.md §20 → `docs/runbooks/model_selection.md`. Idem, §20 condensé qui dit "Haiku pour mécanique, Sonnet par défaut, Opus pour audit ; détail dans le runbook".
3. Bilan : CLAUDE.md passe de ~1100 à ~750 lignes. Plus focalisé sur les **règles**.
4. Pour les sprints très courts : ajouter au template `_TEMPLATE.md` une section "Format léger (sprint <1h)" qui n'exige que objectif, critère de fin, fichiers touchés.

---

### §5.8 — Le Niveau 1 est-il bien découpé ?

**Verdict** : **MODIFIER fortement**. Pivoter en walking skeleton + corriger une contradiction interne.

**Analyse**.
Deux problèmes distincts.

**Problème 1 — Séquencement bottom-up démotivant**.
Le plan actuel : 8 sprints, ~10h, ~15 composants, livre l'E2E au sprint 8. Pendant 7 sprints, Frank a des modules qui passent leurs tests unitaires mais ne forment rien de visible. Pour un solo non-dev qui code le soir et a besoin de feedback rapide, c'est la recette pour décrocher.

Le walking skeleton inverse l'ordre : Sprint 1 livre un E2E **dégradé** (mocks partout : fetcher mock qui renvoie un item RSS hardcodé, parser mock qui renvoie un dict hardcodé, LLM mock qui renvoie une réponse JSON canonique). Le pipeline tourne, le terminal affiche `[1/1] ✓ 1 item curated`, le datalake contient un fichier. Frank voit que ça marche. Sprints 2 à 7 : remplacer un mock à la fois par du vrai (Sprint 2 : vrai fetcher HTTP, Sprint 3 : vrai parser RSS, etc.). À chaque sprint, le pipeline tourne **toujours**, juste plus richement.

C'est aussi mieux pour Claude (l'auteur) : à chaque sprint on a un test E2E vivant qui détecte les régressions immédiatement.

**Problème 2 — Contradiction interne du `level_1_plan.md`**.
Le plan dit : *"1 source RSS, 1 item LAI", critère de fin = "`run_pipeline.py --source press_corporate__medincell` produit 1 item curated"*. Or **medincell n'a pas de RSS**. Vérifié dans `source_catalog.yaml` :
```yaml
- source_key: "press_corporate__medincell"
  rss_url: ""
  html_url: "https://www.medincell.com/news/"
  ingestion_mode: "html"
```
Soit on choisit une autre source pour le Niveau 1 (FierceBiotech ou EndPoints, qui ont du RSS), soit on accepte que le Niveau 1 implémente un parser HTML (plus complexe, BeautifulSoup, sélecteurs CSS).

Recommandation : **changer la source pilote du Niveau 1 pour FierceBiotech (RSS)**. Raisons :
- Parser RSS est nettement plus simple que parser HTML générique. Bon choix pour les fondations.
- FierceBiotech sort des dizaines d'articles par jour → easy de tester avec du contenu réel et frais.
- Le filtre LAI est désactivé en Niveau 1 (accept-all) → on accepte qu'on ingère du non-LAI ; on prouve juste l'architecture.
- Medincell (HTML) arrivera au Niveau 2 quand on aura le parser HTML et les filtres actifs.

**Recommandation concrète**.
1. Réécrire `level_1_plan.md` autour du walking skeleton. 8 sprints réordonnés :
   - **L1-S1** — *Bootstrap + walking skeleton avec mocks* : structure de modules, dataclasses, fetcher mock, parser mock, LLM mock, orchestrator simpliste, run_pipeline.py qui tourne. Fin de sprint : `python -m vectora run pipeline --source mock_source` produit 1 item curated mock dans le datalake.
   - **L1-S2** — *Datalake réel* : remplacer le mock storage par un vrai SQLite + JSONL append. item_id, lookup. Test : le mock pipeline écrit pour de vrai dans `data/datalake_v1/`.
   - **L1-S3** — *Fetcher HTTP réel + parser RSS réel* : remplacer les 2 mocks. Tester sur FierceBiotech RSS en dur.
   - **L1-S4** — *LLM réel (Claude Sonnet via Anthropic)* : remplacer le mock LLM. Premier coût USD réel, traçé dans `curation_log.jsonl`.
   - **L1-S5** — *Config-driven* : remplacer la source hardcodée `mock_source` par chargement YAML depuis canonical. Idem pour l'écosystème, le client.
   - **L1-S6** — *Detect gap + retry minimal* : `detect/gap.py` réel, retry 1× sur erreur LLM transitoire.
   - **L1-S7** — *Tests unitaires des fonctions critiques* : `item_id`, `url_canonicalization`, parser RSS sur fixtures statiques.
   - **L1-S8** — *Polish + smoke test final* : critère de fin global atteint, 1 item bout-en-bout depuis FierceBiotech.
2. Corriger `level_1_plan.md` : source pilote = `press_sector__fiercebiotech`, pas `press_corporate__medincell`.
3. Mettre à jour `STATUS.md` (critère de fin Niveau 1) en cohérence.

---

### §5.9 — OneDrive + Cowork

**Verdict** : **MODIFIER d'urgence**. Sortir le repo de OneDrive avant le premier code commit du Niveau 1.

**Analyse**.
OneDrive sync introduit deux risques distincts pendant un run d'ingestion :
- **Lock transitoire** sur un fichier en cours de sync. Une écriture du moteur peut échouer avec `[Errno 13] Permission denied`. Sur du JSONL append-only, ça plante l'ingestion en cours sans corruption. Sur du JSON index update (lecture-modification-écriture), ça peut laisser le fichier dans un état partiel.
- **Latence de sync** sur des centaines de petites écritures (8000+ ops par run estimé en §0). Pas critique, mais perceptible.

Le risque concret est déjà documenté : Frank a vécu `.git/index.lock bloqué` (cf. STATUS.md, tableau des difficultés). C'était git, demain ce sera le moteur.

La parade est **triviale** : `mv` du repo vers `C:\Users\Frank\dev\vectora-inbox-claude\` (hors OneDrive). Garder éventuellement un backup hebdo manuel des `docs/` vers OneDrive si Frank veut la sync cloud sur la doc seule (pas le code, pas les données).

Coût : 1h (déplacer, reconfigurer VS Code, tester un commit). Bénéfice : élimine une classe entière de bugs futurs.

L'argument "STATUS.md liste ça en optimisation #10" est un faux argument : la priorisation a été faite quand il n'y avait pas de code. Maintenant qu'on s'apprête à écrire du code, ça remonte en tête de liste.

**Recommandation concrète**.
1. Action : **avant Sprint L1-S1**, déplacer le repo. Procédure dans un nouveau runbook `docs/runbooks/move_repo_out_of_onedrive.md`.
2. Cible : `C:\Users\Frank\dev\vectora-inbox-claude\` (ou équivalent sous le profil utilisateur, hors OneDrive).
3. Reconfigurer VS Code workspace pour pointer dessus.
4. Tester : `git status` + un commit + un push de test.
5. Mettre à jour `STATUS.md` (retirer #10 du backlog "future_optimizations" → marquer "fait").
6. Vérifier que Cowork peut toujours monter le nouveau chemin (le mount est dynamique côté Cowork, normalement OK).

**Sur Cowork lui-même** (sandbox Linux, git instable) : c'est une contrainte connue, gérée par "git seulement depuis VS Code Windows" (CLAUDE.md §13). Pas de changement nécessaire. Acceptable. Mais ça signifie que Claude depuis Cowork **ne peut pas faire les commits autonomes** mentionnés dans CLAUDE.md §6 — c'est documenté mais mérite un encadré dans CLAUDE.md §6 plus explicite ("autonomie commit + push : seulement depuis Claude Code dans VS Code, pas depuis Cowork").

---

## 2. Tensions additionnelles (non listées au brief §5)

### §A — Schéma de données non typé / non validé

**Sévérité** : moyenne. **Verdict** : MODIFIER.

Le design parle de `config/schemas.py` avec des dataclasses, mais le format des items raw/curated n'est pas validé à l'écriture. C'est un dict qui doit avoir les bons champs. À la première évolution de schéma (`schema_version: "raw/1.1"`), il n'y a aucun mécanisme pour détecter qu'un consommateur ancien lit un item nouveau format incompatible.

**Recommandation**. Adopter **Pydantic V2** dès le Niveau 1 pour tous les modèles : `RawItem`, `CuratedItem`, `SourceConfig`, `ClientConfig`, `EcosystemConfig`. Coût : une dépendance (Pydantic est très répandu, stable, bien maintenu). Bénéfices : validation à l'écriture (typage runtime), validation à la lecture (détecte les schémas évolués), serialization JSON gratuite, type hints exploités par VS Code (auto-complétion sur `item.title` pour Frank). Les dataclasses prévues deviennent des `BaseModel`.

ADR à créer : `015-pydantic-pour-modeles-de-donnees.md`.

### §B — Pas de stratégie pour itérer le prompt LLM

**Sévérité** : haute (le prompt est **le cœur** du curated). **Verdict** : à anticiper Niveau 2.

`canonical/prompts/normalization/generic_normalization.yaml` contient le prompt en YAML. Le design dit `prompt_version: "generic_normalization@2.0"` — versionnement manuel par filename. Mais aucune mention de :
- Comment tester un nouveau prompt avant de le déployer en runtime ?
- Comment comparer prompt v2.0 vs v2.1 sur les mêmes items ?
- Comment recurer après un changement de prompt ? (déjà mentionné en `future_optimizations.md` #3 — donc différé, mais sans réflexion sur le coût d'attendre)

Quand Frank voudra améliorer la qualité de la curation (et il le voudra, dès qu'il regardera la première fournée d'items curated), il n'a pas d'outil. Il va modifier le YAML, relancer, regarder à l'œil, modifier encore. Méthode lente et non reproductible.

**Recommandation**. Créer dès Niveau 2 (pas Niveau 1) un script `vectora maintenance test-prompt --prompt generic_normalization --version 2.1 --fixtures tests/fixtures/items_for_prompt/`. Il prend ~10 items raw figés (fixtures), tourne le prompt v2.1 dessus, compare la sortie à la sortie v2.0 (diff JSON), affiche le coût. Permet l'itération rapide.

Constituer en parallèle un set de fixtures ("golden items") : 10-20 items raw représentatifs (1 partnership Medincell, 1 regulatory FDA, 1 clinical update, etc.) qui servent de test de non-régression du prompt.

### §C — Estimation de coût pré-run absente du design

**Sévérité** : moyenne. **Verdict** : COMPLÉTER.

CLAUDE.md §15.5 dit : *"Claude annonce le coût estimé avant de lancer"*. Mais le design `datalake_v1_design.md` ne précise nulle part comment cette estimation est calculée ou exposée. Sans implémentation, c'est un vœu pieux.

**Recommandation**. Implémenter en Niveau 2 une fonction `estimate_normalization_cost(client_id) → CostEstimate` :
- Lit le gap actuel (nombre d'items pending).
- Lit `curation_log.jsonl` pour calculer le coût moyen par item sur les N derniers (par défaut 100).
- Multiplie. Renvoie {items_pending, cost_avg_per_item_usd, cost_total_estimated_usd, model}.
Exposer via `vectora run normalize --dry-run` qui affiche l'estimation sans rien faire. Le mode normal affiche aussi l'estimation et demande confirmation si > 50% du cap.

### §D — `actor_type` et `company_id_at_source` couplent le raw au business

**Sévérité** : faible-moyenne. **Verdict** : ÉCLAIRCIR.

Dans l'item raw exemple : `actor_type: "pure_lai"`, `company_id_at_source: "medincell"`. Ces classifications dépendent de l'état actuel des scopes canonical. Si demain Frank reclassifie medincell de `pure_lai` à `hybrid`, les anciens items raw portent une classification obsolète.

Deux choix philosophiques :
- **Snapshot** : raw capture l'état au moment de l'ingestion. Les anciens items restent classés selon les anciennes règles. C'est cohérent, mais demande de documenter explicitement que `actor_type` n'est pas requêtable de manière fiable pour des analyses transversales.
- **Forward-looking** : raw ne contient que ce qui ne change pas (URL, contenu, dates). Les classifications business sont calculées au moment de la lecture, contre l'état canonical actuel. Plus pur, mais plus lent à la lecture.

Le design choisit implicitement le snapshot, sans le dire. Le **dire explicitement** dans le design suffit. Et envisager un script `vectora maintenance refresh-actor-types` qui re-calcule à la demande quand Frank fait une grosse réorg de canonical.

### §E — Pas de validation des configs YAML au démarrage

**Sévérité** : moyenne. **Verdict** : AJOUTER.

Le moteur va charger 6+ fichiers YAML (canonical/scopes/*, ecosystems, sources, clients). Si un fichier est mal formé (clé manquante, type incorrect), où est-ce détecté ? Le design ne dit rien. En pratique, ça plantera au premier accès dans le code, avec un `KeyError` cryptique.

**Recommandation**. À chaque démarrage de `vectora` (CLI), valider tous les YAML chargés contre les modèles Pydantic (cf. §A). Si erreur, message clair pointant le fichier et la clé fautive, exit 1. Coût : quelques ms. Bénéfice : Frank n'a jamais à débugger une erreur Python pour une virgule oubliée dans un YAML.

### §F — Aucun mécanisme de rollback / dry-run

**Sévérité** : moyenne. **Verdict** : AJOUTER en Niveau 2.

Pour un solo non-dev qui pilote un système, la confiance vient de pouvoir tester sans conséquence. Le design n'expose pas de `--dry-run` global. Si Frank lance par erreur `vectora run pipeline --client production` au lieu de `--client mvp_test_30days`, il a écrit dans le datalake. Pas de undo.

**Recommandation**. Mode `--dry-run` sur tous les `run *` qui simule sans écrire. Affiche : "aurait ingéré X items, écrit dans Y fichiers, coûté ~Z USD". Niveau 2.

---

## 3. Synthèse — Top 3 risques (rappel) et Top 3 quick wins (rappel)

### Top 3 risques (rappel structuré)

| # | Risque | Probabilité | Gravité | Tensions |
|---|---|---|---|---|
| 1 | Corruption silencieuse du datalake (indexes incohérents, mutation in-place ratée, OneDrive lock) | Haute | Haute | §5.1, §5.2, §5.9 |
| 2 | Abandon avant fin Niveau 1 (séquencement bottom-up sans feedback rapide) | Moyenne-haute | Critique pour le projet | §5.8 |
| 3 | Bug parser regex dès le premier run (préfixe `r` dans YAML) | Certaine au premier run | Faible (facile à fixer mais embarrassant) | §5.5 |

### Top 3 quick wins (rappel structuré)

| # | Action | Coût | Impact |
|---|---|---|---|
| 1 | Sortir le repo de OneDrive | ~1h | Élimine une classe entière de bugs futurs |
| 2 | Décider d'adopter SQLite pour les indexes | 0h (décision) ; -300 lignes de code à écrire | Atomicité gratuite, simplification massive |
| 3 | Pivoter Niveau 1 en walking skeleton | 0h (décision) ; même budget total | Feedback à chaque sprint, Frank ne décroche pas |

### Bonus (4 actions simples avant Niveau 1)

| # | Action | Coût |
|---|---|---|
| 4 | Corriger le bug `r"..."` dans `source_catalog.yaml` | ~15 min |
| 5 | Décider Pydantic pour les modèles | 0h (décision) |
| 6 | Décider CLI unifiée Typer | 0h (décision) |
| 7 | Changer la source pilote Niveau 1 (medincell HTML → fiercebiotech RSS) | 0h (décision) |

---

## 4. Questions pour Frank — l'audit ne peut pas trancher seul

1. **SQLite ou JSONL+JSON purs ?** Ma recommandation forte : SQLite pour les indexes, JSONL pour les items. Mais c'est ta décision : préfères-tu la garantie de tout-fichier-plat (portabilité maximale, lecture à l'œil) ou l'ACID gratuit de SQLite ? Cf. §5.1.

2. **Walking skeleton ou bottom-up sur le Niveau 1 ?** Ma recommandation forte : walking skeleton. Mais ça implique d'accepter que les Sprints 1-2 produisent du code "dégradé" (mocks, hardcoded) qu'on remplace ensuite. Es-tu à l'aise avec ce mode où le code initial est jetable ? Cf. §5.8.

3. **Source pilote Niveau 1 : medincell (HTML) ou fiercebiotech (RSS) ?** Ma recommandation : fiercebiotech, parce que parser RSS << parser HTML en complexité. Mais medincell est la source business prioritaire. Préfères-tu prouver l'architecture avec une source facile, ou la valider sur la source business prioritaire ? Cf. §5.8.

4. **Discovery automatique : Niveau 2 ou plus tard ?** Ma recommandation : reporter à Niveau 3 ou plus. Tu vas onboarder ~1-2 sources/mois en Niveau 2/3, pas 176 d'un coup. Préfères-tu le confort futur de l'automation (au prix de 30%+ du budget Niveau 2), ou prioriser le durcissement de l'ingestion + reporting ? Cf. §5.4.

5. **Scoring dans le curated : interdit, ou signaux factuels acceptés ?** Ma recommandation : interdire le scoring (opinion), autoriser les signaux factuels (constats déterministes). Mais ça ajoute un module Niveau 2. Es-tu OK avec cette nuance, ou préfères-tu garder le curated 100% factuel sans rien d'éditorial-friendly ? Cf. §5.6.

6. **Date de sortie OneDrive : ce week-end ou avant Niveau 1 ?** Ma recommandation : ce week-end. C'est 1h, et ça libère le démarrage Niveau 1. OK pour bloquer un créneau ?

---

## 5. Recommandation de séquencement avant Niveau 1

Avant Sprint L1-S1, je recommande d'exécuter dans l'ordre :

1. **Décider** sur les 6 questions ci-dessus (1h de discussion Frank ↔ Claude). Sortie : 6 réponses tranchées.
2. **Écrire les ADRs** correspondants pour les décisions modificatrices (estimés : 011-sqlite, 012-cli-typer, 013-onboarding-paliers, 014-signaux-factuels, 015-pydantic). Sprint dédié, ~2h.
3. **Mettre à jour `datalake_v1_design.md` V1.5** pour intégrer les décisions (§3, §4, §6.5, §7, §11, §12). Sprint dédié, ~2h.
4. **Mettre à jour `level_1_plan.md` V2** pour le walking skeleton + nouvelle source pilote. Sprint dédié, ~1h.
5. **Mettre à jour `CLAUDE.md` V1.6** : extraction §15 et §20 vers runbooks, encadré §6 sur la limite Cowork pour les commits. Sprint dédié, ~1h.
6. **Sortir le repo de OneDrive**, runbook + exécution, ~1h.
7. **Corriger le bug regex `r"..."`** dans `source_catalog.yaml`, ~15 min.
8. **Mettre à jour `STATUS.md`** pour refléter tout ça, ~30 min.

**Total** : ~9h de cadrage avant le premier sprint code. Lourd ? Oui. Justifié ? À mon avis oui, parce que chaque décision faite à froid maintenant économise 5x son temps en debug et rework plus tard. Mais c'est ton appel, Frank.

Si tu veux aller plus vite : **minimum vital** avant Niveau 1 = quick wins #1 (OneDrive) + #4 (bug regex) + décisions sur questions 1, 2, 3. Le reste peut s'intégrer au fur et à mesure du Niveau 1.

---

## 6. Ce que cet audit n'a PAS fait

Pour transparence, l'audit n'a pas exploré :
- Le code legacy V3 dans `scripts/legacy_reference/` (ce qu'il y a à reprendre vs jeter, comment, quel coût). C'est un audit séparé qui mérite son propre travail.
- `future_optimizations.md` en détail (le brief m'a renvoyé dessus mais je n'ai pas vérifié sa cohérence avec les autres docs).
- Le contenu détaillé des scopes canoniques (`canonical/scopes/*.yaml`). Je n'ai pas vérifié si les keywords LAI sont bien à jour, exhaustifs, ou correctement structurés. Frank a l'expertise métier, c'est plutôt à lui de valider ça quand il regardera les premiers résultats de filtrage.
- Les prompts LLM réels (`canonical/prompts/normalization/generic_normalization.yaml`). Je les ai survolés via le design mais pas relus en détail. À auditer séparément quand on aura les premières sorties.
- La sécurité opérationnelle au-delà de `.env` (rotation de la clé Anthropic, audit des dépendances, etc.). Hors scope MVP, mais à inscrire dans `future_optimizations.md`.

---

*Fin de l'audit. À débattre.*
