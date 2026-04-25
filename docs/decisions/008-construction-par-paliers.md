# 008 — Construction par paliers : Fondations / Cœur / Maquillage

**Statut** : ✅ Accepté
**Date** : 25/04/2026
**Contexte** : Phase 1 cadrage — Frank a demandé un séquencement explicite

## Le problème

Comment séquencer le développement de Vectora Inbox V1 ? Frank a explicitement demandé : *"identifie ce qui est indispensable au début pour créer le squelette, ce qui vient après, et le maquillage. Je ne veux pas que tu essaies de développer dès le début quelque chose de complet."*

## Options envisagées

1. **Phases techniques séquentielles** : phase 2.2 = créer arborescence, phase 2.3 = ingest, phase 2.4 = normalize, phase 2.5 = maintenance, phase 2.6 = doc. Découpage par tâches techniques.
2. **Paliers de fonctionnalité** : Niveau 1 = squelette qui tourne bout-en-bout sur 1 item, Niveau 2 = utilisable au quotidien sur les 8 sources MVP, Niveau 3 = stable + documenté + observable. Découpage par capacité utilisateur.
3. **Sprints fixes** : itérations de 2 semaines avec backlog priorisé

## La décision

**Option 2 — Construction par paliers de fonctionnalité.**

Trois paliers :
- **Niveau 1 — Fondations** : 1 item LAI ingéré + normalisé bout-en-bout. Squelette qui prouve que l'architecture tient debout.
- **Niveau 2 — Cœur** : 8 sources MVP utilisables au quotidien + workflow d'onboarding (Discovery + Validation + Promotion).
- **Niveau 3 — Maquillage** : moteur stable, observable, robuste, documenté.

## Justification

L'option 1 (phases techniques) a un défaut majeur : **on n'a rien d'utilisable avant la fin**. Si on s'arrête à mi-parcours, on a un demi-pipeline qui ne sert à rien.

L'option 2 (paliers) garantit qu'**à tout moment, le moteur est dans un état utilisable**, juste plus ou moins riche. Si on s'arrête à la fin du Niveau 1, on a un bout-en-bout qui marche sur 1 source. Si on s'arrête à la fin du Niveau 2, on a un MVP LAI vivant. Le Niveau 3 ajoute de la qualité de vie mais n'est pas bloquant pour l'utilisation.

L'option 3 (sprints fixes) ne convient pas : pas d'équipe, pas de cadence imposée, on travaille par sessions au rythme de Frank.

## Critères de fin par palier

Chaque palier a un **critère testable** explicite. On ne passe au palier suivant qu'après l'avoir validé.

| Palier | Critère de fin testable |
|---|---|
| Niveau 1 | `python run_pipeline.py --client mvp_test_30days --source press_corporate__medincell` produit ≥ 1 item dans raw, le même item dans curated, lookup `by_item_id` retourne l'item dans les deux. |
| Niveau 2 | `python run_pipeline.py --client mvp_test_30days` ingère/normalise les 8 sources LAI. `python onboard_source.py --source X` ajoute proprement une 9e source via Discovery+Validation. |
| Niveau 3 | Rapport hebdomadaire `report_full.md` généré automatiquement. Moteur tourne sans surveillance plusieurs semaines. Doc suffisante pour qu'une autre personne reprenne. |

## Conséquences

- Le plan d'exécution Phase 2 du `datalake_v1_design.md` est structuré autour des 3 paliers (§13.3, §13.4, §13.5)
- À chaque palier, un mini-bilan financier et technique est présenté à Frank (cf. CLAUDE.md §15.5)
- À chaque palier validé, un tag git est posé : `v1.0.0-foundations`, `v1.0.0-core`, `v1.0.0`
- Le développement reste **réversible** : si on rate Niveau 2, on peut revenir à Niveau 1 propre
- Pas de "big bang" : le Niveau 3 (maquillage) ne contient que du polish, pas de feature critique
- Les optimisations qui ne rentrent dans aucun palier sont tracées dans `future_optimizations.md`

## Documents liés

- `docs/architecture/datalake_v1_design.md` §13 (plan de transition par paliers)
- `STATUS.md` (roadmap globale)
- `CLAUDE.md` §4 (les paliers de construction), §15.5 (bilan financier par palier)
