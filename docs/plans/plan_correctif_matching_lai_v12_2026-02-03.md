# Plan Correctif - Matching LAI Weekly v12

**Date**: 2026-02-03  
**Objectif**: Corriger le problème de matching (0% → 60-80%) avec approche scalable  
**Basé sur**: diagnostic_matching_lai_weekly_v11_2026-02-03.md  
**Option validée**: Option 1 - Créer lai_domain_definition.yaml

---

## 🎯 OBJECTIFS

### Objectifs Immédiats (Phase 1)
- ✅ Débloquer le matching (0% → >50%)
- ✅ Newsletter fonctionnelle avec 10-15 items pertinents
- ✅ Architecture scalable pour amélioration continue

### Objectifs Long Terme (Phases 2-3)
- ✅ Système d'amélioration continue des prompts
- ✅ Métriques de qualité trackées par version
- ✅ Workflow d'ajustement sans redéploiement code
- ✅ Documentation des learnings E2E

---

## 📋 PHASE 1: CORRECTION IMMÉDIATE (Jour 1)

### Étape 1.1: Créer Domain Definition (2h)

**Fichier**: `canonical/scopes/domain_definitions.yaml`

**Action**: Créer fichier avec structure scalable

```yaml
# Domain Definitions - Matching and Scoring Rules
# Version: 1.0.0
# Last Updated: 2026-02-03
# 
# ÉVOLUTION: Ce fichier sera enrichi au fil des tests E2E
# - Ajouter signaux détectés dans les faux négatifs
# - Retirer signaux générant du bruit (faux positifs)
# - Ajuster scores basés sur feedback utilisateur

lai_domain_definition:
  _metadata:
    version: "1.0.0"
    description: "LAI domain definition for matching and scoring"
    last_updated: "2026-02-03"
    changelog:
      - version: "1.0.0"
        date: "2026-02-03"
        changes: "Initial version - baseline from diagnostic"
        test_run: "lai_weekly_v12"
  
  # SIGNAUX FORTS (high confidence match)
  # Source: Scopes canonical existants via références dynamiques
  core_technologies:
    - "{{ref:lai_keywords.core_phrases}}"
    - "{{ref:lai_keywords.technology_terms_high_precision}}"
  
  pure_player_companies:
    - "{{ref:lai_companies_mvp_core}}"
  
  trademarks:
    - "{{ref:lai_trademarks_global}}"
  
  # SIGNAUX MOYENS (medium confidence)
  technology_families:
    - "{{ref:lai_keywords.technology_use}}"
  
  dosing_intervals:
    - "{{ref:lai_keywords.interval_patterns}}"
  
  # SIGNAUX FAIBLES (low confidence)
  routes:
    - "{{ref:lai_keywords.route_admin_terms}}"
  
  molecules:
    - "{{ref:lai_molecules_global}}"
  
  # EXCLUSIONS (anti-LAI)
  exclusions:
    - "{{ref:lai_keywords.negative_terms}}"
  
  # RÈGLES DE MATCHING
  # ÉVOLUTION: Ajuster seuils basés sur métriques E2E
  matching_rules:
    high_confidence:
      description: "1+ strong signal → high confidence match"
      conditions:
        - "1+ core_technology"
        - "1+ pure_player_company"
        - "1+ trademark"
      min_score: 70
    
    medium_confidence:
      description: "2+ medium signals → medium confidence match"
      conditions:
        - "2+ technology_families"
        - "1+ dosing_interval + 1+ route"
      min_score: 40
    
    low_confidence:
      description: "3+ weak signals + 0 exclusions → low confidence match"
      conditions:
        - "3+ weak signals"
        - "0 exclusions"
      min_score: 20
    
    reject:
      description: "1+ exclusion → reject"
      conditions:
        - "1+ exclusion"
  
  # SCORES DE BASE PAR TYPE D'ÉVÉNEMENT
  # ÉVOLUTION: Ajuster basés sur valeur business réelle
  event_type_base_scores:
    partnership: 60
    regulatory: 70
    clinical_update: 50
    financial_results: 40
    corporate_move: 45
    scientific_publication: 35
    other: 20
  
  # BOOSTS PAR TYPE D'ENTITÉ
  # ÉVOLUTION: Ajuster basés sur corrélation avec pertinence
  entity_boosts:
    pure_player_company: 25
    trademark: 20
    core_technology: 15
    technology_family: 10
    molecule: 8
    dosing_interval: 5
    route: 3
  
  # BOOST DE RÉCENCE
  recency_boost:
    max_boost: 10
    decay_days: 30
  
  # PÉNALITÉ DE CONFIANCE
  confidence_penalty:
    low_confidence: -5
    medium_confidence: 0
    high_confidence: 0
```

