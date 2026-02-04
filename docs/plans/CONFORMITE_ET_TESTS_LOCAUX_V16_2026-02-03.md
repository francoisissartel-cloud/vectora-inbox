# Conformité et Tests Locaux V16 - Ajustements Critiques

**Date**: 2026-02-03  
**Base**: plan_amelioration_strategique_post_e2e_v15_EXECUTABLE_2026-02-03.md  
**Objectif**: Assurer conformité CRITICAL_RULES + Tests locaux complets

---

## 🚨 NON-CONFORMITÉS DÉTECTÉES

### ❌ Non-Conformité 1: Git AVANT Build (Règle #3)

**Plan actuel**:
```bash
# Modifications → Build → Deploy → Test
```

**Règle critique violée**: "Git AVANT Build"

**Correction requise**:
```bash
# 1. Créer branche
git checkout -b fix/v16-corrections-post-e2e-v15

# 2. Modifier fichiers
# ... (toutes les modifications)

# 3. COMMIT AVANT BUILD
git add canonical/ src_v2/ VERSION
git commit -m "fix: corrections post E2E V15 - companies, dosing, grants, filtrage"

# 4. Build
python scripts/build/build_all.py

# 5. Deploy
python scripts/deploy/deploy_env.py --env dev
```

---

### ❌ Non-Conformité 2: VERSION Non Incrémentée (Règle Gouvernance)

**Plan actuel**: Aucune mention de VERSION

**Fichier VERSION actuel**:
```ini
VECTORA_CORE_VERSION=1.4.1
CANONICAL_VERSION=2.2
NORMALIZE_VERSION=2.1.0
INGEST_VERSION=1.5.0
```

**Corrections requises**:
- `VECTORA_CORE_VERSION`: 1.4.1 → **1.4.2** (PATCH: corrections bedrock_client.py + ingestion_profiles.py)
- `CANONICAL_VERSION`: 2.2 → **2.3** (MINOR: ajout rule_7 + amélioration prompts)
- `NORMALIZE_VERSION`: 2.1.0 → **2.1.1** (PATCH: correction extraction titre)
- `INGEST_VERSION`: 1.5.0 → **1.5.1** (PATCH: chargement exclusion_scopes)

**Action**:
```bash
# Modifier VERSION AVANT commit
nano VERSION
```

---

### ❌ Non-Conformité 3: Tests Local AVANT AWS (Règle #6)

**Plan actuel**: Saute directement à deploy AWS

**Règle critique violée**: "Tests Local AVANT AWS"

**Correction requise**: Ajouter Phase 0 complète avec tests locaux détaillés

---

### ❌ Non-Conformité 4: Client Config Manuel (Règle #7)

**Plan actuel**:
```bash
cp lai_weekly_v15.yaml lai_weekly_v16.yaml
# Modifier manuellement
```

**Règle critique violée**: "Client Config Auto-Généré"

**Correction requise**: Utiliser test runner pour génération automatique

---

## ✅ WORKFLOW CONFORME COMPLET

### PHASE 0: Tests Locaux Complets (2h)

#### Étape 0.1: Créer Branche Git (2min)

```bash
git checkout develop
git pull origin develop
git checkout -b fix/v16-corrections-post-e2e-v15
```

#### Étape 0.2: Appliquer Modifications (1h)

**Ordre strict**:
1. Modifier `VERSION` (incrémenter versions)
2. Modifier fichiers canonical (4 fichiers)
3. Modifier code Python (3 fichiers)
4. Commit AVANT build

```bash
# 1. VERSION
nano VERSION
# VECTORA_CORE_VERSION=1.4.2
# CANONICAL_VERSION=2.3
# NORMALIZE_VERSION=2.1.1
# INGEST_VERSION=1.5.1

# 2. Canonical
nano canonical/prompts/normalization/generic_normalization.yaml
nano canonical/prompts/domain_scoring/lai_domain_scoring.yaml
nano canonical/domains/lai_domain_definition.yaml

# 3. Code Python
nano src_v2/vectora_core/normalization/bedrock_client.py
nano src_v2/vectora_core/ingest/ingestion_profiles.py
nano src_v2/vectora_core/ingest/__init__.py

# 4. COMMIT AVANT BUILD
git add VERSION canonical/ src_v2/
git commit -m "fix: corrections post E2E V15

- Restaurer détection companies (ref scope)
- Extraire dosing intervals depuis titre
- Bloquer hallucination injectables and devices
- Classifier grants comme partnerships
- Ajouter rule_7 pure_player + partnership
- Charger exclusion_scopes depuis S3

Closes #XXX"
```

