# Plan Correctif v2 - Parsing Dates Réelles Vectora Inbox

**Date**: 2026-01-29  
**Objectif**: Extraire et utiliser les dates réelles de publication dans les newsletters  
**Architecture**: 3 Lambdas V2 (src_v2/)  
**Client de référence**: lai_weekly_v6  

---

## DIAGNOSTIC APPROFONDI

### Problème identifié

**Symptôme**: 100% des items ont `published_at = date_ingestion` au lieu de leur vraie date

**Test réel effectué** (2026-01-29):
- 23 items ingérés
- 23 items avec date fallback (100%)
- 0 items avec vraie date extraite (0%)

**Exemples de dates présentes dans le contenu mais non extraites**:
```
Source                | Date dans contenu           | published_at actuel
----------------------|----------------------------|--------------------
MedinCell NDA         | "December 9, 2025"         | 2026-01-29
MedinCell Grant       | "November 24, 2025"        | 2026-01-29
Nanexa Semaglutide    | "27 January, 2026"         | 2026-01-29
Camurus Oclaiz        | "09 January 2026"          | 2026-01-29
```

### Analyse technique - Cause racine

**Problème 1: Configuration source non transmise au parser**

Flux actuel:
```
run_ingest_for_client()
  └─> content_parser.parse_source_content(raw_content, source_meta)
       └─> _parse_html_content(content_text, source_key, source_type, source_meta, ...)
            └─> _extract_item_from_element(element, source_key, source_type, source_meta, ...)
                 └─> extract_real_publication_date(pseudo_entry, source_meta)
```

**Issue**: `source_meta` passé à `parse_source_content()` contient:
- `source_key`, `source_type`, `homepage_url`, `rss_url`, `html_url`
- `ingestion_mode`, `enabled`, `tags`

**Mais NE contient PAS**:
- `date_extraction_patterns` (présents dans `source_catalog.yaml`)
- `content_enrichment`, `max_content_length`

**Problème 2: Patterns non chargés depuis source_catalog**

Dans `run_ingest_for_client()`:
```python
source_catalog = config_loader.load_source_catalog(config_bucket)
resolved_sources = config_loader.resolve_sources_for_client(
    client_config, source_catalog, sources
)
```

La fonction `resolve_sources_for_client()` ne copie pas tous les champs de `source_catalog` vers `resolved_sources`.

**Problème 3: Extraction RSS non testée**

Les sources RSS (FiercePharma, FierceBiotech) utilisent `_parse_rss_content()` qui appelle:
```python
published_at = _extract_published_date_with_config(entry, source_meta)
```

Cette fonction appelle `extract_real_publication_date()` mais avec un objet `entry` feedparser qui a des attributs (pas un dict).

### Impact métier

**Actuel**:
- Newsletter affiche dates d'ingestion (2026-01-29)
- Filtre temporel 30 jours inefficace (conserve tout)
- Chronologie réelle perdue
- Items anciens (novembre 2025) traités comme récents

**Attendu**:
- Newsletter affiche dates réelles (2025-12-09, 2026-01-27, etc.)
- Filtre temporel efficace (~50% items filtrés)
- Chronologie respectée
- Seuls items récents traités

---

## PHASE 1: CADRAGE

### 1.1 Objectifs

**Objectif principal**: Extraire et afficher les dates réelles de publication dans les newsletters

**Objectifs spécifiques**:
1. Transmettre `date_extraction_patterns` depuis `source_catalog` jusqu'au parser
2. Corriger extraction dates RSS (champs feedparser)
3. Corriger extraction dates HTML (patterns regex)
4. Valider avec données réelles (pas de simulation)
5. Mesurer l'impact sur le filtre temporel

### 1.2 Périmètre

**Dans le périmètre**:
- ✅ Modification `config_loader.resolve_sources_for_client()` pour copier patterns
- ✅ Correction `extract_real_publication_date()` pour gérer objets feedparser
- ✅ Test avec vraies données lai_weekly_v6
- ✅ Validation filtre temporel avec vraies dates
- ✅ Déploiement Lambda layer + test E2E

**Hors périmètre**:
- ❌ Modification architecture 3 Lambdas
- ❌ Changement format stockage S3
- ❌ Réingestion historique

### 1.3 Contraintes

**Techniques**:
- Respecter architecture src_v2/ existante
- Maintenir compatibilité avec tous les clients
- Préserver performance (<30s par source)

**Métier**:
- Fallback sur date d'ingestion si extraction impossible
- Conserver `ingested_at` pour traçabilité
- Priorité: RSS > contenu > fallback

---

## PHASE 2: CORRECTIFS

