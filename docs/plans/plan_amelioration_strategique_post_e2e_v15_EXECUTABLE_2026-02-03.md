# Plan d'Amélioration Stratégique Post E2E V15 - PLAN UNIFIÉ

**Date**: 2026-02-03  
**Objectif**: Corrections V16 conformes CRITICAL_RULES + Tests locaux complets  
**Durée totale**: 3h15

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Problèmes Corrigés

| # | Problème | Solution | Impact |
|---|----------|----------|--------|
| 1 | Companies non détectées | Ajout ref scope dans prompt | +7 companies/run |
| 2 | Quince rejeté (dosing titre) | Passer titre à Bedrock | +1 item relevant |
| 3 | Eli Lilly faux positif | Bloquer hallucination | -1 faux positif |
| 4 | MedinCell grant rejeté | Classifier grants + rule_7 | +1 item relevant |
| 5 | Bruit RH/Financial ingéré | Charger exclusion_scopes S3 | -3 à -6 items |

### Versions Incrémentées

```ini
VECTORA_CORE_VERSION=1.4.1 → 1.4.2
CANONICAL_VERSION=2.2 → 2.3
NORMALIZE_VERSION=2.1.0 → 2.1.1
INGEST_VERSION=1.5.0 → 1.5.1
```

---

## 📋 PHASES D'EXÉCUTION

### PHASE 0: Préparation Git + Modifications (1h)

#### Étape 0.1: Créer Branche (2min)

```bash
git checkout develop
git pull origin develop
git checkout -b fix/v16-corrections-post-e2e-v15
```

#### Étape 0.2: Incrémenter VERSION (2min)

**Fichier**: `VERSION`

```ini
# AVANT
VECTORA_CORE_VERSION=1.4.1
CANONICAL_VERSION=2.2
NORMALIZE_VERSION=2.1.0
INGEST_VERSION=1.5.0

# APRÈS
VECTORA_CORE_VERSION=1.4.2
CANONICAL_VERSION=2.3
NORMALIZE_VERSION=2.1.1
INGEST_VERSION=1.5.1
```

#### Étape 0.3: Appliquer Modifications Canonical (30min)

**Fichier 1**: `canonical/prompts/normalization/generic_normalization.yaml`

**Modification A - Ligne 17** (ajouter titre):
```yaml
# AVANT
  TEXT TO ANALYZE:
  {{item_text}}

# APRÈS
  TEXT TO ANALYZE:
  Title: {{item_title}}
  Content: {{item_text}}
```

**Modification B - Ligne 38** (classifier grants):
```yaml
# AVANT
  3. EVENT CLASSIFICATION
     - Classify into ONE primary type:
       * partnership (collaborations, licensing, M&A)

# APRÈS
  3. EVENT CLASSIFICATION
     - Classify into ONE primary type:
       * partnership (collaborations, licensing, M&A, grants, funding, research agreements)
     
     CRITICAL DISTINCTIONS:
     - Grant/funding for R&D → partnership (NOT financial_results)
     - Quarterly earnings → financial_results
     
     EXAMPLES:
     - "Company awarded $5M grant for malaria research" → partnership
     - "Company reports Q3 earnings" → financial_results
```

**Modification C - Ligne 54** (companies avec ref):
```yaml
# AVANT
  4. ENTITY EXTRACTION (ALL explicitly mentioned)
     - Companies: ALL pharmaceutical/biotech company names

# APRÈS
  4. ENTITY EXTRACTION (ALL explicitly mentioned)
     - Companies: ALL pharmaceutical/biotech company names mentioned in text
       Reference list (for context): {{ref:company_scopes.lai_companies_global}}
       CRITICAL: Extract company names EXACTLY as they appear in text
```

**Modification D - Ligne 62** (dosing depuis titre):
```yaml
# AVANT
     - Dosing Intervals: ALL dosing frequency terms EXPLICITLY mentioned
       CRITICAL: Only extract if EXPLICITLY stated in text (title or body)

# APRÈS
     - Dosing Intervals: ALL dosing frequency terms EXPLICITLY mentioned
       CRITICAL: Extract from BOTH title AND content
       Priority: Check title FIRST (dosing often in headlines)
```

**Fichier 2**: `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`

