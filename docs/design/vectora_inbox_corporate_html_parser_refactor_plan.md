# Plan de refactoring du parser HTML corporate - Vectora Inbox

**Date de création** : 2025-01-15  
**Objectif** : Refactoring durable du parser HTML corporate avec approche générique + exceptions  
**Périmètre** : Amélioration de l'ingestion HTML sans déploiement AWS  

---

## Vue d'ensemble de la stratégie

### Approche retenue

**Parser générique robustifié** : Utilisé par défaut pour toutes les sources `ingestion_mode: html`
- Heuristiques améliorées pour détecter les cartes d'article
- Extraction robuste des titres, URLs, dates, descriptions
- Gestion des patterns de dates génériques

**Extracteurs spécifiques** : Exception réservée aux sites critiques
- Configuration déclarative dans `canonical/sources/html_extractors.yaml`
- Utilisés uniquement pour Camurus et Peptron (sources problématiques identifiées)
- Fallback automatique sur le parser générique

**Métrologie d'ingestion** : Mesure de performance par source
- Nombre d'items extraits, dates trouvées, erreurs
- Diagnostic automatique des sources problématiques
- Rapports dans `docs/diagnostics/`

---

## 1. Architecture actuelle de parsing HTML

### 1.1 Flux d'ingestion HTML existant

```
Lambda ingest-normalize
├── handler.py (point d'entrée)
├── vectora_core/__init__.py (orchestration)
└── vectora_core/ingestion/
    ├── fetcher.py (récupération HTTP)
    └── parser.py (parsing RSS/HTML)
```

**Processus actuel** :
1. `fetcher.py` : Récupération HTTP avec User-Agent `Vectora-Inbox/1.0`
2. `parser.py` : Parsing avec BeautifulSoup4 et heuristiques basiques
3. Intégration avec profils d'ingestion (`ingestion_profiles.yaml`)
4. Normalisation Bedrock (entités, classification, résumé)

### 1.2 Limitations identifiées

**Parser générique trop simpliste** :
- Heuristiques limitées : `<article>` et divs avec classes contenant 'news'
- Extraction de date défaillante (toujours date actuelle)
- Pas de gestion des URLs relatives
- Pas de détection des métadonnées (Open Graph, JSON-LD)

**Gestion d'erreurs insuffisante** :
- Certificats SSL invalides non gérés (Peptron)
- Pas de retry avec backoff
- Pas de validation des URLs extraites

**Absence de configuration par source** :
- Toutes les sources utilisent le même parser
- Pas de sélecteurs CSS spécifiques
- Pas de patterns de date personnalisés

---

## 2. Architecture cible

### 2.1 Composants de l'architecture refactorisée

```
vectora_core/ingestion/
├── fetcher.py (amélioré)
├── parser.py (refactorisé)
├── html_extractor.py (nouveau)
└── metrics_collector.py (nouveau)

canonical/sources/
├── source_catalog.yaml (existant)
└── html_extractors.yaml (nouveau)

docs/diagnostics/
├── vectora_inbox_corporate_ingestion_metrics_summary.md (nouveau)
└── vectora_inbox_corporate_html_parser_generic_results.md (nouveau)
```

### 2.2 Parser générique renforcé

**Nouvelles heuristiques** :
- Détection de cartes d'articles : `<article>`, `<li>`, `<div>` avec liens principaux
- Patterns CSS étendus : 'news', 'post', 'item', 'press', 'release', 'article'
- Extraction de métadonnées : Open Graph, JSON-LD, microdata
- Gestion des URLs relatives avec base URL automatique

**Extraction de dates améliorée** :
- Patterns génériques : YYYY-MM-DD, DD Month YYYY, Month DD YYYY
- Attributs HTML : `datetime`, `data-date`, `pubdate`
- Texte avec regex : "January 15, 2025", "15/01/2025", "2025-01-15"
- Fallback intelligent : date de dernière modification HTTP

### 2.3 Couche d'extracteurs spécifiques

**Configuration déclarative** (`canonical/sources/html_extractors.yaml`) :
```yaml
extractors:
  press_corporate__camurus:
    selectors:
      container: "div.press-releases-list"
      item: "div.press-release-item"
      title: "h3.title a"
      url: "h3.title a"
      date: "span.date"
      description: "div.excerpt"
    date_format: "%B %d, %Y"
    base_url: "https://www.camurus.com"
    
  press_corporate__peptron:
    selectors:
      container: "table.news-table"
      item: "tr.news-row"
      title: "td.title a"
      url: "td.title a"
      date: "td.date"
    date_format: "%Y.%m.%d"
    base_url: "https://www.peptron.co.kr"
    ssl_verify: false
```

