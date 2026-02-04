# Évaluation et Recommandations d'Amélioration - Fichiers Canonical

**Date**: 2026-02-03  
**Contexte**: Analyse post-test E2E v13 (29 items)  
**Objectif**: Améliorer qualité ingestion, normalisation et domain scoring via fichiers canonical uniquement  
**Périmètre**: Modifications SANS toucher au code Lambda

---

## 📊 SYNTHÈSE EXÉCUTIVE

### Résultats Test E2E v13
- **Items traités**: 29 items
- **Items matchés**: 14 (48%)
- **Problèmes identifiés**: 7 cas critiques nécessitant corrections

### Problèmes Critiques Identifiés

| # | Problème | Type | Impact | Priorité |
|---|----------|------|--------|----------|
| 1 | Faux positifs "manufacturing injectable" | Scoring | Bruit newsletter | 🔴 HAUTE |
| 2 | Mots-clés LAI non détectés ("once-weekly", "once-monthly") | Normalisation | Faux négatifs | 🔴 HAUTE |
| 3 | Hallucinations Bedrock (microspheres non mentionnées) | Prompt | Confiance scoring | 🟠 MOYENNE |
| 4 | URL alternative non ingérée (FierceBiotech) | Ingestion | Perte contenu riche | 🟠 MOYENNE |
| 5 | Résultats financiers pure players matchés | Scoring | Bruit newsletter | 🟡 BASSE |
| 6 | Signaux "hybrid company" trop génériques | Scoring | Faux positifs | 🟡 BASSE |
| 7 | Contenu HTML incomplet (extraction partielle) | Ingestion | Perte signaux | 🟠 MOYENNE |

---

## 🔍 ANALYSE DÉTAILLÉE PAR ÉTAPE

### 1. INGESTION

#### 1.1 Problème: URL Alternative Non Ingérée

**Cas**: AstraZeneca/CSPC partnership
- ❌ **Ingéré**: `endpoints.news` (contenu minimal)
- ✅ **Manqué**: `fiercebiotech.com` (contenu riche avec "once-monthly dosing platform")

**Cause**: Source catalog ne liste qu'une URL par source

**Impact**: Perte de signaux LAI critiques présents dans version alternative

**Recommandation**: 
```yaml
# Ajouter dans source_catalog.yaml
alternative_urls:
  - url: "https://www.fiercebiotech.com/"
    priority: "high"
    reason: "Contenu plus détaillé que Endpoints"
```

#### 1.2 Problème: Extraction HTML Incomplète

**Cas**: Plusieurs items corporate avec contenu tronqué

**Cause**: `max_content_length: 1000` trop restrictif

**Recommandation**:
```yaml
# Dans source_catalog.yaml - sources corporate
max_content_length: 2000  # Augmenter de 1000 → 2000
content_enrichment: "full_article"  # Au lieu de "summary_enhanced"
```

#### 1.3 Problème: Bruit Financier/RH Non Filtré

**Cas**: 
- "Publication of 2026 financial calendar" (MedinCell)
- "Medincell to Join MSCI World Small Cap Index"
- "Nanexa publishes interim report"

**Cause**: Profil `corporate_pure_player_broad` trop permissif

**Recommandation**:
```yaml
# Dans ingestion_profiles.yaml
corporate_pure_player_broad:
  exclusion_scopes:
    - "exclusion_scopes.financial_reporting_terms"  # ✅ Déjà présent
    - "exclusion_scopes.stock_market_terms"  # 🆕 AJOUTER
```

**Nouveau scope à créer**:
```yaml
# Dans exclusion_scopes.yaml
stock_market_terms:
  description: "Termes boursiers/indices sans contenu LAI"
  keywords:
    - "MSCI"
    - "stock index"
    - "market cap"
    - "financial calendar"
    - "interim report"
    - "quarterly report"
    - "half-year results"
    - "consolidated results"
```

---

### 2. NORMALISATION

#### 2.1 Problème CRITIQUE: Mots-Clés LAI Non Détectés

**Cas 1**: Novo Nordisk CagriSema
- **Texte source**: "A **once-weekly shot** of CagriSema"
- **Détecté**: ❌ Aucun signal LAI
- **Attendu**: ✅ `once-weekly` = MEDIUM signal

**Cas 2**: Quince steroid therapy
- **Titre**: "experimental **once-monthly** steroid-based treatment"
- **Détecté**: ❌ Aucun signal LAI
- **Attendu**: ✅ `once-monthly` = MEDIUM signal

