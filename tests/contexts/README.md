# Test Contexts System

**Système de gestion des tests E2E avec traçabilité et protection**

## 🎯 Objectif

Éviter la réutilisation de données anciennes et garantir qu'aucun déploiement AWS ne se fait sans validation locale réussie.

## 📁 Structure

```
contexts/
├── registry.json           # Registre central (source de vérité)
├── local/                  # Contextes tests locaux
│   ├── test_context_001.json
│   └── test_context_002.json
└── aws/                    # Contextes tests AWS
    └── test_context_001.json
```

## 🚀 Usage Rapide

### Test Local

```bash
# Créer nouveau contexte
python tests/local/test_e2e_runner.py --new-context "Description du test"

# Exécuter test
python tests/local/test_e2e_runner.py --run

# Vérifier statut
python tests/local/test_e2e_runner.py --status
```

### Test AWS (après succès local)

```bash
# Promouvoir vers AWS (vérifie automatiquement succès local)
python tests/aws/test_e2e_runner.py --promote "Description validation"

# Exécuter test AWS
python tests/aws/test_e2e_runner.py --run

# Vérifier statut
python tests/aws/test_e2e_runner.py --status
```

## 🛡️ Protection

Le système **BLOQUE automatiquement** le déploiement AWS si:
- Aucun test local n'a été exécuté
- Le test local a échoué
- Le test local est en cours

## 📚 Documentation Complète

Voir: `.q-context/vectora-inbox-test-e2e-system.md`

## 🔑 Registre Central

Le fichier `registry.json` contient:
- Contexte local actuel
- Contexte AWS actuel
- Historique complet
- Règles de protection

**Ne jamais modifier manuellement** - utiliser les runners.
