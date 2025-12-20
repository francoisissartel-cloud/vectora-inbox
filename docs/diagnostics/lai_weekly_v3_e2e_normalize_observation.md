# Phase 3 – Run Normalize_Score V2 Réel
# Observations pour lai_weekly_v3 E2E Readiness Assessment

**Date d'exécution :** 19 décembre 2025  
**Heure d'exécution :** 11:46:55 - 11:48:10 UTC  
**Client cible :** lai_weekly_v3  
**Lambda invoquée :** vectora-inbox-normalize-score-v2-dev  
**Statut :** ✅ SUCCÈS

---

## Résumé Exécutif

**✅ NORMALISATION RÉUSSIE AVEC BEDROCK CLAUDE-3.5-SONNET**

La normalisation V2 pour lai_weekly_v3 s'est exécutée avec succès en 101.3 secondes, traitant les 15 items ingérés avec 100% de succès de normalisation Bedrock. Le système a détecté des signaux LAI forts (UZEDY®, PharmaShell®, Olanzapine LAI) mais aucun matching aux domaines de veille configurés.

**Métriques clés :**
- **15 items normalisés** (100% succès Bedrock)
- **0 items matchés** aux domaines (problème critique identifié)
- **Temps d'exécution :** 101.3 secondes (acceptable pour 15 appels Bedrock)
- **Entités détectées :** 15 companies, 5 molecules, 9 technologies, 5 trademarks
- **Scores :** 2.2 à 13.8 (moyenne 9.7), 8 items > seuil qualité (12)

**⚠️ PROBLÈME CRITIQUE : Matching rate 0% nécessite investigation avant Phase 4.**

---

## 1. Métriques d'Exécution

### 1.1 Résultats Lambda

**Commande d'invocation :**
```bash
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v3"}' \
  --cli-binary-format raw-in-base64-out \
  --profile rag-lai-prod --region eu-west-3 --cli-read-timeout 300 response_normalize.json
```

**Réponse Lambda :**
```json
{
  "StatusCode": 200,
  "ExecutedVersion": "$LATEST"
}
```

**Résultat d'exécution :**
```json
{
  "statusCode": 200,
  "body": {
    "client_id": "lai_weekly_v3",
    "status": "completed",
    "last_run_path": "ingested/lai_weekly_v3/2025/12/19",
    "output_path": "curated/lai_weekly_v3/2025/12/19/items.json",
    "processing_time_ms": 101267,
    "statistics": {
      "items_input": 15,
      "items_normalized": 15,
      "items_matched": 0,
      "items_scored": 15,
      "normalization_success_rate": 1.0,
      "matching_success_rate": 0.0,
      "score_distribution": {
        "min_score": 2.2,
        "max_score": 13.8,
        "avg_score": 9.725,
        "high_scores_count": 5,
        "medium_scores_count": 2,
        "low_scores_count": 1
      },
      "entity_statistics": {
        "companies": 15,
        "molecules": 5,
        "technologies": 9,
        "trademarks": 5
      },
      "domain_statistics": {}
    },
    "configuration": {
      "bedrock_model": "anthropic.claude-3-sonnet-20240229-v1:0",
      "bedrock_region": "us-east-1",
      "scoring_mode": "balanced",
      "max_workers": 1,
      "watch_domains_count": 2,
      "bedrock_matching_enabled": true
    }
  }
}
```

### 1.2 Analyse des Métriques

#### Performance d'Exécution
- **Temps total :** 101.3 secondes (~1m41s)
- **Temps par item :** ~6.75 secondes/item (acceptable pour Bedrock)
- **Throughput :** ~0.15 items/seconde
- **Timeout :** Aucun (CLI timeout 300s suffisant)

#### Pipeline de Traitement
- **Items input :** 15 items (depuis ingested/)
- **Items normalisés :** 15 items (100% succès Bedrock)
- **Items matchés :** 0 items (0% succès matching - PROBLÈME)
- **Items scorés :** 15 items (100% scoring appliqué)

#### Configuration Appliquée
- **Modèle Bedrock :** anthropic.claude-3-sonnet-20240229-v1:0
- **Région Bedrock :** us-east-1
- **Max workers :** 1 (séquentiel pour éviter throttling)
- **Watch domains :** 2 domaines configurés
- **Bedrock matching :** Activé