### 2.4 Métrologie d'ingestion

**Métriques collectées par source** :
- Nombre de pages/flux fetchés
- Nombre d'items candidats trouvés
- Nombre d'items valides retenus (avec titre + URL)
- Nombre d'items avec date détectée
- Temps d'exécution par source
- Erreurs HTTP et parsing

**Exposition des métriques** :
- Structure JSON sérialisable
- Script de diagnostic local
- Rapports automatiques dans `docs/diagnostics/`

---

## 3. Plan d'exécution par phases

### Phase 1 : Parser générique robustifié

**Objectifs** :
- Améliorer le parser générique dans `parser.py`
- Rendre fonctionnelles 4/5 sources (MedinCell, DelSiTech, Nanexa + amélioration générale)
- Maintenir la compatibilité RSS

**Fichiers concernés** :
- `src/vectora_core/ingestion/parser.py`
- `src/vectora_core/ingestion/fetcher.py`

**Modifications** :

1. **Amélioration des heuristiques de détection** :
```python
def _find_article_containers(soup):
    """Trouve les conteneurs d'articles avec heuristiques étendues"""
    containers = []
    
    # Pattern 1: balises <article>
    containers.extend(soup.find_all('article'))
    
    # Pattern 2: divs avec classes news/press
    news_classes = ['news', 'post', 'item', 'press', 'release', 'article', 'story']
    for class_name in news_classes:
        containers.extend(soup.find_all('div', class_=re.compile(class_name, re.I)))
    
    # Pattern 3: listes d'articles
    containers.extend(soup.find_all('li', class_=re.compile('news|post|item', re.I)))
    
    return containers[:20]  # Limiter à 20 items
```

2. **Extraction de dates améliorée** :
```python
def _extract_date_from_element(element):
    """Extrait la date avec patterns multiples"""
    # Attributs HTML
    for attr in ['datetime', 'data-date', 'pubdate']:
        if element.get(attr):
            return _parse_date_string(element[attr])
    
    # Recherche dans le texte
    date_patterns = [
        r'\d{4}-\d{2}-\d{2}',
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'[A-Za-z]+ \d{1,2}, \d{4}',
        r'\d{1,2} [A-Za-z]+ \d{4}'
    ]
    
    text = element.get_text()
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            return _parse_date_string(match.group())
    
    return datetime.now().strftime('%Y-%m-%d')
```

3. **Gestion des URLs relatives** :
```python
def _resolve_url(url, base_url):
    """Résout les URLs relatives"""
    if url.startswith('http'):
        return url
    elif url.startswith('/'):
        return urljoin(base_url, url)
    else:
        return urljoin(base_url + '/', url)
```

**Critères de succès Phase 1** :
- 4/5 sources corporate fonctionnelles (80%)
- Extraction de dates réelles (pas seulement date actuelle)
- Gestion des URLs relatives
- Aucune régression sur les sources RSS

---

### Phase 2 : Instrumentation et métriques

**Objectifs** :
- Ajouter la collecte de métriques par source
- Créer un système de diagnostic automatique
- Identifier les sources problématiques

**Fichiers concernés** :
- `src/vectora_core/ingestion/metrics_collector.py` (nouveau)
- `src/vectora_core/ingestion/parser.py` (instrumentation)
- `scripts/diagnose_corporate_ingestion.py` (nouveau)

**Nouveau module** : `metrics_collector.py`
```python
class IngestionMetrics:
    def __init__(self):
        self.metrics = {}
    
    def record_source_metrics(self, source_key, metrics_data):
        """Enregistre les métriques d'une source"""
        self.metrics[source_key] = {
            'pages_fetched': metrics_data.get('pages_fetched', 0),
            'items_found': metrics_data.get('items_found', 0),
            'items_valid': metrics_data.get('items_valid', 0),
            'items_with_date': metrics_data.get('items_with_date', 0),
            'execution_time': metrics_data.get('execution_time', 0),
            'errors': metrics_data.get('errors', [])
        }
    
    def generate_report(self):
        """Génère un rapport de métriques"""
        return {
            'timestamp': datetime.now().isoformat(),
            'sources': self.metrics,
            'summary': self._calculate_summary()
        }
```

