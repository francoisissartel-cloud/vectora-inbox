# Diagnostic complet et pédagogique – Vectora Inbox MVP LAI

**Document de référence pour comprendre l'état actuel du projet et sa préparation à l'étape "infrastructure + code".**

---

## Résumé exécutif

Vectora Inbox est un moteur de veille sectorielle configurable conçu pour automatiser la surveillance compétitive dans les secteurs biotech et pharma. Le produit transforme des dizaines de sources d'information hétérogènes (sites web d'entreprises, presse spécialisée, bases de données scientifiques) en newsletters professionnelles et structurées, adaptées aux besoins spécifiques de chaque client.

Le projet se concentre actuellement sur un MVP (Minimum Viable Product) pour la verticale LAI (Long-Acting Injectables), un segment pharmaceutique stratégique. L'architecture repose sur trois piliers : des buckets S3 pour stocker les configurations et les données, deux fonctions Lambda pour orchestrer le traitement, et Amazon Bedrock comme "cerveau linguistique" pour comprendre et rédiger les contenus.

Les principaux points forts du projet sont : une gouvernance entièrement pilotée par configuration (pas de logique métier codée en dur), une séparation claire entre les tâches déterministes (matching, scoring) et les tâches linguistiques (normalisation, rédaction), et une extensibilité multi-verticales et multi-clients sans modification de code. Le catalogue de sources compte déjà 180+ entreprises LAI et 19 sources de presse spécialisée, organisés en bouquets réutilisables. Les règles de scoring sont documentées et ajustables, et les contrats métier des deux Lambdas sont complets et précis.

Les points de vigilance concernent principalement la phase d'implémentation : il faudra gérer les erreurs et timeouts des sources externes, surveiller les coûts potentiels (appels Bedrock et APIs externes), et tester progressivement sur un volume limité avant d'élargir. Certaines URLs de sources restent à compléter manuellement, et les scopes d'indications thérapeutiques (addiction, psychiatrie) ne sont pas encore remplis, mais cela n'impacte pas le MVP.

En l'état actuel, le projet est prêt (verdict GREEN) pour la définition de l'infrastructure AWS et la génération des premières Lambdas pour le MVP LAI, avec une complexité maîtrisée et une architecture claire.

---

## Objectifs produit et promesse client

### Qu'est-ce que Vectora Inbox ?

Vectora Inbox est un produit conçu pour résoudre un problème concret : comment suivre efficacement l'actualité d'un secteur complexe (biotech/pharma) sans y passer des heures chaque jour ?

Pour un consultant indépendant ou une petite équipe de veille stratégique, surveiller manuellement des dizaines de sites web, flux RSS et bases de données est chronophage et peu fiable. On risque de manquer des signaux importants (résultats d'essais cliniques, partenariats stratégiques, approbations réglementaires) ou de se noyer dans le bruit (communiqués sans intérêt, offres d'emploi, webinaires).

