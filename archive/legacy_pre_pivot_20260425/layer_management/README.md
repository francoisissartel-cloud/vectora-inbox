# Layer Management - Organisation Structurée

**Date de mise à jour** : 2026-01-31  
**Version** : 2.0 (Optimisé)  
**Objectif** : Gestion cohérente et traçable des Lambda Layers

---

## 📂 STRUCTURE OPTIMISÉE

```
layer_management/
├── active/                       # Layers actuellement déployées
│   ├── vectora-core/
│   │   ├── manifest.json        # Métadonnées (version, Git SHA, ARN)
│   │   └── README.md            # Documentation
│   └── common-deps/
│       ├── manifest.json
│       └── README.md
├── archive/                      # Anciennes versions (< 3 mois)
│   └── 2026-01/                 # Archive mensuelle
├── tools/                        # Outils de validation
│   └── layer_inspection/
└── README.md                     # Ce fichier
```

---

## 🎯 LAYERS ACTIVES

### vectora-core (v1.2.3)

**Statut** : ✅ Production  
**Contenu** : Code métier `vectora_core` (ingest, normalization, newsletter, shared)  
**Utilisé par** : Toutes les Lambdas V2 (ingest, normalize-score, newsletter)

### common-deps (v1.0.5)

**Statut** : ✅ Production  
**Contenu** : Dépendances tierces (PyYAML, requests, feedparser, beautifulsoup4)  
**Utilisé par** : Toutes les Lambdas V2

---

## 🔄 WORKFLOW

### Build Layers

```bash
# Build tous les layers
python scripts/layers/build_all.py

# Résultat:
# .build/layers/vectora-core-1.2.3.zip
# .build/layers/common-deps-1.0.5.zip
# .build/layers/manifest.json
```

### Deploy Layers

```bash
# Deploy vers dev
python scripts/layers/deploy_layer.py --layer all --env dev

# Deploy vers stage
python scripts/layers/deploy_layer.py --layer all --env stage
```

### Archiver Anciennes Versions

```bash
# Archiver manuellement
mkdir -p layer_management/archive/2026-01/
mv .build/layers/vectora-core-1.2.2.zip layer_management/archive/2026-01/

# Ou automatiquement (> 3 mois → S3)
python scripts/maintenance/archive_old_layers.py --older-than 90
```

---

## 📋 MANIFESTS

Chaque layer active a un `manifest.json` contenant :
- Version sémantique (MAJOR.MINOR.PATCH)
- Git SHA du build
- ARN AWS (dev/stage)
- Taille du layer
- Dépendances
- Date de build

**Exemple** : `active/vectora-core/manifest.json`

---

## 🚫 DOSSIERS SUPPRIMÉS (Optimisation 2026-01-31)

Les dossiers suivants ont été supprimés car redondants :

- ❌ `experimental/layer_minimal/` → Non utilisé
- ❌ `experimental/layer_rebuild/` → Approche abandonnée

**Raison** : Simplification et élimination des redondances.

---

## 📚 DOCUMENTATION

- **Règles complètes** : `.q-context/vectora-inbox-layer-management-rules.md`
- **Scripts de build** : `scripts/layers/build_all.py`
- **Gouvernance** : `.q-context/vectora-inbox-governance.md`
- **Blueprint** : `docs/architecture/blueprint-v2-ACTUAL-2026.yaml`

---

## ✅ CHECKLIST MAINTENANCE

- [ ] Vérifier manifests à jour (Git SHA, ARN)
- [ ] Archiver versions > 3 mois vers S3
- [ ] Valider structure layers (python/ à la racine)
- [ ] Tester layers après deploy
- [ ] Documenter changements majeurs

---

*Layer Management - Version 2.0 Optimisée*  
*Date : 2026-01-31*  
*Statut : ✅ OPÉRATIONNEL*
