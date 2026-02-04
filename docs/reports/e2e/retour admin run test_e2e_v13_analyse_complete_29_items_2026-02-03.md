voile un retour du dernier run, j'ai identifié des items matchés qui selon moi ne devraient pas l'etre, je te donne la raison. il faut que tu analyse tout cela, analyse le fonctionnement du moteur et des prompts de scoring utilisés, pour proposer une amélioration. soit mieux utiliser les events patterns, soit améliorer le prompt domain scoring; mais il faut éliminer ce que je considere comme du bruit pour les prochains runs:


### Item 4/14: ✅ MATCHÉ 
**Medincell Appoints Dr Grace Kim, Chief Strategy Officer, U.S. Finance, to Advance into Next Stage of**

- **Source**: press_corporate__medincell
- **Date**: 2025-11-11
- **Type événement**: corporate_move
- **URL**: https://www.medincell.com/wp-content/uploads/2025/11/MDC_G_KIM_10112025_EN_vf.pdf

**Résumé**: Medincell has appointed Dr Grace Kim as Chief Strategy Officer for U.S. Finance to advance the company's growth in the U.S. capital markets.

**Entités extraites (Normalisation)**:
- Aucune entité LAI détectée

**Domain Score**: 85/100 (confidence: high)

**Signaux LAI détectés**:
- **STRONG**: pure_player_company: MedinCell, trademark: UZEDY®
- **MEDIUM**: technology: microspheres
- **WEAK**: route: subcutaneous
**Calcul du score**:
- Score de base: 40
- Boosts entités:
  - pure_player_company: +25
  - trademark: +20
- **TOTAL: 85**

**Explication Bedrock**: Pure player MedinCell mentioned with trademark UZEDY® and microsphere technology. Corporate move event with recent date. High confidence LAI match.

retour admin: ne devrait pas matcher, c'est une simple nommination RH dans une entreprise LAI, c'est insignifiant: aucun impact business, clinique, technologique, scientifique. je ne comprends pas le calcul du score ni les signaux LAI detectés: ou sont les signaux UZEDY, microshperes, subcutaneous? n'y a til pas eu un bug?



### Item 9/14: ✅ MATCHÉ

**Lilly unveils $3.5B factory that will make retatrutide and other obesity drugs**

- **Source**: press_sector__endpoints_news
- **Date**: 2026-01-30
- **Type événement**: corporate_move
- **URL**: https://endpoints.news/lilly-unveils-3-5b-factory-that-will-make-retatrutide-and-other-obesity-drugs/

**Résumé**: Eli Lilly is investing $3.5 billion to build a new factory in Lehigh Valley, PA that will manufacture its next-generation obesity drug retatrutide and other weight loss injectables and devices.

**Entités extraites (Normalisation)**:
- molecules: retatrutide
- indications: obesity

**Domain Score**: 80/100 (confidence: high)

**Signaux LAI détectés**:
- **MEDIUM**: hybrid_company: Eli Lilly, technology_family: microspheres
- **WEAK**: indication: obesity

**Calcul du score**:
- Score de base: 40
- Boosts entités:
  - hybrid_company: +10
  - technology_family: +10
  - key_molecule: +15
- Boost récence: +5
- **TOTAL: 80**

**Explication Bedrock**: Eli Lilly is a hybrid LAI company building a factory for microsphere-based obesity drug retatrutide. Recent corporate move event with multiple medium/weak signals. High confidence LAI match.