**Validation**:
```bash
# Valider syntaxe YAML
python -c "import yaml; yaml.safe_load(open('canonical/scopes/domain_definitions.yaml'))"
```

---

### Étape 1.2: Sync vers S3 (15min)

**Actions**:
```bash
# Sync domain_definitions.yaml
aws s3 cp canonical/scopes/domain_definitions.yaml \
  s3://vectora-inbox-config-dev/canonical/scopes/domain_definitions.yaml \
  --profile rag-lai-prod --region eu-west-3

# Vérifier upload
aws s3 ls s3://vectora-inbox-config-dev/canonical/scopes/ --recursive \
  --profile rag-lai-prod --region eu-west-3 | grep domain_definitions
```

**Validation**:
```bash
# Télécharger et vérifier
aws s3 cp s3://vectora-inbox-config-dev/canonical/scopes/domain_definitions.yaml \
  /tmp/domain_definitions_s3.yaml \
  --profile rag-lai-prod --region eu-west-3

diff canonical/scopes/domain_definitions.yaml /tmp/domain_definitions_s3.yaml
```

---

### Étape 1.3: Créer Client Config v12 (30min)

**Fichier**: `client-config-examples/production/lai_weekly_v12.yaml`

**Action**: Copier v11 et modifier

```bash
# Copier v11 → v12
cp client-config-examples/production/lai_weekly_v11.yaml \
   client-config-examples/production/lai_weekly_v12.yaml
```

**Modifications**:
```yaml
client_profile:
  name: "LAI Intelligence Weekly v12 (Test Domain Definition Fix)"
  client_id: "lai_weekly_v12"
  
metadata:
  template_version: "12.0.0"
  created_date: "2026-02-03"
  created_by: "Correctif Matching - Domain Definition Fix"
  
  creation_notes: |
    OBJECTIF v12 (Correctif Matching):
    🎯 Corriger 0% matching via lai_domain_definition.yaml
    🎯 Valider architecture 2 appels Bedrock
    🎯 Baseline pour amélioration continue
    
    MODIFICATIONS v11 → v12:
    ✅ client_id: "lai_weekly_v11" → "lai_weekly_v12"
    ✅ Ajout domain_definitions.yaml sur S3
    ✅ Config identique pour comparaison
    
    MÉTRIQUES ATTENDUES:
    - Taux matching: 0% → >50%
    - Items matchés: 0/29 → 15+/29
    - Score UZEDY®: 0 → >90
    - Score MedinCell: 0 → >85
```

**Sync vers S3**:
```bash
aws s3 cp client-config-examples/production/lai_weekly_v12.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v12.yaml \
  --profile rag-lai-prod --region eu-west-3
```

---

### Étape 1.4: Test E2E lai_weekly_v12 (1h)

**Actions**:
```bash
# Test complet
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v12
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v12
```

**Télécharger résultats**:
```bash
# Créer dossier temporaire
mkdir -p .tmp/e2e/lai_weekly_v12

# Télécharger items curés
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v12/2026/02/03/items.json \
  .tmp/e2e/lai_weekly_v12/curated_items.json \
  --profile rag-lai-prod --region eu-west-3
```

