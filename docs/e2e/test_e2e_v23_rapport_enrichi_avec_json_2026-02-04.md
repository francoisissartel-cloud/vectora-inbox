# Rapport Enrichi E2E - lai_weekly_v23 DEV

**Date**: 2026-02-04
**Objectif**: Analyse humaine détaillée avec sorties JSON complètes

---

## 📊 VUE D'ENSEMBLE

- Total: 32 items
- Relevant: 20 (62%)
- Score moyen: 76.0

---

## 🔍 ITEM 1/5 - ANALYSE DÉTAILLÉE

### Titre
```
Medincell’s Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension (TEV-‘749 / mdc-TJK) for the Once-Monthly Treatment of Schizophrenia in Adults
```

### Métadonnées
- **Source**: N/A
- **Date**: 2025-12-09
- **URL**: https://www.medincell.com/wp-content/uploads/2025/12/MDC_Olanzapine-NDA-filing_09122025_EN_vf-2.pdf...

### Contenu brut (extrait)
```
Medincell’s Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension (TEV-‘749 / mdc-TJK) for the Once-Monthly Treatment of Schizophrenia in AdultsDecember 9, 2025December 9, 2025...
```

### 📝 SORTIE NORMALISATION (1er appel Bedrock)

```json
{
  "summary": "Teva Pharmaceuticals, a partner of Medincell, announced the submission of a New Drug Application to the U.S. FDA for an olanzapine extended-release injectable suspension (TEV-'749 / mdc-TJK) for the once-monthly treatment of schizophrenia in adults.",
  "entities": {
    "companies": [
      "Medincell",
      "Teva Pharmaceuticals"
    ],
    "molecules": [
      "olanzapine"
    ],
    "technologies": [
      "extended-release injectable suspension"
    ],
    "trademarks": [
      "TEV-'749",
      "mdc-TJK"
    ],
    "indications": [
      "schizophrenia"
    ],
    "dosing_intervals": [
      "once-monthly"
    ]
  },
  "event_classification": {
    "primary_type": "regulatory",
    "confidence": 0.8
  },
  "extracted_date": "2025-12-09",
  "date_confidence": 1.0,
  "normalization_metadata": {
    "bedrock_model": "claude-3-5-sonnet",
    "canonical_version": "2.0",
    "processing_time_ms": 0
  }
}
```

#### Analyse de la normalisation

**Entités extraites**:
- `companies`: 2 détecté(s) → Medincell, Teva Pharmaceuticals
- `molecules`: 1 détecté(s) → olanzapine
- `technologies`: 1 détecté(s) → extended-release injectable suspension
- `trademarks`: 2 détecté(s) → TEV-'749, mdc-TJK
- `indications`: 1 détecté(s) → schizophrenia
- `dosing_intervals`: 1 détecté(s) → once-monthly

**Classification événement**:
- Type primaire: `regulatory`
- Confidence: 0.80

### 🎯 SORTIE DOMAIN SCORING (2ème appel Bedrock)

```json
{
  "is_relevant": true,
  "score": 90,
  "confidence": "high",
  "signals_detected": {
    "strong": [
      "core_technologies: extended-release injectable suspension",
      "trademarks: TEV-'749, mdc-TJK"
    ],
    "medium": [
      "technology_families: extended-release",
      "dosing_intervals: once-monthly",
      "hybrid_companies: Teva Pharmaceuticals"
    ],
    "weak": [
      "molecules: olanzapine"
    ],
    "exclusions": []
  },
  "score_breakdown": {
    "base_score": 60,
    "entity_boosts": {
      "core_technologies": 20,
      "trademarks": 15,
      "hybrid_companies": 10,
      "technology_families": 5,
      "dosing_intervals": 5
    },
    "recency_boost": 0,
    "confidence_penalty": 0,
    "total": 90
  },
  "reasoning": "The item mentions core LAI technologies (extended-release injectable suspension), trademarks, dosing interval, and a hybrid company partner. Multiple strong and medium signals indicate high relevance to the LAI domain."
}
```

#### Analyse du domain scoring

**Décision finale**: ✅ RELEVANT
**Score**: 90/100
**Confidence**: high

**Signaux LAI détectés**:
- STRONG: core_technologies: extended-release injectable suspension, trademarks: TEV-'749, mdc-TJK
- MEDIUM: technology_families: extended-release, dosing_intervals: once-monthly, hybrid_companies: Teva Pharmaceuticals
- WEAK: molecules: olanzapine

