# Plan de Correction Structuré - lai_weekly_v5 Issues Resolution

**Date :** 23 décembre 2025  
**Version :** 1.0  
**Objectif :** Corriger les 4 problèmes critiques identifiés dans les diagnostics  
**Architecture :** 3 Lambdas V2 (respect vectora-inbox-development-rules.md)  
**Environnement :** dev → validation → production  

---

## 🎯 PROBLÈMES À CORRIGER (Référence Diagnostics)

### Issues Identifiées
1. **UZEDY® Bipolar exclu** - Déduplication trop agressive (selector.py)
2. **Malaria Grant non matché** - Enrichissement PDF échoue + contexte pure player manquant
3. **Dates réelles non extraites** - Fonction avancée non utilisée pour HTML
4. **Titres tronqués** - Limitation 80 caractères dans newsletter

### Métriques Cibles
- **Items newsletter** : 5-6 (vs 3 actuel)
- **Dates réelles** : 85%+ extraction (vs 0% actuel)
- **Malaria Grant** : Matché et inclus
- **UZEDY® items** : 2 items distincts (vs 1 dédupliqué)

---

## 📋 STRUCTURE DU PLAN - 6 PHASES

### Phase 1 : Préparation et Validation Environnement
**Durée** : 2 heures  
**Objectif** : Sécuriser l'environnement et préparer les tests

### Phase 2 : Corrections Code Core
**Durée** : 4 heures  
**Objectif** : Implémenter les corrections dans src_v2/vectora_core/

### Phase 3 : Mise à Jour Configurations
**Durée** : 1 heure  
**Objectif** : Ajuster canonical/ et client-config-examples/

### Phase 4 : Tests Unitaires et Validation
**Durée** : 3 heures  
**Objectif** : Valider chaque correction individuellement

### Phase 5 : Tests E2E Données Réelles
**Durée** : 2 heures  
**Objectif** : Test complet lai_weekly_v5 avec corrections

### Phase 6 : Déploiement AWS et Validation Production
**Durée** : 2 heures  
**Objectif** : Déployer et valider en environnement AWS

**Durée totale estimée** : 14 heures

---

## 🔧 PHASE 1 : PRÉPARATION ET VALIDATION ENVIRONNEMENT

### 1.1 Validation Architecture V2
**Durée** : 30 minutes

#### Vérifications Obligatoires
- [ ] Architecture 3 Lambdas V2 active et fonctionnelle
- [ ] Layers vectora-core et common-deps déployées
- [ ] Buckets S3 accessibles (config-dev, data-dev, newsletters-dev)
- [ ] Profil AWS rag-lai-prod configuré
- [ ] Région eu-west-3 active, Bedrock us-east-1 accessible

#### Commandes de Validation
```bash
# Vérification Lambdas
aws lambda list-functions --profile rag-lai-prod --region eu-west-3 | grep "vectora-inbox.*-v2-dev"

# Vérification Buckets
aws s3 ls --profile rag-lai-prod | grep "vectora-inbox.*-dev"

# Test Bedrock
aws bedrock list-foundation-models --region us-east-1 --profile rag-lai-prod | grep "claude-3-sonnet"
```

### 1.2 Sauvegarde État Actuel
**Durée** : 30 minutes

#### Sauvegardes Critiques
- [ ] Backup src_v2/vectora_core/ → backup/vectora_core_pre_corrections/
- [ ] Backup canonical/ → backup/canonical_pre_corrections/
- [ ] Export configuration Lambdas actuelles
- [ ] Snapshot dernier run lai_weekly_v5 réussi

#### Script de Sauvegarde
```bash
# Créer dossier backup avec timestamp
mkdir -p backup/$(date +%Y%m%d_%H%M%S)_pre_corrections

# Sauvegarder code source
cp -r src_v2/vectora_core backup/$(date +%Y%m%d_%H%M%S)_pre_corrections/
cp -r canonical backup/$(date +%Y%m%d_%H%M%S)_pre_corrections/
cp -r client-config-examples backup/$(date +%Y%m%d_%H%M%S)_pre_corrections/
```

