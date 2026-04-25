# Modules d'Ingestion Refactorisés

**Version**: 2.0  
**Date**: 2026-02-10

---

## 📦 MODULES

### date_extractor.py
Extraction unifiée de dates avec cascade intelligente.

**Cascade:**
1. HTML metadata (JSON-LD, meta tags) - 95% confiance
2. RSS pubDate - 90% confiance
3. Text extraction (titre + contenu) - 85% confiance
4. URL patterns - 60% confiance
5. Fallback (date actuelle) - 0% confiance

**Usage:**
```python
from vectora_core.ingest.date_extractor import DateExtractor

extractor = DateExtractor()
result = extractor.extract(
    item_data={'title': 'Article', 'published': '2024-01-15'},
    raw_html='<html>...</html>'
)

print(result.date)        # '2024-01-15'
print(result.source)      # 'html_metadata'
print(result.confidence)  # 0.95
```

---

### content_extractor.py
Extraction unifiée de contenu HTML et PDF.

**Fonctionnalités:**
- Détection automatique du type (HTML/PDF)
- Nettoyage HTML (suppression scripts, styles, nav)
- Extraction PDF avec pdfplumber
- Limite configurable (max_length)
- Timeout configurable

**Usage:**
```python
from vectora_core.ingest.content_extractor import ContentExtractor

extractor = ContentExtractor(timeout=15, max_length=3000)
content = extractor.extract('https://example.com/article')

if content:
    print(f"Extracted {len(content)} chars")
```

---

### html_parser.py
Parser HTML simplifié avec selectors CSS configurables.

**Fonctionnalités:**
- Selectors CSS configurables
- Extraction: titre, URL, date, résumé
- Limite 20 items par page
- Support containers multiples

**Usage:**
```python
from vectora_core.ingest.html_parser import HTMLParser

parser = HTMLParser()
items = parser.parse_listing(
    html='<html>...</html>',
    config={'container': 'article'}
)

for item in items:
    print(f"{item.title}: {item.url}")
```

---

## 🧪 TESTS

### Exécuter les Tests

```bash
# Tous les tests
pytest tests/ingestion/ -v

# Tests spécifiques
pytest tests/ingestion/test_date_extractor.py -v
pytest tests/ingestion/test_content_extractor.py -v
pytest tests/ingestion/test_html_parser.py -v

# Avec couverture
pytest tests/ingestion/ --cov=src_v2.vectora_core.ingest --cov-report=html
```

### Couverture Cible
- date_extractor: > 90%
- content_extractor: > 90%
- html_parser: > 90%

---

## 📊 MÉTRIQUES

### Réduction Code
- Code mort supprimé: -220 lignes
- Fonctions simplifiées: -420 lignes
- Nouveaux modules: +220 lignes
- **Net: -420 lignes (-18%)**

### Qualité
- Modules séparés et testables
- Séparation des responsabilités
- Code plus maintenable
- Meilleure traçabilité

---

## 🔗 INTÉGRATION

Ces modules sont utilisés par `content_parser.py`:

```python
from .date_extractor import DateExtractor
from .content_extractor import ContentExtractor

_date_extractor = DateExtractor()
_content_extractor = ContentExtractor()

# Utilisation dans parse_source_content()
result = _date_extractor.extract(item_dict, raw_html)
content = _content_extractor.extract(url)
```

---

## 📝 DOCUMENTATION

- **Plan**: `docs/PLAN_AMELIORATION_INGEST_PAR_PHASES.md`
- **Rapport**: `docs/RAPPORT_EXECUTION_REFACTORING_INGEST.md`
- **Migration**: `docs/GUIDE_MIGRATION_REFACTORING_INGEST.md`

---

## ✨ AMÉLIORATIONS FUTURES

### date_extractor
- [ ] Support langues supplémentaires
- [ ] Patterns de dates personnalisés par source
- [ ] Cache des résultats

### content_extractor
- [ ] Support formats supplémentaires (DOCX, etc.)
- [ ] Extraction images
- [ ] Résumé automatique

### html_parser
- [ ] Selectors adaptatifs (ML)
- [ ] Détection automatique de structure
- [ ] Support pagination

---

**Contributeurs**: Équipe Vectora  
**Licence**: Propriétaire
