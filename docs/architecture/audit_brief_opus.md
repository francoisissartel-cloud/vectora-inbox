# Brief — Audit Stratégique Profond Vectora Inbox V1

**Destinataire** : Claude Opus (nouvelle session dédiée à l'audit)
**Rédigé par** : Claude Sonnet, après lecture complète du repo le 2026-04-25
**Objectif** : Permettre à Opus de mener un audit stratégique complet avant le démarrage du développement (Niveau 1 — Fondations). Zéro code n'a encore été écrit.

> Ce document est auto-contenu. Opus n'a pas besoin de lire d'autre contexte pour démarrer. Il référence des extraits et des chemins de fichiers précis pour que Opus puisse les lire si besoin.

---

## 1. Qui est Frank — Le contexte humain (critique pour l'audit)

Frank est pharmacien + école de commerce, 11 ans d'expérience industrie pharma (analyste, business analyst, private equity, consulting, tech transfer). Il travaille **seul**, **sans équipe**, **sans budget infrastructure**. Il n'est **pas développeur** — il peut lire du code, valider une architecture, mais il ne code pas.

Le moteur tourne sur son **PC Windows** (OneDrive). Le repo est monté dans une sandbox Linux via Cowork (Claude desktop), ce qui crée des contraintes réelles : git ne fonctionne pas depuis la sandbox (verrous cross-platform), les commits sont faits manuellement depuis VS Code.

**Son avantage compétitif est métier, pas technique** : il sait définir ce qui est signal et ce qui est bruit dans les marchés pharma de niche (LAI, siRNA, cell therapy). Cette expertise est rare et irremplaçable. La technologie est le levier qui la rend scalable.

**Implications pour l'audit** : toute recommandation doit être calibrée pour un solo non-développeur. La simplicité opérationnelle prime sur l'élégance architecturale. Un système que Frank peut comprendre, déboguer et piloter sans aide vaut plus qu'un système optimal qu'il ne peut pas maintenir.

---

## 2. Le Projet — Vision et périmètre V1

### Ce qu'on construit

**Vectora Inbox V1 est un moteur d'alimentation d'un datalake de veille pharmaceutique**, local-first (PC Windows), avec pour seul service externe l'API Anthropic (Claude).

Le datalake produit deux niveaux :
- **raw** : items ingérés tels quels depuis les sources web
- **curated** : items enrichis par LLM (entités extraites, event type, résumé, dates normalisées)

**Ce que V1 ne fait pas** : newsletter, scoring éditorial, RAG, interface utilisateur, livraison d'email. Ces fonctions sont des "consommateurs du datalake", hors scope V1.

### Le premier écosystème : LAI (Long-Acting Injectables)

200+ entreprises pharmaceutiques développent des médicaments LAI (formulations injectables à libération prolongée). Frank cible ce marché en premier car il n'existe aucune newsletter dédiée et son expertise métier y est maximale. La difficulté principale : classifier ce qui est LAI ou pas n'est pas trivial (même molécule peut avoir une forme LAI et non-LAI, pure players vs big pharma ont des profils de signal radicalement différents).

### La vision produit (datalake comme fondation)

```
DATALAKE CURATED (V1)
    ├── Newsletter LAI générique (premier produit)     → B2C abonnement
    ├── Newsletter sur-mesure                          → B2B premium
    ├── Rapports d'expertise ponctuels                 → Vente à des pharma/fonds
    └── RAG / Intelligence augmentée                   → Vision long terme
```

Le datalake n'est pas une fin en soi : c'est la fondation qui rend l'expertise de Frank scalable et reproductible.

---

## 3. État du Repo — Ce qui existe et ce qui n'existe pas

### Structure racine

```
vectora-inbox - claude/
├── CLAUDE.md                    # Règles de travail Frank ↔ Claude (V1.5, ~1100 lignes)
├── STATUS.md                    # Tableau de bord vivant du projet
├── README.md                    # Court, générique
├── canonical/                   # Ontologie et config métier (EXISTANT, actif)
├── config/                      # Configs clients (VIDE — aucun fichier)
├── data/                        # Datalake (VIDE — aucun item)
├── docs/                        # Documentation (NETTOYÉ — 27 fichiers utiles)
├── scripts/
│   ├── legacy_reference/        # Code V3 conservé pour inspiration (30+ fichiers Python)
│   ├── runtime/                 # VIDE (.gitkeep)
│   ├── onboarding/              # VIDE (.gitkeep)
│   └── maintenance/             # VIDE (.gitkeep)
├── src_vectora_inbox_v1/        # CODE PRINCIPAL — entièrement VIDE (7 .gitkeep)
├── tests/                       # Tests legacy V3 (Bedrock) — non applicables à V1
└── archive/                     # Legacy pre-pivot archivé
```

**Réalité : zéro ligne de code V1 n'existe.** Tout est en plan et en config. C'est le bon moment pour un audit.

### Ce qui existe dans `canonical/` (actif, à auditer)

```
canonical/
├── ecosystems/
│   └── lai_ecosystem_definition.yaml       # Définition écosystème LAI
├── events/
│   ├── event_type_definitions.yaml
│   └── event_type_patterns.yaml
├── imports/                                 # Référentiels métier (seed companies, glossaire, etc.)
├── ingestion/
│   └── ingestion_profiles.yaml             # Profils d'ingestion (broad, focused, etc.)
│   # MANQUANT : source_configs.yaml, filter_rules.yaml (référencés dans le design)
├── parsing/
│   ├── html_selectors.yaml                 # Sélecteurs CSS par source (8 lignes, Camurus seulement)
│   └── parsing_config.yaml                 # Patterns de dates par source_type
│   # MANQUANT : url_canonicalization.yaml (critique pour item_id)
├── prompts/
│   └── normalization/
│       └── generic_normalization.yaml      # Prompt V2.0 — vertical-agnostic (existant)
├── scopes/
│   ├── company_scopes.yaml                 # 200+ entreprises LAI
│   ├── exclusion_scopes.yaml
│   ├── indication_scopes.yaml
│   ├── molecule_scopes.yaml
│   ├── technology_scopes.yaml
│   └── trademark_scopes.yaml
└── sources/
    ├── html_extractors.yaml                # Config extraction HTML spécifique (Camurus)
    ├── source_candidates.yaml              # 176 candidats non validés
    └── source_catalog.yaml                 # Sources actives (MVP LAI — 8+ sources)
```

### Observations préliminaires sur `canonical/` (à creuser en audit)

1. **`source_catalog.yaml` mélange plusieurs préoccupations** : metadata source (homepage, RSS URL), config d'ingestion (ingestion_mode, max_content_length), ET patterns de dates (date_extraction_patterns). C'est 3 niveaux de config dans un seul fichier.

2. **`ingestion_profiles.yaml` a des commentaires legacy Bedrock** ("économiser les ressources Bedrock") — le contenu est réutilisable mais le contexte est dépassé.

3. **`canonical/ingestion/source_configs.yaml` n'existe pas** — référencé dans le design comme fichier pivot du workflow Discovery → Validation → Promotion.

4. **`canonical/parsing/url_canonicalization.yaml` n'existe pas** — critique pour le calcul de l'`item_id`.

5. **`html_extractors.yaml` (60 lignes) vs `html_selectors.yaml` (8 lignes)** — deux fichiers couvrant le même domaine (extraction HTML par source) avec des formats différents.

---

## 4. L'Architecture Cible — Résumé des décisions clés

*Document de référence complet : `docs/architecture/datalake_v1_design.md` (V1.4, 1093 lignes)*

### Format de stockage

**JSONL append-only** partitionné par mois de publication (`data/datalake_v1/raw/items/YYYY/MM/items.jsonl`), avec **indexes JSON séparés** (`by_item_id`, `by_source_key`, `by_ecosystem`, `by_event_type`, etc.) mis à jour incrémentalement.

Exception à l'append-only : enrichissement de tags d'écosystème (update in-place sur la ligne JSONL via `line_number` stocké dans `by_item_id`).

### Identifiant unique

`item_id = {source_key}__{sha256(canonical_url)[:16]}`

### Pipeline runtime

```
INGEST → DETECT (gap raw\curated) → NORMALIZE (LLM)
```

Chaque étape indépendante, orchestrable séparément ou enchaînée via `run_pipeline.py`.

### Workflow onboarding source (hors runtime)

```
DISCOVERY → VALIDATION → PROMOTION
```

176 candidats dans `source_candidates.yaml`, 8 sources validées en MVP.

### Structure du code cible

```
src_vectora_inbox_v1/
├── config/          # Loaders canonical + client
├── datalake/        # Abstraction JSONL + indexes + cache
├── ingest/          # Pipeline ingestion runtime
├── detect/          # Gap analysis raw\curated
├── normalize/       # Pipeline normalisation LLM
├── sources/         # Workflow onboarding (hors runtime)
└── stats/           # Health, daily stats, reports
```

### Scripts CLI prévus

20+ scripts séparés : `run_ingest.py`, `run_normalize.py`, `run_pipeline.py`, `discover_source.py`, `validate_source.py`, `promote_source.py`, `onboard_source.py`, `rebuild_indexes.py`, `rebuild_cache.py`, `revalidate_all.py`, `generate_report.py`, `retry_failed.py`...

### Méthode de travail Frank ↔ Claude

Décrite dans `CLAUDE.md` (V1.5, ~1100 lignes). Principes clés :
- Plan → Validation → Exécution (jamais de code sans plan validé)
- Développement par mini-sprints (30min–4h, un fichier de plan par sprint)
- Git depuis VS Code uniquement (sandbox Linux instable pour git)
- Modèles : Haiku pour les tâches mécaniques, Sonnet pour le développement, Opus exceptionnellement
- STATUS.md comme mémoire externalisée du projet

---

## 5. Les Tensions Identifiées — Points à Auditer

Ces points ont été identifiés par Sonnet lors de la lecture du repo. Opus doit les analyser avec esprit critique, donner son verdict (conserver / modifier / rejeter), et proposer des alternatives si pertinent.

### 5.1 Tension architecturale — JSONL + JSON indexes vs SQLite

**Le choix** : JSONL append-only + 10+ fichiers JSON d'index par niveau (raw et curated), mis à jour incrémentalement à chaque insert.

**Arguments pour (dans le design)** : diffable, rebuildable, simple à inspecter à l'œil, pas de dépendance externe, portable.

**Questions critiques** :
- La mise à jour incrémentale de 6-10 fichiers JSON à chaque insert est-elle atomique ? Que se passe-t-il en cas de crash entre l'écriture JSONL et la mise à jour des indexes ?
- L'exception "update in-place" pour l'enrichissement de tags d'écosystème (modifier une ligne à un `line_number` précis dans un fichier JSONL) est-elle implémentable proprement sans risquer de corrompre le fichier ?
- SQLite (stdlib Python, `import sqlite3`) offrirait ACID natif, requêtes composées simples, pas de gestion d'indexes manuelle, et resterait local-first. Pour un solo non-développeur, est-ce vraiment plus complexe à opérer qu'un système maison de JSONL + JSON ?
- Le "diffs lisibles à l'œil" est-il un vrai avantage opérationnel pour Frank, ou une préférence esthétique ?
- **Verdict demandé** : maintenir JSONL + JSON indexes, ou pivoter vers SQLite ? Ou solution hybride (SQLite pour les indexes, JSONL pour les items) ?

### 5.2 Tension d'implémentation — Le `line_number` dans `by_item_id`

**Le design** : l'index `by_item_id` stocke `{item_id → {year, month, line_number}}` pour permettre un lookup O(1) d'un item dans le JSONL. Et pour l'update in-place des tags d'écosystème, le moteur seek() à ce `line_number` et réécrit la ligne.

**Questions critiques** :
- Les lignes JSONL ont des longueurs variables. Si une ligne est modifiée (écrite avec des bytes différents), les line_numbers de toutes les lignes suivantes devront-ils être recalculés ?
- En pratique, pour ne pas faire exploser la complexité, il faudrait que la mise à jour de la ligne ne change pas sa longueur (padding ?), ce qui n'est pas garanti.
- Une alternative plus simple : stocker `{item_id → {year, month}}` sans `line_number`, et charger le fichier mensuel entier en mémoire pour un lookup. Pour des volumes MVP (centaines à quelques milliers d'items), est-ce acceptable ?
- Autre alternative : plutôt que d'update in-place, appender un "patch event" à un fichier séparé, et résoudre à la lecture. Plus robuste, mais plus complexe à interroger.

### 5.3 Tension de complexité — 20+ scripts CLI pour un solo non-développeur

**Le design** prévoit 20+ scripts CLI séparés avec des options diverses (`--no-cache`, `--rebuild-cache`, `--retry-failed`, `--parallel`, `--resume`, `--fail-fast`, `--with-discovery`, `--auto-promote`...).

**Questions critiques** :
- Est-ce que Frank saura quel script lancer dans quelle situation, en conditions réelles (un run qui échoue à 3h du matin, un cache corrompu, une source qui change d'URL) ?
- Une CLI unifiée style `python vectora.py ingest --client mvp`, `python vectora.py normalize`, `python vectora.py source discover --key camurus` serait-elle plus opérable ?
- Ou à l'inverse : 4 scripts principaux (`run_pipeline.py`, `onboard_source.py`, `rebuild.py`, `report.py`) avec flags, et les scripts utilitaires en sous-commandes ?
- **Verdict demandé** : consolider les scripts CLI ? Comment ?

### 5.4 Tension de priorisation — Le workflow Discovery/Validation/Promotion en V1

**Le design** : workflow complet d'onboarding de source (Discovery automatique, Validation, Promotion) avec scripts dédiés et 176 candidats dans `source_candidates.yaml`.

**Réalité V1** : on démarre avec 8 sources déjà "validées" (connues et configurées dans `source_catalog.yaml`). Le workflow Discovery/Validation/Promotion est décrit pour le Niveau 2 (Cœur), pas le Niveau 1.

**Questions critiques** :
- Est-il pertinent d'implémenter ce workflow complet en V1 alors qu'on a déjà 8 sources configurées ?
- Le module `sources/` (discovery, validation, promoters, revalidator) représente une part significative de la complexité du code. Peut-on le simplifier en V1 à "éditer manuellement `source_catalog.yaml` pour ajouter une source", avec le workflow automatisé reporté au Niveau 2 ?
- Inversement, coder le Discovery dès le Niveau 1 permettrait d'utiliser les 176 candidats plus vite. Est-ce un avantage stratégique qui justifie la complexité ?

### 5.5 Tension de design — `source_catalog.yaml` fait trop de choses

**Observation** : `source_catalog.yaml` contient actuellement (pour chaque source) : metadata business (company_id, homepage_url), config d'ingestion (rss_url, html_url, ingestion_mode, ingestion_profile), ET patterns de dates (date_extraction_patterns en inline regex Python). Soit 3 niveaux de préoccupation dans un seul fichier.

**Questions critiques** :
- La séparation `source_catalog.yaml` (qui) / `source_configs.yaml` (comment) décrite dans le design V1 est-elle déjà la bonne réponse, et suffit-elle ?
- Les `date_extraction_patterns` par source devraient-ils être dans `parsing/parsing_config.yaml` (qui a déjà une section `date_patterns` par `source_type`) plutôt qu'inline dans chaque source ?
- Les regex Python en dur dans un YAML (ex: `r"(\w+ \d{1,2}, \d{4})\w*"`) sont-ils maintenables par un non-développeur ? Est-ce le bon endroit ?

### 5.6 Tension de schéma — Le curated est-il assez riche pour alimenter une newsletter ?

**Le design** : l'item curated contient summary, event.type, entities (companies, molecules, technologies, trademarks), curation metadata (modèle, coût, latence).

**Ce qui manque pour une newsletter** :
- **Score de pertinence / importance relative** : sans scoring, comment un consommateur newsletter sélectionne les 5 meilleurs items parmi 50 ? Le design a délibérément supprimé le scoring (legacy newsletter). Mais sans aucun signal de priorisation, la sélection éditoriale sera 100% manuelle.
- **Section éditoriale suggérée** : "Partnerships", "Regulatory", "Clinical Updates" — ces sections correspondent à `event.type`, mais le mapping n'est pas explicite.
- **Indicateur de nouveauté relative** : un item daté d'il y a 6 jours et un item daté d'hier ont le même `published_at` — pas de signal de "fraîcheur" dans le curated.

**Questions critiques** :
- Faut-il ajouter un champ `relevance_score` calculé de façon déterministe (sans LLM) au moment de la curation, basé sur des règles métier simples (pure_player = +1, regulatory = +1, trademark mention = +1, recency = variable) ? Cela ne recrée pas le "scoring bedrock" legacy mais donne un signal minimal pour la sélection newsletter.
- Ou est-il préférable de laisser le datalake neutre et de créer une couche de scoring dans le consommateur newsletter (hors scope V1) ?
- Le curated tel que conçu est-il suffisamment riche pour supporter les cas d'usage downstream (newsletter, rapport, RAG) ?

### 5.7 Tension de méthode — CLAUDE.md est-il trop long et trop dense ?

**Observation** : CLAUDE.md fait ~1100 lignes, 20 sections, couvre les règles de travail, les conventions de code, les conventions git, la gestion des coûts, la documentation vivante, les mini-sprints, la résilience aux plantages, et la gestion des modèles. C'est exhaustif.

**Questions critiques** :
- Un document de règles de 1100 lignes est-il réellement lu et respecté en entier à chaque session, ou certaines sections sont-elles ignorées en pratique ?
- Quelles sections sont essentielles et quelles sont accessoires ? Peut-on identifier un "CLAUDE.md core" de 200 lignes qui capture les règles les plus importantes ?
- Y a-t-il des règles contradictoires ou impossibles à respecter simultanément dans les conditions réelles de travail ?
- La discipline des mini-sprints (un fichier `.md` par sprint, plan validé avant code) est-elle réaliste pour un projet où Frank travaille seul et peut vouloir avancer vite ? Est-ce un overhead justifié ou une bureaucratie contre-productive ?

### 5.8 Tension de séquencement — Le Niveau 1 est-il bien découpé ?

**Le Niveau 1 (Fondations)** a pour critère de fin : `python run_pipeline.py --source press_corporate__medincell` produit 1 item raw puis 1 item curated. Pour y arriver, il faut implémenter : URL canonicalization, item_id, datalake storage (JSONL + indexes), URL cache, HTTP fetcher, parser HTML, filtres canonical, orchestrateur, LLM client Anthropic, parser de réponse LLM, validator anti-hallucination, résolution canonical_id, curation_log.

C'est ~15 composants pour produire 1 item. Le plan prévoit 8 mini-sprints.

**Questions critiques** :
- Est-ce que l'approche "bottom-up" (construire chaque composant proprement avant de les assembler) est la bonne, ou une approche "walking skeleton" (faire tourner le pipeline end-to-end en mode dégradé d'abord, puis renforcer chaque composant) serait-elle plus adaptée à un solo non-développeur qui a besoin de voir des résultats rapidement ?
- Y a-t-il des composants du Niveau 1 qu'on pourrait simplifier radicalement pour le MVP (ex: pas d'index JSON sophistiqué, juste `items.jsonl` + recherche linéaire, pour démarrer) et complexifier seulement si le besoin se confirme ?
- Le fait que la normalisation LLM soit incluse dans le Niveau 1 (et pas reportée au Niveau 2) est-il le bon choix ? Ou faudrait-il avoir un Niveau 0.5 "juste ingestion raw qui fonctionne" avant d'attaquer la curation ?

### 5.9 Tension opérationnelle — Où vit le code dans une architecture Windows + Cowork ?

**Réalité** : Le repo est dans `C:\Users\franc\OneDrive\Bureau\vectora-inbox - claude\`. Il est monté dans la sandbox Linux de Cowork. Les commandes git échouent depuis la sandbox. Les tests Python peuvent-ils être lancés depuis la sandbox ? Ou faut-il VS Code pour tout ce qui est exécution ?

**Questions critiques** :
- Quel est le workflow réaliste de développement ? Cowork écrit le code → Frank lance les tests depuis VS Code → Cowork lit les résultats ? Ou Cowork peut-il exécuter Python dans sa sandbox sur les fichiers du repo ?
- OneDrive introduit-il des risques (sync en cours pendant un run, fichiers verrouillés, latence) qui pourraient affecter la stabilité du moteur ? Est-ce un risque à mitiger ou à ignorer pour le MVP ?
- La recommandation de déplacer le repo hors OneDrive (mentionnée dans STATUS.md `future_optimizations` #10) est-elle urgente ou peut-elle attendre ?

---

## 6. Ce que l'Audit doit Produire

### Format attendu

Un document structuré avec, pour chaque tension identifiée (§5.1 à §5.9) ET pour toute autre tension identifiée par Opus lui-même :

1. **Verdict** : conserver tel quel / modifier / rejeter / indécis
2. **Analyse** (3-5 phrases) : pourquoi ce verdict, les trade-offs réels
3. **Recommandation concrète** si modification : qu'est-ce qu'on change exactement, dans quel fichier, avec quel impact

Et en synthèse finale :
- **Top 3 risques** pour le projet si on démarre le développement maintenant sans changement
- **Top 3 quick wins** : les changements les plus faciles à faire avant de démarrer qui auraient le plus d'impact
- **Questions à poser à Frank** : ce que l'audit ne peut pas trancher sans input métier ou de priorité de Frank

### Ce que l'Audit NE doit PAS faire

- Réécrire le design en entier
- Proposer une architecture radicalement différente sans justification solide
- Ignorer les contraintes de Frank (solo, non-développeur, Windows, budget limité)
- Produire un rapport générique sur "les best practices du datalake" déconnecté du contexte
- Valider sans esprit critique (le but est de trouver les vraies failles, pas de rassurer)

---

## 7. Fichiers Clés à Lire (si Opus veut approfondir)

| Fichier | Pourquoi |
|---|---|
| `docs/architecture/datalake_v1_design.md` | Architecture complète (§3 format, §4 indexes, §6 pipeline, §7 cache, §10 config client, §12 code) |
| `docs/business/contexte_business_v1.md` | Vision produit, profil Frank, stack produit |
| `CLAUDE.md` | Règles de travail complètes (§3 méthode, §6 git, §17 small batches, §18 sprints, §20 modèles) |
| `canonical/sources/source_catalog.yaml` | État réel de la config sources (voir tension §5.5) |
| `canonical/ingestion/ingestion_profiles.yaml` | Profils d'ingestion existants |
| `canonical/prompts/normalization/generic_normalization.yaml` | Prompt LLM de normalisation |
| `docs/architecture/level_1_plan.md` | Plan détaillé du Niveau 1 (mini-sprints prévus) |
| `scripts/legacy_reference/src_v3/ingest/` | Code legacy V3 — ce qui a été construit avant le pivot |
| `STATUS.md` | Où on en est dans la roadmap |

---

## 8. Instructions pour Opus

1. **Lire ce brief en entier d'abord**, puis décider quels fichiers supplémentaires consulter.
2. **Ne pas commencer par valider** — commencer par chercher les failles.
3. **Calibrer chaque recommandation** sur le profil de Frank : solo, non-dev, Windows, budget limité, expertise métier très forte.
4. **Être concret** : "modifier `source_catalog.yaml` pour séparer les concerns" plutôt que "améliorer la séparation des responsabilités".
5. **Trancher** : ne pas répondre "ça dépend" sans expliquer de quoi ça dépend et quelle option tu recommandes par défaut.
6. **Signaler** si tu identifies des tensions non listées dans §5 — c'est probable et bienvenu.

---

*Brief rédigé le 2026-04-25. Zéro code V1 n'existe. C'est le meilleur moment pour un audit.*
