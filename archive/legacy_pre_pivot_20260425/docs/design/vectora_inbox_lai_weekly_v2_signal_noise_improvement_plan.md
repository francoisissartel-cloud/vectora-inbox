# Vectora Inbox LAI Weekly v2 - Plan d'Amélioration Signal/Noise

**Date** : 2025-12-11  
**Objectif** : Propositions concrètes pour améliorer le ratio signal/noise de la newsletter LAI  
**Status** : DESIGN SEULEMENT - Pas d'implémentation à ce stade

---

## Diagnostic de base

**Newsletter Run #2** :
- ✅ 1/5 items LAI authentiques (20%)
- ❌ 4/5 items bruit (80% - HR, finance, corporate)
- ❌ Signal LAI majeur manquant (Nanexa/Moderna)

**Objectif Run #3** :
- ✅ 3-4/5 items LAI authentiques (60-80%)
- ✅ 1-2/5 items corporate utiles (20-40%)
- ✅ Signaux LAI majeurs présents

---

## PHASE P0 : Ajustements Faible Risque / Fort Impact

### 1. Renforcement exclusion_scopes.yaml

**Fichier** : `canonical/scopes/exclusion_scopes.yaml`

**Ajouts proposés** :
```yaml
# Nouvelles exclusions HR
hr_recruitment_terms:
  - "hiring"
  - "seeks"
  - "recruiting" 
  - "job opening"
  - "career opportunities"
  - "position available"
  - "we are looking for"
  - "join our team"

# Nouvelles exclusions Finance
financial_reporting_terms:
  - "financial results"
  - "earnings"
  - "consolidated results"
  - "interim report"
  - "quarterly results"
  - "half-year results"
  - "revenue"
  - "guidance"
  - "financial performance"

# Exclusions Corporate générique
corporate_generic_terms:
  - "leadership change"
  - "CEO departure"
  - "board appointment"
  - "organizational restructuring"
  - "management transition"
```

**Bénéfice attendu** : Filtrage automatique 60-70% du bruit HR/finance  
**Risque** : Faible - Exclusions spécifiques et conservatrices  
**Effort** : 15 minutes

---

### 2. Réduction pure_player_bonus

**Fichier** : `canonical/scoring/scoring_rules.yaml`

**Ajustement proposé** :
```yaml
# Configuration actuelle (hypothèse)
pure_player_bonus: 5.0  # TROP ÉLEVÉ

# Configuration proposée
pure_player_bonus: 2.0  # Réduit de 60%

# Rééquilibrage compensatoire
technology_bonus: 3.0   # Augmenté (était probablement 2.0)
molecule_bonus: 4.0     # Augmenté (était probablement 3.0)
partnership_bonus: 3.0  # Augmenté (était probablement 1.5)
regulatory_bonus: 4.0   # Augmenté pour NDA/approvals
```

**Logique** : Pure players doivent avoir du contenu LAI pour scorer haut, pas juste être des pure players.

**Bénéfice attendu** : Items pure players sans signaux LAI descendent sous le seuil newsletter  
**Risque** : Moyen - Peut affecter légitimes items pure players  
**Effort** : 5 minutes

---

### 3. Enrichissement technology_scopes.yaml

**Fichier** : `canonical/scopes/technology_scopes.yaml`

**Ajouts proposés** :
```yaml
# Termes manquants identifiés via Nanexa/Moderna
drug_delivery_platforms:
  - "PharmaShell"
  - "drug delivery"
  - "controlled release"
  - "sustained release"
  - "extended release"
  - "modified release"
  - "long-acting"
  - "depot formulation"

# Termes techniques LAI génériques
lai_technology_terms:
  - "injectable suspension"
  - "extended-release injectable"
  - "once-monthly"
  - "once-quarterly"
  - "long-acting injectable"
  - "LAI"
  - "depot injection"
```

**Bénéfice attendu** : Nanexa/Moderna et items similaires détectés comme LAI  
**Risque** : Faible - Termes spécifiques LAI  
**Effort** : 10 minutes

---

### 4. Enrichissement trademark_scopes.yaml

**Fichier** : `canonical/scopes/trademark_scopes.yaml`

