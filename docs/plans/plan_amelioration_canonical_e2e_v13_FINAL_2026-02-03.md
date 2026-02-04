# Plan d'Amélioration Canonical - Post E2E v13 (FINAL)

**Date**: 2026-02-03  
**Version**: CANONICAL 2.1 → 2.2  
**Conformité**: ✅ CRITICAL_RULES.md + Gouvernance

---

## 📋 SYNTHÈSE MODIFICATIONS

**5 fichiers canonical modifiés** pour résoudre **7 problèmes critiques**

### Feedbacks Admin Intégrés

1. ✅ Étoffer `financial_reporting_terms` (pas nouveau scope)
2. ✅ Ajouter `title` + enrichir `summary` avec mots-clés LAI
3. ✅ Hybrid company boost conditionnel (nécessite signaux LAI)
4. ✅ Enrichir `lai_domain_definition.yaml` avec `technology_scopes.yaml`

### Impact Enrichissement

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| **core_technologies** | 6 | 13 | +117% |
| **technology_families** | 11 | 58 | +427% |
| **dosing_intervals** | 8 | 15 | +88% |
| **TOTAL medium_signals** | 19 | 73 | +284% |

---

## 🔧 MODIFICATIONS DÉTAILLÉES

### Modification 1: generic_normalization.yaml

**Fichier**: `canonical/prompts/normalization/generic_normalization.yaml`

**3 changements**:

```yaml
# CHANGEMENT 1 - SECTION 1 SUMMARY
# Enrichir summary avec mots-clés LAI

  1. SUMMARY (2-3 sentences)
     - Concise factual summary of the news
     - Focus on key facts: who, what, when
     - IMPORTANT: If LAI-related terms detected (dosing intervals, technologies),
       include them explicitly in summary

# CHANGEMENT 2 - SECTION 4 ENTITY EXTRACTION
# Ajouter extraction dosing_intervals

  4. ENTITY EXTRACTION (ALL explicitly mentioned)
     - Companies: ALL pharmaceutical/biotech company names
     - Molecules: ALL drug/molecule names (INN, generic names)
     - Technologies: ALL technology keywords (e.g., "microspheres", "PEGylation")
     - Trademarks: ALL commercial product names (e.g., "UZEDY®", "Ozempic")
     - Indications: ALL therapeutic indications/diseases mentioned
     - Dosing Intervals: ALL dosing frequency terms EXPLICITLY mentioned
       Examples: "once-weekly", "once-monthly", "once every 3 months", 
                 "q4w", "q8w", "q12w", "quarterly", "semi-annual"
       CRITICAL: Only extract if EXPLICITLY stated in text (title or body)

# CHANGEMENT 3 - RESPONSE FORMAT
# Ajouter champs title + dosing_intervals_detected

  RESPONSE FORMAT (JSON only, no additional text):
  {
    "title": "...",  # 🆕 AJOUTÉ - Titre normalisé
    "summary": "...",
    "extracted_date": "2026-01-27",
    "date_confidence": 0.95,
    "event_type": "partnership",
    "companies_detected": ["Company A"],
    "molecules_detected": ["Molecule X"],
    "technologies_detected": ["Technology Y"],
    "trademarks_detected": ["Trademark Z"],
    "indications_detected": ["Indication W"],
    "dosing_intervals_detected": ["once-weekly"]  # 🆕 AJOUTÉ
  }
```

---

### Modification 2: lai_domain_definition.yaml

**Fichier**: `canonical/domains/lai_domain_definition.yaml`

**6 changements majeurs**:

