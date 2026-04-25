# Guide Tests E2E - Système de Contextes

**Date**: 2026-02-02  
**Version**: 1.0  
**Objectif**: Système robuste de tests E2E que Q Developer comprend systématiquement

---

## 🎯 Problème Résolu

**AVANT** (système manuel):
- Incrémentation manuelle lai_weekly_v7 → v8 → v9
- Q confus sur quand créer nouveau client
- Réutilisation données anciennes
- Pas de garde-fou avant déploiement AWS

**APRÈS** (système de contextes):
- Contextes auto-incrémentés (test_context_001, 002, etc.)
- Séparation claire local vs AWS
- Blocage AWS sans succès local
- Traçabilité complète

---

## 📁 Architecture

```
tests/
├── contexts/
│   ├── registry.json           # 🔑 Registre central (source de vérité)
│   ├── local/                  # Contextes tests locaux
│   │   ├── test_context_001.json
│   │   └── test_context_002.json
│   └── aws/                    # Contextes tests AWS
│       └── test_context_001.json
├── local/
│   └── test_e2e_runner.py      # Runner tests locaux
└── aws/
    └── test_e2e_runner.py      # Runner tests AWS (avec blocage)
```

---

## 🚀 Workflow Standard

### 1. Test Local (OBLIGATOIRE)

```bash
# Créer nouveau contexte
python tests/local/test_e2e_runner.py --new-context "Test domain scoring fix"

# Exécuter test local
python tests/local/test_e2e_runner.py --run

# Vérifier succès
python tests/local/test_e2e_runner.py --status
```

**Résultat**: Contexte `test_context_001` créé avec client `lai_weekly_test_001`

### 2. Test AWS (SI LOCAL RÉUSSI)

```bash
# Promouvoir vers AWS (vérifie automatiquement succès local)
python tests/aws/test_e2e_runner.py --promote "Validation E2E domain scoring"

# Exécuter test AWS
python tests/aws/test_e2e_runner.py --run

# Vérifier résultats
python tests/aws/test_e2e_runner.py --status
```

**Résultat**: Contexte `test_context_001` AWS créé avec client `lai_weekly_v1`

---

## 🛡️ Règles de Protection

### Règle 1: Test Local Obligatoire

**Fichier**: `tests/contexts/registry.json`
```json
{
  "rules": {
    "local_test_required": true,
    "aws_deploy_blocked_without_local_success": true
  }
}
```

**Comportement**:
- ❌ Impossible de promouvoir vers AWS sans test local réussi
- ✅ Message clair avec actions requises
- ⚠️  Flag `--force` disponible (NON RECOMMANDÉ)

### Règle 2: Auto-Incrémentation

**Comportement**:
- Contextes locaux: `test_context_001`, `test_context_002`, etc.
- Clients locaux: `lai_weekly_test_001`, `lai_weekly_test_002`, etc.
- Clients AWS: `lai_weekly_v1`, `lai_weekly_v2`, etc.
- Pas de confusion possible

### Règle 3: Traçabilité

**Chaque contexte AWS trace**:
```json
{
  "id": "test_context_001",
  "promoted_from_local": "test_context_001",
  "purpose": "Validation domain scoring",
  "success": true
}
```

---

## 📋 Commandes Q Developer

### Prompt: Nouveau Test E2E Local

```
Je veux tester une nouvelle modification en local avant déploiement AWS.

Utilise le système de contextes:
1. Crée nouveau contexte: python tests/local/test_e2e_runner.py --new-context "Test [description]"
2. Exécute test local: python tests/local/test_e2e_runner.py --run
3. Vérifie succès et affiche résultats

NE PAS déployer sur AWS tant que test local n'a pas réussi.
```

### Prompt: Promouvoir vers AWS

```
Le test local a réussi. Je veux maintenant tester sur AWS.

Utilise le système de contextes:
1. Vérifie succès local: python tests/local/test_e2e_runner.py --status
2. Promouvois vers AWS: python tests/aws/test_e2e_runner.py --promote "Validation E2E [description]"
3. Exécute test AWS: python tests/aws/test_e2e_runner.py --run
4. Analyse résultats

Le système bloquera automatiquement si test local n'a pas réussi.
```