**Modification - Ligne 11** (bloquer hallucination):
```yaml
# APRÈS ligne 15, ajouter:
  6. CRITICAL: technology_family MUST be from the 73 terms in lai_domain_definition
     - DO NOT detect generic terms: "injectables", "devices", "manufacturing"
  7. Manufacturing facilities WITHOUT specific LAI technology → REJECT
```

**Fichier 3**: `canonical/domains/lai_domain_definition.yaml`

**Modification A - Ligne 167** (exclusions):
```yaml
# APRÈS ligne 167, ajouter:
  # Generic injectable terms (not LAI-specific)
  - "injectables and devices"
  - "injectable manufacturing"
```

**Modification B - Ligne 189** (rule_7):
```yaml
# APRÈS ligne 189, ajouter:
  - id: rule_7
    condition: "pure_player_company + event_type == 'partnership'"
    action: "match with medium confidence (score ≥60)"
    reasoning: "Pure players LAI: all partnerships relevant"
```

#### Étape 0.4: Appliquer Modifications Code Python (20min)

**Fichier 1**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Modification A - Ligne 145**:
```python
# AVANT
prompt = self._build_prompt_approche_b(item_text, item_source_key)

# APRÈS
item_title = item.get('title', '') if isinstance(item, dict) else ''
prompt = self._build_prompt_approche_b(item_text, item_source_key, item_title)
```

**Modification B - Ligne 195**:
```python
# AVANT
def _build_prompt_approche_b(self, item_text: str, item_source_key: str = None) -> str:
    variables = {'item_text': item_text}

# APRÈS
def _build_prompt_approche_b(self, item_text: str, item_source_key: str = None, item_title: str = "") -> str:
    variables = {'item_text': item_text, 'item_title': item_title}
```

**Fichier 2**: `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Modification - Ligne 1** (ajouter après imports):
```python
# Ajouter après ligne 8
_exclusion_scopes_cache = None

def initialize_exclusion_scopes(s3_io, config_bucket: str):
    global _exclusion_scopes_cache
    try:
        scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/exclusion_scopes.yaml')
        _exclusion_scopes_cache = scopes or {}
        logger.info(f"Exclusion scopes chargés: {len(_exclusion_scopes_cache)} catégories")
    except Exception as e:
        logger.warning(f"Échec chargement exclusion_scopes: {e}")
        _exclusion_scopes_cache = {}

def _get_exclusion_terms() -> List[str]:
    if not _exclusion_scopes_cache:
        return EXCLUSION_KEYWORDS
    terms = []
    for scope in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
        terms.extend(_exclusion_scopes_cache.get(scope, []))
    return terms if terms else EXCLUSION_KEYWORDS
```

**Modification - Ligne 150** (modifier fonction):
```python
# AVANT
def _contains_exclusion_keywords(text: str) -> bool:
    for keyword in EXCLUSION_KEYWORDS:

# APRÈS
def _contains_exclusion_keywords(text: str) -> bool:
    exclusion_terms = _get_exclusion_terms()
    for keyword in exclusion_terms:
```

**Fichier 3**: `src_v2/vectora_core/ingest/__init__.py`

**Modification - Ligne 10**:
```python
# AVANT
from .ingestion_profiles import apply_ingestion_profile

# APRÈS
from .ingestion_profiles import apply_ingestion_profile, initialize_exclusion_scopes

# Dans run_ingest_for_client, ajouter AVANT boucle sources:
initialize_exclusion_scopes(s3_io, config_bucket)
```

#### Étape 0.5: Commit AVANT Build (2min)

```bash
git add VERSION canonical/ src_v2/
git commit -m "fix: corrections post E2E V15

- Restaurer détection companies (ref scope)
- Extraire dosing intervals depuis titre
- Bloquer hallucination injectables and devices
- Classifier grants comme partnerships
- Ajouter rule_7 pure_player + partnership
- Charger exclusion_scopes depuis S3

Versions: vectora-core 1.4.2, canonical 2.3"
```

---

### PHASE 1: Tests Locaux Complets (1h)

### PHASE 1: Tests Locaux Complets (1h)

#### Étape 1.1: Tests Unitaires (20min)

```bash
# Créer tests si nécessaire
mkdir -p tests/unit