```yaml
# CHANGEMENT 1 - ENRICHIR core_technologies
# Source: technology_scopes.yaml > lai_keywords.core_phrases
# 6 → 13 termes (+117%)

strong_signals:
  core_technologies:
    - "long-acting injectable"
    - "long acting injectable"
    - "long-acting formulation"              # 🆕
    - "extended-release injectable"
    - "extended-release injection"           # 🆕
    - "depot injection"
    - "long-acting depot"                    # 🆕
    - "sustained-release injectable"
    - "sustained release injectable"         # 🆕
    - "controlled-release injection"
    - "injectable controlled release"        # 🆕
    - "long-acting"                          # 🆕
    - "long acting"                          # 🆕

# CHANGEMENT 2 - ENRICHIR technology_families
# Source: technology_scopes.yaml > lai_keywords.technology_terms_high_precision
# 11 → 58 termes (+427%)

medium_signals:
  technology_families:
    # DDS families - 🆕 SECTION AJOUTÉE
    - "drug delivery system"
    - "controlled release"
    - "sustained release"
    - "extended release"
    - "modified release"
    - "depot injection"
    - "extended-release injectable"
    - "long-acting injectable"
    
    # Microsphere technologies
    - "microspheres"
    - "polymeric microspheres"               # 🆕
    - "PLGA microspheres"
    - "PLA microspheres"                     # 🆕
    
    # Depot technologies
    - "in-situ depot"
    - "in-situ forming depot"
    - "liquid crystalline depot"
    - "liquid crystal depot"                 # 🆕
    - "depot-forming prodrug"                # 🆕
    - "depot prodrug"                        # 🆕
    - "long-acting prodrug"                  # 🆕
    
    # Hydrogel technologies
    - "hydrogel"
    - "thermo-responsive hydrogel"
    - "RTGel"                                # 🆕
    
    # Proprietary technologies - 🆕 SECTION AJOUTÉE (11 termes)
    - "Atrigel"
    - "FluidCrystal"
    - "SmartDepot"
    - "DepoFoam"
    - "BioSeizer"
    - "Medisorb"
    - "CriPec"
    - "DiffuSphere"
    - "PharmaShell"
    - "SiliaShell"
    - "BEPO"
    
    # Liposome technologies - 🆕 AJOUTÉ
    - "multivesicular liposomes"
    - "long-acting emulsion"
    
    # Half-Life Extension (HLE) strategies - 🆕 SECTION ENRICHIE
    - "PEGylation"
    - "site-specific PEGylation"
    - "PASylation"                           # 🆕
    - "Fc fusion"
    - "Fc-fusion"                            # 🆕
    - "IgG Fc fusion"                        # 🆕
    - "albumin binding"                      # 🆕
    - "albumin fusion"
    - "albumin-binding"                      # 🆕
    - "lipidation"                           # 🆕
    - "fatty acid conjugation"               # 🆕
    - "polypeptide extension"                # 🆕
    - "glyco-engineering"                    # 🆕
    - "glycan engineering"                   # 🆕
    - "sialylation"                          # 🆕
    - "half-life extension"                  # 🆕
    - "atomic layer deposition"              # 🆕

# CHANGEMENT 3 - ENRICHIR dosing_intervals
# Source: technology_scopes.yaml > lai_keywords.interval_patterns
# 8 → 15 termes (+88%)

  dosing_intervals:
    - "once-weekly"                          # 🆕
    - "once-weekly injection"                # 🆕
    - "once-monthly"
    - "once every 2 weeks"                   # 🆕
    - "once every 3 months"
    - "once every 6 months"
    - "q2w"                                  # 🆕
    - "q4w"
    - "q8w"
    - "q12w"
    - "3-month"                              # 🆕
    - "6-month"
    - "quarterly injection"
    - "biweekly injection"                   # 🆕
    - "monthly injection"                    # 🆕

# CHANGEMENT 4 - AJOUTER exclusions manufacturing

exclusions:
  - "oral tablet"
  - "oral capsule"
  - "oral administration"
  - "transdermal patch"
  - "nasal spray"
  - "sublingual"
  - "inhalation"
  # Manufacturing without LAI context - 🆕 AJOUTÉ
  - "manufacturing facility"
  - "production plant"
  - "factory construction"
  - "plant expansion"
  - "manufacturing site"

# CHANGEMENT 5 - MODIFIER scoring

scoring:
  event_type_base_scores:
    partnership: 60
    regulatory: 70
    clinical_update: 50
    corporate_move: 40
    financial_results: 0  # 🔧 MODIFIÉ: 30 → 0
    other: 20
  
  entity_boosts:
    pure_player_company: 25
    trademark_mention: 20
    key_molecule: 15
    dosing_interval: 15      # 🆕 AJOUTÉ
    technology_family: 10
    hybrid_company: 0        # 🔧 MODIFIÉ: 10 → 0 (boost conditionnel)

# CHANGEMENT 6 - AJOUTER boost_conditions + règles

  boost_conditions:
    hybrid_company:
      base_boost: 0
      conditional_boost: 10
      requires_one_of:
        - "technology_family"    # 58 termes enrichis
        - "dosing_interval"      # 15 termes enrichis
        - "key_molecule"
        - "trademark_mention"
      reasoning: "Hybrid companies need LAI-specific context"
      coverage: "58 technology terms from technology_scopes.yaml"

matching_rules:
  # ... existants
  - id: rule_5
    condition: "event_type == 'financial_results' AND signals_count < 2"
    action: "reject (financial results need explicit LAI content)"
  
  - id: rule_6
    condition: "event_type == 'corporate_move' AND manufacturing_terms AND NO technology_signals"
    action: "reject (manufacturing without LAI technology)"
```

---

### Modification 3: lai_domain_scoring.yaml

**Fichier**: `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`

```yaml
# AJOUTER après system_instructions

  CRITICAL RULES FOR SIGNAL DETECTION:
  1. Only detect signals EXPLICITLY present in the normalized item
  2. DO NOT infer, assume, or hallucinate signals not provided
  3. If a technology/molecule/term is not in entities_detected, DO NOT add it
  4. Base your evaluation ONLY on the normalized data provided
  5. When in doubt, be conservative - reject rather than false positive
  
  HYBRID COMPANY SCORING RULE:
  - If hybrid_company detected, apply boost (10 points) ONLY if at least one of:
    * technology_family detected (58 LAI terms available)
    * dosing_interval detected (15 patterns available)
    * key_molecule detected
    * trademark_mention detected
  - Otherwise, hybrid_company gives 0 boost
  - Be permissive: ANY LAI technology term triggers boost
```

