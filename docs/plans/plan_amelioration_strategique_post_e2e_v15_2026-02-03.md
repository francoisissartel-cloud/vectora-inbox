# Plan d'Amélioration Stratégique Post E2E V15 - Analyse Approfondie

**Date**: 2026-02-03  
**Base**: Retours admin sur test_e2e_v15_rapport_ingestion_normalisation_scoring.md  
**Objectif**: Corrections ciblées et efficaces respectant l'architecture Vectora-Inbox  
**Durée estimée**: 4-6h

---

## 🎯 ANALYSE STRATÉGIQUE DES RETOURS ADMIN

### Synthèse des Problèmes Identifiés

| # | Problème | Sévérité | Cause Racine | Phase Impactée |
|---|----------|----------|--------------|----------------|
| 1 | Perte détection companies | 🔴 CRITIQUE | Prompt normalization | Normalisation |
| 2 | Faux négatif Quince (once-monthly) | 🔴 CRITIQUE | Extraction dosing_intervals | Normalisation |
| 3 | Faux positif Eli Lilly manufacturing | 🟡 IMPORTANT | Règle hybrid_company mal appliquée | Scoring |
| 4 | Faux négatif MedinCell malaria grant | 🟡 IMPORTANT | Règle pure_player manquante | Scoring |
| 5 | Bruit ingéré (RH, financial) | 🟡 IMPORTANT | Profils ingestion non appliqués | Ingestion |

---

## 🔍 ANALYSE DÉTAILLÉE PAR PROBLÈME

### Problème 1: Perte Détection Companies (CRITIQUE)

**Retour admin**: "il faut comprendre ce qui s'est passé entre les deux run et corriger ce probleme"

**Analyse du système**:

1. **Prompt generic_normalization.yaml** (ligne 54-55):
   ```yaml
   4. ENTITY EXTRACTION (ALL explicitly mentioned)
      - Companies: ALL pharmaceutical/biotech company names
   ```
   - Le prompt DEMANDE l'extraction des companies
   - Format de sortie attendu: `"companies_detected": ["Company A", "Company B"]`

2. **Résultat V15**: `"companies_detected": []` pour TOUS les items

3. **Hypothèses**:
   - ❌ Bedrock ne détecte plus les companies (peu probable - changement de modèle?)
   - ✅ **PLUS PROBABLE**: Prompt trop générique "ALL pharmaceutical/biotech company names"
   - ✅ **PLUS PROBABLE**: Pas de liste de référence fournie à Bedrock

4. **Comparaison avec V13** (qui fonctionnait):
   - V13 utilisait probablement un prompt avec liste explicite de companies
   - OU un scope de référence fourni à Bedrock

**Cause racine**: Le prompt generic_normalization.yaml ne fournit PAS la liste des companies LAI à Bedrock. Il demande "ALL pharmaceutical/biotech company names" sans contexte, donc Bedrock est trop conservateur.

**Solution**:
- Ajouter référence au scope `lai_companies_global` dans le prompt
- Fournir la liste explicite à Bedrock via `{{ref:company_scopes.lai_companies_global}}`

---

### Problème 2: Faux Négatif Quince (CRITIQUE)

**Retour admin**: "ok avec action requise"

**Analyse du système**:

1. **Item Quince**:
   - Titre: "Quince's steroid therapy for rare disease fails, shares tank"
   - Titre complet (probable): "...once-monthly treatment..."
   - Score V15: 0 (rejeté)

2. **Prompt generic_normalization.yaml** (ligne 62-65):
   ```yaml
   - Dosing Intervals: ALL dosing frequency terms EXPLICITLY mentioned
     Examples: "once-weekly", "once-monthly", "once every 3 months", 
               "q4w", "q8w", "q12w", "quarterly", "semi-annual"
     CRITICAL: Only extract if EXPLICITLY stated in text (title or body)
   ```