---

### Étape 1.5: Analyse Résultats (1h)

**Script d'analyse**: `scripts/analysis/analyze_matching_v12.py`

```python
import json

with open('.tmp/e2e/lai_weekly_v12/curated_items.json') as f:
    items = json.load(f)

# Métriques matching
total = len(items)
matched = sum(1 for item in items if item.get('domain_scoring', {}).get('is_relevant'))
match_rate = (matched / total * 100) if total > 0 else 0

print(f"Taux matching: {match_rate:.1f}% ({matched}/{total})")

# Analyse par score
scores = [item.get('domain_scoring', {}).get('score', 0) for item in items if item.get('domain_scoring', {}).get('is_relevant')]
if scores:
    print(f"Score moyen: {sum(scores)/len(scores):.1f}")
    print(f"Score min: {min(scores)}")
    print(f"Score max: {max(scores)}")

# Items clés
for item in items:
    title = item.get('title', '')
    if 'UZEDY' in title or 'MedinCell' in title or 'Extended-Release Injectable' in title:
        score = item.get('domain_scoring', {}).get('score', 0)
        is_relevant = item.get('domain_scoring', {}).get('is_relevant', False)
        print(f"\n{title[:80]}")
        print(f"  Relevant: {is_relevant}, Score: {score}")
```

**Exécution**:
```bash
python scripts/analysis/analyze_matching_v12.py
```

---

### Étape 1.6: Rapport Phase 1 (30min)

**Fichier**: `docs/reports/e2e/test_e2e_v12_phase1_correction_2026-02-03.md`

**Contenu**:
```markdown
# Test E2E v12 - Phase 1 Correction Matching

## Résultats

### Métriques Matching
- Taux matching: X% (objectif: >50%)
- Items matchés: X/29 (objectif: 15+)
- Score UZEDY®: X (objectif: >90)
- Score MedinCell: X (objectif: >85)

### Statut
- ✅ Succès si >50% matching
- ⚠️ Ajustements requis si 30-50%
- ❌ Échec si <30%

### Prochaines Actions
- Si succès: Phase 2 (ajustements fins)
- Si ajustements: Modifier domain_definition
- Si échec: Investiguer logs Bedrock
```

**Critères de succès Phase 1**:
- ✅ Taux matching >50%
- ✅ Items LAI évidents matchés (UZEDY®, MedinCell, Extended-Release)
- ✅ Pas d'erreurs Bedrock

---

## 📋 PHASE 2: AMÉLIORATION CONTINUE (Jour 2-3)

### Étape 2.1: Système de Versioning Prompts

**Objectif**: Tracker évolution des prompts et domain definitions

**Fichier**: `canonical/scopes/domain_definitions.yaml`

**Structure de changelog**:
```yaml
lai_domain_definition:
  _metadata:
    version: "1.1.0"
    changelog:
      - version: "1.1.0"
        date: "2026-02-04"
        changes: "Ajout signaux détectés dans faux négatifs v12"
        test_run: "lai_weekly_v13"
        metrics:
          match_rate_before: "52%"
          match_rate_after: "68%"
          precision_before: "75%"
          precision_after: "82%"
      
      - version: "1.0.0"
        date: "2026-02-03"
        changes: "Initial version - baseline"
        test_run: "lai_weekly_v12"
        metrics:
          match_rate: "52%"
          precision: "75%"
```

---

### Étape 2.2: Analyse Faux Positifs/Négatifs

**Script**: `scripts/analysis/analyze_false_positives_negatives.py`

