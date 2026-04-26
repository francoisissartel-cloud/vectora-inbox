# Vectora Inbox - Plan Correctif Runtime Matching & Scoring

**Date** : 2025-12-12  
**Objectif** : Corriger les problèmes de matching/scoring identifiés pour rendre le workflow end-to-end fonctionnel  
**Basé sur** : Investigation complète des causes racines (matching_scoring_investigation_results.md)  
**Statut** : 🚀 **PRÊT POUR EXÉCUTION**

---

## 🎯 Contexte & Objectif

### Problèmes Identifiés par l'Investigation

L'investigation approfondie a révélé **3 causes racines critiques** :

1. **🔴 Bedrock Technology Detection Défaillante** : 0/104 items ont `technologies_detected` non vide
2. **🔴 Champs LAI Manquants** : `lai_relevance_score`, `anti_lai_detected`, `pure_player_context` = null
3. **🟡 Extraction HTML Partielle** : Nanexa/Moderna summary vide (0 chars)

### Objectif du Plan

**Rendre le workflow lai_weekly_v3 end-to-end fonctionnel** avec :
- Items gold récupérés : 4/4 au lieu de 0/4
- Items avec technologies : >30% au lieu de 0%
- Newsletter LAI authentique : >60% au lieu de 0%
- Pipeline complet : Ingestion → Normalisation → Matching → Scoring → Newsletter

---

## 📋 Plan d'Exécution par Phases

### **PHASE 0 : Préparation & Backup**
*Durée : 30 minutes*

**Objectif** : Sauvegarder l'état actuel et préparer l'environnement de correction

#### 0.1 Backup État Actuel
- [ ] Sauvegarder les fichiers sources actuels
- [ ] Créer un point de restauration Git
- [ ] Documenter la configuration AWS actuelle

#### 0.2 Préparation Environnement
- [ ] Vérifier l'accès aux outils de développement
- [ ] Préparer les scripts de test
- [ ] Valider l'accès AWS dev

**Livrables** :
- Backup complet de l'état actuel
- Environnement de développement prêt

---

### **PHASE 1 : Fix Bedrock Technology Detection**
*Durée : 2-3 heures*

**Objectif** : Corriger le problème critique de détection des technologies par Bedrock

#### 1.1 Diagnostic Bedrock Isolé
- [ ] Créer script de test isolé Bedrock
- [ ] Tester normalisation sur 1 item UZEDY
- [ ] Identifier le problème exact (prompt/parsing/modèle)

#### 1.2 Correction Prompt Bedrock
**Fichier** : `src/vectora_core/normalization/bedrock_client.py`
- [ ] Simplifier la section technology du prompt
- [ ] Réduire le nombre de keywords par catégorie (max 10)
- [ ] Ajouter des exemples explicites
- [ ] Optimiser le format de sortie JSON

#### 1.3 Implémentation Champs LAI
**Fichier** : `src/vectora_core/normalization/normalizer.py`
- [ ] Ajouter `lai_relevance_score` (0-10) dans le prompt
- [ ] Ajouter `anti_lai_detected` (boolean) pour routes orales
- [ ] Ajouter `pure_player_context` (boolean) pour pure players
- [ ] Mettre à jour le parsing JSON

#### 1.4 Test Local Phase 1
- [ ] Tester la normalisation sur les items gold
- [ ] Vérifier que `technologies_detected` est rempli
- [ ] Valider les nouveaux champs LAI

**Critères de Succès** :
- ✅ UZEDY items ont `technologies_detected` non vide
- ✅ Nanexa/Moderna détecte "PharmaShell®"
- ✅ Champs `lai_relevance_score`, `anti_lai_detected`, `pure_player_context` remplis

**Livrables** :
- Prompt Bedrock optimisé
- Normalisation fonctionnelle pour technologies
- Script de test isolé Bedrock

---

### **PHASE 2 : Fix Extraction HTML & Trademarks**
*Durée : 1-2 heures*

**Objectif** : Corriger l'extraction HTML et implémenter la détection des trademarks

#### 2.1 Fix Extraction HTML Nanexa
**Fichier** : `src/vectora_core/ingestion/html_extractor_robust.py`
- [ ] Diagnostiquer pourquoi Nanexa/Moderna a summary vide
- [ ] Améliorer le fallback depuis titre
- [ ] Tester l'extraction sur sources corporate problématiques

#### 2.2 Implémentation Trademark Detection
**Fichier** : `src/vectora_core/normalization/bedrock_client.py`
- [ ] Ajouter section trademark dans le prompt Bedrock
- [ ] Utiliser `trademark_scopes.yaml` pour la détection
- [ ] Tester sur UZEDY®, PharmaShell®

