# Vectora Inbox – Overview

**A clear, structured guide to the Vectora Inbox MVP**  
For humans discovering the project, cloud architects, and AI assistants (Amazon Q Developer / ChatGPT).

---

## 1. Vision and Ambition

### 1.1 What is Vectora Inbox?

Vectora Inbox is a **configurable sector intelligence engine** designed for biotech/pharma competitive monitoring. It automatically produces professional, strategic newsletters by:

- **Aggregating** heterogeneous public sources (RSS feeds, APIs, regulatory databases),
- **Normalizing** content into a common JSON schema using **Amazon Bedrock** as the linguistic brain,
- **Filtering** items based on client-specific domains of interest ("scopes"),
- **Scoring** and prioritizing items using transparent, rule-based logic,
- **Assembling** a structured newsletter in Markdown using **Amazon Bedrock** for editorial quality.

### 1.2 What problem does it solve?

For a solo founder or consultant managing multiple clients:

- **Automated competitive intelligence**: No manual scanning of dozens of sources daily.
- **Multi-client support**: One shared architecture serves many clients with different interests.
- **Configurable quality**: Improve results over time by tuning scopes, keywords, and scoring—without changing code.
- **Professional output**: Clients receive a well-structured, actionable newsletter on a regular schedule.
- **AI-powered understanding**: Bedrock handles the hard linguistic tasks (entity extraction, event classification, editorial writing).

### 1.3 Why this design?

The system is designed to be:

- **Simple**: Minimal AWS services (S3 + Lambda + Bedrock), easy to debug and maintain.
- **Robust**: Configuration-driven, no client-specific logic hardcoded.
- **Scalable**: Add new clients by creating a config file, not by writing new code.
- **Maintainable**: A solo founder can operate and improve it without a large team.
- **Hybrid intelligence**: Bedrock for linguistic tasks, deterministic rules for matching/scoring.

---

## 2. High-Level Architecture

### 2.1 AWS Environment

- **AWS Account**: `786469175371`
- **Region**: `eu-west-3` (Paris)
- **Profile**: `rag-lai-prod` (AWS SSO admin role)

All Vectora Inbox resources are prefixed with `vectora-inbox-` for easy identification.

### 2.2 The 3 S3 Buckets

| Bucket Name | Purpose | Key Prefixes |
|-------------|---------|--------------|
| **`vectora-inbox-config`** | Stores canonical scopes (shared) and client config files (per-client) | `canonical/...`<br>`clients/<client_id>.yaml` |
| **`vectora-inbox-data`** | Stores raw and normalized items for each client | **RAW**: `raw/<client_id>/<source_key>/<YYYY>/<MM>/<DD>/raw.json`<br>**Normalized**: `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json` |
| **`vectora-inbox-newsletters`** | Stores rendered newsletters (Markdown first, later HTML/PDF) | `<client_id>/<YYYY>/<MM>/<DD>/newsletter.md` |

**Important notes on `vectora-inbox-data` layout:**

- **RAW layer** (optional but useful for debugging and replays):
  - Path: `raw/<client_id>/<source_key>/<YYYY>/<MM>/<DD>/raw.json`
  - Where `source_key` = unique ID for the source (e.g., `press_corporate__fiercepharma`, `press_sector__endpointsnews`, `pubmed_lai`, `ctgov_lai`)
  - Purpose: Store raw payloads fetched from RSS/APIs, keep per-source history for debugging, quality checks, and re-normalization.

- **Normalized layer** (input for the engine):
  - Path: `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`
  - This file aggregates all normalized items for a given client and day, across all sources.
  - Each normalized item MUST contain `source_key` and `source_type` fields.