**Cause**: Prompt normalisation ne demande PAS explicitement d'extraire dosing intervals

**Impact**: Faux négatifs sur items LAI légitimes

**Recommandation CRITIQUE**:

```yaml
# Dans generic_normalization.yaml
user_template: |
  4. ENTITY EXTRACTION (ALL explicitly mentioned)
     - Companies: ALL pharmaceutical/biotech company names
     - Molecules: ALL drug/molecule names (INN, generic names)
     - Technologies: ALL technology keywords (e.g., "microspheres", "PEGylation")
     - Trademarks: ALL commercial product names (e.g., "UZEDY®", "Ozempic")
     - Indications: ALL therapeutic indications/diseases mentioned
     - Dosing Intervals: ALL dosing frequency terms (e.g., "once-weekly", "once-monthly", "q4w", "quarterly")  # 🆕 AJOUTER
```

**Ajout dans response format**:
```json
{
  "dosing_intervals_detected": ["once-weekly", "once-monthly"]  // 🆕 AJOUTER
}
```

#### 2.2 Problème: Hallucinations Bedrock

**Cas**: AstraZeneca/CSPC
- **Bedrock dit**: "Microsphere technology mentioned"
- **Texte réel**: Aucune mention de "microspheres"

**Cause**: Prompt scoring trop permissif, Bedrock infère au lieu d'extraire

**Recommandation**:

```yaml
# Dans lai_domain_scoring.yaml
system_instructions: |
  CRITICAL RULES:
  1. Only detect signals EXPLICITLY present in the text
  2. DO NOT infer or hallucinate signals
  3. If a technology is not mentioned by name, do NOT add it to signals_detected
  4. Base your evaluation ONLY on normalized entities provided
```

---

### 3. DOMAIN SCORING

#### 3.1 Problème: Faux Positifs "Manufacturing Injectable"

**Cas**: Eli Lilly manufacturing facilities
- **Texte**: "manufacturing facility for injectable drugs and devices"
- **Score**: 80/100 (MATCHÉ)
- **Attendu**: 0 (NON MATCHÉ)

**Cause**: Signal "hybrid_company: Eli Lilly" suffit pour scorer haut

**Recommandation**:

```yaml
# Dans lai_domain_definition.yaml
exclusions:
  - "oral tablet"
  - "oral capsule"
  # ... existants
  - "manufacturing facility"  # 🆕 AJOUTER
  - "production plant"  # 🆕 AJOUTER
  - "factory construction"  # 🆕 AJOUTER

# Nouvelle règle de contexte
context_rules:
  - id: rule_manufacturing_only
    condition: "event_type == 'corporate_move' AND ('manufacturing' OR 'factory' OR 'plant') AND NO technology_signals"
    action: "reject (manufacturing without LAI technology)"
```

#### 3.2 Problème: Résultats Financiers Pure Players

**Cas**: MedinCell financial results
- **Score**: 55/100 (MATCHÉ)
- **Attendu**: 0 (NON MATCHÉ)

**Cause**: `event_type: financial_results` a base_score = 30, pure player boost = 25 → Total 55

**Recommandation**:

```yaml
# Dans lai_domain_definition.yaml
scoring:
  event_type_base_scores:
    financial_results: 0  # 🔧 MODIFIER: 30 → 0
    
  # Nouvelle règle stricte
  event_type_requirements:
    financial_results:
      require_signals: ["strong", "medium"]  # 🆕 AJOUTER
      min_signal_count: 2
      reasoning: "Financial results need explicit LAI content to be relevant"
```

#### 3.3 Problème: Signaux "Hybrid Company" Trop Génériques

**Cas**: Eli Lilly, Novo Nordisk matchés sans contenu LAI

**Cause**: Signal "hybrid_company" donne +10 points même sans contexte LAI

**Recommandation**:

```yaml
# Dans lai_domain_definition.yaml
scoring:
  entity_boosts:
    hybrid_company: 5  # 🔧 MODIFIER: 10 → 5 (réduire poids)
    
  # Nouvelle règle de combinaison
  boost_combination_rules:
    - id: hybrid_company_boost
      condition: "hybrid_company detected"
      requires_additional: ["technology_family", "dosing_interval", "key_molecule"]
      reasoning: "Hybrid companies need LAI-specific context"
```

---

## 📋 PLAN D'AMÉLIORATION PRIORISÉ

