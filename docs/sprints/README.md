# Mini-sprints — Vectora Inbox V1

Ce dossier contient les **plans de mini-sprints** du projet, ainsi que leurs bilans post-exécution.

## Qu'est-ce qu'un mini-sprint ?

Un mini-sprint est une **unité atomique de travail**, planifiée en amont, exécutée et validée. Granularité visée : **30 min à 4h** de travail effectif.

Plus court que 30 min → c'est un commit, pas un sprint.
Plus long que 4h → on doit redécouper.

## Pourquoi ?

Pour éviter le piège classique du développement : *"j'ai changé 50 choses d'un coup et maintenant rien ne marche, je ne sais plus laquelle a cassé"*.

Avec les mini-sprints :
- Chaque sprint a un **objectif clair** et un **critère de fin testable**
- L'avancement est **traçable** : on sait à tout moment dans quel sprint on est
- Les **risques** sont identifiés en amont, pas découverts en cours
- Les **validations** sont prévues à des points précis
- Le **bilan post-exécution** capture les leçons apprises

## Hiérarchie

```
Palier (Niveau 1, 2, 3)
  ├── Plan de palier (vue d'ensemble)
  │     └── docs/architecture/level_X_plan.md
  └── Mini-sprints (livrables atomiques)
        └── docs/sprints/sprint_NNN_titre.md
```

## Convention de nommage

`sprint_NNN_titre_court_descriptif.md`

- `NNN` : numéro à 3 chiffres, séquentiel (`001`, `002`, ..., `042`, ...)
- `titre_court_descriptif` : 3 à 6 mots en `snake_case` qui résument le sprint
- Exemple : `sprint_001_setup_arborescence.md`, `sprint_002_url_canonicalization.md`

Les sprints sont numérotés dans l'**ordre chronologique** d'exécution, pas par palier.

## Workflow

```
1. Claude rédige le plan dans sprint_NNN.md (à partir du template _TEMPLATE.md)
2. Frank lit et valide (ou demande des modifications)
3. Claude exécute le sprint en suivant le plan
4. Aux points de validation prévus, Claude s'arrête et présente
5. Frank valide chaque étape
6. Une fois fini : Claude remplit la section "Bilan post-exécution"
7. Claude met à jour STATUS.md
8. Si décision architecturale → nouvelle ADR dans docs/decisions/
9. Commit + push
```

## Règle d'or

**Pas de code sans plan validé**. Si le sprint n'existe pas ou n'est pas validé, on ne code pas.

Si en cours de sprint une opportunité d'amélioration surgit : elle est notée dans `STATUS.md` (idées en cours de réflexion) ou `future_optimizations.md`. Elle ne contamine **pas** le sprint en cours.

## Index

L'index courant des sprints est tenu à jour dans `STATUS.md` à la racine.

## Fichiers de ce dossier

- `_TEMPLATE.md` : template à copier pour créer un nouveau sprint
- `README.md` : ce fichier
- `sprint_NNN_titre.md` : un fichier par sprint (passé, en cours, ou planifié)
