# Plan Test Workflow Fresh Data - Vectora Inbox

**Date**: 2026-02-04  
**Objectif**: Valider workflow complet `ingest-v2 → normalize-score-v2 → newsletter-v2` en dev avec données RSS fraîches  
**Durée estimée**: 40-45 minutes  
**Environnement**: dev  

---

## 🎯 OBJECTIF

Valider le workflow complet avec des données RSS fraîches du jour pour confirmer que le système fonctionne correctement en conditions réelles.

---

## 📊 BASELINE DE RÉFÉRENCE (V17)

| Métrique | Valeur V17 | Seuil Min | Seuil Max |
|----------|------------|-----------|-----------|
| Items ingérés | 31 | 25 | 40 |
| Companies détectées | 74% | 70% | 100% |
| Items relevant | 64% | 60% | 80% |
| Score moyen | 71.5 | 65 | 85 |
| Faux négatifs | 0 | 0 | 1 |
| Domain scoring | 100% | 100% | 100% |

**Source**: `.q-context/GOLDEN_TEST_E2E.md`

---

## 📋 ÉTAPES DU PLAN

### ÉTAPE 1: PRÉPARATION (5 min)

**Actions**:
- Vérifier environnement AWS
- Créer nouveau client_id pour test isolé
- Backup état actuel (optionnel)

**Commandes**:
```bash
# Vérifier profil AWS
aws sts get-caller-identity --profile rag-lai-prod

# Créer snapshot (optionnel)
python scripts/snapshot/create_snapshot.py --description "Avant test workflow fresh data"
```

**Client ID**: `lai_weekly_v18`

---

### ÉTAPE 2: CONFIGURATION CLIENT (5 min)

**Actions**:
- Copier config lai_weekly_v17 → lai_weekly_v18
- Upload vers S3

**Commandes**:
```bash
# Copier config de référence
cp client-config-examples/production/lai_weekly_v17.yaml \
   client-config-examples/production/lai_weekly_v18.yaml

# Upload vers S3
aws s3 cp client-config-examples/production/lai_weekly_v18.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v18.yaml \
  --profile rag-lai-prod --region eu-west-3
```

**Paramètres**:
- `period_days: 7` (derniers 7 jours)
- `temporal_mode: balanced`
- Sources: Config v17 (bouquets LAI validés)

---

### ÉTAPE 3: EXÉCUTION WORKFLOW E2E (15-20 min)

**Option A - Script automatisé (RECOMMANDÉ)**:
```bash
python scripts/invoke/invoke_e2e_workflow.py \
  --client-id lai_weekly_v18 \
  --env dev
```

**Option B - Étape par étape**:
```bash
# 1. Ingest (2-3 min)
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id":"lai_weekly_v18"}' \
  .tmp/v18_ingest_response.json \
  --profile rag-lai-prod --region eu-west-3

# 2. Normalize-Score (10-15 min - ASYNCHRONE)
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --payload '{"client_id":"lai_weekly_v18"}' \
  .tmp/v18_normalize_response.json \
  --profile rag-lai-prod --region eu-west-3

# Attendre 10-15 min puis vérifier
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v18/ \
  --recursive --profile rag-lai-prod

# 3. Newsletter (2-3 min)
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload '{"client_id":"lai_weekly_v18"}' \
  .tmp/v18_newsletter_response.json \
  --profile rag-lai-prod --region eu-west-3
```

---

### ÉTAPE 4: RÉCUPÉRATION RÉSULTATS (2 min)

**Commandes**:
```bash
# Date du jour
TODAY=$(date +%Y/%m/%d)

# Télécharger items ingérés
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v18/$TODAY/items.json \
  .tmp/v18_ingested.json --profile rag-lai-prod

# Télécharger items curés
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v18/$TODAY/items.json \
  .tmp/v18_curated.json --profile rag-lai-prod

# Télécharger newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v18/$TODAY/newsletter.md \
  .tmp/v18_newsletter.md --profile rag-lai-prod
```

---

### ÉTAPE 5: ANALYSE MÉTRIQUES (5 min)

