# Guide des Bonnes Pratiques - Q Developer pour Vectora Inbox

**Date** : 2025-12-13  
**Version** : 1.0  
**Scope** : Règles de développement pour maintenir la qualité du code Lambda AWS  

---

## 🎯 Objectif

Ce guide définit les bonnes pratiques à suivre lors du développement avec Q Developer pour garantir :
- **Architecture Lambda propre** et maintenable
- **Déployabilité AWS** optimale
- **Performance** et **scalabilité**
- **Testabilité** et **debuggabilité**

---

## 📁 Structure de Projet Obligatoire

### ✅ Structure Recommandée

```
vectora-inbox/
├── src/
│   ├── lambdas/
│   │   ├── engine/
│   │   │   ├── handler.py          # Handler minimal uniquement
│   │   │   └── requirements.txt    # Dépendances spécifiques
│   │   └── ingest_normalize/
│   │       ├── handler.py          # Handler minimal uniquement
│   │       └── requirements.txt    # Dépendances spécifiques
│   ├── vectora_core/               # Logique métier pure
│   │   ├── config/
│   │   ├── ingestion/
│   │   ├── matching/
│   │   ├── newsletter/
│   │   ├── normalization/
│   │   ├── scoring/
│   │   ├── storage/
│   │   └── utils/
│   └── layers/                     # Layers AWS Lambda
│       ├── vectora-core-layer/
│       └── common-deps-layer/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── scripts/
│   ├── build-layers.ps1
│   ├── deploy-lambdas.ps1
│   └── test-local.ps1
└── requirements.txt                # Dépendances de développement
```

### ❌ Structures Interdites

```
❌ src/lambdas/engine/package/      # Jamais de package complet
❌ src/boto3/                       # Jamais de dépendances dans src/
❌ src/_yaml/                       # Jamais de libs dans le code source
❌ src/lambdas/engine/vectora_core/ # Jamais de duplication de code
```

---

## 🏗️ Règles d'Architecture Lambda

### 1. **Handlers Minimalistes**

#### ✅ FAIRE : Handler Correct
```python
# src/lambdas/engine/handler.py
import json
import logging
from vectora_core import run_engine_for_client

def lambda_handler(event, context):
    """Handler minimal : parsing + délégation + réponse"""
    try:
        client_id = event.get("client_id")
        if not client_id:
            return {"statusCode": 400, "body": {"error": "client_id required"}}
        
        # Délégation complète à vectora_core
        result = run_engine_for_client(client_id, env_vars=os.environ)
        
        return {"statusCode": 200, "body": result}
    except Exception as e:
        return {"statusCode": 500, "body": {"error": str(e)}}
```

#### ❌ NE PAS FAIRE : Handler avec Logique Métier
```python
# ❌ INTERDIT
def lambda_handler(event, context):
    # ❌ Pas de logique métier dans le handler
    items = []
    for source in sources:
        content = requests.get(source.url)  # ❌ Appels HTTP directs
        parsed = parse_rss(content)         # ❌ Parsing dans le handler
        items.extend(parsed)
    
    # ❌ Pas de traitement de données complexe
    scored_items = calculate_scores(items)
    newsletter = generate_newsletter(scored_items)
```

### 2. **Gestion des Dépendances**

#### ✅ FAIRE : Layers AWS Lambda
```python
# requirements.txt (handler seulement)
# Pas de dépendances lourdes ici - utiliser les layers

# Layer vectora-core-layer contient :
# - vectora_core/

# Layer common-deps-layer contient :
# - boto3, pyyaml, requests, feedparser, etc.
```

#### ❌ NE PAS FAIRE : Dépendances dans le Code Source
```python
# ❌ INTERDIT : Copier les libs dans src/
src/
├── boto3/          # ❌ Jamais !
├── yaml/           # ❌ Jamais !
└── requests/       # ❌ Jamais !
```

### 3. **Séparation des Responsabilités**