3. **Problème identifié**:
   - Le prompt dit "title or body" MAIS Bedrock ne reçoit que `{{item_text}}`
   - Si `item_text` ne contient pas le titre complet, "once-monthly" est perdu

4. **Vérification nécessaire**:
   - Comment est construit `{{item_text}}` dans le runtime?
   - Est-ce que le titre est inclus dans item_text?

**Cause racine**: Le titre n'est probablement pas inclus dans `{{item_text}}` OU "once-monthly" est dans une partie tronquée.

**Solution**:
- Modifier le prompt pour extraire dosing_intervals depuis le titre SÉPARÉMENT
- Ajouter variable `{{item_title}}` dans le prompt
- Instruction explicite: "Extract dosing intervals from BOTH title AND body"

---

### Problème 3: Faux Positif Eli Lilly Manufacturing (IMPORTANT)

**Retour admin**: "je ne comprends pas, il me semble qu'on avait validé que un hybrid player doit avoir des strong signals pour etre matché, ou sont les strong signals?"

**Analyse du système**:

1. **Item Eli Lilly**:
   - Titre: "Lilly rounds out quartet of new US plants..."
   - Score V15: 65 (matché)
   - Signals détectés:
     - Medium: "hybrid_company: Eli Lilly"
     - Medium: "technology: injectables and devices"

2. **Règle hybrid_company dans lai_domain_definition.yaml** (ligne 217-224):
   ```yaml
   boost_conditions:
     hybrid_company:
       base_boost: 0
       conditional_boost: 10
       requires_one_of:
         - "technology_family"
         - "dosing_interval"
         - "key_molecule"
         - "trademark_mention"
       reasoning: "Hybrid companies need LAI-specific context"
   ```

3. **Problème identifié**:
   - La règle dit: hybrid_company boost SEULEMENT si technology_family OU dosing_interval OU molecule OU trademark
   - "injectables and devices" a été détecté comme "technology_family"
   - MAIS "injectables and devices" n'est PAS dans la liste des 73 technology_families LAI!

4. **Vérification lai_domain_definition.yaml** (ligne 66-139):
   - Liste des 73 technology_families
   - ❌ "injectables and devices" N'EST PAS dans la liste
   - ❌ "injectables" N'EST PAS dans la liste (trop générique)

**Cause racine**: Bedrock a halluciné "injectables and devices" comme technology_family LAI alors que ce terme n'est pas dans la liste de référence.

**Solution**:
Renforcer CRITICAL RULES dans lai_domain_scoring.yaml:
   - "Only detect technology_family from the 73 terms provided in domain definition"
   - "DO NOT infer generic terms like 'injectables' as LAI technology"

---

### Problème 4: Faux Négatif MedinCell Malaria Grant (IMPORTANT)

**Retour admin**: "cest un evenement important qui devrait matcher: medincell est un pure player lai, et un grant est un event de type funding, donc doit etre traité comme partnership. je veux capter tous les events partnerhsips des pure players meme sans signal LAI"

**Analyse du système**:

1. **Item MedinCell Malaria**:
   - Titre: "Medincell Awarded New Grant to Fight Malaria"
   - Score V15: 0 (rejeté)
   - Reasoning: "Financial results need at least 2 LAI signals (rule_5)"

2. **Problème identifié**:
   - Event classé comme "financial_results" (probablement)
   - Rule_5 appliquée: "financial_results AND signals_count < 2 → reject"
   - MAIS l'admin dit: "grant = funding = partnership"

3. **Classification event_type**:
   - Grant/funding devrait être classé comme "partnership" (collaboration financière)
   - PAS comme "financial_results" (rapports trimestriels)

4. **Règle manquante pour pure_players**:
   - L'admin veut: "tous les events partnerships des pure players même sans signal LAI"
   - Actuellement: pure_player donne +25 points MAIS ne garantit pas le match

**Cause racine**: 
- Event_type mal classé (grant → financial_results au lieu de partnership)
- Règle manquante: pure_player + partnership → auto-match

