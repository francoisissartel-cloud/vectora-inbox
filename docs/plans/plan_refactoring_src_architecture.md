# Plan de Refactoring - Architecture `/src` Vectora Inbox

**Date** : 2025-12-13  
**Priorité** : CRITIQUE  
**Durée Estimée** : 3-5 jours  
**Objectif** : Corriger les problèmes architecturaux majeurs du dossier `/src`  

---

## 🎯 Objectifs du Refactoring

### Objectifs Principaux
1. **Éliminer les duplications** de dépendances (problème critique)
2. **Restructurer le packaging** Lambda selon les bonnes pratiques AWS
3. **Implémenter les Lambda Layers** pour optimiser les déploiements
4. **Corriger les erreurs d'import** (`No module named '_yaml'`)
5. **Réduire la taille des packages** de 70MB à <10MB

### Objectifs Secondaires
1. **Améliorer la maintenabilité** du code
2. **Optimiser les performances** de déploiement
3. **Faciliter les tests** locaux et d'intégration
4. **Documenter** la nouvelle architecture

---

## 📋 Phase 1 : Nettoyage Immédiat (Jour 1)

### 1.1 Audit et Sauvegarde
```powershell
# Créer une sauvegarde avant refactoring
git checkout -b refactor-src-architecture
git add -A
git commit -m "Backup avant refactoring architecture src/"

# Documenter l'état actuel
du -sh src/  # Taille actuelle
find src/ -name "*.py" | wc -l  # Nombre de fichiers Python
```

### 1.2 Suppression des Duplications Critiques
```powershell
# Supprimer les dépendances dupliquées dans src/
Remove-Item -Recurse -Force src/_yaml
Remove-Item -Recurse -Force src/boto3
Remove-Item -Recurse -Force src/botocore
Remove-Item -Recurse -Force src/yaml
Remove-Item -Recurse -Force src/requests
Remove-Item -Recurse -Force src/feedparser
Remove-Item -Recurse -Force src/bs4
Remove-Item -Recurse -Force src/certifi
Remove-Item -Recurse -Force src/charset_normalizer
Remove-Item -Recurse -Force src/dateutil
Remove-Item -Recurse -Force src/idna
Remove-Item -Recurse -Force src/jmespath
Remove-Item -Recurse -Force src/s3transfer
Remove-Item -Recurse -Force src/urllib3
Remove-Item -Recurse -Force src/soupsieve
Remove-Item -Recurse -Force src/typing_extensions

# Supprimer les dossiers dist-info
Get-ChildItem -Path src/ -Filter "*dist-info" -Recurse | Remove-Item -Recurse -Force

# Supprimer les fichiers de dépendances à la racine de src/
Remove-Item -Force src/sgmllib.py
Remove-Item -Force src/six.py
Remove-Item -Force src/typing_extensions.py
Remove-Item -Force src/exclusion_filter.py
Remove-Item -Force src/handler.py
Remove-Item -Force src/README.md
Remove-Item -Force src/*.py -Exclude "__init__.py"
Remove-Item -Force src/*.pyd
```

### 1.3 Nettoyage du Package Engine
```powershell
# Supprimer le package engine complet
Remove-Item -Recurse -Force src/lambdas/engine/package/

# Supprimer les zips de build
Remove-Item -Force src/lambdas/engine/*.zip
```

### 1.4 Validation Post-Nettoyage
```powershell
# Vérifier la structure après nettoyage
tree src/ /F

# Vérifier la taille
du -sh src/

# Tester l'import de vectora_core
python -c "import sys; sys.path.append('src'); import vectora_core; print('✅ Import vectora_core OK')"
```

---

## 📦 Phase 2 : Création des Lambda Layers (Jour 2)

### 2.1 Création du Layer Vectora Core

#### Script de Build
```powershell
# scripts/build-vectora-core-layer.ps1
param(
    [string]$OutputDir = "layers"
)

Write-Host "🏗️ Building Vectora Core Layer..."

# Créer la structure du layer
$layerDir = "$OutputDir/vectora-core"
$pythonDir = "$layerDir/python"

New-Item -ItemType Directory -Force -Path $pythonDir

# Copier vectora_core
Copy-Item -Recurse -Force src/vectora_core $pythonDir/

# Créer le zip
$zipPath = "$OutputDir/vectora-core-layer.zip"
Compress-Archive -Path "$layerDir/*" -DestinationPath $zipPath -Force

Write-Host "✅ Layer créé : $zipPath"
Write-Host "📊 Taille : $((Get-Item $zipPath).Length / 1MB) MB"
```

