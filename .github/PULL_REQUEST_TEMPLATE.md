## 🎯 Description

[Description claire et concise des changements apportés]

## 📦 Type de changement

- [ ] Feature (nouvelle fonctionnalité)
- [ ] Bugfix (correction bug non urgent)
- [ ] Hotfix (correction urgente production)
- [ ] Documentation
- [ ] Refactoring (pas de changement fonctionnel)
- [ ] Configuration (canonical, client config)
- [ ] Infrastructure (CloudFormation, IAM)

## ✅ Checklist Développement

- [ ] **VERSION incrémentée** correctement (MAJOR/MINOR/PATCH)
- [ ] **Tests unitaires** ajoutés ou mis à jour
- [ ] **Tests E2E** passés en dev
- [ ] **Documentation** mise à jour si nécessaire
- [ ] **Pas de fichiers temporaires** committés (`.tmp/`, `.build/` ignorés)
- [ ] **Commit messages** suivent convention (feat/fix/docs/refactor)
- [ ] **Code review** demandé à au moins 1 reviewer

## 🧪 Tests Effectués

### Build
```bash
python scripts/build/build_all.py
```
- [ ] Build réussi sans erreur

### Deploy Dev
```bash
python scripts/deploy/deploy_env.py --env dev
```
- [ ] Deploy réussi
- [ ] Layers publiées correctement
- [ ] Lambdas mises à jour

### Tests E2E
```bash
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7
```
- [ ] StatusCode: 200
- [ ] Résultats attendus obtenus
- [ ] Pas de régression

### Résultats
[Décrire les résultats des tests, métriques, logs pertinents]

## 🌍 Environnements Impactés

- [ ] **dev** - Testé et validé
- [ ] **stage** - À promouvoir après merge
- [ ] **prod** - Nécessite validation stage

## 📊 Métriques (si applicable)

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| Temps d'exécution | X ms | Y ms | +/- Z% |
| Taux de matching | X% | Y% | +/- Z% |
| Coût Bedrock | $X | $Y | +/- Z% |

## 🔗 Références

Refs: #[numéro issue]  
Fixes: #[numéro issue si bugfix]  
Related: #[numéros issues liées]

## 📸 Screenshots/Logs (si applicable)

[Ajouter captures d'écran, logs CloudWatch, ou outputs pertinents]

## ⚠️ Points d'Attention

[Mentionner tout point nécessitant attention particulière du reviewer]

## 🚀 Plan de Déploiement

### Après Merge
1. Deploy dev depuis develop
2. Tests E2E complets en dev
3. Tag version: `git tag v1.X.Y`
4. Promote stage: `python scripts/deploy/promote.py --to stage --version 1.X.Y --git-sha <sha>`
5. Tests E2E en stage
6. Si OK, merge develop → main (pour production)

### Rollback Plan
En cas de problème:
```bash
python scripts/deploy/rollback.py --env stage --to-version 1.X.Y --git-tag v1.X.Y
```

---

**Reviewer**: Merci de vérifier particulièrement [mentionner aspects critiques]
