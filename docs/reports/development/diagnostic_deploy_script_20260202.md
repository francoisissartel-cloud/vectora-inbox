# Diagnostic: Script Deploy et Mise à Jour des Layers

**Date**: 2026-02-02  
**Contexte**: Phase 6ter - Comprendre pourquoi deploy_env.py ne met pas à jour les Lambdas  
**Statut**: ✅ Diagnostic complet

---

## 🔍 Problème Identifié

**Symptôme**: Après `python scripts/deploy/deploy_env.py --env dev`, les Lambdas utilisent encore les anciens layers.

**Exemple**:
- Layer v49 publié ✅
- Lambda utilise encore layer v43 ❌
- Nécessité de mise à jour manuelle avec `aws lambda update-function-configuration`

---

## 📊 Analyse des Scripts

### Script 1: `deploy_env.py`

**Rôle**: Orchestrateur de déploiement

**Actions**:
1. ✅ Lit versions depuis `VERSION`
2. ✅ Appelle `deploy_layer.py` pour vectora-core
3. ✅ Appelle `deploy_layer.py` pour common-deps
4. ❌ **Ne met PAS à jour les Lambdas**

**Conclusion**: Script incomplet - publie les layers mais ne les attache pas aux Lambdas.

---

### Script 2: `deploy_layer.py`

**Rôle**: Publier un layer sur AWS

**Actions**:
1. ✅ Upload ZIP vers S3
2. ✅ Publie layer avec `publish_layer_version`
3. ✅ Retourne ARN du layer
4. ❌ **Ne fait rien avec l'ARN retourné**

**Conclusion**: Script fait son job (publier layer) mais l'appelant ne fait rien avec l'ARN.

---

### Script 3: `deploy_normalize_score_v2_layers.py`

**Rôle**: Déploiement complet d'UNE Lambda avec layers

**Actions**:
1. ✅ Lit ARNs depuis fichiers texte
2. ✅ Upload handler vers S3
3. ✅ Met à jour Lambda avec `update-function-configuration --layers`

**Conclusion**: Script complet mais spécifique à normalize-score-v2. Pas générique.

---

## 🎯 Cause Racine

**Workflow actuel** (incomplet):
```
deploy_env.py
├─ deploy_layer.py (vectora-core) → Publie layer v49 ✅
├─ deploy_layer.py (common-deps) → Publie layer v11 ✅
└─ [FIN] ❌ Lambdas pas mises à jour
```

**Workflow attendu** (complet):
```
deploy_env.py
├─ deploy_layer.py (vectora-core) → Publie layer v49 ✅
├─ deploy_layer.py (common-deps) → Publie layer v11 ✅
├─ update_lambda_layers → Met à jour ingest-v2 ✅
├─ update_lambda_layers → Met à jour normalize-score-v2 ✅
└─ update_lambda_layers → Met à jour newsletter-v2 ✅
```

---

## 💡 Solution Recommandée

**Modifier `deploy_env.py`** pour mettre à jour automatiquement les Lambdas après publication des layers.

**Avantages**:
- ✅ Workflow complet en 1 commande
- ✅ Cohérent avec attente utilisateur
- ✅ Prévention erreurs (impossible d'oublier)

**Implémentation**: Ajouter fonction `update_lambda_layers()` et appeler après deploy des layers.

---

## 📋 Plan d'Implémentation (40 min)

1. Modifier `deploy_layer.py` pour capturer ARN retourné
2. Créer fonction `update_lambda_layers()` dans `deploy_env.py`
3. Appeler fonction pour chaque Lambda (ingest-v2, normalize-score-v2, newsletter-v2)
4. Gérer erreurs (Lambda manquante = warning, pas erreur)
5. Tester avec `--dry-run`

---

## ✅ Critères de Succès

- [ ] `deploy_env.py` publie layers ET met à jour Lambdas
- [ ] 1 commande = déploiement complet
- [ ] Logs clairs montrant chaque étape
- [ ] Gestion erreurs robuste
- [ ] Dry-run fonctionne

---

**Diagnostic créé le**: 2026-02-02  
**Phase**: 6ter  
**Statut**: ✅ Complet - Prêt pour implémentation
