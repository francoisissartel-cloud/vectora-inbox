# Plan Test E2E - lai_weekly_v25 (Moteur v1.6.0)

**Date**: 2026-02-06  
**Objectif**: Tester le nouveau moteur v1.6.0 avec filtrage 100% canonical  
**Durée estimée**: 30 min  
**Client**: lai_weekly_v25 (nouveau)

---

## Contexte

**Moteur v1.6.0** :
- ✅ Exclusion scopes depuis S3 (114 keywords)
- ✅ Pure players depuis S3 (14 entreprises)
- ✅ LAI keywords depuis S3 (200+ keywords)
- ✅ Aucun hardcoding

**Baseline** : lai_weekly_v24 (moteur v24 avec hardcoding partiel)

---

## Phase 1 : Préparation (5 min)

### 1.1 Créer client config lai_weekly_v25

```bash
# Copier config v24
cp clients/lai_weekly_v24.yaml clients/lai_weekly_v25.yaml

# Éditer : changer client_id
# client_id: lai_weekly_v25
```

### 1.2 Upload config sur S3

```bash
aws s3 cp clients/lai_weekly_v25.yaml s3://vectora-inbox-config-dev/clients/lai_weekly_v25.yaml --profile rag-lai-prod --region eu-west-3
```

---

## Phase 2 : Exécution E2E (15 min)

### 2.1 Ingest

```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id":"lai_weekly_v25"}' \
  .tmp/ingest_v25.json \
  --profile rag-lai-prod --region eu-west-3
```

**Attendre** : 20 secondes

### 2.2 Télécharger items ingérés

```bash
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v25/2026/02/06/items.json .tmp/v25_ingested.json --profile rag-lai-prod --region eu-west-3
```

### 2.3 Normalize & Score

```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --payload '{"client_id":"lai_weekly_v25"}' \
  .tmp/normalize_v25.json \
  --profile rag-lai-prod --region eu-west-3
```

**Attendre** : 5-10 minutes

### 2.4 Télécharger items curated

```bash
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v25/2026/02/06/items.json .tmp/v25_curated.json --profile rag-lai-prod --region eu-west-3
```

---

## Phase 3 : Analyse (10 min)

### 3.1 Métriques ingestion

```python
import json
items = json.load(open('.tmp/v25_ingested.json', encoding='utf-8'))
print(f"Items ingérés: {len(items)}")

# Par source
from collections import Counter
sources = Counter([i.get('source_key','') for i in items])
for src, count in sources.most_common():
    print(f"  {src}: {count}")
```

### 3.2 Métriques curation

```python
import json
items = json.load(open('.tmp/v25_curated.json', encoding='utf-8'))

total = len(items)
with_ds = sum(1 for i in items if i.get('has_domain_scoring'))
relevant = sum(1 for i in items if i.get('domain_scoring',{}).get('is_relevant'))
companies = sum(1 for i in items if i.get('normalized_content',{}).get('entities',{}).get('companies'))
scores = [i.get('domain_scoring',{}).get('score',0) for i in items if i.get('has_domain_scoring')]

print(f"Total items: {total}")
print(f"Domain scoring: {with_ds}/{total} ({with_ds/total*100:.0f}%)")
print(f"Companies: {companies}/{total} ({companies/total*100:.0f}%)")
print(f"Relevant: {relevant}/{with_ds} ({relevant/with_ds*100:.0f}%)")
print(f"Score moyen: {sum(scores)/len(scores):.1f}")
```

### 3.3 Distribution sources

```python
sources = Counter([i.get('source_key','') for i in items])
for src, count in sources.most_common():
    print(f"  {src}: {count}")
```

### 3.4 Distribution scores

```python
score_ranges = {
    '90-100': sum(1 for s in scores if 90 <= s <= 100),
    '80-89': sum(1 for s in scores if 80 <= s < 90),
    '70-79': sum(1 for s in scores if 70 <= s < 80),
    '60-69': sum(1 for s in scores if 60 <= s < 70),
    '<60': sum(1 for s in scores if s < 60)
}
for range_name, count in score_ranges.items():
    print(f"  {range_name}: {count}")
```

---

## Phase 4 : Rapport (création manuelle)

Créer `docs/e2e/test_e2e_lai_weekly_v25_rapport_2026-02-06.md` avec :

### Structure (suivre test-e2e-gold-standard.md)

```markdown
# Test E2E - lai_weekly_v25 (Moteur v1.6.0)

## Résumé Exécutif

**Verdict** : [✅ SUCCÈS / ⚠️ ATTENTION / ❌ ÉCHEC]

**Métriques clés** :
- Items ingérés : X
- Items curated : X
- Taux relevant : X%
- Score moyen : X

**Comparaison v24 → v25** :
- Items ingérés : 31 → X ([+/-]X%)
- Relevant : 64% → X% ([+/-]X pp)
- Score moyen : 71.5 → X ([+/-]X pts)

## Métriques Détaillées

### Ingestion
- Items ingérés : X
- Sources actives : X
- Distribution sources : [tableau]

### Curation
- Domain scoring : X/X (X%)
- Companies : X/X (X%)
- Items relevant : X/X (X%)
- Score moyen : X

### Distribution Scores
[Tableau distribution]

## Top 5 Items Relevant

[Liste avec titre, source, score, raison]

## Analyse Faux Négatifs

[Items pertinents LAI exclus à tort]

## Recommandations

[Actions d'amélioration]

## Annexes

### Versions
- Moteur : v1.6.0
- Exclusion scopes : 114 keywords
- LAI keywords : 200+ keywords
- Pure players : 14 entreprises

### Fichiers
- Ingested : s3://vectora-inbox-data-dev/ingested/lai_weekly_v25/2026/02/06/items.json
- Curated : s3://vectora-inbox-data-dev/curated/lai_weekly_v25/2026/02/06/items.json
```

---

## Critères de Succès

**vs v24 (baseline)** :

- [ ] Items ingérés : 20-35 (acceptable)
- [ ] Domain scoring : ≥95%
- [ ] Companies : ≥70%
- [ ] Relevant : ≥60%
- [ ] Score moyen : ≥70
- [ ] Faux négatifs : 0

**Verdict** :
- ✅ SUCCÈS : Toutes métriques ≥ baseline
- ⚠️ ATTENTION : 1-2 métriques < baseline
- ❌ ÉCHEC : 3+ métriques < baseline

---

## Commandes Rapides

```bash
# Tout en une fois
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev --payload '{"client_id":"lai_weekly_v25"}' .tmp/ingest_v25.json --profile rag-lai-prod --region eu-west-3 && \
sleep 20 && \
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v25/2026/02/06/items.json .tmp/v25_ingested.json --profile rag-lai-prod --region eu-west-3 && \
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --invocation-type Event --payload '{"client_id":"lai_weekly_v25"}' .tmp/normalize_v25.json --profile rag-lai-prod --region eu-west-3 && \
echo "Attendre 5-10 min puis:" && \
echo "aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v25/2026/02/06/items.json .tmp/v25_curated.json --profile rag-lai-prod --region eu-west-3"
```

---

**Plan créé le** : 2026-02-06  
**Statut** : Prêt pour exécution