### 2.2 Création du Layer Dépendances Communes

#### Script de Build
```powershell
# scripts/build-common-deps-layer.ps1
param(
    [string]$OutputDir = "layers"
)

Write-Host "🏗️ Building Common Dependencies Layer..."

# Créer la structure du layer
$layerDir = "$OutputDir/common-deps"
$pythonDir = "$layerDir/python"

New-Item -ItemType Directory -Force -Path $pythonDir

# Installer les dépendances depuis lambda-deps
Copy-Item -Recurse -Force lambda-deps/* $pythonDir/

# Nettoyer les fichiers inutiles
Remove-Item -Recurse -Force "$pythonDir/lambdas"
Remove-Item -Force "$pythonDir/*.py" -ErrorAction SilentlyContinue
Remove-Item -Force "$pythonDir/README.md" -ErrorAction SilentlyContinue

# Créer le zip
$zipPath = "$OutputDir/common-deps-layer.zip"
Compress-Archive -Path "$layerDir/*" -DestinationPath $zipPath -Force

Write-Host "✅ Layer créé : $zipPath"
Write-Host "📊 Taille : $((Get-Item $zipPath).Length / 1MB) MB"
```

### 2.3 Test des Layers Localement

#### Script de Test
```python
# scripts/test-layers-local.py
import sys
import os

# Ajouter les layers au PYTHONPATH
sys.path.insert(0, 'layers/vectora-core/python')
sys.path.insert(0, 'layers/common-deps/python')

print("🧪 Test des imports depuis les layers...")

try:
    # Test vectora_core
    import vectora_core
    print("✅ vectora_core importé avec succès")
    
    # Test dépendances communes
    import boto3
    import yaml
    import requests
    import feedparser
    print("✅ Dépendances communes importées avec succès")
    
    # Test fonction principale
    from vectora_core import run_engine_for_client
    print("✅ Fonction principale accessible")
    
    print("🎉 Tous les tests d'import réussis !")
    
except ImportError as e:
    print(f"❌ Erreur d'import : {e}")
    sys.exit(1)
```

---

## 🔧 Phase 3 : Restructuration des Handlers (Jour 3)

### 3.1 Mise à Jour des Requirements

#### Handler Engine
```txt
# src/lambdas/engine/requirements.txt
# Toutes les dépendances sont fournies par les layers
# Ce fichier sert de documentation des dépendances utilisées

# Via vectora-core-layer:
# vectora_core

# Via common-deps-layer:
# boto3>=1.34.0
# pyyaml>=6.0
# requests>=2.31.0
# feedparser>=6.0.10
# python-dateutil>=2.8.2
# beautifulsoup4>=4.12.0
```

#### Handler Ingest Normalize
```txt
# src/lambdas/ingest_normalize/requirements.txt
# Toutes les dépendances sont fournies par les layers
# Ce fichier sert de documentation des dépendances utilisées

# Via vectora-core-layer:
# vectora_core

# Via common-deps-layer:
# boto3>=1.34.0
# pyyaml>=6.0
# requests>=2.31.0
# feedparser>=6.0.10
# python-dateutil>=2.8.2
# beautifulsoup4>=4.12.0
```

### 3.2 Validation des Handlers

#### Test Handler Engine
```python
# scripts/test-engine-handler.py
import sys
import os

# Simuler les layers
sys.path.insert(0, 'layers/vectora-core/python')
sys.path.insert(0, 'layers/common-deps/python')

# Simuler l'environnement Lambda
os.environ.update({
    'CONFIG_BUCKET': 'test-config-bucket',
    'DATA_BUCKET': 'test-data-bucket',
    'NEWSLETTERS_BUCKET': 'test-newsletters-bucket',
    'BEDROCK_MODEL_ID': 'anthropic.claude-sonnet-4-5-20250929-v1:0'
})

# Test du handler
from src.lambdas.engine.handler import lambda_handler

event = {
    "client_id": "test_client",
    "period_days": 7
}

try:
    result = lambda_handler(event, None)
    print(f"✅ Handler testé avec succès : {result['statusCode']}")
except Exception as e:
    print(f"❌ Erreur handler : {e}")
```

---

## 🚀 Phase 4 : Scripts de Déploiement (Jour 4)

### 4.1 Script de Build Complet

