# Vectora Inbox Newsletter Pipeline Overview

## Executive Summary

The Vectora Inbox newsletter pipeline transforms raw external content into curated, intelligent newsletters through a sophisticated 4-phase process:

**From Event to Newsletter:**
```
event = { client_id: "lai_weekly", period_days: 7 }
→ newsletter.md in S3
```

**Core Pipeline Blocks:**

1. **Ingestion** (already documented): Scrapes RSS feeds and APIs from configured sources
2. **Normalization** (Bedrock): Extracts entities, classifies events, generates summaries using Amazon Bedrock
3. **Matching** (domain surveillance): Applies client watch_domains to identify relevant items using canonical scopes
4. **Scoring**: Ranks items by importance using configurable rules (event type, recency, company priority)
5. **Newsletter Assembly** (Bedrock + formatting): Generates editorial content and assembles final Markdown

**Key Differentiators:**
- **Configuration-driven**: Business logic lives in YAML files, not code
- **Canonical scopes**: Reusable entity lists (companies, molecules, technologies) shared across clients
- **Technology profiles**: Advanced matching for complex domains like LAI (Long-Acting Injectables)
- **Transparent scoring**: Rule-based scoring system with explainable factors

## End-to-End Workflow Overview

```
Ingestion (scraping)
  → Profile Filtering (ingestion_profiles.yaml)
    → Normalization (Bedrock + entity detection)
      → Storage (normalized/client_id/YYYY/MM/DD/items.json)
        → Engine (matching + scoring + newsletter)
          → Bedrock (editorial content generation)
            → Newsletter (S3: newsletters/client_id/YYYY/MM/DD/newsletter.md)
```

**Components by Phase:**

| Phase | Lambda | Key Modules | S3 Buckets | Config Files |
|-------|--------|-------------|------------|--------------|
| 1A-1B | ingest-normalize | ingestion/, normalization/ | CONFIG, DATA | client config, canonical scopes, ingestion_profiles |
| 2-3-4 | engine | matching/, scoring/, newsletter/ | CONFIG, DATA, NEWSLETTERS | client config, canonical scopes, matching_rules, scoring_rules |

## Normalization – Runtime Details

### Lambda ingest-normalize

**Configuration Files Used:**

1. **Client Config** (`clients/lai_weekly.yaml`):
   - `client_profile`: language, tone, voice for Bedrock prompts
   - `source_config`: bouquets and sources to ingest
   - `watch_domains`: referenced for scope loading (used in normalization context)

2. **Canonical Scopes** (loaded via scope keys from client config):
   - `company_scopes.yaml`: `lai_companies_global`, `lai_companies_pure_players`, `lai_companies_hybrid`
   - `molecule_scopes.yaml`: `lai_molecules_global`
   - `technology_scopes.yaml`: `lai_keywords` (with technology_complex profile)
   - `trademark_scopes.yaml`: `lai_trademarks_global`
   - `exclusion_scopes.yaml`: HR, ESG, financial exclusions

3. **Ingestion Profiles** (`ingestion_profiles.yaml`):
   - `corporate_pure_player_broad`: Minimal filtering for pure players
   - `corporate_hybrid_technology_focused`: Strict filtering requiring technology signals
   - `press_technology_focused`: Multi-signal requirements for press sources

**Runtime Modules:**

- `vectora_core/config/loader.py`: Loads client config and canonical scopes from S3
- `vectora_core/config/resolver.py`: Resolves source bouquets into individual source_keys
- `vectora_core/ingestion/fetcher.py`: HTTP requests to RSS/API sources
- `vectora_core/ingestion/parser.py`: Parses RSS/JSON into raw items
- `vectora_core/ingestion/profile_filter.py`: Applies ingestion profiles for pre-filtering
- `vectora_core/normalization/normalizer.py`: Orchestrates normalization process
- `vectora_core/normalization/bedrock_client.py`: Bedrock API calls
- `vectora_core/normalization/entity_detector.py`: Rule-based entity detection + Bedrock fusion

**Bedrock Normalization Process:**

1. **Input to Bedrock**:
   - Full text (title + description)
   - Canonical examples (50 companies, 30 molecules, 20 technologies from scopes)
   - Client language preference
   - Event type definitions

