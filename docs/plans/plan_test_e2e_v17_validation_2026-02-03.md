# Plan Test E2E V17 - Validation Corrections V16 avec Données Fraîches

**Date**: 2026-02-03  
**Objectif**: Valider workflow complet Ingest → Normalize avec analyse item par item  
**Client**: lai_weekly_v17 (données fraîches)  
**Durée**: 1h

---

## 🎯 OBJECTIF

Valider que nos corrections V16 fonctionnent sur AWS avec données fraîches:
1. ✅ Companies détectées (23/31 en V16)
2. ✅ Domain scoring fonctionnel (20/31 relevant)
3. ✅ Moins de faux positifs/négatifs vs V15
4. ✅ Workflow Ingest → Normalize complet

**Note**: On ne teste PAS la newsletter (Lambda en panne connue)

---

## 📋 PRÉREQUIS

- [x] Branche `fix/v16-corrections-post-e2e-v15` (11 commits)
- [x] Layers déployés (vectora-core-dev:55)
- [x] Canonical v2.3 sur S3
- [x] Token SSO valide

---

## 🚀 PHASE 1: Préparation Client V17 (10min)

### Étape 1.1: Créer Config Client

```bash
# Copier V16 → V17
cp client-config-examples/production/lai_weekly_v16.yaml \
   client-config-examples/production/lai_weekly_v17.yaml
```

**Modifications**:
```yaml
client_profile:
  name: "LAI Intelligence Weekly v17 (Test E2E Données Fraîches)"
  client_id: "lai_weekly_v17"

metadata:
  template_version: "17.0.0"
  created_date: "2026-02-03"
  created_by: "Test E2E V17 - Validation corrections V16 avec données fraîches"
  canonical_version: "2.3"
  
  creation_notes: |
    Test E2E V17 - Validation corrections V16:
    - Companies détectées (cible: 70%+)
    - Domain scoring fonctionnel (cible: 60%+ relevant)
    - Analyse item par item
    - Comparaison vs V15/V16
    
    ATTENDU:
    - Items ingérés: 25-35
    - Companies: 70%+ items
    - Items relevant: 60%+
    - Faux positifs: 0
    - Faux négatifs: <2
```

### Étape 1.2: Upload Config

```bash
aws s3 cp client-config-examples/production/lai_weekly_v17.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v17.yaml \
  --profile rag-lai-prod --region eu-west-3

# Vérifier
aws s3 ls s3://vectora-inbox-config-dev/clients/ \
  --profile rag-lai-prod | findstr lai_weekly_v17
```

---

## 🔄 PHASE 2: Exécution Workflow (20min)

### Étape 2.1: Ingestion (2min)

```bash
# Créer payload
echo {"client_id": "lai_weekly_v17"} > .tmp/event_v17.json

# Invoquer
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload file://c:/Users/franc/OneDrive/Bureau/vectora-inbox/.tmp/event_v17.json \
  --profile rag-lai-prod --region eu-west-3 \
  .tmp/ingest_v17_response.json

# Lire réponse
type .tmp\ingest_v17_response.json
```

**Validation**:
- StatusCode: 200
- items_ingested: 25-35
- execution_time_seconds: <30s

### Étape 2.2: Télécharger Items Ingérés (1min)

```bash
# Attendre 10s
powershell -Command "Start-Sleep -Seconds 10"

# Télécharger
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v17/2026/02/03/items.json \
  .tmp/v17_ingested.json \
  --profile rag-lai-prod --region eu-west-3
```

### Étape 2.3: Normalisation (15min)

```bash
# Invoquer (asynchrone)
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload file://c:/Users/franc/OneDrive/Bureau/vectora-inbox/.tmp/event_v17.json \
  --profile rag-lai-prod --region eu-west-3 \
  .tmp/normalize_v17_response.json

# StatusCode attendu: 202 (accepté)
type .tmp\normalize_v17_response.json
```

**Attendre 10-15 minutes** (31 items × 2 appels Bedrock = ~10-15 min)

### Étape 2.4: Télécharger Items Normalisés (2min)

```bash
# Vérifier présence fichier
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v17/2026/02/03/ \
  --profile rag-lai-prod --region eu-west-3

# Télécharger
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v17/2026/02/03/items.json \
  .tmp/v17_curated.json \
  --profile rag-lai-prod --region eu-west-3
```

