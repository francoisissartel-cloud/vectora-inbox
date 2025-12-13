# Vectora Inbox - Plan de déploiement AWS DEV pour period_days v2

**Date :** 2024-12-19  
**Objectif :** Déployer la nouvelle logique de résolution de period_days sur AWS DEV

## 🎯 Vue d'ensemble

Déploiement de la fonctionnalité de configuration de fenêtre temporelle au niveau client, avec hiérarchie de priorité :
1. Payload Lambda (`period_days`)
2. Configuration client (`pipeline.default_period_days`)
3. Fallback global (7 jours)

## 📋 Plan de déploiement par phases

### Phase A : Sync des configurations vers S3

**Objectif :** Mettre à jour les configurations client sur S3 avec la nouvelle section `pipeline`

**Actions :**
1. Sync du canonical (pas de changement, mais pour cohérence)
2. Sync des client-config-examples vers S3 (clients/)
3. Vérification que lai_weekly_v2.yaml contient `pipeline.default_period_days: 30`

**Commandes :**
```powershell
# Sync canonical
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod --region eu-west-3

# Sync client configs
aws s3 sync client-config-examples/ s3://vectora-inbox-config-dev/clients/ --profile rag-lai-prod --region eu-west-3
```

**Validation :**
- Vérifier que `s3://vectora-inbox-config-dev/clients/lai_weekly_v2.yaml` contient la section pipeline
- Vérifier que `s3://vectora-inbox-config-dev/clients/client_template_v2.yaml` est à jour

### Phase B : Re-package et update des Lambdas

**Objectif :** Mettre à jour le code des Lambdas avec la nouvelle logique de résolution

**Lambdas concernées :**
- `vectora-inbox-engine-dev` (utilise period_days pour le calcul de fenêtre)
- `vectora-inbox-ingest-normalize-dev` (pour cohérence future, même si pas utilisé actuellement)

**Actions :**
1. Package des Lambdas avec le nouveau code vectora_core
2. Update des fonctions Lambda sur AWS
3. Vérification des variables d'environnement

**Commandes :**
```powershell
# Package engine
.\scripts\package-engine.ps1

# Package ingest-normalize
.\scripts\package-ingest-normalize.ps1

# Update engine
aws lambda update-function-code --function-name vectora-inbox-engine-dev --zip-file fileb://engine-v2.zip --profile rag-lai-prod --region eu-west-3

# Update ingest-normalize
aws lambda update-function-code --function-name vectora-inbox-ingest-normalize-dev --zip-file fileb://ingest-normalize-v2.zip --profile rag-lai-prod --region eu-west-3
```

**Validation :**
- Vérifier que les Lambdas sont mises à jour (LastModified récent)
- Vérifier les logs CloudWatch pour absence d'erreurs de démarrage

### Phase C : Tests end-to-end

**Objectif :** Valider le comportement sur lai_weekly_v2 avec les deux modes

**Tests à effectuer :**
1. **Test configuration client :** Payload sans `period_days` → doit utiliser 30 jours
2. **Test override :** Payload avec `period_days: 7` → doit utiliser 7 jours
3. **Test compatibilité :** Ancien client sans config → doit utiliser 7 jours (fallback)

**Script de test :**
```powershell
.\scripts\test-period-days-v2-dev.ps1
```

**Métriques de validation :**
- Durée de la fenêtre temporelle dans les logs
- Nombre d'items collectés (cohérent avec la fenêtre)
- Absence d'erreurs dans les logs CloudWatch

## 🔧 Détails techniques

### Fichiers modifiés
- `src/vectora_core/__init__.py` : Logique de résolution dans `run_engine_for_client()`
- `src/vectora_core/utils/config_utils.py` : Nouvelle fonction `resolve_period_days()`
- `client-config-examples/lai_weekly_v2.yaml` : Section `pipeline` avec 30 jours
- `client-config-examples/client_template_v2.yaml` : Section `pipeline` avec 7 jours

### Variables d'environnement (inchangées)
- `CONFIG_BUCKET=vectora-inbox-config-dev`
- `DATA_BUCKET=vectora-inbox-data-dev`
- `NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev`
- `BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0`

### Buckets S3 utilisés
- `vectora-inbox-config-dev` : Configurations canonical + client
- `vectora-inbox-data-dev` : Items normalisés
- `vectora-inbox-newsletters-dev` : Newsletters générées
- `vectora-inbox-lambda-code-dev` : Code des Lambdas

## ⚠️ Risques et mitigations

### Risque 1 : Régression sur clients existants
**Mitigation :** Fallback préservé à 7 jours, compatibilité ascendante garantie

### Risque 2 : Configuration client malformée
**Mitigation :** Validation dans `resolve_period_days()`, fallback en cas d'erreur

### Risque 3 : Erreur de packaging Lambda
**Mitigation :** Test local préalable, possibilité de rollback rapide

## 📊 Critères de succès

### Critères fonctionnels
- [ ] lai_weekly_v2 sans `period_days` utilise 30 jours
- [ ] lai_weekly_v2 avec `period_days: 7` utilise 7 jours
- [ ] Clients sans config utilisent 7 jours (fallback)
- [ ] Logs montrent la résolution correcte

### Critères techniques
- [ ] Lambdas déployées sans erreur
- [ ] Configurations S3 synchronisées
- [ ] Temps d'exécution inchangé
- [ ] Pas d'erreurs CloudWatch

## 🚀 Commandes de déploiement

### Script de déploiement complet
```powershell
# Phase A : Sync configurations
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod --region eu-west-3
aws s3 sync client-config-examples/ s3://vectora-inbox-config-dev/clients/ --profile rag-lai-prod --region eu-west-3

# Phase B : Update Lambdas
.\scripts\package-engine.ps1
.\scripts\package-ingest-normalize.ps1
aws lambda update-function-code --function-name vectora-inbox-engine-dev --zip-file fileb://engine-v2.zip --profile rag-lai-prod --region eu-west-3
aws lambda update-function-code --function-name vectora-inbox-ingest-normalize-dev --zip-file fileb://ingest-normalize-v2.zip --profile rag-lai-prod --region eu-west-3

# Phase C : Tests
.\scripts\test-period-days-v2-dev.ps1
```

## 📝 Documentation post-déploiement

Après déploiement, documenter dans :
- `docs/diagnostics/vectora_inbox_period_days_aws_deploy_results.md`
- `docs/diagnostics/vectora_inbox_period_days_aws_end_to_end_results.md`

---

**Prochaine étape :** Exécution du plan de déploiement