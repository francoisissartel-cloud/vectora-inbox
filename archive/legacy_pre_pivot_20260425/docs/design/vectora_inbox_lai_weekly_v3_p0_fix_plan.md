# Vectora Inbox LAI Weekly v3 - Plan de Correction P0

**Objectif** : Workflow end-to-end fonctionnel et raisonnablement pertinent pour lai_weekly_v3  
**Basé sur** : Diagnostics vectora_inbox_lai_weekly_v3_p0_recommendations.md et human_review_sheet.md  
**Priorité** : MVP sécurisé, optimisation ultérieure

---

## Résumé Exécutif

| **Phase** | **Objectif** | **Corrections P0** | **Validation** |
|-----------|--------------|-------------------|----------------|
| **Phase 0** | État des lieux | Vérification déploiement précédent | Cas de test critiques |
| **Phase 1** | P0-1 Bedrock tech | Détection technology LAI normalisée | UZEDY, Nanexa, MedinCell |
| **Phase 2** | P0-2 Exclusions runtime | Filtrage HR/finance effectif | DelSiTech HR, MedinCell finance |
| **Phase 3** | P0-3 HTML Nanexa | Résumé non vide pour Nanexa/Moderna | PharmaShell® détectable |
| **Phase 4** | Déploiement & Run | Pipeline complet lai_weekly_v3 | Newsletter qualité MVP |
| **Phase 5** | Bilan & P1 | Executive summary | Recommandations suite |

**Critères de succès MVP** :
- ✅ Items LAI-strong (Nanexa/Moderna, UZEDY, MedinCell malaria) en newsletter
- ❌ Bruit HR/finance (DelSiTech hiring, MedinCell financial) exclu
- 📊 Newsletter avec ratio signal/noise > 60% (vs 20% actuel)

---

## Phase 0 – Relecture & Confirmation d'État

### Objectifs
- Vérifier l'état du déploiement précédent
- Confirmer les cas de test critiques
- Établir la baseline avant corrections P0

### Actions
1. **Vérification déploiement actuel**
   ```bash
   # Vérifier les Lambdas déployées
   aws lambda list-functions --region eu-west-3 --profile rag-lai-prod | grep vectora
   
   # Vérifier les versions des prompts
   aws s3 ls s3://vectora-inbox-rag-lai-prod/prompts/ --profile rag-lai-prod
   ```

2. **Rappel des cas de test critiques**
   - **Nanexa/Moderna** (PharmaShell) : `"summary": ""` → doit avoir contenu
   - **UZEDY regulatory/extension** : technology non détectée → doit matcher tech_lai_ecosystem
   - **MedinCell malaria grant** : pure player rejeté → doit matcher par contexte
   - **DelSiTech HR items** : bruit en newsletter → doit être exclu
   - **MedinCell finance items** : bruit en newsletter → doit être exclu

3. **Test baseline rapide**
   ```bash
   # Run minimal pour vérifier l'état actuel
   aws lambda invoke --function-name vectora-inbox-ingest-normalize-rag-lai-prod \
     --payload '{"source_key": "test_baseline", "period_days": 1}' \
     --profile rag-lai-prod --region eu-west-3 response.json
   ```

