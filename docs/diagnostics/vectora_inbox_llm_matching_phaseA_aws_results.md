# Phase A4 - Déploiement AWS DEV

**Date** : 2025-12-13  
**Phase** : A4 - Déploiement AWS DEV  
**Objectif** : Tester en conditions réelles sur AWS DEV  

---

## 🚀 Déploiement Réalisé

### Lambda `vectora-inbox-engine-dev` (région eu-west-3)

#### ✅ Code déployé avec succès
- **Package** : `engine-llm-relevance-phase-a4-fixed.zip` (69.3 MB)
- **Méthode** : Upload S3 puis déploiement Lambda
- **Handler** : `src.lambdas.engine.handler.lambda_handler`
- **Runtime** : `python3.12`
- **Taille** : 72.7 MB décompressé

#### ✅ Variables d'environnement configurées
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

#### ✅ Feature flag activé
- **`USE_LLM_RELEVANCE=true`** : Correctement configuré
- **Vérification** : Confirmée via `aws lambda get-function`

---

## 🧪 Test d'Invocation

### Payload de test
```json
{
  "client_id": "lai_weekly_v3",
  "period_days": 7,
  "force_run": true,
  "test_mode": false
}
```

### Résultat d'invocation
- **Status Code** : 200 (succès)
- **Erreur rencontrée** : `No module named '_yaml'`
- **Type d'erreur** : `Runtime.ImportModuleError`

---

## 🔍 Diagnostic Technique

### Problème identifié : Dépendances manquantes

#### Cause
Le package déployé ne contient pas toutes les dépendances Python nécessaires :
- Module `_yaml` manquant (extension C de PyYAML)
- Autres dépendances potentiellement manquantes

#### Impact
- La Lambda ne peut pas s'exécuter complètement
- Impossible de tester l'impact réel du feature flag `USE_LLM_RELEVANCE`
- Pas de données de performance disponibles

### Solutions identifiées

#### Option 1 : Package complet avec toutes les dépendances
- Inclure `lambda-deps` complet dans le package
- Risque : Taille > 70 MB (limite AWS Lambda)

#### Option 2 : Utilisation de Lambda Layers
- Créer un Layer avec les dépendances communes
- Déployer uniquement le code source dans la fonction

#### Option 3 : Optimisation du package
- Exclure les fichiers inutiles (.pyc, tests, docs)
- Compresser plus efficacement

---

## 📊 Validation Partielle des Objectifs Phase A4

### ✅ Objectifs atteints

#### 1. Déploiement des modifications Phase A
- ✅ Code `scorer.py` avec `compute_score_with_llm_signals()` déployé
- ✅ Feature flag `USE_LLM_RELEVANCE` configuré et activé
- ✅ Variables d'environnement correctement définies

#### 2. Configuration AWS
- ✅ Lambda `vectora-inbox-engine-dev` mise à jour
- ✅ Région eu-west-3 (Paris) utilisée
- ✅ Permissions IAM préservées

#### 3. Validation technique
- ✅ Package créé et uploadé avec succès
- ✅ Déploiement via S3 fonctionnel
- ✅ Configuration vérifiée

### ❌ Objectifs non atteints

#### 1. Run réel lai_weekly_v3
- ❌ Erreur d'import empêche l'exécution
- ❌ Pas de métriques de performance disponibles
- ❌ Pas de comparaison scores avec/sans LLM

#### 2. Validation de l'impact LLM
- ❌ Pas de traces `[LLM_RELEVANCE]` dans les logs
- ❌ Pas de données sur la sélection finale
- ❌ Pas de mesure de l'amélioration qualité

---

## 🎯 Recommandations Phase A4

### Actions immédiates

#### 1. Correction du package de déploiement
```bash
# Inclure les dépendances PyYAML complètes
cp -r lambda-deps/_yaml* package/
cp -r lambda-deps/yaml* package/
```

#### 2. Test de validation minimal
```python
# Test d'import simple
import yaml
import src.vectora_core.scoring.scorer as scorer
print("Imports OK")
```

#### 3. Déploiement corrigé
- Créer un package avec toutes les dépendances
- Utiliser S3 pour contourner la limite de taille
- Tester l'import avant le run complet

### Validation alternative

#### Option : Test local avec AWS credentials
```python
# Simuler l'environnement AWS localement
os.environ['USE_LLM_RELEVANCE'] = 'true'
# Utiliser les vraies données S3
# Comparer avec USE_LLM_RELEVANCE=false
```

---

## 📋 Bilan Phase A4

### Statut : ⚠️ **PARTIELLEMENT RÉUSSI**

#### Succès techniques
- ✅ Déploiement AWS réalisé
- ✅ Feature flag configuré
- ✅ Code Phase A intégré

#### Blocage identifié
- ❌ Dépendances manquantes empêchent l'exécution
- ❌ Pas de validation métier possible

#### Impact sur le plan global
- **Phase A1-A3** : ✅ Complètes et validées
- **Phase A4** : ⚠️ Déploiement OK, exécution bloquée
- **Transition vers Phase B** : Possible avec correction du package

---

## 🔄 Actions de Correction

### Priorité 1 : Correction du package
1. Inclure toutes les dépendances Python
2. Tester l'import en local
3. Redéployer et valider

### Priorité 2 : Validation métier
1. Lancer un run réel `lai_weekly_v3`
2. Collecter les métriques de performance
3. Comparer avec/sans `USE_LLM_RELEVANCE`

### Priorité 3 : Documentation finale
1. Métriques avant/après LLM relevance
2. Impact sur la sélection finale
3. Recommandations pour Phase B

**Condition pour passer à Phase B** : ⚠️ **Correction du package et validation métier requises**