### Prompt: Lister Historique

```
Affiche l'historique complet des tests E2E (local et AWS).

Commandes:
- python tests/local/test_e2e_runner.py --list
- python tests/aws/test_e2e_runner.py --list

Présente les résultats de façon claire avec statuts.
```

---

## 🔍 Registre Central

**Fichier**: `tests/contexts/registry.json`

**Structure**:
```json
{
  "version": "1.0.0",
  "last_updated": "2026-02-02T16:30:00",
  "contexts": {
    "local": {
      "current": "test_context_002",
      "history": [
        {
          "id": "test_context_001",
          "created": "2026-02-01T10:00:00",
          "purpose": "Test domain scoring fix",
          "status": "completed",
          "success": true
        },
        {
          "id": "test_context_002",
          "created": "2026-02-02T14:00:00",
          "purpose": "Test extraction dates",
          "status": "in_progress",
          "success": null
        }
      ]
    },
    "aws": {
      "current": "test_context_001",
      "history": [
        {
          "id": "test_context_001",
          "created": "2026-02-01T11:00:00",
          "purpose": "Validation E2E domain scoring",
          "status": "completed",
          "success": true,
          "promoted_from_local": "test_context_001"
        }
      ]
    }
  },
  "rules": {
    "local_test_required": true,
    "aws_deploy_blocked_without_local_success": true,
    "auto_increment_context": true
  }
}
```

---

## 🎓 Exemples Concrets

### Exemple 1: Premier Test E2E

```bash
# Étape 1: Créer contexte local
$ python tests/local/test_e2e_runner.py --new-context "Baseline LAI weekly"
✅ Nouveau contexte créé: test_context_001
   Client ID: lai_weekly_test_001
   Purpose: Baseline LAI weekly

# Étape 2: Exécuter test local
$ python tests/local/test_e2e_runner.py --run
🧪 TEST E2E LOCAL - test_context_001
...
✅ TEST E2E LOCAL RÉUSSI

# Étape 3: Promouvoir vers AWS
$ python tests/aws/test_e2e_runner.py --promote "Validation baseline"
✅ Test local validé: test_context_001
✅ Contexte AWS créé: test_context_001
   Client ID: lai_weekly_v1

# Étape 4: Exécuter test AWS
$ python tests/aws/test_e2e_runner.py --run
☁️  TEST E2E AWS - test_context_001
...
✅ Test AWS réussi
```

### Exemple 2: Test Échoué (Blocage AWS)

```bash
# Étape 1: Test local échoue
$ python tests/local/test_e2e_runner.py --run
❌ TEST E2E LOCAL ÉCHOUÉ

# Étape 2: Tentative promotion AWS
$ python tests/aws/test_e2e_runner.py --promote "Test"
================================================================================
❌ DÉPLOIEMENT AWS BLOQUÉ
================================================================================
Raison: Test local test_context_002 n'a pas réussi
Status: failed

Actions requises:
1. Corriger les erreurs du test local
2. Ré-exécuter: python tests/local/test_e2e_runner.py --run
3. Revenir ici si succès
================================================================================
```

### Exemple 3: Comparaison Versions

```bash
# Lister historique local
$ python tests/local/test_e2e_runner.py --list
📋 Historique contextes locaux:
   ✅ test_context_001 - Baseline LAI weekly (completed)
   ❌ test_context_002 - Test extraction dates (failed)
   ⏳ test_context_003 - Test nouveau prompt (in_progress)

# Lister historique AWS
$ python tests/aws/test_e2e_runner.py --list
📋 Historique contextes AWS:
   ✅ test_context_001 - Validation baseline (from test_context_001)
```

---

## 🤖 Instructions pour Q Developer

### Quand Créer Nouveau Contexte Local

