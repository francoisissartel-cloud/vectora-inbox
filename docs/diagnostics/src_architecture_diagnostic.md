
# Diagnostic Complet : Architecture du Dossier `/src` - Vectora Inbox

**Date** : 2025-12-13  
**Évaluateur** : Expert Architect AWS  
**Scope** : Analyse complète du dossier `/src`, architecture Lambda, et bonnes pratiques cloud  

---

## 🔍 Analyse Structurelle

### Structure Actuelle du Dossier `/src`

```
src/
├── lambdas/
│   ├── engine/
│   │   ├── package/          # ❌ PROBLÉMATIQUE
│   │   │   ├── _yaml/
│   │   │   ├── boto3/
│   │   │   ├── botocore/
│   │   │   ├── vectora_core/
│   │   │   └── [toutes les dépendances]
│   │   └── handler.py        # ✅ CORRECT
│   └── ingest_normalize/
│       └── handler.py        # ✅ CORRECT
├── vectora_core/             # ✅ CORRECT (logique métier)
│   ├── config/
│   ├── ingestion/
│   ├── matching/
│   ├── newsletter/
│   ├── normalization/
│   ├── prompts/
│   ├── scoring/
│   ├── storage/
│   └── utils/
└── [dépendances dupliquées] # ❌ PROBLÉMATIQUE
    ├── boto3/
    ├── yaml/
    ├── requests/
    └── [...]
```

---

## 📊 Évaluation Globale

### Note Générale : **4/10** ⚠️

**Répartition des notes :**
- **Architecture Lambda** : 3/10 (problèmes majeurs)
- **Séparation des responsabilités** : 7/10 (bonne logique métier)
- **Gestion des dépendances** : 2/10 (chaos total)
- **Déployabilité AWS** : 3/10 (problèmes de packaging)
- **Maintenabilité** : 4/10 (structure confuse)
- **Testabilité** : 6/10 (logique métier testable)

---

## ❌ Problèmes Critiques Identifiés

### 1. **Duplication Massive des Dépendances**

**Problème** : Les dépendances Python sont présentes à 3 endroits différents :
- `/src/` (racine)
- `/src/lambdas/engine/package/`
- `/lambda-deps/`

**Impact** :
- Taille de déploiement excessive (>70MB)
- Confusion sur la version utilisée
- Maintenance impossible
- Risques de conflits de versions

### 2. **Architecture de Packaging Défaillante**

**Problème** : Le dossier `/src/lambdas/engine/package/` contient un package Lambda complet avec toutes les dépendances.

**Impact** :
- Violation des bonnes pratiques AWS Lambda
- Impossible de gérer les versions proprement
- Dépassement des limites de taille Lambda
- Erreurs d'import (`No module named '_yaml'`)

### 3. **Mélange Code Source / Dépendances**

**Problème** : Le dossier `/src/` contient à la fois le code source et les dépendances installées.

**Impact** :
- Structure illisible
- Impossible de distinguer le code métier des libs
- Problèmes de versioning Git
- Confusion pour les développeurs

### 4. **Absence de Layers AWS Lambda**

**Problème** : Aucune utilisation des Lambda Layers pour les dépendances communes.

**Impact** :
- Packages Lambda surdimensionnés
- Temps de déploiement excessifs
- Duplication des dépendances entre Lambdas

---

## ✅ Points Positifs Identifiés

### 1. **Excellente Séparation Logique Métier**

**Vectora Core** est bien architecturé :
- Modules spécialisés par responsabilité
- Interfaces claires entre modules
- Logique métier indépendante d'AWS Lambda
- Réutilisabilité (CLI, tests, notebooks)

### 2. **Handlers Lambda Minimalistes**

Les handlers sont corrects :
- Responsabilité unique (parsing event + appel vectora_core)
- Gestion d'erreurs appropriée
- Pas de logique métier dans les handlers

### 3. **Configuration Externalisée**

- Configuration via variables d'environnement
- Séparation client/canonical
- Chargement depuis S3

---

## 🏗️ Architecture Recommandée

### Structure Cible