**Note**: Le fichier est dans `curated/` pas `normalized/` (comportement normal)

---

## 📊 PHASE 3: Analyse Détaillée (30min)

### Étape 3.1: Métriques Globales (5min)

```bash
python -c "
import json

# Charger données
ingested = json.load(open('.tmp/v17_ingested.json', encoding='utf-8'))
curated = json.load(open('.tmp/v17_curated.json', encoding='utf-8'))

print('=== MÉTRIQUES GLOBALES V17 ===\n')

# Ingestion
print(f'Items ingérés: {len(ingested)}')
sources = {}
for item in ingested:
    src = item.get('source_key', 'unknown')
    sources[src] = sources.get(src, 0) + 1
print('Sources:')
for src, count in sorted(sources.items()):
    print(f'  {src}: {count}')

print()

# Normalisation
print(f'Items normalisés: {len(curated)}')

# Companies
items_with_companies = [i for i in curated if i.get('normalized_content', {}).get('entities', {}).get('companies')]
print(f'Items avec companies: {len(items_with_companies)}/{len(curated)} ({len(items_with_companies)*100//len(curated)}%)')

# Domain scoring
items_with_ds = [i for i in curated if i.get('domain_scoring')]
items_relevant = [i for i in curated if i.get('domain_scoring', {}).get('is_relevant')]
scores = [i['domain_scoring']['score'] for i in curated if i.get('domain_scoring', {}).get('score')]

print(f'Items avec domain_scoring: {len(items_with_ds)}/{len(curated)} ({len(items_with_ds)*100//len(curated)}%)')
print(f'Items relevant: {len(items_relevant)}/{len(items_with_ds)} ({len(items_relevant)*100//len(items_with_ds) if items_with_ds else 0}%)')
print(f'Score moyen: {sum(scores)/len(scores) if scores else 0:.1f}/100')
print(f'Scores distribution:')
print(f'  80-100: {len([s for s in scores if s >= 80])}')
print(f'  60-79: {len([s for s in scores if 60 <= s < 80])}')
print(f'  40-59: {len([s for s in scores if 40 <= s < 60])}')
print(f'  0-39: {len([s for s in scores if s < 40])}')
"
```

### Étape 3.2: Analyse Item par Item - Top 10 Relevant (10min)

```bash
python -c "
import json

curated = json.load(open('.tmp/v17_curated.json', encoding='utf-8'))

# Trier par score
items_sorted = sorted(curated, key=lambda x: x.get('domain_scoring', {}).get('score', 0), reverse=True)

print('=== TOP 10 ITEMS RELEVANT ===\n')

for i, item in enumerate(items_sorted[:10], 1):
    ds = item.get('domain_scoring', {})
    entities = item.get('normalized_content', {}).get('entities', {})
    
    print(f'--- ITEM #{i} ---')
    print(f'Title: {item.get(\"title\", \"\")[:80]}...')
    print(f'Source: {item.get(\"source_key\", \"unknown\")}')
    print(f'Event type: {item.get(\"normalized_content\", {}).get(\"event_classification\", {}).get(\"primary_type\", \"unknown\")}')
    print(f'')
    print(f'ENTITIES:')
    print(f'  Companies: {entities.get(\"companies\", [])}')
    print(f'  Molecules: {entities.get(\"molecules\", [])}')
    print(f'  Technologies: {entities.get(\"technologies\", [])}')
    print(f'  Dosing: {entities.get(\"dosing_intervals\", [])}')
    print(f'')
    print(f'DOMAIN SCORING:')
    print(f'  Relevant: {ds.get(\"is_relevant\", False)}')
    print(f'  Score: {ds.get(\"score\", 0)}/100')
    print(f'  Confidence: {ds.get(\"confidence\", \"unknown\")}')
    signals = ds.get('signals_detected', {})
    print(f'  Signals:')
    print(f'    Strong: {signals.get(\"strong\", [])}')
    print(f'    Medium: {signals.get(\"medium\", [])}')
    print(f'  Reasoning: {ds.get(\"reasoning\", \"\")[:150]}...')
    print()
" > .tmp/v17_analysis_top10.txt

type .tmp\v17_analysis_top10.txt
```

