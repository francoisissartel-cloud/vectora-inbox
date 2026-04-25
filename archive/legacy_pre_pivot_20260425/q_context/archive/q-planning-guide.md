# Guide Planification Q Developer

**Date**: 2026-02-02  
**Version**: 2.0  
**Objectif**: Standardiser création et exécution de plans

---

## 🎯 Principe

**Q Developer DOIT créer un plan structuré avant toute modification complexe**

**Modification complexe**:
- Modification > 3 fichiers
- Déploiement AWS
- Changement architecture
- Correction bug critique
- Nouvelle fonctionnalité
- Diagnostic problème

---

## 📋 Règles Obligatoires

### 1. Déclenchement Automatique

**Q DOIT créer plan quand**:
- "Ajoute une nouvelle fonctionnalité..."
- "Corrige le bug..."
- "Déploie vers..."
- "Diagnostique le problème..."
- "Modifie l'architecture..."

### 2. Templates

**Q DOIT utiliser**:
- `.q-context/templates/plan-development-template.md` pour développement
- `.q-context/templates/plan-diagnostic-template.md` pour diagnostic

**Q DOIT**:
- Remplir TOUS les champs
- Adapter phases selon contexte
- Inclure phases Git/Versioning/Tests (voir section 3)
- Estimer durées réalistes

### 3. Phases Obligatoires

**CHAQUE plan développement DOIT inclure**:

**Phase N-2: Versioning**
- Analyser type changement (MAJOR/MINOR/PATCH)
- Incrémenter VERSION
- Durée: 2 min

**Phase N-1: Commit Git**
- Message commit (Conventional Commits)
- Lister fichiers modifiés
- Commandes git exactes
- Durée: 3 min

**Phase N: Tests & Validation**
- Build artefacts
- Deploy dev
- **Tests E2E** (voir `.q-context/vectora-inbox-test-e2e-system.md`)
- Validation résultats
- Durée: 10-15 min

**Phase N+1: Tag & Promotion (si succès)**
- Créer tag Git
- Promouvoir vers stage
- Tests stage
- Durée: 5-10 min

**Phase N+2: Rollback (si échec)**
- Détecter problème
- Proposer rollback
- Exécuter rollback
- Durée: 2-5 min

---

## 🧪 Tests E2E (IMPORTANT)

**Q DOIT utiliser le système de contextes**:

```bash
# 1. Test local (OBLIGATOIRE)
python tests/local/test_e2e_runner.py --new-context "Description"
python tests/local/test_e2e_runner.py --run

# 2. Test AWS (SI LOCAL RÉUSSI)
python tests/aws/test_e2e_runner.py --promote "Validation"
python tests/aws/test_e2e_runner.py --run
```

**Référence complète**: `.q-context/vectora-inbox-test-e2e-system.md`

**Règles critiques**:
- ❌ Jamais AWS sans succès local
- ❌ Jamais réutiliser contexte
- ✅ Toujours nouveau contexte après modification

---

## 📁 Emplacement

**Plans**:
- `docs/plans/plan_[OBJECTIF]_[DATE].md`
- `docs/diagnostics/diagnostic_[PROBLEME]_[DATE].md`

**Rapports**:
- `docs/reports/development/report_[OBJECTIF]_[DATE].md`
- `docs/reports/diagnostics/report_[PROBLEME]_[DATE].md`

---

## 🔄 Exécution Phase par Phase

**Q DOIT**:
- Exécuter UNE phase à la fois
- Présenter résultats
- Demander validation avant phase suivante

**Format checkpoint**:
```
## ✅ Phase [N] Terminée

**Résultats**:
- [Résultat 1]
- [Résultat 2]

**Prêt pour Phase [N+1]** ?
```

---

## 📊 Rapport Final

**Q DOIT créer rapport final** avec:
- Résumé exécutif
- Objectifs atteints vs prévus
- Durées réelles vs estimées
- Leçons apprises
- Recommandations

---

## 🚫 Gestion Erreurs

**En cas de problème, Q DOIT**:
1. STOP immédiat
2. Diagnostic rapide (< 5 min)
3. Proposition: rollback ou correction
4. Attendre validation utilisateur

**Q NE DOIT JAMAIS**:
- Continuer en cas d'erreur
- Modifier plan sans validation
- Ignorer checkpoints

---

## 🎯 Patterns

### Plan Simple (< 1h)
1. Créer plan
2. Présenter
3. Attendre validation
4. Exécuter phases développement
5. Phase Versioning
6. Phase Commit Git
7. Phase Tests & Validation (avec système contextes)
8. Phase Tag & Promotion
9. Finaliser

### Plan Complexe (> 1h)
1. Créer plan détaillé
2. Présenter vue d'ensemble
3. Validation plan complet
4. Phase 0 (cadrage)
5. Checkpoints entre phases
6. Phases développement
7. Phase Versioning
8. Phase Commit Git
9. Phase Tests & Validation (avec système contextes)
10. Phase Tag & Promotion
11. Documentation finale

### Diagnostic
1. Créer plan diagnostic
2. Phase 0: Reproduction
3. Phase 1: Investigation
4. Phase 2: Diagnostic
5. Phase 3: Évaluation risques
6. Phase 4: Recommandations

---

## ✅ Checklist Q Developer

**Avant plan**:
- [ ] Analyser complexité
- [ ] Choisir bon template
- [ ] Estimer durée et risques

**Pendant exécution**:
- [ ] Respecter ordre phases
- [ ] Utiliser checkpoints
- [ ] Demander validation
- [ ] Documenter résultats

**Tests E2E**:
- [ ] Utiliser système contextes
- [ ] Test local AVANT AWS
- [ ] Nouveau contexte après modification

**À la fin**:
- [ ] Créer rapport final
- [ ] Mettre à jour métriques

---

**Guide Planification - Version 2.0**  
**Date**: 2026-02-02  
**Statut**: Opérationnel - Corrigé et simplifié