#### Étape 0.3: Tests Locaux Unitaires (30min)

**Test 1: Extraction Companies**

```python
# tests/unit/test_normalization_companies_v16.py
import pytest
from vectora_core.normalization import BedrockNormalizationClient

def test_companies_extraction_with_scope_ref():
    """Vérifie que companies sont extraites avec référence scope."""
    # Setup
    item_text = "MedinCell announces partnership with Teva for UZEDY commercialization"
    
    # Execute
    result = normalize_item(item_text)
    
    # Assert
    assert len(result['companies_detected']) > 0
    assert 'MedinCell' in result['companies_detected']
    assert 'Teva' in result['companies_detected']
```

**Test 2: Dosing Intervals depuis Titre**

```python
# tests/unit/test_normalization_dosing_title_v16.py
def test_dosing_intervals_from_title():
    """Vérifie extraction dosing depuis titre."""
    # Setup
    item_title = "Quince's once-monthly steroid therapy fails"
    item_text = "The company announced failure of trial..."
    
    # Execute
    result = normalize_item(item_text, item_title=item_title)
    
    # Assert
    assert 'once-monthly' in result['dosing_intervals_detected']
```

**Test 3: Exclusion Injectables and Devices**

```python
# tests/unit/test_scoring_exclusions_v16.py
def test_reject_generic_injectables():
    """Vérifie rejet manufacturing sans tech LAI."""
    # Setup
    item = {
        'title': 'Lilly rounds out quartet of new US plants',
        'normalized_content': {
            'entities': {
                'technologies': ['injectables and devices']
            }
        }
    }
    
    # Execute
    score = score_item(item)
    
    # Assert
    assert score['final_score'] == 0
    assert 'manufacturing without LAI technology' in score['reasoning'].lower()
```

**Test 4: Classification Grants**

```python
# tests/unit/test_normalization_event_type_v16.py
def test_grant_classified_as_partnership():
    """Vérifie que grants sont classés comme partnerships."""
    # Setup
    item_text = "MedinCell awarded $5M grant for malaria research"
    
    # Execute
    result = normalize_item(item_text)
    
    # Assert
    assert result['event_type'] == 'partnership'
```

**Test 5: Rule_7 Pure Player + Partnership**

```python
# tests/unit/test_scoring_rule7_v16.py
def test_pure_player_partnership_auto_match():
    """Vérifie rule_7: pure_player + partnership → match."""
    # Setup
    item = {
        'normalized_content': {
            'event_type': 'partnership',
            'entities': {
                'companies': ['MedinCell']
            }
        }
    }
    
    # Execute
    score = score_item(item)
    
    # Assert
    assert score['final_score'] >= 60
    assert 'rule_7' in score['reasoning'].lower()
```

**Exécution tests**:
```bash
pytest tests/unit/test_*_v16.py -v
# Attendu: 5/5 tests PASSED
```

#### Étape 0.4: Test E2E Local Complet (30min)

**Créer contexte test local**:
```bash
python tests/local/test_e2e_runner.py --new-context "V16 Corrections Post E2E V15"
```

**Résultat attendu**:
```
✅ Contexte créé: test_v16_corrections_001
📁 Dossier: tests/contexts/local/test_v16_corrections_001/
📄 Client config: lai_weekly_test_v16_corrections_001.yaml
```

**Exécuter test E2E local**:
```bash
python tests/local/test_e2e_runner.py --run
```

**Analyse détaillée item par item** (comme E2E V15):

```bash
# Générer analyse détaillée
python tests/local/test_e2e_runner.py --analyze

# Fichier généré: tests/contexts/local/test_v16_corrections_001/analysis_detailed.md
```

**Contenu attendu analysis_detailed.md**:

