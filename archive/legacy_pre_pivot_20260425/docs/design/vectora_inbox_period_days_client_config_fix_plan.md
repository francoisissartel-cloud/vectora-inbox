# Plan Correctif - Period Days Client Config Fix

**Date**: 2024-12-19  
**Environnement**: AWS DEV (eu-west-3)  
**Cause Racine**: La fonction `compute_date_range()` ne connaît pas le `client_config`

## 🎯 Cause Racine Confirmée

**RC1 - Fonction `compute_date_range()` bypasse `resolve_period_days()`**

Le diagnostic local confirme que :
- ✅ Client config `lai_weekly_v2` chargé correctement avec `pipeline.default_period_days: 30`
- ✅ `resolve_period_days(None, client_config)` retourne bien 30
- ❌ `compute_date_range(None, None, None)` utilise fallback 7 jours (2025-12-03 → 2025-12-10)
- ✅ `compute_date_range(30, None, None)` utilise 30 jours (2025-11-10 → 2025-12-10)

**Problème** : Dans `run_engine_for_client()`, l'appel direct à `compute_date_range(period_days, from_date, to_date)` bypasse complètement la logique de résolution de priorité.

## 🛠️ Solution Technique

### Modification Requise

**Fichier** : `src/vectora_core/__init__.py`  
**Fonction** : `run_engine_for_client()`  
**Ligne** : ~220

**Code Actuel (Problématique)** :
```python
# Étape 2 : Calculer la fenêtre temporelle et collecter les items normalisés
logger.info("Calcul de la fenêtre temporelle")
from_date_calc, to_date_calc = date_utils.compute_date_range(period_days, from_date, to_date)
```

**Code Corrigé** :
```python
# Étape 2 : Calculer la fenêtre temporelle et collecter les items normalisés
logger.info("Calcul de la fenêtre temporelle")

# Résoudre period_days selon la hiérarchie de priorité
from vectora_core.utils.config_utils import resolve_period_days
resolved_period_days = resolve_period_days(period_days, client_config)
logger.info(f"Period days résolu : {resolved_period_days} (payload: {period_days})")

# Calculer la fenêtre temporelle avec la valeur résolue
from_date_calc, to_date_calc = date_utils.compute_date_range(resolved_period_days, from_date, to_date)
```

### Hiérarchie de Priorité Respectée

1. **Payload Lambda** (`period_days` != None) → Utilise la valeur du payload
2. **Client Config** (`client_config.pipeline.default_period_days`) → Utilise 30 pour lai_weekly_v2
3. **Fallback Global** (7 jours) → Utilisé si aucune config

## 📋 Plan d'Implémentation

### Phase 1 - Correction Locale

1. ✅ **Diagnostic confirmé** - Cause racine identifiée
2. 🔧 **Modifier `src/vectora_core/__init__.py`** - Intégrer `resolve_period_days()`
3. 🧪 **Test local** - Vérifier que la correction fonctionne
4. 📝 **Supprimer l'instrumentation temporaire** - Nettoyer les logs DEBUG

### Phase 2 - Déploiement AWS DEV

1. 📦 **Package Lambda** - Créer le package avec la correction
2. 🚀 **Déployer** - Mettre à jour `vectora-inbox-engine-dev`
3. ✅ **Test AWS** - Invoquer avec `{"client_id": "lai_weekly_v2"}`
4. 📊 **Validation** - Vérifier les logs CloudWatch

### Phase 3 - Tests de Validation

1. **Test sans override** : `{"client_id": "lai_weekly_v2"}` → Doit utiliser 30 jours
2. **Test avec override** : `{"client_id": "lai_weekly_v2", "period_days": 7}` → Doit utiliser 7 jours
3. **Test client sans pipeline** : Vérifier fallback 7 jours pour autres clients

## 🔍 Critères de Validation

### Logs Attendus (CloudWatch)

Pour `{"client_id": "lai_weekly_v2"}` :
```
[INFO] Client config chargé : LAI Intelligence Weekly
[INFO] Pipeline config : {'default_period_days': 30, 'notes': '...'}
[INFO] Period days résolu : 30 (payload: None)
[INFO] Fenêtre temporelle calculée (30 jours) : 2025-11-10 → 2025-12-10
```

Pour `{"client_id": "lai_weekly_v2", "period_days": 7}` :
```
[INFO] Period days résolu : 7 (payload: 7)
[INFO] Fenêtre temporelle calculée (7 jours) : 2025-12-03 → 2025-12-10
```

### Métriques de Succès

- ✅ `lai_weekly_v2` sans payload → Fenêtre de 30 jours
- ✅ `lai_weekly_v2` avec `period_days: 7` → Fenêtre de 7 jours (override)
- ✅ Autres clients sans section pipeline → Fenêtre de 7 jours (fallback)
- ✅ Compatibilité ascendante maintenue

## 📁 Fichiers Impactés

1. **`src/vectora_core/__init__.py`** - Modification principale
2. **`client-config-examples/lai_weekly_v2.yaml`** - Déjà mis à jour avec section pipeline
3. **Scripts de déploiement** - Réutiliser l'infrastructure existante

## 🚀 Déploiement

**Commande** :
```bash
# Package et déploiement
powershell scripts/package-engine.ps1
aws lambda update-function-code --function-name vectora-inbox-engine-dev --zip-file fileb://engine-fixed.zip --profile rag-lai-prod --region eu-west-3

# Test
aws lambda invoke --function-name vectora-inbox-engine-dev --payload '{"client_id": "lai_weekly_v2"}' response.json
```

---

**Status** : Plan défini - Prêt pour implémentation  
**Prochaine étape** : Phase 1 - Correction locale