### Livrables Phase 0
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_phase0_baseline_check.md`
- Confirmation de l'état des déploiements
- Validation des cas de test critiques

---

## Phase 1 – P0-1 : Bedrock Technology Detection

### Problème Identifié
- **Cause racine** : Bedrock ne détecte aucune technology LAI malgré leur présence dans `technology_scopes.yaml`
- **Impact** : UZEDY, Nanexa/Moderna, items LAI authentiques rejetés
- **Symptômes** : `"technologies_detected": []` pour tous les items

### Solution Technique

#### 1.1 Diagnostic du prompt Bedrock actuel
```bash
# Examiner le prompt de normalisation
cat src/lambdas/ingest_normalize/prompts/normalize_prompt.txt
```

#### 1.2 Correction du prompt de normalisation
**Fichier** : `src/lambdas/ingest_normalize/prompts/normalize_prompt.txt`

```python
# Injection des technology_scopes dans le prompt
ENHANCED_PROMPT = f"""
You are a pharmaceutical industry analyst. Analyze this news item and extract structured information.

TECHNOLOGY DETECTION RULES:
Use these LAI technology terms for detection:
- Extended-Release Injectable, Long-Acting Injectable, LAI
- PharmaShell®, SiliaShell®, BEPO®, Depot injection
- Once-monthly injection, Once-quarterly injection
- UZEDY® (risperidone LAI trademark)

DETECTION INSTRUCTIONS:
1. Scan title and content for exact matches (case-insensitive)
2. Include trademark symbols (®, ™) in detection
3. Detect technology variations: "extended-release injectable" = "LAI"
4. Include in "technologies_detected" array
5. Include in "trademarks_detected" array for branded terms

RESPONSE FORMAT:
{{
  "title": "extracted title",
  "summary": "concise summary",
  "companies_detected": ["company1", "company2"],
  "technologies_detected": ["Extended-Release Injectable", "PharmaShell®"],
  "trademarks_detected": ["UZEDY®", "PharmaShell®"],
  "molecules_detected": ["molecule1"],
  "event_type": "regulatory|partnership|clinical_update|corporate|other",
  "domain_relevance_score": 0.8
}}
"""
```

#### 1.3 Modification du handler de normalisation
**Fichier** : `src/lambdas/ingest_normalize/handler.py`

```python
def load_technology_scopes():
    """Charge les technology_scopes pour injection dans le prompt"""
    try:
        with open('config/technology_scopes.yaml', 'r') as f:
            scopes = yaml.safe_load(f)
        
        # Extraire les termes LAI pour le prompt
        lai_terms = []
        for scope_name, terms in scopes.items():
            if 'lai' in scope_name.lower():
                lai_terms.extend(terms)
        
        return lai_terms
    except Exception as e:
        logger.error(f"Failed to load technology scopes: {e}")
        return []

def enhance_prompt_with_technology_scopes(base_prompt):
    """Injecte les technology scopes dans le prompt Bedrock"""
    lai_terms = load_technology_scopes()
    
    if lai_terms:
        tech_section = f"""
TECHNOLOGY DETECTION TERMS:
{', '.join(lai_terms)}

Specifically detect these patterns:
- "Extended-Release Injectable" or "LAI" 
- "PharmaShell®" or "SiliaShell®"
- "UZEDY®" as LAI trademark
- "depot injection" or "once-monthly"
"""
        return base_prompt + tech_section
    
    return base_prompt
```

### Tests Phase 1

#### 1.4 Tests locaux avec mock data
```python
# Test cases pour validation
test_cases = [
    {
        "title": "FDA Approves Expanded Indication for UZEDY® (risperidone) Extended-Release Injectable",
        "expected_technologies": ["Extended-Release Injectable"],
        "expected_trademarks": ["UZEDY®"]
    },
    {
        "title": "Nanexa and Moderna enter into license agreement for PharmaShell®-based products",
        "expected_technologies": ["PharmaShell®"],
        "expected_trademarks": ["PharmaShell®"]
    },
    {
        "title": "Olanzapine LAI submission to FDA",
        "expected_technologies": ["LAI"],
        "expected_trademarks": []
    }
]
```

#### 1.5 Validation avec Lambda invoke
```bash
# Test avec payload UZEDY
echo '{"title": "FDA Approves UZEDY Extended-Release Injectable", "raw_text": "UZEDY (risperidone) extended-release injectable suspension..."}' | base64 > test_uzedy.b64

aws lambda invoke --function-name vectora-inbox-ingest-normalize-rag-lai-prod \
  --payload file://test_uzedy.b64 \
  --profile rag-lai-prod --region eu-west-3 response_uzedy.json

