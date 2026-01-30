# Comment fonctionne l'ingestion d'un client dans Vectora Inbox

## Résumé exécutif

**Question centrale** : Comment on passe d'un `client_id` à une liste d'items normalisés dans S3 ?

**Réponse courte** :
1. Le client `lai_weekly` déclare des **bouquets de sources** dans sa config (`lai_corporate_mvp` + `lai_press_mvp`)
2. La Lambda `ingest-normalize` résout ces bouquets en **liste d'URLs concrètes** via `source_catalog.yaml`
3. La Lambda **scrappe ces URLs** (HTML pour corporate, RSS pour presse)
4. Elle **normalise** les contenus avec Bedrock en utilisant les **scopes canonical** comme référence
5. Elle écrit les **items normalisés** dans S3

---

## 1. Où est décrit un client ?

### Fichier principal
**`client-config-examples/lai_weekly.yaml`**

### Champs clés pour l'ingestion

```yaml
client_profile:
  client_id: "lai_weekly"        # Identifiant unique
  language: "en"                  # Langue pour Bedrock

watch_domains:                    # Domaines surveillés (utilisés APRÈS ingestion pour le matching)
  - id: "tech_lai_ecosystem"
    company_scope: "lai_companies_global"      # Clé dans canonical/scopes/company_scopes.yaml
    molecule_scope: "lai_molecules_global"     # Clé dans canonical/scopes/molecule_scopes.yaml
    technology_scope: "lai_keywords"           # Clé dans canonical/scopes/technology_scopes.yaml

source_config:                    # Sources à ingérer (utilisées PENDANT l'ingestion)
  source_bouquets_enabled:
    - "lai_press_mvp"             # Bouquet défini dans source_catalog.yaml
    - "lai_corporate_mvp"         # Bouquet défini dans source_catalog.yaml
```

### Ce qui est utilisé pour l'ingestion vs le matching

**PENDANT l'ingestion (Lambda ingest-normalize)** :
- `source_config.source_bouquets_enabled` → détermine QUELLES sources scrapper
- `client_profile.language` → guide Bedrock pour les résumés

**APRÈS l'ingestion (Lambda engine)** :
- `watch_domains` → détermine QUELS items sont pertinents pour le client
- Les scopes (`company_scope`, `molecule_scope`, etc.) → utilisés pour le matching et scoring

---

## 2. Comment les sources sont attachées au client

### Étape 1 : Client déclare des bouquets

Dans `lai_weekly.yaml` :
```yaml
source_config:
  source_bouquets_enabled:
    - "lai_press_mvp"
    - "lai_corporate_mvp"
```

### Étape 2 : Résolution des bouquets

La Lambda lit **`canonical/sources/source_catalog.yaml`** :

```yaml
bouquets:
  - bouquet_id: "lai_corporate_mvp"
    source_keys:
      - "press_corporate__medincell"
      - "press_corporate__camurus"
      - "press_corporate__delsitech"
      - "press_corporate__nanexa"
      - "press_corporate__peptron"

  - bouquet_id: "lai_press_mvp"
    source_keys:
      - "press_sector__fiercebiotech"
      - "press_sector__fiercepharma"
      - "press_sector__endpoints_news"
```

**Résultat** : 8 `source_key` à traiter (5 corporate + 3 presse)

### Étape 3 : Récupération des métadonnées de chaque source

Pour chaque `source_key`, la Lambda lit les métadonnées dans la section `sources:` de `source_catalog.yaml` :

#### Exemple corporate (HTML scraping)
```yaml
- source_key: "press_corporate__medincell"
  homepage_url: "https://www.medincell.com/"
  html_url: "https://www.medincell.com/news/"
  ingestion_mode: "html"
  enabled: true
```

**→ La Lambda va scrapper** : `https://www.medincell.com/news/`

#### Exemple presse (RSS scraping)
```yaml
- source_key: "press_sector__fiercepharma"
  homepage_url: "https://www.fiercepharma.com/"
  rss_url: "https://www.fiercepharma.com/rss/xml"
  ingestion_mode: "rss"
  enabled: true
```

**→ La Lambda va scrapper** : `https://www.fiercepharma.com/rss/xml`

---

## 3. URLs concrètes scrapées pour lai_weekly

