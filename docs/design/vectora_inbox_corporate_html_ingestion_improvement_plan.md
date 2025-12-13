# Plan d'amélioration de l'ingestion corporate HTML - Vectora Inbox

**Date de création** : 2025-01-15  
**Objectif** : Rendre robuste l'ingestion HTML des sources corporate LAI  
**Périmètre** : Sources corporate HTML du MVP LAI avant déploiement AWS  

---

## Vue d'ensemble du plan

Ce plan vise à corriger les failles identifiées dans l'ingestion HTML corporate et à passer de **60% de sources fonctionnelles** à **100%** avec une architecture robuste et maintenable.

**Problèmes à résoudre** :
- 2/5 sources corporate en échec (Camurus, Peptron)
- Parser HTML générique trop simpliste
- Gestion d'erreurs insuffisante
- Absence de configuration par source

**Approche** : Plan par phases avec implémentation progressive et tests à chaque étape.

---

## Phase 1 : Diagnostic (TERMINÉE)

### Objectifs
- Comprendre l'architecture d'ingestion HTML actuelle
- Identifier les sources en échec et leurs causes
- Quantifier l'impact sur le pipeline LAI

### Livrables
- ✅ `docs/diagnostics/vectora_inbox_corporate_html_ingestion_status.md`
- ✅ Analyse des 5 sources corporate MVP LAI
- ✅ Identification des failles techniques

### Critères de succès
- ✅ Cartographie complète du flux d'ingestion HTML
- ✅ Statut précis de chaque source (🟢/🟡/🔴)
- ✅ Quantification du taux de succès (60%)

---

## Phase 2 : Design des améliorations HTML

### Objectifs
- Concevoir les corrections pour les sources en échec
- Définir l'architecture d'un système HTML robuste
- Choisir entre approche P0 (minimale) et P1 (structurée)

### 2.1 Corrections immédiates (P0)

**Fichiers concernés** :
- `src/vectora_core/ingestion/fetcher.py`
- `src/vectora_core/ingestion/parser.py`
- `canonical/sources/source_catalog.yaml`

**Actions P0** :

1. **Correction Peptron (SSL)** :
   ```python
   # Dans fetcher.py
   if source_key == 'press_corporate__peptron':
       response = requests.get(url, timeout=REQUEST_TIMEOUT, verify=False)
   ```

2. **Parser spécifique Camurus** :
   ```python
   # Dans parser.py
   def _parse_camurus_html(soup, source_key, source_type):
       # Sélecteurs spécifiques pour Camurus
       items = []
       press_items = soup.find_all('div', class_='press-release-item')
       # ... extraction spécifique
   ```

3. **Amélioration extraction de date** :
   ```python
   def _extract_date_from_html(element):
       # Chercher patterns de date courants
       date_patterns = [
           r'\d{1,2}/\d{1,2}/\d{4}',
           r'\d{4}-\d{2}-\d{2}',
           r'[A-Za-z]+ \d{1,2}, \d{4}'
       ]
   ```

### 2.2 Architecture structurée (P1)

**Nouveau fichier** : `canonical/html_extractors/extractor_configs.yaml`

```yaml
extractors:
  press_corporate__camurus:
    selectors:
      container: "div.press-releases-list"
      item: "div.press-release-item"
      title: "h3.title a"
      url: "h3.title a"
      date: "span.date"
      description: "div.excerpt p"
    date_format: "%B %d, %Y"
    base_url: "https://www.camurus.com"
    max_items: 20
    
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

**Nouveau module** : `src/vectora_core/ingestion/html_extractor.py`

```python
class ConfigurableHTMLExtractor:
    def __init__(self, config_bucket: str):
        self.extractors = self._load_extractor_configs(config_bucket)
    
    def extract_items(self, html_content: str, source_key: str) -> List[Dict]:
        if source_key in self.extractors:
            return self._extract_with_config(html_content, source_key)
        else:
            return self._extract_with_heuristics(html_content, source_key)
