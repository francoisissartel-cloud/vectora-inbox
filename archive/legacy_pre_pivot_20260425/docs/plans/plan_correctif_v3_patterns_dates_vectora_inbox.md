# Plan Correctif v3 - Amélioration Patterns Dates Vectora Inbox

**Date**: 2026-01-29  
**Objectif**: Corriger l'extraction de dates en améliorant les patterns regex et le nettoyage du contenu  
**Architecture**: Lambda ingest-v2 (src_v2/)  
**Client de référence**: lai_weekly_v6  

---

## DIAGNOSTIC APPROFONDI

### Problème identifié

**Symptôme**: Les patterns de dates ne matchent pas dans le contenu réel

**Test réel effectué** (2026-01-29 post-déploiement layer 36):
- 23 items ingérés
- 0 items avec vraie date extraite (0%)
- 23 items avec date fallback (100%)

**Exemples de dates présentes mais non matchées**:
```
Source                | Contenu                                    | Pattern attendu
----------------------|--------------------------------------------|-----------------
Nanexa                | "PRESSRELEASES27 January, 2026Nanexa..."  | "27 January, 2026"
MedinCell             | "...Q2 2026January 28, 2026January..."    | "January 28, 2026"
Camurus               | "202609 January 2026RegulatoryCamurus..." | "09 January 2026"
```

### Analyse technique - Cause racine

**Problème 1: Patterns regex trop stricts**

Pattern actuel:
```python
r'(\d{1,2}\s+(?:January|...|December)\s*,?\s*\d{4})'
```

Ce pattern nécessite:
- Un chiffre précédé d'un espace ou début de chaîne
- Mais dans "PRESSRELEASES27" il n'y a PAS d'espace avant "27"

**Problème 2: Contenu HTML mal nettoyé**

Le contenu HTML est nettoyé avec `get_text(strip=True)` qui:
- Supprime les balises HTML
- Mais ne garantit PAS d'espaces entre les éléments
- Résultat: "PRESSRELEASES27" au lieu de "PRESSRELEASES 27"

**Problème 3: Sources RSS non testées**

Les sources RSS (FiercePharma, FierceBiotech) devraient avoir `published_parsed`:
- Mais `published_at = 2026-01-29` (fallback)
- Cela suggère que `published_parsed` est vide ou non traité

### Impact métier

**Actuel**:
- 0% de vraies dates extraites
- Filtre temporel inefficace (0% filtré)
- Chronologie perdue
- Items anciens (novembre 2025) traités comme récents

**Attendu**:
- >70% de vraies dates extraites
- >20% d'items filtrés par le filtre temporel
- Chronologie respectée

---

## PHASE 1: CADRAGE

### 1.1 Objectifs

**Objectif principal**: Améliorer l'extraction de dates pour atteindre >70% de succès

**Objectifs spécifiques**:
1. Améliorer les patterns regex pour matcher sans espace avant
2. Améliorer le nettoyage HTML pour ajouter des espaces
3. Vérifier l'extraction RSS avec feedparser
4. Valider avec données réelles

### 1.2 Périmètre

**Dans le périmètre**:
- ✅ Amélioration patterns regex (word boundaries)
- ✅ Amélioration nettoyage HTML (espaces entre éléments)
- ✅ Logging détaillé pour debugging
- ✅ Test avec vraies données lai_weekly_v6

**Hors périmètre**:
- ❌ Modification architecture
- ❌ Changement format stockage
- ❌ Réingestion historique

### 1.3 Contraintes

**Techniques**:
- Respecter architecture src_v2/ existante
- Maintenir compatibilité
- Préserver performance (<30s par source)

**Métier**:
- Fallback sur date d'ingestion si extraction impossible
- Conserver `ingested_at` pour traçabilité

---

## PHASE 2: CORRECTIFS

### 2.1 Correctif 1: Améliorer patterns regex

**Fichier**: `src_v2/vectora_core/ingest/content_parser.py`

**Fonction**: `extract_real_publication_date()` (ligne ~434)

**Modification**:
```python
# Patterns par défaut si non configurés
if not date_patterns:
    date_patterns = [
        # Ajouter \b (word boundary) pour matcher même sans espace avant
        r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})\b',
        r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s*,?\s*\d{4})\b',
        r'\b(\d{2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}/\d{1,2}/\d{4})'
    ]
```