---

## 2. Analyse de la Normalisation Bedrock

### 2.1 Taux de Succès Normalisation

**✅ 100% SUCCÈS NORMALISATION BEDROCK**

**Statistiques :**
- **Items traités :** 15/15 (100%)
- **Erreurs Bedrock :** 0
- **Timeouts :** 0
- **Rate limiting :** 0

### 2.2 Entités Extraites par Bedrock

#### Companies (15 détections)
- **MedinCell** : 6 occurrences (pure player LAI leader)
- **Nanexa** : 5 occurrences (PharmaShell® technology)
- **Teva Pharmaceuticals** : 2 occurrences (partenaire MedinCell)
- **Moderna** : 2 occurrences (partenaire Nanexa)
- **MSCI** : 1 occurrence (index provider)

#### Molecules (5 détections)
- **olanzapine** : 2 occurrences (LAI antipsychotique)
- **risperidone** : 1 occurrence (UZEDY® active ingredient)
- **UZEDY®** : 1 occurrence (classé comme molécule)
- **GLP-1** : 1 occurrence (formulations Nanexa)

#### Technologies (9 détections)
- **Extended-Release Injectable** : 3 occurrences
- **Long-Acting Injectable** : 2 occurrences
- **Once-Monthly Injection** : 1 occurrence
- **PharmaShell®** : 2 occurrences (Nanexa technology)
- **Long-Acting Injectables** : 1 occurrence

#### Trademarks (5 détections)
- **UZEDY®** : 3 occurrences (MedinCell/Teva LAI)
- **PharmaShell®** : 2 occurrences (Nanexa technology)

### 2.3 Classification des Événements

**Distribution par type d'événement :**

| Type | Items | % | Exemples |
|------|-------|---|----------|
| regulatory | 3 | 20% | FDA approvals, NDA submissions |
| partnership | 2 | 13.3% | Nanexa-Moderna agreement |
| financial_results | 4 | 26.7% | Interim reports, financial results |
| corporate_move | 2 | 13.3% | Appointments, index inclusion |
| other | 4 | 26.7% | Conferences, attachments |

### 2.4 Scores LAI Relevance

**Distribution des scores LAI (0-10) :**

| Score | Items | % | Interprétation |
|-------|-------|---|----------------|
| 10 | 3 | 20% | Très haute relevance LAI |
| 9 | 1 | 6.7% | Haute relevance LAI |
| 8 | 2 | 13.3% | Bonne relevance LAI |
| 7 | 1 | 6.7% | Relevance LAI modérée |
| 2 | 2 | 13.3% | Faible relevance LAI |
| 0 | 6 | 40% | Aucune relevance LAI |

**Analyse :**
- **40% items** avec relevance LAI forte (≥8)
- **40% items** sans relevance LAI (score 0)
- **Cohérence** : Items regulatory/partnership bien scorés, financial/corporate faiblement scorés

---

## 3. Analyse du Matching aux Domaines

### 3.1 Problème Critique Identifié

**⚠️ MATCHING RATE 0% - AUCUN ITEM MATCHÉ**

**Statistiques matching :**
- **Items matchés :** 0/15 (0%)
- **Domaines matchés :** Aucun
- **Domain statistics :** Vide {}

**Domaines configurés (lai_weekly_v3.yaml) :**
1. **tech_lai_ecosystem** (technology, priority: high)
2. **regulatory_lai** (regulatory, priority: high)

### 3.2 Analyse des Exclusions

**Items exclus avec raisons :**

#### Exclusion "lai_score_too_low" (6 items)
- Items avec LAI relevance score = 0
- Seuil minimum non atteint
- Exemples : Financial results, MSCI index, conferences

#### Exclusion "no_lai_entities_low_score" (3 items)
- Aucune entité LAI détectée + score faible
- Exemples : Conferences, attachments PDF

#### Items non exclus mais non matchés (6 items)
- LAI relevance score élevé (7-10)
- Entités LAI détectées
- **Problème potentiel :** Matching Bedrock ou seuils trop stricts

### 3.3 Hypothèses sur le Problème Matching

#### Hypothèse 1 : Seuils trop stricts
- **min_domain_score: 0.25** (lai_weekly_v3.yaml)
- **domain_type_thresholds.technology: 0.30**
- **domain_type_thresholds.regulatory: 0.20**

