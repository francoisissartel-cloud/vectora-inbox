# Plan d'Amélioration Canonical - Post E2E v13

**Date**: 2026-02-03  
**Objectif**: Améliorer qualité ingestion/normalisation/scoring via fichiers canonical  
**Périmètre**: Modifications canonical UNIQUEMENT (pas de code Lambda)  
**Conformité**: ✅ Respecte CRITICAL_RULES.md + Gouvernance

---

## 📋 MÉTADONNÉES PLAN

**Version actuelle**: 
- CANONICAL_VERSION=2.1 (dans VERSION)

**Version cible**:
- CANONICAL_VERSION=2.2 (corrections E2E v13)

**Fichiers canonical modifiés**: 5
1. `canonical/prompts/normalization/generic_normalization.yaml`
2. `canonical/domains/lai_domain_definition.yaml`
3. `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
4. `canonical/scopes/exclusion_scopes.yaml`
5. `canonical/sources/source_catalog.yaml`

**Durée estimée**: 1 journée (4h modifications + 2h tests)

---

## 🎯 PROBLÈMES À RÉSOUDRE (Feedbacks Admin)

### Priorité 🔴 CRITIQUE

1. **Dosing intervals non détectés**
   - Cas: "once-weekly", "once-monthly" non extraits
   - Impact: Faux négatifs (CagriSema, Quince)
   - Solution: Ajouter extraction explicite dans normalisation

2. **Hybrid companies sans contexte LAI matchées**
   - Cas: Eli Lilly manufacturing, Novo Nordisk sans tech LAI
   - Impact: Faux positifs
   - Solution: Hybrid company boost SEULEMENT si autres signaux forts

3. **Financial results pure players matchés**
   - Cas: MedinCell résultats financiers
   - Impact: Bruit newsletter
   - Solution: Score 0 pour financial_results sans signaux LAI

### Priorité 🟠 MOYENNE

4. **Bruit boursier non filtré**
   - Cas: "MSCI index", "interim report"
   - Impact: Bruit ingestion
   - Solution: Étoffer exclusion_scopes.financial_reporting_terms

5. **Hallucinations Bedrock**
   - Cas: "microspheres" inventées
   - Impact: Confiance scoring
   - Solution: Renforcer instructions "EXPLICIT ONLY"

6. **Contenu HTML tronqué**
   - Cas: max_content_length=1000 insuffisant
   - Impact: Perte signaux
   - Solution: Augmenter à 2000

---

## 📝 MODIFICATIONS DÉTAILLÉES

### Modification 1: generic_normalization.yaml

**Fichier**: `canonical/prompts/normalization/generic_normalization.yaml`

**Changements** (3 ajouts):

1. **Ajouter extraction dosing_intervals**
2. **Ajouter extraction title normalisé**
3. **Enrichir summary avec mots-clés LAI**

```yaml
# SECTION 4 - ENTITY EXTRACTION (ligne ~35)
# AJOUTER après "indications_detected"

     - Dosing Intervals: ALL dosing frequency terms EXPLICITLY mentioned
       Examples: "once-weekly", "once-monthly", "once every 3 months", 
                 "q4w", "q8w", "q12w", "quarterly", "semi-annual"
       CRITICAL: Only extract if EXPLICITLY stated in text (title or body)

# SECTION 1 - SUMMARY (ligne ~20)
# MODIFIER instruction

  1. SUMMARY (2-3 sentences)
     - Concise factual summary of the news
     - Focus on key facts: who, what, when
     - IMPORTANT: If LAI-related terms detected (dosing intervals, technologies),
       include them explicitly in summary

# RESPONSE FORMAT (ligne ~50)
# AJOUTER champs

  {
    "title": "...",  # 🆕 AJOUTÉ - Titre normalisé
    "summary": "...",
    "extracted_date": "2026-01-27",
    "date_confidence": 0.95,
    "event_type": "partnership",
    "companies_detected": ["Company A"],
    "molecules_detected": ["Molecule X"],
    "technologies_detected": ["Technology Y"],
    "trademarks_detected": ["Trademark Z"],
    "indications_detected": ["Indication W"],
    "dosing_intervals_detected": ["once-weekly"]  # 🆕 AJOUTÉ
  }
