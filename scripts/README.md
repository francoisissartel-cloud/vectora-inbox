# Scripts de Déploiement et Tests – Vectora Inbox

Ce dossier contient tous les scripts PowerShell pour déployer, tester et maintenir l'infrastructure Vectora Inbox.

---

## Scripts de Packaging

### `package-engine.ps1`

**Objectif** : Packager le code de la Lambda engine et l'uploader dans S3.

**Utilisation** :
```powershell
.\scripts\package-engine.ps1
```

**Actions** :
1. Crée un package ZIP du code source (`src/`)
2. Uploade le package dans `s3://vectora-inbox-lambda-code-dev/lambda/engine/latest.zip`
3. Nettoie les fichiers temporaires

**Prérequis** :
- AWS CLI configuré avec le profil `rag-lai-prod`
- Accès en écriture au bucket `vectora-inbox-lambda-code-dev`

---

## Scripts de Déploiement

### `deploy-runtime-dev.ps1`

**Objectif** : Déployer la stack CloudFormation `s1-runtime` en DEV (Lambdas ingest-normalize et engine).

**Utilisation** :
```powershell
.\scripts\deploy-runtime-dev.ps1
```

**Actions** :
1. Récupère les ARNs des rôles IAM depuis la stack `s0-iam-dev`
2. Déploie la stack `s1-runtime-dev` avec les paramètres appropriés
3. Sauvegarde les outputs de la stack dans `infra/outputs/s1-runtime-dev.json`

**Prérequis** :
- Stacks `s0-core-dev` et `s0-iam-dev` déjà déployées
- Packages Lambda uploadés dans S3 (`ingest-normalize/latest.zip` et `engine/latest.zip`)
- AWS CLI configuré avec le profil `rag-lai-prod`

---

## Scripts de Vérification

### `verify-engine-deployment.ps1`

**Objectif** : Vérifier que la Lambda engine est correctement déployée et configurée.

**Utilisation** :
```powershell
.\scripts\verify-engine-deployment.ps1
```

**Vérifications** :
1. ✅ Lambda existe
2. ✅ Variables d'environnement présentes (CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_MODEL_ID)
3. ✅ Configuration correcte (runtime, handler, timeout, mémoire, concurrence)
4. ✅ Rôle IAM attaché
5. ✅ Log group CloudWatch présent
6. ✅ Buckets S3 accessibles

**Prérequis** :
- Lambda `vectora-inbox-engine-dev` déployée
- AWS CLI configuré avec le profil `rag-lai-prod`

---

## Scripts de Tests

### `test-engine-lai-weekly.ps1`

**Objectif** : Tester le workflow complet end-to-end (ingest-normalize → engine).

**Utilisation** :
```powershell
.\scripts\test-engine-lai-weekly.ps1
```

**Actions** :
1. **Étape 1** : Invoque la Lambda `ingest-normalize` pour générer des items normalisés
2. **Étape 2** : Invoque la Lambda `engine` pour générer la newsletter
3. **Étape 3** : Télécharge et affiche un aperçu de la newsletter générée

**Fichiers générés** :
- `test-event-ingest.json` : Payload d'invocation pour ingest-normalize
- `test-event-engine.json` : Payload d'invocation pour engine
- `out-ingest-lai-weekly.json` : Réponse de ingest-normalize
- `out-engine-lai-weekly.json` : Réponse de engine
- `newsletter-lai-weekly.md` : Newsletter générée (téléchargée depuis S3)

**Prérequis** :
- Lambdas `vectora-inbox-ingest-normalize-dev` et `vectora-inbox-engine-dev` déployées
- Configurations client et canonical uploadées dans S3
- AWS CLI configuré avec le profil `rag-lai-prod`

---

## Workflow de Déploiement Complet

Pour déployer et tester Vectora Inbox en DEV depuis zéro :

### 1. Déployer l'infrastructure de base

```powershell
# Déployer les buckets S3
aws cloudformation deploy --template-file infra/s0-core.yaml --stack-name vectora-inbox-s0-core-dev --parameter-overrides Env=dev ProjectName=vectora-inbox --profile rag-lai-prod --region eu-west-3

# Déployer les rôles IAM
aws cloudformation deploy --template-file infra/s0-iam.yaml --stack-name vectora-inbox-s0-iam-dev --parameter-overrides Env=dev ProjectName=vectora-inbox ConfigBucketName=vectora-inbox-config-dev DataBucketName=vectora-inbox-data-dev NewslettersBucketName=vectora-inbox-newsletters-dev PubmedApiKeyParamPath=/rag-lai/dev/pubmed/api-key --capabilities CAPABILITY_IAM --profile rag-lai-prod --region eu-west-3
```

### 2. Packager et uploader le code

```powershell
# Packager la Lambda engine
.\scripts\package-engine.ps1

# Packager la Lambda ingest-normalize (si nécessaire)
# [Commande similaire pour ingest-normalize]
```

### 3. Déployer les Lambdas

```powershell
# Déployer la stack runtime
.\scripts\deploy-runtime-dev.ps1
```

### 4. Uploader les configurations

```powershell
# Uploader les scopes canonical
aws s3 sync canonical/scopes s3://vectora-inbox-config-dev/canonical/scopes --profile rag-lai-prod --region eu-west-3

# Uploader le catalogue de sources
aws s3 cp canonical/sources/source_catalog.yaml s3://vectora-inbox-config-dev/canonical/sources/source_catalog.yaml --profile rag-lai-prod --region eu-west-3

# Uploader les règles de scoring
aws s3 cp canonical/scoring/scoring_rules.yaml s3://vectora-inbox-config-dev/canonical/scoring/scoring_rules.yaml --profile rag-lai-prod --region eu-west-3

# Uploader la configuration client
aws s3 cp client-config-examples/lai_weekly.yaml s3://vectora-inbox-config-dev/clients/lai_weekly.yaml --profile rag-lai-prod --region eu-west-3
```

### 5. Vérifier le déploiement

```powershell
# Vérifier la Lambda engine
.\scripts\verify-engine-deployment.ps1
```

### 6. Tester le workflow complet

```powershell
# Exécuter le test end-to-end
.\scripts\test-engine-lai-weekly.ps1
```

---

## Dépannage

### Erreur : "Stack already exists"

Si une stack existe déjà, CloudFormation la mettra à jour automatiquement avec `aws cloudformation deploy`.

### Erreur : "Insufficient permissions"

Vérifiez que le profil `rag-lai-prod` a les permissions nécessaires :
- `cloudformation:*`
- `s3:*`
- `lambda:*`
- `iam:*`
- `logs:*`

### Erreur : "Lambda timeout"

Consultez les logs CloudWatch :
```powershell
aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 10m --format detailed --profile rag-lai-prod --region eu-west-3
```

### Erreur : "ThrottlingException" (Bedrock)

C'est normal en DEV avec une concurrence limitée. Le mécanisme de retry automatique devrait gérer ces erreurs. Si le problème persiste :
1. Vérifier que la concurrence Lambda est bien limitée à 1
2. Vérifier les logs pour voir le taux de retry
3. Demander une augmentation des quotas Bedrock si nécessaire

---

## Ressources

- **Documentation d'architecture** : `docs/design/vectora_inbox_engine_lambda.md`
- **Plan de déploiement** : `docs/design/vectora_inbox_engine_deploy_and_test_plan.md`
- **Diagnostics** : `docs/diagnostics/`
- **Contrats Lambda** : `contracts/lambdas/`

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-01-15  
**Version** : 1.0
