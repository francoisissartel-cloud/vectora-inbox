# Plan de Correction Lambda Layer PyYAML - vectora-inbox-normalize-score-v2

**Date :** 17 décembre 2025  
**Objectif :** Corriger définitivement l'erreur "No module named 'yaml'" sans contournement code  
**Contraintes :** Respect strict src_lambda_hygiene_v4.md  

---

## Rappel du Contexte

L'architecture V2 Vectora Inbox est déployée avec succès pour vectora-inbox-ingest-v2, mais vectora-inbox-normalize-score-v2 échoue systématiquement avec "No module named 'yaml'". Les corrections précédentes ont créé des layers PyYAML et mis à jour la configuration Lambda, avec restauration du code depuis src_v2, mais l'erreur persiste. Les règles d'hygiène V4 interdisent formellement toute dépendance tierce dans /src, tout stub _yaml ou module factice, et imposent que les dépendances transitent exclusivement via Lambda Layers. Le diagnostic E2E a révélé une progression d'erreurs : yaml → vectora_core.normalization → requests, indiquant un problème de packaging complet des dépendances dans les layers.

---

## Phase 1 – Audit des Layers et du Runtime

### 1.1 Inspection Configuration Lambda Actuelle

**Commandes d'audit prévues :**
```bash
# Configuration complète de la Lambda
aws lambda get-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --profile rag-lai-prod --region eu-west-3 \
  --output json > lambda_config_audit.json

# Extraction des layers attachés (ARN + versions)
jq '.Layers[] | {LayerArn: .Arn, Version: .Arn | split(":") | .[-1]}' lambda_config_audit.json

# Runtime Python exact
jq '.Runtime' lambda_config_audit.json
```

**Informations à collecter :**
- ARN exact de chaque layer attaché
- Version de chaque layer
- Runtime Python (attendu : python3.11)
- Variables d'environnement éventuelles
- Timeout et mémoire configurés

### 1.2 Inspection Contenu des Layers

**Pour chaque layer identifié :**
```bash
# Téléchargement du layer
aws lambda get-layer-version \
  --layer-name vectora-inbox-common-deps-dev \
  --version-number X \
  --profile rag-lai-prod --region eu-west-3 \
  --output json > layer_info.json

# URL de téléchargement
jq -r '.Content.Location' layer_info.json

# Téléchargement et inspection
wget -O layer.zip "$(jq -r '.Content.Location' layer_info.json)"
unzip -l layer.zip | head -20
unzip layer.zip
ls -la python/ 2>/dev/null || ls -la
```

**Vérifications critiques :**
- Structure racine : présence du dossier `python/`
- Contenu PyYAML : `python/yaml/` et `python/_yaml/` (si extension C)
- Autres dépendances : `python/requests/`, `python/boto3/`
- Permissions et ownership des fichiers

---

## Phase 2 – Vérification Structure Interne Layer PyYAML

### 2.1 Structure Attendue pour Runtime Python 3.11

**Structure correcte requise :**
```
layer.zip
└── python/
    ├── yaml/
    │   ├── __init__.py
    │   ├── loader.py
    │   ├── dumper.py
    │   └── ...
    ├── requests/
    │   ├── __init__.py
    │   └── ...
    ├── boto3/
    │   ├── __init__.py
    │   └── ...
    └── feedparser/
        ├── __init__.py
        └── ...
```

**Structure alternative possible :**
```
layer.zip
└── python/
    └── lib/
        └── python3.11/
            └── site-packages/
                ├── yaml/
                ├── requests/
                └── ...
```

### 2.2 Checks de Validation

**Vérifications à effectuer :**
1. **Racine correcte :** Le zip contient-il `python/` à la racine ?
2. **PyYAML complet :** Présence de `yaml/__init__.py` et modules core
3. **Mode pur Python :** Absence d'extensions C (`_yaml.cpython-311-x86_64-linux-gnu.so`)
4. **Dépendances complètes :** requests, boto3, feedparser présents
5. **Permissions :** Fichiers lisibles (644) et dossiers exécutables (755)

