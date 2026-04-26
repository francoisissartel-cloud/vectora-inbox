# Comprendre le Versioning - Guide Simple

**Date** : 2026-01-30  
**Pour** : Administrateurs Vectora Inbox

---

## 🎯 Concept en 1 Phrase

**Le fichier VERSION contient des numéros d'étiquettes qu'on colle sur les artefacts (.zip) qu'on envoie vers AWS.**

---

## 📦 Analogie Simple

Imaginez une usine de boîtes :

```
Votre Repo = Usine
├── src_v2/           ← Recette pour fabriquer les boîtes
├── VERSION           ← Étiquettes à coller (numéros)
└── .build/           ← Boîtes fabriquées avec étiquettes
```

**Fichier VERSION** = Carnet d'étiquettes
```ini
VECTORA_CORE_VERSION=1.2.3  ← Numéro d'étiquette actuel
```

**Build** = Fabriquer une boîte et coller l'étiquette
```
.build/layers/vectora-core-1.2.3.zip  ← Boîte avec étiquette 1.2.3
```

---

## ❓ Questions Fréquentes

### "Chaque fichier doit avoir une version ?"

**NON.** Un seul fichier VERSION à la racine pour tout le repo.

```
✅ CORRECT
vectora-inbox/
└── VERSION  ← UN SEUL fichier

❌ INCORRECT
vectora-inbox/
├── src_v2/VERSION
├── canonical/VERSION
└── scripts/VERSION
```

### "Je dois avoir plusieurs versions dans mon repo ?"

**NON.** Une seule version ACTUELLE dans VERSION.

```
✅ CORRECT
VERSION contient : VECTORA_CORE_VERSION=1.2.4  ← Version actuelle

❌ INCORRECT
vectora-inbox/
├── v1.2.3/
├── v1.2.4/
└── v1.2.5/
```

**L'historique est dans Git**, pas dans des dossiers.

### "Où sont les anciennes versions ?"

**Dans Git commits** :

```bash
git log VERSION
# Commit abc123 : VERSION=1.2.3
# Commit def456 : VERSION=1.2.4  ← Actuel
```

---

## 🔄 Flux Complet

### Situation Initiale

```
Repo Local (branche develop)
├── src_v2/vectora_core/utils.py  (fonctions A, B)
└── VERSION                        (VECTORA_CORE_VERSION=1.2.3)
```

### 1. Créer Branche Feature

```bash
git checkout develop
git pull origin develop
git checkout -b feature/extraction-dates
```

### 2. Vous Modifiez le Code

```python
# Ajout fonction C dans utils.py
def extract_dates():
    pass
```

### 3. Vous Incrémentez VERSION

```ini
# Éditer VERSION
VECTORA_CORE_VERSION=1.3.0  ← Changé de 1.2.3 à 1.3.0 (MINOR)
```

### 4. Vous Committez (AVANT build!)

```bash
git add src_v2/ VERSION
git commit -m "feat(vectora-core): add extract_dates function

- Add extract_dates() in shared/utils.py
- Increment VECTORA_CORE_VERSION to 1.3.0

Refs: #123"
```

### 5. Vous Buildez

```powershell
python scripts/build/build_all.py
```

**Résultat** :
```
.build/layers/vectora-core-1.3.0.zip  ← Contient code A, B, C
```

### 6. Vous Déployez Dev

```powershell
python scripts/deploy/deploy_env.py --env dev
```

**Résultat** :
```
AWS Dev utilise maintenant version 1.3.0 (code A, B, C)
```

### 7. Vous Testez

```powershell
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7
```

### 8. Vous Pushez et Créez PR

```bash
git push origin feature/extraction-dates
# Créer Pull Request sur GitHub: feature/extraction-dates → develop
```

### 9. Après Merge, Tag et Promote

```bash
git checkout develop
git pull origin develop
git tag v1.3.0 -m "Release 1.3.0: Add extract_dates"
git push origin develop --tags
python scripts/deploy/promote.py --to stage --version 1.3.0 --git-sha $(git rev-parse HEAD)
```

---

## 📊 Format Sémantique

```
MAJOR.MINOR.PATCH
  1  .  2  .  3

MAJOR : Breaking change (1.2.3 → 2.0.0)
MINOR : Nouvelle fonction (1.2.3 → 1.3.0)
PATCH : Correction bug (1.2.3 → 1.2.4)
```

### Exemples Concrets

| Modification | Incrémentation | Résultat |
|--------------|----------------|----------|
| Ajout fonction extract_dates() | MINOR | 1.2.3 → 1.3.0 |
| Correction typo | PATCH | 1.2.3 → 1.2.4 |
| Rename fonction (breaking) | MAJOR | 1.2.3 → 2.0.0 |

---

## ✅ Règles Simples

1. **Un seul fichier VERSION** à la racine
2. **Créer branche feature** avant modification
3. **Commit AVANT build** (pas après!)
4. **Incrémenter VERSION** dans le commit
5. **Tag Git** après validation dev
6. **Pas de dossiers de versions** (v1.2.3/, v1.2.4/)
7. **Historique dans Git**, pas dans le repo
8. **Format MAJOR.MINOR.PATCH**
9. **Pull Request** obligatoire pour merge
10. **Synchroniser VERSION ↔ Git tags**

---

## 🎯 Résumé Ultra-Simple

```
1. Créer branche feature
2. Modifier code
3. Éditer VERSION (incrémenter numéro)
4. Commit Git (AVANT build!)
5. Build (génère .zip avec numéro)
6. Deploy dev (AWS utilise .zip avec numéro)
7. Test dev
8. Push et PR
9. Merge dans develop
10. Tag Git (v1.X.Y)
11. Promote stage
```

**C'est tout !** 🎉

---

## 📚 Documentation Complète Git

**Workflows détaillés** : `.q-context/vectora-inbox-git-workflow.md`  
**Règles Git** : `.q-context/vectora-inbox-git-rules.md`  
**Convention commits** : Conventional Commits (feat/fix/docs/refactor)
