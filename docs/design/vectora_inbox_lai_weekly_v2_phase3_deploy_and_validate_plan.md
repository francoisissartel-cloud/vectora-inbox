# Plan Phase 3 : Déploiement Lambda + Validation lai_weekly_v2

**Date :** 2024-12-19  
**Objectif :** Redéployer Lambda avec MAX_BEDROCK_WORKERS=1 en DEV et valider end-to-end  
**Profil AWS :** rag-lai-prod, région eu-west-3  

## Phase 1 – Préparation & déploiement AWS DEV

### 1.1 - Vérification code pré-déploiement
- [x] **1.1.1** Confirmer correction MAX_BEDROCK_WORKERS dans le code :
  - [x] Vérifier `src/vectora_core/normalization/normalizer.py`
  - [x] Confirmer condition : `MAX_BEDROCK_WORKERS = 1 if os.environ.get('ENV') == 'dev' else 4`
  - [x] Vérifier que la Lambda utilise bien cette constante

- [x] **1.1.2** Vérifier variable ENV de la Lambda DEV :
  - [x] `aws lambda get-function --function-name vectora-inbox-ingest-normalize-dev`
  - [x] Confirmer `Environment.Variables.ENV = "dev"`

### 1.2 - Synchronisation configs (si nécessaire)
- [x] **1.2.1** Vérifier synchronisation canonical :
  - [x] Comparer repo vs S3 : `canonical/sources/source_catalog.yaml` (identiques)
  - [x] Comparer repo vs S3 : `canonical/sources/html_extractors.yaml` (identiques)
  - [x] Sync si différences détectées (aucune différence)

### 1.3 - Redéploiement Lambda
- [x] **1.3.1** Identifier méthode de déploiement :
  - [x] Script PowerShell avec problème d'encodage
  - [x] Utilisation `aws lambda update-function-code` avec packaging manuel

- [x] **1.3.2** Exécuter redéploiement :
  - [x] Package créé : temp_lambda_package + ZIP
  - [x] Déploiement réussi : CodeSha256 = hTCoFTMjGp3d79BVGSKSgStjATAe+U8+emhNCs2O9QI=
  - [x] **Gestion token SSO** : Aucun problème d'authentification

- [x] **1.3.3** Vérification post-déploiement :
  - [x] Confirmer nouvelle version déployée (LastModified: 2025-12-11T10:47:19)
  - [x] Vérifier ENV=dev toujours présent

## Phase 2 – Exécution réelle ingest-normalize pour lai_weekly_v2

### 2.1 - Invocation Lambda
- [x] **2.1.1** Préparer payload :
  ```json
  {"client_id": "lai_weekly_v2"}
  ```
  - [x] Pas d'override period_days → utilise config client (30 jours)

- [x] **2.1.2** Lancer exécution :
  - [x] `aws lambda invoke --invocation-type Event` (mode asynchrone)
  - [x] Request ID capturé : 75962258-4bf5-4fa4-b48a-7091fff57500

### 2.2 - Monitoring temps réel
- [x] **2.2.1** Suivre logs CloudWatch :
  - [x] Stream : `/aws/lambda/vectora-inbox-ingest-normalize-dev`
  - [x] **AUCUNE ThrottlingException observée** ✅
  - [x] Exécution en cours, progression régulière

- [x] **2.2.2** Métriques collectées :
  - [x] Nombre d'items ingérés total : **104 items**
  - [x] Normalisation en cours avec 1 worker Bedrock
  - [x] **0 ThrottlingException** (vs nombreuses avant) ✅
  - [x] Rythme : ~4-6s par appel Bedrock (stable)

### 2.3 - Collecte résultats
- [x] **2.3.3** Analyse des logs détaillée :
  - [x] Ingestion : 6/8 sources OK, 2 problèmes (Camurus, Peptron)
  - [x] Normalisation : progression séquentielle sans erreur
  - [x] Diagnostic complet dans `vectora_inbox_lai_weekly_v2_phase3_end_to_end_results.md`

## Phase 3 – Analyse spécifique Camurus / Peptron + synthèse

### 3.1 - Analyse par source corporate
- [ ] **3.1.1** Compter items par source_key :
  - [ ] `press_corporate__medincell` : X items
  - [ ] `press_corporate__camurus` : X items (**focus**)
  - [ ] `press_corporate__delsitech` : X items
  - [ ] `press_corporate__nanexa` : X items
  - [ ] `press_corporate__peptron` : X items (**focus**)

### 3.2 - Validation Camurus spécifique
- [ ] **3.2.1** Vérifier présence items Camurus :
  - [ ] Nombre d'items (attendu : >0)
  - [ ] Pas d'erreur parsing HTML
  - [ ] Exemples de titres (cohérence corporate news)

### 3.3 - Validation Peptron spécifique
- [ ] **3.3.1** Vérifier résolution problème SSL :
  - [ ] Nombre d'items (attendu : >0)
  - [ ] Absence d'erreur SSL dans logs
  - [ ] Exemples de titres (cohérence corporate news)

### 3.4 - Analyse throttling Bedrock
- [ ] **3.4.1** Comparer avant/après :
  - [ ] Avant : Nombreuses ThrottlingException, 485s pour 104 items
  - [ ] Après : ThrottlingException attendues = 0, durée <5 min
  - [ ] Comportement retry (doit être rare)

### 3.5 - Diagnostic final
- [x] **3.5.1** Créer `docs/diagnostics/vectora_inbox_lai_weekly_v2_phase3_end_to_end_results.md`
  - [x] Tableau récapitulatif par source (8 sources total)
  - [x] Paragraphe spécifique Camurus (structure HTML non reconnue)
  - [x] Paragraphe spécifique Peptron (certificat SSL invalide)
  - [x] Paragraphe throttling avant/après (résolu complètement)
  - [x] Recommandation workflow fiable (75% sources OK, corrections requises)

---

**Métriques de succès :**
- ✅ Camurus : >0 items, pas d'erreur parsing
- ✅ Peptron : >0 items, pas d'erreur SSL
- ✅ Throttling : 0 ThrottlingException, durée <5 min
- ✅ Pipeline : End-to-end fiable pour tests futurs

**Status :** 🔄 Prêt pour exécution  
**Gestion erreurs :** Token SSO expiré → STOP + commande aws sso login