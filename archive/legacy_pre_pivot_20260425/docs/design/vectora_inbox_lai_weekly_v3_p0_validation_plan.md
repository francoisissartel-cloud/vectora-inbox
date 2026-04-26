# Vectora Inbox LAI Weekly v3 - Plan de Validation P0

**Date** : 2025-12-11  
**Objectif** : Validation end-to-end des corrections P0 en conditions réelles  
**Environnement** : AWS DEV (vectora-inbox-dev) - Profil rag-lai-prod - Région eu-west-3

---

## 🎯 Objectifs Globaux

Vérifier que les corrections P0 sont implémentées et déployées, puis exécuter un run complet lai_weekly_v3 pour valider :

- **Items gold présents** : Nanexa/Moderna (PharmaShell®), UZEDY® (MedinCell/Teva), MedinCell malaria grant
- **Bruit HR/finance filtré** : DelSiTech hiring, MedinCell financial results
- **Pipeline fonctionnel** : Ingestion → Normalisation → Engine → Newsletter

---

## Phase 1 – Vérification & Récap des Corrections P0

### Objectifs
- Vérifier que les fichiers du repo contiennent les changements P0
- Confirmer la cohérence entre config locale et AWS DEV
- Valider le déploiement des Lambdas

### Inputs
- Fichiers canonical : `technology_scopes.yaml`, `exclusion_scopes.yaml`, `ingestion_profiles.yaml`, `domain_matching_rules.yaml`, `trademark_scopes.yaml`
- Code source : `src/lambdas/engine/exclusion_filter.py`, normalizer Bedrock
- Config client : `client-config-examples/lai_weekly_v3.yaml`
- Buckets S3 : `s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml`

### Commandes Clés
```bash
# Vérification config S3
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly_v3.yaml ./temp-config-check.yaml --profile rag-lai-prod --region eu-west-3

# Vérification versions Lambdas
aws lambda get-function --function-name vectora-inbox-ingest-normalize-dev --profile rag-lai-prod --region eu-west-3
aws lambda get-function --function-name vectora-inbox-engine-dev --profile rag-lai-prod --region eu-west-3
```

### Critères de Succès
- ✅ Tous les fichiers canonical contiennent les corrections P0
- ✅ Config client locale = config S3 DEV
- ✅ Lambdas pointent sur le code avec corrections P0

### Fichier de Diagnostic
`docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_validation_phase1_plan_vs_runtime.md`

---

## Phase 2 – Tests Locaux Ciblés

### Objectifs
- Valider localement les corrections P0 sur des cas représentatifs
- Tester ingestion → normalisation → matching → scoring → exclusion

### Inputs
- Script de test : `test_p0_corrections_local.py` (à créer si nécessaire)
- Cas de test :
  - Item Nanexa/Moderna PharmaShell®
  - Item UZEDY® Extended-Release Injectable
  - Item MedinCell malaria grant
  - Item HR DelSiTech (à exclure)
  - Item finance MedinCell (à exclure)

### Commandes Clés
```bash
# Test local des corrections P0
python test_p0_corrections_local.py --client lai_weekly_v3 --verbose
```

### Critères de Succès
- ✅ Items LAI : technologies détectées, matching LAI, scoring élevé
- ✅ Items HR/finance : exclus avant matching
- ✅ Normalisation Bedrock : entités et technologies extraites
- ✅ Aucune erreur critique dans le pipeline local

### Fichier de Diagnostic
`docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_validation_phase2_local_tests.md`

---

## Phase 3 – Déploiement / Synchro AWS DEV

### Objectifs
- Synchroniser le code validé localement vers AWS DEV
- Confirmer que les Lambdas utilisent les dernières versions

### Inputs
- Scripts de déploiement : `scripts/deploy_*.sh` ou équivalents
- Buckets S3 : canonical, config, packages Lambda
- Fonctions Lambda : `vectora-inbox-ingest-normalize-dev`, `vectora-inbox-engine-dev`

### Commandes Clés
```bash
# Déploiement canonical vers S3
aws s3 sync ./canonical s3://vectora-inbox-canonical-dev/ --profile rag-lai-prod --region eu-west-3

# Déploiement config client
aws s3 cp ./client-config-examples/lai_weekly_v3.yaml s3://vectora-inbox-config-dev/clients/ --profile rag-lai-prod --region eu-west-3

# Mise à jour Lambdas (via scripts existants)
./scripts/deploy_ingest_normalize.sh dev
./scripts/deploy_engine.sh dev
```

