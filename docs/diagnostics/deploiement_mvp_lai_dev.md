# Diagnostic de déploiement MVP LAI - Environnement DEV

## Statut global

**Date** : 2025-01-15  
**Environnement** : DEV  
**Statut** : PRÊT POUR EXÉCUTION MANUELLE

---

## Résumé exécutif

Le plan de déploiement complet a été créé dans `docs/plans/plan_deploiement_cli_mvp_lai.md`. Toutes les commandes nécessaires sont documentées et prêtes à être exécutées.

**Limitation rencontrée** : Le token SSO AWS a expiré pendant la tentative d'exécution automatique. L'utilisateur doit renouveler sa session SSO avant d'exécuter les commandes.

---

## Plan de déploiement créé

### Localisation
`docs/plans/plan_deploiement_cli_mvp_lai.md`

### Contenu
Le plan couvre 6 phases complètes :

1. **Phase 0 - Prérequis locaux** : Vérification AWS CLI, profil, identité
2. **Phase 1 - Validation des templates** : Validation de s0-core, s0-iam, s1-runtime
3. **Phase 2 - Packaging Lambda** : Build et upload des packages ingest-normalize et engine
4. **Phase 3 - Déploiement CloudFormation** : Déploiement des 3 stacks dans l'ordre
5. **Phase 4 - Chargement des configurations** : Upload des scopes canonical et config client
6. **Phase 5 - Test de la Lambda** : Invocation de ingest-normalize pour lai_weekly
7. **Phase 6 - Vérification des sorties** : Inspection des items normalisés dans S3

### Points forts du plan

- **Pédagogique** : Chaque commande est expliquée en français avec son objectif
- **Complet** : Toutes les étapes du déploiement sont couvertes
- **Reproductible** : Les commandes peuvent être copiées-collées directement
- **Sécurisé** : Utilise le profil SSO existant et la région eu-west-3
- **Debuggable** : Inclut des commandes de vérification et de diagnostic

---

## Prérequis pour l'exécution

### 1. Renouveler la session SSO

```powershell
# Se connecter via SSO
aws sso login --profile rag-lai-prod

# Vérifier l'identité
aws sts get-caller-identity --profile rag-lai-prod --region eu-west-3
```

### 2. Vérifier l'environnement local

- AWS CLI version 2.x installé
- Python 3.11+ installé
- pip installé
- PowerShell 5.1+ ou PowerShell Core 7+

### 3. Se positionner dans le répertoire du projet

```powershell
cd C:\Users\franc\OneDrive\Bureau\vectora-inbox
```

---

## Ordre d'exécution recommandé

### Étape 1 : Validation (Phase 1)

Valider les 3 templates CloudFormation pour détecter les erreurs de syntaxe.

**Commandes** : Voir Phase 1 du plan de déploiement.

**Durée estimée** : 1 minute

### Étape 2 : Packaging (Phase 2)

Créer les packages ZIP des Lambdas et les uploader vers S3.

**Commandes** : Voir Phase 2 du plan de déploiement.

**Durée estimée** : 5-10 minutes (dépend de la vitesse de pip install)

### Étape 3 : Déploiement infrastructure (Phase 3)

Déployer les 3 stacks CloudFormation dans l'ordre.

**Commandes** : Voir Phase 3 du plan de déploiement.

**Durée estimée** : 10-15 minutes

### Étape 4 : Configuration (Phase 4)

Uploader les fichiers canonical et la config client vers S3.

**Commandes** : Voir Phase 4 du plan de déploiement.

**Durée estimée** : 2 minutes

### Étape 5 : Test (Phases 5-6)

Invoquer la Lambda ingest-normalize et vérifier les sorties.

**Commandes** : Voir Phases 5-6 du plan de déploiement.

**Durée estimée** : 5 minutes

---

## Ressources créées (après déploiement réussi)

### Stacks CloudFormation

1. `vectora-inbox-s0-core-dev`
2. `vectora-inbox-s0-iam-dev`
3. `vectora-inbox-s1-runtime-dev`

### Buckets S3

1. `vectora-inbox-config-dev` (configurations)
2. `vectora-inbox-data-dev` (données ingérées et normalisées)
3. `vectora-inbox-newsletters-dev` (newsletters générées)
4. `vectora-inbox-lambda-code-dev` (artefacts Lambda)

### Rôles IAM

1. Rôle pour `vectora-inbox-ingest-normalize-dev`
2. Rôle pour `vectora-inbox-engine-dev`

### Fonctions Lambda

1. `vectora-inbox-ingest-normalize-dev`
2. `vectora-inbox-engine-dev`

### Log Groups CloudWatch

1. `/aws/lambda/vectora-inbox-ingest-normalize-dev`
2. `/aws/lambda/vectora-inbox-engine-dev`

---

## Fichiers de sortie attendus

### Outputs CloudFormation

Après déploiement, les fichiers suivants seront créés dans `infra/outputs/` :

1. `s0-core-dev.json` : Outputs de la stack s0-core (noms et ARNs des buckets)
2. `s0-iam-dev.json` : Outputs de la stack s0-iam (ARNs des rôles IAM)
3. `s1-runtime-dev.json` : Outputs de la stack s1-runtime (noms et ARNs des Lambdas)