### Phase 1: Corrections Critiques (Impact Immédiat)

**Priorité 🔴 HAUTE - À faire en premier**

1. **Normalisation: Ajouter extraction dosing intervals**
   - Fichier: `canonical/prompts/normalization/generic_normalization.yaml`
   - Changement: Ajouter `dosing_intervals_detected` dans extraction
   - Impact: Résout faux négatifs CagriSema, Quince

2. **Scoring: Exclure manufacturing sans tech LAI**
   - Fichier: `canonical/domains/lai_domain_definition.yaml`
   - Changement: Ajouter exclusions manufacturing + règle contextuelle
   - Impact: Résout faux positifs Eli Lilly

3. **Scoring: Réduire poids financial_results**
   - Fichier: `canonical/domains/lai_domain_definition.yaml`
   - Changement: `financial_results: 30 → 0`
   - Impact: Résout faux positifs MedinCell financial

### Phase 2: Améliorations Qualité (Impact Moyen)

**Priorité 🟠 MOYENNE**

4. **Ingestion: Filtrer bruit boursier**
   - Fichier: `canonical/scopes/exclusion_scopes.yaml`
   - Changement: Créer `stock_market_terms` scope
   - Impact: Réduit bruit corporate pure players

5. **Normalisation: Prévenir hallucinations**
   - Fichier: `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
   - Changement: Renforcer instructions "EXPLICIT ONLY"
   - Impact: Améliore fiabilité signaux détectés

6. **Ingestion: Augmenter max_content_length**
   - Fichier: `canonical/sources/source_catalog.yaml`
   - Changement: `1000 → 2000` pour sources corporate
   - Impact: Capture plus de signaux LAI

### Phase 3: Optimisations Avancées (Impact Faible)

**Priorité 🟡 BASSE**

7. **Scoring: Réduire poids hybrid_company**
   - Fichier: `canonical/domains/lai_domain_definition.yaml`
   - Changement: `hybrid_company: 10 → 5`
   - Impact: Réduit faux positifs hybrid sans contexte

8. **Ingestion: Ajouter URLs alternatives**
   - Fichier: `canonical/sources/source_catalog.yaml`
   - Changement: Ajouter `alternative_urls` pour sources clés
   - Impact: Capture versions plus riches des news

---

## 🎯 MODIFICATIONS CONCRÈTES RECOMMANDÉES

### Modification 1: generic_normalization.yaml

**Localisation**: `canonical/prompts/normalization/generic_normalization.yaml`

**Changement**:
```yaml
# AVANT (ligne ~35)
  4. ENTITY EXTRACTION (ALL explicitly mentioned)
     - Companies: ALL pharmaceutical/biotech company names
     - Molecules: ALL drug/molecule names (INN, generic names)
     - Technologies: ALL technology keywords (e.g., "microspheres", "PEGylation")
     - Trademarks: ALL commercial product names (e.g., "UZEDY®", "Ozempic")
     - Indications: ALL therapeutic indications/diseases mentioned

# APRÈS
  4. ENTITY EXTRACTION (ALL explicitly mentioned)
     - Companies: ALL pharmaceutical/biotech company names
     - Molecules: ALL drug/molecule names (INN, generic names)
     - Technologies: ALL technology keywords (e.g., "microspheres", "PEGylation")
     - Trademarks: ALL commercial product names (e.g., "UZEDY®", "Ozempic")
     - Indications: ALL therapeutic indications/diseases mentioned
     - Dosing Intervals: ALL dosing frequency terms explicitly mentioned
       Examples: "once-weekly", "once-monthly", "once every 3 months", "q4w", "q8w", "quarterly"
       CRITICAL: Only extract if EXPLICITLY stated in text
```

**Changement response format**:
```yaml
# AVANT (ligne ~50)
  {
    "summary": "...",
    "extracted_date": "2026-01-27",
    "date_confidence": 0.95,
    "event_type": "partnership",
    "companies_detected": ["Company A", "Company B"],
    "molecules_detected": ["Molecule X"],
    "technologies_detected": ["Technology Y"],
    "trademarks_detected": ["Trademark Z"],
    "indications_detected": ["Indication W"]
  }

