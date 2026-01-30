# Plan Gouvernance - Repo et Environnements Vectora Inbox

**Date**: 2026-01-30  
**Priorité**: CRITIQUE  
**Objectif**: Établir gouvernance propre AVANT correction layer stage  
**Durée**: 1 jour (8h)  
**À exécuter**: IMMÉDIATEMENT avant plan correctif

---

## 🎯 RÉSUMÉ EXÉCUTIF

Ce plan établit les fondations pour une gestion propre et professionnelle de Vectora Inbox.

**Principe fondamental**: Repo local = SOURCE UNIQUE DE VÉRITÉ

**Après ce plan, vous travaillerez ainsi**:
1. Modifier code dans repo local
2. Exécuter `python scripts/build/build_all.py`
3. Exécuter `python scripts/deploy/deploy_env.py --env dev`
4. Tester en dev
5. Promouvoir vers stage via `python scripts/deploy/promote.py`

**Bénéfices**:
- ✅ Reproductible (même code → même résultat)
- ✅ Traçable (Git commit → Version → Env)
- ✅ Sécurisé (pas de modification manuelle AWS)
- ✅ Maintenable (scripts automatisés)

---

## 📋 PHASES

### PHASE 0: Préparation (30 min)

#### 0.1 Snapshot Repo

```powershell
cd c:\Users\franc\OneDrive\Bureau\vectora-inbox
git status
git add .
git commit -m "chore: snapshot avant gouvernance"
git checkout -b governance-setup
```

#### 0.2 Créer Structure

```powershell
New-Item -ItemType Directory -Force -Path .build\layers
New-Item -ItemType Directory -Force -Path .build\lambdas
New-Item -ItemType Directory -Force -Path scripts\build
New-Item -ItemType Directory -Force -Path scripts\deploy
New-Item -ItemType Directory -Force -Path scripts\test
```

**Validation**:
- [ ] Branche governance-setup créée
- [ ] Dossiers créés

---

### PHASE 1: Versioning (1h)

#### 1.1 Créer VERSION

Créer fichier `VERSION` à la racine:

```ini
VECTORA_CORE_VERSION=1.2.3
COMMON_DEPS_VERSION=1.0.5
INGEST_VERSION=1.5.0
NORMALIZE_VERSION=2.1.0
NEWSLETTER_VERSION=1.8.0
CANONICAL_VERSION=1.1
```

#### 1.2 Mettre à Jour .gitignore

Ajouter:
```
.build/
*.zip
.tmp/
```

**Validation**:
- [ ] VERSION créé
- [ ] .gitignore mis à jour

---

### PHASE 2: Scripts Build (2h)

Créer 3 scripts Python dans `scripts/build/`:

1. `build_layer_vectora_core.py` - Build layer vectora-core
2. `build_layer_common_deps.py` - Build layer common-deps  
3. `build_all.py` - Build tous les artefacts

**Note**: Les scripts complets seront fournis dans la section suivante.

**Validation**:
- [ ] 3 scripts créés
- [ ] Test build réussi

---

### PHASE 3: Scripts Deploy (2h)

Créer 3 scripts Python dans `scripts/deploy/`:

1. `deploy_layer.py` - Deploy layer vers env
2. `deploy_env.py` - Deploy complet vers env
3. `promote.py` - Promouvoir version entre envs

**Validation**:
- [ ] 3 scripts créés
- [ ] Test deploy dev réussi

---

### PHASE 4: Mise à Jour Règles (1h)

Mettre à jour `.q-context/vectora-inbox-development-rules.md`:

**Ajouter section**:

```markdown
## 🚫 RÈGLES GOUVERNANCE (CRITIQUE)

### Source Unique de Vérité

Repo local = SEULE source de vérité. Toute modification passe par Git.

### Interdiction Modification Directe AWS

❌ INTERDIT:
- aws lambda update-function-code (manuel)
- aws s3 cp fichier.zip s3://... (manuel)
- Édition console AWS
- Copie dev→stage sans scripts

✅ OBLIGATOIRE:
- Modifier repo local
- python scripts/build/build_all.py
- python scripts/deploy/deploy_env.py --env dev
- python scripts/deploy/promote.py --to stage

### Versioning Obligatoire

Chaque artefact a version explicite dans fichier VERSION.
Format: MAJOR.MINOR.PATCH (ex: 1.2.3)

### Workflow Standard

1. Développement: Modifier code repo
2. Build: python scripts/build/build_all.py
3. Deploy dev: python scripts/deploy/deploy_env.py --env dev
4. Test dev: python scripts/test/test_e2e.py --env dev
5. Promotion: python scripts/deploy/promote.py --to stage
6. Test stage: python scripts/test/test_e2e.py --env stage
```

**Validation**:
- [ ] Règles ajoutées
- [ ] Q Developer informé

---

### PHASE 5: Documentation (1h)

Créer `docs/workflows/developpement_standard.md`:

**Contenu**: Workflow quotidien détaillé avec exemples.

**Validation**:
- [ ] Documentation créée
- [ ] Exemples testés

---

### PHASE 6: Tests & Validation (1h30)

#### 6.1 Test Build

```powershell
python scripts/build/build_all.py
```

