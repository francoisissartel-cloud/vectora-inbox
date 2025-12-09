# Plan correctif – Sources MVP LAI

## Phase 0 – Objectif du correctif

### Problème actuel

Actuellement, lors de l'exécution de la Lambda `vectora-inbox-ingest-normalize-dev`, nous observons `items_ingested = 0`. Cela signifie qu'aucun contenu n'est récupéré depuis les sources externes.

**Causes identifiées :**

1. **URLs manquantes ou invalides** : De nombreuses sources dans `source_catalog.yaml` ont des URLs vides (`url: ""`) ou pointent vers des pages d'accueil génériques plutôt que vers des flux RSS ou des pages de news structurées.

2. **Absence de distinction entre sources techniques** : Le catalogue ne distingue pas clairement entre :
   - Sources avec flux RSS disponibles (ingestion facile)
   - Sources HTML nécessitant un parsing spécifique (ingestion plus complexe)
   - Sources API nécessitant une intégration dédiée
   - Sources non encore intégrées techniquement (placeholders)

3. **Confusion entre univers métier et intégration technique** :
   - **Univers métier exhaustif** : nous voulons lister TOUTES les entreprises LAI pertinentes dans les scopes canonical, même si nous ne pouvons pas encore ingérer leurs contenus automatiquement.
   - **Intégration technique progressive** : seules certaines sources sont réellement ingérables aujourd'hui (celles avec RSS ou HTML structuré).

### Solution proposée

Introduire de nouveaux champs dans `source_catalog.yaml` pour distinguer clairement :

- **`ingestion_mode`** : indique le type d'ingestion (`rss`, `html`, `api`, `none`)
- **`enabled`** : indique si la source est activée pour l'ingestion automatique (`true` / `false`)
- **`homepage_url`** : URL de la page d'accueil de l'entreprise (référence)
- **`rss_url`** : URL du flux RSS (si disponible)
- **`html_url`** : URL de la page de news HTML (si disponible)

Créer deux types de bouquets :

- **Bouquets `_universe`** : listes exhaustives de toutes les sources pertinentes (enabled ou non)
- **Bouquets `_mvp`** : sous-ensembles de sources réellement intégrées et activées

---

## Phase 1 – Nouveau modèle de source_catalog.yaml

### Structure attendue pour chaque source

```yaml
sources:
  press_corporate__camurus:
    company_id: "camurus"
    homepage_url: "https://www.camurus.com/"
    rss_url: ""                                              # vide si pas de flux RSS
    html_url: "https://www.camurus.com/media/press-releases"
    ingestion_mode: "html"                                   # "rss" | "html" | "api" | "none"
    enabled: true                                            # true = utilisée par le pipeline
    tags: ["LAI", "corporate"]
    notes: "Source corporate Camurus (Suède). Ingestion HTML sur page press releases."
```

### Explication des champs

**`ingestion_mode`** : Type d'ingestion technique

- `"rss"` : La source dispose d'un flux RSS/Atom → parser RSS (feedparser)
- `"html"` : La source dispose d'une page HTML de news → parser HTML (BeautifulSoup ou équivalent)
- `"api"` : La source nécessite une intégration API spécifique (ex: PubMed, ClinicalTrials.gov)
- `"none"` : La source n'est pas encore intégrée techniquement (placeholder)

**`enabled`** : Activation pour l'ingestion automatique

- `true` : La source est utilisée par le pipeline d'ingestion
- `false` : La source est dans l'univers métier mais ignorée par l'ingestion automatique (pas encore prête, ou désactivée temporairement)

**`homepage_url`** : URL de référence de l'entreprise (toujours renseignée)

**`rss_url`** : URL du flux RSS (si disponible, sinon vide `""`)

**`html_url`** : URL de la page de news HTML (si disponible, sinon vide `""`)

### Règles de cohérence

- Si `ingestion_mode == "rss"` → `rss_url` doit être renseignée
- Si `ingestion_mode == "html"` → `html_url` doit être renseignée
- Si `ingestion_mode == "none"` → `enabled` doit être `false`
- Si `enabled == false` → la source est ignorée par le pipeline (peu importe le mode)

---

## Phase 2 – Bouquets _universe vs _mvp

### Définition des 4 bouquets LAI

**1. `lai_corporate_universe`**