**Commandes de diagnostic :**
```bash
# Vérification structure
find python/ -name "*.py" | grep -E "(yaml|requests|boto3)" | head -10

# Vérification extensions C (à éviter)
find python/ -name "*.so" | grep yaml

# Test import local
cd python && python3 -c "import yaml; print(yaml.__version__)"
```

---

## Phase 3 – Reconstruction Propre du Layer PyYAML

### 3.1 Environnement de Build Compatible

**Approche Docker (recommandée) :**
```bash
# Environnement Linux compatible Lambda
docker run --rm -v $(pwd):/workspace python:3.11-slim bash -c "
  cd /workspace
  mkdir -p layer_rebuild/python
  
  # Installation mode pur Python (pas d'extensions C)
  pip install --target layer_rebuild/python --no-binary PyYAML \
    PyYAML==6.0.1 \
    boto3==1.34.0 \
    requests==2.31.0 \
    feedparser==6.0.10
  
  # Création du zip avec structure correcte
  cd layer_rebuild
  zip -r ../vectora-common-deps-fixed.zip python/
"
```

**Approche pip locale (alternative) :**
```bash
mkdir layer_rebuild && cd layer_rebuild
mkdir python

# Installation avec platform Linux
pip install --target python/ --platform manylinux2014_x86_64 --only-binary=:none: \
  PyYAML==6.0.1 \
  boto3==1.34.0 \
  requests==2.31.0 \
  feedparser==6.0.10

zip -r ../vectora-common-deps-fixed.zip python/
```

### 3.2 Upload et Attachement du Layer

**Création nouvelle version :**
```bash
# Upload du layer corrigé
aws lambda publish-layer-version \
  --layer-name vectora-inbox-common-deps-dev \
  --zip-file fileb://vectora-common-deps-fixed.zip \
  --compatible-runtimes python3.11 \
  --description "PyYAML + deps complètes - fix No module named yaml" \
  --profile rag-lai-prod --region eu-west-3

# Récupération ARN nouvelle version
NEW_LAYER_ARN=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-common-deps-dev \
  --profile rag-lai-prod --region eu-west-3 \
  --query 'LayerVersions[0].LayerVersionArn' --output text)

echo "Nouveau layer ARN: $NEW_LAYER_ARN"
```

**Mise à jour configuration Lambda :**
```bash
# Attachement du nouveau layer
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers "$NEW_LAYER_ARN" \
  --profile rag-lai-prod --region eu-west-3
```

---

## Phase 4 – Instrumentation Temporaire de la Lambda

### 4.1 Logs de Diagnostic Runtime

**Ajout temporaire dans handler.py (src_v2/normalize_score_v2/handler.py) :**
```python
import sys
import os
import json

def lambda_handler(event, context):
    # LOGS TEMPORAIRES - DIAGNOSTIC LAYER
    print(f"=== DIAGNOSTIC RUNTIME ===")
    print(f"Python version: {sys.version}")
    print(f"Python path: {json.dumps(sys.path, indent=2)}")
    
    # Inspection /opt (layers)
    if os.path.exists("/opt"):
        print(f"/opt contents: {os.listdir('/opt')}")
        if os.path.exists("/opt/python"):
            print(f"/opt/python contents: {os.listdir('/opt/python')}")
            
    # Test import yaml
    try:
        import yaml
        print(f"✅ yaml imported successfully: {yaml.__version__}")
    except ImportError as e:
        print(f"❌ yaml import failed: {e}")
        
    # Test import requests
    try:
        import requests
        print(f"✅ requests imported successfully: {requests.__version__}")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
    
    print(f"=== END DIAGNOSTIC ===")
    
    # Code original
    from vectora_core.normalization.normalize_score_handler import handle_normalize_score
    return handle_normalize_score(event, context)
```

### 4.2 Déploiement Version Diagnostic

