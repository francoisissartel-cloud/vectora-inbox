# Plan Test E2E - lai_weekly_v7 (Test Extraction Dates Bedrock)

**Date**: 2026-01-29  
**Client**: lai_weekly_v7 (NOUVEAU)  
**Objectif**: Valider extraction dates réelles via Bedrock (Plan Correctif v4)  
**Layer**: v5 avec parsing dates corrigé  
**Durée estimée**: 30 minutes

---

## 🎯 OBJECTIFS DU TEST

### Objectif Principal
**Valider que >95% des dates sont extraites par Bedrock** (vs 0% actuellement)

### Objectifs Spécifiques
1. ✅ Vérifier extraction `extracted_date` et `date_confidence` dans `normalized_content`
2. ✅ Vérifier utilisation `effective_date` dans `scoring_results`
3. ✅ Vérifier affichage dates réelles dans newsletter
4. ✅ Mesurer taux de succès extraction dates
5. ✅ Comparer dates Bedrock vs dates fallback

### Périmètre
- ✅ Lambda ingest-v2: Nouveau run (dates fallback)
- ✅ Lambda normalize-score-v2: Extraction dates Bedrock (layer v5)
- ✅ Lambda newsletter-v2: Affichage dates réelles
- ✅ Client lai_weekly_v7: Configuration test extraction dates

---

## ✅ PHASE 0: PRÉPARATION (DÉJÀ FAIT)

### 0.1 Configuration client v7
- ✅ Fichier créé: `client-config-examples/lai_weekly_v7.yaml`
- ✅ Uploadé S3: `s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml`
- ✅ Base: lai_weekly_v6.yaml
- ✅ Modifications: client_id, notes test extraction dates

### 0.2 Correctifs appliqués (Plan Correctif v4)
- ✅ Prompt enrichi: `lai_prompt.yaml` (S3)
- ✅ Parser normalizer: `normalizer.py` (layer v5)
- ✅ Scoring dates: `scorer.py` (layer v5)
- ✅ Newsletter dates: `assembler.py` (layer v5)
- ✅ **CRITIQUE**: Parsing Bedrock: `bedrock_client.py` (layer v5)

### 0.3 Environnement
- ✅ Layer v5 déployé
- ✅ Lambda normalize-score-v2: layer v5
- ✅ Lambda newsletter-v2: layer v5
- ✅ Prompt LAI enrichi sur S3

---

## 📋 PHASE 1: INGESTION

### 1.1 Exécution

**Event**: `event_ingest_v7.json`
```json
{
  "client_id": "lai_weekly_v7",
  "force_refresh": true
}
```

**Commande**:
```bash
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload file://event_ingest_v7.json \
  --region eu-west-3 --profile rag-lai-prod \
  response_ingest_v7.json
```

