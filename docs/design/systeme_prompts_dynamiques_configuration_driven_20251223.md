# Système de Prompts Dynamiques Piloté par Configuration - Vectora Inbox

**Date**: 2025-12-23  
**Auteur**: Amazon Q Developer  
**Objectif**: Conception d'un système générique de création de prompts dynamiques pour Bedrock

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Problème Identifié

Le système actuel souffre de **hardcoding massif** dans les prompts Bedrock:
- Termes LAI hardcodés dans `bedrock_client.py`
- Logique métier mélangée avec instructions Bedrock
- Bidouillages successifs (malaria grant, Extended Protection)
- Impossible d'adapter à d'autres verticales sans modifier le code

### Solution Proposée

**Système de Prompts Dynamiques Piloté par Configuration**:
- Prompts génériques dans `canonical/prompts/global_prompts.yaml`
- Construction dynamique basée sur `client_config` et fichiers `canonical`
- Aucune modification de code pour ajuster le comportement
- Générique et applicable à toutes verticales

### Impact Attendu

- **Simplicité**: Ajustements par configuration uniquement
- **Généricité**: Support multi-verticales sans code spécifique
- **Maintenabilité**: Règles métier centralisées dans canonical
- **Puissance**: Pilotage fin du moteur par un humain

---

## 📊 DIAGNOSTIC DE L'EXISTANT

### 1. Architecture Actuelle des Appels Bedrock


**Flux actuel identifié**:

```
normalize_score Lambda
  ↓
normalizer.normalize_items_batch()
  ↓
BedrockNormalizationClient.normalize_item()
  ↓
_build_normalization_prompt_v2() OU _build_normalization_prompt_v1()
  ↓
call_bedrock_with_retry()
  ↓
bedrock_matcher.match_item_to_domains_bedrock()
  ↓
_call_bedrock_matching()
```

**Deux appels Bedrock par item**:
1. **Normalisation**: Extraction entités + classification event_type + score LAI
2. **Matching**: Évaluation pertinence par domaine de veille

### 2. Analyse du Prompt de Normalisation

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Problèmes identifiés**:

```python
# HARDCODING LAI - Ligne 200+
lai_section = "\n\nLAI TECHNOLOGY FOCUS:\n"
lai_section += "Detect these LAI (Long-Acting Injectable) technologies:\n"
lai_section += "- Extended-Release Injectable\n"
lai_section += "- Long-Acting Injectable\n"
lai_section += "- Three-Month Injectable\n"      # NOUVEAU - hardcodé
lai_section += "- Extended Protection\n"         # NOUVEAU pour malaria - hardcodé
```

**Conséquences**:
- ❌ Impossible d'utiliser pour Gene Therapy, Cell Therapy, etc.
- ❌ Bidouillages successifs pour cas particuliers
- ❌ Maintenance complexe et fragile
- ❌ Viole le principe de généricité

### 3. Analyse du Prompt de Matching

**Fichier**: `src_v2/vectora_core/normalization/bedrock_matcher.py`

**Constat**: Le prompt de matching est **déjà plus générique**:

```python
# Ligne 120+ - Construction dynamique depuis watch_domains
domains_context_text = "\n".join([
    f"- {d['domain_id']} ({d['domain_type']}): {'; '.join(d['focus_areas'])}"
    for d in domains_context
])
```

**Mais**: Il utilise les données du prompt de normalisation qui sont hardcodées LAI.

### 4. Analyse de client_config

**Fichier**: `client-config-examples/lai_weekly_v5.yaml`

**Opportunité majeure**:

```yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    type: "technology"
    technology_scope: "lai_keywords"        # Référence canonical
    company_scope: "lai_companies_global"   # Référence canonical
    trademark_scope: "lai_trademarks_global"
```

**Les watch_domains contiennent déjà toute l'information nécessaire** pour:
- Déduire la verticale (LAI, Gene Therapy, etc.)
- Construire les prompts dynamiquement
- Adapter le comportement du moteur

### 5. Analyse des Fichiers Canonical

**Structure actuelle**:

```
canonical/
├── scopes/
│   ├── company_scopes.yaml          # lai_companies_mvp_core, lai_companies_global
│   ├── technology_scopes.yaml       # lai_keywords (structure complexe)
│   ├── molecule_scopes.yaml
│   ├── trademark_scopes.yaml
│   └── indication_scopes.yaml
├── prompts/
│   └── global_prompts.yaml          # Prompts Bedrock (hardcodés LAI)
└── events/
    └── event_type_patterns.yaml     # Patterns event_type (sous-utilisé)
```

