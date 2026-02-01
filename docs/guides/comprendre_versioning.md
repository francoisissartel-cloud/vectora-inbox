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
Repo Local
├── src_v2/vectora_core/utils.py  (fonctions A, B)
└── VERSION                        (VECTORA_CORE_VERSION=1.2.3)
```

### Vous Modifiez le Code

```python
# Ajout fonction C dans utils.py
def extract_dates():
    pass
```

### Vous Incrémentez VERSION

```ini
# Éditer VERSION
VECTORA_CORE_VERSION=1.2.4  ← Changé de 1.2.3 à 1.2.4
```

### Vous Buildez

```powershell
python scripts/build/build_all.py
```

**Résultat** :
```
.build/layers/vectora-core-1.2.4.zip  ← Contient code A, B, C
```

### Vous Déployez

```powershell
python scripts/deploy/deploy_env.py --env dev
```

**Résultat** :
```
AWS Dev utilise maintenant version 1.2.4 (code A, B, C)
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
2. **Incrémenter AVANT build**
3. **Pas de dossiers de versions** (v1.2.3/, v1.2.4/)
4. **Historique dans Git**, pas dans le repo
5. **Format MAJOR.MINOR.PATCH**

---

## 🎯 Résumé Ultra-Simple

```
1. Modifier code
2. Éditer VERSION (incrémenter numéro)
3. Build (génère .zip avec numéro)
4. Deploy (AWS utilise .zip avec numéro)
5. Commit Git (sauvegarde VERSION)
```

**C'est tout !** 🎉