# Vérifier que technologies_detected contient "Extended-Release Injectable"
cat response_uzedy.json | jq '.technologies_detected'
```

### Critères de Succès Phase 1
- ✅ UZEDY items : `"technologies_detected": ["Extended-Release Injectable"]`
- ✅ Nanexa items : `"technologies_detected": ["PharmaShell®"]`
- ✅ LAI items génériques : `"technologies_detected": ["LAI"]`

### Livrables Phase 1
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_phase1_bedrock_tech_fix_results.md`
- Code modifié : `src/lambdas/ingest_normalize/handler.py`
- Prompt modifié : `src/lambdas/ingest_normalize/prompts/normalize_prompt.txt`

---

## Phase 2 – P0-2 : Exclusions HR/Finance au Runtime

### Problème Identifié
- **Cause racine** : `exclusion_scopes.yaml` existe mais n'est pas utilisé dans le pipeline
- **Impact** : DelSiTech HR, MedinCell finance en newsletter (80% bruit)
- **Symptômes** : "DelSiTech is Hiring", "Financial Results" passent le filtre

### Solution Technique

#### 2.1 Implémentation du filtrage d'exclusion
**Fichier** : `src/lambdas/engine/exclusion_filter.py` (nouveau)

```python
import yaml
import logging

logger = logging.getLogger(__name__)

def load_exclusion_scopes():
    """Charge les exclusion_scopes.yaml"""
    try:
        with open('config/exclusion_scopes.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load exclusion scopes: {e}")
        return {}

def apply_exclusion_filters(item, exclusion_scopes):
    """Applique les filtres d'exclusion selon exclusion_scopes.yaml"""
    
    title_lower = item.get('title', '').lower()
    summary_lower = item.get('summary', '').lower()
    content = f"{title_lower} {summary_lower}"
    
    # Vérifier exclusions HR
    hr_terms = exclusion_scopes.get('hr_recruitment_terms', [])
    for term in hr_terms:
        if term.lower() in content:
            return False, f"Excluded by HR term: {term}"
    
    # Vérifier exclusions finance
    finance_terms = exclusion_scopes.get('financial_reporting_terms', [])
    for term in finance_terms:
        if term.lower() in content:
            return False, f"Excluded by finance term: {term}"
    
    return True, "Not excluded"

def filter_items_by_exclusions(items):
    """Filtre une liste d'items selon les exclusions"""
    exclusion_scopes = load_exclusion_scopes()
    filtered_items = []
    
    for item in items:
        is_allowed, reason = apply_exclusion_filters(item, exclusion_scopes)
        
        if is_allowed:
            filtered_items.append(item)
        else:
            item['excluded'] = True
            item['exclusion_reason'] = reason
            logger.info(f"Item excluded: {item.get('title', 'No title')} - {reason}")
    
    return filtered_items
```

#### 2.2 Intégration dans la Lambda engine
**Fichier** : `src/lambdas/engine/handler.py`

```python
from exclusion_filter import filter_items_by_exclusions

def lambda_handler(event, context):
    """Handler principal avec filtrage d'exclusion"""
    
    # Étapes existantes : load items, normalize, etc.
    normalized_items = load_normalized_items(event)
    
    # NOUVEAU : Appliquer les exclusions avant matching/scoring
    filtered_items = filter_items_by_exclusions(normalized_items)
    
    logger.info(f"Items after exclusion filter: {len(filtered_items)}/{len(normalized_items)}")
    
    # Continuer avec matching et scoring sur les items filtrés
    matched_items = apply_matching_logic(filtered_items)
    scored_items = apply_scoring_logic(matched_items)
    
    # Générer newsletter
    newsletter = generate_newsletter(scored_items)
    
    return {
        'statusCode': 200,
        'body': {
            'total_items': len(normalized_items),
            'filtered_items': len(filtered_items),
            'newsletter_items': len(newsletter['items'])
        }
    }
```

### Tests Phase 2

