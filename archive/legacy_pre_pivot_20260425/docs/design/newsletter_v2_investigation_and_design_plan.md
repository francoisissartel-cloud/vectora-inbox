# Plan d'Investigation et Design - Newsletter V2 Lambda

**Date :** 21 décembre 2025  
**Objectif :** Investigation approfondie et préparation de design pour la 3ᵉ Lambda vectora-inbox-newsletter-v2  
**Statut :** Plan d'investigation - AUCUN code ne sera modifié ou créé  

---

## 🎯 CONTEXTE ET OBJECTIFS

### Vision Métier
La Lambda newsletter-v2 doit être la 3ᵉ étape du workflow :
```
INGEST → NORMALIZE/MATCH/SCORE → NEWSLETTER
```

**Rôle précis :**
- Lire les items normalisés/matchés/scorés depuis S3 curated/
- Dédupliquer les items (éviter doublons)
- Sélectionner les items par section selon newsletter_layout
- Appeler Bedrock pour rédaction (titres, résumés, intro)
- Assembler la newsletter (Markdown + JSON) et l'écrire dans S3

**Ce qu'elle NE fait PAS :**
- Refaire du matching ou scoring lourd
- Faire de "consulting stratégique"
- Sélectionner les items via Bedrock (sélection déterministe)

---

## 📋 PLAN D'INVESTIGATION STRUCTURÉ

### Phase 1 : Audit du Workflow Actuel (INGEST → NORMALIZE/MATCH/SCORE)

#### 1.1 Analyse E2E lai_weekly_v4 (Données Réelles)
**Objectif :** Comprendre l'état actuel du workflow sur données réelles

**Actions :**
- [ ] Analyser le rapport E2E lai_weekly_v4 (20 décembre 2025)
- [ ] Valider les métriques : 15 items ingérés → 15 items normalisés → 8 items matchés (53.3%)
- [ ] Comprendre pourquoi 7 items non matchés (matched_domains vides)
- [ ] Évaluer la qualité des scores finaux (range 0-14.9)
- [ ] Identifier les patterns de succès/échec du matching

**Livrables :**
- Synthèse de l'état actuel du workflow
- Identification des points critiques pour la newsletter
- Validation que les données curated/ sont suffisantes

#### 1.2 Validation Architecture 3 Lambdas
**Objectif :** Confirmer que l'architecture est stable et prête

**Actions :**
- [ ] Vérifier que ingest-v2 et normalize-score-v2 sont déployées et fonctionnelles
- [ ] Valider les chemins S3 : ingested/ et curated/
- [ ] Confirmer les variables d'environnement standard
- [ ] Vérifier la conformité aux règles d'hygiène V4

**Livrables :**
- Validation de l'architecture existante
- Liste des prérequis techniques satisfaits

### Phase 2 : Analyse des Données Disponibles dans curated/

#### 2.1 Structure des Items Normalisés
**Objectif :** Comprendre précisément ce qui est disponible pour la newsletter

**Actions :**
- [ ] Analyser la structure JSON des items dans curated_items_lai_v4.json
- [ ] Inventorier tous les champs disponibles :
  - `normalized_content` : summary, entities, event_classification, lai_relevance_score
  - `matching_results` : matched_domains, domain_relevance
  - `scoring_results` : final_score, bonuses, penalties
- [ ] Évaluer la qualité des summaries générés par Bedrock
- [ ] Analyser la richesse des entités extraites (companies, molecules, technologies, trademarks)

**Livrables :**
- Cartographie complète des données disponibles
- Évaluation de la qualité pour génération newsletter

#### 2.2 Problème du Matching 0% (Point Critique)
**Objectif :** Comprendre pourquoi matched_domains est vide pour tous les items

**Actions :**
- [ ] Analyser pourquoi 8/15 items ont matched_domains = []
- [ ] Comprendre l'impact sur la sélection par section
- [ ] Évaluer si la newsletter peut fonctionner en mode dégradé
- [ ] Proposer des solutions de contournement temporaires

**Livrables :**
- Diagnostic du problème de matching
- Solutions de contournement pour la newsletter
- Recommandations de correction

#### 2.3 Analyse de la Déduplication Nécessaire
**Objectif :** Identifier les doublons potentiels dans les données

**Actions :**
- [ ] Détecter les doublons dans curated_items_lai_v4.json
- [ ] Analyser les cas : Nanexa-Moderna Partnership (2 versions identiques)
- [ ] Définir les critères de déduplication :
  - Technique : URL/item_id identiques
  - Sémantique : Même événement, sources différentes
  - Temporelle : Rapports périodiques
- [ ] Proposer un algorithme de déduplication déterministe

