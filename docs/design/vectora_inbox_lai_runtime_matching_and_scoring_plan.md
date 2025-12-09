# Vectora Inbox — LAI Runtime Matching and Scoring Adaptation Plan

**Date:** 2025-01-XX  
**Phase:** Phase 0 - Design Only  
**Status:** Design Document - Awaiting Approval

---

## 1. Business Goal & Current Situation

### 1.1 Current Situation

**Technical Status:**
- ✅ End-to-end pipeline operational: `ingest-normalize` → `engine` → newsletter in S3
- ✅ Canonical refactor completed:
  - `technology_scopes.yaml`: `lai_keywords` restructured into 7 categories
  - `company_scopes.yaml`: `lai_companies_pure_players` vs `lai_companies_hybrid` separated
- ✅ Generic matching engine: fully configuration-driven, no LAI-specific hardcoding

**Business Problem:**
- ❌ LAI precision: **0%** for `lai_weekly` client
- ❌ Engine selects non-LAI pharma news (Pfizer oral drugs, AbbVie TV ads, etc.)
- ❌ Pure player representation: **0%** (target: ≥50%)
- ❌ False positives: **5/5 items** in last test (target: 0)

**Root Cause:**
The runtime (matcher.py, scorer.py) does not yet exploit the new 7-category structure of `lai_keywords`. Current matching logic treats all keywords equally, causing generic terms to trigger false positives.

### 1.2 Target KPIs for `lai_weekly`

| Metric | Current | Target |
|--------|---------|--------|
| LAI precision | 0% | ≥ 80% |
| Pure player representation | 0% | ≥ 50% |
| False positives (obvious non-LAI) | 5/5 | 0 |
| Items selected per newsletter | 5 | 5-10 |

### 1.3 Business Definition of LAI

From `LAI_RATIONALE.md` and canonical imports:

**A Long-Acting Injectable (LAI) must combine 3 mandatory criteria:**
1. **Injectable route** (IM, SC, IV, intravitreal, intra-articular, etc.)
2. **Recognized technology** (DDS or HLE)
3. **Extended duration** (weeks to months from single injection)

**Exclusions:**
- Oral formulations
- Topical/transdermal applications
- Implantable devices
- Gene/cell therapies

---

## 2. Non-Negotiable Constraints

### 2.1 Generic Runtime Principle

**CRITICAL:** The engine must remain **fully generic and configuration-driven**.

- ❌ NO hardcoded "LAI" logic in matcher.py, scorer.py, or __init__.py
- ❌ NO hardcoded company names or drug names in runtime code
- ✅ ALL semantics come from:
  - Canonical scopes (technology, company, molecule, etc.)
  - Domain matching rules (domain_matching_rules.yaml)
  - Client config (watch_domains, priorities)

**Rationale:** The same runtime must work for other verticals (oncology, diabetes, rare diseases) by only changing canonical + client config.

### 2.2 Operational Continuity

- ✅ End-to-end workflow must remain operational after each phase
- ✅ No breaking changes to existing clients
- ✅ Rollback capability at each phase
- ✅ Comprehensive testing before production deployment

### 2.3 Documentation & Traceability

- ✅ Every change must be documented with rationale
- ✅ Diagnostic reports after each phase
- ✅ Clear Definition of Done per phase

---

## 3. Phased Adaptation Plan

### PHASE 1 — Domain Matching Rules Enhancement

**Objective:** Extend `domain_matching_rules.yaml` to exploit the 7-category structure of `lai_keywords` in a generic way.

#### 3.1.1 Current State Analysis

**Current rule for `technology` domains:**
```yaml
technology:
  match_mode: all_required
  dimensions:
    technology:
      requirement: required
      min_matches: 1
    entity:
      requirement: required
      min_matches: 1
      sources: [company, molecule]
```

**Problem:** This rule treats all technology keywords equally. It doesn't distinguish between:
- High-precision signals (`core_phrases`, `technology_terms_high_precision`)
- Context-only signals (`route_admin_terms`, `technology_use`)
- Generic terms that should not match alone (`generic_terms`)

