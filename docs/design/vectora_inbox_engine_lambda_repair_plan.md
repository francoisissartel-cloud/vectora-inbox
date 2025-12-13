# Plan Correctif - Réparation Lambda Engine

**Date** : 2025-12-12  
**Objectif** : Corriger la Lambda engine qui exécute le mauvais code (ingestion au lieu d'engine)  
**Cause Identifiée** : Problème de déploiement/packaging - engine exécute `run_ingest_normalize_for_client` au lieu de `run_engine_for_client`

---

## 🎯 Objectif

Réparer la Lambda `vectora-inbox-engine-dev` pour qu'elle exécute le bon workflow :
- ❌ **Actuel** : Ingestion + Normalisation (mauvais code)
- ✅ **Cible** : Matching + Scoring + Newsletter (bon code)

---

## 📋 Plan par Phases

### Phase 1 - Diagnostic Approfondi (15 min)
**Objectif** : Comprendre exactement ce qui est déployé dans la Lambda engine

**Actions** :
1. Télécharger le package Lambda engine actuel
2. Inspecter le contenu du handler.py
3. Vérifier les imports dans vectora_core
4. Identifier la cause exacte (handler/import/package)

**Critères de Succès** :
- Cause racine identifiée précisément
- Stratégie de correction définie

### Phase 2 - Préparation Package Correct (20 min)
**Objectif** : Créer le package engine correct en local

**Actions** :
1. Vérifier le code source engine local
2. Utiliser le script de packaging engine
3. Valider le contenu du package généré
4. Tester le handler en local si possible

**Critères de Succès** :
- Package engine correct généré
- Handler pointe vers le bon code
- Imports corrects validés

### Phase 3 - Tests Locaux (30 min)
**Objectif** : Valider le workflow engine en local avec données réelles

**Actions** :
1. Tester la fonction `run_engine_for_client` en local
2. Utiliser les items normalisés existants de lai_weekly_v3
3. Vérifier matching, scoring et génération newsletter
4. Valider que le workflow complet fonctionne

**Critères de Succès** :
- Engine fonctionne en local
- Newsletter générée avec succès
- Pas d'erreurs de workflow

### Phase 4 - Déploiement AWS (10 min)
**Objectif** : Déployer le package corrigé sur AWS

**Actions** :
1. Déployer le package engine corrigé
2. Vérifier la configuration Lambda
3. Valider les variables d'environnement

**Critères de Succès** :
- Lambda engine mise à jour
- Configuration cohérente
- Prête pour tests

### Phase 5 - Validation End-to-End (20 min)
**Objectif** : Valider le workflow complet avec données réelles

**Actions** :
1. Test engine isolé avec lai_weekly_v3
2. Test workflow complet (ingestion → engine)
3. Vérifier génération newsletter
4. Valider métriques de performance

**Critères de Succès** :
- Engine exécute le bon code
- Newsletter générée avec Bedrock
- Workflow end-to-end fonctionnel

---

## 🔧 Commandes et Scripts

### Scripts de Packaging
```bash
# Package engine correct
.\scripts\package-engine-simple.ps1

# Déploiement engine
.\scripts\deploy-engine-dev-simple.ps1
```

### Tests de Validation
```bash
# Test engine isolé
aws lambda invoke --function-name vectora-inbox-engine-dev \
  --payload '{"client_id":"lai_weekly_v3","period_days":7}' \
  --cli-binary-format raw-in-base64-out \
  --region eu-west-3 --profile rag-lai-prod out-engine-test.json

# Test workflow complet
# 1. Ingestion (déjà fonctionnelle)
# 2. Engine (à valider)
```

---

## 📊 Critères de Succès Global

### Logs Engine Corrects
```
[INFO] Démarrage de vectora-inbox-engine          ✅
[INFO] Phase 2 : Matching des items               ✅
[INFO] Phase 3 : Scoring des items                ✅
[INFO] Phase 4 : Génération newsletter            ✅
```

### Output Engine Correct
```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly_v3",
    "items_analyzed": 104,
    "items_matched": "~18",
    "items_selected": "~5",
    "s3_output_path": "s3://vectora-inbox-newsletters-dev/...",
    "message": "Newsletter générée avec succès"
  }
}
```

### Workflow End-to-End
- ✅ Ingestion : 104 items normalisés
- ✅ Engine : Newsletter générée
- ✅ Performance : <30s total
- ✅ Qualité : Items gold LAI présents

---

## ⚠️ Points d'Attention

### Risques Identifiés
1. **Package incorrect** : Vérifier que le bon code est packagé
2. **Handler path** : S'assurer que le handler pointe vers engine
3. **Imports** : Valider que les imports sont corrects
4. **Variables env** : Vérifier cohérence après déploiement

### Rollback Plan
- Conserver le package actuel avant modification
- Possibilité de revenir à l'état précédent si problème
- Tests de validation avant mise en production

---

**Prêt pour exécution phase par phase.**