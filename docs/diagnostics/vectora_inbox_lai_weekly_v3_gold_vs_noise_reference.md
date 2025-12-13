# Vectora Inbox LAI Weekly v3 - Référence Gold vs Noise

**Basé sur** : Analyse human feedback v2 et feuille de revue humaine  
**Objectif** : Tableau de référence des items critiques à tracer dans le diagnostic

---

## Items "GOLD" - À Conserver Absolument

| ID | Source Key | Date | Titre | Catégorie | Justification |
|---|---|---|---|---|---|
| LAI_001 | press_corporate__nanexa | 2025-12-11 | Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products | LAI-strong | Partnership majeur LAI : Nanexa (pure player) + Moderna + PharmaShell® technology |
| LAI_002 | press_corporate__medincell | 2025-12-11 | FDA Approves Expanded Indication for UZEDY® (risperidone) Extended-Release Injectable Suspension | LAI-strong | Regulatory milestone LAI : UZEDY trademark + FDA approval + extended-release injectable |
| LAI_015 | press_corporate__medincell | 2025-12-11 | Medincell Awarded New Grant to Fight Malaria | LAI-strong | Pure player LAI avec contexte implicite : MedinCell utilise toujours technologie LAI |
| NL_001 | press_corporate__medincell | 2025-12-11 | Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension | LAI-strong | NDA submission LAI : olanzapine + extended-release injectable + regulatory |

---

## Items "NOISE" - À Exclure Systématiquement

| ID | Source Key | Date | Titre | Catégorie | Justification |
|---|---|---|---|---|---|
| NL_002 | press_corporate__delsitech | 2025-12-11 | DelSiTech is Hiring a Process Engineer | noise-HR | Recrutement pur : aucun signal LAI, juste pure player bonus |
| NL_003 | press_corporate__delsitech | 2025-12-11 | DelSiTech Seeks an Experienced Quality Director | noise-HR | Recrutement pur : aucun signal LAI, juste pure player bonus |
| NL_004 | press_corporate__delsitech | 2025-12-11 | DelSiTech announces a leadership change. Carl-Åke Carlsson, CEO of DelSiTech, leaves the company | noise-corporate | Changement leadership : aucun signal LAI, juste pure player bonus |
| NL_005 | press_corporate__medincell | 2025-12-11 | Medincell Publishes its Consolidated Half-Year Financial Results | noise-finance | Résultats financiers secs : aucun signal LAI, juste pure player bonus |
| PP_001 | press_corporate__nanexa | 2025-12-11 | Nanexa publishes interim report for January-September 2025 | noise-finance | Rapport financier : aucun contenu LAI |
| PP_002 | press_corporate__nanexa | 2025-12-11 | Nanexa publishes interim report for January-June 2025 | noise-finance | Rapport financier : aucun contenu LAI |

---

## Items "NON-LAI" - Sur-Ingestion à Réduire

| ID | Source Key | Date | Titre | Catégorie | Justification |
|---|---|---|---|---|---|
| LAI_004 | press_sector__endpoints_news | 2025-12-10 | USAntibiotics scores sped-up approval for amoxicillin | non-LAI | Extended-release détecté mais contexte antibiotique (non-LAI) |
| LAI_005 | press_sector__fiercebiotech | 2025-12-11 | Pfizer continues renewed obesity push with $150M upfront for Fosun unit's GLP-1 drug | non-LAI | Partnership GLP-1 : aucun signal LAI, route orale probable |
| LAI_007 | press_sector__fiercebiotech | 2025-12-11 | Zealand pens $2.5B oral cardiometabolic collab with fresh-faced Chinese biotech | non-LAI | Route orale explicite (anti-LAI) |
| LAI_008 | press_sector__fiercebiotech | 2025-12-11 | Roche links oral SERD to 30% breast cancer risk reduction in phase 3 adjuvant trial | non-LAI | Route orale explicite (anti-LAI) |
| LAI_010 | press_sector__endpoints_news | 2025-12-09 | Eli Lilly earmarks $6B for GLP-1 pill factory in Alabama | non-LAI | Manufacturing oral explicite (anti-LAI) |

---

## Signaux Critiques à Détecter

### Technology Terms Manqués
- **PharmaShell®** : Technology Nanexa non détectée
- **Extended-release injectable** : Terme LAI non reconnu systématiquement
- **LAI** : Acronyme direct non détecté

### Trademark Terms Manqués  
- **UZEDY®** : Trademark LAI présent dans scope mais non matché

### Exclusion Terms Non Appliqués
- **Hiring, recruiting** : Terms HR non filtrés
- **Financial results, interim report** : Terms finance non filtrés
- **Oral tablet, oral drug, pill** : Terms anti-LAI non filtrés

---

## Métriques Cibles Post-Diagnostic

### Items Gold (Objectif : 100% en newsletter)
- ✅ Nanexa/Moderna PharmaShell : Présent
- ✅ UZEDY regulatory : Présent  
- ✅ MedinCell malaria grant : Présent
- ✅ Olanzapine NDA : Présent

### Items Noise (Objectif : 0% en newsletter)
- ❌ DelSiTech HR (2x) : Exclus
- ❌ MedinCell finance : Exclu
- ❌ Corporate moves sans LAI : Exclus

### Items Non-LAI (Objectif : <30% ingestion)
- ❌ Partnerships non-LAI : Non ingérés
- ❌ Routes orales : Non ingérés  
- ❌ Manufacturing oral : Non ingérés

---

## Utilisation pour le Diagnostic

Ce tableau servira de référence pour :
1. **Phase 4** : Tracer ces items spécifiques dans le dernier run lai_weekly_v3
2. **Identifier** à quelle étape chaque item gold disparaît
3. **Identifier** pourquoi chaque item noise passe encore
4. **Mesurer** l'écart entre objectifs et réalité actuelle