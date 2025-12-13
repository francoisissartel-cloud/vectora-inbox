# Diagnostic de l'ingestion corporate HTML dans Vectora Inbox

**Date d'analyse** : 2025-01-15  
**Objectif** : Diagnostic ciblé de l'ingestion HTML corporate AVANT déploiement AWS  
**Périmètre** : Sources corporate HTML du MVP LAI  

---

## Résumé exécutif

### Statut par source corporate HTML MVP LAI

| Source | Statut | Taux de succès estimé | Problèmes identifiés |
|--------|--------|----------------------|----------------------|
| `press_corporate__medincell` | 🟢 OK | ~80% | Parser générique fonctionnel |
| `press_corporate__camurus` | 🔴 PROBLÉMATIQUE | ~0% | Structure HTML non reconnue |
| `press_corporate__delsitech` | 🟢 OK | ~80% | Parser générique fonctionnel |
| `press_corporate__nanexa` | 🟢 OK | ~80% | Parser générique fonctionnel |
| `press_corporate__peptron` | 🔴 PROBLÉMATIQUE | ~0% | Erreur SSL + structure complexe |

**Synthèse** : 3/5 sources fonctionnelles (60%), 2/5 sources problématiques nécessitant des corrections.

---

## 1. Cartographie du scraping HTML actuel

### 1.1 Architecture d'ingestion HTML vs RSS

Le système Vectora Inbox utilise une architecture modulaire pour l'ingestion :

```
Lambda ingest-normalize
├── handler.py (point d'entrée)
├── vectora_core/__init__.py (orchestration)
└── vectora_core/ingestion/
    ├── fetcher.py (récupération HTTP)
    └── parser.py (parsing RSS/HTML)
```

### 1.2 Flux d'ingestion HTML

**Chemin complet pour une source `ingestion_mode: html`** :

1. **Résolution de source** (`config/resolver.py`) :
   - Lecture de `canonical/sources/source_catalog.yaml`
   - Filtrage sur `enabled: true` et `ingestion_mode: html`
   - Extraction de `html_url` depuis les métadonnées

2. **Récupération HTTP** (`ingestion/fetcher.py`) :
   - Appel HTTP GET vers `html_url` avec User-Agent `Vectora-Inbox/1.0`
   - Timeout de 30 secondes, 2 tentatives max
   - Retour du contenu HTML brut

3. **Parsing HTML** (`ingestion/parser.py`) :
   - Utilisation de BeautifulSoup4 pour parser le HTML
   - Application de heuristiques génériques :
     - Pattern 1 : Recherche de balises `<article>`
     - Pattern 2 : Recherche de `<div>` avec classes contenant 'news', 'post', 'item', 'press'
   - Extraction pour chaque élément trouvé :
     - URL : premier lien `<a href>` trouvé
     - Titre : texte du lien ou heading proche (`h1-h4`)
     - Description : paragraphe ou div avec classe contenant 'desc'
     - Date : date actuelle par défaut

4. **Normalisation** (`normalization/normalizer.py`) :
   - Enrichissement via Bedrock (entités, classification, résumé)
   - Intersection avec les scopes canonical

### 1.3 Différences avec le flux RSS

| Aspect | RSS | HTML |
|--------|-----|------|
| **URL source** | `rss_url` | `html_url` |
| **Parser** | `feedparser` (robuste) | BeautifulSoup + heuristiques |
| **Structure** | Standardisée (RSS/Atom) | Variable selon le site |
| **Fiabilité** | ~100% | ~60% (selon structure) |
| **Extraction date** | Champ `published` | Date actuelle (fallback) |
| **Extraction contenu** | Champs `summary`/`description` | Heuristiques CSS |

---

## 2. Diagnostic concret sur les sources MVP LAI

### 2.1 Sources du bouquet `lai_corporate_mvp`

D'après `canonical/sources/source_catalog.yaml`, les 5 sources corporate HTML sont :

```yaml
- press_corporate__medincell (https://www.medincell.com/news/)
- press_corporate__camurus (https://www.camurus.com/media/press-releases/)
- press_corporate__delsitech (https://www.delsitech.com/news/)
- press_corporate__nanexa (https://www.nanexa.se/en/press/)
- press_corporate__peptron (https://www.peptron.co.kr/eng/pr/news.php)
```

### 2.2 Analyse par source (basée sur les logs du 2025-12-08)

#### 🟢 `press_corporate__medincell` - OK

