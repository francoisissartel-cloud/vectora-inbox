# Claude Development Rules for Vectora Inbox

**Version**: 1.0  
**Date**: 2026-04-22  
**Purpose**: Essential rules for Claude Code to develop Vectora Inbox robustly, simply and controlled

---

## 1. Project Overview

Vectora Inbox is a **data ingestion and datalake creation engine** following a "datalake-first" model.

**Core Flow**:
```
sources → continuous ingestion → raw datalake → normalized/enriched datalake
                                                        ↓
                              newsletters / reports / RAG / exports
```

**Key Principle**: Vectora Inbox creates the datalake foundation. Other tools (newsletters, RAG, dashboards) consume this datalake.

**Current Architecture**: V3 engine (src_v3/) is the active development base with configuration-driven approach.

### **Primary Focus: LAI Ecosystem**
- **Technology Scope**: Long-Acting Injectables (tech_lai_ecosystem)
- **Keywords**: Defined in `canonical/scopes/technology_scopes.yaml` (lai_keywords)
- **Target Companies**: LAI-focused pharmaceutical companies
- **MVP-First Approach**: Validate engine on MVP before extending to other sources

---

## 2. Core Architecture Rules

### **Separation of Concerns**
- **Ingestion ≠ Newsletter/RAG/Dashboards**
- Vectora Inbox = data ingestion + datalake creation ONLY
- Consumer tools are separate components

### **Datalake-First**
- Central datalake is the single source of truth
- All processing flows through structured data storage
- Raw → Normalized → Enriched data pipeline

### **No Client Runs for Ingestion**
- Ingestion runs are data-focused, not client-focused
- Client configurations define what data to extract
- Separation between data collection and data consumption

---

## 3. Development Workflow (MANDATORY)

### **Always Follow This Sequence**:
1. **Plan First** - Analyze requirements, propose approach
2. **User Validation** - Get explicit approval before coding
3. **Phase Execution** - Implement in small, testable phases
4. **Local Testing** - Validate each phase locally before proceeding

### **Never Skip Steps**:
- No coding without plan approval
- No multi-phase changes without intermediate validation
- No deployment without local testing success

---

## 4. Local-First Rule

### **Local Development Priority**:
- All development and testing happens locally
- Use local scripts and configurations
- Local validation before any external deployment

### **Local Tools**:
- Scripts in `scripts/` directory for all operations
- Local cache in `cache/` directory
- Local outputs in `output/` directory
- Configuration files in `canonical/` and `config/`

---

## 5. Configuration-Driven Development (CRITICAL)

### **Everything in Configuration Files**:
- **WHAT** to monitor: `canonical/sources/source_catalog_v3.yaml`
- **WHEN** to collect: `config/clients/{client_id}.yaml` (period_days)
- **HOW** to process: `canonical/ingestion/source_configs_v3.yaml`
- **WHO** to target: `canonical/scopes/technology_scopes.yaml` (lai_keywords)
- **WHERE** to filter: `canonical/ingestion/filter_rules_v3.yaml`

### **Generic Code + Configuration Control**:
- **Code must remain generic** and adaptable
- **Business logic controlled by canonical files**: periods, ingestion types, schedules
- **Add new capabilities through configuration**, not hardcoding
- **Code modifications allowed** when current code cannot support configuration needs

### **Configuration-Driven Examples**:
```python
# ✅ GOOD - Generic code driven by config
period_days = client_config['ingestion']['default_period_days']
ingestion_mode = source_config.get('ingestion_profile', 'balanced')
schedule = client_config.get('schedule', {}).get('frequency', 'on_demand')

# ❌ BAD - Hardcoded business logic
if client_id == "lai_weekly":
    period_days = 7
    use_special_processing()
```

### **When Code Changes Are Needed**:
- Current code cannot support new configuration options
- New ingestion patterns require code adaptation
- Performance optimizations for configuration-driven features
- **Always propose code changes** when configuration alone isn't sufficient

### **Configuration Files Control Everything**:
- Source URLs and parsing rules
- Technology keywords and scopes
- Client filtering preferences and schedules
- Processing timeouts and limits
- Ingestion frequencies and recurrence patterns
- Output formats and destinations

---

## 6. Strict Do / Do Not

### **DO**:
- Write reproducible scripts with clear parameters
- Analyze existing code before proposing changes
- Propose simple, incremental solutions
- Use configuration files for business logic
- Create backups before modifications
- Generate detailed reports and logs
- Test locally before any deployment

