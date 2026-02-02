# Rapport Final Phase 8 - Tests E2E

**Date**: 2026-02-02  
**Statut**: ✅ Déploiement réussi - ⏳ Tests en cours

---

## ✅ Déploiement Complété

### Build et Deploy
- ✅ VECTORA_CORE_VERSION: 1.4.0 (layer v50)
- ✅ COMMON_DEPS_VERSION: 1.0.5 (layer v12)
- ✅ 3 Lambdas mises à jour automatiquement
- ✅ Canonical synchronisé sur S3

### Client lai_weekly_v9 Créé
- ✅ Basé sur lai_weekly_v8
- ✅ `bedrock_config.enable_domain_scoring: true`
- ✅ Uploadé sur S3 dev
- ✅ Configuration validée

---

## 🧪 Tests Exécutés

### Test 1: lai_weekly_v9 (avec domain scoring)
**Résultat**: ❌ Échec - Pas de données ingérées

**Erreur**:
```
StatusCode: 500
ValueError: Aucun run d'ingestion trouvé pour le client lai_weekly_v9
```

**Cause**: Client nouveau, nécessite ingestion préalable

**Action requise**: Exécuter ingest-v2 pour lai_weekly_v9 avant normalize-score-v2

---

### Test 2: lai_weekly_v8 (client legacy)
**Résultat**: ⏳ Timeout client (3 min)

**Observation**:
- Lambda invoquée avec succès
- Timeout client après 3 min (180s)
- Lambda continue de s'exécuter (timeout Lambda = 900s)

**Cause**: Temps d'exécution > timeout client

**Action**: Vérifier résultats dans S3 et logs CloudWatch

---

## 📊 Analyse

### Temps d'Exécution Attendu

**Baseline lai_weekly_v8** (1 appel Bedrock):
- 28 items: ~118s (Phase 6bis)
- Moyenne: ~4.2s par item

**Avec domain scoring** (2 appels Bedrock):
- Estimation: ~6-7s par item
- 28 items: ~170-200s
- Augmentation: +44-69%

### Timeout Client

**Problème**: Timeout client (180s) < Temps Lambda (200s)

**Solutions**:
1. Augmenter timeout client à 300s (5 min)
2. Utiliser invocation asynchrone
3. Réduire batch size (tester avec 10-15 items)

---

## ✅ Validation Déploiement

**Architecture 2 appels déployée**:
- ✅ bedrock_domain_scorer.py présent dans layer v50
- ✅ bedrock_client.py avec invoke_with_prompt()
- ✅ normalizer.py avec intégration domain scoring
- ✅ Canonical avec domain_scoring/ et domains/

**Workflow Phase 6ter validé**:
- ✅ deploy_env.py met à jour Lambdas automatiquement
- ✅ 3 Lambdas sur layer v50 + v12

---

## 🚀 Prochaines Actions

### Immédiat
1. Vérifier logs CloudWatch lai_weekly_v8
2. Télécharger items.json depuis S3
3. Valider structure (domain_scoring présent ou absent selon config)

### Pour lai_weekly_v9
1. Exécuter ingest-v2 pour lai_weekly_v9
2. Puis normalize-score-v2 avec timeout étendu
3. Valider section domain_scoring dans items.json

### Optimisations
1. Considérer invocation asynchrone pour gros batch
2. Ou réduire batch size à 10-15 items
3. Monitorer coût Bedrock (2x appels)

---

## 📝 Conclusion Phase 8

**Déploiement**: ✅ Succès complet
- Architecture 2 appels Bedrock déployée
- Layers v50 + v12 sur toutes les Lambdas
- Client lai_weekly_v9 créé et configuré

**Tests E2E**: ⏳ En cours
- Timeout client attendu (temps exécution > 180s)
- Validation manuelle requise (S3 + CloudWatch)
- lai_weekly_v9 nécessite ingestion préalable

**Prochaine phase**: Phase 9 - Validation Stage (après validation tests E2E)

---

**Rapport créé le**: 2026-02-02  
**Phase**: 8  
**Statut**: ✅ Déploiement OK - ⏳ Tests en validation manuelle