#### 3.1.2 Proposed Enhancement

**Introduce technology complexity profiles:**

```yaml
# New section in domain_matching_rules.yaml
technology_profiles:
  technology_complex:
    description: "Complex technologies requiring multiple signal types (e.g., LAI)"
    signal_requirements:
      high_precision_signals:
        categories: [core_phrases, technology_terms_high_precision]
        min_matches: 1
        weight: 3.0
      supporting_signals:
        categories: [route_admin_terms, interval_patterns]
        min_matches: 1
        weight: 2.0
      context_signals:
        categories: [technology_use]
        min_matches: 0
        weight: 1.0
      excluded_categories: [generic_terms]
      negative_filters:
        categories: [negative_terms]
        action: reject_match
    entity_requirements:
      min_matches: 1
      sources: [company, molecule]
      company_scope_modifiers:
        pure_player_scopes: [lai_companies_pure_players]
        pure_player_rule: high_precision_signals_only
        hybrid_scopes: [lai_companies_hybrid]
        hybrid_rule: high_precision_plus_supporting
    combination_logic: |
      MATCH if:
        (high_precision_signal AND entity) OR
        (supporting_signal AND supporting_signal AND entity) OR
        (high_precision_signal AND pure_player_company)
      REJECT if:
        negative_term detected
  
  technology_simple:
    description: "Simpler technologies with clearer signals (e.g., oral tablets)"
    signal_requirements:
      high_precision_signals:
        categories: [core_phrases]
        min_matches: 1
        weight: 3.0
    entity_requirements:
      min_matches: 1
      sources: [company, molecule]
    combination_logic: |
      MATCH if:
        (high_precision_signal AND entity)
```

**Key Design Decisions:**

1. **Category-based matching:** Reference category names from canonical scopes, not specific keywords
2. **Weighted signals:** Different categories have different confidence levels
3. **Company scope modifiers:** Pure players vs hybrid companies have different matching thresholds
4. **Negative filtering:** Explicit rejection on negative terms
5. **Profile assignment:** Each technology scope references a profile

#### 3.1.3 Technology Scope Metadata

**Extend technology_scopes.yaml with profile references:**

```yaml
lai_keywords:
  _metadata:
    profile: technology_complex
    description: "Long-Acting Injectables - requires multiple signal types"
  core_phrases:
    - "long-acting injectable"
    # ... (existing structure unchanged)
```

#### 3.1.4 Implementation Details

**Files to modify:**
- `canonical/matching/domain_matching_rules.yaml` (add technology_profiles section)
- `canonical/scopes/technology_scopes.yaml` (add _metadata to lai_keywords)

**Backward compatibility:**
- Domains without profile reference use existing `technology` rule
- No breaking changes to other verticals

#### 3.1.5 Definition of Done - Phase 1

- ✅ `domain_matching_rules.yaml` updated with technology_profiles
- ✅ `technology_complex` profile defined with 7-category logic
- ✅ `technology_simple` profile defined for future use
- ✅ `lai_keywords` annotated with `profile: technology_complex`
- ✅ Documentation in `canonical/matching/README.md` updated
- ✅ No code changes yet (rules only)
- ✅ Validation: YAML syntax correct, loads without errors

---

### PHASE 2 — Matching Engine Adaptation

**Objective:** Adapt `matcher.py` to interpret and apply the new technology_profiles rules.

#### 3.2.1 Current Matching Logic

**Current flow in matcher.py:**
1. Extract entities from item (companies, molecules, technologies, indications)
2. Load scopes for each watch_domain
3. Compute intersections (set operations)
4. Apply domain matching rule (all_required or any_required)
5. Return matched_domains list

**Problem:** Technology matching is binary (keyword present or not). No distinction between category types.

#### 3.2.2 Proposed Enhancement

**New matching flow for technology domains with profiles:**

1. **Detect technology scope profile:**
   - Check if technology_scope has `_metadata.profile`
   - Load corresponding profile from domain_matching_rules