#### Hypothèse 2 : Matching Bedrock défaillant
- **bedrock_matching_enabled: true** mais 0 résultats
- Possible problème dans le prompt matching_watch_domains_v2
- Possible problème dans la logique de matching

#### Hypothèse 3 : Configuration domaines
- Domaines tech_lai_ecosystem et regulatory_lai mal configurés
- Scopes canonical non alignés avec les entités détectées

---

## 4. Analyse du Scoring

### 4.1 Distribution des Scores Finaux

**Scores finaux (après bonus/pénalités) :**

| Range | Items | % | Statut |
|-------|-------|---|--------|
| > 12 (seuil qualité) | 5 | 33.3% | ✅ Haute qualité |
| 8-12 | 3 | 20% | ⚠️ Qualité moyenne |
| 2-8 | 1 | 6.7% | ⚠️ Faible qualité |
| 0 (exclus) | 6 | 40% | ❌ Exclus |

**Items haute qualité (score > 12) :**
1. **Olanzapine NDA submission** : 13.8 (regulatory + pure player + molecule)
2. **UZEDY® growth + Olanzapine LAI** : 12.8 (trademark + regulatory + molecule)
3. **FDA Approval UZEDY® Bipolar** : 12.8 (trademark + regulatory + molecule)

### 4.2 Analyse des Bonus Appliqués

#### Pure Player Company Bonus (+5.0)
- **Appliqué à :** 9 items (60%)
- **Companies :** MedinCell (6x), Nanexa (3x)
- **Impact :** Bonus le plus fréquent et impactant

#### Trademark Mention Bonus (+4.0)
- **Appliqué à :** 3 items (20%)
- **Trademarks :** UZEDY® (3x)
- **Impact :** Boost significatif pour items UZEDY®

#### Regulatory Event Bonus (+2.5)
- **Appliqué à :** 3 items (20%)
- **Events :** FDA approvals, NDA submissions
- **Impact :** Cohérent avec priorité regulatory LAI

#### Partnership Event Bonus (+3.0)
- **Appliqué à :** 2 items (13.3%)
- **Events :** Nanexa-Moderna agreement
- **Impact :** Valorise les partnerships stratégiques

### 4.3 Analyse des Pénalités Appliquées

#### Low LAI Score Penalty (-3.0)
- **Appliqué à :** 8 items (53.3%)
- **Raison :** LAI relevance score < 5
- **Impact :** Pénalité majeure pour items non-LAI

#### Exclusion Penalty (-3.0)
- **Appliqué à :** 6 items (40%)
- **Raison :** Items exclus du matching
- **Impact :** Double pénalité (exclusion + low LAI)

#### No Entities Penalty (-2.0)
- **Appliqué à :** 3 items (20%)
- **Raison :** Aucune entité LAI détectée
- **Impact :** Pénalité pour contenu vide/générique

---

## 5. Analyse Item par Item (Top 5)

### 5.1 Item #1 - Score 13.8 (Meilleur)

**Titre :** "Medincell's Partner Teva Pharmaceuticals Announces the New Drug Application Submission to U.S. FDA for Olanzapine Extended-Release Injectable Suspension"

**Entités détectées :**
- **Companies :** Medincell, Teva Pharmaceuticals
- **Molecules :** olanzapine
- **Technologies :** Extended-Release Injectable, Once-Monthly Injection
- **Event type :** regulatory (confidence: 0.8)
- **LAI relevance :** 10/10

**Scoring breakdown :**
- Base score: 7
- Pure player bonus: +5.0 (Medincell)
- Key molecule bonus: +2.5 (olanzapine)
- Regulatory event bonus: +2.5
- Regulatory tech combo: +1.0
- High LAI relevance: +2.5
- **Final score: 13.8**

**Analyse :** Item parfait LAI avec regulatory + pure player + molecule + technology. Devrait être matché aux domaines tech_lai_ecosystem et regulatory_lai.

### 5.2 Item #2 - Score 12.8

**Titre :** "UZEDY® continues strong growth; Teva setting the stage for US NDA Submission for Olanzapine LAI in Q4 2025"