- **The engine Lambda only reads from normalized/**, not from raw/. RAW exists as a useful "debug/replay" layer.

### 2.3 The 2 Lambda Functions

| Lambda Name | Purpose | Uses Bedrock? | Inputs | Outputs |
|-------------|---------|---------------|--------|---------|
| **`vectora-inbox-ingest-normalize`** | Fetches data from sources (RSS, APIs), normalizes items into common JSON schema | **Yes** (for entity extraction, event classification, summaries) | Source definitions (RSS feeds, API endpoints) from config | Normalized items in `s3://vectora-inbox-data/normalized/<client>/...` |
| **`vectora-inbox-engine`** | Reads normalized items + client config, performs matching + scoring, assembles newsletter | **Yes** (for newsletter writing: intros, TL;DR, editorial summaries) | Normalized items from S3, client config from S3, canonical scopes from S3 | Newsletter Markdown in `s3://vectora-inbox-newsletters/<client>/...` |

### 2.4 Where Amazon Bedrock is Used

**Key principle: Bedrock is the "linguistic brain" of Vectora Inbox.**

**Bedrock IS used for:**
- **Phase 1B (Normalization)**: Entity extraction, event type classification, generating concise summaries.
- **Phase 4 (Newsletter Assembly)**: Writing intros, TL;DR, section summaries, rewriting items in the client's tone/voice.

**Bedrock is NOT used for:**
- **Phase 1A (Ingestion)**: HTTP requests, RSS parsing, JSON decoding (pure plumbing).
- **Phase 2 (Matching)**: Set intersections, domain matching (deterministic logic).
- **Phase 3 (Scoring)**: Numeric scoring rules (transparent, explainable).

**Architecture principle:**
- **Bedrock** = understand and write text.
- **Lambda + S3 + configs** = plumbing, skeleton, and organs.

### 2.5 High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VECTORA INBOX MVP FLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

  External Sources                    AWS (eu-west-3, account 786469175371)
  ────────────────                    ────────────────────────────────────

  • RSS feeds          ──┐
  • APIs (ClinicalTrials) │
  • PubMed, FDA, etc.  ──┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Lambda:                 │
              │  vectora-inbox-          │
              │  ingest-normalize        │
              │                          │
              │  • Fetch raw content     │
              │  • Extract entities      │
              │  • Normalize to JSON     │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  S3: vectora-inbox-data  │
              │  normalized/<client>/    │
              │  <YYYY>/<MM>/<DD>/       │
              │  items.json              │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  Lambda:                 │
              │  vectora-inbox-engine    │
              │                          │
              │  • Load client config    │
              │  • Match items to scopes │
              │  • Score & rank items    │
              │  • Assemble newsletter   │
              └──────────┬───────────────┘
                         │
                         ▼
              ┌──────────────────────────┐
              │  S3: vectora-inbox-      │
              │  newsletters/<client>/   │
              │  <YYYY>/<MM>/<DD>/       │
              │  newsletter.md           │
              └──────────────────────────┘
                         │
                         ▼
                    Client receives
                    newsletter (email,
                    web portal, etc.)
```

---

## 3. End-to-End Workflow (Phases)

The Vectora Inbox workflow is divided into 5 phases, from configuration to final newsletter delivery.

### Summary Table

| Phase | Lambda | Uses Bedrock? | Inputs | Outputs | S3 Paths | Admin Levers |
|-------|--------|---------------|--------|---------|----------|--------------||
| **Phase 0: Configuration** | None (manual) | No | Canonical scopes, client requirements | Config YAML files | `s3://vectora-inbox-config/canonical/...`<br>`s3://vectora-inbox-config/clients/<client_id>.yaml` | Add/update scopes, keywords, domains, layout |
| **Phase 1A: Ingestion** | `vectora-inbox-ingest-normalize` | **No** | Source definitions (RSS, APIs) | Raw items (in memory) | Optional: `s3://vectora-inbox-data/raw/<client>/...` | Add/remove sources |
| **Phase 1B: Normalization** | `vectora-inbox-ingest-normalize` | **Yes** | Raw items, canonical scopes, event patterns | Normalized JSON items | `s3://vectora-inbox-data/normalized/<client>/<YYYY>/<MM>/<DD>/items.json` | Refine prompts, adjust entity extraction |
| **Phase 2: Matching** | `vectora-inbox-engine` | **No** | Normalized items, client config, canonical scopes | Matched items (in memory) | N/A (intermediate) | Tune watch domains, scopes |
| **Phase 3: Scoring** | `vectora-inbox-engine` | **No** | Matched items, scoring rules | Ranked items (in memory) | N/A (intermediate) | Tune scoring weights, domain priorities |
| **Phase 4: Newsletter Assembly** | `vectora-inbox-engine` | **Yes** | Ranked items, newsletter layout, client profile | Newsletter Markdown | `s3://vectora-inbox-newsletters/<client>/<YYYY>/<MM>/<DD>/newsletter.md` | Adjust tone, layout, editorial prompts |

---

### Phase 0 – Canonical & Client Configuration

**What happens:**  
The admin defines the "knowledge base" and client-specific settings before any automation runs.

**Canonical configuration** (shared across all clients):
- **Company scopes**: Lists of companies grouped by sector or technology (e.g., LAI companies, addiction-focused companies).
- **Molecule scopes**: Lists of molecules grouped by therapeutic area or technology.
- **Technology keywords**: Terms like "long acting", "depot", "microparticle", "implant".
- **Indication keywords**: Terms like "opioid use disorder", "schizophrenia", "diabetes".
- **Exclusion keywords**: Terms to filter out noise (e.g., "job posting", "webinar").
- **Event type patterns**: Rules to classify items (e.g., "clinical_update", "partnership", "approval").

**Client configuration** (one YAML file per client):
- **Client profile**: Name, language, tone, frequency (weekly, monthly).
- **Watch domains**: Logical groupings of interest (e.g., "tech_lai_ecosystem", "indication_addiction").
  - Each domain references canonical scopes (companies, molecules, technologies, indications).
  - Each domain can add client-specific entities (extra companies, molecules, keywords).
  - Each domain has a priority (high, medium, low).
- **Newsletter layout**: Section titles, max items per section, mapping to watch domains.
- **Newsletter delivery**: Format (Markdown, HTML, PDF), distribution method (email, S3, etc.).

**Where it lives:**
- Canonical: `s3://vectora-inbox-config/canonical/scopes/`
  - `company_scopes.yaml`
  - `molecule_scopes.yaml`
  - `keywords_technologies.yaml`
  - `keywords_indications.yaml`
  - `keywords_exclusions.yaml`
  - `event_type_patterns.yaml`
- Client config: `s3://vectora-inbox-config/clients/<client_id>.yaml`

## Canonical, scopes et verticales

### Principe fondamental : un canonical global pour Vectora Inbox

Les fichiers `canonical/scopes/*.yaml` sont des **bibliothèques globales** partagées par toutes les newsletters et tous les clients de Vectora Inbox. Il n'existe **pas de fichiers canonical séparés par verticale**.

Chaque fichier canonical contient **plusieurs scopes**, identifiés par des **clés** :

- `canonical/scopes/company_scopes.yaml` : toutes les listes de sociétés (LAI, oncologie, thérapie génique, etc.)
- `canonical/scopes/molecule_scopes.yaml` : toutes les listes de molécules
- `canonical/scopes/trademark_scopes.yaml` : toutes les listes de marques commerciales
- `canonical/scopes/technology_scopes.yaml` : toutes les listes de technologies
- `canonical/scopes/indication_scopes.yaml` : toutes les listes d'indications thérapeutiques
- `canonical/scopes/exclusion_scopes.yaml` : toutes les listes de mots-clés d'exclusion

### Comment les verticales sont représentées

Les **verticales** (LAI, oncologie, thérapie génique, etc.) sont encodées par le **préfixe des clés**, pas par des fichiers séparés.

**Exemple dans `company_scopes.yaml` :**

```yaml
# Verticale LAI (Long-Acting Injectables)
lai_companies_global:
  - Camurus
  - Alkermes
  - Indivior
  - Johnson & Johnson

lai_companies_addiction:
  - Camurus
  - Alkermes
  - Indivior

lai_companies_psychiatry:
  - Alkermes
  - Johnson & Johnson
  - Otsuka

# Verticale oncologie (exemple futur)
oncology_companies_global:
  - Roche
  - Pfizer
  - Merck

oncology_companies_solid_tumors:
  - Roche
  - Bristol Myers Squibb
```

**Règle de nommage :**
- Format : `{verticale}_{dimension}_{segment}`
- Exemples :
  - `lai_companies_global` : toutes les sociétés LAI
  - `lai_molecules_addiction` : molécules LAI pour l'addiction
  - `oncology_companies_solid_tumors` : sociétés oncologie spécialisées tumeurs solides

### Comment les configs clients utilisent les scopes

Les configurations clients **référencent simplement les clés** des scopes qu'ils souhaitent utiliser :

**Exemple dans `clients/lai_weekly.yaml` :**

```yaml
watch_domains:
  - id: tech_lai_ecosystem
    type: technology
    company_scope: "lai_companies_global"      # Référence la clé dans company_scopes.yaml
    molecule_scope: "lai_molecules_all"        # Référence la clé dans molecule_scopes.yaml
    technology_scope: "lai_keywords"
    priority: high

  - id: indication_addiction
    type: indication
    company_scope: "lai_companies_addiction"   # Référence une autre clé
    molecule_scope: "lai_molecules_addiction"
    indication_scope: "addiction_keywords"
    priority: high
```

### Comment les Lambdas utilisent les scopes

Les Lambdas **ne devinent jamais la verticale**. Elles suivent un processus simple :

1. **Lire la config client** pour obtenir les clés de scopes (ex : `company_scope: "lai_companies_global"`).
2. **Ouvrir le fichier canonical correspondant** (ex : `company_scopes.yaml`).
3. **Charger la liste associée à la clé** (ex : la liste à la clé `"lai_companies_global"`).
4. **Utiliser cette liste** pour le matching, le filtrage, etc.

**Important :**
- Les Lambdas **ne lisent pas les commentaires YAML**.
- Elles ne "détectent" pas qu'un scope est "LAI" ou "oncologie".
- Elles manipulent simplement des listes identifiées par leurs clés.

### Ajouter une nouvelle verticale

Pour ajouter une nouvelle verticale (ex : thérapie génique) :

1. **Dans les fichiers canonical**, ajouter de nouvelles clés avec le préfixe approprié :
   ```yaml
   # Dans company_scopes.yaml
   gene_therapy_companies_global:
     - Bluebird Bio
     - Spark Therapeutics
     - ...
   
   # Dans molecule_scopes.yaml
   gene_therapy_molecules_all:
     - Zolgensma
     - Luxturna
     - ...
   ```

2. **Dans la config client**, référencer ces nouvelles clés :
   ```yaml
   watch_domains:
     - id: tech_gene_therapy
       company_scope: "gene_therapy_companies_global"
       molecule_scope: "gene_therapy_molecules_all"
   ```

3. **Les Lambdas n'ont pas besoin de changer** : elles continuent de charger les listes via les clés fournies.

### Séparation des responsabilités

**Canonical :**
- Définit les scopes disponibles et leur contenu (listes).
- Peut héberger plusieurs verticales dans le même fichier (via préfixes).
- Maintenu par l'admin.

**Config client :**
- Choisit quels scopes utiliser en référençant leurs clés.
- Combine les scopes dans des `watch_domains`.
- Peut ajouter des entités spécifiques au client.

**Lambdas :**
- N'infèrent pas les verticales.
- Chargent simplement les listes données par les clés dans la config client.
- Effectuent des opérations d'ensemble (intersections, unions) avec ces listes.

**Admin levers to improve quality:**
- **Add new scopes**: Expand canonical lists with new companies, molecules, or keywords.
- **Refine keywords**: Add synonyms, remove false positives.
- **Adjust watch domains**: Change which scopes are active for a client, adjust priorities.
- **Tune layout**: Change section titles, max items, order of sections.

**Effect on final newsletter:**  
Configuration determines which items are matched, how they are scored, and how the newsletter is structured.

---

## Catalogue des sources et bouquets

### Qu'est-ce que le catalogue de sources ?

Le **catalogue de sources** (`canonical/sources/source_catalog.yaml`) est un fichier global qui répond à une question simple :

> **"Quelles sources (flux RSS, APIs, sites web) Vectora Inbox sait-il lire ?"**

Ce catalogue est **partagé** par :
- Toutes les verticales (LAI, thérapie génique, oncologie, etc.),
- Tous les clients,
- Toutes les newsletters.

Il contient deux grandes sections :
1. **`sources:`** → une liste d'entrées individuelles (une par flux RSS, endpoint API, ou site web),
2. **`bouquets:`** → des regroupements logiques de sources pour simplifier les configurations clients.

### Structure d'une entrée de source

Chaque entrée dans la section `sources:` décrit **un point d'entrée unique** pour récupérer du contenu.

**Champs obligatoires :**
- `source_key` : identifiant unique de la source (ex : `press_corporate__medincell`, `press_sector__pharmaphorum`)
- `source_type` : catégorie de la source (ex : `press_corporate`, `press_sector`, `pubmed`, `ctgov`)
- `url` : adresse du flux RSS ou de l'endpoint API (peut être vide `""` si à compléter)
- `default_language` : langue par défaut du contenu (`"en"`, `"fr"`, etc.)

**Champs optionnels importants :**
- `vertical_tags` : liste de tags métiers pour documenter la pertinence (ex : `["lai"]`, `["pharma-biotech"]`)
- `notes` : description libre en français pour l'administrateur (but, périmètre, à compléter, etc.)

**Exemple d'une source corporate LAI :**

```yaml
# Exemple d'entrée corporate LAI dans source_catalog.yaml
sources:
  - source_key: "press_corporate__medincell"
    source_type: "press_corporate"
    url: "https://www.medincell.com/"        # à adapter plus tard au vrai flux
    default_language: "en"
    vertical_tags: ["lai"]
    notes: "Site institutionnel MedinCell (point d'entrée pour récupérer les news LAI)."
```

**Exemple d'une source de presse sectorielle pharma/biotech :**

```yaml
# Exemple de presse sectorielle pharma/biotech
sources:
  - source_key: "press_sector__biocentury"
    source_type: "press_sector"
    url: "https://placeholder/biocentury.rss"
    default_language: "en"
    vertical_tags: ["pharma-biotech"]
    notes: "Presse biotech/pharma orientée financement et stratégie (BioCentury)."
```

### Différence entre sources corporate et sources sectorielles

**Sources corporate** (`press_corporate`) :
- Sites web ou flux RSS des **entreprises elles-mêmes**
- Exemples : MedinCell, Camurus, Alkermes
- Contenu typique : communiqués de presse, résultats cliniques, partenariats
- Utiles pour suivre l'actualité d'une société spécifique

**Sources sectorielles** (`press_sector`) :
- Sites de **presse spécialisée** couvrant un secteur entier
- Exemples : BioCentury, PharmaPhorum, Endpoints News
- Contenu typique : analyses de marché, tendances, actualités multi-entreprises
- Utiles pour avoir une vue d'ensemble du secteur

### Rôle des vertical_tags

Les `vertical_tags` servent principalement à **documenter** la pertinence métier d'une source :
- `["lai"]` : cette source est pertinente pour la verticale Long-Acting Injectables
- `["pharma-biotech"]` : cette source couvre le secteur pharma/biotech en général
- `["gene-therapy"]` : cette source est pertinente pour la thérapie génique

**Important :** Les `vertical_tags` ne sont **pas le mécanisme principal de filtrage** dans le pipeline. Le filtrage métier se fait surtout par :
- Les **scopes canonical** (`canonical/scopes/*.yaml`) qui définissent les listes de sociétés, molécules, technologies, etc.
- La **config client** qui active des bouquets et définit des `watch_domains`
- L'**analyse du contenu** par Bedrock (extraction d'entités, classification d'événements)

Les `vertical_tags` sont utiles pour :
- L'administrateur qui maintient le catalogue ("cette source concerne quelle verticale ?")
- Les futures analyses et statistiques ("combien de sources LAI avons-nous ?")
- La documentation et la compréhension du catalogue

### Qu'est-ce qu'un bouquet de sources ?

Un **bouquet** est un regroupement logique de plusieurs `source_key` dans une unité simple à activer.

**Pourquoi des bouquets ?**
- Éviter d'énumérer 60 sources individuelles dans chaque config client
- Réutiliser des ensembles de sources entre plusieurs clients ou verticales
- Garder les fichiers de configuration **lisibles et maintenables**

**Structure d'un bouquet :**

```yaml
bouquets:
  - bouquet_id: "lai_corporate_all"
    description: "Bouquet pour les flux corporate des principaux acteurs LAI."
    source_keys:
      - "press_corporate__medincell"
      - "press_corporate__camurus"
      - "press_corporate__alkermes"
      # ...

  - bouquet_id: "press_biotech_premium"
    description: "Bouquet pour une sélection de sites de presse biotech/pharma."
    source_keys:
      - "press_sector__pharmaphorum"
      - "press_sector__biocentury"
      - "press_sector__endpoints_news"
      # ...
```

**Exemples de bouquets typiques :**
- `lai_corporate_all` : tous les sites corporate des sociétés LAI suivies
- `press_biotech_premium` : sélection de presse pharma/biotech premium
- `regulatory_fda_ema` : flux réglementaires FDA et EMA (futur)
- `pubmed_lai` : recherches PubMed configurées pour LAI (futur)

### Comment les configs clients utilisent les bouquets

Plutôt que de lister des dizaines de `source_key` individuelles, une config client active simplement des **bouquets** :

```yaml
# Exemple dans clients/lai_weekly.yaml
source_bouquets_enabled:
  - "lai_corporate_all"
  - "press_biotech_premium"

sources_extra_enabled:
  - "press_corporate__special_company"   # optionnel, pour des exceptions
```

**Ce que fait la Lambda d'ingestion :**
1. Lit la config client
2. Résout `source_bouquets_enabled` → obtient la liste complète des `source_key`
3. Ajoute les `sources_extra_enabled` (si présents)
4. Appelle uniquement ces sources-là pour récupérer le contenu

### Différence entre catalogue de sources et scopes canonical

Pour bien comprendre l'architecture, il est important de distinguer :

**Scopes canonical** (`canonical/scopes/*.yaml`) :
- Décrivent des **listes métier** : sociétés, molécules, technologies, indications, etc.
- Exemples : `lai_companies_global`, `lai_molecules_addiction`
- Servent à **analyser le contenu** : matching, scoring, filtrage métier
- Répondent à la question : "Quelles entités métier nous intéressent ?"

**Catalogue de sources** (`canonical/sources/source_catalog.yaml`) :
- Décrit **où aller chercher les textes** : URLs, flux RSS, endpoints API
- Exemples : `press_corporate__medincell`, `press_sector__biocentury`
- Sert à **récupérer le contenu brut** avant analyse
- Répond à la question : "Où lire les actualités ?"

**Bouquets de sources** :
- Regroupent des sources pour simplifier les configurations
- Exemples : `lai_corporate_all`, `press_biotech_premium`
- Servent à **activer facilement** des ensembles de sources
- Répondent à la question : "Quels flux activer pour ce client ?"

**En résumé :**
- **Sources** = points d'entrée pour récupérer du texte
- **Scopes** = listes métier pour interpréter le texte
- **Bouquets** = regroupements de sources pour simplifier les configs

### Exemple complet : du catalogue à la Lambda

**1. Dans `canonical/sources/source_catalog.yaml` :**

```yaml
sources:
  - source_key: "press_corporate__medincell"
    source_type: "press_corporate"
    url: "https://www.medincell.com/feed"
    default_language: "en"
    vertical_tags: ["lai"]
    notes: "Flux RSS MedinCell."

  - source_key: "press_sector__pharmaphorum"
    source_type: "press_sector"
    url: "https://pharmaphorum.com/feed"
    default_language: "en"
    vertical_tags: ["pharma-biotech"]
    notes: "Presse pharma généraliste."

bouquets:
  - bouquet_id: "lai_corporate_all"
    description: "Flux corporate LAI."
    source_keys:
      - "press_corporate__medincell"
      # ... autres sources corporate LAI

  - bouquet_id: "press_biotech_premium"
    description: "Presse biotech premium."
    source_keys:
      - "press_sector__pharmaphorum"
      # ... autres sources presse
```

**2. Dans `clients/lai_weekly.yaml` :**

```yaml
source_bouquets_enabled:
  - "lai_corporate_all"
  - "press_biotech_premium"
```

**3. Dans la Lambda `vectora-inbox-ingest-normalize` :**

```python
# Pseudo-code
client_config = load_client_config("lai_weekly")
source_catalog = load_yaml("canonical/sources/source_catalog.yaml")

# Résoudre les bouquets
active_source_keys = []
for bouquet_id in client_config["source_bouquets_enabled"]:
    bouquet = find_bouquet(source_catalog, bouquet_id)
    active_source_keys.extend(bouquet["source_keys"])

# Pour chaque source active
for source_key in active_source_keys:
    source = find_source(source_catalog, source_key)
    # Appeler l'URL, parser le flux RSS, etc.
    raw_items = fetch_and_parse(source["url"])
    # Normaliser avec Bedrock...
```

### Avantages de cette architecture

**Pour l'administrateur :**
- Un seul catalogue global à maintenir (pas de duplication)
- Ajout facile de nouvelles sources (une entrée dans `sources:`)
- Création simple de nouveaux bouquets (regrouper des `source_key`)
- Réutilisation des sources entre verticales et clients

**Pour les configs clients :**
- Fichiers courts et lisibles (quelques bouquets au lieu de 60 sources)
- Activation rapide de nouveaux flux (ajouter un bouquet)
- Flexibilité pour des exceptions (via `sources_extra_enabled`)

**Pour les Lambdas :**
- Logique simple : résoudre les bouquets → obtenir les `source_key` → appeler les URLs
- Pas de logique métier complexe dans le code d'ingestion
- Séparation claire entre "où lire" (sources) et "quoi chercher" (scopes)

---

### Phase 1A – Ingestion (NO Bedrock)

**What happens:**  
The `vectora-inbox-ingest-normalize` Lambda fetches raw content from external sources.

**Responsibilities:**
- Read canonical + client config to know which sources (`source_key` values) are active.
- For each active `source_key`:
  - Perform HTTP requests (RSS feeds, APIs, etc.).
  - Parse JSON/XML/RSS responses.
  - Extract basic fields: `title`, `description`, `link/url`, `pubDate`, etc.
  - Build a list of **raw items** in memory for that source.

**No Bedrock here:**
- This is pure "plumbing": HTTP calls, RSS parsing, JSON decoding.
- Implemented with normal code (no AI).

**Optional RAW storage:**
- The Lambda may optionally write a single `raw.json` per source under:
  ```
  s3://vectora-inbox-data/raw/<client_id>/<source_key>/<YYYY>/<MM>/<DD>/raw.json
  ```
- Where `source_key` examples: `press_corporate__fiercepharma`, `press_sector__endpointsnews`, `pubmed_lai`, `ctgov_lai`
- Purpose: Debugging, quality checks, and ability to re-normalize later without re-fetching.
- MVP can skip RAW storage initially and focus directly on producing normalized items.

---

### Phase 1B – Normalization (WITH Bedrock)

**What happens:**  
The `vectora-inbox-ingest-normalize` Lambda transforms raw text into a normalized JSON schema.

**Objective:**
Transform raw text (title + body/description) into a **normalized item**.

**Bedrock IS used here to:**
1. **Classify event_type** among a predefined set:
   - `clinical_update`, `partnership`, `regulatory`, `scientific_paper`, `corporate_move`, `financial_results`, `safety_signal`, `manufacturing_supply`.
2. **Detect technologies and indications** when rules are not enough:
   - Use canonical lists (technologies, indications).
   - Use event type patterns from `event_type_patterns.yaml`.
   - Apply explicit instructions in the prompt.
3. **Produce a concise summary** reflecting the "so what" of the item.

**Hybrid approach:**
- First-level entity detection uses canonical keywords (scopes, simple rules).
- Bedrock refines and disambiguates:
  - Among technologies.
  - Among indications.
  - Confirms companies/molecules if needed.

**Normalized JSON schema (example):**
```json
{
  "source_key": "press_corporate__fiercepharma",
  "source_type": "press_corporate",
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "summary": "Camurus reported positive results from a Phase 3 trial of Brixadi (buprenorphine) for opioid use disorder...",
  "url": "https://example.com/article",
  "date": "2025-01-15",
  "companies_detected": ["Camurus"],
  "molecules_detected": ["Brixadi", "buprenorphine"],
  "technologies_detected": ["long acting", "depot"],
  "indications_detected": ["opioid use disorder"],
  "event_type": "clinical_update"
}
```

**Required fields:**
- `source_key`: Unique identifier for the source (e.g., `"press_corporate__fiercepharma"`, `"pubmed_lai"`)
- `source_type`: Category of source (e.g., `"press_corporate"`, `"press_sector"`, `"pubmed"`, `"clinicaltrials"`)

**Inputs:**
- Source definitions (RSS feeds, API endpoints) from canonical/client config.

**Outputs:**
- All normalized items for the client and date written to:  
  `s3://vectora-inbox-data/normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`
- This file aggregates items from all sources (all `source_key` values) for that day.

**What is in scope for the MVP:**
- Start with a limited number of sources (e.g., 5-10 RSS feeds from corporate press and sector press).
- Focus on RSS and simple APIs (ClinicalTrials.gov, PubMed).
- Bedrock-assisted entity extraction and event classification.

**Admin levers to improve quality:**
- **Add/remove sources**: Expand coverage by adding new RSS feeds or APIs.
- **Adjust source priorities**: Mark certain sources as higher quality (affects scoring later).
- **Refine Bedrock prompts**: Improve entity extraction and event classification instructions.
- **Update canonical scopes**: Add synonyms, new companies, molecules, keywords.
- **Refine event type patterns**: Add new patterns to guide Bedrock classification.

**Effect on final newsletter:**  
Better normalization = more accurate matching and scoring = higher quality newsletter.

---

### Phase 2 – Matching (NO Bedrock)

**What happens:**  
The `vectora-inbox-engine` Lambda loads normalized items and client config, then determines which items are relevant to which watch domains.

**Conceptual steps:**

1. **Load client config** from `s3://vectora-inbox-config/clients/<client_id>.yaml`.
2. **Load canonical scopes** from `s3://vectora-inbox-config/canonical/scopes/...`.
3. **Load normalized items** for a given period (e.g., last 7 days) from `s3://vectora-inbox-data/normalized/<client>/<YYYY>/<MM>/<DD>/items.json`.
4. **Match items to watch domains**:
   - For each item, compute intersections:
     - `technologies_detected` ∩ technology scopes
     - `indications_detected` ∩ indication scopes
     - `companies_detected` ∩ company scopes
     - `molecules_detected` ∩ molecule scopes
   - Decide which `watch_domains` the item belongs to based on these intersections and domain definitions.

**No Bedrock here:**
- This is deterministic, rule-based logic: set intersections, if/else.
- Matching must stay explainable and governed by config + canonical.

**Inputs:**
- Normalized items from `s3://vectora-inbox-data/normalized/<client>/...`
- Client config from `s3://vectora-inbox-config/clients/<client_id>.yaml`
- Canonical scopes from `s3://vectora-inbox-config/canonical/scopes/...`

**Outputs:**
- Matched items (in memory, annotated with matching domains).

**Admin levers to improve quality:**
- **Refine watch domains**: Add/remove scopes, add client-specific entities.
- **Adjust domain definitions**: Change intersection logic if needed.

**Effect on final newsletter:**  
Better matching = more relevant items reach the scoring phase.

---

### Phase 3 – Scoring (NO Bedrock)

**What happens:**  
The `vectora-inbox-engine` Lambda computes a numeric score for each matched item.

**Scoring factors (rule-based):**
- **Event relevance**: Clinical updates, approvals, partnerships score higher than press releases.
- **Recency**: More recent items score higher.
- **Domain priority**: Items matching high-priority domains score higher.
- **Key competitors**: Items mentioning top competitors score higher.
- **Key molecules**: Items mentioning priority molecules score higher.
- **Signal depth**: Longer, richer content scores higher.
- **Source type**: Regulatory sources > clinical sources > press > noise.

**No Bedrock here:**
- Scoring is transparent numeric rules (no AI required for MVP).
- All scoring logic is explainable and tunable via config.

**Outputs:**
- Ranked items within each domain, top N selected for each newsletter section.

**Admin levers to improve quality:**
- **Tune scoring weights**: Adjust the relative importance of event type, recency, domain priority, etc.
- **Adjust domain priorities**: Mark certain domains as "high priority" to boost their items.
- **Set thresholds**: Define minimum scores for inclusion in the newsletter.

**Effect on final newsletter:**  
Better scoring = most important items rise to the top = happier clients.

---

### Phase 4 – Newsletter Assembly (WITH Bedrock)

**What happens:**  
The `vectora-inbox-engine` Lambda takes the ranked items and assembles a structured newsletter according to the client's layout preferences.

**Bedrock IS used here to:**
1. **Rewrite individual items** into short, high-quality paragraphs in the specified tone/voice.
2. **Generate newsletter components**:
   - A global newsletter **title**.
   - An **intro/chapeau** setting the context.
   - A **TL;DR** (e.g., bullet points summarizing the week's top signals).
   - **Section introductions** summarizing the week's signals in each domain.

**Conceptual steps:**

1. **Load newsletter layout** from client config (`newsletter_layout` section).
2. **Load client profile** (tone, voice, language) from `client_profile`.
3. **Use Bedrock to generate**:
   - **Title**: e.g., "Weekly Biotech Intelligence – January 15, 2025".
   - **Intro**: A short paragraph setting the context.
   - **TL;DR**: A 2-3 sentence summary of the most important items.
   - **Sections**: Ordered sections (e.g., "LAI Ecosystem", "Addiction Therapeutics", "Regulatory Updates").
     - Each section contains:
       - Section title (from layout config).
       - Top N items (from ranked items in Phase 3).
       - For each item: Bedrock rewrites the summary in the client's tone/voice, with a link to source.
4. **Format as Markdown**:
   - Use headings, bullet points, and links.
   - Keep the tone professional and concise (as specified in client profile).
5. **Write to S3**:
   - Save the newsletter as:  
     `s3://vectora-inbox-newsletters/<client>/<YYYY>/<MM>/<DD>/newsletter.md`

**Inputs:**
- Ranked/selected items from Phase 2 (in memory).
- `newsletter_layout` and `newsletter_delivery` from client config.

**Outputs:**
- Markdown file stored in:  
  `s3://vectora-inbox-newsletters/<client>/<YYYY>/<MM>/<DD>/newsletter.md`
- (Later: HTML and PDF exports can be added.)

**Admin levers to improve quality:**
- **Adjust section structure**: Add/remove sections, change order, change titles.
- **Tune max items per section**: Show more or fewer items based on client feedback.
- **Refine Bedrock prompts**: Adjust editorial instructions for tone, voice, style.
- **Change tone/voice in client profile**: Adjust intro and TL;DR generation (e.g., formal vs. conversational).
- **Set frequency**: Weekly, bi-weekly, or monthly newsletters.

**Effect on final newsletter:**  
Better editorial quality (via Bedrock) + better layout = more readable and actionable newsletter = better client satisfaction.

---

## 4. Multi-Client Support

### 4.1 One Shared Architecture

Vectora Inbox uses a **single shared infrastructure** to serve multiple clients:
- **Same 2 Lambdas** (`vectora-inbox-ingest-normalize`, `vectora-inbox-engine`).
- **Same 3 S3 buckets** (`vectora-inbox-config`, `vectora-inbox-data`, `vectora-inbox-newsletters`).

### 4.2 How Clients Are Differentiated

Different clients are handled by:
- **Separate config YAML files**: `s3://vectora-inbox-config/clients/<client_id>.yaml`
- **Different S3 prefixes**:
  - RAW items: `s3://vectora-inbox-data/raw/<client_id>/<source_key>/...` (optional)
  - Normalized items: `s3://vectora-inbox-data/normalized/<client_id>/...`
  - Newsletters: `s3://vectora-inbox-newsletters/<client_id>/...`

### 4.3 Onboarding a New Client

To add a new client:

1. **Create a new client config YAML** from a template (stored in `/client-config-examples/` in the repo).
2. **Define watch domains**:
   - Select which canonical scopes to activate (companies, molecules, technologies, indications).
   - Optionally add client-specific entities (extra companies, molecules, keywords).
3. **Configure newsletter layout**:
   - Define section titles, max items per section, order of sections.
4. **Set delivery preferences**:
   - Format (Markdown, HTML, PDF).
   - Frequency (weekly, monthly).
   - Distribution method (email, S3, web portal).
5. **Upload the config** to `s3://vectora-inbox-config/clients/<client_id>.yaml`.
6. **Schedule/trigger the Lambdas** for that client:
   - Run `vectora-inbox-ingest-normalize` to fetch and normalize items.
   - Run `vectora-inbox-engine` to generate the first newsletter.

**No code changes required.** All client-specific behavior is driven by configuration.

---

## 5. Admin Levers to Improve Quality Over Time

One of the key strengths of Vectora Inbox is that the admin can continuously improve the system **without changing code**. Here are the main levers:

### 5.1 Update Canonical Scopes

**Where:** `s3://vectora-inbox-config/canonical/scopes/`

**What to change:**
- Add new companies, molecules, technologies, indications.
- Add synonyms and alternative names.
- Remove false positives (e.g., companies with common names that cause noise).

**Effect:**
- Better entity detection in Phase 1 (normalization).
- More accurate matching in Phase 2 (scoring).

### 5.2 Refine Client Configs

**Where:** `s3://vectora-inbox-config/clients/<client_id>.yaml`

**What to change:**
- Adjust watch domains (add/remove scopes, change priorities).
- Add client-specific entities (companies, molecules, keywords).
- Tune newsletter layout (section titles, max items, order).

**Effect:**
- More relevant items in the newsletter.
- Better structure and readability.

### 5.3 Adjust Source Definitions

**Where:** Canonical config or client config (depending on whether sources are shared or client-specific).

**What to change:**
- Add new RSS feeds or API endpoints.
- Remove low-quality sources.
- Adjust source priorities (affects scoring).

**Effect:**
- Broader coverage of relevant content.
- Less noise from low-quality sources.

### 5.4 Tune Scoring Weights

**Where:** Client config or Lambda code (if weights are configurable via config).

**What to change:**
- Adjust the relative importance of event type, recency, domain priority, key competitors, key molecules, signal depth, source type.

**Effect:**
- Items that matter most to the client rise to the top.
- Less important items are filtered out.

### 5.5 Validate Normalized Items

**Where:** `s3://vectora-inbox-data/normalized/<client>/<YYYY>/<MM>/<DD>/items.json`

**What to check:**
- Are entities (companies, molecules, technologies, indications) correctly detected?
- Are event types correctly classified?
- Are there false positives or false negatives?

**Effect:**
- Identify gaps in canonical scopes or entity extraction logic.
- Improve normalization quality over time.

---

## 6. Future Extensions (Beyond MVP)

The MVP is deliberately small and focused:
- **2 Lambdas** (ingest+normalize, engine).
- **3 S3 buckets** (config, data, newsletters).
- **Limited sources** (5-10 RSS feeds, basic APIs).

Possible next steps (not in MVP scope):
- **More sources**: PubMed, FDA, DailyMed, patent databases, social media.
- **Scheduling**: Use AWS EventBridge to trigger Lambdas on a schedule (daily, weekly).
- **UI/Admin console**: Web interface to manage configs, view newsletters, monitor quality.
- **HTML/PDF export**: Convert Markdown newsletters to HTML and PDF.
- **Email delivery**: Integrate with SES to send newsletters directly to clients.
- **Analytics**: Track which items clients click on, which sections are most read.
- **Advanced Bedrock features**: Streaming responses, fine-tuned models, Bedrock Agents (if needed).
- **Bedrock-assisted scoring**: Use Bedrock to refine scoring (beyond MVP's rule-based approach).

**Important:** This document describes the **MVP scope**, not a future platform. The goal is to get a small, reliable system running end-to-end before adding complexity.

---

## 7. Design Principles

### 7.1 Configuration Over Code

- **No client-specific logic in Lambda code.**
- All client-specific behavior comes from config files in S3.
- Clients differ only by:
  - Which scopes they activate.
  - What extra entities they add.
  - How they structure their newsletter.

### 7.2 Simplicity First

- **Two focused Lambdas** that can be tested and debugged easily.
- **Minimal AWS services** (S3 + Lambda + Bedrock, no DynamoDB, RDS, Step Functions, etc.).
- **Clear separation of concerns**:
  - Phase 1A (ingestion) = HTTP plumbing (no Bedrock).
  - Phase 1B (normalization) = linguistic understanding (Bedrock).
  - Phase 2 (matching) = deterministic rules (no Bedrock).
  - Phase 3 (scoring) = transparent numeric rules (no Bedrock).
  - Phase 4 (assembly) = editorial writing (Bedrock).

### 7.3 Extendable Later

- The MVP is designed to be extended without major refactoring.
- More sources, more Lambdas, more services can be added later.
- But the priority is to get **one small but complete workflow running end-to-end**.

### 7.4 Secure and Isolated

- Each client's data is isolated in S3 by prefix (`<client_id>/...`).
- IAM policies ensure Lambdas can only access the buckets they need.
- No cross-client data leakage.

### 7.5 Professional Quality

- Newsletters must be:
  - **Accurate**: Correct entities, correct event types.
  - **Relevant**: Only items that matter to the client.
  - **Readable**: Clear structure, concise summaries, actionable links.
  - **Timely**: Delivered on schedule (weekly, monthly).

---

## 8. Summary

Vectora Inbox is a **simple, robust, configurable intelligence engine** that helps a solo founder deliver professional sector newsletters to multiple clients.

**Key takeaways:**
- **3 S3 buckets**: config, data, newsletters.
- **2 Lambdas**: ingest+normalize, engine.
- **Amazon Bedrock**: Linguistic brain for normalization and editorial writing.
- **5 phases**: configuration → ingestion (no AI) → normalization (Bedrock) → matching (rules) → scoring (rules) → assembly (Bedrock).
- **Multi-client support**: One shared architecture, different configs per client.
- **Admin levers**: Tune scopes, keywords, domains, scoring, layout, Bedrock prompts—without changing code.
- **MVP scope**: Small, focused, end-to-end workflow that works reliably.

This document is intentionally high-level and technology-agnostic. Implementation details (runtime, libraries, exact IAM policies) are controlled by:
- `vectora-inbox-q-rules.md` (AWS context, naming rules, guardrails).
- `blueprint-draft-vectora-inbox.yaml` (declarative infrastructure blueprint).
- Business contracts in `/contracts/` (Lambda specifications).

---

**For Amazon Q Developer / ChatGPT:**  
When you start a new conversation about Vectora Inbox, read this document first to understand the architecture, workflow, and design principles. Then refer to `vectora-inbox-q-rules.md` for AWS context and guardrails, and `blueprint-draft-vectora-inbox.yaml` for infrastructure details.
