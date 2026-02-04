================================================================================
ANALYSE DETAILLEE - 31 ITEMS LAI_WEEKLY_V17
Workflow complet: Ingestion > Normalisation > Domain Scoring > Decision
================================================================================

================================================================================
ITEM #1/31 - press_sector__fiercepharma_20260203_895527
================================================================================

TITRE: <a href="https://www.fiercepharma.com/pharma/fda-gets-under-az-skin-rejection-its-subcutaneous-versi...
SOURCE: press_sector__fiercepharma
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: regulatory
Companies: ['AstraZeneca']
Molecules: ['Saphnelo']
Technologies: []
Dosing: ['every four weeks']
Trademarks: ['Saphnelo']

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 80/100
Confidence: high
Signaux Medium: ['dosing_interval: every four weeks', 'technology_family: subcutaneous version']
Reasoning: Subcutaneous dosing and 4-week dosing interval signals indicate a long-acting injectable formulation. Recent regulatory event for AstraZeneca's Saphnelo. High confidence LAI match....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #2/31 - press_sector__fiercepharma_20260203_2d58a7
================================================================================

TITRE: <a href="https://www.fiercepharma.com/marketing/sanofi-sanctioned-over-ceos-bold-claims-about-pfizer...
SOURCE: press_sector__fiercepharma
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: corporate_move
Companies: ['Sanofi', 'Pfizer']
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Reasoning: No LAI signals detected. The item is about Sanofi being sanctioned over claims made about Pfizer's RSV vaccine, which is not related to long-acting injectables....

--- DECISION FINALE ---
Statut: REJETE

================================================================================
ITEM #3/31 - press_sector__fiercepharma_20260203_e86749
================================================================================

TITRE: <a href="https://www.fiercepharma.com/sponsored/why-human-expertise-still-matters-ai-driven-med-comm...
SOURCE: press_sector__fiercepharma
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: other
Companies: ['RTI Health Solutions']
Molecules: []
Technologies: ['AI']
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Signaux Medium: ['technology: AI']
Reasoning: No strong LAI signals detected. The article discusses AI in medical communications, which is not directly relevant to the LAI domain....

--- DECISION FINALE ---
Statut: REJETE

================================================================================
ITEM #4/31 - press_sector__fiercepharma_20260203_2e9af0
================================================================================

TITRE: <a href="https://www.fiercepharma.com/pharma/lilly-rounds-out-quartet-new-us-plants-35b-injectables-...
SOURCE: press_sector__fiercepharma
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: corporate_move
Companies: ['Eli Lilly']
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 75/100
Confidence: high
Signaux Medium: ['hybrid_company: Eli Lilly', 'technology: injectables and devices']
Reasoning: Eli Lilly is a hybrid company building a new manufacturing facility for injectables and devices. Recent date and medium signals indicate high confidence LAI relevance....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #5/31 - press_sector__fiercepharma_20260203_f18948
================================================================================

TITRE: <a href="https://www.fiercepharma.com/marketing/hims-hers-uses-another-super-bowl-ad-tackle-healthca...
SOURCE: press_sector__fiercepharma
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: corporate_move
Companies: []
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Reasoning: No LAI signals detected. The item is about a healthcare company's Super Bowl ad on healthcare affordability, which is not directly relevant to the LAI domain....

--- DECISION FINALE ---
Statut: REJETE

================================================================================
ITEM #6/31 - press_corporate__nanexa_20260203_4ce385
================================================================================

TITRE: Nanexa Announces Breakthrough Preclinical Data Demonstrating Exceptional Pharmacokinetic Profile for...
SOURCE: press_corporate__nanexa
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: clinical_update
Companies: ['Nanexa']
Molecules: ['semaglutide']
Technologies: ['atomic layer deposition', 'PharmaShell®']
Dosing: ['monthly']
Trademarks: ['PharmaShell®']

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 80/100
Confidence: high
Signaux Medium: ['technology_family: atomic layer deposition', 'technology_family: PharmaShell®', 'dosing_interval: monthly semaglutide']
Reasoning: Nanexa's PharmaShell® atomic layer deposition technology for enabling monthly dosing of semaglutide. Multiple medium signals for LAI drug delivery technology and dosing interval. High confidence match...

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #7/31 - press_corporate__nanexa_20260203_4ce385
================================================================================

