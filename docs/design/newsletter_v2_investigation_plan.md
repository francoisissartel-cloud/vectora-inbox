# Plan d'Investigation Newsletter V2 - Document de Cadrage

**Date :** 21 décembre 2025  
**Objectif :** Préparer sereinement le développement de la 3ᵉ Lambda vectora-inbox-newsletter-v2  
**Statut :** Phase 0 - Cadrage et lecture obligatoire  

---

## 🎯 RÈGLES DE DÉVELOPPEMENT À SUIVRE

### Architecture de Référence (OBLIGATOIRE)
- **Architecture 3 Lambdas V2 validée** : ingest-v2 → normalize-score-v2 → newsletter-v2
- **Code de référence** : `src_v2/` uniquement (100% conforme aux règles d'hygiène V4)
- **Handlers minimalistes** : Délégation à `vectora_core/newsletter/`
- **Configuration pilotée** : Comportement contrôlé par `client_config` + `canonical`
- **Bedrock région** : us-east-1 avec modèle `anthropic.claude-3-sonnet-20240229-v1:0`

### Contraintes Techniques Validées
- **Environnement AWS** : eu-west-3, compte 786469175371, profil rag-lai-prod
- **Structure S3** : `curated/{client_id}/{YYYY}/{MM}/{DD}/items.json` → `newsletters/{client_id}/{YYYY}/{MM}/{DD}/newsletter.md`
- **Lambda Layers** : vectora-core + common-deps (architecture modulaire)
- **Variables d'environnement** : CONFIG_BUCKET, DATA_BUCKET, NEWSLETTERS_BUCKET, BEDROCK_*

### Interdictions Absolues
- ❌ Modification du code dans `src/` (pollué)
- ❌ Architecture 2 Lambdas (historique)
- ❌ Hardcoding client-spécifique
- ❌ Appels Bedrock sans retry/gestion d'erreurs
- ❌ Changements sur AWS pendant l'investigation

---

## 🏗️ ÉLÉMENTS CLÉS DU WORKFLOW ACTUEL À RESPECTER

### Flux de Données Validé E2E
```
Sources LAI → ingest-v2 → S3 ingested/ → normalize-score-v2 → S3 curated/ → newsletter-v2 (à développer)
```

### Architecture Bedrock-Only Pure (Validée)
- **Normalisation** : Extraction entités, classification événements via Bedrock
- **Matching sémantique** : Évaluation pertinence domaines via Bedrock  
- **Scoring déterministe** : Règles métier + bonus configurables
- **Performance validée** : 30 appels Bedrock/run, 100% succès, $0.21/run

### Client de Référence : lai_weekly_v3/v4
- **Données réelles** : 15 items LAI authentiques (MedinCell, UZEDY®, Nanexa, etc.)
- **Domaines** : tech_lai_ecosystem + regulatory_lai
- **Matching rate** : 53.3% (8/15 items matchés)
- **Signal/Bruit** : 40% signal, 60% bruit (acceptable pour newsletter)

### Configuration Pilotée Existante
- **Client config** : `lai_weekly_v3.yaml` / `lai_weekly_v4.yaml` (validés E2E)
- **Canonical scopes** : 180+ entreprises, 90+ molécules, 80+ technologies LAI
- **Prompts Bedrock** : Templates canonicalisés dans `global_prompts.yaml`
- **Structure newsletter** : Sections configurables via `newsletter_layout`

---

## 🔍 GRANDES QUESTIONS À RÉPONDRE

### Questions Métier Prioritaires

1. **Suffisance du workflow actuel**
   - Le travail de normalize_score_v2 est-il suffisant pour alimenter une newsletter ?
   - Quelles informations manquent pour générer du contenu éditorial de qualité ?

2. **Gestion des doublons**
   - Comment identifier et fusionner les items parlant de la même news ?
   - Quels signaux utiliser (URL, domaine, trademark + date, similarité titres) ?

3. **Sélection et structuration**
   - Comment choisir les items à inclure (score minimal, domaine, fraîcheur) ?
   - Comment répartir en sections (mapping domaine → section) ?

4. **Rôle de Bedrock dans la newsletter**
   - Sélection des items ou rédaction uniquement ?
   - Génération titre + chapeau + résumé par item ?
   - Homogénéisation du ton éditorial ?

5. **Généricité et scalabilité**
   - Le moteur reste-t-il 100% générique (sans hardcoding client) ?
   - Coût par run et impact avec 5, 10, 20 clients actifs ?

### Questions Techniques Spécifiques

6. **Contrat newsletter_v2.md**
   - Le contrat existant est-il réaliste et aligné avec le moteur actuel ?
   - Quels champs/sections à ajouter ou modifier ?

7. **Qualité des données curated**
   - Les champs actuels suffisent-ils pour Bedrock (titre, résumé, contexte) ?
   - Y a-t-il perte d'information entre ingestion et normalisation ?

8. **Configuration newsletter**
   - Quels réglages dans client_config et canonical optimiseraient la qualité ?
   - Comment piloter la structure et le style éditorial ?

---

## 📋 PHASES D'INVESTIGATION PLANIFIÉES

### Phase 1 - Cartographie Workflow Actuel
- **Objectif** : Comprendre précisément le flux INGEST → NORMALIZE/MATCH/SCORE
- **Livrables** : `docs/diagnostics/newsletter_v2_current_workflow_map.md`
- **Focus** : Chemins S3, forme des fichiers, métriques réelles lai_weekly_v3/v4

### Phase 2 - Analyse Critique normalize_score_v2
- **Objectif** : Évaluer si le travail actuel est suffisant pour la newsletter
- **Livrables** : `docs/diagnostics/normalize_score_v2_readiness_for_newsletter.md`
- **Focus** : Généricité, qualité matching, informations disponibles par item

### Phase 3 - Problématique Doublons & Perte d'Information
- **Objectif** : Identifier les patterns de déduplication et besoins éditoriaux
- **Livrables** : `docs/design/newsletter_v2_content_requirements.md`
- **Focus** : Signaux de fusion, richesse éditoriale, champs manquants

### Phase 4 - Stratégie Sélection & Structuration
- **Objectif** : Définir comment assembler la newsletter (choix + sections + génération)
- **Livrables** : `docs/design/newsletter_v2_assembly_strategy.md`
- **Focus** : Critères de sélection, rôle Bedrock, coûts et scalabilité

### Phase 5 - Évaluation Contrat newsletter_v2.md
- **Objectif** : Vérifier la pertinence du contrat métier existant
- **Livrables** : Recommandations d'amélioration du contrat
- **Focus** : Alignement avec réalité technique, incohérences, champs manquants

### Phase 6 - Rapport Final de Préparation
- **Objectif** : Synthèse complète avec réponses aux questions et recommandations
- **Livrables** : `docs/design/newsletter_v2_readiness_and_design_summary.md`
- **Focus** : Décisions stratégiques, schéma idéal Lambda, estimation coûts

---

## 📚 SOURCES DE DONNÉES ANALYSÉES

### Documentation Architecture
- ✅ `vectora-inbox-development-rules.md` - Règles de développement V4
- ✅ `blueprint-v2-current.yaml` - Architecture 3 Lambdas validée
- ✅ `contracts/lambdas/ingest_v2.md` - Contrat ingestion
- ✅ `contracts/lambdas/normalize_score_v2.md` - Contrat normalisation/scoring
- ✅ `contracts/lambdas/newsletter_v2.md` - Contrat newsletter (à challenger)

### Code de Référence
- ✅ `src_v2/lambdas/ingest/` - Lambda ingestion validée
- ✅ `src_v2/lambdas/normalize_score/` - Lambda normalisation validée  
- ✅ `src_v2/vectora_core/` - Modules métier réutilisables
- ✅ `src_v2/vectora_core/newsletter/` - Structure newsletter (à compléter)

### Rapports E2E Récents
- ✅ `lai_weekly_v3_real_data_e2e_validation_report.md` - 15 items réels, 100% succès
- ✅ `lai_weekly_v4_e2e_final_report.md` - Architecture Bedrock-Only Pure validée
- ✅ Données jusqu'au 20 décembre 2025 (données fraîches)

### Configuration Validée
- ✅ `client-config-examples/lai_weekly_v3.yaml` - Config client validée E2E
- ✅ `client-config-examples/lai_weekly_v4.yaml` - Config Tech Focus
- ✅ `canonical/prompts/global_prompts.yaml` - Prompts Bedrock canonicalisés
- ✅ `canonical/scopes/*.yaml` - Entités métier LAI (companies, molecules, etc.)

---

## ⚠️ CONTRAINTES D'INVESTIGATION

### Interdictions Strictes
- **Aucune modification de code** dans `src/` ou `src_v2/`
- **Aucun changement de configuration** (client-config, canonical)
- **Aucun nouveau déploiement AWS** ou run Bedrock massif
- **Aucune modification des contrats** existants

### Périmètre Autorisé
- **Lecture et analyse** de tous les fichiers existants
- **Création de documents** dans `docs/design/` et `docs/diagnostics/`
- **Recommandations conceptuelles** structurées et argumentées
- **Estimation de coûts** basée sur les métriques existantes

---

## 🎯 CRITÈRES DE SUCCÈS

### Livrables Attendus
- [ ] 5-6 documents d'analyse détaillée par phase
- [ ] 1 rapport de synthèse final complet
- [ ] Réponses claires aux 8 questions métier/techniques
- [ ] Recommandations concrètes pour le développement

### Qualité Requise
- **Basé sur des données réelles** : Métriques lai_weekly_v3/v4 validées
- **Aligné avec l'architecture V2** : Respect des règles de développement
- **Actionnable** : Recommandations implémentables directement
- **Générique** : Solutions scalables multi-clients

### Validation Finale
- **Architecture cohérente** : Newsletter s'intègre dans le workflow V2
- **Coûts maîtrisés** : Estimation réaliste pour production multi-clients
- **Qualité éditoriale** : Capacité à générer des newsletters pertinentes
- **Maintenance minimale** : Configuration pilote le comportement

---

**🚀 PRÊT POUR L'INVESTIGATION**

Ce plan de cadrage établit les bases solides pour une investigation méthodique de la Lambda newsletter V2. L'approche respecte intégralement l'architecture validée et se base sur des données réelles pour garantir des recommandations pertinentes et implémentables.

**Prochaine étape :** Phase 1 - Cartographie complète du workflow actuel.