**Constat sur technology_scopes.yaml**:

```yaml
lai_keywords:
  _metadata:
    profile: technology_complex
    description: "Long-Acting Injectables - requires multiple signal types"
  core_phrases:
    - "long-acting injectable"
    - "extended-release injection"
  technology_terms_high_precision:
    - "drug delivery system"
    - "PharmaShell®"
  negative_terms:
    - "oral tablet"
    - "topical cream"
```

**Structure riche et bien conçue** mais **sous-exploitée** pour la construction des prompts.

---

## 🎯 CONCEPTION DU SYSTÈME DYNAMIQUE

### Principe Directeur

**"Configuration > Code"**

Les prompts Bedrock doivent être:
1. **Génériques**: Aucune référence à une verticale spécifique
2. **Paramétrables**: Variables substituées dynamiquement
3. **Pilotés par configuration**: `client_config` + `canonical` définissent tout

### Architecture Proposée


```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT_CONFIG.yaml                        │
│  watch_domains:                                              │
│    - id: tech_lai_ecosystem                                  │
│      technology_scope: lai_keywords                          │
│      company_scope: lai_companies_global                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              CANONICAL FILES (scopes/)                       │
│  technology_scopes.yaml:                                     │
│    lai_keywords:                                             │
│      core_phrases: [...]                                     │
│      negative_terms: [...]                                   │
│  company_scopes.yaml:                                        │
│    lai_companies_global: [MedinCell, Camurus, ...]          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│         PROMPT BUILDER (nouveau module)                      │
│  detect_vertical_characteristics()                           │
│  build_normalization_prompt_dynamic()                        │
│  build_matching_prompt_dynamic()                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│       CANONICAL PROMPTS (prompts/global_prompts.yaml)        │
│  normalization:                                              │
│    generic_biotech:                                          │
│      user_template: |                                        │
│        {{item_text}}                                         │
│        {{technology_focus_description}}                      │
│        {{companies_examples}}                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  BEDROCK API                                 │
│  Prompt final construit dynamiquement                        │
└─────────────────────────────────────────────────────────────┘
```

### Composants du Système

#### 1. Prompt Builder (Nouveau Module)

**Fichier**: `src_v2/vectora_core/shared/prompt_builder.py`

**Responsabilités**:
- Analyser `watch_domains` pour détecter la verticale
- Extraire exemples depuis `canonical_scopes`
- Construire descriptions dynamiques
- Substituer variables dans templates
- Générer prompts finaux pour Bedrock

**Fonctions principales**:

```python
def detect_vertical_characteristics(
    watch_domains: List[Dict],
    canonical_scopes: Dict
) -> Dict:
    """
    Détecte automatiquement les caractéristiques de la verticale
    depuis les watch_domains.
    
    Returns:
        {
            'vertical_name': 'LAI' | 'Gene Therapy' | 'Cell Therapy',
            'focus_areas': ['Long-Acting Injectable', ...],
            'companies_examples': ['MedinCell', 'Camurus', ...],
            'technologies_examples': ['Extended-Release Injectable', ...],
            'molecules_examples': ['buprenorphine', ...],
            'trademarks_examples': ['UZEDY', 'PharmaShell', ...],
            'relevance_question': 'How relevant is this to LAI technologies?',
            'anti_signals': ['oral tablet', 'topical cream'],
            'technology_focus_description': 'Detect LAI technologies: ...'
        }
    """
```

```python
def build_normalization_prompt_dynamic(
    item_text: str,
    watch_domains: List[Dict],
    canonical_scopes: Dict,
    canonical_prompts: Dict
) -> str:
    """
    Construit dynamiquement le prompt de normalisation.
    
    Process:
    1. Détecter caractéristiques verticale
    2. Récupérer template générique
    3. Substituer toutes les variables
    4. Retourner prompt final
    """
```

#### 2. Templates Génériques

**Fichier**: `canonical/prompts/global_prompts.yaml`

**Nouveau template de normalisation**:

```yaml
normalization:
  generic_biotech:  # Nom générique (plus "lai_default")
    system_instructions: |
      You are a specialized AI assistant for biotech/pharma news analysis.
      Extract structured information with high precision for the specified domain focus.
      
    user_template: |
      Analyze this biotech/pharma news item and extract structured information.

      CRITICAL: Only extract entities that are EXPLICITLY mentioned in the text.
      Do not invent, infer, or hallucinate entities not present.

      TEXT TO ANALYZE:
      {{item_text}}

      WATCH DOMAINS FOCUS:
      {{domains_focus_description}}

      EXAMPLES OF ENTITIES TO DETECT:
      - Companies: {{companies_examples}}
      - Molecules/Drugs: {{molecules_examples}}
      - Technologies: {{technologies_examples}}
      - Trademarks: {{trademarks_examples}}

      TECHNOLOGY FOCUS AREAS:
      {{technology_focus_description}}

      TASK:
      1. Generate a concise summary (2-3 sentences)
      2. Classify the event type among: {{event_types_list}}
      3. Extract ALL pharmaceutical/biotech company names mentioned
      4. Extract ALL drug/molecule names mentioned
      5. Extract ALL technology keywords mentioned
      6. Extract ALL trademark names mentioned
      7. Extract ALL therapeutic indications mentioned
      8. Evaluate domain relevance (0-10 score): {{relevance_question}}
      9. Detect exclusion signals: {{anti_signals_description}}
      10. Assess company context: {{company_context_rules}}

      RESPONSE FORMAT (JSON only):
      {
        "summary": "...",
        "event_type": "...",
        "companies_detected": ["...", "..."],
        "molecules_detected": ["...", "..."],
        "technologies_detected": ["...", "..."],
        "trademarks_detected": ["...", "..."],
        "indications_detected": ["...", "..."],
        "domain_relevance_score": 0,
        "exclusion_signals_detected": false,
        "company_context": false
      }

      Respond with ONLY the JSON, no additional text.
```

**Variables à substituer**:
- `{{item_text}}`: Texte de l'item
- `{{domains_focus_description}}`: Description générée depuis watch_domains
- `{{companies_examples}}`: Top 10 companies depuis company_scope
- `{{molecules_examples}}`: Top 10 molecules depuis molecule_scope
- `{{technologies_examples}}`: Top 10 technologies depuis technology_scope
- `{{trademarks_examples}}`: Top 5 trademarks depuis trademark_scope
- `{{technology_focus_description}}`: Description détaillée des technologies
- `{{event_types_list}}`: Liste des event_types
- `{{relevance_question}}`: Question adaptée à la verticale
- `{{anti_signals_description}}`: Signaux d'exclusion
- `{{company_context_rules}}`: Règles contexte pure player

#### 3. Détection Automatique de Verticale

**Logique de détection**:

```python
def detect_vertical_from_scopes(technology_scope: str) -> str:
    """
    Détecte la verticale depuis le nom du technology_scope.
    
    Examples:
        'lai_keywords' → 'LAI'
        'gene_therapy_keywords' → 'Gene Therapy'
        'cell_therapy_keywords' → 'Cell Therapy'
    """
    vertical_mapping = {
        'lai': 'Long-Acting Injectable',
        'gene_therapy': 'Gene Therapy',
        'cell_therapy': 'Cell Therapy',
        'antibody': 'Antibody Therapeutics',
        'rna': 'RNA Therapeutics'
    }
    
    for key, vertical in vertical_mapping.items():
        if key in technology_scope.lower():
            return vertical
    
    return 'Biotech/Pharma'  # Fallback générique
```

**Construction de la description technologique**:

```python
def build_technology_focus_description(
    technology_scope_data: Dict,
    vertical_name: str
) -> str:
    """
    Construit la description des technologies depuis le scope.
    
    Args:
        technology_scope_data: Données du scope (ex: lai_keywords)
        vertical_name: Nom de la verticale détectée
    
    Returns:
        Description formatée pour le prompt
    """
    description = f"\n{vertical_name.upper()} TECHNOLOGY FOCUS:\n"
    description += f"Detect these {vertical_name} technologies ONLY if explicitly mentioned:\n"
    
    # Core phrases (haute précision)
    core_phrases = technology_scope_data.get('core_phrases', [])
    if core_phrases:
        for phrase in core_phrases[:15]:  # Limite pour ne pas surcharger
            description += f"- {phrase}\n"
    
    # Technology terms (précision moyenne)
    tech_terms = technology_scope_data.get('technology_terms_high_precision', [])
    if tech_terms:
        description += "\nHigh-precision technology terms:\n"
        for term in tech_terms[:10]:
            description += f"- {term}\n"
    
    # Negative terms (exclusions)
    negative_terms = technology_scope_data.get('negative_terms', [])
    if negative_terms:
        description += "\nEXCLUDE if these terms are present:\n"
        for term in negative_terms[:10]:
            description += f"- {term}\n"
    
    return description
```