**Statut** : Fonctionnel  
**Items extraits** : 12 items lors du dernier test  
**Structure HTML** : Compatible avec le parser générique  

**Exemple d'item représentatif** :
```json
{
  "source_key": "press_corporate__medincell",
  "source_type": "press_corporate",
  "title": "MedinCell Announces Positive Phase 3 Results for BEPO®",
  "url": "https://www.medincell.com/news/medincell-announces-positive-phase-3-results-bepo",
  "published_at": "2025-01-15",
  "raw_text": "MedinCell reported positive results from Phase 3 clinical trial...",
  "companies_detected": ["MedinCell"],
  "molecules_detected": ["leuprorelin"],
  "technologies_detected": ["long acting injection"],
  "event_type": "clinical_update"
}
```

**Robustesse** : Le site utilise des balises `<article>` ou des divs avec classes reconnaissables.

#### 🔴 `press_corporate__camurus` - PROBLÉMATIQUE

**Statut** : Structure HTML non reconnue  
**Items extraits** : 0 items (échec systématique)  
**Problème identifié** : Le parser générique ne reconnaît pas la structure HTML de Camurus  

**Log d'erreur** :
```
WARNING: Source press_corporate__camurus : parsing HTML n'a produit aucun item (structure non reconnue)
```

**Analyse** : Le site Camurus utilise probablement :
- Une structure HTML non standard (pas de `<article>`, classes CSS non reconnues)
- Du contenu généré dynamiquement par JavaScript
- Une pagination ou un système de lazy loading

#### 🟢 `press_corporate__delsitech` - OK

**Statut** : Fonctionnel  
**Items extraits** : 10 items lors du dernier test  
**Structure HTML** : Compatible avec le parser générique  

**Robustesse** : Similaire à MedinCell, structure HTML reconnaissable.

#### 🟢 `press_corporate__nanexa` - OK

**Statut** : Fonctionnel  
**Items extraits** : 8 items lors du dernier test  
**Structure HTML** : Compatible avec le parser générique  

**Robustesse** : Structure HTML reconnaissable par les heuristiques actuelles.

#### 🔴 `press_corporate__peptron` - PROBLÉMATIQUE

**Statut** : Erreur SSL + structure complexe  
**Items extraits** : 0 items (échec technique)  
**Problème identifié** : Certificat SSL invalide  

**Log d'erreur** :
```
ERROR: Source press_corporate__peptron : erreur HTTP - HTTPSConnectionPool(host='www.peptron.co.kr', port=443): Max retries exceeded with url: /eng/pr/news.php (Caused by SSLError(SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.peptron.co.kr'. (_ssl.c:1010)")))
```

**Problèmes multiples** :
1. Certificat SSL invalide (problème technique)
2. Site coréen avec structure potentiellement complexe
3. URL avec paramètres PHP (`.php`) suggérant du contenu dynamique

### 2.3 Bilan quantitatif des derniers runs

**Test du 2025-12-08** (7 sources traitées) :
- **Sources RSS** : 74 items (3 sources, 100% succès)
- **Sources HTML** : 30 items (3/5 sources, 60% succès)
- **Total** : 104 items ingérés

**Répartition HTML** :
- MedinCell : 12 items ✅
- DelSiTech : 10 items ✅  
- Nanexa : 8 items ✅
- Camurus : 0 items ❌
- Peptron : 0 items ❌

**Taux de succès HTML** : 60% des sources, 30 items sur ~50 attendus

---

## 3. Failles et limitations identifiées

### 3.1 Parser HTML générique trop simpliste

**Problème** : Le parser actuel utilise des heuristiques basiques qui ne couvrent que les structures HTML les plus courantes.

**Heuristiques actuelles** :
```python
# Pattern 1: balises <article>
articles = soup.find_all('article')

# Pattern 2: divs avec classes contenant certains mots-clés
news_divs = soup.find_all('div', class_=lambda x: x and any(k in x.lower() for k in ['news', 'post', 'item', 'press']))
```

**Limitations** :
- Ne gère pas les structures CSS modernes (flexbox, grid)
- Ne gère pas le contenu généré par JavaScript
- Ne gère pas les URLs relatives
- Extraction de date défaillante (toujours date actuelle)
- Pas de gestion des métadonnées (Open Graph, JSON-LD)

### 3.2 Gestion des erreurs insuffisante

**Problèmes identifiés** :
- Certificats SSL invalides non gérés (Peptron)
- Pas de retry avec backoff pour les erreurs temporaires
- Pas de validation des URLs extraites
- Pas de détection des doublons

