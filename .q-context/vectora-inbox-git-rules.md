# Règles Git - Vectora Inbox

**Date**: 2026-01-31  
**Version**: 1.0  
**Statut**: RÈGLE CRITIQUE POUR Q DEVELOPER

---

## 🚨 RÈGLE CRITIQUE POUR Q DEVELOPER

**Q Developer DOIT TOUJOURS intégrer Git AVANT le build, pas après le déploiement.**

**Workflow obligatoire**:
```
Git Commit → Build → Deploy → Test → PR → Merge → Tag → Promote
```

**❌ INTERDIT**:
```
Build → Deploy → Test → Git Commit  # Trop tard!
```

---

## 📝 Convention Commits (OBLIGATOIRE)

### Format Standard

```
<type>(<scope>): <subject>

[body optionnel]

[footer optionnel]
```

### Types Autorisés

| Type | Usage | Incrémentation VERSION |
|------|-------|------------------------|
| **feat** | Nouvelle fonctionnalité | MINOR (1.2.3 → 1.3.0) |
| **fix** | Correction bug | PATCH (1.2.3 → 1.2.4) |
| **docs** | Documentation uniquement | Aucune |
| **refactor** | Refactoring sans changement fonctionnel | Aucune ou PATCH |
| **test** | Ajout/modification tests | Aucune |
| **chore** | Maintenance (build, deps) | Aucune ou PATCH |
| **perf** | Amélioration performance | MINOR ou PATCH |
| **BREAKING CHANGE** | Breaking change | MAJOR (1.2.3 → 2.0.0) |

### Scopes Standards

- **vectora-core**: `src_v2/vectora_core/`
- **ingest**: Lambda ingest-v2
- **normalize**: Lambda normalize-score-v2
- **newsletter**: Lambda newsletter-v2
- **canonical**: Fichiers canonical/
- **infra**: CloudFormation
- **scripts**: Scripts build/deploy
- **bedrock**: Intégrations Bedrock

### Exemples Valides

```bash
# Feature avec body
feat(vectora-core): add relative dates extraction

- Add extract_relative_dates() in shared/utils.py
- Integrate in ingest workflow
- Add unit tests test_extract_relative_dates.py
- Increment VECTORA_CORE_VERSION to 1.3.0

Refs: #123

# Bugfix simple
fix(bedrock): increase timeout to 60s

# Documentation
docs(readme): update Git workflow section

# Breaking change
feat(vectora-core): rename normalize_item to process_item

BREAKING CHANGE: Function normalize_item() renamed to process_item().
Update all calls in Lambda handlers.

Increment VECTORA_CORE_VERSION to 2.0.0
```

---

## 🌳 Stratégie de Branches

### Branches Permanentes

**main**
- Code production-ready
- Protected (require PR + review)
- Source des releases production
- Jamais de commit direct

**develop**
- Branche d'intégration
- Code validé en dev
- Base pour features/bugfix
- Protected (require PR)

### Branches Temporaires

**feature/[nom]**: Nouvelles fonctionnalités
```bash
feature/extraction-dates
feature/bedrock-caching
```

**bugfix/[nom]**: Corrections bugs
```bash
bugfix/matching-special-chars
bugfix/s3-timeout
```

**hotfix/[nom]**: Corrections urgentes production
```bash
hotfix/bedrock-timeout
hotfix/memory-leak
```

**config/[nom]**: Modifications canonical
```bash
config/add-tech-entities
config/update-prompts
```

### Règles de Nommage

- ✅ Minuscules uniquement
- ✅ Tirets pour séparer mots
- ✅ Descriptif et court
- ❌ Pas d'espaces
- ❌ Pas de caractères spéciaux

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

### Création Tags (Obligatoire)

```bash
# Tag annoté (OBLIGATOIRE)
git tag -a v1.3.0 -m "Release 1.3.0: Add relative dates extraction"

# Push tags
git push origin develop --tags

# ❌ INTERDIT: Tag lightweight
git tag v1.3.0  # Pas de -a, pas de message
```

### Synchronisation VERSION ↔ Tag

**RÈGLE CRITIQUE**: Le tag Git DOIT correspondre à la version dans VERSION.