#### 2.3 Test Local Phase 2
- [ ] Tester extraction HTML sur Nanexa
- [ ] Vérifier détection trademarks sur UZEDY
- [ ] Valider le fallback HTML

**Critères de Succès** :
- ✅ Nanexa/Moderna a un summary non vide
- ✅ UZEDY® détecté dans `trademarks_detected`
- ✅ PharmaShell® détecté dans `trademarks_detected`

**Livrables** :
- Extraction HTML robuste
- Détection trademarks fonctionnelle

---

### **PHASE 3 : Fix Matching Contextuel**
*Durée : 1 heure*

**Objectif** : Activer le matching contextuel pour les pure players sans signaux explicites

#### 3.1 Activation Matching Contextuel
**Fichier** : `src/vectora_core/matching/matcher.py`
- [ ] Activer la fonction `contextual_matching()` existante
- [ ] Implémenter la logique pure_player sans signaux technology explicites
- [ ] Tester sur MedinCell malaria grant

#### 3.2 Test Local Phase 3
- [ ] Tester le matching sur les items gold
- [ ] Vérifier que MedinCell malaria est matché
- [ ] Valider le matching contextuel

**Critères de Succès** :
- ✅ MedinCell malaria grant a `matched_domains` non vide
- ✅ Pure players sans signaux explicites sont matchés contextuellement

**Livrables** :
- Matching contextuel fonctionnel

---

### **PHASE 4 : Tests Intégrés Locaux**
*Durée : 1 heure*

**Objectif** : Valider l'ensemble des corrections en local avant déploiement

#### 4.1 Test Pipeline Complet Local
- [ ] Exécuter le script de debug mis à jour
- [ ] Tester la normalisation sur 20 items
- [ ] Tester le matching sur les items normalisés
- [ ] Tester le scoring sur les items matchés

#### 4.2 Validation Items Gold
- [ ] Vérifier que les 4 items gold sont correctement traités
- [ ] Valider les métriques de succès
- [ ] Documenter les améliorations

#### 4.3 Tests de Régression
- [ ] Vérifier que les exclusions HR/finance fonctionnent toujours
- [ ] Valider que le scoring fonctionne correctement
- [ ] Tester sur un échantillon d'items variés

**Critères de Succès** :
- ✅ 4/4 items gold récupérés
- ✅ >30% items avec technologies détectées
- ✅ >20% items avec matched_domains
- ✅ Aucune régression sur les fonctionnalités existantes

**Livrables** :
- Pipeline local fonctionnel
- Rapport de tests intégrés
- Métriques de validation

---

### **PHASE 5 : Déploiement AWS Dev**
*Durée : 1 heure*

**Objectif** : Déployer les corrections sur AWS dev et valider

#### 5.1 Déploiement Lambdas
- [ ] Packager les corrections dans les Lambdas
- [ ] Déployer `vectora-inbox-ingest-normalize-dev`
- [ ] Déployer `vectora-inbox-engine-dev`
- [ ] Vérifier les déploiements

#### 5.2 Test Smoke AWS
- [ ] Lancer un test d'ingestion sur 1 source
- [ ] Vérifier la normalisation AWS
- [ ] Tester le matching/scoring AWS
- [ ] Valider les logs

**Critères de Succès** :
- ✅ Déploiement réussi sans erreur
- ✅ Test smoke fonctionnel
- ✅ Logs propres sans erreur critique

**Livrables** :
- Lambdas déployées avec corrections
- Test smoke validé

---

### **PHASE 6 : Run End-to-End AWS**
*Durée : 30 minutes*

**Objectif** : Exécuter un run complet lai_weekly_v3 sur AWS et valider les résultats

#### 6.1 Run Complet lai_weekly_v3
- [ ] Lancer l'ingestion complète (30 jours)
- [ ] Exécuter la normalisation sur tous les items
- [ ] Lancer l'engine (matching + scoring + newsletter)
- [ ] Collecter les résultats

#### 6.2 Validation Résultats
- [ ] Analyser les items normalisés
- [ ] Vérifier les items matchés
- [ ] Examiner la newsletter générée
- [ ] Comparer avec les métriques baseline

**Critères de Succès** :
- ✅ Pipeline end-to-end sans erreur
- ✅ Newsletter générée avec contenu LAI
- ✅ Items gold présents dans la newsletter
- ✅ Métriques de qualité atteintes

**Livrables** :
- Run end-to-end réussi
- Newsletter lai_weekly_v3 fonctionnelle
- Métriques de performance

---

