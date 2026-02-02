# 📚 Documentation Q-Context - Vectora Inbox

**Index centralisé des documents de référence pour Q Developer**

---

## 📚 Documents Essentiels (Ordre de Lecture)

### 0. **Contexte Business** (🔥 LIRE EN PREMIER)
- [`../docs/business/CONTEXTE_BUSINESS_VECTORA.md`](../docs/business/CONTEXTE_BUSINESS_VECTORA.md) - 🎯 **VISION, EXPERTISE MÉTIER, RAISON D'ÊTRE**

### 1. **Démarrage Rapide**
- [`q-response-format.md`](./q-response-format.md) - 🚨 **FORMAT DE RÉPONSE OBLIGATOIRE**
- [`vectora-inbox-assistant-guide.md`](./vectora-inbox-assistant-guide.md) - 🎓 **MODE ASSISTANT GUIDÉ (DÉBUTANTS)**
- [`q-usage-guide.md`](./q-usage-guide.md) - 🌟 **COMMENT UTILISER LES TEMPLATES**
- [`vectora-inbox-governance.md`](./vectora-inbox-governance.md) - Gouvernance et workflow standard
- [`vectora-inbox-q-prompting-guide.md`](./vectora-inbox-q-prompting-guide.md) - Comment prompter Q Developer
- [`../docs/architecture/blueprint-v2-ACTUAL-2026.yaml`](../docs/architecture/blueprint-v2-ACTUAL-2026.yaml) - 📐 **BLUEPRINT SYSTÈME COMPLET** (référence)

### 2. **Git et Versioning** (🔥 NOUVEAU)
- [`vectora-inbox-git-workflow.md`](./vectora-inbox-git-workflow.md) - 🌟 **WORKFLOWS GIT COMPLETS**
- [`vectora-inbox-git-rules.md`](./vectora-inbox-git-rules.md) - 🚨 **RÈGLES GIT OBLIGATOIRES**

### 3. **Développement**
- [`vectora-inbox-development-rules.md`](./vectora-inbox-development-rules.md) - 🔥 **RÈGLES COMPLÈTES (Tests E2E + Client Config + Déploiement AWS)**
- [`vectora-inbox-deployment-checklist.md`](./vectora-inbox-deployment-checklist.md) - 🚨 **CHECKLIST DÉPLOIEMENT AWS COMPLET**
- [`vectora-inbox-coding-standards.md`](./vectora-inbox-coding-standards.md) - 🚨 **STANDARDS DE CODAGE (Encodage, ASCII)**
- [`vectora-inbox-workflows.md`](./vectora-inbox-workflows.md) - Workflows détaillés par scénario
- [`vectora-inbox-test-e2e-system.md`](./vectora-inbox-test-e2e-system.md) - 🔥 **SYSTÈME TESTS E2E (Contextes, Protection AWS)**
- [`q-planning-rules.md`](./q-planning-rules.md) - Règles de planification pour Q

### 3. **Architecture Technique**
- [`vectora-inbox-architecture-overview.md`](./vectora-inbox-architecture-overview.md) - 📐 **ARCHITECTURE DE RÉFÉRENCE**
- [`../docs/architecture/blueprint-v2-ACTUAL-2026.yaml`](../docs/architecture/blueprint-v2-ACTUAL-2026.yaml) - 📋 **BLUEPRINT DÉTAILLÉ** (architecture 3 Lambdas, prompts canoniques, guide d'ajustement)

### 4. **Templates et Outils**
- [`templates/`](./templates/) - Templates de plans standardisés
  - [`plan-development-template.md`](./templates/plan-development-template.md) - Template développement
  - [`plan-diagnostic-template.md`](./templates/plan-diagnostic-template.md) - Template diagnostic
  - [`report-final-template.md`](./templates/report-final-template.md) - Template rapport final
- [`../docs/templates/`](../docs/templates/) - Templates de tests E2E
  - [`TEMPLATE_TEST_E2E_STANDARD.md`](../docs/templates/TEMPLATE_TEST_E2E_STANDARD.md) - 🎯 **TEMPLATE TEST E2E**
  - [`GUIDE_UTILISATION_TEMPLATE_E2E.md`](../docs/templates/GUIDE_UTILISATION_TEMPLATE_E2E.md) - Guide d'utilisation

---

## 🌟 SYSTÈME DE PLANS AUTOMATIQUES

### Comment ça Marche ?

**✅ Q Developer applique automatiquement** :
- Les règles de gouvernance
- Les templates de plans
- L'exécution phase par phase
- Les checkpoints de validation
- La création de rapports finaux

**💬 Vous promptez simplement** :
```
Ajoute une fonction pour extraire les dates relatives.
```

**🤖 Q répond automatiquement** :
```
Je vais créer un plan de développement pour l'extraction de dates relatives.

Plan créé dans docs/plans/plan_extraction_dates_20260131.md

Souhaitez-vous commencer par la Phase 0 (Cadrage) ?
```

**🚀 Consultez** [`q-usage-guide.md`](./q-usage-guide.md) **pour tous les détails**

---

## 🌍 Environnements Disponibles

| Environnement | Statut | Usage |
|---------------|--------|-------|
| **dev** | ✅ Opérationnel | Développement et tests |
| **stage** | ✅ Opérationnel | Pré-production et validation |
| **prod** | 🚧 À créer | Production clients |

---

## 🚀 Commandes Rapides

```bash
# Workflow Git + Build + Deploy
git checkout -b feature/my-feature
# Modifier code + VERSION
git commit -m "feat: description"
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

# Promouvoir vers stage avec Git SHA
git tag v1.X.Y -m "Release 1.X.Y"
python scripts/deploy/promote.py --to stage --version X.Y.Z --git-sha $(git rev-parse HEAD)

# Rollback si problème
python scripts/deploy/rollback.py --env stage --to-version 1.2.3 --git-tag v1.2.3

# Tests
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage
```

---

## 📋 Checklist Admin

- [ ] Lire [`q-usage-guide.md`](./q-usage-guide.md) pour comprendre les templates
- [ ] Utiliser les scripts standardisés uniquement
- [ ] Tester en dev avant stage
- [ ] Incrémenter VERSION avant build
- [ ] Valider hygiène repo avant commit

---

## 🎯 Workflow Standard Résumé

```
Git Branch → Commit → Build → Deploy Dev → Test → PR → Merge → Tag → Promote Stage
```

**Principe**: Git AVANT build, pas après déploiement

---

## 📞 Support Rapide

**En cas de problème**:
1. Consulter logs: `.tmp/logs/`
2. Vérifier version: `cat VERSION`
3. Valider build: `ls .build/layers/`
4. Tester dry-run: `python scripts/deploy/deploy_env.py --env dev --dry-run`

**Reprise après interruption**:
```
Continue le plan docs/plans/plan_[NOM]_[DATE].md à partir de la Phase [N].
```

---

## 📚 Documents Archivés

**Historique**: [`docs/architecture/historical/`](../../docs/architecture/historical/) - Documents techniques détaillés archivés

---

**Dernière mise à jour**: 2026-01-31  
**Architecture de référence**: 3 Lambdas V2 validées E2E  
**Statut**: ✅ Documentation optimisée et système de plans opérationnel