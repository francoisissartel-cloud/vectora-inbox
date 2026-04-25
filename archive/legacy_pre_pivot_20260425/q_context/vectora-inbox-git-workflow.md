# Workflow Git - Vectora Inbox

**Date**: 2026-01-31  
**Version**: 1.0  
**Statut**: RÈGLE OBLIGATOIRE

---

## 🎯 Principe Fondamental

**Git est intégré AVANT le build, pas après le déploiement.**

```
Git Branch → Commit → Build → Deploy Dev → Test → PR → Merge → Tag → Promote Stage
```

---

## 🌳 Stratégie de Branches

### Branches Principales

**main**: Code production-ready
- Toujours déployable
- Protected (require PR + review)
- Source des tags de release

**develop**: Branche d'intégration
- Code validé en dev
- Base pour features
- Merge vers main pour releases

### Branches de Travail

**feature/[nom]**: Nouvelles fonctionnalités
```bash
feature/extraction-dates
feature/bedrock-caching
feature/newsletter-templates
```

**bugfix/[nom]**: Corrections bugs non urgents
```bash
bugfix/matching-special-chars
bugfix/s3-timeout
```

**hotfix/[nom]**: Corrections urgentes production
```bash
hotfix/bedrock-timeout
hotfix/memory-leak
```

---

## 🔄 Workflows Standard

### Workflow 1: Nouvelle Fonctionnalité

```bash
# 1. Créer branche depuis develop
git checkout develop
git pull origin develop
git checkout -b feature/extraction-dates

# 2. Développer
# - Modifier code dans src_v2/
# - Incrémenter VERSION (MINOR: 1.2.3 → 1.3.0)
# - Ajouter tests

# 3. Commit (Conventional Commits)
git add src_v2/ VERSION tests/
git commit -m "feat(vectora-core): add relative dates extraction

- Add extract_relative_dates() in shared/utils.py
- Integrate in ingest workflow
- Add unit tests test_extract_relative_dates.py
- Increment VECTORA_CORE_VERSION to 1.3.0

Refs: #123"

# 4. Build et test local
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v7

# 5. Push branche
git push origin feature/extraction-dates

# 6. Créer Pull Request sur GitHub
# - Base: develop
# - Titre: "feat(vectora-core): add relative dates extraction"
# - Description: Détails + checklist

# 7. Code Review
# - Attendre approbation (1 reviewer minimum)
# - Corriger si nécessaire

# 8. Merge dans develop (via GitHub UI)
# - Squash ou merge commit selon préférence
# - Supprimer branche feature après merge

# 9. Deploy dev depuis develop
git checkout develop
git pull origin develop
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 10. Tests E2E en dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# 11. Tag et promote stage
git tag v1.3.0 -m "Release 1.3.0: Add relative dates extraction"
git push origin develop --tags
python scripts/deploy/promote.py --to stage --version 1.3.0 --git-sha $(git rev-parse HEAD)

# 12. Tests E2E en stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage

# 13. Si OK, merge develop → main (via PR)
# Créer PR: develop → main
# Après merge, tag production si nécessaire
```

**Durée estimée**: 1-2 heures

---

### Workflow 2: Correction Bug Non Urgent

```bash
# 1. Créer branche depuis develop
git checkout develop
git pull origin develop
git checkout -b bugfix/matching-special-chars

# 2. Corriger bug
# - Modifier code
# - Incrémenter VERSION (PATCH: 1.3.0 → 1.3.1)
# - Ajouter test de régression

# 3. Commit
git add src_v2/ VERSION tests/
git commit -m "fix(bedrock): handle special characters in matching

- Escape special chars before Bedrock call
- Add test case for accents and symbols
- Increment VECTORA_CORE_VERSION to 1.3.1

Fixes: #124"

# 4. Build et test
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
# Tests...

# 5. Push et PR vers develop
git push origin bugfix/matching-special-chars
# Créer PR → develop

# 6. Après merge, deploy et promote
git checkout develop
git pull origin develop
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
git tag v1.3.1 -m "Fix: Handle special characters in matching"
git push origin develop --tags
python scripts/deploy/promote.py --to stage --version 1.3.1 --git-sha $(git rev-parse HEAD)
```

**Durée estimée**: 30-60 minutes

---

### Workflow 3: Hotfix Production (URGENT)

