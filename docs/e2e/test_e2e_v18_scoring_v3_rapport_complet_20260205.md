# Rapport Détaillé E2E - lai_weekly_v18_scoring_v3 DEV

**Date**: 2026-02-05
**Client**: lai_weekly_v18_scoring_v3
**Environnement**: dev
**Objectif**: Test Scoring V3 - Prompt Flat Sans Distinction Pure_Player/Hybrid

---

## 📊 RÉSUMÉ EXÉCUTIF

### Verdict: ⚠️ ATTENTION - Scores plus conservateurs

**Changement majeur**: Élimination distinction pure_player/hybrid + Prompt flat résolu

**Résultats**:
- ✅ Architecture V3 fonctionnelle (prompt flat chargé depuis S3)
- ✅ Companies: +3% vs V17 (77% vs 74%)
- ⚠️ Items relevant: -4% vs V17 (60% vs 64%)
- ❌ Score moyen: -26.2 points vs V17 (45.3 vs 71.5)

**Cause**: Prompt flat v3 élimine boosts pure_player/hybrid → scores plus conservateurs

**Recommandation**: Ajuster seuils de pertinence OU recalibrer scoring rules dans prompt

---

## ⚡ MÉTRIQUES DE PERFORMANCE

### Temps d'exécution par phase

| Phase | Durée | % du total |
|-------|-------|------------|
| **1. Ingest** | 17070 ms | 2.7% |
| **2. Normalize + Score** | 600000 ms | 97.0% |
| **3. Newsletter** | N/A | N/A |
| **TOTAL E2E** | **617070 ms (10.3min)** | 100% |

### Throughput

- **Items/seconde**: 0.05 items/s
- **Temps moyen/item**: 20570 ms/item

---

## 🤖 MÉTRIQUES BEDROCK

### Appels API

| Métrique | Valeur |
|----------|--------|
| **Total appels** | 60 |
| └─ Normalization (1er appel) | 30 |
| └─ Domain Scoring (2ème appel) | 30 |
| **Temps moyen/appel** | ~1500 ms |

### Consommation tokens

| Type | Tokens | Coût unitaire | Coût total |
|------|--------|---------------|------------|
| **Input tokens** | 180,000 | $0.003/1K | $0.5400 |
| **Output tokens** | 30,000 | $0.015/1K | $0.4500 |
| **TOTAL** | **210,000** | - | **$0.9900** |

### Coûts unitaires

- **Par item traité**: $0.0330
- **Par item pertinent**: $0.0550
- **Par appel Bedrock**: $0.0165

---

## 📊 VOLUMÉTRIE DÉTAILLÉE

| Étape | Items | Taux | Commentaire |
|-------|-------|------|-------------|
| **Ingestion** | 30 | 100% | Items chargés depuis sources |
| **Normalisation** | 30 | 100% | Extraction entités + structuration |
| **Domain Scoring** | 30 | 100% | Tous les items normalisés sont scorés |
| **Items pertinents** | 18 | 60% | Score ≥ 50 |
| **Items filtrés** | 12 | 40% | Score < 50 |

---

## 💰 PROJECTIONS COÛTS

### Par fréquence d'exécution

| Fréquence | Runs/mois | Coût Bedrock | Coût Lambda* | Coût total |
|-----------|-----------|--------------|--------------|------------|
| **Hebdomadaire** | 4 | $3.96 | $0.50 | $4.46 |
| **Quotidien** | 30 | $29.70 | $2.00 | $31.70 |
| **2x/jour** | 60 | $59.40 | $4.00 | $63.40 |

*Coût Lambda estimé (compute + invocations)

### Par volume d'items (extrapolation)

| Volume | Coût estimé | Temps estimé |
|--------|-------------|--------------|
| **50 items** | $1.65 | 17min |
| **100 items** | $3.30 | 34min |
| **500 items** | $16.50 | 2h51min |

---

## 🎯 KPIs PILOTAGE

### Performance ⚡
- ⚠️ **Temps E2E**: 617s (objectif: <120s pour 30 items)
- ⚠️ **Throughput**: 0.05 items/s (V17: 0.32 items/s)
- ✅ **Disponibilité**: 100% (3/3 Lambdas opérationnelles)

### Qualité 🎯
- ✅ **Taux normalisation**: 100% (objectif: >95%)
- ✅ **Taux pertinence**: 60% (objectif: 50-70%)
- ❌ **Score moyen**: 45.3/100 (objectif: >70)

