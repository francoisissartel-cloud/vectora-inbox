# Plan d'Alignement : Matching Bedrock V2 sur Configuration Normalisation

**Date :** 17 décembre 2025  
**Objectif :** Aligner la partie matching Bedrock de normalize_score_v2 sur la même configuration que la normalisation qui fonctionne déjà  
**Durée estimée :** 1h30  

---

## 🎯 Résumé de l'état actuel

### ✅ Configuration Bedrock normalisation (qui fonctionne)

**Fichier :** `src_v2/vectora_core/normalization/bedrock_client.py`
- **Client utilisé :** `call_bedrock_with_retry()` (API unifiée V2)
- **Modèle par défaut :** Variable d'environnement `BEDROCK_MODEL_ID`
- **Région par défaut :** Variable d'environnement `BEDROCK_REGION` (défaut: `us-east-1`)
- **Retry logic :** Backoff exponentiel + jitter, 3 tentatives max
- **Format requête :** Claude Messages API avec `anthropic_version: bedrock-2023-05-31`
- **Statut :** ✅ Fonctionne en production, 15/15 items normalisés

### 🟡 Configuration Bedrock matching (problématique)

**Fichier :** `src_v2/vectora_core/normalization/bedrock_matcher.py`
- **Client utilisé :** `call_bedrock_with_retry()` (même API que normalisation)
- **Modèle utilisé :** Paramètre `bedrock_model_id` passé depuis handler
- **Région utilisée :** Paramètre `bedrock_region` passé depuis handler
- **Retry logic :** Délègue à `bedrock_client.call_bedrock_with_retry()`
- **Format requête :** Claude Messages API identique à normalisation
- **Statut :** 🟡 0/15 items matchés (erreurs de configuration Bedrock)

### 📊 Différences identifiées

| Aspect | Normalisation (✅ OK) | Matching (🟡 Problème) | Action requise |
|--------|---------------------|------------------------|----------------|
| **Client Bedrock** | `bedrock_client.call_bedrock_with_retry()` | `bedrock_client.call_bedrock_with_retry()` | ✅ Identique |
| **Variables d'env** | `BEDROCK_MODEL_ID`, `BEDROCK_REGION` | Paramètres passés depuis handler | 🔧 Unifier |
| **Modèle utilisé** | `env_vars["BEDROCK_MODEL_ID"]` | `bedrock_model_override` ou paramètre | 🔧 Aligner |
| **Région utilisée** | `env_vars["BEDROCK_REGION"]` | Paramètre `bedrock_region` | 🔧 Aligner |
| **Retry logic** | Intégré dans `call_bedrock_with_retry()` | Délégué à même fonction | ✅ Identique |
| **Format requête** | Messages API standard | Messages API standard | ✅ Identique |

---

## 📋 Plan d'exécution par phases

### Phase 1 – Cadrage technique (15 min)

**Objectif :** Identifier précisément les divergences de configuration entre normalisation et matching

**Actions :**
- Analyser le code de `normalizer.py` pour voir comment il utilise les variables d'environnement Bedrock
- Vérifier comment `bedrock_matcher.py` reçoit ses paramètres Bedrock
- Identifier les variables d'environnement Lambda actuelles (`BEDROCK_MODEL_ID`, `BEDROCK_REGION`)
- Documenter les différences exactes dans la façon dont chaque module accède à la config Bedrock
- Confirmer que les deux utilisent bien la même fonction `call_bedrock_with_retry()`

### Phase 2 – Refactor minimal du matching (30 min)

**Objectif :** Faire que le matching utilise exactement les mêmes variables d'environnement que la normalisation

**Actions :**
- Modifier `bedrock_matcher.py` pour lire directement `os.environ.get('BEDROCK_MODEL_ID')` et `os.environ.get('BEDROCK_REGION')`
- Supprimer les paramètres `bedrock_model_id` et `bedrock_region` de la fonction `match_watch_domains_with_bedrock()`
- Mettre à jour l'appel dans `normalizer.py` pour ne plus passer ces paramètres
- S'assurer que le matching utilise exactement la même logique d'initialisation que `BedrockNormalizationClient`
- Tester que les deux modules lisent les mêmes variables d'environnement

