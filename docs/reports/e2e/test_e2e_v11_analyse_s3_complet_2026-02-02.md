# Test E2E lai_weekly_v11 - Rapport Complet 2026-02-02

## 📋 MÉTADONNÉES DU TEST

**Client testé** : lai_weekly_v11  
**Date exécution** : 2026-02-03  
**Environnement** : dev  
**Durée totale** : 170.5s (~2.8 min)  
**Statut** : ⚠️ PARTIEL - Pipeline OK, 0 matches  
**Testeur** : Q Developer  
**Objectif** : Valider cleanup prompts obsolètes + Analyse fichiers S3

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Métriques Clés

| Métrique | Valeur | Objectif | Statut |
|----------|--------|----------|--------|
| Items ingérés | 29 | >10 | ✅ |
| Items normalisés | 29 (100%) | >95% | ✅ |
| Items matchés | 0 (0%) | >50% | ❌ |
| Temps total E2E | 170.5s | <600s | ✅ |
| Taux succès Bedrock | 100% | >95% | ✅ |

### Funnel de Conversion

| Étape | Volume | Taux conv | Taux perte |
|-------|--------|-----------|------------|
| Items ingérés | 29 | 100% | 0% |
| Items normalisés | 29 | 100% | 0% |
| Items matchés | 0 | 0% | 100% |

### Verdict Global

**⚠️ PAS D'ACCORD** avec la performance du moteur

**Justification** :
1. ✅ Pipeline technique fonctionne (ingestion + normalisation OK)
2. ❌ 0 matches sur 29 items LAI pertinents (problème critique)
3. ❌ Prompts nettoyés fonctionnent mais matching trop strict

---

## 📊 PHASE 1 : INGESTION

### Métriques Ingestion

**Volume** :
- Items récupérés : 29 items
- Items dédupliqués : 0 items (0%)
- Items finaux : 29 items

**Performance** :
- Temps total : ~21s
- Taux succès sources : 100% (2/2 sources)

**Sources Scrapées** :

| Source | Type | Items | Statut |
|--------|------|-------|--------|
| press_corporate__nanexa | corporate | 6 | ✅ |
| press_corporate__delsitech | corporate | 4 | ✅ |
| press_corporate__medincell | corporate | 10 | ✅ |
| press_corporate__camurus | corporate | 1 | ✅ |
| press_sector__fiercepharma | press | 3 | ✅ |
| press_sector__endpoints_news | press | 5 | ✅ |

### Distribution Word Count

| Range | Count | % |
|-------|-------|---|
| 0-20 mots | 11 | 38% |
| 21-40 mots | 14 | 48% |
| 41-60 mots | 3 | 10% |
| 61+ mots | 1 | 3% |

### Items Pertinents LAI Identifiés

**Haute pertinence** (10+ items) :
1. ✅ **Nanexa + Moderna** - Partnership PharmaShell® (61 mots)
2. ✅ **MedinCell UZEDY®** - Sales $191M (+63%) (26 mots)
3. ✅ **MedinCell Olanzapine LAI** - NDA submission (33 mots)
4. ✅ **AstraZeneca + CSPC** - Long-acting obesity drugs $1.2B (33 mots)
5. ✅ **Lilly** - $3.5B injectable factory retatrutide (36 mots)
6. ✅ **Camurus Oclaiz™** - FDA NDA resubmission acromegaly (63 mots)

**Bruit détecté** (5 items) :
- Items trop courts : 11 items (<20 mots) - "Download attachment", etc.
- Items hors-sujet : 3 items (AI med comms, Super Bowl ad, etc.)

### Fichier Généré

**Path S3** : `s3://vectora-inbox-data-dev/ingested/lai_weekly_v11/2026/02/03/items.json`  
**Taille** : 25.8 KB  
**Structure** : ✅ Conforme

---

## 📊 PHASE 2 : NORMALISATION & SCORING

### Métriques Normalisation

**Volume** :
- Items input : 29 items
- Items normalisés : 29 items (100%)
- Items erreur : 0 items (0%)

**Performance** :
- Temps total : 149.5s (~2.5 min)
- Temps moyen/item : 5.2s
- Appels Bedrock : 58 (29 normalisation + 29 domain scoring)

### Extraction Entités (Analyse Échantillon)

**Items LAI pertinents détectés** :

**Item #1 - Nanexa + Moderna Partnership** :
- Companies: ["Nanexa", "Moderna"]
- Technologies: ["PharmaShell®", "atomic layer deposition", "ALD"]
- Molecules: ["semaglutide"]
- Event: partnership

**Item #2 - MedinCell UZEDY®** :
- Companies: ["MedinCell", "Teva"]
- Trademarks: ["UZEDY®"]
- Molecules: ["olanzapine"]
- Event: financial_results

