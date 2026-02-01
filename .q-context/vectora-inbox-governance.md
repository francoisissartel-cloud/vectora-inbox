# ✅ GOUVERNANCE EN PLACE

**Date**: 2026-01-30  
**Commit**: 19b57cc  
**Statut**: OPÉRATIONNEL

---

## 🎯 Principe Fondamental

**Repo local = Source unique de vérité**

Toute modification passe par: Build → Deploy Dev → Test → Promote Stage → Commit

---

## 📦 Versioning

**Fichier VERSION** : Un seul fichier à la racine contenant versions actuelles

```ini
VECTORA_CORE_VERSION=1.2.3
COMMON_DEPS_VERSION=1.0.5
CANONICAL_VERSION=1.1
```

**Format** : MAJOR.MINOR.PATCH
- MAJOR : Breaking change (1.2.3 → 2.0.0)
- MINOR : Nouvelle fonction (1.2.3 → 1.3.0)
- PATCH : Correction bug (1.2.3 → 1.2.4)

**Workflow** :
1. Modifier code
2. Incrémenter VERSION
3. Build (génère .zip avec numéro de version)
4. Deploy (AWS utilise version du .zip)

**Important** :
- ❌ Pas de dossiers v1.2.3/, v1.2.4/
- ✅ Un seul VERSION avec version actuelle
- ✅ Historique dans Git commits

**Guide complet** : `docs/guides/comprendre_versioning.md`

---

## 🚀 Commandes Essentielles

### Build
```bash
python scripts/build/build_all.py
```

### Deploy Dev
```bash
python scripts/deploy/deploy_env.py --env dev
```

### Promote Stage
```bash
python scripts/deploy/promote.py --to stage --version X.Y.Z
```

### Test Dev/Stage
```bash
# Test dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# Test stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage
```

---

## 🌍 Environnements

| Environnement | Statut | Usage |
|---------------|--------|-------|
| **dev** | ✅ Opérationnel | Développement et tests |
| **stage** | ✅ Opérationnel | Pré-production et validation |
| **prod** | 🚧 À créer | Production clients |

---

## 📚 Documentation

- **Workflow quotidien**: `.q-context/vectora-inbox-workflows.md`
- **Règles développement**: `.q-context/vectora-inbox-development-rules.md`
- **Architecture**: `.q-context/vectora-inbox-architecture-overview.md`

---

## 🚫 Interdictions

❌ Modifications directes AWS (console, CLI manuel)  
❌ Build sans incrémenter VERSION  
❌ Deploy direct stage sans test dev

---

## ✅ Workflow Standard

1. **Créer branche** depuis develop
2. Modifier code dans `src_v2/`
3. Incrémenter version dans `VERSION`
4. **Commit** (AVANT build!)
5. `python scripts/build/build_all.py`
6. `python scripts/deploy/deploy_env.py --env dev`
7. Tester en dev
8. **Push et Pull Request**
9. **Merge** dans develop
10. **Tag** version: `git tag v1.X.Y`
11. `python scripts/deploy/promote.py --to stage --version X.Y.Z --git-sha <sha>`
12. Tester en stage
13. **PR develop → main** (pour production)

---

**Gouvernance opérationnelle - Prêt pour développement**