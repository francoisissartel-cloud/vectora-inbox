# Plan de Canonicalisation des Prompts Bedrock - Vectora Inbox

**Date** : 2025-12-12  
**Objectif** : Externaliser les prompts Bedrock hardcodés vers des fichiers canonical versionnés  
**Statut** : Phase de design et diagnostic  

---

## Phase 0 – Rappel du Contexte et Types de Prompts

### Contexte Actuel
Vectora Inbox utilise Amazon Bedrock (Claude Sonnet 4.5) pour deux tâches principales :
1. **Normalisation** (Lambda ingest-normalize) : extraction d'entités, classification, résumé
2. **Newsletter** (Lambda engine) : génération éditoriale, réécriture, assemblage

### Types de Prompts Identifiés
- **Prompts de normalisation** : extraction d'entités LAI, classification d'événements, scoring de relevance
- **Prompts de newsletter** : génération de titres, introductions, TL;DR, reformulations d'items
- **Prompts contextuels** : évaluation de domaines, matching avec watch_domains

### Problématique Actuelle
- Prompts hardcodés dans le code Python (strings multi-lignes)
- Difficile à ajuster sans redéploiement des Lambdas
- Pas de versioning des prompts
- Duplication de logique entre normalisation et newsletter
- Maintenance complexe pour les ajustements métier

---

## Phase 1 – Inventaire des Prompts dans le Code

### 1.1 Prompts de Normalisation (ingest-normalize)

**Fichier** : `src/vectora_core/normalization/bedrock_client.py`  
**Fonction** : `_build_normalization_prompt()`  
**Lambda** : vectora-inbox-ingest-normalize  

**Type de tâche** : Extraction d'entités + classification + résumé  
**Variables injectées** :
- `item_text` : titre + description de l'item
- `canonical_examples` : exemples d'entités (companies, molecules, technologies)
- `domain_contexts` : contextes de domaines pour évaluation
- `lai_section` : section spécialisée LAI hardcodée

**Prompt actuel** (extrait représentatif) :
```
Analyze the following biotech/pharma news item and extract structured information.

TEXT TO ANALYZE:
{item_text}

EXAMPLES OF ENTITIES TO DETECT:
- Companies: {companies_examples}
- Molecules/Drugs: {molecules_examples}  
- Technologies: {technologies_examples}

LAI TECHNOLOGY FOCUS:
Detect these LAI (Long-Acting Injectable) technologies:
- Extended-Release Injectable
- Long-Acting Injectable
[...liste hardcodée...]

TASK:
1. Generate a concise summary (2-3 sentences)
2. Classify the event type among: clinical_update, partnership, regulatory...
[...10 tâches hardcodées...]

RESPONSE FORMAT (JSON only):
{json_example}
```

### 1.2 Prompts de Newsletter (engine)

**Fichier** : `src/vectora_core/newsletter/bedrock_client.py`  
**Fonction** : `_build_ultra_compact_prompt()`  
**Lambda** : vectora-inbox-engine  

**Type de tâche** : Génération éditoriale (titre, intro, TL;DR, reformulations)  
**Variables injectées** :
- `sections_data` : sections avec items sélectionnés
- `client_profile` : nom, langue, tone du client
- `target_date` : date de référence

**Prompt actuel** (version ultra-compacte P1) :
```
JSON newsletter for {client_name} - {target_date}:

{items_text}

Output:
{"title":"{client_name} – {target_date}","intro":"1 sentence","tldr":["point1","point2"],"sections":[...]}

Rules: JSON only, concise, preserve names.
```

### 1.3 Analyse des Duplications et Complexité

**Prompts les plus complexes** :
1. **Normalisation LAI** : 200+ lignes, logique métier LAI hardcodée
2. **Évaluation domaines** : construction dynamique de contextes
3. **Newsletter éditoriale** : format JSON strict, optimisations P1

**Duplications identifiées** :
- Instructions JSON communes entre normalisation et newsletter
- Exemples d'entités répétés (companies, molecules, technologies)
- Logique LAI dupliquée entre prompt et scopes canonical

**Prompts critiques métier** :
- **LAI technology focus** : cœur métier, ajustements fréquents
- **Event type classification** : impact direct sur scoring
- **Editorial tone** : personnalisation client

---

## Phase 2 – Design de l'Architecture "Prompts Canonical"

### 2.1 Structure Cible des Prompts