2. **Categorize detected technology keywords:**
   - For each detected technology keyword, identify its category
   - Build category_matches dict: `{category_name: [matched_keywords]}`

3. **Evaluate signal requirements:**
   - Check high_precision_signals: count matches in core_phrases + technology_terms_high_precision
   - Check supporting_signals: count matches in route_admin_terms + interval_patterns
   - Check context_signals: count matches in technology_use
   - Check negative_filters: detect any negative_terms

4. **Apply company scope modifiers:**
   - Identify if detected companies belong to pure_player_scopes or hybrid_scopes
   - Apply different thresholds based on company type

5. **Evaluate combination_logic:**
   - Parse and apply the logic expression from profile
   - Return match decision with confidence score

6. **Attach matching_details to item:**
   ```python
   item['matching_details'] = {
       'domain_id': domain_id,
       'rule_applied': 'technology_complex',
       'categories_matched': {
           'core_phrases': ['long-acting injectable'],
           'route_admin_terms': ['subcutaneous'],
           'technology_use': []
       },
       'signals_used': {
           'high_precision': 1,
           'supporting': 1,
           'context': 0
       },
       'scopes_hit': {
           'companies': ['MedinCell'],
           'company_scope': 'lai_companies_pure_players'
       },
       'negative_terms_detected': [],
       'match_confidence': 'high'
   }
   ```

#### 3.2.3 Implementation Strategy

**New functions in matcher.py:**

```python
def _load_technology_profile(technology_scope_key, canonical_scopes, matching_rules):
    """Load profile metadata for a technology scope."""
    pass

def _categorize_technology_keywords(detected_keywords, technology_scope_data):
    """Map detected keywords to their categories."""
    pass

def _evaluate_technology_profile_match(
    category_matches,
    profile,
    item_companies,
    canonical_scopes
):
    """Evaluate if item matches technology profile requirements."""
    pass

def _detect_negative_terms(item_text, negative_terms_list):
    """Check if item contains negative terms."""
    pass
```

**Modified function:**

```python
def match_items_to_domains(...):
    # Existing logic for non-technology domains
    # Enhanced logic for technology domains with profiles
    pass
```

#### 3.2.4 Logging Enhancement

**Add structured logging for diagnostics:**

```python
logger.info(
    f"Technology profile match: domain={domain_id}, "
    f"profile={profile_name}, "
    f"high_precision={hp_count}, "
    f"supporting={sup_count}, "
    f"company_type={company_type}, "
    f"decision={match_decision}"
)
```

#### 3.2.5 Definition of Done - Phase 2

- ✅ `matcher.py` updated with profile-aware matching logic
- ✅ Category-based keyword detection implemented
- ✅ Company scope modifiers (pure_player vs hybrid) implemented
- ✅ Negative term filtering implemented
- ✅ `matching_details` structure added to matched items
- ✅ Comprehensive logging added
- ✅ Unit tests created for new functions
- ✅ Integration test: run engine on test corpus, verify matching_details populated
- ✅ Diagnostic report: compare old vs new matching results

---

### PHASE 3 — Scoring Adaptation

**Objective:** Adapt `scorer.py` to leverage matching_details and company scope distinctions.

#### 3.3.1 Current Scoring Logic

**Current factors in scorer.py:**
1. Event type weight
2. Domain priority weight
3. Recency factor
4. Source type weight
5. Signal depth bonus (entity count)
6. Pure player bonus (hardcoded scope reference)

**Problem:** Pure player bonus uses a single scope (`lai_companies_mvp_core`). Doesn't leverage match confidence or signal quality.

#### 3.3.2 Proposed Enhancement

**New scoring factors:**

1. **Match confidence multiplier:**
   - High confidence match (core_phrases + pure_player): 1.5x
   - Medium confidence match (supporting signals + hybrid): 1.2x
   - Low confidence match (minimal signals): 1.0x

