# Rapport d'Exécution - Plan Correctif Pure Players

**Date** : 2026-02-06  
**Version** : v1.7.0 (tentative)  
**Client test** : lai_weekly_v26

---

## ✅ Résumé Exécutif

**Statut Ingestion** : ✅ **SUCCÈS** - Pure players correctement détectés  
**Statut Global** : ❌ **ÉCHEC** - Problème dans normalize-score (domain scoring)

---

## 📋 Étapes Exécutées

### Phase 1 : Build & Deploy ✅
- ✅ Build de toutes les Lambdas réussi
- ✅ Deploy dev réussi
  - vectora-core layer: v77
  - common-deps layer: v38
- ✅ Toutes les Lambdas mises à jour

### Phase 2 : Configuration Client ✅
- ✅ Client lai_weekly_v26 créé
- ✅ Config uploadée sur S3

### Phase 3 : Test Ingestion ✅
- ✅ Ingestion v26 lancée avec succès
- ✅ 27 items ingérés (identique à v25)

### Phase 4 : Vérification Logs ✅
**Pure players détectés** :
- ✅ nanexa : "Pure player LAI détecté : nanexa - ingestion large avec exclusions minimales"
- ✅ medincell : "Pure player LAI détecté : medincell - ingestion large avec exclusions minimales"
- ✅ camurus : "Pure player LAI détecté : camurus - ingestion large avec exclusions minimales"
- ✅ delsitech : "Pure player LAI détecté : delsitech - ingestion large avec exclusions minimales"

**Profil corporate LAI appliqué** :
- nanexa : 6/8 items conservés, 2 exclus
- medincell : 4/12 items conservés, 8 exclus
- camurus : 1/1 items conservés, 0 exclus
- delsitech : 6/10 items conservés, 4 exclus

### Phase 5 : Normalize & Score ❌
- ✅ Normalize-score lancé avec succès
- ❌ **PROBLÈME** : Domain scoring ne détecte AUCUNE entité

---

## 🔍 Analyse Détaillée

### Ingestion : ✅ SUCCÈS

**Preuve** :
```
Source: press_corporate__medincell, Company ID: medincell, Pure player: True
Pure player LAI détecté : medincell - ingestion large avec exclusions minimales
Profil corporate LAI : 4/12 items conservés, 8 exclus
```

**Conclusion** : La correction du code fonctionne parfaitement. Les pure players sont :
1. Correctement extraits depuis `source_key` (ex: `press_corporate__medincell` → `medincell`)
2. Correctement détectés comme pure players LAI
3. Traités avec le profil "ingestion large" (pas de filtrage LAI keywords)

### Normalize-Score : ❌ ÉCHEC

**Problème identifié** :
- **0/27 items** ont des companies détectées
- **0/27 items** ont des technologies détectées
- **domain_relevance_factor** = 0.05 (au lieu de 0.8-1.0)
- **Scores finaux** : 0-3.8 (au lieu de 70-90)

**Exemple** :
```json
{
  "title": "Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application...",
  "source_key": "press_corporate__medincell",
  "domain_scoring": {
    "companies": [],  // ❌ Devrait contenir ["Medincell", "Teva"]
    "technologies": [],  // ❌ Devrait contenir des technologies LAI
    "therapeutic_areas": [],
    "regulatory": []
  },
  "scoring_results": {
    "base_score": 7,
    "final_score": 3.8,  // ❌ Très bas à cause du domain_relevance_factor
    "domain_relevance_factor": 0.05  // ❌ Devrait être ~0.8-1.0
  }
}
```

---

## 📊 Métriques Comparatives

| Métrique | v25 (AVANT) | v26 (APRÈS) | Δ | Statut |
|----------|-------------|-------------|---|--------|
| Items ingérés | 27 | 27 | 0 | ⚠️ |
| Items avec companies | 0 | 0 | 0 | ❌ |
| Items avec technologies | 0 | 0 | 0 | ❌ |
| Taux relevant (score≥70) | 0% | 0% | 0 | ❌ |
| Score moyen | 0.8 | 0.8 | 0 | ❌ |
| Scores 80+ | 0% | 0% | 0 | ❌ |

**Conclusion** : Aucune amélioration car le problème est dans normalize-score, pas dans l'ingestion.

---

## 🎯 Diagnostic Final

