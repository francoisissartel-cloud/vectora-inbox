# Guide Rapide - Configuration GitHub Automatique

**Durée**: 5 minutes

---

## 🎯 Objectif

Automatiser la configuration GitHub (branch protection + labels) via script Python.

---

## 📋 Étapes

### 1. Créer un Token GitHub (2 minutes)

1. **Aller sur GitHub**
   - https://github.com/settings/tokens

2. **Cliquer "Generate new token (classic)"**

3. **Configurer le token**
   - Note: `vectora-inbox-setup`
   - Expiration: `30 days`
   - Cocher les scopes:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `admin:repo_hook` (Full control of repository hooks)

4. **Générer et copier le token**
   - Cliquer **Generate token**
   - ⚠️ **COPIER LE TOKEN** (vous ne le reverrez plus!)
   - Format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### 2. Exécuter le Script (1 minute)

```bash
# Installer requests si nécessaire
pip install requests

# Exécuter le script avec votre token
python scripts/maintenance/setup_github.py --token ghp_VOTRE_TOKEN_ICI
```

**Le script va**:
- ✅ Configurer branch protection pour `main`
- ✅ Configurer branch protection pour `develop`
- ✅ Créer 10 labels standardisés

---

### 3. Commit CODEOWNERS (1 minute)

```bash
git add .github/CODEOWNERS
git commit -m "chore: update CODEOWNERS with francoisissartel-cloud"
git push origin main
```

---

## ✅ Vérification

### Branch Protection
https://github.com/francoisissartel-cloud/vectora-inbox/settings/branches

Vous devriez voir:
- ✅ Rule pour `main`
- ✅ Rule pour `develop`

### Labels
https://github.com/francoisissartel-cloud/vectora-inbox/labels

Vous devriez voir 10 labels avec couleurs.

---

## 🔒 Sécurité Token

**Après utilisation**:
1. Aller sur https://github.com/settings/tokens
2. Cliquer **Delete** sur le token `vectora-inbox-setup`
3. Le token est révoqué

---

## ❌ Alternative Manuelle

Si vous préférez ne pas utiliser de token, suivez le guide manuel:
`docs/guides/configuration_github.md`

---

**Durée totale**: 5 minutes avec script vs 15 minutes manuel
