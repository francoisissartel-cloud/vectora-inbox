# Dossier Build (.build/)

**Statut** : Artefacts de build - Regenerable  
**Version** : 2.0 (Optimisé 2026-01-31)

---

## 📂 STRUCTURE OPTIMISÉE

```
.build/
├── workspace/              # Workspace temporaire de build
│   ├── vectora-core/
│   │   └── python/
│   │       └── vectora_core/
│   └── common-deps/
│       └── python/
│           ├── yaml/
│           ├── requests/
│           └── ...
├── layers/                 # Artefacts finaux (ZIPs)
│   ├── vectora-core-1.2.3.zip
│   ├── common-deps-1.0.5.zip
│   └── manifest.json       # Métadonnées de build
└── README.md               # Ce fichier
```

---

## 🎯 RÈGLES

### ✅ OBLIGATOIRE

- Tous les artefacts de build doivent être stockés ici
- Nommage : `{layer-name}-{MAJOR.MINOR.PATCH}.zip`
- Chaque build génère un `manifest.json` avec Git SHA
- Structure `python/` à la racine de chaque ZIP

### ❌ INTERDIT

- Commiter ce dossier dans Git (.gitignore)
- Créer des sous-dossiers autres que `workspace/` et `layers/`
- Dupliquer le code source (utiliser `workspace/` temporaire)

---

## 🔄 WORKFLOW

### Build

```bash
# Build tous les layers
python scripts/layers/build_all.py

# Résultat:
# .build/layers/vectora-core-1.2.3.zip
# .build/layers/common-deps-1.0.5.zip
# .build/layers/manifest.json
```

### Nettoyage

```bash
# Supprimer workspace temporaire
rm -rf .build/workspace/

# Supprimer tous les artefacts
rm -rf .build/*

# Ou utiliser le script
python scripts/maintenance/cleanup_build.sh
```

### Reconstruction

```bash
# Rebuild complet
python scripts/layers/build_all.py
```

---

## 📋 MANIFEST.JSON

**Emplacement** : `.build/layers/manifest.json`

**Contenu** :
```json
{
  "build_date": "2026-01-31T10:30:00Z",
  "git_sha": "abc123def456",
  "git_branch": "develop",
  "git_tag": "v1.2.3",
  "layers": [
    {
      "layer_name": "vectora-core",
      "version": "1.2.3",
      "zip_path": ".build/layers/vectora-core-1.2.3.zip",
      "size_mb": 12.5
    },
    {
      "layer_name": "common-deps",
      "version": "1.0.5",
      "zip_path": ".build/layers/common-deps-1.0.5.zip",
      "size_mb": 8.2
    }
  ]
}
```

---

## 🚫 DOSSIERS SUPPRIMÉS (Ancienne Structure)

Les dossiers suivants ont été supprimés lors de l'optimisation :

- ❌ `layer_build/` → Remplacé par `workspace/vectora-core/`
- ❌ `layer_fix/` → Remplacé par `workspace/vectora-core/`
- ❌ `layer_vectora_core_approche_b/` → Remplacé par `workspace/vectora-core/`
- ❌ `python/` → Remplacé par `workspace/common-deps/python/`

**Raison** : Redondance et confusion sur la source de vérité.

---

## 📚 DOCUMENTATION ASSOCIÉE

- **Règles layer management** : `.q-context/vectora-inbox-layer-management-rules.md`
- **Scripts de build** : `scripts/layers/build_all.py`
- **Gouvernance** : `.q-context/vectora-inbox-governance.md`

---

*Dossier Build - Version 2.0 Optimisée*  
*Date : 2026-01-31*  
*Statut : ✅ OPÉRATIONNEL*