**Livrables :**
- Algorithme de déduplication en 3 étapes
- Critères de sélection de la "meilleure version"

### Phase 3 : Analyse du Contrat newsletter_v2.md

#### 3.1 Audit de Cohérence du Contrat
**Objectif :** Identifier les incohérences dans le contrat actuel

**Actions :**
- [ ] Vérifier les chemins S3 : outbox/ vs newsletters/
- [ ] Valider les inputs/outputs spécifiés
- [ ] Contrôler les variables d'environnement listées
- [ ] Comparer avec l'architecture réelle V2

**Livrables :**
- Liste des incohérences détectées
- Corrections nécessaires au contrat

#### 3.2 Validation des Spécifications Métier
**Objectif :** Confirmer que le contrat reflète les besoins réels

**Actions :**
- [ ] Valider le workflow métier en 10 étapes
- [ ] Vérifier la cohérence avec newsletter_layout dans lai_weekly_v4.yaml
- [ ] Confirmer les formats de sortie (Markdown + JSON)
- [ ] Valider les appels Bedrock prévus

**Livrables :**
- Validation des spécifications métier
- Ajustements nécessaires

### Phase 4 : Design de la Future Lambda newsletter-v2

#### 4.1 Architecture Technique Détaillée
**Objectif :** Définir l'architecture précise de la Lambda

**Actions :**
- [ ] Définir la structure du handler : `src_v2/lambdas/newsletter/handler.py`
- [ ] Concevoir les modules vectora_core :
  - `vectora_core/newsletter/__init__.py` : run_newsletter_for_client()
  - `vectora_core/newsletter/selector.py` : Sélection et déduplication
  - `vectora_core/newsletter/assembler.py` : Assemblage Markdown
  - `vectora_core/newsletter/bedrock_editor.py` : Appels Bedrock éditoriaux
- [ ] Définir les inputs S3 précis
- [ ] Spécifier les outputs S3 avec structure exacte

**Livrables :**
- Architecture technique complète
- Spécifications des modules

#### 4.2 Algorithmes de Sélection et Déduplication
**Objectif :** Définir les algorithmes déterministes

**Actions :**
- [ ] Concevoir l'algorithme de sélection en 4 étapes :
  1. Filtrage global par score (min_score: 12)
  2. Déduplication (3 étapes)
  3. Sélection par section (newsletter_layout)
  4. Limite globale (max_items_total: 15)
- [ ] Définir les critères de tri par section
- [ ] Spécifier la gestion des sections sans items

**Livrables :**
- Algorithmes détaillés de sélection
- Logique de répartition par section

#### 4.3 Intégration Bedrock pour Contenu Éditorial
**Objectif :** Définir précisément les appels Bedrock

**Actions :**
- [ ] Identifier les prompts nécessaires dans global_prompts.yaml
- [ ] Définir les appels Bedrock :
  - Génération TL;DR (1 appel)
  - Génération introduction (1 appel)
  - Génération résumés de section (1 appel par section)
- [ ] Estimer les coûts Bedrock additionnels
- [ ] Définir la gestion d'erreurs Bedrock

**Livrables :**
- Spécifications des appels Bedrock
- Estimation des coûts

#### 4.4 Format de Sortie Newsletter
**Objectif :** Définir précisément les formats Markdown et JSON

**Actions :**
- [ ] Concevoir le template Markdown avec :
  - Header avec titre et date
  - TL;DR généré par Bedrock
  - Sections avec items sélectionnés
  - Footer avec métriques
- [ ] Définir la structure JSON avec métadonnées complètes
- [ ] Spécifier le manifest de livraison

**Livrables :**
- Templates de sortie détaillés
- Exemples concrets basés sur lai_weekly_v4

### Phase 5 : Analyse des Risques & Points Critiques

#### 5.1 Risques Techniques
**Objectif :** Identifier les risques de développement

**Actions :**
- [ ] Risque matching 0% : Impact sur sélection par section
- [ ] Risque variations de volume : 0-15 items selon les runs
- [ ] Risque qualité Bedrock : Génération éditoriale incohérente
- [ ] Risque timeouts : Appels Bedrock multiples
- [ ] Risque déduplication : Logique complexe

**Livrables :**
- Matrice des risques avec mitigation
- Plans de contingence

#### 5.2 Risques Métier
**Objectif :** Identifier les risques business

**Actions :**
- [ ] Risque qualité newsletter : Contenu non pertinent
- [ ] Risque bruit : 60% items non pertinents dans lai_weekly_v4
- [ ] Risque cohérence éditoriale : Style variable
- [ ] Risque doublons : Même news plusieurs fois
- [ ] Risque sections vides : Pas d'items pour certaines sections