2. **Company scope bonus (generic):**
   - Pure player company: bonus from scoring_rules (existing)
   - Hybrid company with strong signals: reduced bonus
   - No company or weak signals: no bonus

3. **Signal quality score:**
   - Based on categories_matched from matching_details
   - High-precision categories: +2 points per match
   - Supporting categories: +1 point per match
   - Context categories: +0.5 points per match

4. **Negative term penalty:**
   - If negative_terms_detected in matching_details: -10 points or score = 0

#### 3.3.3 Implementation Strategy

**Modified function in scorer.py:**

```python
def compute_score(item, scoring_rules, domain_priority, canonical_scopes):
    # Existing base score calculation
    base_score = event_weight * priority_weight * recency_factor * source_weight
    
    # NEW: Extract matching details
    matching_details = item.get('matching_details', {})
    
    # NEW: Match confidence multiplier
    match_confidence = matching_details.get('match_confidence', 'medium')
    confidence_multipliers = {
        'high': 1.5,
        'medium': 1.2,
        'low': 1.0
    }
    confidence_multiplier = confidence_multipliers.get(match_confidence, 1.0)
    
    # NEW: Signal quality score
    signal_quality_score = _compute_signal_quality_score(matching_details)
    
    # ENHANCED: Pure player bonus (generic via scope)
    pure_player_bonus = _compute_company_scope_bonus(
        item, 
        canonical_scopes, 
        scoring_rules,
        matching_details
    )
    
    # NEW: Negative term penalty
    negative_penalty = 0
    if matching_details.get('negative_terms_detected'):
        negative_penalty = scoring_rules.get('other_factors', {}).get('negative_term_penalty', 10)
    
    # Final score
    final_score = (base_score * confidence_multiplier) + signal_quality_score + pure_player_bonus - negative_penalty
    
    return max(0, round(final_score, 2))
```

**New helper functions:**

```python
def _compute_signal_quality_score(matching_details):
    """Calculate bonus based on signal category quality."""
    pass

def _compute_company_scope_bonus(item, canonical_scopes, scoring_rules, matching_details):
    """Calculate company bonus based on scope type (pure_player vs hybrid)."""
    pass
```

#### 3.3.4 Scoring Rules Configuration

**Extend scoring_rules.yaml:**

```yaml
other_factors:
  # Existing factors...
  
  # NEW: Match confidence multipliers
  match_confidence_multiplier_high: 1.5
  match_confidence_multiplier_medium: 1.2
  match_confidence_multiplier_low: 1.0
  
  # NEW: Signal quality weights
  signal_quality_weight_high_precision: 2.0
  signal_quality_weight_supporting: 1.0
  signal_quality_weight_context: 0.5
  
  # NEW: Negative term penalty
  negative_term_penalty: 10
  
  # ENHANCED: Pure player bonus (now references scope dynamically)
  pure_player_bonus: 3
  pure_player_scopes: [lai_companies_pure_players, lai_companies_mvp_core]
  
  # NEW: Hybrid company bonus (reduced)
  hybrid_company_bonus: 1
  hybrid_company_scopes: [lai_companies_hybrid]
```

#### 3.3.5 Definition of Done - Phase 3

- ✅ `scorer.py` updated with match confidence multiplier
- ✅ Signal quality scoring implemented
- ✅ Company scope bonus generalized (pure_player vs hybrid)
- ✅ Negative term penalty implemented
- ✅ `scoring_rules.yaml` extended with new factors
- ✅ Unit tests for new scoring logic
- ✅ Integration test: verify scores reflect signal quality
- ✅ Diagnostic report: score distribution analysis (before/after)

---

### PHASE 4 — Deployment, Testing & Diagnostics

**Objective:** Safe rollout in DEV with comprehensive testing and diagnostics.

#### 3.4.1 Deployment Strategy

**Step 1: Package & Deploy**
1. Run existing packaging script: `package-engine.ps1`
2. Deploy to DEV Lambda: `deploy-engine-dev.ps1`
3. Verify deployment: check Lambda version, test invocation

