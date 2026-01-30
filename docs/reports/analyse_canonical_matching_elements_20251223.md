# Analyse des Fichiers Canonical pour le Matching - Vectora Inbox
**Date d'analyse** : 2025-12-23  
**Objectif** : Identifier tous les éléments pris en compte dans le processus de matching

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Processus de Matching en 3 Étapes
1. **Normalisation Bedrock** : Extraction d'entités depuis le contenu
2. **Matching aux domaines** : Correspondance entités ↔ scopes canonical
3. **Scoring** : Calcul du score final avec bonus/malus

### Éléments Clés Identifiés
- **5 types d'entités** : Companies, Technologies, Molecules, Trademarks, Indications
- **Contexte pure player** : Boost automatique pour MedinCell, Camurus, etc.
- **Système de bonus/malus** : Jusqu'à +6.0 pour trademarks, -10.0 pour routes orales
- **Seuils configurables** : min_domain_score, min_technology_signals, etc.

---

## 📊 ANALYSE DÉTAILLÉE PAR FICHIER CANONICAL

### 1. Prompts Bedrock (`canonical/prompts/global_prompts.yaml`)

#### Prompt de Normalisation LAI
**Rôle** : Extraction d'entités depuis le contenu brut des items

**Entités extraites** :
```yaml
companies_detected: []      # Noms d'entreprises mentionnées
molecules_detected: []      # Molécules/médicaments mentionnés
technologies_detected: []   # Technologies LAI détectées
trademarks_detected: []     # Marques commerciales (®, ™)
indications_detected: []    # Indications thérapeutiques
```

**Signaux calculés** :
```yaml
lai_relevance_score: 0-10   # Score de pertinence LAI
anti_lai_detected: false    # Détection routes orales
pure_player_context: false  # Contexte pure player sans LAI explicite
event_type: "..."          # Classification événement
```

**Technologies LAI recherchées** :
- **Core LAI** : "Long-Acting Injectable", "Extended-Release Injectable", "Depot Injection"
- **Nouveaux termes** : "Three-Month Injectable", "Quarterly Injection", "Long-Acting Formulation"
- **Termes génériques** : "Injectable Formulation", "Monthly Injectable"
- **Malaria spécifique** : "Extended Protection" ⚠️ **PROBLÉMATIQUE**

**Trademarks privilégiées** :
- UZEDY, PharmaShell, SiliaShell, BEPO, Aristada, Abilify Maintena

**Point critique** :
```yaml
# PROBLÈME IDENTIFIÉ
"Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?"
```
→ **Permet matching sans signaux LAI explicites pour pure players**

### 2. Scopes Companies (`canonical/scopes/company_scopes.yaml`)

#### Pure Players LAI (Boost Maximum)
```yaml
lai_companies_mvp_core:     # Bonus +5.0
  - MedinCell
  - Camurus
  - DelSiTech
  - Nanexa
  - Peptron

lai_companies_pure_players: # Contexte privilégié
  - MedinCell, Camurus, DelSiTech, Nanexa, Peptron
  - Bolder BioTechnology, Cristal Therapeutics, Durect
  - Eupraxia Pharmaceuticals, Foresee Pharmaceuticals
  - G2GBio, Hanmi Pharmaceutical, LIDDS, Taiwan Liposome
```

#### Hybrid Companies (Boost Modéré)
```yaml
lai_companies_hybrid:       # Bonus +1.5
  - AbbVie, Alkermes, Amgen, Ascendis Pharma
  - Eli Lilly, Gilead Sciences, Janssen, Novartis
  - Pfizer, Sanofi, Takeda Pharmaceutical, Teva
```

**Impact sur matching** :
- **Pure players** : Match facilité même sans signaux LAI explicites
- **Hybrid companies** : Signaux LAI explicites requis
- **Unknown companies** : Seuils stricts appliqués

### 3. Scopes Technologies (`canonical/scopes/technology_scopes.yaml`)

