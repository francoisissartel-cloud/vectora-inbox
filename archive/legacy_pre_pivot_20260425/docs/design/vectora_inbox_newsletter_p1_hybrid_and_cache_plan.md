# Vectora Inbox - Plan P1 Newsletter Hybride et Cache

**Date** : 2025-12-12  
**Objectif** : Suppression du fallback newsletter + configuration hybride + cache éditorial  
**Statut** : 📋 **PLAN CRÉÉ - PRÊT POUR EXÉCUTION**

---

## 🎯 Objectif Global P1

Mettre en place une P1 "Newsletter" qui :

1. **Supprime le fallback** en rendant la génération newsletter fiable
2. **Utilise une configuration hybride** :
   - Normalisation en us-east-1 (déjà migrée avec succès)
   - Newsletter en eu-west-3 (ou autre région mieux adaptée, à justifier)
3. **Ajoute un cache éditorial** pour éviter les régénérations inutiles
4. **Optimise le prompt newsletter** (taille -80% vs version initiale) pour réduire les risques de throttling/timeout

**Résultat attendu** : Un workflow E2E stable avec une newsletter éditoriale propre, sans toucher à la logique métier matching/scoring (sauf bug critique).

---

## Phase 0 – Diagnostic Précis du Fallback

### 🎯 Objectifs
- Identifier exactement pourquoi la génération newsletter passe en fallback
- Analyser les erreurs Bedrock (type, région, modèle)
- Vérifier format JSON, taille de prompt, max_tokens, etc.
- Documenter l'état actuel et les invariants métier

### 🔧 Actions
1. **Audit des fichiers existants** :
   - Prompts newsletter actuels
   - Client Bedrock configuration
   - Code Lambda newsletter
   - Logs d'erreur récents

2. **Tests de reproduction** :
   - Isoler la génération newsletter
   - Tester avec payload minimal
   - Identifier le point de défaillance exact

3. **Analyse comparative** :
   - Comparer comportement us-east-1 vs eu-west-3
   - Mesurer taille des prompts actuels
   - Évaluer timeout et limites

### ✅ Critères de Succès
- [ ] Cause(s) probable(s) du fallback identifiée(s)
- [ ] Ce qui fonctionne déjà documenté
- [ ] Invariants métier listés (sections, ton, contraintes factuelles)
- [ ] Diagnostic complet dans `docs/diagnostics/vectora_inbox_newsletter_p1_phase0_diagnostic.md`

---

## Phase 1 – Design Hybride + Cache

### 🎯 Objectifs
- Proposer une architecture P1 pour la newsletter
- Définir la configuration hybride optimale
- Concevoir le système de cache éditorial
- Optimiser le prompt newsletter (-80% tokens)

### 🔧 Actions
1. **Prompt ultra-réduit** :
   - Analyser prompt actuel (baseline tokens)
   - Conserver l'essentiel métier : sections, ton, contraintes factuelles
   - Objectif : ~80% réduction vs version initiale
   - Valider cohérence éditoriale

2. **Client Bedrock hybride** :
   - Normalisation : us-east-1 (déjà validé)
   - Newsletter : recommander région optimale (eu-west-3 ou autre)
   - Justifier le choix technique (latence, quotas, stabilité)

3. **Cache éditorial** :
   - Principe : éviter régénération pour (client_id, period_start, period_end)
   - Structure S3 proposée (préfixe, nom de fichier)
   - Comportement "partial" et régénération forcée
   - Stratégie d'invalidation

### ✅ Critères de Succès
- [ ] Prompt newsletter réduit de ~80% (tokens mesurés)
- [ ] Architecture hybride justifiée techniquement
- [ ] Système de cache S3 spécifié
- [ ] Design documenté dans `docs/design/vectora_inbox_newsletter_p1_hybrid_and_cache_design.md`

---

## Phase 2 – Implémentation Locale

### 🎯 Objectifs
- Implémenter les changements dans le repo local
- Tester sur un petit set d'items gold
- Valider le fonctionnement sans déployer

### 🔧 Actions
1. **Nouveau prompt newsletter** :
   - Implémenter le prompt réduit
   - Conserver la structure 4 sections
   - Maintenir le ton éditorial

2. **Logique client Bedrock hybride** :
   - Normalisation → us-east-1
   - Newsletter → région choisie
   - Configuration par variables d'environnement

3. **Couche cache S3** :
   - Lecture/écriture cache newsletter
   - Intégration dans engine/newsletter
   - Gestion des cas d'erreur

4. **Tests locaux** :
   - Items gold : Nanexa/Moderna, UZEDY, MedinCell malaria
   - Scripts de test simples
   - Validation génération + cache

