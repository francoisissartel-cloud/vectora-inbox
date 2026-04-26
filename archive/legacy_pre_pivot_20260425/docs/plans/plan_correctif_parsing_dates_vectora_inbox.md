# Plan Correctif - Parsing des Dates Vectora Inbox

**Date**: 2026-01-27  
**Objectif**: Corriger le parsing défaillant des dates de publication pour avoir des dates réelles dans les newsletters  
**Architecture**: 3 Lambdas V2 (src_v2/)  
**Client de référence**: lai_weekly_v6  

---

## DIAGNOSTIC PRÉCIS

### Problème identifié

**Symptôme**: Toutes les news ont `published_at: "2026-01-27"` (date d'ingestion) au lieu de leur vraie date de publication

**Impact**:
- Filtre temporel inefficace (30 jours configurés mais news de novembre 2025 récupérées)
- Newsletter affiche dates d'ingestion au lieu des dates réelles des news
- Utilisateurs perdent la chronologie réelle des événements

### Analyse technique

**Fichier problématique**: `src_v2/vectora_core/ingest/content_parser.py`

**Fonction défaillante**: `_extract_published_date_with_config()`
- Ligne 234: Appelle `extract_real_publication_date()` mais fallback systématique sur date actuelle
- Ligne 280: `extract_real_publication_date()` ne trouve pas les dates dans le contenu
- Ligne 320: Patterns d'extraction manquants dans source_config

**Données analysées**:
```
Source                | Vraie date dans contenu | published_at actuel
---------------------|-------------------------|--------------------
MedinCell NDA        | December 9, 2025       | 2026-01-27
MedinCell Grant      | November 24, 2025      | 2026-01-27
Nanexa Semaglutide   | 27 January, 2026       | 2026-01-27
Camurus Oclaiz       | 09 January 2026        | 2026-01-27
```

---

## PHASE 1: CADRAGE

### 1.1 Objectifs

**Objectif principal**: Extraire et utiliser les dates réelles de publication des news

**Objectifs spécifiques**:
1. Corriger l'extraction des dates dans `content_parser.py`
2. Ajouter patterns d'extraction par source dans configurations
3. Séparer `published_at` (date réelle) et `ingested_at` (métadonnée admin)
4. Valider le filtre temporel avec vraies dates
5. Afficher dates réelles dans newsletters finales

### 1.2 Périmètre

**Dans le périmètre**:
- ✅ Extraction dates RSS (champs `published_parsed`, `pubDate`)
- ✅ Extraction dates HTML/contenu (patterns regex)
- ✅ Configuration patterns par source
- ✅ Validation filtre temporel
- ✅ Affichage dates dans newsletter

**Hors périmètre**:
- ❌ Modification architecture 3 Lambdas V2
- ❌ Changement format stockage S3
- ❌ Réingestion historique (focus sur nouveaux runs)

### 1.3 Contraintes

**Techniques**:
- Respecter architecture src_v2/ existante
- Maintenir compatibilité avec lai_weekly_v6.yaml
- Préserver performance ingestion (<30s par source)

**Métier**:
- Fallback sur date d'ingestion si extraction impossible
- Conserver `ingested_at` pour traçabilité admin
- Priorité aux dates RSS > contenu > fallback

---

## PHASE 2: CORRECTIFS

### 2.1 Correctif 1: Améliorer extraction dates RSS

**Fichier**: `src_v2/vectora_core/ingest/content_parser.py`

**Fonction**: `extract_real_publication_date()`

**Modifications**:
```python
def extract_real_publication_date(item_data: Dict[str, Any], source_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extraction intelligente de la date de publication
    1. Parser les champs date RSS (pubDate, dc:date, published_parsed)
    2. Extraction regex dans le contenu HTML
    3. Fallback sur date d'ingestion avec flag
    """
    import re
    from datetime import datetime
    
    # Priorité 1: Champs RSS standards
    if hasattr(item_data, 'published_parsed') and item_data.published_parsed:
        try:
            dt = datetime(*item_data.published_parsed[:6])
            return {
                'date': dt.strftime('%Y-%m-%d'),
                'date_source': 'rss_parsed'
            }
        except (ValueError, TypeError):
            pass
    
    # Priorité 1b: Champ pubDate string
    if hasattr(item_data, 'published') and item_data.published:
        parsed_date = _parse_date_string(item_data.published)
        if parsed_date:
            return {
                'date': parsed_date,
                'date_source': 'rss_pubdate'
            }
    
    # Priorité 2: Extraction contenu avec patterns source
    content = item_data.get('content', '') + ' ' + item_data.get('title', '')
    date_patterns = source_config.get('date_extraction_patterns', [])
    
    # Patterns par défaut si non configurés
    if not date_patterns:
        date_patterns = [
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})'
        ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            parsed_date = _parse_date_string(match)
            if parsed_date:
                return {
                    'date': parsed_date,
                    'date_source': 'content_extraction'
                }
    
    # Priorité 3: Fallback avec flag
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'date_source': 'ingestion_fallback'
    }
```

### 2.2 Correctif 2: Patterns d'extraction par source

**Fichier**: Configuration sources dans S3

**Ajout dans source_catalog.yaml**:
```yaml
sources:
  - source_key: press_corporate__medincell
    date_extraction_patterns:
      - '(\w+ \d{1,2}, \d{4})'  # November 24, 2025
      - '(\d{1,2} \w+ \d{4})'   # 24 November 2025
      - '(\d{4}-\d{2}-\d{2})'   # 2025-11-24
  
  - source_key: press_corporate__nanexa
    date_extraction_patterns:
      - '(\d{1,2} \w+, \d{4})'  # 27 January, 2026
      - '(\w+ \d{1,2}, \d{4})'  # January 27, 2026
  
  - source_key: press_corporate__camurus
    date_extraction_patterns:
      - '(\d{2} \w+ \d{4})'     # 09 January 2026
```

### 2.3 Correctif 3: Améliorer _parse_date_string()

**Fonction**: `_parse_date_string()`

**Ajout formats**:
```python
def _parse_date_string(date_str: str) -> Optional[str]:
    """Parse une chaîne de date dans différents formats"""
    if not date_str:
        return None
    
    # Formats de dates étendus
    date_formats = [
        '%Y-%m-%d',                    # 2025-11-24
        '%d %B %Y',                    # 24 November 2025
        '%B %d, %Y',                   # November 24, 2025
        '%d %b %Y',                    # 24 Nov 2025
        '%b %d, %Y',                   # Nov 24, 2025
        '%d/%m/%Y',                    # 24/11/2025
        '%m/%d/%Y',                    # 11/24/2025
        '%Y-%m-%dT%H:%M:%S',          # ISO avec heure
        '%a, %d %b %Y %H:%M:%S %Z',   # RFC 2822
    ]
    
    # Nettoyer la chaîne
    date_str = date_str.strip()
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None
```

### 2.4 Correctif 4: Validation filtre temporel

**Fichier**: `src_v2/vectora_core/shared/utils.py`

**Fonction**: `apply_temporal_filter()`

**Ajout logging**:
```python
def apply_temporal_filter(items: List[Dict[str, Any]], cutoff_date_str: str, temporal_mode: str = "strict") -> List[Dict[str, Any]]:
    """Filtre les items selon leur date de publication avec logging détaillé"""
    
    cutoff_date = datetime.strptime(cutoff_date_str, '%Y-%m-%d')
    filtered_items = []
    stats = {
        'total': len(items),
        'kept': 0,
        'filtered_old': 0,
        'no_date': 0,
        'fallback_dates': 0
    }
    
    for item in items:
        published_at = item.get('published_at')
        
        if not published_at:
            stats['no_date'] += 1
            continue
        
        try:
            item_date = datetime.strptime(published_at, '%Y-%m-%d')
            
            # Détecter les dates fallback (même jour que l'ingestion)
            ingested_at = item.get('ingested_at', '')
            if ingested_at and published_at == ingested_at[:10]:
                stats['fallback_dates'] += 1
                logger.warning(f"Item avec date fallback: {item.get('title', '')[:50]}...")
            
            if item_date >= cutoff_date:
                filtered_items.append(item)
                stats['kept'] += 1
            else:
                stats['filtered_old'] += 1
                logger.debug(f"Item trop ancien ({published_at}): {item.get('title', '')[:50]}...")
        
        except ValueError:
            stats['no_date'] += 1
    
    logger.info(f"Filtre temporel: {stats['kept']}/{stats['total']} items conservés, "
                f"{stats['filtered_old']} trop anciens, {stats['fallback_dates']} dates fallback")
    
    return filtered_items
```

---

## PHASE 3: TESTS LOCAUX

### 3.1 Test unitaire extraction dates

**Fichier**: `tests/unit/test_date_extraction.py`

```python
def test_extract_real_publication_date():
    """Test extraction dates avec différents formats"""
    
    # Test RSS parsed
    rss_entry = type('Entry', (), {
        'published_parsed': (2025, 11, 24, 10, 30, 0, 0, 0, 0)
    })()
    
    result = extract_real_publication_date(rss_entry, {})
    assert result['date'] == '2025-11-24'
    assert result['date_source'] == 'rss_parsed'
    
    # Test contenu avec pattern
    content_entry = {
        'content': 'Published on November 24, 2025',
        'title': 'Test news'
    }
    
    source_config = {
        'date_extraction_patterns': [r'(\w+ \d{1,2}, \d{4})']
    }
    
    result = extract_real_publication_date(content_entry, source_config)
    assert result['date'] == '2025-11-24'
    assert result['date_source'] == 'content_extraction'
```

### 3.2 Test intégration avec vraies données

**Script**: `tests/integration/test_date_parsing_lai_v6.py`

```python
def test_lai_v6_date_extraction():
    """Test avec données réelles lai_weekly_v6"""
    
    # Charger items ingérés v6
    with open('items_ingested_v6.json') as f:
        items = json.load(f)
    
    # Vérifier extraction dates
    medincell_nda = next(item for item in items if 'Olanzapine' in item['title'])
    
    # Simuler re-parsing avec nouveau code
    parsed_date = extract_date_from_content(medincell_nda['content'])
    
    assert parsed_date == '2025-12-09'  # Vraie date vs 2026-01-27
```

### 3.3 Test filtre temporel

**Script**: `tests/integration/test_temporal_filter_fixed.py`

```python
def test_temporal_filter_with_real_dates():
    """Test filtre temporel avec vraies dates"""
    
    items = [
        {'title': 'Recent', 'published_at': '2026-01-20'},
        {'title': 'Old', 'published_at': '2025-11-24'},  # >30 jours
        {'title': 'Fallback', 'published_at': '2026-01-27'}  # Date ingestion
    ]
    
    cutoff_date = '2025-12-28'  # 30 jours avant 2026-01-27
    filtered = apply_temporal_filter(items, cutoff_date)
    
    assert len(filtered) == 2  # Recent + Fallback conservés
    assert filtered[0]['title'] == 'Recent'
```

---

## PHASE 4: DÉPLOIEMENT AWS

### 4.1 Mise à jour code

**Commandes**:
```bash
# 1. Mise à jour layer vectora-core
cd src_v2
zip -r ../vectora-core-fixed.zip vectora_core/

# 2. Upload layer
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://../vectora-core-fixed.zip \
  --compatible-runtimes python3.11 \
  --region eu-west-3 \
  --profile rag-lai-prod

# 3. Mise à jour Lambda ingest-v2
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:4 \
           arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:NEW_VERSION \
  --region eu-west-3 \
  --profile rag-lai-prod
```

### 4.2 Mise à jour configurations sources

**Upload patterns**:
```bash
# Upload source_catalog.yaml avec patterns
aws s3 cp canonical/sources/source_catalog.yaml \
  s3://vectora-inbox-config-dev/canonical/sources/ \
  --profile rag-lai-prod
```

### 4.3 Test déploiement

**Commandes**:
```bash
# Test ingestion lai_weekly_v6
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v6

# Vérifier dates dans output
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v6/2026/01/27/items.json . \
  --profile rag-lai-prod

# Analyser dates extraites
python scripts/analyze_dates.py items.json
```

---

## PHASE 5: RETOUR USER

### 5.1 Validation métier

**Critères de succès**:
- ✅ Items avec vraies dates de publication (pas 2026-01-27)
- ✅ Filtre temporel efficace (items >30 jours exclus)
- ✅ Newsletter affiche dates réelles
- ✅ Traçabilité avec `date_source` dans logs

**Métriques attendues**:
```
Extraction dates:
- RSS parsed: 60%
- Content extraction: 30%
- Ingestion fallback: 10%

Filtre temporel (30 jours):
- Items conservés: ~8-12 (vs 18 actuellement)
- Items filtrés: ~6-10 (anciens novembre/décembre)
```

### 5.2 Newsletter améliorée

**Avant (problématique)**:
```markdown
### MedinCell + Teva Olanzapine NDA
**Date:** Jan 27, 2026  # Date d'ingestion
```

**Après (corrigé)**:
```markdown
### MedinCell + Teva Olanzapine NDA
**Date:** Dec 09, 2025  # Vraie date de publication
```

### 5.3 Monitoring

**Alertes à configurer**:
- Taux de dates fallback >20%
- Échec extraction dates sur sources principales
- Items filtrés >80% (signe de problème temporel)

**Dashboard CloudWatch**:
- Métrique `DateExtractionSuccess` par source
- Métrique `TemporalFilterEfficiency`
- Logs avec `date_source` pour debugging

---

## IMPACT ET BÉNÉFICES

### Bénéfices utilisateur

1. **Chronologie réelle**: Newsletter respecte l'ordre temporel des événements
2. **Filtre efficace**: Période de 30 jours respectée (vs news de novembre actuellement)
3. **Traçabilité**: Distinction claire entre date publication et date ingestion

### Bénéfices technique

1. **Performance**: Filtre temporel réduit le volume traité (~50% d'items en moins)
2. **Qualité**: Extraction intelligente avec fallback gracieux
3. **Maintenabilité**: Patterns configurables par source

### Risques maîtrisés

1. **Compatibilité**: Aucun changement de format S3 ou API
2. **Fallback**: Date d'ingestion conservée si extraction impossible
3. **Performance**: Patterns regex optimisés, pas d'impact significatif

---

## CONCLUSION

Ce plan correctif résout le problème de parsing des dates de manière minimale et efficace, en respectant l'architecture V2 existante et les règles de développement vectora-inbox.

**Prochaines étapes**:
1. Implémenter correctifs Phase 2
2. Valider tests locaux Phase 3
3. Déployer Phase 4
4. Monitorer retour user Phase 5

**Durée estimée**: 2-3 jours de développement + tests
**Impact**: Amélioration significative de la qualité des newsletters sans risque architectural