#### ✅ FAIRE : Logique Métier dans vectora_core
```python
# src/vectora_core/ingestion/fetcher.py
def fetch_source(source_meta):
    """Logique métier pure - testable indépendamment"""
    url = source_meta.get('url')
    response = requests.get(url, timeout=30)
    return response.text if response.status_code == 200 else None

# src/lambdas/engine/handler.py
def lambda_handler(event, context):
    """Handler minimal - délégation uniquement"""
    return run_engine_for_client(event.get("client_id"))
```

#### ❌ NE PAS FAIRE : Mélange Handler/Logique
```python
# ❌ INTERDIT
def lambda_handler(event, context):
    # ❌ Pas de logique métier complexe ici
    client_config = yaml.load(s3.get_object(...)['Body'])
    sources = resolve_sources(client_config)
    
    for source in sources:
        # ❌ Pas de boucles de traitement dans le handler
        content = fetch_and_parse(source)
        normalized = normalize_with_bedrock(content)
```

---

## 📦 Règles de Packaging

### 1. **Taille des Packages**

#### ✅ Objectifs de Taille
- **Handler Lambda** : < 5MB (code source uniquement)
- **Layer vectora-core** : < 20MB (code métier)
- **Layer common-deps** : < 30MB (dépendances)
- **Total décompressé** : < 250MB (limite AWS)

#### ❌ Tailles Interdites
- **Package Lambda** : > 50MB ❌
- **Fichiers inutiles** : tests, docs, .pyc ❌
- **Dépendances dupliquées** : ❌

### 2. **Contenu des Packages**

#### ✅ Package Lambda (Handler)
```
engine.zip
├── handler.py          # Handler uniquement
└── requirements.txt    # Références aux layers
```

#### ✅ Layer Vectora Core
```
vectora-core-layer.zip
└── python/
    └── vectora_core/
        ├── config/
        ├── ingestion/
        └── [tous les modules métier]
```

#### ❌ Package Lambda Interdit
```
❌ engine.zip
├── handler.py
├── boto3/              # ❌ Dépendances dans le package
├── vectora_core/       # ❌ Code métier dupliqué
└── tests/              # ❌ Tests dans le package
```

---

## 🧪 Règles de Tests

### 1. **Tests Unitaires**

#### ✅ FAIRE : Tests de la Logique Métier
```python
# tests/unit/test_vectora_core.py
import pytest
from vectora_core.scoring import scorer

class TestScorer:
    def test_score_items_with_valid_data(self):
        items = [{"title": "Test", "domain_relevance": {"biotech": 0.8}}]
        rules = {"biotech": {"base_score": 10}}
        
        result = scorer.score_items(items, rules, ["biotech"], {})
        
        assert len(result) == 1
        assert result[0]["final_score"] > 0
```

#### ✅ FAIRE : Tests d'Intégration Lambda
```python
# tests/integration/test_handlers.py
import json
from src.lambdas.engine.handler import lambda_handler

class TestEngineHandler:
    def test_handler_with_valid_event(self):
        event = {"client_id": "test_client"}
        
        result = lambda_handler(event, None)
        
        assert result["statusCode"] == 200
        assert "body" in result
```

#### ❌ NE PAS FAIRE : Tests dans les Packages
```python
# ❌ INTERDIT : Pas de tests dans src/lambdas/
src/lambdas/engine/test_handler.py  # ❌ Jamais !
```

### 2. **Tests Locaux**

#### ✅ FAIRE : Simulation Locale
```python
# scripts/test-local.py
import sys
import os

# Simuler les layers localement
sys.path.insert(0, 'src')
sys.path.insert(0, 'layers/common-deps/python')

# Simuler les variables d'environnement
os.environ['CONFIG_BUCKET'] = 'test-bucket'
os.environ['BEDROCK_MODEL_ID'] = 'test-model'

# Maintenant tester
from src.lambdas.engine.handler import lambda_handler
result = lambda_handler({"client_id": "test"}, None)
```

---

## 🚀 Règles de Déploiement

### 1. **Scripts de Build**