```bash
# 1. Créer branche depuis main (pas develop!)
git checkout main
git pull origin main
git checkout -b hotfix/bedrock-timeout

# 2. Fix rapide
# - Corriger bug critique
# - Incrémenter VERSION (PATCH: 1.3.1 → 1.3.2)
# - Tests minimaux

# 3. Commit
git add src_v2/ VERSION
git commit -m "fix(bedrock): increase timeout to 60s

Critical fix for production timeouts.

Fixes: #125"

# 4. Build et test rapide en dev
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
# Test rapide...

# 5. Merge dans main (PR express ou direct si critique)
git checkout main
git merge hotfix/bedrock-timeout
git tag v1.3.2 -m "Hotfix: Increase Bedrock timeout"
git push origin main --tags

# 6. Deploy stage immédiat
python scripts/deploy/promote.py --to stage --version 1.3.2 --git-sha $(git rev-parse main)

# 7. Tests stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage

# 8. Si OK, deploy prod
python scripts/deploy/promote.py --to prod --version 1.3.2 --git-sha $(git rev-parse main)

# 9. Backport vers develop
git checkout develop
git merge main
git push origin develop
```

**Durée estimée**: 15-30 minutes

---

### Workflow 4: Modification Canonical (Config)

```bash
# 1. Créer branche
git checkout develop
git checkout -b config/add-tech-entities

# 2. Modifier canonical
# - Éditer canonical/scopes/tech_lai_ecosystem.yaml
# - Incrémenter CANONICAL_VERSION (1.1 → 1.2)

# 3. Commit
git add canonical/ VERSION
git commit -m "feat(canonical): add 3 new tech entities

- Add entity_1, entity_2, entity_3 to tech_lai_ecosystem
- Increment CANONICAL_VERSION to 1.2

Refs: #126"

# 4. Push et PR
git push origin config/add-tech-entities
# Créer PR → develop

# 5. Après merge, sync S3
git checkout develop
git pull origin develop

# Sync dev
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3

# Test dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# 6. Tag et sync stage
git tag canonical-v1.2 -m "Canonical 1.2: Add tech entities"
git push origin develop --tags

aws s3 sync canonical/ s3://vectora-inbox-config-stage/canonical/ \
  --profile rag-lai-prod --region eu-west-3

# Test stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage
```

**Durée estimée**: 20-30 minutes

---

## 📝 Convention Commits (OBLIGATOIRE)

### Format Standard

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types Autorisés

- **feat**: Nouvelle fonctionnalité
- **fix**: Correction bug
- **docs**: Documentation uniquement
- **refactor**: Refactoring (pas de changement fonctionnel)
- **test**: Ajout/modification tests
- **chore**: Maintenance (build, deps, etc.)
- **perf**: Amélioration performance

### Scopes Recommandés

- **vectora-core**: Modifications dans src_v2/vectora_core/
- **ingest**: Lambda ingest-v2
- **normalize**: Lambda normalize-score-v2
- **newsletter**: Lambda newsletter-v2
- **canonical**: Modifications canonical/
- **infra**: Infrastructure CloudFormation
- **scripts**: Scripts build/deploy
- **bedrock**: Intégrations Bedrock

### Exemples Concrets

```bash
# Feature
git commit -m "feat(vectora-core): add relative dates extraction

- Add extract_relative_dates() in shared/utils.py
- Integrate in ingest workflow
- Add unit tests
- Increment VECTORA_CORE_VERSION to 1.3.0

Refs: #123"

# Bugfix
git commit -m "fix(bedrock): handle special characters in matching

Escape special chars before Bedrock API call to prevent errors.

Fixes: #124"

# Documentation
git commit -m "docs(readme): update deployment instructions

Add section about Git workflow and tagging."

# Refactoring
git commit -m "refactor(ingest): simplify source fetcher logic

Extract common patterns into helper functions.
No functional changes."

# Hotfix
git commit -m "fix(bedrock): increase timeout to 60s

Critical fix for production timeouts.

Fixes: #125"
```

---

## 🏷️ Gestion des Tags

### Convention Nommage

**Releases code**: `v<MAJOR>.<MINOR>.<PATCH>`
```bash
v1.2.3
v1.3.0
v2.0.0
```

**Releases canonical**: `canonical-v<MAJOR>.<MINOR>`
```bash
canonical-v1.1
canonical-v1.2
```

### Création Tags

```bash
# Tag annoté (recommandé)
git tag -a v1.3.0 -m "Release 1.3.0: Add relative dates extraction

Features:
- Relative dates extraction
- Improved Bedrock matching
- New canonical entities

Tested with lai_weekly_v7 in dev and stage."

# Push tags
git push origin develop --tags

# Lister tags
git tag -l

# Voir détails tag
git show v1.3.0
```

### Rollback avec Tags

