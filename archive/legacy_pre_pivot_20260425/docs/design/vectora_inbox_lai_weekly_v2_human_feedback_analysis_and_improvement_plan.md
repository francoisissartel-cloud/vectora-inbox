# Vectora Inbox LAI Weekly v2 - Analyse Feedback Humain & Plan d'Amélioration

**Date** : 2025-12-11  
**Basé sur** : Annotations humaines de la feuille de revue lai_weekly_v2 Run #2  
**Objectif** : Plan par phases pour améliorer ingestion/matching/scoring selon critères métier

---

## Analyse des Patterns de Désaccord Humain-Moteur

### 🔴 **Problème Critique #1 : Signaux LAI Majeurs Manqués**

**Pattern identifié** : Items LAI-strong exclus de la newsletter
- **Nanexa/Moderna PharmaShell** : LAI-strong, high priority → Exclu (score ~5)
- **UZEDY regulatory** : LAI-strong, high priority → Exclu (score ~8)
- **MedinCell Malaria Grant** : LAI-strong, high priority → Exclu (score ~8)

**Cause racine** : Détection technology défaillante + matching trop restrictif

### 🔴 **Problème Critique #2 : Bruit HR/Finance Dominant**

**Pattern identifié** : Items noise inclus en newsletter
- **DelSiTech HR (2x)** : noise-HR, no → Inclus (score ~15)
- **MedinCell Finance** : noise-finance, no → Inclus (score ~10)

**Cause racine** : pure_player_bonus compense absence signaux LAI + exclusions insuffisantes

### 🔴 **Problème Critique #3 : Sur-Ingestion Non-LAI**

**Pattern identifié** : 12/15 items Table B annotés "non-LAI, no, low"
- Partnerships non-LAI (Pfizer GLP-1, Novartis dermatology)
- Manufacturing oral (Lilly GLP-1 factory)
- Clinical non-LAI (Roche oral SERD)

**Cause racine** : Profils d'ingestion trop larges + pas d'exclusion "oral"

### 🟡 **Problème Secondaire : Pure Players Context**

**Pattern identifié** : Désaccord sur pure players sans signaux LAI explicites
- **MedinCell Malaria** : Humain "LAI-strong" vs Moteur "excluded"
- **UZEDY news** : Humain "LAI-weak, yes" vs Moteur "excluded"

**Logique métier** : Pure players LAI utilisent toujours technologie LAI même si non explicite

---

## Plan d'Amélioration par Phases

### **PHASE 1 : Corrections Critiques Immédiate (P0)**
*Objectif : Capturer signaux LAI majeurs + éliminer bruit dominant*

#### 1.1 Enrichissement Technology Detection
**Fichier** : `canonical/scopes/technology_scopes.yaml`
```yaml
# Ajouts dans technology_terms_high_precision
- "PharmaShell®"          # Nanexa technology
- "SiliaShell®"           # Technology brand
- "BEPO®"                 # Technology brand
- "extended-release injectable"
- "long-acting injectable"
- "LAI"                   # Acronyme direct
- "depot injection"
- "once-monthly injection"
```

**Note** : UZEDY est déjà présent dans `lai_trademark_global` - vérifier que le matching utilise bien ce scope.

#### 1.2 Renforcement Exclusions Anti-LAI
**Fichier** : `canonical/scopes/exclusion_scopes.yaml`
```yaml
# Nouvelles exclusions anti-LAI
anti_lai_routes:
  - "oral tablet"
  - "oral capsule"  
  - "oral drug"
  - "oral medication"
  - "pill factory"
  - "tablet manufacturing"

# Renforcement exclusions HR/Finance
hr_recruitment_terms:
  - "hiring"
  - "seeks"
  - "recruiting"
  - "process engineer"
  - "quality director"

financial_reporting_terms:
  - "financial results"
  - "interim report"
  - "quarterly results"
  - "publishes.*results"
```

#### 1.3 Ajustement Scoring Pure Players
**Fichier** : `canonical/scoring/scoring_rules.yaml`
```yaml
# Logique pure players contextuelle
pure_player_bonus: 1.5              # Réduit de 2.0 à 1.5
pure_player_context_bonus: 3.0      # NOUVEAU : Bonus si contexte LAI implicite

# Bonus signaux LAI explicites
technology_bonus: 4.0               # Augmenté
molecule_bonus: 4.0                 # Augmenté
trademark_bonus: 5.0                # Augmenté
regulatory_bonus: 6.0               # Augmenté pour UZEDY type

# Malus anti-LAI
oral_route_penalty: -10             # NOUVEAU : Pénalité route orale
```

### **PHASE 2 : Amélioration Ingestion Sélective (P1)**
*Objectif : Réduire sur-ingestion non-LAI*

