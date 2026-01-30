# Snapshot lai_v7_stable - 2026-01-30

## 📸 Informations

**ID Snapshot**: `lai_v7_stable_20260130_132356`  
**Date**: 2026-01-30 13:23:56  
**Motif**: Sauvegarde avant implémentation gestion multi-environnements  
**Plan**: Plan Correctif Simplifié - Phase 0  
**Statut**: ✅ VALIDÉ

---

## 📦 Contenu

- **3 Lambdas** (ingest-v2, normalize-score-v2, newsletter-v2)
- **2 Layers** (vectora-core-dev:38, common-deps-dev:4)
- **1 Config client** (lai_weekly_v7.yaml v7.0.0)
- **47 fichiers Canonical** (scopes, prompts, sources, scoring, etc.)
- **Inventaire données** client lai_weekly_v7

**Taille totale**: ~1.6 MB

---

## 🔄 Restauration

### Restaurer Config Client
```bash
aws s3 cp backup/snapshots/lai_v7_stable_20260130_132356/configs/lai_weekly_v7.yaml \
  s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml \
  --profile rag-lai-prod --region eu-west-3
```

### Restaurer Canonical Complet
```bash
aws s3 sync backup/snapshots/lai_v7_stable_20260130_132356/canonical/ \
  s3://vectora-inbox-config-dev/canonical/ \
  --profile rag-lai-prod --region eu-west-3
```

### Restaurer Lambda (rollback code)
```bash
# Voir backup/snapshots/lai_v7_stable_20260130_132356/lambdas/*.json
# pour CodeSha256 et détails configuration
```

---

## ✅ Validation

- [x] Snapshot complet créé
- [x] Test restauration partielle réussi
- [x] Documentation complète
- [x] État stable lai_weekly_v7 préservé

---

## 📁 Emplacement

```
backup/snapshots/lai_v7_stable_20260130_132356/
├── lambdas/           (3 fichiers JSON)
├── layers/            (2 fichiers JSON)
├── configs/           (lai_weekly_v7.yaml)
├── canonical/         (47 fichiers)
├── data/              (inventaire)
├── SNAPSHOT_README.md
└── VALIDATION.md
```

---

## 📝 Notes

- Créé en ~15 minutes
- Point de restauration validé
- Prêt pour rollback si nécessaire
- Base pour Phase 1 du plan correctif

---

**Snapshot sécurisé et validé - Prêt pour phases suivantes**
