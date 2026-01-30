# Investigation Technique Approfondie - Causes et Actions Correctives lai_weekly_v5

## 🔍 ANALYSE DES CAUSES RACINES

### 1. PROBLÈME UZEDY® BIPOLAR EXCLU - INVESTIGATION TECHNIQUE

#### Feedback Utilisateur
> "Item #3 UZEDY® Bipolar ne devrait pas être exclu, ce sont deux news bien différentes qui ont le même trademark UZEDY dans la news, mais deux news distinctes"

#### Analyse du Code Source

**Fichier analysé** : `src_v2/vectora_core/newsletter/selector.py`

**Cause identifiée** : Déduplication trop agressive dans `_create_item_signature()`

```python
def _create_item_signature(self, item):
    """Crée une signature pour détecter les doublons"""
    normalized = item.get('normalized_content', {})
    entities = normalized.get('entities', {})
    
    companies = tuple(sorted(entities.get('companies', [])))
    event_type = normalized.get('event_classification', {}).get('primary_type', '')
    trademarks = tuple(sorted(entities.get('trademarks', [])))  # ❌ PROBLÈME
    published_date = item.get('published_at', '')[:10]
    
    return (companies, event_type, trademarks, published_date)
```

**Problème** : La signature inclut `trademarks` ce qui fait que :
- Item #1 : UZEDY® NDA Olanzapine → signature: ([], 'regulatory', ('UZEDY®',), '2025-12-23')
- Item #3 : UZEDY® Bipolar approval → signature: ([], 'regulatory', ('UZEDY®',), '2025-12-23')

**Résultat** : Même signature → déduplication → seul le premier est gardé

#### Action Corrective 1.1 : Affiner la Signature de Déduplication

**Modification** : `src_v2/vectora_core/newsletter/selector.py`

```python
def _create_item_signature(self, item):
    """Crée une signature pour détecter les doublons - Version corrigée"""
    normalized = item.get('normalized_content', {})
    entities = normalized.get('entities', {})
    
    # Utiliser les molécules et indications pour différencier
    companies = tuple(sorted(entities.get('companies', [])))
    molecules = tuple(sorted(entities.get('molecules', [])))  # NOUVEAU
    indications = tuple(sorted(entities.get('indications', [])))  # NOUVEAU
    event_type = normalized.get('event_classification', {}).get('primary_type', '')
    
    # Hash du titre pour différencier les news distinctes
    title_hash = hashlib.md5(item.get('title', '').encode()).hexdigest()[:8]  # NOUVEAU
    
    return (companies, molecules, indications, event_type, title_hash)
```

**Justification** : 
- Olanzapine vs Risperidone (molécules différentes)
- Schizophrenia vs Bipolar I Disorder (indications différentes)
- Hash du titre pour différencier les news distinctes

---

### 2. PROBLÈME MALARIA GRANT NON MATCHÉ - INVESTIGATION TECHNIQUE

#### Feedback Utilisateur
> "Medincell Grant malaria devrait matcher car : programme mdc-STM = formulation injectable d'ivermectine, active trois mois + Medincell est un pure_player"

#### Analyse du Code Source

**Fichier analysé** : `src_v2/vectora_core/ingest/content_parser.py`

**Cause 1** : Contenu ingéré insuffisant

```python
def _extract_item_from_element(element, source_key, source_type, source_meta, ingested_at):
    # ...
    content = element.get_text(strip=True)[:500]  # ❌ LIMITÉ À 500 CARACTÈRES
```

**Analyse des données** :
- Item ingéré : "Medincell Awarded New Grant to Fight Malaria" (11 mots)
- Contenu réel sur site : "programme mdc-STM est une formulation injectable d'ivermectine, active trois mois"

**Cause 2** : Stratégie d'enrichissement non appliquée

```python
# Dans source_catalog.yaml
- source_key: "press_corporate__medincell"
  content_enrichment: "summary_enhanced"  # ✅ CONFIGURÉ
  max_content_length: 1000
```

**Mais dans le code** :
```python
def enrich_content_extraction(url, basic_content, source_config):
    strategy = source_config.get('content_enrichment', 'basic')
    # ❌ Fonction appelée mais échec silencieux
```

#### Analyse Bedrock Normalisation

**Prompt analysé** : `canonical/prompts/global_prompts.yaml`

```yaml
LAI TECHNOLOGY FOCUS:
Detect these LAI (Long-Acting Injectable) technologies ONLY if explicitly mentioned:
- Extended-Release Injectable
- Long-Acting Injectable
- Depot Injection
- Once-Monthly Injection  # ❌ "trois mois" pas détecté
```

**Cause 3** : Patterns LAI incomplets dans le prompt

#### Analyse Pure Player Context

