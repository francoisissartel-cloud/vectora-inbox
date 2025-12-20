# Layer Management - Organisation Structurée

**Date de création :** 18 décembre 2025  
**Objectif :** Regroupement organisé des dossiers layer_* par fonction

---

## Structure

```
layer_management/
├── active/
│   └── layer_build/          # Layer de production V2
├── experimental/
│   ├── layer_minimal/        # Tests layer minimale
│   └── layer_rebuild/        # Tests layer complète
└── tools/
    └── layer_inspection/     # Outils d'inspection
```

---

## Statuts

### active/ - Layers de Production
- **layer_build/** : ✅ **CRITIQUE** - Layer vectora-inbox-common-deps-v2 utilisée par les Lambdas V2

### experimental/ - Layers Expérimentales
- **layer_minimal/** : ⚠️ **NON UTILISÉE** - Candidat à suppression (janvier 2026)
- **layer_rebuild/** : ⚠️ **APPROCHE ABANDONNÉE** - Candidat à suppression (janvier 2026)

### tools/ - Outils de Développement
- **layer_inspection/** : ✅ **UTILITAIRE** - Outils de debug et validation

---

## Maintenance

**Réévaluation prévue :** 18 janvier 2026  
**Action :** Supprimer les layers expérimentales si non utilisées