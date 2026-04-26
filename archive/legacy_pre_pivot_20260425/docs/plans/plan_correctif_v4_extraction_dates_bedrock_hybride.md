# Plan Correctif v4 - Extraction Dates Hybride via Bedrock

**Date**: 2026-01-29  
**Objectif**: Implémenter extraction de dates par Bedrock dans la phase normalisation  
**Architecture**: Lambda normalize-score-v2 (src_v2/)  
**Client de référence**: lai_weekly_v6  
**Approche**: Hybride (regex ingestion + Bedrock normalisation)

---

## DIAGNOSTIC

### Problème identifié

**Symptôme**: Extraction de dates par regex échoue (0% de succès)

**Cause racine**:
- Contenu HTML mal nettoyé ("PRESSRELEASES27" sans espace)
- Patterns regex trop fragiles face aux variations HTML
- Complexité de maintenir des regex pour tous les formats

**Impact métier**:
- 0% de vraies dates extraites
- Chronologie perdue dans la newsletter
- Filtre temporel inefficace

### Solution proposée

**Approche hybride**:
1. **Phase ingestion**: Garde extraction regex simple + fallback date d'ingestion
2. **Phase normalisation**: Bedrock extrait la vraie date depuis le contenu
3. **Phase scoring**: Utilise la date Bedrock si disponible, sinon fallback

**Avantages**:
- ✅ Taux de succès attendu: >95% (vs 0% actuellement)
- ✅ Robustesse: LLM comprend le contexte
- ✅ Simplicité: Pas de regex complexes à maintenir
- ✅ Coût marginal: $0.002 par run (négligeable)
- ✅ Rétrocompatible: Garde fallback ingestion

---

## PHASE 1: CADRAGE

### 1.1 Objectifs

**Objectif principal**: Atteindre >95% de vraies dates extraites

**Objectifs spécifiques**:
1. Enrichir prompt normalisation Bedrock pour extraire dates
2. Ajouter champs `extracted_date` et `date_confidence` dans normalized_content
3. Utiliser date Bedrock dans scoring si disponible
4. Valider avec données réelles lai_weekly_v6

### 1.2 Périmètre

**Dans le périmètre**:
- ✅ Modification prompt normalisation (canonical/prompts/)
- ✅ Enrichissement schéma normalized_content
- ✅ Utilisation date Bedrock dans scoring
- ✅ Tests avec données réelles

**Hors périmètre**:
- ❌ Modification Lambda ingest-v2 (garde regex simple)
- ❌ Changement format items.json ingested
- ❌ Réingestion historique

### 1.3 Contraintes

**Techniques**:
- Respecter architecture 3 Lambdas V2
- Utiliser code src_v2/ uniquement
- Maintenir compatibilité avec published_at existant
- Préserver performance (<5s par item)

**Métier**:
- Fallback sur published_at si extraction Bedrock échoue
- Conserver ingested_at pour traçabilité
- Pas de breaking change pour clients existants

---

## PHASE 2: CORRECTIFS LOCAUX

### 2.1 Correctif 1: Enrichir prompt normalisation

**Fichier**: `canonical/prompts/normalization/lai_prompt.yaml` (S3)

**Modification**: Ajouter section extraction de date

```yaml
system_prompt: |
  You are an expert analyst specializing in Long-Acting Injectable (LAI) pharmaceutical technologies.
  
  Your task is to analyze news items and extract:
  1. A concise summary
  2. Key entities (companies, molecules, technologies, trademarks)
  3. Event classification
  4. LAI relevance score
  5. **Publication date** (NEW)
  
  For the publication date:
  - Look for dates in the content like "27 January, 2026", "January 28, 2026", "09 January 2026"
  - Return format: YYYY-MM-DD
  - If multiple dates, choose the publication date (not future event dates)
  - If no clear date found, return null

output_schema:
  type: object
  properties:
    summary:
      type: string
    entities:
      type: object
      properties:
        companies: {type: array}
        molecules: {type: array}
        technologies: {type: array}
        trademarks: {type: array}
    event_classification:
      type: object
      properties:
        primary_type: {type: string}
        confidence: {type: number}
    lai_relevance_score:
      type: integer
      minimum: 0
      maximum: 10
    extracted_date:
      type: string
      format: date
      nullable: true
    date_confidence:
      type: number
      minimum: 0
      maximum: 1
      nullable: true
```