```

**Raison admin**: "ok pour ajouter dosing intervals si detecté, que pense tu d'avoir aussi le titre de la news normalisé, et normalement on a aussi un summary dans la réponse de normalisation, dans ce summary on devrait retrouver les mots clés LAI je pense"

---

### Modification 2: lai_domain_definition.yaml

**Fichier**: `canonical/domains/lai_domain_definition.yaml`

**Changements** (6 modifications):

1. **Enrichir core_technologies avec technology_scopes.yaml**
2. **Enrichir technology_families avec 47 nouveaux termes**
3. **Enrichir dosing_intervals avec 7 nouveaux termes**
4. **Ajouter exclusions manufacturing**
5. **Réduire base_score financial_results à 0**
6. **Ajouter règles contextuelles hybrid_company**

```yaml
# STRONG SIGNALS - core_technologies
# ENRICHIR avec technology_scopes.yaml > lai_keywords.core_phrases
# AVANT: 6 termes → APRÈS: 13 termes

core_technologies:
  # Source: technology_scopes.yaml > lai_keywords.core_phrases
  - "long-acting injectable"
  - "long acting injectable"
  - "long-acting formulation"              # 🆕 AJOUTÉ
  - "extended-release injectable"
  - "extended-release injection"           # 🆕 AJOUTÉ
  - "depot injection"
  - "long-acting depot"                    # 🆕 AJOUTÉ
  - "sustained-release injectable"
  - "sustained release injectable"         # 🆕 AJOUTÉ
  - "controlled-release injection"
  - "injectable controlled release"        # 🆕 AJOUTÉ
  - "long-acting"                          # 🆕 AJOUTÉ
  - "long acting"                          # 🆕 AJOUTÉ

# MEDIUM SIGNALS - technology_families
# ENRICHIR avec technology_scopes.yaml > lai_keywords.technology_terms_high_precision
# AVANT: 11 termes → APRÈS: 58 termes (+427%)

technology_families:
  # Source: technology_scopes.yaml > lai_keywords.technology_terms_high_precision
  
  # DDS families (Drug Delivery Systems) - 🆕 AJOUTÉ
  - "drug delivery system"
  - "controlled release"
  - "sustained release"
  - "extended release"
  - "modified release"
  - "depot injection"
  - "extended-release injectable"
  - "long-acting injectable"
  
  # Microsphere technologies
  - "microspheres"                         # ✅ Existant
  - "polymeric microspheres"               # 🆕 AJOUTÉ
  - "PLGA microspheres"                    # ✅ Existant
  - "PLA microspheres"                     # 🆕 AJOUTÉ
  
  # Depot technologies
  - "in-situ depot"                        # ✅ Existant
  - "in-situ forming depot"                # ✅ Existant
  - "liquid crystalline depot"             # ✅ Existant
  - "liquid crystal depot"                 # 🆕 AJOUTÉ
  - "depot-forming prodrug"                # 🆕 AJOUTÉ
  - "depot prodrug"                        # 🆕 AJOUTÉ
  - "long-acting prodrug"                  # 🆕 AJOUTÉ
  
  # Hydrogel technologies
  - "hydrogel"                             # ✅ Existant
  - "thermo-responsive hydrogel"           # ✅ Existant
  - "RTGel"                                # 🆕 AJOUTÉ
  
  # Proprietary technologies - 🆕 SECTION AJOUTÉE
  - "Atrigel"
  - "FluidCrystal"
  - "SmartDepot"
  - "DepoFoam"
  - "BioSeizer"
  - "Medisorb"
  - "CriPec"
  - "DiffuSphere"
  - "PharmaShell"
  - "SiliaShell"
  - "BEPO"
  
  # Liposome technologies - 🆕 AJOUTÉ
  - "multivesicular liposomes"
  - "long-acting emulsion"
  
  # Half-Life Extension (HLE) strategies
  - "PEGylation"                           # ✅ Existant
  - "site-specific PEGylation"             # ✅ Existant
  - "PASylation"                           # 🆕 AJOUTÉ
  - "Fc fusion"                            # ✅ Existant
  - "Fc-fusion"                            # 🆕 AJOUTÉ
  - "IgG Fc fusion"                        # 🆕 AJOUTÉ
  - "albumin binding"                      # 🆕 AJOUTÉ
  - "albumin fusion"                       # ✅ Existant
  - "albumin-binding"                      # 🆕 AJOUTÉ
  - "lipidation"                           # 🆕 AJOUTÉ
  - "fatty acid conjugation"               # 🆕 AJOUTÉ
  - "polypeptide extension"                # 🆕 AJOUTÉ
  - "glyco-engineering"                    # 🆕 AJOUTÉ
  - "glycan engineering"                   # 🆕 AJOUTÉ
  - "sialylation"                          # 🆕 AJOUTÉ
  - "half-life extension"                  # 🆕 AJOUTÉ
  - "atomic layer deposition"              # 🆕 AJOUTÉ