### 2.1 Correctif 1: Transmettre patterns au parser

**Fichier**: `src_v2/vectora_core/shared/config_loader.py`

**Fonction**: `resolve_sources_for_client()`

**Modification**:
```python
def resolve_sources_for_client(
    client_config: Dict[str, Any],
    source_catalog: Dict[str, Any],
    sources_filter: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Résout les sources à traiter pour un client.
    COPIE TOUS LES CHAMPS depuis source_catalog vers resolved_sources.
    """
    # ... code existant ...
    
    # Pour chaque source résolue, copier TOUS les champs du catalog
    resolved_sources = []
    for source_key in unique_sources:
        source_def = next((s for s in catalog_sources if s['source_key'] == source_key), None)
        if source_def:
            # Copier TOUS les champs (pas seulement les basiques)
            resolved_sources.append(source_def.copy())
        else:
            logger.warning(f"Source {source_key} non trouvée dans catalog")
    
    return resolved_sources
```

**Impact**: Les patterns `date_extraction_patterns` seront disponibles dans `source_meta`.

### 2.2 Correctif 2: Gérer objets feedparser

**Fichier**: `src_v2/vectora_core/ingest/content_parser.py`

**Fonction**: `extract_real_publication_date()`

**Modification**:
```python
def extract_real_publication_date(item_data: Any, source_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extraction intelligente de la date de publication.
    Gère à la fois les objets feedparser ET les dicts.
    """
    import re
    
    # Priorité 1: Champs RSS standards - published_parsed
    if hasattr(item_data, 'published_parsed') and item_data.published_parsed:
        try:
            dt = datetime(*item_data.published_parsed[:6])
            return {
                'date': dt.strftime('%Y-%m-%d'),
                'date_source': 'rss_parsed'
            }
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse published_parsed: {e}")
    
    # Priorité 1b: Champ pubDate/published string
    published_str = None
    if hasattr(item_data, 'published'):
        published_str = item_data.published
    elif isinstance(item_data, dict) and 'published' in item_data:
        published_str = item_data['published']
    
    if published_str:
        parsed_date = _parse_date_string(published_str)
        if parsed_date:
            return {
                'date': parsed_date,
                'date_source': 'rss_pubdate'
            }
    
    # Priorité 2: Extraction contenu avec patterns source
    content = ''
    if hasattr(item_data, 'content'):
        content = str(item_data.content)
    elif isinstance(item_data, dict):
        content = str(item_data.get('content', ''))
    
    if hasattr(item_data, 'title'):
        content += ' ' + str(item_data.title)
    elif isinstance(item_data, dict):
        content += ' ' + str(item_data.get('title', ''))
    
    if hasattr(item_data, 'summary'):
        content += ' ' + str(item_data.summary)
    elif isinstance(item_data, dict):
        content += ' ' + str(item_data.get('summary', ''))
    
    date_patterns = source_config.get('date_extraction_patterns', [])
    
    # Patterns par défaut si non configurés
    if not date_patterns:
        date_patterns = [
            r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})',
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s*,?\s*\d{4})',
            r'(\d{2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
        ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            parsed_date = _parse_date_string(match)
            if parsed_date:
                logger.info(f"Date extracted from content: {parsed_date}")
                return {
                    'date': parsed_date,
                    'date_source': 'content_extraction'
                }
    
    # Priorité 3: Fallback avec flag
    title_preview = ''
    if hasattr(item_data, 'title'):
        title_preview = str(item_data.title)[:50]
    elif isinstance(item_data, dict):
        title_preview = str(item_data.get('title', ''))[:50]
    
    logger.warning(f"No date found, using ingestion fallback for: {title_preview}...")
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'date_source': 'ingestion_fallback'
    }
```

### 2.3 Correctif 3: Améliorer _parse_date_string

**Déjà implémenté dans le correctif précédent** - formats étendus ajoutés.

### 2.4 Correctif 4: Logging détaillé

**Déjà implémenté dans le correctif précédent** - logging dans `apply_temporal_filter()`.

---

## PHASE 3: TESTS LOCAUX AVEC DONNÉES RÉELLES

### 3.1 Test avec données réelles S3

**Script**: `tests/integration/test_real_date_extraction.py`

