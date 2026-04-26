# Plan Test E2E Complet - lai_weekly_v6 (Fresh Run)

**Date**: 2026-01-27
**Client**: lai_weekly_v6 (NOUVEAU)
**Objectif**: Test complet workflow Ingestion → Normalisation → Newsletter
**Principe**: Nouveaux runs uniquement, aucune donnee ancienne
**Duree estimee**: 45-60 minutes

---

## OBJECTIFS DU TEST

### Objectifs principaux
1. Tester TOUTES les Lambdas avec nouveaux runs
2. Valider workflow complet: Ingestion → Normalisation → Newsletter
3. Mesurer metriques quantitatives et qualitatives a chaque etape
4. Identifier points d'amelioration moteur et canonical

### Perimetre
- ✅ Lambda ingest-v2: Nouveau run complet
- ✅ Lambda normalize-score-v2: Nouveau run avec Approche B
- ✅ Lambda newsletter-v2: Nouveau run generation newsletter
- ✅ Client lai_weekly_v6: Configuration nouvelle basee sur v5

---

## PHASE 0: PREPARATION CLIENT lai_weekly_v6

### 0.1 Creation configuration client

**Fichier**: `client-config-examples/lai_weekly_v6.yaml`

**Base**: Copie de lai_weekly_v5.yaml avec modifications:
- client_id: lai_weekly_v6
- Ajout filtrage items courts (min_word_count: 50)
- Optimisation deduplication

**Commandes**:
```bash
# Copier v5 vers v6
copy client-config-examples\lai_weekly_v5.yaml client-config-examples\lai_weekly_v6.yaml

# Editer lai_weekly_v6.yaml
# - Changer client_id
# - Ajouter filtres
```

### 0.2 Upload configuration S3

**Commande**:
```bash
aws s3 cp client-config-examples/lai_weekly_v6.yaml s3://vectora-inbox-config-dev/clients/lai_weekly_v6.yaml --profile rag-lai-prod --region eu-west-3
```

**Validation**:
```bash
aws s3 ls s3://vectora-inbox-config-dev/clients/lai_weekly_v6.yaml --profile rag-lai-prod --region eu-west-3
```

### 0.3 Verification environnement

**Checklist**:
- [ ] Lambda ingest-v2 deployee et operationnelle
- [ ] Lambda normalize-score-v2 avec layers Approche B
- [ ] Lambda newsletter-v2 deployee
- [ ] Prompts LAI sur S3
- [ ] Client config lai_weekly_v6 sur S3
- [ ] Acces CloudWatch Logs

**Commandes verification**:
```bash
# Verifier Lambdas
aws lambda list-functions --profile rag-lai-prod --region eu-west-3 --query "Functions[?contains(FunctionName, 'vectora-inbox')].FunctionName"

# Verifier layers normalize-score-v2
aws lambda get-function-configuration --function-name vectora-inbox-normalize-score-v2-dev --profile rag-lai-prod --region eu-west-3 --query "Layers[*].Arn"
```

---

## PHASE 1: INGESTION (Lambda ingest-v2)

### 1.1 Preparation invocation

**Event JSON**: `event_ingest_v6.json`
```json
{
  "client_id": "lai_weekly_v6"
}
```

**Timestamp debut**: _________________

### 1.2 Execution ingestion

**Commande**:
```bash
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev --cli-binary-format raw-in-base64-out --payload file://event_ingest_v6.json response_ingest_v6.json --profile rag-lai-prod --region eu-west-3
```

**Monitoring temps reel**:
```bash
aws logs tail /aws/lambda/vectora-inbox-ingest-v2-dev --follow --profile rag-lai-prod --region eu-west-3
```

### 1.3 Metriques quantitatives

**Volume de donnees**:
- [ ] Nombre total de sources scrapees: _______
- [ ] Nombre total d'items recuperes: _______
- [ ] Nombre d'items apres deduplication: _______
- [ ] Taille fichier items.json (KB): _______

**Performance**:
- [ ] Temps execution total (s): _______
- [ ] Temps moyen par source (s): _______
- [ ] Nombre d'erreurs HTTP: _______
- [ ] Taux de succes scraping (%): _______

**Repartition par source**:
```
Source                    | Items | Temps (s) | Statut
--------------------------|-------|-----------|--------
press_corporate__nanexa   |       |           |
press_corporate__camurus  |       |           |
press_corporate__delsitech|       |           |
press_corporate__medincell|       |           |
press_corporate__peptron  |       |           |
press_lai_fierce_biotech  |       |           |
press_lai_endpoints       |       |           |
```

### 1.4 Analyse qualitative

**Qualite des donnees**:
- [ ] Titres complets: OUI / NON
- [ ] Contenu extrait: OUI / NON
- [ ] Dates presentes: OUI / NON
- [ ] URLs valides: OUI / NON