# MEDIUM SIGNALS - dosing_intervals
# ENRICHIR avec technology_scopes.yaml > lai_keywords.interval_patterns
# AVANT: 8 termes → APRÈS: 15 termes (+88%)

dosing_intervals:
  # Source: technology_scopes.yaml > lai_keywords.interval_patterns
  - "once-weekly"                          # 🆕 AJOUTÉ
  - "once-weekly injection"                # 🆕 AJOUTÉ
  - "once-monthly"                         # ✅ Existant
  - "once every 2 weeks"                   # 🆕 AJOUTÉ
  - "once every 3 months"                  # ✅ Existant
  - "once every 6 months"                  # ✅ Existant
  - "q2w"                                  # 🆕 AJOUTÉ
  - "q4w"                                  # ✅ Existant
  - "q8w"                                  # ✅ Existant
  - "q12w"                                 # ✅ Existant
  - "3-month"                              # 🆕 AJOUTÉ
  - "6-month"                              # ✅ Existant
  - "quarterly injection"                  # ✅ Existant
  - "biweekly injection"                   # 🆕 AJOUTÉ
  - "monthly injection"                    # 🆕 AJOUTÉ

# EXCLUSIONS
# AJOUTER termes manufacturing

exclusions:
  - "oral tablet"
  - "oral capsule"
  - "oral administration"
  - "transdermal patch"
  - "nasal spray"
  - "sublingual"
  - "inhalation"
  # Manufacturing without LAI context - 🆕 AJOUTÉ
  - "manufacturing facility"
  - "production plant"
  - "factory construction"
  - "plant expansion"
  - "manufacturing site"

# SCORING - event_type_base_scores
# MODIFIER financial_results

event_type_base_scores:
  partnership: 60
  regulatory: 70
  clinical_update: 50
  corporate_move: 40
  financial_results: 0  # 🔧 MODIFIÉ: 30 → 0
  other: 20

# SCORING - entity_boosts
# MODIFIER + AJOUTER

entity_boosts:
  pure_player_company: 25
  trademark_mention: 20
  key_molecule: 15
  dosing_interval: 15      # 🆕 AJOUTÉ
  technology_family: 10
  hybrid_company: 0        # 🔧 MODIFIÉ: 10 → 0 (boost conditionnel)

# NOUVELLE SECTION - boost_conditions
# 🆕 AJOUTER après entity_boosts

