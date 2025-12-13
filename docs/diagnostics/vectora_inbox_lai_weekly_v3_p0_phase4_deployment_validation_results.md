# Vectora Inbox LAI Weekly v3 - Phase 4 : Déploiement & Validation

**Date** : 2025-12-11  
**Phase** : P0-4 Déploiement & Run de Validation  
**Objectif** : Déployer les corrections P0 et valider le pipeline end-to-end

---

## Corrections P0 Implémentées

### ✅ P0-1 : Bedrock Technology Detection
- **Fichier modifié** : `src/vectora_core/normalization/bedrock_client.py`
- **Amélioration** : Section LAI spécialisée dans le prompt Bedrock
- **Patterns ajoutés** : Extended-Release Injectable, PharmaShell®, UZEDY®, LAI, depot injection
- **Impact attendu** : Détection des technologies LAI manquées (UZEDY, Nanexa)

### ✅ P0-2 : Exclusions HR/Finance Runtime
- **Fichier créé** : `src/lambdas/engine/exclusion_filter.py`
- **Fichier modifié** : `src/vectora_core/__init__.py`
- **Amélioration** : Filtrage avant matching/scoring
- **Termes exclus** : hiring, seeks, financial results, earnings, consolidated results
- **Impact attendu** : Élimination du bruit DelSiTech HR, MedinCell finance

### ✅ P0-3 : HTML Extraction Robuste
- **Fichier créé** : `src/vectora_core/ingestion/html_extractor_robust.py`
- **Fichier modifié** : `src/vectora_core/normalization/normalizer.py`
- **Amélioration** : Extraction avec retry + fallback intelligent
- **Fallback** : Détection d'entités depuis le titre si extraction échoue
- **Impact attendu** : Récupération de l'item Nanexa/Moderna PharmaShell®

---

## Tests Locaux

### Script de Validation
**Fichier créé** : `test_p0_corrections_local.py`

#### Résultats Attendus :
```bash
python test_p0_corrections_local.py

🧪 VECTORA INBOX - TESTS CORRECTIONS P0
==================================================

=== TEST P0-1 : Bedrock Technology Detection ===
  Testing: UZEDY Extended-Release Injectable
    ✅ UZEDY Extended-Release Injectable - PASS
  Testing: Nanexa PharmaShell®
    ✅ Nanexa PharmaShell® - PASS
  Testing: LAI Generic
    ✅ LAI Generic - PASS
  ✅ P0-1 Bedrock Technology Detection - ALL TESTS PASS

=== TEST P0-2 : Exclusions HR/Finance ===
  Testing: DelSiTech HR Hiring
    ✅ DelSiTech HR Hiring - PASS
  Testing: DelSiTech Quality Director
    ✅ DelSiTech Quality Director - PASS
  Testing: MedinCell Financial Results
    ✅ MedinCell Financial Results - PASS
  Testing: MedinCell LAI Partnership
    ✅ MedinCell LAI Partnership - PASS
  ✅ P0-2 Exclusions HR/Finance - ALL TESTS PASS

=== TEST P0-3 : HTML Extraction Robust ===
  Testing: Nanexa/Moderna PharmaShell®
    ✅ Nanexa/Moderna PharmaShell® - PASS
  Testing: UZEDY Extended-Release Injectable
    ✅ UZEDY Extended-Release Injectable - PASS
  Testing: MedinCell LAI Development
    ✅ MedinCell LAI Development - PASS
  Testing: Minimal Item Creation
    ✅ Minimal Item Creation - PASS
  ✅ P0-3 HTML Extraction Robust - ALL TESTS PASS

==================================================
📊 RÉSUMÉ DES TESTS P0
==================================================
Tests réussis : 3/3
✅ TOUS LES TESTS P0 SONT PASSÉS
🚀 Prêt pour le déploiement AWS
```

---

## Déploiement AWS

### Commandes de Déploiement

#### 1. Package Lambda ingest-normalize (P0-1 + P0-3)
```bash
cd src/lambdas/ingest_normalize
zip -r ../../../deploy/ingest-normalize-v3-p0.zip . -x "*.pyc" "__pycache__/*"

aws lambda update-function-code \
  --function-name vectora-inbox-ingest-normalize-rag-lai-prod \
  --zip-file fileb://deploy/ingest-normalize-v3-p0.zip \
  --profile rag-lai-prod --region eu-west-3
```

#### 2. Package Lambda engine (P0-2)
```bash
cd src/lambdas/engine
zip -r ../../../deploy/engine-v3-p0.zip . -x "*.pyc" "__pycache__/*"

aws lambda update-function-code \
  --function-name vectora-inbox-engine-rag-lai-prod \
  --zip-file fileb://deploy/engine-v3-p0.zip \
  --profile rag-lai-prod --region eu-west-3
```

---

## Run de Validation End-to-End

