# Plan de Test E2E - lai_weekly_v5 avec Approche B

**Date**: 2025-12-23
**Client**: lai_weekly_v5
**Objectif**: Test complet du pipeline Vectora Inbox avec Approche B (prompts pre-construits)
**Duree estimee**: 30-45 minutes

---

## OBJECTIFS DU TEST

### Objectifs quantitatifs
- Mesurer le volume de donnees a chaque etape du pipeline
- Evaluer les performances (temps, cout, scalabilite)
- Identifier les goulots d'etranglement

### Objectifs qualitatifs
- Evaluer la qualite de l'extraction d'entites
- Mesurer la precision du matching
- Analyser la gestion du bruit
- Valider la pertinence des items selectionnes

---

## PHASE 0: PREPARATION ET BASELINE

### 0.1 Verification environnement

**Checklist pre-test**:
- [ ] Lambda normalize-score-v2 avec layer Approche B deploye
- [ ] Fichiers canonical prompts LAI sur S3
- [ ] Client config lai_weekly_v5 avec bedrock_config sur S3
- [ ] Acces CloudWatch Logs configure
- [ ] Scripts d'invocation prets

**Commandes verification**:
```bash
# Verifier layer Lambda
aws lambda get-function-configuration --function-name vectora-inbox-normalize-score-v2-dev --profile rag-lai-prod --region eu-west-3 --query "Layers[*].Arn"

# Verifier prompts S3
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/ --recursive --profile rag-lai-prod --region eu-west-3

# Verifier client config
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly_v5.yaml - --profile rag-lai-prod --region eu-west-3
```

### 0.2 Baseline de reference

**Metriques de reference (lai_weekly_v4)**:
- Items ingesres: ~15-20 items
- Taux de normalisation: 100%
- Taux de matching: 60-70%
- Temps execution normalize-score: 150-180s
- Cout Bedrock: $0.15-0.25
- Items newsletter: 10-15 items

---

## PHASE 1: INGESTION (Lambda ingest-v2)

### 1.1 Execution ingestion

**Commande**:
```bash
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v5
```

**Timestamp debut**: _________________

### 1.2 Metriques quantitatives a collecter

**Volume de donnees**:
- [ ] Nombre total de sources scrapees: _______
- [ ] Nombre total d'items recuperes: _______
- [ ] Nombre d'items apres deduplication: _______
- [ ] Taille totale des donnees (KB): _______

**Performance**:
- [ ] Temps execution total (s): _______
- [ ] Temps moyen par source (s): _______
- [ ] Nombre d'erreurs HTTP: _______
- [ ] Taux de succes scraping (%): _______

**Repartition par source**:
```
Source                    | Items | Temps (s) | Statut
--------------------------|-------|-----------|--------
medincell_press          |       |           |
camurus_press            |       |           |
delsitech_press          |       |           |
nanexa_press             |       |           |
peptron_press            |       |           |
fierce_biotech_lai       |       |           |
endpoints_news_lai       |       |           |
```

### 1.3 Analyse qualitative

**Qualite des donnees ingerees**:
- [ ] Titres complets et coherents: OUI / NON
- [ ] Contenu extrait correctement: OUI / NON
- [ ] Dates de publication presentes: OUI / NON
- [ ] URLs valides: OUI / NON

**Gestion du bruit**:
- [ ] Items hors-sujet detectes: _______
- [ ] Doublons detectes: _______
- [ ] Items trop courts (<100 chars): _______

**Echantillon items ingesres** (3 exemples):
```
1. Titre: _________________________________
   Source: _________________________________
   Date: _________________________________
   Taille contenu: _______ chars

2. Titre: _________________________________
   Source: _________________________________
   Date: _________________________________
   Taille contenu: _______ chars

3. Titre: _________________________________
   Source: _________________________________
   Date: _________________________________
   Taille contenu: _______ chars
```

### 1.4 Verification S3

