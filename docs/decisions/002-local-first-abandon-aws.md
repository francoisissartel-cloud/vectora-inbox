# 002 — Local-first : abandon d'AWS pour V1

**Statut** : ✅ Accepté
**Date** : 24/04/2026
**Contexte** : Phase 1 cadrage — découle directement du pivot (ADR 001)

## Le problème

Vectora Inbox V2 tournait entièrement sur AWS : Lambda pour le code, S3 pour les données, Bedrock pour le LLM, CloudFormation pour l'infra, IAM pour les permissions. Cette stack a deux inconvénients :
- **Friction de développement** : chaque test E2E nécessite build/deploy/test sur AWS, processus long
- **Couplage cloud** : difficile de prototyper rapidement, dépendance forte aux services AWS, coûts variables peu maîtrisés

Avec le pivot V1 et la volonté de Frank de reprendre la main sur son projet, il faut décider de la stack d'exécution.

## Options envisagées

1. **Garder AWS** : continuer avec Lambda + S3 + Bedrock
2. **Local-first** : tout tourne sur le PC de Frank, seul appel externe = API Anthropic
3. **Local + cloud optionnel** : code portable qui peut tourner local ou cloud selon config

## La décision

**Option 2 — Local-first pour V1, avec architecture qui préserve la portabilité cloud (option 3 implicite).**

Concrètement :
- Toutes les opérations tournent localement sur le PC de Frank
- Le datalake est sur le disque local (`data/datalake_v1/`)
- Le seul appel externe est l'API Anthropic (pour la normalisation)
- L'architecture du code prévoit des **abstractions** (`datalake/storage.py`, `normalize/llm/base.py`) qui permettront un jour de basculer vers S3 et Bedrock sans réécriture majeure

## Justification

- **Vélocité de développement** : pas de cycle build/deploy AWS, modifications testables instantanément
- **Coût maîtrisé** : pas d'infra AWS, seul coût = appels API Anthropic (pay-per-use, plafonnable)
- **Simplicité MVP** : un débutant en dev peut comprendre et exécuter le moteur sans connaissances AWS
- **Pas de blocage cloud** : si Anthropic API a un souci, on n'est pas bloqué par toute une stack AWS
- **Migration future préservée** : abstractions Storage/LLM permettent de passer à AWS plus tard si besoin (cf. `future_optimizations.md` §6)

## Conséquences

- Tous les artefacts AWS du projet (CloudFormation, Lambdas, layers, IAM) deviennent **legacy** et sont archivés
- `infra/`, `deployment/`, `monitoring/`, `layer_management/`, `build/` archivés en Phase 2.0
- Le profil AWS `rag-lai-prod` n'est plus utilisé en V1
- Frank doit créer une clé API Anthropic (`sk-ant-...`) au moment de démarrer la normalisation
- Le repo n'a plus aucune dépendance à un compte AWS pour fonctionner
- Le code est conçu avec des interfaces (`Storage`, `LLMClient`) pour permettre une migration AWS future

## Documents liés

- ADR 001 (Pivot vers datalake) — origine de cette décision
- ADR 003 (Anthropic API vs Bedrock) — corollaire LLM
- `docs/architecture/datalake_v1_design.md` §1.4 (principes)
- `docs/architecture/future_optimizations.md` §6 (migration AWS un jour)
- `CLAUDE.md` §0 (legacy AWS officiellement obsolète)
