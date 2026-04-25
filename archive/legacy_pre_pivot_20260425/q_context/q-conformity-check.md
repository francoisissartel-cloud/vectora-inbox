# Règle de Conformité Q-Context - Obligatoire dans Tous les Plans

**Date**: 2026-01-31  
**Version**: 1.0  
**Statut**: RÈGLE CRITIQUE

---

## 🎯 RÈGLE OBLIGATOIRE

**Q Developer DOIT TOUJOURS inclure une section "CONFORMITÉ Q-CONTEXT" dans chaque plan créé.**

**Objectif**: Rassurer l'utilisateur que le plan respecte toutes les règles de gouvernance et ne risque pas d'abîmer le projet.

---

## 📋 SECTION À INCLURE

**Emplacement**: Juste avant la section "VALIDATION AVANT EXÉCUTION"

**Format obligatoire**:

```markdown
---

## ✅ CONFORMITÉ Q-CONTEXT

**Ce plan respecte les règles de gouvernance Vectora Inbox** :

✅ **Architecture** : 3 Lambdas V2 (`.q-context/vectora-inbox-development-rules.md`)
✅ **Git Workflow** : Branche → Commit → Build → Deploy (`.q-context/vectora-inbox-git-workflow.md`)
✅ **Planification** : Phases structurées avec Git/Versioning/Tests (`.q-context/q-planning-rules.md`)
✅ **Versioning** : Incrémentation VERSION avant build
✅ **Environnement** : Cible explicite (dev/stage/prod)
✅ **Scripts** : Utilisation scripts standardisés uniquement
✅ **Hygiène** : Temporaires dans `.tmp/`, builds dans `.build/`
✅ **Tests** : Validation dev avant promotion stage

**Vous pouvez suivre ce plan en toute sécurité - il ne risque pas d'abîmer le projet.**

---
```

---

## 🔍 VALIDATION PAR Q DEVELOPER

**Avant d'inclure cette section, Q DOIT vérifier**:

- [ ] Plan créé dans `docs/plans/` ou `docs/diagnostics/`
- [ ] Phases Git/Versioning/Tests incluses
- [ ] Environnement cible explicite
- [ ] Scripts standardisés utilisés (pas de commandes AWS manuelles)
- [ ] VERSION incrémenté avant build
- [ ] Tests dev avant promotion stage
- [ ] Fichiers temporaires dans `.tmp/`
- [ ] Architecture 3 Lambdas V2 respectée

**Si une règle n'est PAS respectée**: Q DOIT corriger le plan AVANT d'ajouter la section conformité.

---

## 📝 EXEMPLE D'APPLICATION

**Plan conforme**:
```markdown
# Plan de Développement - Correctifs Matching et Dates

[... contenu du plan ...]

---

## ✅ CONFORMITÉ Q-CONTEXT

**Ce plan respecte les règles de gouvernance Vectora Inbox** :

✅ **Architecture** : 3 Lambdas V2
✅ **Git Workflow** : Branche → Commit → Build → Deploy
✅ **Planification** : Phases structurées avec Git/Versioning/Tests
✅ **Versioning** : Incrémentation VERSION avant build
✅ **Environnement** : Cible explicite (dev/stage/prod)
✅ **Scripts** : Utilisation scripts standardisés uniquement
✅ **Hygiène** : Temporaires dans `.tmp/`, builds dans `.build/`
✅ **Tests** : Validation dev avant promotion stage

**Vous pouvez suivre ce plan en toute sécurité - il ne risque pas d'abîmer le projet.**

---

## ✅ VALIDATION AVANT EXÉCUTION

[... suite du plan ...]
```

---

## 🎯 BÉNÉFICES

**Pour l'utilisateur**:
- ✅ Confiance totale dans le plan
- ✅ Rassurance explicite
- ✅ Visibilité sur les règles respectées
- ✅ Pas de risque d'abîmer le projet

**Pour Q Developer**:
- ✅ Auto-validation du plan
- ✅ Checklist de conformité
- ✅ Réduction des erreurs
- ✅ Alignement garanti avec gouvernance

---

## 🚨 NON-RESPECT

**Si Q Developer oublie cette section**:

L'utilisateur DOIT rappeler:
```
Merci d'ajouter la section "CONFORMITÉ Q-CONTEXT" pour me rassurer 
que ce plan respecte bien toutes les règles de gouvernance.
```

---

**Règle créée le**: 2026-01-31  
**Statut**: OBLIGATOIRE dans tous les plans