### Étape 3.3: Analyse Faux Négatifs Potentiels (10min)

**Critères faux négatif**: Item rejeté (score=0) mais contient signaux LAI

```bash
python -c "
import json

curated = json.load(open('.tmp/v17_curated.json', encoding='utf-8'))

# Items rejetés
rejected = [i for i in curated if not i.get('domain_scoring', {}).get('is_relevant')]

print('=== ANALYSE FAUX NÉGATIFS POTENTIELS ===\n')
print(f'Items rejetés: {len(rejected)}\n')

# Chercher items avec signaux LAI mais rejetés
suspicious = []
for item in rejected:
    entities = item.get('normalized_content', {}).get('entities', {})
    
    # Signaux LAI
    has_dosing = len(entities.get('dosing_intervals', [])) > 0
    has_tech = len(entities.get('technologies', [])) > 0
    has_trademark = len(entities.get('trademarks', [])) > 0
    
    if has_dosing or has_tech or has_trademark:
        suspicious.append(item)

print(f'Items suspects (rejetés mais avec signaux LAI): {len(suspicious)}\n')

for i, item in enumerate(suspicious[:5], 1):
    ds = item.get('domain_scoring', {})
    entities = item.get('normalized_content', {}).get('entities', {})
    
    print(f'--- SUSPECT #{i} ---')
    print(f'Title: {item.get(\"title\", \"\")[:80]}...')
    print(f'Companies: {entities.get(\"companies\", [])}')
    print(f'Dosing: {entities.get(\"dosing_intervals\", [])}')
    print(f'Technologies: {entities.get(\"technologies\", [])}')
    print(f'Trademarks: {entities.get(\"trademarks\", [])}')
    print(f'Score: {ds.get(\"score\", 0)}')
    print(f'Reasoning: {ds.get(\"reasoning\", \"\")[:150]}...')
    print()
" > .tmp/v17_analysis_false_negatives.txt

type .tmp\v17_analysis_false_negatives.txt
```

### Étape 3.4: Comparaison V15 vs V17 (5min)

**Créer tableau comparatif**:

```bash
python -c "
import json

v17 = json.load(open('.tmp/v17_curated.json', encoding='utf-8'))

# Métriques V17
items_total = len(v17)
items_companies = len([i for i in v17 if i.get('normalized_content', {}).get('entities', {}).get('companies')])
items_relevant = len([i for i in v17 if i.get('domain_scoring', {}).get('is_relevant')])
scores = [i['domain_scoring']['score'] for i in v17 if i.get('domain_scoring', {}).get('score')]
score_moyen = sum(scores)/len(scores) if scores else 0

print('=== COMPARAISON V15 vs V17 ===\n')
print('| Métrique | V15 | V17 | Évolution |')
print('|----------|-----|-----|-----------|')
print(f'| Items ingérés | 29 | {items_total} | {items_total-29:+d} |')
print(f'| Companies détectées | 0 (0%) | {items_companies} ({items_companies*100//items_total}%) | +{items_companies*100//items_total}% |')
print(f'| Items relevant | 12 (41%) | {items_relevant} ({items_relevant*100//items_total}%) | {items_relevant*100//items_total-41:+d}% |')
print(f'| Score moyen | 81.7 | {score_moyen:.1f} | {score_moyen-81.7:+.1f} |')
print()
print('VERDICT:')
if items_companies*100//items_total >= 70 and items_relevant*100//items_total >= 60:
    print('✅ SUCCÈS - Objectifs atteints')
elif items_companies*100//items_total >= 50:
    print('⚠️ PARTIEL - Amélioration mais objectifs non atteints')
else:
    print('❌ ÉCHEC - Pas d\\'amélioration significative')
" > .tmp/v17_comparison.txt

type .tmp\v17_comparison.txt
```

---

## ✅ PHASE 4: Validation Critères Succès (10min)

### Checklist Validation

**Workflow**:
- [ ] Ingestion: items.json créé dans `ingested/`
- [ ] Normalisation: items.json créé dans `curated/`
- [ ] Durée totale: <20 min