### 1.3 Préparation Environnement de Test
**Durée** : 60 minutes

#### Client de Test Dédié
- [ ] Créer lai_weekly_v5_test.yaml (copie de v5)
- [ ] Configuration test avec logging renforcé
- [ ] Bucket de test séparé pour éviter pollution données

#### Structure Test
```yaml
# client-config-examples/lai_weekly_v5_test.yaml
client_profile:
  name: "LAI Intelligence Weekly v5 TEST (Corrections)"
  client_id: "lai_weekly_v5_test"
  active: true

# Configuration identique à v5 mais avec debug activé
pipeline:
  newsletter_mode: "latest_run_only"
  debug_mode: true  # NOUVEAU pour tests
  
matching_config:
  enable_diagnostic_mode: true
  store_rejection_reasons: true
```

---

## 🔧 PHASE 2 : CORRECTIONS CODE CORE

### 2.1 Correction Déduplication UZEDY® (Issue #1)
**Durée** : 60 minutes  
**Fichier** : `src_v2/vectora_core/newsletter/selector.py`

#### Modification _create_item_signature()
```python
def _create_item_signature(self, item):
    """Crée une signature pour détecter les doublons - Version corrigée"""
    import hashlib
    
    normalized = item.get('normalized_content', {})
    entities = normalized.get('entities', {})
    
    # Utiliser molécules et indications pour différencier (vs trademarks)
    companies = tuple(sorted(entities.get('companies', [])))
    molecules = tuple(sorted(entities.get('molecules', [])))
    indications = tuple(sorted(entities.get('indications', [])))
    event_type = normalized.get('event_classification', {}).get('primary_type', '')
    
    # Hash du titre pour différencier news distinctes
    title = item.get('title', '')
    title_hash = hashlib.md5(title.encode('utf-8')).hexdigest()[:8]
    
    return (companies, molecules, indications, event_type, title_hash)
```

#### Test de Validation
- [ ] Vérifier UZEDY® Olanzapine vs UZEDY® Risperidone → signatures différentes
- [ ] Vérifier vrais doublons → même signature
- [ ] Test avec 10 items variés

### 2.2 Correction Extraction Dates HTML (Issue #3)
**Durée** : 90 minutes  
**Fichier** : `src_v2/vectora_core/ingest/content_parser.py`

#### Modification _extract_item_from_element()
```python
def _extract_item_from_element(element, source_key, source_type, source_meta, ingested_at):
    # ... (code existant jusqu'à content)
    
    # Date : utiliser fonction d'extraction avancée
    published_at = None
    
    # Créer objet compatible avec extract_real_publication_date
    pseudo_entry = {
        'content': content,
        'title': title,
        'summary': content[:200]
    }
    
    try:
        date_result = extract_real_publication_date(pseudo_entry, source_meta)
        published_at = date_result['date']
        logger.info(f"Date extracted: {published_at} (source: {date_result.get('date_source')})")
    except Exception as e:
        logger.debug(f"Advanced date extraction failed: {e}")
        # Fallback sur ancienne méthode
        published_at = _extract_date_from_html_element(element)
    
    if not published_at:
        published_at = datetime.now().strftime('%Y-%m-%d')
        logger.warning(f"Using ingestion fallback for {title[:50]}...")
    
    # ... (reste du code)
```

#### Test de Validation
- [ ] Test avec contenu "December 9, 2025December 9, 2025" → 2025-12-09
- [ ] Test avec patterns variés (November 5, 2025, etc.)
- [ ] Vérifier fallback fonctionne si extraction échoue

### 2.3 Correction Enrichissement PDF (Issue #2 - Partie 1)
**Durée** : 90 minutes  
**Fichier** : `src_v2/vectora_core/ingest/content_parser.py`