# Test 1: Companies
cat > tests/unit/test_companies_v16.py << 'EOF'
def test_companies_with_ref():
    # Vérifier extraction companies avec ref scope
    assert 'MedinCell' in result['companies_detected']
EOF

# Exécuter
pytest tests/unit/test_*_v16.py -v
# Attendu: PASSED
```

#### Étape 1.2: Test E2E Local (30min)

```bash
# Créer contexte test
python tests/local/test_e2e_runner.py --new-context "V16 Corrections"

# Exécuter test E2E local
python tests/local/test_e2e_runner.py --run

# Analyser résultats détaillés
python tests/local/test_e2e_runner.py --analyze
```

**Fichier généré**: `tests/contexts/local/test_v16_corrections_001/analysis_detailed.md`

**Validations attendues**:

```markdown
## Validation 1: Companies Détectées
- Item MedinCell: companies=["MedinCell"] ✅ (vs [] en V15)
- Item Teva: companies=["Teva", "MedinCell"] ✅

## Validation 2: Quince Matché
- Dosing: ["once-monthly"] ✅ (détecté depuis titre)
- Score: 65 ✅ (vs 0 en V15)

## Validation 3: Eli Lilly Rejeté
- Technologies: [] ✅ (hallucination bloquée)
- Score: 0 ✅ (vs 65 en V15)

## Validation 4: MedinCell Grant Matché
- Event type: "partnership" ✅ (vs financial_results)
- Score: 65 ✅ (rule_7 appliquée)

## Validation 5: Filtrage Ingestion
- Items filtrés: 3-6 ✅ (RH/financial)
- Items ingérés: 23-26 ✅ (vs 29 en V15)

## Validation 6: Items Relevant
- Relevant: 14-15 (58-62%) ✅ (vs 12/41% en V15)
```

#### Étape 1.3: Décision GO/NO-GO (10min)

```bash
# Vérifier checklist
cat tests/contexts/local/test_v16_corrections_001/analysis_detailed.md | grep "✅"

# SI 6/6 validations ✅
echo "✅ GO pour deploy AWS"

# SI 1+ validation ❌
echo "❌ NO-GO - Corriger et re-tester"
exit 1
```

---

### PHASE 2: Deploy AWS (SI GO) (45min)

#### Étape 2.1: Build (10min)

```bash
python scripts/build/build_all.py
```

**Résultat attendu**:
```
✅ Layer vectora-core-1.4.2.zip créé
✅ Layer common-deps-1.0.5.zip créé
```

#### Étape 2.2: Deploy Dev (15min)

```bash
python scripts/deploy/deploy_env.py --env dev
```

**Résultat attendu**:
```
✅ Layer vectora-core-1.4.2 publié: arn:aws:lambda:...
✅ Lambda ingest-v2 mise à jour
✅ Lambda normalize-score-v2 mise à jour
✅ Lambda newsletter-v2 mise à jour
```

#### Étape 2.3: Upload Canonical (10min)

```bash
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3
```

**Résultat attendu**:
```
upload: canonical/prompts/normalization/generic_normalization.yaml
upload: canonical/prompts/domain_scoring/lai_domain_scoring.yaml
upload: canonical/domains/lai_domain_definition.yaml
```

#### Étape 2.4: Créer Client AWS (Auto) (5min)

```bash
python tests/aws/test_e2e_runner.py --promote "V16 Corrections"
```

**Résultat attendu**:
```
✅ Client créé: lai_weekly_v16
📄 Config: client-config-examples/production/lai_weekly_v16.yaml
📤 Uploadé: s3://vectora-inbox-config-dev/clients/lai_weekly_v16.yaml
```

#### Étape 2.5: Test E2E AWS (5min)

```bash
python tests/aws/test_e2e_runner.py --run
```

---

### PHASE 3: Validation AWS (30min)

#### Étape 3.1: Télécharger Résultats (5min)

```bash
aws s3 sync s3://vectora-inbox-data-dev/clients/lai_weekly_v16/ \
  .tmp/e2e_v16_aws/ \
  --profile rag-lai-prod --region eu-west-3