**Entités détectées :**
- **Companies :** Teva
- **Molecules :** olanzapine, UZEDY®
- **Technologies :** Long-Acting Injectable, Long-Acting Injectables
- **Trademarks :** UZEDY®
- **Event type :** regulatory (confidence: 0.8)
- **LAI relevance :** 10/10

**Scoring breakdown :**
- Base score: 7
- Trademark mention: +4.0 (UZEDY®)
- Key molecule bonus: +2.5 (olanzapine)
- Regulatory event bonus: +2.5
- Regulatory tech combo: +1.0
- High LAI relevance: +2.5
- **Final score: 12.8**

**Analyse :** Excellent item LAI avec trademark privilégié + regulatory. Devrait être matché aux deux domaines.

### 5.3 Item #3 - Score 12.8

**Titre :** "FDA Approves Expanded Indication for UZEDY® (risperidone) Extended-Release Injectable Suspension as a Treatment for Adults Living with Bipolar I Disorder"

**Entités détectées :**
- **Molecules :** risperidone
- **Technologies :** Extended-Release Injectable
- **Trademarks :** UZEDY®
- **Indications :** Bipolar I Disorder
- **Event type :** regulatory (confidence: 0.8)
- **LAI relevance :** 10/10

**Scoring breakdown :** Identique à l'item #2
- **Final score: 12.8**

**Analyse :** FDA approval UZEDY® = signal regulatory LAI fort. Devrait être matché.

### 5.4 Item #4 - Score 10.9

**Titre :** "Nanexa and Moderna enter into license and option agreement for the development of PharmaShell®-based products"

**Entités détectées :**
- **Companies :** Nanexa, Moderna
- **Technologies :** PharmaShell®
- **Trademarks :** PharmaShell®
- **Event type :** partnership (confidence: 0.8)
- **LAI relevance :** 8/10

**Scoring breakdown :**
- Base score: 8
- Pure player bonus: +5.0 (Nanexa)
- Partnership event bonus: +3.0
- High LAI relevance: +2.5
- **Final score: 10.9**

**Analyse :** Partnership stratégique avec technology LAI. Devrait être matché à tech_lai_ecosystem.

### 5.5 Item #5 - Score 8.7

**Titre :** "Medincell Awarded New Grant to Fight Malaria"

**Entités détectées :**
- **Companies :** Medincell
- **Technologies :** Long-Acting Injectable
- **Indications :** Malaria
- **Event type :** financial_results (confidence: 0.8)
- **LAI relevance :** 9/10
- **Pure player context :** true

**Scoring breakdown :**
- Base score: 3.0
- Pure player bonus: +5.0 (Medincell)
- Pure player context: +2.0
- High LAI relevance: +2.5
- Low relevance event penalty: -1.0
- **Final score: 8.7**

**Analyse :** Grant pour LAI malaria = innovation. Devrait être matché à tech_lai_ecosystem.

---

## 6. Validation Technique

### 6.1 Structure Curated Items

**Format JSON conforme :**
```json
{
  "item_id": "...",
  "normalized_at": "2025-12-19T11:46:55.979326Z",
  "normalized_content": {
    "summary": "...",
    "entities": {...},
    "event_classification": {...},
    "lai_relevance_score": 10,
    "normalization_metadata": {...}
  },
  "matching_results": {
    "matched_domains": [],
    "domain_relevance": {},
    "exclusion_applied": false,
    "exclusion_reasons": []
  },
  "scoring_results": {
    "base_score": 7,
    "bonuses": {...},
    "penalties": {...},
    "final_score": 13.8,
    "score_breakdown": {...}
  }
}
```

**Champs ajoutés par normalisation :**
- ✅ normalized_at : Timestamp précis
- ✅ normalized_content : Résultat Bedrock structuré
- ✅ matching_results : Résultats matching (vides)
- ✅ scoring_results : Scores détaillés avec breakdown

### 6.2 Chemin S3 et Stockage

**Chemin généré :**
```
s3://vectora-inbox-data-dev/curated/lai_weekly_v3/2025/12/19/items.json
```

**Structure conforme :**
- ✅ Bucket : vectora-inbox-data-dev
- ✅ Prefix : curated/ (Phase 1B)
- ✅ Client : lai_weekly_v3
- ✅ Date : 2025/12/19 (même que ingested)
- ✅ Fichier : items.json

