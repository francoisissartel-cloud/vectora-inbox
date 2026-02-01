# Guide Configuration GitHub - Vectora Inbox

**Date**: 2026-01-31  
**Durée estimée**: 15-20 minutes  
**Prérequis**: Accès admin au repository GitHub

---

## 🎯 Objectif

Configurer les protections de branches, CODEOWNERS et labels sur GitHub pour sécuriser le workflow.

---

## 📋 Checklist Complète

- [ ] Configurer Branch Protection pour `main`
- [ ] Configurer Branch Protection pour `develop`
- [ ] Mettre à jour CODEOWNERS avec vrais usernames
- [ ] Créer labels standardisés
- [ ] Tester configuration

---

## 1️⃣ Configurer Branch Protection pour `main`

### Étapes

1. **Aller dans Settings**
   - Ouvrir votre repository sur GitHub
   - Cliquer sur **Settings** (en haut à droite)

2. **Accéder aux Branch Protection Rules**
   - Dans le menu gauche, cliquer sur **Branches**
   - Sous "Branch protection rules", cliquer sur **Add rule**

3. **Configurer la règle pour `main`**

   **Branch name pattern**:
   ```
   main
   ```

   **Cocher les options suivantes**:

   ✅ **Require a pull request before merging**
   - ✅ Require approvals: `1`
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require review from Code Owners

   ✅ **Require status checks to pass before merging**
   - ✅ Require branches to be up to date before merging
   - (Ajouter status checks si CI/CD configuré)

   ✅ **Require conversation resolution before merging**

   ✅ **Include administrators**

   ❌ **Allow force pushes** (DÉCOCHÉ)

   ❌ **Allow deletions** (DÉCOCHÉ)

4. **Sauvegarder**
   - Cliquer sur **Create** en bas de page

---

## 2️⃣ Configurer Branch Protection pour `develop`

### Étapes

1. **Ajouter une nouvelle règle**
   - Toujours dans **Settings → Branches**
   - Cliquer sur **Add rule**

2. **Configurer la règle pour `develop`**

   **Branch name pattern**:
   ```
   develop
   ```

   **Cocher les options suivantes**:

   ✅ **Require a pull request before merging**
   - ✅ Require approvals: `1`
   - ✅ Dismiss stale pull request approvals when new commits are pushed

   ✅ **Require conversation resolution before merging**

   ❌ **Allow force pushes** (DÉCOCHÉ - sauf si admin a besoin)

   ❌ **Allow deletions** (DÉCOCHÉ)

3. **Sauvegarder**
   - Cliquer sur **Create**

---

## 3️⃣ Mettre à Jour CODEOWNERS

### Identifier les Usernames GitHub

1. **Lister les collaborateurs**
   - Aller dans **Settings → Collaborators**
   - Noter les usernames GitHub de chaque personne

   Exemple:
   ```
   @francois-dupont
   @marie-martin
   @jean-durand
   ```

2. **Éditer le fichier CODEOWNERS**

   **Fichier**: `.github/CODEOWNERS`

   **Remplacer**:
   ```
   # AVANT
   * @vectora-admin
   /src_v2/ @vectora-admin @vectora-dev
   ```

   **Par** (avec vrais usernames):
   ```
   # APRÈS
   * @francois-dupont

   # Source Code
   /src_v2/ @francois-dupont @marie-martin

   # Infrastructure
   /infra/ @francois-dupont
   /scripts/deploy/ @francois-dupont

   # Configuration
   /canonical/ @francois-dupont @jean-durand
   /client-config-examples/ @francois-dupont @jean-durand

   # Critical Files
   /VERSION @francois-dupont
   /.github/ @francois-dupont
   ```

3. **Commit et Push**
   ```bash
   git add .github/CODEOWNERS
   git commit -m "chore: update CODEOWNERS with real usernames"
   git push origin main
   ```

### Exemple Complet CODEOWNERS