```powershell
# scripts/build-all.ps1
param(
    [string]$Environment = "dev"
)

Write-Host "🚀 Build complet pour environnement : $Environment"

# 1. Nettoyer les anciens builds
Write-Host "🧹 Nettoyage..."
Remove-Item -Recurse -Force layers -ErrorAction SilentlyContinue
Remove-Item -Force *.zip -ErrorAction SilentlyContinue

# 2. Créer les layers
Write-Host "📦 Création des layers..."
./scripts/build-vectora-core-layer.ps1
./scripts/build-common-deps-layer.ps1

# 3. Tester les layers
Write-Host "🧪 Test des layers..."
python scripts/test-layers-local.py

# 4. Créer les packages Lambda (handlers seulement)
Write-Host "🏗️ Création des packages Lambda..."
./scripts/build-lambda-packages.ps1

# 5. Validation finale
Write-Host "✅ Validation finale..."
./scripts/validate-packages.ps1

Write-Host "🎉 Build terminé avec succès !"
```

### 4.2 Script de Build Lambda Packages

```powershell
# scripts/build-lambda-packages.ps1
Write-Host "🏗️ Building Lambda packages (handlers only)..."

# Engine Lambda
$engineDir = "packages/engine"
New-Item -ItemType Directory -Force -Path $engineDir
Copy-Item src/lambdas/engine/handler.py $engineDir/
Copy-Item src/lambdas/engine/requirements.txt $engineDir/
Compress-Archive -Path "$engineDir/*" -DestinationPath "engine-handler.zip" -Force

# Ingest Normalize Lambda
$ingestDir = "packages/ingest-normalize"
New-Item -ItemType Directory -Force -Path $ingestDir
Copy-Item src/lambdas/ingest_normalize/handler.py $ingestDir/
Copy-Item src/lambdas/ingest_normalize/requirements.txt $ingestDir/
Compress-Archive -Path "$ingestDir/*" -DestinationPath "ingest-normalize-handler.zip" -Force

Write-Host "✅ Packages Lambda créés :"
Write-Host "  - engine-handler.zip : $((Get-Item engine-handler.zip).Length / 1KB) KB"
Write-Host "  - ingest-normalize-handler.zip : $((Get-Item ingest-normalize-handler.zip).Length / 1KB) KB"
```

### 4.3 Script de Validation

```powershell
# scripts/validate-packages.ps1
Write-Host "🔍 Validation des packages..."

function Test-PackageSize {
    param($zipPath, $maxSizeMB)
    
    $sizeMB = (Get-Item $zipPath).Length / 1MB
    if ($sizeMB -gt $maxSizeMB) {
        Write-Host "❌ $zipPath trop volumineux : ${sizeMB}MB > ${maxSizeMB}MB"
        return $false
    } else {
        Write-Host "✅ $zipPath : ${sizeMB}MB (OK)"
        return $true
    }
}

$valid = $true

# Valider les tailles
$valid = $valid -and (Test-PackageSize "vectora-core-layer.zip" 25)
$valid = $valid -and (Test-PackageSize "common-deps-layer.zip" 35)
$valid = $valid -and (Test-PackageSize "engine-handler.zip" 1)
$valid = $valid -and (Test-PackageSize "ingest-normalize-handler.zip" 1)

if ($valid) {
    Write-Host "🎉 Tous les packages sont valides !"
} else {
    Write-Host "❌ Certains packages ne respectent pas les contraintes"
    exit 1
}
```

---

## 🧪 Phase 5 : Tests et Validation (Jour 5)

### 5.1 Tests d'Intégration Locaux