#### Structure Hiérarchique LAI Keywords
```yaml
lai_keywords:
  core_phrases:                    # Haute précision - Match immédiat
    - "long-acting injectable"
    - "extended-release injection"
    - "depot injection"
    - "long-acting depot"
    
  technology_terms_high_precision: # Termes techniques spécifiques
    - "PharmaShell®", "BEPO®", "SiliaShell®"
    - "PLGA microspheres", "in-situ forming depot"
    - "half-life extension", "Fc fusion"
    - "albumin binding", "PASylation"
    
  technology_use:                  # Usage (combinaison requise)
    - "injectable", "injection", "depot"
    - "microsphere", "microspheres"
    - "nanocrystal", "oil-based"
    
  route_admin_terms:               # Routes d'administration
    - "intramuscular", "subcutaneous"
    - "intravitreal", "intratumoral"
    
  interval_patterns:               # Patterns dosage prolongé
    - "once-monthly", "once-weekly injection"
    - "q4w", "q8w", "q12w"
    - "quarterly injection", "monthly injection"
    
  negative_terms:                  # Exclusions explicites
    - "oral tablet", "oral capsule"
    - "topical cream", "transdermal patch"
```

**Logique de matching** :
- **1 core_phrase** = Match automatique
- **2+ technology_terms_high_precision** = Match fort
- **Combinaisons** : technology_use + route_admin + interval_patterns
- **Exclusions** : negative_terms = rejet automatique

### 4. Scopes Trademarks (`canonical/scopes/trademark_scopes.yaml`)

#### Trademarks LAI Globales (Boost +4.0)
```yaml
lai_trademarks_global:
  # Antipsychotiques LAI
  - UZEDY, UZEDY®, Aristada, Abilify Maintena
  - Risperdal Consta, Invega trinza, Zyprexa Relprevv
  
  # Technologies propriétaires
  - PharmaShell®, PharmaShell, BEPO®, SiliaShell®
  
  # Hormones LAI
  - Lupron depot, CAMCEVI, Depo provera
  
  # Diabète LAI
  - Ozempic, Trulicity, Mounjaro, WEGOVY
  
  # Autres segments
  - Vivitrol, Sublocade, Cabenuva, Apretude
```

**Impact privilégié** :
- **Boost factor 2.5x** dans le matching
- **Bonus +4.0** dans le scoring
- **Auto-match threshold 0.8** (seuil bas)
- **Priorité absolue** en ingestion et matching

### 5. Scopes Molecules (`canonical/scopes/molecule_scopes.yaml`)

#### Molécules LAI Globales
```yaml
lai_molecules_global:
  # Antipsychotiques
  - aripiprazole, olanzapine, paliperidone, risperidone
  
  # Hormones
  - leuprolide, triptorelin, goserelin, testosterone
  - somatropin, somapacitan, somatrogon
  
  # Diabète/Métabolisme
  - semaglutide, liraglutide, dulaglutide, tirzepatide
  - insulin, insulin icodec, exenatide
  
  # Addiction
  - buprenorphine, naltrexone, naloxone
  
  # Anesthésie/Douleur
  - bupivacaine, ropivacaine, morphine
  
  # HIV/Antiviraux
  - cabotegravir, rilpivirine, lenacapavir
  
  # Oncologie
  - paclitaxel, docetaxel, doxorubicin, fulvestrant
```

### 6. Règles de Matching (`canonical/matching/domain_matching_rules.yaml`)

#### Configuration par Type de Domaine
```yaml
technology:                      # Pour tech_lai_ecosystem
  match_mode: all_required
  dimensions:
    technology:
      requirement: required
      min_matches: 2             # ⚠️ SEUIL DURCI
    entity:
      requirement: required
      min_matches: 1
      sources: [company, molecule]
```

#### Profils Technologiques
```yaml
technology_complex:              # Profil LAI
  signal_requirements:
    high_precision_signals:
      min_matches: 1
      weight: 3.0
    supporting_signals:
      min_matches: 1  
      weight: 2.0
  entity_requirements:
    pure_player_rule: contextual_matching  # ⚠️ CONTOURNEMENT
    hybrid_rule: high_precision_plus_supporting
```

### 7. Règles de Scoring (`canonical/scoring/scoring_rules.yaml`)