TITRE: Nanexa Announces Breakthrough Preclinical Data Demonstrating Exceptional Pharmacokinetic Profile for...
SOURCE: press_corporate__nanexa
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: clinical_update
Companies: ['Nanexa']
Molecules: ['semaglutide']
Technologies: ['atomic layer deposition', 'PharmaShell®']
Dosing: ['monthly']
Trademarks: ['PharmaShell®']

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 80/100
Confidence: high
Signaux Medium: ['technology_family: atomic layer deposition', 'technology_family: PharmaShell®', 'dosing_interval: monthly semaglutide']
Reasoning: Nanexa's PharmaShell® atomic layer deposition technology for enabling monthly dosing of semaglutide. Multiple medium signals for LAI drug delivery technology and dosing interval. High confidence match...

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #8/31 - press_corporate__nanexa_20260203_6f822c
================================================================================

TITRE: Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based...
SOURCE: press_corporate__nanexa
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: partnership
Companies: ['Nanexa', 'Moderna']
Molecules: []
Technologies: ['PharmaShell®']
Dosing: []
Trademarks: ['PharmaShell®']

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 85/100
Confidence: high
Signaux Medium: ['technology_family: PharmaShell®']
Reasoning: The partnership between Nanexa (a pure-play LAI company) and Moderna involves Nanexa's PharmaShell® technology, which is a medium signal for LAI. The recent date and partnership event type also contri...

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #9/31 - press_corporate__nanexa_20260203_ec88d7
================================================================================

TITRE: Nanexa publishes interim report for January-September 2025...
SOURCE: press_corporate__nanexa
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: financial_results
Companies: ['Nanexa']
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 25/100
Confidence: low
Signaux Strong: ['pure_player_company: Nanexa']
Reasoning: Nanexa is a pure-play LAI company, but the financial results event has no other LAI context, so low confidence match with a low score....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #10/31 - press_corporate__nanexa_20260203_e8d104
================================================================================

TITRE: Download attachment...
SOURCE: press_corporate__nanexa
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: other
Companies: []
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Reasoning: This news item does not contain any substantive information related to long-acting injectables. It appears to be a placeholder or an error message....

--- DECISION FINALE ---
Statut: REJETE

================================================================================
ITEM #11/31 - press_corporate__nanexa_20260203_76ad60
================================================================================

TITRE: Nanexa publishes interim report for January-June 2025...
SOURCE: press_corporate__nanexa
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: financial_results
Companies: ['Nanexa']
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 25/100
Confidence: low
Signaux Strong: ['pure_player_company: Nanexa']
Reasoning: Nanexa is a pure-play LAI company, but the financial results event has no other LAI context, so low confidence match with a low score....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #12/31 - press_corporate__camurus_20260203_1e8bef
================================================================================

TITRE: 09 January 2026RegulatoryCamurus announces FDA acceptance of NDA resubmission for Oclaiz™ for the tr...
SOURCE: press_corporate__camurus
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: regulatory
Companies: ['Camurus']
Molecules: []
Technologies: []
Dosing: []
Trademarks: ['Oclaiz™']

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 85/100
Confidence: high
Signaux Strong: ['pure_player_company: Camurus', 'trademark: Oclaiz™']
Reasoning: Pure player Camurus mentioned with trademark Oclaiz™ for a regulatory event. Recent date. High confidence LAI match....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #13/31 - press_sector__fiercebiotech_20260203_8f7e97
================================================================================