```
canonical/
├── prompts/
│   ├── normalization/
│   │   ├── lai_entity_extraction_v1.yaml
│   │   ├── event_classification_v1.yaml
│   │   ├── domain_evaluation_v1.yaml
│   │   └── README.md
│   ├── newsletter/
│   │   ├── editorial_generation_v1.yaml
│   │   ├── section_intro_v1.yaml
│   │   ├── item_rewriting_v1.yaml
│   │   └── README.md
│   └── shared/
│       ├── json_instructions_v1.yaml
│       ├── entity_examples_v1.yaml
│       └── README.md
```

### 2.2 Format des Prompts Canonical

**Format recommandé** : YAML avec sections structurées

```yaml
# canonical/prompts/normalization/lai_entity_extraction_v1.yaml
prompt_id: "normalization.lai_entity_extraction"
version: "1.0"
description: "Extraction d'entités LAI avec classification et résumé"
model_compatibility: ["claude-3-sonnet", "claude-3-5-sonnet"]

system_instructions: |
  You are a specialized biotech/pharma analyst focused on Long-Acting Injectable (LAI) technologies.
  Extract structured information from news items with high precision.

user_prompt_template: |
  Analyze the following biotech/pharma news item and extract structured information.
  
  TEXT TO ANALYZE:
  {{item_text}}
  
  EXAMPLES OF ENTITIES TO DETECT:
  {{#canonical_examples}}
  - Companies: {{companies}}
  - Molecules/Drugs: {{molecules}}
  - Technologies: {{technologies}}
  {{/canonical_examples}}
  
  {{#lai_focus}}
  LAI TECHNOLOGY FOCUS:
  {{lai_instructions}}
  {{/lai_focus}}
  
  {{#domain_contexts}}
  DOMAINS TO EVALUATE:
  {{domain_list}}
  {{/domain_contexts}}
  
  TASK:
  {{#tasks}}
  {{.}}
  {{/tasks}}
  
  RESPONSE FORMAT (JSON only):
  {{response_format}}

parameters:
  lai_focus:
    lai_instructions: |
      Detect these LAI (Long-Acting Injectable) technologies:
      - Extended-Release Injectable
      - Long-Acting Injectable
      - Depot Injection
      - Once-Monthly Injection
      - Microspheres
      - PLGA
      - In-Situ Depot
      - Hydrogel
      - Subcutaneous Injection
      - Intramuscular Injection
      
      TRADEMARKS to detect:
      - UZEDY, PharmaShell, SiliaShell, BEPO, Aristada, Abilify Maintena
      
      Normalize: 'extended-release injectable' → 'Extended-Release Injectable'

  tasks:
    - "1. Generate a concise summary (2-3 sentences) explaining the key information"
    - "2. Classify the event type among: clinical_update, partnership, regulatory, scientific_paper, corporate_move, financial_results, safety_signal, manufacturing_supply, other"
    - "3. Extract ALL pharmaceutical/biotech company names mentioned"
    - "4. Extract ALL drug/molecule names mentioned (including brand names, generic names)"
    - "5. Extract ALL technology keywords mentioned - FOCUS on LAI technologies listed above"
    - "6. Extract ALL trademark names mentioned (especially those with ® or ™ symbols)"
    - "7. Extract ALL therapeutic indications mentioned"
    - "8. Evaluate LAI relevance (0-10 score): How relevant is this content to Long-Acting Injectable technologies?"
    - "9. Detect anti-LAI signals: Does the content mention oral routes (tablets, capsules, pills)?"
    - "10. Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?"

  response_format:
    summary: "..."
    event_type: "..."
    companies_detected: ["...", "..."]
    molecules_detected: ["...", "..."]
    technologies_detected: ["...", "..."]
    trademarks_detected: ["...", "..."]
    indications_detected: ["...", "..."]
    lai_relevance_score: 0
    anti_lai_detected: false
    pure_player_context: false
    domain_relevance: []

bedrock_config:
  max_tokens: 1000
  temperature: 0.0
  anthropic_version: "bedrock-2023-05-31"
```

### 2.3 Chargement et Cache des Prompts

**Fonction de chargement centralisée** :
```python
# src/vectora_core/prompts/loader.py
class PromptLoader:
    def __init__(self, config_bucket: str):
        self.config_bucket = config_bucket
        self._cache = {}
    
    def load_prompt(self, prompt_id: str, version: str = "latest") -> Dict[str, Any]:
        """Charge un prompt depuis S3 avec cache local"""
        
    def render_prompt(self, prompt_id: str, variables: Dict[str, Any]) -> str:
        """Rend un prompt avec les variables injectées"""
```

### 2.4 Gestion des Variantes par Client

**Approche recommandée** : Surcharge par client_id

```
canonical/prompts/clients/
├── lai_weekly_v3/
│   ├── normalization_overrides.yaml
│   └── newsletter_overrides.yaml
└── default/
    └── README.md
```