#### 4. Construction Dynamique des Exemples

**Extraction depuis canonical_scopes**:

```python
def extract_examples_from_scopes(
    watch_domains: List[Dict],
    canonical_scopes: Dict
) -> Dict[str, str]:
    """
    Extrait les exemples d'entités depuis les scopes référencés
    dans les watch_domains.
    
    Returns:
        {
            'companies_examples': 'MedinCell, Camurus, DelSiTech, ...',
            'molecules_examples': 'buprenorphine, naloxone, ...',
            'technologies_examples': 'long-acting injectable, ...',
            'trademarks_examples': 'UZEDY, PharmaShell, ...'
        }
    """
    examples = {
        'companies_examples': [],
        'molecules_examples': [],
        'technologies_examples': [],
        'trademarks_examples': []
    }
    
    for domain in watch_domains:
        # Companies
        company_scope = domain.get('company_scope')
        if company_scope:
            companies = canonical_scopes.get('companies', {}).get(company_scope, [])
            examples['companies_examples'].extend(companies[:10])
        
        # Molecules
        molecule_scope = domain.get('molecule_scope')
        if molecule_scope:
            molecules = canonical_scopes.get('molecules', {}).get(molecule_scope, [])
            examples['molecules_examples'].extend(molecules[:10])
        
        # Technologies
        technology_scope = domain.get('technology_scope')
        if technology_scope:
            tech_data = canonical_scopes.get('technologies', {}).get(technology_scope, {})
            if isinstance(tech_data, dict):
                core_phrases = tech_data.get('core_phrases', [])
                examples['technologies_examples'].extend(core_phrases[:10])
            elif isinstance(tech_data, list):
                examples['technologies_examples'].extend(tech_data[:10])
        
        # Trademarks
        trademark_scope = domain.get('trademark_scope')
        if trademark_scope:
            trademarks = canonical_scopes.get('trademarks', {}).get(trademark_scope, [])
            examples['trademarks_examples'].extend(trademarks[:5])
    
    # Dédoublonnage et formatage
    return {
        key: ', '.join(list(set(values))[:15])  # Max 15 exemples
        for key, values in examples.items()
    }
```

---

## 🔧 PLAN D'IMPLÉMENTATION

### Phase 1: Création du Prompt Builder

**Fichier à créer**: `src_v2/vectora_core/shared/prompt_builder.py`

**Fonctions à implémenter**:

1. `detect_vertical_characteristics()` - Analyse watch_domains
2. `extract_examples_from_scopes()` - Extraction exemples
3. `build_technology_focus_description()` - Description technologies
4. `build_normalization_prompt_dynamic()` - Construction prompt normalisation
5. `build_matching_prompt_dynamic()` - Construction prompt matching

**Estimation**: 200-300 lignes de code

### Phase 2: Modification de bedrock_client.py

**Fichier à modifier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Changements**:

```python
# AVANT (hardcodé)
def _build_normalization_prompt_v1(self, item_text, canonical_examples, ...):
    lai_section = "\n\nLAI TECHNOLOGY FOCUS:\n"
    lai_section += "Detect these LAI (Long-Acting Injectable) technologies:\n"
    # ... hardcoding ...

# APRÈS (dynamique)
def _build_normalization_prompt_dynamic(self, item_text, watch_domains, 
                                       canonical_scopes, canonical_prompts):
    from ..shared.prompt_builder import build_normalization_prompt_dynamic
    
    return build_normalization_prompt_dynamic(
        item_text, watch_domains, canonical_scopes, canonical_prompts
    )
```

**Modifications**:
- Remplacer `_build_normalization_prompt_v1()` par appel à `prompt_builder`
- Passer `watch_domains` en paramètre (déjà disponible dans normalizer.py)
- Supprimer tout le hardcoding LAI

### Phase 3: Mise à Jour du Template Canonical

**Fichier à modifier**: `canonical/prompts/global_prompts.yaml`

**Changements**:

```yaml
# AVANT
normalization:
  lai_default:  # Nom spécifique LAI
    user_template: |
      # Prompt avec hardcoding LAI

# APRÈS
normalization:
  generic_biotech:  # Nom générique
    user_template: |
      # Prompt avec variables {{...}}
      {{technology_focus_description}}
      {{companies_examples}}
      # etc.
```

### Phase 4: Modification de normalizer.py

**Fichier à modifier**: `src_v2/vectora_core/normalization/normalizer.py`

**Changements**:

```python
# AVANT
normalized_items = normalizer.normalize_items_batch(
    raw_items, canonical_scopes, canonical_prompts, 
    bedrock_model, bedrock_region, max_workers=max_workers,
    watch_domains=watch_domains,
    matching_config=matching_config
)

# APRÈS (aucun changement nécessaire - watch_domains déjà passés)
# Le prompt_builder sera appelé dans bedrock_client.py
```

**Aucune modification majeure** - `watch_domains` est déjà passé correctement.

### Phase 5: Tests et Validation

**Tests à effectuer**:

1. **Test LAI (existant)**: Vérifier que le comportement LAI est préservé
2. **Test Gene Therapy (nouveau)**: Créer un client_config Gene Therapy
3. **Test générique**: Vérifier que le système fonctionne sans verticale spécifique

**Fichiers de test**:
- `tests/unit/test_prompt_builder.py`
- `tests/integration/test_dynamic_prompts_lai.py`
- `tests/integration/test_dynamic_prompts_gene_therapy.py`

---

## 📋 EXEMPLE CONCRET: LAI vs Gene Therapy

### Configuration LAI (existant)

**client_config**:
```yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
```

**Prompt généré dynamiquement**:
```
LONG-ACTING INJECTABLE TECHNOLOGY FOCUS:
Detect these Long-Acting Injectable technologies ONLY if explicitly mentioned:
- long-acting injectable
- extended-release injection
- depot injection
- microspheres
- PLGA

EXAMPLES OF ENTITIES TO DETECT:
- Companies: MedinCell, Camurus, DelSiTech, Nanexa, Peptron
- Technologies: long-acting injectable, extended-release injection, depot injection

Evaluate domain relevance (0-10 score): How relevant is this content to Long-Acting Injectable technologies?

EXCLUDE if these terms are present:
- oral tablet
- topical cream
```

### Configuration Gene Therapy (nouveau)

**client_config**:
```yaml
watch_domains:
  - id: "tech_gene_therapy_ecosystem"
    technology_scope: "gene_therapy_keywords"
    company_scope: "gene_therapy_companies_global"
```

**canonical/scopes/technology_scopes.yaml** (à créer):
```yaml
gene_therapy_keywords:
  _metadata:
    profile: technology_complex
    description: "Gene Therapy - requires multiple signal types"
  core_phrases:
    - "gene therapy"
    - "AAV vector"
    - "lentiviral vector"
    - "CRISPR-Cas9"
    - "gene editing"
  technology_terms_high_precision:
    - "adeno-associated virus"
    - "viral vector"
    - "ex vivo gene therapy"
    - "in vivo gene therapy"
  negative_terms:
    - "small molecule"
    - "traditional drug"
```

**Prompt généré dynamiquement**:
```
GENE THERAPY TECHNOLOGY FOCUS:
Detect these Gene Therapy technologies ONLY if explicitly mentioned:
- gene therapy
- AAV vector
- lentiviral vector
- CRISPR-Cas9
- gene editing

EXAMPLES OF ENTITIES TO DETECT:
- Companies: Bluebird Bio, Spark Therapeutics, uniQure, Voyager Therapeutics
- Technologies: gene therapy, AAV vector, lentiviral vector, CRISPR-Cas9

Evaluate domain relevance (0-10 score): How relevant is this content to Gene Therapy technologies?

EXCLUDE if these terms are present:
- small molecule
- traditional drug
```

**Aucune modification de code** - Tout piloté par configuration!

---

## 🎨 AVANTAGES DE LA CONCEPTION

### 1. Simplicité

**Pour l'humain**:
- Ajuster `client_config.yaml` pour changer le comportement
- Enrichir `canonical/scopes/*.yaml` pour affiner le matching
- Modifier `canonical/prompts/global_prompts.yaml` pour améliorer les prompts

**Aucune modification de code Python nécessaire**

### 2. Généricité

**Support multi-verticales**:
- LAI (existant)
- Gene Therapy (nouveau)
- Cell Therapy (nouveau)
- Antibody Therapeutics (nouveau)
- RNA Therapeutics (nouveau)