```

### Critères de succès Phase 2
- Design technique validé pour P0 et P1
- Spécifications détaillées des modifications
- Estimation des impacts (performance, maintenance)
- Choix argumenté entre P0 et P1

---

## Phase 3 : Implémentation dans le code ingest-normalize

### Objectifs
- Implémenter les corrections choisies (P0 ou P1)
- Maintenir la compatibilité avec les sources RSS
- Ajouter des tests unitaires

### 3.1 Modifications du code (Approche P0)

**Fichier** : `src/vectora_core/ingestion/fetcher.py`
```python
def fetch_source(source_meta: dict) -> Optional[str]:
    # ... code existant ...
    
    # Gestion spéciale pour les sources avec problèmes SSL
    ssl_verify = True
    if source_key in ['press_corporate__peptron']:
        ssl_verify = False
        logger.warning(f"SSL verification disabled for {source_key}")
    
    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT,
        headers={'User-Agent': 'Vectora-Inbox/1.0'},
        verify=ssl_verify
    )
```

**Fichier** : `src/vectora_core/ingestion/parser.py`
```python
def _parse_html_page(raw_content: str, source_key: str, source_type: str, source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    # ... code existant ...
    
    # Parsers spécifiques par source
    if source_key == 'press_corporate__camurus':
        return _parse_camurus_specific(soup, source_key, source_type)
    elif source_key == 'press_corporate__peptron':
        return _parse_peptron_specific(soup, source_key, source_type)
    
    # Fallback sur parser générique
    return _parse_generic_html(soup, source_key, source_type)
```

### 3.2 Modifications du code (Approche P1)

**Nouveau fichier** : `src/vectora_core/ingestion/html_extractor.py`
- Classe `ConfigurableHTMLExtractor`
- Méthodes de parsing configurables
- Gestion des erreurs et fallbacks

**Modification** : `src/vectora_core/ingestion/parser.py`
```python
from vectora_core.ingestion.html_extractor import ConfigurableHTMLExtractor

def _parse_html_page(raw_content: str, source_key: str, source_type: str, source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    extractor = ConfigurableHTMLExtractor(source_meta.get('config_bucket'))
    return extractor.extract_items(raw_content, source_key)
```

### 3.3 Tests unitaires

**Nouveau fichier** : `tests/unit/test_html_extraction.py`
```python
def test_camurus_html_extraction():
    # Test avec HTML réel de Camurus
    
def test_peptron_ssl_handling():
    # Test de la gestion SSL
    
def test_generic_fallback():
    # Test du fallback générique
```

### Critères de succès Phase 3
- Code implémenté et testé localement
- Tests unitaires passants
- Compatibilité RSS préservée
- Documentation du code mise à jour

---

## Phase 4 : Tests (unitaires + simulation end-to-end)

### Objectifs
- Valider les corrections sur les sources en échec
- Tester la non-régression sur les sources fonctionnelles
- Simuler un run complet end-to-end

### 4.1 Tests unitaires

**Fichiers de test** :
- `tests/unit/test_html_extraction.py`
- `tests/unit/test_fetcher_ssl.py`
- `tests/unit/test_parser_specific.py`

**Couverture** :
- Parsing HTML avec différentes structures
- Gestion des erreurs SSL
- Extraction de dates
- Fallback sur parser générique

### 4.2 Tests d'intégration

**Script** : `tests/integration/test_html_sources_mvp.py`
```python
def test_all_corporate_sources():
    """Test toutes les sources corporate HTML du MVP"""
    sources = [
        'press_corporate__medincell',
        'press_corporate__camurus',
        'press_corporate__delsitech', 
        'press_corporate__nanexa',
        'press_corporate__peptron'
    ]
    
    for source_key in sources:
        items = test_source_extraction(source_key)
        assert len(items) > 0, f"Source {source_key} should extract items"
```

### 4.3 Simulation end-to-end

**Script** : `scripts/test_html_ingestion_local.py`
- Simulation complète du pipeline d'ingestion
- Test avec les 5 sources corporate
- Validation du format des items extraits
- Métriques de performance

### Critères de succès Phase 4
- 5/5 sources corporate fonctionnelles
- Taux de succès HTML : 100%
- Items extraits : ~50-60 items/semaine
- Temps d'exécution : <30 secondes
- Aucune régression sur les sources RSS

---

## Phase 5 : Déploiement AWS DEV + monitoring

### Objectifs
- Déployer les corrections sur l'environnement DEV
- Mettre en place le monitoring des sources HTML
- Valider en conditions réelles

### 5.1 Déploiement

**Scripts de déploiement** :
- `scripts/package-ingest-normalize-html-fix.ps1`
- `scripts/deploy-ingest-normalize-html-fix.ps1`

**Étapes** :
1. Package du code avec les corrections
2. Déploiement de la Lambda `vectora-inbox-ingest-normalize-dev`
3. Mise à jour des configurations canonical si nécessaire
4. Test de smoke avec payload minimal

### 5.2 Monitoring

**Métriques à surveiller** :
- Taux de succès par source HTML
- Nombre d'items extraits par source
- Temps de réponse par source
- Erreurs SSL et timeouts

**Alertes CloudWatch** :
- Source avec 0 items pendant 2 runs consécutifs
- Temps d'exécution > 60 secondes
- Taux d'erreur > 20%

### 5.3 Validation en conditions réelles

**Test de validation** :
```json
{
  "client_id": "lai_weekly",
  "sources": [
    "press_corporate__medincell",
    "press_corporate__camurus", 
    "press_corporate__delsitech",
    "press_corporate__nanexa",
    "press_corporate__peptron"
  ],
  "period_days": 7
}
```

**Critères d'acceptation** :
- 5/5 sources retournent des items
- Total items HTML : 40-60 items
- Aucune erreur critique
- Temps d'exécution < 45 secondes

### Critères de succès Phase 5
- Déploiement réussi sans régression
- Monitoring opérationnel
- Validation end-to-end en conditions réelles
- Documentation de déploiement mise à jour

---

## Estimation des efforts

### Approche P0 (Corrections minimales)

| Phase | Effort | Durée |
|-------|--------|-------|
| Phase 2 (Design P0) | 0.5 jour | 4h |
| Phase 3 (Implémentation P0) | 1 jour | 8h |
| Phase 4 (Tests) | 0.5 jour | 4h |
| Phase 5 (Déploiement) | 0.5 jour | 4h |
| **Total P0** | **2.5 jours** | **20h** |

### Approche P1 (Architecture structurée)

| Phase | Effort | Durée |
|-------|--------|-------|
| Phase 2 (Design P1) | 1 jour | 8h |
| Phase 3 (Implémentation P1) | 2 jours | 16h |
| Phase 4 (Tests) | 1 jour | 8h |
| Phase 5 (Déploiement) | 0.5 jour | 4h |
| **Total P1** | **4.5 jours** | **36h** |

---

## Recommandation

### Pour le MVP LAI immédiat : Approche P0

**Justification** :
- Besoin urgent de rendre fonctionnelles les sources Camurus et Peptron
- Effort minimal pour un gain maximal (60% → 100%)
- Risque faible de régression
- Déploiement rapide possible

### Pour l'évolution long terme : Migration vers P1

**Justification** :
- Système plus maintenable et extensible
- Facilite l'ajout de nouvelles sources corporate
- Meilleure observabilité et debugging
- Architecture plus robuste

**Plan de migration** :
1. Implémenter P0 pour débloquer le MVP
2. Planifier P1 pour la version suivante
3. Migrer progressivement les sources vers la configuration déclarative

---

## Risques et mitigation

### Risques techniques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression sur sources fonctionnelles | Faible | Élevé | Tests exhaustifs, déploiement progressif |
| Camurus change sa structure HTML | Moyen | Moyen | Monitoring, fallback sur parser générique |
| Peptron reste inaccessible | Élevé | Faible | Désactivation temporaire si nécessaire |

### Risques opérationnels

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Augmentation du temps d'exécution | Moyen | Faible | Optimisation, timeout adaptatif |
| Coûts Bedrock plus élevés | Faible | Faible | Monitoring des coûts |
| Maintenance accrue | Moyen | Moyen | Documentation, tests automatisés |

---

## Conclusion

Ce plan propose une approche pragmatique pour résoudre les problèmes d'ingestion HTML corporate dans Vectora Inbox :

1. **Phase 1** ✅ : Diagnostic complet réalisé
2. **Phases 2-5** : Plan d'exécution détaillé avec 2 approches
3. **Recommandation** : P0 pour le MVP, P1 pour l'évolution

**Objectif** : Passer de 60% à 100% de sources corporate fonctionnelles avec un effort maîtrisé et des risques minimisés.

---

**Document créé le** : 2025-01-15  
**Dernière mise à jour** : 2025-01-15  
**Version** : 1.0