**Gestion du bruit**:
- [ ] Items hors-sujet: _______
- [ ] Doublons: _______
- [ ] Items trop courts (<50 mots): _______

**Echantillon items** (3 exemples):
```
1. Titre: _________________________________
   Source: _________________________________
   Taille: _______ mots

2. Titre: _________________________________
   Source: _________________________________
   Taille: _______ mots

3. Titre: _________________________________
   Source: _________________________________
   Taille: _______ mots
```

### 1.5 Verification S3

**Commandes**:
```bash
# Lister run ingested
aws s3 ls s3://vectora-inbox-data-dev/ingested/lai_weekly_v6/ --recursive --profile rag-lai-prod --region eu-west-3

# Telecharger items.json
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v6/YYYY/MM/DD/items.json items_ingested_v6.json --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Fichier items.json present
- [ ] Structure JSON valide
- [ ] Nombre items coherent

---

## PHASE 2: NORMALISATION (Lambda normalize-score-v2)

### 2.1 Preparation invocation

**Event JSON**: `event_normalize_v6.json`
```json
{
  "client_id": "lai_weekly_v6"
}
```

**Timestamp debut**: _________________

### 2.2 Execution normalisation

**Commande**:
```bash
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --cli-binary-format raw-in-base64-out --payload file://event_normalize_v6.json response_normalize_v6.json --profile rag-lai-prod --region eu-west-3
```

**Monitoring temps reel**:
```bash
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev --follow --profile rag-lai-prod --region eu-west-3
```

### 2.3 Metriques quantitatives - Normalisation

**Volume**:
- [ ] Items input: _______
- [ ] Items normalises: _______
- [ ] Items erreur: _______
- [ ] Taux succes (%): _______

**Appels Bedrock**:
- [ ] Nombre appels normalisation: _______
- [ ] Nombre appels matching: _______
- [ ] Nombre throttling: _______
- [ ] Nombre erreurs: _______

**Performance**:
- [ ] Temps execution (s): _______
- [ ] Temps moyen/item (s): _______
- [ ] Temps appels Bedrock (s): _______

**Cout**:
- [ ] Tokens input total: _______
- [ ] Tokens output total: _______
- [ ] Cout Bedrock ($): _______

### 2.4 Metriques quantitatives - Extraction entites

**Totaux**:
- [ ] Companies: _______
- [ ] Molecules: _______
- [ ] Technologies: _______
- [ ] Trademarks: _______
- [ ] Indications: _______

**Moyennes par item**:
- [ ] Companies/item: _______
- [ ] Molecules/item: _______
- [ ] Technologies/item: _______

**Event types**:
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

### 2.5 Analyse qualitative - Extraction

**Precision extraction** (5 items):
```
Item 1:
- Companies: _________________________________
- Precision: _____ / _____
- Hallucinations: _____

Item 2:
- Companies: _________________________________
- Precision: _____ / _____
- Hallucinations: _____

[Items 3-5]
```

**Qualite summaries**:
- [ ] Coherents: OUI / NON
- [ ] Longueur appropriee: OUI / NON
- [ ] Informations cles: OUI / NON

**Approche B - Validation**:
- [ ] Logs "Approche B activee": OUI / NON
- [ ] References resolues: OUI / NON
- [ ] Taille prompt (chars): _______

### 2.6 Metriques quantitatives - Matching

**Volume**:
- [ ] Items a matcher: _______
- [ ] Items matches: _______
- [ ] Items non-matches: _______
- [ ] Taux matching (%): _______

**Repartition domaines**:
```
Domain               | Matches | Conf High | Conf Med | Conf Low
---------------------|---------|-----------|----------|----------
tech_lai_ecosystem   |         |           |          |
```

**Performance**:
- [ ] Temps matching (s): _______
- [ ] Cout Bedrock ($): _______

### 2.7 Analyse qualitative - Matching

**Precision** (5 items):
```
Item 1:
- Domaine: _________________________________
- Score: _______
- Confidence: _______
- Match correct: OUI / NON

[Items 2-5]
```

**Faux positifs**: _______
**Faux negatifs**: _______

### 2.8 Metriques quantitatives - Scoring

**Distribution scores**:
```
Score Range    | Count | %
---------------|-------|-----
0-5            |       |
5-10           |       |
10-15          |       |
15-20          |       |
20+            |       |
```

**Statistiques**:
- [ ] Score min: _______
- [ ] Score max: _______
- [ ] Score moyen: _______
- [ ] Score median: _______

**Bonuses appliques**:
```
Bonus Type              | Items | Bonus moyen
------------------------|-------|------------
pure_player_companies   |       |
trademark_mentions      |       |
key_molecules           |       |
```

### 2.9 Verification S3 curated

**Commandes**:
```bash
# Lister run curated
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v6/ --recursive --profile rag-lai-prod --region eu-west-3