```markdown
# Test E2E Local V16 - Analyse Détaillée Item par Item

## Items Ingérés: 23-26 (vs 29 en V15)

### Items Filtrés à l'Ingestion (3-6 items)

1. **MedinCell Appoints Dr Grace Kim** - ❌ FILTRÉ
   - Raison: Exclusion "appoints" détectée (hr_content)
   - Attendu: ✅ CORRECT (bruit RH)

2. **Publication of 2026 financial calendar** - ❌ FILTRÉ
   - Raison: Exclusion "financial calendar" détectée (financial_reporting_terms)
   - Attendu: ✅ CORRECT (bruit financial)

3. **MedinCell Publishes Consolidated Half-Year Results** - ❌ FILTRÉ
   - Raison: Exclusion "half-year results" détectée (financial_reporting_terms)
   - Attendu: ✅ CORRECT (bruit financial)

---

## Items Normalisés: 23-26

### Validation 1: Companies Détectées

**Item 1: Teva/MedinCell NDA**
```json
{
  "title": "Teva and MedinCell Announce FDA Acceptance...",
  "normalized_content": {
    "entities": {
      "companies": ["Teva", "MedinCell"],  // ✅ DÉTECTÉ (vs [] en V15)
      "dosing_intervals": ["once-monthly"],
      "trademarks": ["TEV-'749"]
    }
  }
}
```
- Companies: ✅ **RESTAURÉ** (2 companies vs 0 en V15)
- Dosing: ✅ Détecté
- Attendu: ✅ SUCCÈS

**Item 2: Camurus Oclaiz**
```json
{
  "title": "Camurus Receives FDA Approval for Oclaiz...",
  "normalized_content": {
    "entities": {
      "companies": ["Camurus"],  // ✅ DÉTECTÉ
      "trademarks": ["Oclaiz™"]
    }
  }
}
```
- Companies: ✅ **RESTAURÉ**
- Attendu: ✅ SUCCÈS

---

### Validation 2: Dosing Intervals depuis Titre

**Item 3: Quince Steroid (FAUX NÉGATIF V15)**
```json
{
  "title": "Quince's once-monthly steroid therapy for rare disease fails",
  "normalized_content": {
    "entities": {
      "dosing_intervals": ["once-monthly"]  // ✅ DÉTECTÉ (vs [] en V15)
    },
    "event_type": "clinical_update"
  },
  "final_score": 65,  // ✅ MATCHÉ (vs 0 en V15)
  "reasoning": "Dosing interval detected + clinical update"
}
```
- Dosing: ✅ **CORRIGÉ** (détecté depuis titre)
- Score: ✅ **MATCHÉ** (65 vs 0)
- Attendu: ✅ SUCCÈS

---

### Validation 3: Exclusion "injectables and devices"

**Item 4: Eli Lilly Manufacturing (FAUX POSITIF V15)**
```json
{
  "title": "Lilly rounds out quartet of new US plants...",
  "normalized_content": {
    "entities": {
      "companies": ["Eli Lilly"],  // ✅ DÉTECTÉ
      "technologies": []  // ✅ "injectables and devices" NON détecté
    },
    "event_type": "corporate_move"
  },
  "final_score": 0,  // ✅ REJETÉ (vs 65 en V15)
  "reasoning": "Manufacturing facility without LAI technology (rule_6)"
}
```
- Technologies: ✅ **CORRIGÉ** (hallucination bloquée)
- Score: ✅ **REJETÉ** (0 vs 65)
- Attendu: ✅ SUCCÈS

---

### Validation 4: Classification Grants + Rule_7

**Item 5: MedinCell Malaria Grant (FAUX NÉGATIF V15)**
```json
{
  "title": "Medincell Awarded New Grant to Fight Malaria",
  "normalized_content": {
    "entities": {
      "companies": ["MedinCell"]  // ✅ DÉTECTÉ
    },
    "event_type": "partnership"  // ✅ CORRIGÉ (vs financial_results en V15)
  },
  "final_score": 65,  // ✅ MATCHÉ (vs 0 en V15)
  "reasoning": "Pure player + partnership (rule_7)"
}
```
- Event type: ✅ **CORRIGÉ** (partnership vs financial_results)
- Score: ✅ **MATCHÉ** (rule_7 appliquée)
- Attendu: ✅ SUCCÈS

---

## Résumé Validations

| Validation | V15 | V16 Local | Statut |
|------------|-----|-----------|--------|
| Companies détectées | 0 | 7 | ✅ RESTAURÉ |
| Quince matché | ❌ | ✅ | ✅ CORRIGÉ |
| Eli Lilly rejeté | ❌ | ✅ | ✅ CORRIGÉ |
| MedinCell grant matché | ❌ | ✅ | ✅ CORRIGÉ |
| Items filtrés ingestion | 0 | 3-6 | ✅ NOUVEAU |
| Items relevant | 12 (41%) | 14-15 (58-62%) | ✅ AMÉLIORATION |

---

## Critères de Succès Local

- [x] Companies: >5 détectées ✅
- [x] Quince: score ≥60 ✅
- [x] Eli Lilly: score=0 ✅
- [x] MedinCell grant: score ≥60 ✅
- [x] Filtrage ingestion: 3-6 items ✅
- [x] Items relevant: ≥14 (≥54%) ✅

**Verdict**: ✅ **TOUS LES CRITÈRES VALIDÉS EN LOCAL**
```

