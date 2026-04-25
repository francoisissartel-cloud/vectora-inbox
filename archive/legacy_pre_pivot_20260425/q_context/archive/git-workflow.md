# Git Workflow Vectora Inbox

**Date**: 2026-02-02  
**Version**: 2.0  
**Statut**: RÈGLE OBLIGATOIRE

---

## 🚨 PRINCIPE FONDAMENTAL

**Git AVANT Build, pas après déploiement**

```
Git Branch → Commit → Build → Deploy Dev → Test → PR → Merge → Tag → Promote Stage
```

**❌ INTERDIT**: Build → Deploy → Commit

---

## 🌳 Stratégie de Branches

**main**: Production-ready, protected, require PR  
**develop**: Intégration, base pour features  
**feature/[nom]**: Nouvelles fonctionnalités  
**bugfix/[nom]**: Corrections bugs  
**hotfix/[nom]**: Corrections urgentes  
**config/[nom]**: Modifications canonical

---

## 🔄 Workflows Standard

### Workflow 1: Nouvelle Fonctionnalité

```bash
# 1. Créer branche
git checkout develop
git pull origin develop
git checkout -b feature/extraction-dates

# 2. Développer
# - Modifier code src_v2/
# - Incrémenter VERSION (MINOR: 1.2.3 → 1.3.0)
# - Ajouter tests

# 3. Commit
git add src_v2/ VERSION tests/
git commit -m "feat(vectora-core): add relative dates extraction

- Add extract_relative_dates() in shared/utils.py
- Integrate in ingest workflow
- Add unit tests
- Increment VECTORA_CORE_VERSION to 1.3.0

Refs: #123"

# 4. Build et test
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v7

# 5. Push et PR
git push origin feature/extraction-dates
# Créer PR sur GitHub: feature/extraction-dates → develop

# 6. Après merge
git checkout develop
git pull origin develop
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 7. Tag et promote
git tag v1.3.0 -m "Release 1.3.0: Add relative dates extraction"
git push origin develop --tags
python scripts/deploy/promote.py --to stage --version 1.3.0 --git-sha $(git rev-parse HEAD)

# 8. Test stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage
```

---

### Workflow 2: Hotfix Production (URGENT)

```bash
# 1. Créer branche depuis main
git checkout main
git pull origin main
git checkout -b hotfix/bedrock-timeout

# 2. Fix rapide
# - Corriger bug
# - Incrémenter VERSION (PATCH: 1.3.1 → 1.3.2)

# 3. Commit
git add src_v2/ VERSION
git commit -m "fix(bedrock): increase timeout to 60s

Critical fix for production timeouts.

Fixes: #125"

# 4. Build et test dev
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# 5. Merge main
git checkout main
git merge hotfix/bedrock-timeout
git tag v1.3.2 -m "Hotfix: Increase Bedrock timeout"
git push origin main --tags

# 6. Deploy stage
python scripts/deploy/promote.py --to stage --version 1.3.2 --git-sha $(git rev-parse main)

# 7. Backport develop
git checkout develop
git merge main
git push origin develop
```

---

### Workflow 3: Modification Canonical

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

- Add entity_1, entity_2, entity_3
- Increment CANONICAL_VERSION to 1.2

Refs: #126"

# 4. Push et PR
git push origin config/add-tech-entities
# Créer PR → develop

# 5. Après merge, sync S3
git checkout develop
git pull origin develop

aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3

# Test dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# 6. Tag et sync stage
git tag canonical-v1.2 -m "Canonical 1.2: Add tech entities"
git push origin develop --tags

aws s3 sync canonical/ s3://vectora-inbox-config-stage/canonical/ \
  --profile rag-lai-prod --region eu-west-3
```

---

## 📝 Convention Commits (OBLIGATOIRE)

### Format

```
<type>(<scope>): <subject>

[body]

[footer]
```

### Types

| Type | Usage | VERSION |
|------|-------|---------|
| **feat** | Nouvelle fonctionnalité | MINOR (1.2.3 → 1.3.0) |
| **fix** | Correction bug | PATCH (1.2.3 → 1.2.4) |
| **docs** | Documentation | Aucune |
| **refactor** | Refactoring | Aucune ou PATCH |
| **test** | Tests | Aucune |
| **chore** | Maintenance | Aucune ou PATCH |
| **perf** | Performance | MINOR ou PATCH |
| **BREAKING CHANGE** | Breaking change | MAJOR (1.2.3 → 2.0.0) |

### Scopes

- **vectora-core**: `src_v2/vectora_core/`
- **ingest**: Lambda ingest-v2
- **normalize**: Lambda normalize-score-v2
- **newsletter**: Lambda newsletter-v2
- **canonical**: Fichiers canonical/
- **infra**: CloudFormation
- **scripts**: Scripts build/deploy
- **bedrock**: Intégrations Bedrock

### Exemples

```bash
# Feature
feat(vectora-core): add relative dates extraction

- Add extract_relative_dates() in shared/utils.py
- Add unit tests
- Increment VECTORA_CORE_VERSION to 1.3.0

Refs: #123

# Bugfix
fix(bedrock): handle special characters in matching

Escape special chars before Bedrock API call.

Fixes: #124

# Breaking change
feat(vectora-core): rename normalize_item to process_item

BREAKING CHANGE: Function normalize_item() renamed to process_item().
Update all calls in Lambda handlers.

Increment VECTORA_CORE_VERSION to 2.0.0
```

---

## 🏷️ Gestion des Tags

### Convention

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

### Création

```bash
# Tag annoté (OBLIGATOIRE)
git tag -a v1.3.0 -m "Release 1.3.0: Add relative dates extraction"

