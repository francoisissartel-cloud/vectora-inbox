# Vectora Inbox – Overview (for Q Developer & humans)

Vectora Inbox is a **generic, configurable intelligence engine** for biotech/pharma (and other sectors later).
It helps a solo founder or consultant automatically produce:

- a professional, strategic newsletter,
- based on public heterogeneous sources,
- filtered by client-specific domains of interest ("scopes"),
- prioritized by a scoring model,
- assembled into a Markdown newsletter (HTML/PDF later),
- without hardcoding client-specific logic in the code.

The system must remain:
- simple (one main engine Lambda + S3 buckets),
- generic,
- configuration-driven,
- enrichable over time,
- secure (each client isolated in S3),
- professional in editorial quality.

---

## 1. Core concepts

### 1.1 Canonical vs client config

- **Canonical** (shared across all clients) contains:
  - company scopes,
  - molecule scopes,
  - technology keyword scopes,
  - indication keyword scopes,
  - exclusion keyword sets,
  - event type patterns.

  Examples (stored under `canonical/scopes/`):
  - `company_scopes.yaml`
  - `molecule_scopes.yaml`
  - `keywords_technologies.yaml`
  - `keywords_indications.yaml`
  - `keywords_exclusions.yaml`
  - `event_type_patterns.yaml`

- **Client config** (one file per client, stored in S3) contains:
  - newsletter profile (tone, language, frequency),
  - domains of interest (`watch_domains`),
  - mapping from domains to scopes in canonical,
  - extra companies/molecules/keywords specific to the client,
  - newsletter layout (sections, max items),
  - delivery/export parameters.

  Example key sections:
  - `client_profile`
  - `watch_domains`
  - `newsletter_layout`
  - `newsletter_delivery`

**Rule**: client config = selection + additions on top of canonical.  
No duplication of canonical lists inside client config.

---

## 2. S3 buckets and structure

Vectora Inbox uses **three main buckets**:

1. `vectora-inbox-config`
   - `canonical/` : universal scopes and patterns.
   - `clients/`   : one YAML file per client (`xxx_client.yaml`).

2. `vectora-inbox-data`
   - `raw/<client>/<source>/<YYYY>/<MM>/<DD>/...`  
     → source-specific raw data (RSS, HTML, JSON, etc.).
   - `normalized/<client>/<YYYY>/<MM>/<DD>/items.json`  
     → normalized items with a standard JSON structure.
   - `matched/<client>/<YYYY>/<MM>/<DD>/items.json`  
     → same items, but annotated with matching/mapping info if needed.

3. `vectora-inbox-newsletters`
   - `<client>/<YYYY>/<MM>/<DD>/newsletter.md`  
     → main newsletter export in Markdown.
   - optionally later: `newsletter.html`, `newsletter.pdf`.

Sources (conceptual) include:
- corporate press,
- sector press,
- ClinicalTrials.gov,
- PubMed,
- FDA / DailyMed.

The MVP can start by assuming that normalized items already exist in
`vectora-inbox-data/normalized/...`.

---

## 3. Normalized item structure (key to the engine)

Every content item used by the engine is normalized to a common JSON schema, for example:

```json
{
  "source_type": "press",
  "title": "Example title",
  "summary": "Short abstract of the content...",
  "url": "https://example.com/article",
  "date": "2025-01-15",

  "companies_detected": ["Camurus", "Medincell"],
  "molecules_detected": ["Brixadi"],
  "technologies_detected": ["long acting", "depot"],
  "indications_detected": ["opioid use disorder"],
  "event_type": "clinical_update"
}
Normalization includes:

entity extraction (companies, molecules),

technology keyword detection,

indication keyword detection,

event type classification,

basic text cleaning.

This normalized layer is what makes matching, scoring and newsletter assembly possible.

4. Matching logic (item ↔ watch domains)

Client config defines watch_domains, such as:

a technology domain (tech_lai_ecosystem) with:

technology_scope referencing canonical LAI keywords,

company_scope referencing canonical LAI companies,

molecule_scope referencing canonical LAI molecules.

an indication domain (indication_addiction) with:

indication_scope,

related company and molecule scopes,

possibly extra client-specific companies or molecules.

An item matches a domain if there is an intersection between:

technologies_detected and the technology scope,

indications_detected and the indication scope,

companies_detected and the company scope,

molecules_detected and the molecule scope.

Client config can set domain priority (e.g. high, medium).

5. Scoring and selection

The engine computes a score for each item based on a weighted combination of:

event relevance (e.g. clinical update, partnership, approval),

recency,

domain priority,

presence of key competitors,

presence of key molecules,

signal depth (length and richness of the content),

source type (e.g. regulatory > clinical > press > noise).

For each newsletter section:

keep up to max_items,

sort items by score,

group by domain if relevant.

6. Newsletter assembly (engine Lambda behavior)

The engine Lambda (vectora-inbox-engine) does conceptually:

Reads the client config from:

s3://vectora-inbox-config/clients/<client_id>.yaml

Loads normalized items for a given period (e.g. last 7 days) from:

s3://vectora-inbox-data/normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json

Applies:

domain matching,

scoring,

selection per newsletter section.

Assembles the newsletter according to newsletter_layout:

title (generated if required),

intro (generated if required),

TL;DR summary,

ordered sections with bullet points or short paragraphs,

references to source URLs.

Writes the result as Markdown to:

s3://vectora-inbox-newsletters/<client_id>/<YYYY>/<MM>/<DD>/newsletter.md

Later, HTML/PDF exports can be added, but Markdown is the first target for the MVP.

7. Design principles for the MVP

Single engine Lambda:

Prefer one well-defined Lambda that can be tested and debugged easily.

It must be able to run for one client and a given date range.

Configuration over code:

No client-specific rules in the Lambda code.

Clients differ only by:

which scopes they activate,

what extra entities they add,

how they structure their newsletter.

Simplicity first:

It is acceptable to start with manual or external ingestion of normalized items.

The MVP goal is to have a reliable engine + newsletter generation running end-to-end.

Extendable later:

More sources and ingestion Lambdas can be added in future steps,
once the core newsletter pipeline is stable.

This overview is intentionally high-level and technology-agnostic.
Implementation details (runtime, libraries, exact IAM policies) are controlled by the combination of:

vectora-inbox-q-rules.md

blueprint-draft-vectora-inbox.yaml

business contracts in /contracts.