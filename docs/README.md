# Documentation Vectora Inbox

Ce dossier contient toute la documentation du projet Vectora Inbox.

---

## 📊 Documents de Statut

### `STATUS.md`
**Vue d'ensemble du projet** – Statut global, composants implémentés, infrastructure, prochaines actions.

**Quand le consulter** : Pour avoir une vue d'ensemble rapide de l'état du projet.

### `EXECUTION_SUMMARY.md`
**Résumé de la dernière session** – Ce qui a été accompli, livrables, prochaines étapes.

**Quand le consulter** : Pour comprendre ce qui a été fait récemment et ce qui reste à faire.

---

## 📐 Documents de Design

### `design/vectora_inbox_engine_lambda.md`
**Design complet de la Lambda engine** – Architecture, phases (matching, scoring, newsletter), contrats, plan d'implémentation.

**Quand le consulter** : Pour comprendre l'architecture et la logique métier de la Lambda engine.

### `design/vectora_inbox_engine_deploy_and_test_plan.md`
**Plan de déploiement et tests** – Plan détaillé en 4 phases (Déploiement, Tests, Diagnostics, Préparation Stage/Prod).

**Quand le consulter** : Pour déployer et tester la Lambda engine en DEV.

---

## 🔍 Documents de Diagnostic

### `diagnostics/vectora_inbox_engine_implementation.md`
**Diagnostic d'implémentation** – Résumé de l'implémentation de la Lambda engine, modules créés, logique de matching/scoring/newsletter.

**Quand le consulter** : Pour comprendre comment la Lambda engine a été implémentée.

### `diagnostics/vectora_inbox_engine_first_run.md`
**Diagnostic du premier run** – Template pour documenter le premier run end-to-end (résultats, qualité, métriques, problèmes).

**Quand le consulter** : Après avoir exécuté le test end-to-end, pour documenter les résultats.

### `diagnostics/bedrock_sonnet45_success_final_dev.md`
**Migration vers Claude Sonnet 4.5** – Diagnostic de la migration vers le nouveau modèle Bedrock.

**Quand le consulter** : Pour comprendre la configuration Bedrock et les problèmes de throttling.

### `diagnostics/ingestion_mvp_lai_after_redeploy.md`
**Test d'ingestion MVP LAI** – Résultats du test d'ingestion après redéploiement.

**Quand le consulter** : Pour comprendre les résultats de l'ingestion et les sources qui fonctionnent.

---

## 📚 Guides

### `guides/guide_execution_deploiement_engine.md`
**Guide d'exécution pas à pas** – Guide détaillé pour déployer et tester la Lambda engine en DEV.

**Quand le consulter** : Avant d'exécuter le déploiement et les tests manuellement.

---

## 📋 Plans

### `plans/plan_deploiement_cli_mvp_lai.md`
**Plan de déploiement CLI MVP LAI** – Plan complet pour déployer l'infrastructure de base en DEV.

**Quand le consulter** : Pour déployer l'infrastructure de base (buckets, rôles IAM, Lambdas).

### `plans/plan_correctif_sources_mvp_lai.md`
**Plan correctif sources MVP LAI** – Plan pour corriger les sources d'ingestion.

**Quand le consulter** : Pour comprendre les corrections apportées aux sources d'ingestion.

### `plans/plan_redeploiement_correctif_mvp_lai_dev.md`
**Plan de redéploiement correctif** – Plan pour redéployer après corrections.

**Quand le consulter** : Pour comprendre le processus de redéploiement après corrections.

---

## 🗂️ Organisation des Documents

```
docs/
├── README.md                          ← Vous êtes ici
├── STATUS.md                          ← Statut global du projet
├── EXECUTION_SUMMARY.md               ← Résumé de la dernière session
├── design/                            ← Documents de design et architecture
│   ├── vectora_inbox_engine_lambda.md
│   └── vectora_inbox_engine_deploy_and_test_plan.md
├── diagnostics/                       ← Diagnostics et résultats de tests
│   ├── vectora_inbox_engine_implementation.md
│   ├── vectora_inbox_engine_first_run.md
│   ├── bedrock_sonnet45_success_final_dev.md
│   └── ingestion_mvp_lai_after_redeploy.md
├── guides/                            ← Guides d'exécution pas à pas
│   └── guide_execution_deploiement_engine.md
└── plans/                             ← Plans de déploiement et corrections
    ├── plan_deploiement_cli_mvp_lai.md
    ├── plan_correctif_sources_mvp_lai.md
    └── plan_redeploiement_correctif_mvp_lai_dev.md
```

---

## 🚀 Démarrage Rapide

### Pour déployer la Lambda engine en DEV

1. **Consulter le statut** : `STATUS.md`
2. **Lire le guide d'exécution** : `guides/guide_execution_deploiement_engine.md`
3. **Suivre le plan** : `design/vectora_inbox_engine_deploy_and_test_plan.md`
4. **Exécuter les scripts** : Voir `../scripts/README.md`

### Pour comprendre l'architecture

1. **Design de la Lambda engine** : `design/vectora_inbox_engine_lambda.md`
2. **Diagnostic d'implémentation** : `diagnostics/vectora_inbox_engine_implementation.md`

### Pour diagnostiquer un problème

1. **Consulter les diagnostics existants** : `diagnostics/`
2. **Consulter les logs CloudWatch** : Voir commandes dans `guides/guide_execution_deploiement_engine.md`

---

## 📞 Ressources Complémentaires

- **Scripts de déploiement** : `../scripts/README.md`
- **Configurations canonical** : `../canonical/README.md`
- **Contrats Lambda** : `../contracts/README.md`
- **Code source** : `../src/README.md`
- **Infrastructure** : `../infra/README.md`

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-01-15  
**Version** : 1.0
