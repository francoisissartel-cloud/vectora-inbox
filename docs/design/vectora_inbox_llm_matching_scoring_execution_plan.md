# Plan d'Exécution - Vectora Inbox LLM Matching/Scoring

**Date** : 2025-12-12  
**Objectif** : Implémentation progressive du LLM gating pour matching/scoring  
**Client cible** : lai_weekly_v3  
**Contrainte** : SANS casser le workflow existant (fallback déterministe obligatoire)  

---

## 🎯 Objectif Global

Mettre en place un vrai "LLM gating" pour le matching/scoring, en s'appuyant sur Bedrock, avec :
- Un prompt dédié LLM-matching/scoring défini dans `canonical/prompts/global_prompts.yaml`
- Un pipeline hybride : règles déterministes + signaux LLM
- Une implémentation sûre, progressive, testée localement puis déployée sur AWS
- SANS casser le workflow existant (fallback déterministe obligatoire)

---

## 📋 Phases d'Exécution

### Phase A – Quick Win : Exploiter les signaux LLM déjà présents

**Objectif** : Utiliser ce que Bedrock produit déjà (ex. `lai_relevance_score`) dans le scoring, SANS ajout d'un nouveau prompt.

#### A1. Diagnostic des signaux existants
**Type** : Diagnostic  
**Objectif** : Identifier les signaux LLM déjà présents dans les items normalisés  

**Fichiers concernés** :
- Analyse des items S3 normalisés pour `lai_weekly_v3`
- `src/vectora_core/bedrock/bedrock_client.py` (prompt de normalisation actuel)

**Travail** :
- Examiner les réponses Bedrock de normalisation existantes
- Identifier les champs de pertinence : `lai_relevance_score`, `domain_relevance`, etc.
- Vérifier leur sérialisation dans les items S3 normalisés
- Analyser leur distribution et fiabilité

**Critères de succès** :
- Documentation complète des signaux LLM existants
- Compréhension de leur format et distribution
- Identification des champs exploitables pour le scoring

**Livrables** :
- `docs/diagnostics/vectora_inbox_llm_matching_phaseA_current_signals.md`

**Condition pour passer à A2** : Signaux LLM identifiés et documentés

---

#### A2. Intégration minimale dans le scoring
**Type** : Code + Configuration  
**Objectif** : Utiliser les signaux LLM existants dans le calcul de score  

**Fichiers concernés** :
- `src/vectora_core/scoring/scorer.py`
- `canonical/scoring/scoring_rules.yaml`
- Variables d'environnement (feature flag)

**Travail** :
- Ajouter feature flag `USE_LLM_RELEVANCE` (défaut: false)
- Modifier `scorer.py` pour lire les champs LLM si présents
- Intégrer comme multiplicateur/bonus dans le calcul de score
- Assurer que le comportement par défaut reste STRICTEMENT identique

**Critères de succès** :
- Scoring sans flag = comportement actuel inchangé
- Scoring avec flag = intégration des signaux LLM
- Tests unitaires passent
- Pas de régression sur le workflow existant

**Livrables** :
- Code modifié avec feature flag
- Tests unitaires mis à jour

**Condition pour passer à A3** : Code fonctionnel avec tests passants

---

#### A3. Tests locaux
**Type** : Tests  
**Objectif** : Valider le comportement avec/sans LLM relevance  

**Fichiers concernés** :
- `tests/unit/scoring/test_scorer.py`
- `tests/integration/`

**Travail** :
- Tests unitaires : scoring identique sans flag
- Tests unitaires : scoring modifié avec flag actif
- Tests d'intégration avec données réelles `lai_weekly_v3`
- Validation des calculs de score

**Critères de succès** :
- Tous les tests passent
- Comportement par défaut préservé
- Impact LLM mesurable et cohérent

**Livrables** :
- `docs/diagnostics/vectora_inbox_llm_matching_phaseA_local_tests.md`

**Condition pour passer à A4** : Tests locaux validés et documentés

---

#### A4. Déploiement AWS DEV
**Type** : Déploiement + Validation  
**Objectif** : Tester en conditions réelles sur AWS DEV  

**Fichiers concernés** :
- Lambda `engine` (déploiement DEV)
- Configuration environnement DEV

**Travail** :
- Déployer les modifications sur AWS DEV
- Activer `USE_LLM_RELEVANCE=true` UNIQUEMENT pour `lai_weekly_v3`
- Lancer un run réel complet
- Collecter métriques avant/après
- Comparer distribution des scores et sélection finale