**💡 Pourquoi cet item est pertinent pour LAI**:
- **Signaux moyens détectés**:
  - Eli Lilly développe des produits LAI (parmi d'autres)
  - Technologie LAI mentionnée: microspheres
 
retour admin: ne devrait pas matcher, ce n'est pas dans la définition des LAI;  je ne comprends pas le calcul du score ni les signaux LAI detectés: ou sont les signaux microshperes? ce n'est pas un key molecule ni un LAI; c'es un simple médicament injectable. 



### Item 12/14: ✅ MATCHÉ

**<a href="https://www.fiercepharma.com/pharma/lilly-rounds-out-quartet-new-us-plants-35b-injectables-**

- **Source**: press_sector__fiercepharma
- **Date**: 2023-05-19
- **Type événement**: corporate_move
- **URL**: https://www.fiercepharma.com/pharma/lilly-rounds-out-quartet-new-us-plants-35b-injectables-and-device-facility-pa

**Résumé**: Eli Lilly announced plans to build a new $3.5 billion manufacturing facility for injectable drugs and devices in Pennsylvania's Lehigh Valley. This is the fourth new US plant Lilly has unveiled as part of its 'Lilly in America' investment initiative announced last year.

**Entités extraites (Normalisation)**:
- Aucune entité LAI détectée

**Domain Score**: 80/100 (confidence: high)

**Signaux LAI détectés**:
- **MEDIUM**: hybrid_company: Eli Lilly

**Calcul du score**:
- Score de base: 40
- Boosts entités:
  - hybrid_company: +10
- Boost récence: +10
- **TOTAL: 80**

**Explication Bedrock**: Eli Lilly is a hybrid company involved in LAI development. The item describes a new manufacturing facility for injectables and devices, which could be relevant for LAI production. Recent date further boosts the score.

**💡 Pourquoi cet item est pertinent pour LAI**:
- **Signaux moyens détectés**:
  - Eli Lilly développe des produits LAI (parmi d'autres)


retour admin: ne devrait pas matcher, ce n'est pas dans la définition des LAI;  c'est seulement une information sur le manufacturing d'injectable.



### Item 13/14: ✅ MATCHÉ

**<a href="https://www.fiercebiotech.com/biotech/novos-cagrisema-tops-semaglutide-ph-3-diabetes-study-**

- **Source**: press_sector__fiercebiotech
- **Date**: 2026-02-03
- **Type événement**: clinical_update
- **URL**: https://www.fiercebiotech.com/biotech/novos-cagrisema-tops-semaglutide-ph-3-diabetes-study-still-falls-short-25-weight-loss-goal

**Résumé**: Novo Nordisk's GLP-1/amylin combination drug CagriSema outperformed semaglutide in a phase 3 trial for type 2 diabetes, but did not achieve the 25% weight loss goal set by the company.

**Entités extraites (Normalisation)**:
- molecules: CagriSema, semaglutide
- indications: type 2 diabetes

**Domain Score**: 70/100 (confidence: medium)

**Signaux LAI détectés**:
- **MEDIUM**: hybrid_company: Novo Nordisk
- **WEAK**: molecule: semaglutide

**Calcul du score**:
- Score de base: 50
- Boosts entités:
  - hybrid_company: +10
  - key_molecule: +15
- Boost récence: +5
- Pénalité confiance: -10
- **TOTAL: 70**

**Explication Bedrock**: Novo Nordisk is a hybrid LAI company and semaglutide is a key molecule. Clinical update event type. Recent date but only medium confidence signals detected.

**💡 Pourquoi cet item est pertinent pour LAI**:
- **Signaux moyens détectés**:
  - Novo Nordisk développe des produits LAI (parmi d'autres)
- **Type d'événement pertinent**: clinical_update (événements clés pour le secteur LAI)

retour admin: cet item est interessant est devrait bien etre matché, mais pas pour les raisons evoquées par bedrock: si on analyse la news sur l'uRL on observe "A once-weekly shot of CagriSema, which combines semaglutide with the experimental amylin receptor agonist cagrilintide, reduced patients’ blood sugar by 1.91% on average from a baseline of 8.2% and dropped their weight by 14.2% after 68 weeks, Novo announced on Feb. 2. Injectable semaglutide, better known as Ozempic and Wegovy, came up short with reductions of 1.76% and 10.2%, respectively." on voit donc les mots clés "once-weekly" et "injectable" ce qui devrait tomber dans la définition des LAI. pourtant il semble que l'ingestion et la normalisation n'aient pas permis de capter ces mots clés précieux: il faut comprendre pourquoi lors de l'ingest ou de la normalisation on a pas recollter cela.




### Item 14/14: ✅ MATCHÉ

**Medincell Publishes its Consolidated Half-Year Financial Results (April 1st , 2025 – September 30, 2**

- **Source**: press_corporate__medincell
- **Date**: 2025-12-09
- **Type événement**: financial_results
- **URL**: https://www.medincell.com/wp-content/uploads/2025/12/MDC_HY-Results-EN_09122025-1.pdf

**Résumé**: Medincell published its consolidated financial results for the half-year period from April 1st, 2025 to September 30, 2025.

**Entités extraites (Normalisation)**:
- Aucune entité LAI détectée

**Domain Score**: 55/100 (confidence: medium)

**Signaux LAI détectés**:

**Calcul du score**:
- Score de base: 30
- Boost récence: +5
- Pénalité confiance: -10
- **TOTAL: 55**

**Explication Bedrock**: The item is about financial results from MedinCell, a pure-play LAI company. However, no specific LAI products or technologies are mentioned. Medium confidence match due to lack of strong/medium signals.

**💡 Pourquoi cet item est pertinent pour LAI**:

retour admin: ne devrait pas matcher: c'est purement un rapport financier, c'est du bruit. 



### Item 11/14: ✅ MATCHÉ

**AstraZeneca pays $1.2B for CSPC's long-acting obesity drugs**

- **Source**: press_sector__endpoints_news
- **Date**: 2023-05-18
- **Type événement**: partnership
- **URL**: https://endpoints.news/astrazeneca-pays-1-2b-for-cspcs-long-acting-obesity-drugs/

**Résumé**: AstraZeneca has entered into a $1.2 billion upfront partnership with CSPC Pharmaceutical spanning eight drug programs and multiple platform technologies for long-acting obesity drugs.

**Entités extraites (Normalisation)**:
- indications: obesity

**Domain Score**: 80/100 (confidence: high)

**Signaux LAI détectés**:
- **MEDIUM**: technology_families: microspheres
- **WEAK**: indication: obesity

**Calcul du score**:
- Score de base: 60
- Boosts entités:
  - technology_family: +10
- Boost récence: +10
- **TOTAL: 80**

**Explication Bedrock**: Microsphere technology mentioned for long-acting obesity drugs in a recent partnership. No exclusions detected. High confidence LAI match.

**💡 Pourquoi cet item est pertinent pour LAI**:
- **Signaux moyens détectés**:
  - Technologie LAI mentionnée: microspheres
- **Type d'événement pertinent**: partnership (événements clés pour le secteur LAI)

retour admin: je ne comprends pas d'où vient l'information "**Signaux LAI détectés**:
- **MEDIUM**: technology_families: microsphères" est ce que bedrock a halluciné? en tout cas c'est bien un match ar c'est du long acting. je me demande pourquoi cette news n'a pas été ingerée sur fiercebiotech sur l'url https://www.fiercebiotech.com/biotech/astrazeneca-returns-chinas-cspc-47b-obesity-deal; peut tu essayer de comprendre pourquoi on a pas ingéré cette news qui a beaucoup plus de texte accessible, avec des infos clés comme

"In return for the ex-China rights to all eight programs as well as use of CSPC’s artificial intelligence molecular design capabilities and LiquidGel once-monthly dosing platform technology, AstraZeneca is making the $1.2 billion upfront payment, with the potential for a further $3.5 billion to follow in development and milestone payments across all programs." Avec ces mots clés on voit que c'est le domaine de LAI:"once-monthly dosing platform technology"; essaye de comprendre ce qui s'est passé et de faire en sorte que on puisse ingeré cette news et la matcher.




### Item 3/15: ❌ NON MATCHÉ

**Quince's steroid therapy for rare disease fails, shares tank**

- **Source**: press_sector__endpoints_news
- **Date**: 2026-01-30
- **Type événement**: clinical_update
- **URL**: https://endpoints.news/quinces-steroid-therapy-for-rare-disease-fails-shares-tank/

**Résumé**: Quince Therapeutics' experimental once-monthly steroid-based treatment failed a Phase 3 trial for the rare genetic condition ataxia-telangiectasia, leading the company to stop development of the drug.

**Entités extraites (Normalisation)**:
- indications: ataxia-telangiectasia

**Domain Score**: 0 (non pertinent)

**Explication Bedrock**: No LAI signals detected in the item. The therapy failed for a rare disease indication unrelated to long-acting injectables. Not LAI-relevant.

**💡 Pourquoi cet item N'EST PAS pertinent pour LAI**:

---
retour admin: cela devrait matcher: le titre parle bien de once-monthly treatment.





ensuite d'une manière générale, sur les autres items non-matché je suis d'accord avec les choix du moteur: peux tu evaluer comment on peut éviter d'ingerer ces news inutiles si il y a des patterns évidents et facile a integrer au moteur d'ingestion?
