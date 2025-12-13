# Vectora Inbox LAI Weekly v2 - Feuille de Revue Humaine

**Date** : 2025-12-11  
**Run analysé** : lai_weekly_v2 Run #2  
**Objectif** : Calibrage humain pour améliorer la qualité du moteur

---

## Instructions de Revue

**Colonnes à remplir** :
- `human_label` : LAI-strong, LAI-weak, non-LAI, noise-HR, noise-finance, noise-corporate
- `human_keep_in_newsletter` : yes / no
- `human_priority` : high / medium / low
- `human_comments` : Justification libre

---

## Table A : Items Inclus dans la Newsletter (5 items)

Ces items ont été sélectionnés par le moteur pour la newsletter finale.

| item_id | source_key | date | title | company_signals | technology_signals | molecule_signals | engine_matched_domains | engine_decision | engine_total_score | engine_reason | human_label | human_keep_in_newsletter | human_priority | human_comments |
|---------|------------|------|-------|-----------------|-------------------|------------------|------------------------|-----------------|-------------------|---------------|-------------|--------------------------|----------------|----------------|
| NL_001 | press_corporate__medincell | 2025-12-11 | Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension | MedinCell | extended-release injectable | olanzapine | [tech_lai_ecosystem] | included_in_newsletter | ~25 | pure_player + molecule + regulatory | LAI-strong | LAI-strong | yes | high |major event: submission of New drug application LAI (NDA)
| NL_002 | press_corporate__delsitech | 2025-12-11 | DelSiTech is Hiring a Process Engineer | DelSiTech | none | none | [tech_lai_ecosystem] | included_in_newsletter | ~15 | pure_player bonus only |noise-HR  | no | low |  |
| NL_003 | press_corporate__delsitech | 2025-12-11 | DelSiTech Seeks an Experienced Quality Director | DelSiTech | none | none | [tech_lai_ecosystem] | included_in_newsletter | ~15 | pure_player bonus only |noise-HR  |no  | low |  |
| NL_004 | press_corporate__delsitech | 2025-12-11 | DelSiTech announces a leadership change. Carl-Åke Carlsson, CEO of DelSiTech, leaves the company | DelSiTech | none | none | [tech_lai_ecosystem] | included_in_newsletter | ~12 | pure_player + corporate | noise-corporate | no | low |  |
| NL_005 | press_corporate__medincell | 2025-12-11 | Medincell Publishes its Consolidated Half-Year Financial Results | MedinCell | none | none | [tech_lai_ecosystem] | included_in_newsletter | ~10 | pure_player + financial | noise-finance | no | low |  |

---

## Table B : Items LAI Candidats Non Retenus (15 items)

Ces items ont des signaux LAI potentiels mais n'ont pas été retenus dans la newsletter.