#### 2.3 Tests locaux avec cas HR/finance
```python
# Test cases pour validation exclusions
exclusion_test_cases = [
    {
        "title": "DelSiTech is Hiring a Process Engineer",
        "expected_excluded": True,
        "expected_reason": "hiring"
    },
    {
        "title": "DelSiTech Seeks an Experienced Quality Director", 
        "expected_excluded": True,
        "expected_reason": "seeks"
    },
    {
        "title": "MedinCell Publishes Consolidated Financial Results",
        "expected_excluded": True,
        "expected_reason": "financial results"
    },
    {
        "title": "MedinCell Partnership for LAI Development",
        "expected_excluded": False,
        "expected_reason": "Not excluded"
    }
]
```

#### 2.4 Validation avec run engine
```bash
# Test avec payload contenant items HR/finance
echo '{"normalized_items": [{"title": "DelSiTech is Hiring", "summary": "Process engineer position"}]}' | base64 > test_exclusions.b64

aws lambda invoke --function-name vectora-inbox-engine-rag-lai-prod \
  --payload file://test_exclusions.b64 \
  --profile rag-lai-prod --region eu-west-3 response_exclusions.json

# Vérifier que l'item est exclu
cat response_exclusions.json | jq '.filtered_items'
```

### Critères de Succès Phase 2
- ❌ "DelSiTech is Hiring" : `excluded: true, reason: "hiring"`
- ❌ "DelSiTech Seeks Quality Director" : `excluded: true, reason: "seeks"`
- ❌ "MedinCell Financial Results" : `excluded: true, reason: "financial results"`
- ✅ Items LAI authentiques : `excluded: false`

### Livrables Phase 2
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_phase2_exclusions_runtime_results.md`
- Code nouveau : `src/lambdas/engine/exclusion_filter.py`
- Code modifié : `src/lambdas/engine/handler.py`

---

## Phase 3 – P0-3 : Correction Perte News Nanexa/Moderna

### Problème Identifié
- **Cause racine** : `"summary": ""` pour item Nanexa/Moderna PharmaShell
- **Impact** : Partnership LAI majeur non détectable par Bedrock
- **Symptômes** : HTML extraction échoue ou timeout Bedrock

### Solution Technique

#### 3.1 Diagnostic de l'extraction HTML
```bash
# Examiner les logs d'extraction pour Nanexa
aws logs filter-log-events --log-group-name /aws/lambda/vectora-inbox-ingest-normalize-rag-lai-prod \
  --filter-pattern "Nanexa" --profile rag-lai-prod --region eu-west-3
```

#### 3.2 Amélioration de l'extraction avec fallback
**Fichier** : `src/lambdas/ingest_normalize/html_extractor.py`

```python
def extract_content_with_fallback(url, title, max_retries=2):
    """Extraction HTML avec fallback robuste"""
    
    for attempt in range(max_retries):
        try:
            # Tentative extraction HTML normale
            content = extract_html_content(url, timeout=10)
            
            if content and len(content.strip()) > 50:
                logger.info(f"HTML extraction successful for {url} (attempt {attempt + 1})")
                return content
                
        except Exception as e:
            logger.warning(f"HTML extraction attempt {attempt + 1} failed for {url}: {e}")
            
            if attempt < max_retries - 1:
                time.sleep(2)  # Retry delay
    
    # Fallback : utiliser le titre comme contenu minimal
    if title and len(title.strip()) > 10:
        fallback_content = f"""
Title: {title}

Content extraction failed for this URL. Analysis based on title only.
This appears to be a pharmaceutical industry news item that requires manual review.
"""
        logger.info(f"Using title fallback for {url}")
        return fallback_content
    
    logger.error(f"Complete extraction failure for {url}")
    return None

def create_minimal_item_from_title(item):
    """Crée un item minimal basé uniquement sur le titre"""
    title = item.get('title', '')
    
    return {
        'title': title,
        'summary': f"Content extraction failed. Title-based analysis: {title}",
        'companies_detected': extract_companies_from_title(title),
        'technologies_detected': extract_technologies_from_title(title),
        'trademarks_detected': extract_trademarks_from_title(title),
        'molecules_detected': [],
        'event_type': 'other',
        'domain_relevance_score': 0.3,  # Score réduit pour items partiels
        'extraction_status': 'title_only_fallback'
    }