**Ajouts proposés** :
```yaml
lai_trademarks_global:
  # Ajouts pour Nanexa
  - "PharmaShell"
  - "PharmaShell®"
  
  # Autres trademarks LAI manquants potentiels
  - "BEPO"           # DelSiTech
  - "SiliaShell"     # DelSiTech  
  - "UZEDY"          # MedinCell/Teva
  - "BEPO®"
  - "SiliaShell®"
  - "UZEDY®"
```

**Bénéfice attendu** : Détection trademark améliore matching et scoring  
**Risque** : Faible - Trademarks vérifiés  
**Effort** : 5 minutes

---

### 5. Ajustement seuil matching (si configurable)

**Fichier** : `canonical/matching/domain_matching_rules.yaml`

**Ajustement proposé** :
```yaml
tech_lai_ecosystem:
  # Configuration actuelle (hypothèse)
  minimum_signals: 1
  
  # Configuration proposée
  minimum_signals_pure_player: 2    # Pure players need company + 1 LAI signal
  minimum_signals_hybrid: 1         # Hybrid companies more flexible
  
  # Ou alternative plus simple
  require_lai_signal_for_pure_players: true
```

**Bénéfice attendu** : Pure players sans signaux LAI ne matchent plus  
**Risque** : Moyen - Peut exclure items légitimes  
**Effort** : Variable selon implémentation actuelle

---

## PHASE P1 : Améliorations Structurelles

### 1. Amélioration Bedrock Prompt (Normalisation)

**Fichier** : Code Lambda `ingest_normalize` 

**Enhancement proposé** :
```python
# Ajout au prompt Bedrock
ENHANCED_PROMPT = """
...existing prompt...

Additionally, classify the content type:
- technical: R&D, clinical trials, regulatory approvals, partnerships, technology
- hr: recruitment, hiring, job postings, personnel announcements  
- finance: earnings, financial results, revenue, guidance
- corporate: leadership changes, awards, general corporate news

Score LAI relevance (0-10):
- 8-10: Direct LAI technology, molecules, or regulatory milestones
- 5-7: LAI companies with technical/partnership content
- 2-4: LAI companies with corporate updates
- 0-1: Pure HR, finance, or generic content

Include in response:
"content_type": "technical|hr|finance|corporate",
"lai_relevance_score": 0-10
"""
```

**Bénéfice attendu** : Détection explicite du type de contenu + scoring de pertinence  
**Risque** : Moyen - Changement de prompt peut affecter autres détections  
**Effort** : 2 heures (dev + test)

---

### 2. Scoring Contextuel Avancé

**Fichier** : `canonical/scoring/scoring_rules.yaml`

**Nouveaux paramètres proposés** :
```yaml
# Malus par type de contenu
content_type_adjustments:
  hr: -3.0              # Forte pénalité HR
  finance: -1.5         # Pénalité modérée finance
  corporate: -0.5       # Légère pénalité corporate
  technical: +1.0       # Bonus contenu technique

# Bonus LAI relevance score
lai_relevance_multiplier: 0.5  # Score final *= (1 + lai_relevance_score * 0.5)

# Bonus partnerships
partnership_detection_bonus: 2.0  # "license agreement", "partnership", "collaboration"
```

**Bénéfice attendu** : Scoring discriminant basé sur contenu réel  
**Risque** : Élevé - Changement majeur logique scoring  
**Effort** : 4 heures (dev + test)

---

### 3. Matching Rules Discriminantes

**Fichier** : Code Lambda `engine` ou configuration

**Logique proposée** :
```python
def enhanced_matching_logic(item):
    """Enhanced matching with content-aware rules"""
    
    base_match = item.company_in_scope('lai_companies_global')
    if not base_match:
        return False
    
    # Pure players need LAI signals
    if item.company_type == 'pure_player':
        has_lai_signal = (
            item.technologies_detected or 
            item.molecules_detected or 
            item.trademarks_detected or
            item.lai_relevance_score >= 6
        )
        return has_lai_signal
    
    # Hybrid companies more flexible
    else:
        return item.lai_relevance_score >= 4
```

**Bénéfice attendu** : Matching basé sur contenu, pas juste company  
**Risque** : Élevé - Changement logique core  
**Effort** : 6 heures (dev + test)