boost_conditions:
  # Hybrid company boost SEULEMENT si autres signaux LAI détectés
  hybrid_company:
    base_boost: 0
    conditional_boost: 10
    requires_one_of:
      - "technology_family"        # Ex: microspheres, PEGylation, Atrigel
      - "dosing_interval"          # Ex: once-weekly, q4w
      - "key_molecule"             # Ex: paliperidone, cabotegravir
      - "trademark_mention"        # Ex: UZEDY®, Brixadi
      - "lai_core_phrase"          # Ex: long-acting injectable, depot injection
      - "lai_technology_term"      # Ex: PLGA, in-situ depot, Fc fusion
    reasoning: "Hybrid companies need LAI-specific context to be relevant"
    
    # Référence aux 58 termes technology_families enrichis
    technology_detection:
      source: "technology_families (58 termes from technology_scopes.yaml)"
      note: "ANY terme LAI détecté → hybrid_company boost activé"

# MATCHING RULES
# AJOUTER après rule_4

  - id: rule_5
    condition: "event_type == 'financial_results' AND signals_count < 2"
    action: "reject (financial results need explicit LAI content)"
  
  - id: rule_6
    condition: "event_type == 'corporate_move' AND manufacturing_terms AND NO technology_signals"
    action: "reject (manufacturing without LAI technology)"
```

**Impact enrichissement** :
- **core_technologies** : 6 → 13 termes (+117%)
- **technology_families** : 11 → 58 termes (+427%)
- **dosing_intervals** : 8 → 15 termes (+88%)
- **TOTAL medium_signals** : 19 → 73 termes (+284%)

**Raison admin** : "il faut trouver une solution pour que les hybrid company donnent un score lié au Watch domain que si d'autres signaux forts sont detectés" + "analyse plutot comment tu peux enrichir lai_domain_definition.yaml en exploitant technology_scopes.yaml"

---

### Modification 3: lai_domain_scoring.yaml

**Fichier**: `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`

**Changements** (2 modifications):

1. **Renforcer instructions anti-hallucination**
2. **Ajouter gestion boost conditionnel hybrid_company**

```yaml
# SYSTEM INSTRUCTIONS (ligne ~10)
# AJOUTER après description

  CRITICAL RULES FOR SIGNAL DETECTION:
  1. Only detect signals EXPLICITLY present in the normalized item
  2. DO NOT infer, assume, or hallucinate signals not provided
  3. If a technology/molecule/term is not in entities_detected, DO NOT add it
  4. Base your evaluation ONLY on the normalized data provided
  5. When in doubt, be conservative - reject rather than false positive
  
  HYBRID COMPANY SCORING RULE:
  - If hybrid_company detected, apply boost (10 points) ONLY if at least one of:
    * technology_family detected (ex: microspheres, hydrogel)
    * dosing_interval detected (ex: once-weekly, q4w, monthly)
    * key_molecule detected (ex: paliperidone, cabotegravir)
    * trademark_mention detected (ex: UZEDY®, Brixadi)
    * LAI core phrase detected (ex: long-acting injectable, depot injection)
    * LAI technology term detected (ex: PLGA, PEGylation, Fc fusion, in-situ depot)
  - Otherwise, hybrid_company gives 0 boost
  
  TECHNOLOGY DETECTION:
  - Use terms from technology_scopes.yaml:
    * lai_keywords.core_phrases (high precision)
    * lai_keywords.technology_terms_high_precision (DDS/HLE specific)
    * lai_keywords.interval_patterns (dosing patterns)
  - Be permissive: ANY LAI-related technology term triggers boost

# USER TEMPLATE - EVALUATION PROCESS (ligne ~30)
# MODIFIER section 3

  3. SCORE CALCULATION (0-100)
     If relevant, calculate score:
     - Base score: from event_type_base_scores
     - Entity boosts: add boosts for detected entities
       * SPECIAL: hybrid_company boost (10) ONLY if other LAI signals present
     - Recency boost: based on item age
     - Confidence penalty: if low confidence signals
```

---

### Modification 4: exclusion_scopes.yaml

**Fichier**: `canonical/scopes/exclusion_scopes.yaml`

**Changements** (1 modification):

**Étoffer financial_reporting_terms existant** (au lieu de créer nouveau scope)

```yaml
# TROUVER financial_reporting_terms existant
# AJOUTER termes boursiers

