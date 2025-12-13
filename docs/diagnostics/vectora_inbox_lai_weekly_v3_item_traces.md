# Vectora Inbox LAI Weekly v3 - Traçage Items Critiques

**Objectif** : Tracer les items critiques dans le dernier run lai_weekly_v3 (104 items)  
**Basé sur** : Données normalisées du 11 décembre 2025 et newsletter finale

---

## Résumé Exécutif

| **Item Critique** | **Ingéré** | **Normalisé** | **Matché** | **En Newsletter** | **Diagnostic** |
|-------------------|------------|---------------|------------|-------------------|----------------|
| **Nanexa/Moderna PharmaShell** | ✅ | ❌ | ❌ | ❌ | **ÉCHEC NORMALISATION** - Summary vide |
| **UZEDY Bipolar Approval** | ✅ | ✅ | ❌ | ❌ | **ÉCHEC MATCHING** - Aucune technology détectée |
| **UZEDY Growth/NDA** | ✅ | ✅ | ❌ | ❌ | **ÉCHEC MATCHING** - Aucune technology détectée |
| **MedinCell Malaria Grant** | ✅ | ✅ | ❌ | ❌ | **ÉCHEC MATCHING** - Aucune technology détectée |
| **MedinCell Olanzapine NDA** | ✅ | ✅ | ✅ | ✅ | **SUCCÈS** - En newsletter |

**Constat principal** : Les items LAI-strong échouent principalement au **MATCHING** car aucune technology n'est détectée par Bedrock.

---

## 1. Traçage Item : Nanexa/Moderna PharmaShell

### 1.1 Données Brutes
```json
{
  "source_key": "press_corporate__nanexa",
  "title": "Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products",
  "url": "https://nanexa.com/mfn_news/nanexa-and-moderna-enter-into-license-and-option-agreement-for-the-development-of-pharmashell-based-products/",
  "date": "2025-12-11"
}
```

### 1.2 Traçage Pipeline
| **Étape** | **Status** | **Détail** |
|-----------|------------|------------|
| **Ingestion** | ✅ **RÉUSSI** | Item présent dans les données brutes |
| **Normalisation** | ❌ **ÉCHEC** | Summary vide : `"summary": ""` |
| **Entités détectées** | ❌ **ÉCHEC** | `"companies_detected": ["Nanexa"]` seulement |
| **Technologies détectées** | ❌ **ÉCHEC** | `"technologies_detected": []` |
| **Matching** | ❌ **ÉCHEC** | Pas de technology → pas de match |
| **Newsletter** | ❌ **ÉCHEC** | Item absent |

### 1.3 Diagnostic de l'Échec
**Cause racine** : **Échec de normalisation Bedrock**
- Le summary est vide, indiquant un problème d'extraction HTML ou de traitement Bedrock
- Sans contenu normalisé, Bedrock ne peut pas détecter PharmaShell® ni Moderna
- **PharmaShell®** est pourtant présent dans `technology_scopes.yaml` (technology_terms_high_precision)
- **Moderna** devrait être détecté comme company

**Impact** : Item LAI-strong majeur perdu dès la normalisation

---

## 2. Traçage Item : UZEDY Bipolar Approval

### 2.1 Données Normalisées
```json
{
  "source_key": "press_corporate__medincell",
  "title": "FDA Approves Expanded Indication for UZEDY® (risperidone) Extended-Release Injectable Suspension as a Treatment for Adults Living with Bipolar I Disorder",
  "summary": "The FDA has approved an expanded indication for UZEDY (risperidone extended-release injectable suspension) for the treatment of adults with Bipolar I Disorder...",
  "companies_detected": [],
  "molecules_detected": ["risperidone"],
  "technologies_detected": [],
  "event_type": "other"
}
```

### 2.2 Traçage Pipeline
| **Étape** | **Status** | **Détail** |
|-----------|------------|------------|
| **Ingestion** | ✅ **RÉUSSI** | Item présent |
| **Normalisation** | ✅ **RÉUSSI** | Summary correct, risperidone détecté |
| **Companies détectées** | ❌ **ÉCHEC** | `"companies_detected": []` (devrait détecter MedinCell) |
| **Technologies détectées** | ❌ **ÉCHEC** | `"technologies_detected": []` |
| **Matching** | ❌ **ÉCHEC** | Pas de technology → pas de match domain tech_lai_ecosystem |
| **Newsletter** | ❌ **ÉCHEC** | Item absent |