**Calcul du score**:
```
Base score:           60
  + core_technologies    +20
  + trademarks           +15
  + hybrid_companies     +10
  + technology_families   +5
  + dosing_intervals      +5
  + recency_boost       +0
  + confidence_penalty  +0
                     ----
TOTAL:                90
```

**Reasoning**:
> The item mentions core LAI technologies (extended-release injectable suspension), trademarks, dosing interval, and a hybrid company partner. Multiple strong and medium signals indicate high relevance to the LAI domain.

#### ❓ Questions pour analyse humaine

1. **La normalisation est-elle correcte ?**
   - Les entités détectées correspondent-elles au contenu ?
   - Le summary capture-t-il l'essentiel ?
   - L'event_type est-il approprié ?

2. **Le domain scoring est-il justifié ?**
   - Les signaux détectés sont-ils pertinents ?
   - Le score reflète-t-il l'importance LAI de l'item ?
   - Le reasoning est-il convaincant ?

3. **Décision finale**
   - [ ] D'accord avec la décision du système
   - [ ] Pas d'accord - devrait être relevant
   - [ ] Pas d'accord - ne devrait pas être relevant
   - [ ] Score trop élevé/trop bas

**Notes**:
```


```

---

## 🔍 ITEM 2/5 - ANALYSE DÉTAILLÉE

### Titre
```
Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products
```

### Métadonnées
- **Source**: N/A
- **Date**: 2025-12-10
- **URL**: https://nanexa.com/mfn_news/nanexa-and-moderna-enter-into-license-and-option-agreement-for-the-devel...

### Contenu brut (extrait)
```
10 December, 2025Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based productsThe agreement covers the development of up to five undisclosed compounds. Nanexa will receive an upfront payment of USD 3 million and is entitled to up to USD 500 million in potential milestone payments as well as a tiered single-digit royalty on product sales.READ MORE...
```

### 📝 SORTIE NORMALISATION (1er appel Bedrock)

```json
{
  "summary": "Nanexa and Moderna have entered into a license and option agreement for the development of up to five undisclosed compounds using Nanexa's PharmaShell® technology. Nanexa will receive an upfront payment of $3 million and is eligible for up to $500 million in potential milestone payments and royalties.",
  "entities": {
    "companies": [
      "Nanexa",
      "Moderna"
    ],
    "molecules": [],
    "technologies": [
      "PharmaShell®"
    ],
    "trademarks": [
      "PharmaShell®"
    ],
    "indications": [],
    "dosing_intervals": []
  },
  "event_classification": {
    "primary_type": "partnership",
    "confidence": 0.8
  },
  "extracted_date": "2025-12-10",
  "date_confidence": 1.0,
  "normalization_metadata": {
    "bedrock_model": "claude-3-5-sonnet",
    "canonical_version": "2.0",
    "processing_time_ms": 0
  }
}
```

#### Analyse de la normalisation

**Entités extraites**:
- `companies`: 2 détecté(s) → Nanexa, Moderna
- `technologies`: 1 détecté(s) → PharmaShell®
- `trademarks`: 1 détecté(s) → PharmaShell®

**Classification événement**:
- Type primaire: `partnership`
- Confidence: 0.80

### 🎯 SORTIE DOMAIN SCORING (2ème appel Bedrock)

```json
{
  "is_relevant": true,
  "score": 90,
  "confidence": "high",
  "signals_detected": {
    "strong": [
      "core_technologies",
      "pure_player_companies",
      "trademarks"
    ],
    "medium": [],
    "weak": [],
    "exclusions": []
  },
  "score_breakdown": {
    "base_score": 70,
    "entity_boosts": {
      "pure_player_company": 10,
      "trademark": 10
    },
    "recency_boost": 0,
    "confidence_penalty": 0,
    "total": 90
  },
  "reasoning": "The item mentions the pure player company Nanexa, their core PharmaShell® technology which is a trademark, and a partnership event with Moderna. Multiple strong signals indicate high relevance to the LAI domain."
}
```

#### Analyse du domain scoring

**Décision finale**: ✅ RELEVANT
**Score**: 90/100
**Confidence**: high

**Signaux LAI détectés**:
- STRONG: core_technologies, pure_player_companies, trademarks

**Calcul du score**:
```
Base score:           70
  + pure_player_company  +10
  + trademark            +10
  + recency_boost       +0
  + confidence_penalty  +0
                     ----
TOTAL:                90
```

**Reasoning**:
> The item mentions the pure player company Nanexa, their core PharmaShell® technology which is a trademark, and a partnership event with Moderna. Multiple strong signals indicate high relevance to the LAI domain.