# APRÈS
  {
    "summary": "...",
    "extracted_date": "2026-01-27",
    "date_confidence": 0.95,
    "event_type": "partnership",
    "companies_detected": ["Company A", "Company B"],
    "molecules_detected": ["Molecule X"],
    "technologies_detected": ["Technology Y"],
    "trademarks_detected": ["Trademark Z"],
    "indications_detected": ["Indication W"],
    "dosing_intervals_detected": ["once-weekly", "once-monthly"]
  }
```

---

### Modification 2: lai_domain_definition.yaml

**Localisation**: `canonical/domains/lai_domain_definition.yaml`

**Changement 1 - Exclusions**:
```yaml
# AVANT (ligne ~80)
exclusions:
  - "oral tablet"
  - "oral capsule"
  - "oral administration"
  - "transdermal patch"
  - "nasal spray"
  - "sublingual"
  - "inhalation"

# APRÈS
exclusions:
  - "oral tablet"
  - "oral capsule"
  - "oral administration"
  - "transdermal patch"
  - "nasal spray"
  - "sublingual"
  - "inhalation"
  # Manufacturing without LAI context
  - "manufacturing facility"
  - "production plant"
  - "factory construction"
  - "plant expansion"
```

**Changement 2 - Scoring**:
```yaml
# AVANT (ligne ~100)
  event_type_base_scores:
    partnership: 60
    regulatory: 70
    clinical_update: 50
    corporate_move: 40
    financial_results: 30
    other: 20

# APRÈS
  event_type_base_scores:
    partnership: 60
    regulatory: 70
    clinical_update: 50
    corporate_move: 40
    financial_results: 0  # 🔧 MODIFIÉ: 30 → 0
    other: 20
```

**Changement 3 - Entity Boosts**:
```yaml
# AVANT (ligne ~110)
  entity_boosts:
    pure_player_company: 25
    trademark_mention: 20
    key_molecule: 15
    hybrid_company: 10
    technology_family: 10

# APRÈS
  entity_boosts:
    pure_player_company: 25
    trademark_mention: 20
    key_molecule: 15
    dosing_interval: 15  # 🆕 AJOUTÉ
    hybrid_company: 5    # 🔧 MODIFIÉ: 10 → 5
    technology_family: 10
```

**Changement 4 - Nouvelle règle contextuelle**:
```yaml
# APRÈS matching_rules (ligne ~95)
matching_rules:
  - id: rule_1
    condition: "1+ strong signal detected"
    action: "match with high confidence"
    
  - id: rule_2
    condition: "2+ medium signals detected"
    action: "match with medium confidence"
    
  - id: rule_3
    condition: "3+ weak signals detected AND 0 exclusions"
    action: "match with low confidence"
    
  - id: rule_4
    condition: "1+ exclusion detected"
    action: "reject (not LAI)"
  
  # 🆕 NOUVELLE RÈGLE
  - id: rule_5
    condition: "event_type == 'financial_results' AND signals_detected < 2"
    action: "reject (financial results need explicit LAI content)"
  
  # 🆕 NOUVELLE RÈGLE
  - id: rule_6
    condition: "event_type == 'corporate_move' AND manufacturing_terms AND NO technology_signals"
    action: "reject (manufacturing without LAI technology)"
```

---

### Modification 3: lai_domain_scoring.yaml

**Localisation**: `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`

**Changement**:
```yaml
# AVANT (ligne ~10)
system_instructions: |
  You are a specialized AI assistant for evaluating biotech/pharma news relevance 
  to the Long-Acting Injectables (LAI) domain.
  
  Your task: Determine if an item is LAI-relevant and assign a relevance score (0-100).

# APRÈS
system_instructions: |
  You are a specialized AI assistant for evaluating biotech/pharma news relevance 
  to the Long-Acting Injectables (LAI) domain.
  
  Your task: Determine if an item is LAI-relevant and assign a relevance score (0-100).
  
  CRITICAL RULES FOR SIGNAL DETECTION:
  1. Only detect signals EXPLICITLY present in the normalized item
  2. DO NOT infer, assume, or hallucinate signals not provided
  3. If a technology/molecule/term is not in the entities_detected, DO NOT add it
  4. Base your evaluation ONLY on the normalized data provided
  5. When in doubt, be conservative - reject rather than false positive
```

---

### Modification 4: exclusion_scopes.yaml

**Localisation**: `canonical/scopes/exclusion_scopes.yaml`

**Changement - Nouveau scope**:
```yaml
# AJOUTER à la fin du fichier