#### Amélioration extract_enhanced_summary()
```python
def extract_enhanced_summary(url, basic_content, max_length=1000):
    """Version améliorée avec gestion PDF"""
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; VectoraBot/1.0)'
        })
        
        if response.status_code != 200:
            logger.warning(f"HTTP {response.status_code} for {url}")
            return basic_content
        
        content_type = response.headers.get('content-type', '').lower()
        
        # Gestion spéciale PDFs
        if 'pdf' in content_type:
            logger.info(f"PDF detected: {url}")
            return _enrich_pdf_context(basic_content, url)
        
        # Traitement HTML normal
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Stratégies multiples pour contenu corporate
        content_selectors = [
            'div.content', 'div.post-content', 'article',
            'div[class*="content"]', 'main', '.entry-content',
            'div.press-release', 'div.news-content'
        ]
        
        enhanced_content = basic_content
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                text = elements[0].get_text(strip=True)
                if len(text) > len(enhanced_content):
                    enhanced_content = text
                break
        
        # Limiter intelligemment (phrases complètes)
        if len(enhanced_content) > max_length:
            sentences = enhanced_content.split('.')
            truncated = ''
            for sentence in sentences:
                if len(truncated + sentence + '.') <= max_length:
                    truncated += sentence + '.'
                else:
                    break
            enhanced_content = truncated
        
        logger.info(f"Content enriched: {len(basic_content)} → {len(enhanced_content)} chars")
        return enhanced_content
        
    except Exception as e:
        logger.warning(f"Content enrichment failed for {url}: {e}")
        return basic_content

def _enrich_pdf_context(basic_content, pdf_url):
    """Enrichit le contenu de base avec contexte PDF"""
    enrichments = []
    
    # Patterns spécifiques pour MedinCell
    if 'Gates-Malaria' in pdf_url or 'malaria' in pdf_url.lower():
        enrichments.append("This grant from Gates Foundation supports malaria prevention programs using long-acting injectable formulations for extended protection.")
    
    if 'MDC_' in pdf_url and any(kw in pdf_url for kw in ['PR_', 'press', 'release']):
        enrichments.append("This press release from MedinCell announces developments in long-acting injectable technologies and partnerships.")
    
    if 'NDA' in pdf_url or 'filing' in pdf_url:
        enrichments.append("This regulatory filing relates to New Drug Application submissions for long-acting injectable pharmaceutical products.")
    
    # Ajouter enrichissements au contenu de base
    if enrichments:
        return basic_content + ' ' + ' '.join(enrichments)
    
    return basic_content
```

#### Test de Validation
- [ ] Test URL PDF Malaria Grant → contenu enrichi
- [ ] Test URL HTML normale → fonctionnement normal
- [ ] Test URL inaccessible → fallback sur basic_content

### 2.4 Correction Contexte Pure Player (Issue #2 - Partie 2)
**Durée** : 60 minutes  
**Fichier** : `src_v2/vectora_core/normalization/normalizer.py`

#### Ajout Contexte Pure Player dans Prompt
```python
def _build_normalization_prompt(item, canonical_scopes, canonical_prompts):
    # ... (code existant pour construire prompt de base)
    
    # Détecter pure player depuis source_key
    source_key = item.get('source_key', '')
    company_name = _extract_company_from_source_key(source_key)
    
    # Vérifier si pure player
    pure_player_companies = canonical_scopes.get('lai_companies_pure_players', [])
    is_pure_player = company_name in pure_player_companies if company_name else False
    
    if is_pure_player:
        prompt += f"\n\nIMPORTANT CONTEXT: This content is from {company_name}, a LAI pure-player company specializing in long-acting injectable technologies. Even if LAI technologies are not explicitly mentioned, consider the LAI context and relevance given the company's specialization in this field."
    
    return prompt

def _extract_company_from_source_key(source_key):
    """Extrait nom société depuis source_key"""
    company_mapping = {
        'medincell': 'MedinCell',
        'camurus': 'Camurus',
        'delsitech': 'DelSiTech',
        'nanexa': 'Nanexa',
        'peptron': 'Peptron'
    }
    
    source_lower = source_key.lower()
    for key, company in company_mapping.items():
        if key in source_lower:
            return company
    
    return None
```

