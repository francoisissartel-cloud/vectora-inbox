# Instructions de déploiement AWS pour Lambda ingest V2

## Étape 1: Reconnexion AWS SSO (OBLIGATOIRE)

Le token SSO a expiré. Exécutez d'abord :

```bash
aws sso login --profile rag-lai-prod
```

Puis vérifiez la connectivité :

```bash
aws sts get-caller-identity --profile rag-lai-prod --region eu-west-3
```

Vous devriez voir :
```json
{
    "UserId": "...",
    "Account": "786469175371", 
    "Arn": "arn:aws:sts::786469175371:assumed-role/AWSReservedSSO_RAGLai-Admin_dd0aa74f23dac197/Franck"
}
```

## Étape 2: Vérifier que la Lambda existe

```bash
aws lambda get-function --function-name vectora-inbox-ingest-dev --profile rag-lai-prod --region eu-west-3
```

## Étape 3: Upload des client_config modifiés

```bash
# Upload du template avec le champ active
aws s3 cp "client-config-examples/client_config_template.yaml" s3://vectora-inbox-config-dev/clients/client_config_template.yaml --profile rag-lai-prod --region eu-west-3

# Upload de la config lai_weekly_v3 avec active: true  
aws s3 cp "client-config-examples/lai_weekly_v3.yaml" s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml --profile rag-lai-prod --region eu-west-3
```

## Étape 4: Déploiement du code Lambda

```bash
# Déployer le package ZIP vers la Lambda
aws lambda update-function-code --function-name vectora-inbox-ingest-dev --zip-file fileb://ingest-v2-active-scan.zip --profile rag-lai-prod --region eu-west-3
```

## Étape 5: Tests de validation

### Test 1: Event vide (nouveau comportement)
```bash
aws lambda invoke --function-name vectora-inbox-ingest-dev --payload '{}' --profile rag-lai-prod --region eu-west-3 response_empty.json

# Voir le résultat
type response_empty.json
```

**Résultat attendu :**
```json
{
  "statusCode": 200,
  "body": {
    "clients_discovered": 2,
    "clients_active": 1, 
    "clients_processed": 1,
    "status": "success"
  }
}
```

### Test 2: Event avec client_id (rétrocompatibilité)
```bash
aws lambda invoke --function-name vectora-inbox-ingest-dev --payload '{"client_id": "lai_weekly_v3", "dry_run": true}' --profile rag-lai-prod --region eu-west-3 response_client.json

# Voir le résultat  
type response_client.json
```

**Résultat attendu :**
```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly_v3",
    "status": "success",
    "items_final": 0,
    "dry_run": true
  }
}
```

## Étape 6: Vérification des logs CloudWatch

```bash
# Voir les logs récents
aws logs describe-log-streams --log-group-name /aws/lambda/vectora-inbox-ingest-dev --profile rag-lai-prod --region eu-west-3 --order-by LastEventTime --descending --max-items 1
```

## Validation du succès

✅ **Event vide `{}` accepté** : Plus d'erreur 400  
✅ **Mode multi-clients activé** : Scan des clients actifs  
✅ **Rétrocompatibilité préservée** : Mode single-client fonctionne  
✅ **Logs CloudWatch** : Exécution visible dans les logs  

## En cas de problème

### Erreur "Function not found"
Vérifier le nom exact :
```bash
aws lambda list-functions --profile rag-lai-prod --region eu-west-3 | grep vectora-inbox
```

### Erreur S3 "Access Denied"
Vérifier les buckets :
```bash
aws s3 ls --profile rag-lai-prod --region eu-west-3 | grep vectora-inbox
```

### Package trop volumineux
Le package fait 0.1 MB, bien en dessous de la limite AWS de 50 MB.

## Fichiers créés lors de l'implémentation

- ✅ Package : `ingest-v2-active-scan.zip` (0.1 MB)
- ✅ Tests : `tests/integration/test_ingest_v2_active_scan.py`
- ✅ Rapport : `docs/reports/ingest_v2_active_scan_implementation_report.md`
- ✅ Scripts : `scripts/package_ingest_v2_active_scan.py`

## Modifications apportées

**Code modifié :**
- `src_v2/vectora_core/shared/config_loader.py` (+3 fonctions scan)
- `src_v2/vectora_core/shared/s3_io.py` (+1 fonction list S3)
- `src_v2/vectora_core/ingest/__init__.py` (+1 fonction multi-clients)
- `src_v2/lambdas/ingest/handler.py` (routage intelligent)

**Configuration :**
- `client-config-examples/client_config_template.yaml` (+champ active)
- `client-config-examples/lai_weekly_v3.yaml` (+active: true)

Le déploiement implémente le **modèle d'activation cible** avec support complet de l'event vide `{}` et scan automatique des clients actifs.