- **Contenu** : TOUTES les sources corporate LAI (environ 180 entreprises)
- **Critère** : `source_type == "press_corporate"` ET `tags` contient `"LAI"`
- **Statut** : `enabled: true` OU `enabled: false` (exhaustif)
- **Usage** : Photographie complète du périmètre LAI, documentation, planification

**2. `lai_press_universe`**

- **Contenu** : TOUTES les sources de presse pertinentes pour LAI/biotech/pharma
- **Critère** : `source_type == "press_sector"` ET `tags` contient `"pharma-biotech"`
- **Statut** : `enabled: true` OU `enabled: false`
- **Usage** : Vue exhaustive des sources de presse disponibles

**3. `lai_corporate_mvp`**

- **Contenu** : Sous-ensemble de sources corporate LAI pilotes avec `enabled: true`
- **Critère** : `source_type == "press_corporate"` ET `tags` contient `"LAI"` ET `enabled == true` ET `ingestion_mode != "none"`
- **Sources minimales** :
  - MedinCell (France)
  - Camurus (Suède)
  - DelSiTech (Finlande)
  - Nanexa (Suède)
  - Peptron (Corée du Sud)
- **Usage** : Ingestion automatique pour le MVP

**4. `lai_press_mvp`**

- **Contenu** : Sous-ensemble de sources presse intégrées pour le MVP
- **Critère** : `source_type == "press_sector"` ET `enabled == true` ET `ingestion_mode == "rss"`
- **Sources minimales** :
  - FierceBiotech
  - FiercePharma
  - Endpoints News
- **Usage** : Ingestion automatique pour le MVP

### Principe clé

- **`_universe`** = vision exhaustive du périmètre métier (documentation, planification)
- **`_mvp`** = sous-ensemble techniquement intégré et activé (ingestion automatique)

Les bouquets `_universe` servent à documenter l'ambition complète, les bouquets `_mvp` servent à l'exécution concrète.

---

## Phase 3 – Évolution de config.resolver

### Objectif

Faire en sorte que `resolve_sources_for_client()` filtre automatiquement les sources selon le champ `enabled`.

### Modifications dans `src/vectora_core/config/resolver.py`

**Fonction `resolve_sources_for_client()`** :

1. **Charger les bouquets activés** depuis la config client
2. **Développer chaque bouquet** en liste de `source_key`
3. **Récupérer les métadonnées** de chaque source depuis le catalogue
4. **Filtrer sur `enabled: true`** :
   - Si `enabled == false` → logger un avertissement et ignorer la source
   - Si `enabled == true` → inclure la source dans la liste finale
5. **Gérer les sources sans `ingestion_mode`** :
   - Si le champ `ingestion_mode` est absent → considérer comme `"none"` + log warning
6. **Retourner la liste filtrée** de sources activées

**Logs attendus** :

```
INFO: Résolution des sources pour le client 'lai_weekly'
INFO: Bouquet 'lai_corporate_mvp' résolu : 5 sources
INFO: Bouquet 'lai_press_mvp' résolu : 3 sources
INFO: Total de sources uniques après résolution : 8
INFO: Filtrage sur enabled=true : 8 sources activées, 0 sources ignorées
INFO: Sources résolues avec métadonnées : 8
```

**Exemple de log pour source désactivée** :

```
WARNING: Source 'press_corporate__novartis' est désactivée (enabled=false), ignorée
```

---

## Phase 4 – Évolution de ingestion.fetcher / ingestion.parser

### Objectif

Adapter le fetcher et le parser pour gérer les modes `rss` et `html`.

### Modifications dans `src/vectora_core/ingestion/fetcher.py`

**Fonction `fetch_source(source_meta: dict)`** :