#### 2.1 Profils Ingestion Plus Sélectifs
**Fichier** : `canonical/ingestion/ingestion_profiles.yaml`
```yaml
technology_complex:
  # Critères plus stricts pour presse sectorielle
  sector_press_requirements:
    require_one_of:
      - lai_company_detected
      - lai_technology_detected  
      - lai_molecule_detected
      - lai_trademark_detected
    exclude_if:
      - oral_route_detected
      - anti_lai_terms_detected
  
  # Pure players : ingestion large mais scoring contextuel
  corporate_pure_players:
    ingest_all: true
    apply_context_scoring: true
```

#### 2.2 LLM Gating Amélioré
**Fichier** : Code Lambda `ingest_normalize`
```python
# Prompt Bedrock enrichi
ENHANCED_PROMPT = """
...existing prompt...

For LAI relevance assessment:
- Score 8-10: Direct LAI technology, molecules, regulatory milestones
- Score 6-7: Pure LAI players with implicit LAI context (grants, partnerships)
- Score 4-5: Hybrid companies with LAI-adjacent content
- Score 0-3: Non-LAI content (oral routes, unrelated partnerships)

Detect anti-LAI signals:
- "oral", "tablet", "pill", "capsule" = strong anti-LAI
- "topical", "nasal", "inhalation" = anti-LAI

Include fields:
"lai_relevance_score": 0-10,
"anti_lai_detected": boolean,
"pure_player_context": boolean
"""
```

### **PHASE 3 : Matching Contextuel Intelligent (P1)**
*Objectif : Matching adapté au type de company*

#### 3.1 Matching Rules Différenciées
**Fichier** : Code Lambda `engine` ou configuration
```python
def contextual_matching(item):
    """Matching adapté au type de company"""
    
    # Pure players LAI : logique contextuelle
    if item.is_pure_player_lai():
        # Signaux LAI explicites OU contexte LAI implicite
        has_explicit_lai = (item.technologies_detected or 
                           item.molecules_detected or 
                           item.trademarks_detected)
        
        has_implicit_context = (
            item.lai_relevance_score >= 6 or
            item.pure_player_context or
            item.event_type in ['regulatory', 'partnership', 'clinical_update']
        )
        
        return has_explicit_lai or has_implicit_context
    
    # Hybrid companies : signaux LAI explicites requis
    elif item.is_hybrid_company():
        return (item.technologies_detected and 
                item.lai_relevance_score >= 5 and
                not item.anti_lai_detected)
    
    # Autres : signaux LAI forts requis
    else:
        return (item.technologies_detected and 
                item.lai_relevance_score >= 7)
```

#### 3.2 Vérification Trademark Detection
**Fichier** : `canonical/scopes/trademark_scopes.yaml`

**Action** : Vérifier que UZEDY est bien présent dans `lai_trademarks_global` et que la phase de matching utilise correctement ce scope.

```yaml
# Pattern matching pour LAI (si pas déjà présent)
- ".*LAI$"              # Suffixe LAI
- ".*Injectable$"       # Suffixe Injectable
- ".*Depot$"           # Suffixe Depot
```

**Note** : PharmaShell®, SiliaShell® et BEPO® sont des marques technologiques, pas des médicaments - elles sont ajoutées dans technology_scopes.yaml.

### **PHASE 4 : Scoring Contextuel Avancé (P2)**
*Objectif : Scoring nuancé selon contexte métier*

#### 4.1 Scoring Multi-Dimensionnel
**Fichier** : `canonical/scoring/scoring_rules.yaml`
```yaml
# Scoring contextuel par type de company
contextual_scoring:
  pure_players:
    base_bonus: 2.0
    context_multipliers:
      regulatory_milestone: 3.0      # UZEDY approvals
      partnership_bigpharma: 2.5     # Nanexa/Moderna
      grant_funding: 2.0             # MedinCell malaria
      clinical_update: 2.0
      
  hybrid_companies:
    base_bonus: 1.0
    require_explicit_lai: true
    
  unknown_companies:
    base_bonus: 0.5
    require_strong_lai: true

# Pénalités contextuelles
contextual_penalties:
  hr_content: -5.0
  financial_only: -3.0
  conference_only: -2.0
  anti_lai_route: -10.0
```

#### 4.2 Scoring Temporel et Récence
```yaml
# Bonus récence pour signaux forts
recency_bonuses:
  regulatory_milestone:
    0_7_days: 2.0
    8_30_days: 1.0
    
  partnership_announcement:
    0_7_days: 1.5
    8_30_days: 0.5
```

---

## Séquence d'Implémentation

### **Sprint 1 (Immédiat) : Phase 1 - Corrections Critiques**
- ✅ Technology scopes enrichis (PharmaShell®, SiliaShell®, BEPO®, LAI)
- ✅ Vérification UZEDY dans lai_trademark_global et matching
- ✅ Exclusions anti-LAI (oral routes)
- ✅ Scoring ajusté (pure_player_bonus réduit, technology_bonus augmenté)
- 🎯 **Objectif** : Nanexa/Moderna en newsletter, bruit HR éliminé