```bash
# Voir code d'une version spécifique
git checkout v1.2.3

# Rollback vers version précédente
python scripts/deploy/rollback.py --env stage --to-version 1.2.3 --git-tag v1.2.3

# Revenir à develop
git checkout develop
```

---

## 🔒 Protection des Branches

### Configuration GitHub (À appliquer)

**Branch: main**
- ✅ Require pull request reviews (1 minimum)
- ✅ Require status checks to pass (tests CI)
- ✅ Require branches to be up to date
- ✅ Include administrators
- ❌ Allow force pushes
- ❌ Allow deletions

**Branch: develop**
- ✅ Require pull request reviews (1 minimum)
- ⚠️ Allow force pushes (avec précaution, admin uniquement)
- ❌ Allow deletions

**Branch patterns: feature/*, bugfix/*, hotfix/***
- Pas de protection (branches temporaires)
- Supprimer après merge

---

## 📋 Checklist Pull Request

### Template PR (À créer dans `.github/PULL_REQUEST_TEMPLATE.md`)

```markdown
## Description
[Description claire des changements]

## Type de changement
- [ ] Feature (nouvelle fonctionnalité)
- [ ] Bugfix (correction bug)
- [ ] Hotfix (correction urgente)
- [ ] Documentation
- [ ] Refactoring

## Checklist
- [ ] VERSION incrémentée correctement
- [ ] Tests unitaires ajoutés/mis à jour
- [ ] Tests E2E passés en dev
- [ ] Documentation mise à jour
- [ ] Pas de fichiers temporaires (`.tmp/`, `.build/` ignorés)
- [ ] Commit messages suivent convention
- [ ] Code review demandé

## Tests
- [ ] Build réussi: `python scripts/build/build_all.py`
- [ ] Deploy dev réussi: `python scripts/deploy/deploy_env.py --env dev`
- [ ] Tests E2E: `python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7`

## Environnements impactés
- [ ] dev
- [ ] stage
- [ ] prod

## Références
Refs: #[numéro issue]
Fixes: #[numéro issue si bugfix]
```

---

## 🚫 Anti-Patterns à Éviter

### ❌ Commit après déploiement

```bash
# ❌ MAUVAIS
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
git commit -m "add feature"  # Trop tard!
```

```bash
# ✅ BON
git commit -m "feat: add feature"
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

### ❌ Travailler directement sur develop/main

```bash
# ❌ MAUVAIS
git checkout develop
# Modifier code...
git commit -m "add feature"
git push origin develop
```

```bash
# ✅ BON
git checkout develop
git checkout -b feature/my-feature
# Modifier code...
git commit -m "feat: add feature"
git push origin feature/my-feature
# Créer PR
```

### ❌ Oublier d'incrémenter VERSION

```bash
# ❌ MAUVAIS
# Modifier code
git commit -m "feat: add feature"
# VERSION pas modifiée!
```

```bash
# ✅ BON
# Modifier code
# Éditer VERSION: 1.2.3 → 1.3.0
git add src_v2/ VERSION
git commit -m "feat: add feature"
```

### ❌ Tag sans commit

```bash
# ❌ MAUVAIS
git tag v1.3.0
# Pas de commit correspondant!
```

```bash
# ✅ BON
git commit -m "feat: add feature"
git tag v1.3.0 -m "Release 1.3.0"
```

---

## 🎯 Résumé Visuel

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKFLOW COMPLET                          │
└─────────────────────────────────────────────────────────────┘

develop ──┬──> feature/extraction-dates
          │         │
          │         ├─ Commit 1: feat(core): add function
          │         ├─ Commit 2: test: add unit tests
          │         ├─ Commit 3: docs: update readme
          │         │
          │         ├─ Build + Deploy dev + Test
          │         │
          │         └─ PR → develop
          │
          ├──< Merge feature
          │
          ├─ Tag v1.3.0
          │
          ├─ Promote stage
          │
          └─ PR → main (release)

main ─────┬──< Merge develop
          │
          └─ Tag production-v1.3.0 (si applicable)
```

---

## 📞 Support

**En cas de conflit Git**:
```bash
git status
git diff
git merge --abort  # Si merge en cours
git rebase --abort  # Si rebase en cours
```

**Récupérer branche supprimée**:
```bash
git reflog
git checkout -b feature/recovered <commit-sha>
```

**Annuler dernier commit (pas encore pushé)**:
```bash
git reset --soft HEAD~1  # Garde les modifications
git reset --hard HEAD~1  # Supprime les modifications
```

---

**Workflow Git - Version 1.0**  
**Date**: 2026-01-31  
**Statut**: RÈGLE OBLIGATOIRE - À appliquer immédiatement
