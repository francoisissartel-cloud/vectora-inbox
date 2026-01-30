# ✅ GOUVERNANCE EN PLACE

**Date**: 2026-01-30  
**Commit**: 19b57cc  
**Statut**: OPÉRATIONNEL

---

## 🎯 Principe Fondamental

**Repo local = Source unique de vérité**

Toute modification passe par: Build → Deploy Dev → Test → Promote Stage → Commit

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

### Test
```bash
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7
```

---

## 📚 Documentation

- **Workflow quotidien**: `docs/workflows/developpement_standard.md`
- **Règles développement**: `.q-context/vectora-inbox-development-rules.md`
- **Résumé complet**: `docs/plans/RESUME_GOUVERNANCE_COMPLETE.md`

---

## 🚫 Interdictions

❌ Modifications directes AWS (console, CLI manuel)  
❌ Build sans incrémenter VERSION  
❌ Deploy direct stage sans test dev

---

## ✅ Workflow Standard

1. Modifier code dans `src_v2/`
2. Incrémenter version dans `VERSION`
3. `python scripts/build/build_all.py`
4. `python scripts/deploy/deploy_env.py --env dev`
5. Tester en dev
6. `python scripts/deploy/promote.py --to stage --version X.Y.Z`
7. Tester en stage
8. `git commit` et `git push`

---

**Gouvernance opérationnelle - Prêt pour développement**
