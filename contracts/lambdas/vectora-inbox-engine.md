# Contrat métier – Lambda `vectora-inbox-engine`

---

# 1. Rôle et objectif de la Lambda

La Lambda `vectora-inbox-engine` est responsable des **Phases 2, 3 et 4** du workflow Vectora Inbox :

- **Phase 2 : Matching** – déterminer quels items normalisés correspondent aux domaines d'intérêt du client (watch_domains).
- **Phase 3 : Scoring** – attribuer un score à chaque item pour prioriser les plus importants.
- **Phase 4 : Génération de la newsletter** – assembler une newsletter structurée, lisible et "premium" avec l'aide d'Amazon Bedrock.

Cette Lambda **ne fait pas** :
- d'ingestion HTTP vers les sources externes,
- de normalisation brute des items (c'est le rôle de `vectora-inbox-ingest-normalize`),
- de gestion d'e-mail (hors scope MVP),
- de scheduling (déclenchement extérieur).

Son rôle est de transformer une liste d'items normalisés en une newsletter actionnable, adaptée aux besoins spécifiques du client.

---

# 2. Contexte dans le workflow Vectora Inbox

La Lambda `vectora-inbox-engine` intervient **après** la phase d'ingestion et de normalisation.

## Prérequis

Elle suppose que les items normalisés existent déjà dans :

- **`s3://vectora-inbox-data/normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`**

## Configurations lues

Elle lit :

- **Configuration canonique** (`s3://vectora-inbox-config/canonical/`) :
  - Scopes de companies, molecules, technologies, indications.
  - Patterns d'événements.
  - Mots-clés d'exclusion.

- **Configuration client** (`s3://vectora-inbox-config/clients/<client_id>.yaml`) :
  - `client_profile` : langue, tone, voice.
  - `watch_domains` : définition des domaines d'intérêt.
  - `newsletter_layout` : structure de la newsletter (sections, max_items).
  - `newsletter_delivery` : périodicité, format export.

## Sorties

Elle écrit dans :

- **`s3://vectora-inbox-newsletters/<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`**

---

# 3. Entrées de la Lambda (événement et données)

La Lambda est déclenchée par un événement JSON contenant les paramètres suivants (au niveau métier) :

## Paramètres obligatoires

- **`client_id`** (string) : identifiant unique du client (ex : `"lai_weekly"`).

## Paramètres optionnels

- **`period_days`** (integer) : nombre de jours à remonter dans le passé pour collecter les items normalisés (ex : `7` pour la dernière semaine).

- **`from_date`** et **`to_date`** (strings ISO8601) : fenêtre temporelle explicite.
  - Exemple : `"from_date": "2025-01-08"`, `"to_date": "2025-01-15"`

- **`target_date`** (string ISO8601) : date de référence pour la newsletter (ex : `"2025-01-15"`).
  - Utilisée pour nommer le fichier de sortie et pour le contexte éditorial.

## Processus de collecte des items

La Lambda :

1. Lit la configuration client pour déterminer la fenêtre temporelle (ex : dernière semaine).
2. Liste les fichiers `items.json` dans la fenêtre temporelle :
   - `s3://vectora-inbox-data/normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json`
3. Charge tous les items normalisés en mémoire.
4. Lit les scopes canoniques et la configuration client.

---

# 4. Configurations lues (canonical + client)

## 4.1 Configuration canonique

Emplacement : `s3://vectora-inbox-config/canonical/`

Contenu :

- **Scopes canoniques** :
  - `company_scopes.yaml` : listes de sociétés groupées par secteur ou technologie.
  - `molecule_scopes.yaml` : listes de molécules groupées par aire thérapeutique.
  - `keywords_technologies.yaml` : mots-clés et synonymes pour les technologies.
  - `keywords_indications.yaml` : mots-clés et synonymes pour les indications.
  - `keywords_exclusions.yaml` : mots-clés pour filtrer le bruit.
  - `event_type_patterns.yaml` : patterns pour classifier les événements.

## 4.2 Configuration client

Emplacement : `s3://vectora-inbox-config/clients/<client_id>.yaml`

Contenu :

- **`client_profile`** :
  - `name` : nom lisible du client.
  - `client_id` : identifiant machine.
  - `language` : langue du client (ex : `"en"`, `"fr"`).
  - `tone` : ton de la newsletter (ex : `"executive"`, `"scientific"`, `"investor"`).
  - `voice` : style rédactionnel (ex : `"concise"`, `"analytical"`, `"conversational"`).
  - `frequency` : périodicité (ex : `"weekly"`, `"monthly"`).

- **`watch_domains`** :
  - Liste des domaines d'intérêt du client.
  - Chaque domaine contient :
    - `id` : identifiant unique du domaine (ex : `"tech_lai_ecosystem"`).
    - `type` : type de domaine (ex : `"technology"`, `"indication"`, `"regulatory"`).
    - Références aux scopes canoniques : `technology_scope`, `company_scope`, `molecule_scope`, `indication_scope`.
    - Entités spécifiques au client : `add_companies`, `add_molecules`.
    - `priority` : priorité du domaine (ex : `"high"`, `"medium"`, `"low"`).

- **`newsletter_layout`** :
  - `sections` : liste des sections de la newsletter.
  - Chaque section contient :
    - `id` : identifiant unique de la section.
    - `title` : titre de la section (ex : `"Top Signals – LAI Ecosystem"`).
    - `source_domains` : liste des `watch_domains` à inclure dans cette section.
    - `max_items` : nombre maximum d'items à afficher dans cette section.
    - `filter_event_types` (optionnel) : liste des `event_type` à inclure (ex : `["partnership"]`).

- **`newsletter_delivery`** :
  - `format` : format de sortie (ex : `"markdown"`, `"html"`, `"pdf"`).
  - `include_tldr` : inclure un TL;DR en haut de la newsletter (boolean).
  - `include_intro` : inclure un paragraphe d'introduction (boolean).
  - `delivery_method` : méthode de livraison (ex : `"s3"`, `"email"`).
  - `notification_email` : adresse e-mail pour notification (optionnel).

---

# 5. Phase 2 – Matching (SANS Bedrock)

## Objectif

Déterminer, pour chaque item normalisé, à quels `watch_domains` il appartient.

## Comment la Lambda utilise les scopes canonical pour le matching

La Lambda `vectora-inbox-engine` charge les scopes canonical pour effectuer le matching. Voici le processus détaillé :

### Chargement des scopes par watch_domain

Pour chaque `watch_domain` défini dans la config client, la Lambda :

1. **Lit les clés de scopes référencées** dans le domaine :
   - `company_scope` (ex : `"lai_companies_global"`)
   - `molecule_scope` (ex : `"lai_molecules_all"`)
   - `trademark_scope` (ex : `"lai_trademarks_global"`)
   - `technology_scope` (ex : `"lai_keywords"`)
   - `indication_scope` (ex : `"addiction_keywords"`)

2. **Ouvre les fichiers canonical correspondants** :
   - `company_scopes.yaml`, `molecule_scopes.yaml`, `trademark_scopes.yaml`, etc.

3. **Charge les listes associées aux clés** :
   - Exemple : dans `company_scopes.yaml`, charge la liste à la clé `"lai_companies_global"`

4. **Utilise ces listes pour calculer les intersections** avec les champs détectés dans l'item normalisé.

### Exemple concret

**Item normalisé :**
```json
{
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "companies_detected": ["Camurus"],
  "molecules_detected": ["Brixadi", "buprenorphine"],
  "technologies_detected": ["long acting", "depot"],
  "indications_detected": ["opioid use disorder"],
  "event_type": "clinical_update"
}
```

**Config client - watch_domain :**
```yaml
watch_domains:
  - id: tech_lai_ecosystem
    company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_all"
    technology_scope: "lai_keywords"
```

**Fichier `canonical/scopes/company_scopes.yaml` :**
```yaml
lai_companies_global:
  - Camurus
  - Alkermes
  - Indivior
```

**Processus dans la Lambda :**
```python
# Pseudo-code
config = load_client_config("lai_weekly")
domain = config["watch_domains"][0]  # tech_lai_ecosystem

# Charger les scopes via les clés
company_scopes = load_yaml("canonical/scopes/company_scopes.yaml")
company_list = company_scopes[domain["company_scope"]]  # ["Camurus", "Alkermes", "Indivior"]

# Calculer l'intersection
item_companies = set(item["companies_detected"])  # {"Camurus"}
scope_companies = set(company_list)  # {"Camurus", "Alkermes", "Indivior"}

if item_companies & scope_companies:  # {"Camurus"} ∩ {...} = {"Camurus"} (non vide)
    # L'item matche ce domaine
    item["matched_domains"].append("tech_lai_ecosystem")
```

**Résultat :** L'item est ajouté au domaine `tech_lai_ecosystem` car `"Camurus"` est présent dans la liste `lai_companies_global`.

### Principes importants

- **Le moteur ne "connaît" pas la verticale** : il ne sait pas que `"lai_companies_global"` est "LAI". Il charge juste la liste à cette clé et calcule des intersections.

- **La logique de verticale est encodée dans** :
  - Le **contenu des listes canonical** (quelles sociétés, molécules, etc.)
  - Le **choix des scopes dans la config client** (quelles clés référencer)

- **Les Lambdas manipulent des ensembles** : elles effectuent des opérations d'intersection, union, différence sur les listes chargées via les clés.

- **Pas d'inférence, pas de devinette** : tout est déterministe et basé sur les configurations.

### Résumé du processus de chargement des scopes

**Pour chaque watch_domain dans la config client :**

1. **Lire les clés de scopes** dans le domaine (ex : `company_scope: "lai_companies_global"`)

2. **Charger les fichiers canonical** correspondants :
   - `canonical/scopes/company_scopes.yaml`
   - `canonical/scopes/molecule_scopes.yaml`
   - `canonical/scopes/technology_scopes.yaml`
   - etc.

3. **Extraire les listes** associées aux clés :
   - Dans `company_scopes.yaml`, chercher la clé `"lai_companies_global"` et récupérer la liste
   - Dans `molecule_scopes.yaml`, chercher la clé `"lai_molecules_all"` et récupérer la liste
   - etc.

4. **Construire en mémoire des ensembles** (sets Python) pour chaque dimension :
   - `companies_in_scope = set(["Camurus", "Alkermes", ...])`
   - `molecules_in_scope = set(["buprenorphine", "naltrexone", ...])`
   - `keywords_in_scope = set(["long acting", "depot", ...])`

5. **Utiliser ces ensembles** pour le matching et le scoring :
   - Calculer les intersections avec les champs détectés dans les items
   - Déterminer si un item appartient au domaine
   - Calculer des bonus de score si des entités clés sont présentes

**Exemple de code pseudo-Python :**

```python
# Charger la config client
config = load_yaml("s3://vectora-inbox-config/clients/lai_weekly.yaml")

# Pour chaque watch_domain
for domain in config["watch_domains"]:
    # Charger les scopes canonical via les clés
    company_scopes_file = load_yaml("s3://vectora-inbox-config/canonical/scopes/company_scopes.yaml")
    companies_in_scope = set(company_scopes_file[domain["company_scope"]])
    
    molecule_scopes_file = load_yaml("s3://vectora-inbox-config/canonical/scopes/molecule_scopes.yaml")
    molecules_in_scope = set(molecule_scopes_file[domain["molecule_scope"]])
    
    # Pour chaque item normalisé
    for item in normalized_items:
        # Calculer les intersections
        item_companies = set(item["companies_detected"])
        item_molecules = set(item["molecules_detected"])
        
        if (item_companies & companies_in_scope) or (item_molecules & molecules_in_scope):
            # L'item matche ce domaine
            item["matched_domains"].append(domain["id"])
```

## Logique de matching

Pour chaque item normalisé :

1. **Charger les champs détectés** :
   - `technologies_detected` (liste de strings)
   - `indications_detected` (liste de strings)
   - `companies_detected` (liste de strings)
   - `molecules_detected` (liste de strings)

2. **Pour chaque `watch_domain` défini dans la config client** :
   - Calculer les intersections :
     - `technologies_detected` ∩ scopes de technologies activés dans ce domaine.
     - `indications_detected` ∩ scopes d'indications activés dans ce domaine.
     - `companies_detected` ∩ scopes de companies activés dans ce domaine (canoniques + ajouts client).
     - `molecules_detected` ∩ scopes de molecules activés dans ce domaine (canoniques + ajouts client).

3. **Décider si l'item appartient au domaine** :
   - Si au moins une intersection est non vide → l'item appartient au domaine.
   - Un item peut appartenir à plusieurs domaines.

4. **Annoter l'item** :
   - Ajouter un champ `matched_domains` (liste de `watch_domain` IDs) à l'item en mémoire.

## Contraintes importantes

- **Matching = logique déterministe** : intersections d'ensembles, règles if/else.
- **Pas d'appel Bedrock** : tout est contrôlé par les configurations canoniques et client.
- **Transparence** : un humain doit pouvoir comprendre pourquoi un item a été matché à un domaine.

## Exemple

Item normalisé :
```json
{
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "companies_detected": ["Camurus"],
  "molecules_detected": ["Brixadi", "buprenorphine"],
  "technologies_detected": ["long acting", "depot"],
  "indications_detected": ["opioid use disorder"],
  "event_type": "clinical_update"
}
```

Watch domain `tech_lai_ecosystem` :
- `technology_scope`: `LAI_keywords` (contient "long acting", "depot")
- `company_scope`: `LAI_companies` (contient "Camurus")

Résultat : l'item est matché au domaine `tech_lai_ecosystem`.

---

# 6. Phase 3 – Scoring (SANS Bedrock pour le MVP)

## Objectif

Attribuer un score numérique à chaque item pour prioriser les plus importants.

## Facteurs de scoring

Le score d'un item est calculé en combinant plusieurs facteurs (sans entrer dans des formules détaillées) :

1. **Importance de l'`event_type`** :
   - `clinical_update`, `regulatory`, `approval` → score élevé.
   - `partnership`, `scientific_paper` → score moyen.
   - `corporate_move`, `financial_results` → score plus faible.
   - `other` → score minimal.

2. **Récence de l'événement** :
   - Items plus récents → score plus élevé.
   - Décroissance exponentielle avec le temps.

3. **Priorité du `watch_domain`** :
   - Items matchés à des domaines `priority: "high"` → boost de score.
   - Items matchés à des domaines `priority: "low"` → score réduit.

4. **Présence de compétiteurs clés** :
   - Si l'item mentionne des sociétés prioritaires (définies dans la config client) → boost de score.

5. **Présence de molécules clés** :
   - Si l'item mentionne des molécules prioritaires → boost de score.

6. **Type de source (`source_type`)** :
   - Sources réglementaires (`regulatory`) → score élevé.
   - Sources cliniques (`clinicaltrials`, `pubmed`) → score moyen-élevé.
   - Presse sectorielle (`press_sector`) → score moyen.
   - Presse corporate (`press_corporate`) → score plus faible.

7. **Longueur / richesse de l'item** :
   - Items avec plus d'entités détectées → score légèrement plus élevé (signal de richesse).

## Contraintes importantes

- **Scoring = règles simples et transparentes** : pas d'IA, pas de boîte noire.
- **Pas d'appel Bedrock** : tout est calculé avec des formules numériques.
- **Tunabilité** : les poids de chaque facteur peuvent être ajustés via la configuration client (ou dans le code si nécessaire).
- **Explicabilité** : un humain doit pouvoir comprendre pourquoi un item a un score élevé ou faible.

## Résultat

Chaque item se voit attribuer un score numérique (ex : entre 0 et 100).

Les items sont ensuite triés par score décroissant au sein de chaque `watch_domain`.

---

# 7. Phase 4 – Assemblage de la newsletter (AVEC Bedrock)

## Objectif

Transformer une liste d'items scorés en une newsletter structurée, lisible et "premium".

## 7.1 Entrées de la phase newsletter

- **Items sélectionnés** : top N items par section (selon `newsletter_layout.sections[].max_items`).
- **Regroupement par section** : items organisés selon `newsletter_layout.sections`.
- **`client_profile`** : tone, voice, langue.
- **Paramétrage `newsletter_delivery`** : format, include_tldr, include_intro.

## 7.2 Contrat métier avec Bedrock (génération éditoriale)

Amazon Bedrock est utilisé pour les tâches éditoriales que les règles simples ne peuvent pas gérer.

### Ce que la Lambda envoie à Bedrock

Un prompt structuré contenant :

- **Liste des items retenus par section** :
  - Pour chaque item : titre, summary, score, source, URL, date, entités détectées.
- **Contexte global de la semaine** :
  - Période couverte (ex : "semaine du 8 au 15 janvier 2025").
  - Nombre total d'items analysés.
  - Domaines d'intérêt du client.
- **Attentes sur le ton** :
  - Ton : executive, scientific, investor (selon `client_profile.tone`).
  - Voice : concise, analytical, conversational (selon `client_profile.voice`).
  - Langue : anglais ou français (selon `client_profile.language`).
- **Structure attendue** :
  - Titre de la newsletter.
  - Paragraphe d'introduction (chapeau).
  - TL;DR (2-5 bullet points).
  - Sections (titres, intros, items).

### Ce qu'elle attend en retour de Bedrock

Une réponse structurée (Markdown ou JSON parsable) contenant :

1. **Titre de la newsletter** :
   - Exemple : "Weekly Biotech Intelligence – January 15, 2025"
   - Exemple (français) : "Veille Biotech Hebdomadaire – 15 janvier 2025"

2. **Paragraphe d'introduction (chapeau)** :
   - 2-4 phrases résumant le contexte de la semaine.
   - Exemple : "Cette semaine a été marquée par plusieurs avancées cliniques dans le domaine des LAI, notamment les résultats positifs de Camurus pour Brixadi. Les partenariats stratégiques se multiplient dans le secteur de l'addiction, tandis que la FDA continue d'accélérer les approbations de nouvelles formulations."

3. **TL;DR (Too Long; Didn't Read)** :
   - 3 à 5 bullet points résumant les signaux les plus importants de la semaine.
   - Exemple :
     - "Camurus annonce des résultats positifs de Phase 3 pour Brixadi dans le traitement de l'addiction aux opioïdes."
     - "Partenariat stratégique entre Alkermes et un acteur majeur de la santé mentale."
     - "La FDA approuve une nouvelle formulation LAI pour la schizophrénie."

4. **Pour chaque section** :
   - **Texte d'introduction de la section** (1-2 phrases) :
     - Exemple : "Le secteur des LAI continue de se structurer avec plusieurs annonces majeures cette semaine."
   - **Formulations synthétiques pour chaque item** :
     - Réécriture du summary en respectant le ton/voice du client.
     - Inclusion du lien source.
     - Exemple :
       ```markdown
       **Camurus – Résultats positifs de Phase 3 pour Brixadi**  
       Camurus a annoncé des résultats positifs pour son essai de Phase 3 de Brixadi (buprenorphine) dans le traitement de l'addiction aux opioïdes. Cette avancée renforce la position de Camurus dans le segment des LAI pour l'addiction.  
       [Lire l'article](https://example.com/article)
       ```

### Contraintes pour Bedrock

- **Ne pas halluciner** : Bedrock doit se limiter aux informations présentes dans les items fournis.
- **Ne pas inventer de faits** : pas de chiffres, dates, ou noms inventés.
- **Respecter la langue du client** : si le client est francophone, tout le contenu doit être en français.
- **Garder les noms exacts** : noms de sociétés, molécules, technologies doivent être conservés tels quels (pas de traduction).
- **Ton cohérent** : respecter le tone et voice définis dans `client_profile`.

## 7.3 Assemblage du Markdown

La Lambda assemble la sortie de Bedrock en un document Markdown cohérent :

1. **En-tête** :
   - Titre de la newsletter (généré par Bedrock).
   - Date de génération.

2. **Introduction** :
   - Paragraphe d'introduction (généré par Bedrock).

3. **TL;DR** :
   - Liste de bullet points (générée par Bedrock).

4. **Sections** :
   - Pour chaque section définie dans `newsletter_layout.sections` :
     - Titre de la section (depuis la config).
     - Texte d'introduction de la section (généré par Bedrock).
     - Liste des items (formulations générées par Bedrock + liens sources).

5. **Pied de page** (optionnel) :
   - Informations de contact, disclaimer, etc.

## Exemple de structure Markdown

```markdown
# Weekly Biotech Intelligence – January 15, 2025

Cette semaine a été marquée par plusieurs avancées cliniques dans le domaine des LAI, notamment les résultats positifs de Camurus pour Brixadi. Les partenariats stratégiques se multiplient dans le secteur de l'addiction, tandis que la FDA continue d'accélérer les approbations de nouvelles formulations.

## TL;DR

- Camurus annonce des résultats positifs de Phase 3 pour Brixadi dans le traitement de l'addiction aux opioïdes.
- Partenariat stratégique entre Alkermes et un acteur majeur de la santé mentale.
- La FDA approuve une nouvelle formulation LAI pour la schizophrénie.

---

## Top Signals – LAI Ecosystem

Le secteur des LAI continue de se structurer avec plusieurs annonces majeures cette semaine.

**Camurus – Résultats positifs de Phase 3 pour Brixadi**  
Camurus a annoncé des résultats positifs pour son essai de Phase 3 de Brixadi (buprenorphine) dans le traitement de l'addiction aux opioïdes. Cette avancée renforce la position de Camurus dans le segment des LAI pour l'addiction.  
[Lire l'article](https://example.com/article)

**Alkermes – Partenariat stratégique pour Vivitrol**  
Alkermes a signé un partenariat avec un acteur majeur de la santé mentale pour étendre la distribution de Vivitrol (naltrexone) en Europe.  
[Lire l'article](https://example.com/article2)

---

## Addiction – All Modalities

Les innovations dans le traitement de l'addiction se multiplient, avec des approches variées (LAI, oraux, digitaux).

**Indivior – Lancement de Sublocade en Asie**  
Indivior a annoncé le lancement de Sublocade (buprenorphine LAI) dans plusieurs pays asiatiques, marquant une expansion géographique significative.  
[Lire l'article](https://example.com/article3)

---

*Newsletter générée par Vectora Inbox – Powered by Amazon Bedrock*
```

---

# 8. Sorties de la Lambda (S3 et format)

## Fichier newsletter (obligatoire)

La Lambda écrit un fichier Markdown à l'emplacement :

- **`s3://vectora-inbox-newsletters/<client_id>/<YYYY>/<MM>/<DD>/newsletter.md`**

Où :
- `<client_id>` : identifiant du client (ex : `lai_weekly`).
- `<YYYY>/<MM>/<DD>` : date de référence de la newsletter (ex : `2025/01/15`).

## Formats futurs (hors scope MVP)

- **HTML** : conversion du Markdown en HTML avec CSS.
- **PDF** : génération d'un PDF à partir du HTML.

Pour le MVP, on se concentre sur **Markdown uniquement**.

---

# 9. Gestion des erreurs et cas limites

## Que faire s'il n'y a aucun item sélectionné ?

- **Newsletter minimale** : générer une newsletter avec un message explicite.
  - Exemple : "Aucun signal critique cette semaine. Nous continuons de surveiller vos domaines d'intérêt."
- **Log explicite** : enregistrer l'absence d'items pour analyse ultérieure.

## Que faire si Bedrock échoue pour la génération éditoriale ?

- **Fallback possible** :
  - Générer une newsletter plus simple sans l'aide de Bedrock.
  - Utiliser les summaries existants des items normalisés (sans réécriture).
  - Ajouter un disclaimer : "Newsletter générée en mode dégradé."
- **Log explicite** : enregistrer l'erreur (modèle, prompt, message d'erreur).

## Que faire si la configuration client est invalide ?

- **Validation au démarrage** : vérifier que la config client est bien formée (YAML valide, champs obligatoires présents).
- **Si invalide** : lever une erreur explicite et arrêter le traitement.
- **Log explicite** : indiquer quel champ est manquant ou invalide.

## Que faire si les items normalisés sont absents ?

- **Vérifier l'existence des fichiers** `normalized/<client_id>/<YYYY>/<MM>/<DD>/items.json` dans la fenêtre temporelle.
- **Si aucun fichier trouvé** :
  - Log explicite : "Aucun item normalisé trouvé pour la période demandée."
  - Newsletter minimale avec un message explicite.

---

# 10. Hors périmètre de cette Lambda

Cette Lambda **ne fait pas** :

- **Pas d'appel HTTP externe vers les sources** : c'est le rôle de `vectora-inbox-ingest-normalize`.
- **Pas de normalisation brute** : c'est le rôle de `vectora-inbox-ingest-normalize`.
- **Pas de gestion d'e-mail** : hors scope MVP (peut être ajouté plus tard avec SES).
- **Pas de scheduling** : le déclenchement est extérieur (manuel pour le MVP, EventBridge plus tard).
- **Pas de génération HTML/PDF** : hors scope MVP (Markdown uniquement).

---

# 11. Exemples d'événements (JSON)

Cette section fournit des exemples concrets d'événements d'entrée et de sortie pour faciliter l'implémentation et les tests.

## 11.1 Exemple d'événement d'entrée (trigger)

**Cas d'usage :** Exécution manuelle pour le client `lai_weekly`, traitant les items des 7 derniers jours.

```json
{
  "client_id": "lai_weekly",
  "period_days": 7,
  "target_date": "2025-01-15"
}
```

**Cas d'usage :** Exécution avec une fenêtre temporelle explicite.

```json
{
  "client_id": "lai_weekly",
  "from_date": "2025-01-08",
  "to_date": "2025-01-15",
  "target_date": "2025-01-15"
}
```

## 11.2 Exemple de sortie réussie

**Cas d'usage :** Génération de newsletter réussie pour le client `lai_weekly`.

```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T11:45:00Z",
    "target_date": "2025-01-15",
    "period": {
      "from_date": "2025-01-08",
      "to_date": "2025-01-15"
    },
    "items_analyzed": 138,
    "items_matched": 87,
    "items_selected": 13,
    "sections_generated": 2,
    "s3_output_path": "s3://vectora-inbox-newsletters/lai_weekly/2025/01/15/newsletter.md",
    "execution_time_seconds": 28.7,
    "message": "Newsletter générée avec succès."
  }
}
```

## 11.3 Exemple de sortie avec erreur

**Cas d'usage :** Échec lors de la génération (erreur Bedrock, items normalisés absents, etc.).

```json
{
  "statusCode": 500,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T11:45:00Z",
    "error_type": "BedrockError",
    "message": "Erreur lors de la génération éditoriale avec Bedrock : ThrottlingException - Rate limit exceeded",
    "items_analyzed": 138,
    "items_matched": 87,
    "fallback_used": true,
    "s3_output_path": "s3://vectora-inbox-newsletters/lai_weekly/2025/01/15/newsletter.md",
    "execution_time_seconds": 15.2,
    "note": "Newsletter générée en mode dégradé (sans réécriture Bedrock)."
  }
}
```

**Cas d'usage :** Aucun item normalisé trouvé pour la période demandée.

```json
{
  "statusCode": 404,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T11:45:00Z",
    "error_type": "NoDataError",
    "message": "Aucun item normalisé trouvé pour la période du 2025-01-08 au 2025-01-15.",
    "period": {
      "from_date": "2025-01-08",
      "to_date": "2025-01-15"
    },
    "execution_time_seconds": 3.4,
    "note": "Vérifier que la Lambda ingest-normalize a bien été exécutée pour cette période."
  }
}
```

**Cas d'usage :** Configuration client invalide.

```json
{
  "statusCode": 400,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T11:45:00Z",
    "error_type": "ConfigurationError",
    "message": "Configuration client invalide : champ 'newsletter_layout' manquant dans lai_weekly.yaml",
    "execution_time_seconds": 1.8
  }
}
```

---

**Fin du contrat métier pour `vectora-inbox-engine`.**

Ce document est destiné à être lu par un humain (développeur, architecte, chef de projet) et par Amazon Q Developer pour implémenter la Lambda sans ambiguïté.