```

#### 3.3 Modification du handler de normalisation
**Fichier** : `src/lambdas/ingest_normalize/handler.py`

```python
def normalize_item_with_bedrock_robust(item):
    """Normalisation avec gestion d'erreur améliorée"""
    
    raw_text = item.get('raw_text', '')
    title = item.get('title', '')
    url = item.get('url', '')
    
    # Si pas de contenu, essayer extraction avec fallback
    if not raw_text or len(raw_text.strip()) < 50:
        logger.info(f"Attempting content extraction with fallback for: {title}")
        raw_text = extract_content_with_fallback(url, title)
    
    # Si toujours pas de contenu, créer item minimal
    if not raw_text:
        logger.warning(f"Creating minimal item from title: {title}")
        return create_minimal_item_from_title(item)
    
    # Normalisation Bedrock normale
    try:
        normalized = bedrock_normalize(raw_text, item)
        
        # Vérifier que la normalisation a produit un résultat valide
        if not normalized.get('summary') or len(normalized['summary'].strip()) < 10:
            logger.warning(f"Bedrock produced empty summary for: {title}")
            # Fallback sur item minimal
            return create_minimal_item_from_title(item)
        
        return normalized
        
    except Exception as e:
        logger.error(f"Bedrock normalization failed for {title}: {e}")
        return create_minimal_item_from_title(item)
```

### Tests Phase 3

#### 3.4 Test spécifique Nanexa/Moderna
```bash
# Test avec URL Nanexa réelle ou mock
echo '{"url": "https://nanexa.com/nanexa-moderna-pharmashell", "title": "Nanexa and Moderna enter into license agreement for PharmaShell®-based products"}' | base64 > test_nanexa.b64

aws lambda invoke --function-name vectora-inbox-ingest-normalize-rag-lai-prod \
  --payload file://test_nanexa.b64 \
  --profile rag-lai-prod --region eu-west-3 response_nanexa.json

# Vérifier que summary n'est pas vide
cat response_nanexa.json | jq '.summary'
```

#### 3.5 Validation de la détection PharmaShell®
```python
# Après correction, vérifier que PharmaShell® est détecté
expected_result = {
    "title": "Nanexa and Moderna enter into license agreement for PharmaShell®-based products",
    "summary": "Non-empty summary content...",
    "technologies_detected": ["PharmaShell®"],
    "trademarks_detected": ["PharmaShell®"],
    "extraction_status": "success"  # ou "title_only_fallback"
}
```

### Critères de Succès Phase 3
- ✅ Nanexa/Moderna : `"summary": "Non-empty content"`
- ✅ PharmaShell® détecté : `"technologies_detected": ["PharmaShell®"]`
- ✅ Fallback fonctionnel : items avec extraction échouée ont un contenu minimal

### Livrables Phase 3
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_phase3_nanexa_html_fix_results.md`
- Code modifié : `src/lambdas/ingest_normalize/html_extractor.py`
- Code modifié : `src/lambdas/ingest_normalize/handler.py`

---

## Phase 4 – Déploiement & Run de Validation

### Objectifs
- Déployer toutes les corrections P0 (Phases 1-3)
- Exécuter un run complet lai_weekly_v3 en DEV
- Valider la qualité de la newsletter générée

### Actions de Déploiement

#### 4.1 Package et déploiement des Lambdas
```bash
# Déploiement Lambda ingest-normalize (Phase 1 + 3)
cd src/lambdas/ingest_normalize
zip -r ../../../deploy/ingest-normalize-v3-p0.zip . -x "*.pyc" "__pycache__/*"

aws lambda update-function-code \
  --function-name vectora-inbox-ingest-normalize-rag-lai-prod \
  --zip-file fileb://deploy/ingest-normalize-v3-p0.zip \
  --profile rag-lai-prod --region eu-west-3

# Déploiement Lambda engine (Phase 2)
cd src/lambdas/engine
zip -r ../../../deploy/engine-v3-p0.zip . -x "*.pyc" "__pycache__/*"

aws lambda update-function-code \
  --function-name vectora-inbox-engine-rag-lai-prod \
  --zip-file fileb://deploy/engine-v3-p0.zip \
  --profile rag-lai-prod --region eu-west-3
```