**Qualité Détection**:
- [ ] Companies: ≥70% items
- [ ] Domain scoring: 100% items
- [ ] Items relevant: ≥60%
- [ ] Score moyen: 70-90

**Amélioration vs V15**:
- [ ] Companies: +70% (0% → 70%+)
- [ ] Items relevant: +20% (41% → 60%+)
- [ ] Faux négatifs: <2 items

**Cas d'Usage Spécifiques** (si présents dans données):
- [ ] Item avec dosing dans titre: Détecté ✅
- [ ] Item grant/funding: Classé partnership ✅
- [ ] Item pure_player: Score élevé ✅
- [ ] Item manufacturing générique: Rejeté ✅

---

## 📝 PHASE 5: Rapport Final (10min)

### Créer Rapport

**Fichier**: `docs/reports/e2e/test_e2e_v17_rapport_2026-02-03.md`

```markdown
# Rapport Test E2E V17 - Validation Corrections V16

**Date**: 2026-02-03
**Client**: lai_weekly_v17
**Environnement**: dev
**Durée**: Xmin

## Résumé Exécutif

✅ / ⚠️ / ❌ **[VERDICT]**

## Métriques

| Métrique | V15 | V17 | Évolution | Cible | Statut |
|----------|-----|-----|-----------|-------|--------|
| Items ingérés | 29 | X | +X | 25-35 | ✅/❌ |
| Companies | 0 (0%) | X (X%) | +X% | ≥70% | ✅/❌ |
| Items relevant | 12 (41%) | X (X%) | +X% | ≥60% | ✅/❌ |
| Score moyen | 81.7 | X | +X | 70-90 | ✅/❌ |

## Top 5 Items

[Copier depuis analyse]

## Faux Négatifs

[Copier depuis analyse]

## Problèmes Détectés

[Liste]

## Recommandations

[Actions]

## Conclusion

[Synthèse]
```

### Commit Rapport

```bash
git add docs/reports/e2e/test_e2e_v17_rapport_2026-02-03.md
git add .tmp/v17_*.txt
git commit -m "test: rapport E2E V17 - validation corrections V16

- Items ingérés: X
- Companies: X% (vs 0% en V15)
- Items relevant: X% (vs 41% en V15)
- Analyse item par item complète

[VERDICT]: ✅/⚠️/❌"
```

---

## 🎯 CRITÈRES DÉCISION FINALE

### ✅ SUCCÈS (Merge dans develop)

**Conditions**:
- Companies: ≥70% items
- Items relevant: ≥60%
- Faux négatifs: ≤2
- Workflow complet fonctionnel

**Actions**:
1. Push branche
2. Créer PR
3. Merge dans develop
4. Tag v1.4.2

### ⚠️ SUCCÈS PARTIEL (Merge avec réserves)

**Conditions**:
- Companies: 50-69% items
- Items relevant: 50-59%
- Amélioration vs V15 confirmée

**Actions**:
1. Documenter limitations
2. Créer issues pour améliorations
3. Merge quand même
4. Planifier corrections

### ❌ ÉCHEC (Ne pas merger)

**Conditions**:
- Companies: <50% items
- Pas d'amélioration vs V15
- Workflow cassé

**Actions**:
1. Analyser causes
2. Corriger bugs
3. Retest
4. Ne pas merger

---

## 💡 NOTES IMPORTANTES

### Pourquoi `curated/` et pas `normalized/` ?

Le fichier est dans `curated/` car:
1. Lambda normalize-score-v2 écrit directement dans `curated/`
2. C'est le comportement normal (pas un bug)
3. Le fichier contient bien les données normalisées + domain_scoring

### Pourquoi Domain Scoring Fonctionne ?

Si domain_scoring est présent dans `curated/`, c'est que:
1. ✅ Normalisation a tourné
2. ✅ Bedrock a répondu (2 appels par item)
3. ✅ Domain scoring calculé
4. ✅ Fichier écrit sur S3

Le "problème" V16 n'était pas un vrai problème, juste une confusion sur le nom du dossier.

---

**Plan créé**: 2026-02-03 20:00  
**Durée estimée**: 1h  
**Conformité Q Context**: ✅ 100%  
**Base template**: test-e2e-aws-template.md v2.0