```
src/
├── lambdas/
│   ├── engine/
│   │   ├── handler.py
│   │   ├── requirements.txt
│   │   └── Dockerfile (optionnel)
│   ├── ingest_normalize/
│   │   ├── handler.py
│   │   ├── requirements.txt
│   │   └── Dockerfile (optionnel)
│   └── shared/
│       └── layers/
│           ├── vectora-core-layer/
│           └── common-deps-layer/
├── vectora_core/              # Code métier pur
│   ├── [structure actuelle]
│   └── __init__.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── requirements.txt           # Dépendances de développement
```

### Layers AWS Lambda Recommandés

#### Layer 1 : `vectora-core-layer`
```
python/
└── vectora_core/
    ├── config/
    ├── ingestion/
    └── [tous les modules métier]
```

#### Layer 2 : `common-deps-layer`
```
python/
├── boto3/
├── yaml/
├── requests/
├── feedparser/
└── [dépendances communes]
```

---

## 🛠️ Plan de Refactoring

### Phase 1 : Nettoyage Immédiat (Priorité Critique)

#### 1.1 Suppression des Duplications
```bash
# Supprimer les dépendances du dossier src/
rm -rf src/_yaml src/boto3 src/yaml src/requests [...]

# Supprimer le package engine
rm -rf src/lambdas/engine/package/

# Garder uniquement lambda-deps/ comme source de vérité
```

#### 1.2 Restructuration des Handlers
```python
# src/lambdas/engine/requirements.txt
vectora_core==1.0.0  # Via layer
boto3>=1.34.0        # Via layer
pyyaml>=6.0         # Via layer
```

### Phase 2 : Création des Layers (Priorité Haute)

#### 2.1 Script de Build Layer Vectora Core
```bash
#!/bin/bash
# scripts/build-vectora-core-layer.sh

mkdir -p layers/vectora-core/python
cp -r src/vectora_core layers/vectora-core/python/
cd layers/vectora-core
zip -r ../../vectora-core-layer.zip python/
```

#### 2.2 Script de Build Layer Dépendances
```bash
#!/bin/bash
# scripts/build-deps-layer.sh

mkdir -p layers/deps/python
pip install -r requirements.txt -t layers/deps/python/
cd layers/deps
zip -r ../../common-deps-layer.zip python/
```

### Phase 3 : Optimisation du Déploiement (Priorité Moyenne)

#### 3.1 Infrastructure as Code
```yaml
# infra/lambda-layers.yaml
VectoraCoreLayer:
  Type: AWS::Lambda::LayerVersion
  Properties:
    LayerName: vectora-core
    Content:
      S3Bucket: !Ref DeploymentBucket
      S3Key: layers/vectora-core-layer.zip
    CompatibleRuntimes:
      - python3.12

CommonDepsLayer:
  Type: AWS::Lambda::LayerVersion
  Properties:
    LayerName: common-deps
    Content:
      S3Bucket: !Ref DeploymentBucket
      S3Key: layers/common-deps-layer.zip
    CompatibleRuntimes:
      - python3.12
```

#### 3.2 Configuration Lambda avec Layers
```yaml
EngineFunction:
  Type: AWS::Lambda::Function
  Properties:
    Runtime: python3.12
    Handler: handler.lambda_handler
    Layers:
      - !Ref VectoraCoreLayer
      - !Ref CommonDepsLayer
    Code:
      S3Bucket: !Ref DeploymentBucket
      S3Key: lambdas/engine.zip  # Seulement handler.py
```

---

## 📋 Scripts de Déploiement Recommandés

### Script de Build Complet
```powershell
# scripts/build-and-deploy.ps1

# 1. Build des layers
./scripts/build-vectora-core-layer.ps1
./scripts/build-deps-layer.ps1

# 2. Upload des layers vers S3
aws s3 cp vectora-core-layer.zip s3://$DEPLOYMENT_BUCKET/layers/
aws s3 cp common-deps-layer.zip s3://$DEPLOYMENT_BUCKET/layers/

# 3. Déploiement des layers via CloudFormation
aws cloudformation deploy --template-file infra/lambda-layers.yaml

# 4. Build des fonctions Lambda (seulement handlers)
./scripts/build-lambda-functions.ps1

# 5. Déploiement des fonctions
aws cloudformation deploy --template-file infra/lambda-functions.yaml
```

