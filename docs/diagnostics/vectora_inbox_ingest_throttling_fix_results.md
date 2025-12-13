# Diagnostic Throttling Bedrock : ingest-normalize (DEV)

**Date :** 2024-12-19  
**Objectif :** Réduire les ThrottlingException lors de la normalisation en DEV  

## B1 - Diagnostic Throttling en DEV

### B1.1 - Analyse logs CloudWatch ✅

**Dernière exécution lai_weekly_v2 (2025-12-11 09:47-09:50) :**
- 📊 **Volume d'items** : 104 items à normaliser
- ⚠️ **ThrottlingException** : Nombreuses occurrences
  - Pattern répétitif : tentative 1/4 → retry → tentative 2/4 → retry...
  - Plusieurs échecs après 4 tentatives complètes
  - Messages : "Too many requests, please wait before trying again"
- ⏱️ **Durée totale** : 485 secondes (8 minutes 5 secondes)
- 🔄 **Retries effectués** : Centaines de retries avec backoff exponentiel

### B1.2 - Vérification code Lambda dev ✅

**Analyse `src/vectora_core/normalization/normalizer.py` :**
- ⚠️ **MAX_BEDROCK_WORKERS** : `4` (problème identifié)
- ✅ **Retry/backoff** : Implémenté dans `bedrock_client.py`
  - `max_retries = 3` (4 tentatives total)
  - Backoff exponentiel : `base_delay * (2 ** attempt) + jitter`
- ✅ **Chunking** : Via `ThreadPoolExecutor` avec `max_workers=MAX_BEDROCK_WORKERS`

**Analyse `src/vectora_core/normalization/bedrock_client.py` :**
- ✅ Gestion ThrottlingException correcte
- ✅ Retry automatique avec délais croissants
- ✅ Logging détaillé des tentatives

### B1.3 - Vérification configuration Lambda AWS ✅

**Configuration actuelle :**
- ✅ **Fonction** : `vectora-inbox-ingest-normalize-dev`
- ⚠️ **ReservedConcurrentExecutions** : NON CONFIGURÉ
- 📊 **Limites compte** : 10 exécutions concurrentes total
- ✅ **Environnement** : `ENV=dev` confirmé

**Contrainte identifiée :**
- Impossible de configurer ReservedConcurrentExecutions=1 
- Raison : compte limité à 10 exécutions total, minimum 10 non-réservées requis

## B2 - Corrections P0 sur parallélisation & volume

### B2.1 - Forcer MAX_BEDROCK_WORKERS=1 en DEV ✅

**Correction appliquée :**
```python
# Avant
MAX_BEDROCK_WORKERS = 4

# Après  
import os
MAX_BEDROCK_WORKERS = 1 if os.environ.get('ENV') == 'dev' else 4
```

**Impact :**
- ✅ DEV : 1 seul appel Bedrock simultané
- ✅ PROD : 4 appels simultanés (inchangé)
- ✅ Réduction drastique attendue des ThrottlingException

### B2.2 - ReservedConcurrentExecutions ⚠️

**Tentative de configuration :**
- ❌ `aws lambda put-function-concurrency --reserved-concurrent-executions 1`
- **Erreur** : "decreases account's UnreservedConcurrentExecution below its minimum value of [10]"
- **Conclusion** : Impossible avec les limites actuelles du compte

### B2.3 - Limite volume items (optionnel DEV) 

**Analyse du besoin :**
- 📊 Volume actuel : 104 items lai_weekly_v2 (acceptable)
- ⏱️ Avec 1 worker : durée estimée ~3-4 minutes (vs 8+ actuellement)
- 💡 **Décision** : Pas de limite volume nécessaire pour l'instant

**Implémentation future si besoin :**
```python
# Dans normalize_items_batch()
if os.environ.get('ENV') == 'dev' and len(raw_items) > 60:
    logger.warning(f"DEV: Limitation à 60 items (sur {len(raw_items)})")
    raw_items = raw_items[:60]
```

### B2.4 - Documentation corrections B2 ✅

**Résumé corrections appliquées :**
- ✅ **MAX_BEDROCK_WORKERS** : 4 → 1 en DEV
- ❌ **ReservedConcurrentExecutions** : Impossible (limites compte)
- ⏸️ **Limite volume** : Non nécessaire pour l'instant
- ⚠️ **Redéploiement** : Requis pour appliquer les changements

**Status B2 :** Corrections code terminées, redéploiement en attente