2. **Bedrock Prompt Structure**:
   - Entity extraction instructions with canonical examples
   - Event classification among predefined types
   - Summary generation (2-3 sentences, client language)
   - Strict instructions: no hallucination, preserve exact entity names

3. **Output from Bedrock**:
   - `summary`: Factual summary in client language
   - `event_type`: One of clinical_update, regulatory, partnership, etc.
   - `companies_detected`: List of company names
   - `molecules_detected`: List of molecule/drug names
   - `technologies_detected`: List of technology terms
   - `indications_detected`: List of therapeutic indications

**Normalized Item Format (Open-World Schema):**
```json
{
  "source_key": "press_corporate__camurus",
  "source_type": "press_corporate",
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "summary": "Camurus reported positive results from Phase 3 trial...",
  "url": "https://example.com/article",
  "date": "2025-01-15",
  
  // OPEN-WORLD: All entities detected by Bedrock
  "companies_detected": ["Camurus"],
  "molecules_detected": ["buprenorphine"],
  "trademarks_detected": ["Brixadi"],
  "technologies_detected": ["long acting", "depot"],
  "indications_detected": ["opioid use disorder"],
  
  // CANONICAL INTERSECTION: Entities present in scopes
  "companies_in_scopes": ["Camurus"],
  "molecules_in_scopes": ["buprenorphine"],
  "trademarks_in_scopes": ["Brixadi"],
  "technologies_in_scopes": ["long acting"],
  "indications_in_scopes": ["opioid use disorder"],
  

"event_type": "clinical_update"
}
```

## Matching & Selection – Runtime Details (Lambda engine)

### Configuration Files Used:

1. **Client Config** (`clients/lai_weekly.yaml`):
   - `watch_domains`: Defines surveillance domains with scope references
   - `newsletter_layout`: Section structure and item limits
   - `client_profile`: Editorial preferences

2. **Canonical Scopes** (same as normalization):
   - Loaded via scope keys referenced in watch_domains
   - Used for intersection calculations

3. **Matching Rules** (`canonical/matching/domain_matching_rules.yaml`):
   - `technology_profiles`: Complex matching logic for technology domains
   - Domain type rules: technology, indication, regulatory, default

4. **Scoring Rules** (`canonical/scoring/scoring_rules.yaml`):
   - Event type weights, domain priority weights
   - Company bonuses, recency decay, signal quality factors

### Runtime Modules:

- `vectora_core/__init__.py`: `run_engine_for_client()` orchestration
- `vectora_core/matching/matcher.py`: Domain matching logic
- `vectora_core/scoring/scorer.py`: Score calculation
- `vectora_core/newsletter/assembler.py`: Newsletter generation orchestration
- `vectora_core/newsletter/bedrock_client.py`: Editorial content generation
- `vectora_core/newsletter/formatter.py`: Markdown assembly

### Step-by-Step Process for lai_weekly:

1. **Load Normalized Items from S3**:
   - Scans `s3://data/normalized/lai_weekly/YYYY/MM/DD/items.json` for date range
   - Aggregates all items from the period (e.g., last 7 days)

2. **Apply Domain Matching Rules**:
   - For each watch_domain in client config:
     - Load canonical scopes via scope keys (e.g., `lai_companies_global`)
     - Calculate intersections: item entities ∩ scope entities
     - Apply domain type rules (technology domains require multiple signals)
     - For `tech_lai_ecosystem` with `technology_complex` profile:
       - Categorize technology keywords (core_phrases, technology_terms_high_precision, etc.)
       - Apply company scope modifiers (pure_player vs hybrid rules)
       - Evaluate combination logic with confidence scoring

3. **Score Calculation**:
   - Base score: `event_type_weight × domain_priority_weight × recency_factor × source_type_weight`
   - Bonuses: pure_player_bonus (+3), signal_quality_score, match_confidence_multiplier
   - Penalties: negative_term_penalty (-10)
   - Company scope bonuses: pure players get higher bonus than hybrids

4. **Item Selection by Section**:
   - Group items by newsletter sections (defined in `newsletter_layout`)
   - Apply section filters (e.g., only "partnership" events for partnerships section)
   - Rank by score and select top N items per section