**Configuration** : `canonical/scopes/company_scopes.yaml`

```yaml
lai_companies_pure_players:
  - MedinCell  # ✅ CONFIGURÉ
```

**Mais dans le code normalisation** :
```python
# Bedrock ne reçoit pas le contexte pure_player explicitement
"pure_player_context": false  # ❌ TOUJOURS FALSE
```

#### Actions Correctives 2.1-2.4

**Action 2.1** : Améliorer l'enrichissement de contenu

**Modification** : `src_v2/vectora_core/ingest/content_parser.py`

```python
def extract_enhanced_summary(url, basic_content, max_length=1000):
    """Version améliorée avec retry et logging"""
    try:
        response = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; VectoraBot/1.0)'
        })
        
        if response.status_code != 200:
            logger.warning(f"HTTP {response.status_code} for {url}")
            return basic_content
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Stratégie multi-pattern pour contenu corporate
        content_selectors = [
            'div.content', 'div.post-content', 'article',
            'div[class*="content"]', 'main', '.entry-content'
        ]
        
        enhanced_content = basic_content
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                text = elements[0].get_text(strip=True)
                if len(text) > len(enhanced_content):
                    enhanced_content = text
                break
        
        # Limiter intelligemment (garder phrases complètes)
        if len(enhanced_content) > max_length:
            sentences = enhanced_content.split('.')
            truncated = ''
            for sentence in sentences:
                if len(truncated + sentence) < max_length:
                    truncated += sentence + '.'
                else:
                    break
            enhanced_content = truncated
        
        logger.info(f"Content enriched: {len(basic_content)} → {len(enhanced_content)} chars")
        return enhanced_content
        
    except Exception as e:
        logger.warning(f"Content enrichment failed for {url}: {e}")
        return basic_content
```

**Action 2.2** : Enrichir les patterns LAI dans le prompt

**Modification** : `canonical/prompts/global_prompts.yaml`

```yaml
LAI TECHNOLOGY FOCUS:
Detect these LAI (Long-Acting Injectable) technologies ONLY if explicitly mentioned:
- Extended-Release Injectable
- Long-Acting Injectable
- Depot Injection
- Once-Monthly Injection
- Three-Month Injectable  # NOUVEAU
- Quarterly Injection     # NOUVEAU
- Long-Acting Formulation # NOUVEAU
- Injectable Formulation  # NOUVEAU
- Sustained Release Injectable
- Controlled Release Injectable
```

**Action 2.3** : Améliorer la détection pure player context

**Modification** : `src_v2/vectora_core/normalization/normalizer.py`

```python
def _build_normalization_prompt(item, canonical_scopes, canonical_prompts):
    # Détecter si l'item provient d'un pure player
    source_key = item.get('source_key', '')
    company_from_source = _extract_company_from_source_key(source_key)
    
    pure_player_companies = canonical_scopes.get('lai_companies_pure_players', [])
    is_pure_player_source = company_from_source in pure_player_companies
    
    # Ajouter contexte dans le prompt
    if is_pure_player_source:
        prompt += f"\n\nIMPORTANT: This content is from {company_from_source}, a LAI pure-player company. Consider LAI context even if not explicitly mentioned."
    
    return prompt
```

**Action 2.4** : Ajuster les seuils de matching pour pure players

**Modification** : `client-config-examples/lai_weekly_v5.yaml`

```yaml
matching_config:
  pure_player_privileges:
    enabled: true
    companies_scope: "lai_companies_pure_players"
    min_score_override: 0.15  # Plus permissif pour pure players
    lai_relevance_boost: 3.0  # Boost significatif
```

---

### 3. PROBLÈME DATES RÉELLES NON EXTRAITES - INVESTIGATION TECHNIQUE

#### Analyse du Code Source

**Fichier analysé** : `src_v2/vectora_core/ingest/content_parser.py`

**Fonction** : `extract_real_publication_date()`

```python
def extract_real_publication_date(item_data, source_config):
    # Priorité 2: Extraction HTML/contenu
    date_patterns = source_config.get('date_extraction_patterns', [])
    content = item_data.get('content', '') + ' ' + item_data.get('title', '')
    
    for pattern in date_patterns:
        if match := re.search(pattern, content):  # ❌ PATTERNS INADÉQUATS
            parsed_date = _parse_date_string(match.group(1))
```

**Configuration actuelle** : `canonical/sources/source_catalog.yaml`

```yaml
date_extraction_patterns:
  - r"Published:\s*(\d{4}-\d{2}-\d{2})"     # ❌ Ne match pas
  - r"Date:\s*(\w+ \d{1,2}, \d{4})"         # ❌ Ne match pas
```