**Découverte importante**: Le fichier `canonical/events/event_type_patterns.yaml` existe et définit les patterns d'événements, MAIS:
- "grant" et "funding" ne sont PAS dans les keywords partnership
- Ce fichier est probablement NON utilisé dans le workflow actuel (pas de référence dans les prompts)

**Solution double**:
1. **Priorité 1**: Améliorer classification event_type dans generic_normalization.yaml:
   - "partnership (collaborations, licensing, M&A, **grants, funding, research agreements**)"
   - Ajouter section CRITICAL DISTINCTIONS avec exemples
2. **Priorité 2**: Mettre à jour event_type_patterns.yaml (pour cohérence documentaire):
   - Ajouter "grant", "awarded grant", "funding" aux title_keywords
3. Ajouter rule_7 dans lai_domain_definition.yaml:
   - "pure_player_company + partnership → match (score ≥60)"

---

### Problème 5: Bruit Ingéré (RH, Financial) (IMPORTANT)

**Retour admin**: "pourquoi continue t on a ingerer ces items? je pensais avec plan_amelioration_canonical_e2e_v13_FINAL_2026-02-03.md que on allait améliorer la pahse ingestion en evitant d'ingerer du bruit évident, comme des sujets RH ou financials pures."

**Analyse du système**:

1. **Items rejetés en V15**:
   - "Medincell Appoints Dr Grace Kim..." (RH)
   - "Publication of the 2026 financial calendar" (Financial)
   - "Medincell Publishes its Consolidated Half-Year Financial Results" (Financial)

2. **Profil ingestion actuel** (ingestion_profiles.yaml ligne 18-35):
   ```yaml
   corporate_pure_player_broad:
     strategy: "broad_ingestion"
     signal_requirements:
       mode: "exclude_only"
       exclusion_scopes:
         - "exclusion_scopes.hr_content"
         - "exclusion_scopes.esg_generic"
         - "exclusion_scopes.financial_generic"
         - "exclusion_scopes.anti_lai_routes"
         - "exclusion_scopes.hr_recruitment_terms"
         - "exclusion_scopes.financial_reporting_terms"
   ```

3. **Problème identifié**:
   - Le profil DÉFINIT les exclusions
   - MAIS ces exclusions ne sont probablement PAS appliquées dans le runtime
   - Les items RH/financial sont ingérés puis rejetés en scoring (gaspillage Bedrock)

4. **Vérification nécessaire**:
   - Est-ce que le runtime applique les ingestion_profiles?
   - Où sont définis les exclusion_scopes référencés?

**Cause racine**: Les profils d'ingestion sont définis mais probablement pas appliqués dans le code Lambda ingest-v2.

**Solution**:
1. Vérifier si exclusion_scopes.yaml existe et contient les termes RH/financial
2. Implémenter l'application des profils d'ingestion dans Lambda ingest-v2
3. OU ajouter filtrage simple dans ingest-v2 basé sur keywords:
   - Rejeter si titre contient: "appoint", "hire", "financial results", "earnings", "quarterly report"

---

## 🎯 PLAN D'ACTION PRIORISÉ

### Phase 1: Corrections Critiques (2-3h)

#### Action 1.1: Restaurer Détection Companies (1h)

**Fichier**: `canonical/prompts/normalization/generic_normalization.yaml`

**Modifications**:

```yaml
# AVANT (ligne 54-55)
  4. ENTITY EXTRACTION (ALL explicitly mentioned)
     - Companies: ALL pharmaceutical/biotech company names

# APRÈS
  4. ENTITY EXTRACTION (ALL explicitly mentioned)
     - Companies: ALL pharmaceutical/biotech company names mentioned
       Reference list (for context): {{ref:company_scopes.lai_companies_global}}
       CRITICAL: Extract company names EXACTLY as they appear in text
       Examples: "MedinCell", "Teva", "Novo Nordisk", "Eli Lilly"
```