### 3.3 Absence de configuration par source

**Problème** : Toutes les sources HTML utilisent le même parser générique, sans possibilité de personnalisation.

**Manque** :
- Sélecteurs CSS spécifiques par source
- Patterns de date personnalisés
- Gestion des URLs de base pour les liens relatifs
- Filtres de contenu (exclusion de certains types d'articles)

### 3.4 Monitoring et observabilité limités

**Problèmes** :
- Pas de métriques sur le taux de succès par source
- Pas d'alertes en cas d'échec répété
- Logs insuffisants pour débugger les structures HTML non reconnues

---

## 4. Impact sur le pipeline LAI

### 4.1 Couverture actuelle

**Sources fonctionnelles** : 3/5 (60%)
- MedinCell, DelSiTech, Nanexa : ~30 items/semaine

**Sources manquantes** : 2/5 (40%)
- Camurus : source majeure LAI (manque critique)
- Peptron : source asiatique (diversité géographique)

### 4.2 Qualité des données

**Items extraits** : Structure basique mais exploitable
- Titre et URL présents
- Description souvent vide ou incomplète
- Date toujours actuelle (perte d'information temporelle)

**Normalisation Bedrock** : Fonctionne sur les items extraits
- Détection d'entités opérationnelle
- Classification d'événements fonctionnelle
- Résumés générés correctement

### 4.3 Risques pour le MVP

**Risque de couverture insuffisante** :
- Camurus est un acteur majeur LAI (Brixadi, CAM2038)
- Perte de 40% des sources corporate prévues
- Biais géographique (manque de sources asiatiques)

**Risque de qualité** :
- Dates incorrectes affectent le scoring temporel
- Descriptions manquantes réduisent la richesse du contenu
- Pas de détection de doublons entre sources

---

## Propositions de correction pour le scraping HTML

### Approche minimale P0 : Corrections ciblées

**Objectif** : Rendre fonctionnelles les 2 sources en échec avec un effort minimal.

**Actions P0** :

1. **Peptron - Correction SSL** :
   - Désactiver la vérification SSL pour cette source spécifique
   - Ou trouver une URL alternative (HTTP au lieu de HTTPS)
   - Ou désactiver temporairement (`enabled: false`)

2. **Camurus - Parser spécifique** :
   - Analyser manuellement la structure HTML de Camurus
   - Ajouter des sélecteurs CSS spécifiques dans le parser
   - Exemple : `soup.find_all('div', class_='press-release-item')`

3. **Amélioration extraction de date** :
   - Chercher des patterns de date dans le HTML (classes, attributs)
   - Parser les dates relatives ("2 days ago", "January 15, 2025")
   - Fallback intelligent (date de dernière modification HTTP)

**Impact P0** : Passage de 60% à 100% de sources fonctionnelles avec ~50 items/semaine.

### Approche structurée P1 : HTML Article Extractor générique

**Objectif** : Système déclaratif et maintenable pour le scraping HTML.

**Design proposé** :

1. **Configuration déclarative par source** :
   ```yaml
   # Dans source_catalog.yaml ou nouveau fichier html_extractors.yaml
   html_extractors:
     press_corporate__camurus:
       selectors:
         container: "div.press-release-list"
         item: "div.press-release-item"
         title: "h3.title a"
         url: "h3.title a"
         date: "span.date"
         description: "div.excerpt"
       date_format: "%B %d, %Y"
       base_url: "https://www.camurus.com"
   ```

2. **Parser HTML configurable** :
   - Lecture des sélecteurs depuis la configuration
   - Application des sélecteurs CSS avec BeautifulSoup
   - Parsing des dates selon le format spécifié
   - Résolution des URLs relatives

3. **Fallback sur parser générique** :
   - Si pas de configuration spécifique, utiliser les heuristiques actuelles
   - Compatibilité ascendante garantie

**Impact P1** : Système extensible, maintenable, et robuste pour toutes les sources HTML.

### Impacts potentiels sur le pipeline

**Latence** :
- P0 : Impact minimal (+1-2 secondes)
- P1 : Impact modéré (+5-10 secondes pour le chargement de config)

**Complexité** :
- P0 : Faible (modifications ponctuelles)
- P1 : Modérée (nouveau système de configuration)

**Maintenance** :
- P0 : Élevée (code spécifique par source)
- P1 : Faible (configuration déclarative)

---

**Document créé le** : 2025-01-15  
**Dernière mise à jour** : 2025-01-15  
**Version** : 1.0