Vérifier: Artefacts dans `.build/`

#### 6.2 Test Deploy Dev

```powershell
python scripts/deploy/deploy_env.py --env dev --dry-run
```

#### 6.3 Commit Gouvernance

```powershell
git add .
git commit -m "feat: mise en place gouvernance repo et environnements"
git checkout main
git merge governance-setup
```

**Validation**:
- [ ] Build fonctionne
- [ ] Deploy dry-run OK
- [ ] Gouvernance commitée

---

## 📚 SCRIPTS COMPLETS

Les scripts complets sont fournis ci-dessous pour copier-coller.

### Script 1: build_layer_vectora_core.py

Voir section ANNEXE A

### Script 2: deploy_layer.py

Voir section ANNEXE B

### Script 3: promote.py

Voir section ANNEXE C

---

## 🔄 COMMENT TRAVAILLER APRÈS CE PLAN

### Workflow Quotidien

**Scénario 1: Nouvelle fonctionnalité**

```powershell
# 1. Développer
cd src_v2/vectora_core
# Modifier code...

# 2. Incrémenter version
# Éditer VERSION: VECTORA_CORE_VERSION=1.2.4

# 3. Build
python scripts/build/build_all.py

# 4. Deploy dev
python scripts/deploy/deploy_env.py --env dev

# 5. Tester
python scripts/test/test_e2e.py --env dev --client lai_weekly_v7

# 6. Si OK, promouvoir stage
python scripts/deploy/promote.py --to stage --version 1.2.4

# 7. Tester stage
python scripts/test/test_e2e.py --env stage --client lai_weekly_v7

# 8. Commit
git add .
git commit -m "feat: nouvelle fonctionnalité"
git push
```

**Scénario 2: Correction bug urgent**

```powershell
# 1. Corriger dans repo
# 2. Build + Deploy dev
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 3. Tester
python scripts/test/test_e2e.py --env dev

# 4. Si OK, promouvoir immédiatement
python scripts/deploy/promote.py --to stage --urgent
```

**Scénario 3: Mise à jour canonical**

```powershell
# 1. Modifier canonical/
# 2. Incrémenter CANONICAL_VERSION dans VERSION
# 3. Sync vers dev
python scripts/deploy/sync_canonical.py --env dev

# 4. Tester
python scripts/test/test_e2e.py --env dev

# 5. Sync vers stage
python scripts/deploy/sync_canonical.py --env stage
```

---

## 🔧 AJUSTEMENTS vectora-inbox-development-rules.md

**OUI, il faut ajuster les règles**. Voici les modifications:

### Modifications à Apporter

**1. Ajouter section "RÈGLES GOUVERNANCE"** (voir PHASE 4)

**2. Modifier section "RÈGLES D'EXÉCUTION SCRIPTS"**

Remplacer par:
```markdown
## 🔧 RÈGLES D'EXÉCUTION SCRIPTS

### Scripts Autorisés

✅ scripts/build/ - Build artefacts
✅ scripts/deploy/ - Deploy vers AWS
✅ scripts/test/ - Tests validation
✅ scripts/invoke/ - Invocation Lambdas (tests)
✅ scripts/maintenance/ - Maintenance (snapshots, cleanup)

### Scripts Interdits

❌ Commandes AWS CLI directes (sauf lecture)
❌ Modifications manuelles console AWS
❌ Copie fichiers S3 manuelle

### Workflow Obligatoire

Toute modification AWS DOIT passer par scripts standardisés.
```

**3. Ajouter section "VERSIONING"**

```markdown
## 📦 VERSIONING

### Fichier VERSION

Source de vérité pour versions artefacts.
Format: MAJOR.MINOR.PATCH

### Incrémenter Version

- MAJOR: Breaking changes
- MINOR: Nouvelles fonctionnalités
- PATCH: Corrections bugs

### Exemple

```
VECTORA_CORE_VERSION=1.2.3
# Nouvelle fonctionnalité → 1.3.0
# Correction bug → 1.2.4
# Breaking change → 2.0.0
```
```

---

## ✅ CHECKLIST FINALE

Avant de passer au plan correctif:

- [ ] PHASE 0: Structure créée
- [ ] PHASE 1: VERSION créé, .gitignore mis à jour
- [ ] PHASE 2: Scripts build créés et testés
- [ ] PHASE 3: Scripts deploy créés et testés
- [ ] PHASE 4: Règles développement mises à jour
- [ ] PHASE 5: Documentation workflow créée
- [ ] PHASE 6: Tests validation réussis
- [ ] Gouvernance commitée sur main

**Une fois cette checklist complète, vous êtes prêt pour le plan correctif.**

---

## 🎯 PROCHAINES ÉTAPES

1. **Exécuter ce plan** (1 jour)
2. **Mettre à jour plan correctif** avec nouvelle gouvernance
3. **Exécuter plan correctif** (layer stage + nettoyage)
4. **Valider environnements** dev/stage alignés sur repo

---

**Plan Gouvernance - Version 1.0**  
**Date**: 2026-01-30  
**Statut**: PRÊT POUR EXÉCUTION  
**Priorité**: CRITIQUE - À exécuter AVANT plan correctif