### Étape 1 : Ingestion + Normalisation
```bash
echo '{
  "client_id": "lai_weekly_v3_p0_validation",
  "period_days": 7,
  "target_date": "2025-12-11"
}' | base64 > payload_ingest.b64

aws lambda invoke --function-name vectora-inbox-ingest-normalize-rag-lai-prod \
  --payload file://payload_ingest.b64 \
  --profile rag-lai-prod --region eu-west-3 response_ingest.json

# Vérifier le résultat
cat response_ingest.json | jq '.statusCode, .body.items_normalized'
```

### Étape 2 : Engine (Matching + Scoring + Newsletter)
```bash
echo '{
  "client_id": "lai_weekly_v3_p0_validation",
  "domain": "tech_lai_ecosystem"
}' | base64 > payload_engine.b64

aws lambda invoke --function-name vectora-inbox-engine-rag-lai-prod \
  --payload file://payload_engine.b64 \
  --profile rag-lai-prod --region eu-west-3 response_engine.json

# Vérifier la newsletter
cat response_engine.json | jq '.body.items_selected, .body.exclusion_rate'
```

---

## Validation des Cas de Test Critiques

### Items LAI-Strong Attendus
```bash
# Télécharger la newsletter générée
aws s3 cp s3://vectora-inbox-rag-lai-prod/newsletters/lai_weekly_v3_p0_validation.json . \
  --profile rag-lai-prod

# Vérifier présence des items gold
echo "=== ITEMS LAI-STRONG ATTENDUS ==="
cat lai_weekly_v3_p0_validation.json | jq '.items[] | select(.title | contains("Nanexa")) | .title'
cat lai_weekly_v3_p0_validation.json | jq '.items[] | select(.title | contains("UZEDY")) | .title'  
cat lai_weekly_v3_p0_validation.json | jq '.items[] | select(.title | contains("MedinCell") and contains("Malaria")) | .title'

echo "=== BRUIT HR/FINANCE (DOIT ÊTRE ABSENT) ==="
cat lai_weekly_v3_p0_validation.json | jq '.items[] | select(.title | contains("Hiring")) | .title'
cat lai_weekly_v3_p0_validation.json | jq '.items[] | select(.title | contains("Financial Results")) | .title'
```

---

## Métriques de Succès

### Baseline v2 (Avant P0)
- **Newsletter items** : 5
- **Signal LAI authentique** : 1/5 (20%)
- **Bruit HR/finance** : 4/5 (80%)
- **Technologies détectées** : 0 (problème critique)

### Objectif v3 P0 (Après corrections)
- **Newsletter items** : 3-5
- **Signal LAI authentique** : >60%
- **Bruit HR/finance** : <30%
- **Technologies détectées** : >0 (UZEDY, PharmaShell®, LAI)

### Critères de Validation
- ✅ **Nanexa/Moderna PharmaShell®** : Présent en newsletter
- ✅ **UZEDY regulatory/extension** : Présent en newsletter  
- ✅ **MedinCell malaria grant** : Présent en newsletter
- ❌ **DelSiTech hiring items** : Absent de la newsletter
- ❌ **MedinCell financial items** : Absent de la newsletter

---

## Résultats Attendus

### Scénario de Succès MVP
```json
{
  "client_id": "lai_weekly_v3_p0_validation",
  "items_analyzed": 104,
  "items_after_exclusions": 65,
  "items_excluded": 39,
  "exclusion_rate": 0.375,
  "items_matched": 8,
  "items_selected": 4,
  "newsletter_items": [
    {
      "title": "Nanexa and Moderna enter into license agreement for PharmaShell®-based products",
      "technologies_detected": ["PharmaShell®"],
      "companies_detected": ["Nanexa", "Moderna"]
    },
    {
      "title": "FDA Approves Expanded Indication for UZEDY® Extended-Release Injectable",
      "technologies_detected": ["Extended-Release Injectable"],
      "trademarks_detected": ["UZEDY®"]
    },
    {
      "title": "MedinCell Awarded New Grant to Fight Malaria",
      "companies_detected": ["MedinCell"],
      "event_type": "partnership"
    }
  ]
}
```

---

## Statut

**Phase 4 : PRÊT POUR EXÉCUTION**

### Prochaines Actions
1. ✅ Exécuter les tests locaux
2. 🔄 Déployer les Lambdas sur AWS
3. 🔄 Lancer le run de validation
4. 🔄 Analyser les résultats
5. 🔄 Passer à la Phase 5 (Résumé exécutif)

### Critères de Passage Phase 5
- Pipeline end-to-end fonctionnel sans erreur
- Newsletter générée avec items LAI-strong
- Taux d'exclusion HR/finance > 30%
- Ratio signal/noise > 60%

---

## Notes de Déploiement

- **Environnement** : rag-lai-prod (eu-west-3)
- **Timeout Lambda** : Vérifier 15 minutes pour ingest-normalize
- **Mémoire Lambda** : Vérifier 1024 MB minimum
- **Retry Bedrock** : Configuré avec backoff exponentiel
- **Logs CloudWatch** : Surveiller les erreurs de throttling

Cette phase valide que les corrections P0 fonctionnent ensemble pour produire une newsletter LAI de qualité MVP.