#### ❓ Questions pour analyse humaine

1. **La normalisation est-elle correcte ?**
   - Les entités détectées correspondent-elles au contenu ?
   - Le summary capture-t-il l'essentiel ?
   - L'event_type est-il approprié ?

2. **Le domain scoring est-il justifié ?**
   - Les signaux détectés sont-ils pertinents ?
   - Le score reflète-t-il l'importance LAI de l'item ?
   - Le reasoning est-il convaincant ?

3. **Décision finale**
   - [ ] D'accord avec la décision du système
   - [ ] Pas d'accord - devrait être relevant
   - [ ] Pas d'accord - ne devrait pas être relevant
   - [ ] Score trop élevé/trop bas

**Notes**:
```


```

---

## 🔍 ITEM 3/5 - ANALYSE DÉTAILLÉE

### Titre
```
Medincell Awarded New Grant to Fight Malaria
```

### Métadonnées
- **Source**: N/A
- **Date**: 2025-11-24
- **URL**: https://www.medincell.com/wp-content/uploads/2025/11/MDC_Gates-Malaria_PR_24112025_vf.pdf...

### Contenu brut (extrait)
```
Medincell Awarded New Grant to Fight MalariaNovember 24, 2025November 24, 2025...
```

### 📝 SORTIE NORMALISATION (1er appel Bedrock)

```json
{
  "summary": "Medincell was awarded a new grant to fund research efforts to fight malaria. The grant amount and details were not provided.",
  "entities": {
    "companies": [
      "Medincell"
    ],
    "molecules": [],
    "technologies": [],
    "trademarks": [],
    "indications": [
      "malaria"
    ],
    "dosing_intervals": []
  },
  "event_classification": {
    "primary_type": "partnership",
    "confidence": 0.8
  },
  "extracted_date": "2025-11-24",
  "date_confidence": 1.0,
  "normalization_metadata": {
    "bedrock_model": "claude-3-5-sonnet",
    "canonical_version": "2.0",
    "processing_time_ms": 0
  }
}
```

#### Analyse de la normalisation

**Entités extraites**:
- `companies`: 1 détecté(s) → Medincell
- `indications`: 1 détecté(s) → malaria

**Classification événement**:
- Type primaire: `partnership`
- Confidence: 0.80

### 🎯 SORTIE DOMAIN SCORING (2ème appel Bedrock)

```json
{
  "is_relevant": true,
  "score": 65,
  "confidence": "medium",
  "signals_detected": {
    "strong": [],
    "medium": [],
    "weak": [
      "indication: malaria"
    ],
    "exclusions": []
  },
  "score_breakdown": {
    "base_score": 60,
    "entity_boosts": {
      "company": 5
    },
    "recency_boost": 0,
    "confidence_penalty": 0,
    "total": 65
  },
  "reasoning": "The item mentions Medincell receiving a grant to research malaria treatments, which is a relevant indication for LAI therapies. However, no specific LAI technologies or products are mentioned, resulting in a medium confidence match with a moderate score."
}
```

#### Analyse du domain scoring

**Décision finale**: ✅ RELEVANT
**Score**: 65/100
**Confidence**: medium

**Signaux LAI détectés**:
- WEAK: indication: malaria

**Calcul du score**:
```
Base score:           60
  + company               +5
  + recency_boost       +0
  + confidence_penalty  +0
                     ----
TOTAL:                65
```

**Reasoning**:
> The item mentions Medincell receiving a grant to research malaria treatments, which is a relevant indication for LAI therapies. However, no specific LAI technologies or products are mentioned, resulting in a medium confidence match with a moderate score.

#### ❓ Questions pour analyse humaine

1. **La normalisation est-elle correcte ?**
   - Les entités détectées correspondent-elles au contenu ?
   - Le summary capture-t-il l'essentiel ?
   - L'event_type est-il approprié ?

2. **Le domain scoring est-il justifié ?**
   - Les signaux détectés sont-ils pertinents ?
   - Le score reflète-t-il l'importance LAI de l'item ?
   - Le reasoning est-il convaincant ?

3. **Décision finale**
   - [ ] D'accord avec la décision du système
   - [ ] Pas d'accord - devrait être relevant
   - [ ] Pas d'accord - ne devrait pas être relevant
   - [ ] Score trop élevé/trop bas

**Notes**:
```


```

---

## 🔍 ITEM 4/5 - ANALYSE DÉTAILLÉE