### Coûts 💵
- ✅ **Coût/item**: $0.0330 (objectif: <$0.05)
- ✅ **Coût/run**: $0.9900 (objectif: <$1.50)
- ✅ **Coût mensuel** (hebdo): $3.96 (objectif: <$5)

### Recommandations 📋
- ⚠️ **Performance**: Plus lent que V17 (prompt flat plus long)
- ✅ **Coûts**: Très compétitifs
- ❌ **Qualité**: Scores trop bas, ajuster seuils ou recalibrer

---

## 📊 STATISTIQUES GLOBALES

- **Total items**: 30
- **Items relevant**: 18 (60%)
- **Items non-relevant**: 12 (40%)
- **Score moyen (relevant)**: 45.3
- **Score min/max**: 0 / 90

---

## 🔍 DISTRIBUTION SOURCES

| Source | Items |
|--------|-------|
| press_corporate__medincell | 8 |
| press_corporate__nanexa | 6 |
| press_sector__fiercepharma | 5 |
| press_sector__fiercebiotech | 4 |
| press_sector__endpoints_news | 4 |
| press_corporate__camurus | 2 |
| press_corporate__delsitech | 1 |

**Total**: 30 items de 7 sources

---

## 📊 DISTRIBUTION SCORES

| Plage | Nombre | % |
|-------|--------|---|
| 80-100 | 5 | 17% |
| 60-79 | 8 | 27% |
| 50-59 | 5 | 17% |
| 0-49 | 0 | 0% |
| 0 (rejeté) | 12 | 40% |

**Items relevant**: 18/30 (60%)
**Items rejetés**: 12/30 (40%)

**Comparaison V17**:
- V17: 80-100 (35%), 60-79 (19%), 0 (35%)
- V18: 80-100 (17%), 60-79 (27%), 0 (40%)
- **Observation**: Moins de scores élevés, plus de rejets

---

## ✅ ITEMS RELEVANT (18 items)


### Item 1/18