```python
# tests/integration/test_refactored_architecture.py
import unittest
import sys
import os

class TestRefactoredArchitecture(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Setup des paths pour simuler les layers"""
        sys.path.insert(0, 'layers/vectora-core/python')
        sys.path.insert(0, 'layers/common-deps/python')
        
        # Variables d'environnement de test
        os.environ.update({
            'CONFIG_BUCKET': 'test-config',
            'DATA_BUCKET': 'test-data',
            'NEWSLETTERS_BUCKET': 'test-newsletters',
            'BEDROCK_MODEL_ID': 'test-model'
        })
    
    def test_vectora_core_import(self):
        """Test que vectora_core s'importe correctement"""
        import vectora_core
        self.assertTrue(hasattr(vectora_core, 'run_engine_for_client'))
        self.assertTrue(hasattr(vectora_core, 'run_ingest_normalize_for_client'))
    
    def test_dependencies_import(self):
        """Test que toutes les dépendances s'importent"""
        import boto3
        import yaml
        import requests
        import feedparser
        from bs4 import BeautifulSoup
        # Tous les imports doivent réussir
    
    def test_engine_handler_structure(self):
        """Test que le handler engine est correct"""
        from src.lambdas.engine.handler import lambda_handler
        
        # Test avec event invalide
        result = lambda_handler({}, None)
        self.assertEqual(result['statusCode'], 400)
        
        # Test avec event valide (mock)
        # Note: nécessiterait des mocks pour S3/Bedrock
    
    def test_package_sizes(self):
        """Test que les packages respectent les contraintes de taille"""
        import os
        
        # Vérifier que les layers existent et ont une taille raisonnable
        self.assertTrue(os.path.exists('layers/vectora-core-layer.zip'))
        self.assertTrue(os.path.exists('layers/common-deps-layer.zip'))
        
        # Vérifier les tailles
        core_size = os.path.getsize('layers/vectora-core-layer.zip') / (1024*1024)
        deps_size = os.path.getsize('layers/common-deps-layer.zip') / (1024*1024)
        
        self.assertLess(core_size, 25, "Vectora core layer trop volumineux")
        self.assertLess(deps_size, 35, "Dependencies layer trop volumineux")

if __name__ == '__main__':
    unittest.main()
```

### 5.2 Test de Déploiement AWS DEV

```powershell
# scripts/test-deploy-dev.ps1
Write-Host "🚀 Test de déploiement sur AWS DEV..."

# 1. Upload des layers vers S3
Write-Host "📤 Upload des layers..."
aws s3 cp vectora-core-layer.zip s3://vectora-inbox-deployment-dev/layers/
aws s3 cp common-deps-layer.zip s3://vectora-inbox-deployment-dev/layers/

# 2. Créer/Mettre à jour les layers
Write-Host "🔄 Mise à jour des layers AWS..."
$coreLayerArn = aws lambda publish-layer-version `
    --layer-name vectora-core `
    --content S3Bucket=vectora-inbox-deployment-dev,S3Key=layers/vectora-core-layer.zip `
    --compatible-runtimes python3.12 `
    --query 'LayerVersionArn' --output text

$depsLayerArn = aws lambda publish-layer-version `
    --layer-name common-deps `
    --content S3Bucket=vectora-inbox-deployment-dev,S3Key=layers/common-deps-layer.zip `
    --compatible-runtimes python3.12 `
    --query 'LayerVersionArn' --output text

Write-Host "✅ Layers créés :"
Write-Host "  - Vectora Core: $coreLayerArn"
Write-Host "  - Common Deps: $depsLayerArn"

# 3. Mettre à jour les fonctions Lambda
Write-Host "🔄 Mise à jour des fonctions Lambda..."

# Upload des handlers
aws s3 cp engine-handler.zip s3://vectora-inbox-deployment-dev/functions/
aws s3 cp ingest-normalize-handler.zip s3://vectora-inbox-deployment-dev/functions/

# Mettre à jour la fonction engine
aws lambda update-function-code `
    --function-name vectora-inbox-engine-dev `
    --s3-bucket vectora-inbox-deployment-dev `
    --s3-key functions/engine-handler.zip

aws lambda update-function-configuration `
    --function-name vectora-inbox-engine-dev `
    --layers $coreLayerArn $depsLayerArn

