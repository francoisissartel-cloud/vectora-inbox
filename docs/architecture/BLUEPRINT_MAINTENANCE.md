# Guide de Maintenance du Blueprint

**Objectif** : Éviter que le blueprint devienne obsolète comme avant

---

## 🎯 Principe

**Le blueprint doit être mis à jour PENDANT les chantiers, pas après.**

---

## 📋 Règles de Mise à Jour

### Règle 1 : Mise à jour OBLIGATOIRE pour changements majeurs

**Changements majeurs** (mise à jour blueprint OBLIGATOIRE) :
- ✅ Ajout/suppression/modification de Lambda
- ✅ Changement de modèle Bedrock
- ✅ Nouveau système (ex: prompts canoniques)
- ✅ Changement d'architecture (ex: 2 Lambdas → 3 Lambdas)
- ✅ Nouveau bucket S3 ou changement de structure
- ✅ Modification des variables d'environnement critiques
- ✅ Changement de région AWS

**Action** : Mettre à jour le blueprint DANS LE MÊME COMMIT que le code

### Règle 2 : Mise à jour RECOMMANDÉE pour changements mineurs

**Changements mineurs** (mise à jour recommandée) :
- ⚠️ Ajout de paramètres optionnels dans event Lambda
- ⚠️ Modification de timeout/memory Lambda
- ⚠️ Ajout de nouveaux scopes canonical
- ⚠️ Modification de seuils dans client config

**Action** : Mettre à jour le blueprint dans un commit dédié (peut être différé)

### Règle 3 : Pas de mise à jour nécessaire

**Changements qui ne nécessitent PAS de mise à jour** :
- ❌ Corrections de bugs sans impact architecture
- ❌ Refactoring interne sans changement d'interface
- ❌ Ajout de logs
- ❌ Modifications de documentation autre que blueprint

---

## 🔄 Workflow de Mise à Jour

### Scénario 1 : Changement majeur (ex: nouvelle Lambda)

```bash
# 1. Créer branche feature
git checkout -b feature/add-analytics-lambda

# 2. Développer le code
# Modifier src_v2/lambdas/analytics/handler.py
# Modifier infra/s1-runtime.yaml

# 3. Mettre à jour le blueprint IMMÉDIATEMENT
# Éditer docs/architecture/blueprint-v2-ACTUAL-2026.yaml
# Ajouter section pour analytics Lambda

# 4. Commit ENSEMBLE
git add src_v2/ infra/ docs/architecture/blueprint-v2-ACTUAL-2026.yaml
git commit -m "feat: add analytics lambda

- Add analytics Lambda for metrics collection
- Update CloudFormation template
- Update blueprint with analytics Lambda details

Refs: #123"

# 5. Push et PR
git push origin feature/add-analytics-lambda
```

### Scénario 2 : Changement mineur (ex: nouveau scope)

```bash
# 1. Modifier canonical
# Éditer canonical/scopes/company_scopes.yaml

# 2. Sync vers S3
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/

# 3. Tester
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# 4. Si OK, mettre à jour blueprint (peut être différé)
# Éditer docs/architecture/blueprint-v2-ACTUAL-2026.yaml
# Mettre à jour section tuning_guide si nécessaire

# 5. Commit
git add canonical/ docs/architecture/blueprint-v2-ACTUAL-2026.yaml
git commit -m "feat: add new companies to lai_companies_global

- Add 5 new biotech companies
- Update blueprint tuning guide examples"
```

---

## ✅ Checklist Avant Merge

**Avant de merger une PR avec changements majeurs** :

- [ ] Code modifié
- [ ] Tests passés
- [ ] Blueprint mis à jour (section concernée)
- [ ] Date `last_updated` mise à jour dans blueprint
- [ ] Changelog ajouté dans section `metadata.changes` du blueprint
- [ ] README.md mis à jour si nécessaire

---

## 🤖 Automatisation avec Q Developer

### Prompt pour Q Developer

Quand vous faites un changement majeur, demandez à Q :

```
J'ai modifié [description du changement].

Mets à jour le blueprint docs/architecture/blueprint-v2-ACTUAL-2026.yaml 
pour refléter ce changement.

Sections à mettre à jour : [architecture/bedrock/prompt_system/etc.]
```

### Règle pour Q Developer