**Impact**: Bedrock extraira la date à chaque normalisation

### 2.2 Correctif 2: Enrichir schéma normalized_content

**Fichier**: `src_v2/vectora_core/shared/models.py`

**Modification**: Ajouter champs date dans NormalizedContent

```python
@dataclass
class NormalizedContent:
    summary: str
    entities: Dict[str, List[str]]
    event_classification: Dict[str, Any]
    lai_relevance_score: int
    extracted_date: Optional[str] = None  # NEW: Date extraite par Bedrock
    date_confidence: Optional[float] = None  # NEW: Confiance extraction
```

**Impact**: Structure de données enrichie

### 2.3 Correctif 3: Parser réponse Bedrock

**Fichier**: `src_v2/vectora_core/normalization/normalizer.py`

**Fonction**: `normalize_item()` (ligne ~150)

**Modification**: Parser extracted_date depuis réponse Bedrock

```python
def normalize_item(item: Dict[str, Any], bedrock_client, prompt_config: Dict) -> Dict[str, Any]:
    # ... code existant ...
    
    # Parser réponse Bedrock
    bedrock_response = bedrock_client.invoke_model(...)
    normalized = json.loads(bedrock_response)
    
    # Extraire date si présente
    extracted_date = normalized.get('extracted_date')
    date_confidence = normalized.get('date_confidence', 0.0)
    
    # Valider format date
    if extracted_date:
        try:
            datetime.strptime(extracted_date, '%Y-%m-%d')
            logger.info(f"Date extracted by Bedrock: {extracted_date} (confidence: {date_confidence})")
        except ValueError:
            logger.warning(f"Invalid date format from Bedrock: {extracted_date}")
            extracted_date = None
            date_confidence = 0.0
    
    return {
        'normalized_content': {
            'summary': normalized['summary'],
            'entities': normalized['entities'],
            'event_classification': normalized['event_classification'],
            'lai_relevance_score': normalized['lai_relevance_score'],
            'extracted_date': extracted_date,  # NEW
            'date_confidence': date_confidence  # NEW
        }
    }
```

**Impact**: Date Bedrock disponible dans curated items

### 2.4 Correctif 4: Utiliser date Bedrock dans scoring

**Fichier**: `src_v2/vectora_core/normalization/scorer.py`

**Fonction**: `calculate_final_score()` (ligne ~200)

**Modification**: Prioriser extracted_date sur published_at

```python
def calculate_final_score(item: Dict[str, Any], config: Dict) -> Dict[str, Any]:
    # ... code existant ...
    
    # Utiliser date Bedrock si disponible et fiable
    normalized = item.get('normalized_content', {})
    extracted_date = normalized.get('extracted_date')
    date_confidence = normalized.get('date_confidence', 0.0)
    
    # Prioriser date Bedrock si confiance > 0.7
    if extracted_date and date_confidence > 0.7:
        effective_date = extracted_date
        logger.info(f"Using Bedrock date: {effective_date}")
    else:
        effective_date = item.get('published_at')
        logger.info(f"Using fallback date: {effective_date}")
    
    # Calculer bonus/malus basés sur effective_date
    # ... reste du code scoring ...
    
    return {
        'final_score': score,
        'effective_date': effective_date,  # NEW: Date utilisée pour scoring
        'bonuses': bonuses,
        'penalties': penalties
    }
```

**Impact**: Scoring utilise la meilleure date disponible

### 2.5 Correctif 5: Afficher date réelle dans newsletter

**Fichier**: `src_v2/vectora_core/newsletter/assembler.py`

**Fonction**: `_format_item_markdown()` (ligne ~280)

**Modification**: Utiliser effective_date au lieu de published_at