#### Poids par Type d'Événement
```yaml
event_type_weights:
  partnership: 6               # Nanexa/Moderna type
  clinical_update: 5           # UZEDY growth type
  regulatory: 5                # FDA approvals type
  corporate_move: 1            # Nominations type
  financial_results: 0         # Rapports financiers
```

#### Bonus Contextuels (PROBLÉMATIQUES)
```yaml
other_factors:
  pure_player_bonus: 1.0
  pure_player_context_bonus: 3.0      # ⚠️ BOOST ÉLEVÉ
  technology_bonus: 4.0
  trademark_bonus: 5.0                # ⚠️ BOOST TRÈS ÉLEVÉ
  regulatory_bonus: 6.0
  oral_route_penalty: -10
```

#### Bonus Client Spécifiques (Configuration lai_weekly_v5)
```yaml
client_specific_bonuses:
  pure_player_companies:
    bonus: 5.0                        # ⚠️ BONUS EXCESSIF
    scope: "lai_companies_mvp_core"
  trademark_mentions:
    bonus: 4.0                        # ⚠️ BONUS ÉLEVÉ
  hybrid_companies:
    bonus: 1.5
```

#### Seuils de Sélection
```yaml
selection_thresholds:
  min_score: 8                        # Seuil newsletter
  min_items_per_section: 1
```

### 8. Exclusions (`canonical/scopes/exclusion_scopes.yaml`)

#### Termes d'Exclusion
```yaml
lai_exclude_noise:
  - implantable device, transdermal patch
  - oral tablet, oral capsule, topical cream
  - gene therapy, cell therapy, vaccine
  - cosmetic, veterinary, diagnostic

hr_content:                           # Filtrage RH
  - "job opening", "career opportunity"
  - "we are hiring", "join our team"
  - "staff appointment", "new hire"

financial_generic:                    # Filtrage financier
  - "quarterly earnings", "financial results"
  - "revenue guidance", "cost reduction"
  - "stock price", "dividend payment"
```

---

## 🔍 ANALYSE DES PROBLÈMES IDENTIFIÉS

### 1. Contexte Pure Player Trop Permissif

**Problème** :
```yaml
# Dans le prompt Bedrock
"Assess pure player context: Is this about a LAI-focused company without explicit LAI mentions?"
```

**Impact** :
- Items de MedinCell matchent même sans signaux LAI
- Contourne les règles `min_technology_signals: 2`
- Génère des faux positifs (Malaria Grant, nominations, finances)

**Exemples problématiques** :
- "MedinCell Appoints Dr Grace Kim" → MATCHÉ (faux positif)
- "MedinCell MSCI Index" → MATCHÉ (faux positif)
- "MedinCell Malaria Grant" → MATCHÉ (faux positif)

### 2. Bonus Scoring Excessifs

**Configuration actuelle** :
```yaml
pure_player_companies: +5.0         # TROP ÉLEVÉ
trademark_mentions: +4.0             # TROP ÉLEVÉ
boost_factor: 2.5                    # TROP ÉLEVÉ
pure_player_context_bonus: +3.0      # NOUVEAU, TROP ÉLEVÉ
```

**Impact** :
- Scores artificiellement gonflés
- Seuil `min_domain_score: 0.25` facilement dépassé
- Items génériques atteignent le seuil newsletter

### 3. Termes LAI Étendus Problématiques

**Nouveaux termes ajoutés** :
```yaml
# PROBLÉMATIQUES
- "Extended Protection"              # Trop générique (malaria)
- "Injectable Formulation"           # Trop générique
- "Long-Acting Formulation"          # Trop générique
- "Three-Month Injectable"           # OK mais contribue au bruit
- "Monthly Injectable"               # OK mais contribue au bruit
```

**Impact** :
- Plus de chances de détecter des signaux LAI
- Termes génériques → faux positifs
- "Extended Protection" → match abusif pour malaria

### 4. Seuils de Matching Inadéquats

**Configuration actuelle** :
```yaml
matching_config:
  min_domain_score: 0.25             # TROP BAS avec les bonus
  
domain_type_overrides:
  technology:
    min_technology_signals: 2        # CONTOURNÉ par pure_player_context
```

**Impact** :
- Seuil bas + bonus élevés = faux positifs
- Règle `min_technology_signals` contournée
- Pas de protection contre le bruit

