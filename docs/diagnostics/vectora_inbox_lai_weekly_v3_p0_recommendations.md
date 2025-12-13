# Vectora Inbox LAI Weekly v3 - Recommandations P0

**Objectif** : Proposer 2-4 corrections P0 pour garantir que les items "gold" passent et éliminer le bruit  
**Basé sur** : Diagnostic des causes racines identifiées en Phase 4

---

## Résumé Exécutif

| **Recommandation** | **Priorité** | **Impact** | **Effort** |
|-------------------|--------------|------------|------------|
| **P0-1 : Fixer détection technology Bedrock** | 🔴 **CRITIQUE** | Récupère Nanexa/UZEDY/MedinCell | **MOYEN** |
| **P0-2 : Implémenter exclusions HR/finance** | 🔴 **CRITIQUE** | Élimine bruit DelSiTech HR | **FAIBLE** |
| **P0-3 : Activer matching contextuel pure players** | 🟡 **IMPORTANT** | Récupère MedinCell malaria | **MOYEN** |
| **P0-4 : Fixer normalisation HTML** | 🟡 **IMPORTANT** | Récupère Nanexa/Moderna | **ÉLEVÉ** |

**Objectif** : Avec P0-1 et P0-2, la newsletter devrait contenir les items LAI-strong et éliminer le bruit HR/finance.

---

## P0-1 : Fixer Détection Technology Bedrock 🔴

### Problème Identifié
Bedrock ne détecte aucune technology LAI malgré leur présence dans `technology_scopes.yaml` :
- "Extended-Release Injectable" non détecté dans les titres UZEDY
- "LAI" non détecté dans "Olanzapine LAI"
- "PharmaShell®" non détecté (mais item a summary vide)

### Cause Racine Probable
Le prompt Bedrock ou la logique de détection d'entités ne référence pas correctement `technology_scopes.yaml`

### Solution Recommandée
**Vérifier et corriger le prompt Bedrock dans la Lambda ingest-normalize**

```python
# Dans src/lambdas/ingest_normalize/handler.py
# Vérifier que le prompt inclut bien les technology_scopes

ENHANCED_PROMPT = f"""
...existing prompt...

Technology Detection:
Use these LAI technology terms for detection:
{technology_scopes_content}

Specifically detect:
- "extended-release injectable", "long-acting injectable", "LAI"
- "PharmaShell®", "SiliaShell®", "BEPO®"
- "depot injection", "once-monthly injection"
- "UZEDY®" as trademark

Include in response:
"technologies_detected": [list of detected technologies],
"trademarks_detected": [list of detected trademarks]
"""
```

### Validation
- Tester avec les items UZEDY : "Extended-Release Injectable" doit être détecté
- Tester avec item Nanexa (si summary fixé) : "PharmaShell®" doit être détecté

### Impact Attendu
✅ **UZEDY regulatory items** → Détection technology → Match tech_lai_ecosystem → Newsletter  
✅ **UZEDY growth items** → Détection technology → Match tech_lai_ecosystem → Newsletter

---

## P0-2 : Implémenter Exclusions HR/Finance 🔴

### Problème Identifié
Les exclusions HR/finance ne sont pas appliquées dans le pipeline :
- Items "DelSiTech is Hiring" passent en newsletter
- Items "DelSiTech Seeks Quality Director" passent en newsletter
- `exclusion_scopes.hr_recruitment_terms` existe mais n'est pas utilisé

### Cause Racine Probable
La logique d'exclusion n'est pas implémentée dans le code Lambda engine

### Solution Recommandée
**Implémenter le filtrage d'exclusion dans la Lambda engine**

