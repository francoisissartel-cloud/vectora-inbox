# Plan de Correction Vectora Inbox : Peptron & Camurus + Throttling Bedrock

**Date :** 2024-12-19  
**Objectif :** Corrections ciblées sur Corporate HTML (Peptron & Camurus) et Throttling Bedrock en DEV  
**Profil AWS :** rag-lai-prod, région eu-west-3  

## A. Corporate HTML : Peptron & Camurus

### A1 - Diagnostic repo ↔ AWS
- [ ] **A1.1** Vérifier dans le repo les fichiers clés :
  - [ ] `src/vectora_core/ingestion/parser.py` (parser HTML générique)
  - [ ] `src/vectora_core/ingestion/html_extractor.py` (extracteurs spécifiques)
  - [ ] `canonical/sources/source_catalog.yaml` (définitions Camurus/Peptron)
  - [ ] `canonical/sources/html_extractors.yaml` (extracteurs spécifiques)
- [ ] **A1.2** Vérifier en AWS DEV :
  - [ ] Lambda `vectora-inbox-ingest-normalize-dev` packagée avec parser/html_extractor
  - [ ] Bucket config S3 contient les versions à jour des canonical
- [ ] **A1.3** Documenter dans `docs/diagnostics/vectora_inbox_corporate_peptron_camurus_fix_results.md`

### A2 - Corrections de sync & config
- [x] **A2.1** Synchroniser si décalage détecté :
  - [x] Sync canonical vers bucket config DEV (déjà synchronisé)
  - [x] Re-package Lambda ingest-normalize (correction MAX_BEDROCK_WORKERS)
  - [ ] Redéploiement stack/runtime requis
- [x] **A2.2** Vérifier configurations spécifiques :
  - [x] Peptron : stratégie SSL (ssl_verify: false dans html_extractors.yaml)
  - [x] Camurus : extractor spécifique dans html_extractors.yaml
- [x] **A2.3** Mettre à jour diagnostic A2

### A3 - Test ciblé Corporate HTML (DEV)
- [ ] **A3.1** Lancer exécution limitée aux 5 sources corporate LAI :
  - [ ] medincell, camurus, delsitech, nanexa, peptron
  - [ ] Utiliser mode debug/paramètre restrictif si disponible
- [ ] **A3.2** Vérifier résultats :
  - [ ] Items Camurus (≠ 0)
  - [ ] Peptron sans erreur SSL
  - [ ] Volume réaliste d'items par source
- [ ] **A3.3** Documenter résultats & métriques dans diagnostic A3

## B. Throttling Bedrock - ingest-normalize (DEV)

### B1 - Diagnostic Throttling en DEV
- [x] **B1.1** Analyser logs CloudWatch `vectora-inbox-ingest-normalize-dev` :
  - [x] Volume d'items à normaliser (104 items lai_weekly_v2)
  - [x] Nombre de ThrottlingException (nombreuses)
  - [x] Durée totale d'exécution (485 secondes)
  - [x] Nombre de retries effectués (centaines)
- [x] **B1.2** Vérifier code Lambda dev :
  - [x] Valeur actuelle MAX_BEDROCK_WORKERS (4 - problème identifié)
  - [x] Présence retry/backoff (implémenté)
  - [x] Logique chunking d'items (ThreadPoolExecutor)
- [x] **B1.3** Vérifier configuration Lambda AWS :
  - [x] ReservedConcurrentExecutions (impossible - limites compte)
  - [x] Confirmation environnement DEV
- [x] **B1.4** Documenter dans `docs/diagnostics/vectora_inbox_ingest_throttling_fix_results.md`

### B2 - Corrections P0 sur parallélisation & volume
- [x] **B2.1** Forcer MAX_BEDROCK_WORKERS=1 en DEV :
  - [x] Condition sur Env == dev dans code/config
- [x] **B2.2** Vérifier/rétablir ReservedConcurrentExecutions=1 (impossible)
- [x] **B2.3** Optionnel DEV-only : limite volume items :
  - [x] Analyse : pas nécessaire pour 104 items
  - [x] Code prêt si besoin futur
  - [x] Documenter limitation DEV vs PROD
- [x] **B2.4** Documenter corrections dans diagnostic B2

### B3 - Test de validation Throttling (DEV)
- [ ] **B3.1** Lancer run complet ingest-normalize pour lai_weekly_v2 :
  - [ ] REDÉPLOIEMENT REQUIS avant test
  - [ ] Configuration actuelle (fenêtre default_period_days)
- [ ] **B3.2** Observer métriques :
  - [ ] Nombre d'items normalisés vs ingérés
  - [ ] Présence/absence ThrottlingException
  - [ ] Durée totale d'exécution
  - [ ] Comportement retry (acceptable vs avalanche)
- [ ] **B3.3** Documenter résultats dans diagnostic B3

## Résumé Final
- [x] **Final** Créer `docs/diagnostics/vectora_inbox_peptron_camurus_and_throttling_final_summary.md`
  - [x] Statut final Peptron & Camurus
  - [x] Mesures anti-throttling DEV et limites
  - [x] État global pipeline ingestion → normalisation lai_weekly_v2 DEV

---

**Status :** ✅ Corrections appliquées - Redéploiement requis  
**Dernière mise à jour :** Phases A1, A2, B1, B2 et résumé final terminés