stock_market_terms:
  description: "Termes boursiers/indices sans contenu LAI - filtrage bruit corporate"
  scope_type: "exclusion"
  keywords:
    # Indices boursiers
    - "MSCI"
    - "MSCI World"
    - "MSCI Small Cap"
    - "stock index"
    - "market index"
    - "benchmark index"
    
    # Rapports financiers génériques
    - "financial calendar"
    - "interim report"
    - "quarterly report"
    - "half-year results"
    - "consolidated results"
    - "earnings report"
    
    # Termes boursiers
    - "market cap"
    - "share price"
    - "stock performance"
    - "trading volume"
    
  notes: |
    Ce scope filtre le bruit boursier des pure players LAI.
    Utilisé dans ingestion_profiles.yaml > corporate_pure_player_broad.
```

---

### Modification 5: source_catalog.yaml

**Localisation**: `canonical/sources/source_catalog.yaml`

**Changement 1 - Max content length**:
```yaml
# AVANT (sources corporate, ligne ~15)
  - source_key: "press_corporate__medincell"
    # ...
    content_enrichment: "summary_enhanced"
    max_content_length: 1000

# APRÈS
  - source_key: "press_corporate__medincell"
    # ...
    content_enrichment: "full_article"
    max_content_length: 2000
```

**Changement 2 - URLs alternatives** (optionnel, Phase 3):
```yaml
# AJOUTER dans press_sector__endpoints_news
  - source_key: "press_sector__endpoints_news"
    homepage_url: "https://endpts.com/"
    rss_url: "https://endpts.com/feed/"
    # ...
    alternative_urls:  # 🆕 AJOUTÉ
      - url: "https://www.fiercebiotech.com/"
        match_strategy: "title_similarity"
        priority: "high"
        reason: "FierceBiotech often has more detailed version"
```

---

### Modification 6: ingestion_profiles.yaml

**Localisation**: `canonical/ingestion/ingestion_profiles.yaml`

**Changement**:
```yaml
# AVANT (ligne ~20)
  corporate_pure_player_broad:
    # ...
    signal_requirements:
      mode: "exclude_only"
      exclusion_scopes:
        - "exclusion_scopes.hr_content"
        - "exclusion_scopes.esg_generic"
        - "exclusion_scopes.financial_generic"
        - "exclusion_scopes.anti_lai_routes"
        - "exclusion_scopes.hr_recruitment_terms"
        - "exclusion_scopes.financial_reporting_terms"

# APRÈS
  corporate_pure_player_broad:
    # ...
    signal_requirements:
      mode: "exclude_only"
      exclusion_scopes:
        - "exclusion_scopes.hr_content"
        - "exclusion_scopes.esg_generic"
        - "exclusion_scopes.financial_generic"
        - "exclusion_scopes.anti_lai_routes"
        - "exclusion_scopes.hr_recruitment_terms"
        - "exclusion_scopes.financial_reporting_terms"
        - "exclusion_scopes.stock_market_terms"  # 🆕 AJOUTÉ
```

---

## 📊 IMPACT ATTENDU DES MODIFICATIONS

### Métriques Avant/Après (Estimation)

| Métrique | Avant | Après | Amélioration |
|----------|-------|-------|--------------|
| **Faux positifs** | 5/14 (36%) | 1/14 (7%) | -80% |
| **Faux négatifs** | 2/15 (13%) | 0/15 (0%) | -100% |
| **Précision** | 64% | 93% | +45% |
| **Bruit newsletter** | Élevé | Faible | -70% |

### Cas Résolus

✅ **Faux négatifs résolus**:
- CagriSema (once-weekly détecté)
- Quince steroid (once-monthly détecté)

✅ **Faux positifs résolus**:
- Eli Lilly manufacturing (exclu)
- MedinCell financial results (score 0)
- Nanexa interim reports (filtré ingestion)

✅ **Qualité améliorée**:
- Hallucinations Bedrock réduites (instructions renforcées)
- Contenu HTML plus complet (max_length augmenté)

---

## ⚠️ RISQUES ET LIMITATIONS

### Risques Identifiés

1. **Sur-filtrage possible**
   - Risque: Exclure manufacturing légitime avec tech LAI
   - Mitigation: Règle contextuelle (manufacturing OK si technology_signals)

2. **Dépendance qualité extraction HTML**
   - Risque: Dosing intervals dans HTML mal parsé
   - Mitigation: Augmenter max_content_length

3. **Bedrock peut ignorer nouvelles instructions**
   - Risque: Hallucinations persistent malgré prompt renforcé
   - Mitigation: Tester avec exemples problématiques

### Limitations Acceptées

- **URLs alternatives**: Implémentation complexe, Phase 3 seulement
- **Hybrid companies**: Réduction poids peut créer faux négatifs, à surveiller
- **Financial results**: Score 0 strict, peut manquer annonces LAI dans earnings

---

## 🚀 PLAN D'IMPLÉMENTATION

### Étape 1: Modifications Fichiers Canonical

```bash
# 1. Créer branche
git checkout -b fix/canonical-improvements-e2e-v13