```

#### Étape 3.2: Analyser Résultats AWS (10min)

```bash
python tests/aws/test_e2e_runner.py --analyze
```

**Fichier généré**: `.tmp/e2e_v16_aws/analysis_detailed.md`

#### Étape 3.3: Comparer Local vs AWS (10min)

```bash
python scripts/analysis/compare_local_aws.py \
  --local tests/contexts/local/test_v16_corrections_001/ \
  --aws .tmp/e2e_v16_aws/
```

**Résultat attendu**:
```
Comparaison Local vs AWS V16
============================

Items ingérés:     Local 24 | AWS 24 | Diff 0 ✅
Companies:         Local 7  | AWS 7  | Diff 0 ✅
Items relevant:    Local 14 | AWS 14 | Diff 0 ✅

Validations:
  Quince matché:         Local ✅ | AWS ✅
  Eli Lilly rejeté:      Local ✅ | AWS ✅
  MedinCell grant:       Local ✅ | AWS ✅

Verdict: ✅ REPRODUCTIBILITÉ PARFAITE
```

#### Étape 3.4: Validation Finale (5min)

**Critères de succès**:

| Critère | V15 | V16 | Statut |
|---------|-----|-----|--------|
| Items ingérés | 29 | 23-26 | ✅ |
| Items relevant | 12 (41%) | 14-15 (58%) | ✅ |
| Companies | 0 | 7 | ✅ |
| Faux positifs | 1 | 0 | ✅ |
| Faux négatifs | 2 | 0 | ✅ |

---

### PHASE 4: Git et Documentation (15min)

#### Étape 4.1: Push Branche (5min)

```bash
git push origin fix/v16-corrections-post-e2e-v15
```

#### Étape 4.2: Pull Request (5min)

**Titre**: `fix: Corrections post E2E V15 - companies, dosing, grants, filtrage`

**Description**:
```markdown
## Corrections

- [x] Restaurer détection companies
- [x] Extraire dosing depuis titre
- [x] Bloquer hallucination injectables
- [x] Classifier grants comme partnerships
- [x] Ajouter rule_7 pure_player
- [x] Charger exclusion_scopes S3

## Tests

- [x] Tests locaux: 6/6 ✅
- [x] Tests AWS: 6/6 ✅
- [x] Reproductibilité: Local=AWS ✅

## Métriques

| Métrique | V15 | V16 | Évolution |
|----------|-----|-----|--------|
| Items relevant | 12 (41%) | 14 (58%) | +17% |
| Companies | 0 | 7 | ✅ |
| Faux positifs | 1 | 0 | ✅ |

Versions: vectora-core 1.4.2, canonical 2.3
```

#### Étape 4.3: Tag Version (5min)

```bash
# Après merge dans develop
git checkout develop
git pull origin develop
git tag v2.3.0 -m "V16: Corrections post E2E V15"
git push origin v2.3.0
```

---

## ✅ CHECKLIST COMPLÈTE

### Phase 0: Préparation
- [ ] Branche créée
- [ ] VERSION incrémentée
- [ ] Modifications canonical appliquées (4 fichiers)
- [ ] Modifications code Python appliquées (3 fichiers)
- [ ] Commit AVANT build ✅

### Phase 1: Tests Locaux
- [ ] Tests unitaires: 5/5 PASSED
- [ ] Test E2E local exécuté
- [ ] Analyse détaillée générée
- [ ] 6/6 validations ✅
- [ ] Décision GO ✅

### Phase 2: Deploy AWS
- [ ] Build layers
- [ ] Deploy dev
- [ ] Upload canonical
- [ ] Client V16 créé (auto)
- [ ] Test E2E AWS exécuté

### Phase 3: Validation AWS
- [ ] Résultats téléchargés
- [ ] Analyse AWS générée
- [ ] Comparaison Local/AWS
- [ ] Reproductibilité validée ✅

### Phase 4: Git
- [ ] Branche pushée
- [ ] Pull Request créée
- [ ] Tag version créé

---

## 📊 RÉSUMÉ FINAL

**Durée totale**: 3h15
- Phase 0 (Préparation): 1h
- Phase 1 (Tests locaux): 1h
- Phase 2 (Deploy AWS): 45min
- Phase 3 (Validation): 30min
- Phase 4 (Git): 15min

**Conformité**: ✅ 100% CRITICAL_RULES
- ✅ Git AVANT build
- ✅ VERSION incrémentée
- ✅ Tests local AVANT AWS
- ✅ Client auto-généré
- ✅ Environnement explicite

**Impact attendu**:
- Items relevant: +17% (41% → 58%)
- Companies détectées: Restauré (0 → 7)
- Faux positifs: -100% (1 → 0)
- Faux négatifs: -100% (2 → 0)

---

**Plan créé**: 2026-02-03  
**Statut**: ✅ PRÊT POUR EXÉCUTION  
**Un seul plan, 4 phases séquentielles**ofiles.py`.