```python
# Dans src/lambdas/engine/handler.py
def apply_exclusion_filters(item, exclusion_scopes):
    """Applique les filtres d'exclusion selon exclusion_scopes.yaml"""
    
    title_lower = item.get('title', '').lower()
    summary_lower = item.get('summary', '').lower()
    
    # Vérifier exclusions HR
    hr_terms = exclusion_scopes.get('hr_recruitment_terms', [])
    for term in hr_terms:
        if term.lower() in title_lower or term.lower() in summary_lower:
            return False, f"Excluded by HR term: {term}"
    
    # Vérifier exclusions finance
    finance_terms = exclusion_scopes.get('financial_reporting_terms', [])
    for term in finance_terms:
        if term.lower() in title_lower or term.lower() in summary_lower:
            return False, f"Excluded by finance term: {term}"
    
    return True, "Not excluded"

# Appliquer avant le scoring
for item in normalized_items:
    is_allowed, reason = apply_exclusion_filters(item, exclusion_scopes)
    if not is_allowed:
        item['excluded'] = True
        item['exclusion_reason'] = reason
```

### Validation
- Tester avec "DelSiTech is Hiring" : doit être exclu par "hiring"
- Tester avec "DelSiTech Seeks Quality Director" : doit être exclu par "seeks"
- Tester avec "MedinCell Financial Results" : doit être exclu par "financial results"

### Impact Attendu
❌ **DelSiTech HR items** → Exclusion HR → Pas en newsletter  
❌ **MedinCell finance items** → Exclusion finance → Pas en newsletter

---

## P0-3 : Activer Matching Contextuel Pure Players 🟡

### Problème Identifié
Les pure players LAI sans signaux technology explicites sont rejetés :
- "MedinCell Malaria Grant" rejeté malgré MedinCell = pure player LAI
- La logique contextuelle définie dans `domain_matching_rules.yaml` n'est pas active

### Cause Racine Probable
Le matching engine n'implémente pas la règle `pure_player_rule: contextual_matching`

### Solution Recommandée
**Implémenter le matching contextuel pour pure players**

```python
# Dans src/lambdas/engine/matching.py
def contextual_matching_for_pure_players(item, company_scopes):
    """Matching contextuel pour pure players LAI"""
    
    companies = item.get('companies_detected', [])
    pure_player_scopes = ['lai_companies_mvp_core', 'lai_companies_pure_players']
    
    # Vérifier si au moins une company est pure player LAI
    for company in companies:
        if is_company_in_scopes(company, pure_player_scopes, company_scopes):
            # Pure player LAI : matching contextuel
            event_type = item.get('event_type', 'other')
            
            # Contextes LAI implicites pour pure players
            if event_type in ['partnership', 'regulatory', 'clinical_update']:
                return True, "Pure player LAI with implicit LAI context"
            
            # Grant/funding pour pure players LAI
            title_lower = item.get('title', '').lower()
            if any(term in title_lower for term in ['grant', 'funding', 'award']):
                return True, "Pure player LAI with funding context"
    
    return False, "No contextual matching"

# Intégrer dans la logique de matching principale
def match_domain_tech_lai_ecosystem(item, scopes):
    # Logique existante pour technology signals
    has_tech_signals = check_technology_signals(item, scopes)
    if has_tech_signals:
        return True, "Technology signals detected"
    
    # Nouveau : matching contextuel pour pure players
    contextual_match, reason = contextual_matching_for_pure_players(item, scopes)
    if contextual_match:
        return True, reason
    
    return False, "No matching signals"
```

### Validation
- Tester avec "MedinCell Malaria Grant" : doit matcher par contexte pure player + grant
- Tester avec "DelSiTech Partnership" : doit matcher par contexte pure player + partnership
- Tester avec items non-pure players : ne doit pas matcher sans technology

### Impact Attendu
✅ **MedinCell malaria grant** → Matching contextuel → Newsletter  
✅ **Autres pure players avec contexte LAI** → Matching contextuel → Newsletter

---

## P0-4 : Fixer Normalisation HTML 🟡

### Problème Identifié
Certains items ont un summary vide après normalisation :
- "Nanexa/Moderna PharmaShell" : `"summary": ""`
- Cause probable : échec d'extraction HTML ou timeout Bedrock

