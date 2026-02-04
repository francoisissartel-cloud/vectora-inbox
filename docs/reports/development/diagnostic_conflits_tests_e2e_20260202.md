# Diagnostic Conflits Tests E2E - .q-context

**Date**: 2026-02-02  
**Statut**: ✅ RÉSOLU

---

## 🔍 PROBLÈMES IDENTIFIÉS

### Conflit 1: Référence Fichier Supprimé

**Fichier**: `q-planning-rules.md` ligne 17  
**Problème**: Référence `.q-context/q-conformity-check.md` (supprimé lors optimisation)  
**Impact**: Q Developer confus si cherche ce fichier

### Conflit 2: Tests E2E Non Détaillés

**Fichiers concernés**:
- `q-planning-rules.md`: Mentionne "Tests E2E" sans détails
- `vectora-inbox-test-e2e-system.md`: Décrit système complet

**Problème**: Q Developer ne sait pas quelle méthode utiliser  
**Impact**: Risque de tests E2E incorrects

### Conflit 3: Redondance Partielle

**Problème**: 2 fichiers parlent de tests à niveaux différents  
**Impact**: Confusion sur workflow complet

---

## ✅ SOLUTIONS APPLIQUÉES

### Solution 1: Nouveau Fichier Simplifié

**Créé**: `.q-context/q-planning-guide.md` (250 lignes vs 500+ avant)

**Changements**:
- ❌ Supprimé référence `q-conformity-check.md`
- ✅ Ajouté lien explicite vers `vectora-inbox-test-e2e-system.md`
- ✅ Section "Tests E2E (IMPORTANT)" avec commandes exactes
- ✅ Règles critiques tests E2E intégrées
- ✅ Simplifié patterns et exemples

### Solution 2: Supprimé Ancien Fichier

**Supprimé**: `q-planning-rules.md` (obsolète)

### Solution 3: Hiérarchie Claire

**Maintenant**:
1. `q-planning-guide.md` → Planification générale + référence tests E2E
2. `vectora-inbox-test-e2e-system.md` → Système complet tests E2E

**Lien clair**: q-planning-guide pointe vers test-e2e-system pour détails

---

## 📊 RÉSULTAT

### Avant
```
.q-context/
├── q-planning-rules.md (500+ lignes)
│   ├── ❌ Référence fichier supprimé
│   ├── ❌ Tests E2E non détaillés
│   └── ❌ Pas de lien vers système contextes
└── vectora-inbox-test-e2e-system.md
    └── Système complet mais isolé
```

### Après
```
.q-context/
├── q-planning-guide.md (250 lignes) ✅
│   ├── ✅ Pas de référence obsolète
│   ├── ✅ Section Tests E2E avec commandes
│   └── ✅ Lien explicite vers test-e2e-system.md
└── vectora-inbox-test-e2e-system.md ✅
    └── Système complet référencé par planning
```

---

## 🎯 BÉNÉFICES

1. **Zéro conflit**: Pas de références obsolètes
2. **Hiérarchie claire**: Planning → Système E2E
3. **Simplicité**: 250 lignes vs 500+ avant
4. **Cohérence**: Workflow tests E2E unifié

---

## ✅ VALIDATION

**Q Developer peut maintenant**:
- Créer plan avec `q-planning-guide.md`
- Voir section Tests E2E avec commandes exactes
- Suivre lien vers `vectora-inbox-test-e2e-system.md` pour détails
- Utiliser système contextes correctement

**Pas de confusion possible**

---

**Diagnostic créé**: 2026-02-02  
**Statut**: ✅ CONFLITS RÉSOLUS