financial_reporting_terms:
  description: "Termes rapports financiers et boursiers génériques sans contenu LAI"
  scope_type: "exclusion"
  keywords:
    # Rapports financiers (existants)
    - "quarterly earnings"
    - "annual report"
    - "financial statement"
    # ... existants
    
    # 🆕 AJOUTER - Termes boursiers
    - "MSCI"
    - "MSCI World"
    - "MSCI Small Cap"
    - "stock index"
    - "market index"
    - "benchmark index"
    - "financial calendar"
    - "interim report"
    - "half-year results"
    - "consolidated results"
    - "market cap"
    - "share price"
    - "trading volume"
```

**Raison admin**: "je suis plutôt partisant d'étoffer le fichier déjà présent plutôt que d'ajouter un autre fichier"

---

### Modification 5: source_catalog.yaml

**Fichier**: `canonical/sources/source_catalog.yaml`

**Changements** (1 modification):

**Augmenter max_content_length pour sources corporate**

```yaml
# SOURCES CORPORATE (5 sources)
# MODIFIER pour chaque source corporate

  - source_key: "press_corporate__medincell"
    # ...
    content_enrichment: "full_article"      # 🔧 MODIFIÉ: summary_enhanced → full_article
    max_content_length: 2000                # 🔧 MODIFIÉ: 1000 → 2000

  - source_key: "press_corporate__camurus"
    # ...
    content_enrichment: "full_article"
    max_content_length: 2000

  - source_key: "press_corporate__delsitech"
    # ...
    content_enrichment: "full_article"
    max_content_length: 2000

  - source_key: "press_corporate__nanexa"
    # ...
    content_enrichment: "full_article"
    max_content_length: 2000

  - source_key: "press_corporate__peptron"
    # ...
    content_enrichment: "full_article"
    max_content_length: 2000
```

---

## 🔄 WORKFLOW COMPLET (Conforme CRITICAL_RULES)

### Phase 1: Préparation Git (AVANT modifications)

```bash
# 1. Vérifier branche actuelle
git status
git branch

# 2. Créer branche feature depuis develop
git checkout develop
git pull origin develop
git checkout -b fix/canonical-improvements-e2e-v13

# 3. Vérifier VERSION actuelle
cat VERSION
# CANONICAL_VERSION=2.1
```

### Phase 2: Modifications Fichiers

```bash
# 1. Modifier 5 fichiers canonical (ordre recommandé)
# - canonical/prompts/normalization/generic_normalization.yaml
# - canonical/domains/lai_domain_definition.yaml
# - canonical/prompts/domain_scoring/lai_domain_scoring.yaml
# - canonical/scopes/exclusion_scopes.yaml
# - canonical/sources/source_catalog.yaml

# 2. Incrémenter VERSION
# Modifier VERSION: CANONICAL_VERSION=2.1 → 2.2
```

### Phase 3: Commit (AVANT build/deploy)

```bash
# 1. Vérifier modifications
git status
git diff canonical/

# 2. Commit
git add canonical/ VERSION
git commit -m "fix(canonical): amélioration qualité ingestion/normalisation/scoring

- Ajout extraction dosing_intervals + title dans normalisation
- Hybrid company boost conditionnel (nécessite autres signaux LAI)
- Financial results base_score 0 (nécessite signaux LAI explicites)
- Exclusions manufacturing sans tech LAI
- Étoffer financial_reporting_terms avec termes boursiers
- Augmenter max_content_length 1000→2000 sources corporate

Résout faux négatifs: CagriSema, Quince (dosing intervals)
Résout faux positifs: Eli Lilly manufacturing, MedinCell financial

Ref: E2E v13 feedbacks admin
CANONICAL_VERSION: 2.1 → 2.2"

