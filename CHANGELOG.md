# Changelog

## [Unreleased]

### Added
- **🎯 Refactor Canonical LAI (technology_scopes + company_scopes) - Phase "Canonical Only" (COMPLÉTÉ)**
  - **Statut** : 🟢 GREEN - Refactor canonical terminé, adaptation code runtime en attente
  - **Date** : 2025-01-XX
  - **Objectif** : Améliorer la précision LAI de 0% vers >50% en nettoyant les scopes canonical sans modifier le code runtime
  - **Changements clés** :
    - ✅ Restructuration complète de `canonical/scopes/technology_scopes.yaml` (lai_keywords)
    - ✅ Séparation des company scopes en `lai_companies_pure_players` et `lai_companies_hybrid`
    - ✅ Documentation exhaustive (3 fichiers diagnostics créés)
    - ✅ Mise à jour du CHANGELOG et des synthèses existantes
  - **Restructuration de technology_scopes.yaml** :
    - **Avant** : Liste plate de 78 termes non structurés
    - **Après** : Structure hiérarchique à 7 catégories (120+ termes classifiés)
    - **Nouvelles catégories** :
      - `core_phrases` (13 termes) : expressions explicites LAI (haute précision)
      - `technology_terms_high_precision` (38 termes) : DDS + HLE spécifiques
      - `technology_use` (10 termes) : termes d'usage (combinaison requise)
      - `route_admin_terms` (13 termes) : routes d'administration (contexte nécessaire)
      - `interval_patterns` (14 termes) : patterns de dosage prolongé (signaux forts)
      - `generic_terms` (12 termes) : termes trop larges (isolés, ne matchent plus seuls)
      - `negative_terms` (11 termes) : exclusions explicites (signaux NON-LAI)
    - **Termes déplacés vers generic_terms (ne matchent plus seuls)** :
      - drug delivery system, liposomes, liposomal, emulsion, lipid emulsion
      - PEG, PEGylation, PEGylated, protein engineering
      - hydrogel, nanosuspension
    - **Routes d'administration isolées** : subcutaneous, intramuscular, etc. ne matchent plus seules
  - **Séparation des company scopes** :
    - **lai_companies_pure_players (14 entreprises)** :
      - MedinCell, Camurus, DelSiTech, Nanexa, Peptron
      - Bolder BioTechnology, Cristal Therapeutics, Durect
      - Eupraxia Pharmaceuticals, Foresee Pharmaceuticals, G2GBio
      - Hanmi Pharmaceutical, LIDDS, Taiwan Liposome
      - **Usage prévu** : 1 signal fort LAI suffit pour déclencher un match haute confiance
    - **lai_companies_hybrid (27 entreprises)** :
      - Big pharma : AbbVie, Pfizer, Novo Nordisk, Sanofi, Takeda, etc.
      - Mid pharma : Alkermes, Ipsen, Jazz Pharmaceuticals, etc.
      - **Usage prévu** : signaux multiples requis pour déclencher un match LAI (éviter faux positifs)
  - **Principe métier** :
    - Pure players : business model 100% LAI → 1 signal suffit
    - Hybrid : portfolio diversifié → combinaison de signaux requise
  - **Impact attendu** :
    - Précision LAI : de 0% vers >50% (après adaptation code runtime)
    - Faux positifs big pharma : de ~80% vers <10% des matches
    - Vrais positifs pure players : conservés à ~100%
  - **Contrainte respectée** : Aucune modification du code runtime (matcher.py, scorer.py, etc.) dans cette phase
  - **Documents créés** :
    - `docs/design/vectora_inbox_lai_technology_scopes_refactor_plan.md` (plan de design)
    - `docs/diagnostics/vectora_inbox_lai_technology_scopes_refactor_results.md` (diagnostic technology_scopes)
    - `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md` (diagnostic company_scopes)
  - **Documents mis à jour** :
    - `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md` (ajout section refactor canonical)
    - `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_executive_summary.md` (mise à jour statut)
    - `CHANGELOG.md` (cette entrée)
  - **Prochaines étapes (phase suivante - code runtime)** :
    1. Adapter `domain_matching_rules.yaml` pour exploiter les 7 catégories de lai_keywords
    2. Modifier `matcher.py` pour implémenter la logique de combinaison de signaux
    3. Adapter `scorer.py` pour différencier pure_players vs hybrid
    4. Tester sur le corpus existant et mesurer la nouvelle précision LAI
  - **Estimation temps phase suivante** : 4-8 heures