| item_id | source_key | date | title | company_signals | technology_signals | molecule_signals | engine_matched_domains | engine_decision | engine_total_score | engine_reason | human_label | human_keep_in_newsletter | human_priority | human_comments |
|---------|------------|------|-------|-----------------|-------------------|------------------|------------------------|-----------------|-------------------|---------------|-------------|--------------------------|----------------|----------------|
| LAI_001 | press_corporate__nanexa | 2025-12-11 | Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products | Nanexa | none_detected | none | [] | excluded | ~5 | PharmaShell not detected as LAI tech |LAI-strong  | yes | high | A partnership involving a core_players should always be kept |
| LAI_002 | press_corporate__medincell | 2025-12-11 | FDA Approves Expanded Indication for UZEDY® (risperidone) Extended-Release Injectable Suspension | none_detected | extended-release injectable | risperidone | [] | excluded | ~8 | regulatory + molecule but no company match | LAI-strong | yes |high  | Uzedy is a trademark in the scope; this news has to be kept: its a trademark in the scope regulatory news |
| LAI_003 | press_corporate__medincell | 2025-12-11 | UZEDY® continues strong growth; Teva setting the stage for US NDA Submission for Olanzapine LAI | none_detected | none_detected | olanzapine | [] | excluded | ~6 | molecule detected but weak signals |LAI-weak  | yes   |medium  | its a strategic informative news from a core_player; to be included depending on scoring compared to others items, but if we have few items in a newsletter we can include this |
| LAI_004 | press_sector__endpoints_news | 2025-12-10 | USAntibiotics scores sped-up approval for amoxicillin | none | extended-release | none | [] | excluded | ~4 | extended-release detected but not LAI context |non-LAI  | no | low | why ingested? we need to understand why its ingested and avoid ingestion if possible |
| LAI_005 | press_sector__fiercebiotech | 2025-12-11 | Pfizer continues renewed obesity push with $150M upfront for Fosun unit's GLP-1 drug | Pfizer | none | none | [] | excluded | ~7 | hybrid company + partnership but no LAI tech | non-LAI |no  |  low| why ingested? we need to understand why its ingested and avoid ingestion if possible |
| LAI_006 | press_sector__fiercebiotech | 2025-12-11 | Novartis pens $1.7B immuno-dermatology pact with AI-enabled British biotech | Novartis | none | none | [] | excluded | ~6 | hybrid company + partnership but no LAI | non-LAI |no  | low | why ingested? we need to understand why its ingested and avoid ingestion if possible |
| LAI_007 | press_sector__fiercebiotech | 2025-12-11 | Zealand pens $2.5B oral cardiometabolic collab with fresh-faced Chinese biotech | none | none | none | [] | excluded | ~5 | partnership but oral route (anti-LAI) | non-LAI | no | low | why ingested? we need to understand why its ingested and avoid ingestion if possible |
| LAI_008 | press_sector__fiercebiotech | 2025-12-11 | Roche links oral SERD to 30% breast cancer risk reduction in phase 3 adjuvant trial | none | none | none | [] | excluded | ~4 | clinical but oral route (anti-LAI) |  |  |  |  |
| LAI_009 | press_sector__fiercebiotech | 2025-12-11 | ASH: Novartis details ianalumab's phase 3 win in rare blood disease | Novartis | none | none | [] | excluded | ~5 | hybrid company + clinical but no LAI | non-lai |  no| low | why ingested? we need to understand why its ingested and avoid ingestion if possible |
| LAI_010 | press_sector__endpoints_news | 2025-12-09 | Eli Lilly earmarks $6B for GLP-1 pill factory in Alabama | Eli Lilly | none | none | [] | excluded | ~6 | hybrid company + manufacturing but oral | non_lai |  |  | why ingested? we need to understand why its ingested and avoid ingestion if possible |
| LAI_011 | press_sector__endpoints_news | 2025-12-09 | Novartis to partner with AI-focused Relation on atopic diseases | Novartis | none | none | [] | excluded | ~5 | hybrid company + partnership but no LAI | non-lai |no  | low | why ingested? we need to understand why its ingested and avoid ingestion if possible |
| LAI_012 | press_sector__fiercebiotech | 2025-12-11 | Formation Bio unveils new subsidiary with $605M Lynk deal | none | none | none | [] | excluded | ~4 | partnership but no LAI signals | non-lai | no | low | why ingested? we need to understand why its ingested and avoid ingestion if possible |
| LAI_013 | press_sector__fiercebiotech | 2025-12-11 | Chinese biotech led by AstraZeneca veteran reels in $108M for KRAS phase 3 plans | AstraZeneca | none | none | [] | excluded | ~5 | hybrid company mention + funding but no LAI |non-lai  | no | low | why ingested? we need to understand why its ingested and avoid ingestion if possible |
| LAI_014 | press_sector__endpoints_news | 2025-12-09 | SanegeneBio raises $110M in follow-up to metabolic deal with Lilly | Eli Lilly | none | none | [] | excluded | ~5 | hybrid company + partnership but no LAI | non-lai |no  | low |why ingested? we need to understand why its ingested and avoid ingestion if possible  |
| LAI_015 | press_corporate__medincell | 2025-12-11 | Medincell Awarded New Grant to Fight Malaria | MedinCell | none | none | [] | excluded | ~8 | pure_player + grant but no LAI tech mentioned | strong-lai |yes  | high |medincell is a core_player; so this news has to be kept. Medincell use lai technology, even if its not clearly written  |

---

## Table C : Corporate Pure Players Non Retenus (10 items)

Items provenant de pure players LAI mais exclus de la newsletter.