**Step 2: Smoke Test**
1. Run test script: `test-engine-lai-weekly.ps1`
2. Verify newsletter generated in S3
3. Check CloudWatch logs for errors

**Step 3: Diagnostic Analysis**
1. Download generated newsletter
2. Analyze items selected
3. Verify matching_details populated
4. Calculate LAI precision metrics

#### 3.4.2 Test Scenarios

**Test 1: Pure Player with Strong LAI Signal**
- Input: "MedinCell announces long-acting injectable formulation"
- Expected: MATCH (high confidence), high score, selected

**Test 2: Hybrid Company with Weak Signal**
- Input: "Pfizer reports quarterly earnings"
- Expected: NO MATCH, not selected

**Test 3: Hybrid Company with Strong LAI Signal**
- Input: "AbbVie's Skyrizi extended-release injectable shows efficacy in Phase 3"
- Expected: MATCH (medium confidence), medium score, potentially selected

**Test 4: Negative Term Filtering**
- Input: "Camurus develops oral tablet formulation"
- Expected: NO MATCH or very low score (negative term detected)

**Test 5: Generic Term Only**
- Input: "Takeda advances drug delivery system for oncology"
- Expected: NO MATCH (generic_terms alone insufficient)

#### 3.4.3 Diagnostic Document Structure

**Create: `docs/diagnostics/vectora_inbox_lai_mvp_matching_v2_results.md`**

**Sections:**
1. **Executive Summary**
   - Date, environment, test corpus size
   - Key metrics: precision, recall, false positives
   - Comparison with previous version

2. **Quantitative Results**
   - Items analyzed: X
   - Items matched: Y (Z%)
   - Items selected: W
   - LAI precision: P%
   - Pure player representation: Q%
   - False positives: R

3. **Qualitative Analysis**
   - Examples of correctly matched items (true positives)
   - Examples of correctly rejected items (true negatives)
   - Examples of false positives (if any) with root cause
   - Examples of false negatives (if any) with root cause

4. **Matching Details Analysis**
   - Distribution of match confidence levels
   - Most common category combinations
   - Company scope distribution (pure_player vs hybrid)
   - Negative terms detected (count)

5. **Scoring Analysis**
   - Score distribution histogram
   - Average score by match confidence
   - Pure player bonus impact
   - Signal quality score impact

6. **Recommendations**
   - Threshold adjustments needed
   - Scope refinements needed
   - Rule modifications needed

#### 3.4.4 Rollback Strategy

**If LAI precision < 50% or critical issues detected:**

1. **Immediate rollback:**
   - Redeploy previous Lambda version
   - Verify old version operational
   - Document rollback reason

2. **Root cause analysis:**
   - Review diagnostic report
   - Identify specific failure mode
   - Propose fix

3. **Iterative refinement:**
   - Adjust rules in canonical (not code)
   - Redeploy and retest
   - Repeat until KPIs met

#### 3.4.5 Success Criteria

**Minimum acceptance criteria for Phase 4:**
- ✅ LAI precision ≥ 80%
- ✅ Pure player representation ≥ 50%
- ✅ False positives (obvious non-LAI) = 0
- ✅ No runtime errors in CloudWatch logs
- ✅ Newsletter generated successfully
- ✅ Matching_details populated for all matched items

**Stretch goals:**
- LAI precision ≥ 90%
- Pure player representation ≥ 70%
- Recall ≥ 80% (capture most true LAI items)

#### 3.4.6 Definition of Done - Phase 4

- ✅ Engine Lambda deployed to DEV
- ✅ Test script executed successfully
- ✅ Newsletter generated and analyzed
- ✅ Diagnostic report created with metrics
- ✅ Success criteria met OR rollback executed with documented reason
- ✅ Lessons learned documented
- ✅ Go/No-Go decision for PROD deployment

---

## 4. Technical Architecture Decisions

### 4.1 Why Category-Based Matching?

**Alternative considered:** Keyword-level weights in canonical scopes

**Decision:** Category-based matching in domain_matching_rules

