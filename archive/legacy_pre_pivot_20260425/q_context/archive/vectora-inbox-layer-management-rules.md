# Règles de Gestion des Lambda Layers - Vectora Inbox

**Date**: 2026-01-31  
**Version**: 1.0  
**Objectif**: Gestion cohérente, traçable et automatisée des Lambda Layers

---

## 🎯 PRINCIPE FONDAMENTAL

**Source unique de vérité** : 
- Code source : `src_v2/vectora_core/`
- Métadonnées : `layer_management/active/`
- Artefacts : `.build/layers/` (temporaire, regenerable)

---

## 📂 ORGANISATION DES DOSSIERS

### `.build/` - Artefacts Temporaires (NON versionné Git)

**Structure obligatoire** :
```
.build/
├── workspace/                    # Workspace temporaire de build
│   ├── vectora-core/
│   │   └── python/vectora_core/
│   └── common-deps/
│       └── python/
├── layers/                       # Artefacts finaux
│   ├── vectora-core-1.2.3.zip   # ✅ Versioning sémantique
│   ├── common-deps-1.0.5.zip    # ✅ Versioning sémantique
│   └── manifest.json            # Métadonnées de build
└── README.md
```

**Règles** :
- ✅ Peut être supprimé et régénéré à tout moment
- ✅ Nommage obligatoire : `{layer-name}-{MAJOR.MINOR.PATCH}.zip`
- ✅ Chaque build génère un manifest.json avec Git SHA
- ❌ Ne jamais commiter dans Git (.gitignore)

---

### `layer_management/` - Gestion Structurée (versionné Git)

**Structure obligatoire** :
```
layer_management/
├── active/                       # Layers actuellement déployées
│   ├── vectora-core/
│   │   ├── manifest.json        # Version, Git SHA, ARN AWS
│   │   └── README.md
│   └── common-deps/
│       ├── manifest.json
│       └── README.md
├── archive/                      # Anciennes versions (< 3 mois)
│   ├── 2026-01/
│   │   ├── vectora-core-1.2.2.zip
│   │   └── manifest.json
│   └── 2025-12/
└── tools/                        # Outils de validation
    ├── validate_layer.py
    ├── compare_layers.py
    └── README.md
```

**Règles** :
- ✅ Versionné dans Git
- ✅ Chaque layer active a un manifest.json avec Git SHA
- ✅ Archive mensuelle (supprimer > 3 mois, uploader vers S3)
- ✅ README.md par layer expliquant son rôle

---

### `scripts/layers/` - Scripts de Build et Deploy

**Scripts obligatoires** :
- `build_all.py` : Build tous les layers
- `build_vectora_core.py` : Build vectora-core uniquement
- `build_common_deps.py` : Build common-deps uniquement
- `deploy_layer.py` : Deploy layer vers AWS + sauvegarde ARN

**Règles** :
- ✅ Toujours sauvegarder .zip dans `.build/layers/`
- ✅ Toujours créer manifest.json avec Git SHA
- ✅ Toujours mettre à jour `layer_management/active/{layer}/manifest.json`
- ✅ Logs détaillés de chaque étape

---

## 🔄 WORKFLOW STANDARD

### Build Layer

```bash
# 1. Modifier code source
vim src_v2/vectora_core/shared/utils.py

# 2. Incrémenter VERSION
echo "VECTORA_CORE_VERSION=1.2.4" >> VERSION

# 3. Commit changements (AVANT build)
git add src_v2/vectora_core/ VERSION
git commit -m "feat(vectora-core): add utility function"

# 4. Build layer
python scripts/layers/build_vectora_core.py
# Output: .build/layers/vectora-core-1.2.4.zip
#         .build/layers/manifest.json (avec Git SHA)

# 5. Deploy vers AWS dev
python scripts/layers/deploy_layer.py --layer vectora-core --env dev
# Output: ARN sauvegardé dans layer_management/active/vectora-core/manifest.json

# 6. Test en dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# 7. Si succès, archiver ancienne version
mkdir -p layer_management/archive/2026-01/
mv .build/layers/vectora-core-1.2.3.zip layer_management/archive/2026-01/

# 8. Tag Git
git tag v1.2.4 -m "Release vectora-core 1.2.4"
git push origin develop --tags
```

### Promote Layer vers Stage

```bash
# 1. Promouvoir layer
python scripts/layers/deploy_layer.py --layer vectora-core --env stage --version 1.2.4

# 2. Test en stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage

# 3. Si succès, mettre à jour manifest stage
# (automatique via deploy_layer.py)
```

### Rollback Layer

```bash
# 1. Identifier version cible
cat layer_management/archive/2026-01/manifest.json

# 2. Redéployer ancienne version
python scripts/layers/deploy_layer.py --layer vectora-core --version 1.2.3 --env dev

# 3. Vérifier déploiement
aws lambda get-layer-version --layer-name vectora-inbox-vectora-core-dev --version-number X
```

---

## 📋 FORMAT MANIFEST.JSON

**Emplacement** : `layer_management/active/{layer-name}/manifest.json`