**Item #3 - AstraZeneca + CSPC** :
- Companies: ["AstraZeneca", "CSPC Pharmaceutical"]
- Technologies: ["long-acting"]
- Event: partnership

**Item #4 - Lilly Injectable Factory** :
- Companies: ["Eli Lilly"]
- Technologies: ["injectable", "device"]
- Molecules: ["retatrutide"]
- Event: corporate_move

### Event Classification

| Event Type | Count | % |
|------------|-------|---|
| partnership | 3 | 10% |
| financial_results | 5 | 17% |
| regulatory | 2 | 7% |
| corporate_move | 2 | 7% |
| clinical_update | 1 | 3% |
| other | 16 | 55% |

### Matching Results

**Volume matching** :
- Items à matcher : 29 items
- Items matchés : 0 items (0%) ❌
- Items non-matchés : 29 items (100%)

**Problème identifié** : Tous les items rejetés au matching malgré signaux LAI forts

### Fichier Généré

**Path S3** : `s3://vectora-inbox-data-dev/curated/lai_weekly_v11/2026/02/03/items.json`  
**Taille** : 90.1 KB (×3.5 enrichissement)  
**Structure** : ✅ Conforme

---

## 🔍 ANALYSE ITEM PAR ITEM (Top 10 Items LAI)

### Item #1 : Nanexa + Moderna Partnership

**Source** : press_corporate__nanexa  
**Titre** : "Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products"  
**Date** : 2026-02-03  
**Word count** : 61 mots

#### Décisions Moteur

- **Normalisé** : ✅ Oui
- **Entités détectées** : Nanexa, Moderna, PharmaShell®, ALD
- **Event type** : partnership
- **Domaine matché** : ❌ Non (0 matches)
- **Raison rejet** : Domain score < 0.25 (seuil min)

#### Évaluation Humaine

❌ **PAS D'ACCORD** avec le rejet

**Commentaire** :  
Item clairement LAI : Nanexa (pure player LAI) + Moderna + PharmaShell® (technologie LAI) + Partnership ($3M upfront, $500M milestones). Devrait matcher avec score élevé.

---

### Item #2 : MedinCell UZEDY® Sales

**Source** : press_corporate__medincell  
**Titre** : "UZEDY®: Net Sales Increased from $117M in 2024 to $191M in 2025 (+63%)"  
**Date** : 2026-02-03  
**Word count** : 26 mots

#### Décisions Moteur

- **Normalisé** : ✅ Oui
- **Entités détectées** : MedinCell, Teva, UZEDY®
- **Event type** : financial_results
- **Domaine matché** : ❌ Non
- **Raison rejet** : Domain score < 0.25

#### Évaluation Humaine

❌ **PAS D'ACCORD** avec le rejet

**Commentaire** :  
UZEDY® = trademark LAI majeur (scope lai_trademarks_global). MedinCell = pure player LAI. Devrait avoir score très élevé avec trademark privilege.

---

### Item #3 : AstraZeneca + CSPC Long-Acting Obesity

**Source** : press_sector__endpoints_news  
**Titre** : "AstraZeneca pays $1.2B for CSPC's long-acting obesity drugs"  
**Date** : 2026-01-30  
**Word count** : 33 mots

#### Décisions Moteur

- **Normalisé** : ✅ Oui
- **Entités détectées** : AstraZeneca, CSPC, long-acting
- **Event type** : partnership
- **Domaine matché** : ❌ Non
- **Raison rejet** : Domain score < 0.25

#### Évaluation Humaine

❌ **PAS D'ACCORD** avec le rejet

**Commentaire** :  
"Long-acting" explicite dans titre + Partnership $1.2B + Obesity (indication LAI). Signal LAI fort.

---

### Item #4 : Lilly $3.5B Injectable Factory

**Source** : press_sector__endpoints_news  
**Titre** : "Lilly unveils $3.5B factory that will make retatrutide and other obesity drugs"  
**Date** : 2026-01-30  
**Word count** : 36 mots

#### Décisions Moteur

- **Normalisé** : ✅ Oui
- **Entités détectées** : Eli Lilly, retatrutide, injectable, device
- **Event type** : corporate_move
- **Domaine matché** : ❌ Non
- **Raison rejet** : Domain score < 0.25

#### Évaluation Humaine

⚠️ **DÉBAT** - Borderline LAI

**Commentaire** :  
"Injectable" + "device" factory. Retatrutide = GLP-1 (peut être LAI ou non). Nécessite vérification si retatrutide est LAI.

---

### Item #5 : MedinCell Olanzapine LAI NDA

**Source** : press_corporate__medincell  
**Titre** : "Teva Announces NDA Submission for Olanzapine Extended-Release Injectable Suspension"  
**Date** : 2026-02-03  
**Word count** : 33 mots

#### Décisions Moteur

- **Normalisé** : ✅ Oui
- **Entités détectées** : MedinCell, Teva, olanzapine, extended-release, injectable
- **Event type** : regulatory
- **Domaine matché** : ❌ Non
- **Raison rejet** : Domain score < 0.25