# Push tags
git push origin develop --tags

# ❌ INTERDIT: Tag lightweight
git tag v1.3.0  # Sans -a
```

### Synchronisation VERSION ↔ Tag

**RÈGLE CRITIQUE**: Tag Git DOIT correspondre à VERSION

```bash
# ✅ CORRECT
VERSION: VECTORA_CORE_VERSION=1.3.0
Git tag: v1.3.0

# ❌ INCORRECT
VERSION: VECTORA_CORE_VERSION=1.3.0
Git tag: v1.2.9  # Pas synchronisé!
```

---

## 🔒 Protection des Branches

### Configuration GitHub

**Branch: main**
- ✅ Require PR reviews (1 minimum)
- ✅ Require status checks
- ✅ Include administrators
- ❌ Allow force pushes
- ❌ Allow deletions

**Branch: develop**
- ✅ Require PR reviews (1 minimum)
- ❌ Allow force pushes (sauf admin urgence)
- ❌ Allow deletions

---

## 📋 Checklist Avant Commit

**Q Developer DOIT vérifier**:

- [ ] Code dans `src_v2/` (pas `archive/_src/`)
- [ ] VERSION incrémentée si nécessaire
- [ ] Tests ajoutés/mis à jour
- [ ] Pas de fichiers temporaires (`.tmp/`, `.build/`)
- [ ] Pas de secrets/credentials
- [ ] Message commit suit convention
- [ ] Branche feature/bugfix (pas main/develop)

---

## 📋 Template Pull Request

```markdown
## Description
[Description claire]

## Type
- [ ] Feature
- [ ] Bugfix
- [ ] Hotfix
- [ ] Documentation
- [ ] Configuration

## Checklist
- [ ] VERSION incrémentée
- [ ] Tests ajoutés/mis à jour
- [ ] Tests E2E passés en dev
- [ ] Documentation mise à jour
- [ ] Commit messages suivent convention

## Tests
- [ ] Build: `python scripts/build/build_all.py`
- [ ] Deploy dev: `python scripts/deploy/deploy_env.py --env dev`
- [ ] Tests E2E: `python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7`

## Environnements
- [ ] dev
- [ ] stage
- [ ] prod

## Références
Refs: #[issue]
Fixes: #[issue]
```

---

## 🚫 Anti-Patterns

### ❌ Commit Après Déploiement

```bash
# ❌ MAUVAIS
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
git commit -m "add feature"  # Trop tard!

# ✅ BON
git commit -m "feat: add feature"
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

### ❌ Travailler sur develop/main

```bash
# ❌ MAUVAIS
git checkout develop
# Modifier code...
git commit -m "add feature"

# ✅ BON
git checkout develop
git checkout -b feature/my-feature
# Modifier code...
git commit -m "feat: add feature"
```

### ❌ Oublier VERSION

```bash
# ❌ MAUVAIS
# Modifier code
git commit -m "feat: add feature"
# VERSION pas modifiée!

# ✅ BON
# Modifier code
# Éditer VERSION: 1.2.3 → 1.3.0
git add src_v2/ VERSION
git commit -m "feat: add feature"
```

---

## 🎯 Règles Q Developer

### Avant Modification

**Q DOIT**:
1. Vérifier branche: `git branch --show-current`
2. Si main/develop, créer branche feature/bugfix
3. Vérifier état: `git status`

### Pendant Développement

**Q DOIT**:
1. Modifier code `src_v2/` uniquement
2. Incrémenter VERSION si nécessaire
3. Ajouter tests
4. Commit AVANT build

### Après Développement

**Q DOIT**:
1. Build et deploy dev
2. Tester en dev
3. Push branche
4. Proposer création PR

### Format Réponse Q

```markdown
## ✅ Modifications Terminées

**Branche**: feature/extraction-dates
**Commits**: 3 commits
- feat(vectora-core): add extract_relative_dates()
- test(vectora-core): add unit tests
- docs(readme): update usage

**VERSION**: 1.2.3 → 1.3.0 (MINOR)

**Prochaines étapes**:
1. Build: `python scripts/build/build_all.py`
2. Deploy dev: `python scripts/deploy/deploy_env.py --env dev`
3. Test: `python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v7`
4. Push: `git push origin feature/extraction-dates`
5. Créer PR: feature/extraction-dates → develop

**Souhaitez-vous que je procède au build et deploy dev ?**
```

---

## 🔄 Rollback

### Rollback Code

```bash
# Identifier version
git tag -l
git show v1.2.3

# Rollback
python scripts/deploy/rollback.py --env stage --to-version 1.2.3 --git-tag v1.2.3

# Vérifier
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage
```

### Rollback Commit

```bash
# Annuler dernier commit (pas pushé)
git reset --soft HEAD~1  # Garde modifications
git reset --hard HEAD~1  # Supprime modifications

# Annuler commit pushé
git revert <commit-sha>
git push origin feature/my-feature
```

---

## 📞 Support

### Commandes Utiles

```bash
# État
git status
git branch --show-current

# Historique
git log --oneline --graph --all

# Tags
git tag -l
git show v1.3.0

# Différences
git diff
git diff --staged

# Annulations
git restore <file>
git restore --staged <file>
git reset --soft HEAD~1
```

### Résolution Conflits

```bash
# Voir conflits
git status

# Résoudre et continuer
git add <fichiers-résolus>
git commit  # Si merge
git rebase --continue  # Si rebase

# Abandonner
git merge --abort
git rebase --abort
```

---

**Git Workflow - Version 2.0**  
**Date**: 2026-02-02  
**Statut**: RÈGLE OBLIGATOIRE