**Fichier**: `src_v2/vectora_core/ingest/ingestion_profiles.py`

**Modification ligne 1-20** (ajouter imports et fonction de chargement):
```python
"""
Profils d'ingestion pour Vectora Inbox V2.
"""

from typing import Any, Dict, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

# Variables globales pour scopes chargés depuis S3
_exclusion_scopes_cache = None
_s3_io = None
_config_bucket = None

def initialize_exclusion_scopes(s3_io, config_bucket: str):
    """Charge les exclusion_scopes depuis S3 (appelé au démarrage)."""
    global _exclusion_scopes_cache, _s3_io, _config_bucket
    _s3_io = s3_io
    _config_bucket = config_bucket
    
    try:
        scopes = s3_io.read_yaml_from_s3(config_bucket, 'canonical/scopes/exclusion_scopes.yaml')
        _exclusion_scopes_cache = scopes or {}
        logger.info(f"Exclusion scopes chargés: {len(_exclusion_scopes_cache)} catégories")
    except Exception as e:
        logger.warning(f"Échec chargement exclusion_scopes: {e}. Utilisation fallback.")
        _exclusion_scopes_cache = {}

def _get_exclusion_terms() -> List[str]:
    """Retourne la liste combinée des termes d'exclusion depuis S3."""
    if not _exclusion_scopes_cache:
        # Fallback sur keywords hardcodés
        return EXCLUSION_KEYWORDS
    
    # Combiner hr_content, financial_generic, hr_recruitment_terms, financial_reporting_terms
    terms = []
    for scope_name in ['hr_content', 'financial_generic', 'hr_recruitment_terms', 'financial_reporting_terms']:
        scope_terms = _exclusion_scopes_cache.get(scope_name, [])
        terms.extend(scope_terms)
    
    return terms if terms else EXCLUSION_KEYWORDS

# Mots-clés LAI pour filtrage de la presse (inchangé)
LAI_KEYWORDS = [
    # ... (garder existant)
]

# Mots-clés d'exclusion FALLBACK (si S3 échoue)
EXCLUSION_KEYWORDS = [
    # ... (garder existant)
]
```

**Modification ligne 150-160** (fonction `_contains_exclusion_keywords`):
```python
# AVANT
def _contains_exclusion_keywords(text: str) -> bool:
    """
    Vérifie si le texte contient des mots-clés d'exclusion.
    """
    text_lower = text.lower()
    
    for keyword in EXCLUSION_KEYWORDS:
        if keyword.lower() in text_lower:
            return True
    
    return False

# APRÈS
def _contains_exclusion_keywords(text: str) -> bool:
    """
    Vérifie si le texte contient des mots-clés d'exclusion (depuis S3 ou fallback).
    """
    text_lower = text.lower()
    exclusion_terms = _get_exclusion_terms()
    
    for keyword in exclusion_terms:
        if keyword.lower() in text_lower:
            logger.debug(f"Exclusion détectée: '{keyword}' dans texte")
            return True
    
    return False
```

**Fichier 2**: `src_v2/vectora_core/ingest/__init__.py`

**Modification** (ajouter initialisation):
```python
# AVANT (ligne ~10)
from .source_fetcher import fetch_from_source
from .content_parser import parse_content
from .ingestion_profiles import apply_ingestion_profile

# APRÈS
from .source_fetcher import fetch_from_source
from .content_parser import parse_content
from .ingestion_profiles import apply_ingestion_profile, initialize_exclusion_scopes

# Dans run_ingest_for_client (ligne ~50), ajouter AVANT la boucle sources:
def run_ingest_for_client(...):
    # ... (code existant)
    
    # Initialiser exclusion scopes depuis S3
    from .ingestion_profiles import initialize_exclusion_scopes
    initialize_exclusion_scopes(s3_io, config_bucket)
    
    # ... (continuer avec boucle sources)
```