# Mettre à jour la fonction ingest-normalize
aws lambda update-function-code `
    --function-name vectora-inbox-ingest-normalize-dev `
    --s3-bucket vectora-inbox-deployment-dev `
    --s3-key functions/ingest-normalize-handler.zip

aws lambda update-function-configuration `
    --function-name vectora-inbox-ingest-normalize-dev `
    --layers $coreLayerArn $depsLayerArn

Write-Host "✅ Fonctions Lambda mises à jour"

# 4. Test d'invocation
Write-Host "🧪 Test d'invocation..."
$testPayload = @{
    client_id = "lai_weekly_v3"
    period_days = 7
    test_mode = $true
} | ConvertTo-Json

$result = aws lambda invoke `
    --function-name vectora-inbox-engine-dev `
    --payload $testPayload `
    --output json `
    response.json

Write-Host "📊 Résultat du test :"
Get-Content response.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## 📊 Métriques de Succès

### Avant Refactoring
- **Taille totale src/** : ~200MB
- **Package Lambda** : 70MB
- **Erreurs d'import** : `No module named '_yaml'`
- **Temps de déploiement** : >5 minutes
- **Maintenabilité** : Faible

### Après Refactoring (Objectifs)
- **Taille totale src/** : <50MB
- **Handler Lambda** : <1MB
- **Layer vectora-core** : <20MB
- **Layer common-deps** : <30MB
- **Erreurs d'import** : 0
- **Temps de déploiement** : <2 minutes
- **Maintenabilité** : Élevée

---

## 🚨 Risques et Mitigation

### Risques Identifiés

#### 1. **Rupture de Compatibilité**
- **Risque** : Les imports existants peuvent échouer
- **Mitigation** : Tests complets avant déploiement
- **Rollback** : Branche de sauvegarde disponible

#### 2. **Problèmes de Layers**
- **Risque** : Layers mal configurés ou incompatibles
- **Mitigation** : Tests locaux avec simulation des layers
- **Rollback** : Déploiement des packages monolithiques temporairement

#### 3. **Dépendances Manquantes**
- **Risque** : Oubli de dépendances dans les layers
- **Mitigation** : Script de validation automatique
- **Rollback** : Ajout rapide des dépendances manquantes

### Plan de Rollback

```powershell
# scripts/rollback.ps1
Write-Host "🔄 Rollback vers l'architecture précédente..."

# 1. Restaurer depuis la branche de sauvegarde
git checkout main
git branch -D refactor-src-architecture

# 2. Redéployer les packages monolithiques
./scripts/deploy-engine-dev-simple.ps1

# 3. Valider le fonctionnement
./scripts/test-engine-lai-weekly.ps1
```

---

## 📅 Planning Détaillé

### Jour 1 (Lundi) - Nettoyage
- **09:00-10:00** : Audit et sauvegarde
- **10:00-12:00** : Suppression des duplications
- **14:00-16:00** : Validation post-nettoyage
- **16:00-17:00** : Tests d'import de base

### Jour 2 (Mardi) - Layers
- **09:00-11:00** : Création du layer vectora-core
- **11:00-12:00** : Création du layer common-deps
- **14:00-16:00** : Tests locaux des layers
- **16:00-17:00** : Optimisation et validation

### Jour 3 (Mercredi) - Handlers
- **09:00-11:00** : Mise à jour des requirements
- **11:00-12:00** : Validation des handlers
- **14:00-16:00** : Tests d'intégration locaux
- **16:00-17:00** : Documentation

### Jour 4 (Jeudi) - Scripts
- **09:00-12:00** : Scripts de build et déploiement
- **14:00-16:00** : Scripts de validation
- **16:00-17:00** : Tests des scripts

### Jour 5 (Vendredi) - Tests AWS
- **09:00-11:00** : Déploiement sur AWS DEV
- **11:00-12:00** : Tests d'invocation
- **14:00-16:00** : Validation complète
- **16:00-17:00** : Documentation finale

---

## ✅ Critères de Validation

### Phase 1 - Nettoyage
- [ ] Aucune duplication de dépendances dans `src/`
- [ ] Taille de `src/` réduite de >80%
- [ ] `vectora_core` toujours importable

### Phase 2 - Layers
- [ ] Layer vectora-core créé et testé
- [ ] Layer common-deps créé et testé
- [ ] Tous les imports fonctionnent localement

### Phase 3 - Handlers
- [ ] Handlers inchangés fonctionnellement
- [ ] Requirements.txt documentés
- [ ] Tests d'intégration passent

### Phase 4 - Scripts
- [ ] Build automatisé fonctionnel
- [ ] Validation automatique des packages
- [ ] Documentation des scripts

### Phase 5 - AWS
- [ ] Déploiement AWS réussi
- [ ] Tests d'invocation passent
- [ ] Performance améliorée
- [ ] Aucune régression fonctionnelle

---

## 📞 Support et Escalation

### Contacts
- **Architect Lead** : Disponible pour questions techniques
- **DevOps** : Support pour déploiement AWS
- **QA** : Validation des tests

### Escalation
- **Blocage technique** : Escalation immédiate
- **Problème AWS** : Support AWS Premium
- **Régression critique** : Rollback immédiat

---

**Status** : PRÊT POUR EXÉCUTION  
**Prochaine étape** : Validation du plan et début Phase 1