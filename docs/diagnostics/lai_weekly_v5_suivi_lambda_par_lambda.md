# Suivi Détaillé Lambda par Lambda - lai_weekly_v5 Run 2025-12-23

## 📊 VUE D'ENSEMBLE DU WORKFLOW

```
INGESTION (15 items) → NORMALISATION (15 items) → MATCHING (6 items) → SCORING (6 items) → NEWSLETTER (3 items)
```

---

## 🔄 LAMBDA 1 : INGESTION (vectora-inbox-ingest-v2-dev)

### Métriques d'Exécution
- **Durée** : 18.12 secondes
- **Sources traitées** : 7 sources
- **Sources échouées** : 1 source
- **Items bruts** : 16 items
- **Items dédupliqués** : 1 item
- **Items finaux** : 15 items

### Items Ingérés par Source

#### Source : press_corporate__nanexa (6 items)
1. **Item ID** : press_corporate__nanexa_20251223_6f822c
   - **Titre** : "Nanexa and Moderna enter into license and option agreement..."
   - **Date ingestion** : 2025-12-23T07:23:32.073225
   - **Date published_at** : 2025-12-23 ❌ **PROBLÈME**
   - **Word count** : 71 mots
   - **Hash** : sha256:a6f60bd2b0d446163f5bee10d1c134f77d3228b27e0b3e62cef64f33d4208a2d

2. **Item ID** : press_corporate__nanexa_20251223_6f822c (DOUBLON)
   - **Titre** : "Nanexa and Moderna enter into license and option agreement..." (version courte)
   - **Date ingestion** : 2025-12-23T07:23:32.073225
   - **Date published_at** : 2025-12-23 ❌ **PROBLÈME**
   - **Word count** : 61 mots
   - **Hash** : sha256:d9b83fe6cb94dcaa8e1245f54fd2e589b6cf48151c4b60378d8012a5e5a20125

3. **Item ID** : press_corporate__nanexa_20251223_ec88d7
   - **Titre** : "Nanexa publishes interim report for January-September 2025"
   - **Date published_at** : 2025-12-23 ❌ **PROBLÈME**
   - **Word count** : 39 mots

4. **Item ID** : press_corporate__nanexa_20251223_ec88d7 (DOUBLON)
   - **Titre** : "Nanexa publishes interim report for January-September 2025"
   - **Word count** : 10 mots (version tronquée)

5. **Item ID** : press_corporate__nanexa_20251223_e8d104
   - **Titre** : "Download attachment"
   - **Word count** : 2 mots ❌ **CONTENU INUTILE**

6. **Item ID** : press_corporate__nanexa_20251223_76ad60
   - **Titre** : "Nanexa publishes interim report for January-June 2025"
   - **Word count** : 10 mots

#### Source : press_corporate__delsitech (2 items)
7. **Item ID** : press_corporate__delsitech_20251223_e3d7ad
   - **Titre** : "Partnership Opportunities in Drug Delivery 2025 Boston, October 27-28"
   - **Word count** : 13 mots

8. **Item ID** : press_corporate__delsitech_20251223_ad0afc
   - **Titre** : "BIO International Convention 2025 Boston, June 16-19"
   - **Word count** : 11 mots

#### Source : press_corporate__medincell (7 items)
9. **Item ID** : press_corporate__medincell_20251223_2b08cd
   - **Titre** : "Medincell Publishes its Consolidated Half-Year Financial Results..."
   - **Word count** : 19 mots

10. **Item ID** : press_corporate__medincell_20251223_516562 ⭐ **SÉLECTIONNÉ**
    - **Titre** : "Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application..."
    - **Word count** : 33 mots
    - **Contenu** : Contient "December 9, 2025" (date réelle)

11. **Item ID** : press_corporate__medincell_20251223_150759 ❗ **MALARIA GRANT**
    - **Titre** : "Medincell Awarded New Grant to Fight Malaria"
    - **Word count** : 11 mots
    - **Contenu** : Contient "November 24, 2025" (date réelle)

12. **Item ID** : press_corporate__medincell_20251223_63c5d2
    - **Titre** : "Medincell Appoints Dr Grace Kim, Chief Strategy Officer..."
    - **Word count** : 23 mots

13. **Item ID** : press_corporate__medincell_20251223_846e38
    - **Titre** : "Medincell to Join MSCI World Small Cap Index..."
    - **Word count** : 16 mots

14. **Item ID** : press_corporate__medincell_20251223_c147c4 ⭐ **SÉLECTIONNÉ**
    - **Titre** : "UZEDY® continues strong growth; Teva setting the stage for US NDA..."
    - **Word count** : 22 mots
    - **Contenu** : Contient "November 5, 2025" (date réelle)

15. **Item ID** : press_corporate__medincell_20251223_1781cc
    - **Titre** : "FDA Approves Expanded Indication for UZEDY® (risperidone)..."
    - **Word count** : 24 mots
    - **Contenu** : Contient "October 10, 2025" (date réelle)

