# GUIDE - Transition Nouveau Chat

**Date**: 2026-01-30  
**Situation**: Session actuelle proche limite tokens (130K/200K)

---

## 📋 CE QUI A ÉTÉ FAIT

### ✅ Complété dans Cette Session

1. **Diagnostic complet** problème layer stage legacy
   - Cause: Layer stage créé depuis fichier ancien (v42.zip)
   - Impact: Extraction dates absente en stage
   - Rapport: `.tmp/diagnostic_repo_dev_stage.md`

2. **Plans créés**:
   - `plan_gouvernance_repo_et_environnements.md` (8h, gouvernance)
   - `plan_correctif_layer_stage_et_amelioration_promotion.md` (4h, correction)
   - `annexes_scripts_gouvernance.md` (scripts Python complets)
   - `avis_expert_gestion_repo_et_environnements.md` (analyse architecte)

3. **Préparation gouvernance**:
   - Commit snapshot: d2872c1
   - Branche créée: governance-setup
   - Structure documentée

---

## 🚀 PROCHAINES ÉTAPES

### Étape 1: Nouveau Chat - Exécuter Gouvernance

**Fichiers à copier-coller**:

**Option A - Prompt Court** (recommandé):
```
Ouvrir: docs/plans/PROMPT_COURT_NOUVEAU_CHAT.txt
Copier tout le contenu
Coller dans nouveau chat Amazon Q Developer
```

**Option B - Prompt Détaillé**:
```
Ouvrir: docs/plans/PROMPT_NOUVEAU_CHAT_GOUVERNANCE.md
Copier tout le contenu
Coller dans nouveau chat Amazon Q Developer
```

**Durée**: 6-7 heures

**Résultat**: Gouvernance en place, scripts fonctionnels

---

### Étape 2: Après Gouvernance - Correction Layer

Une fois gouvernance terminée, dans un nouveau chat:

**Prompt**:
```
Je viens de terminer la gouvernance Vectora Inbox.

Tâche: Mettre à jour et exécuter plan correctif layer stage.

Fichiers:
- @docs/plans/plan_correctif_layer_stage_et_amelioration_promotion.md
- @docs/plans/annexes_scripts_gouvernance.md

Adapter le plan correctif pour utiliser les nouveaux scripts build/deploy de la gouvernance.
Puis exécuter le plan pour corriger layer stage legacy.
```

**Durée**: 4 heures

**Résultat**: Dev/Stage alignés sur repo, extraction dates fonctionnelle

---

## 📁 FICHIERS IMPORTANTS

### Documents de Référence

```
docs/plans/
├── plan_gouvernance_repo_et_environnements.md      # Plan gouvernance (ÉTAPE 1)
├── annexes_scripts_gouvernance.md                  # Scripts Python complets
├── plan_correctif_layer_stage_et_amelioration_promotion.md  # Plan correctif (ÉTAPE 2)
├── SUIVI_EXECUTION_GOUVERNANCE.md                  # État actuel
├── PROMPT_NOUVEAU_CHAT_GOUVERNANCE.md              # Prompt détaillé
└── PROMPT_COURT_NOUVEAU_CHAT.txt                   # Prompt court ⭐

docs/architecture/
└── avis_expert_gestion_repo_et_environnements.md   # Analyse expert

.tmp/
├── diagnostic_repo_dev_stage.md                    # Diagnostic problème
├── phase0_audit_infrastructure.md                  # Audit infra
├── phase1_comparaison_configurations.md            # Comparaison configs
└── phase3_test_e2e_stage.md                        # Tests E2E stage
```

---

## 🎯 CHECKLIST TRANSITION

Avant de fermer cette session:

- [x] Plans créés et documentés
- [x] Prompts nouveau chat créés
- [x] Guide transition créé
- [x] Fichiers sauvegardés dans repo
- [ ] Commit final (à faire dans nouveau chat)

Avant de commencer nouveau chat:

- [ ] Lire `PROMPT_COURT_NOUVEAU_CHAT.txt`
- [ ] Vérifier branche `governance-setup` active
- [ ] Avoir 6-7h disponibles
- [ ] AWS CLI configuré

---

## 💡 CONSEILS

1. **Utiliser prompt court**: Plus facile à copier-coller
2. **Exécuter phase par phase**: Ne pas tout faire d'un coup
3. **Valider chaque phase**: Tester avant de continuer
4. **Copier scripts complets**: Ne pas recréer, utiliser annexes
5. **Demander aide si bloqué**: Q Developer peut débloquer

---

## 📞 SUPPORT

Si problème pendant exécution:

1. **Consulter**: `plan_gouvernance_repo_et_environnements.md`
2. **Vérifier**: `SUIVI_EXECUTION_GOUVERNANCE.md`
3. **Référence**: `annexes_scripts_gouvernance.md`
4. **Diagnostic**: `.tmp/diagnostic_repo_dev_stage.md`

---

## ✅ RÉSUMÉ EXÉCUTIF

**Situation**: Layer stage legacy, pas de gouvernance

**Solution**: 
1. Gouvernance (6-7h) → Repo = source vérité
2. Correctif (4h) → Dev/Stage alignés

**Documents prêts**: Tous les plans et scripts créés

**Action immédiate**: Copier `PROMPT_COURT_NOUVEAU_CHAT.txt` dans nouveau chat

**Durée totale**: 10-11 heures (2 jours)

**Bénéfice**: Système propre, maintenable, sans risque répétition erreur

---

**Guide Transition - Version 1.0**  
**Date**: 2026-01-30  
**Prêt pour nouveau chat**