```python
"""
Analyse des faux positifs et faux négatifs pour amélioration continue.
"""

def analyze_false_positives(items, human_labels):
    """Items matchés à tort."""
    false_positives = []
    for item in items:
        if item['domain_scoring']['is_relevant'] and not human_labels.get(item['item_id']):
            false_positives.append({
                'title': item['title'],
                'score': item['domain_scoring']['score'],
                'signals': item['domain_scoring']['signals_detected'],
                'reasoning': item['domain_scoring']['reasoning']
            })
    return false_positives

def analyze_false_negatives(items, human_labels):
    """Items LAI manqués."""
    false_negatives = []
    for item in items:
        if not item['domain_scoring']['is_relevant'] and human_labels.get(item['item_id']):
            false_negatives.append({
                'title': item['title'],
                'entities': item['normalized_content']['entities'],
                'missing_signals': analyze_missing_signals(item)
            })
    return false_negatives

def generate_recommendations(false_positives, false_negatives):
    """Génère recommandations d'ajustement."""
    recommendations = []
    
    # Faux positifs → signaux trop permissifs
    for fp in false_positives:
        if 'weak' in fp['signals']:
            recommendations.append({
                'action': 'increase_threshold',
                'target': 'weak_signals',
                'reason': f"Faux positif: {fp['title'][:50]}"
            })
    
    # Faux négatifs → signaux manquants
    for fn in false_negatives:
        for entity_type, entities in fn['entities'].items():
            for entity in entities:
                if entity not in get_current_scopes(entity_type):
                    recommendations.append({
                        'action': 'add_to_scope',
                        'target': f'{entity_type}_scope',
                        'value': entity,
                        'reason': f"Faux négatif: {fn['title'][:50]}"
                    })
    
    return recommendations
```

---

### Étape 2.3: Workflow d'Ajustement

**Processus**:

1. **Analyser résultats E2E**
   ```bash
   python scripts/analysis/analyze_false_positives_negatives.py \
     --items .tmp/e2e/lai_weekly_v12/curated_items.json \
     --human-labels .tmp/e2e/lai_weekly_v12/human_labels.json \
     --output .tmp/e2e/lai_weekly_v12/recommendations.json
   ```

2. **Appliquer recommandations**
   - Modifier `canonical/scopes/domain_definitions.yaml`
   - Incrémenter version (1.0.0 → 1.1.0)
   - Ajouter changelog entry

3. **Sync vers S3**
   ```bash
   aws s3 cp canonical/scopes/domain_definitions.yaml \
     s3://vectora-inbox-config-dev/canonical/scopes/domain_definitions.yaml \
     --profile rag-lai-prod --region eu-west-3
   ```

4. **Test E2E v13**
   ```bash
   # Nouveau client_id pour données fraîches
   python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v13
   ```

5. **Comparer métriques**
   ```bash
   python scripts/analysis/compare_versions.py \
     --v1 lai_weekly_v12 \
     --v2 lai_weekly_v13
   ```

---

### Étape 2.4: Dashboard Métriques

**Fichier**: `scripts/monitoring/matching_dashboard.py`

```python
"""
Dashboard de monitoring des métriques de matching.
Génère rapport HTML avec évolution des métriques.
"""

def generate_dashboard(versions):
    """Génère dashboard HTML."""
    metrics_history = []
    
    for version in versions:
        items = load_items(version)
        metrics = calculate_metrics(items)
        metrics_history.append({
            'version': version,
            'date': get_test_date(version),
            'match_rate': metrics['match_rate'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'avg_score': metrics['avg_score']
        })
    
    # Générer graphiques
    plot_match_rate_evolution(metrics_history)
    plot_precision_recall(metrics_history)
    plot_score_distribution(metrics_history)
    
    # Générer HTML
    html = generate_html_report(metrics_history)
    with open('docs/reports/matching_dashboard.html', 'w') as f:
        f.write(html)
```

**Usage**:
```bash
python scripts/monitoring/matching_dashboard.py \
  --versions lai_weekly_v12,lai_weekly_v13,lai_weekly_v14
```

---

## 📋 PHASE 3: INDUSTRIALISATION (Jour 4-5)

### Étape 3.1: Tests Automatisés

**Fichier**: `tests/integration/test_domain_scoring.py`

