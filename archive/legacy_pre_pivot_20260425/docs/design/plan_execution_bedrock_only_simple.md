# Plan d'Exécution : Architecture Bedrock-Only Simple

**Date :** 19 décembre 2025  
**Objectif :** Supprimer le matching déterministe, garder seulement Bedrock  
**Statut :** 🚀 EXÉCUTION IMMÉDIATE  
**Conformité :** Règles vectora-inbox-development-rules.md

---

## 🎯 OBJECTIF SIMPLE

**Supprimer physiquement** le matching déterministe qui écrase les résultats Bedrock.

**Modification unique :** Remplacer 10 lignes de logique hybride par 2 lignes simples.

**Résultat attendu :** Taux de matching de 0% → 60-80% en 20 minutes.

---

## 📋 PLAN D'EXÉCUTION (4 PHASES)

### PHASE 1 : LOCALISATION (2 minutes)
- Localiser le fichier `src_v2/vectora_core/normalization/__init__.py`
- Identifier les lignes de logique hybride à supprimer
- Vérifier accès AWS

### PHASE 2 : MODIFICATION (3 minutes)
- Supprimer la logique `if bedrock_only` complète
- Remplacer par `matched_items = normalized_items`
- Supprimer l'import `matcher`

### PHASE 3 : DÉPLOIEMENT (10 minutes)
- Créer package layer vectora_core
- Publier nouvelle version layer
- Mettre à jour Lambda normalize-score-v2-dev

### PHASE 4 : TEST RÉEL (5 minutes)
- Invoquer Lambda avec lai_weekly_v3
- Vérifier logs "Architecture Bedrock-Only Pure"
- Confirmer items_matched > 0

---

## 🔧 MODIFICATION EXACTE

**Fichier :** `src_v2/vectora_core/normalization/__init__.py`

**SUPPRIMER ces lignes (~105-115) :**
```python
# 5. Matching aux domaines de veille (mode Bedrock-only ou hybride)
if client_config.get('matching_config', {}).get('bedrock_only', False):
    # Mode Bedrock-only : utiliser directement les résultats Bedrock
    matched_items = normalized_items
    logger.info("Mode Bedrock-only activé : matching déterministe ignoré")
else:
    # Mode hybride existant (fallback)
    logger.info("Matching déterministe aux domaines de veille...")
    matched_items = matcher.match_items_to_domains(
        normalized_items,
        client_config,
        canonical_scopes
    )
```

**REMPLACER par ces lignes :**
```python
# 5. Architecture Bedrock-Only Pure - Matching déterministe supprimé
matched_items = normalized_items
logger.info("Architecture Bedrock-Only Pure : matching déterministe supprimé")
```

**SUPPRIMER l'import :**
```python
# AVANT
from . import normalizer, matcher, scorer

# APRÈS  
from . import normalizer, scorer
```

---

## ✅ CRITÈRES DE SUCCÈS

### Technique
- [ ] Code modifié (10 lignes → 2 lignes)
- [ ] Import matcher supprimé
- [ ] Layer déployé avec succès
- [ ] Lambda mise à jour

### Fonctionnel
- [ ] Lambda s'exécute (StatusCode: 200)
- [ ] Log "Architecture Bedrock-Only Pure" présent
- [ ] Items matchés > 0 (vs 0 actuellement)
- [ ] Amélioration confirmée

---

## 🚀 EXÉCUTION

**Durée totale estimée :** 20 minutes  
**Risque :** Très faible (simplification)  
**Rollback :** Immédiat si nécessaire

---

*Plan d'Exécution Architecture Bedrock-Only Simple*  
*Date : 19 décembre 2025*  
*Statut : 🚀 PRÊT POUR EXÉCUTION IMMÉDIATE*