TITRE: <a href="https://www.fiercebiotech.com/biotech/novos-cagrisema-tops-semaglutide-ph-3-diabetes-study-...
SOURCE: press_sector__fiercebiotech
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: clinical_update
Companies: ['Novo Nordisk']
Molecules: ['CagriSema', 'semaglutide']
Technologies: []
Dosing: []
Trademarks: ['CagriSema', 'Ozempic']

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 80/100
Confidence: high
Signaux Medium: ['hybrid_company: Novo Nordisk', 'technology_family: microspheres', 'dosing_interval: once-weekly']
Reasoning: Novo Nordisk is a hybrid company developing LAI products. Mentions of microsphere technology and once-weekly dosing interval for CagriSema. Clinical trial update with recent date. High confidence LAI ...

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #14/31 - press_sector__fiercebiotech_20260203_8d1e08
================================================================================

TITRE: <a href="https://www.fiercebiotech.com/biotech/wave-regains-rights-genetic-disease-rna-editor-gsk" h...
SOURCE: press_sector__fiercebiotech
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: partnership
Companies: ['Wave Life Sciences', 'GSK']
Molecules: ['WVE-006']
Technologies: ['RNA editing', 'oligonucleotide']
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Reasoning: No LAI signals detected in the item. The technology mentioned is RNA editing, which is not related to long-acting injectable formulations....

--- DECISION FINALE ---
Statut: REJETE

================================================================================
ITEM #15/31 - press_corporate__medincell_20260203_aa5561
================================================================================

TITRE: UZEDY®: Net Sales Increased from $117M in 2024 to $191M in 2025 (+63%) ; OLANZAPINE LAI: EU Submissi...
SOURCE: press_corporate__medincell
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: financial_results
Companies: []
Molecules: ['OLANZAPINE']
Technologies: ['LAI']
Dosing: []
Trademarks: ['UZEDY®']

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 85/100
Confidence: high
Signaux Strong: ['trademark: UZEDY®']
Signaux Medium: ['dosing_interval: q2 2026']
Reasoning: The item mentions the LAI trademark UZEDY® and a dosing interval (Q2 2026 submission), indicating high relevance to the LAI domain. The recent date further boosts the score....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #16/31 - press_corporate__medincell_20260203_662f02
================================================================================

TITRE: Publication of the 2026 financial calendar...
SOURCE: press_corporate__medincell
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: financial_results
Companies: []
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Reasoning: The item is about publishing a financial calendar, which does not contain any LAI-relevant information based on the provided definition and signals. The rule 'reject (financial results need explicit L...

--- DECISION FINALE ---
Statut: REJETE

================================================================================
ITEM #17/31 - press_corporate__medincell_20260203_2b08cd
================================================================================