```
# Code Owners - Vectora Inbox

# Default owner (lead dev)
* @francois-dupont

# Q Context and Documentation
/.q-context/ @francois-dupont
/docs/ @francois-dupont @marie-martin

# Source Code (require 2 reviewers)
/src_v2/vectora_core/ @francois-dupont @marie-martin
/src_v2/lambdas/ @francois-dupont @marie-martin

# Infrastructure (admin only)
/infra/ @francois-dupont
/scripts/deploy/ @francois-dupont
/scripts/maintenance/ @francois-dupont

# Configuration (admin + data team)
/canonical/ @francois-dupont @jean-durand
/client-config-examples/ @francois-dupont @jean-durand

# Critical Files (admin only)
/VERSION @francois-dupont
/.github/ @francois-dupont
/.gitignore @francois-dupont

# Tests (dev team)
/tests/ @marie-martin @jean-durand
```

---

## 4️⃣ Créer Labels Standardisés

### Étapes

1. **Accéder aux Labels**
   - Aller dans **Issues** (onglet en haut)
   - Cliquer sur **Labels** (à côté de Milestones)

2. **Créer les Labels**

   Cliquer sur **New label** pour chaque label ci-dessous:

   ### Label 1: feature
   - **Name**: `feature`
   - **Description**: `New feature or enhancement`
   - **Color**: `#0E8A16` (vert)
   - Cliquer **Create label**

   ### Label 2: bugfix
   - **Name**: `bugfix`
   - **Description**: `Bug fix (non-urgent)`
   - **Color**: `#FFA500` (orange)
   - Cliquer **Create label**

   ### Label 3: hotfix
   - **Name**: `hotfix`
   - **Description**: `Critical bug fix (urgent)`
   - **Color**: `#D73A4A` (rouge)
   - Cliquer **Create label**

   ### Label 4: documentation
   - **Name**: `documentation`
   - **Description**: `Documentation only changes`
   - **Color**: `#0075CA` (bleu)
   - Cliquer **Create label**

   ### Label 5: refactoring
   - **Name**: `refactoring`
   - **Description**: `Code refactoring (no functional change)`
   - **Color**: `#FBCA04` (jaune)
   - Cliquer **Create label**

   ### Label 6: configuration
   - **Name**: `configuration`
   - **Description**: `Configuration changes (canonical, client config)`
   - **Color**: `#BFD4F2` (bleu clair)
   - Cliquer **Create label**

   ### Label 7: infrastructure
   - **Name**: `infrastructure`
   - **Description**: `Infrastructure changes (CloudFormation, IAM)`
   - **Color**: `#5319E7` (violet)
   - Cliquer **Create label**

   ### Label 8: needs-review
   - **Name**: `needs-review`
   - **Description**: `Waiting for code review`
   - **Color**: `#FBCA04` (jaune)
   - Cliquer **Create label**

   ### Label 9: approved
   - **Name**: `approved`
   - **Description**: `Approved and ready to merge`
   - **Color**: `#0E8A16` (vert)
   - Cliquer **Create label**

   ### Label 10: blocked
   - **Name**: `blocked`
   - **Description**: `Blocked by dependencies or issues`
   - **Color**: `#D73A4A` (rouge)
   - Cliquer **Create label**

---

## 5️⃣ Tester la Configuration

### Test 1: Branch Protection `main`

1. **Essayer de push direct sur main**
   ```bash
   git checkout main
   echo "test" >> test.txt
   git add test.txt
   git commit -m "test"
   git push origin main
   ```

   **Résultat attendu**: ❌ Rejeté avec message:
   ```
   remote: error: GH006: Protected branch update failed for refs/heads/main.
   ```

   ✅ **Si rejeté, la protection fonctionne!**

2. **Nettoyer**
   ```bash
   git reset --hard HEAD~1
   git checkout develop
   ```

### Test 2: Pull Request avec CODEOWNERS

