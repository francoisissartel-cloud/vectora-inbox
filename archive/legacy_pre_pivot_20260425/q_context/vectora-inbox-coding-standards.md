# Règles de Codage - Encodage et Compatibilité

**Fichier**: `.q-context/vectora-inbox-coding-standards.md`  
**Objectif**: Éviter les problèmes d'encodage Windows/Unix

---

## 🎯 Règle Principale: ASCII-First

**TOUJOURS utiliser des caractères ASCII dans le code Python exécutable**

### ❌ À ÉVITER

```python
# Emojis dans les prints
print("🎯 Starting process...")
print("✅ Success!")
print("❌ Failed!")

# Flèches Unicode
print(f"Promoting {from_env} → {to_env}")

# Symboles spéciaux
print("⚠️ Warning: Check configuration")
```

### ✅ À UTILISER

```python
# Préfixes textuels clairs
print("[TARGET] Starting process...")
print("[OK] Success!")
print("[ERROR] Failed!")

# Flèches ASCII
print(f"Promoting {from_env} -> {to_env}")

# Warnings textuels
print("[WARNING] Check configuration")
```

---

## 📋 Conventions de Préfixes

### Pour les Scripts Python

| Type | Préfixe | Exemple |
|------|---------|---------|
| Info | `[INFO]` | `[INFO] Processing 10 items` |
| Succès | `[OK]` ou `[SUCCESS]` | `[OK] Build completed` |
| Erreur | `[ERROR]` | `[ERROR] Connection failed` |
| Warning | `[WARNING]` | `[WARNING] Deprecated function` |
| Debug | `[DEBUG]` | `[DEBUG] Variable value: 42` |
| Étape | `[STEP]` | `[STEP 1/3] Loading data` |
| Validation | `[CHECK]` | `[CHECK] Verifying integrity` |
| Snapshot | `[SNAPSHOT]` | `[SNAPSHOT] Creating backup` |
| Rollback | `[ROLLBACK]` | `[ROLLBACK] Restoring state` |
| Tests | `[TEST]` | `[TEST] Running unit tests` |
| Deploy | `[DEPLOY]` | `[DEPLOY] Pushing to stage` |
| Build | `[BUILD]` | `[BUILD] Compiling sources` |

### Pour la Documentation Markdown

**Les emojis SONT AUTORISÉS** dans:
- ✅ Fichiers Markdown (`.md`)
- ✅ Commentaires de documentation
- ✅ README
- ✅ Plans de développement
- ✅ Rapports

**Raison**: Markdown est affiché dans des viewers qui supportent Unicode.

---

## 🔧 Solutions Techniques

### Option 1: Forcer UTF-8 (Recommandé pour nouveaux scripts)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script avec support UTF-8 explicite
"""
import sys
import io

# Forcer UTF-8 pour stdout/stderr
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Maintenant les emojis fonctionnent
print("✅ Success!")  # OK sur Windows
```

### Option 2: ASCII-Only (Recommandé pour scripts existants)

```python
#!/usr/bin/env python3
"""
Script compatible Windows sans modification
"""

# Utiliser uniquement ASCII
print("[OK] Success!")  # Fonctionne partout
print("[ERROR] Failed!")
print("dev -> stage")  # Flèche ASCII
```

### Option 3: Fonction Helper

```python
def safe_print(message: str, emoji: str = "", prefix: str = ""):
    """Print avec fallback ASCII sur Windows"""
    try:
        print(f"{emoji} {message}")
    except UnicodeEncodeError:
        print(f"{prefix} {message}")

# Usage
safe_print("Success!", emoji="✅", prefix="[OK]")
safe_print("Failed!", emoji="❌", prefix="[ERROR]")
```

---

## 📦 Checklist Avant Commit

Avant de committer un script Python:

- [ ] Aucun emoji dans les `print()` ou `f-strings`
- [ ] Aucune flèche Unicode (→ ← ↑ ↓)
- [ ] Aucun symbole spécial (⚠️ 💡 📦 🎯)
- [ ] Utilisation de préfixes `[INFO]`, `[OK]`, `[ERROR]`
- [ ] Test sur Windows si possible

---

## 🎓 Exemples de Refactoring

### Avant (Problématique)
```python
def deploy(env):
    print(f"🚀 Deploying to {env}...")
    if success:
        print(f"✅ Deployment successful!")
        print(f"dev → {env}")
    else:
        print(f"❌ Deployment failed!")
        print(f"⚠️ Check logs")
```

### Après (Compatible)
```python
def deploy(env):
    print(f"[DEPLOY] Deploying to {env}...")
    if success:
        print(f"[OK] Deployment successful!")
        print(f"dev -> {env}")
    else:
        print(f"[ERROR] Deployment failed!")
        print(f"[WARNING] Check logs")
```

---

## 🔍 Détection Automatique

### Script de Validation

```python
#!/usr/bin/env python3
"""
Détecte les caractères Unicode problématiques dans les scripts Python
"""
import re
import sys
from pathlib import Path

def check_file(filepath):
    """Vérifie un fichier pour caractères Unicode"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex pour détecter emojis et symboles
    unicode_pattern = re.compile(r'[^\x00-\x7F]+')
    
    issues = []
    for i, line in enumerate(content.split('\n'), 1):
        if unicode_pattern.search(line):
            issues.append((i, line.strip()))
    
    return issues

# Usage
if __name__ == '__main__':
    for py_file in Path('scripts').rglob('*.py'):
        issues = check_file(py_file)
        if issues:
            print(f"[WARNING] {py_file}:")
            for line_num, line in issues:
                print(f"  Line {line_num}: {line[:60]}...")
```

---

## 📚 Ressources

### Encodages Python
- UTF-8: Support universel, recommandé pour fichiers
- ASCII: Compatible partout, recommandé pour output console
- cp1252: Encodage Windows par défaut (limité)

### Commandes Utiles

```bash
# Vérifier encodage d'un fichier
file -i script.py

# Convertir UTF-8 -> ASCII (supprimer accents)
iconv -f UTF-8 -t ASCII//TRANSLIT input.txt > output.txt

# Trouver caractères non-ASCII
grep --color='auto' -P -n "[\x80-\xFF]" script.py
```

---

## 🎯 Règle d'Or

> **Si ça s'exécute sur Windows, utilise ASCII.  
> Si c'est de la documentation, les emojis sont OK.**

---

**Créé**: 2026-02-02  
**Auteur**: Amazon Q Developer  
**Statut**: Règle active