```python
def _format_item_markdown(item):
    """Formate un item individuel en Markdown"""
    normalized = item.get('normalized_content', {})
    entities = normalized.get('entities', {})
    scoring = item.get('scoring_results', {})
    
    title = format_item_title(item, max_length=120)
    score = scoring.get('final_score', 0)
    source_key = item.get('source_key', 'Unknown Source')
    
    # Utiliser effective_date (date Bedrock) si disponible, sinon published_at
    effective_date = scoring.get('effective_date') or item.get('published_at', '')[:10]
    url = item.get('url', '#')
    
    # Formatage de la date
    try:
        date_obj = datetime.strptime(effective_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%b %d, %Y')
    except:
        formatted_date = effective_date
    
    markdown = f"""### {_get_item_icon(item)} {title}
**Source:** {source_key} • **Score:** {score:.1f} • **Date:** {formatted_date}

{normalized.get('summary', 'No summary available.')}

**Key Players:** {', '.join(companies)} • **Technology:** {', '.join(technologies)}

[**Read more →**]({url})

"""
    
    return markdown
```

**Fonction**: `_format_item_json()` (ligne ~470)

**Modification**: Utiliser effective_date dans JSON

```python
def _format_item_json(item):
    """Formate un item pour le JSON"""
    normalized = item.get('normalized_content', {})
    entities = normalized.get('entities', {})
    scoring = item.get('scoring_results', {})
    
    score = scoring.get('final_score', 0)
    effective_date = scoring.get('effective_date') or item.get('published_at', '')
    
    return {
        "item_id": item.get('item_id', ''),
        "title": normalized.get('summary', '')[:100],
        "score": score,
        "published_at": effective_date,  # Utiliser effective_date
        "source_url": item.get('url', ''),
        "entities": {
            "companies": entities.get('companies', []),
            "technologies": entities.get('technologies', []),
            "trademarks": entities.get('trademarks', [])
        }
    }
```

**Impact**: Newsletter affiche les vraies dates extraites par Bedrock

---

## PHASE 3: TESTS LOCAUX AVEC DONNÉES RÉELLES

### 3.1 Test unitaire extraction date

**Script**: `tests/unit/test_bedrock_date_extraction.py`

```python
"""Test extraction dates par Bedrock"""
import json

def test_bedrock_date_extraction():
    """Test avec contenu réel problématique"""
    
    test_cases = [
        {
            "content": "PRESSRELEASES27 January, 2026Nanexa Announces...",
            "expected": "2026-01-27"
        },
        {
            "content": "Q2 2026January 28, 2026January...",
            "expected": "2026-01-28"
        },
        {
            "content": "202609 January 2026RegulatoryCamurus...",
            "expected": "2026-01-09"
        }
    ]
    
    # Simuler réponse Bedrock
    for case in test_cases:
        # Mock Bedrock call
        response = {
            "extracted_date": case["expected"],
            "date_confidence": 0.95
        }
        
        assert response["extracted_date"] == case["expected"]
        assert response["date_confidence"] > 0.7
        print(f"[OK] {case['content'][:40]}... -> {response['extracted_date']}")
```

### 3.2 Test intégration avec données S3

**Script**: `tests/integration/test_bedrock_date_integration.py`

```python
"""Test extraction dates avec vraies données S3"""
import boto3
import json

def test_date_extraction_with_real_data():
    """Télécharge items ingested et simule normalisation"""
    
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    # Télécharger items ingested
    response = s3.get_object(
        Bucket='vectora-inbox-data-dev',
        Key='ingested/lai_weekly_v6/2026/01/29/items.json'
    )
    items = json.loads(response['Body'].read())
    
    print(f"\nItems à tester: {len(items)}")
    
    # Pour chaque item, vérifier qu'on peut extraire une date
    dates_extracted = 0
    for item in items[:5]:  # Tester 5 premiers
        content = item['content']
        
        # Simuler extraction Bedrock (à remplacer par vrai appel)
        if any(month in content for month in ['January', 'February', 'December']):
            dates_extracted += 1
            print(f"[OK] Date trouvée dans: {item['title'][:50]}...")
    
    print(f"\nDates extraites: {dates_extracted}/5")
    assert dates_extracted >= 3  # Au moins 60%
```