**Même code, configurations différentes**

### 3. Puissance

**Pilotage fin**:
- Ajuster les exemples d'entités
- Modifier les descriptions technologiques
- Changer les signaux d'exclusion
- Adapter les questions de relevance

**Tout depuis les fichiers canonical**

### 4. Maintenabilité

**Règles métier centralisées**:
- `canonical/scopes/` pour les entités
- `canonical/prompts/` pour les templates
- `client_config` pour l'orchestration

**Pas de dispersion dans le code**

### 5. Testabilité

**Tests faciles**:
- Créer un nouveau `client_config`
- Ajouter des `canonical/scopes`
- Lancer le moteur
- Vérifier les résultats

**Pas besoin de modifier le code pour tester**

---

## ⚠️ POINTS DE VIGILANCE

### 1. Taille des Prompts

**Risque**: Prompts trop longs si trop d'exemples

**Solution**:
- Limiter à 10-15 exemples par catégorie
- Prioriser les exemples les plus représentatifs
- Monitorer la taille des prompts générés

### 2. Performance

**Risque**: Construction dynamique à chaque appel

**Solution**:
- Cacher les caractéristiques détectées par client_id
- Construire une seule fois au début du batch
- Réutiliser pour tous les items du même client

### 3. Compatibilité Ascendante

**Risque**: Casser le comportement LAI existant

**Solution**:
- Garder `_build_normalization_prompt_v1()` en fallback
- Tester exhaustivement avec `lai_weekly_v5`
- Comparer les résultats avant/après

### 4. Complexité des Scopes

**Risque**: Structure `lai_keywords` complexe (core_phrases, technology_terms, etc.)

**Solution**:
- Documenter la structure attendue
- Fournir des exemples pour chaque verticale
- Valider la structure au chargement

---

## 📊 ÉVALUATION DE L'EXISTANT

### Ce qui est Bien Conçu ✅