### Titre
```
09 January 2026RegulatoryCamurus announces FDA acceptance of NDA resubmission for Oclaiz™ for the treatment of acromegaly
```

### Métadonnées
- **Source**: N/A
- **Date**: 2026-01-09
- **URL**: https://www.camurus.com/media/press-releases/2026/camurus-announces-fda-acceptance-of-nda-resubmissi...

### Contenu brut (extrait)
```
202609 January 2026RegulatoryCamurus announces FDA acceptance of NDA resubmission for Oclaiz™ for the treatment of acromegaly202530 December 2025RegulatoryChange in number of shares and votes in Camurus16 December 2025Camurus and Gubra enter into a collaboration and license agreement to develop a long-acting treatment for hypoparathyroidism28 November 2025RegulatoryChange in number of shares and votes in Camurus13 November 2025RegulatoryCamurus’ Nomination Committee appointed for the Annual Gene...
```

### 📝 SORTIE NORMALISATION (1er appel Bedrock)

```json
{
  "summary": "Camurus announced that the FDA has accepted the resubmission of their New Drug Application (NDA) for Oclaiz™, a treatment for acromegaly.",
  "entities": {
    "companies": [
      "Camurus"
    ],
    "molecules": [],
    "technologies": [],
    "trademarks": [
      "Oclaiz™"
    ],
    "indications": [
      "acromegaly"
    ],
    "dosing_intervals": []
  },
  "event_classification": {
    "primary_type": "regulatory",
    "confidence": 0.8
  },
  "extracted_date": "2026-01-09",
  "date_confidence": 1.0,
  "normalization_metadata": {
    "bedrock_model": "claude-3-5-sonnet",
    "canonical_version": "2.0",
    "processing_time_ms": 0
  }
}
```

#### Analyse de la normalisation

**Entités extraites**:
- `companies`: 1 détecté(s) → Camurus
- `trademarks`: 1 détecté(s) → Oclaiz™
- `indications`: 1 détecté(s) → acromegaly

**Classification événement**:
- Type primaire: `regulatory`
- Confidence: 0.80

### 🎯 SORTIE DOMAIN SCORING (2ème appel Bedrock)

```json
{
  "is_relevant": true,
  "score": 80,
  "confidence": "high",
  "signals_detected": {
    "strong": [
      "pure_player_company: Camurus",
      "trademark: Oclaiz™"
    ],
    "medium": [],
    "weak": [
      "indication: acromegaly"
    ],
    "exclusions": []
  },
  "score_breakdown": {
    "base_score": 60,
    "entity_boosts": {
      "pure_player_company": 25,
      "trademark": 20
    },
    "recency_boost": 0,
    "confidence_penalty": 0,
    "total": 80
  },
  "reasoning": "The item mentions the pure player company Camurus and their trademark product Oclaiz™ for treatment of acromegaly. This is a regulatory event related to an LAI product, so it is highly relevant to the LAI domain."
}
```

#### Analyse du domain scoring

**Décision finale**: ✅ RELEVANT
**Score**: 80/100
**Confidence**: high

**Signaux LAI détectés**:
- STRONG: pure_player_company: Camurus, trademark: Oclaiz™
- WEAK: indication: acromegaly

**Calcul du score**:
```
Base score:           60
  + pure_player_company  +25
  + trademark            +20
  + recency_boost       +0
  + confidence_penalty  +0
                     ----
TOTAL:                80
```

**Reasoning**:
> The item mentions the pure player company Camurus and their trademark product Oclaiz™ for treatment of acromegaly. This is a regulatory event related to an LAI product, so it is highly relevant to the LAI domain.

#### ❓ Questions pour analyse humaine

1. **La normalisation est-elle correcte ?**
   - Les entités détectées correspondent-elles au contenu ?
   - Le summary capture-t-il l'essentiel ?
   - L'event_type est-il approprié ?

2. **Le domain scoring est-il justifié ?**
   - Les signaux détectés sont-ils pertinents ?
   - Le score reflète-t-il l'importance LAI de l'item ?
   - Le reasoning est-il convaincant ?

3. **Décision finale**
   - [ ] D'accord avec la décision du système
   - [ ] Pas d'accord - devrait être relevant
   - [ ] Pas d'accord - ne devrait pas être relevant
   - [ ] Score trop élevé/trop bas

**Notes**:
```


```

---

## 🔍 ITEM 5/5 - ANALYSE DÉTAILLÉE

### Titre
```
UZEDY® continues strong growth; Teva setting the stage for US NDA Submission for Olanzapine LAI in Q4 2025
```