### 1.2 Métriques Attendues
- Items ingérés: ~20-25
- Dates: Fallback (date d'ingestion)
- Temps: ~15-20s

### 1.3 Validation
```bash
# Télécharger items ingested
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v7/2026/01/29/items.json \
  items_ingested_v7.json --region eu-west-3 --profile rag-lai-prod

# Vérifier structure
type items_ingested_v7.json | jq ".[0] | keys"
```

**Checklist**:
- [ ] Fichier items.json présent
- [ ] Champ `published_at` présent (date fallback)
- [ ] Nombre items: _______

---

## 📋 PHASE 2: NORMALISATION (FOCUS EXTRACTION DATES)

### 2.1 Exécution

**Event**: `event_normalize_v7.json`
```json
{
  "client_id": "lai_weekly_v7"
}
```

**Commande**:
```bash
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload file://event_normalize_v7.json \
  --region eu-west-3 --profile rag-lai-prod \
  response_normalize_v7.json
```

**Note**: Peut prendre 5-10 minutes pour 20-25 items

### 2.2 Métriques Extraction Dates (CRITIQUE)

**Télécharger items curated**:
```bash
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v7/2026/01/29/items.json \
  items_curated_v7.json --region eu-west-3 --profile rag-lai-prod
```

**Analyser extraction dates**:
```bash
python scripts/validate_bedrock_dates_v7.py
```

**Métriques attendues**:
```
Métrique                    | Cible  | Actuel | Status
----------------------------|--------|--------|--------
Dates Bedrock extraites     | >95%   |        | 
Haute confiance (>0.8)      | >90%   |        |
Dates fallback utilisées    | <5%    |        |
Effective_date = Bedrock    | >95%   |        |
```

### 2.3 Validation Structure Données

**Vérifier normalized_content**:
```bash
# Extraire premier item
type items_curated_v7.json | jq ".[0].normalized_content"
```

**Champs attendus**:
- [ ] `extracted_date`: "2026-01-XX" ou null
- [ ] `date_confidence`: 0.0-1.0
- [ ] `summary`: présent
- [ ] `entities`: présent
- [ ] `lai_relevance_score`: 0-10

**Vérifier scoring_results**:
```bash
# Extraire scoring
type items_curated_v7.json | jq ".[0].scoring_results"
```

**Champs attendus**:
- [ ] `effective_date`: "2026-01-XX"
- [ ] `final_score`: nombre
- [ ] `bonuses`: objet
- [ ] `penalties`: objet

### 2.4 Analyse Qualitative Dates

**Échantillon 5 items**:
```
Item 1:
- Title: _________________________________
- Published_at (fallback): _______
- Extracted_date (Bedrock): _______
- Date_confidence: _______
- Effective_date (scoring): _______
- Match correct: OUI / NON

Item 2:
- Title: _________________________________
- Published_at (fallback): _______
- Extracted_date (Bedrock): _______
- Date_confidence: _______
- Effective_date (scoring): _______
- Match correct: OUI / NON

[Items 3-5]
```

### 2.5 Logs CloudWatch

**Vérifier logs extraction**:
```bash
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 30m --region eu-west-3 --profile rag-lai-prod \
  --format short | findstr "Date extracted"
```

**Logs attendus**:
- "Date extracted by Bedrock: 2026-01-XX (confidence: 0.XX)"
- "Using Bedrock date: 2026-01-XX"
- "Using fallback date: 2026-01-29" (si échec)

---

## 📋 PHASE 3: NEWSLETTER (VÉRIFICATION DATES AFFICHÉES)

### 3.1 Exécution

**Event**: `event_newsletter_v7.json`
```json
{
  "client_id": "lai_weekly_v7"
}
```

**Commande**:
```bash
aws lambda invoke --function-name vectora-inbox-newsletter-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload file://event_newsletter_v7.json \
  --region eu-west-3 --profile rag-lai-prod \
  response_newsletter_v7.json
```

### 3.2 Vérification Dates Newsletter

**Télécharger newsletter**:
```bash
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v7/2026/01/29/newsletter.md \
  newsletter_v7.md --region eu-west-3 --profile rag-lai-prod
```

**Analyser dates affichées**:
```bash
# Extraire toutes les dates
type newsletter_v7.md | findstr "Date:"
```

**Validation**:
- [ ] Dates affichées != 2026-01-29 (pas toutes fallback)
- [ ] Dates cohérentes avec contenu
- [ ] Format: "Jan 27, 2026" ou similaire

**Échantillon 3 items newsletter**:
```
Item 1:
- Title: _________________________________
- Date affichée: _______
- Date attendue: _______
- Correct: OUI / NON

Item 2:
- Title: _________________________________
- Date affichée: _______
- Date attendue: _______
- Correct: OUI / NON

Item 3:
- Title: _________________________________
- Date affichée: _______
- Date attendue: _______
- Correct: OUI / NON
```

---

## 📊 PHASE 4: ANALYSE RÉSULTATS

### 4.1 Métriques Finales Extraction Dates

```
Métrique                    | Avant  | Cible  | Après  | Delta  | Status
----------------------------|--------|--------|--------|--------|--------
Vraies dates extraites      | 0%     | >95%   |        |        |
Dates Bedrock fiables       | N/A    | >90%   |        |        |
Dates fallback              | 100%   | <5%    |        |        |
Temps normalisation/item    | 4.9s   | <5.5s  |        |        |
Coût par run                | $0.21  | <$0.25 |        |        |
```

### 4.2 Comparaison v7 vs v6

```
Métrique                    | v6     | v7     | Delta
----------------------------|--------|--------|-------
Items ingérés               |        |        |
Dates Bedrock extraites     | 0%     |        |
Dates affichées newsletter  | Fallback|       |
Qualité chronologie         | Perdue |        |
```

### 4.3 Validation Objectif

**Objectif**: >95% de vraies dates extraites

**Résultat**: _______ %

**Status**: ✅ SUCCÈS / ❌ ÉCHEC / ⚠️ PARTIEL

**Si ÉCHEC ou PARTIEL**:
- Cause identifiée: _________________________________
- Action corrective: _________________________________

---

## 📋 PHASE 5: VALIDATION FINALE

### 5.1 Checklist Validation

**Extraction Dates**:
- [ ] >95% items avec `extracted_date` non-null
- [ ] >90% items avec `date_confidence` > 0.8
- [ ] <5% items utilisent date fallback
- [ ] Dates extraites cohérentes avec contenu

**Scoring**:
- [ ] `effective_date` présent dans tous items
- [ ] `effective_date` utilise date Bedrock si confiance > 0.7
- [ ] Recency factor calculé avec date effective
- [ ] Penalties calculées avec date effective

**Newsletter**:
- [ ] Dates affichées != toutes fallback
- [ ] Dates cohérentes avec contenu
- [ ] Format dates correct
- [ ] Chronologie restaurée

**Performance**:
- [ ] Temps normalisation < 10min
- [ ] Coût Bedrock < $0.30
- [ ] Aucune erreur Lambda
- [ ] Aucun throttling

### 5.2 Décision GO/NO-GO

**Critères**:
- [ ] Extraction dates >= 95%
- [ ] Performance acceptable
- [ ] Newsletter correcte
- [ ] Aucune régression

**Décision**: ✅ GO / ❌ NO-GO / ⚠️ GO avec réserves

**Réserves**:
- _________________________________
- _________________________________

---

## 📁 FICHIERS GÉNÉRÉS

### Fichiers de Test
- `event_ingest_v7.json`
- `event_normalize_v7.json`
- `event_newsletter_v7.json`

### Fichiers de Résultats
- `response_ingest_v7.json`
- `response_normalize_v7.json`
- `response_newsletter_v7.json`
- `items_ingested_v7.json`
- `items_curated_v7.json`
- `newsletter_v7.md`

### Script de Validation
- `scripts/validate_bedrock_dates_v7.py`

---

## 🎯 CONCLUSION

### Si SUCCÈS (>95% dates extraites)
✅ Plan Correctif v4 validé  
✅ Extraction dates Bedrock fonctionnelle  
✅ Chronologie restaurée dans newsletter  
✅ Prêt pour production

### Si ÉCHEC (<80% dates extraites)
❌ Diagnostic approfondi requis  
❌ Vérifier logs Bedrock  
❌ Ajuster prompt si nécessaire  
❌ Retester avec échantillon réduit

---

**Plan Test E2E - lai_weekly_v7**  
**Version 1.0 - 2026-01-29**  
**Durée estimée: 30 minutes**  
**Focus: Extraction Dates Bedrock**
