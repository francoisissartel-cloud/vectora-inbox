# Plan d'Investigation : Normalize Score V2 - Matching à 0% sur lai_weekly_v3

## Section 1 – Contexte

### Rôle de normalize_score_v2 dans le workflow Vectora Inbox

La Lambda `vectora-inbox-normalize-score-v2` est la **2ème étape critique** du pipeline Vectora Inbox V2 :

1. **Ingest V2** → Récupération contenus bruts → S3 `ingested/`
2. **Normalize Score V2** → Normalisation Bedrock + Matching + Scoring → S3 `curated/`
3. **Newsletter V2** → Assemblage newsletter → S3 `newsletters/`

**Responsabilités de normalize_score_v2** :
- **Normalisation Bedrock** : Extraction d'entités (companies, molecules, technologies, trademarks), classification d'événements, résumés
- **Matching aux domaines** : Déterminer quels `watch_domains` correspondent à chaque item basé sur les entités détectées
- **Scoring de pertinence** : Calculer le score final basé sur les règles métier, bonus et pénalités
- **Stockage S3** : Items normalisés et scorés dans `curated/{client_id}/{YYYY}/{MM}/{DD}/items.json`

### Problème observé sur lai_weekly_v3

**Symptômes** :
- ✅ **Ingest V2 fonctionne** : Items ingérés correctement dans S3 `ingested/`
- ✅ **Bedrock V2 répond** : Appels Bedrock semblent opérationnels (pas d'erreur 500)
- ❌ **Matching = 0%** : Aucun item n'est matché aux domaines de veille (`tech_lai_ecosystem`, `regulatory_lai`)
- ❌ **Entités = 0** : Statistiques d'extraction d'entités (companies, molecules, etc.) remontent à 0

**Impact métier** :
- Aucun item dans S3 `curated/` ou items avec `matched_domains: []`
- Newsletter vide ou avec contenu non pertinent
- Pipeline fonctionnellement cassé malgré l'absence d'erreurs techniques

## Section 2 – Hypothèses initiales

### Hypothèse A : Réponse Bedrock correcte mais mal parsée
- **Symptôme** : Bedrock renvoie des entités mais le code ne les lit pas correctement
- **Causes possibles** :
  - Structure JSON de la réponse Bedrock différente de ce que le code attend
  - Clés JSON incorrectes (ex: `entities.companies` vs `entities.company`)
  - Parsing JSON défaillant ou incomplet
  - Gestion d'erreurs qui masque les problèmes de parsing

### Hypothèse B : Listes canonical non chargées ou mal référencées
- **Symptôme** : Entités détectées par Bedrock mais pas de matching car scopes vides
- **Causes possibles** :
  - Scopes canonical (`lai_companies_global`, `lai_molecules_global`, etc.) non chargés depuis S3
  - Références incorrectes dans `lai_weekly_v3.yaml` vers les scopes
  - Erreurs de chargement S3 des fichiers canonical silencieuses
  - Structure des scopes canonical incompatible avec le code de matching

### Hypothèse C : Thresholds de matching/scoring trop stricts
- **Symptôme** : Entités détectées et scopes chargés mais conditions de matching non remplies
- **Causes possibles** :
  - `require_entity_signals: true` mais aucune entité ne match les scopes
  - `min_technology_signals: 2` mais seulement 1 signal détecté
  - Seuils de confiance trop élevés (`auto_match_threshold: 0.8`)
  - Logique de matching trop restrictive

### Hypothèse D : Structure de la réponse Bedrock a changé
- **Symptôme** : Code écrit pour une version de prompt/modèle mais Bedrock utilise une autre
- **Causes possibles** :
  - Migration vers Claude Sonnet 4.5 avec format de réponse différent
  - Prompts canonical modifiés sans adaptation du code de parsing
  - Modèle Bedrock configuré différent de celui attendu par le code
  - Région Bedrock (`us-east-1` vs `eu-west-3`) avec comportements différents

### Hypothèse E : Problème de configuration client lai_weekly_v3
- **Symptôme** : Configuration client incompatible avec le code de matching
- **Causes possibles** :
  - `watch_domains` mal configurés dans `lai_weekly_v3.yaml`
  - Références vers des scopes canonical inexistants
  - Configuration de matching incompatible (`matching_profile`, `domain_type_overrides`)
  - Variables d'environnement manquantes ou incorrectes

## Section 3 – Méthodologie d'investigation

### Approche systématique par étapes

**Principe** : Investiguer de façon méthodique en remontant le pipeline depuis les données finales vers les données sources.

#### Étape 1 : Exécuter un run réel complet sur lai_weekly_v3
- **Objectif** : Obtenir des données fraîches et complètes pour l'analyse
- **Actions** :
  - Lancer `vectora-inbox-ingest-v2` pour `lai_weekly_v3`
  - Puis lancer `vectora-inbox-normalize-score-v2` sur le dernier run
  - Capturer tous les logs CloudWatch des deux Lambdas
  - Noter les timestamps et durées d'exécution

#### Étape 2 : Inspecter les fichiers S3 en sortie d'ingest_v2
- **Objectif** : Valider que l'input de normalize_score_v2 est correct
- **Actions** :
  - Lister les fichiers dans `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/`
  - Télécharger et analyser le dernier `items.json`
  - Compter le nombre d'items ingérés
  - Vérifier la structure des items (title, content, url, published_at, etc.)
  - Identifier quelques items représentatifs pour le suivi

#### Étape 3 : Inspecter les fichiers S3 en sortie de normalize_score_v2
- **Objectif** : Analyser l'output pour comprendre où le processus échoue
- **Actions** :
  - Lister les fichiers dans `s3://vectora-inbox-data-dev/curated/lai_weekly_v3/`
  - Télécharger et analyser le dernier `items.json`
  - Compter le nombre d'items normalisés vs ingérés
  - Examiner la structure des items normalisés :
    - `normalized_content` : présent ? entités détectées ?
    - `matching_results` : `matched_domains` vide ?
    - `scoring_results` : scores calculés ?

#### Étape 4 : Analyser les logs CloudWatch de normalize_score_v2
- **Objectif** : Comprendre le comportement interne de la Lambda
- **Actions** :
  - Extraire les logs du dernier run de `normalize_score_v2`
  - Rechercher les patterns :
    - Chargement des configurations (client_config, canonical)
    - Appels Bedrock (requêtes, réponses, erreurs)
    - Processus de matching (entités trouvées, domaines matchés)
    - Calculs de scoring
    - Erreurs ou warnings
  - Identifier les métriques : nombre d'items traités à chaque étape

#### Étape 5 : Examiner la réponse Bedrock réelle
- **Objectif** : Valider que Bedrock renvoie bien des entités utilisables
- **Actions** :
  - Extraire des exemples de réponses Bedrock depuis les logs
  - Analyser la structure JSON réelle vs structure attendue par le code
  - Vérifier la présence des champs :
    - `entities.companies`, `entities.molecules`, `entities.technologies`, `entities.trademarks`
    - `event_classification.primary_type`, `event_classification.secondary_types`
    - `summary`, `language`, `sentiment`
  - Comparer avec les prompts canonical utilisés

#### Étape 6 : Vérifier le chargement des canonical
- **Objectif** : S'assurer que les scopes de matching sont bien chargés
- **Actions** :
  - Vérifier la présence des fichiers canonical sur S3 :
    - `s3://vectora-inbox-config-dev/canonical/scopes/company_scopes.yaml`
    - `s3://vectora-inbox-config-dev/canonical/scopes/molecule_scopes.yaml`
    - `s3://vectora-inbox-config-dev/canonical/scopes/technology_scopes.yaml`
    - `s3://vectora-inbox-config-dev/canonical/scopes/trademark_scopes.yaml`
  - Télécharger et examiner le contenu des scopes LAI :
    - `lai_companies_global` : liste des entreprises LAI
    - `lai_molecules_global` : liste des molécules LAI
    - `lai_keywords` : mots-clés technologiques LAI
    - `lai_trademarks_global` : marques commerciales LAI
  - Vérifier les logs de chargement des canonical dans normalize_score_v2

#### Étape 7 : Analyser la logique de matching
- **Objectif** : Comprendre pourquoi les entités détectées ne matchent pas les domaines
- **Actions** :
  - Examiner le code de matching dans `src_v2/vectora_core/normalization/matcher.py`
  - Tracer le processus pour quelques items représentatifs :
    - Entités extraites par Bedrock
    - Scopes canonical chargés
    - Logique de comparaison (exact match, fuzzy match, normalisation)
    - Conditions de matching (`require_entity_signals`, `min_technology_signals`)
    - Résultat final du matching
  - Identifier les points de rupture dans la chaîne de matching

## Section 4 – Données & périmètre de test

### Client de test
- **Client** : `lai_weekly_v3`
- **Configuration** : `client-config-examples/lai_weekly_v3.yaml`
- **Domaines de veille** :
  - `tech_lai_ecosystem` (priority: high, technology_scope: lai_keywords, company_scope: lai_companies_global)
  - `regulatory_lai` (priority: high, technology_scope: lai_keywords, company_scope: lai_companies_global)

### Fenêtre temporelle
- **Période par défaut** : 30 jours (`default_period_days: 30` dans lai_weekly_v3.yaml)
- **Sources** : Bouquets `lai_corporate_mvp` + `lai_press_mvp` (8 sources au total)
- **Volume attendu** : 20-50 items sur 30 jours selon les sources LAI

### Environnement AWS
- **Région** : `eu-west-3` (Paris)
- **Profil** : `rag-lai-prod`
- **Buckets** :
  - Config : `vectora-inbox-config-dev`
  - Data : `vectora-inbox-data-dev`
- **Lambdas** :
  - Ingest : `vectora-inbox-ingest-v2-dev`
  - Normalize : `vectora-inbox-normalize-score-v2-dev`

### Métriques de référence
- **Items ingérés** : X items (à mesurer lors du run)
- **Items normalisés** : Y items (devrait = X)
- **Items matchés** : 0 actuellement (problème à résoudre)
- **Entités détectées** : 0 actuellement (problème à résoudre)

## Section 5 – Livrables attendus

### Livrable 1 : Rapport de diagnostic détaillé
- **Fichier** : `docs/diagnostics/normalize_score_v2_matching_investigation_report.md`
- **Contenu** :
  - Résumé exécutif (5-10 bullet points sur la cause racine)
  - Pipeline réel observé (métriques détaillées)
  - Analyse des entités (ce que Bedrock renvoie vs ce que le code lit)
  - Analyse du matching (pourquoi 0% de matching)
  - Exemples concrets d'items (avant/après normalisation)

### Livrable 2 : Liste de recommandations priorisées
- **Format** : Section dans le rapport de diagnostic
- **Contenu** :
  - Recommandations court terme (fixes immédiats sans casser l'archi)
  - Recommandations moyen terme (améliorations structurelles)
  - Priorisation par impact/effort
  - Estimation des risques de chaque recommandation

### Livrable 3 : Pistes de patch (sans implémentation)
- **Format** : Section dans le rapport de diagnostic
- **Contenu** :
  - Plan de patch en 3-5 étapes concrètes
  - Code à modifier (fichiers, fonctions, lignes approximatives)
  - Tests de validation pour chaque étape
  - Critères de succès mesurables

### Livrable 4 : Données de test pour validation
- **Fichiers** :
  - Exemples d'items ingérés (`fixtures/lai_weekly_v3_ingested_sample.json`)
  - Exemples de réponses Bedrock (`fixtures/lai_weekly_v3_bedrock_responses.json`)
  - Exemples d'items normalisés attendus (`fixtures/lai_weekly_v3_normalized_expected.json`)
- **Usage** : Tests de régression pour valider les corrections

---

## Critères de succès de l'investigation

### Critères techniques
- ✅ Cause racine du matching à 0% identifiée avec certitude
- ✅ Cause racine des entités à 0 identifiée avec certitude
- ✅ Pipeline complet tracé avec métriques à chaque étape
- ✅ Exemples concrets d'items problématiques analysés
- ✅ Plan de correction détaillé et validé

### Critères métier
- ✅ Compréhension claire de l'impact sur la newsletter LAI
- ✅ Estimation du taux de matching attendu après correction
- ✅ Validation que la correction ne cassera pas les autres clients
- ✅ Plan de test pour valider la correction

### Critères de livraison
- ✅ Rapport de diagnostic complet et actionnable
- ✅ Recommandations priorisées avec estimation d'effort
- ✅ Données de test pour validation des corrections
- ✅ Aucune modification de code dans cette phase (diagnostic uniquement)

---

**Prêt pour l'exécution de l'investigation sur données réelles du MVP lai_weekly_v3.**