### Métadonnées
- **Source**: N/A
- **Date**: 2025-11-05
- **URL**: https://www.medincell.com/wp-content/uploads/2025/11/PR_MDC_Teva-earnings-Q3_2025_05112025_vf.pdf...

### Contenu brut (extrait)
```
UZEDY® continues strong growth; Teva setting the stage for US NDA Submission for Olanzapine LAI in Q4 2025November 5, 2025November 5, 2025...
```

### 📝 SORTIE NORMALISATION (1er appel Bedrock)

```json
{
  "summary": "Teva is preparing to submit a New Drug Application (NDA) for an olanzapine long-acting injectable (LAI) formulation to the US FDA in Q4 2025. UZEDY®, a product of Teva, continues to show strong growth.",
  "entities": {
    "companies": [
      "Teva"
    ],
    "molecules": [
      "olanzapine"
    ],
    "technologies": [
      "LAI"
    ],
    "trademarks": [
      "UZEDY®"
    ],
    "indications": [],
    "dosing_intervals": []
  },
  "event_classification": {
    "primary_type": "regulatory",
    "confidence": 0.8
  },
  "extracted_date": "2025-11-05",
  "date_confidence": 1.0,
  "normalization_metadata": {
    "bedrock_model": "claude-3-5-sonnet",
    "canonical_version": "2.0",
    "processing_time_ms": 0
  }
}
```

#### Analyse de la normalisation

**Entités extraites**:
- `companies`: 1 détecté(s) → Teva
- `molecules`: 1 détecté(s) → olanzapine
- `technologies`: 1 détecté(s) → LAI
- `trademarks`: 1 détecté(s) → UZEDY®

**Classification événement**:
- Type primaire: `regulatory`
- Confidence: 0.80

### 🎯 SORTIE DOMAIN SCORING (2ème appel Bedrock)

```json
{
  "is_relevant": true,
  "score": 90,
  "confidence": "high",
  "signals_detected": {
    "strong": [
      "core_technologies: LAI",
      "pure_player_companies: Teva",
      "trademarks: UZEDY®"
    ],
    "medium": [],
    "weak": [
      "molecules: olanzapine"
    ],
    "exclusions": []
  },
  "score_breakdown": {
    "base_score": 70,
    "entity_boosts": {
      "core_technologies": 20,
      "pure_player_companies": 15,
      "trademarks": 10
    },
    "recency_boost": 5,
    "confidence_penalty": 0,
    "total": 90
  },
  "reasoning": "The item mentions a long-acting injectable (LAI) formulation of olanzapine by Teva, a pure-play pharma company, and their trademarked product UZEDY®. The regulatory event of an upcoming NDA submission is highly relevant to the LAI domain. Strong signals and a recent date result in a high confidence, high scoring match."
}
```

#### Analyse du domain scoring

**Décision finale**: ✅ RELEVANT
**Score**: 90/100
**Confidence**: high

**Signaux LAI détectés**:
- STRONG: core_technologies: LAI, pure_player_companies: Teva, trademarks: UZEDY®
- WEAK: molecules: olanzapine

**Calcul du score**:
```
Base score:           70
  + core_technologies    +20
  + pure_player_companies +15
  + trademarks           +10
  + recency_boost       +5
  + confidence_penalty  +0
                     ----
TOTAL:                90
```

**Reasoning**:
> The item mentions a long-acting injectable (LAI) formulation of olanzapine by Teva, a pure-play pharma company, and their trademarked product UZEDY®. The regulatory event of an upcoming NDA submission is highly relevant to the LAI domain. Strong signals and a recent date result in a high confidence, high scoring match.

#### ❓ Questions pour analyse humaine

1. **La normalisation est-elle correcte ?**
   - Les entités détectées correspondent-elles au contenu ?
   - Le summary capture-t-il l'essentiel ?
   - L'event_type est-il approprié ?

2. **Le domain scoring est-il justifié ?**
   - Les signaux détectés sont-ils pertinents ?
   - Le score reflète-t-il l'importance LAI de l'item ?
   - Le reasoning est-il convaincant ?

3. **Décision finale**
   - [ ] D'accord avec la décision du système
   - [ ] Pas d'accord - devrait être relevant
   - [ ] Pas d'accord - ne devrait pas être relevant
   - [ ] Score trop élevé/trop bas

**Notes**:
```


```

---

## ❌ ITEMS NON-RELEVANT (Échantillon)

### Item non-relevant 1/3