**Exemple de surcharge client** :
```yaml
# canonical/prompts/clients/lai_weekly_v3/normalization_overrides.yaml
base_prompt: "normalization.lai_entity_extraction"
overrides:
  parameters:
    lai_focus:
      additional_trademarks:
        - "UZEDY®"
        - "PharmaShell®"
      focus_areas:
        - "malaria prevention"
        - "psychiatric medications"
```

---

## Phase 3 – Stratégie de Migration (sans exécuter encore)

### 3.1 Ordre de Migration Recommandé

**Phase A : Normalisation LAI (P0)**
- Prompt le plus critique et complexe
- Impact direct sur la qualité des signaux
- Fichier cible : `canonical/prompts/normalization/lai_entity_extraction_v1.yaml`
- Fonctions à modifier : `_build_normalization_prompt()` dans `bedrock_client.py`

**Phase B : Newsletter éditoriale (P1)**
- Prompt moins critique mais plus visible
- Fichier cible : `canonical/prompts/newsletter/editorial_generation_v1.yaml`
- Fonctions à modifier : `_build_ultra_compact_prompt()` dans `newsletter/bedrock_client.py`

**Phase C : Prompts de domaines (P2)**
- Évaluation des watch_domains
- Fichier cible : `canonical/prompts/normalization/domain_evaluation_v1.yaml`
- Logique dans `domain_context_builder.py`

### 3.2 Stratégie de Migration Sans Casse

**Feature flags environnementaux** :
```python
USE_CANONICAL_PROMPTS = os.environ.get('USE_CANONICAL_PROMPTS', 'false').lower() == 'true'

if USE_CANONICAL_PROMPTS:
    prompt = prompt_loader.render_prompt('normalization.lai_entity_extraction', variables)
else:
    prompt = _build_normalization_prompt(item_text, canonical_examples, domain_contexts)  # Fallback
```

**Validation A/B** :
- Déployer avec feature flag désactivé
- Activer progressivement par client_id
- Comparer les résultats (items normalisés, scores, newsletter)
- Rollback immédiat si régression détectée

### 3.3 Préservation de la Généricité des Lambdas

**Principe** : Les Lambdas restent génériques, guidées par :
1. **client_config** : configuration spécifique au client
2. **canonical prompts** : prompts versionnés et paramétrables
3. **Variables d'environnement** : feature flags et configuration runtime

**Exemple d'intégration** :
```python
# Dans normalize_item()
prompt_config = client_config.get('prompts', {})
normalization_prompt_id = prompt_config.get('normalization', 'normalization.lai_entity_extraction')

prompt = prompt_loader.render_prompt(
    normalization_prompt_id,
    {
        'item_text': full_text,
        'canonical_examples': canonical_examples,
        'domain_contexts': domain_contexts
    }
)
```

---

## Phase 4 – Stratégie de Tests Locaux

### 4.1 Scripts de Test Recommandés

**Test de régression prompts** :
```python
# test_canonical_prompts_regression.py
def test_normalization_prompt_regression():
    """Compare les résultats ancien vs nouveau prompt sur dataset de référence"""
    
def test_newsletter_prompt_regression():
    """Compare les newsletters générées ancien vs nouveau prompt"""
    
def test_prompt_rendering():
    """Valide le rendu des prompts avec différentes variables"""
```

**Datasets de test** :
- Items normalisés de référence (Nanexa/Moderna, UZEDY, MedinCell)
- Newsletters générées historiques (lai_weekly_v3)
- Cas edge : items sans entités, textes très courts, caractères spéciaux

### 4.2 Métriques de Validation

**Normalisation** :
- Nombre d'entités détectées (companies, molecules, technologies)
- Scores LAI (lai_relevance_score)
- Classification event_type
- Cohérence des résumés

**Newsletter** :
- Longueur des textes générés
- Respect du format JSON
- Cohérence éditoriale (tone, style)
- Temps de génération

### 4.3 Critères de Succès Tests Locaux

