# Client Config Examples - Structure

**Date**: 2026-02-02  
**Système**: Génération automatique via contextes de test

---

## 📁 Structure

```
client-config-examples/
├── production/              # Configs production
│   └── lai_weekly_prod.yaml
├── test/
│   ├── local/              # Configs test local (lai_weekly_test_XXX)
│   └── aws/                # Configs test AWS (lai_weekly_vX)
├── templates/              # Templates réutilisables
│   └── lai_weekly_template.yaml
└── archive/                # Anciens configs (v3-v9)
```

## 🎯 Usage

### Production

**Config stable**: `production/lai_weekly_prod.yaml`  
**Client ID**: `lai_weekly_prod`

### Tests

**NE PAS créer manuellement**. Utiliser les runners:

```bash
# Test local
python tests/local/test_e2e_runner.py --new-context "Description"
# → Génère: test/local/test_context_001.yaml

# Test AWS
python tests/aws/test_e2e_runner.py --promote "Validation"
# → Génère: test/aws/test_context_001.yaml
# → Upload: s3://vectora-inbox-config-dev/clients/lai_weekly_v1.yaml
```

## 📋 Règles

1. **Production**: Modifier `production/lai_weekly_prod.yaml` manuellement
2. **Tests**: Générer automatiquement via runners
3. **Templates**: Modifier `templates/lai_weekly_template.yaml` pour tous les tests
4. **Archive**: Ne pas modifier (historique)

## 🔗 Documentation

Voir: `.q-context/vectora-inbox-client-config-system.md`
