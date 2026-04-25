# Layer common-deps

**Nom AWS** : `vectora-inbox-common-deps-dev`  
**Version actuelle** : 1.0.5  
**Statut** : ✅ Actif

---

## 📋 DESCRIPTION

Layer contenant les dépendances tierces communes utilisées par toutes les Lambdas V2.

---

## 📦 DÉPENDANCES

```
PyYAML==6.0.1           # Parsing YAML (configs, prompts)
requests==2.31.0        # HTTP client
feedparser==6.0.10      # Parsing RSS feeds
beautifulsoup4==4.14.3  # Parsing HTML
```

---

## 🔄 BUILD

```bash
# Build layer
python scripts/layers/build_common_deps.py

# Ou build tous les layers
python scripts/layers/build_all.py
```

**Note** : Le build installe les dépendances en mode pure Python (pas de binaires C) pour compatibilité Lambda.

---

## 🚀 DEPLOY

```bash
# Deploy vers dev
python scripts/layers/deploy_layer.py --layer common-deps --env dev

# Deploy vers stage
python scripts/layers/deploy_layer.py --layer common-deps --env stage
```

---

## ⚙️ CONFIGURATION

**Source** : `src_v2/requirements.txt`

Pour ajouter une dépendance :
1. Ajouter dans `src_v2/requirements.txt`
2. Incrémenter `COMMON_DEPS_VERSION` dans `VERSION`
3. Rebuild : `python scripts/layers/build_common_deps.py`
4. Deploy : `python scripts/layers/deploy_layer.py --layer common-deps --env dev`

---

## 📊 MÉTADONNÉES

Voir `manifest.json` pour :
- Version actuelle
- Git SHA du build
- ARN AWS (dev/stage)
- Taille du layer
- Liste des dépendances

---

## 📚 DOCUMENTATION

- **Requirements** : `src_v2/requirements.txt`
- **Règles** : `.q-context/vectora-inbox-layer-management-rules.md`
- **Blueprint** : `docs/architecture/blueprint-v2-ACTUAL-2026.yaml`
