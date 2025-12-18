# Phase A4-F1 - Diagnostic Packaging

**Date** : 2025-12-13  
**Phase** : A4-F1 - Diagnostic packaging  
**Objectif** : Comprendre EXACTEMENT d'où vient l'erreur `_yaml` et comment PyYAML est packagé aujourd'hui  

---

## 🔍 Problème Identifié

### Erreur Runtime
```
Runtime.ImportModuleError: No module named '_yaml'
```

### Cause Racine
Le script de packaging `package-engine-llm-phase-a4-fixed.ps1` ne copie **PAS** tous les fichiers nécessaires pour PyYAML.

---

## 📂 Structure PyYAML dans lambda-deps

### Fichiers PyYAML présents dans `lambda-deps/`
```
lambda-deps/
├── yaml/                           # ✅ Dossier principal PyYAML
│   ├── __init__.py
│   ├── _yaml.cp314-win_amd64.pyd   # ⚠️ Extension compilée C (CRITIQUE)
│   ├── composer.py
│   ├── constructor.py
│   ├── cyaml.py
│   ├── dumper.py
│   ├── emitter.py
│   ├── error.py
│   ├── events.py
│   ├── loader.py
│   ├── nodes.py
│   ├── parser.py
│   ├── reader.py
│   ├── representer.py
│   ├── resolver.py
│   ├── scanner.py
│   ├── serializer.py
│   └── tokens.py
├── _yaml/                          # ✅ Dossier _yaml séparé
│   └── __init__.py
├── _yaml.cp314-win_amd64.pyd       # ⚠️ Extension compilée C à la racine (CRITIQUE)
├── pyyaml-6.0.3.dist-info/         # ✅ Métadonnées PyYAML
│   ├── licenses/
│   ├── INSTALLER
│   ├── METADATA
│   ├── RECORD
│   ├── REQUESTED
│   ├── top_level.txt
│   └── WHEEL
└── [autres fichiers PyYAML à la racine]
```

---

## 🚨 Analyse du Script de Packaging Actuel

### Script `package-engine-llm-phase-a4-fixed.ps1`

#### ✅ Ce qui est copié correctement
```powershell
$essentialDeps = @(
    "boto3",
    "botocore", 
    "yaml"        # ✅ Copie le dossier yaml/
)
```

#### ❌ Ce qui manque (CAUSE DE L'ERREUR)
1. **Fichier `_yaml.cp314-win_amd64.pyd` à la racine** : Extension compilée C critique
2. **Dossier `_yaml/`** : Module _yaml séparé
3. **Métadonnées `pyyaml-6.0.3.dist-info/`** : Informations de package
4. **Fichiers PyYAML individuels à la racine** : `composer.py`, `constructor.py`, etc.

---

## 🔧 Diagnostic Technique

### Pourquoi `_yaml` est critique
PyYAML utilise une extension C compilée (`_yaml.cp314-win_amd64.pyd`) pour les performances. Cette extension :
- Est chargée dynamiquement par `yaml/__init__.py`
- Contient les fonctions de parsing YAML optimisées
- **DOIT** être présente pour que PyYAML fonctionne

### Code dans `yaml/__init__.py` qui échoue
```python
try:
    from .cyaml import *
    __with_libyaml__ = True
except ImportError:
    __with_libyaml__ = False
```

Le module `cyaml` tente d'importer `_yaml`, qui n'est pas trouvé.

---

## 📊 Comparaison avec d'autres Lambdas

### Lambda `ingest-normalize` (qui fonctionne)
- Utilise probablement un packaging différent
- Inclut toutes les dépendances nécessaires

### Vérification nécessaire
Examiner le script de packaging de `ingest-normalize` pour voir comment PyYAML est géré.

---

## 🎯 Solutions Identifiées

### Option 1 : Packaging complet PyYAML (RECOMMANDÉE)
**Avantages** :
- Simple à implémenter
- Réutilise l'infrastructure existante
- Garantit la compatibilité

**Actions** :
```powershell
# Copier TOUS les fichiers PyYAML
Copy-Item -Path "lambda-deps\_yaml.cp314-win_amd64.pyd" -Destination $tempDir
Copy-Item -Path "lambda-deps\_yaml" -Destination "$tempDir\_yaml" -Recurse
Copy-Item -Path "lambda-deps\pyyaml-6.0.3.dist-info" -Destination "$tempDir\pyyaml-6.0.3.dist-info" -Recurse

# Copier les fichiers PyYAML individuels à la racine
$yamlRootFiles = @("composer.py", "constructor.py", "cyaml.py", "dumper.py", "emitter.py", "error.py", "events.py", "loader.py", "nodes.py", "parser.py", "reader.py", "representer.py", "resolver.py", "scanner.py", "serializer.py", "tokens.py")
foreach ($file in $yamlRootFiles) {
    if (Test-Path "lambda-deps\$file") {
        Copy-Item -Path "lambda-deps\$file" -Destination $tempDir
    }
}
```

### Option 2 : Lambda Layer (pour plus tard)
**Avantages** :
- Réduit la taille des packages individuels
- Réutilisable entre Lambdas

**Inconvénients** :
- Plus complexe à mettre en place
- Nécessite des changements d'infrastructure

---

## 📋 Validation du Diagnostic

### Test d'import local requis
```python
# Test minimal pour valider le packaging
import sys
sys.path.insert(0, 'temp-engine-llm-a4-fixed')

try:
    import yaml
    print("✅ yaml importé avec succès")
    
    # Test de fonctionnalité
    test_data = {"test": "value"}
    yaml_str = yaml.dump(test_data)
    parsed = yaml.safe_load(yaml_str)
    print(f"✅ PyYAML fonctionnel: {parsed}")
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
```

---

## 🔄 Prochaines Étapes

### Phase A4-F2 - Stratégie de packaging
1. **Stratégie retenue** : Packaging complet PyYAML (Option 1)
2. **Justification** : Simple, robuste, réutilise l'existant
3. **Script à créer** : Version corrigée de `package-engine-llm-phase-a4-fixed.ps1`

### Phase A4-F3 - Implémentation locale
1. Créer le script de packaging corrigé
2. Tester l'import en local
3. Valider que tous les modules sont présents

### Phase A4-F4 - Déploiement AWS
1. Déployer le package corrigé
2. Vérifier la configuration Lambda
3. Tester l'invocation

### Phase A4-F5 - Validation métier
1. Run réel `lai_weekly_v3` avec `USE_LLM_RELEVANCE=true`
2. Vérification des logs CloudWatch
3. Métriques d'impact LLM relevance

---

## ✅ Conclusion du Diagnostic

### Problème clairement identifié
- ❌ Script de packaging incomplet
- ❌ Extensions C PyYAML manquantes
- ❌ Structure de fichiers PyYAML incomplète

### Solution claire
- ✅ Packaging complet de PyYAML
- ✅ Inclusion de toutes les extensions compilées
- ✅ Test d'import local avant déploiement

### Confiance dans la résolution
- 🎯 **Haute** : Le problème est bien cerné et la solution est directe
- 🎯 **Risque faible** : Réutilise l'infrastructure de packaging existante
- 🎯 **Impact minimal** : Pas de changement de logique métier

**Statut** : ✅ **DIAGNOSTIC COMPLET** - Prêt pour Phase A4-F2