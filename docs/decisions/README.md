# Architecture Decision Records (ADRs)

Ce dossier contient l'**historique des décisions architecturales** prises sur Vectora Inbox V1. Chaque fichier décrit une décision, ses alternatives, sa justification et ses conséquences.

## Pourquoi des ADRs ?

Quand on prend une décision technique, on a souvent une bonne raison. Mais cette raison s'oublie en quelques semaines. Six mois plus tard, on se demande "pourquoi on a fait ça déjà ?" et on perd du temps à reconstituer le contexte — ou pire, on défait une bonne décision parce qu'on a oublié pourquoi elle avait été prise.

Une ADR est une **fiche courte** (1 page max) qui répond à : quel était le problème, quelles options on avait, qu'a-t-on décidé, et pourquoi.

## Format des ADRs

Chaque ADR est numérotée chronologiquement (`001-...`, `002-...`, etc.) et suit le même format :

- **Header** : numéro, titre, statut, date, contexte
- **Le problème** : qu'est-ce qu'on cherchait à résoudre
- **Options envisagées** : alternatives considérées
- **Décision** : ce qu'on a choisi
- **Justification** : pourquoi
- **Conséquences** : ce que ça implique
- **Documents liés** : référence vers le design doc, autres ADRs, etc.

## Règle d'or

**Une ADR est immutable** une fois écrite. Si on revient sur une décision, on n'édite pas l'ADR existante : on en écrit une nouvelle qui la **supersede** (annule et remplace), et on marque le statut de l'ancienne en `Superseded by ADR-XXX`.

Cela préserve la mémoire historique : on sait qu'on a un jour décidé X, puis qu'on a changé pour Y, et pourquoi.

## Index des ADRs

Le tableau à jour des décisions actives est dans `STATUS.md` à la racine du repo (section "Décisions architecturales clés").
