# Vectora Inbox LAI Weekly v3 - Phase 4 : Run End-to-End #1 - Résultats

**Date** : 2025-12-11  
**Objectif** : Workflow end-to-end réel lai_weekly_v3 après corrections timeout  
**Status** : ❌ **ÉCHEC TECHNIQUE** - Problème déploiement code Lambda  

---

## Résumé Exécutif

**Problème critique** : Lambda `vectora-inbox-engine-dev` exécute le code d'ingestion au lieu du code engine  
**Cause racine** : Désynchronisation déploiement code entre les deux Lambdas  
**Impact** : Workflow end-to-end impossible, pas de newsletter générée  
**Action requise** : Redéploiement correct du code engine

---

## Tentative d'Exécution

### **Commande Exécutée**
```bash
aws lambda invoke \
  --function-name vectora-inbox-engine-dev \
  --payload fileb://engine_payload_v3.json \
  engine_response_v3.json \
  --profile rag-lai-prod \
  --region eu-west-3
```

**Payload** : `{"client_id": "lai_weekly_v3", "period_days": 30}`

### **Résultat Observé**
- ❌ **Timeout client AWS CLI** : Read timeout sur endpoint
- ❌ **Code incorrect** : Lambda engine exécute code ingestion
- ❌ **Pas de newsletter** : Workflow interrompu

---

## Analyse des Logs

### **Request ID** : `a16b4256-a3f2-4826-81fb-97c28f003f63`

**Timeline d'exécution** :
- **21:05:49** : START - Démarrage Lambda
- **21:05:49** : ❌ **ERREUR** - "Démarrage de vectora-inbox-ingest-normalize" au lieu de "vectora-inbox-engine"
- **21:05:52** : Chargement configuration lai_weekly_v3 (correct)
- **21:05:53** : Chargement scopes canonical (correct)
- **21:06:40+** : Appels Bedrock avec ThrottlingException (normalisation au lieu d'engine)

### **Problème Identifié**
```
[INFO] Démarrage de vectora-inbox-ingest-normalize
```
**Au lieu de** :
```
[INFO] Démarrage de vectora-inbox-engine
```

**Diagnostic** : La Lambda `vectora-inbox-engine-dev` contient le code de la Lambda `vectora-inbox-ingest-normalize-dev`

---

## Configuration Lambda Vérifiée

### **Lambda vectora-inbox-engine-dev**
- ✅ **Timeout** : 900s (correction appliquée)
- ✅ **Memory** : 512 MB
- ✅ **Handler** : `handler.lambda_handler`
- ✅ **Runtime** : `python3.12`
- ❌ **Code** : Contient code ingestion au lieu d'engine

### **Lambda vectora-inbox-ingest-normalize-dev**
- ✅ **Timeout** : 600s
- ✅ **Configuration** : Correcte

---

## Données Disponibles

### **Items Normalisés Existants**
- ✅ **Fichier** : `s3://vectora-inbox-data-dev/normalized/lai_weekly_v3/2025/12/11/items.json`
- ✅ **Taille** : 77.7 KB (104 items)
- ✅ **Date** : 2025-12-11 (aujourd'hui)
- ✅ **Qualité** : Items LAI pertinents détectés (Nanexa/Moderna, MedinCell/UZEDY, etc.)

### **Configuration Client**
- ✅ **Client config** : `lai_weekly_v3.yaml` présent S3
- ✅ **Period_days** : 30 (cohérent)
- ✅ **Watch_domains** : 2 domaines configurés
- ✅ **Canonical config** : Synchronisé

---

## Cause Racine Technique

### **Hypothèse Principale**
**Désynchronisation déploiement code** :
1. Les deux Lambdas partagent le même package de déploiement
2. Le code engine n'a pas été correctement déployé
3. La Lambda engine exécute le handler d'ingestion

### **Vérifications Nécessaires**
1. **Code source** : Vérifier le contenu du package Lambda engine
2. **Handler configuration** : Confirmer que le handler pointe vers le bon module
3. **Déploiement** : Redéployer le code engine correct

---

## Impact sur le Workflow

### **Phase 3 (Corrections)** : ✅ **SUCCÈS**
- Timeout Lambda augmenté 300s → 900s
- Configuration AWS mise à jour
- Pas de régression

### **Phase 4 (Run E2E)** : ❌ **ÉCHEC**
- Ingestion : ✅ Données disponibles (104 items)
- Engine : ❌ Code incorrect déployé
- Newsletter : ❌ Pas générée

---

## Métriques Partielles

### **Ingestion/Normalisation** (Données existantes)
- **Items traités** : 104 items
- **Sources** : Corporate + Press sector
- **Companies détectées** : Nanexa, MedinCell, Moderna, Pfizer, etc.
- **Molecules détectées** : olanzapine, risperidone
- **Technologies détectées** : Aucune (problème potentiel)

### **Engine/Newsletter**
- **Items matchés** : Non calculé (échec technique)
- **Items sélectionnés** : Non calculé
- **Newsletter générée** : Non

---

## Actions Correctives Requises

### **Action Immédiate**
1. **Identifier source du problème** :
   - Vérifier scripts de déploiement
   - Comparer packages Lambda engine vs ingestion
   - Identifier pourquoi même code dans les deux

2. **Redéployer code engine** :
   - Utiliser scripts existants `scripts/`
   - Vérifier que le bon code est déployé
   - Tester avec payload simple

3. **Re-run Phase 4** :
   - Relancer engine avec données existantes
   - Valider génération newsletter
   - Documenter métriques complètes

### **Vérifications Post-Correction**
- ✅ Logs montrent "Démarrage de vectora-inbox-engine"
- ✅ Pas d'appels Bedrock normalisation
- ✅ Appels Bedrock newsletter generation
- ✅ Newsletter stockée S3

---

## Recommandations

### **Court Terme**
1. **Priorité absolue** : Corriger déploiement code engine
2. **Test simple** : Payload minimal pour valider correction
3. **Run complet** : Workflow end-to-end avec données existantes

### **Moyen Terme**
1. **Améliorer CI/CD** : Validation déploiement automatique
2. **Tests déploiement** : Vérifier que chaque Lambda a le bon code
3. **Monitoring** : Alertes sur logs incorrects

---

## Conclusion Phase 4

**❌ ÉCHEC TECHNIQUE** : Problème déploiement code empêche validation workflow

**Cause racine** : Lambda engine contient code ingestion  
**Correction requise** : Redéploiement code engine  
**Données prêtes** : 104 items normalisés disponibles  
**Prochaine action** : Corriger déploiement et relancer Phase 4

---

**Phase 4 – Run end-to-end : ÉCHEC TECHNIQUE**

**Problème** : ❌ **DÉPLOIEMENT CODE LAMBDA**  
**Solution** : Redéployer code engine correct  
**Prochaine action** : Correction déploiement + nouveau run