**Critères de succès** :
- Run complet réussi sans erreur
- Métriques collectées et analysées
- Impact LLM documenté
- Workflow end-to-end fonctionnel

**Livrables** :
- `docs/diagnostics/vectora_inbox_llm_matching_phaseA_aws_results.md`

**Condition pour passer à Phase B** : Phase A stabilisée et documentée avec résultats AWS concluants

---

### Phase B – Nouveau prompt dédié LLM-matching

**Objectif** : Introduire un DEUXIÈME prompt Bedrock pour le "domain relevance / matching LLM" configurable dans canonical.

#### B1. Design détaillé du prompt et de l'API interne
**Type** : Design + Configuration  
**Objectif** : Définir le prompt LLM-matching dans canonical  

**Fichiers concernés** :
- `canonical/prompts/global_prompts.yaml`
- Spécifications API interne

**Travail** :
- Ajouter entrée `llm_matching_prompt` dans `global_prompts.yaml`
- Définir format d'input : texte, entités, watch_domains
- Définir format d'output : relevance_score, is_relevant, reason par domaine
- Spécifier configuration Bedrock (modèle, tokens, température)

**Critères de succès** :
- Prompt clairement défini et documenté
- Format input/output spécifié
- Configuration Bedrock optimisée

**Livrables** :
- `docs/design/vectora_inbox_llm_matching_prompt_spec.md`
- `canonical/prompts/global_prompts.yaml` mis à jour

**Condition pour passer à B2** : Spécifications complètes et validées

---

#### B2. Implémentation du LLM matcher
**Type** : Code  
**Objectif** : Créer le module LLM matcher autonome  

**Fichiers concernés** :
- `src/vectora_core/matching/llm_matcher.py` (nouveau)
- `tests/unit/matching/test_llm_matcher.py` (nouveau)

**Travail** :
- Créer module `llm_matcher.py`
- Fonctions : construire input, appeler Bedrock, parser output
- Gestion d'erreurs et fallback
- Tests unitaires avec fixtures synthétiques

**Critères de succès** :
- Module autonome fonctionnel
- Tests unitaires passants
- Gestion d'erreurs robuste
- Pas d'appel Bedrock réel dans les tests unitaires

**Livrables** :
- Code du module LLM matcher
- Tests unitaires

**Condition pour passer à B3** : Module testé et fonctionnel

---

#### B3. Intégration dans la Lambda
**Type** : Code + Intégration  
**Objectif** : Intégrer LLM matcher dans le pipeline  

**Fichiers concernés** :
- `src/vectora_core/bedrock/bedrock_client.py`
- Lambda `ingest-normalize` ou `engine` (à déterminer)

**Travail** :
- Choisir point d'intégration optimal (après normalisation)
- Ajouter feature flag `USE_LLM_MATCHING`
- Intégrer appel LLM matcher avec gestion d'erreurs
- Fallback automatique en cas d'erreur Bedrock

**Critères de succès** :
- Intégration transparente dans le pipeline
- Feature flag fonctionnel
- Fallback robuste en cas d'erreur
- Pas de régression du workflow existant

**Livrables** :
- Code d'intégration
- Tests d'intégration

**Condition pour passer à B4** : Intégration stable et testée

---

#### B4. Hybridation matching LLM + règles déterministes
**Type** : Code  
**Objectif** : Combiner matching LLM et déterministe  

**Fichiers concernés** :
- `src/vectora_core/matching/domain_matcher.py`
- `canonical/matching/matching_rules.yaml`

**Travail** :
- Modifier `domain_matcher.py` pour consommer résultats LLM
- Logique hybride : LLM_score + règles déterministes
- Priorisation intelligente (LLM confiant vs règles critiques)
- Préservation du chemin 100% déterministe

**Critères de succès** :
- Logique hybride fonctionnelle
- Équilibre LLM/déterministe configurable
- Chemin déterministe préservé
- Tests de non-régression passants

**Livrables** :
- Code de matching hybride
- Configuration des règles

**Condition pour passer à B5** : Matching hybride validé

---

#### B5. Ajustement du scoring
**Type** : Code  
**Objectif** : Intégrer scores LLM dans le calcul final  

**Fichiers concernés** :
- `src/vectora_core/scoring/scorer.py`
- `canonical/scoring/scoring_rules.yaml`

