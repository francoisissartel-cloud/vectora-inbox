# Statut du Projet Vectora Inbox – 2025-01-15

**Auteur** : Amazon Q Developer  
**Date** : 2025-01-15  
**Version** : 1.0

---

## Résumé Exécutif

Le projet Vectora Inbox est **prêt pour le déploiement et les tests end-to-end en DEV**.

**Statut global** : 🟡 **AMBER** – Infrastructure et code prêts, en attente d'exécution manuelle

---

## Composants Implémentés

### ✅ Lambda ingest-normalize (OPÉRATIONNELLE)

**Statut** : ✅ GREEN – Déployée et testée avec succès

**Fonctionnalités** :
- Ingestion depuis 8 sources (RSS + HTML)
- Normalisation avec Bedrock (Claude Sonnet 4.5)
- Détection d'entités (companies, molecules, technologies, indications)
- Écriture des items normalisés dans S3

**Derniers tests** :
- 104 items ingérés depuis 7 sources sur 8 (87.5% de succès)
- Normalisation Bedrock opérationnelle
- Temps d'exécution : ~22 secondes

**Mécanismes de résilience** :
- Retry automatique sur ThrottlingException (3 retries max)
- Limitation de la concurrence (1 en DEV)
- Parallélisation contrôlée (4 workers Bedrock)

---

### ✅ Lambda engine (IMPLÉMENTÉE, EN ATTENTE DE DÉPLOIEMENT)

**Statut** : 🟡 AMBER – Code implémenté, déploiement en attente

**Fonctionnalités** :
- **Phase 2 - Matching** : Calcul des intersections d'ensembles pour déterminer les items pertinents
- **Phase 3 - Scoring** : Attribution de scores basés sur 7 facteurs (event_type, récence, priorité, etc.)
- **Phase 4 - Newsletter** : Génération éditoriale avec Bedrock + assemblage Markdown

**Modules implémentés** :
- `src/vectora_core/matching/matcher.py` : Matching déterministe
- `src/vectora_core/scoring/scorer.py` : Calcul de scores transparents
- `src/vectora_core/newsletter/assembler.py` : Orchestration de la génération
- `src/vectora_core/newsletter/bedrock_client.py` : Appels Bedrock avec retry
- `src/vectora_core/newsletter/formatter.py` : Assemblage Markdown

**Prochaines étapes** :
1. Packager et uploader le code dans S3
2. Déployer la stack s1-runtime avec les modifications
3. Tester le workflow complet (ingest-normalize → engine)

---

## Infrastructure AWS

### ✅ Stacks CloudFormation Déployées

**s0-core-dev** : Buckets S3
- `vectora-inbox-config-dev` : Configurations (canonical + client)
- `vectora-inbox-data-dev` : Items normalisés
- `vectora-inbox-newsletters-dev` : Newsletters générées
- `vectora-inbox-lambda-code-dev` : Packages Lambda

**s0-iam-dev** : Rôles IAM
- `IngestNormalizeRole` : Permissions S3 (config + data), SSM (PubMed), Bedrock
- `EngineRole` : Permissions S3 (config + data + newsletters), Bedrock

**s1-runtime-dev** : Fonctions Lambda
- `vectora-inbox-ingest-normalize-dev` : Ingestion + normalisation
- `vectora-inbox-engine-dev` : Matching + scoring + newsletter

### 🟡 Modifications en Attente de Déploiement

**infra/s0-iam.yaml** :
- ✅ Ajout des permissions CONFIG_BUCKET pour le rôle Engine

**infra/s1-runtime.yaml** :
- ✅ Ajout de la limite de concurrence pour la Lambda engine (ReservedConcurrentExecutions: 1 en DEV)

---

## Configurations Canonical

### ✅ Scopes LAI

**Fichiers** : `canonical/scopes/*.yaml`

**Contenu** :
- `company_scopes.yaml` : 50+ entreprises LAI globales
- `molecule_scopes.yaml` : 20+ molécules LAI
- `technology_scopes.yaml` : Mots-clés LAI (long acting, depot, etc.)
- `indication_scopes.yaml` : Indications thérapeutiques
- `trademark_scopes.yaml` : Marques commerciales LAI
- `exclusion_scopes.yaml` : Termes d'exclusion

### ✅ Catalogue de Sources

**Fichier** : `canonical/sources/source_catalog.yaml`

**Contenu** :
- 8 sources MVP activées (3 presse RSS + 5 corporate HTML)
- Bouquets : `lai_corporate_mvp`, `press_biotech_premium`

### ✅ Règles de Scoring

**Fichier** : `canonical/scoring/scoring_rules.yaml`

**Contenu** :
- Poids par event_type (clinical_update: 5, regulatory: 5, partnership: 6, etc.)
- Poids par priorité de domaine (high: 3, medium: 2, low: 1)
- Facteurs additionnels (récence, type de source, profondeur du signal)
- Seuils de sélection (min_score: 10, min_items_per_section: 1)

### ✅ Configuration Client

**Fichier** : `client-config-examples/lai_weekly.yaml`

**Contenu** :
- Profil client (nom, verticale, langue, tone, voice)
- Watch domains (tech_lai_ecosystem, addiction_focus)
- Bouquets de sources (lai_corporate_mvp, press_biotech_premium)
- Layout de newsletter (2 sections principales)