1. **Structure canonical/scopes/**:
   - Séparation claire par type d'entité
   - Structure riche (core_phrases, negative_terms)
   - Métadonnées utiles (_metadata)

2. **watch_domains dans client_config**:
   - Références aux scopes canonical
   - Flexibilité multi-domaines
   - Configuration claire

3. **Prompt de matching**:
   - Déjà assez générique
   - Construction dynamique depuis watch_domains
   - Bonne séparation des responsabilités

### Ce qui Doit Être Amélioré ❌

1. **Prompt de normalisation**:
   - Hardcoding massif dans bedrock_client.py
   - Logique métier mélangée avec instructions
   - Impossible à adapter sans modifier le code

2. **Utilisation des scopes**:
   - Structure riche mais sous-exploitée
   - Pas utilisée pour construire les prompts
   - Duplication entre scopes et code

3. **Généricité**:
   - Tout est LAI-spécifique
   - Impossible d'ajouter une verticale sans coder
   - Viole le principe "Configuration > Code"

### Verdict Global

**Architecture existante: 7/10**
- Bonne base avec canonical et client_config
- Mais hardcoding dans le code Python
- Potentiel énorme avec le système dynamique proposé

**Avec le système dynamique: 9/10**
- Générique et puissant
- Pilotable par configuration
- Maintenable et évolutif

---

## 🚀 MIGRATION PROGRESSIVE

### Étape 1: Création du Prompt Builder (Semaine 1)

**Objectif**: Module fonctionnel sans casser l'existant

**Livrables**:
- `src_v2/vectora_core/shared/prompt_builder.py`
- Tests unitaires
- Documentation

### Étape 2: Intégration dans bedrock_client.py (Semaine 2)

**Objectif**: Utiliser le prompt builder en parallèle de v1

**Livrables**:
- Méthode `_build_normalization_prompt_dynamic()`
- Fallback sur v1 si erreur
- Tests d'intégration

### Étape 3: Migration du Template Canonical (Semaine 2)

**Objectif**: Template générique dans global_prompts.yaml

**Livrables**:
- Nouveau template `generic_biotech`
- Variables documentées
- Exemples de substitution

### Étape 4: Tests LAI Exhaustifs (Semaine 3)

**Objectif**: Vérifier que LAI fonctionne identiquement

**Livrables**:
- Tests E2E avec lai_weekly_v5
- Comparaison résultats v1 vs dynamique
- Validation métriques (matching rate, scores)

### Étape 5: Activation par Défaut (Semaine 4)

**Objectif**: Système dynamique devient le défaut

**Livrables**:
- Suppression de v1 (ou mise en legacy)
- Documentation utilisateur
- Guide de création de nouvelles verticales

---

## 📚 DOCUMENTATION UTILISATEUR

### Guide: Créer une Nouvelle Verticale

**Exemple: Ajouter "Cell Therapy"**

#### 1. Créer les Scopes Canonical

**Fichier**: `canonical/scopes/technology_scopes.yaml`

```yaml
cell_therapy_keywords:
  _metadata:
    profile: technology_complex
    description: "Cell Therapy - CAR-T, TCR-T, TIL"
  core_phrases:
    - "CAR-T cell therapy"
    - "chimeric antigen receptor"
    - "T cell therapy"
    - "tumor-infiltrating lymphocytes"
  technology_terms_high_precision:
    - "autologous CAR-T"
    - "allogeneic CAR-T"
    - "TCR-T therapy"
    - "TIL therapy"
  negative_terms:
    - "small molecule"
    - "antibody drug conjugate"
```

**Fichier**: `canonical/scopes/company_scopes.yaml`

```yaml
cell_therapy_companies_global:
  - Kite Pharma
  - Juno Therapeutics
  - Novartis
  - Gilead Sciences
  - Bristol Myers Squibb
  - Allogene Therapeutics
  - CRISPR Therapeutics
```

#### 2. Créer le Client Config

**Fichier**: `client-config-examples/cell_therapy_weekly_v1.yaml`

```yaml
client_id: "cell_therapy_weekly_v1"

watch_domains:
  - id: "tech_cell_therapy_ecosystem"
    type: "technology"
    technology_scope: "cell_therapy_keywords"
    company_scope: "cell_therapy_companies_global"
    
matching_config:
  min_domain_score: 0.30
  
scoring_config:
  event_type_weight_overrides:
    clinical_update: 9
    regulatory: 8
```

#### 3. Lancer le Moteur

```bash
# Aucune modification de code nécessaire!
python scripts/invoke/invoke_normalize_score_v2.py \
  --client-id cell_therapy_weekly_v1
```

**Le système détectera automatiquement**:
- Verticale: "Cell Therapy"
- Technologies: CAR-T, TCR-T, TIL
- Companies: Kite, Juno, Novartis, etc.
- Prompt adapté dynamiquement

---

## 🎯 CONCLUSION

### Résumé de la Conception

**Système de Prompts Dynamiques Piloté par Configuration**:

1. **Prompt Builder**: Module central qui analyse watch_domains et construit les prompts
2. **Templates Génériques**: Prompts avec variables dans global_prompts.yaml
3. **Détection Automatique**: Verticale déduite depuis technology_scope
4. **Construction Dynamique**: Exemples et descriptions depuis canonical_scopes
5. **Aucune Modification de Code**: Tout piloté par configuration

### Forces de la Solution

✅ **Simplicité**: Ajustements par configuration uniquement  
✅ **Généricité**: Support multi-verticales sans code spécifique  
✅ **Puissance**: Pilotage fin du moteur par un humain  
✅ **Maintenabilité**: Règles métier centralisées  
✅ **Évolutivité**: Ajout de verticales en quelques minutes  

### Points de Vigilance

⚠️ **Taille des prompts**: Limiter les exemples  
⚠️ **Performance**: Cacher les caractéristiques détectées  
⚠️ **Compatibilité**: Tester exhaustivement LAI  
⚠️ **Complexité scopes**: Documenter la structure attendue  

### Prochaines Étapes

1. **Validation de la conception** avec le product owner
2. **Création du prompt_builder.py** (Phase 1)
3. **Intégration dans bedrock_client.py** (Phase 2)
4. **Tests LAI exhaustifs** (Phase 4)
5. **Activation par défaut** (Phase 5)

### Impact Attendu

**Avant**:
- Hardcoding LAI dans le code
- Impossible d'ajouter une verticale sans coder
- Maintenance complexe et fragile

**Après**:
- Configuration pilote tout
- Ajout de verticales en minutes
- Maintenance simple et robuste

**Objectif atteint**: Moteur générique, puissant, et pilotable par un humain via configuration.

---

*Document de conception réalisé le 2025-12-23*  
*Basé sur l'analyse complète du code et des diagnostics existants*  
*Objectif: Système de prompts dynamiques pour Vectora Inbox*