- **🎯 Refactor Matching Générique Piloté par Config/Canonical (DÉPLOYÉ - RÉSULTATS ANALYSÉS)**
  - **Statut** : 🔴 RED - Déploiement réussi, mais 0% de précision LAI (scopes canonical incorrects)
  - **Date de test** : 2025-12-09
  - **Résultats** :
    - Items analysés : 50
    - Items matchés : 2 (4%, vs 16% avant)
    - Items sélectionnés : 2 (vs 5 avant)
    - **Précision LAI** : **0%** (0/2 items sont LAI)
    - **Faux positifs** : 2 (Agios oncologie, WuXi AppTec CDMO)
  - **Diagnostic** : `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md`
  - **Problème identifié** : Le refactor de matching fonctionne correctement (technology AND entity), mais les **scopes canonical sont incorrects** :
    - `lai_keywords` contient des termes trop génériques ("drug delivery system", "liposomes", "PEG", "subcutaneous", etc.)
    - Ces termes matchent n'importe quelle news pharma/biotech, pas seulement les LAI
  - **Correction appliquée** : Bug d'import dans `__init__.py` corrigé (ajout de `resolver` dans les imports)
  - **Déploiements** :
    - Script `redeploy-engine-matching-refactor.ps1` exécuté avec succès (2 fois)
    - Package Lambda : 17.46 MB avec toutes les dépendances
    - Configs canonical uploadées dans S3
  - **Actions prioritaires** :
    1. **URGENT** : Nettoyer `lai_keywords` - retirer les termes génériques, ne garder que les termes spécifiques LAI
    2. Enrichir les logs de matching pour afficher les entités matchées
    3. Vérifier l'ingestion des sources corporate LAI (MedinCell, Camurus, etc.)
  - **Prochaines étapes** :
    - Auditer et nettoyer `canonical/scopes/technology_scopes.yaml`
    - Re-déployer et re-tester
    - Vérifier que la précision LAI atteint ≥ 80%
  - **Objectif** : Rendre le matching 100% générique et piloté par config/canonical, sans aucune logique métier LAI codée en dur
  - **Document de plan** : `docs/design/vectora_inbox_domain_matching_refactor_plan.md`
  - **Problème initial** :
    - Matcher trop permissif : sélectionne des items dès qu'une company match (souvent big pharma) sans vérifier le contexte technology
    - Résultat : 0% de précision LAI pour le domaine `tech_lai_ecosystem`
    - Logique codée en dur : `if domain_type == 'technology'` dans le code
  - **Solution implémentée** :
    - ✅ Création du fichier `canonical/matching/domain_matching_rules.yaml` avec règles déclaratives par type de domaine
    - ✅ Règles pour `technology`, `indication`, `regulatory`, `default`
    - ✅ Adaptation de `config/resolver.py` : ajout de `load_matching_rules()`
    - ✅ Adaptation de `matching/matcher.py` : ajout de `_evaluate_matching_rule()` pour évaluer les règles de manière générique
    - ✅ Adaptation de `scoring/scorer.py` : remplacement de la liste hardcodée de pure players par une référence à un scope (`lai_companies_mvp_core`)
    - ✅ Mise à jour de `canonical/scoring/scoring_rules.yaml` : `pure_player_scope` au lieu de `pure_players_lai`
    - ✅ Mise à jour de l'orchestration dans `src/vectora_core/__init__.py` : chargement et passage des matching rules
    - ✅ Création de `canonical/matching/README.md` pour documenter le système
  - **Principe clé** : Aucun `if domain.id == "tech_lai_ecosystem"` dans le code. Tout est piloté par des règles déclaratives dans canonical
  - **Exemple de règle** (domaine `technology`) :
    - `match_mode: all_required`
    - `technology.requirement: required` (au moins 1 mot-clé technology)
    - `entity.requirement: required` (au moins 1 company OU molecule)
    - Résultat : Item avec `MedinCell` + `extended-release injectable` → MATCH, Item avec `Pfizer` seul → NO MATCH
  - **Extensibilité** : Le même moteur est réutilisable pour d'autres verticaux (oncologie, diabète, etc.) sans modification du code
  - **Critères de succès pour le MVP LAI** :
    - Précision LAI : ≥ 80% des items sélectionnés sont clairement LAI
    - Représentation pure players : ≥ 50% des items concernent des pure players LAI
    - Zéro faux positif big pharma sans contexte LAI
  - **Fichiers créés** :
    - `canonical/matching/domain_matching_rules.yaml`
    - `canonical/matching/README.md`
    - `scripts/redeploy-engine-matching-refactor.ps1`
    - `scripts/test-engine-matching-refactor.ps1`
    - `docs/diagnostics/vectora_inbox_lai_mvp_matching_refactor_results.md`
    - `docs/design/vectora_inbox_domain_matching_refactor_plan.md`
    - `docs/design/vectora_inbox_domain_matching_refactor_summary.md`
  - **Fichiers modifiés** :
    - `src/vectora_core/config/resolver.py`
    - `src/vectora_core/matching/matcher.py`
    - `src/vectora_core/scoring/scorer.py`
    - `src/vectora_core/__init__.py`
    - `canonical/scoring/scoring_rules.yaml`
    - `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md`
  - **Prochaines étapes** (ARCHIVÉES - Remplacées par actions prioritaires ci-dessus) :
    - ✅ Redéployer : `.\scripts\redeploy-engine-matching-refactor.ps1`
    - ✅ Tester : `.\scripts\test-engine-matching-refactor.ps1`
    - ✅ Compléter le diagnostic de résultats
    - ✅ Évaluer les critères de Done et mettre à jour le statut