**Script de diagnostic** : `scripts/diagnose_corporate_ingestion.py`
```python
def diagnose_corporate_sources():
    """Diagnostic des sources corporate HTML"""
    sources = ['press_corporate__medincell', 'press_corporate__camurus', 
               'press_corporate__delsitech', 'press_corporate__nanexa', 
               'press_corporate__peptron']
    
    results = {}
    for source_key in sources:
        result = test_source_ingestion(source_key)
        results[source_key] = result
    
    generate_diagnostic_report(results)
```

**Critères de succès Phase 2** :
- Métriques collectées pour toutes les sources HTML
- Rapport de diagnostic automatique généré
- Identification des sources à améliorer

---

### Phase 3 : Extracteurs spécifiques pour sources critiques

**Objectifs** :
- Implémenter la couche d'extracteurs spécifiques
- Rendre fonctionnelles Camurus et Peptron
- Maintenir le fallback sur parser générique

**Fichiers concernés** :
- `canonical/sources/html_extractors.yaml` (nouveau)
- `src/vectora_core/ingestion/html_extractor.py` (nouveau)
- `src/vectora_core/ingestion/parser.py` (intégration)

**Configuration des extracteurs** :
```yaml
# canonical/sources/html_extractors.yaml
extractors:
  press_corporate__camurus:
    selectors:
      container: "div.press-releases"
      item: "div.press-release-item"
      title: "h3 a"
      url: "h3 a"
      date: "time"
      description: "div.excerpt"
    date_format: "%B %d, %Y"
    base_url: "https://www.camurus.com"
    
  press_corporate__peptron:
    selectors:
      container: "table.board_list"
      item: "tr"
      title: "td.subject a"
      url: "td.subject a"
      date: "td.date"
    date_format: "%Y.%m.%d"
    base_url: "https://www.peptron.co.kr"
    ssl_verify: false
```

**Module d'extraction configurable** :
```python
class ConfigurableHTMLExtractor:
    def __init__(self, config_bucket=None):
        self.extractors = self._load_extractor_configs(config_bucket)
    
    def extract_items(self, html_content, source_key):
        """Extrait les items avec config spécifique ou générique"""
        if source_key in self.extractors:
            return self._extract_with_config(html_content, source_key)
        else:
            return self._extract_with_heuristics(html_content, source_key)
    
    def _extract_with_config(self, html_content, source_key):
        """Extraction avec configuration spécifique"""
        config = self.extractors[source_key]
        soup = BeautifulSoup(html_content, 'html.parser')
        
        items = []
        container = soup.select_one(config['selectors']['container'])
        if container:
            item_elements = container.select(config['selectors']['item'])
            for element in item_elements[:20]:
                item = self._extract_item_with_selectors(element, config)
                if item:
                    items.append(item)
        
        return items
```

**Critères de succès Phase 3** :
- 5/5 sources corporate fonctionnelles (100%)
- Camurus et Peptron extraient des items valides
- Fallback générique préservé pour les autres sources

---

### Phase 4 : Tests et validation

**Objectifs** :
- Créer une suite de tests complète
- Valider la non-régression RSS
- Tester l'intégration avec les profils d'ingestion

**Fichiers concernés** :
- `tests/unit/test_html_parser_refactor.py` (nouveau)
- `tests/integration/test_corporate_sources.py` (nouveau)
- `scripts/test_html_ingestion_local.py` (nouveau)

**Tests unitaires** :
```python
def test_generic_parser_improvements():
    """Test du parser générique amélioré"""
    
def test_date_extraction_patterns():
    """Test de l'extraction de dates avec différents formats"""
    
def test_url_resolution():
    """Test de la résolution des URLs relatives"""
    
def test_specific_extractors():
    """Test des extracteurs spécifiques Camurus/Peptron"""
    
def test_fallback_mechanism():
    """Test du fallback générique"""
```

**Tests d'intégration** :
```python
def test_all_corporate_sources_mvp():
    """Test end-to-end des 5 sources corporate"""
    sources = ['press_corporate__medincell', 'press_corporate__camurus',
               'press_corporate__delsitech', 'press_corporate__nanexa', 
               'press_corporate__peptron']
    
    for source_key in sources:
        items = simulate_source_ingestion(source_key)
        assert len(items) > 0, f"Source {source_key} should extract items"
        assert all('title' in item and 'url' in item for item in items)
```