### Phase 3 – Vérification configuration AWS (20 min)

**Objectif :** S'assurer que les variables d'environnement et permissions IAM sont correctes

**Actions :**
- Vérifier les variables d'environnement actuelles de la Lambda `vectora-inbox-normalize-score-v2-dev`
- Confirmer que `BEDROCK_MODEL_ID` utilise un modèle supporté (ex: `anthropic.claude-3-sonnet-20240229-v1:0`)
- Confirmer que `BEDROCK_REGION` est définie (défaut: `us-east-1`)
- Vérifier les permissions IAM du rôle Lambda pour `bedrock:InvokeModel`
- Ajuster si nécessaire pour utiliser le même modèle que la normalisation qui fonctionne

### Phase 4 – Tests locaux (15 min)

**Objectif :** Valider que le matching utilise maintenant la même config que la normalisation

**Actions :**
- Créer un script de test local qui simule l'appel de matching avec les mêmes env vars
- Tester que `bedrock_matcher.py` lit correctement `BEDROCK_MODEL_ID` et `BEDROCK_REGION`
- Vérifier que les deux modules (normalisation et matching) utilisent exactement les mêmes paramètres Bedrock
- Simuler un appel complet de `normalize_items_batch()` avec matching activé
- Confirmer qu'aucune régression n'est introduite dans la normalisation

### Phase 5 – Déploiement AWS (10 min)

**Objectif :** Déployer la Lambda mise à jour avec la configuration alignée

**Actions :**
- Packager et déployer la Lambda `vectora-inbox-normalize-score-v2-dev`
- Utiliser le profil `rag-lai-prod` et la région `eu-west-3`
- Vérifier que les variables d'environnement sont correctement définies
- Confirmer que le déploiement est réussi (Status: Active)
- Valider que la taille du package reste acceptable

### Phase 6 – Tests réels MVP lai_weekly_v3 (15 min)

**Objectif :** Valider que le matching fonctionne maintenant avec la même config que la normalisation

**Actions :**
- Lancer un test réel sur le MVP `lai_weekly_v3` avec 15 items
- Analyser les logs CloudWatch pour confirmer que normalisation ET matching utilisent le même modèle/région
- Vérifier que le taux de matching passe de 0% à >0%
- Mesurer les métriques : items normalisés, items matchés, temps d'exécution, erreurs
- Confirmer qu'il n'y a plus d'erreur de modèle non supporté ou de permissions

### Phase 7 – Synthèse et rapport final (15 min)

**Objectif :** Documenter les résultats et confirmer l'alignement réussi

**Actions :**
- Créer le rapport `bedrock_matching_v2_alignment_report.md`
- Documenter les modifications apportées (code + config)
- Présenter les métriques avant/après (taux de matching, erreurs, temps)
- Confirmer que matching et normalisation utilisent maintenant exactement la même config Bedrock
- Évaluer la robustesse et recommandations pour généralisation à d'autres clients

---

## 🔧 Modifications techniques prévues

### Code à modifier

**1. `src_v2/vectora_core/normalization/bedrock_matcher.py` :**
```python
# AVANT (paramètres passés)
def match_watch_domains_with_bedrock(
    normalized_item, watch_domains, canonical_scopes, 
    bedrock_model_id, bedrock_region="us-east-1"
):

# APRÈS (lecture env vars comme normalisation)
def match_watch_domains_with_bedrock(
    normalized_item, watch_domains, canonical_scopes
):
    bedrock_model_id = os.environ.get('BEDROCK_MODEL_ID')
    bedrock_region = os.environ.get('BEDROCK_REGION', 'us-east-1')
```

