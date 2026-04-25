# 001 — Pivot du projet : moteur de newsletter → moteur d'alimentation de datalake

**Statut** : ✅ Accepté
**Date** : 24/04/2026
**Contexte** : Phase 1 cadrage — première décision fondatrice après transfert de Q Developer à Claude

## Le problème

Vectora Inbox a été démarré il y a 8 mois avec Q Developer (AWS) comme **moteur de génération de newsletters** : ingestion → normalisation → matching → scoring → rédaction de newsletter. Frank, en utilisant le projet, a réalisé que cette approche est limitée :
- Le moteur produit *un seul* artefact (la newsletter) à chaque run
- Pour générer un autre type d'artefact (un rapport, un dashboard, un RAG), il faut tout re-ingérer
- La logique métier (scoring, matching) est figée dans le moteur, hors de la portée des consommateurs

Frank veut une approche plus pérenne, où le moteur produit un **artefact de référence** que plusieurs consommateurs (newsletters, rapports, RAG) viennent piocher.

## Options envisagées

1. **Continuer sur l'approche newsletter** : optimiser le moteur existant
2. **Pivoter vers un moteur d'alimentation de datalake** : le moteur ne produit plus de newsletter, il alimente un datalake propre. Les newsletters et autres consommateurs deviennent des projets séparés qui interrogent le datalake.
3. **Hybride** : le moteur fait les deux (alimente le datalake ET génère la newsletter)

## La décision

**Option 2 — Pivot complet vers un moteur d'alimentation de datalake.**

## Justification

- **Séparation des responsabilités** : un moteur d'ingestion qui fait *aussi* de la rédaction éditoriale est trop couplé. Le datalake comme artefact intermédiaire découple proprement.
- **Réutilisation** : un seul datalake → newsletters, rapports, RAG, dashboards multiples. Pas de re-ingestion à chaque besoin.
- **Évolutivité** : ajouter un nouveau consommateur ne nécessite plus de modifier le moteur.
- **Clarté de la dette technique** : le moteur a une responsabilité claire (alimenter le datalake), facile à tester, à maintenir, à monitorer.
- **Frank a une vision business à long terme** où la veille pharma alimente plusieurs produits, pas qu'un seul.

L'option hybride (3) a été écartée car elle aurait gardé le couplage actuel et compliqué le moteur.

## Conséquences

- Les Lambdas `newsletter-v2` et toute la logique éditoriale deviennent **legacy** et sont archivées
- Le `normalize_score` V2 est partiellement récupéré : la partie *normalisation* est gardée, la partie *matching/scoring* (qui est de la logique newsletter) est archivée
- Le projet entier est renommé conceptuellement : "Vectora Inbox" reste le nom mais le périmètre change
- Le scope newsletter sera traité plus tard, dans un projet séparé qui consommera le datalake
- L'architecture, les configs client, les règles de travail sont entièrement repensées (V1)

## Documents liés

- `docs/architecture/datalake_v1_design.md` §1 (vision et principes)
- `docs/architecture/phase1_audit_pivot_datalake.md` (audit de l'existant)
- `CLAUDE.md` §0 (rôle de Claude post-pivot)