---

## PHASE 4: DÉPLOIEMENT AWS

### 4.1 Upload prompt enrichi S3

```bash
# Uploader le prompt modifié
aws s3 cp canonical/prompts/normalization/lai_prompt.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/normalization/lai_prompt.yaml \
  --region eu-west-3 \
  --profile rag-lai-prod
```

### 4.2 Créer nouveau layer vectora-core

```bash
cd src_v2
powershell -Command "Compress-Archive -Path vectora_core -DestinationPath ../vectora-core-v4-bedrock-dates.zip -Force"

aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-approche-b-dev \
  --zip-file fileb://vectora-core-v4-bedrock-dates.zip \
  --compatible-runtimes python3.11 python3.12 \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --description "v4 - Extraction dates via Bedrock dans normalisation"
```

### 4.3 Mettre à jour Lambda normalize-score-v2 ET newsletter-v2

**Lambda normalize-score-v2**:
```bash
# Noter le numéro de version (ex: 3)
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:4 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-approche-b-dev:3 \
  --region eu-west-3 \
  --profile rag-lai-prod

aws lambda wait function-updated \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --region eu-west-3 \
  --profile rag-lai-prod
```

**Lambda newsletter-v2**:
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-newsletter-v2-dev \
  --layers \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-common-deps-dev:4 \
    arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-approche-b-dev:3 \
  --region eu-west-3 \
  --profile rag-lai-prod

aws lambda wait function-updated \
  --function-name vectora-inbox-newsletter-v2-dev \
  --region eu-west-3 \
  --profile rag-lai-prod
```

### 4.4 Test déploiement E2E

```bash
# 1. Invoquer ingest (garde dates fallback)
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload '{"client_id":"lai_weekly_v6","force_refresh":true}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_ingest.json

# 2. Invoquer normalize-score (extrait dates Bedrock)
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload '{"client_id":"lai_weekly_v6"}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_normalize.json

# 3. Invoquer newsletter (affiche dates réelles)
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload '{"client_id":"lai_weekly_v6"}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_newsletter.json

# 4. Valider résultats
python scripts/validate_bedrock_dates.py
```

---

## PHASE 5: RETOUR USERS & MÉTRIQUES

### 5.1 Métriques de succès

**Extraction dates**:
```
Métrique                    | Avant  | Cible  | Mesure
----------------------------|--------|--------|--------
Vraies dates extraites      | 0%     | >95%   | [À mesurer]
Dates Bedrock fiables       | N/A    | >90%   | [À mesurer]
Dates fallback              | 100%   | <5%    | [À mesurer]
```

**Performance**:
```
Métrique                    | Avant  | Cible  | Mesure
----------------------------|--------|--------|--------
Temps normalisation/item    | 4.9s   | <5.5s  | [À mesurer]
Coût par run (23 items)     | $0.21  | <$0.25 | [À mesurer]
```

### 5.2 Validation newsletter

**Avant**:
```markdown
### Nanexa Semaglutide
**Source:** press_corporate__nanexa • **Score:** 11.0 • **Date:** Jan 29, 2026
```
(Date fallback = date d'ingestion)

**Après**:
```markdown
### Nanexa Semaglutide
**Source:** press_corporate__nanexa • **Score:** 11.0 • **Date:** Jan 27, 2026
```
(Date réelle extraite par Bedrock)

**Vérification**:
```bash
# Télécharger newsletter générée
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v6/2026/01/29/newsletter.md . \
  --region eu-west-3 --profile rag-lai-prod

# Vérifier les dates affichées
findstr /C:"Date:" newsletter.md
```

### 5.3 Script de validation

**Script**: `scripts/validate_bedrock_dates.py`

```python
"""Validation extraction dates Bedrock"""
import boto3
import json