```bash
# ✅ CORRECT
VERSION contient: VECTORA_CORE_VERSION=1.3.0
Git tag: v1.3.0

# ❌ INCORRECT
VERSION contient: VECTORA_CORE_VERSION=1.3.0
Git tag: v1.2.9  # Pas synchronisé!
```

**Validation automatique** (dans scripts/build/build_all.py):
```python
# Vérifier cohérence VERSION ↔ Git tag
version_file = read_version()
git_tag = get_latest_git_tag()

if f"v{version_file}" != git_tag:
    raise ValueError(f"VERSION ({version_file}) doesn't match Git tag ({git_tag})")
```

---

## 🔒 Protection des Branches

### Configuration GitHub Requise

**Branch: main**
```yaml
protection_rules:
  require_pull_request_reviews:
    required_approving_review_count: 1
  require_status_checks:
    strict: true
    contexts:
      - "tests-unit"
      - "tests-e2e"
  enforce_admins: true
  allow_force_pushes: false
  allow_deletions: false
```

**Branch: develop**
```yaml
protection_rules:
  require_pull_request_reviews:
    required_approving_review_count: 1
  allow_force_pushes: false  # Sauf admin en cas d'urgence
  allow_deletions: false
```

---

## 📋 Checklist Avant Commit

**Q Developer DOIT vérifier**:

- [ ] Code modifié dans `src_v2/` (pas `archive/_src/`)
- [ ] VERSION incrémentée si nécessaire
- [ ] Tests unitaires ajoutés/mis à jour
- [ ] Pas de fichiers temporaires (`.tmp/`, `.build/` dans .gitignore)
- [ ] Pas de secrets/credentials dans le code
- [ ] Message commit suit convention
- [ ] Branche feature/bugfix créée (pas de commit direct sur develop)

---

## 📋 Checklist Pull Request

**Template PR** (`.github/PULL_REQUEST_TEMPLATE.md`):

```markdown
## 🎯 Description
[Description claire des changements]

## 📦 Type de changement
- [ ] Feature (nouvelle fonctionnalité)
- [ ] Bugfix (correction bug)
- [ ] Hotfix (correction urgente)
- [ ] Documentation
- [ ] Refactoring
- [ ] Configuration (canonical)

## ✅ Checklist Développement
- [ ] VERSION incrémentée correctement
- [ ] Tests unitaires ajoutés/mis à jour
- [ ] Tests E2E passés en dev
- [ ] Documentation mise à jour si nécessaire
- [ ] Pas de fichiers temporaires committés
- [ ] Commit messages suivent convention
- [ ] Code review demandé

## 🧪 Tests Effectués
- [ ] Build réussi: `python scripts/build/build_all.py`
- [ ] Deploy dev: `python scripts/deploy/deploy_env.py --env dev`
- [ ] Tests E2E: `python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7`
- [ ] Résultats: [Décrire résultats]

## 🌍 Environnements Impactés
- [ ] dev
- [ ] stage
- [ ] prod

## 🔗 Références
Refs: #[numéro issue]
Fixes: #[numéro issue si bugfix]

## 📸 Screenshots/Logs (si applicable)
[Ajouter captures ou logs pertinents]
```

---

## 🚫 Interdictions Absolues

### ❌ Commit Direct sur main/develop

```bash
# ❌ INTERDIT
git checkout develop
# Modifier code...
git commit -m "add feature"
git push origin develop
```

```bash
# ✅ OBLIGATOIRE
git checkout develop
git checkout -b feature/my-feature
# Modifier code...
git commit -m "feat: add feature"
git push origin feature/my-feature
# Créer PR
```

### ❌ Build/Deploy AVANT Commit

```bash
# ❌ INTERDIT
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
git commit -m "add feature"  # Trop tard!
```

```bash
# ✅ OBLIGATOIRE
git commit -m "feat: add feature"
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

### ❌ Tag Sans Annotation

```bash
# ❌ INTERDIT
git tag v1.3.0  # Tag lightweight

# ✅ OBLIGATOIRE
git tag -a v1.3.0 -m "Release 1.3.0: Description"
```

### ❌ Force Push sur main/develop

```bash
# ❌ INTERDIT
git push --force origin main
git push --force origin develop

