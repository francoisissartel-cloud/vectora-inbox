# Scripts de Promotion Multi-Environnements

Scripts pour promouvoir code et configurations entre environnements.

## 📋 Scripts Disponibles

### promote_dev_to_stage_simple.ps1 (Windows)

Script PowerShell pour promouvoir dev → stage.

**Usage**:
```powershell
.\scripts\deploy\promote_dev_to_stage_simple.ps1 [client_id]
```

**Exemple**:
```powershell
.\scripts\deploy\promote_dev_to_stage_simple.ps1 lai_weekly
```

### promote_dev_to_stage_simple.sh (Linux/Mac)

Script Bash pour promouvoir dev → stage.

**Usage**:
```bash
./scripts/deploy/promote_dev_to_stage_simple.sh [client_id]
```

**Exemple**:
```bash
./scripts/deploy/promote_dev_to_stage_simple.sh lai_weekly
```

## 🔄 Workflow Promotion

Le script effectue les étapes suivantes :

1. **Snapshot pré-promotion** (optionnel)
   - Crée un snapshot de l'environnement source
   - Nom: `pre_promotion_YYYYMMDD_HHMMSS`

2. **Copie code Lambda**
   - Synchronise `s3://vectora-inbox-lambda-code-dev/` → `s3://vectora-inbox-lambda-code-stage/`
   - Inclut layers et packages Lambda

3. **Update Lambdas**
   - Met à jour le code des Lambdas stage
   - Lambdas: `ingest-v2-stage`, `normalize-score-v2-stage`

4. **Copie configurations**
   - Synchronise canonical dev → stage
   - Copie config client spécifiée

5. **Tests E2E** (optionnel)
   - Teste les Lambdas stage avec le client

## ⚙️ Configuration

### Prérequis

- AWS CLI configuré avec profil `rag-lai-prod`
- Accès compte AWS 786469175371
- Environnements dev et stage déjà créés

### Variables

- `ENV_SOURCE`: Environnement source (défaut: `dev`)
- `ENV_TARGET`: Environnement cible (défaut: `stage`)
- `CLIENT_ID`: ID client à promouvoir (défaut: `lai_weekly`)

## 📝 Exemples

### Promotion Standard

```powershell
# Promouvoir lai_weekly de dev vers stage
.\scripts\deploy\promote_dev_to_stage_simple.ps1 lai_weekly
```

### Promotion Autre Client

```powershell
# Promouvoir autre client
.\scripts\deploy\promote_dev_to_stage_simple.ps1 autre_client
```

## ✅ Validation

Après promotion, vérifier :

1. **Code Lambda mis à jour**
   ```bash
   aws lambda get-function --function-name vectora-inbox-ingest-v2-stage \
     --profile rag-lai-prod --region eu-west-3 \
     --query 'Configuration.LastModified'
   ```

2. **Configurations copiées**
   ```bash
   aws s3 ls s3://vectora-inbox-config-stage/clients/ \
     --profile rag-lai-prod --region eu-west-3
   ```

3. **Tests E2E**
   ```bash
   python scripts/invoke/invoke_ingest_v2.py --env stage --client-id lai_weekly
   ```

## 🔙 Rollback

En cas de problème, restaurer depuis snapshot :

```bash
python scripts/maintenance/rollback_snapshot.py --snapshot "pre_promotion_YYYYMMDD"
```

## 📊 Logs

Les logs de promotion sont affichés en temps réel :
- Cyan: Informations générales
- Yellow: Étapes en cours
- Green: Succès
- Gray: Détails

## ⚠️ Notes Importantes

- **Snapshot**: Ligne commentée par défaut, décommenter si nécessaire
- **Tests E2E**: Ligne commentée par défaut, décommenter pour tester automatiquement
- **Durée**: ~2-3 minutes pour promotion complète
- **Idempotent**: Peut être exécuté plusieurs fois sans problème

## 🎯 Prochaines Étapes

Pour créer script promotion stage → prod :
1. Dupliquer `promote_dev_to_stage_simple.ps1`
2. Renommer en `promote_stage_to_prod_simple.ps1`
3. Modifier `ENV_SOURCE="stage"` et `ENV_TARGET="prod"`

---

**Scripts créés le**: 2026-01-30  
**Version**: 1.0.0  
**Statut**: ✅ Testé et validé