### Problèmes Identifiés - Ingestion
1. **❌ Extraction dates** : Toutes les dates = 2025-12-23 (date run)
2. **❌ Doublons** : Même item_id avec contenus différents
3. **❌ Contenu inutile** : "Download attachment" (2 mots)
4. **❌ Patterns dates** : Ne matchent pas les formats HTML réels

---

## 🧠 LAMBDA 2 : NORMALISATION/SCORING (vectora-inbox-normalize-score-v2-dev)

### Métriques d'Exécution
- **Durée** : ~3 minutes (timeout CLI mais succès)
- **Items traités** : 15 items
- **Items normalisés** : 15 items (100%)
- **Appels Bedrock** : ~30 appels (2 par item : normalisation + matching)
- **Modèle utilisé** : claude-3-5-sonnet

### Normalisation Item par Item

#### Items avec Matching Réussi (6/15)

**Item #1 : press_corporate__medincell_20251223_516562** ⭐
- **Normalisation** : 2025-12-23T07:26:52.596424Z
- **Summary** : "Teva Pharmaceuticals has submitted a New Drug Application to the U.S. FDA for Olanzapine Extended-Release Injectable Suspension..."
- **Entités détectées** :
  - Molecules : ["Olanzapine"]
  - Indications : ["Schizophrenia"]
- **Event type** : regulatory (confidence: 0.8)
- **LAI relevance** : 9/10 ✅
- **Matching** : tech_lai_ecosystem (score: 0.8, confidence: high)
- **Reasoning** : "Extended-release injectable formulation for schizophrenia"
- **Score final** : 10.2/20

**Item #2 : press_corporate__medincell_20251223_c147c4** ⭐
- **Normalisation** : 2025-12-23T07:27:10.513735Z
- **Summary** : "Teva is preparing to submit a New Drug Application (NDA) to the US FDA for its long-acting injectable (LAI) formulation..."
- **Entités détectées** :
  - Molecules : ["olanzapine"]
  - Trademarks : ["UZEDY®"]
- **Event type** : regulatory (confidence: 0.8)
- **LAI relevance** : 9/10 ✅
- **Matching** : tech_lai_ecosystem (score: 0.8, confidence: high)
- **Score final** : 10.2/20

**Item #3 : press_corporate__medincell_20251223_1781cc**
- **Normalisation** : 2025-12-23T07:27:15.420980Z
- **Summary** : "The FDA has approved an expanded indication for UZEDY® (risperidone) Extended-Release Injectable Suspension..."
- **Entités détectées** :
  - Molecules : ["risperidone"]
  - Trademarks : ["UZEDY®"]
  - Indications : ["Bipolar I Disorder"]
- **Event type** : regulatory (confidence: 0.8)
- **LAI relevance** : 9/10 ✅
- **Matching** : tech_lai_ecosystem (score: 0.8, confidence: high)
- **Score final** : 10.2/20
- **Statut newsletter** : ❌ Exclu (déduplication/trimming)

**Item #4 : press_corporate__nanexa_20251223_6f822c** ⭐
- **Normalisation** : 2025-12-23T07:26:12.528928Z
- **Summary** : "Nanexa and Moderna have entered into a license and option agreement for the development of up to five undisclosed compounds using Nanexa's PharmaShell® technology..."
- **Entités détectées** :
  - Trademarks : ["PharmaShell®"]
- **Event type** : partnership (confidence: 0.8)
- **LAI relevance** : 8/10 ✅
- **Matching** : tech_lai_ecosystem (score: 0.6, confidence: medium)
- **Reasoning** : "PharmaShell® technology related to controlled/sustained release formulations"
- **Score final** : 9.8/20

**Item #5 : press_corporate__nanexa_20251223_6f822c (doublon)**
- **Normalisation** : 2025-12-23T07:26:17.272825Z
- **Summary** : Identique à #4
- **Score final** : 9.8/20
- **Statut newsletter** : ❌ Exclu (déduplication)

**Item #6 : press_corporate__nanexa_20251223_ec88d7**
- **Normalisation** : 2025-12-23T07:26:21.959173Z
- **Summary** : "Nanexa published an interim report for January-September 2025, highlighting progress in optimizing GLP-1 formulations..."
- **Entités détectées** :
  - Molecules : ["GLP-1"]
  - Trademarks : ["PharmaShell"]
- **Event type** : financial_results (confidence: 0.8)
- **LAI relevance** : 3/10 ❌ **FAIBLE**
- **Matching** : tech_lai_ecosystem (score: 0.6, confidence: medium)
- **Score final** : 0/20 (pénalisé)
- **Statut newsletter** : ❌ Exclu (score insuffisant)

#### Items sans Matching (9/15)

**Item #7 : press_corporate__medincell_20251223_150759** ❗ **MALARIA GRANT**
- **Normalisation** : 2025-12-23T07:26:56.720482Z
- **Summary** : "Medincell, a pharmaceutical company, has been awarded a new grant to fund its efforts in fighting malaria..."
- **Entités détectées** :
  - Indications : ["malaria"]