### **PHASE 7 : Analyse Impact & Rapport**
*Durée : 30 minutes*

**Objectif** : Analyser l'impact des corrections et documenter les résultats

#### 7.1 Analyse Comparative
- [ ] Comparer métriques avant/après corrections
- [ ] Analyser la qualité de la newsletter
- [ ] Évaluer l'impact sur les items gold
- [ ] Mesurer les performances

#### 7.2 Rapport Final
- [ ] Documenter les corrections appliquées
- [ ] Résumer l'impact sur le workflow
- [ ] Identifier les améliorations futures
- [ ] Recommandations pour la production

**Critères de Succès** :
- ✅ Amélioration significative des métriques
- ✅ Workflow end-to-end fonctionnel
- ✅ Items gold récupérés
- ✅ Newsletter de qualité

**Livrables** :
- Rapport d'impact complet
- Recommandations pour la suite
- Documentation des corrections

---

## 📊 Métriques de Validation

### Métriques Critiques (Avant → Objectif)

| **Métrique** | **Avant** | **Objectif** | **Validation** |
|--------------|-----------|--------------|----------------|
| Items avec technologies | 0% | >30% | ✅ Bedrock détecte |
| Items gold matchés | 0/4 | 4/4 | ✅ Tous récupérés |
| Items avec matched_domains | 4.8% | >20% | ✅ Matching fonctionnel |
| Newsletter LAI authentique | 0% | >60% | ✅ Contenu pertinent |
| Pipeline end-to-end | ❌ Cassé | ✅ Fonctionnel | ✅ Complet |

### Métriques de Performance

| **Composant** | **Métrique** | **Objectif** |
|---------------|--------------|--------------|
| Normalisation | Temps d'exécution | <2 minutes |
| Matching | Items traités | 100% |
| Scoring | Calcul scores | <30s |
| Newsletter | Génération | <1 minute |

---

## 🛠️ Outils & Scripts

### Scripts de Test
- `scripts/debug_matching_scoring_lai_weekly_v3.py` : Debug complet
- `scripts/test_bedrock_technology_detection.py` : Test isolé Bedrock (à créer)
- `scripts/validate_corrections.py` : Validation post-correction (à créer)

### Commandes AWS
```bash
# Déploiement ingest-normalize
aws lambda update-function-code --function-name vectora-inbox-ingest-normalize-dev

# Déploiement engine  
aws lambda update-function-code --function-name vectora-inbox-engine-dev

# Test run complet
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev --payload file://test-payload.json
```

---

## 🎯 Critères de Succès Global

### ✅ Succès Technique
- Pipeline end-to-end fonctionnel sans erreur
- Tous les items gold récupérés et traités
- Métriques de qualité atteintes
- Performance maintenue

### ✅ Succès Business
- Newsletter lai_weekly_v3 avec contenu LAI authentique
- Réduction significative du bruit (HR/finance)
- Signaux LAI majeurs capturés
- Workflow prêt pour utilisation régulière

### ✅ Succès Opérationnel
- Déploiement AWS réussi
- Monitoring fonctionnel
- Documentation complète
- Plan de rollback validé

---

## 📋 Suivi d'Exécution

| Phase | Statut | Durée Prévue | Durée Réelle | Commentaires |
|-------|--------|--------------|--------------|--------------|
| Phase 0 | ✅ Terminé | 30 min | 30 min | Backup & préparation |
| Phase 1 | ✅ Terminé | 2-3h | 2h | Fix Bedrock critical - Prompt LAI optimisé |
| Phase 2 | ✅ Terminé | 1-2h | 1h | Fix HTML & trademarks - Fallback validé |
| Phase 3 | ✅ Terminé | 1h | 30 min | Fix matching contextuel - Activé |
| Phase 4 | ✅ Terminé | 1h | 1h | Tests intégrés locaux - Validés |
| Phase 5 | ✅ Terminé | 1h | 1h | Déploiement AWS - Lambdas mises à jour |
| Phase 6 | ⚠️ Partiel | 30 min | 30 min | Run end-to-end - Problème encodage |
| Phase 7 | ✅ Terminé | 30 min | 30 min | Analyse & rapport - Complet |

**Durée totale estimée** : 6-8 heures

---

## 🚀 Prochaines Étapes

1. **Validation du plan** : Confirmer l'approche et les priorités
2. **Démarrage Phase 0** : Backup et préparation
3. **Exécution séquentielle** : Phases 1-7 avec validation à chaque étape
4. **Rapport final** : Impact et recommandations

**Le plan est prêt pour exécution immédiate. Chaque phase est autonome avec des critères de succès clairs.**