### Critères de Succès
- ✅ Canonical synchronisé sur S3
- ✅ Config client déployée
- ✅ Lambdas mises à jour avec timestamps récents
- ✅ Aucune erreur de déploiement

### Fichier de Diagnostic
`docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_validation_phase3_aws_sync.md`

---

## Phase 4 – Run End-to-End Réel sur AWS DEV

### Objectifs
- Exécuter le workflow complet lai_weekly_v3 en conditions réelles
- Collecter les métriques détaillées à chaque phase
- Identifier la présence/absence des items gold

### Inputs
- Client config : `lai_weekly_v3`
- Période : 30 jours (données récentes)
- Lambdas : `vectora-inbox-ingest-normalize-dev`, `vectora-inbox-engine-dev`

### Commandes Clés
```powershell
# Invocation ingestion + normalisation
$payload = '{"client_id":"lai_weekly_v3","period_days":30}'
$bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
$b64 = [System.Convert]::ToBase64String($bytes)

aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload $b64 `
  --cli-binary-format raw-in-base64-out `
  --profile rag-lai-prod `
  --region eu-west-3 `
  out-ingest-lai-weekly-v3.json

# Invocation engine
aws lambda invoke `
  --function-name vectora-inbox-engine-dev `
  --payload $b64 `
  --cli-binary-format raw-in-base64-out `
  --profile rag-lai-prod `
  --region eu-west-3 `
  out-engine-lai-weekly-v3.json
```

### Critères de Succès
- ✅ Ingestion : >50 items, sources diversifiées
- ✅ Normalisation : technologies LAI détectées
- ✅ Exclusions : items HR/finance filtrés
- ✅ Matching : items LAI identifiés
- ✅ Newsletter : items gold présents et priorisés

### Fichier de Diagnostic
`docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_validation_phase4_e2e_results.md`

---

## Phase 5 – Analyse Métrique & Évaluation Métier

### Objectifs
- Analyser les résultats du run end-to-end
- Évaluer la qualité métier vs objectifs P0
- Identifier les points d'amélioration P1

### Inputs
- Résultats Phase 4 : métriques, newsletter, logs
- Objectifs P0 : items gold, filtrage bruit
- Baseline : résultats v2/run2 précédents

### Commandes Clés
```bash
# Analyse des résultats S3
aws s3 ls s3://vectora-inbox-results-dev/lai_weekly_v3/ --profile rag-lai-prod --region eu-west-3
aws s3 cp s3://vectora-inbox-results-dev/lai_weekly_v3/latest/newsletter.json ./analysis/ --profile rag-lai-prod --region eu-west-3
```

### Critères de Succès
- ✅ Items gold : 3/3 présents (Nanexa/Moderna, UZEDY®, MedinCell malaria)
- ✅ Bruit filtré : <30% d'items HR/finance dans la newsletter
- ✅ Signal/noise : >60% d'items LAI authentiques
- ✅ Technologies : >3 types détectés par Bedrock

### Fichier de Diagnostic
`docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_validation_phase5_analysis.md`

---

## Phase 6 – Executive Summary

### Objectifs
- Synthétiser les résultats de validation
- Évaluer la maturité du MVP lai_weekly_v3
- Recommander les prochaines étapes

### Inputs
- Diagnostics Phases 1-5
- Métriques de performance
- Évaluation qualitative métier

### Critères de Succès
- ✅ Statut MVP clair : immature / présentable / montrable client
- ✅ Explication des écarts vs objectifs P0
- ✅ Backlog P1 priorisé (3-5 éléments max)

### Fichier de Diagnostic
`docs/diagnostics/vectora_inbox_lai_weekly_v3_p0_validation_executive_summary.md`

---

## 🚨 Gestion des Blocages

Si blocage technique (auth AWS, réseau, etc.) :
1. Documenter le blocage dans `/docs/diagnostics/`
2. Arrêter le plan sans basculer en simulation
3. Proposer des solutions de contournement
4. Ne pas utiliser de vieilles données sans autorisation explicite

---

## 📊 Métriques Cibles

| **Phase** | **Métrique Clé** | **Objectif** |
|-----------|------------------|--------------|
| Phase 1 | Alignement config | 100% |
| Phase 2 | Tests locaux | 5/5 cas passent |
| Phase 3 | Déploiement | 0 erreur |
| Phase 4 | Items gold | 3/3 présents |
| Phase 5 | Signal/noise | >60% |
| Phase 6 | Maturité MVP | Présentable+ |

---

**Plan créé le 2025-12-11 - Prêt pour exécution phase par phase**