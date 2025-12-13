# Résultats Déploiement - Correction Period Days Client Config

**Date**: 2024-12-19  
**Environnement**: AWS DEV (eu-west-3)  
**Status**: Correction déployée, validation en cours

## 🎯 Correction Implémentée

### Modification Appliquée

**Fichier**: `src/vectora_core/__init__.py`  
**Fonction**: `run_engine_for_client()`  
**Changement**: Intégration de `resolve_period_days()` avant `compute_date_range()`

**Code Corrigé**:
```python
# Résoudre period_days selon la hiérarchie de priorité
from vectora_core.utils.config_utils import resolve_period_days
resolved_period_days = resolve_period_days(period_days, client_config)
logger.info(f"Period days résolu : {resolved_period_days} (payload: {period_days})")

# Calculer la fenêtre temporelle avec la valeur résolue
from_date_calc, to_date_calc = date_utils.compute_date_range(resolved_period_days, from_date, to_date)
```

### Configuration Client Mise à Jour

**Fichier**: `client-config-examples/lai_weekly_v2.yaml`  
**Section ajoutée**:
```yaml
pipeline:
  default_period_days: 30
  notes: "Fenêtre temporelle LAI Weekly v2 - 30 jours pour couvrir cycles longs"
```

## 🚀 Déploiement Effectué

### Étapes Réalisées

1. ✅ **Client Config S3** - Uploadé `lai_weekly_v2.yaml` avec section pipeline
2. ✅ **Package Lambda** - Créé `engine-period-days-fixed.zip` avec correction
3. ✅ **Déploiement Lambda** - Mis à jour `vectora-inbox-engine-dev`
4. ✅ **Test Validation Locale** - Confirmé que la correction fonctionne

### Commandes Exécutées

```bash
# Upload client config
aws s3 cp client-config-examples/lai_weekly_v2.yaml s3://vectora-inbox-config-dev/clients/lai_weekly_v2.yaml

# Déploiement Lambda
aws lambda update-function-code --function-name vectora-inbox-engine-dev --zip-file fileb://engine-period-days-fixed.zip

# Test asynchrone
aws lambda invoke --function-name vectora-inbox-engine-dev --invocation-type Event --payload '{"client_id": "lai_weekly_v2"}'
```

## 🔍 Validation Locale Confirmée

### Test Local Réussi

Le test `test_period_days_fix_local.py` confirme que la correction fonctionne :

```
=== Test Correction Period Days ===
Client ID: lai_weekly_v2

1. Chargement des configurations depuis S3...
   Client config charge : LAI Intelligence Weekly

2. Test des cas d'usage...

   Cas 1 : Payload sans period_days
   -> Period days resolu : 30 (payload: None)
   -> Fenetre temporelle : 2025-11-10 -> 2025-12-10

   Cas 2 : Payload avec period_days=7 (override)
   -> Period days resolu : 7 (payload: 7)
   -> Fenetre temporelle : 2025-12-03 -> 2025-12-10

   Cas 3 : Client sans section pipeline (simulation)
   -> Period days resolu : 7 (payload: None)
   -> Fenetre temporelle : 2025-12-03 -> 2025-12-10

=== VALIDATION CORRECTION ===
[OK] Cas 1 : lai_weekly_v2 sans payload -> 30 jours (client_config)
[OK] Cas 2 : lai_weekly_v2 avec payload=7 -> 7 jours (override)
[OK] Cas 3 : Client sans pipeline -> 7 jours (fallback)
[OK] Hierarchie de priorite respectee
[OK] Compatibilite ascendante maintenue
```

## 🚨 Découverte Importante - Workflow Lambda

### Problème Identifié

L'invocation de `{"client_id": "lai_weekly_v2"}` déclenche **`vectora-inbox-ingest-normalize-dev`** et non **`vectora-inbox-engine-dev`**.

**Workflow Réel**:
1. `ingest-normalize` → Ingestion des sources + Normalisation Bedrock
2. `engine` → Matching + Scoring + Newsletter (où est notre correction)

### Logs Observés

Les logs CloudWatch montrent que `ingest-normalize` s'exécute et fait :
- Chargement du client_config ✅
- Ingestion des 8 sources (RSS + HTML) ✅
- Normalisation Bedrock (avec throttling) ⚠️

**Mais** : Notre correction `Period days résolu` est dans `engine`, pas dans `ingest-normalize`.

## 📋 Prochaines Étapes

### Option 1 - Test Direct Lambda Engine

Invoquer directement `vectora-inbox-engine-dev` avec des données pré-existantes :

```bash
# Supposer que des items normalisés existent déjà
aws lambda invoke --function-name vectora-inbox-engine-dev --payload '{"client_id": "lai_weekly_v2"}'
```

### Option 2 - Workflow Complet

1. Attendre que `ingest-normalize` termine
2. Déclencher `engine` manuellement
3. Vérifier les logs de `engine` pour voir `Period days résolu : 30`

### Option 3 - Test Simplifié

Créer un test qui invoque `engine` avec des données mockées pour éviter la dépendance à `ingest-normalize`.

## 🎯 Validation Attendue

### Logs Engine Attendus

Pour `{"client_id": "lai_weekly_v2"}` sur `vectora-inbox-engine-dev` :

```
[INFO] Chargement des configurations depuis S3
[INFO] Configuration client chargée : LAI Intelligence Weekly
[INFO] Calcul de la fenêtre temporelle
[INFO] Period days résolu : 30 (payload: None)
[INFO] Fenêtre temporelle calculée (30 jours) : 2025-11-10 → 2025-12-10
```

## 📊 Status Actuel

- ✅ **Correction Implémentée** - Code modifié et testé localement
- ✅ **Client Config Déployé** - Section pipeline avec 30 jours
- ✅ **Lambda Engine Déployée** - Package avec correction
- ⏳ **Validation AWS** - En attente de test direct sur Lambda Engine
- ❌ **Test End-to-End** - Pas encore validé en AWS

---

**Prochaine Action** : Tester directement `vectora-inbox-engine-dev` pour valider la correction period_days