**Script analyse rapide**:
```bash
python -c "
import json

items = json.load(open('.tmp/v18_curated.json', encoding='utf-8'))

total = len(items)
with_ds = sum(1 for i in items if i.get('has_domain_scoring'))
relevant = sum(1 for i in items if i.get('domain_scoring',{}).get('is_relevant'))
companies = sum(1 for i in items if i.get('normalized_content',{}).get('entities',{}).get('companies'))
scores = [i.get('domain_scoring',{}).get('score',0) for i in items if i.get('has_domain_scoring')]
avg_score = sum(scores)/len(scores) if scores else 0

print('='*60)
print('MÉTRIQUES V18 vs V17 (BASELINE)')
print('='*60)
print(f'Items ingérés:       {total:2d} (V17: 31)')
print(f'Domain scoring:      {with_ds}/{total} ({with_ds/total*100:.0f}%) (V17: 100%)')
print(f'Companies:           {companies}/{total} ({companies/total*100:.0f}%) (V17: 74%)')
print(f'Items relevant:      {relevant}/{with_ds} ({relevant/with_ds*100:.0f}%) (V17: 64%)')
print(f'Score moyen:         {avg_score:.1f} (V17: 71.5)')
print('='*60)

print('\nVERDICT:')
if companies/total >= 0.70 and relevant/with_ds >= 0.60 and avg_score >= 65:
    print('✅ SUCCÈS - Toutes métriques >= seuils')
elif companies/total >= 0.65 and relevant/with_ds >= 0.55:
    print('⚠️ ATTENTION - Métriques proches seuils')
else:
    print('❌ ÉCHEC - Métriques < seuils')
"
```

---

### ÉTAPE 6: RAPPORT STRUCTURÉ (10 min)

**Créer rapport selon format Golden Test**:
```bash
cat > docs/reports/e2e/test_e2e_v18_rapport_$(date +%Y-%m-%d).md << 'EOF'
# Test E2E V18 - Données Fraîches

## Résumé Exécutif

**Verdict**: [À compléter]

Test workflow complet avec données RSS fraîches.

Résultats clés:
- Companies: X% (objectif 70%+) [Statut]
- Items relevant: X% (objectif 60%+) [Statut]
- Faux négatifs: X (objectif 0) [Statut]

**Décision**: [MERGE / CORRIGER / ROLLBACK]

## Métriques Comparatives

| Métrique | V17 | V18 | Evolution | Cible | Statut |
|----------|-----|-----|-----------|-------|--------|
| Items ingérés | 31 | X | +X% | 25-35 | ✅/❌ |
| Companies | 74% | X% | +X% | ≥70% | ✅/❌ |
| Items relevant | 64% | X% | +X% | ≥60% | ✅/❌ |
| Score moyen | 71.5 | X | +X | 65-85 | ✅/❌ |

## Distribution Sources

[À compléter]

## Top 5 Items Relevant

[À compléter]

## Analyse Faux Négatifs

[À compléter]

## Annexes

### Fichiers Générés
- `.tmp/v18_ingested.json`
- `.tmp/v18_curated.json`
- `.tmp/v18_newsletter.md`

### Versions
- vectora-core: [voir VERSION]
- canonical: [voir VERSION]
- client: lai_weekly_v18
- environnement: dev
EOF
```

---

### ÉTAPE 7: DÉCISION (2 min)

**Critères**:

✅ **SUCCÈS** (workflow validé):
- Companies ≥ 70%
- Items relevant ≥ 60%
- Score moyen 65-85
- 0-1 faux négatifs

⚠️ **ATTENTION** (à surveiller):
- 1-2 métriques légèrement < seuils
- Justification claire nécessaire

❌ **ÉCHEC** (investigation requise):
- 3+ métriques < seuils
- Faux négatifs > 1
- Régression vs V17

---

## ✅ CHECKLIST COMPLÈTE

**Avant exécution**:
- [ ] Profil AWS configuré (`rag-lai-prod`)
- [ ] Client ID choisi (`lai_weekly_v18`)
- [ ] Config client créée et uploadée S3
- [ ] Dossier `.tmp/` prêt

**Pendant exécution**:
- [ ] Ingest complété (2-3 min)
- [ ] Normalize-Score lancé (asynchrone)
- [ ] Attente 10-15 min
- [ ] Newsletter générée (2-3 min)

**Après exécution**:
- [ ] Résultats téléchargés depuis S3
- [ ] Métriques calculées
- [ ] Comparaison vs V17 effectuée
- [ ] Rapport créé selon format Golden Test
- [ ] Décision prise

---

## ⏱️ TEMPS TOTAL

- Préparation: 5 min
- Configuration: 5 min
- Exécution workflow: 15-20 min
- Analyse: 5 min
- Rapport: 10 min

**TOTAL: 40-45 minutes**

---

## 🎯 PROCHAINES ÉTAPES

**Si SUCCÈS**:
- Documenter dans rapport
- Archiver résultats
- Workflow validé

**Si ATTENTION/ÉCHEC**:
- Analyser logs Lambda (CloudWatch)
- Identifier items problématiques
- Ajuster configuration (voir blueprint tuning_guide)
- Re-tester

---

## 📚 RÉFÉRENCES

- Golden Test E2E: `.q-context/GOLDEN_TEST_E2E.md`
- Blueprint: `docs/architecture/blueprint-v2-ACTUAL-2026.yaml`
- Workflow: `.q-context/00-START-HERE.md`
- Règles critiques: `.q-context/CRITICAL_RULES.md`

---

**Plan créé**: 2026-02-04  
**Statut**: PRÊT À EXÉCUTER