### **Sprint 2 (1 semaine) : Phase 2 - Ingestion Sélective**
- Profils ingestion plus stricts pour presse sectorielle
- LLM gating avec lai_relevance_score et anti_lai_detected
- 🎯 **Objectif** : Réduction 50% sur-ingestion non-LAI

### **Sprint 3 (2 semaines) : Phase 3 - Matching Contextuel**
- Matching rules différenciées par type company
- Vérification trademark detection et pattern-based
- 🎯 **Objectif** : Pure players contextuels matchés, hybrid companies filtrés

### **Sprint 4 (1 mois) : Phase 4 - Scoring Avancé**
- Scoring multi-dimensionnel contextuel
- Bonus/malus temporels et thématiques
- 🎯 **Objectif** : Newsletter optimale avec priorités métier

### **Sprint 5 (1 semaine) : Phase 5 - Tests & Validation**
- Test complet du pipeline avec les modifications
- Nouveau run et génération de newsletter
- Comparaison avec anciennes newsletters
- Mesure de progression sur métriques clés
- 🎯 **Objectif** : Validation des améliorations avant déploiement

---

## Métriques de Validation

### **Après Phase 1**
- Nanexa/Moderna présent en newsletter ✅
- Bruit HR/finance <20% ✅
- Signaux LAI authentiques >60% ✅

### **Après Phase 2**
- Items non-LAI ingérés <30% (vs 70% actuel)
- Précision ingestion >80%

### **Après Phase 3**
- Pure players contextuels matchés >90%
- Hybrid companies sans LAI filtrés >80%

### **Après Phase 5 - Tests & Validation**
- Comparaison newsletter avant/après modifications
- Métriques de progression :
  - Signaux LAI majeurs capturés : >95%
  - Bruit HR/Finance éliminé : >80%
  - Précision globale newsletter : >85%
- Validation satisfaisante → Proposition déploiement AWS

---

## Phase 5 : Tests & Validation Complète

### **5.1 Protocole de Test**
```bash
# 1. Backup configuration actuelle
aws s3 cp s3://vectora-inbox-config/ s3://vectora-inbox-config-backup/ --recursive

# 2. Déploiement modifications test
# - technology_scopes.yaml (PharmaShell®, SiliaShell®, BEPO®)
# - Vérification lai_trademark_global (UZEDY)
# - exclusion_scopes.yaml (anti-LAI routes)
# - scoring_rules.yaml (ajustements)

# 3. Run test complet
# Période test : même période que Run #2 pour comparaison
```

### **5.2 Génération Newsletter Test**
- Exécution pipeline complet avec nouvelles configurations
- Génération newsletter test sur même période que Run #2
- Export résultats pour comparaison

### **5.3 Analyse Comparative**
**Métriques de comparaison** :
```yaml
comparison_metrics:
  lai_signals_captured:
    before: "Nanexa/Moderna: excluded, UZEDY: excluded, MedinCell: excluded"
    after: "Nanexa/Moderna: included, UZEDY: included, MedinCell: included"
    
  noise_reduction:
    before: "DelSiTech HR: included, MedinCell Finance: included"
    after: "DelSiTech HR: excluded, MedinCell Finance: excluded"
    
  precision_improvement:
    before: "12/15 items non-LAI in newsletter"
    after: "<5/15 items non-LAI in newsletter"
```

### **5.4 Critères de Validation**
**Seuils de satisfaction** :
- ✅ Nanexa/Moderna PharmaShell® : Présent en newsletter
- ✅ UZEDY regulatory : Présent en newsletter  
- ✅ MedinCell Malaria Grant : Présent en newsletter
- ✅ Bruit HR DelSiTech : Exclu de newsletter
- ✅ Bruit Finance MedinCell : Exclu de newsletter
- ✅ Items non-LAI : <30% de la newsletter (vs 80% avant)

### **5.5 Proposition Déploiement AWS**
Si validation satisfaisante :
```bash
# Déploiement production
1. Backup configuration production
2. Déploiement configurations validées
3. Monitoring première newsletter production
4. Rollback plan si nécessaire
```

**Livrable final** : Rapport de validation + recommandation déploiement AWS

### **Après Phase 4**
- Newsletter 80-90% signaux LAI authentiques
- Accord humain-moteur >85%
- Temps annotation <20 min/session

---

## Conclusion

**Stratégie** : Corrections immédiates (Phase 1) puis amélioration progressive de la sélectivité et du contexte.

**Priorité absolue** : Capturer Nanexa/Moderna + éliminer bruit HR/finance = Newsletter utilisable.

**Vision long-terme** : Moteur contextuel qui comprend les nuances métier LAI (pure players vs hybrid, explicite vs implicite).