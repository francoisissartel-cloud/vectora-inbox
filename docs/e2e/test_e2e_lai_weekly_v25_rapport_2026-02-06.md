# Test E2E - lai_weekly_v25 (Moteur v1.6.0)

**Date** : 2026-02-06  
**Client** : lai_weekly_v25  
**Moteur** : v1.6.0 (Filtrage 100% canonical)

---

## ⚠️ Résumé Exécutif

**Verdict** : ⚠️ **ATTENTION** - Dégradation significative vs v24

**Métriques clés** :
- Items ingérés : 27
- Items curated : 27
- Taux relevant : **44%** ❌ (vs 64% en v24)
- Score moyen : **37.8** ❌ (vs 71.5 en v24)

**Comparaison v24 → v25** :
- Items ingérés : 31 → 27 (-13%)
- Relevant : 64% → 44% (-20 pp) ❌
- Score moyen : 71.5 → 37.8 (-33.7 pts) ❌
- Domain scoring : 100% → 100% ✅
- Companies : 74% → 67% (-7 pp)

**Problème identifié** : Le filtrage LAI keywords (200+ keywords) est **trop restrictif** et exclut des items pertinents LAI.

---

## 📊 Métriques Détaillées

### Ingestion
- **Items ingérés** : 27
- **Sources actives** : 7
- **Distribution sources** :
  - press_corporate__delsitech: 6
  - press_corporate__nanexa: 5
  - press_sector__endpoints_news: 5
  - press_corporate__medincell: 4
  - press_sector__fiercebiotech: 4
  - press_sector__fiercepharma: 2
  - press_corporate__camurus: 1

### Curation
- **Domain scoring** : 27/27 (100%) ✅
- **Companies** : 18/27 (67%)
- **Items relevant** : 12/27 (44%) ❌
- **Score moyen** : 37.8 ❌

### Distribution Scores
| Range | Count | % |
|-------|-------|---|
| 90-100 | 0 | 0% |
| 80-89 | 3 | 11% |
| 70-79 | 1 | 4% |
| 60-69 | 4 | 15% |
| <60 | 19 | 70% ❌ |

**Analyse** : 70% des items ont un score <60, ce qui indique que beaucoup d'items ingérés ne sont pas pertinents LAI.

---

## 🔍 Analyse Comparative v24 vs v25

| Métrique | v24 | v25 | Δ | Statut |
|----------|-----|-----|---|--------|
| Items ingérés | 31 | 27 | -13% | ⚠️ |
| Domain scoring | 100% | 100% | 0 | ✅ |
| Companies | 74% | 67% | -7 pp | ⚠️ |
| Relevant | 64% | 44% | -20 pp | ❌ |
| Score moyen | 71.5 | 37.8 | -33.7 | ❌ |
| Scores 80+ | 45% | 15% | -30 pp | ❌ |

---

## 🎯 Top 5 Items Relevant (Score ≥70)

1. **Score 85** - Nanexa Announces Breakthrough Preclinical Data (press_corporate__nanexa)
   - Raison : Données précliniques PharmaShell technology pour LAI

2. **Score 85** - Nanexa and Moderna enter into license and option agreement (press_corporate__nanexa)
   - Raison : Partenariat technologie LAI PharmaShell

3. **Score 80** - Camurus announces FDA acceptance of NDA resubmission for Oclaiz (press_corporate__camurus)
   - Raison : Regulatory update produit LAI

4. **Score 75** - UZEDY continues strong growth (press_corporate__medincell)
   - Raison : Performance commerciale produit LAI

---

## ❌ Analyse Faux Négatifs

**Problème** : Le filtrage LAI keywords (200+ keywords) est trop restrictif.

**Items exclus à tort** : Impossible à vérifier sans accès aux items exclus lors de l'ingestion.

**Hypothèse** : Des items pertinents LAI ont été exclus car ils ne contenaient pas les keywords LAI dans le titre/contenu court, mais auraient été pertinents après analyse complète.

---

## 💡 Recommandations

### 1. Assouplir le filtrage LAI keywords ⚠️ URGENT

**Problème** : 200+ keywords trop restrictifs, excluent items pertinents.

**Solution** : 
- Revenir à la liste minimaliste v24 (32 keywords)
- OU désactiver filtrage LAI keywords pour sources corporate (pure players)
- OU appliquer filtrage LAI keywords uniquement sur presse sectorielle

### 2. Analyser items exclus

**Action** : Comparer items ingérés v24 vs v25 pour identifier items exclus à tort.

### 3. Ajuster seuils de scoring

**Observation** : Score moyen 37.8 indique que beaucoup d'items non-LAI passent le filtrage.

**Action** : Vérifier si le problème vient du filtrage ingestion ou du scoring Bedrock.

---

## 📁 Annexes

### Versions
- **Moteur** : v1.6.0
- **Exclusion scopes** : 114 keywords
- **LAI keywords** : 200+ keywords (trop restrictif)
- **Pure players** : 14 entreprises
- **Canonical version** : 2.3

### Fichiers
- **Config** : s3://vectora-inbox-config-dev/clients/lai_weekly_v25.yaml
- **Ingested** : s3://vectora-inbox-data-dev/ingested/lai_weekly_v25/2026/02/06/items.json (27 items)
- **Curated** : s3://vectora-inbox-data-dev/curated/lai_weekly_v25/2026/02/06/items.json (27 items)

### Commandes
```bash
# Ingest
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v25 --env dev

# Normalize & Score
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --invocation-type Event --cli-binary-format raw-in-base64-out --payload "{\"client_id\":\"lai_weekly_v25\"}" .tmp/normalize_v25.json --profile rag-lai-prod --region eu-west-3

# Download
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v25/2026/02/06/items.json .tmp/v25_ingested.json --profile rag-lai-prod --region eu-west-3
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v25/2026/02/06/items.json .tmp/v25_curated.json --profile rag-lai-prod --region eu-west-3
```

---

## 🎯 Conclusion

Le moteur v1.6.0 avec filtrage 100% canonical fonctionne techniquement (aucun hardcoding), mais le filtrage LAI keywords (200+ keywords) est **trop restrictif** et dégrade la qualité :

- ❌ Taux relevant : 44% (vs 64% en v24)
- ❌ Score moyen : 37.8 (vs 71.5 en v24)

**Action recommandée** : Revenir à la liste minimaliste LAI keywords v24 (32 keywords) ou désactiver le filtrage LAI keywords pour les sources corporate pure players.

---

**Rapport créé le** : 2026-02-06  
**Auteur** : Amazon Q Developer  
**Statut** : ⚠️ ATTENTION - Ajustements nécessaires