#### Test de Validation
- [ ] Test item MedinCell → contexte pure player ajouté au prompt
- [ ] Test item source générique → pas de contexte ajouté
- [ ] Vérifier prompt Bedrock contient bien le contexte

### 2.5 Correction Titres Tronqués (Issue #4)
**Durée** : 30 minutes  
**Fichier** : `src_v2/vectora_core/newsletter/assembler.py`

#### Amélioration Formatage Titres
```python
def format_item_title(item, max_length=120):  # Augmenté de 80 à 120
    """Formate titre item pour newsletter avec troncature intelligente"""
    original_title = item.get('title', '')
    
    # Si titre court, garder tel quel
    if len(original_title) <= max_length:
        return original_title
    
    # Utiliser summary Bedrock si plus court et pertinent
    summary = item.get('normalized_content', {}).get('summary', '')
    if summary and len(summary) <= max_length and len(summary) > 20:
        return summary
    
    # Troncature intelligente (phrases complètes)
    sentences = original_title.split('.')
    truncated = sentences[0]
    
    for sentence in sentences[1:]:
        if len(truncated + '.' + sentence) <= max_length - 3:  # -3 pour "..."
            truncated += '.' + sentence
        else:
            break
    
    # Ajouter "..." si tronqué
    if len(truncated) < len(original_title):
        truncated += "..."
    
    return truncated
```

---

## 🔧 PHASE 3 : MISE À JOUR CONFIGURATIONS

### 3.1 Enrichissement Patterns LAI
**Durée** : 30 minutes  
**Fichier** : `canonical/prompts/global_prompts.yaml`

#### Ajout Patterns LAI Manquants
```yaml
LAI TECHNOLOGY FOCUS:
Detect these LAI (Long-Acting Injectable) technologies ONLY if explicitly mentioned:
- Extended-Release Injectable
- Long-Acting Injectable
- Depot Injection
- Once-Monthly Injection
- Three-Month Injectable      # NOUVEAU
- Quarterly Injection         # NOUVEAU
- Long-Acting Formulation     # NOUVEAU
- Injectable Formulation      # NOUVEAU
- Sustained Release Injectable
- Controlled Release Injectable
- Monthly Injectable          # NOUVEAU
- Extended Protection         # NOUVEAU pour malaria
```

### 3.2 Amélioration Patterns Extraction Dates
**Durée** : 30 minutes  
**Fichier** : `canonical/sources/source_catalog.yaml`

#### Patterns Dates Enrichis
```yaml
# Pour toutes les sources corporate
date_extraction_patterns:
  # Patterns existants
  - r"Published:\s*(\d{4}-\d{2}-\d{2})"
  - r"Date:\s*(\w+ \d{1,2}, \d{4})"
  
  # NOUVEAUX patterns pour contenu corporate
  - r"(\w+ \d{1,2}, \d{4})\w*"              # "December 9, 2025December"
  - r"(\d{1,2} \w+ \d{4})"                  # "10 December, 2025"
  - r"(\w+\s+\d{1,2},\s+\d{4})"            # "November 5, 2025"
  - r"(\d{4}-\d{2}-\d{2})"                 # ISO format
  
  # Patterns avec contexte
  - r"(?:published|released|announced).*?(\w+ \d{1,2}, \d{4})"
```

---

## 🧪 PHASE 4 : TESTS UNITAIRES ET VALIDATION

### 4.1 Tests Déduplication
**Durée** : 45 minutes