#### ✅ FAIRE : Scripts Automatisés
```powershell
# scripts/build-and-deploy.ps1

# 1. Build des layers
Write-Host "Building layers..."
./scripts/build-vectora-core-layer.ps1
./scripts/build-common-deps-layer.ps1

# 2. Build des handlers
Write-Host "Building handlers..."
./scripts/build-lambda-handlers.ps1

# 3. Déploiement
Write-Host "Deploying to AWS..."
aws cloudformation deploy --template-file infra/lambda-stack.yaml
```

#### ❌ NE PAS FAIRE : Déploiement Manuel
```powershell
# ❌ INTERDIT : Pas de déploiement manuel
zip -r engine.zip src/  # ❌ Package incorrect
aws lambda update-function-code --function-name engine --zip-file fileb://engine.zip  # ❌ Déploiement direct
```

### 2. **Validation Pré-Déploiement**

#### ✅ FAIRE : Checks Automatiques
```python
# scripts/validate-package.py
import zipfile
import sys

def validate_lambda_package(zip_path):
    """Valide qu'un package Lambda respecte les bonnes pratiques"""
    with zipfile.ZipFile(zip_path, 'r') as z:
        files = z.namelist()
        
        # Vérifier la taille
        if len(z.read(files[0])) > 50 * 1024 * 1024:  # 50MB
            print("❌ Package trop volumineux")
            return False
        
        # Vérifier qu'il n'y a pas de dépendances
        forbidden = ['boto3/', 'yaml/', 'requests/']
        for file in files:
            if any(file.startswith(dep) for dep in forbidden):
                print(f"❌ Dépendance interdite trouvée : {file}")
                return False
        
        print("✅ Package valide")
        return True
```

---

## 🔧 Configuration et Variables d'Environnement

### 1. **Variables d'Environnement**

#### ✅ FAIRE : Configuration Externalisée
```python
# src/lambdas/engine/handler.py
def lambda_handler(event, context):
    env_vars = {
        "CONFIG_BUCKET": os.environ.get("CONFIG_BUCKET"),
        "DATA_BUCKET": os.environ.get("DATA_BUCKET"),
        "BEDROCK_MODEL_ID": os.environ.get("BEDROCK_MODEL_ID"),
        "LOG_LEVEL": os.environ.get("LOG_LEVEL", "INFO"),
    }
    
    # Validation
    required = ["CONFIG_BUCKET", "DATA_BUCKET", "BEDROCK_MODEL_ID"]
    missing = [var for var in required if not env_vars.get(var)]
    if missing:
        return {"statusCode": 500, "body": {"error": f"Missing env vars: {missing}"}}
```

#### ❌ NE PAS FAIRE : Configuration Hard-Codée
```python
# ❌ INTERDIT
def lambda_handler(event, context):
    config_bucket = "vectora-inbox-config-dev"  # ❌ Hard-codé
    bedrock_model = "claude-3-sonnet"           # ❌ Hard-codé
```

### 2. **Gestion des Secrets**

#### ✅ FAIRE : AWS Systems Manager
```python
# src/vectora_core/utils/secrets.py
import boto3

def get_secret(parameter_name):
    """Récupère un secret depuis SSM Parameter Store"""
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
    return response['Parameter']['Value']
```

#### ❌ NE PAS FAIRE : Secrets dans le Code
```python
# ❌ INTERDIT
API_KEY = "sk-1234567890abcdef"  # ❌ Jamais de secrets en dur
```

---

## 📊 Monitoring et Logging

### 1. **Logging Structuré**

#### ✅ FAIRE : Logs JSON Structurés
```python
# src/vectora_core/utils/logger.py
import logging
import json

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def info(self, message, **kwargs):
        log_data = {"level": "INFO", "message": message, **kwargs}
        self.logger.info(json.dumps(log_data))

# Usage
logger = StructuredLogger(__name__)
logger.info("Processing items", client_id="lai_weekly", item_count=42)
```

#### ❌ NE PAS FAIRE : Logs Non Structurés
```python
# ❌ INTERDIT
print(f"Processing {len(items)} items for {client_id}")  # ❌ Print
logging.info("Something happened")  # ❌ Message vague
```

