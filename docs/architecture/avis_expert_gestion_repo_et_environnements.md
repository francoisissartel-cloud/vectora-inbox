# Avis Expert Architecte Cloud AWS - Gestion Repo & Environnements Vectora Inbox

**Date**: 2026-01-30  
**Expert**: Architecte Cloud AWS  
**Contexte**: Post-mortem incident layer stage legacy  
**Objectif**: Établir gouvernance propre et best practices

---

## 🎯 RÉPONSES AUX QUESTIONS CRITIQUES

### Q1: Le plan permettra-t-il d'avoir dev/stage correspondant au repo ?

**Réponse**: ⚠️ **PARTIELLEMENT - Nécessite compléments**

**Ce que le plan fait**:
- ✅ Corrige layer stage legacy (problème immédiat)
- ✅ Reconstruit depuis repo local (bonne approche)
- ✅ Propose système promotion (vision long terme)

**Ce que le plan NE fait PAS**:
- ❌ Ne nettoie pas fichiers legacy en dev
- ❌ Ne synchronise pas dev avec repo
- ❌ Ne met pas en place gouvernance stricte
- ❌ Ne crée pas scripts build automatisés

**Verdict**: Le plan corrige l'urgence mais ne résout pas le problème structurel.

---

### Q2: Le plan permettra-t-il de nettoyer AWS des fichiers legacy ?

**Réponse**: ❌ **NON - Pas prévu dans le plan actuel**

**Fichiers legacy identifiés**:

1. **S3 lambda-code-stage**:
   - `layers/vectora-core-v42.zip` (ANCIEN)
   - Autres fichiers .zip potentiellement obsolètes

2. **S3 lambda-code-dev**:
   - Probablement vide ou contient fichiers obsolètes
   - Pas de structure cohérente

3. **Layers AWS**:
   - `vectora-inbox-vectora-core-approche-b-dev:1-9` (anciennes versions)
   - `vectora-inbox-yaml-fix-dev` (legacy)
   - `vectora-inbox-yaml-minimal-dev` (legacy)
   - `vectora-inbox-dependencies` (legacy)

4. **Lambdas potentiellement obsolètes**:
   - Versions anciennes non supprimées
   - Code handlers potentiellement différents

**Impact**: Risque de confusion et réutilisation accidentelle de code obsolète.

---

### Q3: Que recommander IMMÉDIATEMENT pour une gestion propre ?

**Réponse**: 🚨 **ÉTABLIR GOUVERNANCE AVANT CORRECTION**

**Principe**: "Measure twice, cut once" - Définir les règles avant d'agir.

---

## 🏗️ ARCHITECTURE CIBLE RECOMMANDÉE

### Principe Fondamental: Source Unique de Vérité

```
┌─────────────────────────────────────────────────────────────┐
│                    REPO LOCAL (Git)                         │
│                  SOURCE UNIQUE DE VÉRITÉ                    │
│                                                             │
│  src_v2/          - Code source                            │
│  canonical/       - Configurations métier                   │
│  .build/          - Artefacts buildés (gitignored)         │
│  scripts/build/   - Scripts build reproductibles           │
│  scripts/deploy/  - Scripts déploiement                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────────────┐
                    │  BUILD LOCAL  │
                    └───────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              S3 ARTEFACTS VERSIONNÉS (Staging)              │
│                                                             │
│  s3://vectora-inbox-artifacts/                             │
│    ├─ layers/                                              │
│    │   ├─ vectora-core-1.2.3.zip                          │
│    │   └─ common-deps-1.0.5.zip                           │
│    ├─ lambdas/                                             │
│    │   ├─ ingest-v2-1.5.0.zip                             │
│    │   └─ normalize-score-v2-2.1.0.zip                    │
│    └─ canonical/                                           │
│        └─ v1.1/                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
            ┌───────────────────────────────┐
            │                               │
            ↓                               ↓
    ┌──────────────┐              ┌──────────────┐
    │  ENV DEV     │              │  ENV STAGE   │
    │              │              │              │
    │ Version:     │              │ Version:     │
    │ - layers 1.2.3│   Promote   │ - layers 1.2.3│
    │ - lambdas 1.5.0│  ──────→   │ - lambdas 1.5.0│
    │ - canonical 1.1│             │ - canonical 1.1│
    └──────────────┘              └──────────────┘
```

