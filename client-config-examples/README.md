# Guide de configuration client pour Vectora Inbox

Ce guide vous explique comment créer et configurer une nouvelle newsletter de veille sectorielle avec Vectora Inbox.

## À quoi sert une config client ?

Une **configuration client** (fichier `client-config-*.yaml`) décrit ce que Vectora Inbox doit surveiller pour un client donné et comment générer sa newsletter personnalisée.

Concrètement, ce fichier permet de définir :

- **L'identité du client** : identifiant unique (`client_id`), nom de la newsletter, langue
- **La verticale métier** : pour l'instant, LAI (Long-Acting Injectables)
- **La fréquence de génération** : hebdomadaire (`weekly`), mensuelle (`monthly`), etc.
- **Les sources d'information activées** : via des bouquets réutilisables (ex: sites corporate, presse spécialisée)
- **Les scopes métier** : listes d'entreprises, molécules, technologies et mots-clés à surveiller
- **La structure de la newsletter** : sections, nombre d'items par section, filtres par type d'événement

En résumé : **ce fichier décrit ce qu'on surveille pour un client et avec quelles sources**.

---

## Inventaire des briques disponibles pour configurer un client

Vectora Inbox fonctionne avec des **briques réutilisables** : des scopes métier (listes d'entreprises, molécules, mots-clés) et des bouquets de sources (groupes de sites web). Voici ce qui existe déjà dans le dépôt.

### Scopes d'entreprises (company_scopes.yaml)

Les scopes d'entreprises regroupent les sociétés pharmaceutiques et biotechs actives dans le domaine LAI.

- **`lai_companies_global`** : liste exhaustive des entreprises LAI suivies globalement (environ 180 sociétés : AbbVie, Alkermes, Amgen, Camurus, Eli Lilly, Gilead, Indivior, Ipsen, Janssen, MedinCell, Novo Nordisk, Pfizer, Sanofi, Takeda, etc.)

**Utilisation** : ce scope permet de détecter les actualités mentionnant ces entreprises dans les textes ingérés.

### Scopes de molécules (molecule_scopes.yaml)

Les scopes de molécules regroupent les principes actifs (DCI / INN) utilisés dans les formulations LAI.

- **`lai_molecules_global`** : liste globale des molécules LAI (environ 90 molécules : aripiprazole, buprenorphine, cabotegravir, exenatide, leuprolide, naltrexone, olanzapine, paliperidone, risperidone, semaglutide, somatropin, testosterone, etc.)
- **`lai_molecules_addiction`** : molécules LAI pour addiction / OUD (vide pour l'instant, à remplir plus tard)
- **`lai_molecules_psychiatry`** : molécules LAI pour psychiatrie (vide pour l'instant, à remplir plus tard)
- **`lai_molecules_other`** : autres molécules LAI (vide pour l'instant)
- **`lai_molecules_all`** : union de tous les scopes de molécules LAI (vide pour l'instant, à remplir manuellement ou par script)

**Utilisation** : ces scopes permettent de détecter les actualités mentionnant ces molécules dans les textes ingérés.

### Scopes de technologies (technology_scopes.yaml)

Les scopes de technologies regroupent les mots-clés et expressions indiquant des formulations ou technologies LAI.

- **`lai_keywords`** : mots-clés génériques pour identifier les technologies LAI dans les textes (environ 80 termes : "long-acting", "extended-release injection", "depot injection", "PLGA microspheres", "PEGylation", "Fc fusion", "subcutaneous", "once-monthly", "q4w", etc.)
- **`lai_delivery_systems`** : systèmes de délivrance spécifiques (vide pour l'instant, à compléter si pertinent)
- **`lai_formulation_technologies`** : technologies de formulation (vide pour l'instant, à compléter si pertinent)

**Utilisation** : ces scopes permettent de détecter les actualités mentionnant ces technologies dans les textes ingérés.

### Scopes de trademarks (trademark_scopes.yaml)

Les scopes de trademarks regroupent les noms commerciaux de médicaments LAI.

- **`lai_trademarks_global`** : noms de marque globaux LAI (environ 70 produits : Abilify Maintena, Aristada, Brixadi, Bydureon, Cabenuva, Camcevi, Exparel, Invega Trinza, Lupron Depot, Mounjaro, Ozempic, Perseris, Risperdal Consta, Sublocade, Trulicity, Uzedy, Vivitrol, Wegovy, Zyprexa Relprevv, etc.)

**Utilisation** : ces scopes permettent de détecter les actualités mentionnant ces noms de marque dans les textes ingérés.

### Scopes d'exclusions (exclusion_scopes.yaml)

Les scopes d'exclusions regroupent les mots-clés et contextes à exclure pour réduire le bruit (faux positifs).

- **`lai_exclude_noise`** : termes génériques à exclure (environ 15 termes : "implantable device", "transdermal patch", "oral tablet", "cosmetic", "veterinary", "vaccine", "gene therapy", "cell therapy", "CAR-T", etc.)
- **`exclude_contexts`** : contextes non pertinents (vide pour l'instant, à compléter si besoin)
- **`lai_exclusion_scopes`** : autres exclusions (vide pour l'instant)

**Utilisation** : ces scopes permettent de filtrer les actualités non pertinentes.

### Scopes d'indications thérapeutiques (indication_scopes.yaml)

Les scopes d'indications regroupent les mots-clés indiquant les indications thérapeutiques cibles.

- **`addiction_keywords`** : mots-clés pour addiction / OUD (vide pour l'instant, à remplir plus tard)
- **`psychiatry_keywords`** : mots-clés pour psychiatrie (vide pour l'instant, à remplir plus tard)
- **`other_indications_keywords`** : autres indications (vide pour l'instant)

**Utilisation** : ces scopes permettront de segmenter la veille par indication thérapeutique (fonctionnalité non-MVP).

---

### Bouquets de sources disponibles

Un **bouquet** est un groupe de sources (sites web, flux RSS, APIs) que l'on peut activer d'un coup dans une config client. Cela simplifie la maintenance : au lieu de lister 100 sources individuellement, on active un bouquet qui les regroupe.

Les bouquets sont définis dans `canonical/sources/source_catalog.yaml`.

#### Bouquets corporate LAI

- **`lai_corporate_mvp`** : sous-bouquet MVP pour tester l'ingestion avec quelques sites corporate LAI représentatifs (8 sources : MedinCell, Camurus, G2GBio, Alkermes, Indivior, Ascendis Pharma, Novo Nordisk, Ipsen)
- **`lai_corporate_all`** : bouquet complet avec tous les sites corporate des entreprises LAI (environ 180 sources)

**Utilisation** : ces bouquets permettent de surveiller les communiqués de presse et actualités publiés sur les sites institutionnels des entreprises LAI.

#### Bouquets de presse biotech/pharma

- **`press_biotech_premium`** : sélection de presse sectorielle biotech/pharma premium (19 sources : FiercePharma, FierceBiotech, Endpoints News, BioCentury, BioWorld, Genetic Engineering News, Pink Sheet, Scrip Intelligence, etc.)

**Utilisation** : ce bouquet permet de surveiller l'actualité sectorielle (deals, essais cliniques, approbations réglementaires, etc.) dans la presse spécialisée.

---

## Comment créer une nouvelle config client (étape par étape)

Voici la démarche à suivre pour créer une nouvelle configuration client.

### 1. Choisir la verticale

Pour l'instant, Vectora Inbox ne supporte que la verticale **LAI** (Long-Acting Injectables).

Cela influence principalement les scopes métier : tous les scopes LAI sont préfixés `lai_*` (ex: `lai_companies_global`, `lai_molecules_global`, `lai_keywords`).

### 2. Choisir les bouquets de sources

Vous devez décider quelles sources d'information activer pour ce client.

**Recommandations** :

- **Pour un MVP ou un test** : commencez par `lai_corporate_mvp` (8 sources corporate LAI) + `press_biotech_premium` (19 sources de presse). Cela permet de tester l'ingestion avec un volume gérable.
- **Pour une veille complète** : utilisez `lai_corporate_all` (180 sources corporate LAI) + `press_biotech_premium`. Attention, cela génère beaucoup plus de données à traiter.

**Où trouver la liste des bouquets ?** Dans `canonical/sources/source_catalog.yaml`, section `bouquets:`.

### 3. Choisir les scopes métier

Vous devez définir quels scopes métier utiliser pour ce client. Les scopes déterminent ce que Vectora Inbox va surveiller dans les textes ingérés.

**Scopes obligatoires pour un domaine de veille LAI** :

- **`company_scope`** : choisir un scope dans "Scopes d'entreprises" (ex: `lai_companies_global`)
- **`molecule_scope`** : choisir un scope dans "Scopes de molécules" (ex: `lai_molecules_global`)
- **`technology_scope`** : choisir un scope dans "Scopes de technologies" (ex: `lai_keywords`)

**Important** : ces clés doivent exister dans les fichiers `canonical/scopes/*.yaml`. Si vous créez une nouvelle clé, vous devez d'abord l'ajouter dans le fichier de scopes correspondant.

### 4. Paramètres de base

Vous devez définir les paramètres de base de la newsletter :

- **`client_id`** : identifiant unique du client (ex: `lai_weekly`, `lai_monthly_addiction`)
- **`name`** : nom de la newsletter (ex: "LAI Intelligence Weekly")
- **`frequency`** : fréquence de génération (`"weekly"`, `"monthly"`, etc.)
- **`language`** : langue de la newsletter (`"en"`, `"fr"`, etc.)
- **`tone`** : ton de la newsletter (`"executive"`, `"technical"`, etc.)
- **`voice`** : style de la newsletter (`"concise"`, `"detailed"`, etc.)

**Autres paramètres optionnels** :

- **`newsletter_title`** : titre de la newsletter (si différent du `name`)
- **`notification_email`** : email de notification pour la livraison
- **`delivery_method`** : méthode de livraison (`"s3"`, `"email"`, etc.)
- **`include_tldr`** : inclure un résumé exécutif (TL;DR) dans la newsletter (`true` / `false`)
- **`include_intro`** : inclure une introduction dans la newsletter (`true` / `false`)

### 5. Tester progressivement

**Recommandation** : commencez petit, puis étendez progressivement.

1. **Commencez par peu de sources** : utilisez `lai_corporate_mvp` (8 sources) pour tester l'ingestion
2. **Vérifiez que les clés de scopes existent** : ouvrez les fichiers `canonical/scopes/*.yaml` et vérifiez que les clés que vous utilisez (ex: `lai_companies_global`) sont bien définies
3. **Testez la génération de la newsletter** : lancez la Lambda engine avec cette config et vérifiez le résultat
4. **Étendez ensuite** : passez à `lai_corporate_all` (180 sources) et ajoutez d'autres bouquets si nécessaire

---

## Exemple de config client minimal commenté

Voici un exemple complet mais minimal de configuration client, basé sur la structure réelle de `lai_weekly.yaml`, mais simplifié pour faciliter la compréhension.

```yaml
# Profil du client : identité et paramètres de base de la newsletter.
client_profile:
  name: "LAI Intelligence Weekly"
  client_id: "lai_weekly"
  language: "en"              # Langue de la newsletter finale (en, fr, etc.)
  tone: "executive"           # Ton professionnel et synthétique
  voice: "concise"            # Style concis
  frequency: "weekly"         # Fréquence de génération : hebdomadaire

# Domaines de veille : définit ce que le client souhaite surveiller.
# Chaque domaine correspond à un ensemble de scopes métier (entreprises, molécules, technologies).
watch_domains:
  - id: "tech_lai_ecosystem"
    type: "technology"
    # Références aux scopes canonical (ces clés DOIVENT exister dans canonical/scopes/)
    technology_scope: "lai_keywords"           # Mots-clés LAI (voir technology_scopes.yaml)
    company_scope: "lai_companies_global"      # Entreprises LAI (voir company_scopes.yaml)
    molecule_scope: "lai_molecules_global"     # Molécules LAI (voir molecule_scopes.yaml)
    priority: "high"                           # Priorité haute pour ce domaine

  - id: "regulatory_lai"
    type: "regulatory"
    technology_scope: "lai_keywords"           # Surveillance réglementaire LAI
    priority: "high"

# Configuration des sources d'information.
# On utilise des BOUQUETS (groupes de sources prédéfinis) plutôt que de lister
# chaque source individuellement. Cela simplifie la maintenance.
source_config:
  # Bouquets activés : liste des bouquets à utiliser pour l'ingestion.
  # Ces bouquets sont définis dans canonical/sources/source_catalog.yaml
  source_bouquets_enabled:
    - "lai_corporate_mvp"        # Sous-ensemble MVP de sites corporate LAI (8 sources)
    - "press_biotech_premium"    # Presse sectorielle pharma/biotech (19 sources)
  
  # Sources supplémentaires (optionnel) : permet d'ajouter des sources spécifiques
  # en plus des bouquets, si besoin.
  # Exemple : ["press_corporate__novartis", "press_sector__nature_biotechnology"]
  sources_extra_enabled: []

# Structure de la newsletter finale.
# Définit les sections de la newsletter et les règles de sélection des items.
newsletter_layout:
  sections:
    - id: "top_signals"
      title: "Top Signals – LAI Ecosystem"
      source_domains:
        - "tech_lai_ecosystem"    # Signaux technologiques LAI
        - "regulatory_lai"        # Signaux réglementaires LAI
      max_items: 5                # Maximum 5 items dans cette section

    - id: "partnerships_deals"
      title: "Partnerships & Deals"
      source_domains:
        - "tech_lai_ecosystem"
      max_items: 3
      filter_event_types:
        - "partnership"           # Ne garder que les événements de type "partnership"

# Configuration de la livraison de la newsletter.
newsletter_delivery:
  format: "markdown"            # Format de sortie : Markdown
  include_tldr: true            # Inclure un résumé exécutif (TL;DR)
  include_intro: true           # Inclure une introduction
  delivery_method: "s3"         # Méthode de livraison : stockage S3
  notification_email: "client@example.com"  # Email de notification
```

### Explications des blocs principaux

#### `client_profile`

Définit l'identité du client et les paramètres de base de la newsletter.

- **`client_id`** : identifiant unique (obligatoire, doit être unique dans le système)
- **`name`** : nom de la newsletter (obligatoire)
- **`language`** : langue de la newsletter (obligatoire, ex: "en", "fr")
- **`frequency`** : fréquence de génération (obligatoire, ex: "weekly", "monthly")
- **`tone`** et **`voice`** : paramètres optionnels pour guider le style de la newsletter

#### `watch_domains`

Définit les domaines de veille pour ce client. Chaque domaine correspond à un ensemble de scopes métier.

- **`id`** : identifiant unique du domaine (obligatoire)
- **`type`** : type de domaine (obligatoire, ex: "technology", "indication", "regulatory")
- **`technology_scope`**, **`company_scope`**, **`molecule_scope`** : références aux scopes canonical (obligatoires, doivent exister dans `canonical/scopes/*.yaml`)
- **`priority`** : priorité du domaine (obligatoire, ex: "high", "medium", "low")

**Où trouver les valeurs possibles ?** Dans la section "Inventaire des briques disponibles" de ce README, ou directement dans les fichiers `canonical/scopes/*.yaml`.

#### `source_config`

Définit les sources d'information à utiliser pour ce client.

- **`source_bouquets_enabled`** : liste des bouquets à activer (obligatoire, doit contenir au moins un bouquet)
- **`sources_extra_enabled`** : liste de sources supplémentaires à activer individuellement (optionnel, peut être vide)

**Où trouver les valeurs possibles ?** Dans la section "Bouquets de sources disponibles" de ce README, ou directement dans `canonical/sources/source_catalog.yaml`, section `bouquets:`.

#### `newsletter_layout`

Définit la structure de la newsletter finale (sections, nombre d'items, filtres).

- **`sections`** : liste des sections de la newsletter (obligatoire, doit contenir au moins une section)
  - **`id`** : identifiant unique de la section (obligatoire)
  - **`title`** : titre de la section (obligatoire)
  - **`source_domains`** : liste des domaines de veille à inclure dans cette section (obligatoire)
  - **`max_items`** : nombre maximum d'items dans cette section (obligatoire)
  - **`filter_event_types`** : liste des types d'événements à inclure (optionnel, si absent, tous les types sont inclus)

#### `newsletter_delivery`

Définit les paramètres de livraison de la newsletter.

- **`format`** : format de sortie (obligatoire, ex: "markdown", "html", "json")
- **`delivery_method`** : méthode de livraison (obligatoire, ex: "s3", "email")
- **`include_tldr`**, **`include_intro`** : options pour inclure un résumé exécutif et une introduction (optionnels, par défaut `false`)
- **`notification_email`** : email de notification (optionnel)

---

## Ressources complémentaires

- **Liste complète des scopes** : voir les fichiers dans `canonical/scopes/`
- **Liste complète des sources et bouquets** : voir `canonical/sources/source_catalog.yaml`
- **Règles de scoring** : voir `canonical/scoring/scoring_rules.yaml` et `canonical/scoring/scoring_examples.md`
- **Contrats des Lambdas** : voir `contracts/lambdas/vectora-inbox-ingest-normalize.md` et `contracts/lambdas/vectora-inbox-engine.md`
- **Documentation du répertoire canonical** : voir `canonical/README.md`

---

## Questions fréquentes

**Q : Puis-je créer mes propres scopes ?**

Oui, vous pouvez ajouter de nouvelles clés dans les fichiers `canonical/scopes/*.yaml`. Par exemple, pour créer un scope `lai_companies_addiction`, ajoutez une nouvelle entrée dans `canonical/scopes/company_scopes.yaml` avec la liste des entreprises concernées.

**Q : Puis-je créer mes propres bouquets ?**

Oui, vous pouvez ajouter de nouveaux bouquets dans `canonical/sources/source_catalog.yaml`, section `bouquets:`. Un bouquet est simplement une liste de `source_keys` existants.

**Q : Puis-je activer des sources individuelles sans passer par un bouquet ?**

Oui, utilisez le champ `sources_extra_enabled` dans `source_config`. Vous pouvez y lister des `source_keys` individuels (ex: `["press_corporate__novartis", "press_sector__nature_biotechnology"]`).

**Q : Comment savoir si mes clés de scopes sont valides ?**

Ouvrez les fichiers `canonical/scopes/*.yaml` et vérifiez que les clés que vous utilisez (ex: `lai_companies_global`) sont bien définies. Si une clé n'existe pas, la Lambda engine renverra une erreur.

**Q : Que se passe-t-il si j'active trop de sources ?**

L'ingestion prendra plus de temps et générera plus de données. Commencez par un bouquet MVP (ex: `lai_corporate_mvp`) pour tester, puis étendez progressivement.

**Q : Comment ajuster les règles de scoring ?**

Les règles de scoring sont définies dans `canonical/scoring/scoring_rules.yaml`. Vous pouvez ajuster les poids par type d'événement, priorité de domaine, etc. Consultez `canonical/scoring/scoring_examples.md` pour des exemples concrets.