### Cause Racine Probable
- URL non accessible ou contenu HTML complexe
- Timeout Bedrock ou erreur de parsing
- Extraction HTML défaillante

### Solution Recommandée
**Améliorer la robustesse de l'extraction HTML et gestion d'erreurs**

```python
# Dans src/lambdas/ingest_normalize/html_extractor.py
def extract_content_with_fallback(url, title):
    """Extraction HTML avec fallback sur le titre"""
    
    try:
        # Tentative extraction HTML normale
        content = extract_html_content(url)
        if content and len(content.strip()) > 50:
            return content
    except Exception as e:
        logger.warning(f"HTML extraction failed for {url}: {e}")
    
    # Fallback : utiliser le titre comme contenu minimal
    if title:
        fallback_content = f"Title: {title}\n\nContent extraction failed, using title for analysis."
        logger.info(f"Using title fallback for {url}")
        return fallback_content
    
    return None

# Dans src/lambdas/ingest_normalize/handler.py
def normalize_item_with_bedrock(item):
    """Normalisation avec gestion d'erreur améliorée"""
    
    raw_text = item.get('raw_text', '')
    title = item.get('title', '')
    
    # Si pas de contenu, essayer fallback
    if not raw_text or len(raw_text.strip()) < 50:
        raw_text = extract_content_with_fallback(item.get('url'), title)
    
    if not raw_text:
        # Dernier recours : créer un item minimal basé sur le titre
        return create_minimal_item_from_title(item)
    
    # Normalisation Bedrock normale
    return bedrock_normalize(raw_text, item)
```

### Validation
- Tester avec URL Nanexa/Moderna : doit avoir un summary non vide
- Tester avec URLs problématiques : doit utiliser fallback titre
- Vérifier que les items avec fallback peuvent quand même être matchés

### Impact Attendu
✅ **Nanexa/Moderna PharmaShell** → Summary non vide → Détection entities → Matching → Newsletter

---

## Séquence d'Implémentation Recommandée

### Sprint Immédiat (P0-1 + P0-2)
1. **Fixer détection technology Bedrock** (P0-1)
2. **Implémenter exclusions HR/finance** (P0-2)
3. **Tester avec run lai_weekly_v3**

**Objectif** : Newsletter avec UZEDY items + sans bruit HR

### Sprint Suivant (P0-3 + P0-4)
1. **Activer matching contextuel pure players** (P0-3)
2. **Fixer normalisation HTML** (P0-4)
3. **Test complet et validation**

**Objectif** : Newsletter complète avec tous les items LAI-strong

---

## Métriques de Validation Post-Corrections

### Après P0-1 + P0-2
- ✅ **UZEDY regulatory items** : Présents en newsletter
- ✅ **UZEDY growth items** : Présents en newsletter  
- ❌ **DelSiTech HR items** : Exclus de la newsletter
- ❌ **MedinCell finance items** : Exclus de la newsletter

### Après P0-3 + P0-4
- ✅ **Nanexa/Moderna PharmaShell** : Présent en newsletter
- ✅ **MedinCell malaria grant** : Présent en newsletter
- ✅ **Tous items LAI-strong** : Présents en newsletter
- ❌ **Bruit HR/finance** : <20% de la newsletter

### Objectif Final
- **Signaux LAI authentiques** : >80% (vs 20% actuel)
- **Items LAI-strong manqués** : 0 (vs 3-4 actuels)
- **Bruit HR/finance** : <10% (vs 80% actuel)

---

## Conclusion

Ces 4 recommandations P0 adressent les causes racines identifiées dans le diagnostic :

1. **P0-1** résout le problème principal de détection technology
2. **P0-2** élimine le bruit dominant HR/finance  
3. **P0-3** récupère les pure players avec contexte LAI implicite
4. **P0-4** résout les échecs de normalisation

**Avec P0-1 et P0-2 seulement**, la newsletter devrait déjà être significativement améliorée et utilisable pour le MVP.