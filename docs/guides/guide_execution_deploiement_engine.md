# Guide d'Exécution – Déploiement et Tests de la Lambda Engine

**Date** : 2025-01-15  
**Auteur** : Amazon Q Developer  
**Objectif** : Guider l'exécution manuelle du déploiement et des tests de la Lambda engine

---

## Vue d'ensemble

Ce guide vous accompagne pas à pas pour :
1. **Déployer** la Lambda engine en DEV
2. **Tester** le workflow complet (ingest-normalize → engine)
3. **Diagnostiquer** les résultats
4. **Documenter** l'avancement

---

## Prérequis

Avant de commencer, vérifiez que :

✅ **Infrastructure de base déployée** :
- Stack `vectora-inbox-s0-core-dev` (buckets S3)
- Stack `vectora-inbox-s0-iam-dev` (rôles IAM)
- Stack `vectora-inbox-s1-runtime-dev` (Lambdas)

✅ **Configurations uploadées dans S3** :
- Scopes canonical dans `s3://vectora-inbox-config-dev/canonical/scopes/`
- Catalogue de sources dans `s3://vectora-inbox-config-dev/canonical/sources/source_catalog.yaml`
- Règles de scoring dans `s3://vectora-inbox-config-dev/canonical/scoring/scoring_rules.yaml`
- Configuration client dans `s3://vectora-inbox-config-dev/clients/lai_weekly.yaml`

✅ **AWS CLI configuré** :
- Profil `rag-lai-prod` configuré
- Région `eu-west-3`
- Permissions suffisantes (CloudFormation, Lambda, S3, IAM, Logs)

✅ **Code à jour** :
- Dernières modifications dans `src/` (matching, scoring, newsletter)
- Modifications d'infra dans `infra/s0-iam.yaml` et `infra/s1-runtime.yaml`

---

## Phase 1 : Déploiement de la Lambda Engine

### Étape 1.1 : Redéployer le rôle IAM Engine

**Pourquoi** : Le rôle IAM Engine a été mis à jour pour inclure les permissions de lecture du CONFIG_BUCKET.

**Commande** :

```powershell
aws cloudformation deploy `
  --template-file infra/s0-iam.yaml `
  --stack-name vectora-inbox-s0-iam-dev `
  --parameter-overrides `
    Env=dev `
    ProjectName=vectora-inbox `
    ConfigBucketName=vectora-inbox-config-dev `
    DataBucketName=vectora-inbox-data-dev `
    NewslettersBucketName=vectora-inbox-newsletters-dev `
    PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key `
  --capabilities CAPABILITY_IAM `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat attendu** : Message `Successfully created/updated stack - vectora-inbox-s0-iam-dev`

---

### Étape 1.2 : Packager et uploader le code de la Lambda engine

**Commande** :

```powershell
.\scripts\package-engine.ps1
```

**Actions** :
1. Crée un package ZIP du code source (`src/`)
2. Uploade le package dans `s3://vectora-inbox-lambda-code-dev/lambda/engine/latest.zip`

**Résultat attendu** : Message `Package uploadé avec succès dans s3://vectora-inbox-lambda-code-dev/lambda/engine/latest.zip`

---

### Étape 1.3 : Déployer la stack s1-runtime avec les modifications

**Commande** :

```powershell
.\scripts\deploy-runtime-dev.ps1
```

**Actions** :
1. Récupère les ARNs des rôles IAM depuis la stack `s0-iam-dev`
2. Déploie la stack `s1-runtime-dev` avec les paramètres appropriés
3. Sauvegarde les outputs dans `infra/outputs/s1-runtime-dev.json`

**Résultat attendu** : Message `Stack déployée avec succès`

---

### Étape 1.4 : Vérifier le déploiement

**Commande** :

```powershell
.\scripts\verify-engine-deployment.ps1
```

**Vérifications** :
- ✅ Lambda existe
- ✅ Variables d'environnement présentes
- ✅ Configuration correcte (concurrence = 1 en DEV)
- ✅ Rôle IAM attaché
- ✅ Buckets S3 accessibles