1. **Créer une branche test**
   ```bash
   git checkout develop
   git checkout -b test/codeowners
   echo "test" >> src_v2/test.txt
   git add src_v2/test.txt
   git commit -m "test: verify CODEOWNERS"
   git push origin test/codeowners
   ```

2. **Créer PR sur GitHub**
   - Aller sur GitHub
   - Cliquer sur **Pull requests** → **New pull request**
   - Base: `develop`, Compare: `test/codeowners`
   - Créer la PR

3. **Vérifier**
   - ✅ Les reviewers définis dans CODEOWNERS sont automatiquement ajoutés
   - ✅ Le label peut être ajouté manuellement

4. **Nettoyer**
   - Fermer la PR sans merger
   - Supprimer la branche

### Test 3: Labels

1. **Créer une issue test**
   - Aller dans **Issues** → **New issue**
   - Titre: "Test labels"
   - Ajouter un label (ex: `feature`)
   - ✅ Vérifier que le label apparaît avec la bonne couleur

2. **Fermer l'issue**

---

## 📊 Résumé Configuration

### Branch Protection

| Branche | Require PR | Require Review | Force Push | Delete |
|---------|------------|----------------|------------|--------|
| `main` | ✅ | ✅ (1) | ❌ | ❌ |
| `develop` | ✅ | ✅ (1) | ❌ | ❌ |

### CODEOWNERS

| Path | Owners |
|------|--------|
| `*` | Lead dev |
| `/src_v2/` | Lead dev + Dev team |
| `/infra/` | Admin only |
| `/canonical/` | Admin + Data team |
| `/VERSION` | Admin only |

### Labels Créés

| Label | Couleur | Usage |
|-------|---------|-------|
| `feature` | Vert | Nouvelles fonctionnalités |
| `bugfix` | Orange | Corrections bugs |
| `hotfix` | Rouge | Corrections urgentes |
| `documentation` | Bleu | Documentation |
| `refactoring` | Jaune | Refactoring |
| `configuration` | Bleu clair | Config |
| `infrastructure` | Violet | Infra |
| `needs-review` | Jaune | En attente review |
| `approved` | Vert | Approuvé |
| `blocked` | Rouge | Bloqué |

---

## ✅ Validation Finale

**Checklist**:
- [ ] Branch protection `main` active (test push direct rejeté)
- [ ] Branch protection `develop` active
- [ ] CODEOWNERS mis à jour avec vrais usernames
- [ ] 10 labels créés avec bonnes couleurs
- [ ] Test PR montre reviewers automatiques
- [ ] Labels visibles dans Issues et PRs

---

## 🚀 Prochaines Étapes

### Optionnel: CI/CD avec GitHub Actions

Créer `.github/workflows/tests.yml`:

```yaml
name: Tests
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r src_v2/requirements.txt
      - name: Run tests
        run: python -m pytest tests/
```

### Optionnel: Auto-assign Labels

Créer `.github/labeler.yml`:

```yaml
feature:
  - 'src_v2/**'
  - 'tests/**'

documentation:
  - 'docs/**'
  - '**/*.md'

configuration:
  - 'canonical/**'
  - 'client-config-examples/**'

infrastructure:
  - 'infra/**'
  - 'scripts/deploy/**'
```

---

## 📞 Support

**En cas de problème**:

1. **Branch protection ne fonctionne pas**
   - Vérifier que vous avez les droits admin
   - Vérifier le nom exact de la branche (case-sensitive)

2. **CODEOWNERS ne fonctionne pas**
   - Vérifier que le fichier est dans `.github/CODEOWNERS`
   - Vérifier que les usernames existent (avec @)
   - Vérifier que les paths commencent par `/`

3. **Labels ne s'appliquent pas automatiquement**
   - Les labels doivent être ajoutés manuellement aux PRs
   - Utiliser GitHub Actions pour auto-labeling

---

**Configuration GitHub - Version 1.0**  
**Date**: 2026-01-31  
**Statut**: Guide complet prêt à l'emploi
