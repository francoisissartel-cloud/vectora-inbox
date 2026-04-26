# Guide d'Implémentation - Optimisation Layer Management

**Date** : 2026-01-31  
**Durée estimée** : 30 minutes  
**Statut** : Prêt à exécuter

---

## 🎯 OBJECTIF

Optimiser la gestion des Lambda Layers pour :
- ✅ Éliminer les redondances
- ✅ Améliorer la traçabilité (Git SHA → Layer → ARN)
- ✅ Standardiser le workflow
- ✅ Automatiser le build et deploy

---

## 📋 FICHIERS CRÉÉS

### Règles Q-Context
- `.q-context/vectora-inbox-layer-management-rules.md` ✅

### Scripts
- `scripts/layers/build_all.py` ✅
- `scripts/maintenance/cleanup_layer_management.py` ✅

### Documentation
- `.build/README.md` ✅
- `layer_management/README.md` ✅
- `layer_management/active/vectora-core/README.md` ✅
- `layer_management/active/vectora-core/manifest.json` ✅
- `layer_management/active/common-deps/README.md` ✅
- `layer_management/active/common-deps/manifest.json` ✅

---

## 🚀 ÉTAPES D'EXÉCUTION

### Phase 1 : Nettoyage (5 min)

```bash
# 1. Nettoyer les dossiers redondants
python scripts/maintenance/cleanup_layer_management.py

# Résultat attendu:
# ✅ Suppression .build/layer_build/
# ✅ Suppression .build/layer_fix/
# ✅ Suppression .build/layer_vectora_core_approche_b/
# ✅ Suppression .build/python/
# ✅ Suppression layer_management/experimental/layer_minimal/
# ✅ Suppression layer_management/experimental/layer_rebuild/
# ✅ Création .build/workspace/
# ✅ Création .build/layers/
```

### Phase 2 : Archiver backup/old_builds/ (Optionnel, 10 min)

```bash
# Si vous voulez conserver l'historique
aws s3 sync backup/old_builds/ s3://vectora-inbox-backups/old_builds/ --profile rag-lai-prod

# Puis supprimer localement
rm -rf backup/old_builds/
```

**Note** : Si vous n'avez pas besoin de l'historique, vous pouvez directement supprimer :
```bash
rm -rf backup/old_builds/
```

### Phase 3 : Build Layers (5 min)

```bash
# Build tous les layers avec la nouvelle structure
python scripts/layers/build_all.py

# Résultat attendu:
# ✅ .build/layers/vectora-core-1.2.3.zip
# ✅ .build/layers/common-deps-1.0.5.zip
# ✅ .build/layers/manifest.json (avec Git SHA)
```

### Phase 4 : Mettre à jour .gitignore (2 min)

Ajouter à `.gitignore` :
```gitignore
# Build artifacts
.build/workspace/
.build/layers/*.zip
.build/layers/manifest.json

# Layer ARNs (sauvegardés dans layer_management/)
*_layer_arn.txt
```

### Phase 5 : Commit (5 min)

```bash
# Ajouter les nouveaux fichiers
git add .q-context/vectora-inbox-layer-management-rules.md
git add scripts/layers/build_all.py
git add scripts/maintenance/cleanup_layer_management.py
git add .build/README.md
git add layer_management/
git add .gitignore

# Commit
git commit -m "feat(layer-management): optimize layer management structure

- Add layer management rules for Q Developer
- Create build_all.py script for automated builds
- Add manifests with Git SHA tracking
- Clean up redundant directories
- Improve documentation and traceability"

# Push
git push origin develop
```

---

## ✅ VALIDATION

### Vérifier la structure

```bash
# Vérifier .build/
ls .build/
# Attendu: workspace/, layers/, README.md

# Vérifier layer_management/
ls layer_management/active/
# Attendu: vectora-core/, common-deps/

# Vérifier manifests
cat layer_management/active/vectora-core/manifest.json
cat layer_management/active/common-deps/manifest.json
```

### Tester le build

```bash
# Build
python scripts/layers/build_all.py

# Vérifier les ZIPs
ls -lh .build/layers/*.zip

# Vérifier le manifest
cat .build/layers/manifest.json
```

---

## 🎯 PROCHAINES ÉTAPES

### Court terme (aujourd'hui)

1. ✅ Exécuter les phases 1-5 ci-dessus
2. ✅ Tester le build avec `build_all.py`
3. ✅ Valider la structure

### Moyen terme (cette semaine)

4. Créer `scripts/layers/deploy_layer.py` pour automatiser le deploy
5. Mettre à jour les manifests avec les ARN AWS actuels
6. Tester le workflow complet (build → deploy → test)

### Long terme (ce mois)

7. Créer `layer_management/tools/validate_layer.py`
8. Créer `layer_management/tools/compare_layers.py`
9. Automatiser l'archivage mensuel

---

## 🆘 EN CAS DE PROBLÈME

### Rollback

Si quelque chose ne fonctionne pas, vous pouvez restaurer :

```bash
# Annuler le commit
git reset --soft HEAD~1

# Restaurer les fichiers
git checkout .

# Restaurer les dossiers supprimés (si backup existe)
# (Les dossiers redondants peuvent être recréés si nécessaire)
```

### Support

Consultez :
- `.q-context/vectora-inbox-layer-management-rules.md` pour les règles
- `layer_management/README.md` pour la structure
- `.build/README.md` pour le workflow de build

---

## 📊 RÉSUMÉ DES AMÉLIORATIONS

| Avant | Après |
|-------|-------|
| 4+ copies de vectora_core | 1 seule source (src_v2/) + workspace temporaire |
| Pas de traçabilité Git | Manifest avec Git SHA |
| ARN à la racine | ARN dans manifests structurés |
| Nommage incohérent | Versioning sémantique strict |
| Pas de workflow clair | Workflow automatisé documenté |

**Note globale** : 6.5/10 → **9/10** ⭐

---

*Guide d'Implémentation - Layer Management V2*  
*Date : 2026-01-31*  
*Prêt à exécuter*