**Impact**: Les patterns matcheront "PRESSRELEASES27 January, 2026" car `\b` détecte la frontière entre "S" et "2".

### 2.2 Correctif 2: Améliorer nettoyage HTML

**Fichier**: `src_v2/vectora_core/ingest/content_parser.py`

**Fonction**: `_clean_html_content()` (ligne ~708)

**Modification**:
```python
def _clean_html_content(content: str) -> str:
    """
    Nettoie le contenu HTML en supprimant les balises et en ajoutant des espaces.
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        # Utiliser separator=' ' pour garantir des espaces entre éléments
        return soup.get_text(separator=' ', strip=True)
    except ImportError:
        import re
        # Remplacer balises par espaces (pas juste supprimer)
        clean = re.sub('<[^<]+?>', ' ', content)
        # Normaliser espaces multiples
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    except Exception:
        return content.strip()
```

**Impact**: "PRESSRELEASES27" deviendra "PRESSRELEASES 27" avec un espace.

### 2.3 Correctif 3: Logging détaillé

**Fichier**: `src_v2/vectora_core/ingest/content_parser.py`

**Fonction**: `extract_real_publication_date()` (ligne ~379)

**Modification**:
```python
# Après chaque tentative d'extraction, logger le résultat
logger.debug(f"Attempting date extraction for: {title_preview}")
logger.debug(f"Content sample: {content[:100]}")
logger.debug(f"Patterns to try: {len(date_patterns)}")

# Dans la boucle de patterns
for i, pattern in enumerate(date_patterns):
    matches = re.findall(pattern, content, re.IGNORECASE)
    if matches:
        logger.debug(f"Pattern {i} matched: {matches[:3]}")
    # ...
```

**Impact**: Meilleure observabilité pour debugging.

---

## PHASE 3: TESTS LOCAUX AVEC DONNÉES RÉELLES

### 3.1 Test unitaire patterns

**Script**: `tests/unit/test_date_patterns.py`

```python
"""Test patterns de dates avec exemples réels"""
import re

def test_date_patterns_real_content():
    """Test avec contenu réel problématique"""
    
    # Exemples réels
    test_cases = [
        ("PRESSRELEASES27 January, 2026Nanexa", "2026-01-27"),
        ("Q2 2026January 28, 2026January", "2026-01-28"),
        ("202609 January 2026RegulatoryCamurus", "2026-01-09"),
        ("December 9, 2025December", "2025-12-09"),
    ]
    
    pattern = r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})\b'
    
    for content, expected_date in test_cases:
        matches = re.findall(pattern, content, re.IGNORECASE)
        assert len(matches) > 0, f"No match for: {content}"
        print(f"[OK] {content[:30]}... -> {matches[0]}")
```

### 3.2 Test avec données S3

**Script**: `tests/integration/test_date_extraction_v3.py`

```python
"""Test extraction dates après correctifs v3"""
import boto3
import json

def test_date_extraction_v3():
    """Télécharge items et vérifie extraction"""
    
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    # Télécharger items post-déploiement
    response = s3.get_object(
        Bucket='vectora-inbox-data-dev',
        Key='ingested/lai_weekly_v6/2026/01/29/items.json'
    )
    items = json.loads(response['Body'].read())
    
    # Analyser
    real_dates = sum(1 for i in items if i['published_at'] != i['ingested_at'][:10])
    
    print(f"Vraies dates: {real_dates}/{len(items)} ({real_dates*100//len(items)}%)")
    
    # Objectif: >70%
    assert real_dates > len(items) * 0.7
```

---

## PHASE 4: DÉPLOIEMENT AWS

### 4.1 Créer nouveau layer

```bash
cd src_v2
powershell -Command "Compress-Archive -Path vectora_core -DestinationPath ../vectora-core-v3-date-patterns.zip -Force"

aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://vectora-core-v3-date-patterns.zip \
  --compatible-runtimes python3.11 python3.12 \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --description "Correctif v3 patterns dates - word boundaries + nettoyage HTML"
```

### 4.2 Mettre à jour Lambda

