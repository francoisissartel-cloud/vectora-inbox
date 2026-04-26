# PROMPT POUR NOUVEAU CHAT - Exécution Plan Gouvernance Vectora Inbox

Copier-coller ce prompt dans un nouveau chat Amazon Q Developer.

---

## 🎯 CONTEXTE

Je travaille sur le projet Vectora Inbox (système de veille pharmaceutique). 

**Situation actuelle**:
- Repo local: `c:\Users\franc\OneDrive\Bureau\vectora-inbox`
- Branche actuelle: `governance-setup`
- Commit actuel: d2872c1 "chore: snapshot avant mise en place gouvernance"
- Environnement: Windows, AWS CLI configuré (profil rag-lai-prod)

**Problème identifié**: 
- Layer stage utilise code legacy (extraction dates absente)
- Pas de gouvernance claire repo/environnements
- Risque répétition erreurs

**Solution**: Mettre en place gouvernance AVANT correction

---

## 📋 TÂCHE À EXÉCUTER

Exécuter le **Plan de Gouvernance** (phases restantes) pour établir:
1. Repo local = source unique de vérité
2. Versioning explicite artefacts
3. Scripts build/deploy reproductibles
4. Workflow développement clair

**Durée estimée**: 6-7 heures (phases 0.2 à 6)

---

## 📁 FICHIERS À UTILISER

**IMPORTANT**: Utiliser ces 3 fichiers du repo comme référence:

1. **@docs/plans/plan_gouvernance_repo_et_environnements.md**
   - Plan complet avec 6 phases détaillées
   - Commandes à exécuter
   - Checklist validation

2. **@docs/plans/annexes_scripts_gouvernance.md**
   - 5 scripts Python complets (ANNEXES A-D)
   - Modifications vectora-inbox-development-rules.md (ANNEXE E)
   - Prêts à copier-coller

3. **@docs/plans/SUIVI_EXECUTION_GOUVERNANCE.md**
   - État actuel (PHASE 0.1 complétée)
   - Prochaines étapes
   - Commandes PowerShell prêtes

---

## 🚀 INSTRUCTIONS D'EXÉCUTION

### Étape 1: Lire les Documents

Lire et comprendre:
- `plan_gouvernance_repo_et_environnements.md` (plan complet)
- `annexes_scripts_gouvernance.md` (scripts)
- `SUIVI_EXECUTION_GOUVERNANCE.md` (état actuel)

### Étape 2: Exécuter Phases Restantes

**PHASE 0.2**: Créer structure dossiers (5 min)
- Créer `.build/`, `scripts/build/`, `scripts/deploy/`, `scripts/test/`

**PHASE 1**: Versioning (1h)
- Créer fichier `VERSION`
- Mettre à jour `.gitignore`

**PHASE 2**: Scripts Build (2h)
- Créer `scripts/build/build_layer_vectora_core.py`
- Créer `scripts/build/build_layer_common_deps.py`
- Créer `scripts/build/build_all.py`
- Copier code depuis ANNEXES A-D

**PHASE 3**: Scripts Deploy (2h)
- Créer `scripts/deploy/deploy_layer.py`
- Créer `scripts/deploy/deploy_env.py`
- Créer `scripts/deploy/promote.py`
- Copier code depuis ANNEXES

**PHASE 4**: Mise à Jour Règles (1h)
- Modifier `.q-context/vectora-inbox-development-rules.md`
- Ajouter sections depuis ANNEXE E

**PHASE 5**: Documentation (1h)
- Créer `docs/workflows/developpement_standard.md`
- Documenter workflow quotidien

**PHASE 6**: Tests & Validation (1h30)
- Tester build: `python scripts/build/build_all.py`
- Tester deploy dry-run
- Commit final sur main

### Étape 3: Validation Finale

Vérifier checklist complète dans `plan_gouvernance_repo_et_environnements.md`

---

## ⚠️ RÈGLES IMPORTANTES

1. **Exécuter phase par phase**: Valider chaque phase avant de continuer
2. **Copier scripts complets**: Utiliser code exact depuis annexes_scripts_gouvernance.md
3. **Tester après chaque phase**: Ne pas continuer si erreurs
4. **Demander confirmation**: Avant actions critiques (commit, merge)
5. **Respecter structure**: Ne pas modifier organisation dossiers

---

## 🎯 RÉSULTAT ATTENDU

À la fin de l'exécution:

✅ Structure repo propre (`.build/`, `scripts/`, `VERSION`)
✅ Scripts build/deploy fonctionnels
✅ Règles développement mises à jour
✅ Documentation workflow créée
✅ Tests validation réussis
✅ Gouvernance commitée sur main

**Après gouvernance**: Mettre à jour plan correctif puis corriger layer stage

---

## 📞 QUESTIONS FRÉQUENTES

**Q: Dois-je créer les scripts manuellement ?**
R: NON. Copier code complet depuis `annexes_scripts_gouvernance.md` ANNEXES A-D.

**Q: Que faire si erreur ?**
R: Arrêter, analyser, corriger, puis reprendre.

**Q: Puis-je sauter des phases ?**
R: NON. Chaque phase est nécessaire.

**Q: Combien de temps ça prend ?**
R: 6-7 heures au total (phases 0.2 à 6).

---

## 🚀 COMMENCER MAINTENANT

**Première action**: Lire `@docs/plans/plan_gouvernance_repo_et_environnements.md` puis exécuter PHASE 0.2.

**Commande de démarrage**:
```powershell
cd c:\Users\franc\OneDrive\Bureau\vectora-inbox
git status  # Vérifier branche governance-setup
```

---

**Prompt Version 1.0**  
**Date**: 2026-01-30  
**Prêt pour nouveau chat Amazon Q Developer**