**Test de validation**:
```bash
# Relancer ingestion
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v16

# Vérifier logs:
# Attendu: "Exclusion scopes chargés: 4 catégories"
# Attendu: Items RH/financial filtrés AVANT ingestion
# Attendu: -3 à -6 items ingérés (filtrage effectif)
```

---

### PHASE 3: Build, Deploy et Test E2E (30min)

#### Étape 3.1: Upload Configs Canonical (5min)

```bash
# Upload tous les fichiers canonical modifiés
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3 \
  --exclude "*" \
  --include "prompts/normalization/generic_normalization.yaml" \
  --include "prompts/domain_scoring/lai_domain_scoring.yaml" \
  --include "domains/lai_domain_definition.yaml"
```

#### Étape 3.2: Rebuild et Redeploy Layer Vectora-Core (15min)

```bash
# Build layer avec code modifié
python scripts/build/build_all.py

# Deploy layer + lambdas sur dev
python scripts/deploy/deploy_env.py --env dev
```

#### Étape 3.3: Créer et Upload Client V16 (5min)

```bash
# Créer config client V16
cp client-config-examples/production/lai_weekly_v15.yaml \
   client-config-examples/production/lai_weekly_v16.yaml

# Modifier dans lai_weekly_v16.yaml:
# - client_id: lai_weekly_v16
# - template_version: "16.0.0"

# Upload client V16
aws s3 cp client-config-examples/production/lai_weekly_v16.yaml \
  s3://vectora-inbox-config-dev/clients/ \
  --profile rag-lai-prod --region eu-west-3
```

#### Étape 3.4: Lancer Test E2E V16 (5min)

```bash
# Lancer pipeline complet
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v16

# Attendre fin exécution (~3-4 min)
# Télécharger résultats depuis S3
```

---

## ✅ CRITÈRES DE SUCCÈS V16

### Métriques Quantitatives

| Métrique | V15 (Avant) | V16 (Cible) | Validation |
|----------|-------------|-------------|------------|
| **Items ingérés** | 29 | 23-26 | Filtrage RH/financial effectif |
| **Items relevant** | 12 (41%) | ≥14 (≥54%) | Retour niveau V13 |
| **Score moyen** | 81.7 | ≥85 | Amélioration qualité |
| **Companies détectées** | 0 | >5 | Restauré |
| **Faux positifs** | 1 | 0 | Eli Lilly rejeté |
| **Faux négatifs** | 2 | 0 | Quince + MedinCell matchés |

### Validations Qualitatives

#### ✅ Validation 1: Companies Détectées
```json
// Dans items_normalized.json, vérifier:
{
  "normalized_content": {
    "entities": {
      "companies": ["MedinCell", "Teva", "Novo Nordisk", ...]  // NON VIDE
    }
  }
}
```

#### ✅ Validation 2: Quince Matché
```json
// Item Quince dans items_normalized.json:
{
  "title": "Quince's steroid therapy...",
  "normalized_content": {
    "entities": {
      "dosing_intervals": ["once-monthly"]  // DÉTECTÉ
    }
  },
  "final_score": 65  // ≥60 (matché)
}
```

#### ✅ Validation 3: Eli Lilly Rejeté
```json
// Item Eli Lilly manufacturing:
{
  "title": "Lilly rounds out quartet of new US plants...",
  "final_score": 0,  // REJETÉ
  "reasoning": "Manufacturing without LAI technology"
}
```

#### ✅ Validation 4: MedinCell Grant Matché
```json
// Item MedinCell malaria grant:
{
  "title": "Medincell Awarded New Grant to Fight Malaria",
  "normalized_content": {
    "event_type": "partnership"  // PAS financial_results
  },
  "final_score": 65,  // ≥60 (matché)
  "reasoning": "Pure player + partnership (rule_7)"
}
```