**Commande**:
```bash
# Lister dernier run ingested
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v5/ --recursive --profile rag-lai-prod --region eu-west-3 | tail -5

# Telecharger items.json
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v5/YYYY/MM/DD/items.json items_ingested.json --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Fichier items.json present sur S3
- [ ] Structure JSON valide
- [ ] Nombre items coherent avec logs

---

## PHASE 2: NORMALISATION (Lambda normalize-score-v2 - Approche B)

### 2.1 Execution normalisation

**Commande**:
```bash
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v5
```

**Timestamp debut**: _________________

### 2.2 Metriques quantitatives - Normalisation Bedrock

**Volume de donnees**:
- [ ] Items a normaliser (input): _______
- [ ] Items normalises avec succes: _______
- [ ] Items en erreur: _______
- [ ] Taux de succes normalisation (%): _______

**Appels Bedrock**:
- [ ] Nombre total d'appels Bedrock normalisation: _______
- [ ] Nombre d'appels reussis: _______
- [ ] Nombre de throttling: _______
- [ ] Nombre d'erreurs autres: _______

**Performance**:
- [ ] Temps execution normalisation (s): _______
- [ ] Temps moyen par item (s): _______
- [ ] Temps total appels Bedrock (s): _______
- [ ] Overhead prompt_resolver (s): _______

**Cout**:
- [ ] Tokens input total: _______
- [ ] Tokens output total: _______
- [ ] Cout Bedrock normalisation ($): _______

### 2.3 Metriques quantitatives - Extraction entites

**Entites extraites (totaux)**:
- [ ] Nombre total de companies: _______
- [ ] Nombre total de molecules: _______
- [ ] Nombre total de technologies: _______
- [ ] Nombre total de trademarks: _______
- [ ] Nombre total d'indications: _______

**Repartition par item** (moyenne):
- [ ] Companies par item (moy): _______
- [ ] Molecules par item (moy): _______
- [ ] Technologies par item (moy): _______

**Event types detectes**:
```
Event Type           | Count | %
---------------------|-------|-----
partnership          |       |
clinical_update      |       |
regulatory           |       |
corporate_move       |       |
financial_results    |       |
other                |       |
```

### 2.4 Analyse qualitative - Extraction entites

**Precision extraction** (echantillon 5 items):
```
Item 1:
- Companies detectees: _________________________________
- Precision (TP/Total): _____ / _____
- Hallucinations (FP): _____
- Manques (FN): _____

Item 2:
- Companies detectees: _________________________________
- Precision (TP/Total): _____ / _____
- Hallucinations (FP): _____
- Manques (FN): _____

[Repeter pour items 3-5]
```

**Qualite des summaries**:
- [ ] Summaries coherents: OUI / NON
- [ ] Longueur appropriee (2-3 phrases): OUI / NON
- [ ] Informations cles presentes: OUI / NON

**Approche B - Validation**:
- [ ] Logs confirment "Approche B activee": OUI / NON
- [ ] References {{ref:}} resolues: OUI / NON
- [ ] Fallback V1 utilise: OUI / NON
- [ ] Taille prompt final (chars): _______

### 2.5 Metriques quantitatives - Matching Bedrock

**Volume matching**:
- [ ] Items a matcher: _______
- [ ] Items matches (>=1 domaine): _______
- [ ] Items non-matches: _______
- [ ] Taux de matching (%): _______

**Appels Bedrock matching**:
- [ ] Nombre total d'appels: _______
- [ ] Nombre reussis: _______
- [ ] Nombre erreurs: _______

**Repartition par domaine**:
```
Domain ID            | Items matches | Confidence high | Confidence medium | Confidence low
---------------------|---------------|-----------------|-------------------|---------------
tech_lai_ecosystem   |               |                 |                   |
```

**Performance matching**:
- [ ] Temps execution matching (s): _______
- [ ] Temps moyen par item (s): _______
- [ ] Cout Bedrock matching ($): _______

### 2.6 Analyse qualitative - Matching

**Precision matching** (echantillon 5 items matches):
```
Item 1:
- Titre: _________________________________
- Domaine matche: _________________________________
- Relevance score: _______
- Confidence: _______
- Reasoning: _________________________________
- Match correct: OUI / NON