- **Event type** : partnership (confidence: 0.8) ✅ **PARTNERSHIP DÉTECTÉ**
- **LAI relevance** : 0/10 ❌ **PROBLÈME CRITIQUE**
- **Matching** : ❌ **AUCUN MATCH** (domain_relevance vide)
- **Score final** : 0/20
- **Statut newsletter** : ❌ Exclu (pas de match)

**Analyse Malaria Grant** :
- ✅ Correctement classé comme "partnership"
- ❌ LAI relevance = 0 (Bedrock ne voit pas le lien LAI)
- ❌ Aucun match sur tech_lai_ecosystem
- **Problème** : Grant pour développement LAI malaria non reconnu comme LAI

**Autres items non matchés** :
- Rapports financiers (LAI relevance: 0-1)
- Nominations (LAI relevance: 0)
- Conférences génériques (LAI relevance: 0-2)
- "Download attachment" (LAI relevance: 0)

### Problèmes Identifiés - Normalisation
1. **❌ CRITIQUE : Malaria Grant non matché** - Perte contenu pertinent
2. **❌ Doublons traités** - Gaspillage appels Bedrock
3. **❌ Contenu inutile normalisé** - "Download attachment"

---

## 📰 LAMBDA 3 : NEWSLETTER (vectora-inbox-newsletter-v2-dev)

### Métriques d'Exécution
- **Durée** : ~2 minutes
- **Items traités** : 15 items
- **Items après matching** : 6 items
- **Items après déduplication** : 4 items
- **Items sélectionnés** : 3 items
- **Trimming appliqué** : ✅ Oui
- **Événements critiques préservés** : 3

### Processus de Sélection

#### Étape 1 : Filtrage par Matching
- **Input** : 15 items normalisés
- **Output** : 6 items matchés
- **Exclus** : 9 items (dont Malaria Grant)

#### Étape 2 : Déduplication
- **Input** : 6 items matchés
- **Output** : 4 items uniques
- **Exclus** : 2 doublons (Nanexa partnership)

#### Étape 3 : Scoring et Trimming
- **Input** : 4 items uniques
- **Output** : 3 items sélectionnés
- **Exclus** : 1 item (Nanexa rapport - score 0)

#### Étape 4 : Distribution par Sections
- **regulatory_updates** : 2 items (max: 6)
  - Teva NDA Olanzapine (score: 10.2)
  - UZEDY® NDA preparation (score: 10.2)
- **partnerships_deals** : 1 item (max: 4)
  - Nanexa-Moderna partnership (score: 9.8)
- **clinical_updates** : 0 items
- **others** : 0 items

### Génération Contenu Newsletter

#### TL;DR Generation
- **Appel Bedrock** : ✅ Succès
- **Contenu** : 3 bullet points résumant les signaux clés

#### Introduction Generation
- **Appel Bedrock** : ✅ Succès
- **Contenu** : Introduction contextuelle pour executives

#### Titres des Items
- **Problème identifié** : Titres tronqués à ~80 caractères
- **Exemple** : "Teva Pharmaceuticals has submitted a New Drug Application to the U.S. FDA for Olanzapine Extended-Re"
- **Titre complet** : "Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension..."

### Métriques Newsletter Finale
- **Total items** : 3 signaux
- **Sections remplies** : 2/4 sections
- **Sources uniques** : 2 sources
- **Trademarks clés** : PharmaShell®, UZEDY®
- **Fill rates** :
  - regulatory_updates : 33% (2/6 max)
  - partnerships_deals : 25% (1/4 max)
  - clinical_updates : 0%
  - others : 0%

### Problèmes Identifiés - Newsletter
1. **❌ Titres tronqués** - Impact lisibilité
2. **❌ Dates incorrectes** - Toutes à 2025-12-23
3. **❌ Sections vides** - clinical_updates, others

---

## 🎯 SYNTHÈSE GLOBALE

### Flux de Données
```
15 items ingérés
├── 15 items normalisés (100%)
├── 6 items matchés (40%)
├── 4 items après déduplication (67% des matchés)
└── 3 items newsletter (75% des dédupliqués, 50% des matchés)
```

### Problèmes Critiques Identifiés

1. **❌ EXTRACTION DATES** (Lambda 1)
   - Patterns regex inadéquats
   - Fallback systématique sur date ingestion

2. **❌ MALARIA GRANT NON MATCHÉ** (Lambda 2)
   - LAI relevance = 0 par Bedrock
   - Grant LAI malaria non reconnu

3. **❌ DOUBLONS** (Lambda 1)
   - Même item_id, contenus différents
   - Gaspillage ressources

4. **❌ TITRES TRONQUÉS** (Lambda 3)
   - Limitation génération newsletter

### Performance vs Objectifs
- **Workflow E2E** : ✅ Fonctionnel
- **Anti-hallucinations** : ✅ Validé (0 hallucination)
- **Distribution spécialisée** : ✅ Validé (2 sections)
- **Extraction dates** : ❌ Non fonctionnel
- **Volume newsletter** : ⚠️ Réduit (3 vs 5-6 attendus)

### Recommandations Prioritaires
1. **Corriger patterns extraction dates**
2. **Revoir critères matching grants/partnerships**
3. **Optimiser déduplication ingestion**
4. **Améliorer génération titres newsletter**