**Titre**: Partnership Opportunities in Drug Delivery 2025 Boston, October 27-28

**Sortie normalisation**:
```json
{
  "summary": "The text mentions an event titled 'Partnership Opportunities in Drug Delivery 2025' taking place in Boston on October 27-28. No other specific details about partnerships, companies, or technologies are provided.",
  "entities": {
    "companies": [],
    "molecules": [],
    "technologies": [],
    "trademarks": [],
    "indications": [],
    "dosing_intervals": []
  },
  "event_classification": {
    "primary_type": "partnership",
    "confidence": 0.8
  },
  "extracted_date": "2025-08-15",
  "date_confidence": 1.0,
  "normalization_metadata": {
    "bedrock_model": "claude-3-5-sonnet",
    "canonical_version": "2.0",
    "processing_time_ms": 0
  }
}
```

**Sortie domain scoring**:
```json
{
  "is_relevant": false,
  "score": 0,
  "confidence": "high",
  "signals_detected": {
    "strong": [],
    "medium": [],
    "weak": [],
    "exclusions": []
  },
  "score_breakdown": null,
  "reasoning": "The normalized item does not contain any signals related to long-acting injectable technologies, companies, products or indications. It only mentions a generic partnership event with no relevant details. Therefore, it is not relevant to the LAI domain."
}
```

**Raison du rejet**: The normalized item does not contain any signals related to long-acting injectable technologies, companies, products or indications. It only mentions a generic partnership event with no relevant details. Therefore, it is not relevant to the LAI domain.

---

### Item non-relevant 2/3

**Titre**: <a href="https://www.fiercepharma.com/marketing/rising-stars-barbara-leal-lives-and-works-mantra-humans-first-professionals-second" hreflang="en">Rising Stars: emagineHealth's Barbara Leal lives and works by the mantra of ‘humans first, professionals second’</a>

**Sortie normalisation**:
```json
{
  "summary": "The article is a Q&A with Barbara Leal of emagineHealth, discussing her approach to healthcare and pharma marketing. No specific companies, molecules, technologies, or dosing intervals are mentioned.",
  "entities": {
    "companies": [
      "emagineHealth"
    ],
    "molecules": [],
    "technologies": [],
    "trademarks": [],
    "indications": [],
    "dosing_intervals": []
  },
  "event_classification": {
    "primary_type": "corporate_move",
    "confidence": 0.8
  },
  "extracted_date": null,
  "date_confidence": 0.0,
  "normalization_metadata": {
    "bedrock_model": "claude-3-5-sonnet",
    "canonical_version": "2.0",
    "processing_time_ms": 0
  }
}
```

**Sortie domain scoring**:
```json
{
  "is_relevant": false,
  "score": 0,
  "confidence": "high",
  "signals_detected": {
    "strong": [],
    "medium": [],
    "weak": [],
    "exclusions": []
  },
  "score_breakdown": null,
  "reasoning": "No strong, medium or weak signals detected related to LAI domain. The item is about a marketing professional's approach and does not mention any specific companies, molecules, technologies or dosing intervals relevant to LAI."
}
```

**Raison du rejet**: No strong, medium or weak signals detected related to LAI domain. The item is about a marketing professional's approach and does not mention any specific companies, molecules, technologies or dosing intervals relevant to LAI.

---

### Item non-relevant 3/3

**Titre**: Publication of the 2026 financial calendar

**Sortie normalisation**:
```json
{
  "summary": "The news item announces the publication of the 2026 financial calendar for a company.",
  "entities": {
    "companies": [],
    "molecules": [],
    "technologies": [],
    "trademarks": [],
    "indications": [],
    "dosing_intervals": []
  },
  "event_classification": {
    "primary_type": "financial_results",
    "confidence": 0.8
  },
  "extracted_date": "2026-01-12",
  "date_confidence": 1.0,
  "normalization_metadata": {
    "bedrock_model": "claude-3-5-sonnet",
    "canonical_version": "2.0",
    "processing_time_ms": 0
  }
}
```

**Sortie domain scoring**:
```json
{
  "is_relevant": false,
  "score": 0,
  "confidence": "high",
  "signals_detected": {
    "strong": [],
    "medium": [],
    "weak": [],
    "exclusions": []
  },
  "score_breakdown": null,
  "reasoning": "No LAI signals detected. The item is about publishing a financial calendar, which is not relevant to the LAI domain."
}
```

**Raison du rejet**: No LAI signals detected. The item is about publishing a financial calendar, which is not relevant to the LAI domain.

---