### Fichiers de test

1. `test-event-ingest.json` : Événement de test pour la Lambda ingest-normalize
2. `out-ingest-lai-weekly.json` : Réponse de la Lambda après invocation
3. `items-normalized.json` : Items normalisés téléchargés depuis S3

---

## Points de vigilance

### 1. Token SSO

Le token SSO expire après quelques heures. Si vous voyez l'erreur :
```
Error when retrieving token from sso: Token has expired and refresh failed
```

Exécutez :
```powershell
aws sso login --profile rag-lai-prod
```

### 2. Bucket d'artefacts Lambda

Le bucket `vectora-inbox-lambda-code-dev` doit être créé AVANT le déploiement de s1-runtime. Si vous voyez une erreur lors du déploiement de s1-runtime mentionnant que le bucket n'existe pas, créez-le manuellement :

```powershell
aws s3 mb s3://vectora-inbox-lambda-code-dev --profile rag-lai-prod --region eu-west-3
```

### 3. Dépendances Python

Le packaging Lambda nécessite que toutes les dépendances soient installées dans le dossier de build. Si vous voyez des erreurs d'import lors de l'exécution de la Lambda, vérifiez que :

- `requirements.txt` est à jour
- `pip install -r requirements.txt -t $BUILD_DIR` s'est exécuté sans erreur
- Le package `vectora_core` est bien copié dans le dossier de build

### 4. Permissions IAM

Les rôles IAM créés par s0-iam doivent avoir les permissions nécessaires pour :

- Lire/écrire dans les buckets S3
- Invoquer les modèles Bedrock
- Écrire dans CloudWatch Logs
- Lire les paramètres SSM (pour la clé API PubMed)

Si vous voyez des erreurs de permissions lors de l'exécution des Lambdas, consultez les logs CloudWatch et vérifiez les policies IAM dans la stack s0-iam.

---

## Commandes de diagnostic

### Vérifier l'état des stacks

```powershell
# Lister toutes les stacks vectora-inbox
aws cloudformation list-stacks --profile rag-lai-prod --region eu-west-3 --query "StackSummaries[?contains(StackName, 'vectora-inbox')]"
```

### Vérifier les buckets S3

```powershell
# Lister les buckets vectora-inbox
aws s3 ls --profile rag-lai-prod --region eu-west-3 | Select-String "vectora-inbox"
```

### Vérifier les fonctions Lambda

```powershell
# Lister les fonctions vectora-inbox
aws lambda list-functions --profile rag-lai-prod --region eu-west-3 --query "Functions[?contains(FunctionName, 'vectora-inbox')]"
```

### Consulter les logs d'une Lambda

```powershell
# Logs de ingest-normalize
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev --since 30m --format detailed --profile rag-lai-prod --region eu-west-3

# Logs de engine
aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 30m --format detailed --profile rag-lai-prod --region eu-west-3
```

### Vérifier les événements d'une stack

```powershell
# Événements de s0-core
aws cloudformation describe-stack-events --stack-name vectora-inbox-s0-core-dev --profile rag-lai-prod --region eu-west-3 --max-items 20
```

---

## Prochaines étapes après déploiement réussi

### 1. Tester la Lambda engine

Une fois que ingest-normalize fonctionne, tester la Lambda engine :

```powershell
# Créer un événement de test
@"
{
  "client_id": "lai_weekly",
  "period_days": 7
}
"@ | Out-File -Encoding utf8 test-event-engine.json

# Invoquer la Lambda
aws lambda invoke `
  --function-name vectora-inbox-engine-dev `
  --payload file://test-event-engine.json `
  --profile rag-lai-prod `
  --region eu-west-3 `
  out-engine-lai-weekly.json
```

### 2. Vérifier la newsletter générée

```powershell
# Lister les newsletters
aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly/ --recursive --profile rag-lai-prod --region eu-west-3

# Télécharger la newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/2025/01/15/newsletter.md newsletter.md --profile rag-lai-prod --region eu-west-3
```

### 3. Itérer sur les configurations

- Ajuster les scopes dans `canonical/scopes/*.yaml`
- Modifier les règles de scoring dans `canonical/scoring/scoring_rules.yaml`
- Affiner la config client dans `client-config-examples/lai_weekly.yaml`
- Re-uploader les fichiers modifiés vers S3
- Re-tester les Lambdas

### 4. Déployer en STAGE

Une fois le DEV validé, répéter le processus avec `Env=stage` :

- Créer les stacks `vectora-inbox-s0-core-stage`, etc.
- Uploader les configs vers `vectora-inbox-config-stage`
- Tester avec les mêmes événements

---

## Conclusion

Le plan de déploiement est complet et prêt à être exécuté. L'utilisateur doit :

1. Renouveler sa session SSO AWS
2. Suivre le plan étape par étape dans `docs/plans/plan_deploiement_cli_mvp_lai.md`
3. Consulter ce diagnostic en cas de problème
4. Documenter les résultats dans le CHANGELOG

**Statut final** : ✅ PRÊT POUR EXÉCUTION MANUELLE