#### 4.2 Run complet lai_weekly_v3
```bash
# Invocation complète du pipeline
# Étape 1 : Ingestion + Normalisation
echo '{"source_key": "lai_weekly_v3_p0_validation", "period_days": 7, "target_date": "2025-12-11"}' | base64 > payload_ingest.b64

aws lambda invoke --function-name vectora-inbox-ingest-normalize-rag-lai-prod \
  --payload file://payload_ingest.b64 \
  --profile rag-lai-prod --region eu-west-3 response_ingest.json

# Vérifier le résultat de l'ingestion
cat response_ingest.json | jq '.statusCode, .body.total_items, .body.normalized_items'

# Étape 2 : Engine (Matching + Scoring + Newsletter)
echo '{"source_key": "lai_weekly_v3_p0_validation", "domain": "tech_lai_ecosystem"}' | base64 > payload_engine.b64

aws lambda invoke --function-name vectora-inbox-engine-rag-lai-prod \
  --payload file://payload_engine.b64 \
  --profile rag-lai-prod --region eu-west-3 response_engine.json

# Vérifier la newsletter générée
cat response_engine.json | jq '.body.newsletter.items | length'
```

### Validation des Cas de Test Critiques

#### 4.3 Vérification des items gold
```bash
# Télécharger la newsletter générée
aws s3 cp s3://vectora-inbox-rag-lai-prod/newsletters/lai_weekly_v3_p0_validation.json . \
  --profile rag-lai-prod

# Vérifier présence des items LAI-strong
cat lai_weekly_v3_p0_validation.json | jq '.items[] | select(.title | contains("Nanexa")) | .title'
cat lai_weekly_v3_p0_validation.json | jq '.items[] | select(.title | contains("UZEDY")) | .title'  
cat lai_weekly_v3_p0_validation.json | jq '.items[] | select(.title | contains("MedinCell") and contains("Malaria")) | .title'

# Vérifier absence du bruit HR/finance
cat lai_weekly_v3_p0_validation.json | jq '.items[] | select(.title | contains("Hiring")) | .title'
cat lai_weekly_v3_p0_validation.json | jq '.items[] | select(.title | contains("Financial Results")) | .title'
```

### Métriques de Validation

#### 4.4 Calcul du ratio signal/noise
```python
# Script de validation des métriques
def calculate_newsletter_quality(newsletter_file):
    with open(newsletter_file, 'r') as f:
        newsletter = json.load(f)
    
    items = newsletter.get('items', [])
    total_items = len(items)
    
    # Classification manuelle des items
    lai_strong = 0
    lai_weak = 0
    noise = 0
    
    for item in items:
        title = item.get('title', '').lower()
        
        # LAI-strong patterns
        if any(pattern in title for pattern in ['uzedy', 'pharmashell', 'extended-release injectable', 'lai']):
            lai_strong += 1
        # Noise patterns  
        elif any(pattern in title for pattern in ['hiring', 'seeks', 'financial results', 'appointment']):
            noise += 1
        else:
            lai_weak += 1
    
    signal_ratio = (lai_strong + lai_weak * 0.5) / total_items if total_items > 0 else 0
    
    return {
        'total_items': total_items,
        'lai_strong': lai_strong,
        'lai_weak': lai_weak, 
        'noise': noise,
        'signal_ratio': signal_ratio
    }
```

### Critères de Succès Phase 4
- ✅ **Items LAI-strong présents** : Nanexa/Moderna, UZEDY, MedinCell malaria
- ❌ **Bruit HR/finance absent** : DelSiTech hiring, MedinCell financial
- 📊 **Ratio signal/noise > 60%** (objectif MVP vs 20% baseline)
- 🚀 **Pipeline end-to-end fonctionnel** : ingestion → newsletter sans erreur