**Travail** :
- Intégrer `domain_relevance` LLM dans le scoring
- Pondération configurable LLM vs autres signaux
- Maintenir compatibilité avec Phase A
- Documentation de la logique de scoring

**Critères de succès** :
- Scoring enrichi fonctionnel
- Pondération configurable
- Compatibilité Phase A préservée
- Logique documentée

**Livrables** :
- `docs/design/vectora_inbox_llm_matching_scoring_logic.md`
- Code de scoring mis à jour

**Condition pour passer à Phase C** : Scoring hybride complet et documenté

---

### Phase C – Tests, métriques et déploiement AWS

**Objectif** : Validation complète et déploiement en conditions réelles.

#### C1. Tests locaux
**Type** : Tests + Validation  
**Objectif** : Validation sur dataset de référence  

**Fichiers concernés** :
- `tests/integration/test_llm_matching_complete.py`
- Dataset de référence

**Travail** :
- Construire dataset de référence avec cas métiers clés
- Tester scénarios : déterministe seul, Phase A, Phase B complète
- Mesurer taux de récupération, bruit, stabilité
- Validation des performances

**Critères de succès** :
- Dataset représentatif construit
- Tous les scénarios testés
- Métriques de qualité mesurées
- Performance acceptable

**Livrables** :
- Dataset de référence
- Résultats de tests complets

**Condition pour passer à C2** : Tests locaux concluants

---

#### C2. Déploiement AWS DEV
**Type** : Déploiement + Validation  
**Objectif** : Test en conditions réelles AWS  

**Fichiers concernés** :
- Lambdas `ingest-normalize` + `engine` (DEV)
- Configuration environnement

**Travail** :
- Déployer modifications complètes sur AWS DEV
- Activer `USE_LLM_MATCHING=true` pour `lai_weekly_v3`
- Run complet réel avec métriques
- Collecte performance et coût

**Critères de succès** :
- Déploiement réussi sans erreur
- Run complet fonctionnel
- Métriques collectées
- Coût estimé acceptable

**Livrables** :
- Métriques de run réel
- Analyse performance/coût

**Condition pour passer à C3** : Run AWS réussi avec métriques satisfaisantes

---

#### C3. Diagnostic & Synthèse
**Type** : Documentation + Recommandations  
**Objectif** : Bilan complet et recommandations  

**Fichiers concernés** :
- Documentation finale

**Travail** :
- Diagnostic global des résultats
- Analyse impact qualité/coût
- Recommandations pour la suite
- Synthèse exécutive

**Critères de succès** :
- Diagnostic complet rédigé
- Impact clairement quantifié
- Recommandations actionnables
- Architecture validée ou ajustements proposés

**Livrables** :
- `docs/diagnostics/vectora_inbox_llm_matching_scoring_phaseC_results.md`
- `docs/diagnostics/vectora_inbox_llm_matching_scoring_phaseC_executive_summary.md`

**Condition de fin** : Documentation complète et recommandations formulées

---

## 🚨 Contraintes et Garde-fous

### Feature Flags Obligatoires
- `USE_LLM_RELEVANCE` : Utilisation signaux LLM existants (Phase A)
- `USE_LLM_MATCHING` : Nouveau prompt LLM matching (Phase B)
- Défaut : `false` pour tous les flags
- Activation : uniquement pour `lai_weekly_v3` en DEV

### Fallback Automatique
- En cas d'erreur Bedrock : fallback déterministe automatique
- Logging des erreurs sans casser le pipeline
- Workflow end-to-end toujours fonctionnel

### Validation Continue
- Chaque phase doit être stabilisée avant passage à la suivante
- Tests de non-régression obligatoires
- Documentation des problèmes et corrections

### Données Réelles Uniquement
- Pas de simulation ou données synthétiques pour la validation
- Utilisation des vraies Lambdas, S3, et runs `lai_weekly_v3`
- Correction des problèmes techniques avant continuation

---

## 📊 Métriques de Succès

### Phase A
- Signaux LLM identifiés et exploitables
- Impact mesurable sur le scoring
- Workflow préservé

### Phase B
- Prompt LLM-matching fonctionnel
- Matching hybride équilibré
- Performance acceptable

### Phase C
- Amélioration qualité mesurée
- Coût acceptable
- Architecture stable

### Global
- Matching/scoring hybride fonctionnel en DEV pour `lai_weekly_v3`
- Prompt clairement défini dans canonical
- Métriques réelles impact qualité/coût
- Recommandations pour la suite