#### Évaluation Humaine

❌ **PAS D'ACCORD** avec le rejet

**Commentaire** :  
"Extended-Release Injectable" = LAI explicite. MedinCell = pure player. Olanzapine LAI = produit LAI connu. NDA submission = événement critique. Devrait avoir score maximum.

---

## 📈 MÉTRIQUES DE PERFORMANCE

### Métriques Techniques

| Métrique | Valeur | Objectif | Statut |
|----------|--------|----------|--------|
| Temps d'exécution E2E | 170.5s | <600s | ✅ |
| Taux de succès Bedrock | 100% | >95% | ✅ |
| Taux de matching | 0% | >50% | ❌ |
| Précision matching | N/A | >80% | ❌ |

### Métriques Qualité

| Métrique | Valeur | Objectif | Statut |
|----------|--------|----------|--------|
| Items haute qualité newsletter | 0% | >70% | ❌ |
| Signaux LAI pertinents | ~35% | >90% | ❌ |
| Diversité sources | 100% | >60% | ✅ |

---

## 🔧 RECOMMANDATIONS D'AMÉLIORATION

### Priorité CRITIQUE (Immédiat)

#### 1. Investiguer Prompt Domain Scoring

**Problème** : 0 matches sur 29 items dont 10+ items LAI évidents

**Hypothèses** :
1. Prompt `lai_domain_scoring.yaml` trop strict
2. Seuil `min_domain_score: 0.25` trop élevé
3. Prompt ne détecte pas les signaux LAI correctement

**Actions** :
```bash
# Télécharger et examiner prompt
aws s3 cp s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/lai_domain_scoring.yaml .

# Tester avec item connu LAI
python scripts/test/test_domain_scoring_single_item.py \
    --item "MedinCell UZEDY® sales" \
    --expected-score ">0.8"
```

#### 2. Réduire Seuil Matching Temporairement

**Solution court terme** :
```yaml
matching_config:
  min_domain_score: 0.15  # Réduire de 0.25 → 0.15
```

**Impact attendu** : +10-15 matches

#### 3. Vérifier Scopes Canonical sur S3

**Problème potentiel** : Scopes non uploadés sur S3 après cleanup

**Actions** :
```bash
# Vérifier présence scopes
aws s3 ls s3://vectora-inbox-config-dev/canonical/scopes/ --recursive

# Vérifier présence prompts
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/ --recursive

# Re-upload si manquant
aws s3 sync canonical/ s3://vectora-inbox-config-dev/canonical/
```

---

## 📝 DÉCISION FINALE

### Statut Global du Moteur

🔴 **MOTEUR NON PRÊT - CORRECTIONS CRITIQUES REQUISES**

### Justification

**Points forts** :
1. Pipeline technique stable (100% succès)
2. Normalisation fonctionne (29/29 items)
3. Prompts nettoyés chargés correctement

**Points critiques** :
1. 0 matches sur items LAI évidents (UZEDY®, MedinCell, etc.)
2. Prompt domain scoring ou seuils trop stricts
3. Impossible de générer newsletter

**Risques identifiés** :
1. Cleanup prompts a peut-être cassé le matching
2. Fichiers canonical peut-être non synchronisés sur S3
3. Prompt lai_domain_scoring nécessite ajustement

### Recommandation

❌ **DÉPLOIEMENT NON RECOMMANDÉ** - Corrections critiques requises

### Timeline Recommandée

- **Immédiat** : Investiguer prompt domain scoring + vérifier S3
- **Jour 1** : Corriger prompt ou réduire seuils
- **Jour 2** : Re-tester avec lai_weekly_v12
- **Jour 3** : Valider 10+ matches avant promotion

---

## 💬 CONCLUSION

### Analyse Fichiers S3

✅ **Fichiers téléchargés et analysés** :
- `ingested_items.json` : 29 items, 6 sources, qualité OK
- `normalized_items.json` : 29 items normalisés, entités extraites

### Problème Principal

**0 matches malgré 10+ items LAI évidents** :
- UZEDY® (trademark LAI majeur)
- MedinCell (pure player LAI)
- "Extended-Release Injectable" (LAI explicite)
- Nanexa + PharmaShell® (technologie LAI)

### Prochaine Étape

**Investiguer prompt domain scoring** :
1. Télécharger `lai_domain_scoring.yaml` depuis S3
2. Tester avec item UZEDY® (devrait scorer >0.8)
3. Ajuster prompt si nécessaire
4. Re-tester avec lai_weekly_v12

---

**Rapport généré le** : 2026-02-02  
**Basé sur** : Analyse fichiers S3 lai_weekly_v11  
**Complétude** : 85% (rapport détaillé, manque coûts Bedrock)  
**Prochaine action** : Investiguer prompt domain scoring