# Telecharger items.json
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v6/YYYY/MM/DD/items.json items_curated_v6.json --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Fichier present
- [ ] Structure valide
- [ ] Champs normalized_content
- [ ] Champs matching_results
- [ ] Champs scoring_results

---

## PHASE 3: NEWSLETTER (Lambda newsletter-v2)

### 3.1 Preparation invocation

**Event JSON**: `event_newsletter_v6.json`
```json
{
  "client_id": "lai_weekly_v6"
}
```

**Timestamp debut**: _________________

### 3.2 Execution newsletter

**Commande**:
```bash
aws lambda invoke --function-name vectora-inbox-newsletter-v2-dev --cli-binary-format raw-in-base64-out --payload file://event_newsletter_v6.json response_newsletter_v6.json --profile rag-lai-prod --region eu-west-3
```

**Monitoring temps reel**:
```bash
aws logs tail /aws/lambda/vectora-inbox-newsletter-v2-dev --follow --profile rag-lai-prod --region eu-west-3
```

### 3.3 Metriques quantitatives - Selection

**Volume**:
- [ ] Items curated disponibles: _______
- [ ] Items selectionnes: _______
- [ ] Taux selection (%): _______

**Repartition sections**:
```
Section              | Max | Selectionnes | Trimmes
---------------------|-----|--------------|--------
regulatory_updates   | 6   |              |
partnerships_deals   | 4   |              |
clinical_updates     | 5   |              |
others               | 8   |              |
```

**Deduplication**:
- [ ] Items dedupliques: _______

### 3.4 Metriques quantitatives - Generation editoriale

**Appels Bedrock**:
- [ ] TL;DR generation: OUI / NON
- [ ] Introduction generation: OUI / NON
- [ ] Tokens input: _______
- [ ] Tokens output: _______
- [ ] Cout ($): _______

**Performance**:
- [ ] Temps execution (s): _______
- [ ] Temps editorial (s): _______

### 3.5 Analyse qualitative - Newsletter

**Qualite TL;DR**:
- [ ] Present: OUI / NON
- [ ] Longueur appropriee: OUI / NON
- [ ] Informations cles: OUI / NON
- [ ] Ton executif: OUI / NON

**Qualite introduction**:
- [ ] Presente: OUI / NON
- [ ] Contexte clair: OUI / NON
- [ ] Longueur appropriee: OUI / NON

**Qualite sections**:
```
Section              | Items | Pertinence | Ordre | Qualite
---------------------|-------|------------|-------|--------
regulatory_updates   |       | 1-5        | OK/KO | 1-5
partnerships_deals   |       | 1-5        | OK/KO | 1-5
clinical_updates     |       | 1-5        | OK/KO | 1-5
others               |       | 1-5        | OK/KO | 1-5
```

**Gestion bruit**:
- [ ] Items hors-sujet: _______
- [ ] Items redondants: _______
- [ ] Items peu pertinents: _______

### 3.6 Verification S3 newsletter

**Commandes**:
```bash
# Lister newsletters
aws s3 ls s3://vectora-inbox-newsletters-dev/lai_weekly_v6/ --recursive --profile rag-lai-prod --region eu-west-3

# Telecharger newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v6/YYYY/MM/DD/newsletter.md newsletter_v6.md --profile rag-lai-prod --region eu-west-3
```

**Validation**:
- [ ] Fichier newsletter.md present
- [ ] Format Markdown valide
- [ ] Toutes sections presentes
- [ ] Metriques incluses

---

## PHASE 4: ANALYSE GLOBALE E2E

### 4.1 Funnel de conversion complet

```
Etape                    | Volume | Taux conv | Taux perte
-------------------------|--------|-----------|------------
Sources scrapees         |        | -         | -
Items ingesres           |        | ___%      | ___%
Items normalises         |        | ___%      | ___%
Items matches            |        | ___%      | ___%
Items scores >10         |        | ___%      | ___%
Items newsletter         |        | ___%      | ___%
```

### 4.2 Performance globale

**Temps execution**:
- [ ] Ingestion (s): _______
- [ ] Normalisation (s): _______
- [ ] Newsletter (s): _______
- [ ] Total E2E (s): _______

**Cout global**:
- [ ] Bedrock normalisation ($): _______
- [ ] Bedrock matching ($): _______
- [ ] Bedrock editorial ($): _______
- [ ] Total Bedrock ($): _______
- [ ] Lambda (estime) ($): _______
- [ ] Total E2E ($): _______

### 4.3 Qualite du signal