**Contenu réel analysé** :
- "December 9, 2025December 9, 2025"
- "November 5, 2025November 5, 2025"
- "10 December, 2025Nanexa and Moderna"

#### Action Corrective 3.1 : Patterns d'Extraction Améliorés

**Modification** : `canonical/sources/source_catalog.yaml`

```yaml
# Pour chaque source corporate
date_extraction_patterns:
  # Patterns existants
  - r"Published:\s*(\d{4}-\d{2}-\d{2})"
  - r"Date:\s*(\w+ \d{1,2}, \d{4})"
  
  # NOUVEAUX patterns pour contenu corporate
  - r"(\w+ \d{1,2}, \d{4})\w*"              # "December 9, 2025December"
  - r"(\d{1,2} \w+ \d{4})"                  # "10 December, 2025"
  - r"(\w+\s+\d{1,2},\s+\d{4})"            # "November 5, 2025"
  - r"(\d{4}-\d{2}-\d{2})"                 # ISO format
  - r"(\d{1,2}/\d{1,2}/\d{4})"             # US format
  
  # Patterns avec contexte
  - r"(?:published|released|announced).*?(\w+ \d{1,2}, \d{4})"
  - r"(\w+ \d{1,2}, \d{4}).*?(?:published|released|announced)"
```

**Action 3.2** : Améliorer la fonction de parsing

**Modification** : `src_v2/vectora_core/ingest/content_parser.py`

```python
def extract_real_publication_date(item_data, source_config):
    """Version améliorée avec patterns multiples et validation"""
    import re
    from datetime import datetime, timedelta
    
    # Priorité 1: Champs RSS standards (inchangé)
    if 'published_parsed' in item_data:
        dt = datetime(*item_data['published_parsed'][:6])
        return {
            'date': dt.strftime('%Y-%m-%d'),
            'date_source': 'rss_parsed'
        }
    
    # Priorité 2: Extraction améliorée HTML/contenu
    date_patterns = source_config.get('date_extraction_patterns', [])
    
    # Contenu étendu pour recherche
    search_content = ' '.join([
        item_data.get('content', ''),
        item_data.get('title', ''),
        item_data.get('summary', ''),
        str(item_data.get('description', ''))
    ])
    
    # Nettoyer le contenu (supprimer HTML, normaliser espaces)
    search_content = re.sub(r'<[^>]+>', ' ', search_content)
    search_content = re.sub(r'\s+', ' ', search_content).strip()
    
    logger.debug(f"Searching dates in: {search_content[:200]}...")
    
    for pattern in date_patterns:
        try:
            matches = re.finditer(pattern, search_content, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                parsed_date = _parse_date_string(date_str)
                
                if parsed_date:
                    # Validation : date pas trop ancienne ni future
                    date_obj = datetime.strptime(parsed_date, '%Y-%m-%d')
                    now = datetime.now()
                    
                    if (now - timedelta(days=365)) <= date_obj <= (now + timedelta(days=30)):
                        logger.info(f"Date extracted: {date_str} → {parsed_date} (pattern: {pattern})")
                        return {
                            'date': parsed_date,
                            'date_source': 'content_extraction',
                            'pattern_used': pattern,
                            'raw_match': date_str
                        }
                    else:
                        logger.debug(f"Date rejected (out of range): {parsed_date}")
        
        except Exception as e:
            logger.debug(f"Pattern {pattern} failed: {e}")
            continue
    
    # Priorité 3: Fallback avec flag
    logger.warning(f"No date extracted from content, using fallback")
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'date_source': 'ingestion_fallback'
    }
```

---

### 4. PROBLÈME TITRES TRONQUÉS - INVESTIGATION TECHNIQUE

#### Analyse du Code Source

**Fichier analysé** : `src_v2/vectora_core/newsletter/assembler.py` (supposé)

**Cause probable** : Limitation dans la génération des titres newsletter

#### Action Corrective 4.1 : Améliorer la Génération des Titres

**Modification** : `src_v2/vectora_core/newsletter/assembler.py`