```python
"""
Test extraction dates avec vraies données S3
"""
import boto3
import json

def test_real_date_extraction():
    """Télécharge items réels et vérifie extraction dates"""
    
    # Télécharger items ingérés récents
    s3 = boto3.client('s3', region_name='eu-west-3')
    response = s3.get_object(
        Bucket='vectora-inbox-data-dev',
        Key='ingested/lai_weekly_v6/2026/01/29/items.json'
    )
    items = json.loads(response['Body'].read())
    
    print(f"\nAnalyse {len(items)} items réels")
    
    # Analyser les dates
    fallback_count = 0
    real_date_count = 0
    
    for item in items:
        published_at = item.get('published_at')
        ingested_at = item.get('ingested_at', '')[:10]
        
        if published_at == ingested_at:
            fallback_count += 1
        else:
            real_date_count += 1
            print(f"  [OK] {item['title'][:50]}... -> {published_at}")
    
    print(f"\nRésultats:")
    print(f"  Vraies dates: {real_date_count}/{len(items)} ({real_date_count*100//len(items)}%)")
    print(f"  Dates fallback: {fallback_count}/{len(items)} ({fallback_count*100//len(items)}%)")
    
    # Objectif: >70% vraies dates
    assert real_date_count > len(items) * 0.7, f"Trop de fallback: {fallback_count}/{len(items)}"

if __name__ == '__main__':
    test_real_date_extraction()
```

### 3.2 Test filtre temporel avec vraies données

**Script**: `tests/integration/test_temporal_filter_real.py`

```python
"""
Test filtre temporel avec vraies données
"""
import boto3
import json
from datetime import datetime, timedelta

def test_temporal_filter_real():
    """Vérifie que le filtre temporel fonctionne avec vraies dates"""
    
    # Télécharger items
    s3 = boto3.client('s3', region_name='eu-west-3')
    response = s3.get_object(
        Bucket='vectora-inbox-data-dev',
        Key='ingested/lai_weekly_v6/2026/01/29/items.json'
    )
    items = json.loads(response['Body'].read())
    
    # Calculer cutoff (30 jours)
    cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # Compter items avant/après cutoff
    recent = [i for i in items if i.get('published_at', '') >= cutoff_date]
    old = [i for i in items if i.get('published_at', '') < cutoff_date]
    
    print(f"\nFiltre temporel (cutoff: {cutoff_date}):")
    print(f"  Items récents: {len(recent)}")
    print(f"  Items anciens: {len(old)}")
    
    # Objectif: au moins 20% d'items filtrés
    filter_rate = len(old) / len(items) if items else 0
    print(f"  Taux filtrage: {filter_rate*100:.0f}%")
    
    assert filter_rate > 0.2, f"Filtre inefficace: seulement {filter_rate*100:.0f}% filtrés"

if __name__ == '__main__':
    test_temporal_filter_real()
```

### 3.3 Commandes de test

```bash
# Test extraction dates
python tests/integration/test_real_date_extraction.py

# Test filtre temporel
python tests/integration/test_temporal_filter_real.py
```

---

## PHASE 4: DÉPLOIEMENT AWS

### 4.1 Mise à jour code

**Commandes**:
```bash
# 1. Créer layer avec correctifs
cd src_v2
powershell -Command "Compress-Archive -Path vectora_core -DestinationPath ../vectora-core-v2-fixed.zip -Force"

# 2. Publier layer
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://../vectora-core-v2-fixed.zip \
  --compatible-runtimes python3.11 python3.12 \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --description "Correctif v2 parsing dates - transmission patterns + gestion feedparser"

# 3. Noter le numéro de version (ex: 36)
```

### 4.2 Mise à jour Lambda

```bash
# Mettre à jour ingest-v2 avec nouveau layer
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:4 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:36 \
  --region eu-west-3 \
  --profile rag-lai-prod

# Attendre mise à jour
aws lambda wait function-updated \
  --function-name vectora-inbox-ingest-v2-dev \
  --region eu-west-3 \
  --profile rag-lai-prod
```

### 4.3 Test déploiement

```bash
# Test ingestion lai_weekly_v6
python scripts/test_ingest_date_fix.py

# Télécharger résultat
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v6/[DATE]/items.json items_post_fix.json --profile rag-lai-prod

# Analyser dates
python scripts/analyze_dates_fix.py
```

---

## PHASE 5: RETOUR USERS & MÉTRIQUES

### 5.1 Métriques de succès

**Extraction dates**:
```
Métrique                    | Avant  | Cible  | Mesure
----------------------------|--------|--------|--------
Vraies dates extraites      | 0%     | >70%   | [À mesurer]
Dates fallback              | 100%   | <30%   | [À mesurer]
Sources RSS avec dates      | 0%     | >90%   | [À mesurer]
Sources HTML avec dates     | 0%     | >60%   | [À mesurer]
```