### Avantages Architecture Cible

1. **Source unique**: Repo Git = vérité absolue
2. **Reproductible**: Build identique à chaque fois
3. **Versionné**: Chaque artefact a une version explicite
4. **Traçable**: Git commit → Version artefact → Env déployé
5. **Rollback facile**: Redéployer version précédente
6. **Pas de drift**: Impossible d'avoir dev ≠ stage si même version

---

## 🚨 RÈGLES À METTRE EN PLACE IMMÉDIATEMENT

### RÈGLE #1: Interdiction Modification Directe AWS

**Principe**: Aucune modification manuelle des ressources AWS

**Interdit**:
- ❌ Éditer code Lambda dans console AWS
- ❌ Uploader fichiers manuellement dans S3
- ❌ Créer layers sans script
- ❌ Modifier configs dans S3 directement

**Autorisé**:
- ✅ Modifier code dans repo local
- ✅ Exécuter scripts build
- ✅ Exécuter scripts deploy
- ✅ Consulter AWS (lecture seule)

**Enforcement**: 
```markdown
# Ajouter dans .q-context/vectora-inbox-development-rules.md

## 🚫 RÈGLE CRITIQUE: INTERDICTION MODIFICATION DIRECTE AWS

Q Developer DOIT REFUSER toute commande qui modifie AWS sans passer par scripts.

❌ INTERDIT:
- aws lambda update-function-code (manuel)
- aws s3 cp fichier.zip s3://... (manuel)
- Édition console AWS

✅ OBLIGATOIRE:
- Modifier repo local
- python scripts/build/build_all.py
- python scripts/deploy/deploy_env.py --env dev

Exception: Debugging urgent avec validation post-facto obligatoire.
```

---

### RÈGLE #2: Versioning Obligatoire

**Principe**: Chaque artefact a une version sémantique

**Format**: `MAJOR.MINOR.PATCH` (ex: 1.2.3)

**Versioning**:
- **Layers**: `vectora-core-1.2.3.zip`
- **Lambdas**: `ingest-v2-1.5.0.zip`
- **Canonical**: Tag Git `canonical-v1.1`

**Fichier version**: `VERSION` à la racine du repo
```
VECTORA_CORE_VERSION=1.2.3
COMMON_DEPS_VERSION=1.0.5
INGEST_VERSION=1.5.0
NORMALIZE_VERSION=2.1.0
NEWSLETTER_VERSION=1.8.0
CANONICAL_VERSION=1.1
```

**Enforcement**:
```python
# scripts/build/build_all.py
def get_version(component):
    with open('VERSION') as f:
        for line in f:
            if line.startswith(f'{component}_VERSION='):
                return line.split('=')[1].strip()
    raise ValueError(f"Version {component} not found")
```

---

### RÈGLE #3: Build Reproductible

**Principe**: Même code → Même artefact

**Exigences**:
- Build depuis repo local propre (git status clean)
- Dépendances figées (requirements.txt avec versions exactes)
- Pas de dépendances système
- Checksum artefacts documenté

**Script build standard**:
```bash
# scripts/build/build_all.py
1. Vérifier git status clean
2. Lire versions depuis VERSION
3. Builder layers avec versions
4. Builder lambdas avec versions
5. Calculer checksums
6. Générer manifest.json
```

**Manifest artefacts**:
```json
{
  "build_date": "2026-01-30T14:30:00Z",
  "git_commit": "a1b2c3d4",
  "git_branch": "main",
  "artifacts": {
    "vectora-core": {
      "version": "1.2.3",
      "file": "vectora-core-1.2.3.zip",
      "sha256": "abc123...",
      "size_bytes": 260005
    }
  }
}
```

---

### RÈGLE #4: Promotion Contrôlée

**Principe**: Dev → Stage → Prod avec validation à chaque étape

**Workflow**:
```
1. Développement en local
2. Build artefacts versionnés
3. Deploy dev + Tests automatiques
4. Si tests OK → Promotion stage
5. Tests stage + Validation métier
6. Si validation OK → Promotion prod
```

