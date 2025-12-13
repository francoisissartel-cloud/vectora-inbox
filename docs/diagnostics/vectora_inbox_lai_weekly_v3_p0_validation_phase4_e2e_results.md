# Vectora Inbox LAI Weekly v3 - Phase 4 : Run End-to-End AWS DEV

**Date** : 2025-12-12  
**Phase** : 4 - Run end-to-end réel sur AWS DEV  
**Statut** : ⚠️ PARTIELLEMENT TERMINÉE (Blocage Bedrock Throttling)

---

## 🎯 Objectifs Phase 4

- ⚠️ Exécuter le workflow complet lai_weekly_v3 en conditions réelles
- ⚠️ Collecter les métriques détaillées à chaque phase
- ⚠️ Identifier la présence/absence des items gold

---

## 🚧 Blocage Technique Rencontré

### ❌ Problème : Bedrock Throttling Exception

**Symptômes** :
- Lambda ingest-normalize s'exécute mais timeout après 15 minutes
- Logs montrent des ThrottlingException répétées sur Bedrock
- Réponses Bedrock non-JSON (parsing failures)
- Aucun résultat final dans S3

**Logs d'erreur observés** :
```
[WARNING] ThrottlingException détectée (tentative 1/4). Retry dans 0.57s...
[WARNING] ThrottlingException détectée (tentative 2/4). Retry dans 1.08s...
[WARNING] ThrottlingException détectée (tentative 3/4). Retry dans 2.03s...
[ERROR] ThrottlingException - Échec après 4 tentatives. Abandon de l'appel Bedrock.
[WARNING] Réponse Bedrock non-JSON, tentative d'extraction manuelle
```

**Cause racine** :
- Volume élevé d'items à normaliser (104 items sur 30 jours)
- Appels Bedrock séquentiels sans parallélisation
- Quotas Bedrock dépassés en région eu-west-3

---

## 📊 Métriques Partielles Collectées

### ✅ Phase 1A : Ingestion des Sources

**Sources traitées** : 8/8 sources configurées
- ✅ **press_corporate__medincell** : 12 items récupérés
- ✅ **press_corporate__nanexa** : 8 items récupérés  
- ✅ **press_corporate__delsitech** : 10 items récupérés
- ✅ **press_sector__endpoints_news** : 24 items récupérés
- ❌ **press_corporate__peptron** : 0 items (SSL certificate error)
- ✅ **press_sector__fiercebiotech** : 25 items récupérés
- ❌ **press_corporate__camurus** : 0 items (parsing HTML failed)
- ✅ **press_sector__fiercepharma** : 25 items récupérés

**Résultats Ingestion** :
- **Total items bruts** : 104 items
- **Filtre temporel** : 104 items conservés, 0 items ignorés
- **Période** : 30 jours (2025-11-12 à 2025-12-12)

### ⚠️ Phase 1B : Normalisation Bedrock

**Statut** : Échec partiel par throttling
- **Items à normaliser** : 104 items
- **Workers parallèles** : 1 (séquentiel)
- **Appels Bedrock réussis** : ~10-15 items (estimation)
- **Appels Bedrock échoués** : ~90+ items (throttling)

**Problèmes identifiés** :
- Réponses Bedrock non-JSON fréquentes
- Retry logic insuffisant pour le volume
- Pas de parallélisation des appels

---

## 🔍 Analyse des Sources

### ✅ Sources Fonctionnelles

1. **MedinCell** (12 items) : ✅ Pure player LAI
2. **Nanexa** (8 items) : ✅ Pure player LAI  
3. **DelSiTech** (10 items) : ✅ Pure player LAI
4. **Endpoints News** (24 items) : ✅ Presse sectorielle
5. **FierceBiotech** (25 items) : ✅ Presse sectorielle
6. **FiercePharma** (25 items) : ✅ Presse sectorielle

### ❌ Sources Problématiques

1. **Peptron** : SSL certificate error
   - Erreur : "certificate verify failed: Hostname mismatch"
   - Impact : Perte d'une source pure player LAI

2. **Camurus** : HTML parsing failed
   - Erreur : "parsing HTML n'a produit aucun item (structure non reconnue)"
   - Impact : Perte d'une source pure player LAI majeure

---

## 🎯 Items Gold - Statut Inconnu

**Impossibilité de vérifier** les items gold à cause du blocage Bedrock :
- ❓ **Nanexa/Moderna PharmaShell®** : Présence inconnue
- ❓ **UZEDY® Extended-Release Injectable** : Présence inconnue  
- ❓ **MedinCell malaria grant** : Présence inconnue

**Note** : Les sources Nanexa (8 items) et MedinCell (12 items) ont été ingérées, mais la normalisation Bedrock n'a pas pu extraire les entités/technologies.

---

## 🚨 Corrections P0 - Validation Partielle

### ✅ P0-1 : Bedrock Technology Detection
- **Statut** : Déployé mais non testé en conditions réelles
- **Raison** : Throttling Bedrock empêche la normalisation
- **Section LAI** : Présente dans le code déployé

### ✅ P0-2 : Exclusions HR/Finance Runtime  
- **Statut** : Non testé (phase engine non atteinte)
- **Raison** : Pas d'items normalisés à filtrer

### ✅ P0-3 : HTML Extraction Robust
- **Statut** : Partiellement validé
- **Succès** : MedinCell, Nanexa, DelSiTech extraits avec succès
- **Échecs** : Camurus (parsing failed), Peptron (SSL error)

---

## 📋 Recommandations Immédiates

### 🔧 Solutions Techniques

1. **Optimisation Bedrock** :
   - Réduire la taille des prompts (moins d'exemples canonical)
   - Implémenter la parallélisation des appels (2-3 workers)
   - Augmenter les délais de retry (backoff plus long)

2. **Gestion des quotas** :
   - Demander une augmentation des quotas Bedrock eu-west-3
   - Implémenter un cache Bedrock pour éviter les re-normalisations
   - Ajouter un mode "batch processing" avec pause entre lots

3. **Sources problématiques** :
   - Peptron : Désactiver SSL verification ou corriger le certificat
   - Camurus : Mettre à jour le parser HTML pour leur nouvelle structure

### 🎯 Run de Validation Alternative

**Option 1** : Run avec période réduite (7 jours au lieu de 30)
- Réduire le volume d'items à ~30-40 items
- Éviter le throttling Bedrock
- Valider les corrections P0 sur un échantillon

**Option 2** : Run en mode simulation
- Utiliser des données pré-normalisées existantes
- Tester uniquement les phases engine + newsletter
- Valider P0-2 (exclusions) et génération newsletter

---

## ⚠️ Statut Phase 4

**Résultat** : ⚠️ **BLOCAGE TECHNIQUE - BEDROCK THROTTLING**

**Métriques collectées** :
- ✅ Ingestion : 104 items de 6/8 sources
- ❌ Normalisation : Échec par throttling Bedrock
- ❌ Engine : Non exécuté (pas d'items normalisés)
- ❌ Newsletter : Non générée

**Impact sur validation P0** :
- P0-1 : Non testé en conditions réelles
- P0-2 : Non testé (phase non atteinte)  
- P0-3 : Partiellement validé (6/8 sources OK)

---

## 🚀 Prochaines Étapes

1. **Résolution immédiate** : Implémenter les optimisations Bedrock
2. **Run alternatif** : Tester avec période réduite (7 jours)
3. **Validation P0** : Utiliser des données simulées si nécessaire
4. **Documentation** : Créer un plan P1 pour résoudre les problèmes de scalabilité

**La validation P0 nécessite une approche alternative pour contourner les limitations Bedrock actuelles.**