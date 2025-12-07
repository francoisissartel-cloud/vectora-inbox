# Vectora Inbox – Q Rules (Environment + Repo + Guardrails)

You (Amazon Q Developer) are working on the `vectora-inbox` project.
Your main goals are:

- Help build a **simple, robust MVP** that works end-to-end.
- Avoid unnecessary complexity and extra AWS services.
- Reuse the existing AWS SSO admin environment.

This file tells you:

- **where** Vectora Inbox lives in AWS,
- **which profile/region** to use,
- **how** the repository is organized,
- **what you must not do**.

---

## 1. AWS execution context (very important)

### 1.1 Account, profile, region

Vectora Inbox runs in:

- **AWS Account ID**: `786469175371`
- **AWS CLI profile**: `rag-lai-prod`
- **Primary region**: `eu-west-3` (Paris)

When you propose AWS CLI commands, always assume:

```bash
--profile rag-lai-prod --region eu-west-3
Examples:

aws s3 ls --profile rag-lai-prod --region eu-west-3
aws cloudformation deploy ... --profile rag-lai-prod --region eu-west-3
aws lambda update-function-code ... --profile rag-lai-prod --region eu-west-3

1.2 SSO / role context

The human uses AWS IAM Identity Center (SSO).
When connected, the effective role looks like:

arn:aws:sts::786469175371:assumed-role/AWSReservedSSO_RAGLai-Admin_dd0aa74f23dac197/Franck


Assumptions for you:

The rag-lai-prod profile has enough permissions to:

create S3 buckets,

create/update CloudFormation stacks,

create/update Lambda functions,

attach basic IAM roles/policies.

Do not propose changes to Identity Center / SSO configuration.

If a command might fail due to permissions, explain it clearly and suggest minimal changes (no big IAM redesign).

2. Naming rules for Vectora Inbox resources

All AWS resources created for this project must follow these conventions.

2.1 Global prefix

Use the prefix: vectora-inbox- (or vectora-inbox for S3).

Apply this prefix to:

S3 buckets

Lambda function names

CloudFormation stack names

IAM roles dedicated to Vectora Inbox

2.2 S3 buckets (fixed for the MVP)

These bucket names are canonical for the MVP, in eu-west-3:

**vectora-inbox-config**

Canonical scopes and client config files.

Structure:
- `canonical/...`
- `clients/<client_id>.yaml`

**vectora-inbox-data**

Raw and normalized items.

Structure (CRITICAL - must be respected):

**RAW layer** (optional but useful for debugging and replays):
- Path pattern: `raw/<client_id>/<source_key>/<YYYY>/<MM>/<DD>/raw.json`
- Where:
  - `client_id` = client identifier (e.g., `lai_weekly`)
  - `source_key` = unique ID for the source (e.g., `press_corporate__fiercepharma`, `press_sector__endpointsnews`, `pubmed_lai`, `ctgov_lai`)
  - Date folders = ingestion date
- Purpose: Store raw payloads fetched from RSS/APIs, keep per-source history for debugging, quality checks, and re-normalization.
- RAW is **per-client and per-source** (source_key).

**Normalized layer** (input for the engine):
- Path pattern: `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`
- This file aggregates all normalized items for a given client and day, across all sources.
- Each normalized item MUST contain:
  - `source_key`: string (e.g., `"press_corporate__fiercepharma"`)
  - `source_type`: string (e.g., `"press_corporate"`)
  - Plus other fields: title, summary, url, date, detected entities, event_type, etc.
- Normalized is **per-client and per-day**, aggregating all sources.

**Important:**
- The `vectora-inbox-engine` Lambda only reads from **normalized/**, not from raw/.
- RAW exists as a useful, optional "debug/replay" layer.

**vectora-inbox-newsletters**

Rendered newsletters (Markdown first, later HTML/PDF).

Structure:
- `<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`

These names and structures must be reused consistently in:
- CloudFormation templates,
- IAM policies (S3 access),
- Lambda code.

2.3 Lambda functions

For the MVP, there are exactly **2 Lambdas**:

**1. vectora-inbox-ingest-normalize**

Phase 1A – Ingestion (NO Bedrock):
- Reads canonical + client config to know which sources (source_keys) are active.
- For each active `source_key`:
  - Performs HTTP calls (RSS, APIs, etc.),
  - Parses the responses,
  - Builds a list of raw items in memory for that source.
- Optionally writes a single `raw.json` per source under:
  `raw/<client_id>/<source_key>/<YYYY>/<MM>/<DD>/raw.json`

Phase 1B – Normalization (WITH Bedrock + rules):
- For each raw item (regardless of source key):
  - Builds a Bedrock prompt (classification + extraction + summary),
  - Combines Bedrock output with rule-based matching against canonical scopes.
- Produces a normalized item with fields including:
  - `source_key`, `source_type`, `title`, `summary`, `url`, `date`,
  - `companies_detected`, `molecules_detected`, `technologies_detected`, `indications_detected`, `event_type`
- Writes all normalized items for the client and date into:
  `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`

**2. vectora-inbox-engine**
- Matching (rule-based) + Scoring (rule-based) + Newsletter assembly (Bedrock-assisted editorial writing)
- **Never needs to read RAW**; assumes normalized data is already there.

Rules:

Do not create additional Lambdas unless:

there is a Markdown business contract in /contracts/lambdas/,

and the human explicitly requested it.

2.4 CloudFormation stacks

Use stack names like:

vectora-inbox-s0-core → core S3 buckets and basic tags

vectora-inbox-s0-iam → IAM roles/policies (later, if needed)

vectora-inbox-s1-engine → main engine Lambda + permissions

Do not invent extra stacks without explicit confirmation.

2.5 IAM roles

When dedicated IAM roles are needed for Vectora Inbox:

Prefer not to hardcode RoleName when possible.

If a fixed RoleName is necessary, keep it short and prefixed, e.g.:

vectora-inbox-engine-role

---

## 3. Règles de nommage des scopes canonical

### 3.1 Principes fondamentaux

Les scopes canonical suivent des règles strictes pour garantir la cohérence et la maintenabilité :

1. **La verticale est portée par le préfixe de la clé** (ex : `lai_`, `oncology_`, `gene_therapy_`, etc.).

2. **Les fichiers `canonical/scopes/*.yaml` restent uniques et globaux** pour tout Vectora Inbox.
   - Il n'existe **pas** de fichiers séparés par verticale.
   - Toutes les verticales cohabitent dans les mêmes fichiers, différenciées par leurs préfixes.

3. **Les Lambdas ne lisent pas les commentaires des YAML**, uniquement les clés référencées dans les configs clients.
   - Les commentaires sont pour les humains et Q Developer.
   - Le runtime ne s'appuie que sur les clés et leurs valeurs.

4. **Les clés de scopes doivent être en `snake_case`** et suivre le format :
   ```
   {verticale}_{dimension}_{segment}
   ```
   - `verticale` : `lai`, `oncology`, `gene_therapy`, etc.
   - `dimension` : `companies`, `molecules`, `trademarks`, `technologies`, `indications`, `exclusions`
   - `segment` : `global`, `addiction`, `psychiatry`, `solid_tumors`, etc.

### 3.2 Exemples de nommage correct

**Dans `company_scopes.yaml` :**
```yaml
lai_companies_global:        # Toutes les sociétés LAI
lai_companies_addiction:     # Sociétés LAI spécialisées addiction
lai_companies_psychiatry:    # Sociétés LAI spécialisées psychiatrie
oncology_companies_global:   # Toutes les sociétés oncologie (futur)
```

**Dans `molecule_scopes.yaml` :**
```yaml
lai_molecules_all:           # Toutes les molécules LAI
lai_molecules_addiction:     # Molécules LAI pour addiction
oncology_molecules_all:      # Toutes les molécules oncologie (futur)
```

**Dans `trademark_scopes.yaml` :**
```yaml
lai_trademarks_global:       # Toutes les marques LAI
lai_trademarks_addiction:    # Marques LAI pour addiction
lai_trademarks_psychiatry:   # Marques LAI pour psychiatrie
```

### 3.3 Règles pour Q Developer

Lorsque tu travailles sur les scopes canonical :

- **Ne jamais renommer une clé existante** sans instruction explicite de l'humain.
  - Les configs clients référencent ces clés : un renommage casse tout.

- **Ne pas inventer de nouvelles conventions de nommage**.
  - Respecter le format `{verticale}_{dimension}_{segment}`.

- **Ne pas créer de fichiers canonical séparés par verticale**.
  - Toutes les verticales cohabitent dans les mêmes fichiers.

- **Ne pas supposer qu'une Lambda "connaît" la verticale**.
  - Les Lambdas ne font que charger des listes via leurs clés.
  - Elles ne "savent" pas si c'est LAI, oncologie, ou autre chose.

- **Utiliser les commentaires YAML pour documenter l'intention**.
  - Mais rappelle-toi : les commentaires ne sont jamais lus par le runtime.

### 3.4 Exemple complet : du canonical à la Lambda

**1. Dans `canonical/scopes/company_scopes.yaml` :**
```yaml
# Verticale LAI - Sociétés globales
lai_companies_global:
  - Camurus
  - Alkermes
  - Indivior
```

**2. Dans `clients/lai_weekly.yaml` :**
```yaml
watch_domains:
  - id: tech_lai_ecosystem
    company_scope: "lai_companies_global"  # Référence la clé
```

**3. Dans la Lambda `vectora-inbox-engine` :**
```python
# Pseudo-code
config = load_client_config("lai_weekly")
domain = config["watch_domains"][0]
company_scope_key = domain["company_scope"]  # "lai_companies_global"

company_scopes = load_yaml("canonical/scopes/company_scopes.yaml")
company_list = company_scopes[company_scope_key]  # ["Camurus", "Alkermes", "Indivior"]

# Utiliser company_list pour le matching
if item["companies_detected"] & set(company_list):
    # Item matche ce domaine
```

La Lambda ne "sait" pas que c'est LAI. Elle charge juste la liste à la clé `"lai_companies_global"`.

---

## 4. Règles pour le catalogue de sources et les bouquets

### 4.1 Nommage des `source_key`

Les `source_key` sont les identifiants uniques des sources dans le catalogue. Ils doivent suivre des règles strictes :

**Format obligatoire :**
- Toujours en `snake_case` minuscule
- Format : `{type_prefix}__{slug}`
- Pas d'espaces, pas de caractères spéciaux (sauf `_`)

**Préfixes recommandés par type de source :**
- `press_corporate__` : sites web ou flux RSS des entreprises elles-mêmes
  - Exemples : `press_corporate__medincell`, `press_corporate__camurus`
- `press_sector__` : presse sectorielle spécialisée
  - Exemples : `press_sector__biocentury`, `press_sector__pharmaphorum`
- `pubmed__` : recherches PubMed configurées (futur)
  - Exemples : `pubmed__lai_addiction`, `pubmed__gene_therapy`
- `ctgov__` : recherches ClinicalTrials.gov configurées (futur)
  - Exemples : `ctgov__lai_phase3`, `ctgov__oncology_trials`
- `fda__` : flux réglementaires FDA (futur)
  - Exemples : `fda__drug_approvals`, `fda__safety_alerts`

**Règles pour le slug (partie après `__`) :**
- Dérivé du nom de la source ou de la société
- Espaces → `_` (underscore)
- Ponctuation supprimée ou remplacée par `_`
- Exemples :
  - "MedinCell" → `medincell`
  - "BioCentury" → `biocentury`
  - "Endpoints News" → `endpoints_news`
  - "Nature Biotechnology" → `nature_biotechnology`

**Important : ne pas inclure la verticale dans le `source_key`**

Éviter : `press_corporate__lai_medincell` (redondant)

Préférer : `press_corporate__medincell` + `vertical_tags: ["lai"]`

**Pourquoi ?**
- Une source peut servir plusieurs verticales (via `vertical_tags`)
- La spécialisation métier est portée par :
  - Les `vertical_tags` (documentation)
  - Les scopes canonical (matching)
  - La config client (activation)

### 4.2 Nommage des `bouquet_id`

Les `bouquet_id` sont les identifiants des regroupements de sources. Ils suivent aussi des règles strictes :

**Format obligatoire :**
- Toujours en `snake_case` minuscule
- Format recommandé : `{verticale_ou_theme}_{type}_{segment}`
- Pas d'espaces, pas de caractères spéciaux (sauf `_`)

**Exemples de bouquets bien nommés :**
- `lai_corporate_all` : tous les flux corporate LAI
- `lai_corporate_addiction` : flux corporate LAI spécialisés addiction
- `press_biotech_premium` : sélection premium de presse biotech
- `press_pharma_general` : presse pharma généraliste
- `regulatory_fda_ema` : flux réglementaires FDA et EMA (futur)
- `pubmed_lai_all` : toutes les recherches PubMed LAI (futur)

**Principes de nommage :**
- Le préfixe indique la verticale ou le thème (`lai_`, `press_`, `regulatory_`, etc.)
- Le milieu indique le type de sources (`corporate`, `sector`, `biotech`, `pharma`, etc.)
- Le suffixe indique le segment ou la couverture (`all`, `premium`, `addiction`, etc.)

### 4.3 Structure du fichier `source_catalog.yaml`

**Emplacement canonique :**
- `canonical/sources/source_catalog.yaml`

**Structure obligatoire :**
```yaml
sources:
  - source_key: "..."
    source_type: "..."
    url: "..."
    default_language: "..."
    vertical_tags: [...]  # optionnel
    notes: "..."          # optionnel mais recommandé
  # ... autres sources

bouquets:
  - bouquet_id: "..."
    description: "..."
    source_keys:
      - "..."
      - "..."
  # ... autres bouquets
```

**Champs obligatoires pour une source :**
- `source_key` : identifiant unique (voir règles 4.1)
- `source_type` : catégorie (`press_corporate`, `press_sector`, `pubmed`, `ctgov`, etc.)
- `url` : adresse du flux RSS ou endpoint API (peut être `""` si à compléter)
- `default_language` : langue par défaut (`"en"`, `"fr"`, etc.)

**Champs optionnels mais recommandés :**
- `vertical_tags` : liste de tags métiers (`["lai"]`, `["pharma-biotech"]`, etc.)
- `notes` : description en français pour l'administrateur

**Champs obligatoires pour un bouquet :**
- `bouquet_id` : identifiant unique (voir règles 4.2)
- `description` : description en français du bouquet
- `source_keys` : liste des `source_key` inclus dans le bouquet

### 4.4 Règles pour Q Developer lors de modifications

**Ne JAMAIS faire sans instruction explicite :**

1. **Renommer un `source_key` ou `bouquet_id` existant**
   - Les configs clients référencent ces identifiants
   - Un renommage casse toutes les références
   - Si un renommage est nécessaire, demander confirmation explicite

2. **Créer des fichiers de catalogue séparés par verticale**
   - Pas de `lai_sources.yaml`, `oncology_sources.yaml`, etc.
   - Le standard est **un seul** `source_catalog.yaml` global
   - Toutes les verticales cohabitent dans le même fichier

3. **Supprimer des sources ou bouquets existants**
   - Vérifier d'abord qu'aucune config client ne les utilise
   - Demander confirmation avant suppression

**TOUJOURS faire lors de l'ajout d'une nouvelle source :**

1. **Renseigner tous les champs obligatoires**
   - `source_key`, `source_type`, `url`, `default_language`
   - Si l'URL n'est pas encore connue : `url: ""` + note explicative

2. **Ajouter une note en français**
   - Expliquer le but de la source
   - Indiquer le périmètre (corporate, sectoriel, etc.)
   - Mentionner si l'URL est à compléter

3. **Ajouter des `vertical_tags` si pertinent**
   - Uniquement si c'est utile et compréhensible
   - Exemples : `["lai"]`, `["pharma-biotech"]`, `["gene-therapy"]`
   - Ne pas inventer de nouveaux tags sans cohérence

4. **Garder les commentaires en français**
   - Tous les commentaires YAML doivent être en français
   - Ils servent à documenter pour les humains

**Exemple d'ajout correct d'une nouvelle source :**

```yaml
# Ajout d'une nouvelle source corporate LAI
- source_key: "press_corporate__camurus"
  source_type: "press_corporate"
  url: ""  # URL à compléter manuellement (flux RSS ou page news)
  default_language: "en"
  vertical_tags: ["lai"]
  notes: "Site institutionnel Camurus (société LAI suédoise, spécialisée addiction et psychiatrie)."
```

**TOUJOURS faire lors de la modification d'un bouquet :**

1. **Ne pas retirer des `source_key` existants sans consigne**
   - Vérifier d'abord l'impact sur les configs clients
   - Demander confirmation si nécessaire

2. **Éviter les doublons dans `source_keys`**
   - Chaque `source_key` ne doit apparaître qu'une fois dans un bouquet

3. **Privilégier une liste triée pour la lisibilité**
   - Trier alphabétiquement ou par catégorie logique
   - Facilite la maintenance et la revue

4. **Mettre à jour la description si le contenu change**
   - La description doit refléter le contenu actuel du bouquet

**Exemple de modification correcte d'un bouquet :**

```yaml
# Ajout d'une source à un bouquet existant
- bouquet_id: "lai_corporate_all"
  description: "Flux corporate des sociétés LAI suivies (MedinCell, Camurus, Alkermes, etc.)."
  source_keys:
    - "press_corporate__alkermes"
    - "press_corporate__camurus"      # Nouvelle source ajoutée
    - "press_corporate__indivior"
    - "press_corporate__medincell"
    # Liste triée alphabétiquement pour la lisibilité
```

### 4.5 Validation et cohérence

**Avant de commiter des changements au catalogue :**

1. **Vérifier l'unicité des identifiants**
   - Chaque `source_key` doit être unique dans `sources:`
   - Chaque `bouquet_id` doit être unique dans `bouquets:`

2. **Vérifier les références dans les bouquets**
   - Chaque `source_key` référencé dans un bouquet doit exister dans `sources:`
   - Pas de références cassées

3. **Vérifier la cohérence des `vertical_tags`**
   - Utiliser des tags existants et cohérents
   - Ne pas inventer de nouveaux tags sans raison

4. **Vérifier la syntaxe YAML**
   - Indentation correcte (2 espaces)
   - Guillemets pour les chaînes contenant des caractères spéciaux
   - Listes avec tirets `-` correctement alignés

### 4.6 Différence avec les scopes canonical

**Important : ne pas confondre sources et scopes**

**Catalogue de sources** (`canonical/sources/source_catalog.yaml`) :
- Décrit **où aller chercher les textes** (URLs, flux RSS, APIs)
- Exemples : `press_corporate__medincell`, `press_sector__biocentury`
- Utilisé par : Lambda d'ingestion (`vectora-inbox-ingest-normalize`)
- Question : "Où lire les actualités ?"

**Scopes canonical** (`canonical/scopes/*.yaml`) :
- Décrivent **des listes métier** (sociétés, molécules, technologies, indications)
- Exemples : `lai_companies_global`, `lai_molecules_addiction`
- Utilisés par : Lambda moteur (`vectora-inbox-engine`) pour le matching et le scoring
- Question : "Quelles entités métier nous intéressent ?"

**Les deux sont complémentaires mais distincts :**
- Les **sources** fournissent le contenu brut
- Les **scopes** servent à analyser et filtrer ce contenu
- Les **bouquets** simplifient l'activation des sources
- Les **watch_domains** (dans les configs clients) combinent les scopes pour définir les intérêts métier

---

## 5. Repository map (how the codebase is organized)

You are working in the GitHub repo:

francoisissartel-cloud/vectora-inbox

Default branch: main

Key folders (root of the repo):

/infra

Infrastructure-as-code (CloudFormation/SAM/CDK).

No business logic here.

For the MVP: at least one stack s0-core to create the 3 buckets.

/src

Runtime code (Lambda functions, helpers).

MVP target: 2 Lambdas:

vectora-inbox-ingest-normalize (ingestion + normalization with Bedrock),

vectora-inbox-engine (matching + scoring + newsletter assembly with Bedrock).

/canonical

Shared business knowledge (no client-specific logic):

company scopes,

molecule scopes,

technology keyword scopes,

indication keyword scopes,

exclusion keyword sets,

event type patterns,

**source catalog** (nouveau : `canonical/sources/source_catalog.yaml`).

/client-config-examples

Example YAML configs showing what a real client file in S3 should look like.

/contracts

Business contracts for Lambdas and components (Markdown).

Before adding/changing a Lambda, there should be a contract here.

/docs

Documentation for humans (architecture, workflows).

/.q-context

Guidance files for you:

vectora-inbox-overview.md

vectora-inbox-q-rules.md (this file)

blueprint-draft-vectora-inbox.yaml

---

## 6. Amazon Bedrock usage rules

### 6.1 Where Bedrock IS used

Bedrock is the **"linguistic brain"** of Vectora Inbox. Use it for:

**Phase 1B – Normalization** (`vectora-inbox-ingest-normalize`):
- Entity extraction (companies, molecules, technologies, indications)
- Event type classification (clinical_update, partnership, regulatory, etc.)
- Generating concise summaries ("so what" of each item)

**Phase 4 – Newsletter Assembly** (`vectora-inbox-engine`):
- Writing newsletter intros, TL;DR, section summaries
- Rewriting item summaries in the client's tone/voice
- Generating newsletter titles

### 6.2 Where Bedrock is NOT used

Bedrock is NOT used for:

**Phase 1A – Ingestion**:
- HTTP requests
- RSS parsing
- JSON/XML decoding
- (This is pure "plumbing", implemented with normal code)

**Phase 2 – Matching**:
- Set intersections (technologies_detected ∩ technology scopes)
- Domain matching logic
- (This is deterministic, rule-based, explainable)

**Phase 3 – Scoring**:
- Numeric scoring rules (event relevance, recency, domain priority, etc.)
- (This is transparent, tunable, no AI required for MVP)

### 6.3 Bedrock configuration

**Model configuration:**
- Model IDs and variants must be provided via **environment variables**, not hardcoded:
  - `BEDROCK_MODEL_NORMALIZE` (for Phase 1B normalization)
  - `BEDROCK_MODEL_EDITORIAL` (for Phase 4 newsletter assembly)
- Example values: `anthropic.claude-3-sonnet-20240229-v1:0`, `anthropic.claude-3-haiku-20240307-v1:0`

**IAM permissions:**
- Both Lambda execution roles must include:
  - `bedrock:InvokeModel` (required)
  - `bedrock:InvokeModelWithResponseStream` (if streaming is used)
- Restrict to region `eu-west-3`
- Restrict to specific model ARNs if possible

**Bedrock guardrails:**
- Do NOT introduce Bedrock Knowledge Bases, Agents, or other advanced Bedrock services in the MVP
- Do NOT introduce other AI services (SageMaker, Comprehend, etc.) without explicit human request
- Focus only on direct model invocation via the Bedrock Runtime API

---

**S3 layout must be respected:**
- When generating code or CloudFormation, respect the canonical S3 layout:
  - RAW: `raw/<client_id>/<source_key>/<YYYY>/<MM>/<DD>/raw.json`
  - Normalized: `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`
- Do not introduce alternative directory structures for the MVP.

---

## 7. Guardrails against complexity

To keep the project simple and maintainable:

Do not:

introduce DynamoDB, RDS, Step Functions, EventBridge, or other services

unless the human clearly asks for them.

Do not:

create additional Lambdas beyond the 2 MVP Lambdas before the MVP works end-to-end.

Do not:

create resources in other regions than eu-west-3 for Vectora Inbox.

Always prefer:

a small pipeline that works (2 Lambdas + 3 buckets + Bedrock),

clear YAML + Markdown contracts,

configuration over extra code and services.

The priority is to get one small but complete workflow running end-to-end, not an over-engineered system.

---

## 8. Fundamental business rules (never break these)

**No client-specific logic in code:**
- All client-specific behavior must come from:
  - canonical scopes (shared),
  - client config files in S3 (vectora-inbox-config/clients/...).

**Canonical vs client config:**
- Canonical:
  - universal lists and patterns (companies, molecules, technologies, indications, exclusions, event types).
- Client config:
  - selection + extra items (add companies/molecules/keywords),
  - definitions of watch_domains,
  - newsletter layout and delivery settings.
- Do not duplicate canonical lists inside client config.

**Normalized items are mandatory:**
- Every item used by the engine must follow the normalized JSON structure, e.g.:
```json
{
  "source_key": "press_corporate__fiercepharma",
  "source_type": "press_corporate",
  "title": "...",
  "summary": "...",
  "url": "...",
  "date": "...",
  "companies_detected": [],
  "molecules_detected": [],
  "technologies_detected": [],
  "indications_detected": [],
  "event_type": "clinical_update"
}
```
- `source_key` and `source_type` are REQUIRED fields in every normalized item.

**Matching and scoring are rule-based and transparent:**
- Matching = set intersections (deterministic)
- Scoring = numeric rules (explainable, tunable)
- No Bedrock in matching or scoring for the MVP