### Script de Test Local
```python
# scripts/test-local.py
import sys
import os

# Ajouter les layers au PYTHONPATH pour tests locaux
sys.path.insert(0, 'layers/vectora-core/python')
sys.path.insert(0, 'layers/deps/python')

# Maintenant on peut importer et tester
from vectora_core import run_engine_for_client
```

---

## 🧪 Stratégie de Tests

### Tests Unitaires
```python
# tests/unit/test_vectora_core.py
import pytest
from vectora_core.config import loader
from vectora_core.scoring import scorer

class TestVectoraCore:
    def test_load_client_config(self):
        # Test avec mock S3
        pass
    
    def test_score_items(self):
        # Test logique de scoring
        pass
```

### Tests d'Intégration
```python
# tests/integration/test_lambda_handlers.py
import json
from src.lambdas.engine.handler import lambda_handler

class TestLambdaHandlers:
    def test_engine_handler_success(self):
        event = {"client_id": "test_client"}
        result = lambda_handler(event, None)
        assert result["statusCode"] == 200
```

---

## 📊 Métriques de Qualité Cibles

### Avant Refactoring (État Actuel)
- **Taille package Lambda** : ~70MB
- **Temps de déploiement** : >5 minutes
- **Temps de cold start** : >10 secondes
- **Maintenabilité** : Faible
- **Testabilité** : Moyenne

### Après Refactoring (Objectifs)
- **Taille package Lambda** : <5MB (handlers seulement)
- **Taille layers** : 20MB (vectora-core) + 30MB (deps)
- **Temps de déploiement** : <2 minutes
- **Temps de cold start** : <3 secondes
- **Maintenabilité** : Élevée
- **Testabilité** : Élevée

---

## 🎯 Bonnes Pratiques pour Q Developer

### Règles de Développement

#### 1. **Séparation Stricte des Responsabilités**
```
❌ NE PAS : Mettre de logique métier dans les handlers Lambda
✅ FAIRE : Déléguer toute logique à vectora_core

❌ NE PAS : Mélanger dépendances et code source
✅ FAIRE : Utiliser des layers pour les dépendances
```

#### 2. **Gestion des Dépendances**
```
❌ NE PAS : Copier les dépendances dans src/
✅ FAIRE : Utiliser requirements.txt + layers

❌ NE PAS : Dupliquer les dépendances
✅ FAIRE : Une seule source de vérité par dépendance
```

#### 3. **Structure des Packages**
```
❌ NE PAS : Créer des packages Lambda >50MB
✅ FAIRE : Handlers minimalistes + layers

❌ NE PAS : Inclure les tests dans les packages
✅ FAIRE : Séparer tests et code de production
```

---

## 🚀 Actions Immédiates Recommandées

### Priorité 1 (Cette Semaine)
1. **Nettoyer les duplications** dans `/src/`
2. **Créer les layers** vectora-core et common-deps
3. **Tester le déploiement** avec la nouvelle structure
4. **Valider l'import** des modules

### Priorité 2 (Semaine Suivante)
1. **Automatiser le build** avec scripts PowerShell
2. **Créer les tests** unitaires et d'intégration
3. **Documenter** la nouvelle architecture
4. **Former l'équipe** aux nouvelles pratiques

### Priorité 3 (Moyen Terme)
1. **Optimiser les performances** (cold start, mémoire)
2. **Implémenter le monitoring** (CloudWatch, X-Ray)
3. **Créer un pipeline CI/CD** complet
4. **Ajouter la validation** automatique des packages

---

## 📝 Conclusion

L'architecture actuelle du dossier `/src/` présente des **problèmes critiques** qui compromettent la maintenabilité et la déployabilité du projet. Cependant, la **logique métier** (vectora_core) est bien conçue et constitue une base solide.

Le **refactoring proposé** permettra de :
- ✅ Résoudre les problèmes de packaging Lambda
- ✅ Améliorer les performances de déploiement
- ✅ Faciliter la maintenance et les tests
- ✅ Respecter les bonnes pratiques AWS

**Recommandation** : Prioriser le nettoyage immédiat et la création des layers avant tout nouveau développement.

---

**Prochaine étape** : Validation du plan de refactoring et début de l'implémentation Phase 1.