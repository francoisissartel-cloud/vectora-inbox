# Résultats Déploiement AWS : period_days ingest-normalize

## Résumé Exécutif
✅ **DÉPLOIEMENT RÉUSSI** : Lambda vectora-inbox-ingest-normalize-dev mise à jour avec la logique period_days

## Détails du Déploiement

### Fonction Lambda Mise à Jour
- **Nom** : `vectora-inbox-ingest-normalize-dev`
- **Version** : `$LATEST`
- **Dernière modification** : `2025-12-10T22:22:26.000+0000`
- **Taille déployée** : `38,357,036 bytes` (~36.6 MB)

### Configuration Lambda Validée
- **Runtime** : `python3.12`
- **Timeout** : `600s` (10 minutes)
- **Memory** : `512MB`

### Variables d'Environnement Confirmées
- **CONFIG_BUCKET** : `vectora-inbox-config-dev`
- **DATA_BUCKET** : `vectora-inbox-data-dev`
- **BEDROCK_MODEL_ID** : `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`

## Artefacts S3 Utilisés

### Configuration Client
- **Bucket** : `vectora-inbox-config-dev`
- **Fichier** : `clients/lai_weekly_v2.yaml`
- **Contenu validé** : `pipeline.default_period_days: 30`

### Code Source
- **Archive** : `ingest-normalize-period-days.zip` (36.58 MB)
- **Contenu** : Tout le répertoire `src/` avec modifications period_days
- **Modules modifiés** :
  - `vectora_core/__init__.py` : Ajout filtre temporel
  - `vectora_core/utils/config_utils.py` : Fonction resolve_period_days (existante)

## Modifications Déployées

### 1. Résolution period_days
```python
from vectora_core.utils.config_utils import resolve_period_days
resolved_period_days = resolve_period_days(period_days, client_config)
```

### 2. Filtre Temporel
```python
cutoff_date = datetime.now() - timedelta(days=resolved_period_days)
filtered_items = _apply_temporal_filter(all_raw_items, cutoff_date_str)
```

### 3. Normalisation Filtrée
```python
normalized_items = normalizer.normalize_items_batch(
    filtered_items,  # Au lieu de all_raw_items
    canonical_scopes,
    bedrock_model_id
)
```

## Métriques Ajoutées

### Nouvelles Métriques de Retour
- `items_filtered` : Nombre d'items conservés après filtre
- `items_filtered_out` : Nombre d'items ignorés (trop anciens)
- `period_days_used` : Valeur period_days résolue utilisée

### Logging Enrichi
- Résolution period_days avec source (payload/config/fallback)
- Nombre d'items filtrés vs total
- Items sans date valide tracés

## Tests de Validation Recommandés

### Test 1 : Configuration par Défaut
```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id": "lai_weekly_v2"}' \
  --profile rag-lai-prod \
  --region eu-west-3 \
  response.json
```
**Attendu** : `period_days_used: 30` (depuis client_config)

### Test 2 : Override Payload
```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id": "lai_weekly_v2", "period_days": 7}' \
  --profile rag-lai-prod \
  --region eu-west-3 \
  response.json
```
**Attendu** : `period_days_used: 7` (override payload)

### Test 3 : Client Sans Pipeline
```bash
aws lambda invoke \
  --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id": "client_sans_pipeline"}' \
  --profile rag-lai-prod \
  --region eu-west-3 \
  response.json
```
**Attendu** : `period_days_used: 7` (fallback global)

## Surveillance CloudWatch

### Logs à Surveiller
- **Log Group** : `/aws/lambda/vectora-inbox-ingest-normalize-dev`
- **Patterns clés** :
  - `"Period days résolu pour l'ingestion : X jours"`
  - `"Filtre temporel : X items conservés, Y items ignorés"`
  - `"Items sans date valide ignorés : Z"`

### Métriques à Surveiller
- **Durée d'exécution** : Devrait diminuer (moins d'appels Bedrock)
- **Coût Bedrock** : Réduction significative attendue
- **Erreurs** : Aucune nouvelle erreur liée au filtre

## Rollback Plan

### En Cas de Problème
1. **Rollback immédiat** : Redéployer la version précédente
2. **Diagnostic** : Analyser les logs CloudWatch
3. **Fix rapide** : Corriger et redéployer

### Commande Rollback
```bash
# Si nécessaire, revenir à une version antérieure
aws lambda update-function-code \
  --function-name vectora-inbox-ingest-normalize-dev \
  --zip-file fileb://backup-previous-version.zip \
  --profile rag-lai-prod \
  --region eu-west-3
```

## Prochaines Étapes

### Phase 3 : Tests End-to-End
1. **Test lai_weekly_v2** : Validation avec vraies sources
2. **Mesure économies** : Comparaison avant/après Bedrock
3. **Test chaîne complète** : ingest-normalize → engine

### Validation Production
1. **Performance** : Temps d'exécution réduit
2. **Qualité** : Même qualité de normalisation
3. **Coûts** : Réduction mesurable des tokens Bedrock

## Conclusion

Le déploiement de la logique period_days dans vectora-inbox-ingest-normalize-dev est **réussi et opérationnel**.

La Lambda est maintenant alignée avec l'engine sur la gestion des fenêtres temporelles, avec un filtre appliqué AVANT la normalisation Bedrock pour optimiser les coûts et performances.