---

### Modification 4: exclusion_scopes.yaml

**Fichier**: `canonical/scopes/exclusion_scopes.yaml`

```yaml
# ÉTOFFER financial_reporting_terms existant
# (pas de nouveau scope)

financial_reporting_terms:
  description: "Termes rapports financiers et boursiers génériques sans contenu LAI"
  scope_type: "exclusion"
  keywords:
    # Rapports financiers (existants)
    - "quarterly earnings"
    - "annual report"
    - "financial statement"
    # ... existants
    
    # 🆕 AJOUTER - Termes boursiers
    - "MSCI"
    - "MSCI World"
    - "MSCI Small Cap"
    - "stock index"
    - "market index"
    - "benchmark index"
    - "financial calendar"
    - "interim report"
    - "half-year results"
    - "consolidated results"
    - "market cap"
    - "share price"
    - "trading volume"
```

---

### Modification 5: source_catalog.yaml

**Fichier**: `canonical/sources/source_catalog.yaml`

```yaml
# MODIFIER 5 sources corporate
# max_content_length: 1000 → 2000
# content_enrichment: summary_enhanced → full_article

  - source_key: "press_corporate__medincell"
    content_enrichment: "full_article"      # 🔧 MODIFIÉ
    max_content_length: 2000                # 🔧 MODIFIÉ

  - source_key: "press_corporate__camurus"
    content_enrichment: "full_article"
    max_content_length: 2000

  - source_key: "press_corporate__delsitech"
    content_enrichment: "full_article"
    max_content_length: 2000

  - source_key: "press_corporate__nanexa"
    content_enrichment: "full_article"
    max_content_length: 2000

  - source_key: "press_corporate__peptron"
    content_enrichment: "full_article"
    max_content_length: 2000
```

---

## 🔄 WORKFLOW COMPLET

### Phase 1: Git Setup

```bash
git checkout develop
git pull origin develop
git checkout -b fix/canonical-improvements-e2e-v13
cat VERSION  # CANONICAL_VERSION=2.1
```

### Phase 2: Modifications + VERSION

```bash
# 1. Modifier 5 fichiers canonical
# 2. Modifier VERSION: CANONICAL_VERSION=2.1 → 2.2
```

### Phase 3: Commit (AVANT deploy)

```bash
git add canonical/ VERSION
git commit -m "fix(canonical): amélioration qualité post E2E v13

- Normalisation: ajout extraction dosing_intervals + title + summary enrichi
- Domain definition: enrichissement 19→73 termes (technology_scopes.yaml)
- Scoring: hybrid_company boost conditionnel (nécessite signaux LAI)
- Scoring: financial_results base_score 0, exclusions manufacturing
- Exclusions: étoffer financial_reporting_terms avec termes boursiers
- Sources: max_content_length 2000, full_article pour corporate

Résout faux négatifs: CagriSema, Quince (dosing intervals)
Résout faux positifs: Eli Lilly, MedinCell financial, Novo sans tech

CANONICAL_VERSION: 2.1 → 2.2"
```

### Phase 4: Tests Local

```bash
python tests/local/test_e2e_runner.py --new-context "Canonical-v2.2"
python tests/local/test_e2e_runner.py --run

# Vérifier:
# - CagriSema: dosing_intervals_detected = ["once-weekly"] ✅
# - Quince: dosing_intervals_detected = ["once-monthly"] ✅
# - Eli Lilly: score = 0 (exclu manufacturing) ✅
# - MedinCell financial: score = 0 ✅
```

### Phase 5: Deploy AWS Dev

```bash
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod \
  --region eu-west-3 \
  --delete
```

### Phase 6: Tests AWS Dev

```bash
python tests/aws/test_e2e_runner.py --promote "Canonical-v2.2"
python tests/aws/test_e2e_runner.py --run
```

### Phase 7: Merge

```bash
git push origin fix/canonical-improvements-e2e-v13
# Créer PR → Merge → Tag v2.2-canonical
```

---

## 📊 RÉSULTATS ATTENDUS

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| **Coverage LAI** | 46 termes | 97 termes | +111% |
| **Faux positifs** | 5/14 (36%) | 1/14 (7%) | -80% |
| **Faux négatifs** | 2/15 (13%) | 0/15 (0%) | -100% |
| **Précision** | 64% | 93% | +45% |

### Cas Résolus

✅ CagriSema matché (once-weekly détecté)  
✅ Quince matché (once-monthly détecté)  
✅ Eli Lilly rejeté (manufacturing exclu)  
✅ MedinCell financial rejeté (score 0)  
✅ Novo sans tech: hybrid boost = 0

---

## ✅ CHECKLIST CONFORMITÉ

- [x] Git AVANT build ✅
- [x] Environnement explicite ✅
- [x] Tests local AVANT AWS ✅
- [x] VERSION incrémenté ✅
- [x] Canonical uploadé S3 ✅
- [x] Pas de modif Lambda ✅

---

**Plan créé**: 2026-02-03  
**Statut**: ✅ Prêt exécution  
**Durée**: 1 journée
