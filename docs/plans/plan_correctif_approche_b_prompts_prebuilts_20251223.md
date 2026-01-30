# Plan Correctif: Implémentation Approche B - Prompts Pré-construits

**Date**: 2025-12-23  
**Objectif**: Implémenter l'Approche B (Prompts Pré-construits) sur Vectora Inbox  
**POC**: lai_weekly_v5  
**Principe**: Configuration > Code

---

## 🎯 OBJECTIF ET VISION

### Problème Actuel

**Hardcoding LAI dans bedrock_client.py** (lignes 200-250):
```python
lai_section = "\n\nLAI TECHNOLOGY FOCUS:\n"
lai_section += "Detect these LAI (Long-Acting Injectable) technologies:\n"
lai_section += "- Extended-Release Injectable\n"
lai_section += "- Three-Month Injectable\n"      # Hardcodé
lai_section += "- Extended Protection\n"         # Hardcodé pour malaria
```

**Conséquences**:
- Impossible d'adapter à Gene Therapy sans modifier le code
- Bidouillages successifs
- Viole "Configuration > Code"

### Solution Approche B

**Prompts pré-construits dans canonical/prompts/** avec références aux scopes:
- `lai_normalization_prompt.yaml` - Prompt normalisation LAI complet
- `lai_matching_prompt.yaml` - Prompt matching LAI complet
- Références dynamiques: `{{ref:lai_companies_global}}`
- Module `prompt_resolver.py` (50 lignes) pour résolution

### Bénéfices

✅ **Simplicité**: Code minimal (50 lignes vs 300)  
✅ **Visibilité**: Prompt complet visible dans fichier  
✅ **Performance**: Overhead <1% du temps total  
✅ **Contrôle**: Humain ajuste prompts sans toucher au code  
✅ **Debugging**: Copier-coller dans Bedrock Playground  

---

## 📊 PHASE 0: DIAGNOSTIC EXISTANT

### 0.1 Analyse Architecture Actuelle

**Lambdas appelant Bedrock**:

1. **normalize-score-v2**:
   - Appel 1: Normalisation (extraction entités)
   - Appel 2: Matching (évaluation domaines)

2. **newsletter-v2**:
   - Appel 3: Génération éditoriale (TL;DR, intro)

**Flux Normalisation**:
```
normalize_score/__init__.py::run_normalize_score_for_client()
  ↓
normalizer.normalize_items_batch()
  ↓
BedrockNormalizationClient.normalize_item()
  ↓
_build_normalization_prompt_v2() OU _build_normalization_prompt_v1()
  ↓ HARDCODING LAI ICI
call_bedrock_with_retry()
```

**Flux Matching**:
```
normalizer.normalize_items_batch()
  ↓
bedrock_matcher.match_item_to_domains_bedrock()
  ↓
_call_bedrock_matching()
  ↓
call_bedrock_with_retry()
```

### 0.2 Fichiers Canonical Existants

**Structure actuelle**:
```
canonical/
├── scopes/
│   ├── company_scopes.yaml          # lai_companies_global (✅ bien conçu)
│   ├── technology_scopes.yaml       # lai_keywords (✅ structure riche)
│   ├── molecule_scopes.yaml         # lai_molecules_global
│   ├── trademark_scopes.yaml        # lai_trademarks_global
│   └── indication_scopes.yaml
├── prompts/
│   └── global_prompts.yaml          # ❌ Hardcodé LAI actuellement
└── events/
    └── event_type_patterns.yaml     # ✅ Patterns event_type
```

**Qualité**: Scopes excellents, prompts à refactorer

### 0.3 Client Config Existant

**lai_weekly_v5.yaml** (extrait):
```yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    trademark_scope: "lai_trademarks_global"
```

**Qualité**: ✅ Excellent, prêt pour Approche B

### 0.4 Points de Vigilance Identifiés

⚠️ **Question 1**: Faut-il un prompt par client ou par verticale?
- **Recommandation**: Par verticale (lai, gene_therapy, etc.)
- **Raison**: Plusieurs clients peuvent partager la même verticale

⚠️ **Question 2**: Comment organiser canonical/prompts/?
- **Recommandation**: Structure par type + verticale
- **Exemple**: `canonical/prompts/normalization/lai_prompt.yaml`

⚠️ **Question 3**: Compatibilité avec prompts existants?
- **Recommandation**: Garder fallback sur global_prompts.yaml
- **Migration progressive**: Nouveau système en priorité, ancien en fallback

---

## 📋 PHASE 1: CRÉATION FICHIERS CANONICAL PROMPTS

### 1.1 Structure Proposée

```
canonical/prompts/
├── normalization/
│   ├── lai_prompt.yaml              # NOUVEAU
│   └── gene_therapy_prompt.yaml     # Futur
├── matching/
│   ├── lai_prompt.yaml              # NOUVEAU
│   └── gene_therapy_prompt.yaml     # Futur
└── global_prompts.yaml              # EXISTANT (fallback)
```

### 1.2 Création lai_normalization_prompt.yaml

**Fichier**: `canonical/prompts/normalization/lai_prompt.yaml`

**Contenu** (structure complète avec références):

```yaml
# Prompt de normalisation LAI pré-construit
# Utilise des références aux scopes canonical: {{ref:scope_name}}

metadata:
  vertical: "LAI"
  version: "1.0"
  created_date: "2025-12-23"
  description: "Prompt normalisation pour Long-Acting Injectables"

system_instructions: |
  You are a specialized AI assistant for biotech/pharma news analysis.
  Focus on Long-Acting Injectable (LAI) technologies and related entities.
  Extract structured information with high precision.

user_template: |
  Analyze this biotech/pharma news item and extract structured information.

  CRITICAL: Only extract entities that are EXPLICITLY mentioned in the text.
  FORBIDDEN: Do not invent, infer, or hallucinate entities not present.

  TEXT TO ANALYZE:
  {{item_text}}

  LAI TECHNOLOGY FOCUS:
  Detect these Long-Acting Injectable technologies ONLY if explicitly mentioned:
  {{ref:lai_keywords.core_phrases}}

  High-precision technology terms:
  {{ref:lai_keywords.technology_terms_high_precision}}

  EXAMPLES OF ENTITIES TO DETECT:
  - Companies: {{ref:lai_companies_global}}
  - Molecules: {{ref:lai_molecules_global}}
  - Trademarks: {{ref:lai_trademarks_global}}

  EXCLUDE if these terms are present:
  {{ref:lai_keywords.negative_terms}}

  TASK:
  1. Generate a concise summary (2-3 sentences)
  2. Classify event type: clinical_update, partnership, regulatory, corporate_move, financial_results, other
  3. Extract ALL pharmaceutical/biotech company names mentioned
  4. Extract ALL drug/molecule names mentioned
  5. Extract ALL technology keywords mentioned
  6. Extract ALL trademark names mentioned
  7. Extract ALL therapeutic indications mentioned
  8. Evaluate LAI relevance (0-10 score)
  9. Detect anti-LAI signals
  10. Assess pure player context

  RESPONSE FORMAT (JSON only):
  {
    "summary": "...",
    "event_type": "...",
    "companies_detected": ["..."],
    "molecules_detected": ["..."],
    "technologies_detected": ["..."],
    "trademarks_detected": ["..."],
    "indications_detected": ["..."],
    "lai_relevance_score": 0,
    "anti_lai_detected": false,
    "pure_player_context": false
  }

  Respond with ONLY the JSON, no additional text.

bedrock_config:
  max_tokens: 1000
  temperature: 0.0
  anthropic_version: "bedrock-2023-05-31"
```

**Taille estimée**: ~1.5 KB (compact)

### 1.3 Création lai_matching_prompt.yaml

**Fichier**: `canonical/prompts/matching/lai_prompt.yaml`

**Contenu**:

```yaml
# Prompt de matching LAI pré-construit

metadata:
  vertical: "LAI"
  version: "1.0"
  created_date: "2025-12-23"
  description: "Prompt matching pour Long-Acting Injectables"

system_instructions: |
  You are a domain relevance expert for biotech/pharma intelligence.
  Evaluate how relevant a normalized news item is to LAI watch domains.
  Be precise and conservative in your evaluations.

user_template: |
  Evaluate the relevance of this normalized item to the LAI watch domains:

  ITEM TO EVALUATE:
  Title: {{item_title}}
  Summary: {{item_summary}}
  Entities: {{item_entities}}
  Event Type: {{item_event_type}}

  WATCH DOMAINS TO EVALUATE:
  {{domains_context}}

  For each domain, evaluate:
  1. Is this item relevant to LAI technologies?
  2. Relevance score (0.0 to 1.0)?
  3. Confidence level (high/medium/low)?
  4. Which entities contributed to the match?
  5. Brief reasoning

  EVALUATION CRITERIA:
  - LAI technology signals required
  - Company relevance to LAI ecosystem
  - Be conservative: prefer false negatives over false positives

  RESPONSE FORMAT (JSON only):
  {
    "domain_evaluations": [
      {
        "domain_id": "...",
        "is_relevant": true/false,
        "relevance_score": 0.0-1.0,
        "confidence": "high/medium/low",
        "reasoning": "...",
        "matched_entities": {...}
      }
    ]
  }

  Respond with ONLY the JSON, no additional text.

bedrock_config:
  max_tokens: 1500
  temperature: 0.1
  anthropic_version: "bedrock-2023-05-31"
```

### 1.4 Modification client_config

**Fichier**: `client-config-examples/lai_weekly_v5.yaml`

**Ajout section bedrock_config**:

```yaml
# NOUVEAU: Configuration des prompts Bedrock
bedrock_config:
  normalization_prompt: "lai"      # Référence à canonical/prompts/normalization/lai_prompt.yaml
  matching_prompt: "lai"           # Référence à canonical/prompts/matching/lai_prompt.yaml

# EXISTANT (inchangé)
watch_domains:
  - id: "tech_lai_ecosystem"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
```

---

## 🔧 PHASE 2: CRÉATION MODULE PROMPT_RESOLVER

### 2.1 Nouveau Module

**Fichier**: `src_v2/vectora_core/shared/prompt_resolver.py`

**Taille**: ~80 lignes (minimaliste)

**Fonctions**:

```python
def resolve_prompt_references(
    prompt_template: str,
    canonical_scopes: Dict
) -> str:
    """
    Résout les références {{ref:...}} dans un prompt.
    
    Exemples:
        {{ref:lai_companies_global}} → "MedinCell, Camurus, ..."
        {{ref:lai_keywords.core_phrases}} → "long-acting injectable, ..."
    """

def load_prompt_for_client(
    client_config: Dict,
    prompt_type: str,  # "normalization" ou "matching"
    config_bucket: str
) -> Dict:
    """
    Charge le prompt pré-construit pour un client.
    
    Process:
    1. Lire bedrock_config.normalization_prompt depuis client_config
    2. Charger canonical/prompts/{prompt_type}/{vertical}_prompt.yaml
    3. Retourner prompt config
    """
```

### 2.2 Implémentation Minimale

**Code complet** (~80 lignes):

```python
import re
import logging
from typing import Dict, Any
from . import s3_io

logger = logging.getLogger(__name__)

def resolve_prompt_references(
    prompt_template: str,
    canonical_scopes: Dict[str, Any]
) -> str:
    """Résout {{ref:scope}} et {{ref:scope.field}}"""
    
    pattern = r'\{\{ref:([a-z_]+)(?:\.([a-z_]+))?\}\}'
    
    def replace_ref(match):
        scope_name = match.group(1)
        field_name = match.group(2)
        
        scope_data = canonical_scopes.get(scope_name)
        if not scope_data:
            logger.warning(f"Scope '{scope_name}' not found")
            return f"[SCOPE_NOT_FOUND:{scope_name}]"
        
        if field_name:
            if isinstance(scope_data, dict):
                field_data = scope_data.get(field_name, [])
            else:
                return f"[INVALID_SCOPE_STRUCTURE:{scope_name}]"
        else:
            field_data = scope_data
        
        if isinstance(field_data, list):
            return ', '.join(str(item) for item in field_data[:15])
        else:
            return str(field_data)
    
    resolved = re.sub(pattern, replace_ref, prompt_template)
    return resolved


def load_prompt_for_client(
    client_config: Dict[str, Any],
    prompt_type: str,
    config_bucket: str
) -> Dict[str, Any]:
    """Charge prompt pré-construit depuis canonical"""
    
    bedrock_config = client_config.get('bedrock_config', {})
    prompt_key = f"{prompt_type}_prompt"
    vertical = bedrock_config.get(prompt_key)
    
    if not vertical:
        logger.warning(f"No {prompt_key} in client bedrock_config")
        return None
    
    prompt_path = f"canonical/prompts/{prompt_type}/{vertical}_prompt.yaml"
    
    try:
        prompt_config = s3_io.read_yaml_from_s3(config_bucket, prompt_path)
        logger.info(f"Loaded prompt: {prompt_path}")
        return prompt_config
    except Exception as e:
        logger.error(f"Failed to load prompt {prompt_path}: {e}")
        return None
```

---

## 🔨 PHASE 3: MODIFICATION BEDROCK_CLIENT.PY

### 3.1 Modifications Minimales

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Changements**:

1. **Import prompt_resolver**:
```python
from ..shared import prompt_resolver
```

2. **Nouvelle méthode** (ajouter après ligne 150):
```python
def _build_normalization_prompt_prebuilt(
    self, item_text, client_config, canonical_scopes, canonical_prompts, config_bucket
):
    """Construit prompt depuis fichier pré-construit"""
    
    # Charger prompt pré-construit
    prompt_config = prompt_resolver.load_prompt_for_client(
        client_config, "normalization", config_bucket
    )
    
    if not prompt_config:
        # Fallback sur méthode existante
        logger.warning("Prompt pré-construit non trouvé, fallback sur v1")
        return self._build_normalization_prompt_v1(
            item_text, {}, None, None
        )
    
    # Résoudre références
    template = prompt_config['user_template']
    resolved = prompt_resolver.resolve_prompt_references(template, canonical_scopes)
    
    # Substituer {{item_text}}
    final_prompt = resolved.replace('{{item_text}}', item_text)
    
    return final_prompt
```

3. **Modifier normalize_item()** (ligne ~120):
```python
def normalize_item(self, item_text, canonical_examples, 
                  domain_contexts=None, canonical_prompts=None,
                  item_source_key=None, client_config=None, config_bucket=None):
    
    # NOUVEAU: Essayer prompt pré-construit d'abord
    if client_config and config_bucket:
        prompt = self._build_normalization_prompt_prebuilt(
            item_text, client_config, canonical_examples, 
            canonical_prompts, config_bucket
        )
    else:
        # Fallback sur méthode existante
        prompt = self._build_normalization_prompt_v1(
            item_text, canonical_examples, domain_contexts, item_source_key
        )
```

**Lignes modifiées**: ~30 lignes ajoutées, 5 lignes modifiées

### 3.2 Modification Normalizer.py

**Fichier**: `src_v2/vectora_core/normalization/normalizer.py`

**Changement**: Passer client_config et config_bucket à bedrock_client

**Ligne ~80** dans `_normalize_sequential()`:
```python
# AVANT
normalization_result = bedrock_client.normalize_item(
    item_text, examples, canonical_prompts=canonical_prompts,
    item_source_key=item.get('source_key')
)

# APRÈS
normalization_result = bedrock_client.normalize_item(
    item_text, examples, canonical_prompts=canonical_prompts,
    item_source_key=item.get('source_key'),
    client_config=client_config,  # NOUVEAU
    config_bucket=config_bucket   # NOUVEAU
)
```

**Ligne ~50** dans `normalize_items_batch()`:
```python
# Ajouter paramètres
def normalize_items_batch(
    raw_items, canonical_scopes, canonical_prompts,
    bedrock_model, bedrock_region, max_workers=1,
    watch_domains=None, matching_config=None,
    client_config=None, config_bucket=None  # NOUVEAU
):
```

**Lignes modifiées**: ~10 lignes

### 3.3 Modification __init__.py

**Fichier**: `src_v2/vectora_core/normalization/__init__.py`

**Ligne ~70** dans `run_normalize_score_for_client()`:
```python
# APRÈS chargement config (ligne 40)
config_bucket = env_vars["CONFIG_BUCKET"]  # Stocker pour passage

# Ligne ~70
normalized_items = normalizer.normalize_items_batch(
    raw_items, canonical_scopes, canonical_prompts,
    bedrock_model, env_vars["BEDROCK_REGION"],
    max_workers=max_workers,
    watch_domains=watch_domains,
    matching_config=matching_config,
    client_config=client_config,  # NOUVEAU
    config_bucket=config_bucket   # NOUVEAU
)
```

**Lignes modifiées**: ~5 lignes

---

## 🧪 PHASE 4: TESTS LOCAUX

### 4.1 Test Unitaire prompt_resolver

**Fichier**: `tests/unit/test_prompt_resolver.py` (NOUVEAU)

**Tests**:
```python
def test_resolve_simple_reference():
    """Test {{ref:lai_companies_global}}"""

def test_resolve_nested_reference():
    """Test {{ref:lai_keywords.core_phrases}}"""

def test_missing_scope():
    """Test scope inexistant"""

def test_load_prompt_for_client():
    """Test chargement prompt depuis S3"""
```

### 4.2 Test Intégration Normalisation

**Script**: `scripts/test_normalization_prebuilt_local.py` (NOUVEAU)

**Process**:
1. Charger lai_weekly_v5.yaml
2. Charger canonical scopes
3. Charger prompt pré-construit
4. Tester sur 5 items réels
5. Comparer résultats avec v1

**Validation**:
- Prompt final généré correctement
- Références résolues
- Entités extraites identiques à v1

---

## 🚀 PHASE 5: DÉPLOIEMENT AWS

### 5.1 Upload Fichiers Canonical

**Commandes**:
```bash
# Upload prompts LAI
aws s3 cp canonical/prompts/normalization/lai_prompt.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/normalization/ \
  --profile rag-lai-prod

aws s3 cp canonical/prompts/matching/lai_prompt.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/matching/ \
  --profile rag-lai-prod

# Upload client_config modifié
aws s3 cp client-config-examples/lai_weekly_v5.yaml \
  s3://vectora-inbox-config-dev/clients/ \
  --profile rag-lai-prod
```

### 5.2 Build et Deploy Lambda

**Script**: `scripts/deploy/deploy_normalize_score_v2_prebuilt.py` (NOUVEAU)

**Process**:
1. Build package avec prompt_resolver.py
2. Upload vers S3
3. Update Lambda normalize-score-v2

**Commande**:
```bash
python scripts/deploy/deploy_normalize_score_v2_prebuilt.py
```

### 5.3 Validation Déploiement

**Checks**:
- [ ] Fichiers canonical uploadés
- [ ] Lambda mise à jour
- [ ] Variables d'environnement OK
- [ ] Logs CloudWatch accessibles

---

## ✅ PHASE 6: TESTS E2E POC

### 6.1 Test lai_weekly_v5

**Payload**:
```json
{
  "client_id": "lai_weekly_v5",
  "force_reprocess": false
}
```

**Invocation**:
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload file://payload_lai_v5.json \
  --profile rag-lai-prod \
  response.json
```

### 6.2 Validation Résultats

**Métriques attendues**:
- ✅ Items normalisés: 100%
- ✅ Prompt pré-construit utilisé (check logs)
- ✅ Références résolues correctement
- ✅ Entités extraites cohérentes avec v1
- ✅ Temps d'exécution similaire (<5% différence)

**Logs à vérifier**:
```
"Loaded prompt: canonical/prompts/normalization/lai_prompt.yaml"
"Resolved 5 references in prompt"
"Using prebuilt prompt for normalization"
```

### 6.3 Comparaison v1 vs Approche B

**Script**: `scripts/analysis/compare_v1_vs_prebuilt.py` (NOUVEAU)

**Comparaison**:
- Nombre d'entités extraites
- Event types classifiés
- Scores LAI
- Temps d'exécution

**Seuils acceptables**:
- Différence entités: <5%
- Différence scores: <10%
- Temps exécution: <5%

---

## 📊 PHASE 7: RETOUR UTILISATEUR

### 7.1 Documentation Utilisateur

**Fichier**: `docs/guides/guide_ajustement_prompts_approche_b.md` (NOUVEAU)

**Contenu**:
- Comment ajuster un prompt LAI
- Comment créer un prompt pour nouvelle verticale
- Syntaxe des références {{ref:...}}
- Tests dans Bedrock Playground

### 7.2 Checklist Ajustements

**Pour ajuster la sélectivité**:
1. Modifier `canonical/prompts/normalization/lai_prompt.yaml`
2. Ajuster instructions CRITICAL/FORBIDDEN
3. Modifier références aux scopes
4. Upload vers S3
5. Tester avec lai_weekly_v5

**Pas de modification de code Python nécessaire**

### 7.3 Monitoring

**Métriques CloudWatch**:
- Temps résolution prompts
- Taux succès chargement prompts
- Fallback sur v1 (doit être 0%)

---

## 📋 RÉCAPITULATIF MODIFICATIONS

### Fichiers Créés (6)

1. `canonical/prompts/normalization/lai_prompt.yaml` (~1.5 KB)
2. `canonical/prompts/matching/lai_prompt.yaml` (~1 KB)
3. `src_v2/vectora_core/shared/prompt_resolver.py` (~80 lignes)
4. `tests/unit/test_prompt_resolver.py` (~100 lignes)
5. `scripts/test_normalization_prebuilt_local.py` (~150 lignes)
6. `docs/guides/guide_ajustement_prompts_approche_b.md` (doc)

### Fichiers Modifiés (4)

1. `client-config-examples/lai_weekly_v5.yaml` (+5 lignes)
2. `src_v2/vectora_core/normalization/bedrock_client.py` (+35 lignes)
3. `src_v2/vectora_core/normalization/normalizer.py` (+10 lignes)
4. `src_v2/vectora_core/normalization/__init__.py` (+5 lignes)

**Total code ajouté**: ~280 lignes  
**Total code modifié**: ~55 lignes  
**Ratio**: Minimaliste et ciblé

---

## ⚠️ POINTS DE VIGILANCE

### Vigilance 1: Compatibilité Ascendante

**Risque**: Casser le comportement existant

**Mitigation**:
- Fallback sur v1 si prompt pré-construit absent
- Tests comparatifs v1 vs Approche B
- Déploiement progressif (POC lai_weekly_v5 d'abord)

### Vigilance 2: Résolution Références

**Risque**: Références mal résolues (scope inexistant)

**Mitigation**:
- Validation au chargement
- Logs explicites si scope manquant
- Tests unitaires exhaustifs

### Vigilance 3: Performance

**Risque**: Overhead résolution références

**Mitigation**:
- Mesure temps résolution (<20ms attendu)
- Cache possible si nécessaire
- Monitoring CloudWatch

### Vigilance 4: Synchronisation S3

**Risque**: Prompts S3 désynchronisés avec code

**Mitigation**:
- Versioning des prompts (metadata.version)
- Upload systématique lors déploiement
- Validation au démarrage Lambda

---

## 🎯 CRITÈRES DE SUCCÈS

### Succès Technique

✅ Prompt pré-construit chargé et utilisé  
✅ Références résolues correctement  
✅ Résultats identiques à v1 (±5%)  
✅ Performance maintenue (<5% overhead)  
✅ Aucun fallback sur v1  

### Succès Métier

✅ Humain peut ajuster prompts sans code  
✅ Debugging facilité (prompt visible)  
✅ Tests manuels possibles (Playground)  
✅ Documentation claire  
✅ Générique (prêt pour Gene Therapy)  

### Succès Opérationnel

✅ Déploiement sans incident  
✅ Logs exploitables  
✅ Monitoring en place  
✅ Rollback possible  
✅ Documentation à jour  

---

## 📅 PLANNING ESTIMÉ

**Phase 0 (Diagnostic)**: 2h - Analyse existant  
**Phase 1 (Canonical)**: 3h - Création prompts LAI  
**Phase 2 (Resolver)**: 2h - Module prompt_resolver  
**Phase 3 (Bedrock)**: 3h - Modifications bedrock_client  
**Phase 4 (Tests locaux)**: 2h - Tests unitaires + intégration  
**Phase 5 (Déploiement)**: 1h - Upload S3 + deploy Lambda  
**Phase 6 (Tests E2E)**: 2h - POC lai_weekly_v5  
**Phase 7 (Documentation)**: 1h - Guide utilisateur  

**Total estimé**: 16h (2 jours)

---

## 🚦 PROCHAINES ÉTAPES

1. **Validation du plan** avec product owner
2. **Phase 1**: Création prompts LAI dans canonical
3. **Phase 2**: Implémentation prompt_resolver
4. **Phase 3**: Modifications bedrock_client
5. **Phase 4**: Tests locaux
6. **Phase 5**: Déploiement AWS
7. **Phase 6**: POC lai_weekly_v5
8. **Phase 7**: Documentation et retour

**Prêt à démarrer**: Toutes les informations nécessaires sont disponibles

---

*Plan correctif réalisé le 2025-12-23*  
*Basé sur analyse complète du code et des diagnostics*  
*Objectif: Approche B opérationnelle sur lai_weekly_v5*
