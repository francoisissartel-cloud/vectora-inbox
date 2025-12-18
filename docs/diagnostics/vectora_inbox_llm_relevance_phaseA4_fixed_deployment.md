# Phase A4-F4 - Déploiement AWS DEV Corrigé

**Date** : 2025-12-13  
**Phase** : A4-F4 - Déploiement AWS DEV avec package corrigé  
**Objectif** : Déployer le package PyYAML corrigé sur Lambda `vectora-inbox-engine-dev`  

---

## 📦 Package Final Validé

### Package déployé
- **Nom** : `engine-llm-relevance-phase-a4-clean.zip`
- **Taille** : 68.44 MB
- **Statut** : ✅ **Validé par tests locaux complets**

### Corrections appliquées
- ✅ **Structure propre** : Code source dans `src/`, dépendances à la racine
- ✅ **PyYAML Python pur** : Aucune extension C (.pyd) incompatible
- ✅ **cyaml.py factice** : Évite les imports d'extensions C
- ✅ **src/__init__.py vide** : Plus de stub `_yaml` problématique

---

## 🚀 Déploiement en Cours

### Prêt pour déploiement
Le package a passé tous les tests locaux :
- ✅ Import yaml réussi (mode Python pur)
- ✅ Sérialisation/désérialisation YAML fonctionnelle
- ✅ Import scorer réussi avec `compute_score_with_llm_signals`
- ✅ Import handler Lambda réussi avec `lambda_handler`

### Commande de déploiement
```powershell
powershell -ExecutionPolicy Bypass -File "scripts\deploy-llm-relevance-phase-a4-complete.ps1"
```

**Note** : Le script de déploiement doit être adapté pour utiliser le nouveau package `engine-llm-relevance-phase-a4-clean.zip`

---

## 🎯 Objectifs Phase A4-F4

### Étapes de déploiement
1. **Upload S3** : Package corrigé vers `s3://vectora-inbox-data-dev/lambda-packages/`
2. **Mise à jour Lambda** : Code de `vectora-inbox-engine-dev`
3. **Vérification config** : Variables d'environnement et handler
4. **Test d'invocation** : Smoke test basique
5. **Vérification logs** : Absence d'erreurs d'import

### Validation attendue
- ✅ Pas d'erreur `Runtime.ImportModuleError: No module named '_yaml'`
- ✅ Lambda s'exécute sans erreur d'import
- ✅ Prêt pour Phase A4-F5 (Run réel `lai_weekly_v3`)

---

## 📋 Configuration Lambda Cible

### Variables d'environnement requises
```json
{
  "USE_LLM_RELEVANCE": "true",
  "USE_CANONICAL_PROMPTS": "true",
  "BEDROCK_MODEL_ID": "anthropic.claude-sonnet-4-5-20250929-v1:0",
  "BEDROCK_REGION": "us-east-1",
  "CONFIG_BUCKET": "vectora-inbox-config-dev",
  "DATA_BUCKET": "vectora-inbox-data-dev",
  "NEWSLETTERS_BUCKET": "vectora-inbox-newsletters-dev",
  "LOG_LEVEL": "INFO"
}
```

### Configuration Lambda
- **Runtime** : `python3.12`
- **Handler** : `src.lambdas.engine.handler.lambda_handler`
- **Timeout** : 900s
- **Memory** : 512MB
- **Région** : eu-west-3

---

## ✅ Résultat Attendu

### Succès du déploiement si
- ✅ Upload S3 réussi
- ✅ Mise à jour Lambda réussie
- ✅ Test d'invocation sans erreur d'import
- ✅ Logs CloudWatch propres

### Transition vers Phase A4-F5
Une fois le déploiement réussi, passage immédiat à la Phase A4-F5 pour :
- Run réel `lai_weekly_v3` avec `USE_LLM_RELEVANCE=true`
- Validation des traces `[LLM_RELEVANCE]` dans les logs
- Métriques d'impact LLM relevance sur le scoring

**Statut** : ✅ **RÉUSSI** - Package ultra-propre déployé avec succès

### Résultat final
- ✅ **Package ultra-propre** : `engine-llm-relevance-phase-a4-ultra-clean.zip` (16.96 MB)
- ✅ **Déploiement AWS** : Lambda `vectora-inbox-engine-dev` mise à jour
- ✅ **Test d'invocation** : Aucune erreur d'import `_yaml`
- ✅ **Logs CloudWatch** : Lambda s'exécute sans erreur de packaging
- ✅ **Erreur NoSuchKey** : Normale pour un test avec client_id inexistant

### Validation technique
- ✅ **Problème résolu** : `Runtime.ImportModuleError: No module named '_yaml'` éliminé
- ✅ **PyYAML fonctionnel** : Mode Python pur opérationnel
- ✅ **Structure propre** : Code source séparé, dépendances à la racine
- ✅ **Taille optimisée** : 16.96 MB vs 68+ MB précédemment