---

## Scripts de Déploiement et Tests

### ✅ Scripts Créés

**Packaging** :
- `scripts/package-engine.ps1` : Package et upload du code engine

**Déploiement** :
- `scripts/deploy-runtime-dev.ps1` : Déploiement de la stack s1-runtime

**Vérification** :
- `scripts/verify-engine-deployment.ps1` : Vérification du déploiement

**Tests** :
- `scripts/test-engine-lai-weekly.ps1` : Test end-to-end complet

---

## Documentation

### ✅ Documents de Design

- `docs/design/vectora_inbox_engine_lambda.md` : Design complet de la Lambda engine
- `docs/design/vectora_inbox_engine_deploy_and_test_plan.md` : Plan de déploiement et tests

### ✅ Documents de Diagnostic

- `docs/diagnostics/vectora_inbox_engine_implementation.md` : Diagnostic d'implémentation
- `docs/diagnostics/vectora_inbox_engine_first_run.md` : Template de diagnostic du premier run

### ✅ Guides

- `docs/guides/guide_execution_deploiement_engine.md` : Guide d'exécution pas à pas
- `scripts/README.md` : Documentation des scripts

---

## Prochaines Actions

### Phase 1 : Déploiement (À EXÉCUTER MANUELLEMENT)

1. **Redéployer le rôle IAM Engine** :
   ```powershell
   aws cloudformation deploy --template-file infra/s0-iam.yaml --stack-name vectora-inbox-s0-iam-dev --parameter-overrides Env=dev ProjectName=vectora-inbox ConfigBucketName=vectora-inbox-config-dev DataBucketName=vectora-inbox-data-dev NewslettersBucketName=vectora-inbox-newsletters-dev PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key --capabilities CAPABILITY_IAM --profile rag-lai-prod --region eu-west-3
   ```

2. **Packager et uploader le code engine** :
   ```powershell
   .\scripts\package-engine.ps1
   ```

3. **Déployer la stack s1-runtime** :
   ```powershell
   .\scripts\deploy-runtime-dev.ps1
   ```

4. **Vérifier le déploiement** :
   ```powershell
   .\scripts\verify-engine-deployment.ps1
   ```

### Phase 2 : Tests (À EXÉCUTER MANUELLEMENT)

1. **Exécuter le test end-to-end** :
   ```powershell
   .\scripts\test-engine-lai-weekly.ps1
   ```

2. **Consulter les logs CloudWatch** :
   ```powershell
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 10m --format detailed --profile rag-lai-prod --region eu-west-3
   ```

### Phase 3 : Documentation (À COMPLÉTER APRÈS TESTS)

1. **Compléter le diagnostic** : `docs/diagnostics/vectora_inbox_engine_first_run.md`
2. **Mettre à jour le CHANGELOG** : `CHANGELOG.md`
3. **Évaluer la qualité de la newsletter** : Critères de ton, contenu, pertinence

---

## Risques et Points de Vigilance

### 🟡 Throttling Bedrock

**Risque** : Taux de throttling ~10-15% observé sur ingest-normalize

**Mitigation** :
- Concurrence Lambda limitée à 1 en DEV
- Retry automatique avec backoff exponentiel
- Parallélisation contrôlée (4 workers)

**Action** : Surveiller les logs lors du premier run de engine

### 🟡 Qualité Éditoriale

**Risque** : Bedrock pourrait générer des textes non conformes (hallucinations, ton inadapté)

**Mitigation** :
- Prompts structurés avec contraintes strictes
- Fallback en cas d'échec Bedrock
- Évaluation qualitative manuelle après le premier run

**Action** : Ajuster les prompts si nécessaire après le test

### 🟢 Permissions IAM

**Risque** : Permissions manquantes pour le rôle Engine

**Mitigation** :
- Permissions CONFIG_BUCKET ajoutées dans s0-iam.yaml
- Vérification automatique avec verify-engine-deployment.ps1

**Action** : Redéployer s0-iam-dev avant de tester

---

## Métriques de Succès

### Critères de Validation

✅ **Matching fonctionnel** : Items correctement matchés aux watch_domains (vérifiable via logs)

✅ **Scoring cohérent** : Items triés par score décroissant (vérifiable via logs)

✅ **Bedrock opérationnel** : Appels API réussis avec génération de textes éditoriaux

✅ **Newsletter générée** : Fichier Markdown valide dans S3

✅ **Pas de régression** : Lambda ingest-normalize continue de fonctionner

### Scénario de Test Nominal

**Input** :
```json
{
  "client_id": "lai_weekly",
  "period_days": 7
}
```

**Output attendu** :
- Newsletter Markdown dans `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/01/15/newsletter.md`
- Réponse Lambda avec `statusCode: 200` et statistiques d'exécution
- Logs CloudWatch détaillés (nb items, nb appels Bedrock, temps d'exécution)

---

## Conclusion

Le projet Vectora Inbox est **techniquement prêt** pour le déploiement et les tests en DEV. Toutes les composantes sont implémentées et documentées. L'exécution manuelle des phases 1, 2 et 3 permettra de valider le workflow complet et de documenter le premier run.

**Recommandation** : Procéder au déploiement et aux tests selon le guide d'exécution (`docs/guides/guide_execution_deploiement_engine.md`).

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-01-15  
**Version** : 1.0