**Filtre temporel**:
```
Métrique                    | Avant  | Cible  | Mesure
----------------------------|--------|--------|--------
Items filtrés (>30j)        | 0%     | >20%   | [À mesurer]
Items conservés             | 100%   | <80%   | [À mesurer]
Efficacité filtre           | 0%     | >50%   | [À mesurer]
```

**Performance**:
```
Métrique                    | Avant  | Cible  | Mesure
----------------------------|--------|--------|--------
Temps ingestion/source      | ~2s    | <3s    | [À mesurer]
Temps total ingestion       | ~15s   | <20s   | [À mesurer]
```

### 5.2 Validation newsletter

**Avant (problématique)**:
```markdown
### MedinCell + Teva Olanzapine NDA
**Date:** Jan 29, 2026  # Date d'ingestion
```

**Après (corrigé)**:
```markdown
### MedinCell + Teva Olanzapine NDA
**Date:** Dec 09, 2025  # Vraie date de publication
```

### 5.3 Script de validation

**Script**: `scripts/validate_date_fix.py`

```python
"""
Validation complète du correctif dates
"""
import boto3
import json
from datetime import datetime, timedelta

def validate_date_fix():
    """Valide que le correctif fonctionne"""
    
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    # Télécharger items
    response = s3.get_object(
        Bucket='vectora-inbox-data-dev',
        Key='ingested/lai_weekly_v6/2026/01/29/items.json'
    )
    items = json.loads(response['Body'].read())
    
    print(f"\n{'='*70}")
    print(f"VALIDATION CORRECTIF PARSING DATES")
    print(f"{'='*70}\n")
    
    # Métriques extraction
    fallback = sum(1 for i in items if i.get('published_at') == i.get('ingested_at', '')[:10])
    real_dates = len(items) - fallback
    
    print(f"Extraction dates:")
    print(f"  Total items: {len(items)}")
    print(f"  Vraies dates: {real_dates} ({real_dates*100//len(items)}%)")
    print(f"  Dates fallback: {fallback} ({fallback*100//len(items)}%)")
    print(f"  Statut: {'[OK]' if real_dates > len(items)*0.7 else '[ECHEC]'}")
    
    # Métriques filtre temporel
    cutoff = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    old_items = [i for i in items if i.get('published_at', '') < cutoff]
    
    print(f"\nFiltre temporel:")
    print(f"  Cutoff (30j): {cutoff}")
    print(f"  Items anciens: {len(old_items)} ({len(old_items)*100//len(items)}%)")
    print(f"  Statut: {'[OK]' if len(old_items) > len(items)*0.2 else '[ECHEC]'}")
    
    # Exemples
    print(f"\nExemples dates extraites:")
    for item in items[:5]:
        if item.get('published_at') != item.get('ingested_at', '')[:10]:
            print(f"  - {item['title'][:50]}... -> {item['published_at']}")
    
    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    validate_date_fix()
```

### 5.4 Monitoring CloudWatch

**Métriques à surveiller**:
- `DateExtractionSuccess` par source
- `DateFallbackRate` global
- `TemporalFilterEfficiency`
- `IngestionDuration` par source

**Alarmes**:
- Taux fallback >40% pendant 2 runs consécutifs
- Échec extraction sur sources principales
- Dégradation performance >50%

---

## IMPACT ET BÉNÉFICES

### Bénéfices utilisateur

1. **Chronologie réelle**: Newsletter respecte l'ordre temporel des événements
2. **Filtre efficace**: Période de 30 jours respectée
3. **Traçabilité**: Distinction claire entre date publication et date ingestion
4. **Qualité**: Seules les news récentes dans la newsletter

### Bénéfices technique

1. **Performance**: Filtre temporel réduit le volume traité (~30-50%)
2. **Qualité**: Extraction intelligente avec fallback gracieux
3. **Maintenabilité**: Patterns configurables par source
4. **Observabilité**: Logging détaillé avec source de date

### Risques maîtrisés

1. **Compatibilité**: Aucun changement de format S3 ou API
2. **Fallback**: Date d'ingestion conservée si extraction impossible
3. **Performance**: Impact minimal (<1s par source)
4. **Rollback**: Layer précédent conservé pour rollback rapide

---

## CONCLUSION

Ce plan correctif v2 résout le problème de parsing des dates en corrigeant la cause racine : la non-transmission des `date_extraction_patterns` depuis `source_catalog` jusqu'au parser.

**Prochaines étapes**:
1. Implémenter correctifs Phase 2
2. Tester avec données réelles Phase 3
3. Déployer Phase 4
4. Valider métriques Phase 5

**Durée estimée**: 1 jour de développement + tests + déploiement
**Impact**: Amélioration significative de la qualité des newsletters avec dates réelles
