# Rapport Test E2E v14 - Canonical v2.2

**Date**: 2026-02-03  
**Client**: lai_weekly_v14  
**Canonical**: v2.2  
**Statut**: ⚠️ COMPLÉTÉ - 0% MATCHING PERSISTANT

---

## ✅ ACTIONS RÉALISÉES

### 1. Création lai_weekly_v14.yaml ✅

**Base**: lai_weekly_v12.yaml  
**Modifications**:
- client_id: `lai_weekly_v14`
- canonical_version: `"2.2"` (au lieu de 2.1)
- template_version: `"14.0.0"`
- notification_email: `lai-weekly-v14@vectora.com`

### 2. Upload S3 ✅

```bash
aws s3 cp lai_weekly_v14.yaml s3://vectora-inbox-config-dev/clients/
```

**Résultat**: ✅ 9.2 KiB uploadé

### 3. Copie Données v13 → v14 ✅

```bash
aws s3 sync s3://.../ingested/lai_weekly_v13/ s3://.../ingested/lai_weekly_v14/
```

**Résultat**: ✅ 25.8 KiB copié (29 items)

### 4. Test E2E Lambda ✅

```bash
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v14"}' response_v14.json
```

**Résultat**: ✅ StatusCode 200

---

## 📊 RÉSULTATS TEST E2E v14

### Statistiques Globales

| Métrique | Valeur | Statut |
|----------|--------|--------|
| **StatusCode** | 200 | ✅ |
| **Items input** | 29 | ✅ |
| **Items normalized** | 29 | ✅ |
| **Items matched** | 0 | ⚠️ |
| **Items scored** | 29 | ✅ |
| **Processing time** | 162.7s | ✅ |
| **Normalization success rate** | 100% | ✅ |
| **Matching success rate** | 0% | ⚠️ |

### Distribution des Scores

| Catégorie | Count | Seuil |
|-----------|-------|-------|
| **High scores** | 0 | ≥ 25 |
| **Medium scores** | 0 | 10-24 |
| **Low scores** | 12 | < 10 |
| **No score** | 17 | 0 |

**Scores détaillés**:
- Min: 0.2
- Max: 3.3
- Avg: 1.74

### Entités Détectées

| Type | Count |
|------|-------|
| Companies | 0 |
| Molecules | 9 |
| Technologies | 0 |
| Trademarks | 8 |

---

## ⚠️ PROBLÈME PERSISTANT: 0% MATCHING

### Analyse

**Observation**: Même avec Canonical v2.2, 0/29 items matched

**Scores trop bas**:
- Max score: 3.3 (seuil: 25)
- 12 items avec score < 10
- 17 items avec score = 0

**Hypothèses**:

1. **Seuil trop élevé** ⚠️
   - `min_domain_score: 0.25` (25 points)
   - Max score obtenu: 3.3
   - Écart: -87%

2. **Canonical v2.2 trop strict** ⚠️
   - `financial_results` base_score = 0
   - `hybrid_company` boost = 0 (sans signaux)
   - Exclusions manufacturing
   - Règles strictes appliquées

3. **Entités non détectées** ⚠️
   - 0 companies détectées
   - 0 technologies détectées
   - Seulement 9 molecules + 8 trademarks

---

## 🔍 COMPARAISON VERSIONS

### Tests Local (Phase 5)

| Métrique | Valeur |
|----------|--------|
| Items testés | 3 |
| Items matched | 2 (67%) |
| Scores | 85, 75, 0 |
| Canonical | v2.2 local |

### Tests AWS v12 (Phase 7)

| Métrique | Valeur |
|----------|--------|
| Items input | 29 |
| Items matched | 0 (0%) |
| Canonical | v2.2 S3 |

### Tests AWS v14 (Actuel)

| Métrique | Valeur |
|----------|--------|
| Items input | 29 |
| Items matched | 0 (0%) |
| Max score | 3.3 |
| Canonical | v2.2 S3 |

**Conclusion**: Problème systématique sur AWS, pas lié à la version client

---

## 🎯 DIAGNOSTIC

### Cause Probable: Données v13 Incompatibles

**Hypothèse**: Les 29 items de v13 sont peut-être:
1. Déjà normalisés avec ancien canonical
2. Manquent d'entités détectées (0 companies, 0 technologies)
3. Ont des scores calculés avec ancienne logique

**Preuve**:
- Tests locaux (nouveaux items): 67% matching ✅
- Tests AWS (items v13): 0% matching ⚠️

### Cause Secondaire: Seuil Inadapté

**Observation**:
- Seuil: 25 points
- Max score: 3.3 points
- Écart: -87%

**Possible que**:
- Canonical v2.2 génère des scores plus bas
- Seuil 25 était calibré pour v2.1
- Besoin d'ajuster à 5-10 pour v2.2

---

## 🎯 ACTIONS RECOMMANDÉES

### Option 1: Baisser Seuil (RAPIDE)

```yaml
# Modifier lai_weekly_v14.yaml
matching_config:
  min_domain_score: 0.05  # Au lieu de 0.25
```

**Avantage**: Test rapide  
**Inconvénient**: Peut générer faux positifs

### Option 2: Nouvelles Données (RECOMMANDÉ)

```bash
# Ingérer de nouvelles données avec Canonical v2.2
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v14
```

**Avantage**: Test avec données fraîches  
**Inconvénient**: Nécessite ingestion

### Option 3: Analyser 1 Item

```bash
# Télécharger 1 item normalisé
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v14/2026/02/03/items.json ./

# Analyser le contenu
cat items.json | jq '.[0]'
```

**Avantage**: Comprendre pourquoi score si bas  
**Inconvénient**: Manuel

---

## 📝 CONCLUSION

**Statut**: ⚠️ Test E2E v14 complété mais 0% matching persistant

**Canonical v2.2**: ✅ Déployé et chargé correctement

**Problème**: Scores trop bas (max 3.3 vs seuil 25)

**Cause probable**: 
1. Données v13 incompatibles (anciennes)
2. Seuil inadapté pour Canonical v2.2

**Recommandation**: Baisser seuil à 0.05 et re-tester, ou ingérer nouvelles données

---

**Rapport créé**: 2026-02-03  
**Durée test**: ~5 minutes  
**Fichiers créés**:
- `client-config-examples/production/lai_weekly_v14.yaml`
- `s3://vectora-inbox-config-dev/clients/lai_weekly_v14.yaml`
- `s3://vectora-inbox-data-dev/ingested/lai_weekly_v14/`
