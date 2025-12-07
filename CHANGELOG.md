# Changelog

## [Unreleased]

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