**Décision GO/NO-GO**:
```bash
# SI analysis_detailed.md montre 6/6 validations ✅
# → GO pour deploy AWS

# SI 1+ validation ❌
# → NO-GO, corriger et re-tester local
```

---

### PHASE 1: Deploy AWS (SI GO) (30min)

#### Étape 1.1: Build (5min)

```bash
python scripts/build/build_all.py
```

#### Étape 1.2: Deploy Dev (10min)

```bash
python scripts/deploy/deploy_env.py --env dev
```

#### Étape 1.3: Upload Canonical (5min)

```bash
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3
```

#### Étape 1.4: Créer Client AWS (Auto-généré) (5min)

```bash
# Utiliser test runner pour génération automatique
python tests/aws/test_e2e_runner.py --promote "V16 Corrections Post E2E V15"
```

**Résultat attendu**:
```
✅ Client créé: lai_weekly_v16
📄 Config: client-config-examples/production/lai_weekly_v16.yaml
📤 Uploadé vers: s3://vectora-inbox-config-dev/clients/lai_weekly_v16.yaml
```

#### Étape 1.5: Test E2E AWS (5min)

```bash
python tests/aws/test_e2e_runner.py --run
```

---

### PHASE 2: Validation AWS Détaillée (30min)

**Télécharger résultats**:
```bash
aws s3 sync s3://vectora-inbox-data-dev/clients/lai_weekly_v16/ \
  .tmp/e2e_v16_aws/ \
  --profile rag-lai-prod --region eu-west-3
```

**Générer analyse détaillée**:
```bash
python tests/aws/test_e2e_runner.py --analyze
```

**Comparer Local vs AWS**:
```bash
python scripts/analysis/compare_local_aws.py \
  --local tests/contexts/local/test_v16_corrections_001/ \
  --aws .tmp/e2e_v16_aws/
```

**Résultat attendu**:
```
Comparaison Local vs AWS V16
=============================

Items ingérés:
  Local: 24
  AWS:   24
  Diff:  0 ✅

Companies détectées:
  Local: 7
  AWS:   7
  Diff:  0 ✅

Items relevant:
  Local: 14 (58%)
  AWS:   14 (58%)
  Diff:  0 ✅

Validations critiques:
  Quince matché:         Local ✅ | AWS ✅
  Eli Lilly rejeté:      Local ✅ | AWS ✅
  MedinCell grant matché: Local ✅ | AWS ✅

Verdict: ✅ LOCAL = AWS (reproductibilité parfaite)
```

---

### PHASE 3: Git et Documentation (15min)

#### Étape 3.1: Push Branche (5min)

```bash
git push origin fix/v16-corrections-post-e2e-v15
```

#### Étape 3.2: Créer Pull Request (5min)

**Titre**: `fix: Corrections post E2E V15 - companies, dosing, grants, filtrage`