TITRE: Medincell Publishes its Consolidated Half-Year Financial Results (April 1st , 2025 – September 30, 2...
SOURCE: press_corporate__medincell
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: financial_results
Companies: ['Medincell']
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 60/100
Confidence: medium
Reasoning: Pure player MedinCell mentioned but no LAI-specific context like technology or dosing interval. Financial results event with recent date but low confidence due to lack of relevant signals....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #18/31 - press_corporate__medincell_20260203_516562
================================================================================

TITRE: Medincell’s Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA f...
SOURCE: press_corporate__medincell
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: regulatory
Companies: ['Medincell', 'Teva Pharmaceuticals']
Molecules: ['olanzapine']
Technologies: ['extended-release injectable suspension']
Dosing: ['once-monthly']
Trademarks: ["TEV-'749", 'mdc-TJK']

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 90/100
Confidence: high
Signaux Strong: ['pure_player_company: Medincell', "trademark: TEV-'749 / mdc-TJK"]
Signaux Medium: ['technology: extended-release injectable suspension', 'dosing_interval: once-monthly', 'hybrid_company: Teva Pharmaceuticals']
Reasoning: Pure player Medincell and partner Teva mentioned with extended-release injectable suspension technology, trademark, and once-monthly dosing interval for schizophrenia treatment. Recent regulatory even...

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #19/31 - press_corporate__medincell_20260203_150759
================================================================================

TITRE: Medincell Awarded New Grant to Fight Malaria...
SOURCE: press_corporate__medincell
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: partnership
Companies: ['Medincell']
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 70/100
Confidence: medium
Signaux Medium: ['technology: microspheres']
Reasoning: Mention of microsphere technology for malaria indication. Partnership event type. Medium confidence LAI match based on technology signal....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #20/31 - press_corporate__medincell_20260203_63c5d2
================================================================================

TITRE: Medincell Appoints Dr Grace Kim, Chief Strategy Officer, U.S. Finance, to Advance into Next Stage of...
SOURCE: press_corporate__medincell
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: corporate_move
Companies: ['Medincell']
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 70/100
Confidence: medium
Signaux Medium: ['technology: microspheres']
Reasoning: MedinCell is a pure player LAI company and microspheres are a LAI technology. Corporate move event with recent date. Medium confidence match due to lack of strong signals....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #21/31 - press_corporate__medincell_20260203_846e38
================================================================================

TITRE: Medincell to Join MSCI World Small Cap Index, a Leading Global Benchmark...
SOURCE: press_corporate__medincell
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: corporate_move
Companies: ['Medincell']
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 85/100
Confidence: high
Signaux Strong: ['pure_player_company: Medincell', 'trademark: UZEDY®']
Reasoning: Pure player Medincell mentioned with trademark UZEDY®. Corporate move event with recent date. High confidence LAI match....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #22/31 - press_corporate__medincell_20260203_c147c4
================================================================================

TITRE: UZEDY® continues strong growth; Teva setting the stage for US NDA Submission for Olanzapine LAI in Q...
SOURCE: press_corporate__medincell
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: regulatory
Companies: ['Teva']
Molecules: ['olanzapine']
Technologies: ['LAI']
Dosing: []
Trademarks: ['UZEDY®']

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 85/100
Confidence: high
Signaux Strong: ['trademark: UZEDY®']
Signaux Medium: ['hybrid_company: Teva', 'technology: LAI']
Reasoning: Teva (hybrid company) mentioned with UZEDY® trademark and LAI technology for olanzapine. Regulatory event with recent date. High confidence LAI match....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #23/31 - press_sector__endpoints_news_20260203_5675a6
================================================================================

TITRE: Daiichi ends work on an ADC; Layoffs at GSK's R&D unit...
SOURCE: press_sector__endpoints_news
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: corporate_move
Companies: ['Daiichi Sankyo', 'GSK', 'Acadia Pharmaceuticals', 'Eli Lilly', 'PepLib Biotech', 'MeiraGTx', 'ZipBio', 'Santé Ventures', 'Adlai Nortye', 'NMD Pharma', 'Eton Pharmaceuticals', 'vTv Therapeutics', 'Newsoara']
Molecules: []
Technologies: ['ADC']
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Reasoning: No LAI signals detected. The item is about a discontinued antibody-drug conjugate program and layoffs at a company's R&D unit, which are not relevant to the LAI domain....

--- DECISION FINALE ---
Statut: REJETE

================================================================================
ITEM #24/31 - press_sector__endpoints_news_20260203_98ac34
================================================================================

TITRE: Updated: Do Pfizer’s monthly GLP-1 data justify Metsera’s $10B price tag?...
SOURCE: press_sector__endpoints_news
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: clinical_update
Companies: ['Pfizer', 'Metsera']
Molecules: ['GLP-1']
Technologies: []
Dosing: ['monthly']
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 75/100
Confidence: high
Signaux Medium: ['technology_family: controlled release', 'dosing_interval: monthly injection']
Reasoning: The item mentions a monthly injectable GLP-1 drug for obesity from Pfizer's acquisition of Metsera, indicating a long-acting injectable formulation with controlled release technology. High confidence ...

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #25/31 - press_sector__endpoints_news_20260203_ce7939
================================================================================

TITRE: AstraZeneca gets CRL for prefilled pen version of lupus drug Saphnelo...
SOURCE: press_sector__endpoints_news
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: regulatory
Companies: ['AstraZeneca']
Molecules: ['Saphnelo']
Technologies: []
Dosing: []
Trademarks: ['Saphnelo']

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 85/100
Confidence: high
Signaux Medium: ['technology_families: microspheres']
Reasoning: The item mentions AstraZeneca (hybrid company), Saphnelo (trademark), and microspheres (LAI technology). It's a recent regulatory event. High confidence LAI match....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #26/31 - press_sector__endpoints_news_20260131_cee7af
================================================================================

TITRE: Big Pharma earnings kick off; Third-round IRA drugs selected; Hengrui’s trailblazing moment; and mor...
SOURCE: press_sector__endpoints_news
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: financial_results
Companies: ['Teva', 'Roche', 'Sanofi', 'Takeda', 'Regeneron']
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Reasoning: No LAI signals detected. The item discusses financial results from major pharmaceutical companies and drug pricing negotiations under the Inflation Reduction Act, but does not mention any LAI-specific...

--- DECISION FINALE ---
Statut: REJETE

================================================================================
ITEM #27/31 - press_sector__endpoints_news_20260130_e5a715
================================================================================

TITRE: FDA says it explained issues early on for Corcept's rejected Cushing's syndrome drug...
SOURCE: press_sector__endpoints_news
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: regulatory
Companies: ['Corcept Therapeutics', 'FDA']
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Reasoning: No LAI signals detected. The item is about a rejected drug application for a Cushing's syndrome treatment, with no mention of long-acting injectable technologies or formulations....

--- DECISION FINALE ---
Statut: REJETE

================================================================================
ITEM #28/31 - press_corporate__delsitech_20260203_e3d7ad
================================================================================

TITRE: Partnership Opportunities in Drug Delivery 2025 Boston, October 27-28...
SOURCE: press_corporate__delsitech
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: partnership
Companies: []
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 70/100
Confidence: medium
Signaux Medium: ['technology: drug delivery system']
Reasoning: The event is a partnership focused on drug delivery, which is a medium signal technology family for LAI. No strong signals detected, so medium confidence match....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #29/31 - press_corporate__delsitech_20260203_ad0afc
================================================================================

TITRE: BIO International Convention 2025 Boston, June 16-19...
SOURCE: press_corporate__delsitech
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: other
Companies: []
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Reasoning: No LAI signals detected and item is about a general biotech convention. Not relevant to the LAI domain....

--- DECISION FINALE ---
Statut: REJETE

================================================================================
ITEM #30/31 - press_corporate__delsitech_20260203_dddc9f
================================================================================

TITRE: Bio Europe Spring 2025 Milan, March 17-19...
SOURCE: press_corporate__delsitech
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: other
Companies: []
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: OUI
Score: 40/100
Confidence: medium
Reasoning: Event type 'other' with recent date but no strong or medium LAI signals detected. Low confidence match based on recency....

--- DECISION FINALE ---
Statut: SELECTIONNE pour newsletter

================================================================================
ITEM #31/31 - press_corporate__delsitech_20260203_e99236
================================================================================

TITRE: TIDES Asia 2025 Kyoto, February 26-28...
SOURCE: press_corporate__delsitech
DATE: N/A

--- ETAPE 1: INGESTION ---
Statut: OK Ingere
Filtres passés: min_word_count (50+), exclusion_keywords, deduplication

--- ETAPE 2: NORMALISATION (Bedrock Appel 1) ---
Event Type: other
Companies: []
Molecules: []
Technologies: []
Dosing: []
Trademarks: []

--- ETAPE 3: DOMAIN SCORING (Bedrock Appel 2) ---
Relevant: NON
Score: 0/100
Confidence: high
Reasoning: No LAI signals detected. Conference announcement not directly relevant to long-acting injectables domain....

--- DECISION FINALE ---
Statut: REJETE

================================================================================
FIN DE L ANALYSE - 31 items traites
================================================================================
