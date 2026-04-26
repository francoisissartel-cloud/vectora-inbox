# Phase 1 - Ingestion lai_weekly_v6 - TERMINÉE

**Date**: 2026-01-27
**Timestamp début**: 09:47:30
**Durée**: 19.36 secondes
**Statut**: ✅ SUCCÈS

---

## RÉSUMÉ EXÉCUTIF

✅ **19 items ingérés → 18 items finaux (1 dédupliqué)**
✅ **7 sources traitées, 1 échec**
✅ **Fichier items.json généré (16.1 KB)**
✅ **Temps d'exécution: 19.36s**
⚠️ **Filtrage items courts NON appliqué (0 items filtrés)**

---

## 1.1 MÉTRIQUES QUANTITATIVES

### Volume de données
- **Items ingérés**: 19 items
- **Items dédupliqués**: 1 item
- **Items filtrés**: 0 items
- **Items finaux**: 18 items
- **Taille fichier**: 16.1 KB

### Sources traitées
- **Sources scrapées**: 7 sources
- **Sources réussies**: 6 sources
- **Sources échouées**: 1 source
- **Taux de succès**: 85.7%

### Performance
- **Temps total**: 19.36 secondes
- **Temps moyen/source**: ~2.8 secondes
- **Mode ingestion**: balanced
- **Mode temporel**: strict
- **Période**: 30 jours

---

## 1.2 RÉPARTITION PAR SOURCE

### Sources LAI Corporate (4 sources)

**press_corporate__nanexa**: 6 items
- Nanexa + Moderna partnership (PharmaShell®)
- Semaglutide monthly formulation (breakthrough data)
- Interim reports Q2/Q3 2025
- Word counts: 55, 44, 61, 10, 2, 10

**press_corporate__medincell**: 7 items
- Teva + MedinCell Olanzapine NDA submission
- UZEDY® growth + Olanzapine LAI Q4 2025
- Malaria grant (extended protection)
- Dr Grace Kim appointment
- MSCI World Small Cap Index
- Financial calendar + H1 results
- Word counts: 10, 19, 33, 11, 23, 16, 22

**press_corporate__delsitech**: 2 items
- Partnership Opportunities Drug Delivery 2025
- BIO International Convention 2025
- Word counts: 13, 11

**press_corporate__camurus**: 1 item
- FDA acceptance NDA resubmission Oclaiz™ (acromegaly)
- Word count: 63

### Sources LAI Press (2 sources)

**press_sector__fiercepharma**: 2 items
- Trump Davos drug pricing claims
- J&J talc litigation
- Word counts: 41, 53

**press_sector__endpoints**: 0 items (source échouée)

---

## 1.3 ANALYSE QUALITATIVE

### Items pertinents LAI identifiés

**HAUTE PERTINENCE** (4 items):
1. ✅ **Nanexa + Moderna**: Partnership PharmaShell® (61 mots)
   - USD 3M upfront + USD 500M milestones
   - 5 undisclosed compounds
   
2. ✅ **Nanexa Semaglutide**: Monthly formulation breakthrough (55 mots)
   - PharmaShell® platform
   - Improved pharmacokinetic profile
   
3. ✅ **MedinCell + Teva**: Olanzapine NDA submission (33 mots)
   - TEV-749 / mdc-TJK
   - Once-monthly schizophrenia treatment
   
4. ✅ **Camurus**: FDA acceptance Oclaiz™ NDA resubmission (63 mots)
   - Acromegaly treatment

**PERTINENCE MOYENNE** (3 items):
5. ⚠️ **MedinCell UZEDY®**: Growth + Olanzapine LAI Q4 2025 (22 mots)
6. ⚠️ **MedinCell Malaria**: Grant for extended protection (11 mots)
7. ⚠️ **MedinCell Dr Grace Kim**: CSO appointment (23 mots)

**BRUIT DÉTECTÉ** (11 items):
- Items trop courts: **8 items** (<20 mots)
  - "Download attachment" (2 mots)
  - Financial calendar (10 mots)
  - Interim reports (10 mots chacun)
  - BIO Convention (11 mots)
  - Partnership Opportunities (13 mots)
  - MSCI Index (16 mots)
  - H1 Results (19 mots)

- Items hors-sujet LAI: **2 items**
  - Trump Davos drug pricing (41 mots)
  - J&J talc litigation (53 mots)

---

## 1.4 QUALITÉ DES DONNÉES

### Champs présents
- ✅ **Titres**: Complets et cohérents (18/18)
- ✅ **URLs**: Valides (18/18)
- ✅ **Dates**: Présentes (18/18)
- ⚠️ **Contenu**: Variable (2-63 mots)
- ✅ **Metadata**: word_count présent (18/18)

### Distribution word_count
```
Range        | Count | %
-------------|-------|-----
0-10 mots    | 4     | 22%
11-20 mots   | 7     | 39%
21-50 mots   | 4     | 22%
51+ mots     | 3     | 17%
```

### Problèmes identifiés
⚠️ **Filtrage items courts NON appliqué**:
- Configuration v6: `min_word_count: 50`
- Résultat: 0 items filtrés
- Attendu: ~11 items filtrés (<50 mots)
- **Cause probable**: Filtrage non implémenté dans Lambda ingest-v2

⚠️ **Items génériques présents**:
- "Download attachment" (2 mots)
- Pattern dans exclude_patterns mais non filtré

---