### ✅ Critères de Succès
- [ ] Code implémenté sans modification logique métier
- [ ] Tests locaux passent sur items gold
- [ ] Cache fonctionne (lecture/écriture)
- [ ] Résultats documentés dans `docs/diagnostics/vectora_inbox_newsletter_p1_phase2_local_tests.md`

---

## Phase 3 – Déploiement AWS DEV

### 🎯 Objectifs
- Packager et déployer les Lambdas modifiées
- Configurer les variables d'environnement
- Valider le déploiement

### 🔧 Actions
1. **Packaging Lambdas** :
   - Engine (scoring + newsletter)
   - Modules partagés (clients Bedrock, cache)
   - Vérification dépendances

2. **Déploiement DEV** :
   - Profil rag-lai-prod, région eu-west-3
   - Variables d'environnement cohérentes
   - Validation permissions IAM

3. **Tests post-déploiement** :
   - Invocation Lambda isolée
   - Vérification logs
   - Test cache S3

### ✅ Critères de Succès
- [ ] Lambdas déployées avec succès
- [ ] Variables d'environnement configurées
- [ ] Tests post-déploiement réussis
- [ ] Commandes et résultats documentés dans `docs/diagnostics/vectora_inbox_newsletter_p1_phase3_aws_deployment.md`

---

## Phase 4 – Run E2E (lai_weekly_v3) + Métriques

### 🎯 Objectifs
- Lancer un run complet lai_weekly_v3 en conditions réelles
- Mesurer les performances et la fiabilité
- Valider l'élimination du fallback

### 🔧 Actions
1. **Run E2E complet** :
   - lai_weekly_v3 (period_days: 7)
   - Ingestion → Normalisation → Matching/Scoring → Newsletter
   - Conditions réelles (pas de simulation)

2. **Métriques collectées** :
   - Temps total pipeline
   - Temps spécifique newsletter
   - Nb d'appels Bedrock newsletter (cache impact)
   - Erreurs ou fallback (attendu : 0)

3. **Validation qualité** :
   - Newsletter Markdown générée
   - Inspection métier du contenu
   - Comparaison avec versions précédentes

### ✅ Critères de Succès
- [ ] Run E2E complet sans fallback
- [ ] Newsletter générée avec qualité éditoriale
- [ ] Métriques performance collectées
- [ ] Cache fonctionne (1er run = appels Bedrock, 2ème run = 0 appels)
- [ ] Diagnostic complet dans `docs/diagnostics/vectora_inbox_newsletter_p1_phase4_e2e_results.md`

---

## Phase 5 – Executive Summary & Recommandations

### 🎯 Objectifs
- Synthétiser les résultats de la P1
- Documenter l'impact avant/après
- Recommander les optimisations P2

### 🔧 Actions
1. **Résumé exécutif** :
   - Changements concrets implémentés
   - Impact avant/après (temps, fiabilité, coûts)
   - Validation MVP LAI

2. **Analyse qualitative** :
   - Newsletter fiable et éditorialement correcte
   - Scalabilité pour le MVP
   - Retours utilisateur potentiels

3. **Recommandations P2** :
   - Optimisations futures identifiées
   - Améliorations système
   - Évolutions fonctionnelles

### ✅ Critères de Succès
- [ ] Executive summary complet
- [ ] Impact quantifié (métriques avant/après)
- [ ] Recommandations P2 priorisées
- [ ] Document final dans `docs/diagnostics/vectora_inbox_newsletter_p1_hybrid_and_cache_results.md`

---

## 📋 Contraintes & Principes

### Contraintes Techniques
- ✅ Pas de nouvelles "grosses" refontes d'architecture
- ✅ Rester dans l'esprit actuel de Vectora Inbox
- ✅ Pas de simulation pour Phase 4 E2E (vrai run obligatoire)
- ✅ Documentation complète de chaque phase

### Contraintes Métier
- ✅ Ne pas toucher à la logique métier matching/scoring (sauf bug critique)
- ✅ Conserver la structure newsletter 4 sections
- ✅ Maintenir la qualité éditoriale
- ✅ Préserver les items gold (Nanexa/Moderna, UZEDY, etc.)

### Métriques de Succès Global
- 🎯 **Fallback éliminé** : 0% fallback sur run E2E
- 🎯 **Performance** : Newsletter générée en <30s
- 🎯 **Cache efficace** : 0 appels Bedrock sur 2ème run identique
- 🎯 **Qualité maintenue** : Newsletter éditorialement satisfaisante
- 🎯 **Coût optimisé** : Réduction appels Bedrock grâce au cache

---

## 🚀 Prochaines Étapes

**Plan P1 newsletter créé, je passe à la Phase 0.**

L'exécution commencera par le diagnostic précis du fallback pour identifier les causes racines et établir une baseline solide avant l'implémentation des améliorations.