Vectora Inbox automatise cette veille en :
- **Collectant** automatiquement les actualités depuis des sources pertinentes (sites d'entreprises, presse spécialisée, PubMed, ClinicalTrials.gov, FDA)
- **Filtrant** intelligemment les contenus selon les domaines d'intérêt du client (technologies, indications thérapeutiques, entreprises clés)
- **Priorisant** les signaux les plus importants grâce à un système de scoring transparent
- **Rédigeant** une newsletter professionnelle et structurée, avec des résumés clairs et un ton adapté

### À quoi sert Vectora Inbox pour un client ?

Concrètement, un client de Vectora Inbox reçoit chaque semaine (ou chaque mois) une newsletter qui répond à des questions stratégiques :
- Quelles sont les avancées cliniques majeures dans mon domaine cette semaine ?
- Quels partenariats ou acquisitions ont été annoncés ?
- Quelles approbations réglementaires ont été obtenues ?
- Quelles entreprises concurrentes ont publié des résultats importants ?

Au lieu de passer 5 à 10 heures par semaine à parcourir des dizaines de sites, le client consacre 15 à 30 minutes à lire une newsletter ciblée et actionnable.

### Ce que la newsletter apporte par rapport à une veille manuelle

Une newsletter Vectora Inbox n'est pas une simple agrégation de flux RSS. Elle apporte :

1. **Filtrage métier intelligent** : seuls les contenus pertinents pour les domaines surveillés sont inclus (pas de bruit)
2. **Priorisation** : les signaux les plus importants remontent en tête (résultats cliniques, partenariats, approbations)
3. **Résumés de qualité** : chaque item est résumé en 2-3 phrases claires, rédigées par Bedrock dans le ton du client
4. **Structure professionnelle** : sections thématiques, TL;DR exécutif, introduction contextuelle
5. **Gain de temps massif** : 15 minutes de lecture au lieu de plusieurs heures de recherche manuelle

### Cible principale : biotech/pharma

Le produit cible principalement :
- **Consultants indépendants** en stratégie biotech/pharma
- **Petites équipes de veille** dans des fonds d'investissement ou des entreprises pharma
- **Business developers** qui doivent suivre l'actualité de leur secteur
- **Analystes financiers** spécialisés en biotech

Le MVP se concentre sur la verticale LAI (Long-Acting Injectables), un segment pharmaceutique en forte croissance, avec des applications en psychiatrie, addiction, diabète, oncologie, etc.

---

## Architecture fonctionnelle (workflow end-to-end)

Cette section décrit le workflow de Vectora Inbox au niveau "métier", sans entrer dans les détails techniques du code. L'objectif est de comprendre comment les données circulent, de l'ingestion des sources jusqu'à la newsletter finale.

### Vue d'ensemble : 5 phases principales

Le workflow Vectora Inbox se décompose en 5 phases :

0. **Configuration** (manuelle, avant l'exécution)
1. **Ingestion** (récupération des données brutes depuis les sources externes)
2. **Normalisation** (transformation des textes bruts en items structurés et enrichis)
3. **Matching** (détermination des items pertinents pour chaque client)
4. **Scoring** (priorisation des items par importance)
5. **Génération de la newsletter** (assemblage et rédaction finale)

### Phase 0 : Configuration (manuelle)

Avant toute exécution automatique, un administrateur configure :

**Les scopes canonical** (bibliothèque métier globale) :
- Listes d'entreprises LAI (environ 180 sociétés : Camurus, Alkermes, MedinCell, Novo Nordisk, etc.)
- Listes de molécules LAI (environ 90 molécules : buprenorphine, paliperidone, semaglutide, etc.)
- Listes de technologies (mots-clés : "long acting", "depot injection", "PLGA microspheres", etc.)
- Listes d'indications thérapeutiques (mots-clés : "opioid use disorder", "schizophrenia", etc.)
- Mots-clés d'exclusion (pour filtrer le bruit : "job posting", "webinar", etc.)

**Le catalogue de sources** :
- Définition de toutes les sources disponibles (URLs, types, tags)
- Organisation en bouquets réutilisables (ex : "lai_corporate_mvp" = 8 sites corporate LAI pour tester)

**Les règles de scoring** :
- Poids par type d'événement (clinique = 5, partenariat = 6, corporate = 2, etc.)
- Poids par priorité de domaine (high = 3, medium = 2, low = 1)
- Facteurs additionnels (bonus compétiteurs, récence, type de source)

**La configuration client** :
- Identité du client (nom, langue, ton, fréquence)
- Domaines de veille (quels scopes activer, quelle priorité)
- Bouquets de sources à utiliser
- Structure de la newsletter (sections, nombre d'items par section)

Cette phase est entièrement manuelle et pilotée par des fichiers YAML stockés dans S3.

### Phase 1 : Ingestion (sans IA)

**Objectif** : récupérer les contenus bruts depuis les sources externes.

**Comment ça marche** :
- La Lambda `vectora-inbox-ingest-normalize` lit la configuration client pour savoir quelles sources activer
- Elle résout les bouquets (ex : "lai_corporate_mvp" → 8 sources corporate LAI)
- Pour chaque source, elle effectue un appel HTTP (flux RSS ou API)
- Elle parse la réponse (XML pour RSS, JSON pour APIs)
- Elle extrait les champs de base : titre, description, URL, date de publication

**Entrées** : URLs des sources (définies dans le catalogue)

**Sorties** : liste d'items bruts en mémoire (titre, description, URL, date, source)

**Pas d'IA ici** : c'est de la "plomberie" HTTP pure (requêtes, parsing, stockage temporaire)

### Phase 2 : Normalisation (avec Bedrock)

**Objectif** : transformer chaque item brut en item structuré et enrichi.

**Comment ça marche** :
- Pour chaque item brut, la Lambda construit un prompt pour Bedrock
- Le prompt contient : le texte de l'item + des exemples d'entités à détecter (entreprises, molécules, technologies) + les types d'événements possibles
- Bedrock analyse le texte et retourne : un résumé court (2-3 phrases), le type d'événement (ex : "clinical_update"), les entités détectées (entreprises, molécules, technologies, indications)
- La Lambda complète avec des règles déterministes (détection par mots-clés, validation des entités)
- Elle produit un item normalisé avec tous les champs structurés

**Entrées** : items bruts + scopes canonical + prompts Bedrock

**Sorties** : items normalisés (JSON structuré avec entités détectées, type d'événement, résumé)

**Rôle de Bedrock** : comprendre le texte, extraire les entités, classifier l'événement, générer un résumé

**Ce qui est déterministe** : détection par mots-clés, validation des entités, filtrage par exclusions

### Phase 3 : Matching (sans IA)

**Objectif** : déterminer quels items sont pertinents pour quels domaines de veille du client.

**Comment ça marche** :
- La Lambda `vectora-inbox-engine` charge les items normalisés depuis S3
- Elle lit la configuration client pour connaître les domaines de veille (ex : "tech_lai_ecosystem", "regulatory_lai")
- Pour chaque domaine, elle charge les scopes canonical correspondants (entreprises, molécules, technologies)
- Pour chaque item, elle calcule des intersections : les entreprises détectées dans l'item sont-elles dans le scope d'entreprises du domaine ? Les molécules détectées sont-elles dans le scope de molécules ?
- Si au moins une intersection est non vide, l'item est matché au domaine

**Entrées** : items normalisés + configuration client + scopes canonical

**Sorties** : items annotés avec leurs domaines de correspondance

**Logique** : intersections d'ensembles (déterministe, transparent, expliquable)

**Pas d'IA ici** : tout est basé sur des règles et des listes prédéfinies

### Phase 4 : Scoring (sans IA)

**Objectif** : attribuer un score numérique à chaque item pour prioriser les plus importants.

**Comment ça marche** :
- Pour chaque item matché, la Lambda calcule un score en combinant plusieurs facteurs :
  - Type d'événement (clinique/réglementaire = score élevé, corporate = score plus faible)
  - Récence (items récents = score plus élevé, avec décroissance exponentielle)
  - Priorité du domaine (domaines "high priority" = boost de score)
  - Présence de compétiteurs clés (bonus si l'item mentionne une entreprise prioritaire)
  - Présence de molécules clés (bonus si l'item mentionne une molécule prioritaire)
  - Type de source (sources réglementaires > sources cliniques > presse)
- Les items sont triés par score décroissant au sein de chaque domaine
- Seuls les top N items par section sont retenus pour la newsletter

**Entrées** : items matchés + règles de scoring (poids, facteurs, seuils)

**Sorties** : items scorés et triés

**Logique** : formules numériques transparentes (pas de boîte noire)

**Pas d'IA ici** : tout est calculé avec des règles explicites et ajustables

### Phase 5 : Génération de la newsletter (avec Bedrock)

**Objectif** : assembler une newsletter professionnelle, structurée et lisible.

**Comment ça marche** :
- La Lambda sélectionne les top N items par section (selon la configuration client)
- Elle construit un prompt pour Bedrock contenant : la liste des items retenus + le contexte de la semaine + les attentes sur le ton et la structure
- Bedrock génère : un titre de newsletter, une introduction (chapeau), un TL;DR (3-5 bullet points résumant les signaux clés), des intros de sections, des reformulations des items dans le ton du client
- La Lambda assemble le tout en Markdown : titre, intro, TL;DR, sections avec items, liens vers les sources

**Entrées** : items scorés et sélectionnés + configuration client (ton, voice, langue, structure)

**Sorties** : newsletter en Markdown stockée dans S3

**Rôle de Bedrock** : rédaction éditoriale (intros, TL;DR, reformulations)

**Ce qui est déterministe** : sélection des items, structure de la newsletter, assemblage du Markdown

### Distinction entre tâches déterministes et tâches linguistiques

**Bedrock est utilisé pour** :
- Comprendre le sens d'un texte (Phase 2 : normalisation)
- Extraire des entités (entreprises, molécules, technologies)
- Classifier des événements (clinique, partenariat, réglementaire)
- Rédiger des contenus (résumés, intros, TL;DR) (Phase 5 : génération)

**Bedrock n'est PAS utilisé pour** :
- Récupérer les données (Phase 1 : ingestion HTTP)
- Décider si un item est pertinent (Phase 3 : matching par intersections)
- Calculer des scores (Phase 4 : scoring numérique)

Cette séparation garantit que la logique métier reste transparente, expliquable et ajustable, tout en bénéficiant de la puissance de l'IA pour les tâches linguistiques complexes.

---

## Architecture technique (vue AWS, sans code)

Cette section explique les briques AWS qui seront créées pour faire fonctionner Vectora Inbox, sans entrer dans les détails de code ou de CloudFormation.

### Les 3 buckets S3

Vectora Inbox repose sur 3 buckets S3, chacun avec un rôle spécifique :

**1. `vectora-inbox-config`** (configurations)
- **Rôle** : stocker les configurations canoniques (scopes partagés) et les configurations par client
- **Contenu** :
  - `canonical/scopes/*.yaml` : listes d'entreprises, molécules, technologies, indications, exclusions
  - `canonical/sources/source_catalog.yaml` : catalogue de sources et bouquets
  - `canonical/scoring/scoring_rules.yaml` : règles de scoring
  - `clients/<client_id>.yaml` : configuration de chaque client (domaines de veille, bouquets activés, structure de newsletter)
- **Accès** : lecture par les 2 Lambdas, écriture manuelle par l'admin

**2. `vectora-inbox-data`** (données)
- **Rôle** : stocker les items bruts (optionnel, pour debug) et les items normalisés (obligatoire)
- **Structure** :
  - `raw/<client_id>/<source_key>/<YYYY>/<MM>/<DD>/raw.json` : items bruts par source (optionnel)
  - `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json` : items normalisés agrégés (obligatoire)
- **Accès** : écriture par `vectora-inbox-ingest-normalize`, lecture par `vectora-inbox-engine`

**3. `vectora-inbox-newsletters`** (newsletters)
- **Rôle** : stocker les newsletters générées
- **Structure** :
  - `<client_id>/<YYYY>/<MM>/<DD>/newsletter.md` : newsletter en Markdown
- **Accès** : écriture par `vectora-inbox-engine`, lecture par le client (ou système de distribution)

### Les 2 fonctions Lambda

**1. `vectora-inbox-ingest-normalize`** (Phase 1)
- **Rôle** : ingestion des sources externes + normalisation avec Bedrock
- **Déclenchement** : manuel (MVP) ou EventBridge (futur)
- **Entrées** : événement JSON avec `client_id`, `period_days` (optionnel), `sources` (optionnel)
- **Sorties** : fichier `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json` dans S3
- **Utilise Bedrock** : oui (pour la normalisation)
- **Durée estimée** : quelques minutes (dépend du nombre de sources)

**2. `vectora-inbox-engine`** (Phases 2, 3, 4)
- **Rôle** : matching + scoring + génération de newsletter
- **Déclenchement** : manuel (MVP) ou EventBridge (futur)
- **Entrées** : événement JSON avec `client_id`, `period_days` (optionnel), `target_date` (optionnel)
- **Sorties** : fichier `<client_id>/<YYYY>/<MM>/<DD>/newsletter.md` dans S3
- **Utilise Bedrock** : oui (pour la génération éditoriale)
- **Durée estimée** : quelques dizaines de secondes

### Amazon Bedrock (modèle de langage)

**Rôle** : "cerveau linguistique" de Vectora Inbox

**Modèles utilisés** :
- Un modèle pour la normalisation (ex : Claude 3 Haiku pour rapidité et coût)
- Un modèle pour la génération éditoriale (ex : Claude 3 Sonnet pour qualité)

**Configuration** :
- Les IDs de modèles sont passés via des variables d'environnement aux Lambdas (ex : `BEDROCK_MODEL_NORMALIZE`, `BEDROCK_MODEL_EDITORIAL`)
- Pas de modèles fine-tunés pour le MVP (utilisation des modèles de base)

**Permissions IAM** :
- Les rôles d'exécution des Lambdas doivent avoir `bedrock:InvokeModel` sur les modèles utilisés
- Région : `eu-west-3` (Paris)

### Scheduling (futur, hors MVP)

Pour le MVP, les Lambdas sont déclenchées manuellement (AWS CLI ou console).

Plus tard, on pourra ajouter :
- **EventBridge** : règles de scheduling pour déclencher les Lambdas automatiquement (ex : tous les lundis à 8h pour une newsletter hebdomadaire)
- **Step Functions** : orchestration des 2 Lambdas en séquence (ingestion → attendre → génération)

### Gestion des secrets (APIs externes)

Certaines sources externes nécessitent des clés API (ex : PubMed, ClinicalTrials.gov).

**Stockage** :
- Les clés API sont stockées dans **AWS Systems Manager Parameter Store** (SSM)
- Exemple : `/vectora-inbox/pubmed/api-key`

**Accès** :
- Les Lambdas lisent les clés via des variables d'environnement pointant vers les paramètres SSM
- Exemple : `PUBMED_API_KEY_PARAM=/vectora-inbox/pubmed/api-key`
- Les rôles IAM des Lambdas doivent avoir `ssm:GetParameter` sur ces paramètres

### Région AWS

Toutes les ressources Vectora Inbox sont créées dans la région **`eu-west-3`** (Paris).

### Permissions IAM (grandes lignes)

**Rôle de `vectora-inbox-ingest-normalize`** :
- Lecture : `s3:GetObject` sur `vectora-inbox-config/*`
- Écriture : `s3:PutObject` sur `vectora-inbox-data/raw/*` et `vectora-inbox-data/normalized/*`
- Bedrock : `bedrock:InvokeModel` sur les modèles de normalisation
- SSM : `ssm:GetParameter` sur les clés API (si nécessaire)

**Rôle de `vectora-inbox-engine`** :
- Lecture : `s3:GetObject` sur `vectora-inbox-config/*` et `vectora-inbox-data/normalized/*`
- Écriture : `s3:PutObject` sur `vectora-inbox-newsletters/*`
- Bedrock : `bedrock:InvokeModel` sur les modèles éditoriaux

### Ce qui n'est PAS dans le MVP

Pour garder l'architecture simple, le MVP n'inclut pas :
- DynamoDB (pas de base de données, tout est dans S3)
- RDS (pas de base relationnelle)
- Step Functions (pas d'orchestration complexe)
- SES (pas d'envoi d'e-mails automatique)
- CloudWatch Dashboards (monitoring basique uniquement)
- API Gateway (pas d'API REST publique)

L'objectif est de valider le workflow end-to-end avec le minimum de services AWS.


---

## Gouvernance et configuration (canonical, scopes, sources, scoring)

Cette section explique comment Vectora Inbox est gouverné par des configurations, et non par du code en dur. C'est un principe fondamental du projet : toute la logique métier est pilotée par des fichiers YAML modifiables sans toucher au code des Lambdas.

### 1. Canonical / scopes : la bibliothèque métier globale

**Qu'est-ce que le canonical ?**

Le répertoire `canonical/` contient la "bibliothèque métier globale" de Vectora Inbox. C'est une base de connaissances partagée par toutes les verticales (LAI, thérapie génique, thérapie cellulaire, etc.) et tous les clients.

**Structure du canonical** :
- `canonical/scopes/` : listes métier (entreprises, molécules, technologies, indications, exclusions)
- `canonical/sources/` : catalogue de sources et bouquets
- `canonical/scoring/` : règles de scoring et exemples

**Principe clé : un canonical global, pas de fichiers séparés par verticale**

Il n'existe pas de fichiers `lai_scopes.yaml` ou `oncology_scopes.yaml`. Toutes les verticales cohabitent dans les mêmes fichiers, différenciées par des préfixes de clés.

**Exemple dans `company_scopes.yaml`** :
```yaml
# Verticale LAI
lai_companies_global:
  - Camurus
  - Alkermes
  - Indivior
  - MedinCell
  # ... environ 180 sociétés

# Verticale oncologie (futur)
oncology_companies_global:
  - Roche
  - Pfizer
  - Merck
```

**Règle de nommage des clés** : `{verticale}_{dimension}_{segment}`

Exemples :
- `lai_companies_global` : toutes les sociétés LAI
- `lai_molecules_addiction` : molécules LAI pour l'addiction
- `lai_keywords` : mots-clés technologiques LAI
- `oncology_companies_us` : sociétés oncologie aux États-Unis (futur)

**Comment les Lambdas utilisent les scopes**

Les Lambdas ne "connaissent" pas la verticale. Elles ne savent pas que `lai_companies_global` est "LAI". Elles manipulent simplement des listes identifiées par leurs clés.

Processus :
1. La config client référence une clé (ex : `company_scope: "lai_companies_global"`)
2. La Lambda ouvre le fichier `company_scopes.yaml`
3. Elle charge la liste à la clé `"lai_companies_global"`
4. Elle utilise cette liste pour le matching ou le scoring

**Avantages de cette approche** :
- Pas de logique métier codée en dur dans les Lambdas
- Ajout d'une nouvelle verticale = créer de nouvelles clés dans les fichiers canonical
- Pas besoin de modifier le code des Lambdas pour ajouter une verticale

**État actuel des scopes LAI** :
- `lai_companies_global` : ~180 entreprises (complet)
- `lai_molecules_global` : ~90 molécules (complet)
- `lai_keywords` : ~80 mots-clés technologiques (complet)
- `lai_trademarks_global` : ~70 noms de marque (complet)
- `addiction_keywords` : vide (non-MVP)
- `psychiatry_keywords` : vide (non-MVP)

### 2. Catalogue de sources et bouquets

**Qu'est-ce que le catalogue de sources ?**

Le fichier `canonical/sources/source_catalog.yaml` répond à une question simple : "Quelles sources (flux RSS, APIs, sites web) Vectora Inbox sait-il lire ?"

**Structure du catalogue** :
- Section `sources:` : liste exhaustive des sources disponibles (URLs, types, tags)
- Section `bouquets:` : regroupements logiques de sources pour simplifier les configurations

**Exemple d'une source corporate LAI** :
```yaml
- source_key: "press_corporate__medincell"
  source_type: "press_corporate"
  url: "https://www.medincell.com/"
  default_language: "en"
  vertical_tags: ["lai"]
  notes: "Site institutionnel MedinCell (société LAI française)."
```

**Exemple d'une source de presse sectorielle** :
```yaml
- source_key: "press_sector__fiercepharma"
  source_type: "press_sector"
  url: "https://www.fiercepharma.com/"
  default_language: "en"
  vertical_tags: ["pharma-biotech"]
  notes: "Presse sectorielle orientée industrie pharmaceutique."
```

**Différence entre sources corporate et sources sectorielles** :

- **Sources corporate** (`press_corporate`) : sites web des entreprises elles-mêmes (communiqués de presse, résultats cliniques)
- **Sources sectorielles** (`press_sector`) : presse spécialisée couvrant le secteur entier (analyses, tendances, actualités multi-entreprises)

**Qu'est-ce qu'un bouquet ?**

Un bouquet est un regroupement logique de plusieurs sources dans une unité simple à activer.

**Pourquoi des bouquets ?**
- Éviter d'énumérer 180 sources individuelles dans chaque config client
- Réutiliser des ensembles de sources entre plusieurs clients
- Garder les fichiers de configuration lisibles et maintenables

**Exemple de bouquet MVP** :
```yaml
- bouquet_id: "lai_corporate_mvp"
  description: "Sous-bouquet MVP avec 8 sites corporate LAI pour tester l'ingestion."
  source_keys:
    - "press_corporate__medincell"
    - "press_corporate__camurus"
    - "press_corporate__g2gbio"
    - "press_corporate__alkermes"
    - "press_corporate__indivior"
    - "press_corporate__ascendis_pharma"
    - "press_corporate__novo_nordisk"
    - "press_corporate__ipsen"
```

**Exemple de bouquet presse** :
```yaml
- bouquet_id: "press_biotech_premium"
  description: "Sélection de presse sectorielle biotech/pharma premium."
  source_keys:
    - "press_sector__fiercepharma"
    - "press_sector__endpoints_news"
    - "press_sector__biocentury"
    # ... 19 sources au total
```

**Comment les configs clients utilisent les bouquets** :
```yaml
# Dans lai_weekly.yaml
source_config:
  source_bouquets_enabled:
    - "lai_corporate_mvp"        # 8 sources corporate LAI
    - "press_biotech_premium"    # 19 sources presse
```

**Comment la Lambda résout les bouquets** :
1. Lire `source_bouquets_enabled` dans la config client
2. Charger `source_catalog.yaml`
3. Pour chaque bouquet, extraire la liste des `source_keys`
4. Agréger et dédupliquer
5. Résultat : liste finale des sources à traiter (27 sources dans l'exemple ci-dessus)

**État actuel du catalogue** :
- ~180 sources corporate LAI (URLs à compléter manuellement pour certaines)
- 19 sources de presse sectorielle pharma/biotech
- 3 sources d'API scientifiques/réglementaires (PubMed, ClinicalTrials.gov, FDA labels)
- 2 bouquets LAI : `lai_corporate_mvp` (8 sources, pour tester) et `lai_corporate_all` (180 sources, complet)
- 1 bouquet presse : `press_biotech_premium` (19 sources)
- 3 bouquets API : `science_pubmed_lai`, `trials_ctgov_lai`, `reg_fda_labels_lai`

**Différence entre sources et scopes** :

- **Sources** (`source_catalog.yaml`) : où aller chercher les textes (URLs, flux RSS, APIs)
- **Scopes** (`scopes/*.yaml`) : listes métier pour interpréter les textes (entreprises, molécules, technologies)
- **Bouquets** : regroupements de sources pour simplifier les configs

### 3. Scoring : règles de priorisation

**Qu'est-ce que le scoring ?**

Le scoring est le mécanisme qui attribue un score numérique à chaque item pour prioriser les plus importants. C'est une étape cruciale : sans scoring, tous les items auraient le même poids, et la newsletter serait noyée dans le bruit.

**Fichier de référence** : `canonical/scoring/scoring_rules.yaml`

**Grandes lignes des poids** :

**1. Poids par type d'événement** (`event_type_weights`) :
- `clinical_update` : 5 (résultats d'essais cliniques = très important)
- `regulatory` : 5 (approbations FDA, CRL = très important)
- `partnership` : 6 (deals, licensing = hyper stratégique)
- `financial_results` : 3 (contexte business, moins ciblé)
- `corporate_move` : 2 (changements de management, secondaire)
- `scientific_publication` : 3 (publications, plutôt "background")
- `other` : 1 (faible priorité par défaut)

**2. Poids par priorité de domaine** (`domain_priority_weights`) :
- `high` : 3 (domaines "core" pour le client)
- `medium` : 2 (domaines importants mais pas critiques)
- `low` : 1 (domaines périphériques)

**3. Facteurs additionnels** (`other_factors`) :
- `competitor_company_bonus` : 2 (bonus si l'item mentionne un compétiteur clé)
- `key_molecule_bonus` : 1.5 (bonus si l'item mentionne une molécule clé)
- `recency_decay_half_life_days` : 7 (demi-vie de décroissance pour la récence)
- `signal_depth_bonus` : 0.3 (bonus par entité pertinente détectée)
- `source_type_weight_corporate` : 2 (poids pour sources corporate)
- `source_type_weight_sector` : 1.5 (poids pour sources sectorielles)
- `source_type_weight_generic` : 1 (poids pour sources généralistes)

**4. Seuils de sélection** (`selection_thresholds`) :
- `min_score` : 10 (score minimum pour inclusion dans la newsletter)
- `min_items_per_section` : 1 (nombre minimum d'items par section, même si score < 10)

**Exemple de calcul de score** (simplifié) :

Item : "Camurus annonce des résultats positifs de Phase 3 pour Brixadi"
- Type d'événement : `clinical_update` → poids 5
- Domaine : `tech_lai_ecosystem` (priorité high) → poids 3
- Compétiteur clé : Camurus → bonus 2
- Molécule clé : Brixadi → bonus 1.5
- Récence : publié il y a 2 jours → facteur ~0.9
- Source : corporate → poids 2

Score final (formule simplifiée) : (5 + 3 + 2 + 1.5) × 0.9 × 2 ≈ 20.7

Cet item sera très probablement inclus dans la newsletter (score > 10).

**Fichier d'exemples** : `canonical/scoring/scoring_examples.md`

Ce fichier contient 4 exemples détaillés de calcul de score pas-à-pas, pour comprendre la logique et ajuster les poids si nécessaire.

**Avantages du scoring déterministe** :
- Transparent : on peut expliquer pourquoi un item a un score élevé
- Ajustable : on peut modifier les poids dans `scoring_rules.yaml` sans toucher au code
- Reproductible : le même item aura toujours le même score (pas d'aléatoire)

### 4. Config client : personnalisation par client

**Qu'est-ce qu'une config client ?**

Un fichier YAML qui décrit ce que Vectora Inbox doit surveiller pour un client donné et comment générer sa newsletter personnalisée.

**Emplacement** : `clients/<client_id>.yaml` (dans S3, bucket `vectora-inbox-config`)

**Exemple** : `clients/lai_weekly.yaml`

**Contenu d'une config client** :

**1. Profil du client** (`client_profile`) :
- `name` : nom de la newsletter (ex : "LAI Intelligence Weekly")
- `client_id` : identifiant unique (ex : "lai_weekly")
- `language` : langue de la newsletter (ex : "en", "fr")
- `tone` : ton professionnel (ex : "executive", "scientific")
- `voice` : style rédactionnel (ex : "concise", "analytical")
- `frequency` : fréquence de génération (ex : "weekly", "monthly")

**2. Domaines de veille** (`watch_domains`) :
- Liste des domaines d'intérêt du client
- Chaque domaine référence des scopes canonical (via leurs clés)
- Exemple :
  ```yaml
  - id: "tech_lai_ecosystem"
    type: "technology"
    technology_scope: "lai_keywords"
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    trademark_scopes: "lai_trademarks_global"
    exclusion_scopes: "lai_exclude_noise"
    priority: "high"
  ```

**3. Configuration des sources** (`source_config`) :
- `source_bouquets_enabled` : liste des bouquets à activer
- `sources_extra_enabled` : sources additionnelles (optionnel)
- Exemple :
  ```yaml
  source_bouquets_enabled:
    - "lai_corporate_mvp"
    - "press_biotech_premium"
  ```

**4. Structure de la newsletter** (`newsletter_layout`) :
- `sections` : liste des sections de la newsletter
- Chaque section contient : `id`, `title`, `source_domains`, `max_items`, `filter_event_types` (optionnel)
- Exemple :
  ```yaml
  sections:
    - id: "top_signals"
      title: "Top Signals – LAI Ecosystem"
      source_domains:
        - "tech_lai_ecosystem"
        - "regulatory_lai"
      max_items: 5
  ```

**5. Livraison de la newsletter** (`newsletter_delivery`) :
- `format` : format de sortie (ex : "markdown", "html", "pdf")
- `include_tldr` : inclure un TL;DR (boolean)
- `include_intro` : inclure une introduction (boolean)
- `delivery_method` : méthode de livraison (ex : "s3", "email")
- `notification_email` : email de notification (optionnel)

**Comment un client réutilise les scopes et bouquets** :

Au lieu de lister 180 entreprises et 27 sources individuellement, le client référence simplement :
- Des clés de scopes (ex : `"lai_companies_global"`)
- Des bouquets (ex : `"lai_corporate_mvp"`)

Cela rend la config client courte, lisible et maintenable.

**État actuel** :
- 1 config client d'exemple : `lai_weekly.yaml` (complet et testé)
- Guide de configuration : `client-config-examples/README.md` (complet)

---

## Rôle de Bedrock dans Vectora Inbox

Cette section explique clairement où Amazon Bedrock intervient dans le workflow, et où il n'intervient pas. C'est important pour comprendre la séparation entre tâches linguistiques (IA) et tâches déterministes (règles).

### Où Bedrock intervient

**1. Phase 1B : Normalisation (compréhension du texte)**

Bedrock est utilisé pour transformer un texte brut (titre + description d'un article) en item structuré.

**Tâches confiées à Bedrock** :
- **Classification d'événement** : déterminer le type d'événement parmi une liste prédéfinie (ex : `clinical_update`, `partnership`, `regulatory`, `scientific_paper`, `corporate_move`, `financial_results`, `safety_signal`, `manufacturing_supply`, `other`)
- **Extraction d'entités** : identifier les entreprises, molécules, technologies et indications mentionnées dans le texte
- **Génération de résumé** : produire un résumé court (2-3 phrases) expliquant le "so what" de l'item

**Exemple de prompt (simplifié)** :
```
Texte : "Camurus Announces Positive Phase 3 Results for Brixadi in Opioid Use Disorder"

Tâche : Analyser ce texte et retourner :
- Type d'événement : [clinical_update, partnership, regulatory, ...]
- Entreprises mentionnées : [liste]
- Molécules mentionnées : [liste]
- Technologies mentionnées : [liste]
- Indications mentionnées : [liste]
- Résumé court (2-3 phrases)

Contexte : Voici des exemples d'entreprises LAI : Camurus, Alkermes, Indivior, ...
Voici des exemples de molécules LAI : buprenorphine, paliperidone, ...
```

**Sortie attendue de Bedrock** :
```json
{
  "event_type": "clinical_update",
  "companies_detected": ["Camurus"],
  "molecules_detected": ["Brixadi", "buprenorphine"],
  "technologies_detected": ["long acting"],
  "indications_detected": ["opioid use disorder"],
  "summary": "Camurus a annoncé des résultats positifs pour son essai de Phase 3 de Brixadi (buprenorphine) dans le traitement de l'addiction aux opioïdes. Cette avancée renforce la position de Camurus dans le segment des LAI pour l'addiction."
}
```

**2. Phase 4 : Génération de la newsletter (rédaction éditoriale)**

Bedrock est utilisé pour rédiger les composants éditoriaux de la newsletter.

**Tâches confiées à Bedrock** :
- **Titre de la newsletter** : ex : "Weekly Biotech Intelligence – January 15, 2025"
- **Introduction (chapeau)** : 2-4 phrases résumant le contexte de la semaine
- **TL;DR** : 3-5 bullet points résumant les signaux les plus importants
- **Intros de sections** : 1-2 phrases introduisant chaque section
- **Reformulations des items** : réécriture des résumés dans le ton/voice du client

**Exemple de prompt (simplifié)** :
```
Contexte : Newsletter hebdomadaire pour un client biotech, ton "executive", style "concise", langue "en"

Items retenus cette semaine :
1. Camurus – Résultats positifs Phase 3 pour Brixadi (score: 20.7)
2. Alkermes – Partenariat stratégique pour Vivitrol (score: 18.3)
3. FDA – Approbation d'une nouvelle formulation LAI (score: 22.1)

Tâche : Générer :
- Un titre de newsletter
- Une introduction (2-4 phrases)
- Un TL;DR (3-5 bullet points)
- Une intro pour la section "Top Signals – LAI Ecosystem"
- Des reformulations des 3 items ci-dessus dans le ton "executive" et style "concise"
```

**Sortie attendue de Bedrock** :
```markdown
# Weekly Biotech Intelligence – January 15, 2025

Cette semaine a été marquée par plusieurs avancées cliniques dans le domaine des LAI, notamment les résultats positifs de Camurus pour Brixadi. Les partenariats stratégiques se multiplient dans le secteur de l'addiction, tandis que la FDA continue d'accélérer les approbations de nouvelles formulations.

## TL;DR
- Camurus annonce des résultats positifs de Phase 3 pour Brixadi dans le traitement de l'addiction aux opioïdes.
- Partenariat stratégique entre Alkermes et un acteur majeur de la santé mentale.
- La FDA approuve une nouvelle formulation LAI pour la schizophrénie.

## Top Signals – LAI Ecosystem

Le secteur des LAI continue de se structurer avec plusieurs annonces majeures cette semaine.

**Camurus – Résultats positifs de Phase 3 pour Brixadi**
Camurus a annoncé des résultats positifs pour son essai de Phase 3 de Brixadi (buprenorphine) dans le traitement de l'addiction aux opioïdes. Cette avancée renforce la position de Camurus dans le segment des LAI pour l'addiction.
[Lire l'article](https://example.com/article)

...
```

### Où Bedrock n'intervient PAS

**Phase 1A : Ingestion (plomberie HTTP)**
- Appels HTTP vers les sources externes
- Parsing RSS/XML/JSON
- Extraction des champs de base (titre, description, URL, date)
- **Pourquoi pas Bedrock ?** C'est de la "plomberie" pure, pas de compréhension linguistique nécessaire

**Phase 2 : Matching (logique déterministe)**
- Calcul des intersections entre entités détectées et scopes canonical
- Décision si un item appartient à un domaine de veille
- **Pourquoi pas Bedrock ?** La logique doit rester transparente, expliquable et contrôlée par configuration

**Phase 3 : Scoring (règles numériques)**
- Calcul du score basé sur des poids et facteurs prédéfinis
- Tri des items par score décroissant
- **Pourquoi pas Bedrock ?** Le scoring doit être reproductible, ajustable et expliquable (pas de boîte noire)

### Exemples de prompts métier typiques

**Prompt de normalisation** (haut niveau) :
- "Analyse ce texte et identifie : le type d'événement, les entreprises mentionnées, les molécules, les technologies, les indications. Génère un résumé court."

**Prompt de génération éditoriale** (haut niveau) :
- "Rédige une newsletter hebdomadaire pour un client biotech, ton executive, style concise. Inclus : titre, intro, TL;DR, intros de sections, reformulations des items."

**Contraintes pour Bedrock** :
- Ne pas inventer de faits (rester fidèle au texte source)
- Respecter la langue du client (anglais ou français)
- Conserver les noms exacts (entreprises, molécules, technologies)
- Respecter le ton et le style définis dans la config client

### Avantages de cette séparation

**Transparence** : la logique métier (matching, scoring) reste expliquable et contrôlable

**Flexibilité** : on peut ajuster les règles de matching et scoring sans retoucher les prompts Bedrock

**Qualité** : Bedrock se concentre sur ce qu'il fait le mieux (comprendre et rédiger), pas sur des tâches déterministes

**Coût** : on n'appelle Bedrock que pour les tâches linguistiques complexes, pas pour des calculs simples


---

## Extensibilité multi-verticales et multi-clients

Cette section explique comment l'architecture actuelle de Vectora Inbox permet d'ajouter facilement de nouvelles verticales (au-delà de LAI) et de gérer plusieurs clients avec des besoins différents, sans modifier le code des Lambdas.

### Comment la structure actuelle permet l'extensibilité

**1. Préfixes de clés dans les scopes canonical**

Les scopes canonical utilisent un pattern de nommage `{verticale}_{dimension}_{segment}` qui permet de faire cohabiter plusieurs verticales dans les mêmes fichiers.

**Exemple actuel (LAI)** :
```yaml
# Dans company_scopes.yaml
lai_companies_global:
  - Camurus
  - Alkermes
  - Indivior
  # ...

lai_companies_addiction:
  - Camurus
  - Alkermes
  - Indivior
```

**Exemple futur (thérapie génique)** :
```yaml
# Dans le même fichier company_scopes.yaml
gene_therapy_companies_global:
  - Bluebird Bio
  - Spark Therapeutics
  - uniQure
  # ...

gene_therapy_companies_cns:
  - Bluebird Bio
  - Voyager Therapeutics
```

**Avantage** : pas besoin de créer des fichiers séparés par verticale, tout cohabite dans les mêmes fichiers canonical.

**2. Vertical_tags dans le catalogue de sources**

Les sources dans `source_catalog.yaml` utilisent des tags pour documenter leur pertinence métier.

**Exemple actuel (LAI)** :
```yaml
- source_key: "press_corporate__medincell"
  source_type: "press_corporate"
  url: "https://www.medincell.com/"
  vertical_tags: ["lai"]
```

**Exemple futur (thérapie génique)** :
```yaml
- source_key: "press_corporate__bluebird_bio"
  source_type: "press_corporate"
  url: "https://www.bluebirdbio.com/"
  vertical_tags: ["gene-therapy"]
```

**Avantage** : les sources peuvent être réutilisées entre verticales (ex : une source de presse généraliste peut avoir les tags `["lai", "gene-therapy"]`).

**3. Bouquets réutilisables**

Les bouquets permettent de créer des ensembles de sources spécifiques à une verticale, tout en réutilisant des sources communes.

**Exemple actuel (LAI)** :
```yaml
- bouquet_id: "lai_corporate_mvp"
  source_keys:
    - "press_corporate__medincell"
    - "press_corporate__camurus"
    # ...
```

**Exemple futur (thérapie génique)** :
```yaml
- bouquet_id: "gene_therapy_corporate_all"
  source_keys:
    - "press_corporate__bluebird_bio"
    - "press_corporate__spark_therapeutics"
    # ...

- bouquet_id: "gene_therapy_mixed"
  source_keys:
    - "press_corporate__bluebird_bio"
    - "press_sector__fiercebiotech"  # Source réutilisée
    - "press_sector__genetic_engineering_news"
```

**Avantage** : on peut créer des bouquets mixtes (sources spécifiques + sources communes).

**4. Configs client indépendantes**

Chaque client a sa propre config YAML qui référence les scopes et bouquets qui l'intéressent.

**Exemple actuel (client LAI)** :
```yaml
# lai_weekly.yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    technology_scope: "lai_keywords"

source_config:
  source_bouquets_enabled:
    - "lai_corporate_mvp"
    - "press_biotech_premium"
```

**Exemple futur (client thérapie génique)** :
```yaml
# gene_therapy_monthly.yaml
watch_domains:
  - id: "tech_gene_therapy_cns"
    company_scope: "gene_therapy_companies_cns"
    molecule_scope: "gene_therapy_molecules_all"
    technology_scope: "gene_therapy_keywords"

source_config:
  source_bouquets_enabled:
    - "gene_therapy_corporate_all"
    - "press_biotech_premium"  # Bouquet réutilisé
```

**Avantage** : chaque client choisit ses scopes et bouquets, sans impacter les autres clients.

### Ajouter une nouvelle verticale : étapes concrètes

**Exemple : ajouter la verticale "thérapie génique"**

**Étape 1 : Enrichir les scopes canonical**

Dans `canonical/scopes/company_scopes.yaml`, ajouter :
```yaml
gene_therapy_companies_global:
  - Bluebird Bio
  - Spark Therapeutics
  - uniQure
  - Voyager Therapeutics
  # ...
```

Dans `canonical/scopes/molecule_scopes.yaml`, ajouter :
```yaml
gene_therapy_molecules_all:
  - Zolgensma
  - Luxturna
  - Hemgenix
  # ...
```

Dans `canonical/scopes/technology_scopes.yaml`, ajouter :
```yaml
gene_therapy_keywords:
  - "AAV vector"
  - "lentiviral vector"
  - "gene editing"
  - "CRISPR"
  # ...
```

**Étape 2 : Ajouter des sources dans le catalogue**

Dans `canonical/sources/source_catalog.yaml`, ajouter :
```yaml
- source_key: "press_corporate__bluebird_bio"
  source_type: "press_corporate"
  url: "https://www.bluebirdbio.com/"
  vertical_tags: ["gene-therapy"]

- source_key: "press_corporate__spark_therapeutics"
  source_type: "press_corporate"
  url: "https://www.sparktx.com/"
  vertical_tags: ["gene-therapy"]
# ...
```

**Étape 3 : Créer un bouquet**

Dans `canonical/sources/source_catalog.yaml`, ajouter :
```yaml
- bouquet_id: "gene_therapy_corporate_all"
  description: "Flux corporate des sociétés de thérapie génique."
  source_keys:
    - "press_corporate__bluebird_bio"
    - "press_corporate__spark_therapeutics"
    # ...
```

**Étape 4 : Créer une config client**

Créer `clients/gene_therapy_monthly.yaml` :
```yaml
client_profile:
  name: "Gene Therapy Intelligence Monthly"
  client_id: "gene_therapy_monthly"
  language: "en"
  tone: "scientific"
  voice: "analytical"
  frequency: "monthly"

watch_domains:
  - id: "tech_gene_therapy_cns"
    company_scope: "gene_therapy_companies_cns"
    molecule_scope: "gene_therapy_molecules_all"
    technology_scope: "gene_therapy_keywords"
    priority: "high"

source_config:
  source_bouquets_enabled:
    - "gene_therapy_corporate_all"
    - "press_biotech_premium"

newsletter_layout:
  sections:
    - id: "top_signals"
      title: "Top Signals – Gene Therapy"
      source_domains:
        - "tech_gene_therapy_cns"
      max_items: 5

newsletter_delivery:
  format: "markdown"
  include_tldr: true
  include_intro: true
```

**Étape 5 : Tester**

Lancer les Lambdas avec `client_id: "gene_therapy_monthly"` et vérifier que :
- Les sources sont bien récupérées
- Les items sont bien normalisés
- Le matching fonctionne avec les nouveaux scopes
- La newsletter est générée correctement

**Aucune modification de code nécessaire** : les Lambdas manipulent simplement les listes chargées via les clés, sans "savoir" qu'il s'agit de thérapie génique.

### Gérer plusieurs clients avec des scopes différents

**Exemple : 3 clients LAI avec des besoins différents**

**Client 1 : LAI global (toutes indications)**
```yaml
# lai_weekly.yaml
watch_domains:
  - id: "tech_lai_ecosystem"
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    priority: "high"
```

**Client 2 : LAI addiction uniquement**
```yaml
# lai_addiction_monthly.yaml
watch_domains:
  - id: "indication_addiction"
    company_scope: "lai_companies_addiction"
    molecule_scope: "lai_molecules_addiction"
    indication_scope: "addiction_keywords"
    priority: "high"
```

**Client 3 : LAI psychiatrie uniquement**
```yaml
# lai_psychiatry_weekly.yaml
watch_domains:
  - id: "indication_psychiatry"
    company_scope: "lai_companies_psychiatry"
    molecule_scope: "lai_molecules_psychiatry"
    indication_scope: "psychiatry_keywords"
    priority: "high"
```

**Avantage** : chaque client a sa propre newsletter, avec des contenus filtrés selon ses domaines d'intérêt, sans impacter les autres clients.

### Limitations actuelles (non bloquantes pour le MVP)

**1. Certains scopes ne sont pas encore remplis**

- `lai_molecules_addiction` : vide (non-MVP)
- `lai_molecules_psychiatry` : vide (non-MVP)
- `addiction_keywords` : vide (non-MVP)
- `psychiatry_keywords` : vide (non-MVP)

**Impact** : les clients qui voudraient une newsletter spécifique "addiction" ou "psychiatrie" ne peuvent pas encore être servis. Mais le MVP LAI global fonctionne parfaitement avec `lai_companies_global` et `lai_molecules_global`.

**2. Certaines URLs de sources restent à compléter**

Dans `source_catalog.yaml`, certaines sources ont `url: ""` ou des URLs de recherche Google (à nettoyer manuellement).

**Impact** : ces sources ne peuvent pas être ingérées tant que les URLs ne sont pas complétées. Mais le bouquet MVP (`lai_corporate_mvp`) contient 8 sources avec URLs valides, suffisant pour tester.

**3. Les APIs scientifiques/réglementaires ne sont pas encore activées**

Les sources `science_pubmed_api`, `trials_ctgov_api`, `reg_fda_labels_api` sont définies dans le catalogue, mais pas encore utilisées dans les configs clients.

**Impact** : le MVP se concentre sur les sources corporate et presse. Les APIs scientifiques/réglementaires seront ajoutées dans une version ultérieure.

**Ces limitations ne bloquent pas le MVP LAI** : on peut générer des newsletters de qualité avec les sources corporate et presse actuelles.

---

## État de préparation pour l'infrastructure et le code

Cette section transforme le diagnostic précédent (qui était AMBER, puis GREEN après les corrections) en une synthèse claire de l'état actuel du projet.

### Principaux risques qui ont été traités

**1. Clés de scopes corrigées**

**Problème initial** : certaines clés de scopes dans `lai_weekly.yaml` ne correspondaient pas aux clés réelles dans les fichiers canonical (ex : `LAI_keywords` au lieu de `lai_keywords`).

**Correction** : toutes les clés ont été alignées avec les fichiers canonical. Les références sont maintenant cohérentes.

**Statut** : ✅ Résolu

**2. Bouquets MVP créés**

**Problème initial** : le bouquet `lai_corporate_all` contenait 180 sources, dont beaucoup avec URLs manquantes ou invalides. Tester l'ingestion avec 180 sources était risqué.

**Correction** : création du bouquet `lai_corporate_mvp` avec 8 sources corporate LAI ayant des URLs valides (MedinCell, Camurus, G2GBio, Alkermes, Indivior, Ascendis Pharma, Novo Nordisk, Ipsen).

**Statut** : ✅ Résolu

**3. Contrats Lambdas précisés**

**Problème initial** : les contrats des Lambdas manquaient de détails sur la résolution des bouquets et le chargement des scopes.

**Correction** : ajout de sections détaillées dans `contracts/lambdas/vectora-inbox-ingest-normalize.md` et `contracts/lambdas/vectora-inbox-engine.md` expliquant :
- Comment résoudre les bouquets (4 étapes)
- Comment charger les scopes canonical (5 étapes)
- Exemples de code pseudo-Python

**Statut** : ✅ Résolu

**4. Guide config client créé**

**Problème initial** : pas de documentation claire pour créer ou maintenir une config client.

**Correction** : création de `client-config-examples/README.md` avec :
- Inventaire complet des scopes disponibles
- Inventaire des bouquets disponibles
- Guide pas-à-pas pour créer une config client
- Exemple minimal commenté

**Statut** : ✅ Résolu

**5. Scoring complété avec seuils et exemples**

**Problème initial** : les règles de scoring manquaient de seuils de sélection (score minimum, nombre minimum d'items par section).

**Correction** : ajout de la section `selection_thresholds` dans `scoring_rules.yaml` + création de `scoring_examples.md` avec 4 exemples détaillés.

**Statut** : ✅ Résolu

### Points à surveiller lors de l'implémentation

**1. Gestion des erreurs et timeouts**

**Risque** : certaines sources externes peuvent être lentes, indisponibles ou retourner des erreurs HTTP.

**Mitigation** :
- Implémenter des retries avec backoff exponentiel (2-3 tentatives)
- Logger explicitement les erreurs (URL, code HTTP, message)
- Continuer le traitement des autres sources en cas d'échec d'une source
- Ne pas bloquer toute l'ingestion si une source échoue

**2. Coûts potentiels (Bedrock + APIs externes)**

**Risque** : les appels Bedrock et les APIs externes (PubMed, ClinicalTrials.gov) peuvent générer des coûts significatifs si le volume est élevé.

**Mitigation** :
- Commencer avec un volume limité (bouquet MVP = 8 sources)
- Monitorer les coûts Bedrock via CloudWatch
- Utiliser des modèles Bedrock économiques pour la normalisation (ex : Claude 3 Haiku)
- Limiter le nombre d'appels API externes (ex : 100 résultats max par requête PubMed)
- Mettre en place des alertes de coût dans AWS Budgets

**3. Besoin de tester sur un petit volume avant d'élargir**

**Risque** : passer directement de 0 à 180 sources peut révéler des bugs ou des problèmes de performance.

**Mitigation** :
- Phase 1 : tester avec `lai_corporate_mvp` (8 sources) + `press_biotech_premium` (19 sources) = 27 sources
- Phase 2 : valider la qualité des newsletters générées (résumés, matching, scoring)
- Phase 3 : élargir progressivement (ajouter 10-20 sources à la fois)
- Phase 4 : passer à `lai_corporate_all` (180 sources) une fois la stabilité confirmée

**4. Qualité des résumés Bedrock**

**Risque** : les résumés générés par Bedrock peuvent être trop longs, trop courts, ou manquer de pertinence.

**Mitigation** :
- Tester les prompts de normalisation sur un échantillon d'items
- Ajuster les instructions dans les prompts (ex : "résumé en 2-3 phrases maximum")
- Valider manuellement les premiers résumés générés
- Itérer sur les prompts si nécessaire

**5. Gestion des doublons**

**Risque** : un même article peut être récupéré depuis plusieurs sources (ex : un communiqué de presse repris par plusieurs sites).

**Mitigation** :
- Implémenter une détection de doublons basée sur l'URL ou le titre
- Dédupliquer les items avant la normalisation (ou après)
- Garder uniquement la version de la source la plus fiable (ex : source corporate > presse)

### Verdict global sur la préparation

**En l'état actuel, le projet est prêt (verdict GREEN) pour la définition de l'infrastructure AWS (stacks) et la génération des premières Lambdas pour le MVP LAI, avec une complexité maîtrisée.**

**Justification** :

✅ **Gouvernance complète** : scopes canonical, catalogue de sources, règles de scoring, configs client

✅ **Contrats métier clairs** : les 2 Lambdas ont des contrats détaillés avec exemples JSON

✅ **Bouquets MVP testables** : `lai_corporate_mvp` (8 sources) + `press_biotech_premium` (19 sources)

✅ **Documentation pédagogique** : README pour canonical, contrats, config client, scoring

✅ **Extensibilité démontrée** : architecture prête pour multi-verticales et multi-clients

✅ **Séparation claire** : tâches déterministes (matching, scoring) vs tâches linguistiques (Bedrock)

⚠️ **Points de vigilance** : gestion des erreurs, coûts, tests progressifs, qualité des résumés

**Prochaine étape recommandée** : définir les stacks CloudFormation pour créer les 3 buckets S3, les 2 Lambdas, et les permissions IAM.

---

## Recommandations et prochaines étapes

Cette section propose des recommandations concrètes, triées par priorité et horizon temporel.

### Étapes immédiates (infra + code MVP LAI)

**1. Définir les stacks d'infrastructure**

**Objectif** : créer les ressources AWS nécessaires au MVP.

**Actions** :
- Stack `vectora-inbox-s0-core` : créer les 3 buckets S3 (`vectora-inbox-config`, `vectora-inbox-data`, `vectora-inbox-newsletters`)
- Stack `vectora-inbox-s0-iam` : créer les rôles IAM pour les 2 Lambdas (permissions S3, Bedrock, SSM)
- Stack `vectora-inbox-s1-lambdas` : créer les 2 Lambdas (`vectora-inbox-ingest-normalize`, `vectora-inbox-engine`)

**Livrables** :
- Templates CloudFormation (ou SAM/CDK)
- Scripts de déploiement
- Documentation de déploiement

**2. Générer les Lambdas en respectant les contrats**

**Objectif** : implémenter les 2 Lambdas selon les contrats métier.

**Actions** :
- Implémenter `vectora-inbox-ingest-normalize` :
  - Phase 1A : ingestion HTTP (RSS parsing, API calls)
  - Phase 1B : normalisation avec Bedrock (prompts, parsing des réponses)
  - Résolution des bouquets (4 étapes)
  - Chargement des scopes canonical
  - Écriture des items normalisés dans S3
- Implémenter `vectora-inbox-engine` :
  - Chargement des items normalisés depuis S3
  - Phase 2 : matching (intersections d'ensembles)
  - Phase 3 : scoring (formules numériques)
  - Phase 4 : génération de newsletter avec Bedrock (prompts, assemblage Markdown)
  - Écriture de la newsletter dans S3

**Livrables** :
- Code des 2 Lambdas (Python recommandé)
- Tests unitaires (au moins pour les fonctions critiques)
- Documentation technique

**3. Mettre en place un jeu de test avec `lai_weekly` + `lai_corporate_mvp`**

**Objectif** : valider le workflow end-to-end sur un volume limité.

**Actions** :
- Uploader les fichiers canonical dans `s3://vectora-inbox-config/canonical/`
- Uploader `lai_weekly.yaml` dans `s3://vectora-inbox-config/clients/`
- Déclencher `vectora-inbox-ingest-normalize` avec `client_id: "lai_weekly"`, `period_days: 7`
- Vérifier que les items normalisés sont bien écrits dans S3
- Déclencher `vectora-inbox-engine` avec `client_id: "lai_weekly"`, `period_days: 7`
- Vérifier que la newsletter est bien générée dans S3
- Lire la newsletter et valider manuellement la qualité (résumés, structure, pertinence)

**Livrables** :
- Newsletter de test générée
- Rapport de validation (qualité, bugs identifiés, améliorations suggérées)

### Étapes à court terme (améliorations confort)

**1. Enrichir progressivement les scopes**

**Objectif** : compléter les scopes non-MVP pour permettre des newsletters plus ciblées.

**Actions** :
- Remplir `lai_molecules_addiction` avec les molécules LAI pour addiction
- Remplir `lai_molecules_psychiatry` avec les molécules LAI pour psychiatrie
- Remplir `addiction_keywords` avec les mots-clés d'indication
- Remplir `psychiatry_keywords` avec les mots-clés d'indication
- Créer des scopes `lai_companies_addiction` et `lai_companies_psychiatry` si pertinent

**Livrables** :
- Scopes enrichis dans `canonical/scopes/*.yaml`
- Configs client d'exemple pour addiction et psychiatrie

**2. Connecter les APIs PubMed/ClinicalTrials.gov/FDA**

**Objectif** : ajouter des sources scientifiques et réglementaires à la veille.

**Actions** :
- Implémenter l'ingestion PubMed (API E-utilities)
- Implémenter l'ingestion ClinicalTrials.gov (API v2)
- Implémenter l'ingestion FDA labels (API openFDA)
- Créer des bouquets `science_pubmed_lai`, `trials_ctgov_lai`, `reg_fda_labels_lai`
- Tester l'ingestion avec ces nouvelles sources
- Valider la qualité des items normalisés (résumés scientifiques)

**Livrables** :
- Code d'ingestion pour les 3 APIs
- Bouquets activés dans les configs client
- Newsletters de test incluant des items scientifiques/réglementaires

**3. Ajouter quelques tableaux de bord simples**

**Objectif** : monitorer la santé du système et la qualité des newsletters.

**Actions** :
- Créer un dashboard CloudWatch avec :
  - Nombre d'items ingérés par jour
  - Nombre d'items normalisés par jour
  - Nombre de newsletters générées par jour
  - Durée d'exécution des Lambdas
  - Erreurs et timeouts
  - Coûts Bedrock (nombre de tokens)
- Créer des alertes CloudWatch pour :
  - Échecs de Lambda
  - Coûts Bedrock dépassant un seuil
  - Durée d'exécution anormalement longue

**Livrables** :
- Dashboard CloudWatch configuré
- Alertes CloudWatch configurées
- Documentation de monitoring

### Étapes à moyen terme (nouvelles verticales, industrialisation)

**1. Ajouter une deuxième verticale**

**Objectif** : valider l'extensibilité multi-verticales de l'architecture.

**Actions** :
- Choisir une verticale (ex : thérapie génique, thérapie cellulaire, oncologie)
- Créer les scopes canonical pour cette verticale (entreprises, molécules, technologies)
- Ajouter des sources dans le catalogue (corporate, presse)
- Créer un bouquet pour cette verticale
- Créer une config client d'exemple
- Tester le workflow end-to-end
- Valider que les Lambdas fonctionnent sans modification de code

**Livrables** :
- Scopes canonical pour la nouvelle verticale
- Bouquet et config client
- Newsletter de test pour la nouvelle verticale
- Rapport de validation de l'extensibilité

**2. Industrialiser les tests automatiques**

**Objectif** : garantir la qualité du code et éviter les régressions.

**Actions** :
- Écrire des tests unitaires pour les fonctions critiques (parsing, matching, scoring)
- Écrire des tests d'intégration pour les workflows complets (ingestion → normalisation → génération)
- Mettre en place un pipeline CI/CD (ex : GitHub Actions, AWS CodePipeline)
- Automatiser les déploiements (dev → staging → prod)

**Livrables** :
- Suite de tests automatiques
- Pipeline CI/CD configuré
- Documentation de contribution

**3. Travailler des métriques de qualité de la newsletter**

**Objectif** : mesurer et améliorer la qualité des newsletters générées.

**Actions** :
- Définir des métriques de qualité :
  - Pertinence des items sélectionnés (feedback client)
  - Qualité des résumés (longueur, clarté, fidélité au texte source)
  - Diversité des sources (éviter de ne citer qu'une seule source)
  - Fraîcheur des items (éviter les items trop anciens)
- Collecter des feedbacks clients (sondages, entretiens)
- Ajuster les règles de scoring et les prompts Bedrock en fonction des feedbacks
- Itérer sur la qualité

**Livrables** :
- Métriques de qualité définies
- Processus de collecte de feedback
- Rapports d'amélioration continue

---

**Fin du diagnostic complet et pédagogique – Vectora Inbox MVP LAI**