### 2. **Métriques CloudWatch**

#### ✅ FAIRE : Métriques Métier
```python
# src/vectora_core/utils/metrics.py
import boto3

def put_metric(metric_name, value, unit='Count', **dimensions):
    """Envoie une métrique CloudWatch"""
    cloudwatch = boto3.client('cloudwatch')
    cloudwatch.put_metric_data(
        Namespace='VectoraInbox',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Dimensions': [{'Name': k, 'Value': v} for k, v in dimensions.items()]
        }]
    )

# Usage
put_metric('ItemsProcessed', len(items), client_id=client_id)
```

---

## 🔒 Sécurité et Bonnes Pratiques

### 1. **Gestion des Erreurs**

#### ✅ FAIRE : Gestion Robuste
```python
def lambda_handler(event, context):
    try:
        result = run_engine_for_client(client_id)
        return {"statusCode": 200, "body": result}
    
    except ValueError as e:
        logger.error("Configuration error", error=str(e))
        return {"statusCode": 400, "body": {"error": "Invalid configuration"}}
    
    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        return {"statusCode": 500, "body": {"error": "Internal server error"}}
```

#### ❌ NE PAS FAIRE : Erreurs Non Gérées
```python
# ❌ INTERDIT
def lambda_handler(event, context):
    client_id = event["client_id"]  # ❌ Peut lever KeyError
    result = run_engine_for_client(client_id)  # ❌ Peut lever n'importe quelle exception
    return result  # ❌ Format de réponse incorrect
```

### 2. **Validation des Entrées**

#### ✅ FAIRE : Validation Stricte
```python
def validate_event(event):
    """Valide l'événement d'entrée"""
    required_fields = ["client_id"]
    for field in required_fields:
        if not event.get(field):
            raise ValueError(f"Missing required field: {field}")
    
    # Validation des types
    if "period_days" in event and not isinstance(event["period_days"], int):
        raise ValueError("period_days must be an integer")
```

---

## 📋 Checklist de Développement

### Avant Chaque Commit

- [ ] ✅ Handlers contiennent uniquement parsing + délégation + réponse
- [ ] ✅ Aucune dépendance dans `src/lambdas/`
- [ ] ✅ Logique métier dans `vectora_core/` uniquement
- [ ] ✅ Tests unitaires pour la nouvelle logique
- [ ] ✅ Variables d'environnement externalisées
- [ ] ✅ Gestion d'erreurs appropriée
- [ ] ✅ Logging structuré

### Avant Chaque Déploiement

- [ ] ✅ Validation des packages (taille, contenu)
- [ ] ✅ Tests d'intégration passent
- [ ] ✅ Layers buildés et testés
- [ ] ✅ Variables d'environnement configurées
- [ ] ✅ Monitoring et alertes en place

### Avant Chaque Release

- [ ] ✅ Tests end-to-end sur AWS DEV
- [ ] ✅ Performance validée (cold start < 5s)
- [ ] ✅ Métriques CloudWatch fonctionnelles
- [ ] ✅ Documentation mise à jour
- [ ] ✅ Rollback plan préparé

---

## 🎓 Formation Continue

### Ressources Recommandées

1. **AWS Lambda Best Practices**
   - [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
   - [Lambda Layers Documentation](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html)

2. **Python pour AWS Lambda**
   - [Python Lambda Packaging](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html)
   - [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

3. **Architecture Serverless**
   - [AWS Well-Architected Serverless Lens](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/)

---

## 🚨 Signalement des Problèmes

Si vous identifiez des violations de ces bonnes pratiques dans le code existant :

1. **Créer un ticket** dans `/docs/diagnostics/`
2. **Documenter** le problème et l'impact
3. **Proposer** une solution conforme
4. **Prioriser** selon l'impact (critique/majeur/mineur)

---

**Version** : 1.0  
**Dernière mise à jour** : 2025-12-13  
**Prochaine révision** : Après refactoring Phase 1