- ✅ **Régression < 5%** sur métriques clés
- ✅ **Performance maintenue** (temps d'exécution)
- ✅ **Format JSON stable** (pas d'erreurs de parsing)
- ✅ **Prompts rendus correctement** (pas de variables manquantes)

---

## Phase 5 – Stratégie de Déploiement AWS

### 5.1 Ordre des Opérations

**Étape 1 : Sync canonical prompts**
```bash
aws s3 sync canonical/prompts/ s3://vectora-inbox-config-dev/canonical/prompts/ --delete
```

**Étape 2 : Package Lambdas avec nouveau code**
```bash
# Ajouter prompt_loader dans vectora_core
# Modifier bedrock_client.py avec feature flags
./scripts/package-ingest-normalize.ps1
./scripts/package-engine.ps1
```

**Étape 3 : Deploy avec feature flags OFF**
```bash
aws lambda update-function-code --function-name vectora-inbox-ingest-normalize-dev --zip-file fileb://ingest-normalize.zip
aws lambda update-function-environment-variables --function-name vectora-inbox-ingest-normalize-dev --environment Variables='{USE_CANONICAL_PROMPTS=false}'
```

**Étape 4 : Tests de non-régression**
```bash
# Test avec anciens prompts (feature flag OFF)
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev --payload file://test-event.json out-test.json
```

**Étape 5 : Activation progressive**
```bash
# Activer pour un client test
aws lambda update-function-environment-variables --function-name vectora-inbox-ingest-normalize-dev --environment Variables='{USE_CANONICAL_PROMPTS=true,CANONICAL_PROMPTS_CLIENT_WHITELIST=lai_weekly_v3}'
```

### 5.2 Validation Post-Déploiement

**Logs à surveiller** :
- `Prompt loaded from canonical: {prompt_id}` (succès chargement)
- `Fallback to hardcoded prompt: {reason}` (échec chargement)
- `Bedrock response parsed successfully` (pas de régression parsing)

**Items de test de référence** :
- Nanexa/Moderna (PharmaShell detection)
- UZEDY regulatory (trademark detection)
- MedinCell malaria (LAI context detection)

**Métriques de validation** :
- Temps d'exécution Lambda (pas d'augmentation >20%)
- Taux d'erreur Bedrock (maintenu <5%)
- Qualité des items normalisés (score LAI, entités détectées)

### 5.3 Plan de Rollback

**Rollback immédiat** :
```bash
# Désactiver feature flag
aws lambda update-function-environment-variables --function-name vectora-inbox-ingest-normalize-dev --environment Variables='{USE_CANONICAL_PROMPTS=false}'
```

**Rollback complet** :
```bash
# Redéployer version précédente
aws lambda update-function-code --function-name vectora-inbox-ingest-normalize-dev --zip-file fileb://ingest-normalize-backup.zip
```

**Critères de rollback** :
- Erreur de chargement prompts >10%
- Régression qualité >15% sur items de référence
- Augmentation temps d'exécution >50%
- Erreurs de parsing JSON >5%

---

## 🎯 Résumé Exécutif

### 3-4 Idées Clés du Design Cible

1. **Prompts externalisés en YAML** : Structure claire avec system_instructions, user_prompt_template, parameters
2. **Chargement centralisé avec cache** : PromptLoader avec cache S3 et fallback vers prompts hardcodés
3. **Migration progressive avec feature flags** : Déploiement sans risque avec validation A/B
4. **Variantes par client** : Surcharge des prompts via client_config et canonical/prompts/clients/

### Prompts les Plus Critiques à Externaliser en Premier

1. **Normalisation LAI** (`_build_normalization_prompt`) : 200+ lignes, logique métier critique
2. **Newsletter éditoriale** (`_build_ultra_compact_prompt`) : Format JSON strict, optimisations P1
3. **Évaluation domaines** : Construction dynamique de contextes pour watch_domains

### Risques Principaux à Surveiller

1. **Régression qualité** : Changement subtil de prompt → impact sur détection d'entités
2. **Performance** : Chargement S3 des prompts → latence supplémentaire
3. **Parsing JSON** : Modification format prompt → erreurs de parsing Bedrock
4. **Fallback** : Échec chargement canonical → nécessité de fallback robuste

---

## 📋 Prochaines Étapes Recommandées

### P0 - Actions Immédiates
1. **Validation du design** : Revue de l'architecture prompts canonical proposée
2. **Création prompt LAI** : Externaliser `_build_normalization_prompt` en YAML
3. **Implémentation PromptLoader** : Fonction de chargement avec cache et fallback

### P1 - Implémentation
1. **Migration normalisation** : Feature flag + tests de régression
2. **Migration newsletter** : Externalisation `_build_ultra_compact_prompt`
3. **Tests end-to-end** : Validation sur items de référence (Nanexa, UZEDY, MedinCell)

### P2 - Optimisation
1. **Variantes clients** : Surcharge prompts par client_id
2. **Versioning avancé** : Gestion des versions de prompts
3. **Monitoring** : Métriques de qualité et performance des prompts canonical

---

**Ce plan permet d'externaliser les prompts Bedrock sans risque de régression, avec une migration progressive et des mécanismes de fallback robustes.**