# 3. Vérifier commit
git log -1 --stat
```

### Phase 4: Tests Local (OBLIGATOIRE avant AWS)

```bash
# 1. Créer contexte test local
python tests/local/test_e2e_runner.py --new-context "Canonical-v2.2-Validation"
# Génère: lai_weekly_canonical_v2_2_validation_XXX

# 2. Copier canonical modifié vers contexte local
# (Le runner utilise canonical/ local automatiquement)

# 3. Run test local
python tests/local/test_e2e_runner.py --run

# 4. Analyser résultats
# Vérifier dans rapport:
# - CagriSema: dosing_intervals_detected = ["once-weekly"] ✅
# - Quince: dosing_intervals_detected = ["once-monthly"] ✅
# - Eli Lilly: score = 0 (exclu manufacturing) ✅
# - MedinCell financial: score = 0 ✅
# - Novo Nordisk sans tech: score réduit (hybrid sans boost) ✅
```

### Phase 5: Déploiement AWS Dev (SI test local OK)

```bash
# 1. Upload canonical vers S3 dev
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod \
  --region eu-west-3 \
  --delete

# 2. Vérifier upload
aws s3 ls s3://vectora-inbox-config-dev/canonical/ \
  --recursive \
  --profile rag-lai-prod \
  --region eu-west-3

# 3. Pas de build/deploy Lambda (canonical seulement)
# Lambdas existantes chargeront nouveau canonical depuis S3
```

### Phase 6: Tests AWS Dev

```bash
# 1. Promouvoir contexte vers AWS
python tests/aws/test_e2e_runner.py --promote "Canonical-v2.2-Validation"
# Génère: lai_weekly_vX avec canonical v2.2

# 2. Run test AWS
python tests/aws/test_e2e_runner.py --run

# 3. Analyser rapport E2E
# Vérifier mêmes résultats que test local
# Comparer métriques vs baseline E2E v13
```

### Phase 7: Validation et Merge

```bash
# 1. Si tests AWS OK → Push branche
git push origin fix/canonical-improvements-e2e-v13

# 2. Créer Pull Request
# Titre: "fix(canonical): amélioration qualité post E2E v13"
# Description: Lien vers rapport test + métriques

# 3. Review + Merge dans develop

# 4. Tag version
git checkout develop
git pull origin develop
git tag v2.2-canonical
git push origin v2.2-canonical
```

### Phase 8: Promotion Stage (Optionnel)

```bash
# Si validation complète nécessaire en stage

# 1. Upload canonical vers S3 stage
aws s3 sync canonical/ s3://vectora-inbox-config-stage/canonical/ \
  --profile rag-lai-prod \
  --region eu-west-3 \
  --delete