1. **Lire le champ `ingestion_mode`** depuis `source_meta`
2. **Brancher selon le mode** :
   - Si `ingestion_mode == "rss"` :
     - Utiliser `rss_url` (ou fallback sur `url` si `rss_url` est vide)
     - Effectuer un GET HTTP
     - Retourner le contenu brut (XML)
   - Si `ingestion_mode == "html"` :
     - Utiliser `html_url` (ou fallback sur `homepage_url` si `html_url` est vide)
     - Effectuer un GET HTTP
     - Retourner le contenu brut (HTML)
   - Si `ingestion_mode == "none"` ou absent :
     - Logger un warning
     - Retourner `None` (pas d'ingestion)
3. **Gérer les erreurs HTTP** (timeout, 404, 500) :
   - Logger l'erreur avec détails (URL, code HTTP, message)
   - Retourner `None`
   - Continuer avec les autres sources (ne pas bloquer tout le pipeline)

**Logs attendus** :

```
INFO: Récupération de press_corporate__camurus depuis https://www.camurus.com/media/press-releases
INFO: Source press_corporate__camurus : 15234 caractères récupérés
WARNING: Source press_corporate__novartis : ingestion_mode='none', skip
```

### Modifications dans `src/vectora_core/ingestion/parser.py`

**Fonction `parse_source_content(raw_content: str, source_meta: dict)`** :

1. **Lire le champ `ingestion_mode`** depuis `source_meta`
2. **Brancher selon le mode** :
   - Si `ingestion_mode == "rss"` :
     - Utiliser `feedparser.parse(raw_content)`
     - Extraire les items (titre, URL, date, description)
     - Retourner la liste d'items bruts
   - Si `ingestion_mode == "html"` :
     - Utiliser BeautifulSoup ou un parser HTML simple
     - Chercher des patterns de news (ex: `<article>`, `<h2><a>`, etc.)
     - Extraire titre, URL, date (si possible), snippet
     - Retourner la liste d'items bruts
     - **Si aucun item trouvé** : logger un warning et retourner liste vide (ne pas planter)
3. **Gérer les erreurs de parsing** :
   - Logger l'erreur avec détails
   - Retourner liste vide
   - Continuer avec les autres sources

**Principe KISS pour le parsing HTML** :

- Ne pas chercher à gérer tous les cas possibles
- Implémenter un parser générique simple (chercher des liens dans des balises `<article>`, `<div class="news">`, etc.)
- Si la structure HTML est trop exotique → retourner 0 items plutôt que planter
- Logger clairement quand une source HTML ne produit aucun item

**Logs attendus** :

```
INFO: Parsing du contenu de press_corporate__camurus (type: press_corporate)
INFO: Source press_corporate__camurus : 12 items parsés
WARNING: Source press_corporate__delsitech : parsing HTML n'a produit aucun item (structure HTML non reconnue)
```

### Limitations documentées

- Le parsing HTML est générique et peut ne pas fonctionner sur toutes les structures
- Si une source HTML ne produit aucun item, c'est normal (structure non reconnue)
- Il faudra potentiellement ajouter des parsers spécifiques par source dans une version ultérieure
- Pour le MVP, on accepte un taux de succès partiel (50-70% des sources HTML)

---

## Phase 5 – Mise à jour du client lai_weekly

### Objectif

Adapter `client-config-examples/lai_weekly.yaml` pour utiliser les nouveaux bouquets `_mvp`.

### Modifications dans `lai_weekly.yaml`

**Section `source_config`** :

```yaml
source_config:
  source_bouquets_enabled:
    - "lai_press_mvp"        # Sources presse intégrées (FierceBiotech, FiercePharma, Endpoints)
    - "lai_corporate_mvp"    # Sources corporate LAI pilotes (MedinCell, Camurus, DelSiTech, Nanexa, Peptron)
  
  sources_extra_enabled: []  # Aucune source additionnelle pour le MVP
```

**Vérification des scopes** :

- `watch_domains` doit toujours référencer `lai_companies_global`, `lai_molecules_global`, `lai_keywords`
- Ces scopes sont cohérents avec les entreprises présentes dans `lai_corporate_mvp`

**Commentaires à ajouter** :

```yaml
# Bouquets activés pour le MVP LAI :
# - lai_press_mvp : 3 sources de presse sectorielle avec flux RSS
# - lai_corporate_mvp : 5 sources corporate LAI avec ingestion HTML
# Total : environ 8 sources activées pour l'ingestion automatique
```

---

## Phase 6 – Test de la Lambda ingest-normalize

### Objectif

Valider que le pipeline d'ingestion fonctionne avec les nouvelles sources et produit `items_ingested > 0`.

### Étapes de test

**1. Re-déploiement (si nécessaire)**

Si le code des Lambdas a été modifié (resolver, fetcher, parser), re-packager et re-déployer :

```powershell
# Re-packager la Lambda ingest-normalize
$BUILD_DIR = "build/ingest-normalize"
Remove-Item -Recurse -Force $BUILD_DIR -ErrorAction SilentlyContinue
mkdir $BUILD_DIR
Copy-Item src/lambdas/ingest_normalize/handler.py $BUILD_DIR/handler.py
Copy-Item -Recurse src/vectora_core $BUILD_DIR/vectora_core
pip install -r requirements.txt -t $BUILD_DIR --upgrade
Compress-Archive -Path $BUILD_DIR/* -DestinationPath build/ingest-normalize.zip -Force

# Upload vers S3
aws s3 cp build/ingest-normalize.zip s3://vectora-inbox-lambda-code-dev/lambda/ingest-normalize/latest.zip `
  --profile rag-lai-prod `
  --region eu-west-3

# Mettre à jour la Lambda
aws lambda update-function-code `
  --function-name vectora-inbox-ingest-normalize-dev `
  --s3-bucket vectora-inbox-lambda-code-dev `
  --s3-key lambda/ingest-normalize/latest.zip `
  --profile rag-lai-prod `
  --region eu-west-3
```

**2. Invocation de la Lambda**

```powershell
# Créer le payload JSON
$payload = @{
  client_id = "lai_weekly"
  period_days = 7
} | ConvertTo-Json

# Invoquer la Lambda
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload $payload `
  --cli-binary-format raw-in-base64-out `
  response.json `
  --profile rag-lai-prod `
  --region eu-west-3

# Lire la réponse
Get-Content response.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**3. Résultats attendus**

**Succès minimal** :

```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly",
    "execution_date": "2025-01-15T10:30:00Z",
    "sources_processed": 8,
    "items_ingested": 45,
    "items_normalized": 45,
    "s3_output_path": "s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/01/15/items.json",
    "execution_time_seconds": 87.3
  }
}
```

**Critères de succès** :

- `items_ingested > 0` (au moins quelques items récupérés)
- `sources_processed >= 3` (au moins quelques sources ont fonctionné)
- Pas d'erreur critique (statusCode 200)

**Si `items_ingested == 0`** :

- Vérifier les logs CloudWatch pour identifier les sources en échec
- Vérifier que les URLs RSS/HTML sont correctes
- Vérifier que les parsers fonctionnent (logs de parsing)

**4. Consultation des logs CloudWatch**

```powershell
# Récupérer les derniers logs
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev `
  --follow `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Logs attendus** :

```
INFO: Démarrage de l'ingestion + normalisation pour le client : lai_weekly
INFO: Chargement des configurations depuis S3
INFO: Résolution des sources à traiter
INFO: Nombre de sources à traiter : 8
INFO: Phase 1A : Ingestion des sources
INFO: Récupération de press_sector__fiercebiotech depuis https://www.fiercebiotech.com/rss
INFO: Source press_sector__fiercebiotech : 12 items récupérés
INFO: Récupération de press_corporate__camurus depuis https://www.camurus.com/media/press-releases
INFO: Source press_corporate__camurus : 5 items récupérés
...
INFO: Total items bruts récupérés : 45
INFO: Phase 1B : Normalisation des items avec Bedrock
INFO: Total items normalisés : 45
INFO: Écriture des items normalisés dans s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/01/15/items.json
INFO: Ingestion + normalisation terminée
```

**5. Vérification des fichiers S3**

```powershell
# Lister les fichiers normalisés
aws s3 ls s3://vectora-inbox-data-dev/normalized/lai_weekly/ --recursive `
  --profile rag-lai-prod `
  --region eu-west-3

# Télécharger le fichier d'items normalisés
aws s3 cp s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/01/15/items.json items.json `
  --profile rag-lai-prod `
  --region eu-west-3

# Inspecter le contenu
Get-Content items.json | ConvertFrom-Json | Select-Object -First 3 | ConvertTo-Json -Depth 10
```

**Structure attendue d'un item normalisé** :

```json
{
  "source_key": "press_corporate__camurus",
  "source_type": "press_corporate",
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "summary": "Camurus a annoncé des résultats positifs pour son essai de Phase 3...",
  "url": "https://www.camurus.com/news/2025/01/phase-3-results",
  "date": "2025-01-10",
  "companies_detected": ["Camurus"],
  "molecules_detected": ["Brixadi", "buprenorphine"],
  "technologies_detected": ["long acting", "depot"],
  "indications_detected": ["opioid use disorder"],
  "event_type": "clinical_update"
}
```

### Interprétation des résultats

**Scénario 1 : `items_ingested > 0`** ✅

- Le pipeline fonctionne
- Au moins quelques sources produisent des items
- Passer à la Phase 7 (test de la Lambda engine)

**Scénario 2 : `items_ingested == 0`** ⚠️

- Aucune source n'a produit d'items
- Causes possibles :
  - URLs RSS/HTML incorrectes ou vides
  - Parsers ne reconnaissent pas les structures
  - Erreurs HTTP (timeouts, 404)
- Actions :
  - Consulter les logs CloudWatch pour identifier les sources en échec
  - Vérifier manuellement les URLs dans un navigateur
  - Ajuster les URLs ou les parsers si nécessaire

**Scénario 3 : Erreur critique (statusCode 500)** ❌

- Le pipeline a planté
- Causes possibles :
  - Erreur de code (bug dans resolver, fetcher, parser)
  - Configuration invalide (clés de scopes manquantes)
  - Problème d'accès S3 ou Bedrock
- Actions :
  - Consulter les logs CloudWatch pour identifier l'erreur
  - Corriger le code ou la configuration
  - Re-déployer et re-tester

---

## Phase 7 – Limitations et TODOs

### Limitations connues du MVP

**1. URLs RSS/HTML à compléter manuellement**

- Certaines sources dans `lai_corporate_universe` n'ont pas encore d'URLs RSS ou HTML valides
- Ces sources resteront avec `enabled: false` jusqu'à ce que les URLs soient trouvées
- **Action utilisateur** : rechercher manuellement les flux RSS ou pages de news pour ces sources

**2. Parsing HTML générique**

- Le parser HTML est simple et peut ne pas fonctionner sur toutes les structures
- Taux de succès attendu : 50-70% des sources HTML
- **Action future** : ajouter des parsers spécifiques par source si nécessaire

**3. Scopes d'indications non remplis**

- `addiction_keywords`, `psychiatry_keywords` sont vides
- Les domaines de veille spécifiques (addiction, psychiatrie) ne peuvent pas encore être utilisés
- **Action future** : remplir ces scopes pour permettre des newsletters ciblées

**4. APIs scientifiques/réglementaires non activées**

- PubMed, ClinicalTrials.gov, FDA labels sont définis mais pas encore utilisés
- **Action future** : activer ces sources dans une version ultérieure

### TODOs pour amélioration continue

**Court terme** :

- [ ] Compléter les URLs RSS/HTML pour les sources prioritaires (top 20 entreprises LAI)
- [ ] Tester le parsing HTML sur un échantillon de sources et ajuster si nécessaire
- [ ] Monitorer les coûts Bedrock et optimiser les prompts si nécessaire

**Moyen terme** :

- [ ] Remplir les scopes d'indications (addiction, psychiatrie)
- [ ] Activer les APIs scientifiques/réglementaires (PubMed, ClinicalTrials.gov)
- [ ] Ajouter des parsers HTML spécifiques pour les sources complexes

**Long terme** :

- [ ] Implémenter la détection de doublons (même article depuis plusieurs sources)
- [ ] Ajouter un système de cache pour éviter de re-fetcher les mêmes contenus
- [ ] Implémenter un système de retry avec backoff exponentiel pour les sources lentes

---

## Résumé exécutif

### Ce qui a été fait

1. **Nouveau modèle de `source_catalog.yaml`** avec champs `ingestion_mode`, `enabled`, `homepage_url`, `rss_url`, `html_url`
2. **Création de bouquets `_universe` et `_mvp`** pour distinguer périmètre métier et intégration technique
3. **Évolution de `config.resolver`** pour filtrer sur `enabled: true`
4. **Évolution de `ingestion.fetcher` et `ingestion.parser`** pour gérer les modes `rss` et `html`
5. **Mise à jour de `lai_weekly.yaml`** pour utiliser les bouquets `_mvp`
6. **Plan de test complet** avec commandes CLI et critères de succès

### Résultat attendu

- `items_ingested > 0` lors de l'invocation de la Lambda `vectora-inbox-ingest-normalize-dev`
- Au moins 3-5 sources produisent des items (presse RSS + quelques sources corporate HTML)
- Le pipeline est robuste aux sources en échec (continue avec les autres sources)
- Les logs sont clairs et permettent de diagnostiquer les problèmes

### Prochaines étapes après succès

1. Tester la Lambda `vectora-inbox-engine-dev` pour générer la première newsletter
2. Valider la qualité des résumés et du matching
3. Itérer sur les configurations (scopes, scoring, prompts) si nécessaire
4. Élargir progressivement le nombre de sources activées
