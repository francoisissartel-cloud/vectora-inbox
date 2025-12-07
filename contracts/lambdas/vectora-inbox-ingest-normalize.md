# Contrat métier – Lambda `vectora-inbox-ingest-normalize`

---

# 1. Rôle et objectif de la Lambda

La Lambda `vectora-inbox-ingest-normalize` est responsable de la **Phase 1** du workflow Vectora Inbox.

Elle gère :
- l'**ingestion des sources externes** (flux RSS, APIs publiques),
- la **production d'items normalisés** prêts à être exploités par le moteur.

Cette Lambda **ne fait pas** :
- de matching avec les domaines d'intérêt (watch_domains),
- de scoring des items,
- de génération de newsletter,
- d'envoi d'e-mails.

Son rôle est de transformer des contenus hétérogènes (RSS, JSON d'APIs) en un format unifié et enrichi, stocké dans S3, pour qu'un client donné puisse ensuite les analyser et les filtrer.

---

# 2. Contexte dans le workflow Vectora Inbox

La Lambda `vectora-inbox-ingest-normalize` intervient en **Phase 1**, qui se décompose en deux sous-phases :

- **Phase 1A – Ingestion** : récupération des données brutes depuis les sources externes (sans IA).
- **Phase 1B – Normalisation** : enrichissement et structuration des items avec l'aide d'Amazon Bedrock.

## Architecture globale

Vectora Inbox repose sur **3 buckets S3** :

1. **`vectora-inbox-config`** : contient les configurations canoniques (scopes partagés) et les fichiers de configuration par client.
2. **`vectora-inbox-data`** : contient les données brutes (optionnel, pour debug) et les items normalisés.
3. **`vectora-inbox-newsletters`** : contient les newsletters générées (hors scope de cette Lambda).

## Dépendances de la Lambda

Cette Lambda dépend de :

- **`vectora-inbox-config`** :
  - Définitions canoniques des sources (RSS, APIs) par `source_key`.
  - Mapping `source_key` → `source_type` (ex : `press_corporate`, `press_sector`, `pubmed`, `clinicaltrials`).
  - Listes canoniques (companies, molecules, technologies, indications, exclusions, event_type_patterns).
  - Configuration client : quels `source_key` sont activés, langue du client, paramètres de filtrage.

- **`vectora-inbox-data`** :
  - Écriture dans `raw/` (optionnel, pour debug et rejeu).
  - Écriture dans `normalized/` (obligatoire, entrée du moteur).

- **Amazon Bedrock** :
  - Utilisé **uniquement en Phase 1B** pour la normalisation (extraction d'entités, classification d'événements, génération de résumés).
  - **Pas utilisé en Phase 1A** (ingestion HTTP pure).

---

# 3. Entrées de la Lambda (événement et paramètres)

La Lambda est déclenchée par un événement JSON contenant les paramètres suivants (au niveau métier) :

## Paramètres obligatoires

- **`client_id`** (string) : identifiant unique du client (ex : `"lai_weekly"`).

## Paramètres optionnels

- **`sources`** (liste de strings) : liste des `source_key` à traiter. Si absent, tous les `source_key` activés pour le client sont traités.
  - Exemple : `["press_corporate__fiercepharma", "pubmed_lai"]`

- **`period_days`** (integer) : nombre de jours à remonter dans le passé pour l'ingestion (ex : `7` pour la dernière semaine).

- **`from_date`** et **`to_date`** (strings ISO8601) : fenêtre temporelle explicite pour l'ingestion.
  - Exemple : `"from_date": "2025-01-01"`, `"to_date": "2025-01-07"`

## Résolution des sources à traiter

La Lambda doit résoudre la liste finale des `source_key` à traiter en combinant :
1. Les bouquets activés dans la config client (`source_bouquets_enabled`)
2. Les sources additionnelles (`sources_extra_enabled`)
3. Le paramètre optionnel `sources` de l'événement (qui peut surcharger la config)

Si le paramètre `sources` est fourni dans l'événement, il prend la priorité sur la configuration client.

## Qui peut appeler cette Lambda ?

- **Exécution manuelle** (MVP) : via AWS CLI ou console Lambda.
- **Plus tard** (hors scope MVP) : déclenchement automatique via EventBridge (scheduler quotidien ou hebdomadaire).

---

# 4. Configurations lues (canonical + client)

Avant de commencer le traitement, la Lambda lit les configurations suivantes depuis S3.

## 4.1 Configuration canonique

Emplacement : `s3://vectora-inbox-config/canonical/`

Contenu :

- **Définition des sources** :
  - Liste des `source_key` disponibles (ex : `press_corporate__fiercepharma`, `press_sector__endpointsnews`, `pubmed_lai`, `ctgov_lai`).
  - Pour chaque `source_key` : URL (RSS ou API), type de parsing (RSS, JSON), fréquence de mise à jour.
  - Mapping `source_key` → `source_type` (ex : `press_corporate`, `press_sector`, `pubmed`, `clinicaltrials`).

- **Scopes canoniques** :
  - `company_scopes.yaml` : listes de sociétés groupées par secteur ou technologie.
  - `molecule_scopes.yaml` : listes de molécules groupées par aire thérapeutique.
  - `keywords_technologies.yaml` : mots-clés et synonymes pour les technologies (ex : "long acting", "depot", "microparticle").
  - `keywords_indications.yaml` : mots-clés et synonymes pour les indications (ex : "opioid use disorder", "schizophrenia").
  - `keywords_exclusions.yaml` : mots-clés pour filtrer le bruit (ex : "job posting", "webinar").
  - `event_type_patterns.yaml` : patterns pour classifier les événements (ex : "clinical_update", "partnership", "regulatory").

## 4.2 Configuration client

Emplacement : `s3://vectora-inbox-config/clients/<client_id>.yaml`

Contenu :

- **`client_profile`** :
  - `name` : nom lisible du client.
  - `client_id` : identifiant machine (utilisé dans les chemins S3).
  - `language` : langue du client (ex : `"en"`, `"fr"`), utile pour les résumés Bedrock.
  - `tone`, `voice`, `frequency` : paramètres éditoriaux (utilisés plus tard par le moteur).

- **`watch_domains`** :
  - Liste des domaines d'intérêt du client (utilisés plus tard par le moteur pour le matching).
  - Chaque domaine référence des scopes canoniques et peut ajouter des entités spécifiques au client.

- **Sources activées** :
  - La configuration client peut spécifier quels `source_key` sont activés pour ce client.
  - Si non spécifié, tous les `source_key` canoniques sont utilisés.

### Résolution des bouquets de sources

La configuration client peut utiliser des **bouquets** (groupes de sources prédéfinis) au lieu de lister chaque source individuellement. Voici comment la Lambda doit résoudre les bouquets :

#### Processus de résolution

1. **Lire la section `source_config` dans la config client** :
   - `source_bouquets_enabled` : liste des identifiants de bouquets à activer (ex : `["lai_corporate_mvp", "press_biotech_premium"]`)
   - `sources_extra_enabled` : liste optionnelle de `source_key` individuels à ajouter en plus des bouquets

2. **Pour chaque `bouquet_id` dans `source_bouquets_enabled`** :
   - Charger le fichier `canonical/sources/source_catalog.yaml`
   - Trouver la définition du bouquet dans la section `bouquets:`
   - Extraire la liste des `source_keys` de ce bouquet

3. **Agréger toutes les sources** :
   - Combiner les `source_keys` de tous les bouquets activés
   - Ajouter les `sources_extra_enabled` (si présents)
   - Dédupliquer la liste finale (un même `source_key` ne doit apparaître qu'une fois)

4. **Résultat** : liste finale des `source_key` à traiter pour ce run d'ingestion

#### Exemple de configuration client

```yaml
# Fragment de lai_weekly.yaml
source_config:
  source_bouquets_enabled:
    - "lai_corporate_mvp"        # Bouquet de 8 sources corporate LAI
    - "press_biotech_premium"    # Bouquet de presse sectorielle
  sources_extra_enabled:
    - "press_corporate__novartis"  # Source additionnelle spécifique
```

#### Exemple de résolution

**Étape 1** : Charger `source_catalog.yaml` et trouver les bouquets :

```yaml
# Dans source_catalog.yaml
bouquets:
  - bouquet_id: "lai_corporate_mvp"
    source_keys:
      - "press_corporate__medincell"
      - "press_corporate__camurus"
      - "press_corporate__g2gbio"
      # ... 5 autres sources
  
  - bouquet_id: "press_biotech_premium"
    source_keys:
      - "press_sector__fiercepharma"
      - "press_sector__endpoints_news"
      # ... autres sources presse
```

**Étape 2** : Extraire les `source_keys` :
- Bouquet `lai_corporate_mvp` → 8 sources corporate
- Bouquet `press_biotech_premium` → 19 sources presse
- Sources extra → 1 source (`press_corporate__novartis`)

**Étape 3** : Dédupliquer et obtenir la liste finale :
- Total : 28 `source_key` uniques à traiter

#### Avantages de cette approche

- **Maintenance simplifiée** : l'admin modifie les bouquets dans `source_catalog.yaml` sans toucher aux configs clients
- **Réutilisabilité** : un même bouquet peut être utilisé par plusieurs clients
- **Flexibilité** : possibilité d'ajouter des sources spécifiques via `sources_extra_enabled`

---

# 5. Phase 1A – Ingestion (SANS Bedrock)

## Objectif

Récupérer les contenus bruts depuis les sources externes (RSS, APIs) et les parser en mémoire.

## Processus

Pour chaque `source_key` activé pour le client :

1. **Effectuer l'appel HTTP** :
   - Flux RSS : requête GET sur l'URL du flux.
   - API (ex : PubMed, ClinicalTrials.gov) : requête GET ou POST selon l'API.

2. **Parser la réponse** :
   - RSS/XML : extraction des balises `<item>`, `<title>`, `<description>`, `<link>`, `<pubDate>`.
   - JSON : extraction des champs pertinents selon la structure de l'API.

3. **Construire une liste d'items bruts en mémoire** :
   - Chaque item brut contient au minimum :
     - `title` (string)
     - `description` ou `body` (string)
     - `url` (string)
     - `date` (string ou ISO8601)
     - `source_key` (string, ex : `"press_corporate__fiercepharma"`)
     - `source_type` (string, ex : `"press_corporate"`)

## Écriture optionnelle en RAW

Pour faciliter le debug et permettre le rejeu, la Lambda **peut** écrire un fichier `raw.json` par source :

- **Emplacement** : `s3://vectora-inbox-data/raw/<client_id>/<source_key>/<YYYY>/<MM>/<DD>/raw.json`
- **Contenu** : liste des items bruts récupérés pour cette source et cette date.
- **Utilité** : permet de rejouer la normalisation sans refaire les appels HTTP, utile pour tester des améliorations de prompts Bedrock.

## Contraintes importantes

- **Aucun appel Bedrock** n'est fait en Phase 1A.
- Cette phase est purement "plomberie HTTP" : requêtes, parsing, stockage temporaire.
- Les items bruts ne sont pas encore enrichis (pas d'extraction d'entités, pas de classification d'événements).

---

# 6. Phase 1B – Normalisation (AVEC Bedrock + règles)

## Objectif

Transformer chaque item brut en **item normalisé** prêt pour le moteur.

Un item normalisé contient :
- Les métadonnées de base (titre, résumé, URL, date, source).
- Les entités détectées (companies, molecules, technologies, indications).
- Le type d'événement (`event_type`).

## 6.1 Entrée de la phase de normalisation

Pour chaque item brut, la Lambda dispose de :

- **Texte** : titre + description (+ contenu complet si disponible).
- **Métadonnées** : `source_key`, `source_type`, date, langue.
- **Listes et patterns canoniques** :
  - Listes de companies, molecules, technologies, indications.
  - Patterns d'événements (`event_type_patterns.yaml`).
  - Mots-clés d'exclusion.

## 6.2 Contrat métier avec Bedrock (normalisation)

Amazon Bedrock est utilisé pour les tâches linguistiques complexes que les règles simples ne peuvent pas gérer.

### Ce que la Lambda envoie à Bedrock

Un prompt structuré contenant :

- **Le texte de l'item** (titre + description).
- **Les listes canoniques** (extraits pertinents) :
  - Exemples de companies, molecules, technologies, indications.
  - Liste des `event_type` possibles (ex : `clinical_update`, `partnership`, `regulatory`, `scientific_paper`, `corporate_move`, `financial_results`, `safety_signal`, `manufacturing_supply`, `other`).
- **Les instructions** :
  - Extraire les entités mentionnées (companies, molecules, technologies, indications).
  - Classifier l'événement parmi les `event_type` prédéfinis.
  - Générer un résumé court (2-3 phrases) expliquant le "so what" de l'item.
  - Respecter la langue du client (anglais ou français selon `client_profile.language`).

### Ce que la Lambda attend en retour de Bedrock

Une réponse structurée (JSON ou texte parsable) contenant :

- **`summary`** (string) : résumé court et factuel de l'item (2-3 phrases).
- **`event_type`** (string) : type d'événement parmi la liste canonique.
  - Si incertain → utiliser `"other"`.
- **`companies_detected`** (liste de strings) : noms des sociétés mentionnées.
- **`molecules_detected`** (liste de strings) : noms des molécules mentionnées.
- **`technologies_detected`** (liste de strings) : technologies identifiées (ex : "long acting", "depot").
- **`indications_detected`** (liste de strings) : indications thérapeutiques identifiées (ex : "opioid use disorder").

### Contraintes pour Bedrock

- **Ne pas inventer de faits** : Bedrock doit se limiter aux informations présentes dans le texte.
- **Si l'event_type est incertain** : utiliser `"other"` plutôt que de deviner.
- **Respecter la langue** : si le client est francophone, le résumé doit être en français.
- **Noms exacts** : conserver les noms de sociétés et molécules tels qu'ils apparaissent dans le texte (pas de traduction, pas de normalisation excessive).

## 6.3 Comment la Lambda utilise les scopes canonical

La Lambda `vectora-inbox-ingest-normalize` charge les scopes canonical pour enrichir la normalisation. Voici le processus détaillé :

### Chargement des scopes par dimension

Pour chaque dimension métier (companies, molecules, trademarks, technologies, indications, exclusions), la Lambda :

1. **Ouvre le fichier canonical correspondant** :
   - `company_scopes.yaml` pour les sociétés
   - `molecule_scopes.yaml` pour les molécules
   - `trademark_scopes.yaml` pour les marques
   - `technology_scopes.yaml` pour les technologies
   - `indication_scopes.yaml` pour les indications
   - `exclusion_scopes.yaml` pour les exclusions

2. **Lit la config client** pour obtenir les clés de scopes à utiliser :
   - Exemple : `company_scope: "lai_companies_global"`

3. **Charge la liste associée à la clé** dans le fichier canonical :
   - Exemple : dans `company_scopes.yaml`, charge la liste à la clé `"lai_companies_global"`

4. **Utilise cette liste** pour :
   - Guider Bedrock dans l'extraction d'entités (en fournissant des exemples dans le prompt)
   - Valider les entités détectées par Bedrock
   - Effectuer une détection complémentaire par mots-clés

### Exemple concret

**Config client `lai_weekly.yaml` :**
```yaml
watch_domains:
  - id: tech_lai_ecosystem
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_all"
    technology_scope: "lai_keywords"
```

**Processus dans la Lambda :**
```python
# Pseudo-code
config = load_client_config("lai_weekly")
domain = config["watch_domains"][0]

# Charger les scopes canonical via les clés
company_scopes = load_yaml("canonical/scopes/company_scopes.yaml")
company_list = company_scopes[domain["company_scope"]]  # Charge "lai_companies_global"

molecule_scopes = load_yaml("canonical/scopes/molecule_scopes.yaml")
molecule_list = molecule_scopes[domain["molecule_scope"]]  # Charge "lai_molecules_all"

# Utiliser ces listes pour la normalisation
for item in raw_items:
    # Fournir company_list et molecule_list à Bedrock dans le prompt
    normalized = normalize_with_bedrock(item, company_list, molecule_list)
```

### Principes importants

- **La Lambda ne lit pas les commentaires YAML** : elle ne sait pas que `"lai_companies_global"` est "LAI". Elle charge juste la liste à cette clé.

- **La Lambda ne devine pas la verticale** : elle ne fait aucune inférence sur le type de verticale (LAI, oncologie, etc.). Elle manipule simplement des listes identifiées par leurs clés.

- **Les noms de clés sont décidés par l'admin** : ils suivent la règle de nommage `{verticale}_{dimension}_{segment}` (ex : `lai_companies_global`).

- **La logique métier est dans le contenu des listes, pas dans le code** : pour changer de verticale, il suffit de créer de nouvelles clés dans les fichiers canonical et de les référencer dans la config client.

## 6.4 Règles supplémentaires (sans Bedrock)

La Lambda combine les propositions de Bedrock avec des règles déterministes :

- **Détection par mots-clés** :
  - Recherche de mots-clés canoniques dans le texte (technologies, indications).
  - Complète ou corrige les propositions de Bedrock.

- **Filtrage par exclusions** :
  - Si l'item contient des mots-clés d'exclusion (ex : "job posting", "webinar"), il peut être marqué comme non pertinent ou filtré.

- **Validation des entités** :
  - Vérifier que les companies/molecules détectées par Bedrock existent dans les listes canoniques ou sont plausibles.

## 6.5 Schéma de l'item normalisé

Chaque item normalisé doit contenir les champs suivants (au niveau métier, pas JSON technique) :

- **`source_key`** (string, obligatoire) : identifiant unique de la source (ex : `"press_corporate__fiercepharma"`).
- **`source_type`** (string, obligatoire) : catégorie de la source (ex : `"press_corporate"`, `"press_sector"`, `"pubmed"`, `"clinicaltrials"`).
- **`title`** (string) : titre de l'item.
- **`summary`** (string) : résumé court généré par Bedrock.
- **`url`** (string) : lien vers la source originale.
- **`date`** (string ISO8601) : date de publication de l'item.
- **`companies_detected`** (liste de strings) : sociétés mentionnées.
- **`molecules_detected`** (liste de strings) : molécules mentionnées.
- **`technologies_detected`** (liste de strings) : technologies identifiées.
- **`indications_detected`** (liste de strings) : indications thérapeutiques identifiées.
- **`event_type`** (string) : type d'événement parmi la liste canonique.

---

# 7. Sorties de la Lambda (S3 et formats)

## Fichier normalisé (obligatoire)

La Lambda écrit un seul fichier par client et par jour :

- **Emplacement** : `s3://vectora-inbox-data/normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`
- **Contenu** : liste JSON d'items normalisés (tous les `source_key` agrégés).
- **Format** : JSON array, chaque élément est un item normalisé.

Exemple de structure :

```json
[
  {
    "source_key": "press_corporate__fiercepharma",
    "source_type": "press_corporate",
    "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
    "summary": "Camurus reported positive results from a Phase 3 trial of Brixadi (buprenorphine) for opioid use disorder...",
    "url": "https://example.com/article",
    "date": "2025-01-15",
    "companies_detected": ["Camurus"],
    "molecules_detected": ["Brixadi", "buprenorphine"],
    "technologies_detected": ["long acting", "depot"],
    "indications_detected": ["opioid use disorder"],
    "event_type": "clinical_update"
  },
  {
    "source_key": "pubmed_lai",
    "source_type": "pubmed",
    "title": "Long-acting injectable antipsychotics: a review",
    "summary": "This review examines the efficacy and safety of long-acting injectable antipsychotics...",
    "url": "https://pubmed.ncbi.nlm.nih.gov/12345678",
    "date": "2025-01-14",
    "companies_detected": [],
    "molecules_detected": ["risperidone", "paliperidone"],
    "technologies_detected": ["long acting", "injectable"],
    "indications_detected": ["schizophrenia"],
    "event_type": "scientific_paper"
  }
]
```

## Fichiers RAW (optionnel, recommandé pour debug)

La Lambda peut écrire un fichier `raw.json` par source :

- **Emplacement** : `s3://vectora-inbox-data/raw/<client_id>/<source_key>/<YYYY>/<MM>/<DD>/raw.json`
- **Contenu** : items bruts récupérés en Phase 1A (avant normalisation).
- **Utilité** : debug, rejeu de la normalisation sans refaire les appels HTTP.

---

# 8. Gestion des erreurs et cas limites

## Que faire si une source ne répond pas ?

- **Log explicite** : enregistrer l'erreur (URL, code HTTP, message d'erreur).
- **Continuer le traitement** : ne pas bloquer les autres sources.
- **Possibilité de retry** : tenter 2-3 fois avec backoff exponentiel.
- **Si échec définitif** : passer à la source suivante, ne pas écrire de fichier `raw.json` pour cette source.

## Que faire si Bedrock renvoie une erreur ?

- **Log explicite** : enregistrer l'erreur (modèle, prompt, message d'erreur).
- **Fallback possible** :
  - Utiliser uniquement les règles déterministes (mots-clés) pour cet item.
  - Marquer l'item comme "partiellement normalisé" (champ `normalization_status: "fallback"`).
- **Si échec critique** : ne pas inclure cet item dans le fichier normalisé (ou l'inclure avec un flag d'erreur).

## Que faire si aucun item valide n'est obtenu ?

- **Log explicite** : indiquer qu'aucun item n'a été récupéré pour ce client et cette date.
- **Possibilités** :
  - Ne pas écrire de fichier `normalized/` (le moteur saura qu'il n'y a rien à traiter).
  - Ou écrire un fichier vide avec un champ `metadata` indiquant l'absence de données :
    ```json
    {
      "metadata": {
        "client_id": "lai_weekly",
        "date": "2025-01-15",
        "status": "no_items",
        "reason": "No items retrieved from sources"
      },
      "items": []
    }
    ```

## Que faire si un item contient des mots-clés d'exclusion ?

- **Filtrer l'item** : ne pas l'inclure dans le fichier normalisé.
- **Log optionnel** : enregistrer les items filtrés pour analyse ultérieure (amélioration des règles d'exclusion).

---

# 9. Hors périmètre de cette Lambda

Cette Lambda **ne fait pas** :

- **Pas de matching avec les watch_domains** : c'est le rôle de `vectora-inbox-engine` (Phase 2).
- **Pas de scoring** : c'est le rôle de `vectora-inbox-engine` (Phase 3).
- **Pas de génération de newsletter** : c'est le rôle de `vectora-inbox-engine` (Phase 4).
- **Pas d'envoi d'e-mails** : hors scope MVP.
- **Pas d'écriture dans le bucket `vectora-inbox-newsletters`** : ce bucket est réservé au moteur.

---

# 10. Exemples d'événements (JSON)

Cette section fournit des exemples concrets d'événements d'entrée et de sortie pour faciliter l'implémentation et les tests.

## 10.1 Exemple d'événement d'entrée (trigger)

**Cas d'usage :** Exécution manuelle pour le client `lai_weekly`, ingérant les données des 7 derniers jours.

```json
{
  "client_id": "lai_weekly",
  "period_days": 7
}
```

**Cas d'usage :** Exécution avec une fenêtre temporelle explicite.

```json
{
  "client_id": "lai_weekly",
  "from_date": "2025-01-08",
  "to_date": "2025-01-15"
}
```

**Cas d'usage :** Exécution pour des sources spécifiques uniquement.

```json
{
  "client_id": "lai_weekly",
  "period_days": 7,
  "sources": [
    "press_corporate__medincell",
    "press_corporate__camurus",
    "press_sector__fiercepharma"
  ]
}
```

## 10.2 Exemple de sortie réussie

**Cas d'usage :** Ingétion et normalisation réussies pour le client `lai_weekly`.

```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T10:30:00Z",
    "period": {
      "from_date": "2025-01-08",
      "to_date": "2025-01-15"
    },
    "sources_processed": 27,
    "items_ingested": 142,
    "items_normalized": 138,
    "items_filtered": 4,
    "s3_output_path": "s3://vectora-inbox-data/normalized/lai_weekly/2025/01/15/items.json",
    "execution_time_seconds": 45.3,
    "message": "Ingestion et normalisation terminées avec succès."
  }
}
```

## 10.3 Exemple de sortie avec erreur

**Cas d'usage :** Échec lors de l'ingéstion (source inaccessible, erreur Bedrock, etc.).

```json
{
  "statusCode": 500,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T10:30:00Z",
    "error_type": "IngestionError",
    "message": "Erreur lors de l'ingéstion de la source press_corporate__medincell : HTTP 503 Service Unavailable",
    "sources_processed": 12,
    "sources_failed": 1,
    "failed_sources": [
      {
        "source_key": "press_corporate__medincell",
        "error": "HTTP 503 Service Unavailable",
        "retry_count": 3
      }
    ],
    "items_normalized": 67,
    "s3_output_path": "s3://vectora-inbox-data/normalized/lai_weekly/2025/01/15/items.json",
    "execution_time_seconds": 32.1
  }
}
```

**Cas d'usage :** Erreur critique (configuration client invalide).

```json
{
  "statusCode": 400,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T10:30:00Z",
    "error_type": "ConfigurationError",
    "message": "Configuration client invalide : champ 'source_config' manquant dans lai_weekly.yaml",
    "execution_time_seconds": 2.1
  }
}
```

---

**Fin du contrat métier pour `vectora-inbox-ingest-normalize`.**

Ce document est destiné à être lu par un humain (développeur, architecte, chef de projet) et par Amazon Q Developer pour implémenter la Lambda sans ambiguïté.