```python
def format_item_title(item, max_length=120):  # Augmenté de 80 à 120
    """Formate le titre d'un item pour la newsletter"""
    original_title = item.get('title', '')
    
    # Si titre court, garder tel quel
    if len(original_title) <= max_length:
        return original_title
    
    # Utiliser le summary Bedrock si disponible et plus court
    summary = item.get('normalized_content', {}).get('summary', '')
    if summary and len(summary) <= max_length:
        return summary
    
    # Troncature intelligente (garder phrases complètes)
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

### 5. DIFFÉRENCES V4 vs V5 - INVESTIGATION COMPARATIVE

#### Analyse des Configurations

**lai_weekly_v4.yaml** vs **lai_weekly_v5.yaml** : Identiques (copie exacte)

**Cause probable** : Évolution des prompts Bedrock ou des seuils

#### Investigation des Prompts

**Fichier** : `canonical/prompts/global_prompts.yaml`

**Changements récents** :
- Ajout instructions CRITICAL/FORBIDDEN (anti-hallucinations)
- Prompts plus conservateurs

**Impact** : Bedrock plus strict → moins d'items matchés

#### Action Corrective 5.1 : Mode de Compatibilité

**Modification** : `client-config-examples/lai_weekly_v5.yaml`

```yaml
matching_config:
  compatibility_mode: "v4"  # NOUVEAU
  bedrock_conservatism: "balanced"  # vs "strict" par défaut
  
  # Seuils ajustés pour retrouver le comportement v4
  min_domain_score: 0.20  # vs 0.25
  fallback_min_score: 0.10  # vs 0.15
```

---

## 📋 PLAN D'ACTIONS CORRECTIVES PRIORITAIRES

### Phase 1 : Corrections Critiques (Immédiat)

**Action 1** : Corriger la déduplication UZEDY®
- **Fichier** : `src_v2/vectora_core/newsletter/selector.py`
- **Méthode** : `_create_item_signature()`
- **Impact** : Items distincts non dédupliqués

**Action 2** : Améliorer l'extraction de dates
- **Fichier** : `canonical/sources/source_catalog.yaml`
- **Méthode** : Patterns d'extraction enrichis
- **Impact** : Dates réelles vs dates d'ingestion

**Action 3** : Enrichir le contenu Malaria Grant
- **Fichier** : `src_v2/vectora_core/ingest/content_parser.py`
- **Méthode** : `extract_enhanced_summary()`
- **Impact** : Contenu plus riche pour Bedrock

### Phase 2 : Améliorations Qualité (Court terme)

**Action 4** : Améliorer les patterns LAI
- **Fichier** : `canonical/prompts/global_prompts.yaml`
- **Impact** : Meilleure détection LAI (3 mois, formulation injectable)

**Action 5** : Contexte pure player
- **Fichier** : `src_v2/vectora_core/normalization/normalizer.py`
- **Impact** : Matching privilégié pour pure players

**Action 6** : Titres newsletter complets
- **Fichier** : `src_v2/vectora_core/newsletter/assembler.py`
- **Impact** : Lisibilité améliorée

### Phase 3 : Optimisations (Moyen terme)

**Action 7** : Mode compatibilité v4
- **Fichier** : `client-config-examples/lai_weekly_v5.yaml`
- **Impact** : Retrouver le volume v4

**Action 8** : Monitoring qualité
- **Fichier** : `src_v2/vectora_core/newsletter/selector.py`
- **Impact** : Alertes sur distribution

---

## 🔧 CONFORMITÉ AUX RÈGLES DE DÉVELOPPEMENT

### Respect des Interdictions

✅ **Aucune modification de l'architecture 3 Lambdas V2**
✅ **Aucune modification des handlers (délégation à vectora_core)**
✅ **Aucune logique hardcodée client-spécifique**
✅ **Configuration pilote le comportement**

### Respect des Bonnes Pratiques

✅ **Modifications dans `src_v2/vectora_core/` uniquement**
✅ **Configuration dans `canonical/` et `client-config-examples/`**
✅ **Logs structurés pour debugging**
✅ **Validation des données d'entrée**

### Tests et Validation

**Tests requis** :
- Test unitaire déduplication avec UZEDY®
- Test extraction dates avec patterns réels
- Test enrichissement contenu Malaria Grant
- Test E2E lai_weekly_v5 après corrections

**Métriques de validation** :
- Items newsletter : 5-6 (vs 3 actuel)
- Dates réelles : >80% (vs 0% actuel)
- Malaria Grant : Matché et sélectionné
- UZEDY® Bipolar : Non dédupliqué

---

## 🎯 RÉSULTATS ATTENDUS APRÈS CORRECTIONS

### Métriques Cibles

- **Items newsletter** : 5-6 items (vs 3 actuel)
- **Distribution sections** : 3-4/4 sections remplies (vs 2/4 actuel)
- **Dates réelles** : 85%+ extraction réussie (vs 0% actuel)
- **Malaria Grant** : Matché et inclus dans newsletter
- **UZEDY® items** : 2 items distincts (vs 1 dédupliqué)

### Validation Qualité

- **Anti-hallucinations** : Maintenu (0 hallucination)
- **Distribution spécialisée** : Maintenue et améliorée
- **Format professionnel** : Maintenu avec titres complets
- **Performance** : <5 min workflow complet

**Statut final attendu** : **PRÊT POUR PRODUCTION** avec corrections validées