**Test**:
- Relancer normalisation sur item MedinCell
- Vérifier: `companies_detected: ["MedinCell"]`

---

#### Action 1.2: Corriger Extraction Dosing Intervals depuis Titre (1h)

**Fichier**: `canonical/prompts/normalization/generic_normalization.yaml`

**Modifications**:

```yaml
# AVANT (ligne 17-18)
  TEXT TO ANALYZE:
  {{item_text}}

# APRÈS
  TEXT TO ANALYZE:
  Title: {{item_title}}
  Content: {{item_text}}

# AVANT (ligne 62-65)
     - Dosing Intervals: ALL dosing frequency terms EXPLICITLY mentioned
       Examples: "once-weekly", "once-monthly", "once every 3 months", 
                 "q4w", "q8w", "q12w", "quarterly", "semi-annual"
       CRITICAL: Only extract if EXPLICITLY stated in text (title or body)

# APRÈS
     - Dosing Intervals: ALL dosing frequency terms EXPLICITLY mentioned
       Examples: "once-weekly", "once-monthly", "once every 3 months", 
                 "q4w", "q8w", "q12w", "quarterly", "semi-annual"
       CRITICAL: Extract from BOTH title AND content
       Priority: Check title FIRST, then content
       Common patterns in titles: "once-weekly", "once-monthly", "monthly", "quarterly"
```

**Test**:
- Relancer normalisation sur item Quince
- Vérifier: `dosing_intervals_detected: ["once-monthly"]`

---

#### Action 1.3: Bloquer Hallucination "injectables and devices" (30min)

**Fichier**: `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`

**Modifications**:

```yaml
# AVANT (ligne 11-15)
  CRITICAL RULES FOR SIGNAL DETECTION:
  1. Only detect signals EXPLICITLY present in the normalized item
  2. DO NOT infer, assume, or hallucinate signals not provided
  3. If a technology/molecule/term is not in entities_detected, DO NOT add it
  4. Base your evaluation ONLY on the normalized data provided
  5. When in doubt, be conservative - reject rather than false positive

# APRÈS
  CRITICAL RULES FOR SIGNAL DETECTION:
  1. Only detect signals EXPLICITLY present in the normalized item
  2. DO NOT infer, assume, or hallucinate signals not provided
  3. If a technology/molecule/term is not in entities_detected, DO NOT add it
  4. Base your evaluation ONLY on the normalized data provided
  5. When in doubt, be conservative - reject rather than false positive
  6. CRITICAL: technology_family MUST be from the 73 terms in domain definition
     - DO NOT detect generic terms like "injectables", "devices", "manufacturing"
     - DO NOT infer LAI technology from manufacturing context
  7. Manufacturing facilities WITHOUT specific LAI technology → REJECT
```

**Fichier**: `canonical/domains/lai_domain_definition.yaml`

**Modifications**:

```yaml
# AVANT (ligne 160-167)
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
  - "manufacturing site"

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
  - "manufacturing site"
  # Generic injectable terms (not LAI-specific)
  - "injectables and devices"
  - "injectable manufacturing"
  - "injectable production"
```

**Test**:
- Relancer scoring sur item Eli Lilly
- Vérifier: Score 0 (rejeté) OU technology_family non détecté

---

### Phase 2: Corrections Importantes (1-2h)

#### Action 2.1: Ajouter Règle Pure Player + Partnership (30min)

**Fichier**: `canonical/domains/lai_domain_definition.yaml`

**Modifications**:

```yaml
# AVANT (ligne 169-189)
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
  
  - id: rule_5
    condition: "event_type == 'financial_results' AND signals_count < 2"
    action: "reject (financial results need explicit LAI content)"
  
  - id: rule_6
    condition: "event_type == 'corporate_move' AND manufacturing_terms AND NO technology_signals"
    action: "reject (manufacturing without LAI technology)"

# APRÈS
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
  
  - id: rule_5
    condition: "event_type == 'financial_results' AND signals_count < 2"
    action: "reject (financial results need explicit LAI content)"
  
  - id: rule_6
    condition: "event_type == 'corporate_move' AND manufacturing_terms AND NO technology_signals"
    action: "reject (manufacturing without LAI technology)"
  
  - id: rule_7
    condition: "pure_player_company + event_type == 'partnership'"
    action: "match with medium confidence (score ≥60)"
    reasoning: "Pure players LAI: all partnerships relevant even without explicit LAI signals"
```

**Test**:
- Relancer scoring sur item MedinCell malaria grant
- Vérifier: Score ≥60 (matché)

---

#### Action 2.2: Améliorer Classification Event Type (30min)

**Fichier 1**: `canonical/prompts/normalization/generic_normalization.yaml` (PRIORITÉ 1)

**Modifications**:

```yaml
# AVANT (ligne 38-44)
  3. EVENT CLASSIFICATION
     - Classify into ONE primary type:
       * partnership (collaborations, licensing, M&A)
       * regulatory (approvals, submissions, designations)
       * clinical_update (trial results, enrollments, milestones)
       * corporate_move (leadership, strategy, restructuring)
       * financial_results (earnings, funding, investments)
       * other (if none of above fit)

# APRÈS
  3. EVENT CLASSIFICATION
     - Classify into ONE primary type:
       * partnership (collaborations, licensing, M&A, grants, funding, research agreements)
       * regulatory (approvals, submissions, designations)
       * clinical_update (trial results, enrollments, milestones)
       * corporate_move (leadership appointments, strategy, restructuring)
       * financial_results (quarterly earnings, annual reports, financial calendars)
       * other (if none of above fit)
     
     CRITICAL DISTINCTIONS:
     - Grant/funding for R&D or projects → partnership (NOT financial_results)
     - Quarterly earnings report → financial_results
     - Leadership appointment → corporate_move
     - Manufacturing facility announcement → corporate_move
     
     EXAMPLES:
     - "Company awarded $5M grant for malaria research" → partnership
     - "Company receives funding from foundation" → partnership
     - "Company reports Q3 earnings" → financial_results
     - "Company raises $50M in Series B" → financial_results
```

**Fichier 2**: `canonical/events/event_type_patterns.yaml` (PRIORITÉ 2 - cohérence)

**Modifications**:

```yaml
# AVANT (ligne 50-52)
  description: >
    Collaborations, licensing agreements, co-development deals, strategic alliances,
    option agreements, research partnerships.

# APRÈS
  description: >
    Collaborations, licensing agreements, co-development deals, strategic alliances,
    option agreements, research partnerships, grants, and funding agreements.

# AVANT (ligne 58-75)
  title_keywords:
    - "partnership"
    - "collaboration"
    - "licensing agreement"
    [...]
    - "enters into agreement"

# APRÈS
  title_keywords:
    - "partnership"
    - "collaboration"
    - "licensing agreement"
    [...]
    - "enters into agreement"
    # Funding & Grants (ajout 2026-02-03)
    - "grant"
    - "awarded grant"
    - "receives grant"
    - "funding"
    - "awarded funding"
    - "receives funding"
    - "research grant"
    - "development grant"
```

**Note**: Le fichier event_type_patterns.yaml est probablement non utilisé dans le workflow actuel (pas de référence dans les prompts), mais on le met à jour pour cohérence documentaire et usage futur potentiel.

**Test**:
- Relancer normalisation sur item MedinCell malaria grant
- Vérifier: `event_type: "partnership"`

---

#### Action 2.3: Implémenter Filtrage Ingestion Basique (1h)

**Option A: Filtrage simple dans Lambda ingest-v2** (recommandé pour MVP)

**Fichier**: `src/lambdas/ingest_v2/handler.py` (à localiser)

**Logique à ajouter**:

```python
# Filtrage basique pour pure players
def should_filter_out_pure_player(title, content):
    """Filtre le bruit évident pour pure players LAI"""
    
    # Patterns RH à rejeter
    hr_patterns = [
        "appoint", "hire", "join", "promote", "chief", "officer",
        "board of directors", "management team", "new ceo", "new cfo"
    ]
    
    # Patterns financial à rejeter
    financial_patterns = [
        "financial calendar", "quarterly results", "annual report",
        "earnings", "financial results", "half-year results",
        "q1 results", "q2 results", "q3 results", "q4 results"
    ]
    
    # Patterns ESG à rejeter
    esg_patterns = [
        "sustainability report", "esg report", "carbon footprint",
        "diversity", "inclusion"
    ]
    
    text_lower = (title + " " + content).lower()
    
    # Rejeter si pattern RH sans contexte LAI
    for pattern in hr_patterns:
        if pattern in text_lower:
            # Sauf si contexte LAI fort
            if not any(lai in text_lower for lai in ["long-acting", "depot", "microsphere", "uzedy", "brixadi"]):
                return True
    
    # Rejeter si pattern financial pur
    for pattern in financial_patterns:
        if pattern in text_lower:
            # Sauf si contexte LAI fort
            if not any(lai in text_lower for lai in ["long-acting", "depot", "microsphere", "uzedy", "brixadi"]):
                return True
    
    return False
```

**Option B: Créer exclusion_scopes.yaml** (plus propre, plus long)

**Fichier**: `canonical/scopes/exclusion_scopes.yaml` (à créer)

```yaml
exclusion_scopes:
  hr_content:
    - "appoint"
    - "hire"
    - "join"
    - "promote"
    - "chief officer"
    - "board of directors"
  
  financial_generic:
    - "financial calendar"
    - "quarterly results"
    - "annual report"
    - "earnings"
    - "financial results"
  
  hr_recruitment_terms:
    - "new ceo"
    - "new cfo"
    - "new chief"
  
  financial_reporting_terms:
    - "q1 results"
    - "q2 results"
    - "q3 results"
    - "q4 results"
    - "half-year results"
```

**Recommandation**: Option A pour V16 (rapide), Option B pour V17 (propre)

---

### Phase 3: Test E2E V16 (1h)

#### Test 3.1: Relancer Pipeline Complet

```bash
# 1. Upload configs modifiés
aws s3 cp canonical/prompts/normalization/generic_normalization.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/normalization/ \
  --profile rag-lai-prod --region eu-west-3

aws s3 cp canonical/prompts/domain_scoring/lai_domain_scoring.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ \
  --profile rag-lai-prod --region eu-west-3

aws s3 cp canonical/domains/lai_domain_definition.yaml \
  s3://vectora-inbox-config-dev/canonical/domains/ \
  --profile rag-lai-prod --region eu-west-3

# 2. Créer client V16
cp client-config-examples/production/lai_weekly_v15.yaml \
   client-config-examples/production/lai_weekly_v16.yaml

# Modifier: client_id → lai_weekly_v16, template_version → 16.0.0

# 3. Upload client V16
aws s3 cp client-config-examples/production/lai_weekly_v16.yaml \
  s3://vectora-inbox-config-dev/clients/ \
  --profile rag-lai-prod --region eu-west-3

# 4. Lancer ingestion
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v16

# 5. Lancer normalisation
python .tmp/e2e_v16/invoke_normalize.py

# 6. Analyser résultats
python .tmp/e2e_v16/generate_analysis.py
```

#### Test 3.2: Critères de Succès V16

| Critère | V15 (Avant) | V16 (Cible) | Statut |
|---------|-------------|-------------|--------|
| Companies détectées | 0 | >5 | [ ] |
| Faux négatif Quince | ❌ | ✅ | [ ] |
| Faux positif Eli Lilly | ❌ | ✅ | [ ] |
| Faux négatif MedinCell grant | ❌ | ✅ | [ ] |
| Items RH ingérés | 3 | 0 | [ ] |
| Items financial ingérés | 3 | 0 | [ ] |
| Items relevant | 12 (41%) | ≥14 (48%) | [ ] |