**Rationale:**
- Keeps canonical scopes clean (just lists of keywords)
- Matching logic centralized in rules (easier to adjust)
- Reusable for other verticals (oncology can define own categories)
- No code changes needed to adjust matching behavior

### 4.2 Why Company Scope Modifiers?

**Alternative considered:** Separate domain rules for pure_player vs hybrid

**Decision:** Single rule with company scope modifiers

**Rationale:**
- Avoids duplication of domain definitions in client config
- Maintains single source of truth for technology matching
- Allows gradual refinement of company classifications
- Easier to test (one rule to validate)

### 4.3 Why Matching Details Structure?

**Alternative considered:** Just log matching decisions

**Decision:** Attach matching_details to each item

**Rationale:**
- Enables downstream scoring to use match quality
- Facilitates diagnostics (can analyze without re-running)
- Supports future features (explain why item was selected)
- Minimal performance impact (small dict per item)

### 4.4 Why Negative Term Filtering?

**Alternative considered:** Just rely on positive signals

**Decision:** Explicit negative term detection and penalty

**Rationale:**
- Prevents edge cases (e.g., article comparing LAI vs oral)
- Improves precision with minimal complexity
- Easy to maintain (just a list in canonical)
- Aligns with business requirement (0 obvious false positives)

---

## 5. Risk Analysis & Mitigation

### 5.1 Risk: Over-Complexity in Rules

**Description:** Technology_profiles become too complex to maintain

**Likelihood:** Medium  
**Impact:** High (blocks future verticals)

**Mitigation:**
- Start with simple profiles (technology_complex, technology_simple)
- Document each rule with examples
- Provide validation tools (YAML linter, rule tester)
- Regular review and simplification

### 5.2 Risk: Performance Degradation

**Description:** Category-based matching slower than simple intersection

**Likelihood:** Low  
**Impact:** Medium (Lambda timeout)

**Mitigation:**
- Profile matching logic during development
- Optimize hot paths (category lookup, scope checks)
- Monitor Lambda execution time in CloudWatch
- Set timeout alerts

### 5.3 Risk: False Negatives Increase

**Description:** Stricter matching misses valid LAI items

**Likelihood:** Medium  
**Impact:** Medium (reduced recall)

**Mitigation:**
- Measure recall in diagnostics (not just precision)
- Maintain test corpus of known LAI items
- Iteratively adjust thresholds based on false negatives
- Accept some false negatives to achieve precision target

### 5.4 Risk: Canonical Drift

**Description:** Scopes and rules become inconsistent over time

**Likelihood:** Medium  
**Impact:** High (matching breaks)

**Mitigation:**
- Automated validation: check scope references in rules
- Version control for canonical (Git)
- Change log for all canonical updates
- Periodic audits (quarterly review)

---

## 6. Testing Strategy

### 6.1 Unit Tests

**New test files:**
- `tests/test_matcher_profiles.py`: Test profile loading and evaluation
- `tests/test_matcher_categories.py`: Test category-based keyword detection
- `tests/test_scorer_confidence.py`: Test match confidence scoring

**Coverage target:** ≥ 80% for new functions

### 6.2 Integration Tests

**Test scenarios:**
1. End-to-end with test corpus (50 items, known LAI/non-LAI labels)
2. Verify matching_details populated correctly
3. Verify scores reflect signal quality
4. Verify negative term filtering works

**Test data:**
- `tests/data/lai_test_corpus.json`: Curated test items with labels

### 6.3 Regression Tests

**Ensure no breaking changes:**
1. Run engine on previous test corpus
2. Verify non-LAI domains still work (if any exist)
3. Verify newsletter generation still works
4. Verify S3 output format unchanged

### 6.4 Performance Tests

**Measure execution time:**
1. Baseline: current matcher.py on 100 items
2. New version: profile-aware matcher.py on 100 items
3. Target: < 10% increase in execution time

---

## 7. Documentation Deliverables

### 7.1 Per-Phase Documents