```bash
# Noter le numéro de version (ex: 37)
aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:4 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:37 \
  --region eu-west-3 \
  --profile rag-lai-prod

aws lambda wait function-updated \
  --function-name vectora-inbox-ingest-v2-dev \
  --region eu-west-3 \
  --profile rag-lai-prod
```

### 4.3 Test déploiement

```bash
# Invoquer Lambda
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload file://event_ingest_date_fix_test.json \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_v3.json

# Valider résultats
python scripts/validate_date_fix.py
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
Sources HTML avec dates     | 0%     | >60%   | [À mesurer]
Sources RSS avec dates      | 0%     | >90%   | [À mesurer]
```

**Filtre temporel**:
```
Métrique                    | Avant  | Cible  | Mesure
----------------------------|--------|--------|--------
Items filtrés (>30j)        | 0%     | >20%   | [À mesurer]
Efficacité filtre           | 0%     | >50%   | [À mesurer]
```

### 5.2 Validation newsletter

**Avant**:
```markdown
### Nanexa Semaglutide
**Date:** Jan 29, 2026  # Fallback
```

**Après**:
```markdown
### Nanexa Semaglutide
**Date:** Jan 27, 2026  # Vraie date
```

### 5.3 Script de validation

**Script**: `scripts/validate_date_fix_v3.py`

```python
"""Validation correctif v3"""
import boto3
import json
from datetime import datetime, timedelta

def validate_v3():
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    response = s3.get_object(
        Bucket='vectora-inbox-data-dev',
        Key='ingested/lai_weekly_v6/2026/01/29/items.json'
    )
    items = json.loads(response['Body'].read())
    
    # Métriques
    fallback = sum(1 for i in items if i['published_at'] == i['ingested_at'][:10])
    real_dates = len(items) - fallback
    
    # Par source
    by_source = {}
    for item in items:
        src = item['source_key']
        if src not in by_source:
            by_source[src] = {'total': 0, 'real': 0}
        by_source[src]['total'] += 1
        if item['published_at'] != item['ingested_at'][:10]:
            by_source[src]['real'] += 1
    
    print(f"\n{'='*70}")
    print(f"VALIDATION CORRECTIF V3")
    print(f"{'='*70}\n")
    print(f"Global: {real_dates}/{len(items)} ({real_dates*100//len(items)}%)\n")
    
    for src, stats in sorted(by_source.items()):
        pct = stats['real']*100//stats['total'] if stats['total'] else 0
        print(f"  {src[:30]:30} {stats['real']}/{stats['total']} ({pct}%)")
    
    success = real_dates > len(items) * 0.7
    print(f"\n{'='*70}")
    print(f"{'[SUCCES]' if success else '[ECHEC]'} {real_dates}/{len(items)} vraies dates")
    print(f"{'='*70}\n")
    
    return success
```

---

## IMPACT ET BÉNÉFICES

### Bénéfices utilisateur

1. **Chronologie réelle**: Dates de publication correctes dans la newsletter
2. **Filtre efficace**: Items anciens (>30j) correctement filtrés
3. **Qualité**: Seules les news récentes affichées

### Bénéfices technique

1. **Robustesse**: Patterns avec word boundaries plus flexibles
2. **Qualité**: Nettoyage HTML amélioré avec espaces
3. **Observabilité**: Logging détaillé pour debugging

### Risques maîtrisés

1. **Compatibilité**: Aucun changement de format
2. **Fallback**: Date d'ingestion conservée si échec
3. **Performance**: Impact minimal (<1s par source)
4. **Rollback**: Layer précédent conservé

---

## CONCLUSION

Ce plan correctif v3 résout le problème de matching des patterns en:
1. Ajoutant `\b` (word boundaries) aux patterns regex
2. Améliorant le nettoyage HTML avec `separator=' '`
3. Ajoutant du logging détaillé

**Prochaines étapes**:
1. Implémenter correctifs Phase 2
2. Tester localement Phase 3
3. Déployer Phase 4
4. Valider métriques Phase 5

**Durée estimée**: 2-3 heures (développement + tests + déploiement)
**Impact**: Amélioration de 0% à >70% d'extraction de vraies dates