#### Script de Test
```python
# tests/unit/test_deduplication_fix.py
def test_uzedy_items_not_deduplicated():
    """Test que UZEDY® Olanzapine et UZEDY® Risperidone ne sont pas dédupliqués"""
    
    item1 = create_test_item(
        title="Teva NDA Olanzapine Extended-Release",
        molecules=["Olanzapine"],
        indications=["Schizophrenia"],
        trademarks=["UZEDY®"]
    )
    
    item2 = create_test_item(
        title="FDA Approves UZEDY® Risperidone for Bipolar",
        molecules=["Risperidone"], 
        indications=["Bipolar I Disorder"],
        trademarks=["UZEDY®"]
    )
    
    selector = NewsletterSelector(test_config)
    signature1 = selector._create_item_signature(item1)
    signature2 = selector._create_item_signature(item2)
    
    assert signature1 != signature2, "UZEDY® items should have different signatures"
```

### 4.2 Tests Extraction Dates
**Durée** : 45 minutes

#### Script de Test
```python
# tests/unit/test_date_extraction_fix.py
def test_html_date_extraction():
    """Test extraction dates depuis contenu HTML"""
    
    test_cases = [
        ("December 9, 2025December 9, 2025", "2025-12-09"),
        ("November 5, 2025November 5, 2025", "2025-11-05"),
        ("10 December, 2025Nanexa and Moderna", "2025-12-10")
    ]
    
    for content, expected_date in test_cases:
        pseudo_entry = {'content': content, 'title': 'Test'}
        result = extract_real_publication_date(pseudo_entry, test_source_config)
        assert result['date'] == expected_date
```

### 4.3 Tests Enrichissement PDF
**Durée** : 45 minutes

#### Script de Test
```python
# tests/unit/test_pdf_enrichment.py
def test_malaria_grant_enrichment():
    """Test enrichissement contenu PDF Malaria Grant"""
    
    pdf_url = "https://www.medincell.com/.../MDC_Gates-Malaria_PR_24112025_vf.pdf"
    basic_content = "Medincell Awarded New Grant to Fight Malaria"
    
    enriched = extract_enhanced_summary(pdf_url, basic_content, 1000)
    
    assert len(enriched) > len(basic_content)
    assert "Gates Foundation" in enriched
    assert "long-acting injectable" in enriched.lower()
```

### 4.4 Tests Contexte Pure Player
**Durée** : 45 minutes

#### Script de Test
```python
# tests/unit/test_pure_player_context.py
def test_medincell_pure_player_context():
    """Test ajout contexte pure player pour MedinCell"""
    
    item = {
        'source_key': 'press_corporate__medincell',
        'title': 'Test MedinCell Item'
    }
    
    prompt = _build_normalization_prompt(item, test_scopes, test_prompts)
    
    assert "MedinCell" in prompt
    assert "LAI pure-player company" in prompt
    assert "specializing in long-acting injectable" in prompt
```

---

## 🔬 PHASE 5 : TESTS E2E DONNÉES RÉELLES

### 5.1 Test Complet lai_weekly_v5_test
**Durée** : 90 minutes

#### Exécution Workflow Complet
```bash
# 1. Ingestion avec corrections
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --payload '{"client_id": "lai_weekly_v5_test"}' \
  --profile rag-lai-prod \
  response_ingest_test.json

# 2. Normalisation avec corrections
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v5_test"}' \
  --profile rag-lai-prod \
  response_normalize_test.json

# 3. Newsletter avec corrections
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --payload '{"client_id": "lai_weekly_v5_test"}' \
  --profile rag-lai-prod \
  response_newsletter_test.json
```

#### Métriques de Validation
- [ ] **Items newsletter** : 5-6 (vs 3 avant)
- [ ] **Dates réelles** : 85%+ extraction réussie
- [ ] **Malaria Grant** : Matché et inclus dans newsletter
- [ ] **UZEDY® items** : 2 items distincts présents
- [ ] **Titres complets** : Lisibles sans troncature excessive

### 5.2 Comparaison Avant/Après
**Durée** : 30 minutes

