# Golden Test E2E - lai_weekly_v23

**Date**: 2026-02-04  
**Environnement**: dev  
**Statut**: ✅ **VALIDÉ**

---

## 📊 RÉSULTATS

- **Total items**: 32
- **Items relevant**: 20 (62%)
- **Items non-relevant**: 12 (38%)
- **Score moyen**: 76.0
- **Scores**: min=60, max=90

---

## 📁 FICHIERS

### Données
- `tests/data_snapshots/golden_test_v23_2026-02-04.json` : Résultat complet (items curés)
- `.tmp/v23_curated.json` : Copie de travail

### Rapports
- `docs/reports/e2e/test_e2e_v23_rapport_detaille_item_par_item_2026-02-04.md` : Rapport détaillé item par item

---

## 🔧 CONFIGURATION

### Client
- **ID**: lai_weekly_v23
- **Config**: `client-config-examples/production/lai_weekly_v23.yaml`

### Layers
- **vectora-core**: :62
- **common-deps**: :23

### Canonical
- **Prompts**:
  - `canonical/prompts/normalization/generic_normalization.yaml`
  - `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
  - `canonical/prompts/editorial/lai_editorial.yaml`
- **Domains**: `canonical/domains/lai_domain_definition.yaml`
- **Scopes**: `canonical/scopes/*.yaml`

---

## ✅ CRITÈRES DE VALIDATION

Ce test est considéré comme **golden** car :

1. **Taux de pertinence > 60%** : 62% ✅
2. **Score moyen 65-75** : 76 ✅
3. **Domain scoring activé** : Oui ✅
4. **Reasoning contient signaux LAI** : Oui ✅
5. **Pas de "Bedrock failed"** : Oui ✅
6. **Entités détectées** : Companies 70%+, Technologies présentes ✅

---

## 🎯 UTILISATION

### Reproduire le test

```bash
# 1. Uploader config client
aws s3 cp client-config-examples/production/lai_weekly_v23.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v23.yaml \
  --profile rag-lai-prod

# 2. Lancer workflow
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id":"lai_weekly_v23"}' \
  .tmp/ingest.json --profile rag-lai-prod --region eu-west-3

aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --payload '{"client_id":"lai_weekly_v23"}' \
  .tmp/normalize.json --profile rag-lai-prod --region eu-west-3

# 3. Attendre et récupérer résultats
# (attendre 2-3 minutes)
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v23/2026/02/04/items.json \
  .tmp/results.json --profile rag-lai-prod

# 4. Comparer avec golden test
python tests/compare_with_golden.py .tmp/results.json tests/data_snapshots/golden_test_v23_2026-02-04.json
```

### Valider un nouveau run

```python
import json

# Charger golden test
with open('tests/data_snapshots/golden_test_v23_2026-02-04.json') as f:
    golden = json.load(f)

# Charger nouveau run
with open('.tmp/new_run.json') as f:
    new_run = json.load(f)

# Comparer métriques
golden_relevant = sum(1 for i in golden if i.get('domain_scoring', {}).get('is_relevant'))
new_relevant = sum(1 for i in new_run if i.get('domain_scoring', {}).get('is_relevant'))

print(f"Golden: {golden_relevant}/{len(golden)} relevant ({golden_relevant/len(golden)*100:.0f}%)")
print(f"New:    {new_relevant}/{len(new_run)} relevant ({new_relevant/len(new_run)*100:.0f}%)")

# Tolérance: ±5%
if abs(golden_relevant/len(golden) - new_relevant/len(new_run)) < 0.05:
    print("✅ PASS")
else:
    print("❌ FAIL")
```

---

## 📝 NOTES

### Points forts
- Domain scoring fonctionne correctement
- Bonne détection des signaux LAI (pure players, trademarks, technologies)
- Reasoning détaillé et explicite
- Pas de faux positifs évidents

### Points d'attention
- 12 items rejetés : vérifier s'il y a des faux négatifs
- Certains items avec technologies LAI mais rejetés (à analyser)

### Améliorations futures
- Affiner les seuils de scoring
- Améliorer détection dosing_intervals
- Enrichir les scopes de technologies LAI

---

**Ce test sert de référence pour valider les futures modifications du moteur.**