---

## 📊 IMPACT ATTENDU

### Métriques Prévisionnelles V16

| Métrique | V13 | V15 | V16 (Prévu) | Évolution |
|----------|-----|-----|-------------|-----------|
| Items ingérés | 29 | 29 | ~23 | -6 (filtrage RH/financial) |
| Items relevant | 14 (48%) | 12 (41%) | 14-15 (61-65%) | +2-3 |
| Score moyen | 38.3 | 81.7 | 85+ | +3-5 |
| Faux positifs | 5 | 1 | 0 | -1 |
| Faux négatifs | 1 | 1 | 0 | -1 |
| Companies détectées | ✅ | ❌ | ✅ | Restauré |

### Gains Attendus

1. **Qualité**: 
   - 0 faux positifs
   - 0 faux négatifs
   - Companies détectées restaurées

2. **Efficacité**:
   - -20% items ingérés (filtrage RH/financial)
   - -20% appels Bedrock (économie coûts)

3. **Précision**:
   - Pure players: tous les partnerships matchés
   - Hybrid players: seulement avec signaux LAI forts

---

## 🎯 CHECKLIST VALIDATION

### Avant Déploiement

- [ ] generic_normalization.yaml modifié (companies + dosing_intervals)
- [ ] lai_domain_scoring.yaml modifié (CRITICAL RULES renforcées)
- [ ] lai_domain_definition.yaml modifié (exclusions + rule_7)
- [ ] Filtrage ingestion implémenté (Option A ou B)
- [ ] Configs uploadés sur S3 dev
- [ ] Client V16 créé et uploadé

### Après Test E2E V16

- [ ] Companies détectées: >5 ✅
- [ ] Quince matché ✅
- [ ] Eli Lilly rejeté ✅
- [ ] MedinCell grant matché ✅
- [ ] Items RH filtrés ✅
- [ ] Items financial filtrés ✅
- [ ] Items relevant: ≥14 (≥48%) ✅

---

## 📁 FICHIERS À MODIFIER

### Priorité 1 (Critique)

1. `canonical/prompts/normalization/generic_normalization.yaml`
   - Ligne 17-18: Ajouter {{item_title}}
   - Ligne 54-55: Ajouter référence company_scopes
   - Ligne 62-65: Améliorer extraction dosing_intervals

2. `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
   - Ligne 11-15: Renforcer CRITICAL RULES (anti-hallucination)

3. `canonical/domains/lai_domain_definition.yaml`
   - Ligne 160-167: Ajouter exclusions "injectables and devices"
   - Ligne 169-189: Ajouter rule_7 (pure_player + partnership)

### Priorité 2 (Important)

4. `canonical/prompts/normalization/generic_normalization.yaml`
   - Ligne 38-44: Améliorer classification event_type

5. `src/lambdas/ingest_v2/handler.py` (à localiser)
   - Ajouter fonction should_filter_out_pure_player()

6. `client-config-examples/production/lai_weekly_v16.yaml`
   - Créer depuis V15

---

## 🚀 PROCHAINES ÉTAPES

### Immédiat (Aujourd'hui)

1. Appliquer corrections Phase 1 (2-3h)
2. Appliquer corrections Phase 2 (1-2h)
3. Lancer test E2E V16 (1h)

### Court Terme (Cette Semaine)

4. Analyser résultats V16
5. Itérer si nécessaire (V17)
6. Documenter learnings

### Moyen Terme (Semaine Prochaine)

7. Implémenter exclusion_scopes.yaml proprement
8. Créer tests unitaires pour chaque règle
9. Préparer promotion vers stage

---

**Plan créé**: 2026-02-03  
**Durée estimée**: 4-6h  
**Statut**: ⏳ PRÊT POUR EXÉCUTION