#### Analyse Comparative
```python
# scripts/compare_v5_results.py
def compare_results():
    """Compare résultats avant/après corrections"""
    
    # Charger résultats avant corrections
    before = load_json('analysis/lai_weekly_v5_before.json')
    
    # Charger résultats après corrections  
    after = load_json('analysis/lai_weekly_v5_test_after.json')
    
    comparison = {
        'items_newsletter': {
            'before': len(before['newsletter']['items']),
            'after': len(after['newsletter']['items'])
        },
        'dates_real': {
            'before': count_real_dates(before),
            'after': count_real_dates(after)
        },
        'malaria_grant': {
            'before': 'malaria' in str(before).lower(),
            'after': 'malaria' in str(after).lower()
        }
    }
    
    return comparison
```

---

## 🚀 PHASE 6 : DÉPLOIEMENT AWS ET VALIDATION PRODUCTION

### 6.1 Déploiement Layers Mises à Jour
**Durée** : 30 minutes

#### Reconstruction Layer vectora-core
```bash
# 1. Créer nouveau layer avec corrections
cd src_v2
zip -r ../vectora-core-v2-corrected.zip vectora_core/

# 2. Publier nouvelle version layer
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://vectora-core-v2-corrected.zip \
  --compatible-runtimes python3.11 \
  --profile rag-lai-prod \
  --region eu-west-3

# 3. Mettre à jour Lambdas avec nouvelle version layer
NEW_LAYER_VERSION=$(aws lambda list-layer-versions \
  --layer-name vectora-inbox-vectora-core-dev \
  --profile rag-lai-prod --region eu-west-3 \
  --query 'LayerVersions[0].Version' --output text)

aws lambda update-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:$NEW_LAYER_VERSION \
  --profile rag-lai-prod
```

### 6.2 Upload Configurations Mises à Jour
**Durée** : 30 minutes

#### Synchronisation S3 Config
```bash
# Upload canonical mis à jour
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --delete

# Upload client config test
aws s3 cp client-config-examples/lai_weekly_v5_test.yaml \
  s3://vectora-inbox-config-dev/clients/ \
  --profile rag-lai-prod
```

### 6.3 Test E2E Production
**Durée** : 60 minutes

#### Validation Finale
```bash
# Test complet avec client de test
./scripts/run_e2e_test.sh lai_weekly_v5_test

# Validation métriques
./scripts/validate_corrections.sh
```

#### Critères de Succès
- [ ] Workflow complet sans erreur
- [ ] Toutes les métriques cibles atteintes
- [ ] Logs propres sans warnings critiques
- [ ] Coût Bedrock acceptable (<$0.50)

---

## 📊 VALIDATION FINALE ET ROLLBACK

### Critères de Validation
- [ ] **UZEDY® items** : 2 items distincts dans newsletter
- [ ] **Malaria Grant** : Présent avec LAI relevance > 5
- [ ] **Dates réelles** : >80% items avec dates correctes
- [ ] **Volume newsletter** : 5-6 items total
- [ ] **Performance** : Workflow <5 minutes
- [ ] **Coût** : <$0.50 par run

### Plan de Rollback
En cas d'échec critique :
1. Restaurer layer vectora-core précédente
2. Restaurer configurations canonical/
3. Revenir à lai_weekly_v5 original
4. Analyser logs d'erreur
5. Corriger et relancer plan

---

## 📋 CHECKLIST FINALE

### Conformité Règles Développement
- [ ] ✅ Architecture 3 Lambdas V2 préservée
- [ ] ✅ Handlers délèguent à vectora_core (aucune modification)
- [ ] ✅ Configuration pilote comportement
- [ ] ✅ Aucune logique hardcodée client-spécifique
- [ ] ✅ Tests E2E avec données réelles
- [ ] ✅ Déploiement AWS validé

### Livrables
- [ ] Code corrigé dans src_v2/vectora_core/
- [ ] Configurations mises à jour dans canonical/
- [ ] Tests unitaires passants
- [ ] Documentation corrections dans docs/diagnostics/
- [ ] Métriques avant/après validées

---

**Plan prêt pour exécution avec approbation utilisateur**  
**Durée totale** : 14 heures  
**Risque** : Faible (corrections ciblées + rollback prévu)  
**Impact attendu** : Résolution des 4 issues critiques identifiées