#### ✅ Validation 5: Filtrage Ingestion
```bash
# Dans logs Lambda ingest-v2, vérifier:
# "Exclusion scopes chargés: 4 catégories"
# "Item exclu (bruit): Medincell Appoints Dr Grace Kim..."
# "Item exclu (bruit): Publication of the 2026 financial calendar"
# "Profil corporate LAI : 5/8 items conservés"  # 3 items RH/financial filtrés
```

---

## 📊 IMPACT ATTENDU

### Gains Qualité

| Aspect | Amélioration |
|--------|--------------|
| **Précision** | 0 faux positifs, 0 faux négatifs |
| **Rappel** | +2 items pertinents (Quince, MedinCell grant) |
| **Détection entités** | Companies restaurées (+5-7 companies/run) |
| **Classification** | Grants correctement classés comme partnerships |

### Gains Efficacité

| Aspect | Amélioration |
|--------|--------------|
| **Coûts Bedrock** | -20% appels (filtrage ingestion) |
| **Temps exécution** | -15% (moins d'items à normaliser) |
| **Qualité données** | +30% items relevant (41% → 54%) |

### Gains Architecture

| Aspect | Amélioration |
|--------|--------------|
| **Conformité** | Utilisation exclusion_scopes.yaml depuis S3 |
| **Maintenabilité** | Exclusions centralisées dans canonical |
| **Évolutivité** | Ajout facile de nouveaux termes d'exclusion |

---

## 📁 FICHIERS MODIFIÉS (RÉCAPITULATIF)

### Canonical (4 fichiers)
1. `canonical/prompts/normalization/generic_normalization.yaml` (lignes 17, 38, 54, 62)
2. `canonical/prompts/domain_scoring/lai_domain_scoring.yaml` (ligne 11)
3. `canonical/domains/lai_domain_definition.yaml` (lignes 167, 189)

### Code Python (2 fichiers)
4. `src_v2/vectora_core/normalization/bedrock_client.py` (lignes 145, 195)
5. `src_v2/vectora_core/ingest/ingestion_profiles.py` (lignes 1-20, 150-160)
6. `src_v2/vectora_core/ingest/__init__.py` (ligne ~50)

### Client Config (1 fichier)
7. `client-config-examples/production/lai_weekly_v16.yaml` (nouveau)

---

## 🚀 COMMANDES COMPLÈTES

```bash
# 1. Upload canonical
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3

# 2. Build + Deploy
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 3. Upload client V16
aws s3 cp client-config-examples/production/lai_weekly_v16.yaml \
  s3://vectora-inbox-config-dev/clients/ \
  --profile rag-lai-prod --region eu-west-3

# 4. Test E2E
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v16

# 5. Analyser résultats
python .tmp/e2e_v16/generate_analysis.py
```

---

## 📋 CHECKLIST EXÉCUTION

### Avant Modifications
- [ ] Backup des fichiers canonical actuels
- [ ] Snapshot de l'environnement dev actuel
- [ ] Vérifier que V15 est stable

### Modifications
- [ ] Action 1.1: Companies (generic_normalization.yaml)
- [ ] Action 1.2: Dosing intervals (generic_normalization.yaml + bedrock_client.py)
- [ ] Action 1.3: Hallucination (lai_domain_scoring.yaml + lai_domain_definition.yaml)
- [ ] Action 2.1: Event type (generic_normalization.yaml)
- [ ] Action 2.2: Rule_7 (lai_domain_definition.yaml)
- [ ] Action 2.3: Filtrage ingestion (ingestion_profiles.py + __init__.py)

### Déploiement
- [ ] Upload canonical vers S3
- [ ] Build layer vectora-core
- [ ] Deploy layer + lambdas
- [ ] Créer client V16
- [ ] Upload client V16

### Validation
- [ ] Test E2E V16 exécuté
- [ ] Companies détectées: >5 ✅
- [ ] Quince matché ✅
- [ ] Eli Lilly rejeté ✅
- [ ] MedinCell grant matché ✅
- [ ] Items RH/financial filtrés ✅
- [ ] Items relevant: ≥14 (≥54%) ✅

---

**Plan créé**: 2026-02-03  
**Durée estimée**: 4h  
**Statut**: ✅ PRÊT POUR EXÉCUTION  
**Option choisie**: Option B (filtrage ingestion propre avec exclusion_scopes.yaml)