### Sources corporate (ingestion_mode: html)
1. **MedinCell** : https://www.medincell.com/news/
2. **Camurus** : https://www.camurus.com/media/press-releases/
3. **DelSiTech** : https://www.delsitech.com/news/
4. **Nanexa** : https://www.nanexa.se/en/press/
5. **Peptron** : https://www.peptron.co.kr/eng/pr/news.php

### Sources presse (ingestion_mode: rss)
6. **FierceBiotech** : https://www.fiercebiotech.com/rss/xml
7. **FiercePharma** : https://www.fiercepharma.com/rss/xml
8. **Endpoints News** : https://endpts.com/feed/

---

## 4. Rôle des scopes canonical pour l'ingestion

### Les scopes sont utilisés PENDANT la normalisation (Phase 1B)

La Lambda charge les scopes depuis `canonical/scopes/` :
- `company_scopes.yaml` → liste des entreprises LAI
- `molecule_scopes.yaml` → liste des molécules LAI
- `technology_scopes.yaml` → mots-clés LAI
- `trademark_scopes.yaml` → marques commerciales LAI

### Comment la Lambda les utilise

1. **Envoi à Bedrock** : La Lambda envoie des extraits de ces listes à Bedrock dans le prompt de normalisation
   - "Voici des exemples d'entreprises LAI : MedinCell, Camurus, Alkermes..."
   - "Voici des exemples de molécules LAI : buprenorphine, paliperidone, risperidone..."

2. **Détection d'entités** : Bedrock utilise ces listes pour identifier les entités dans le texte

3. **Validation** : La Lambda peut valider que les entités détectées par Bedrock existent dans les scopes

### Exemple pour lai_weekly

Config client référence :
```yaml
watch_domains:
  - company_scope: "lai_companies_global"
    molecule_scope: "lai_molecules_global"
    technology_scope: "lai_keywords"
```

Lambda charge depuis `canonical/scopes/company_scopes.yaml` :
```yaml
lai_companies_global:
  - MedinCell
  - Camurus
  - Alkermes
  - Indivior
  # ... ~180 entreprises
```

**Important** : Les scopes servent à GUIDER la normalisation, pas à FILTRER les sources. Le filtrage se fait plus tard dans la Lambda engine.

---

## 5. Fichiers dont dépend la Lambda ingest-normalize

### Fichiers de configuration (lus depuis S3)

1. **`clients/lai_weekly.yaml`**
   - Détermine quels bouquets activer
   - Fournit la langue pour Bedrock

2. **`canonical/sources/source_catalog.yaml`**
   - Définit les bouquets (mapping bouquet_id → source_keys)
   - Définit les sources (mapping source_key → URLs + ingestion_mode)

3. **`canonical/scopes/company_scopes.yaml`**
   - Listes d'entreprises pour guider Bedrock

4. **`canonical/scopes/molecule_scopes.yaml`**
   - Listes de molécules pour guider Bedrock

5. **`canonical/scopes/technology_scopes.yaml`**
   - Mots-clés technologiques pour guider Bedrock

6. **`canonical/scopes/trademark_scopes.yaml`**
   - Marques commerciales pour guider Bedrock

7. **`canonical/scopes/exclusion_scopes.yaml`**
   - Mots-clés à exclure (filtrage du bruit)

### Code runtime (dans le package Lambda)

8. **`src/vectora_core/config/loader.py`**
   - Charge les configs depuis S3

9. **`src/vectora_core/config/resolver.py`**
   - Résout les bouquets en liste de sources

10. **`src/vectora_core/ingestion/fetcher.py`**
    - Effectue les requêtes HTTP vers les URLs

11. **`src/vectora_core/ingestion/parser.py`**
    - Parse le HTML/RSS en items bruts

12. **`src/vectora_core/normalization/normalizer.py`**
    - Appelle Bedrock pour normaliser les items

13. **`src/lambdas/ingest_normalize/handler.py`**
    - Point d'entrée Lambda

---

