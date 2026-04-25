# .q-context - Guide Q Developer

**Index centralisé pour Amazon Q Developer**

---

## 🚨 LIRE EN PREMIER (Ordre Obligatoire)

1. **[CRITICAL_RULES.md](./CRITICAL_RULES.md)** - 🔥 Top 10 règles NON-NÉGOCIABLES
2. **[architecture.md](./architecture.md)** - Architecture 3 Lambdas V2
3. **[git-workflow.md](./git-workflow.md)** - Workflow Git complet

---

## 📚 LIRE SI BESOIN

4. **[aws-deployment.md](./aws-deployment.md)** - Déploiement AWS (Code + Data + Test)
5. **[test-e2e-aws-template.md](./test-e2e-aws-template.md)** - 🆕 **TEST E2E AWS (RÉFÉRENCE UNIQUE)**
6. **[q-planning-guide.md](./q-planning-guide.md)** - Planification et phases
7. **[vectora-inbox-q-prompting-guide.md](./vectora-inbox-q-prompting-guide.md)** - Comment prompter Q
8. **[vectora-inbox-development-rules.md](./vectora-inbox-development-rules.md)** - Règles développement complètes

---

## 🎯 TEMPLATES

9. **[templates/](./templates/)** - Templates plans/diagnostics/rapports
   - `plan-development-template.md`
   - `plan-diagnostic-template.md`
   - `report-final-template.md`
   - `test-e2e-template.md` - Template rapport E2E détaillé (après test)

---

## 🚀 Quick Start

### Commandes Essentielles

```bash
# Build
python scripts/build/build_all.py

# Deploy dev
python scripts/deploy/deploy_env.py --env dev

# Test dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# Promote stage
python scripts/deploy/promote.py --to stage --version X.Y.Z

# Test stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage
```

### Workflow Git Standard

```bash
git checkout -b feature/my-feature
# Modifier code + VERSION
git commit -m "feat: description"
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
git push origin feature/my-feature
# Créer PR
```

---

## 🌍 Environnements

| Env | Statut | Usage |
|-----|--------|-------|
| **dev** | ✅ Opérationnel | Développement et tests |
| **stage** | ✅ Opérationnel | Pré-production |
| **prod** | 🚧 À créer | Production clients |

---

## 📋 Checklist Admin

- [ ] Lire CRITICAL_RULES.md pour comprendre règles
- [ ] Utiliser scripts standardisés uniquement
- [ ] Tester en dev avant stage
- [ ] Incrémenter VERSION avant build
- [ ] Valider hygiène repo avant commit

---

## 🎯 Principe Fondamental

**Moins de contexte = Meilleure performance Q Developer**

Ce dossier contient UNIQUEMENT les règles et guides essentiels.  
Historique et détails dans `docs/`.

---

## 📞 Support Rapide

**En cas de problème**:
1. Consulter logs: `.tmp/logs/`
2. Vérifier version: `cat VERSION`
3. Valider build: `ls .build/layers/`
4. Test dry-run: `python scripts/deploy/deploy_env.py --env dev --dry-run`

**Reprise après interruption**:
```
Continue le plan docs/plans/plan_[NOM]_[DATE].md à partir de la Phase [N].
```

---

**Dernière mise à jour**: 2026-02-02  
**Architecture**: 3 Lambdas V2 validées E2E  
**Statut**: ✅ Documentation optimisée