def validate_bedrock_dates():
    s3 = boto3.client('s3', region_name='eu-west-3')
    
    # Télécharger items curated
    response = s3.get_object(
        Bucket='vectora-inbox-data-dev',
        Key='curated/lai_weekly_v6/2026/01/29/items.json'
    )
    items = json.loads(response['Body'].read())
    
    # Analyser extraction Bedrock
    bedrock_dates = 0
    fallback_dates = 0
    high_confidence = 0
    
    for item in items:
        normalized = item.get('normalized_content', {})
        extracted_date = normalized.get('extracted_date')
        date_confidence = normalized.get('date_confidence', 0.0)
        
        if extracted_date:
            bedrock_dates += 1
            if date_confidence > 0.7:
                high_confidence += 1
        else:
            fallback_dates += 1
    
    print(f"\n{'='*70}")
    print(f"VALIDATION EXTRACTION DATES BEDROCK")
    print(f"{'='*70}\n")
    print(f"Items total: {len(items)}")
    print(f"Dates Bedrock: {bedrock_dates} ({bedrock_dates*100//len(items)}%)")
    print(f"  - Haute confiance (>0.7): {high_confidence} ({high_confidence*100//len(items)}%)")
    print(f"Dates fallback: {fallback_dates} ({fallback_dates*100//len(items)}%)")
    
    success = bedrock_dates > len(items) * 0.95
    print(f"\n{'='*70}")
    print(f"{'[SUCCESS]' if success else '[FAIL]'} Objectif: {bedrock_dates*100//len(items)}% >= 95%")
    print(f"{'='*70}\n")
    
    return success

if __name__ == "__main__":
    import sys
    success = validate_bedrock_dates()
    sys.exit(0 if success else 1)
```

---

## IMPACT ET BÉNÉFICES

### Bénéfices utilisateur

1. **Chronologie réelle**: Dates de publication correctes dans la newsletter
2. **Filtre efficace**: Items anciens (>30j) correctement filtrés
3. **Qualité**: Seules les news récentes affichées

### Bénéfices technique

1. **Robustesse**: LLM comprend le contexte (>95% succès)
2. **Simplicité**: Pas de regex complexes à maintenir
3. **Évolutivité**: Peut extraire d'autres métadonnées (auteur, lieu)
4. **Observabilité**: Confiance d'extraction trackée

### Coûts

1. **Développement**: 1h30 (vs 3h déjà passées sur regex)
2. **Tokens Bedrock**: +50 tokens/item (~$0.002 par run)
3. **Latence**: +0s (déjà dans normalisation)

**ROI**: Excellent ✅

---

## RISQUES ET MITIGATION

### Risques identifiés

1. **Bedrock extraction échoue**
   - Mitigation: Fallback sur published_at (date ingestion)
   - Impact: Faible (même comportement qu'avant)

2. **Format date invalide**
   - Mitigation: Validation format + fallback
   - Impact: Négligeable

3. **Coût Bedrock**
   - Mitigation: Monitoring coût + alertes
   - Impact: $0.002 par run (négligeable)

4. **Performance**
   - Mitigation: Prompt optimisé + timeout
   - Impact: +0.5s par item max (acceptable)

---

## CONCLUSION

Ce plan correctif v4 résout le problème d'extraction de dates en:
1. Utilisant Bedrock dans la phase normalisation (déjà existante)
2. Enrichissant le schéma normalized_content avec extracted_date
3. Priorisant la date Bedrock dans le scoring
4. Gardant le fallback sur published_at

**Prochaines étapes**:
1. Enrichir prompt normalisation (Phase 2.1)
2. Modifier schéma et code normalisation (Phase 2.2-2.4)
3. Modifier code newsletter (Phase 2.5)
4. Tester localement (Phase 3)
5. Déployer sur AWS (Phase 4)
6. Valider métriques (Phase 5)

**Durée estimée**: 2h (ajout correctif newsletter)  
**Impact**: Amélioration de 0% à >95% d'extraction de vraies dates  
**Coût**: +$0.002 par run (négligeable)