**2. `src_v2/vectora_core/normalization/normalizer.py` :**
```python
# AVANT (passage de paramètres)
bedrock_matching_result = match_watch_domains_with_bedrock(
    item_for_matching, watch_domains, canonical_scopes, bedrock_model, bedrock_region
)

# APRÈS (pas de paramètres Bedrock)
bedrock_matching_result = match_watch_domains_with_bedrock(
    item_for_matching, watch_domains, canonical_scopes
)
```

### Variables d'environnement à vérifier

**Lambda `vectora-inbox-normalize-score-v2-dev` :**
- `BEDROCK_MODEL_ID` : Doit utiliser un modèle supporté (ex: `anthropic.claude-3-sonnet-20240229-v1:0`)
- `BEDROCK_REGION` : Doit être `us-east-1` (région par défaut observée dans le code)
- Autres variables inchangées : `CONFIG_BUCKET`, `DATA_BUCKET`, etc.

### Permissions IAM à vérifier

**Rôle :** `vectora-inbox-s0-iam-dev-IngestNormalizeRole-*`
- Action : `bedrock:InvokeModel`
- Ressource : `arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-*`

---

## 📊 Critères de succès

### Critères techniques obligatoires

| Critère | Seuil | Validation |
|---------|-------|------------|
| Déploiement Lambda | Succès | Status: Active |
| Variables d'env alignées | 100% | Même `BEDROCK_MODEL_ID` et `BEDROCK_REGION` |
| Code unifié | 100% | Même fonction `call_bedrock_with_retry()` |
| Aucune régression | 100% | Normalisation fonctionne toujours |

### Critères métier attendus

| Critère | Objectif | Validation |
|---------|----------|------------|
| Taux de matching | > 0% | Au moins 1 item matché sur 15 |
| Erreurs Bedrock | 0 | Plus d'erreur de modèle non supporté |
| Temps d'exécution | < 30s | Pipeline complet acceptable |
| Cohérence config | 100% | Logs montrent même modèle/région |

---

## 🚨 Risques et mitigations

### Risques identifiés

1. **Régression normalisation :** Modification pourrait casser la normalisation qui fonctionne
   - **Mitigation :** Tests locaux avant déploiement, modifications minimales

2. **Variables d'env manquantes :** `BEDROCK_MODEL_ID` ou `BEDROCK_REGION` non définies
   - **Mitigation :** Vérification préalable, valeurs par défaut dans le code

3. **Permissions IAM insuffisantes :** Rôle Lambda sans `bedrock:InvokeModel`
   - **Mitigation :** Vérification et ajustement des permissions si nécessaire

### Plan de rollback

En cas de problème critique :
1. **Rollback code :** Restaurer la version précédente de `bedrock_matcher.py` et `normalizer.py`
2. **Rollback Lambda :** Redéployer la version précédente du package
3. **Validation :** Confirmer que la normalisation fonctionne toujours

---

## 🎯 Résultat attendu

À la fin de ce plan :

✅ **Configuration unifiée :** Matching et normalisation utilisent exactement les mêmes variables d'environnement Bedrock  
✅ **Client unifié :** Les deux utilisent la même fonction `call_bedrock_with_retry()` avec la même logique de retry  
✅ **Modèle aligné :** Le matching utilise le même modèle Bedrock que la normalisation qui fonctionne  
✅ **Région alignée :** Le matching utilise la même région Bedrock que la normalisation  
✅ **Taux de matching amélioré :** Passage de 0% à >0% d'items correctement matchés  
✅ **Robustesse maintenue :** Aucune régression sur la normalisation existante  

**Impact minimal :** Modifications de seulement ~10 lignes de code pour aligner les configurations  
**Conformité hygiene_v4 :** Respect total des règles d'architecture src_v2  
**Généralisation :** Configuration facilement applicable à d'autres clients  

---

**Temps total estimé :** 1h30  
**Complexité :** Faible (alignement de configuration)  
**Impact :** Critique (résolution du matching à 0%)