```python
"""
Tests d'intégration pour domain scoring.
Valide que les items LAI évidents sont toujours matchés.
"""

import pytest

GOLDEN_ITEMS = [
    {
        'title': 'MedinCell UZEDY® Sales',
        'entities': {'companies': ['MedinCell'], 'trademarks': ['UZEDY®']},
        'expected_score': 90,
        'expected_confidence': 'high'
    },
    {
        'title': 'Nanexa PharmaShell® Partnership',
        'entities': {'companies': ['Nanexa'], 'technologies': ['PharmaShell®']},
        'expected_score': 85,
        'expected_confidence': 'high'
    }
]

@pytest.mark.parametrize('golden_item', GOLDEN_ITEMS)
def test_golden_items_matched(golden_item):
    """Items LAI évidents doivent toujours être matchés."""
    result = score_item_for_domain(golden_item, domain_definition, canonical_scopes)
    
    assert result['is_relevant'] == True
    assert result['score'] >= golden_item['expected_score']
    assert result['confidence'] == golden_item['expected_confidence']
```

**Exécution**:
```bash
pytest tests/integration/test_domain_scoring.py -v
```

---

### Étape 3.2: Script de Validation Prompts

**Fichier**: `scripts/maintenance/validate_prompts.py`

```python
"""
Valide que tous les prompts ont leurs références résolues.
"""

def validate_prompt_references(prompt_path, canonical_scopes):
    """Valide références {{ref:}}."""
    with open(prompt_path) as f:
        content = f.read()
    
    refs = re.findall(r'\{\{ref:([^}]+)\}\}', content)
    missing = []
    
    for ref in refs:
        if not resolve_scope_path(ref, canonical_scopes):
            missing.append(ref)
    
    if missing:
        print(f"❌ {prompt_path}: Missing references:")
        for ref in missing:
            print(f"   - {{{{ref:{ref}}}}}")
        return False
    
    print(f"✅ {prompt_path}: All references valid")
    return True

if __name__ == '__main__':
    canonical_scopes = load_canonical_scopes()
    
    prompts = [
        'canonical/prompts/normalization/generic_normalization.yaml',
        'canonical/prompts/domain_scoring/lai_domain_scoring.yaml',
        'canonical/prompts/editorial/lai_editorial.yaml'
    ]
    
    all_valid = all(validate_prompt_references(p, canonical_scopes) for p in prompts)
    sys.exit(0 if all_valid else 1)
```

**Intégration CI/CD**:
```bash
# Ajouter dans .github/workflows/validate.yml
- name: Validate Prompts
  run: python scripts/maintenance/validate_prompts.py
```

---

### Étape 3.3: Documentation Amélioration Continue

**Fichier**: `docs/guides/amelioration_continue_prompts.md`

```markdown
# Guide d'Amélioration Continue des Prompts

## Workflow Standard

### 1. Test E2E
- Lancer test avec client_id incrémenté
- Télécharger résultats depuis S3

### 2. Analyse Humaine
- Labelliser 20-30 items (pertinent/non pertinent)
- Identifier faux positifs et faux négatifs

### 3. Générer Recommandations
```bash
python scripts/analysis/analyze_false_positives_negatives.py
```

### 4. Appliquer Ajustements
- Modifier `canonical/scopes/domain_definitions.yaml`
- Incrémenter version
- Ajouter changelog

### 5. Sync et Test
```bash
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_vXX
```

### 6. Comparer Métriques
```bash
python scripts/analysis/compare_versions.py --v1 vXX --v2 vYY
```

### 7. Commit si Amélioration
```bash
git add canonical/scopes/domain_definitions.yaml
git commit -m "feat: improve matching v1.X.0 (+5% match rate)"
```

## Métriques à Tracker

- **Match Rate**: % items matchés
- **Precision**: % items matchés pertinents
- **Recall**: % items pertinents matchés
- **Avg Score**: Score moyen des items matchés
- **False Positive Rate**: % faux positifs
- **False Negative Rate**: % faux négatifs

## Seuils de Qualité

- Match Rate: 60-80%
- Precision: >80%
- Recall: >70%
- Avg Score: >60
```