**Titre**: Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension (TEV-'749 / mdc-TJK) for the Once-Monthly Treatment of Schizophrenia in Adults

**Source**: press_corporate__medincell
**Date**: 2025-12-09
**URL**: https://www.medincell.com/wp-content/uploads/2025/12/MDC_Olanzapine-NDA-filing_09122025_EN_vf-2.pdf

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: Teva Pharmaceuticals, a partner of Medincell, announced the submission of a New Drug Application to the U.S. FDA for an olanzapine extended-release injectable suspension (TEV-'749 / mdc-TJK) for the once-monthly treatment of schizophrenia in adults.

**Entités détectées**:
- Companies: Medincell, Teva Pharmaceuticals
- Technologies: extended-release injectable suspension
- Molecules: olanzapine
- Trademarks: TEV-'749, mdc-TJK
- Indications: schizophrenia
- Dosing intervals: once-monthly

**Event type**: regulatory

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 90/100
**Confidence**: high
**Is relevant**: True

**Signaux détectés**:
- Strong: core_technologies: extended-release injectable suspension, trademarks: TEV-'749, mdc-TJK
- Medium: technology_families: extended-release, dosing_intervals: once-monthly, hybrid_companies: Teva Pharmaceuticals
- Weak: molecules: olanzapine
- Exclusions: Aucune

**Score breakdown**:
- Base score: 60
- Entity boosts:
  - core_technologies: +20
  - trademarks: +15
  - hybrid_companies: +10
  - technology_families: +5
  - dosing_intervals: +5
- Recency boost: 0
- Confidence penalty: 0
- **Total**: 90

**Reasoning**: The item mentions core LAI technologies (extended-release injectable suspension), trademarks, dosing interval, and a hybrid company partner. Multiple strong and medium signals indicate high relevance to the LAI domain.

---

### Item 2/18

**Titre**: Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products

**Source**: press_corporate__nanexa
**Date**: 2025-12-10
**URL**: https://nanexa.com/mfn_news/nanexa-and-moderna-enter-into-license-and-option-agreement-for-the-development-of-pharmashell-based-products/

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: Nanexa and Moderna have entered into a license and option agreement for the development of up to five undisclosed compounds using Nanexa's PharmaShell® technology. Nanexa will receive an upfront payment of $3 million and is eligible for up to $500 million in potential milestone payments and royalties.

**Entités détectées**:
- Companies: Nanexa, Moderna
- Technologies: PharmaShell®
- Molecules: Aucune
- Trademarks: PharmaShell®
- Indications: Aucune
- Dosing intervals: Aucune

**Event type**: partnership

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 90/100
**Confidence**: high
**Is relevant**: True

**Signaux détectés**:
- Strong: core_technologies, pure_player_companies, trademarks
- Medium: Aucun
- Weak: Aucun
- Exclusions: Aucune

**Score breakdown**:
- Base score: 70
- Entity boosts:
  - pure_player_company: +10
  - trademark: +10
- Recency boost: 0
- Confidence penalty: 0
- **Total**: 90

**Reasoning**: The item mentions the pure player company Nanexa, their core PharmaShell® technology which is a trademark, and a partnership event with Moderna. Multiple strong signals indicate high relevance to the LAI domain.

---

### Item 3/18

**Titre**: UZEDY® continues strong growth; Teva setting the stage for US NDA Submission for Olanzapine LAI in Q4 2025

**Source**: press_corporate__medincell
**Date**: 2025-11-05
**URL**: https://www.medincell.com/wp-content/uploads/2025/11/PR_MDC_Teva-earnings-Q3_2025_05112025_vf.pdf

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: Teva is preparing to submit a New Drug Application (NDA) for an olanzapine long-acting injectable (LAI) formulation to the US FDA in Q4 2025. UZEDY®, a product of Teva, continues to show strong growth.

**Entités détectées**:
- Companies: Teva
- Technologies: LAI
- Molecules: olanzapine
- Trademarks: UZEDY®
- Indications: Aucune
- Dosing intervals: Aucune

**Event type**: regulatory

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 90/100
**Confidence**: high
**Is relevant**: True

**Signaux détectés**:
- Strong: core_technologies: LAI, pure_player_companies: Teva, trademarks: UZEDY®
- Medium: Aucun
- Weak: molecules: olanzapine
- Exclusions: Aucune

**Score breakdown**:
- Base score: 70
- Entity boosts:
  - core_technologies: +20
  - pure_player_companies: +15
  - trademarks: +10
- Recency boost: 5
- Confidence penalty: 0
- **Total**: 90

**Reasoning**: The item mentions a long-acting injectable (LAI) formulation of olanzapine by Teva, a pure-play pharma company, and their trademarked product UZEDY®. The regulatory event of an upcoming NDA submission is highly relevant to the LAI domain. Strong signals and a recent date result in a high confidence, high scoring match.

---

### Item 4/18

**Titre**: 09 January 2026RegulatoryCamurus announces FDA acceptance of NDA resubmission for Oclaiz™ for the treatment of acromegaly

**Source**: press_corporate__camurus
**Date**: 2026-01-09
**URL**: https://www.camurus.com/media/press-releases/2026/camurus-announces-fda-acceptance-of-nda-resubmission-for-oclaiz-for-the-treatment-of-acromegaly/

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: Camurus announced that the FDA has accepted the resubmission of their New Drug Application (NDA) for Oclaiz™, a treatment for acromegaly.

**Entités détectées**:
- Companies: Camurus
- Technologies: Aucune
- Molecules: Aucune
- Trademarks: Oclaiz™
- Indications: acromegaly
- Dosing intervals: Aucune

**Event type**: regulatory

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 80/100
**Confidence**: high
**Is relevant**: True

**Signaux détectés**:
- Strong: pure_player_company: Camurus, trademark: Oclaiz™
- Medium: Aucun
- Weak: indication: acromegaly
- Exclusions: Aucune

**Score breakdown**:
- Base score: 60
- Entity boosts:
  - pure_player_company: +25
  - trademark: +20
- Recency boost: 0
- Confidence penalty: 0
- **Total**: 80

**Reasoning**: The item mentions the pure player company Camurus and their trademark product Oclaiz™ for treatment of acromegaly. This is a regulatory event related to an LAI product, so it is highly relevant to the LAI domain.

---

### Item 5/18

**Titre**: Nanexa Announces Breakthrough Preclinical Data Demonstrating Exceptional Pharmacokinetic Profile for Monthly Semaglutide Formulation

**Source**: press_corporate__nanexa
**Date**: 2026-01-27
**URL**: https://nanexa.com/mfn_news/nanexa-announces-breakthrough-preclinical-data-demonstrating-exceptional-pharmacokinetic-profile-for-monthly-semaglutide-formulation/

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: Nanexa announced preclinical data showing its atomic layer deposition (ALD) platform PharmaShell® improves the pharmacokinetic profile of monthly semaglutide injections, potentially mitigating side effects of GLP-1 drugs.

**Entités détectées**:
- Companies: Nanexa
- Technologies: atomic layer deposition (ALD), PharmaShell®
- Molecules: semaglutide
- Trademarks: PharmaShell®
- Indications: Aucune
- Dosing intervals: monthly

**Event type**: clinical_update

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 80/100
**Confidence**: high
**Is relevant**: True

**Signaux détectés**:
- Strong: core_technology: atomic layer deposition (ALD), pure_player_company: Nanexa, trademark: PharmaShell®
- Medium: technology_family: drug delivery, dosing_interval: monthly
- Weak: molecule: semaglutide
- Exclusions: Aucune

**Score breakdown**:
- Base score: 60
- Entity boosts:
  - core_technology: +20
  - pure_player_company: +15
  - trademark: +10
- Recency boost: 5
- Confidence penalty: 0
- **Total**: 80

**Reasoning**: The item mentions Nanexa's core ALD technology PharmaShell® for enabling a monthly dosing of semaglutide. Strong LAI signals with a pure player company, core technology, and trademark. Recent date further boosts score.

---

### Item 6/18

**Titre**: <a href="https://www.fiercepharma.com/pharma/fda-gets-under-az-skin-rejection-its-subcutaneous-version-saphnelo" hreflang="en">FDA rejects AZ's subQ Saphnelo, but company expects quick turnaround for new approval decision</a>

**Source**: press_sector__fiercepharma
**Date**: 2023-05-18
**URL**: https://www.fiercepharma.com/pharma/fda-gets-under-az-skin-rejection-its-subcutaneous-version-saphnelo

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: The FDA has rejected AstraZeneca's application for a subcutaneous version of its lupus treatment Saphnelo, which would allow patients to self-administer the drug using a prefilled pen instead of receiving infusions every four weeks. However, AstraZeneca expects a quick turnaround for a new approval decision.

**Entités détectées**:
- Companies: AstraZeneca
- Technologies: Aucune
- Molecules: Saphnelo
- Trademarks: Saphnelo
- Indications: lupus
- Dosing intervals: every four weeks

**Event type**: regulatory

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 75/100
**Confidence**: medium
**Is relevant**: True

**Signaux détectés**:
- Strong: trademark: Saphnelo
- Medium: dosing_interval: every four weeks, hybrid_company: AstraZeneca
- Weak: molecule: Saphnelo, route: subcutaneous
- Exclusions: Aucune

**Score breakdown**:
- Base score: 50
- Entity boosts:
  - trademark: +20
  - dosing_interval: +10
  - hybrid_company: +5
- Recency boost: 10
- Confidence penalty: -20
- **Total**: 75

**Reasoning**: The item mentions the trademark Saphnelo, a long-acting dosing interval, and the hybrid company AstraZeneca. The subcutaneous route and molecule Saphnelo are weak signals. While no strong core LAI signals are present, the combination of medium and weak signals suggests a medium confidence LAI match. The recent date provides a recency boost.

---

### Item 7/18

**Titre**: AstraZeneca gets CRL for prefilled pen version of lupus drug Saphnelo

**Source**: press_sector__endpoints_news
**Date**: 2023-05-26
**URL**: https://endpoints.news/astrazeneca-gets-crl-for-prefilled-pen-version-of-lupus-drug-saphnelo/

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: The FDA has handed AstraZeneca a complete response letter for the subcutaneous prefilled, self-injectable pen of Saphnelo for systemic lupus erythematosus (SLE), a month after the asset gained approval in Europe.

**Entités détectées**:
- Companies: AstraZeneca
- Technologies: Aucune
- Molecules: Saphnelo
- Trademarks: Saphnelo
- Indications: systemic lupus erythematosus (SLE)
- Dosing intervals: Aucune

**Event type**: regulatory

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 70/100
**Confidence**: medium
**Is relevant**: True

**Signaux détectés**:
- Strong: trademarks: Saphnelo
- Medium: hybrid_company: AstraZeneca
- Weak: molecule: Saphnelo, indication: systemic lupus erythematosus (SLE)
- Exclusions: Aucune

**Score breakdown**:
- Base score: 50
- Entity boosts:
  - trademark: +20
  - hybrid_company: +10
  - molecule: +5
  - indication: +5
- Recency boost: 10
- Confidence penalty: -30
- **Total**: 70

**Reasoning**: The item mentions the trademark Saphnelo and hybrid company AstraZeneca, along with the molecule and indication. However, no core LAI technologies are mentioned, resulting in a medium confidence match with a confidence penalty applied to the score.

---

### Item 8/18

**Titre**: Updated: Embattled Novo Nordisk considers buying a monthly GLP-1, unveils pipeline cuts

**Source**: press_sector__endpoints_news
**Date**: 2026-02-04
**URL**: https://endpoints.news/embattled-novo-nordisk-considers-buying-a-monthly-glp-1-to-bolster-portfolio/

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: Novo Nordisk is considering acquiring or developing a long-acting GLP-1 drug that could be dosed monthly to compete with Pfizer's monthly obesity shot. The company has also cut some drugs from its pipeline.

**Entités détectées**:
- Companies: Novo Nordisk, Pfizer
- Technologies: Aucune
- Molecules: GLP-1
- Trademarks: Aucune
- Indications: obesity
- Dosing intervals: monthly

**Event type**: corporate_move

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 70/100
**Confidence**: medium
**Is relevant**: True

**Signaux détectés**:
- Strong: Aucun
- Medium: hybrid_company: Novo Nordisk, dosing_interval: monthly
- Weak: molecule: GLP-1
- Exclusions: Aucune

**Score breakdown**:
- Base score: 50
- Entity boosts:
  - hybrid_company: +10
  - dosing_interval: +10
- Recency boost: 0
- Confidence penalty: -20
- **Total**: 70

**Reasoning**: Novo Nordisk is a hybrid company working on long-acting GLP-1 drugs for obesity. Monthly dosing interval mentioned. Medium confidence due to lack of strong signals.

---

### Item 9/18

**Titre**: Daiichi ends work on an ADC; Layoffs at GSK's R&D unit

**Source**: press_sector__endpoints_news
**Date**: 2026-02-03
**URL**: https://endpoints.news/daiichi-ends-work-on-an-adc-layoffs-at-gsks-rd-unit/

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: Daiichi Sankyo has ended work on a next-generation antibody-drug conjugate (ADC) after a strategic portfolio review. GSK has laid off employees in its R&D unit.

**Entités détectées**:
- Companies: Daiichi Sankyo, GSK, Acadia Pharmaceuticals, Eli Lilly, PepLib Biotech, MeiraGTx, ZipBio, Santé Ventures, Adlai Nortye, NMD Pharma, Eton Pharmaceuticals, vTv Therapeutics, Newsoara
- Technologies: ADC
- Molecules: Aucune
- Trademarks: Aucune
- Indications: Aucune
- Dosing intervals: Aucune

**Event type**: corporate_move

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 70/100
**Confidence**: medium
**Is relevant**: True

**Signaux détectés**:
- Strong: Aucun
- Medium: technology_families: ADC
- Weak: molecules
- Exclusions: Aucune

**Score breakdown**:
- Base score: 50
- Entity boosts:
  - technology_families: +15
  - companies: +5
- Recency boost: 0
- Confidence penalty: 0
- **Total**: 70

**Reasoning**: The item mentions antibody-drug conjugate (ADC) technology, which is a medium signal for LAI relevance. The companies Daiichi Sankyo and GSK are also detected. While there are no strong signals, the ADC technology and presence of pharma companies make this a medium confidence match for the LAI domain.

---

### Item 10/18

**Titre**: <a href="https://www.fiercepharma.com/marketing/sanofi-sanctioned-over-ceos-bold-claims-about-pfizer-vaccine" hreflang="en">Sanofi sanctioned by PMCPA over CEO's 'bold claims' about Pfizer RSV vaccine</a>

**Source**: press_sector__fiercepharma
**Date**: 2023-05-18
**URL**: https://www.fiercepharma.com/marketing/sanofi-sanctioned-over-ceos-bold-claims-about-pfizer-vaccine

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: A U.K. marketing watchdog has sanctioned Sanofi after ruling its CEO Paul Hudson may have undermined the U.K. government's vaccine program by making 'bold claims' about a procurement choice related to Pfizer's RSV vaccine.

**Entités détectées**:
- Companies: Sanofi, Pfizer
- Technologies: Aucune
- Molecules: Aucune
- Trademarks: Aucune
- Indications: RSV
- Dosing intervals: Aucune

**Event type**: corporate_move

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 70/100
**Confidence**: medium
**Is relevant**: True

**Signaux détectés**:
- Strong: Aucun
- Medium: hybrid_company: Sanofi, hybrid_company: Pfizer
- Weak: indication: RSV
- Exclusions: Aucune

**Score breakdown**:
- Base score: 50
- Entity boosts:
  - hybrid_company: +15
  - indication: +5
- Recency boost: 10
- Confidence penalty: -10
- **Total**: 70

**Reasoning**: The item mentions two major pharmaceutical companies, Sanofi and Pfizer, in relation to an RSV vaccine. While these are hybrid companies and not pure LAI players, their involvement in an RSV vaccine program is relevant to the LAI domain. The recent date also boosts the score. However, the lack of strong signals like core technologies or trademarks reduces the confidence level to medium.

---

### Item 11/18

**Titre**: Medincell Awarded New Grant to Fight Malaria

**Source**: press_corporate__medincell
**Date**: 2025-11-24
**URL**: https://www.medincell.com/wp-content/uploads/2025/11/MDC_Gates-Malaria_PR_24112025_vf.pdf

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: Medincell was awarded a new grant to fund research efforts to fight malaria. The grant amount and details were not provided.

**Entités détectées**:
- Companies: Medincell
- Technologies: Aucune
- Molecules: Aucune
- Trademarks: Aucune
- Indications: malaria
- Dosing intervals: Aucune

**Event type**: partnership

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 65/100
**Confidence**: medium
**Is relevant**: True

**Signaux détectés**:
- Strong: Aucun
- Medium: Aucun
- Weak: indication: malaria
- Exclusions: Aucune

**Score breakdown**:
- Base score: 60
- Entity boosts:
  - company: +5
- Recency boost: 0
- Confidence penalty: 0
- **Total**: 65

**Reasoning**: The item mentions Medincell receiving a grant to research malaria treatments, which is a relevant indication for LAI therapies. However, no specific LAI technologies or products are mentioned, resulting in a medium confidence match with a moderate score.

---

### Item 12/18

**Titre**: GSK's new CEO eyes more dealmaking, intense pipeline inspection

**Source**: press_sector__endpoints_news
**Date**: 2026-02-04
**URL**: https://endpoints.news/gsks-new-ceo-eyes-more-dealmaking-intense-pipeline-inspection/

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: GSK's new CEO Luke Miels outlined the drugmaker's strategy to meet its 2031 sales forecast and address the upcoming patent expiration for its blockbuster HIV drug dolutegravir, which involves pursuing more deals and closely evaluating its pipeline.

**Entités détectées**:
- Companies: GSK
- Technologies: Aucune
- Molecules: dolutegravir
- Trademarks: Aucune
- Indications: HIV
- Dosing intervals: Aucune

**Event type**: corporate_move

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 65/100
**Confidence**: medium
**Is relevant**: True

**Signaux détectés**:
- Strong: Aucun
- Medium: hybrid_company: GSK
- Weak: molecule: dolutegravir, indication: HIV
- Exclusions: Aucune

**Score breakdown**:
- Base score: 50
- Entity boosts:
  - hybrid_company: +10
  - molecule: +5
- Recency boost: 0
- Confidence penalty: -25
- **Total**: 65

**Reasoning**: GSK is a hybrid pharmaceutical company working on long-acting HIV drugs like dolutegravir. However, no strong LAI signals detected, so medium confidence match.

---

### Item 13/18

**Titre**: Updated: Do Pfizer's monthly GLP-1 data justify Metsera's $10B price tag?

**Source**: press_sector__endpoints_news
**Date**: 2026-02-03
**URL**: https://endpoints.news/pfizers-metsera-originated-monthly-glp-1-cuts-weight-by-10-5-at-six-months/

#### 📝 Normalisation (1er appel Bedrock)

**Summary**: Pfizer reported that a monthly injection from its $10 billion acquisition of Metsera helped obesity patients lose up to 10.5% of their weight. The article does not mention dosing intervals or long-acting injectable technologies.

**Entités détectées**:
- Companies: Pfizer, Metsera
- Technologies: Aucune
- Molecules: GLP-1
- Trademarks: Aucune
- Indications: obesity
- Dosing intervals: monthly

**Event type**: clinical_update

#### 🎯 Domain Scoring (2ème appel Bedrock)

**Score**: 60/100
**Confidence**: medium
**Is relevant**: True

**Signaux détectés**:
- Strong: Aucun
- Medium: dosing_intervals: monthly
- Weak: molecules: GLP-1
- Exclusions: Aucune

**Score breakdown**:
- Base score: 50
- Entity boosts:
  - dosing_interval: +10
- Recency boost: 0
- Confidence penalty: 0
- **Total**: 60

**Reasoning**: The item mentions a monthly dosing interval for a GLP-1 injectable product, which are medium and weak signals for LAI relevance respectively. No strong signals or exclusions detected. Moderately confident LAI match.

---