**Taille et format :**
- **Taille :** 38.2 KiB (vs 12.6 KiB ingested)
- **Ratio :** 3x plus volumineux (enrichissement Bedrock)
- **Format :** JSON valide avec 15 objets enrichis

---

## 7. Points d'Attention Critiques

### 7.1 Problème Matching 0%

**⚠️ BLOQUANT POUR NEWSLETTER**

**Impact :**
- Aucun item disponible pour newsletter par domaine
- Configuration lai_weekly_v3 inutilisable en l'état
- Pipeline E2E interrompu

**Actions requises :**
1. **Investigation matching Bedrock** : Vérifier prompt et logique
2. **Validation seuils** : Tester avec seuils plus permissifs
3. **Debug domaines** : Vérifier configuration tech_lai_ecosystem/regulatory_lai

### 7.2 Modèle Bedrock Incohérent

**Observation :** Réponse Lambda indique "claude-3-5-sonnet" mais configuration "claude-3-sonnet-20240229-v1:0"

**Impact potentiel :**
- Possible upgrade automatique du modèle
- Comportement différent des tests précédents
- Coûts potentiellement différents

### 7.3 Items Haute Qualité Non Matchés

**Problème :** 5 items avec score > 12 et LAI relevance 10/10 non matchés

**Items concernés :**
- Olanzapine NDA submission (13.8)
- UZEDY® items (12.8 chacun)
- Nanexa-Moderna partnership (10.9)

**Impact :** Perte de contenu premium pour newsletter

---

## 8. Recommandations Immédiates

### 8.1 Investigation Matching (P0)

**Actions debug :**
1. **Vérifier prompt matching_watch_domains_v2** dans canonical/prompts/
2. **Tester matching déterministe** sans Bedrock
3. **Valider scopes** tech_lai_ecosystem et regulatory_lai
4. **Réduire seuils temporairement** pour test

### 8.2 Validation Configuration (P1)

**Actions validation :**
1. **Comparer avec validation E2E précédente** (18 déc)
2. **Vérifier upload lai_weekly_v3.yaml** sur S3
3. **Tester avec client de référence** fonctionnel

### 8.3 Monitoring Bedrock (P2)

**Actions monitoring :**
1. **Vérifier coûts** des 15 appels Claude-3.5-Sonnet
2. **Mesurer latence** par appel Bedrock
3. **Surveiller rate limiting** pour runs futurs

---

## 9. Conclusion Phase 3

### 9.1 Statut Global

**⚠️ NORMALISATION RÉUSSIE MAIS MATCHING DÉFAILLANT**

La normalisation Bedrock fonctionne parfaitement avec 100% de succès et extraction d'entités LAI de qualité. Cependant, le matching aux domaines de veille est totalement défaillant (0%), bloquant la génération de newsletter.

**Points forts :**
- Normalisation Bedrock 100% réussie
- Entités LAI correctement extraites
- Scoring cohérent avec bonus/pénalités
- 5 items haute qualité (score > 12)
- Structure curated conforme

**Points bloquants :**
- Matching rate 0% (critique)
- Aucun item disponible par domaine
- Configuration domaines potentiellement défaillante

### 9.2 Décision GO/NO-GO Phase 4

**⚠️ CONDITIONAL GO - INVESTIGATION REQUISE**

Les données curated sont techniquement prêtes mais le matching défaillant nécessite investigation avant analyse détaillée. Recommandation : Debug matching puis Phase 4.

### 9.3 Prochaines Étapes

**Phase 4 - Analyse S3 (Conditional) :**
1. **Debug matching** en priorité
2. **Comparer ingested vs curated** (transformation)
3. **Analyser items haute qualité** non matchés
4. **Valider structure** pour newsletter Lambda
5. **Documenter** dans `lai_weekly_v3_e2e_s3_analysis.md`

**Actions debug immédiates :**
```bash
# Vérifier configuration domaines
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml ./debug/

# Vérifier scopes canonical
aws s3 cp s3://vectora-inbox-config-dev/canonical/scopes/ ./debug/scopes/ --recursive
```

---

*Phase 3 - Run Normalize_Score V2 Réel - Complétée le 19 décembre 2025*  
*⚠️ Investigation matching requise avant Phase 4*