5. **Bedrock Editorial Generation**:
   - Send selected items + context to Bedrock
   - Generate: newsletter title, introduction, TL;DR, section intros, item reformulations
   - Respect client tone/voice/language preferences

6. **Markdown Assembly**:
   - Combine Bedrock editorial content with structured sections
   - Add metadata, links, footer
   - Write to `s3://newsletters/lai_weekly/YYYY/MM/DD/newsletter.md`

## Role of the 3 Configuration Layers

### Client Config (`client-config-examples/*.yaml`)
**Controls:**
- `client_id`, `watch_domains`: What to monitor
- `source_config.source_bouquets_enabled`: Which sources to ingest
- `newsletter_layout.sections`: Newsletter structure
- `client_profile`: Language, tone, voice for Bedrock

**Example Decision:** Client wants to monitor LAI ecosystem → references `lai_companies_global` scope

### Canonical (`canonical/scopes/*.yaml`, `canonical/matching/*.yaml`, etc.)
**Controls:**
- **Entity definitions**: Lists of companies, molecules, technologies by vertical
- **Matching rules**: How to combine signals for domain matching
- **Scoring rules**: Weights and factors for item ranking
- **Ingestion profiles**: Pre-filtering strategies by source type

**Example Decision:** `lai_companies_global` contains 150+ companies → defines LAI universe

### Hard-coded (`matcher.py`, `scorer.py`, `newsletter/assembler.py`, etc.)
**Controls:**
- **Intersection algorithms**: Set operations for matching
- **Score calculation formulas**: Mathematical combination of factors
- **Bedrock prompt construction**: How to structure AI requests
- **Markdown formatting**: Output structure

**Example Decision:** Technology domains require `min_matches: 2` → coded in matching logic

### Decision Authority Matrix:

| Decision Type | Client Config | Canonical | Code |
|---------------|---------------|-----------|------|
| Which companies to monitor | ✓ (scope references) | ✓ (scope content) | |
| Matching logic complexity | | ✓ (rules) | ✓ (algorithms) |
| Scoring weights | | ✓ (rules) | ✓ (formulas) |
| Newsletter sections | ✓ (layout) | | ✓ (formatting) |
| Bedrock prompts | ✓ (tone/voice) | ✓ (examples) | ✓ (structure) |

## Current Limitations and Fragility Points

### Current Risks:

1. **LAI-Specific Dependencies**:
   - Technology profiles hardcoded for LAI use case
   - Company scope modifiers assume pure_player/hybrid distinction
   - Risk: Difficult to adapt to other verticals without code changes

2. **Bedrock Rate Limiting**:
   - MAX_BEDROCK_WORKERS = 4 for normalization
   - No retry logic with exponential backoff
   - Risk: Throttling errors during high-volume periods

3. **Matching Fallbacks**:
   - If technology_complex profile fails, falls back to basic rules
   - Some items may be missed if profile metadata is incorrect
   - Risk: Inconsistent matching behavior

4. **Configuration Validation**:
   - Limited validation of scope key references
   - Missing scopes fail silently or cause runtime errors
   - Risk: Configuration errors not caught early

### Already Aligned with Vectora Inbox Design:

1. **Generic Engine Architecture**: Core modules are vertical-agnostic
2. **Configuration-Driven Logic**: Business rules in YAML, not code
3. **Canonical Scope System**: Reusable entity definitions
4. **Modular Pipeline**: Clear separation of concerns between phases

### Not Yet Aligned (Pre-Production Fixes Needed):

1. **Multi-Vertical Support**: 
   - Technology profiles need generalization
   - Company scope types should be configurable
   - Scoring rules should be client-specific

2. **Error Handling & Resilience**:
   - Bedrock retry mechanisms
   - Graceful degradation when scopes are missing
   - Better validation of configuration files

3. **Performance Optimization**:
   - Batch processing for large item volumes
   - Caching of canonical scopes
   - Parallel processing of multiple clients

4. **Monitoring & Observability**:
   - Detailed metrics on matching accuracy
   - Performance tracking per phase
   - Configuration drift detection

---

*This document provides a comprehensive technical overview of the Vectora Inbox newsletter pipeline as implemented in the current MVP. It serves as both operational documentation and architectural reference for future enhancements.*