**Package et déploiement :**
```bash
cd src_v2
python ../scripts/package_normalize_score_v2_deploy.py
```

**Test avec logs :**
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3"}' \
  response_diagnostic.json \
  --profile rag-lai-prod --region eu-west-3

# Consultation logs CloudWatch
aws logs filter-log-events \
  --log-group-name /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --start-time $(date -d '5 minutes ago' +%s)000 \
  --profile rag-lai-prod --region eu-west-3
```

---

## Phase 5 – Tests Ciblés

### 5.1 Test Import Minimal

**Payload de test simple :**
```json
{
  "client_id": "lai_weekly_v3",
  "test_mode": true
}
```

**Critères de succès :**
- ✅ Logs montrent "yaml imported successfully"
- ✅ Logs montrent "requests imported successfully"
- ✅ Pas d'erreur "No module named"
- ✅ Handler vectora_core accessible

### 5.2 Test Fonctionnel Complet

**Après succès import, test avec données réelles :**
```bash
# Test sur vraies données S3 lai_weekly_v3
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3"}' \
  response_functional_test.json \
  --profile rag-lai-prod --region eu-west-3

# Vérification outputs S3
aws s3 ls s3://vectora-inbox-dev/curated/lai_weekly_v3/ \
  --profile rag-lai-prod --region eu-west-3
```

**Critères de succès fonctionnel :**
- ✅ Exécution sans erreur technique
- ✅ Fichiers créés dans S3 curated/
- ✅ Logs Bedrock API calls (si configuré)
- ✅ Durée d'exécution < 5 minutes

---

## Phase 6 – Rapport de Correctif

### 6.1 Structure du Rapport Final

**Fichier à créer :** `docs/diagnostics/normalize_score_v2_yaml_layer_fix_report.md`

**Sections obligatoires :**
1. **Cause Racine Identifiée**
   - Analyse technique précise du problème layer
   - Différence entre structure attendue vs réelle
   - Impact sur la chaîne d'imports vectora_core

2. **Modifications Exactes Réalisées**
   - Commandes de reconstruction du layer
   - Configuration Lambda mise à jour
   - Versions des dépendances installées

3. **Validation et Tests**
   - Logs de diagnostic runtime
   - Résultats tests import + fonctionnel
   - Métriques de performance observées

4. **Recommandations Hygiène V4**
   - Mise à jour éventuelle src_lambda_hygiene_v4.md
   - Section "Packaging des layers PyYAML"
   - Procédure de validation layers

### 6.2 Annexe Options de Contournement (Non Implémentées)

**Important :** Le rapport documentera uniquement en annexe, sans implémentation :
- Option B : Contournement s3_io.py avec import conditionnel
- Option C : Fallback YAML custom pour environnement Lambda
- Évaluation de ces options pour cycles futurs si nécessaire

---

## Important : Pas de Contournement dans s3_io.py

**Engagement ferme pour ce cycle :**
- ❌ Aucun workaround dans s3_io.py ne sera implémenté
- ❌ Aucun import conditionnel magique dans le code métier
- ❌ Aucun fallback YAML custom temporaire
- ✅ Correction uniquement via layers et configuration Lambda
- ✅ Toute idée de contournement sera documentée en annexe du rapport final comme option future, mais non codée

**Justification :** Respecter l'architecture propre V2 et identifier la vraie cause racine du problème de packaging des layers, plutôt que masquer le symptôme par du code de contournement.

---

## Livrables Attendus

1. **✅ Plan détaillé** : `docs/design/normalize_score_v2_yaml_layer_debug_plan.md`
2. **🎯 Layer PyYAML corrigé** : Nouvelle version avec structure et dépendances complètes
3. **📋 Logs de validation** : Import yaml + requests fonctionnels en Lambda
4. **📊 Rapport final** : `docs/diagnostics/normalize_score_v2_yaml_layer_fix_report.md`

**Durée estimée :** 4-6 heures  
**Priorité :** Critique - Bloquant pour pipeline V2 complet