**Precision globale**:
- [ ] Items pertinents/total: ____ / ____
- [ ] Taux bruit (%): _______
- [ ] Taux faux positifs (%): _______
- [ ] Taux faux negatifs (%): _______

**Qualite entites**:
- [ ] Precision companies (%): _______
- [ ] Precision molecules (%): _______
- [ ] Precision technologies (%): _______
- [ ] Taux hallucinations (%): _______

**Qualite newsletter**:
- [ ] Pertinence globale (1-5): _____
- [ ] Diversite sujets (1-5): _____
- [ ] Qualite editoriale (1-5): _____
- [ ] Utilite executives (1-5): _____

---

## PHASE 5: COMPARAISON v6 vs v5

### 5.1 Metriques comparatives

```
Metrique                      | v5    | v6    | Delta
------------------------------|-------|-------|-------
Items ingesres                | 15    |       |
Taux matching (%)             | 100   |       |
Temps normalisation (s)       | ~300  |       |
Cout Bedrock normalisation    | ~$0.2 |       |
Items newsletter              | -     |       |
Qualite globale (1-5)         | -     |       |
```

### 5.2 Ameliorations observees

**v6 vs v5**:
- [ ] _________________________________
- [ ] _________________________________
- [ ] _________________________________

**Regressions observees**:
- [ ] _________________________________
- [ ] _________________________________

---

## PHASE 6: RECOMMANDATIONS

### 6.1 Ameliorations moteur

**Priorite HAUTE**:
1. _________________________________
2. _________________________________
3. _________________________________

**Priorite MOYENNE**:
1. _________________________________
2. _________________________________

### 6.2 Ameliorations canonical

**Scopes a enrichir**:
- [ ] lai_companies_global: _________________________________
- [ ] lai_keywords: _________________________________
- [ ] lai_molecules_global: _________________________________

**Prompts a optimiser**:
- [ ] Normalisation: _________________________________
- [ ] Matching: _________________________________

### 6.3 Ameliorations configuration

**lai_weekly_v6.yaml**:
- [ ] Ajuster min_domain_score: _______
- [ ] Ajuster max_items sections: _______
- [ ] Ajuster bonuses: _______

---

## PHASE 7: VALIDATION FINALE

### 7.1 Checklist validation

**Fonctionnel**:
- [ ] Pipeline E2E execute sans erreur
- [ ] Tous fichiers S3 presents
- [ ] Newsletter generee et valide
- [ ] Logs CloudWatch complets

**Qualite**:
- [ ] Taux matching >= 60%
- [ ] Precision extraction >= 80%
- [ ] Taux bruit < 20%
- [ ] Qualite newsletter >= 3/5

**Performance**:
- [ ] Temps execution < 600s
- [ ] Cout total < $1.00
- [ ] Aucun throttling
- [ ] Aucune erreur Lambda

**Approche B**:
- [ ] Prompts utilises
- [ ] References resolues
- [ ] Aucun fallback V1
- [ ] Logs confirment

### 7.2 Decision GO/NO-GO

**Criteres**:
- [ ] Tous criteres fonctionnels OK
- [ ] 3/4 criteres qualite OK
- [ ] 3/4 criteres performance OK
- [ ] Approche B fonctionnelle

**Decision**: GO / NO-GO / GO avec reserves

**Reserves**:
- _________________________________
- _________________________________

---

## ANNEXES

### A. Scripts preparation

**Creation lai_weekly_v6.yaml**:
```bash
# Copier et editer
copy client-config-examples\lai_weekly_v5.yaml client-config-examples\lai_weekly_v6.yaml
```

**Upload S3**:
```bash
aws s3 cp client-config-examples/lai_weekly_v6.yaml s3://vectora-inbox-config-dev/clients/lai_weekly_v6.yaml --profile rag-lai-prod --region eu-west-3
```

### B. Events JSON

**event_ingest_v6.json**:
```json
{"client_id": "lai_weekly_v6"}
```

**event_normalize_v6.json**:
```json
{"client_id": "lai_weekly_v6"}
```

**event_newsletter_v6.json**:
```json
{"client_id": "lai_weekly_v6"}
```

### C. Commandes analyse

**Compter items**:
```bash
type items_ingested_v6.json | jq ". | length"
```

**Extraire companies**:
```bash
type items_curated_v6.json | jq ".[].normalized_content.entities.companies"
```

**Score moyen**:
```bash
type items_curated_v6.json | jq "[.[].scoring_results.final_score] | add / length"
```

---

**Plan Test E2E Complet - lai_weekly_v6**
**Version 1.0 - 2026-01-27**
**Duree estimee: 45-60 minutes**
**Workflow: Ingestion → Normalisation → Newsletter**