**Résultat attendu** : Message `✅ Lambda engine déployée et configurée correctement`

---

## Phase 2 : Tests End-to-End

### Étape 2.1 : Exécuter le test complet

**Commande** :

```powershell
.\scripts\test-engine-lai-weekly.ps1
```

**Actions** :
1. Invoque `ingest-normalize` pour générer des items normalisés
2. Invoque `engine` pour générer la newsletter
3. Télécharge et affiche un aperçu de la newsletter

**Fichiers générés** :
- `test-event-ingest.json`
- `test-event-engine.json`
- `out-ingest-lai-weekly.json`
- `out-engine-lai-weekly.json`
- `newsletter-lai-weekly.md`

**Résultat attendu** :
- Réponse `ingest-normalize` avec `statusCode: 200` et `items_normalized > 0`
- Réponse `engine` avec `statusCode: 200` et `items_selected > 0`
- Newsletter Markdown téléchargée avec succès

---

### Étape 2.2 : Consulter les logs CloudWatch

**Commande** :

```powershell
# Logs de ingest-normalize
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev `
  --since 10m `
  --format detailed `
  --profile rag-lai-prod `
  --region eu-west-3

# Logs de engine
aws logs tail /aws/lambda/vectora-inbox-engine-dev `
  --since 10m `
  --format detailed `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Points à vérifier** :
- ✅ Pas d'erreurs critiques
- ✅ Statistiques d'exécution (nb items, nb appels Bedrock, temps)
- ✅ Taux de throttling Bedrock acceptable (<10%)

---

## Phase 3 : Diagnostics et Documentation

### Étape 3.1 : Compléter le diagnostic

**Fichier** : `docs/diagnostics/vectora_inbox_engine_first_run.md`

**Actions** :
1. Ouvrir le fichier template
2. Compléter les sections avec les résultats du test :
   - Résultats de l'exécution (ingest-normalize + engine)
   - Analyse de la newsletter générée (structure, qualité éditoriale, pertinence)
   - Métriques techniques (appels Bedrock, performance)
   - Problèmes rencontrés et solutions
   - Recommandations d'ajustement

**Statut final** : Changer le statut de `⏳ EN ATTENTE D'EXÉCUTION` à `✅ GREEN` / `⚠️ AMBER` / `❌ RED`

---

### Étape 3.2 : Mettre à jour le CHANGELOG

**Fichier** : `CHANGELOG.md`

**Actions** :
1. Trouver l'entrée `⏳ Plan de déploiement et tests engine (EN COURS)`
2. Mettre à jour le statut de chaque phase :
   - Phase 1 : ✅ COMPLÉTÉ
   - Phase 2 : ✅ COMPLÉTÉ
   - Phase 3 : ✅ COMPLÉTÉ
3. Ajouter les statistiques du test :
   - Items analysés : [X]
   - Items matchés : [Y]
   - Items sélectionnés : [Z]
   - Sections générées : [N]
   - Temps d'exécution : [T] secondes

**Statut final** : Changer le statut global de `⏳ AMBER` à `✅ GREEN`

---

## Résumé des Livrables

À la fin de ce guide, vous devriez avoir :

✅ **Infrastructure** :
- Lambda engine déployée avec les bonnes permissions
- Concurrence limitée à 1 en DEV
- Variables d'environnement correctes

✅ **Tests** :
- Workflow complet testé (ingest-normalize → engine)
- Newsletter générée et téléchargée
- Logs CloudWatch consultés

✅ **Documentation** :
- Diagnostic complété (`docs/diagnostics/vectora_inbox_engine_first_run.md`)
- CHANGELOG mis à jour avec le statut final
- Évaluation qualitative de la newsletter

✅ **Prochaines étapes** :
- Plan d'itération défini
- Préparation STAGE documentée
- Monitoring planifié

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-01-15  
**Version** : 1.0