# ✅ AUTORISÉ (avec précaution)
git push --force origin feature/my-feature  # Branche temporaire uniquement
```

### ❌ Commit Fichiers Temporaires

```bash
# ❌ INTERDIT
git add .tmp/
git add .build/
git add event_test.json
git add response_20260131.json

# ✅ OBLIGATOIRE
# Vérifier .gitignore contient:
.tmp/
.build/
event_*.json
response_*.json
```

---

## 🎯 Règles pour Q Developer

### Avant Toute Modification

**Q DOIT**:
1. Vérifier branche actuelle: `git branch --show-current`
2. Si sur main/develop, créer branche feature/bugfix
3. Vérifier état propre: `git status`

### Pendant Développement

**Q DOIT**:
1. Modifier code dans `src_v2/` uniquement
2. Incrémenter VERSION si nécessaire
3. Ajouter tests
4. Commit AVANT build

### Après Développement

**Q DOIT**:
1. Build et deploy dev
2. Tester en dev
3. Push branche
4. Proposer création PR
5. Attendre validation utilisateur

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
5. Créer PR sur GitHub: feature/extraction-dates → develop

**Souhaitez-vous que je procède au build et deploy dev ?**
```

---

## 🔄 Workflow Rollback

### Rollback Code

```bash
# 1. Identifier version cible
git tag -l
git show v1.2.3

# 2. Rollback avec script
python scripts/deploy/rollback.py --env stage --to-version 1.2.3 --git-tag v1.2.3

# 3. Vérifier déploiement
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage
```

### Rollback Commit (Local)

```bash
# Annuler dernier commit (pas encore pushé)
git reset --soft HEAD~1  # Garde modifications
git reset --hard HEAD~1  # Supprime modifications

# Annuler commit pushé (créer commit inverse)
git revert <commit-sha>
git push origin feature/my-feature
```

---

## 📊 Métriques Git

### Vérifications Automatiques

**Avant chaque build** (dans `scripts/build/build_all.py`):
```python
# 1. Vérifier pas de modifications non committées
if has_uncommitted_changes():
    raise ValueError("Uncommitted changes detected. Commit first.")

# 2. Vérifier VERSION synchronisée avec Git tag
if not version_matches_tag():
    raise ValueError("VERSION doesn't match latest Git tag")

# 3. Vérifier branche actuelle
current_branch = get_current_branch()
if current_branch in ['main', 'develop']:
    print(f"⚠️ Warning: Building from {current_branch}")
```

### Audit Git

```bash
# Historique VERSION
git log --oneline VERSION

# Commits depuis dernier tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# Différences entre tags
git diff v1.2.3..v1.3.0

# Fichiers modifiés entre versions
git diff --name-only v1.2.3..v1.3.0
```

---

## 📞 Support Git

### Commandes Utiles

```bash
# État actuel
git status
git branch --show-current

# Historique
git log --oneline --graph --all
git log --follow VERSION

# Tags
git tag -l
git show v1.3.0

# Différences
git diff
git diff --staged
git diff develop..feature/my-feature

# Annulations
git restore <file>  # Annuler modifications
git restore --staged <file>  # Unstage
git reset --soft HEAD~1  # Annuler commit
```

### Résolution Conflits

```bash
# En cas de conflit lors merge/rebase
git status  # Voir fichiers en conflit

# Éditer fichiers, résoudre conflits
# Chercher: <<<<<<< HEAD

git add <fichiers-résolus>
git commit  # Si merge
git rebase --continue  # Si rebase

# Abandonner merge/rebase
git merge --abort
git rebase --abort
```

---

## ✅ Checklist Finale Q Developer

**Avant chaque proposition de code, Q DOIT vérifier**:

- [ ] Branche feature/bugfix créée (pas main/develop)
- [ ] Commits suivent convention
- [ ] VERSION incrémentée si nécessaire
- [ ] Commits AVANT build
- [ ] Pas de fichiers temporaires
- [ ] Tests ajoutés/mis à jour
- [ ] Documentation mise à jour
- [ ] PR template rempli

---

**Règles Git - Version 1.0**  
**Date**: 2026-01-31  
**Statut**: RÈGLE CRITIQUE - Application Obligatoire