**Critères de succès Phase 4** :
- Tous les tests unitaires passent
- 5/5 sources corporate extraient des items
- Aucune régression sur les sources RSS
- Intégration avec profils d'ingestion préservée

---

### Phase 5 : Documentation et diagnostic final

**Objectifs** :
- Documenter les améliorations apportées
- Créer les rapports de diagnostic
- Fournir un guide de maintenance

**Livrables** :
- `docs/diagnostics/vectora_inbox_corporate_html_parser_generic_results.md`
- `docs/diagnostics/vectora_inbox_corporate_ingestion_metrics_summary.md`
- `docs/diagnostics/vectora_inbox_corporate_html_specific_extractors_results.md`
- `docs/diagnostics/vectora_inbox_corporate_html_parser_refactor_results.md`

**Contenu des diagnostics** :
1. **Résultats du parser générique** : Performance sur les sources standard
2. **Métriques d'ingestion** : Tableau de bord par source MVP LAI
3. **Extracteurs spécifiques** : Configuration et résultats Camurus/Peptron
4. **Résultats finaux** : Bilan complet du refactoring

**Critères de succès Phase 5** :
- Documentation complète des améliorations
- Rapports de diagnostic générés automatiquement
- Guide de maintenance pour les extracteurs spécifiques

---

## 4. Impacts et considérations

### 4.1 Compatibilité et intégration

**Flux RSS préservé** :
- Aucune modification du parsing RSS
- Tests de non-régression systématiques
- Séparation claire des logiques RSS/HTML

**Profils d'ingestion respectés** :
- Le filtrage par profil reste après parsing
- Intégration avec `ingestion_profiles.yaml` préservée
- Pas de modification de la logique de matching/scoring

### 4.2 Performance et scalabilité

**Impact sur la latence** :
- Parser générique : +2-3 secondes par source
- Extracteurs spécifiques : +1-2 secondes par source
- Chargement de configuration : +1 seconde au démarrage

**Optimisations** :
- Cache des configurations d'extracteurs
- Limitation à 20 items par source
- Timeout adaptatif par source

### 4.3 Maintenance et évolutivité

**Ajout de nouvelles sources** :
- Parser générique fonctionne par défaut
- Extracteur spécifique si nécessaire (configuration YAML)
- Pas de modification de code pour les cas standards

**Maintenance des extracteurs** :
- Configuration déclarative facile à modifier
- Tests automatisés pour détecter les changements de structure
- Fallback automatique en cas d'échec

---

## 5. Risques et mitigation

### 5.1 Risques techniques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression RSS | Faible | Élevé | Tests exhaustifs, séparation des logiques |
| Sites changent structure | Moyen | Moyen | Monitoring, fallback générique |
| Performance dégradée | Faible | Moyen | Optimisations, timeouts adaptatifs |

### 5.2 Risques opérationnels

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Maintenance accrue | Moyen | Faible | Configuration déclarative, documentation |
| Complexité système | Faible | Moyen | Architecture modulaire, tests automatisés |

---

## Executive Summary

### Objectif
Refactoring durable du parser HTML corporate pour passer de 60% à 100% de sources fonctionnelles avec une architecture générique + exceptions.

### Approche
1. **Parser générique robustifié** : Heuristiques améliorées, extraction de dates, gestion URLs relatives
2. **Extracteurs spécifiques** : Configuration déclarative pour Camurus et Peptron uniquement
3. **Métrologie** : Métriques par source pour identifier les problèmes

### Plan d'exécution
- **Phase 1** : Parser générique amélioré (4/5 sources fonctionnelles)
- **Phase 2** : Instrumentation et métriques
- **Phase 3** : Extracteurs spécifiques (5/5 sources fonctionnelles)
- **Phase 4** : Tests et validation complète
- **Phase 5** : Documentation et diagnostic final

### Bénéfices attendus
- **100% des sources corporate fonctionnelles** (vs 60% actuellement)
- **Architecture maintenable** avec configuration déclarative
- **Monitoring automatique** des performances par source
- **Compatibilité préservée** avec RSS et profils d'ingestion

### Effort estimé
- **3-4 jours** de développement
- **Risque faible** de régression
- **Impact positif immédiat** sur la couverture LAI

---

**Document créé le** : 2025-01-15  
**Dernière mise à jour** : 2025-01-15  
**Version** : 1.0