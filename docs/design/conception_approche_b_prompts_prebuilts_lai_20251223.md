# Conception Approche B: Prompts Pré-construits pour Vectora Inbox

**Date**: 2025-12-23  
**Auteur**: Expert Cloud AWS - Architecture Vectora Inbox  
**Objectif**: Conception détaillée de l'Approche B (Prompts Pré-construits) pour LAI

---

## 🎯 CONTEXTE ET AMBITION

### Vision Vectora Inbox

**Core Business**: Moteur d'intelligence sectorielle configurable pour biotech/pharma
- **Générique**: Support multi-verticales (LAI, Gene Therapy, Cell Therapy, etc.)
- **Configurable**: Pilotage par fichiers canonical + client_config
- **Maintenable**: Solo founder peut ajuster sans modifier le code
- **Scalable**: Ajout de clients et verticales sans refactoring

### Problème Actuel

**Hardcoding LAI dans bedrock_client.py**:
```python
# Ligne 200+ dans bedrock_client.py
lai_section = "\n\nLAI TECHNOLOGY FOCUS:\n"
lai_section += "Detect these LAI (Long-Acting Injectable) technologies:\n"
lai_section += "- Extended-Release Injectable\n"
lai_section += "- Three-Month Injectable\n"      # NOUVEAU - hardcodé
lai_section += "- Extended Protection\n"         # NOUVEAU pour malaria - hardcodé
```

**Conséquences**:
- ❌ Impossible d'adapter à Gene Therapy sans modifier le code
- ❌ Bidouillages successifs (malaria grant)
- ❌ Viole le principe "Configuration > Code"
- ❌ Maintenance complexe et fragile

### Objectif de l'Approche B

**Prompts Pré-construits dans Canonical**:
- Prompts figés par verticale dans `canonical/prompts/`
- Références aux scopes canonical: `{{ref:lai_companies_global}}`
- Résolution simple et rapide au runtime
- Visibilité directe pour debugging et ajustements

---

## 📊 ANALYSE DE L'EXISTANT

### Architecture Actuelle des Appels Bedrock

**Flux identifié**:

```
normalize_score Lambda
  ↓
normalizer.normalize_items_batch()
  ↓ (pour chaque item)
BedrockNormalizationClient.normalize_item()
  ↓
_build_normalization_prompt_v2() OU _build_normalization_prompt_v1()
  ↓
call_bedrock_with_retry() → Bedrock API
  ↓
_parse_bedrock_response_v1()
  ↓
bedrock_matcher.match_item_to_domains_bedrock()
  ↓
_call_bedrock_matching() → Bedrock API
```

**Deux appels Bedrock par item**:
1. **Normalisation**: Extraction entités + classification event_type + score LAI
2. **Matching**: Évaluation pertinence par domaine de veille

### Fichiers Canonical Existants

**Structure actuelle**:

```
canonical/
├── scopes/
│   ├── company_scopes.yaml          # lai_companies_mvp_core, lai_companies_global
│   ├── technology_scopes.yaml       # lai_keywords (structure riche)
│   ├── molecule_scopes.yaml         # lai_molecules_global
│   ├── trademark_scopes.yaml        # lai_trademarks_global
│   └── indication_scopes.yaml       # addiction_keywords, etc.
├── prompts/
│   └── global_prompts.yaml          # Prompts actuels (hardcodés LAI)
└── events/
    └── event_type_patterns.yaml     # Patterns event_type
```

**Qualité des scopes existants**: ✅ Excellente
- Structure riche (core_phrases, technology_terms_high_precision, negative_terms)
- Métadonnées utiles (_metadata)
- Bien organisés par verticale (préfixe lai_)

### Client Config Existant

**lai_weekly_v5.yaml** (extrait):

```yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    type: "technology"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    trademark_scope: "lai_trademarks_global"
```

**Qualité**: ✅ Excellente
- Références claires aux scopes canonical
- Structure cohérente
- Prêt pour l'Approche B

---

## 🏗️ CONCEPTION APPROCHE B

### Principe Fondamental

**"Prompts Pré-construits + Références Canonical = Simplicité + Performance"**

Les prompts sont **écrits en dur** par verticale dans `canonical/prompts/`, avec des **références dynamiques** aux scopes pour éviter la duplication.

### Architecture Proposée

```
┌─────────────────────────────────────────────────────────────┐
│              CANONICAL/PROMPTS/ (Nouveaux fichiers)          │
│                                                              │
│  lai_normalization_prompt.yaml                               │
│  ├── Prompt complet LAI écrit en dur                        │
│  ├── Instructions anti-hallucinations                       │
│  ├── Références: {{ref:lai_companies_global}}               │
│  └── Références: {{ref:lai_keywords.core_phrases}}          │
│                                                              │
│  lai_matching_prompt.yaml                                    │
│  └── Prompt matching LAI avec références                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         CLIENT_CONFIG (lai_weekly_v5.yaml)                   │
│                                                              │
│  bedrock_config:                                             │
│    normalization_prompt: "lai_normalization"                 │
│    matching_prompt: "lai_matching"                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│    PROMPT_RESOLVER (nouveau module - 50 lignes)              │
│                                                              │
│  resolve_prompt_references()                                 │
│  ├── Charge prompt pré-construit                            │
│  ├── Résout {{ref:scope_name}}                              │
│  ├── Résout {{ref:scope_name.field}}                        │
│  └── Substitue {{item_text}}                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  BEDROCK API                                 │
│  Prompt final avec exemples résolus                         │
└─────────────────────────────────────────────────────────────┘
```

### Nouveaux Fichiers Canonical

#### 1. lai_normalization_prompt.yaml

**Emplacement**: `canonical/prompts/lai_normalization_prompt.yaml`

**Contenu** (structure complète):