### **DO NOT**:
- Modify multiple components simultaneously
- Add unnecessary dependencies
- Hardcode business rules in Python code
- Mix ingestion logic with newsletter/scoring logic
- Skip validation steps
- Make assumptions about data formats
- Deploy without local testing

---

## 7. Debugging Protocol

### **Structured Diagnostic Format**:
When debugging issues, always provide:
- **Problem Description**: Clear statement of what's wrong
- **Current Behavior**: What actually happens
- **Expected Behavior**: What should happen
- **Investigation Steps**: What you checked
- **Root Cause Analysis**: Why it's happening
- **Proposed Solution**: How to fix it
- **Validation Plan**: How to verify the fix

### **Never Patch Without Understanding**:
- Always identify root cause before fixing
- Document why the problem occurred
- Ensure fix addresses cause, not just symptoms
- Test fix thoroughly before deployment

---

## 8. Data Model Principles

### **Structured Items/Events**:
- Consistent data structure across all sources
- Required fields: url, title, content, date, source_key
- Optional fields: company_id, event_type, domain_scores
- Proper date formatting and validation

### **Datalake Coherence**:
- Raw data preservation in original format
- Normalized data with consistent schema
- Enriched data with additional metadata
- Clear lineage from raw to enriched

### **Cache Management**:
- Client-specific caches to avoid false negatives
- URL-based caching with content validation
- Cache invalidation strategies
- Performance metrics tracking

---

## 9. How Claude Should Behave

### **Question When in Doubt**:
- Ask for clarification on ambiguous requirements
- Confirm understanding before implementation
- Validate assumptions with user
- Request examples when specifications are unclear

### **Always Simplify**:
- Propose the simplest solution that works
- Avoid unnecessary complexity
- Choose readable code over clever code
- Minimize dependencies and external calls

### **Validate Before Critical Steps**:
- Get approval before modifying core components
- Confirm backup creation before changes
- Validate test results before proceeding
- Check configuration consistency before deployment

### **Communication Style**:
- Be direct and specific in proposals
- Provide clear reasoning for recommendations
- Explain trade-offs when multiple options exist
- Give concrete examples rather than abstract descriptions

---

## 10. File Organization Rules

### **Source Code Structure**:
- **src_v3/**: Active development codebase
- **canonical/**: Configuration and business logic
- **scripts/**: Operational and maintenance scripts
- **cache/**: Local caching (client-specific)
- **output/**: Run results and reports

### **Configuration Management**:
- All sources in `canonical/sources/`
- All business rules in `canonical/ingestion/`
- All client configs in `config/clients/`
- No configuration in source code

### **Temporary Files**:
- Use `.tmp/` for temporary files
- Clean up temporary files after use
- Never leave temporary files in root directory
- Use descriptive names for temporary files

---

## 11. Testing and Validation

### **Local Testing Requirements**:
- Test individual components before integration
- Validate configuration files before use
- Check data quality in outputs
- Verify cache functionality

### **Validation Scripts**:
- Use existing validation scripts in `scripts/validation/`
- Create new validation scripts for new features
- Always run validation before considering work complete
- Document validation results

---

## 12. MVP-First Development Strategy

### **Validate on MVP Before Extension**:
- **Primary Target**: MVP client (`mvp_test_30days.yaml`)
- **Core Sources**: LAI ecosystem sources in `lai_full_mvp` bouquet
- **Technology Focus**: Long-Acting Injectables (lai_keywords scope)
- **Validation Criteria**: Engine must work perfectly on MVP before adding new sources

### **MVP Validation Process**:
1. **Test MVP Client**: Run `mvp_test_30days` configuration
2. **Verify LAI Detection**: Check technology_scopes.yaml matching
3. **Validate Source Processing**: Ensure all MVP sources work correctly
4. **Confirm Output Quality**: Review ingested items and reports
5. **Only Then Extend**: Add new sources/clients after MVP success

### **MVP Configuration Reference**:
- **Client Config**: `config/clients/mvp_test_30days.yaml`
- **Technology Scope**: `canonical/scopes/technology_scopes.yaml` (lai_keywords)
- **Source Bouquet**: `lai_full_mvp` in source_catalog_v3.yaml
- **Watch Domain**: `tech_lai_ecosystem`

---

## 13. Error Handling Standards

### **Graceful Degradation**:
- Continue processing other sources if one fails
- Generate reports even when errors occur
- Log errors with sufficient detail for debugging
- Provide fallback mechanisms where possible

### **Error Reporting**:
- Include error context and stack traces
- Categorize errors by severity
- Suggest remediation steps when possible
- Track error patterns for system improvement

---

**This document serves as the primary reference for Claude Code development work on Vectora Inbox. All development must comply with these rules.**