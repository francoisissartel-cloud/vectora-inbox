# Snapshot lai_v7_stable - 2026-01-30 13:23:56

## 📸 Informations Snapshot

**Date**: 2026-01-30 13:23:56  
**Motif**: Sauvegarde avant implémentation gestion multi-environnements  
**Client**: lai_weekly_v7  
**Environnement source**: dev

## 📦 Contenu Snapshot

### Lambdas (3)
- `vectora-inbox-ingest-v2-dev`
- `vectora-inbox-normalize-score-v2-dev`
- `vectora-inbox-newsletter-v2-dev`

### Layers (2)
- `vectora-inbox-vectora-core-dev`
- `vectora-inbox-common-deps-dev`

### Configurations
- `lai_weekly_v7.yaml` (config client complète)

### Canonical
- Scopes (company, indication, molecule, technology, trademark, exclusion)
- Prompts (matching, normalization, editorial)
- Sources (source_catalog.yaml, html_extractors.yaml)
- Scoring (scoring_rules.yaml)
- Ingestion (ingestion_profiles.yaml)
- Events (event_type_definitions.yaml, event_type_patterns.yaml)

### Données
- Inventaire données client lai_weekly_v7

## 🔄 Restauration

### Restaurer Config Client
```bash
aws s3 cp backup/snapshots/lai_v7_stable_20260130_132356/configs/lai_weekly_v7.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml \
  --profile rag-lai-prod --region eu-west-3
```

### Restaurer Canonical
```bash
aws s3 sync backup/snapshots/lai_v7_stable_20260130_132356/canonical/ \
  s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3
```

### Restaurer Lambda (exemple ingest-v2)
```bash
# Récupérer CodeSha256 depuis lambdas/ingest-v2-dev.json
# Puis update-function-code avec version spécifique
```

## ✅ Validation Snapshot

- [x] 3 Lambdas sauvegardées
- [x] 2 Layers sauvegardées
- [x] Config client lai_weekly_v7.yaml
- [x] Canonical complet (37 fichiers)
- [x] Inventaire données créé

## 📝 Notes

- Snapshot créé avant Phase 1 du plan correctif multi-env
- État stable et fonctionnel du moteur lai_weekly_v7
- Toutes les configurations métier préservées
- Point de restauration validé

---

**Snapshot prêt pour rollback si nécessaire**