**Format obligatoire** :
```json
{
  "layer_name": "vectora-inbox-vectora-core-dev",
  "version": "1.2.4",
  "git_sha": "abc123def456789",
  "git_tag": "v1.2.4",
  "git_branch": "develop",
  "build_date": "2026-01-31T10:30:00Z",
  "build_user": "francois",
  "aws_arn_dev": "arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:42",
  "aws_arn_stage": "arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-stage:15",
  "size_mb": 12.5,
  "dependencies": {
    "pyyaml": "6.0.1",
    "requests": "2.31.0",
    "boto3": "1.34.0"
  },
  "source_path": "src_v2/vectora_core/",
  "compatible_runtimes": ["python3.11", "python3.12"]
}
```

**Champs obligatoires** :
- `layer_name` : Nom AWS du layer
- `version` : Version sémantique (MAJOR.MINOR.PATCH)
- `git_sha` : SHA du commit Git
- `build_date` : Date ISO8601 du build
- `aws_arn_dev` : ARN AWS en dev
- `size_mb` : Taille du layer compressé

---

## 🚫 INTERDICTIONS ABSOLUES

**Q Developer DOIT REFUSER** :

❌ **Créer layers sans versioning sémantique**
```bash
# ❌ INTERDIT
vectora-core-v2.zip
layer_v6.zip
vectora-core-date-fix.zip

# ✅ OBLIGATOIRE
vectora-core-1.2.3.zip
common-deps-1.0.5.zip
```

❌ **Sauvegarder ARN à la racine du repo**
```bash
# ❌ INTERDIT
vectora_core_layer_arn.txt (racine)
common_deps_layer_arn.txt (racine)

# ✅ OBLIGATOIRE
layer_management/active/vectora-core/manifest.json
layer_management/active/common-deps/manifest.json
```

❌ **Dupliquer layers dans plusieurs dossiers**
```bash
# ❌ INTERDIT
.build/layer_build/
.build/layer_fix/
.build/layer_vectora_core_approche_b/
.build/python/

# ✅ OBLIGATOIRE
.build/workspace/vectora-core/  (temporaire)
.build/layers/vectora-core-1.2.3.zip  (artefact final)
```

❌ **Commiter `.build/` dans Git**
```bash
# ❌ INTERDIT
git add .build/

# ✅ OBLIGATOIRE
# .build/ doit être dans .gitignore
```

❌ **Garder archives > 3 mois dans repo**
```bash
# ❌ INTERDIT
layer_management/archive/2025-10/  (> 3 mois)

# ✅ OBLIGATOIRE
# Uploader vers S3 puis supprimer
aws s3 sync layer_management/archive/2025-10/ s3://vectora-inbox-backups/layers/2025-10/
rm -rf layer_management/archive/2025-10/
```

---

## ✅ CHECKLIST AVANT DEPLOY LAYER

**Q Developer DOIT vérifier** :

- [ ] VERSION incrémentée dans fichier `VERSION`
- [ ] Code source commité dans Git
- [ ] Build réussi (`.build/layers/{layer}-{version}.zip` créé)
- [ ] Manifest.json créé avec Git SHA actuel
- [ ] Taille layer < 50MB compressé
- [ ] Structure `python/` à la racine du ZIP
- [ ] Pas d'extensions C (.so, .pyd) si layer pure Python
- [ ] Layer déployée vers AWS
- [ ] ARN sauvegardé dans `layer_management/active/{layer}/manifest.json`
- [ ] Ancienne version archivée dans `layer_management/archive/{YYYY-MM}/`
- [ ] README.md mis à jour si changements majeurs

---

## 🔧 COMMANDES RAPIDES

### Build et Deploy Complet

```bash
# Build tous les layers
python scripts/layers/build_all.py

# Deploy vers dev
python scripts/layers/deploy_layer.py --layer all --env dev

# Test
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7
```

### Validation Layer

```bash
# Valider structure layer
python layer_management/tools/validate_layer.py .build/layers/vectora-core-1.2.4.zip

# Comparer deux versions
python layer_management/tools/compare_layers.py \
  layer_management/archive/2026-01/vectora-core-1.2.3.zip \
  .build/layers/vectora-core-1.2.4.zip
```

### Nettoyage

```bash
# Nettoyer workspace temporaire
rm -rf .build/workspace/

# Archiver anciennes versions (> 3 mois)
python scripts/maintenance/archive_old_layers.py --older-than 90
```

---

## 📚 DOCUMENTATION ASSOCIÉE

- **Gouvernance générale** : `.q-context/vectora-inbox-governance.md`
- **Règles développement** : `.q-context/vectora-inbox-development-rules.md`
- **Blueprint technique** : `docs/architecture/blueprint-v2-ACTUAL-2026.yaml`

---

## 🎯 OBJECTIF POUR Q DEVELOPER

**Q Developer DOIT TOUJOURS** :

1. ✅ Utiliser versioning sémantique pour layers
2. ✅ Créer manifest.json avec Git SHA
3. ✅ Sauvegarder ARN dans `layer_management/active/`
4. ✅ Archiver anciennes versions
5. ✅ Valider structure avant deploy
6. ✅ Documenter changements dans README.md
7. ✅ Tester layer après deploy

**Résultat attendu** : Gestion des layers traçable, cohérente et automatisée.

---

*Règles de Gestion des Lambda Layers - Version 1.0*  
*Date : 2026-01-31*  
*Statut : ✅ OPÉRATIONNEL*