**Description**:
```markdown
## Problèmes Corrigés

### 🔴 Critique
- [x] Restaurer détection companies (ajout ref scope)
- [x] Extraire dosing intervals depuis titre
- [x] Bloquer hallucination "injectables and devices"

### 🟡 Important
- [x] Classifier grants comme partnerships
- [x] Ajouter rule_7 pure_player + partnership
- [x] Charger exclusion_scopes depuis S3

## Tests

### Local
- [x] 5/5 tests unitaires PASSED
- [x] Test E2E local: 6/6 validations ✅
- [x] Items relevant: 14/24 (58%)

### AWS Dev
- [x] Test E2E AWS: 6/6 validations ✅
- [x] Reproductibilité Local=AWS ✅

## Métriques

| Métrique | V15 | V16 | Évolution |
|----------|-----|-----|-----------|
| Items ingérés | 29 | 24 | -17% (filtrage) |
| Items relevant | 12 (41%) | 14 (58%) | +17% |
| Companies détectées | 0 | 7 | ✅ Restauré |
| Faux positifs | 1 | 0 | ✅ Corrigé |
| Faux négatifs | 2 | 0 | ✅ Corrigé |

## Versions

- VECTORA_CORE_VERSION: 1.4.1 → 1.4.2
- CANONICAL_VERSION: 2.2 → 2.3
- NORMALIZE_VERSION: 2.1.0 → 2.1.1
- INGEST_VERSION: 1.5.0 → 1.5.1

## Fichiers Modifiés

- VERSION
- canonical/prompts/normalization/generic_normalization.yaml
- canonical/prompts/domain_scoring/lai_domain_scoring.yaml
- canonical/domains/lai_domain_definition.yaml
- src_v2/vectora_core/normalization/bedrock_client.py
- src_v2/vectora_core/ingest/ingestion_profiles.py
- src_v2/vectora_core/ingest/__init__.py

Closes #XXX
```

#### Étape 3.3: Tag Version (5min)

```bash
# Après merge dans develop
git checkout develop
git pull origin develop
git tag v2.3.0 -m "V16: Corrections post E2E V15"
git push origin v2.3.0
```

---

## 📋 CHECKLIST CONFORMITÉ COMPLÈTE

### Règles Critiques

- [ ] Règle #1: Architecture 3 Lambdas V2 ✅ (respectée)
- [ ] Règle #2: Code dans src_v2/ ✅ (respectée)
- [ ] Règle #3: Git AVANT Build ✅ (corrigée)
- [ ] Règle #4: Environnement explicite ✅ (respectée)
- [ ] Règle #5: Deploy = Code + Data + Test ✅ (respectée)
- [ ] Règle #6: Tests Local AVANT AWS ✅ (ajoutée)
- [ ] Règle #7: Client Config Auto-Généré ✅ (corrigée)
- [ ] Règle #8: Bedrock us-east-1 + Sonnet ✅ (respectée)
- [ ] Règle #9: Temporaires dans .tmp/ ✅ (respectée)
- [ ] Règle #10: Blueprint à jour ⚠️ (à faire si modif architecture)

### Gouvernance

- [ ] VERSION incrémentée ✅ (ajoutée)
- [ ] Branche depuis develop ✅ (ajoutée)
- [ ] Commit AVANT build ✅ (ajoutée)
- [ ] Tests local complets ✅ (ajoutée)
- [ ] Tests AWS validation ✅ (respectée)
- [ ] Pull Request ✅ (ajoutée)
- [ ] Tag version ✅ (ajoutée)

---

## 🎯 RÉSUMÉ AJUSTEMENTS

### Ajouts Critiques

1. **Phase 0 complète**: Tests locaux détaillés item par item
2. **Workflow Git**: Branche → Commit → Build → Deploy
3. **VERSION**: Incrémentation versions (1.4.2, 2.3, 2.1.1, 1.5.1)
4. **Client auto-généré**: Utilisation test runners
5. **Comparaison Local/AWS**: Validation reproductibilité

### Durée Totale Ajustée

- Phase 0 (Tests locaux): 2h
- Phase 1 (Deploy AWS): 30min
- Phase 2 (Validation AWS): 30min
- Phase 3 (Git/Doc): 15min

**Total**: 3h15 (vs 4h plan initial)

---

**Document créé**: 2026-02-03  
**Statut**: ✅ CONFORME CRITICAL_RULES + Tests locaux complets  
**Prêt pour exécution**: OUI
