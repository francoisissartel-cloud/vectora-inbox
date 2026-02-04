# Règles de Promotion Environnements

**Date**: 2026-02-03  
**Statut**: RÈGLE STRICTE

---

## ⚠️ RÈGLE CRITIQUE

**AUCUNE promotion vers stage ou prod sans accord EXPLICITE de l'admin**

---

## 🔒 Workflow de Promotion

### Dev → Stage

**Prérequis**:
1. ✅ Tests locaux réussis
2. ✅ Deploy dev réussi
3. ✅ Tests AWS dev complets réussis
4. ✅ Validation admin des résultats
5. ⚠️ **ACCORD EXPLICITE ADMIN REQUIS**

**Commande**:
```bash
# ⚠️ NE PAS EXÉCUTER SANS ACCORD ADMIN
python scripts/deploy/promote.py --to stage --version X.Y.Z
```

### Stage → Prod

**Prérequis**:
1. ✅ Tests stage complets réussis
2. ✅ Validation admin des résultats stage
3. ✅ Période de stabilisation (minimum 24h)
4. ⚠️ **ACCORD EXPLICITE ADMIN REQUIS**

**Commande**:
```bash
# ⚠️ NE PAS EXÉCUTER SANS ACCORD ADMIN
python scripts/deploy/promote.py --to prod --version X.Y.Z
```

---

## ✅ Actions Autorisées Sans Accord

- Modifications code local
- Tests locaux
- Deploy vers **dev uniquement**
- Création branches Git
- Création PR
- Push GitHub

---

## 🚫 Actions Interdites Sans Accord

- ❌ Promotion dev → stage
- ❌ Promotion stage → prod
- ❌ Modifications directes stage/prod
- ❌ Deploy manuel stage/prod

---

## 📋 Process de Demande d'Accord

1. **Préparer rapport complet**:
   - Résultats tests dev
   - Métriques avant/après
   - Liste modifications
   - Impact attendu

2. **Demander accord admin**:
   - Présenter rapport
   - Attendre validation explicite
   - Noter accord dans rapport

3. **Exécuter promotion**:
   - Uniquement après accord
   - Documenter dans rapport
   - Monitorer résultats

---

**Règle établie**: 2026-02-03  
**Applicable à**: Tous les déploiements stage/prod
