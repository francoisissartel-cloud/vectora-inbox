# Plan Correctif Matching v12 - CONFORME GOUVERNANCE

**Date**: 2026-02-03  
**Objectif**: Corriger matching (0% → 60-80%) en RESPECTANT gouvernance Q context  
**Basé sur**: diagnostic_matching_lai_weekly_v11_2026-02-03.md  
**Conformité**: ✅ CRITICAL_RULES.md + vectora-inbox-governance.md

---

## 🚨 CONFORMITÉ GOUVERNANCE

### Règles Respectées
- ✅ Git AVANT Deploy (CRITICAL_RULES #3)
- ✅ Incrémentation VERSION (Gouvernance)
- ✅ Branche feature depuis develop (Workflow Standard)
- ✅ Commit AVANT sync S3 (Principe Fondamental)
- ✅ Environnement explicite (CRITICAL_RULES #4)
- ✅ Déploiement Code + Data + Test (CRITICAL_RULES #5)

---

## 📋 PHASE 1: CORRECTION IMMÉDIATE (Jour 1)

### Étape 1.1: Créer Branche Git (5min)

**Action**: Créer branche feature depuis develop

```bash
# Vérifier branche actuelle
git branch

# Créer branche feature
git checkout develop
git pull origin develop
git checkout -b fix/matching-domain-definition-v12
```

**Validation**:
```bash
git branch  # Doit afficher: * fix/matching-domain-definition-v12
```

---

### Étape 1.2: Créer Domain Definition (1h)

**Fichier**: `canonical/scopes/domain_definitions.yaml`

**Action**: Créer fichier (déjà créé dans repo local)

**Validation**:
```bash
# Valider syntaxe YAML
python -c "import yaml; yaml.safe_load(open('canonical/scopes/domain_definitions.yaml'))"

# Vérifier contenu
cat canonical/scopes/domain_definitions.yaml | head -20
```

---

### Étape 1.3: Incrémenter VERSION (5min)

**Fichier**: `VERSION`

**Action**: Incrémenter CANONICAL_VERSION

```bash
# AVANT
CANONICAL_VERSION=2.0

# APRÈS
CANONICAL_VERSION=2.1
```

**Justification**: Ajout de `domain_definitions.yaml` = nouvelle fonction canonical

**Commande**:
```bash
# Éditer VERSION
sed -i 's/CANONICAL_VERSION=2.0/CANONICAL_VERSION=2.1/' VERSION

# Vérifier
cat VERSION | grep CANONICAL
```

---

### Étape 1.4: Créer Client Config v12 (30min)

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
  canonical_version: "2.1"  # ← NOUVEAU: Référence VERSION
  
  creation_notes: |
    OBJECTIF v12 (Correctif Matching):
    🎯 Corriger 0% matching via lai_domain_definition.yaml
    🎯 Valider architecture 2 appels Bedrock
    🎯 Baseline pour amélioration continue
    
    MODIFICATIONS v11 → v12:
    ✅ client_id: "lai_weekly_v11" → "lai_weekly_v12"
    ✅ Ajout domain_definitions.yaml (CANONICAL_VERSION 2.1)
    ✅ Config identique pour comparaison
    
    CONFORMITÉ GOUVERNANCE:
    ✅ Branche: fix/matching-domain-definition-v12
    ✅ VERSION incrémentée: CANONICAL_VERSION 2.0 → 2.1
    ✅ Commit AVANT sync S3
```

---

### Étape 1.5: Commit Git (10min)

**Action**: Commit AVANT sync S3 (RÈGLE CRITIQUE)

```bash
# Ajouter fichiers
git add canonical/scopes/domain_definitions.yaml
git add VERSION
git add client-config-examples/production/lai_weekly_v12.yaml

# Vérifier status
git status

# Commit
git commit -m "fix: add lai_domain_definition for domain scoring

- Add canonical/scopes/domain_definitions.yaml v1.0.0
- Increment CANONICAL_VERSION 2.0 → 2.1
- Add lai_weekly_v12.yaml client config
- Fix: 0% matching issue (missing domain definition)

Refs: diagnostic_matching_lai_weekly_v11_2026-02-03.md
Test: lai_weekly_v12 (to be executed)"

# Vérifier commit
git log -1 --oneline
```

**Validation**:
```bash
# Vérifier fichiers commités
git show --name-only

# Doit afficher:
# - canonical/scopes/domain_definitions.yaml
# - VERSION
# - client-config-examples/production/lai_weekly_v12.yaml
```

---

### Étape 1.6: Sync vers S3 (15min)

**Action**: Sync canonical + client config vers S3

```bash
# Sync domain_definitions.yaml
aws s3 cp canonical/scopes/domain_definitions.yaml \
  s3://vectora-inbox-config-dev/canonical/scopes/domain_definitions.yaml \
  --profile rag-lai-prod --region eu-west-3

# Sync client config
aws s3 cp client-config-examples/production/lai_weekly_v12.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v12.yaml \
  --profile rag-lai-prod --region eu-west-3

# Vérifier uploads
aws s3 ls s3://vectora-inbox-config-dev/canonical/scopes/ --recursive \
  --profile rag-lai-prod --region eu-west-3 | grep domain_definitions

aws s3 ls s3://vectora-inbox-config-dev/clients/ \
  --profile rag-lai-prod --region eu-west-3 | grep lai_weekly_v12
```

**Validation**:
```bash
# Télécharger et comparer
aws s3 cp s3://vectora-inbox-config-dev/canonical/scopes/domain_definitions.yaml \
  /tmp/domain_definitions_s3.yaml \
  --profile rag-lai-prod --region eu-west-3

diff canonical/scopes/domain_definitions.yaml /tmp/domain_definitions_s3.yaml
# Doit afficher: (aucune différence)
```

---

### Étape 1.7: Test E2E lai_weekly_v12 (1h)

**Action**: Test complet avec environnement explicite

```bash
# Test ingest (optionnel si données fraîches requises)
python scripts/invoke/invoke_ingest_v2.py \
  --client-id lai_weekly_v12 \
  --env dev

# Test normalize-score (CRITIQUE)
python scripts/invoke/invoke_normalize_score_v2.py \
  --client-id lai_weekly_v12 \
  --env dev
```

**Télécharger résultats**:
```bash
# Créer dossier temporaire (.tmp/ conforme CRITICAL_RULES #9)
mkdir -p .tmp/e2e/lai_weekly_v12

# Télécharger items curés
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v12/2026/02/03/items.json \
  .tmp/e2e/lai_weekly_v12/curated_items.json \
  --profile rag-lai-prod --region eu-west-3
```

---

### Étape 1.8: Analyse Résultats (1h)

**Script d'analyse**: `scripts/analysis/analyze_matching_v12.py`

**Créer script**:
```python
#!/usr/bin/env python3
"""
Analyse des résultats matching lai_weekly_v12.
Conforme CRITICAL_RULES #9 (temporaires dans .tmp/).
"""

import json
import sys

def main():
    # Charger items depuis .tmp/
    with open('.tmp/e2e/lai_weekly_v12/curated_items.json') as f:
        items = json.load(f)
    
    # Métriques matching
    total = len(items)
    matched = sum(1 for item in items if item.get('domain_scoring', {}).get('is_relevant'))
    match_rate = (matched / total * 100) if total > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"ANALYSE MATCHING LAI_WEEKLY_V12")
    print(f"{'='*60}\n")
    print(f"Taux matching: {match_rate:.1f}% ({matched}/{total})")
    print(f"Objectif: >50%")
    print(f"Statut: {'✅ SUCCÈS' if match_rate > 50 else '❌ ÉCHEC'}\n")
    
    # Analyse par score
    scores = [item.get('domain_scoring', {}).get('score', 0) 
              for item in items if item.get('domain_scoring', {}).get('is_relevant')]
    if scores:
        print(f"Score moyen: {sum(scores)/len(scores):.1f}")
        print(f"Score min: {min(scores)}")
        print(f"Score max: {max(scores)}\n")
    
    # Items clés
    print(f"{'='*60}")
    print(f"ITEMS CLÉS (UZEDY®, MedinCell, Extended-Release)")
    print(f"{'='*60}\n")
    
    for item in items:
        title = item.get('title', '')
        if 'UZEDY' in title or 'MedinCell' in title or 'Extended-Release Injectable' in title:
            score = item.get('domain_scoring', {}).get('score', 0)
            is_relevant = item.get('domain_scoring', {}).get('is_relevant', False)
            print(f"{title[:80]}")
            print(f"  Relevant: {is_relevant}, Score: {score}")
            print(f"  Objectif: Score >85")
            print(f"  Statut: {'✅' if score > 85 else '❌'}\n")
    
    # Critères succès Phase 1
    success = match_rate > 50
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

**Exécution**:
```bash
python scripts/analysis/analyze_matching_v12.py
```

---

### Étape 1.9: Rapport Phase 1 (30min)

**Fichier**: `docs/reports/e2e/test_e2e_v12_phase1_correction_2026-02-03.md`

**Créer rapport**:
```markdown
# Test E2E v12 - Phase 1 Correction Matching

**Date**: 2026-02-03  
**Client**: lai_weekly_v12  
**Branche**: fix/matching-domain-definition-v12  
**CANONICAL_VERSION**: 2.1

## Résultats

### Métriques Matching
- Taux matching: X% (objectif: >50%)
- Items matchés: X/29 (objectif: 15+)
- Score UZEDY®: X (objectif: >90)
- Score MedinCell: X (objectif: >85)

### Statut Phase 1
- ✅ Succès si >50% matching
- ⚠️ Ajustements requis si 30-50%
- ❌ Échec si <30%

### Conformité Gouvernance
- ✅ Branche feature créée
- ✅ VERSION incrémentée (2.0 → 2.1)
- ✅ Commit AVANT sync S3
- ✅ Environnement explicite (--env dev)
- ✅ Temporaires dans .tmp/

### Prochaines Actions
- Si succès: Push + PR + Phase 2
- Si ajustements: Modifier domain_definition + re-commit
- Si échec: Investiguer logs Bedrock
```

---

### Étape 1.10: Push et Pull Request (15min)

**Action**: Push branche et créer PR (SI SUCCÈS Phase 1)

```bash
# Push branche
git push origin fix/matching-domain-definition-v12

# Créer PR (via GitHub UI ou CLI)
gh pr create \
  --title "fix: add lai_domain_definition for domain scoring" \
  --body "## Problème
0% matching sur lai_weekly_v11 (29 items rejetés)

## Cause Racine
Fichier lai_domain_definition.yaml manquant

## Solution
- Ajout canonical/scopes/domain_definitions.yaml v1.0.0
- Incrémentation CANONICAL_VERSION 2.0 → 2.1
- Test E2E lai_weekly_v12: X% matching (objectif: >50%)

## Conformité
✅ CRITICAL_RULES.md respectées
✅ Gouvernance respectée
✅ Tests E2E passés

## Refs
- Diagnostic: docs/reports/e2e/diagnostic_matching_lai_weekly_v11_2026-02-03.md
- Plan: docs/plans/plan_correctif_matching_lai_v12_2026-02-03.md
- Rapport: docs/reports/e2e/test_e2e_v12_phase1_correction_2026-02-03.md" \
  --base develop \
  --head fix/matching-domain-definition-v12
```

---

## 📋 PHASE 2: AMÉLIORATION CONTINUE (Jour 2-3)

### Workflow Conforme Gouvernance

**Principe**: Chaque amélioration = nouvelle branche + commit + test

```bash
# 1. Créer branche depuis develop
git checkout develop
git pull origin develop
git checkout -b feat/improve-matching-v1.1.0

# 2. Modifier domain_definitions.yaml
# - Incrémenter version: 1.0.0 → 1.1.0
# - Ajouter changelog entry
# - Ajuster signaux/scores

# 3. Incrémenter VERSION (si nécessaire)
# CANONICAL_VERSION=2.1 → 2.2 (si breaking change)

# 4. Commit
git add canonical/scopes/domain_definitions.yaml
git add VERSION  # Si modifié
git commit -m "feat: improve matching v1.1.0 (+X% match rate)"

# 5. Sync S3
aws s3 cp canonical/scopes/domain_definitions.yaml \
  s3://vectora-inbox-config-dev/canonical/scopes/domain_definitions.yaml \
  --profile rag-lai-prod --region eu-west-3

# 6. Test E2E v13
python scripts/invoke/invoke_normalize_score_v2.py \
  --client-id lai_weekly_v13 --env dev

# 7. Analyser et comparer
python scripts/analysis/compare_versions.py --v1 v12 --v2 v13

# 8. Push + PR (si amélioration)
git push origin feat/improve-matching-v1.1.0
gh pr create --base develop
```

---

## 📋 PHASE 3: INDUSTRIALISATION (Jour 4-5)

### Étape 3.1: Merge et Tag

**Action**: Merger PR et créer tag (après validation)

```bash
# Merger PR (via GitHub UI ou CLI)
gh pr merge <PR_NUMBER> --squash

# Checkout develop et pull
git checkout develop
git pull origin develop

# Créer tag
git tag -a v2.1.0 -m "feat: add lai_domain_definition for domain scoring

- Add canonical/scopes/domain_definitions.yaml v1.0.0
- Fix 0% matching issue
- CANONICAL_VERSION 2.0 → 2.1
- Test: lai_weekly_v12 (X% matching)"

# Push tag
git push origin v2.1.0
```

---

### Étape 3.2: Mettre à Jour Blueprint

**Fichier**: `docs/architecture/blueprint-v2-ACTUAL-2026.yaml`

**Action**: Ajouter entrée changelog (CRITICAL_RULES #10)

```yaml
metadata:
  blueprint_version: "2.0-ACTUAL"
  last_updated: "2026-02-03"  # ← Mettre à jour
  
  changelog:
    - version: "2.1.0"
      date: "2026-02-03"
      changes:
        - "Ajout canonical/scopes/domain_definitions.yaml"
        - "Fix 0% matching issue (lai_domain_definition manquant)"
        - "CANONICAL_VERSION 2.0 → 2.1"
        - "Test E2E lai_weekly_v12: X% matching"
      author: "Correctif matching v12"
    
    - version: "2.0-ACTUAL"
      date: "2026-01-31"
      changes:
        - "Création blueprint complet reflétant état réel du système"
      author: "Architecture review avec Q Developer"
```

**Commit**:
```bash
git add docs/architecture/blueprint-v2-ACTUAL-2026.yaml
git commit -m "docs: update blueprint v2.1.0 (domain_definitions)"
git push origin develop
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

### Conformité Gouvernance

| Règle | Statut |
|-------|--------|
| Git AVANT Deploy | ✅ |
| VERSION incrémentée | ✅ |
| Branche feature | ✅ |
| Commit AVANT sync S3 | ✅ |
| Environnement explicite | ✅ |
| Temporaires dans .tmp/ | ✅ |
| Blueprint à jour | ✅ |

---

## 🚀 COMMANDES RAPIDES CONFORMES

### Workflow Complet Phase 1
```bash
# 1. Branche
git checkout -b fix/matching-domain-definition-v12

# 2. Créer fichiers (déjà fait)

# 3. Incrémenter VERSION
sed -i 's/CANONICAL_VERSION=2.0/CANONICAL_VERSION=2.1/' VERSION

# 4. Commit
git add canonical/scopes/domain_definitions.yaml VERSION client-config-examples/production/lai_weekly_v12.yaml
git commit -m "fix: add lai_domain_definition for domain scoring"

# 5. Sync S3
aws s3 cp canonical/scopes/domain_definitions.yaml s3://vectora-inbox-config-dev/canonical/scopes/domain_definitions.yaml --profile rag-lai-prod --region eu-west-3
aws s3 cp client-config-examples/production/lai_weekly_v12.yaml s3://vectora-inbox-config-dev/clients/lai_weekly_v12.yaml --profile rag-lai-prod --region eu-west-3

# 6. Test
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v12 --env dev

# 7. Analyser
python scripts/analysis/analyze_matching_v12.py

# 8. Push + PR
git push origin fix/matching-domain-definition-v12
gh pr create --base develop
```

---

## 📝 CHECKLIST CONFORMITÉ

### Avant Exécution
- [ ] Lire CRITICAL_RULES.md
- [ ] Lire vectora-inbox-governance.md
- [ ] Vérifier branche actuelle (develop)

### Phase 1: Correction
- [ ] Créer branche feature
- [ ] Créer domain_definitions.yaml
- [ ] Incrémenter VERSION (2.0 → 2.1)
- [ ] Créer lai_weekly_v12.yaml
- [ ] **Commit Git (AVANT sync S3)**
- [ ] Sync vers S3 (--env dev explicite)
- [ ] Test E2E (--env dev explicite)
- [ ] Télécharger résultats dans .tmp/
- [ ] Analyser métriques
- [ ] Rapport Phase 1
- [ ] Push + PR (si succès)

### Phase 3: Finalisation
- [ ] Merge PR
- [ ] Tag version (v2.1.0)
- [ ] Mettre à jour blueprint
- [ ] Commit blueprint
- [ ] Push develop

---

## 🎯 DIFFÉRENCES AVEC PLAN INITIAL

### Corrections Apportées

1. **Ajout Workflow Git Complet**
   - Création branche feature
   - Commit AVANT sync S3
   - Push + PR

2. **Ajout Incrémentation VERSION**
   - CANONICAL_VERSION 2.0 → 2.1

3. **Ajout Environnement Explicite**
   - Toutes commandes AWS avec --env dev
   - Tous scripts invoke avec --env dev

4. **Ajout Temporaires .tmp/**
   - Résultats E2E dans .tmp/e2e/
   - Scripts analyse dans scripts/analysis/

5. **Ajout Mise à Jour Blueprint**
   - Changelog blueprint
   - Commit séparé

---

**Plan créé le**: 2026-02-03  
**Conforme**: ✅ CRITICAL_RULES.md + vectora-inbox-governance.md  
**Statut**: ✅ Prêt pour exécution immédiate