**Checklist promotion**:
```markdown
## Checklist Promotion Dev → Stage

### Pré-Promotion
- [ ] Tests E2E dev réussis (>95% succès)
- [ ] Aucune régression détectée
- [ ] Changelog version documenté
- [ ] Code review approuvé
- [ ] Snapshot dev créé

### Promotion
- [ ] Version identique dev/stage
- [ ] Artefacts checksums validés
- [ ] Configs synchronisées
- [ ] Variables ENV correctes

### Post-Promotion
- [ ] Tests E2E stage réussis
- [ ] Métriques cohérentes (±5%)
- [ ] Validation fonctionnelle OK
- [ ] Rapport promotion généré
```

---

### RÈGLE #5: Nettoyage Régulier

**Principe**: Supprimer ressources obsolètes régulièrement

**Fréquence**: Hebdomadaire

**Cibles**:
- Layers anciennes versions (garder 3 dernières)
- Lambdas versions non utilisées
- Fichiers S3 temporaires (>30 jours)
- Logs CloudWatch (>90 jours)

**Script nettoyage**:
```bash
# scripts/maintenance/cleanup_aws.py --env dev --dry-run
# scripts/maintenance/cleanup_aws.py --env dev --execute
```

---

## 📋 PLAN D'ACTION RECOMMANDÉ (Avant Correction)

### PHASE 0: Établir Gouvernance (1 jour)

**Objectif**: Mettre en place règles et structure avant toute action

#### 0.1 Créer Structure Repo

```bash
# Créer dossiers manquants
mkdir -p .build/layers
mkdir -p .build/lambdas
mkdir -p .build/manifests
mkdir -p scripts/build
mkdir -p scripts/deploy
mkdir -p scripts/test
mkdir -p scripts/maintenance

# Créer fichier VERSION
echo "VECTORA_CORE_VERSION=1.2.3" > VERSION
echo "COMMON_DEPS_VERSION=1.0.5" >> VERSION
echo "INGEST_VERSION=1.5.0" >> VERSION
echo "NORMALIZE_VERSION=2.1.0" >> VERSION
echo "NEWSLETTER_VERSION=1.8.0" >> VERSION
echo "CANONICAL_VERSION=1.1" >> VERSION

# Mettre à jour .gitignore
echo ".build/" >> .gitignore
echo ".tmp/" >> .gitignore
```

#### 0.2 Mettre à Jour Règles Développement

**Fichier**: `.q-context/vectora-inbox-development-rules.md`

**Ajouter**:
- Règle #1: Interdiction modification directe AWS
- Règle #2: Versioning obligatoire
- Règle #3: Build reproductible
- Règle #4: Promotion contrôlée
- Règle #5: Nettoyage régulier

#### 0.3 Créer Scripts Build Minimaux

**Fichier**: `scripts/build/build_layer_vectora_core.py`

```python
#!/usr/bin/env python3
"""Build vectora-core layer avec versioning"""
import os
import shutil
import zipfile
from pathlib import Path

def get_version():
    with open('VERSION') as f:
        for line in f:
            if line.startswith('VECTORA_CORE_VERSION='):
                return line.split('=')[1].strip()
    raise ValueError("VECTORA_CORE_VERSION not found")

def build_layer():
    version = get_version()
    print(f"Building vectora-core layer version {version}")
    
    # Créer structure
    build_dir = Path('.build/layers/vectora-core-build')
    build_dir.mkdir(parents=True, exist_ok=True)
    python_dir = build_dir / 'python'
    python_dir.mkdir(exist_ok=True)
    
    # Copier code
    shutil.copytree('src_v2/vectora_core', python_dir / 'vectora_core')
    
    # Créer zip
    output_file = f'.build/layers/vectora-core-{version}.zip'
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(build_dir)
                zipf.write(file_path, arcname)
    
    # Nettoyer
    shutil.rmtree(build_dir)
    
    print(f"✅ Layer built: {output_file}")
    return output_file

if __name__ == '__main__':
    build_layer()
```

#### 0.4 Créer Script Deploy Minimal

**Fichier**: `scripts/deploy/deploy_layer.py`

