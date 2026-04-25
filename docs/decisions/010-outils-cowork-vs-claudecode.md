# 010 — Outils de travail : Cowork pour cadrage, Claude Code pour développement

**Statut** : ✅ Accepté
**Date** : 25/04/2026
**Contexte** : Phase 1 cadrage — Frank a demandé une comparaison des deux outils

## Le problème

Frank dispose de deux environnements pour travailler avec Claude :
1. **Cowork** (interface Claude desktop, web ou app)
2. **Claude Code** (extension VS Code)

Quel outil utiliser pour quel type de travail ?

## Options envisagées

1. **Tout en Cowork** : conversation, design, code, tests
2. **Tout en Claude Code** : tout faire dans VS Code
3. **Hybride** : choix de l'outil selon la nature du travail

## La décision

**Option 3 — Hybride, avec règles claires sur quel outil pour quoi.**

| Phase | Outil recommandé | Pourquoi |
|---|---|---|
| Phase 2.0 (ménage repo) | Cowork → bascule vers Claude Code (à cause souci OneDrive) | Discussion + petite exécution |
| Phase 2.1 (audit nommage) | Cowork | Beaucoup d'analyse, peu de code |
| Niveau 1 (Fondations) | Cowork ou Claude Code, indifférent | 5-10 fichiers, ça passe partout |
| Niveau 2 (Cœur) | Claude Code | 30-40 fichiers, beaucoup d'allers-retours, tests |
| Niveau 3 (Maquillage) | Indifférent | Beaucoup de doc, peu de code dense |

## Justification

**Cowork est meilleur pour** :
- Conversation ouverte, négociation, débat
- Lecture confortable de documents longs
- Design d'architecture, planning, audit
- Décisions stratégiques

**Claude Code est meilleur pour** :
- Boucle écrire → tester → corriger rapide (terminal Windows direct, pas de sandbox isolé)
- Refactor multi-fichiers
- Navigation IDE native (sauter à la définition, etc.)
- Exécution de tests dans le vrai environnement

**Découverte pratique** : Cowork rencontre des problèmes de permissions sur `.git/index.lock` car le repo est dans OneDrive (le sandbox Linux dans lequel Cowork tourne ne peut pas modifier des fichiers verrouillés par OneDrive). Claude Code tourne directement sur Windows et n'a pas ce problème.

## Conséquences

- Le projet doit fonctionner **identiquement** dans les deux environnements (pas de hack spécifique)
- Les **règles de CLAUDE.md** s'appliquent à l'identique dans les deux outils
- La mémoire partagée entre les deux est dans les fichiers du repo (CLAUDE.md, STATUS.md, design doc, ADRs)
- Frank a déjà installé l'extension Claude Code (validé)
- Le test git push initial a été fait depuis Claude Code avec succès
- Au moment de basculer entre les deux outils, Claude doit lire `STATUS.md` pour reprendre le contexte

## Recommandation long terme

Déplacer le repo hors de OneDrive (ex: `C:\Users\franc\Projects\vectora-inbox\`) pour :
- Éliminer définitivement le souci de lock OneDrive
- Pouvoir basculer entre Cowork et Claude Code librement sans contrainte technique
- Accélérer Git localement (pas de double sync)

À faire à un moment calme. Tracé dans `future_optimizations.md` §10.

## Documents liés

- `CLAUDE.md` §13 (Outil de travail)
- `CLAUDE.md` §14 (Comment Frank vérifie le respect des règles dans les deux outils)
- `future_optimizations.md` §10 (déplacement repo hors OneDrive)
- ADR 008 (paliers) — outil par palier