**Phase 1:**
- `canonical/matching/README.md` (updated with profiles)
- `docs/diagnostics/phase1_rules_enhancement.md`

**Phase 2:**
- `src/vectora_core/matching/README.md` (new, explains matcher logic)
- `docs/diagnostics/phase2_matcher_adaptation.md`

**Phase 3:**
- `src/vectora_core/scoring/README.md` (new, explains scorer logic)
- `docs/diagnostics/phase3_scorer_adaptation.md`

**Phase 4:**
- `docs/diagnostics/vectora_inbox_lai_mvp_matching_v2_results.md`
- `docs/diagnostics/vectora_inbox_lai_mvp_phase4_deployment_report.md`

### 7.2 Updated Documents

- `CHANGELOG.md`: Entry for each phase
- `README.md`: Update architecture section if needed
- `docs/design/vectora_inbox_lai_technology_scopes_refactor_plan.md`: Mark as completed

---

## 8. Timeline Estimate

**Phase 1 (Rules Enhancement):**
- Design & implementation: 2 hours
- Validation & documentation: 1 hour
- **Total: 3 hours**

**Phase 2 (Matcher Adaptation):**
- Implementation: 4 hours
- Unit tests: 2 hours
- Integration tests: 2 hours
- Documentation: 1 hour
- **Total: 9 hours**

**Phase 3 (Scorer Adaptation):**
- Implementation: 3 hours
- Unit tests: 1 hour
- Integration tests: 1 hour
- Documentation: 1 hour
- **Total: 6 hours**

**Phase 4 (Deployment & Diagnostics):**
- Deployment: 1 hour
- Testing: 2 hours
- Diagnostic analysis: 2 hours
- Documentation: 1 hour
- **Total: 6 hours**

**Grand Total: 24 hours (3 working days)**

---

## 9. Success Metrics Summary

### 9.1 Technical Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Code coverage (new functions) | 0% | ≥80% | pytest --cov |
| Lambda execution time | 30s | <33s | CloudWatch |
| Matching_details populated | 0% | 100% | Diagnostic script |
| YAML validation errors | 0 | 0 | yamllint |

### 9.2 Business Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| LAI precision | 0% | ≥80% | Manual review |
| Pure player representation | 0% | ≥50% | Automated count |
| False positives | 5/5 | 0 | Manual review |
| Items selected | 5 | 5-10 | Newsletter count |

### 9.3 Operational Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Deployment success rate | 100% | CI/CD logs |
| Rollback time (if needed) | <15 min | Manual timing |
| Documentation completeness | 100% | Checklist |

---

## 10. Conclusion & Next Steps

### 10.1 Summary

This plan defines a **4-phase approach** to adapt the Vectora Inbox runtime to exploit the new 7-category LAI canonical structure:

1. **Phase 1:** Enhance domain matching rules with technology profiles
2. **Phase 2:** Adapt matcher.py for category-based matching
3. **Phase 3:** Adapt scorer.py for match confidence and signal quality
4. **Phase 4:** Deploy, test, and diagnose in DEV

**Key principles maintained:**
- ✅ Generic, configuration-driven runtime
- ✅ No LAI-specific hardcoding
- ✅ Reusable for other verticals
- ✅ Operational continuity at each phase

**Expected outcome:**
- LAI precision: 0% → ≥80%
- Pure player representation: 0% → ≥50%
- False positives: 5 → 0

### 10.2 Approval Required

**This is a design document only. No code has been modified yet.**

**Before proceeding to Phase 1 execution, I need your explicit approval.**

---

**Question pour vous:**

Souhaites-tu que je commence la **Phase 1** (adaptation des règles de matching) ?

Si oui, réponds par quelque chose comme **"GO PHASE 1"** et je l'exécuterai étape par étape, avec tests et diagnostics à chaque phase.

Si tu souhaites des ajustements au plan, indique-moi les modifications souhaitées et je mettrai à jour ce document.

---

**Document Status:** ✅ READY FOR REVIEW  
**Next Action:** AWAITING APPROVAL TO START PHASE 1