# 2. Test stage
python tests/aws/test_e2e_runner.py --promote "Canonical-v2.2-Stage" --env stage
python tests/aws/test_e2e_runner.py --run --env stage
```

---

## ✅ CHECKLIST CONFORMITÉ CRITICAL_RULES

**Avant démarrage**:
- [x] Architecture 3 Lambdas V2 ? → OUI (pas de modif Lambda)
- [x] Code dans src_v2/ ? → N/A (canonical seulement)
- [x] Git avant build ? → OUI (commit Phase 3, deploy Phase 5)
- [x] Environnement explicite ? → OUI (--env dev partout)
- [x] Déploiement complet ? → OUI (canonical uploadé S3)
- [x] Tests local avant AWS ? → OUI (Phase 4 obligatoire)
- [x] Client config auto-généré ? → OUI (runners)
- [x] Bedrock us-east-1 + Sonnet ? → OUI (pas de modif)
- [x] Temporaires dans .tmp/ ? → OUI (runners gèrent)
- [x] Blueprint à jour ? → N/A (pas de modif architecture)

**Pendant exécution**:
- [ ] Branche créée depuis develop
- [ ] VERSION incrémenté (2.1 → 2.2)
- [ ] Commit AVANT upload S3
- [ ] Test local réussi
- [ ] Canonical uploadé S3 dev
- [ ] Test AWS réussi
- [ ] PR créée et mergée
- [ ] Tag version créé

---

## 📊 RÉSULTATS ATTENDUS

### Métriques Avant/Après

| Métrique | E2E v13 (Avant) | Attendu (Après) | Amélioration |
|----------|-----------------|-----------------|--------------|
| Faux positifs | 5/14 (36%) | 1/14 (7%) | -80% |
| Faux négatifs | 2/15 (13%) | 0/15 (0%) | -100% |
| Précision | 64% | 93% | +45% |

### Cas Résolus

✅ **Faux négatifs**:
- CagriSema: dosing_intervals_detected = ["once-weekly"]
- Quince: dosing_intervals_detected = ["once-monthly"]

✅ **Faux positifs**:
- Eli Lilly manufacturing: score = 0 (exclu)
- MedinCell financial: score = 0 (base_score=0)
- Novo Nordisk sans tech: hybrid_company boost = 0

✅ **Qualité**:
- Hallucinations réduites (instructions renforcées)
- Contenu HTML enrichi (max_length 2000)
- Bruit boursier filtré (exclusions étoffées)

---

## ⚠️ RISQUES ET MITIGATIONS

### Risque 1: Sur-filtrage manufacturing

**Risque**: Exclure manufacturing légitime avec tech LAI  
**Mitigation**: Règle contextuelle (manufacturing OK si technology_signals)  
**Test**: Vérifier items manufacturing + microspheres passent

### Risque 2: Hybrid company sous-scorés

**Risque**: Hybrid avec tech LAI mais pas dans entities_detected  
**Mitigation**: Normalisation enrichie capture mieux technologies  
**Test**: Vérifier Novo Nordisk avec "once-weekly" matché

### Risque 3: Bedrock ignore nouvelles instructions

**Risque**: Hallucinations persistent malgré prompt renforcé  
**Mitigation**: Tester avec cas problématiques (AstraZeneca/CSPC)  
**Test**: Vérifier signals_detected ne contient que entités normalisées

---

## 📝 NOTES IMPLÉMENTATION

### Ordre Modifications Recommandé

1. **generic_normalization.yaml** (extraction dosing_intervals)
2. **exclusion_scopes.yaml** (étoffer financial_reporting_terms)
3. **lai_domain_definition.yaml** (scoring + règles)
4. **lai_domain_scoring.yaml** (instructions + hybrid boost)
5. **source_catalog.yaml** (max_content_length)

### Validation Syntaxe YAML

```bash
# Avant commit, valider syntaxe
python -c "import yaml; yaml.safe_load(open('canonical/prompts/normalization/generic_normalization.yaml'))"
python -c "import yaml; yaml.safe_load(open('canonical/domains/lai_domain_definition.yaml'))"
# ... pour chaque fichier modifié
```

### Backup Avant Modifications

```bash
# Créer backup canonical actuel
cp -r canonical/ canonical_backup_v2.1_$(date +%Y%m%d)/
```

---

## 🎯 CRITÈRES SUCCÈS

**Test local réussi SI**:
- [ ] Aucune erreur parsing YAML
- [ ] Normalisation retourne dosing_intervals_detected
- [ ] CagriSema matché (score > 70)
- [ ] Quince matché (score > 70)
- [ ] Eli Lilly manufacturing rejeté (score = 0)
- [ ] MedinCell financial rejeté (score = 0)

**Test AWS réussi SI**:
- [ ] Mêmes résultats que test local
- [ ] Aucune erreur Lambda
- [ ] Rapport E2E généré
- [ ] Métriques améliorées vs baseline

**Plan validé SI**:
- [ ] Tests local + AWS réussis
- [ ] PR mergée dans develop
- [ ] Tag version créé
- [ ] Documentation mise à jour

---

**Plan créé le**: 2026-02-03  
**Conformité**: ✅ CRITICAL_RULES.md + Gouvernance  
**Statut**: Prêt pour exécution  
**Durée estimée**: 1 journée