**Livrables :**
- Analyse des risques métier
- Recommandations qualité

#### 5.3 Points Critiques de Performance
**Objectif :** Identifier les goulots d'étranglement

**Actions :**
- [ ] Temps d'exécution : Appels Bedrock séquentiels vs parallèles
- [ ] Coûts : Estimation précise des appels additionnels
- [ ] Scalabilité : Performance avec 20+ clients
- [ ] Fiabilité : Gestion des échecs Bedrock

**Livrables :**
- Analyse de performance
- Recommandations d'optimisation

### Phase 6 : Recommandations Concrètes pour le Codage

#### 6.1 Prérequis Techniques
**Objectif :** Lister ce qui doit être prêt avant le codage

**Actions :**
- [ ] Corrections nécessaires au contrat newsletter_v2.md
- [ ] Ajustements à lai_weekly_v4.yaml si nécessaires
- [ ] Prompts newsletter à ajouter dans global_prompts.yaml
- [ ] Variables d'environnement à définir
- [ ] Structure S3 newsletters/ à créer

**Livrables :**
- Checklist des prérequis
- Plan de préparation

#### 6.2 Ordre de Développement Recommandé
**Objectif :** Définir la séquence optimale de développement

**Actions :**
- [ ] Phase 1 : Handler minimal + structure vectora_core
- [ ] Phase 2 : Sélection et déduplication (sans Bedrock)
- [ ] Phase 3 : Assemblage Markdown basique
- [ ] Phase 4 : Intégration Bedrock éditorial
- [ ] Phase 5 : Tests E2E et optimisation

**Livrables :**
- Plan de développement par phases
- Critères de validation par phase

#### 6.3 Tests et Validation
**Objectif :** Définir la stratégie de tests

**Actions :**
- [ ] Tests unitaires : Déduplication, sélection, assemblage
- [ ] Tests d'intégration : Appels Bedrock, écriture S3
- [ ] Tests E2E : Workflow complet sur lai_weekly_v4
- [ ] Tests de charge : Performance avec volumes réels
- [ ] Tests de qualité : Validation éditoriale

**Livrables :**
- Stratégie de tests complète
- Critères d'acceptation

---

## 📊 MÉTRIQUES DE SUCCÈS

### Métriques Techniques
- **Temps d'exécution :** < 2 minutes pour 15 items
- **Taux de succès :** > 95% des exécutions
- **Coût par newsletter :** < $2 USD (incluant Bedrock)
- **Déduplication :** 0 doublons dans la newsletter finale

### Métriques Qualité
- **Cohérence éditoriale :** Style uniforme via Bedrock
- **Pertinence :** > 80% des items sélectionnés pertinents
- **Complétude :** Toutes les sections avec au moins 1 item
- **Lisibilité :** Newsletter Markdown bien formatée

### Métriques Métier
- **Satisfaction utilisateur :** > 4/5 sur qualité newsletter
- **Engagement :** > 70% des items lus
- **Feedback :** < 10% de signalements de doublons/erreurs

---

## 🎯 LIVRABLES ATTENDUS

### Rapport d'Investigation
- **Fichier :** `docs/diagnostics/newsletter_v2_readiness_review_lai_weekly_v4.md`
- **Contenu :** Synthèse complète avec recommandations

### Corrections Identifiées
- **Contrat newsletter_v2.md :** Corrections P0 listées
- **Configuration lai_weekly_v4.yaml :** Ajustements si nécessaires
- **Prompts global_prompts.yaml :** Extensions newsletter

### Recommandation Finale
- **Statut :** GO/NO-GO pour démarrage du codage
- **Conditions :** Liste des prérequis à satisfaire
- **Timeline :** Estimation du développement

---

## ⚠️ CONTRAINTES ET LIMITATIONS

### Contraintes Techniques
- **Architecture V2 obligatoire :** Respect des règles d'hygiène V4
- **Bedrock us-east-1 :** Région validée uniquement
- **S3 structure :** Respect de la structure curated/ → newsletters/
- **Variables d'environnement :** Standard défini

### Contraintes Métier
- **Matching sélectif :** Préférer qualité vs quantité
- **Style factuel :** Pas de "competitive analysis" pour MVP
- **Configuration pilotée :** newsletter_layout comme vérité unique
- **Déterminisme :** Sélection reproductible

### Contraintes de Temps
- **Investigation uniquement :** Aucun code modifié
- **Rapport complet :** Toutes les phases analysées
- **Recommandations concrètes :** Prêt pour décision GO/NO-GO

---

**Plan d'Investigation Newsletter V2 - Version 1.0**  
**Prêt pour exécution - Aucune modification de code autorisée**