### 2.3 Diagnostic de l'Échec
**Cause racine** : **Échec de détection technology par Bedrock**
- **"Extended-Release Injectable"** est présent dans le titre et summary
- **"Extended-Release Injectable"** est dans `technology_scopes.yaml` (technology_terms_high_precision)
- **UZEDY** est présent dans `trademark_scopes.yaml` (lai_trademarks_global)
- Bedrock n'a détecté ni la technology ni le trademark

**Impact** : Item LAI-strong regulatory majeur perdu au matching

---

## 3. Traçage Item : UZEDY Growth/NDA

### 3.1 Données Normalisées
```json
{
  "source_key": "press_corporate__medincell",
  "title": "UZEDY® continues strong growth; Teva setting the stage for US NDA Submission for Olanzapine LAI in Q4 2025",
  "summary": "Teva's UZEDY® (risperidone extended-release injectable suspension) continues to demonstrate strong commercial growth. The company is preparing to submit a New Drug Application...",
  "companies_detected": [],
  "molecules_detected": ["olanzapine"],
  "technologies_detected": [],
  "event_type": "other"
}
```

### 3.2 Traçage Pipeline
| **Étape** | **Status** | **Détail** |
|-----------|------------|------------|
| **Ingestion** | ✅ **RÉUSSI** | Item présent |
| **Normalisation** | ✅ **RÉUSSI** | Summary correct, olanzapine détecté |
| **Companies détectées** | ❌ **ÉCHEC** | `"companies_detected": []` (devrait détecter Teva) |
| **Technologies détectées** | ❌ **ÉCHEC** | `"technologies_detected": []` |
| **Matching** | ❌ **ÉCHEC** | Pas de technology → pas de match |
| **Newsletter** | ❌ **ÉCHEC** | Item absent |

### 3.3 Diagnostic de l'Échec
**Cause racine** : **Échec de détection technology par Bedrock**
- **"extended-release injectable suspension"** est présent dans le summary
- **"LAI"** est présent dans le titre
- **UZEDY®** est présent dans le titre et summary
- Bedrock n'a détecté aucun de ces signaux LAI

**Impact** : Item LAI-strong commercial/regulatory perdu au matching

---

## 4. Traçage Item : MedinCell Malaria Grant

### 4.1 Données Normalisées
```json
{
  "source_key": "press_corporate__medincell",
  "title": "Medincell Awarded New Grant to Fight Malaria",
  "summary": "MedinCell has been awarded a new grant to support its efforts in fighting malaria. This funding will likely advance the company's research and development programs focused on malaria prevention and treatment.",
  "companies_detected": ["MedinCell"],
  "molecules_detected": [],
  "technologies_detected": [],
  "event_type": "other"
}
```

### 4.2 Traçage Pipeline
| **Étape** | **Status** | **Détail** |
|-----------|------------|------------|
| **Ingestion** | ✅ **RÉUSSI** | Item présent |
| **Normalisation** | ✅ **RÉUSSI** | Summary correct, MedinCell détecté |
| **Companies détectées** | ✅ **RÉUSSI** | `"companies_detected": ["MedinCell"]` |
| **Technologies détectées** | ❌ **ÉCHEC** | `"technologies_detected": []` |
| **Matching** | ❌ **ÉCHEC** | Pas de technology → pas de match tech_lai_ecosystem |
| **Newsletter** | ❌ **ÉCHEC** | Item absent |

### 4.3 Diagnostic de l'Échec
**Cause racine** : **Logique de matching trop stricte**
- MedinCell est correctement détecté comme company
- MedinCell est un pure player LAI (dans lai_companies_mvp_core)
- Selon le plan human feedback, les pure players LAI devraient avoir un matching contextuel
- La règle `domain_matching_rules.yaml` exige des signaux technology même pour les pure players

**Impact** : Item LAI-strong pure player perdu par logique de matching trop stricte

---

## 5. Traçage Item : MedinCell Olanzapine NDA (SUCCÈS)

### 5.1 Données Normalisées
```json
{
  "source_key": "press_corporate__medincell",
  "title": "Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension (TEV-'749 / mdc-TJK) for the Once-Monthly Treatment of Schizophrenia in Adults",
  "summary": "Teva Pharmaceuticals, in partnership with MedinCell, has submitted a New Drug Application (NDA) to the U.S. FDA for TEV-'749/mdc-TJK, an olanzapine extended-release injectable...",
  "companies_detected": ["MedinCell"],
  "molecules_detected": ["olanzapine"],
  "technologies_detected": [],
  "event_type": "other"
}
```