[Repeter pour items 2-5]
```

**Faux positifs** (items matches a tort):
- [ ] Nombre de faux positifs detectes: _______
- [ ] Exemples: _________________________________

**Faux negatifs** (items LAI non-matches):
- [ ] Nombre de faux negatifs detectes: _______
- [ ] Exemples: _________________________________

### 2.7 Metriques quantitatives - Scoring

**Distribution des scores**:
```
Score Range    | Count | %
---------------|-------|-----
0-5            |       |
5-10           |       |
10-15          |       |
15-20          |       |
20+            |       |
```

**Statistiques scores**:
- [ ] Score minimum: _______
- [ ] Score maximum: _______
- [ ] Score moyen: _______
- [ ] Score median: _______

**Bonuses appliques**:
```
Bonus Type              | Items concernes | Bonus moyen
------------------------|-----------------|------------
pure_player_companies   |                 |
trademark_mentions      |                 |
key_molecules           |                 |
hybrid_companies        |                 |
```

### 2.8 Verification S3 curated

**Commande**:
```bash
# Lister dernier run curated
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v5/ --recursive --profile rag-lai-prod --region eu-west-3 | tail -5

# Telecharger items.json
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v5/YYYY/MM/DD/items.json items_curated.json --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Fichier items.json present sur S3
- [ ] Structure JSON valide avec normalized_content
- [ ] Champs matching_results presents
- [ ] Champs scoring_results presents

---

## PHASE 3: NEWSLETTER (Lambda newsletter-v2)

### 3.1 Execution newsletter

**Commande**:
```bash
python scripts/invoke/invoke_newsletter_v2.py --client-id lai_weekly_v5
```

**Timestamp debut**: _________________

### 3.2 Metriques quantitatives - Selection

**Volume selection**:
- [ ] Items curated disponibles: _______
- [ ] Items selectionnes pour newsletter: _______
- [ ] Taux de selection (%): _______

**Repartition par section**:
```
Section ID           | Max items | Items selectionnes | Items trimmes
---------------------|-----------|--------------------|--------------
regulatory_updates   | 6         |                    |
partnerships_deals   | 4         |                    |
clinical_updates     | 5         |                    |
others               | 8         |                    |
```

**Deduplication**:
- [ ] Items dedupliques: _______
- [ ] Methode: similarity / exact

### 3.3 Metriques quantitatives - Generation editoriale

**Appels Bedrock editorial**:
- [ ] Appel TL;DR generation: OUI / NON
- [ ] Appel introduction generation: OUI / NON
- [ ] Tokens input TL;DR: _______
- [ ] Tokens output TL;DR: _______
- [ ] Cout Bedrock editorial ($): _______

**Performance**:
- [ ] Temps execution newsletter (s): _______
- [ ] Temps generation editoriale (s): _______

### 3.4 Analyse qualitative - Newsletter

**Qualite TL;DR**:
- [ ] TL;DR present: OUI / NON
- [ ] Longueur appropriee (2-3 bullets): OUI / NON
- [ ] Informations cles presentes: OUI / NON
- [ ] Ton executif: OUI / NON

**Qualite introduction**:
- [ ] Introduction presente: OUI / NON
- [ ] Contexte clair: OUI / NON
- [ ] Longueur appropriee (1-2 phrases): OUI / NON

**Qualite sections**:
```
Section              | Items | Pertinence | Ordre | Qualite globale
---------------------|-------|------------|-------|----------------
regulatory_updates   |       | 1-5        | OK/KO | 1-5
partnerships_deals   |       | 1-5        | OK/KO | 1-5
clinical_updates     |       | 1-5        | OK/KO | 1-5
others               |       | 1-5        | OK/KO | 1-5
```