## 6. Schéma du flux d'ingestion

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. DÉCLENCHEMENT                                                │
│    Event Lambda: { "client_id": "lai_weekly" }                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. CHARGEMENT CONFIG                                            │
│    - Lit clients/lai_weekly.yaml depuis S3                      │
│    - Extrait: source_bouquets_enabled = ["lai_press_mvp",      │
│                                          "lai_corporate_mvp"]   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. RÉSOLUTION DES BOUQUETS                                      │
│    - Lit canonical/sources/source_catalog.yaml                  │
│    - Développe "lai_press_mvp" → 3 source_keys                  │
│    - Développe "lai_corporate_mvp" → 5 source_keys              │
│    - Total: 8 source_keys                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. RÉCUPÉRATION MÉTADONNÉES                                     │
│    Pour chaque source_key, lit dans source_catalog.yaml:       │
│    - ingestion_mode (rss ou html)                               │
│    - rss_url ou html_url                                        │
│    - enabled (true/false)                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. SCRAPING (Phase 1A)                                          │
│    Pour chaque source:                                          │
│    - Si ingestion_mode=rss → GET sur rss_url                    │
│    - Si ingestion_mode=html → GET sur html_url                  │
│    - Parse le contenu (XML/HTML)                                │
│    - Extrait: titre, description, URL, date                     │
│    → Résultat: liste d'items bruts                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. NORMALISATION (Phase 1B)                                     │
│    - Charge les scopes canonical (companies, molecules, etc.)   │
│    - Pour chaque item brut:                                     │
│      • Envoie à Bedrock avec prompt + scopes                    │
│      • Bedrock extrait: companies, molecules, technologies      │
│      • Bedrock génère: résumé, event_type                       │
│    → Résultat: liste d'items normalisés                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. ÉCRITURE S3                                                  │
│    Écrit dans: s3://vectora-inbox-data/                         │
│                normalized/lai_weekly/2025/01/15/items.json      │
│    Format: JSON array d'items normalisés                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Différence ingestion vs matching

### INGESTION (Lambda ingest-normalize)
- **Question** : "Quelles sources scrapper ?"
- **Réponse** : Déterminée par `source_config.source_bouquets_enabled`
- **Résultat** : Tous les items de toutes les sources activées sont ingérés et normalisés
- **Pas de filtrage métier** : On récupère TOUT ce qui est publié sur les sources

### MATCHING (Lambda engine)
- **Question** : "Quels items sont pertinents pour le client ?"
- **Réponse** : Déterminée par `watch_domains` + scopes canonical
- **Résultat** : Seuls les items matchant les domaines surveillés sont sélectionnés
- **Filtrage métier** : On ne garde que ce qui parle de LAI, des entreprises LAI, etc.

---

## 8. Exemple concret : lai_weekly

### Configuration
- **Bouquets activés** : `lai_press_mvp` + `lai_corporate_mvp`
- **Nombre de sources** : 8 (3 presse RSS + 5 corporate HTML)
- **Scopes utilisés** : `lai_companies_global`, `lai_molecules_global`, `lai_keywords`

### URLs scrapées
- 3 flux RSS (FierceBiotech, FiercePharma, Endpoints)
- 5 pages HTML corporate (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)

### Résultat typique
- **Items ingérés** : ~150 items bruts (tous les articles de la semaine)
- **Items normalisés** : ~145 items (quelques-uns filtrés par exclusions)
- **Items matchés** : ~30 items (seuls ceux parlant de LAI après matching dans engine)
- **Items dans newsletter** : ~8 items (top items après scoring)

---

## 9. Points clés à retenir

1. **Les bouquets simplifient la config** : Au lieu de lister 8 sources, on active 2 bouquets

2. **source_catalog.yaml est la source de vérité** : C'est là que sont définies toutes les URLs

3. **Les scopes guident Bedrock** : Ils ne filtrent pas l'ingestion, ils aident à la normalisation

4. **L'ingestion est exhaustive** : On récupère TOUT, le filtrage se fait après

5. **Deux modes d'ingestion** :
   - **RSS** : Pour la presse (flux XML structurés)
   - **HTML** : Pour les sites corporate (scraping de pages web)

6. **Dépendances claires** :
   - Client config → déclare les bouquets
   - Source catalog → définit les bouquets et les URLs
   - Scopes canonical → guident la normalisation
   - Code runtime → orchestre le tout

---

**Fichier créé le** : 2025-01-XX  
**Auteur** : Documentation générée pour Vectora Inbox MVP