```python
#!/usr/bin/env python3
"""Deploy layer vers environnement AWS"""
import argparse
import boto3
import hashlib
from pathlib import Path

def deploy_layer(layer_file, env, layer_name):
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    s3 = session.client('s3')
    lambda_client = session.client('lambda')
    
    # Upload vers S3
    bucket = f'vectora-inbox-lambda-code-{env}'
    key = f'layers/{Path(layer_file).name}'
    
    print(f"Uploading {layer_file} to s3://{bucket}/{key}")
    s3.upload_file(layer_file, bucket, key)
    
    # Publier layer
    print(f"Publishing layer {layer_name}-{env}")
    response = lambda_client.publish_layer_version(
        LayerName=f'{layer_name}-{env}',
        Content={'S3Bucket': bucket, 'S3Key': key},
        CompatibleRuntimes=['python3.11', 'python3.12'],
        Description=f'Built from repo - {Path(layer_file).stem}'
    )
    
    print(f"✅ Layer published: {response['LayerVersionArn']}")
    return response['LayerVersionArn']

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--layer-file', required=True)
    parser.add_argument('--env', required=True, choices=['dev', 'stage', 'prod'])
    parser.add_argument('--layer-name', required=True)
    args = parser.parse_args()
    
    deploy_layer(args.layer_file, args.env, args.layer_name)
```

#### 0.5 Documenter Workflow

**Fichier**: `docs/workflows/build_and_deploy.md`

```markdown
# Workflow Build & Deploy

## 1. Développement Local

```bash
# Modifier code dans src_v2/
git add .
git commit -m "feat: nouvelle fonctionnalité"
```

## 2. Build Artefacts

```bash
# Incrémenter version dans VERSION
# VECTORA_CORE_VERSION=1.2.4

# Build layer
python scripts/build/build_layer_vectora_core.py
```

## 3. Deploy Dev

```bash
# Deploy layer
python scripts/deploy/deploy_layer.py \
  --layer-file .build/layers/vectora-core-1.2.4.zip \
  --env dev \
  --layer-name vectora-inbox-vectora-core

# Mettre à jour Lambda
python scripts/deploy/update_lambda.py \
  --function vectora-inbox-normalize-score-v2-dev \
  --layer-version latest
```

## 4. Tests Dev

```bash
python scripts/test/test_e2e.py --env dev --client lai_weekly_v7
```

## 5. Promotion Stage

```bash
python scripts/deploy/promote.py --from dev --to stage --version 1.2.4
```
```

---

### PHASE 1: Audit et Nettoyage AWS (2 heures)

**Objectif**: Inventorier et nettoyer ressources obsolètes

#### 1.1 Inventaire Complet

**Script**: `scripts/maintenance/audit_aws.py`

```python
#!/usr/bin/env python3
"""Audit complet ressources AWS Vectora Inbox"""
import boto3
import json
from datetime import datetime

def audit_layers(session, env):
    lambda_client = session.client('lambda')
    layers = []
    
    # Lister tous les layers
    response = lambda_client.list_layers()
    for layer in response['Layers']:
        if 'vectora-inbox' in layer['LayerName']:
            versions = lambda_client.list_layer_versions(
                LayerName=layer['LayerName']
            )
            for version in versions['LayerVersions']:
                layers.append({
                    'name': layer['LayerName'],
                    'version': version['Version'],
                    'arn': version['LayerVersionArn'],
                    'created': version['CreatedDate'],
                    'size': version.get('CodeSize', 0),
                    'description': version.get('Description', '')
                })
    
    return layers

def audit_s3_files(session, env):
    s3 = session.client('s3')
    bucket = f'vectora-inbox-lambda-code-{env}'
    files = []
    
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix='layers/')
        for obj in response.get('Contents', []):
            files.append({
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat()
            })
    except:
        pass
    
    return files

def main():
    session = boto3.Session(profile_name='rag-lai-prod', region_name='eu-west-3')
    
    report = {
        'audit_date': datetime.now().isoformat(),
        'dev': {
            'layers': audit_layers(session, 'dev'),
            's3_files': audit_s3_files(session, 'dev')
        },
        'stage': {
            'layers': audit_layers(session, 'stage'),
            's3_files': audit_s3_files(session, 'stage')
        }
    }
    
    with open('.tmp/audit_aws.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print("✅ Audit complet: .tmp/audit_aws.json")

if __name__ == '__main__':
    main()
```

#### 1.2 Identifier Ressources Obsolètes

**Critères obsolescence**:
- Layers avec nommage legacy (`approche-b`, `yaml-fix`, etc.)
- Layers versions anciennes (garder 3 dernières)
- Fichiers S3 non référencés par layers actifs
- Lambdas versions non utilisées

#### 1.3 Plan Nettoyage

**Fichier**: `.tmp/plan_nettoyage_aws.md`