### Livrables Phase 4
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_phase4_deployment_validation_results.md`
- Newsletter générée : `lai_weekly_v3_p0_validation.json`
- Métriques de qualité calculées

---

## Phase 5 – Résumé & Recommandations P1

### Objectifs
- Synthèse executive des résultats P0
- Identification de ce qui marche vs problématique
- Recommandations pour itération P1

### Actions

#### 5.1 Executive Summary
**Fichier** : `docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_executive_summary.md`

Structure du résumé :
```markdown
# Executive Summary - Vectora Inbox LAI Weekly v3 P0

## Résultats P0 (MVP Sécurisé)

### ✅ Corrections Réussies
- **P0-1 Bedrock Technology** : [Statut] - [Métriques]
- **P0-2 Exclusions Runtime** : [Statut] - [Métriques]  
- **P0-3 HTML Nanexa** : [Statut] - [Métriques]

### 📊 Métriques Newsletter v3
- **Items total** : X
- **Ratio signal/noise** : Y% (objectif 60%)
- **Items LAI-strong** : Z (Nanexa ✅/❌, UZEDY ✅/❌, MedinCell ✅/❌)
- **Bruit éliminé** : W% (HR/finance)

### ⚠️ Points Problématiques Restants
- [Problème 1] : [Description] - [Impact]
- [Problème 2] : [Description] - [Impact]

## Recommandations P1

### Priorité Haute
1. **[Recommandation 1]** : [Justification] - [Effort estimé]
2. **[Recommandation 2]** : [Justification] - [Effort estimé]

### Priorité Moyenne  
3. **[Recommandation 3]** : [Justification] - [Effort estimé]

### Optimisations Futures
- [Optimisation 1] : [Description]
- [Optimisation 2] : [Description]

## Conclusion MVP
[Statut global : OK pour MVP / Nécessite P1 critique / Échec MVP]
```

#### 5.2 Analyse comparative
```python
# Comparaison v2 vs v3 P0
comparison_metrics = {
    'v2_baseline': {
        'signal_ratio': 0.20,
        'lai_strong_items': 1,
        'noise_items': 4,
        'total_newsletter_items': 5
    },
    'v3_p0': {
        'signal_ratio': 0.XX,  # À calculer
        'lai_strong_items': X,
        'noise_items': Y,
        'total_newsletter_items': Z
    }
}
```

### Critères d'Évaluation MVP
- **✅ MVP OK** : Signal ratio > 60%, items gold présents, bruit < 30%
- **⚠️ MVP Partiel** : Signal ratio 40-60%, items gold partiels, bruit < 50%  
- **❌ MVP Échec** : Signal ratio < 40%, items gold absents, bruit > 50%

### Livrables Phase 5
- `docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_executive_summary.md`
- Recommandations P1 priorisées
- Décision GO/NO-GO pour production

---

## Annexes

### Commandes de Déploiement Rapide
```bash
# Déploiement complet P0
./scripts/deploy_p0_fixes.sh

# Run de validation
./scripts/run_lai_weekly_v3_validation.sh

# Vérification des métriques
./scripts/validate_newsletter_quality.sh
```

### Rollback Plan
```bash
# En cas d'échec critique
aws lambda update-function-code \
  --function-name vectora-inbox-ingest-normalize-rag-lai-prod \
  --zip-file fileb://backup/ingest-normalize-v2-stable.zip

aws lambda update-function-code \
  --function-name vectora-inbox-engine-rag-lai-prod \
  --zip-file fileb://backup/engine-v2-stable.zip
```

### Contacts & Escalation
- **Échec Phase 1-3** : Continuer avec corrections partielles
- **Échec Phase 4** : Rollback et analyse des logs
- **Échec Phase 5** : Décision P1 critique vs MVP partiel