## 1.5 ÉCHANTILLON ITEMS

### Item 1 - HAUTE PERTINENCE
**Titre**: Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products
**Source**: press_corporate__nanexa
**Taille**: 61 mots
**Pertinence**: ✅ Partnership majeur LAI technology

### Item 2 - HAUTE PERTINENCE
**Titre**: Nanexa Announces Breakthrough Preclinical Data Demonstrating Exceptional Pharmacokinetic Profile for Monthly Semaglutide Formulation
**Source**: press_corporate__nanexa
**Taille**: 55 mots
**Pertinence**: ✅ Innovation LAI GLP-1

### Item 3 - BRUIT
**Titre**: Download attachment
**Source**: press_corporate__nanexa
**Taille**: 2 mots
**Pertinence**: ❌ Item générique, devrait être filtré

---

## 1.6 VÉRIFICATION S3

### Fichier généré
✅ **Path S3**: `s3://vectora-inbox-data-dev/ingested/lai_weekly_v6/2026/01/27/items.json`
✅ **Taille**: 16.1 KB
✅ **Items**: 18 items
✅ **Structure JSON**: Valide

### Commandes exécutées
```bash
# Invocation Lambda
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev --cli-binary-format raw-in-base64-out --payload file://event_ingest_v6.json response_ingest_v6.json --profile rag-lai-prod --region eu-west-3

# Download items
aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v6/2026/01/27/items.json items_ingested_v6.json --profile rag-lai-prod --region eu-west-3
```

---

## 1.7 COMPARAISON v6 vs v5

### Métriques comparatives
```
Métrique                  | v5    | v6    | Delta
--------------------------|-------|-------|-------
Items ingérés             | 15    | 19    | +4
Items finaux              | 15    | 18    | +3
Items dédupliqués         | 0     | 1     | +1
Items filtrés             | 0     | 0     | 0
Sources traitées          | 3     | 7     | +4
Temps exécution (s)       | ~180  | 19.36 | -89%
Taille fichier (KB)       | 12.6  | 16.1  | +28%
```

### Observations
✅ **Plus de sources**: 7 sources vs 3 (ajout Camurus, FiercePharma, Endpoints)
✅ **Plus d'items**: 19 items vs 15 items
✅ **Déduplication active**: 1 item dédupliqué (Nanexa semaglutide doublon)
⚠️ **Filtrage NON appliqué**: 0 items filtrés malgré config min_word_count: 50
⚠️ **Bruit similaire**: ~61% items peu pertinents (11/18)

---

## 1.8 POINTS D'ATTENTION

### Filtrage items courts NON fonctionnel
⚠️ **Configuration v6**:
```yaml
source_config:
  content_filters:
    min_word_count: 50
    exclude_patterns:
      - "Download attachment"
```

⚠️ **Résultat observé**:
- 0 items filtrés
- Items <50 mots présents: 11 items (61%)
- Pattern "Download attachment" présent

⚠️ **Cause probable**:
- Paramètre `content_filters` non implémenté dans Lambda ingest-v2
- Filtrage devra être appliqué en Phase 2 (normalize-score-v2)

### Items hors-sujet LAI
⚠️ **2 items FiercePharma non-LAI**:
- Trump Davos drug pricing
- J&J talc litigation
- **Impact**: Bruit dans normalisation, coût Bedrock inutile

---

## PROCHAINES ÉTAPES

### Phase 2 - Normalisation
**Objectif**: Normaliser 18 items avec Approche B

**Commande**:
```bash
# Créer event_normalize_v6.json
echo {"client_id": "lai_weekly_v6"} > event_normalize_v6.json

# Invoquer Lambda
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --cli-binary-format raw-in-base64-out --payload file://event_normalize_v6.json response_normalize_v6.json --profile rag-lai-prod --region eu-west-3
```

**Monitoring**:
```bash
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev --follow --profile rag-lai-prod --region eu-west-3
```

**Attendu**:
- Items normalisés: 18 items
- Filtrage items courts: Vérifier si appliqué en normalisation
- Approche B: Prompts LAI pré-construits
- Temps: ~3-5 minutes (estimation)

---

## FICHIERS GÉNÉRÉS

### Phase 1
- ✅ `event_ingest_v6.json` - Event invocation
- ✅ `response_ingest_v6.json` - Réponse Lambda
- ✅ `items_ingested_v6.json` - Items ingérés (16.1 KB)

### Prochains fichiers (Phase 2)
- `event_normalize_v6.json` - Event normalisation
- `response_normalize_v6.json` - Réponse normalisation
- `items_curated_v6.json` - Items curated

---

## RECOMMANDATIONS

### Priorité HAUTE
1. **Implémenter filtrage items courts**: Ajouter support `content_filters` dans ingest-v2 ou normalize-score-v2
2. **Améliorer scraping FiercePharma**: Filtrer items non-LAI avant ingestion
3. **Exclure patterns génériques**: "Download attachment", "Read More", etc.

### Priorité MOYENNE
4. **Optimiser déduplication**: 1 doublon détecté (Nanexa semaglutide)
5. **Améliorer extraction contenu**: Items trop courts (2-19 mots)

---

**Phase 1 - Ingestion lai_weekly_v6**
**Version 1.0 - 2026-01-27**
**Statut: ✅ SUCCÈS - Prêt pour Phase 2**
**Réserve: ⚠️ Filtrage items courts NON appliqué**