**Contenu**:
- Liste ressources à supprimer
- Risques identifiés
- Ordre suppression
- Commandes exécution

---

### PHASE 2: Reconstruction Propre (4 heures)

**Objectif**: Reconstruire dev et stage depuis repo local

#### 2.1 Reconstruire Dev

```bash
# 1. Build depuis repo
python scripts/build/build_layer_vectora_core.py
python scripts/build/build_layer_common_deps.py

# 2. Deploy dev
python scripts/deploy/deploy_layer.py --layer-file .build/layers/vectora-core-1.2.3.zip --env dev --layer-name vectora-inbox-vectora-core
python scripts/deploy/deploy_layer.py --layer-file .build/layers/common-deps-1.0.5.zip --env dev --layer-name vectora-inbox-common-deps

# 3. Mettre à jour Lambdas dev
python scripts/deploy/update_all_lambdas.py --env dev

# 4. Tests
python scripts/test/test_e2e.py --env dev
```

#### 2.2 Reconstruire Stage

```bash
# Même processus que dev
python scripts/deploy/deploy_layer.py --layer-file .build/layers/vectora-core-1.2.3.zip --env stage --layer-name vectora-inbox-vectora-core
python scripts/deploy/deploy_layer.py --layer-file .build/layers/common-deps-1.0.5.zip --env stage --layer-name vectora-inbox-common-deps
python scripts/deploy/update_all_lambdas.py --env stage
python scripts/test/test_e2e.py --env stage
```

#### 2.3 Validation Alignement

```bash
# Comparer dev et stage
python scripts/test/compare_environments.py --env1 dev --env2 stage
```

---

## ✅ RECOMMANDATIONS FINALES

### Ordre d'Exécution Recommandé

**NE PAS exécuter plan_correctif_layer_stage_et_amelioration_promotion.md immédiatement**

**À la place**:

1. **JOUR 1: Gouvernance** (ce document)
   - Mettre à jour règles développement
   - Créer structure repo
   - Créer scripts build/deploy minimaux
   - Documenter workflow

2. **JOUR 2: Audit & Nettoyage**
   - Auditer ressources AWS
   - Identifier obsolètes
   - Nettoyer progressivement

3. **JOUR 3-4: Reconstruction**
   - Reconstruire dev depuis repo
   - Reconstruire stage depuis repo
   - Valider alignement

4. **JOUR 5: Validation**
   - Tests E2E complets
   - Comparaison métriques
   - Documentation finale

### Bénéfices Approche Recommandée

✅ **Source unique**: Repo = vérité absolue  
✅ **Reproductible**: Build identique à chaque fois  
✅ **Traçable**: Git commit → Version → Env  
✅ **Propre**: Pas de fichiers legacy  
✅ **Sécurisé**: Promotion contrôlée  
✅ **Maintenable**: Scripts automatisés  

### Risques Approche Actuelle (Plan Correctif Seul)

⚠️ **Correction symptôme**: Layer stage corrigé mais problème structurel reste  
⚠️ **Pas de gouvernance**: Risque répétition erreur  
⚠️ **Fichiers legacy**: Restent en place, risque confusion  
⚠️ **Pas de versioning**: Impossible tracer versions déployées  
⚠️ **Pas de rollback**: Difficile revenir en arrière  

---

## 🎯 VERDICT FINAL

### Le plan actuel est-il suffisant ?

**NON** - Il corrige l'urgence mais ne résout pas le problème de fond.

### Que faire ?

**OPTION A (RECOMMANDÉE)**: Établir gouvernance PUIS exécuter plan correctif modifié

**OPTION B**: Exécuter plan correctif PUIS établir gouvernance (risque répétition)

### Mon avis d'expert

En tant qu'architecte cloud AWS, je recommande **FORTEMENT l'OPTION A**.

**Pourquoi ?**
- Vous avez déjà perdu du temps avec l'incident layer legacy
- Sans gouvernance, vous allez répéter l'erreur
- Investir 2 jours maintenant = Économiser des semaines plus tard
- Vous aurez un système propre, maintenable, et professionnel

**Analogie**: Vous ne construisez pas une maison sans fondations. Les règles de gouvernance sont vos fondations.

---

**Avis Expert - Version 1.0**  
**Date**: 2026-01-30  
**Recommandation**: ÉTABLIR GOUVERNANCE AVANT CORRECTION  
**Priorité**: CRITIQUE