### Added
- **🎯 Phase 4 - Test & Acceptation MVP LAI (ARCHIVÉ - Remplacé par Refactor Matching Générique)**
  - **Statut** : 🔴 RED - MVP LAI à ajuster (0% de précision LAI)
  - **Date de test** : 2025-12-08
  - **Environnement** : DEV
  - **Résultats du test** :
    - Items analysés : 50
    - Items matchés : 8 (16%)
    - Items sélectionnés : 5
    - **Items LAI** : **0** (0% de précision LAI)
    - **Items pure players LAI** : **0** (0%)
    - **Faux positifs** : **5** (100%)
  - **Newsletter générée** : `s3://vectora-inbox-newsletters-dev/lai_weekly/2025/12/08/newsletter.md`
  - **Problème identifié** : Le matcher sélectionne des items mentionnant des big pharma (Pfizer, AbbVie, Takeda) SANS vérifier que l'item concerne les technologies LAI
  - **Exemples de faux positifs** :
    - Pfizer - Hympavzi Phase 3 data (hémophilie, pas LAI)
    - AbbVie - Skyrizi TV advertising (publicité, pas LAI)
    - Takeda/Otsuka - FDA safety probe (pas LAI)
  - **Métriques vs objectifs** :
    - Précision LAI : 0% (objectif 80-90%) ❌
    - Proportion pure players : 0% (objectif ≥50%) ❌
    - Faux positifs : 5 (objectif 0) ❌
  - **Décision** : **MVP LAI – DEV : À AJUSTER**
  - **Ajustements nécessaires** :
    1. **Prioritaire** : Modifier `matcher.py` pour exiger (company ET technology LAI) au lieu de (company OU technology)
    2. Vérifier l'ingestion des sources corporate LAI (MedinCell, Camurus, etc.)
    3. Augmenter le bonus pure players de 3 à 10
  - **Documents créés** :
    - `docs/design/vectora_inbox_lai_mvp_phase4_execution_plan.md` (plan d'exécution)
    - `docs/diagnostics/vectora_inbox_lai_mvp_phase4_test_logs.md` (logs de test)
    - `docs/diagnostics/vectora_inbox_lai_mvp_focus_results.md` (analyse détaillée)
    - `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md` (résumé final)
  - **Prochaines étapes** :
    - Implémenter l'ajustement prioritaire (matching LAI obligatoire)
    - Relancer un test Phase 4 bis
    - Réévaluer les métriques et décider de l'acceptation MVP LAI

- **🎯 Recentrage LAI pour lai_weekly MVP (IMPLÉMENTÉ)**
  - **Statut** : 🟡 AMBER - Implémentation complétée, tests révèlent un problème de matching
  - **Objectif** : Newsletter très centrée LAI, même si trop strict (préférer manquer des news plutôt qu'avoir du bruit)
  - **Problème identifié** : Newsletter actuelle contient 37.5% de faux positifs (Pfizer Hympavzi, AbbVie Skyrizi, etc.)
  - **Documents** :
    - Diagnostic : `docs/diagnostics/lai_weekly_mvp_semantic_gap_analysis.md`
    - Plan : `docs/design/vectora_inbox_lai_mvp_focus_plan.md`
  - **Solution implémentée** :
    - ✅ Création du scope `lai_companies_mvp_core` (5 pure players LAI: MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
    - ✅ Matching avec ET logique pour domaines `technology` : exige (entity ET technology) au lieu de (entity OU technology)
    - ✅ Bonus scoring `pure_player_lai_bonus` (+3 points) pour favoriser les pure players LAI
    - ✅ Retrait des mots-clés LAI trop génériques (`PAS`, `DDS`) pour réduire les faux positifs
  - **Impact attendu** :
    - Précision LAI : 80-90% des items retenus clairement LAI (vs 37.5% avant)
    - Pure players LAI : ≥ 50% des items (vs 37.5% avant)
    - Zéro faux positif big pharma sans contexte LAI
  - **Prochaines étapes** :
    - ⏳ Re-packager et redéployer la Lambda engine avec les changements
    - ⏳ Re-lancer un run complet pour lai_weekly (7 jours) en DEV
    - ⏳ Valider les critères de succès (précision, représentation pure players)
    - ⏳ Documenter les résultats dans `docs/diagnostics/vectora_inbox_lai_mvp_focus_results.md`
- **✅ Correction Bedrock Output Tuning (COMPLÉTÉ)**
  - **Statut** : 🟢 GREEN - Problème de JSON tronqué résolu, newsletters complètes et lisibles
  - **Objectif** : Résoudre le problème de JSON tronqué et de Markdown non exploitable
  - **Document de plan** : `docs/design/vectora_inbox_bedrock_output_tuning_plan.md`
  - **Document de diagnostic** : `docs/diagnostics/vectora_inbox_bedrock_output_tuning_results.md`
  - **Problème initial** :
    - Réponse Bedrock tronquée au milieu d'une phrase ("...and geographic")
    - JSON incomplet et impossible à parser
    - Newsletter contenant du JSON brut tronqué au lieu de Markdown structuré
    - Champs `tldr` et `sections` vides
  - **Cause racine** : `max_tokens=3000` insuffisant pour générer un JSON complet avec 2 sections et 5 items
  - **Solution implémentée** :
    - ✅ Augmentation de `max_tokens` de 3000 à 8000 dans `bedrock_client.py`
    - ✅ Amélioration du prompt Bedrock : consignes renforcées pour JSON compact et concis
    - ✅ Ajout de "CRITICAL INSTRUCTIONS" pour éviter les balises markdown
    - ✅ Limitation explicite de la longueur des résumés (2-3 phrases max)
  - **Résultats** :
    - ✅ Newsletter complète : 3.1 KiB (vs 590 bytes avant) - **5.3x plus grande**
    - ✅ JSON parsé sans erreur, structure complète (title, intro, tldr, sections)
    - ✅ Markdown structuré et lisible (titre, intro, TL;DR, sections, items)
    - ✅ Temps d'exécution : 17.73s (vs 20.33s avant) - **13% plus rapide**
    - ✅ Qualité éditoriale : ton professionnel, textes concis, pas d'hallucination
  - **Impact** :
    - Coût par newsletter : ~$0.015 (vs ~$0.009 avant) - augmentation acceptable
    - Latence : Légèrement réduite malgré l'augmentation de max_tokens
    - Robustesse : Aucune erreur de parsing, logs propres
  - **Statut final** : Lambda `vectora-inbox-engine-dev` opérationnelle de bout en bout 🟢 GREEN

- **🔧 Patch formatage Markdown newsletter (ARCHIVÉ)**
  - **Statut** : 🔴 ÉCHEC - Le problème n'était pas le parsing mais la réponse Bedrock tronquée
  - **Objectif** : Corriger le problème de formatage de la newsletter (JSON brut → Markdown lisible)
  - **Document de plan** : `docs/design/vectora_inbox_newsletter_formatting_patch.md`
  - **Document de diagnostic** : `docs/diagnostics/vectora_inbox_engine_markdown_patch.md`
  - **Problème initial** :
    - Newsletter générée contient du JSON brut au lieu d'un Markdown structuré
    - Cause : Réponse Bedrock contient du JSON enveloppé dans des balises markdown (```json ... ```)
  - **Solution implémentée** :
    - ✅ Amélioration du parsing dans `bedrock_client.py` : détection et extraction des balises markdown
    - ✅ Modification de `assembler.py` : retour du contenu éditorial JSON en plus du Markdown
    - ✅ Modification de `__init__.py` : écriture de `newsletter.md` ET `newsletter.json` dans S3
    - ✅ Création des scripts de redéploiement et test (`redeploy-engine-markdown-patch.ps1`, `test-engine-markdown-patch.ps1`)
  - **Prochaines étapes** :
    - ⏳ Repackager et redéployer la Lambda engine
    - ⏳ Tester avec `lai_weekly` (7 jours)
    - ⏳ Vérifier que `newsletter.md` contient du Markdown lisible
    - ⏳ Vérifier que `newsletter.json` contient la structure éditoriale
    - ⏳ Mettre à jour le statut de AMBER → GREEN si succès

- **✅ Plan de déploiement et tests engine (COMPLÉTÉ)**
  - **Statut** : 🟢 GREEN - Lambda déployée, testée et opérationnelle de bout en bout
  - **Objectif** : Déployer la Lambda engine en DEV, tester le workflow complet, préparer stage/prod
  - **Document de plan** : `docs/design/vectora_inbox_engine_deploy_and_test_plan.md`
  - **Phase 1 - Wiring Infra & Déploiement DEV** :
    - ✅ Ajout des permissions CONFIG_BUCKET pour le rôle IAM Engine (lecture des configs client et scopes)
    - ✅ Ajout de la limite de concurrence pour la Lambda engine en DEV (ReservedConcurrentExecutions: 1)
    - ✅ Création du script `scripts/package-engine.ps1` (packaging et upload du code)
    - ✅ Création du script `scripts/deploy-runtime-dev.ps1` (déploiement de la stack s1-runtime)
    - ⏳ Packaging et upload du code engine dans S3
    - ⏳ Déploiement de la stack s1-runtime-dev avec les modifications
    - ⏳ Vérification du déploiement (Lambda engine opérationnelle)
  - **Phase 2 - Tests end-to-end** :
    - ✅ Création du script `scripts/test-engine-lai-weekly.ps1` (test complet ingest-normalize → engine)
    - ⏳ Exécution de ingest-normalize pour générer des items normalisés
    - ⏳ Exécution de engine pour générer la newsletter
    - ⏳ Vérification de la newsletter générée dans S3
    - ⏳ Consultation des logs CloudWatch
  - **Phase 3 - Diagnostics & Qualité** :
    - ✅ Création du template `docs/diagnostics/vectora_inbox_engine_first_run.md`
    - ⏳ Complétion du diagnostic avec les résultats du test
    - ⏳ Évaluation qualitative de la newsletter (ton, contenu, pertinence)
    - ⏳ Mise à jour du CHANGELOG avec le statut final
  - **Phase 4 - Préparation Stage/Prod** :
    - ✅ Design de la duplication d'infra (documenté dans le plan)
    - ✅ Stratégie de quotas Bedrock (documentée dans le plan)
    - ✅ Stratégie de monitoring et alertes (documentée dans le plan)
    - ✅ Stratégie de scheduling (documentée dans le plan)
  - **Résultats** :
    - ✅ Lambda déployée avec succès en DEV
    - ✅ Test end-to-end réussi (50 items analysés, 8 matchés, 5 sélectionnés)
    - ✅ Newsletter générée dans S3
    - ⚠️ Problème de formatage détecté (JSON brut au lieu de Markdown)
  - **Prochaines étapes** :
    - ⏳ Appliquer le patch de formatage Markdown
    - ⏳ Valider le nouveau format de newsletter
    - ⏳ Mettre à jour le statut de AMBER → GREEN
    - ⏳ Planifier le déploiement stage/prod (Phase 4)

- **✅ Lambda vectora-inbox-engine implémentée (COMPLÉTÉ)**
  - **Statut** : ✅ GREEN - Implémentation complète des Phases 2, 3 et 4
  - **Objectif** : Transformer les items normalisés en newsletter structurée avec Bedrock
  - **Document de design** : `docs/design/vectora_inbox_engine_lambda.md`
  - **Phase 2 - Matching** :
    - Module `src/vectora_core/matching/matcher.py` implémenté
    - Calcul des intersections d'ensembles (companies, molecules, technologies, indications)
    - Annotation des items avec `matched_domains` (list[str])
    - Logique déterministe et transparente (pas d'IA)
  - **Phase 3 - Scoring** :
    - Module `src/vectora_core/scoring/scorer.py` implémenté
    - Calcul des scores basé sur : event_type, priorité domaine, récence, type de source, profondeur du signal
    - Décroissance exponentielle de la récence (demi-vie 7 jours)
    - Tri des items par score décroissant
  - **Phase 4 - Génération de newsletter** :
    - Module `src/vectora_core/newsletter/assembler.py` : orchestration de la génération
    - Module `src/vectora_core/newsletter/bedrock_client.py` : appels Bedrock avec retry/backoff
    - Module `src/vectora_core/newsletter/formatter.py` : assemblage du Markdown final
    - Réutilisation du même mécanisme de retry que ingest-normalize (ThrottlingException)
    - Génération de : titre, intro, TL;DR, sections avec items reformulés
  - **Orchestration complète** :
    - Fonction `run_engine_for_client()` dans `src/vectora_core/__init__.py`
    - Collecte des items normalisés depuis S3 (fenêtre temporelle)
    - Gestion des cas limites : aucun item trouvé, échec Bedrock, config invalide
    - Écriture de la newsletter dans `s3://vectora-inbox-newsletters-dev/<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`
  - **Script de test** : `scripts/test-engine-lai-weekly.ps1`
  - **Prochaines étapes** :
    - Packager et déployer la Lambda engine en DEV
    - Test d'intégration complet : ingest-normalize → engine → newsletter
    - Créer le diagnostic `docs/diagnostics/vectora_inbox_engine_first_run.md`
    - Mettre à jour le CHANGELOG avec le statut final
- **✅ Mode mono-instance pour ingest-normalize en DEV (COMPLÉTÉ)**
  - **Statut** : ✅ GREEN - Configuration CloudFormation mise à jour
  - **Objectif** : Éliminer les invocations concurrentes en DEV pour réduire le throttling Bedrock
  - **Configuration** : `ReservedConcurrentExecutions = 1` pour l'environnement DEV uniquement
  - **Origine du problème** :
    - 3 invocations Lambda simultanées observées lors des tests manuels
    - Débit total vers Bedrock : ~12 appels simultanés (3 Lambdas × 4 workers)
    - Taux de throttling Bedrock : ~30-40%
  - **Solution implémentée** :
    - Ajout de `ReservedConcurrentExecutions: 1` dans `infra/s1-runtime.yaml`
    - Condition CloudFormation `IsDevEnvironment` pour appliquer uniquement en DEV
    - STAGE/PROD restent avec concurrence illimitée
  - **Impact attendu** :
    - Invocations séquentielles : une seule Lambda à la fois en DEV
    - Débit Bedrock réduit : ~4 appels simultanés max (1 Lambda × 4 workers)
    - Taux de throttling attendu : <10% (vs ~30-40% avant)
    - Taux d'échec final attendu : <2% (vs ~5-10% avant)
  - **Déploiement** :
    - Redéployer la stack `vectora-inbox-s1-runtime-dev` avec CloudFormation
    - Vérifier avec `aws lambda get-function-concurrency`
  - **Documentation** :
    - `docs/diagnostics/ingest_normalize_concurrency.md` : analyse complète
    - Explication de l'origine des invocations concurrentes (tests manuels)
    - Stratégie de montée en charge DEV → STAGE → PROD
  - **Prochaines étapes** :
    - Tester avec un batch complet (7 jours, 8 sources)
    - Valider que le taux de throttling est <10%
    - Demander une augmentation des quotas Bedrock pour STAGE/PROD

- **✅ Résilience Bedrock : Retry + réduction parallélisation (COMPLÉTÉ)**
  - **Statut** : ✅ GREEN - Mécanisme de retry implémenté et testé
  - **Objectif** : Réduire le taux d'erreurs ThrottlingException de ~10-15% à <5%
  - **Wrapper de retry** (`bedrock_client.py`) :
    - Fonction `_call_bedrock_with_retry()` avec backoff exponentiel
    - Max 3 retries (4 tentatives au total)
    - Délais : 0.5s, 1.0s, 2.0s avec jitter aléatoire
    - Détection automatique des ThrottlingException
    - Logging détaillé (WARNING à chaque retry, ERROR si échec final)
  - **Réduction de la parallélisation** (`normalizer.py`) :
    - Ajout de ThreadPoolExecutor avec `MAX_BEDROCK_WORKERS = 4`
    - Limite le débit vers Bedrock tout en gardant un traitement batch raisonnable
    - Gestion robuste des erreurs : les items en échec ne bloquent pas les autres
  - **Tests unitaires** (`tests/unit/test_bedrock_retry.py`) :
    - ✅ Retry réussi après ThrottlingException
    - ✅ Échec après épuisement des retries
    - ✅ Pas de retry sur erreur non-throttling
    - ✅ Succès dès la première tentative
  - **Documentation mise à jour** :
    - `docs/diagnostics/bedrock_sonnet45_success_final_dev.md` : section "Résilience et gestion du throttling"
    - Détails sur le comportement en production, monitoring recommandé, alertes
  - **Impact attendu** :
    - Taux de succès Bedrock : >95% (vs ~85-90% avant)
    - Temps d'exécution : +10-20% (acceptable pour un batch newsletter)
    - Robustesse accrue face aux pics de charge
  - **Compatibilité** :
    - ✅ ARN du inference profile inchangé : `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
    - ✅ Contrat d'entrée/sortie de la Lambda inchangé
    - ✅ Intégration avec l'infra (EventBridge, S3, IAM) inchangée
  - **Prochaines étapes** :
    - Tester en conditions réelles avec une exécution Lambda complète
    - Monitorer les métriques CloudWatch (taux de retry, échecs)
    - Ajuster MAX_BEDROCK_WORKERS si nécessaire (6-8 workers si quotas suffisants)

### Changed
- **✅ Migration réussie vers Claude Sonnet 4.5 - Environnement DEV (COMPLÉTÉE)**
  - **Statut** : ✅ GREEN - Migration complétée avec succès, normalisation Bedrock opérationnelle
  - **Profil d'inférence final** : `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` (profil EU multi-régions)
  - **Raison de la migration** : Les modèles Anthropic récents nécessitent un inference profile au lieu du modelId direct
  - **Résolution du problème** : Identification du bon inference profile ID via `aws bedrock list-inference-profiles`
  - **Tests de validation** :
    - ✅ Appel Bedrock direct réussi avec le profil EU
    - ✅ Lambda ingest-normalize opérationnelle (104 items ingérés, normalisation Bedrock fonctionnelle)
    - ✅ Extraction d'entités validée (companies: Eli Lilly, Novo Nordisk, Pfizer, AbbVie, etc.)
    - ✅ Extraction de molécules validée (olanzapine, risperidone)
    - ✅ Génération de résumés validée (~200 caractères par item)
  - **Infrastructure mise à jour** :
    - Stack `vectora-inbox-s1-runtime-dev` : paramètre `BedrockModelId` = `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
    - Lambda ingest-normalize : variable `BEDROCK_MODEL_ID` = `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
    - Lambda engine : variable `BEDROCK_MODEL_ID` = `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
  - **Profil d'inférence** :
    - Nom : EU Anthropic Claude Sonnet 4.5
    - Régions couvertes : eu-north-1, eu-west-3, eu-south-1, eu-south-2, eu-west-1, eu-central-1
    - Statut : ACTIVE
    - Type : SYSTEM_DEFINED
  - **Points de vigilance** :
    - ⚠️ Throttling observé (~10-15% des appels) lors d'invocations simultanées - comportement normal
    - ⚠️ Latence accrue (~3-5s par appel vs ~2-3s avec Claude 3 Sonnet)
    - ⚠️ Coûts légèrement supérieurs (~0.05-0.10 USD par exécution de 104 items)
  - **Diagnostic complet** : `docs/diagnostics/bedrock_sonnet45_success_final_dev.md`
  - **Prochaines étapes** : Tester la Lambda engine pour générer la première newsletter avec le nouveau modèle

### [Archivé] Tentatives de migration Claude Sonnet 4.5 (échecs)
- **Tentative 1** : Model ID direct `anthropic.claude-sonnet-4-5-20250929-v1:0` → Échec "inference profile required"
- **Tentative 2** : Profil EU incorrect `eu.anthropic.claude-sonnet-4-5-v2:0` → Échec "invalid model identifier"
- **Tentative 3** : Profil US incorrect `us.anthropic.claude-sonnet-4-5-v2:0` → Échec "invalid model identifier"
- **Solution finale** : Profil EU correct `eu.anthropic.claude-sonnet-4-5-20250929-v1:0` → ✅ Succès

### Redéploiement correctif sources MVP LAI en environnement DEV

- **Exécution complète du plan de redéploiement** (`docs/plans/plan_redeploiement_correctif_mvp_lai_dev.md`) :
  - Re-packaging de la Lambda `vectora-inbox-ingest-normalize-dev` avec BeautifulSoup4 et le code mis à jour (17.4 MB)
  - Upload du nouveau package ZIP dans `s3://vectora-inbox-lambda-code-dev/lambda/ingest-normalize/latest.zip`
  - Mise à jour du code de la fonction Lambda sur AWS avec `aws lambda update-function-code`
  - Re-upload des configurations mises à jour (`source_catalog.yaml` et `lai_weekly.yaml`) dans `s3://vectora-inbox-config-dev`
  - Invocation de test de la Lambda avec le payload `{"client_id":"lai_weekly","period_days":7}`
  - Analyse des résultats (logs CloudWatch, fichiers S3, statistiques d'exécution)

- **Résultats du test d'ingestion** (`docs/diagnostics/ingestion_mvp_lai_after_redeploy.md`) :
  - ✅ **Succès partiel** : 104 items ingérés depuis 7 sources sur 8 (87.5% de succès)
  - ✅ **Sources presse RSS** : 100% de succès (FierceBiotech 25 items, FiercePharma 25 items, Endpoints News 24 items)
  - ✅ **Sources corporate HTML** : 60% de succès (MedinCell 12 items, DelSiTech 10 items, Nanexa 8 items)
  - ⚠️ **Camurus** : 0 items (structure HTML non reconnue par le parser générique)
  - ❌ **Peptron** : 0 items (erreur SSL - certificat invalide)
  - ⚠️ **Normalisation Bedrock** : Erreurs d'accès (AccessDeniedException) - le modèle Claude 3 Sonnet nécessite une souscription AWS Marketplace
  - ✅ **Écriture S3** : Fichier `normalized/lai_weekly/2025/12/08/items.json` créé avec succès (60 188 caractères)
  - **Temps d'exécution** : 21.95 secondes

- **Correction d'un bug d'import** :
  - Ajout de l'import `Optional` manquant dans `src/vectora_core/ingestion/parser.py`
  - Ce bug causait une erreur `NameError: name 'Optional' is not defined` lors de la première invocation
  - Correction appliquée et Lambda re-déployée immédiatement

- **Points de vigilance identifiés** :
  - Le parser HTML générique fonctionne sur 60% des sources corporate (3/5)
  - Certaines structures HTML complexes (Camurus) nécessitent des parsers spécifiques
  - L'accès Bedrock doit être activé via AWS Marketplace pour permettre la normalisation complète
  - La source Peptron doit être désactivée ou son URL corrigée (problème de certificat SSL)

- **Prochaines étapes** :
  - Activer l'accès au modèle Claude 3 Sonnet sur AWS Marketplace
  - Améliorer le parser HTML pour Camurus ou créer un parser spécifique
  - Corriger ou désactiver la source Peptron
  - Tester la Lambda engine pour générer la première newsletter

### Plan correctif sources MVP LAI exécuté

- **Création et exécution du plan correctif** (`docs/plans/plan_correctif_sources_mvp_lai.md`) :
  - Plan complet en 7 phases pour rendre le pipeline d'ingestion robuste et aware de `ingestion_mode`
  - Introduction des champs `ingestion_mode` (rss/html/api/none), `enabled` (true/false), `homepage_url`, `rss_url`, `html_url` dans le modèle de source
  - Distinction claire entre univers métier exhaustif (_universe) et intégration technique progressive (_mvp)
  - Création de 4 bouquets LAI : `lai_corporate_universe`, `lai_press_universe`, `lai_corporate_mvp`, `lai_press_mvp`

- **Nouveau modèle de source_catalog.yaml** :
  - Remplacement de l'ancien catalogue par un nouveau modèle avec 8 sources MVP activées
  - 5 sources corporate LAI prioritaires (MedinCell, Camurus, DelSiTech, Nanexa, Peptron) avec `ingestion_mode: "html"` et `enabled: true`
  - 3 sources presse (FierceBiotech, FiercePharma, Endpoints News) avec `ingestion_mode: "rss"` et `enabled: true`
  - Bouquets `lai_corporate_mvp` (5 sources) et `lai_press_mvp` (3 sources) pour le MVP
  - Ancien catalogue sauvegardé dans `source_catalog_backup.yaml`

- **Évolution du code Python** :
  - `config/resolver.py` : ajout du filtrage sur `enabled: true` et `ingestion_mode != "none"` avec logs clairs
  - `ingestion/fetcher.py` : branchement selon `ingestion_mode` (rss → rss_url, html → html_url, none → skip)
  - `ingestion/parser.py` : ajout d'un parser HTML générique (KISS) avec BeautifulSoup pour extraire des items depuis des pages HTML
  - Parser HTML cherche des patterns courants (`<article>`, divs avec class 'news'/'post'/'press') et extrait titre, URL, description
  - Gestion robuste des erreurs : si une source échoue, le pipeline continue avec les autres sources

- **Mise à jour de lai_weekly.yaml** :
  - Utilisation des nouveaux bouquets `lai_press_mvp` et `lai_corporate_mvp`
  - Total de 8 sources activées pour l'ingestion automatique (3 presse RSS + 5 corporate HTML)
  - Commentaires mis à jour pour refléter le nouveau modèle

- **Résultat attendu** :
  - Le pipeline d'ingestion devrait maintenant produire `items_ingested > 0` lors de l'invocation de la Lambda
  - Au moins 3-5 sources devraient produire des items (presse RSS + quelques sources corporate HTML)
  - Le système est robuste aux sources en échec et continue avec les autres
  - Les logs sont clairs et permettent de diagnostiquer les problèmes

### Déploiement MVP LAI - Environnement DEV

- **Création du plan de déploiement CLI complet** (`docs/plans/plan_deploiement_cli_mvp_lai.md`) :
  - Plan détaillé en français couvrant 6 phases : prérequis, validation templates, packaging Lambda, déploiement CloudFormation, chargement configurations, test et vérification.
  - Toutes les commandes PowerShell nécessaires pour déployer l'environnement DEV (compte 786469175371, région eu-west-3, profil rag-lai-prod).
  - Explications pédagogiques pour chaque étape avec résultats attendus.
  - Section de dépannage et commandes de diagnostic.
  - Prochaines étapes après déploiement réussi (test engine, itération configs, déploiement STAGE).

- **Création du diagnostic de déploiement** (`docs/diagnostics/deploiement_mvp_lai_dev.md`) :
  - Résumé exécutif du statut (PRÊT POUR EXÉCUTION MANUELLE).
  - Documentation des ressources qui seront créées (stacks, buckets, rôles, Lambdas).
  - Points de vigilance (token SSO, bucket artefacts, dépendances Python, permissions IAM).
  - Commandes de diagnostic pour vérifier l'état du déploiement.
  - Prochaines étapes après déploiement réussi.

- **Exécution réussie du déploiement DEV (Phases 1-3)** :
  - ✅ Phase 1 : Validation des 3 templates CloudFormation (s0-core, s0-iam, s1-runtime)
  - ✅ Phase 2 : Packaging et upload des Lambdas vers S3 (ingest-normalize.zip 17MB, engine.zip 17MB)
  - ✅ Phase 3 : Déploiement des 3 stacks CloudFormation :
    - Stack `vectora-inbox-s0-core-dev` : 3 buckets S3 créés (config, data, newsletters)
    - Stack `vectora-inbox-s0-iam-dev` : 2 rôles IAM créés (IngestNormalizeRole, EngineRole)
    - Stack `vectora-inbox-s1-runtime-dev` : 2 fonctions Lambda créées (ingest-normalize-dev, engine-dev)
  - Outputs sauvegardés dans `infra/outputs/` (s0-core-dev.json, s0-iam-dev.json, s1-runtime-dev.json)
  - Infrastructure complète déployée et opérationnelle en environnement DEV

- Alignement entre l'infra S1-runtime (`infra/s1-runtime.yaml`) et le code Python
  (`src/`) : vérification des handlers Lambda (chemins de modules) et harmonisation
  des variables d'environnement utilisées par les fonctions (`CONFIG_BUCKET`,
  `DATA_BUCKET`, `NEWSLETTERS_BUCKET`, `BEDROCK_MODEL_ID`, etc.). Mise à jour de
  la documentation (`infra/README.md` et `src/README.md`) pour expliquer de
  manière pédagogique comment les Lambdas sont câblées au code et aux buckets S3.
  Les handlers sont confirmés alignés (`handler.lambda_handler` dans l'infra →
  `lambda_handler(event, context)` dans le code). Les variables d'environnement
  sont parfaitement alignées entre l'infra et le code pour les deux Lambdas.
  Ajout de tableaux de mapping et d'exemples concrets pour faciliter la compréhension
  par un débutant.
- Mise en place de la structure de code `src/` avec les deux points d'entrée Lambda
  (`vectora-inbox-ingest-normalize` et `vectora-inbox-engine`) et le package `vectora_core`
  contenant les squelettes de modules métier (config, ingestion, normalisation, matching,
  scoring, newsletter, storage, utils). Les handlers Lambda sont minces et délèguent toute
  la logique métier à `vectora_core`. Pour l'instant, les modules contiennent principalement
  des squelettes avec signatures de fonctions, docstrings en français et TODOs. La logique
  métier complète sera implémentée dans des étapes suivantes. Ajout de `requirements.txt`
  avec les dépendances minimales (boto3, pyyaml, requests, feedparser, python-dateutil)
  et de `src/README.md` expliquant l'architecture et l'état actuel du code.
- Ajout de la stack S1-runtime (`infra/s1-runtime.yaml`) pour définir les deux
  fonctions Lambda principales (ingest-normalize et engine) avec leurs variables
  d'environnement, log groups CloudWatch, et connexions aux buckets S3 et rôles IAM.
  Mise à jour de `infra/README.md` pour documenter le rôle de chaque Lambda,
  leurs paramètres, et un exemple de déploiement PowerShell.
- Ajout de la stack IAM S0 (`infra/s0-iam.yaml`) pour créer les rôles IAM des
  futures Lambdas (`vectora-inbox-ingest-normalize` et `vectora-inbox-engine`)
  avec les permissions S3, Logs, SSM (PubMed) et Bedrock nécessaires au MVP.
- Ajout de l'infrastructure S0-core (template `infra/s0-core.yaml`) pour créer
  les trois buckets S3 de base (`config`, `data`, `newsletters`) et d'un
  `infra/README.md` expliquant comment déployer la stack via CLI en eu-west-3.

### Phase 2 : Confort développeur (suite)

- **[2.8]** Mise à jour de `.q-context/vectora-inbox-q-rules.md` pour que Amazon Q Developer lise systématiquement `docs/diagnostics/vectora-inbox-deep-diagnostic.md` et `.q-context/vectora-inbox-overview.md` avant toute modification importante (architecture, canonical, contrats, infra, code).
  - Ajout d'une nouvelle section "Priorité de lecture pour Amazon Q Developer" expliquant quand et pourquoi consulter ces deux documents de référence.
  - Clarification de la différence entre `.q-context/` (brain court terme) et `docs/diagnostics/` (vue 360° détaillée).
  - Renumérotation des sections suivantes pour maintenir la cohérence du document.

### Phase 2 : Confort développeur (suite)

- **[2.7]** Rédaction de `docs/vectora-inbox-deep-diagnostic.md` : diagnostic complet
  et pédagogique 360° sur Vectora Inbox (MVP LAI, architecture, gouvernance,
  extensibilité, préparation à l'infrastructure et au code).
  - Résumé exécutif : vision produit, état actuel, points forts, points de vigilance, verdict GREEN.
  - Objectifs produit et promesse client : à quoi sert Vectora Inbox, ce que la newsletter apporte.
  - Architecture fonctionnelle : workflow end-to-end en 5 phases (configuration, ingestion, normalisation, matching, scoring, génération).
  - Architecture technique : vue AWS sans code (3 buckets S3, 2 Lambdas, Bedrock, IAM, région eu-west-3).
  - Gouvernance et configuration : canonical/scopes, catalogue de sources et bouquets, règles de scoring, configs client.
  - Rôle de Bedrock : où Bedrock intervient (normalisation, génération éditoriale) et où il n'intervient pas (ingestion, matching, scoring).
  - Extensibilité multi-verticales et multi-clients : comment ajouter une nouvelle verticale, gérer plusieurs clients.
  - État de préparation : risques traités, points de vigilance, verdict GREEN pour l'infrastructure et le code.
  - Recommandations et prochaines étapes : étapes immédiates (infra + code MVP), court terme (enrichissement, APIs), moyen terme (nouvelles verticales, industrialisation).

### Phase 2 : Confort développeur (suite)

- **[2.6]** Ajout des sources d'API globales (PubMed, ClinicalTrials.gov, FDA labels)
  dans `canonical/sources/source_catalog.yaml`, ainsi que des bouquets LAI
  associés pour préparer l'ingestion scientifique et réglementaire :
  - Trois nouvelles sources API : `science_pubmed_api`, `trials_ctgov_api`, `reg_fda_labels_api`.
  - Trois nouveaux bouquets LAI : `science_pubmed_lai`, `trials_ctgov_lai`, `reg_fda_labels_lai`.
  - Tous les commentaires et descriptions sont en français, adaptés pour les débutants.
  - Les sources sont groupées dans une section dédiée "Sources d'API scientifiques & réglementaires".
  - Les bouquets sont groupés dans une section dédiée "Bouquets scientifiques & réglementaires (APIs)".


- **[2.5]** Ajout de `client-config-examples/README.md` comme guide pour créer et maintenir les configurations clients :
  - Explication pédagogique du rôle d'une config client (identité, verticale, fréquence, bouquets, scopes).
  - Inventaire complet des scopes disponibles (entreprises, molécules, technologies, trademarks, exclusions, indications) avec description de chaque clé.
  - Inventaire des bouquets de sources disponibles (corporate LAI, presse biotech/pharma) avec description.
  - Guide pas-à-pas pour créer une nouvelle config client (choisir la verticale, les bouquets, les scopes, les paramètres de base, tester progressivement).
  - Exemple de config client minimal commenté en français, basé sur `lai_weekly.yaml` mais simplifié.
  - Section FAQ et ressources complémentaires pour faciliter la maintenance.

### Phase 1 : Cohérence MVP LAI

- **[1.1]** Correction et simplification de `client-config-examples/lai_weekly.yaml` :
  - Alignement de toutes les références de scopes avec les clés existantes dans `canonical/scopes/*`
    (`lai_keywords`, `lai_companies_global`, `lai_molecules_global`).
  - Ajout de la section `source_config` avec `source_bouquets_enabled` pour utiliser les bouquets
    `lai_corporate_mvp` et `press_biotech_premium`.
  - Commentaire des scopes non-MVP (addiction, schizophrenia) qui ne sont pas encore remplis.
  - Simplification de la structure de la newsletter (2 sections principales pour le MVP).
  - Tous les commentaires convertis en français avec explications pour débutants.

- **[1.2]** Création du bouquet `lai_corporate_mvp` dans `canonical/sources/source_catalog.yaml` :
  - Sous-bouquet MVP avec 8 sources corporate LAI représentatives ayant des URLs valides
    (MedinCell, Camurus, G2GBio, Alkermes, Indivior, Ascendis Pharma, Novo Nordisk, Ipsen).
  - Permet de tester l'ingestion avec un ensemble réaliste et gérable de sources LAI.

- **[1.3]** Ajout des seuils de sélection dans `canonical/scoring/scoring_rules.yaml` :
  - Nouvelle section `selection_thresholds` avec `min_score: 10` (score minimum pour inclusion)
    et `min_items_per_section: 1` (nombre minimum d'items par section).
  - Permet à la Lambda engine de décider quels items inclure dans la newsletter finale.

- **[1.4]** Clarification de la résolution des bouquets dans `contracts/lambdas/vectora-inbox-ingest-normalize.md` :
  - Ajout d'une section détaillée expliquant comment la Lambda doit résoudre les bouquets de sources.
  - Processus en 4 étapes : lecture de `source_bouquets_enabled`, chargement des définitions de bouquets,
    agrégation des `source_keys`, déduplication.
  - Exemples concrets avec `lai_corporate_mvp` et `press_biotech_premium`.
  - Explication de la priorité entre paramètre d'événement et configuration client.

- **[1.5]** Clarification du chargement des scopes dans `contracts/lambdas/vectora-inbox-engine.md` :
  - Ajout d'un résumé détaillé du processus de chargement des scopes canonical en 5 étapes.
  - Exemple de code pseudo-Python montrant comment charger les scopes via les clés et calculer les intersections.
  - Clarification que les Lambdas ne "connaissent" pas la verticale, elles manipulent juste des ensembles
    identifiés par leurs clés.

### Phase 2 : Confort développeur

- **[2.1]** Ajout d'exemples JSON d'entrée/sortie dans les contrats des 2 Lambdas :
  - `vectora-inbox-ingest-normalize.md` : 3 exemples d'entrée (exécution standard, fenêtre temporelle,
    sources spécifiques) et 3 exemples de sortie (succès, erreur partielle, erreur critique).
  - `vectora-inbox-engine.md` : 2 exemples d'entrée et 4 exemples de sortie (succès, erreur Bedrock,
    aucune donnée, configuration invalide).
  - Tous les exemples sont réalistes et directement utilisables pour les tests.

- **[2.2]** Création de `canonical/README.md` :
  - Documentation complète de la structure du répertoire `canonical/` (scopes, sources, scoring, imports).
  - Explication du pattern de nommage `{verticale}_{dimension}_{segment}` avec exemples concrets.
  - Guide pratique : comment ajouter une entreprise ou un mot-clé dans un scope.
  - Clarification du rôle des Lambdas : elles manipulent des listes via des clés, sans "connaître" la verticale.
  - Section FAQ et bonnes pratiques pour faciliter la maintenance.

- **[2.3]** Création de `canonical/scoring/scoring_examples.md` :
  - 4 exemples détaillés de calcul de score pas-à-pas (score élevé, moyen, faible, réglementaire).
  - Tableau synthétique comparant les 4 exemples (type d'événement, récence, score, inclusion).
  - Explication des principes clés du scoring (type d'événement, récence, compétiteurs, domaine, source).
  - Guide pratique : comment ajuster les poids dans `scoring_rules.yaml` si nécessaire.

- **[2.4]** Création de `contracts/README.md` :
  - Explication du rôle des contrats métier (spécifications pour développeurs, architectes, Amazon Q).
  - Liste des contrats disponibles avec description de leur contenu (ingest-normalize, engine).
  - Guide d'utilisation : comment lire les contrats, utiliser les exemples JSON, respecter les spécifications.
  - Clarification des différences entre `contracts/`, `canonical/` et `.q-context/`.
  - Bonnes pratiques et FAQ pour faciliter la maintenance des contrats.

- Initialisation des règles de scoring dans `scoring_rules.yaml` avec des poids
  métier par type d'évènement, priorité de domaine et facteurs additionnels
  (compétiteurs, molécules clés, récence, type de source).
- Réorganisation de `canonical/sources/source_catalog.yaml` en sections lisibles
  (sources corporate LAI, presse pharma/biotech premium) avec ajout de commentaires
  visuels en français pour améliorer la navigation, sans modification du contenu métier.
- Ajout des sources de presse sectorielle FiercePharma, FierceBiotech,
  FierceHealthcare et Endpoints News dans `canonical/sources/source_catalog.yaml`
  et inclusion dans le bouquet `press_biotech_premium`.
- Initialisation d'un bouquet de presse sectorielle pharma/biotech premium
  dans `canonical/sources/source_catalog.yaml` (sources `press_sector__*`)
  et alimentation du bouquet `press_biotech_premium`.
- Création/mise à jour des sources corporate LAI dans `canonical/sources/source_catalog.yaml`
  à partir de `company_seed_lai.csv`, et alimentation du bouquet `lai_corporate_all`
  avec l'ensemble des `source_key` corporate LAI.
- Mise à jour du scope `lai_companies_global` dans `canonical/scopes/company_scopes.yaml`
  à partir du fichier d'amorçage `company_seed_lai.csv` (liste exhaustive des sociétés LAI).
- Ajout de la structure `sources` + `bouquets` dans `canonical/sources/source_catalog.yaml`
  pour gérer un catalogue global de sources et des bouquets réutilisables (ex: `lai_corporate_all`,
  `press_biotech_premium`).
- Initialisation des scopes LAI globaux dans `canonical/scopes/*.yaml`
  à partir de l'export `canonical/imports/vectora-inbox-lai-core-scopes.yaml`
  (entreprises, molécules, trademarks, mots-clés LAI, termes d'exclusion).