---

## 📊 MÉTRIQUES DE SUCCÈS

### Phase 1 (Jour 1)

| Métrique | Avant | Objectif | Critique |
|----------|-------|----------|----------|
| Taux matching | 0% | >50% | ✅ |
| Items matchés | 0/29 | 15+/29 | ✅ |
| Score UZEDY® | 0 | >90 | ✅ |
| Score MedinCell | 0 | >85 | ✅ |
| Newsletter générée | ❌ | ✅ | ✅ |

### Phase 2 (Jour 2-3)

| Métrique | Objectif Phase 1 | Objectif Phase 2 |
|----------|------------------|------------------|
| Taux matching | >50% | 60-80% |
| Precision | >70% | >80% |
| Recall | >60% | >70% |
| Faux positifs | <30% | <20% |
| Faux négatifs | <40% | <30% |

### Phase 3 (Jour 4-5)

| Livrable | Statut |
|----------|--------|
| Tests automatisés | ✅ |
| Script validation prompts | ✅ |
| Dashboard métriques | ✅ |
| Documentation complète | ✅ |
| Code mergé develop | ✅ |

---

## 🚀 COMMANDES RAPIDES

### Test E2E Complet
```bash
# Version courte
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v12

# Version complète avec analyse
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v12
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v12
python scripts/analysis/analyze_matching_v12.py
```

### Sync Canonical vers S3
```bash
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3 --exclude "*.md"
```

### Comparer Versions
```bash
python scripts/analysis/compare_versions.py \
  --v1 lai_weekly_v12 --v2 lai_weekly_v13 \
  --output docs/reports/comparison_v12_v13.md
```

### Générer Dashboard
```bash
python scripts/monitoring/matching_dashboard.py \
  --versions lai_weekly_v12,lai_weekly_v13,lai_weekly_v14 \
  --output docs/reports/matching_dashboard.html
```

---

## 📝 CHECKLIST EXÉCUTION

### Phase 1: Correction Immédiate
- [ ] Créer `canonical/scopes/domain_definitions.yaml`
- [ ] Valider syntaxe YAML
- [ ] Sync vers S3
- [ ] Créer `lai_weekly_v12.yaml`
- [ ] Sync client config vers S3
- [ ] Test E2E lai_weekly_v12
- [ ] Télécharger résultats S3
- [ ] Analyser métriques matching
- [ ] Rapport Phase 1
- [ ] Validation critères succès (>50% matching)

### Phase 2: Amélioration Continue
- [ ] Analyser faux positifs/négatifs
- [ ] Générer recommandations
- [ ] Ajuster domain_definitions.yaml
- [ ] Incrémenter version (1.0.0 → 1.1.0)
- [ ] Sync vers S3
- [ ] Test E2E lai_weekly_v13
- [ ] Comparer v12 vs v13
- [ ] Générer dashboard métriques
- [ ] Validation critères succès (60-80% matching, >80% precision)

### Phase 3: Industrialisation
- [ ] Créer tests automatisés
- [ ] Créer script validation prompts
- [ ] Créer dashboard monitoring
- [ ] Documenter workflow amélioration continue
- [ ] Commit et tag version
- [ ] Merge dans develop
- [ ] Mettre à jour blueprint

---

## 🎯 PROCHAINES ACTIONS IMMÉDIATES

1. **Créer domain_definitions.yaml** (maintenant)
2. **Sync vers S3** (dans 15min)
3. **Test E2E v12** (dans 30min)
4. **Analyser résultats** (dans 2h)
5. **Rapport Phase 1** (dans 3h)

**Timeline totale Phase 1**: 4-5 heures  
**Confiance succès**: 95%

---

**Plan créé le**: 2026-02-03  
**Basé sur**: diagnostic_matching_lai_weekly_v11_2026-02-03.md  
**Statut**: ✅ Prêt pour exécution immédiate