---

### 4. Auto-enrichissement Scopes

**Fichier** : Nouveau module `scope_enhancement.py`

**Fonctionnalité proposée** :
```python
def auto_enhance_scopes(newsletter_items, feedback_scores):
    """Auto-detect missing LAI terms from high-scoring items"""
    
    # Extract terms from items with high LAI relevance
    high_relevance_items = [item for item in newsletter_items 
                           if item.lai_relevance_score >= 8]
    
    # NLP extraction of technical terms
    candidate_terms = extract_technical_terms(high_relevance_items)
    
    # Suggest additions to technology_scopes
    return {
        'technology_terms': candidate_terms,
        'confidence_scores': calculate_confidence(candidate_terms)
    }
```

**Bénéfice attendu** : Amélioration continue sans maintenance manuelle  
**Risque** : Élevé - Complexité + faux positifs  
**Effort** : 2 jours (dev + test)

---

## Stratégie de Déploiement

### Étape 1 : P0 Immédiat (Run #3)
1. **exclusion_scopes.yaml** : Ajout termes HR/finance
2. **scoring_rules.yaml** : pure_player_bonus 5.0 → 2.0
3. **technology_scopes.yaml** : Ajout PharmaShell + drug delivery
4. **trademark_scopes.yaml** : Ajout PharmaShell®
5. **Test Run #3** : Validation impact

**Timeline** : 30 minutes config + 1h test  
**Risque** : Faible  
**Impact attendu** : Newsletter avec 60-80% signaux LAI

### Étape 2 : P1 Structurel (Run #4)
1. **Bedrock prompt** : Content type + LAI relevance
2. **Scoring contextuel** : Malus HR/finance + bonus relevance
3. **Test Run #4** : Validation complète

**Timeline** : 1 jour dev + test  
**Risque** : Moyen  
**Impact attendu** : Newsletter avec 80-90% signaux LAI

### Étape 3 : P1 Avancé (Run #5+)
1. **Matching discriminant** : Logique content-aware
2. **Auto-enhancement** : Learning continu
3. **Monitoring** : Métriques qualité

**Timeline** : 1 semaine dev + test  
**Risque** : Élevé  
**Impact attendu** : Newsletter robuste long-terme

---

## Métriques de Validation

### Run #3 (Post P0)
- **Bruit HR** : 0% (actuellement 40%)
- **Bruit Finance** : <10% (actuellement 20%)
- **Signaux LAI** : >60% (actuellement 20%)
- **Nanexa/Moderna** : Présent dans newsletter

### Run #4 (Post P1)
- **Bruit total** : <20% (actuellement 80%)
- **Signaux LAI** : >80% (actuellement 20%)
- **Cohérence temporelle** : Stable sur 3 runs consécutifs

### Long-terme
- **Newsletter utilisable** : Veille LAI opérationnelle
- **Maintenance minimale** : Auto-adaptation
- **Couverture complète** : Signaux majeurs captés

---

## Points d'Attention

### Risques P0
- **Over-exclusion** : Exclusions trop strictes peuvent éliminer contenu légitime
- **Pure player impact** : Réduction bonus peut affecter items légitimes
- **Validation nécessaire** : Test sur plusieurs runs pour stabilité

### Risques P1
- **Prompt stability** : Changements Bedrock peuvent affecter autres détections
- **Scoring complexity** : Logique complexe = plus de bugs potentiels
- **Performance** : Calculs additionnels peuvent ralentir pipeline

### Mitigations
- **Rollback plan** : Sauvegarde configurations actuelles
- **A/B testing** : Comparaison avant/après sur mêmes données
- **Monitoring** : Alertes sur métriques qualité

---

## Conclusion

**Approche recommandée** : Déploiement progressif P0 → P1 avec validation à chaque étape.

**Impact attendu P0** : Amélioration immédiate 60-80% avec risque minimal.

**Impact attendu P1** : Newsletter LAI opérationnelle avec 80-90% signaux authentiques.

**Validation critique** : Run #3 avec corrections P0 doit montrer Nanexa/Moderna dans newsletter et réduction drastique bruit HR/finance.