### Problème Racine

Le **domain scoring** dans `normalize-score-v2` ne détecte **AUCUNE** entité (companies, technologies).

**Causes possibles** :
1. ❌ Canonical `company_scopes.yaml` ou `technology_scopes.yaml` vides/mal chargés
2. ❌ Logique de matching cassée dans `normalize-score-v2`
3. ❌ Bedrock API ne retourne pas les entités correctement
4. ❌ Problème de parsing des résultats Bedrock

### Impact

Sans domain scoring fonctionnel :
- `domain_relevance_factor` = 0.05 (au lieu de 0.8-1.0)
- Scores finaux très bas (0-3.8 au lieu de 70-90)
- Aucun item considéré comme relevant (score < 70)

---

## 💡 Recommandations

### 1. Vérifier Canonical Domain Scopes ⚠️ URGENT

```bash
# Vérifier que les scopes sont bien chargés
aws s3 cp s3://vectora-inbox-config-dev/canonical/scopes/company_scopes.yaml .tmp/ --profile rag-lai-prod --region eu-west-3
aws s3 cp s3://vectora-inbox-config-dev/canonical/scopes/technology_scopes.yaml .tmp/ --profile rag-lai-prod --region eu-west-3

# Vérifier contenu
cat .tmp/company_scopes.yaml
cat .tmp/technology_scopes.yaml
```

### 2. Vérifier Logs Normalize-Score ⚠️ URGENT

```bash
# Chercher erreurs de chargement canonical
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 30m \
  --filter-pattern "ERROR" \
  --profile rag-lai-prod --region eu-west-3

# Chercher logs de domain scoring
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 30m \
  --filter-pattern "domain_scoring" \
  --profile rag-lai-prod --region eu-west-3
```

### 3. Tester Normalize-Score Isolément

```bash
# Test avec un item spécifique
python scripts/invoke/invoke_normalize_score_v2.py \
  --client-id lai_weekly_v26 \
  --env dev \
  --debug
```

### 4. Comparer avec v24 (Baseline Fonctionnelle)

Si v24 fonctionnait correctement, comparer :
- Versions des layers
- Configuration canonical
- Code de normalize-score

---

## 🔄 Prochaines Étapes

### Option A : Débugger Normalize-Score (Recommandé)

1. Vérifier chargement canonical scopes
2. Vérifier logs Bedrock API
3. Tester domain scoring isolément
4. Corriger le problème identifié

### Option B : Rollback Temporaire

Si le problème est bloquant :
```bash
# Rollback vers version précédente
git checkout HEAD~1 src_v2/
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

---

## 📁 Fichiers Modifiés

### Code
- `src_v2/vectora_core/ingest/ingestion_profiles.py` (lignes 127-136)
  - ✅ Extraction `company_id` depuis `source_key`
  - ✅ Log debug ajouté
  - ✅ Fonctionne correctement

### Configuration
- `config/clients/lai_weekly_v26.yaml` (créé)

### Logs
- `.tmp/logs_pure_players.txt` (logs de détection pure players)
- `.tmp/baseline_v25/` (sauvegarde v25)
- `.tmp/results_v26/` (résultats v26)

---

## 🎓 Leçons Apprises

1. ✅ **Correction pure players** : Le code fonctionne parfaitement au niveau ingestion
2. ❌ **Test E2E nécessaire** : Un test uniquement sur l'ingestion ne suffit pas
3. ⚠️ **Domain scoring critique** : Sans domain scoring, les scores sont inutilisables
4. 📝 **Logs essentiels** : Les logs ont permis de diagnostiquer rapidement le problème

---

## 📝 Conclusion

**Statut Ingestion** : ✅ **SUCCÈS COMPLET**
- Pure players correctement détectés
- Ingestion large appliquée
- Pas de filtrage LAI keywords pour pure players

**Statut Global** : ❌ **ÉCHEC PARTIEL**
- Problème dans normalize-score (domain scoring)
- Nécessite investigation et correction séparée

**Action immédiate** : Débugger normalize-score-v2 pour comprendre pourquoi le domain scoring ne détecte aucune entité.

---

**Rapport créé le** : 2026-02-06  
**Auteur** : Amazon Q Developer  
**Statut** : ⚠️ Investigation nécessaire sur normalize-score