**Gestion du bruit**:
- [ ] Items hors-sujet dans newsletter: _______
- [ ] Items redondants: _______
- [ ] Items peu pertinents (score <10): _______

### 3.5 Verification S3 newsletter

**Commande**:
```bash
# Lister newsletters
aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly_v5/ --recursive --profile rag-lai-prod --region eu-west-3 | tail -5

# Telecharger newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v5/YYYY/MM/DD/newsletter.md newsletter.md --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Fichier newsletter.md present sur S3
- [ ] Format Markdown valide
- [ ] Toutes sections presentes
- [ ] Metriques incluses

---

## PHASE 4: ANALYSE GLOBALE E2E

### 4.1 Metriques globales pipeline

**Funnel de conversion**:
```
Etape                    | Volume | Taux conversion | Taux perte
-------------------------|--------|-----------------|------------
Sources scrapees         |        | -               | -
Items ingesres           |        | 100%            | 0%
Items normalises         |        | ___%            | ___%
Items matches            |        | ___%            | ___%
Items scores >10         |        | ___%            | ___%
Items newsletter         |        | ___%            | ___%
```

**Performance globale**:
- [ ] Temps total E2E (s): _______
- [ ] Temps ingestion (s): _______
- [ ] Temps normalisation (s): _______
- [ ] Temps newsletter (s): _______

**Cout global**:
- [ ] Cout Bedrock normalisation ($): _______
- [ ] Cout Bedrock matching ($): _______
- [ ] Cout Bedrock editorial ($): _______
- [ ] Cout total Bedrock ($): _______
- [ ] Cout Lambda (estime) ($): _______
- [ ] Cout total E2E ($): _______

### 4.2 Analyse qualitative globale

**Qualite du signal**:
- [ ] Precision globale (items pertinents/total): ____ / ____
- [ ] Taux de bruit (items hors-sujet): ___%
- [ ] Taux de faux positifs matching: ___%
- [ ] Taux de faux negatifs matching: ___%

**Qualite des entites**:
- [ ] Precision extraction companies: ___%
- [ ] Precision extraction molecules: ___%
- [ ] Precision extraction technologies: ___%
- [ ] Taux d'hallucinations: ___%

**Qualite newsletter finale**:
- [ ] Pertinence globale (1-5): _____
- [ ] Diversite des sujets (1-5): _____
- [ ] Qualite editoriale (1-5): _____
- [ ] Utilite pour executives (1-5): _____

### 4.3 Comparaison Approche B vs V1

**Si test V1 disponible**:
```
Metrique                      | V1 (hardcode) | Approche B | Delta
------------------------------|---------------|------------|-------
Temps normalisation (s)       |               |            |
Cout Bedrock normalisation    |               |            |
Taux matching (%)             |               |            |
Precision extraction (%)      |               |            |
Items newsletter              |               |            |
Qualite globale (1-5)         |               |            |
```

**Avantages Approche B observes**:
- [ ] _________________________________
- [ ] _________________________________
- [ ] _________________________________

**Inconvenients Approche B observes**:
- [ ] _________________________________
- [ ] _________________________________

---

## PHASE 5: ANALYSE SCALABILITE

### 5.1 Projection volume

**Scenario 1x (actuel)**:
- Sources: ~7 sources
- Items/jour: ~15-20 items
- Cout/run: ~$0.20-0.30

**Scenario 5x**:
- Sources: ~35 sources
- Items/jour: ~75-100 items
- Cout/run estime: ~$_____ (projection)
- Temps execution estime: ~_____ s

**Scenario 10x**:
- Sources: ~70 sources
- Items/jour: ~150-200 items
- Cout/run estime: ~$_____ (projection)
- Temps execution estime: ~_____ s

### 5.2 Goulots d'etranglement identifies

**Performance**:
- [ ] Goulot 1: _________________________________
- [ ] Goulot 2: _________________________________
- [ ] Goulot 3: _________________________________

**Cout**:
- [ ] Poste de cout principal: _________________________________
- [ ] Optimisation possible: _________________________________

**Qualite**:
- [ ] Point faible 1: _________________________________
- [ ] Point faible 2: _________________________________

---

## PHASE 6: RECOMMANDATIONS D'AMELIORATION

### 6.1 Ameliorations moteur

**Priorite HAUTE**:
1. _________________________________
2. _________________________________
3. _________________________________

**Priorite MOYENNE**:
1. _________________________________
2. _________________________________

**Priorite BASSE**:
1. _________________________________

### 6.2 Ameliorations fichiers canonical

**Scopes a enrichir**:
- [ ] lai_companies_global: ajouter _____ companies
- [ ] lai_keywords: ajouter _____ termes
- [ ] lai_molecules_global: ajouter _____ molecules
- [ ] lai_trademarks_global: ajouter _____ trademarks

**Prompts a optimiser**:
- [ ] Prompt normalisation: _________________________________
- [ ] Prompt matching: _________________________________

**Nouvelles regles a ajouter**:
- [ ] _________________________________
- [ ] _________________________________

### 6.3 Ameliorations configuration client

**lai_weekly_v5.yaml**:
- [ ] Ajuster min_domain_score: actuel _____ → propose _____
- [ ] Ajuster max_items sections: _________________________________
- [ ] Ajuster scoring bonuses: _________________________________

---

## PHASE 7: VALIDATION FINALE

### 7.1 Checklist validation

**Fonctionnel**:
- [ ] Pipeline E2E execute sans erreur
- [ ] Tous les fichiers S3 presents
- [ ] Newsletter generee et valide
- [ ] Logs CloudWatch complets

**Qualite**:
- [ ] Taux de matching >= 60%
- [ ] Precision extraction >= 80%
- [ ] Taux de bruit < 20%
- [ ] Qualite newsletter >= 3/5

**Performance**:
- [ ] Temps execution < 300s
- [ ] Cout total < $0.50
- [ ] Aucun throttling Bedrock
- [ ] Aucune erreur Lambda

**Approche B**:
- [ ] Prompts pre-construits utilises
- [ ] References {{ref:}} resolues
- [ ] Aucun fallback V1 force
- [ ] Logs confirment Approche B

### 7.2 Decision GO/NO-GO

**Criteres de validation**:
- [ ] Tous les criteres fonctionnels OK
- [ ] Au moins 3/4 criteres qualite OK
- [ ] Au moins 3/4 criteres performance OK
- [ ] Approche B fonctionnelle

**Decision**: GO / NO-GO / GO avec reserves

**Reserves eventuelles**:
- _________________________________
- _________________________________

---

## ANNEXES

### A. Commandes utiles

**Logs CloudWatch**:
```bash
# Logs ingest-v2
aws logs tail /aws/lambda/vectora-inbox-ingest-v2-dev --follow --profile rag-lai-prod --region eu-west-3

# Logs normalize-score-v2
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev --follow --profile rag-lai-prod --region eu-west-3

# Logs newsletter-v2
aws logs tail /aws/lambda/vectora-inbox-newsletter-v2-dev --follow --profile rag-lai-prod --region eu-west-3
```

**Analyse fichiers JSON**:
```bash
# Compter items
cat items_ingested.json | jq '. | length'

# Extraire companies
cat items_curated.json | jq '.[].normalized_content.entities.companies' | jq -s 'add | unique'

# Calculer score moyen
cat items_curated.json | jq '[.[].scoring_results.final_score] | add / length'
```

### B. Template rapport final

**Fichier**: `test_e2e_lai_weekly_v5_YYYYMMDD.md`

Structure:
1. Resume executif
2. Metriques quantitatives
3. Analyse qualitative
4. Comparaison Approche B vs V1
5. Recommandations
6. Annexes (logs, screenshots)

---

**Plan de Test E2E - lai_weekly_v5**
**Version 1.0 - 2025-12-23**
**Duree estimee: 30-45 minutes**
