# Sprint NNN — Titre court et descriptif

> Template : copier ce fichier, le renommer `sprint_NNN_titre.md` (NNN à 3 chiffres),
> remplir chaque section. Ne pas modifier ce template.

**Statut** : ⏸ Planifié
**Palier** : Niveau X (Fondations / Cœur / Maquillage)
**Date prévue** : YYYY-MM-DD
**Date effective** : (à remplir à l'exécution)
**Estimation** : ~Xh
**Durée réelle** : (à remplir post-exécution)

---

## Objectif

Une phrase claire qui décrit ce que le sprint produit. Doit être compréhensible en isolation, sans contexte du palier.

Exemple : *Implémenter la fonction de canonicalisation d'URL et le calcul d'`item_id`, avec leurs tests unitaires.*

---

## Critère de fin testable

Liste de cases à cocher concrètes. Chaque case doit pouvoir être validée par une commande, un test, ou une observation directe.

- [ ] Le test `tests/unit/test_X.py::test_Y` passe
- [ ] La commande `python -c "from src.X import Y; print(Y(...))"` retourne ce qui est attendu
- [ ] (etc. — autant de cases que nécessaire)

Si toutes les cases sont cochées, le sprint est terminé.

---

## Tâches détaillées (dans l'ordre d'exécution)

Liste numérotée. Chaque tâche doit être suffisamment précise pour être exécutée sans ambiguïté.

1. Créer `src/path/file.py` avec :
   - Fonction `func1(arg: type) -> type`
   - Fonction `func2(arg: type) -> type`
   - Type hints obligatoires (CLAUDE.md §5)
   - Docstrings sur chaque fonction publique
2. Créer `tests/unit/test_file.py` avec :
   - Test 1 : (description du cas)
   - Test 2 : (description du cas)
3. Lancer `pytest tests/unit/test_file.py -v` et valider que tous les tests passent
4. Commit : `feat(scope): brief description`
5. Push sur la branche en cours

---

## Fichiers créés / modifiés / supprimés

Liste précise. Toute modification non listée ici est une dérive du plan.

**✨ Créés** :
- `src/path/file.py`
- `tests/unit/test_file.py`

**📝 Modifiés** :
- (fichier si applicable, sinon "aucun")

**🗑️ Supprimés** :
- (fichier si applicable, sinon "aucun")

---

## Règles à suivre (références CLAUDE.md)

Lister les sections de CLAUDE.md qui s'appliquent particulièrement à ce sprint :

- §5 (conventions de code) : type hints, docstrings, snake_case
- §7 (conventions Git) : commit avec format `<type>(<scope>): description`
- §8 (tests) : tests unitaires obligatoires (Niveau 2+)
- §17 (small batches) : commit toutes les 15-30 min
- (etc.)

---

## Points de validation par Frank

Endroits où Claude s'arrête et demande validation avant de continuer.

- ⏸ **Avant exécution** : valider le plan dans son ensemble
- ⏸ **Après l'étape N** : montrer le diff pour valider la cohérence
- ⏸ **Après l'étape M** : valider le test avant push
- ⏸ **Après push** : valider que c'est bon pour merger

---

## Risques identifiés

Anticiper ce qui pourrait mal tourner et les mitigations.

| # | Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|---|
| 1 | (description) | Faible / Moyenne / Élevée | Faible / Moyen / Élevé | (action préventive) |

---

## Dépendances

Ce qui doit exister AVANT de pouvoir exécuter ce sprint.

- ADR XXX (titre) — accepté
- Sprint NNN (titre) — terminé et mergé
- Fichier `path/file.py` — existant
- Configuration `canonical/x.yaml` — à jour

Si une dépendance manque, le sprint ne peut pas démarrer. On fait d'abord la dépendance.

---

## Bilan post-exécution

À remplir UNE FOIS le sprint terminé. Ne pas pré-remplir.

### Durée réelle vs estimation

- Estimé : ~Xh
- Réel : ~Yh
- Écart : (justifier si > 50%)

### Commits effectués

- `<sha>` : `<type>(<scope>): <message>`
- `<sha>` : `<type>(<scope>): <message>`

### Difficultés rencontrées

(Description courte des problèmes inattendus et de leur résolution.)

### Décisions prises en cours de route

(Si des choix techniques non prévus ont été faits. Si majeurs → créer une ADR.)

### Ce qui reste pour le prochain sprint

(Si quelque chose n'a pas pu être fait, ou si une nouvelle tâche est apparue.)

### Validation Frank

- Date de validation : YYYY-MM-DD
- Commentaires éventuels :

---

*Sprint NNN — fin du document.*