**TOUJOURS créer nouveau contexte si**:
- Nouvelle modification code (fix, feature, refactor)
- Test d'une nouvelle configuration
- Validation après merge
- Comparaison performance

**Commande**:
```bash
python tests/local/test_e2e_runner.py --new-context "[description claire]"
```

### Quand Promouvoir vers AWS

**UNIQUEMENT si**:
- Test local a réussi (success=true)
- Pas de régression détectée
- Prêt pour validation E2E complète

**Commande**:
```bash
python tests/aws/test_e2e_runner.py --promote "[description validation]"
```

### Quand NE PAS Promouvoir

**JAMAIS promouvoir si**:
- Test local échoué
- Résultats incohérents
- Régression détectée
- Doute sur stabilité

**Le système bloquera automatiquement**

---

## 📊 Métriques et Reporting

### Fichiers Générés

**Local**:
- `tests/contexts/local/test_context_XXX.json` - Contexte complet
- `.tmp/test_e2e_local_results.json` - Résultats détaillés

**AWS**:
- `tests/contexts/aws/test_context_XXX.json` - Contexte complet
- Logs CloudWatch Lambda

### Intégration Template E2E

**Le template existant** (`docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`) **reste valide**.

**Nouveau workflow**:
1. Créer contexte: `test_context_XXX`
2. Exécuter test avec runner
3. Remplir template avec résultats du contexte
4. Comparer avec contextes précédents

---

## 🔧 Maintenance

### Nettoyer Anciens Contextes

```bash
# Archiver contextes >30 jours
python scripts/maintenance/archive_old_contexts.py --days 30
```

### Réinitialiser Registre

```bash
# Backup
cp tests/contexts/registry.json tests/contexts/registry.backup.json

# Reset (ATTENTION)
python tests/local/test_e2e_runner.py --reset-registry
```

---

## ✅ Checklist Q Developer

Avant chaque test E2E, Q doit:

- [ ] Vérifier registre: `tests/contexts/registry.json` existe
- [ ] Créer nouveau contexte local avec description claire
- [ ] Exécuter test local AVANT toute tentative AWS
- [ ] Vérifier succès local explicitement
- [ ] Promouvoir vers AWS UNIQUEMENT si local réussi
- [ ] Documenter résultats dans contexte
- [ ] Mettre à jour registre automatiquement

---

## 🚨 Règles Critiques

### RÈGLE 1: Jamais Réutiliser Contexte

❌ **INTERDIT**:
```bash
# Ré-exécuter sur même contexte après modification
python tests/local/test_e2e_runner.py --run  # Sur test_context_001
# Modifier code
python tests/local/test_e2e_runner.py --run  # ENCORE sur test_context_001
```

✅ **CORRECT**:
```bash
python tests/local/test_e2e_runner.py --run  # Sur test_context_001
# Modifier code
python tests/local/test_e2e_runner.py --new-context "Après fix"  # test_context_002
python tests/local/test_e2e_runner.py --run  # Sur test_context_002
```

### RÈGLE 2: Jamais AWS Sans Local

❌ **INTERDIT**:
```bash
# Déployer directement sur AWS
python scripts/deploy/deploy_env.py --env dev
python tests/aws/test_e2e_runner.py --promote "Test"  # BLOQUÉ
```

✅ **CORRECT**:
```bash
# Test local d'abord
python tests/local/test_e2e_runner.py --new-context "Test"
python tests/local/test_e2e_runner.py --run
# Si succès, déployer
python scripts/deploy/deploy_env.py --env dev
python tests/aws/test_e2e_runner.py --promote "Validation"
```

### RÈGLE 3: Toujours Documenter Purpose

❌ **INTERDIT**:
```bash
python tests/local/test_e2e_runner.py --new-context "test"
```

✅ **CORRECT**:
```bash
python tests/local/test_e2e_runner.py --new-context "Validation domain scoring fix après correction config_loader"
```

---

**Guide Tests E2E - Version 1.0**  
**Date**: 2026-02-02  
**Statut**: Système opérationnel et prêt pour Q Developer