### 5.2 Traçage Pipeline
| **Étape** | **Status** | **Détail** |
|-----------|------------|------------|
| **Ingestion** | ✅ **RÉUSSI** | Item présent |
| **Normalisation** | ✅ **RÉUSSI** | Summary complet, entités détectées |
| **Companies détectées** | ✅ **RÉUSSI** | `"companies_detected": ["MedinCell"]` |
| **Molecules détectées** | ✅ **RÉUSSI** | `"molecules_detected": ["olanzapine"]` |
| **Technologies détectées** | ❌ **ÉCHEC** | `"technologies_detected": []` |
| **Matching** | ✅ **RÉUSSI** | Match réussi malgré absence technology |
| **Newsletter** | ✅ **RÉUSSI** | **Présent en newsletter** |

### 5.3 Diagnostic du Succès
**Pourquoi cet item passe-t-il ?**
- MedinCell détecté (pure player LAI)
- Olanzapine détecté (molecule LAI)
- Titre très explicite avec "Extended-Release Injectable Suspension"
- Probablement matché par une règle différente ou exception

**Anomalie** : Même problème de détection technology que les autres items UZEDY

---

## 6. Traçage Items "Noise" dans la Newsletter

### 6.1 Items HR DelSiTech (PRÉSENTS en newsletter)

#### DelSiTech Process Engineer
```json
{
  "title": "DelSiTech is Hiring a Process Engineer",
  "companies_detected": ["DelSiTech"],
  "technologies_detected": [],
  "event_type": "other"
}
```

#### DelSiTech Quality Director  
```json
{
  "title": "DelSiTech Seeks an Experienced Quality Director",
  "companies_detected": ["DelSiTech"],
  "technologies_detected": [],
  "event_type": "other"
}
```

### 6.2 Diagnostic du Passage
**Pourquoi ces items HR passent-ils ?**
- DelSiTech détecté (pure player LAI dans lai_companies_mvp_core)
- Bonus pure_player: 5.0 (configuré dans lai_weekly_v3.yaml)
- Aucune exclusion HR appliquée malgré `exclusion_scopes.hr_recruitment_terms`
- Score final probablement > 12 (seuil min_score)

**Problème** : Les exclusions HR ne sont pas appliquées dans le pipeline

---

## 7. Analyse des Causes Racines

### 7.1 Problème Principal : Détection Technology Défaillante

**Constat** : Bedrock ne détecte aucune technology LAI dans les items critiques
- "Extended-Release Injectable" non détecté
- "LAI" non détecté  
- "PharmaShell®" non détecté
- "UZEDY®" non détecté comme trademark

**Impact** : Matching domain tech_lai_ecosystem échoue systématiquement

### 7.2 Problème Secondaire : Exclusions Non Appliquées

**Constat** : Les exclusions HR/finance ne filtrent pas les items noise
- `exclusion_scopes.hr_recruitment_terms` non appliqué
- Items "hiring", "recruiting" passent en newsletter
- Pure player bonus (5.0) compense l'absence de signaux LAI

### 7.3 Problème Tertiaire : Matching Contextuel Non Implémenté

**Constat** : Les pure players LAI sans signaux technology explicites sont rejetés
- MedinCell malaria grant rejeté malgré pure player status
- Logique contextuelle du plan human feedback non active

---

## Conclusion Phase 4

**Phase 4 terminée** - Le diagnostic révèle que le problème principal n'est **PAS** dans les configurations (qui sont correctes) mais dans **l'exécution runtime** :

### 🔴 Problèmes Critiques Identifiés

1. **Bedrock ne détecte pas les technologies LAI** malgré leur présence dans technology_scopes.yaml
2. **Les exclusions HR/finance ne sont pas appliquées** malgré leur présence dans exclusion_scopes.yaml  
3. **Le matching contextuel pour pure players n'est pas implémenté** malgré sa définition dans domain_matching_rules.yaml

### 🎯 Items LAI-Strong Perdus
- **Nanexa/Moderna PharmaShell** : Échec normalisation (summary vide)
- **UZEDY regulatory** : Échec matching (technology non détectée)
- **MedinCell malaria** : Échec matching (logique contextuelle non active)

### ✅ Items Noise Présents
- **DelSiTech HR (2x)** : Passent car exclusions non appliquées + pure player bonus
- **MedinCell finance** : Passe car exclusions non appliquées + pure player bonus

Le problème est dans **l'implémentation du code Lambda**, pas dans les configurations.