| item_id | source_key | date | title | company_signals | technology_signals | molecule_signals | engine_matched_domains | engine_decision | engine_total_score | engine_reason | human_label | human_keep_in_newsletter | human_priority | human_comments |
|---------|------------|------|-------|-----------------|-------------------|------------------|------------------------|-----------------|-------------------|---------------|-------------|--------------------------|----------------|----------------|
| PP_001 | press_corporate__nanexa | 2025-12-11 | Nanexa publishes interim report for January-September 2025 | Nanexa | none | none | [] | excluded | ~3 | pure_player but financial report |noise-finance  | no | low |  |
| PP_002 | press_corporate__nanexa | 2025-12-11 | Nanexa publishes interim report for January-June 2025 | Nanexa | none | none | [] | excluded | ~3 | pure_player but financial report |noise-finance  |no  |low  |  |
| PP_003 | press_corporate__delsitech | 2025-12-11 | Appointment of Outi Heikkilä as Chief Operations Officer | none_detected | none | none | [] | excluded | ~2 | corporate appointment but weak company detection |noise-HR  | no | low |  |
| PP_004 | press_corporate__delsitech | 2025-12-11 | Partnership Opportunities in Drug Delivery 2025 Boston | none_detected | drug delivery | none | [] | excluded | ~4 | conference + drug delivery but weak signals |noise-corporate  |no  |low  | just a simple conference, no need to include this |
| PP_005 | press_corporate__delsitech | 2025-12-11 | Drug Delivery and Formulation Summit 2025 Boston | none_detected | drug delivery | none | [] | excluded | ~4 | conference + drug delivery but weak signals | noise-corporate | no | low |just a simple conference, no need to include this  |
| PP_006 | press_corporate__delsitech | 2025-12-11 | CRS Annual Meeting & Exposition 2025 Philadelphia | none_detected | controlled release | none | [] | excluded | ~4 | conference + controlled release but weak |noise-corporate  | no | low |  |
| PP_007 | press_corporate__medincell | 2025-12-11 | Medincell Management to Present at Healthcare Conferences | MedinCell | none | none | [] | excluded | ~6 | pure_player + conferences but no LAI content | noise-corporate |no  |low  |  |
| PP_008 | press_corporate__medincell | 2025-12-11 | Medincell Appoints Dr Grace Kim, Chief Strategy Officer | MedinCell | none | none | [] | excluded | ~5 | pure_player + appointment but no LAI | noise-corporate | no | low |  |
| PP_009 | press_corporate__medincell | 2025-12-11 | Medincell to Join MSCI World Small Cap Index | MedinCell | none | none | [] | excluded | ~4 | pure_player + financial milestone but no LAI | noise-corporate | no | low |  |
| PP_010 | press_corporate__medincell | 2025-12-11 | Medincell to Participate in Healthcare Conferences | MedinCell | none | none | [] | excluded | ~5 | pure_player + conferences but no LAI content | noise-corporate |no  |low  | just a simple conference, no need to include this  |

---

## Métriques du Run Analysé

### Items Traités
- **Total items normalisés** : 104
- **Items corporate pure players** : 30 (MedinCell: 12, DelSiTech: 10, Nanexa: 8)
- **Items presse sectorielle** : 74 (FiercePharma: 25, FierceBiotech: 25, Endpoints: 24)

### Détection d'Entités
- **Companies détectées** : 15 (7 pure players, 8 hybrid)
- **Molecules détectées** : 3 (olanzapine: 2x, risperidone: 1x)
- **Technologies détectées** : 0 (problème critique identifié)
- **Trademarks détectées** : 0 (PharmaShell® non reconnu)

### Résultats Engine
- **Items inclus newsletter** : 5
- **Items exclus** : 99
- **Ratio signal/noise newsletter** : 20% LAI authentique / 80% bruit

---

## Points d'Attention pour la Revue

### Signaux LAI Manqués
1. **Nanexa/Moderna PharmaShell** : Partnership majeur LAI non détecté
2. **UZEDY regulatory** : Approbation LAI non matchée
3. **Extended-release terms** : Détection technology défaillante

### Bruit Dominant
1. **DelSiTech HR** : 2 annonces recrutement en newsletter
2. **MedinCell finance** : Résultats financiers sans contenu LAI
3. **Corporate générique** : Changements leadership sans impact LAI

### Patterns à Identifier
- Pure players sans signaux LAI dominent-ils injustement ?
- Partnerships LAI authentiques sont-ils sous-détectés ?
- Regulatory milestones LAI passent-ils à travers ?

---

## Utilisation de cette Feuille

1. **Remplir les colonnes humaines** pour chaque item
2. **Identifier les patterns** de désaccord humain-moteur
3. **Proposer des ajustements** canonical/matching/scoring
4. **Valider les corrections** sur run suivant

**Temps estimé** : 30-45 minutes pour annotation complète