# 2. Modifier fichiers (ordre recommandé)
# - canonical/prompts/normalization/generic_normalization.yaml
# - canonical/domains/lai_domain_definition.yaml
# - canonical/prompts/domain_scoring/lai_domain_scoring.yaml
# - canonical/scopes/exclusion_scopes.yaml
# - canonical/sources/source_catalog.yaml
# - canonical/ingestion/ingestion_profiles.yaml

# 3. Commit
git add canonical/
git commit -m "fix: amélioration qualité ingestion/normalisation/scoring (E2E v13)"
```

### Étape 2: Déploiement et Test

```bash
# 1. Upload canonical vers S3 dev
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod \
  --region eu-west-3

# 2. Test E2E avec cas problématiques
python tests/local/test_e2e_runner.py --new-context "Canonical-Improvements"

# 3. Vérifier résolution des cas
# - CagriSema: dosing_intervals_detected = ["once-weekly"]
# - Quince: dosing_intervals_detected = ["once-monthly"]
# - Eli Lilly: score = 0 (exclu manufacturing)
# - MedinCell financial: score = 0 (financial_results base = 0)
```

### Étape 3: Validation AWS

```bash
# 1. Promouvoir vers AWS
python tests/aws/test_e2e_runner.py --promote "Canonical-Improvements-Validation"

# 2. Run test AWS
python tests/aws/test_e2e_runner.py --run

# 3. Analyser rapport
# Vérifier métriques: précision, faux positifs, faux négatifs
```

### Étape 4: Merge et Documentation

```bash
# 1. Push et PR
git push origin fix/canonical-improvements-e2e-v13

# 2. Merge après validation

# 3. Documenter changements
# Mettre à jour docs/architecture/blueprint-v2-ACTUAL-2026.yaml
```

---

## 📝 CHECKLIST VALIDATION

**Avant déploiement**:
- [ ] Tous les fichiers canonical modifiés
- [ ] Syntaxe YAML validée
- [ ] Scopes référencés existent
- [ ] Commit avec message descriptif

**Après déploiement dev**:
- [ ] Canonical uploadé sur S3 dev
- [ ] Test local avec cas problématiques
- [ ] CagriSema matché (dosing_intervals détectés)
- [ ] Quince matché (dosing_intervals détectés)
- [ ] Eli Lilly rejeté (manufacturing exclu)
- [ ] MedinCell financial rejeté (score 0)

**Après test AWS**:
- [ ] Rapport E2E généré
- [ ] Métriques améliorées vs baseline
- [ ] Aucune régression sur cas valides
- [ ] Blueprint mis à jour

---

## 🎯 CONCLUSION

### Résumé des Améliorations

**6 fichiers canonical modifiés** pour résoudre **7 problèmes critiques**:

1. ✅ Extraction dosing intervals (normalisation)
2. ✅ Exclusion manufacturing sans tech (scoring)
3. ✅ Financial results score 0 (scoring)
4. ✅ Filtrage bruit boursier (ingestion)
5. ✅ Prévention hallucinations (prompt)
6. ✅ Contenu HTML enrichi (ingestion)

**Impact attendu**: 
- Précision: 64% → 93% (+45%)
- Faux positifs: -80%
- Faux négatifs: -100%

**Effort**: 
- Modifications: 2-3 heures
- Tests: 1-2 heures
- Total: 1 journée

### Prochaines Étapes

1. **Immédiat**: Implémenter Phase 1 (corrections critiques)
2. **Court terme**: Implémenter Phase 2 (améliorations qualité)
3. **Moyen terme**: Implémenter Phase 3 (optimisations avancées)
4. **Long terme**: Monitorer métriques et ajuster si nécessaire

---

**Rapport créé le**: 2026-02-03  
**Auteur**: Amazon Q Developer  
**Statut**: ✅ Prêt pour implémentation  
**Validation**: En attente feedback admin