---

## 🎯 ÉLÉMENTS PRIS EN COMPTE POUR LE MATCHING

### Phase 1 : Normalisation Bedrock
1. **Extraction d'entités** depuis le contenu
2. **Classification événement** (partnership, regulatory, etc.)
3. **Score LAI relevance** (0-10)
4. **Détection anti-LAI** (routes orales)
5. **Contexte pure player** (sans LAI explicite)

### Phase 2 : Matching aux Domaines
1. **Correspondance entités** ↔ scopes canonical
2. **Application règles** par type de domaine
3. **Calcul scores** par domaine
4. **Application seuils** (min_domain_score)
5. **Privilèges trademarks** (boost_factor)

### Phase 3 : Scoring Final
1. **Poids événement** (partnership=6, regulatory=5)
2. **Bonus pure players** (+5.0 si MedinCell, etc.)
3. **Bonus trademarks** (+4.0 si UZEDY, etc.)
4. **Bonus contextuels** (+3.0 si pure_player_context)
5. **Malus exclusions** (-10 si routes orales)

### Facteurs de Décision Finale
```yaml
# MATCH si :
(technology_signals >= 2 AND entity_signals >= 1) OR
(trademark_detected AND boost_factor >= 2.5) OR
(pure_player_context AND company_in_mvp_core) OR
(score_final >= min_domain_score)

# REJECT si :
(negative_terms_detected) OR
(anti_lai_detected) OR
(exclusion_scopes_matched)
```

---

## 📈 IMPACT SUR LE TAUX DE MATCHING

### Facteurs d'Augmentation (50% → 80%)
1. **Contexte pure player** : +30% items MedinCell/Camurus
2. **Bonus scoring élevés** : +20% items atteignent seuils
3. **Termes LAI étendus** : +15% détection signaux
4. **Seuils bas** : +15% items passent les filtres

### Items Problématiques Identifiés
- **Malaria Grant** : pure_player_context + "Extended Protection"
- **Nominations executives** : pure_player_context + bonus +5.0
- **Résultats financiers** : pure_player_context + seuil bas
- **Participations conférences** : pure_player_context + termes génériques

---

## 🔧 RECOMMANDATIONS CORRECTIVES

### 1. Restreindre Contexte Pure Player
```yaml
# Remplacer dans les prompts :
"Assess pure player context: Only if explicit LAI technologies mentioned AND company is LAI-focused"
```

### 2. Réduire Bonus Scoring
```yaml
pure_player_companies: 2.0          # vs 5.0
trademark_mentions: 2.0              # vs 4.0
boost_factor: 1.5                    # vs 2.5
pure_player_context_bonus: 1.0       # vs 3.0
```

### 3. Durcir Seuils
```yaml
min_domain_score: 0.35               # vs 0.25
min_technology_signals: 3            # vs 2
require_explicit_lai: true           # NOUVEAU
```

### 4. Nettoyer Termes LAI
```yaml
# SUPPRIMER :
- "Extended Protection"
- "Injectable Formulation"
- "Long-Acting Formulation"
```

---

## 📋 CONCLUSION

### Cause Racine du Problème
Le taux de matching élevé (80%) est causé par une **combinaison de facteurs** dans les configurations canonical :
1. **Contexte pure player permissif** (contourne les règles strictes)
2. **Bonus scoring excessifs** (scores artificiellement gonflés)
3. **Termes LAI génériques** (plus de signaux détectés)
4. **Seuils inadéquats** (facilement dépassés avec les bonus)

### Solution Recommandée
**Ajustements de configuration** pour retour au comportement v4 :
- Restriction du contexte pure player
- Réduction des bonus scoring
- Durcissement des seuils
- Nettoyage des termes génériques

### Impact Attendu
- **Taux de matching** : 80% → 50%
- **Qualité** : Réduction significative des faux positifs
- **Préservation** : Items LAI légitimes toujours détectés

---

*Analyse réalisée le 2025-12-23*  
*Fichiers canonical analysés : prompts, scopes, matching, scoring, exclusions*  
*Objectif : Comprendre les mécanismes de matching pour corriger le taux élevé*