# Plan Test E2E lai_weekly_v13 - AWS Dev

**Date**: 2026-02-03  
**Objectif**: Tester moteur en dev AWS et comparer v11/v12/v13  
**Conformité**: ✅ CRITICAL_RULES.md + vectora-inbox-governance.md

---

## 🚨 CONFORMITÉ GOUVERNANCE

### Règles Respectées
- ✅ Git AVANT Deploy (CRITICAL_RULES #3)
- ✅ Pas d'incrémentation VERSION (test uniquement, pas de nouvelle fonction)
- ✅ Branche feature depuis main (Workflow Standard)
- ✅ Commit AVANT sync S3 (Principe Fondamental)
- ✅ Environnement explicite --env dev (CRITICAL_RULES #4)
- ✅ Test E2E complet (CRITICAL_RULES #5)
- ✅ Temporaires dans .tmp/ (CRITICAL_RULES #9)

### VERSION Actuelle
```
CANONICAL_VERSION=2.1
VECTORA_CORE_VERSION=1.4.1
NORMALIZE_VERSION=2.1.0
```

**Justification pas d'incrémentation**: lai_weekly_v13 = copie v12 pour test comparatif, aucune nouvelle fonction.

---

## 📋 PHASE 1: PRÉPARATION (30min)

### Étape 1.1: Créer Branche Git (5min)

```bash
git checkout main
git pull origin main
git checkout -b test/lai-weekly-v13-aws-dev
```

**Validation**:
```bash
git branch  # Doit afficher: * test/lai-weekly-v13-aws-dev
```

---

### Étape 1.2: Créer Client Config v13 (10min)

**Fichier**: `client-config-examples/production/lai_weekly_v13.yaml`

```bash
# Copier v12 → v13
cp client-config-examples/production/lai_weekly_v12.yaml \
   client-config-examples/production/lai_weekly_v13.yaml
```

**Modifications minimales**:
- `client_id: "lai_weekly_v12"` → `"lai_weekly_v13"`
- `name: "v12 (Test Domain Definition Fix)"` → `"v13 (Test AWS Dev Comparison)"`
- `template_version: "12.0.0"` → `"13.0.0"`
- `created_date: "2026-02-03"`
- `created_by: "Test E2E AWS Dev - Comparison v11/v12/v13"`

**Config identique à v12 pour comparaison**.

---

### Étape 1.3: Commit Git (5min)

```bash
git add client-config-examples/production/lai_weekly_v13.yaml

git commit -m "test: add lai_weekly_v13 for AWS dev comparison

- Copy lai_weekly_v12.yaml → lai_weekly_v13.yaml
- Identical config for v11/v12/v13 comparison
- Test E2E AWS dev environment

Refs: plan_test_e2e_lai_weekly_v13_aws_dev_2026-02-03.md"

git log -1 --oneline
```

---

### Étape 1.4: Sync Client Config vers S3 Dev (10min)

```bash
# Upload lai_weekly_v13.yaml
aws s3 cp client-config-examples/production/lai_weekly_v13.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v13.yaml \
  --profile rag-lai-prod --region eu-west-3

# Vérifier upload
aws s3 ls s3://vectora-inbox-config-dev/clients/ \
  --profile rag-lai-prod --region eu-west-3 | findstr lai_weekly_v13
```

**Validation**:
```bash
# Télécharger et comparer
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly_v13.yaml \
  .tmp/lai_weekly_v13_s3.yaml \
  --profile rag-lai-prod --region eu-west-3

diff client-config-examples/production/lai_weekly_v13.yaml .tmp/lai_weekly_v13_s3.yaml
# Doit afficher: (aucune différence)
```

---

## 📋 PHASE 2: TEST E2E AWS DEV (1h30)

### Étape 2.1: Test Ingest v13 (20min)

```bash
python scripts/invoke/invoke_ingest_v2.py \
  --client-id lai_weekly_v13 \
  --env dev
```

**Métriques attendues**:
- Items ingérés: ~29 (même période que v11/v12)
- Sources scrapées: 2 (lai_corporate_mvp, lai_press_mvp)
- StatusCode: 200

---

### Étape 2.2: Test Normalize-Score v13 (1h)

```bash
python scripts/invoke/invoke_normalize_score_v2.py \
  --event lai_weekly_v13
```

**Note**: Ajouter lai_weekly_v13 au script si nécessaire.

**Métriques attendues**:
- Items input: 29
- Items normalized: 29
- Items matched: ~14 (comme v12)
- Items scored: 29
- StatusCode: 200

---

### Étape 2.3: Télécharger Résultats v13 (10min)

```bash
# Créer dossier temporaire
mkdir .tmp\e2e\lai_weekly_v13

# Télécharger items curés
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v13/2026/02/03/items.json \
  .tmp/e2e/lai_weekly_v13/curated_items.json \
  --profile rag-lai-prod --region eu-west-3
```

---

## 📋 PHASE 3: ANALYSE COMPARATIVE (1h)

### Étape 3.1: Télécharger Résultats v11 et v12 (10min)

```bash
# v11
mkdir .tmp\e2e\lai_weekly_v11
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v11/2026/02/02/items.json \
  .tmp/e2e/lai_weekly_v11/curated_items.json \
  --profile rag-lai-prod --region eu-west-3

# v12 (déjà téléchargé normalement)
# Vérifier existence
dir .tmp\e2e\lai_weekly_v12\curated_items.json
```

---

### Étape 3.2: Script Analyse Comparative (30min)

**Fichier**: `scripts/analysis/compare_v11_v12_v13.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load_items(version):
    path = f'.tmp/e2e/lai_weekly_v{version}/curated_items.json'
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def analyze_version(items, version):
    total = len(items)
    matched = sum(1 for item in items if item.get('domain_scoring', {}).get('is_relevant'))
    match_rate = (matched / total * 100) if total > 0 else 0
    
    scores = [item.get('domain_scoring', {}).get('score', 0) 
              for item in items if item.get('domain_scoring', {}).get('is_relevant')]
    
    return {
        'version': version,
        'total': total,
        'matched': matched,
        'match_rate': match_rate,
        'score_avg': sum(scores)/len(scores) if scores else 0,
        'score_min': min(scores) if scores else 0,
        'score_max': max(scores) if scores else 0
    }

def main():
    print(f"\n{'='*70}")
    print(f"ANALYSE COMPARATIVE v11 vs v12 vs v13")
    print(f"{'='*70}\n")
    
    results = []
    for v in ['11', '12', '13']:
        try:
            items = load_items(v)
            result = analyze_version(items, v)
            results.append(result)
        except FileNotFoundError:
            print(f"⚠️ Fichier v{v} non trouvé, ignoré\n")
    
    # Tableau comparatif
    print(f"{'Version':<10} {'Total':<8} {'Matchés':<10} {'Taux':<10} {'Score Moy':<12} {'Min':<6} {'Max':<6}")
    print(f"{'-'*70}")
    
    for r in results:
        print(f"v{r['version']:<9} {r['total']:<8} {r['matched']:<10} "
              f"{r['match_rate']:.1f}%{'':<6} {r['score_avg']:.1f}{'':<8} "
              f"{r['score_min']:<6} {r['score_max']:<6}")
    
    # Évolution
    if len(results) >= 2:
        print(f"\n{'='*70}")
        print(f"ÉVOLUTION")
        print(f"{'='*70}\n")
        
        v11_rate = results[0]['match_rate']
        v12_rate = results[1]['match_rate']
        v13_rate = results[2]['match_rate'] if len(results) > 2 else 0
        
        print(f"v11 → v12: {v11_rate:.1f}% → {v12_rate:.1f}% ({v12_rate - v11_rate:+.1f} pts)")
        if len(results) > 2:
            print(f"v12 → v13: {v12_rate:.1f}% → {v13_rate:.1f}% ({v13_rate - v12_rate:+.1f} pts)")
            print(f"v11 → v13: {v11_rate:.1f}% → {v13_rate:.1f}% ({v13_rate - v11_rate:+.1f} pts)")
    
    # Items clés
    print(f"\n{'='*70}")
    print(f"ITEMS CLÉS (UZEDY®, MedinCell)")
    print(f"{'='*70}\n")
    
    for r in results:
        items = load_items(r['version'])
        print(f"v{r['version']}:")
        for item in items:
            title = item.get('title', '')
            if 'UZEDY' in title or 'MedinCell' in title:
                score = item.get('domain_scoring', {}).get('score', 0)
                is_relevant = item.get('domain_scoring', {}).get('is_relevant', False)
                print(f"  {title[:60]}: {score} ({'✅' if is_relevant else '❌'})")
        print()

if __name__ == '__main__':
    main()
```

**Exécution**:
```bash
python scripts/analysis/compare_v11_v12_v13.py
```

---

### Étape 3.3: Rapport Comparatif (20min)

**Fichier**: `docs/reports/e2e/test_e2e_v13_comparison_v11_v12_v13_2026-02-03.md`

**Contenu**:
```markdown
# Test E2E v13 - Comparaison v11/v12/v13

**Date**: 2026-02-03  
**Environnement**: AWS Dev  
**CANONICAL_VERSION**: 2.1

## Résultats Comparatifs

| Version | Total | Matchés | Taux | Score Moy | Min | Max |
|---------|-------|---------|------|-----------|-----|-----|
| v11 | X | X | X% | X | X | X |
| v12 | X | X | X% | X | X | X |
| v13 | X | X | X% | X | X | X |

## Évolution

- v11 → v12: X% → X% (+X pts)
- v12 → v13: X% → X% (+X pts)
- v11 → v13: X% → X% (+X pts)

## Items Clés

### UZEDY®
- v11: Score X
- v12: Score X
- v13: Score X

### MedinCell
- v11: Score X
- v12: Score X
- v13: Score X

## Conclusion

✅ Moteur stable: v12 ≈ v13
✅ Amélioration confirmée: v11 → v12/v13
```

---

## 📋 PHASE 4: FINALISATION (30min)

### Étape 4.1: Commit Résultats (10min)

```bash
git add scripts/analysis/compare_v11_v12_v13.py
git add docs/reports/e2e/test_e2e_v13_comparison_v11_v12_v13_2026-02-03.md

git commit -m "test: add v11/v12/v13 comparison analysis

- Add compare_v11_v12_v13.py script
- Add comparative E2E report
- Confirm v12/v13 stability and v11→v12 improvement

Results: v11 (X%) → v12 (X%) → v13 (X%)"
```

---

### Étape 4.2: Push Branche (5min)

```bash
git push -u origin test/lai-weekly-v13-aws-dev
```

---

### Étape 4.3: Décision Merge (15min)

**Si v12 ≈ v13** (différence <5%):
- ✅ Moteur stable
- ✅ Merge branche
- ✅ Documenter baseline v12/v13

**Si v13 >> v12** (amélioration >10%):
- ⚠️ Investiguer cause amélioration
- ⚠️ Vérifier données identiques
- ⚠️ Analyser différences config

**Si v13 << v12** (régression >10%):
- ❌ Investiguer cause régression
- ❌ Vérifier logs Lambda
- ❌ Ne pas merger

---

## 📊 CRITÈRES DE SUCCÈS

### Succès Complet ✅
- v13 exécuté sans erreur
- Taux matching v13 ≈ v12 (±5%)
- Items clés détectés (UZEDY®, MedinCell)
- Rapport comparatif généré

### Succès Partiel ⚠️
- v13 exécuté avec warnings
- Taux matching v13 différent v12 (5-10%)
- Investigation requise

### Échec ❌
- v13 erreur Lambda
- Taux matching v13 << v12 (>10% régression)
- Items clés non détectés

---

## 🔧 TROUBLESHOOTING

### Erreur "Client config not found"
```bash
# Vérifier S3
aws s3 ls s3://vectora-inbox-config-dev/clients/ \
  --profile rag-lai-prod --region eu-west-3 | findstr lai_weekly_v13

# Re-upload si nécessaire
aws s3 cp client-config-examples/production/lai_weekly_v13.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v13.yaml \
  --profile rag-lai-prod --region eu-west-3
```

### Erreur "No ingestion run found"
```bash
# Vérifier données ingérées
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v13/ --recursive \
  --profile rag-lai-prod --region eu-west-3

# Re-exécuter ingest si nécessaire
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v13 --env dev
```

### Script invoke manquant lai_weekly_v13
```bash
# Ajouter dans scripts/invoke/invoke_normalize_score_v2.py
# Section get_test_event():
"lai_weekly_v13": {
    "client_id": "lai_weekly_v13"
},
```

---

## 📝 CHECKLIST FINALE

- [ ] Branche test/lai-weekly-v13-aws-dev créée
- [ ] lai_weekly_v13.yaml créé (copie v12)
- [ ] Commit AVANT sync S3
- [ ] Client config uploadé S3 dev
- [ ] Ingest v13 exécuté (StatusCode 200)
- [ ] Normalize-score v13 exécuté (StatusCode 200)
- [ ] Résultats v11/v12/v13 téléchargés
- [ ] Script comparaison exécuté
- [ ] Rapport comparatif créé
- [ ] Résultats commités
- [ ] Branche poussée
- [ ] Décision merge prise

---

**Plan créé**: 2026-02-03  
**Durée estimée**: 3h  
**Conformité**: ✅ CRITICAL_RULES + Gouvernance