Ajouter dans `.q-context/vectora-inbox-development-rules.md` :

```markdown
## Maintenance du Blueprint

**Q Developer DOIT** :
- ✅ Proposer la mise à jour du blueprint pour tout changement majeur
- ✅ Inclure la mise à jour du blueprint dans le même commit que le code
- ✅ Mettre à jour la date `last_updated` dans le blueprint
- ✅ Ajouter une entrée dans `metadata.changes`

**Changements majeurs nécessitant mise à jour blueprint** :
- Modification d'architecture (Lambdas, buckets, IAM)
- Changement de modèle Bedrock ou région
- Nouveau système (prompts, scopes, etc.)
- Modification des variables d'environnement critiques
```

---

## 📊 Audit Périodique

### Fréquence : Mensuel ou après chaque release majeure

**Checklist d'audit** :

1. **Architecture** :
   - [ ] Lambdas dans blueprint = Lambdas déployées ?
   - [ ] Variables d'environnement à jour ?
   - [ ] Permissions IAM à jour ?

2. **Bedrock** :
   - [ ] Modèle dans blueprint = Modèle en prod ?
   - [ ] Région correcte ?

3. **Configuration** :
   - [ ] Client de référence à jour ?
   - [ ] Versions dans VERSION = Versions dans blueprint ?

4. **Guide d'ajustement** :
   - [ ] Exemples toujours valides ?
   - [ ] Nouveaux leviers documentés ?

**Commande d'audit** :

```bash
# Script à créer
python scripts/maintenance/audit_blueprint.py
```

---

## 🔧 Script d'Audit Automatique

Créer `scripts/maintenance/audit_blueprint.py` :

```python
"""
Audit du blueprint pour détecter les divergences avec le code/infra.

Vérifie :
- Lambdas dans blueprint vs handlers dans src_v2/
- Versions dans blueprint vs VERSION
- Modèle Bedrock dans blueprint vs infra CloudFormation
"""

import yaml
import os
from pathlib import Path

def audit_blueprint():
    # Charger blueprint
    with open('docs/architecture/blueprint-v2-ACTUAL-2026.yaml') as f:
        blueprint = yaml.safe_load(f)
    
    # Charger VERSION
    with open('VERSION') as f:
        version_lines = f.readlines()
    
    issues = []
    
    # Vérifier versions
    blueprint_versions = blueprint['versioning']['current_versions']
    for line in version_lines:
        if '=' in line:
            key, value = line.strip().split('=')
            bp_key = key.lower().replace('_version', '')
            if bp_key in blueprint_versions:
                if blueprint_versions[bp_key] != value:
                    issues.append(f"Version mismatch: {key} = {value} (VERSION) vs {blueprint_versions[bp_key]} (blueprint)")
    
    # Vérifier handlers Lambdas
    handlers_in_code = []
    for handler_file in Path('src_v2/lambdas').rglob('handler.py'):
        handlers_in_code.append(handler_file.parent.name)
    
    lambdas_in_blueprint = [l['id'].replace('_v2', '') for l in blueprint['architecture']['lambdas']]
    
    for handler in handlers_in_code:
        if handler not in lambdas_in_blueprint:
            issues.append(f"Lambda handler exists in code but not in blueprint: {handler}")
    
    # Afficher résultats
    if issues:
        print("⚠️ DIVERGENCES DÉTECTÉES :")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ Blueprint à jour")
        return True

if __name__ == '__main__':
    audit_blueprint()
```

---

## 📝 Template de Commit pour Mise à Jour Blueprint

```
docs: update blueprint for [changement]

Blueprint updates:
- Section [architecture/bedrock/etc.]: [description]
- Updated last_updated date
- Added changelog entry

Reflects changes from: [commit SHA ou PR #]
```

---

## 🎯 Résumé : Comment Éviter l'Obsolescence

1. **Mise à jour PENDANT le développement** (pas après)
2. **Commit ENSEMBLE** (code + blueprint)
3. **Q Developer propose automatiquement** la mise à jour
4. **Audit mensuel** avec script automatique
5. **Checklist avant merge** obligatoire

**Principe clé** : Le blueprint fait partie du code, pas de la documentation "à côté".

---

**Date de création** : 2026-01-31  
**Prochaine révision** : Après première release majeure
