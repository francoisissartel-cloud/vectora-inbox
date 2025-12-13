# Diagnostic - Period Days Client Config AWS Root Cause

**Date**: 2024-12-19  
**Environnement**: AWS DEV (eu-west-3)  
**Client concerné**: lai_weekly_v2  
**Problème**: La valeur `default_period_days: 30` du client_config n'est pas utilisée en AWS DEV

## 🔍 Analyse du Code Actuel

### Architecture de Résolution Period Days

La hiérarchie de priorité implémentée dans `src/vectora_core/utils/config_utils.py::resolve_period_days()` :

1. **Payload Lambda** (`event["period_days"]`) - Priorité absolue
2. **Client Config** (`client_config.pipeline.default_period_days`) - Priorité intermédiaire  
3. **Fallback Global** (7 jours) - Fallback

### Flux d'Exécution Actuel

#### 1. Handler Lambda Engine
- **Fichier**: `src/lambdas/engine/handler.py`
- **Fonction**: `lambda_handler(event, context)`
- **Extraction**: `period_days = event.get("period_days")` (peut être None)
- **Transmission**: Passe `period_days` à `run_engine_for_client()`

#### 2. Fonction de Haut Niveau
- **Fichier**: `src/vectora_core/__init__.py`
- **Fonction**: `run_engine_for_client()`
- **Chargement Config**: `client_config = loader.load_client_config(client_id, config_bucket)`
- **Calcul Fenêtre**: `from_date_calc, to_date_calc = date_utils.compute_date_range(period_days, from_date, to_date)`

#### 3. Calcul de la Fenêtre Temporelle
- **Fichier**: `src/vectora_core/utils/date_utils.py`
- **Fonction**: `compute_date_range(period_days, from_date, to_date)`
- **⚠️ PROBLÈME IDENTIFIÉ**: Cette fonction ne reçoit PAS le `client_config` !

### 🚨 Cause Racine Identifiée

**RC1 - Fonction `compute_date_range()` ne connaît pas le client_config**

La fonction `date_utils.compute_date_range()` ne reçoit que le paramètre `period_days` du payload, mais n'a aucun accès au `client_config` pour lire `pipeline.default_period_days`.

**Code actuel problématique** dans `src/vectora_core/__init__.py::run_engine_for_client()` :
```python
# Étape 2 : Calculer la fenêtre temporelle et collecter les items normalisés
logger.info("Calcul de la fenêtre temporelle")
from_date_calc, to_date_calc = date_utils.compute_date_range(period_days, from_date, to_date)
```

La fonction `compute_date_range()` ne peut donc pas appliquer la hiérarchie de priorité car elle ne connaît que `period_days` (payload) et utilise un fallback de 7 jours.

## 🔧 Hypothèses à Vérifier

### H1 - Client Config Chargement Correct
- ✅ Le client_config `lai_weekly_v2` est-il correctement chargé depuis S3 ?
- ✅ La section `pipeline.default_period_days: 30` est-elle présente ?
- ✅ Le bucket et la clé S3 sont-ils corrects ?

### H2 - Fonction resolve_period_days Non Utilisée
- ❌ La fonction `config_utils.resolve_period_days()` existe mais n'est jamais appelée
- ❌ Le calcul de fenêtre temporelle bypasse complètement cette logique

### H3 - Différence Local vs AWS
- En local : tests unitaires peuvent mocker ou passer directement les bonnes valeurs
- En AWS : le flux réel passe par `date_utils.compute_date_range()` qui ignore le client_config

## 📋 Plan de Diagnostic AWS

### Étape 1 - Instrumentation Temporaire

Ajouter des logs de debug dans `run_engine_for_client()` pour capturer :

```python
# Après chargement du client_config
logger.info(f"DEBUG - Client config chargé : {client_config.get('client_profile', {}).get('name')}")
logger.info(f"DEBUG - Pipeline config : {client_config.get('pipeline', {})}")

# Avant calcul de fenêtre
logger.info(f"DEBUG - period_days du payload : {period_days}")
logger.info(f"DEBUG - from_date du payload : {from_date}")
logger.info(f"DEBUG - to_date du payload : {to_date}")

# Test de resolve_period_days
from vectora_core.utils.config_utils import resolve_period_days
resolved_period = resolve_period_days(period_days, client_config)
logger.info(f"DEBUG - resolve_period_days() retourne : {resolved_period}")
```

### Étape 2 - Test AWS DEV

Invoquer `vectora-inbox-engine-dev` avec :
```json
{"client_id": "lai_weekly_v2"}
```

### Étape 3 - Analyse CloudWatch Logs

Rechercher les logs DEBUG pour confirmer :
- Le client_config est bien chargé avec `pipeline.default_period_days: 30`
- `resolve_period_days()` retourne bien 30
- Mais `compute_date_range()` utilise le fallback 7 jours

## 🎯 Solution Attendue

**Modifier `run_engine_for_client()`** pour utiliser `resolve_period_days()` avant d'appeler `compute_date_range()` :

```python
# Résoudre period_days selon la hiérarchie de priorité
from vectora_core.utils.config_utils import resolve_period_days
resolved_period_days = resolve_period_days(period_days, client_config)

# Calculer la fenêtre temporelle avec la valeur résolue
from_date_calc, to_date_calc = date_utils.compute_date_range(resolved_period_days, from_date, to_date)
```

## 📊 Validation Attendue

Après correction, pour `{"client_id": "lai_weekly_v2"}` :
- ✅ `resolve_period_days(None, client_config)` → 30
- ✅ `compute_date_range(30, None, None)` → fenêtre de 30 jours
- ✅ Logs montrent "Fenêtre temporelle calculée (30 jours)"

---

**Status**: Diagnostic initial - Cause racine identifiée  
**Prochaine étape**: Instrumentation et validation AWS DEV