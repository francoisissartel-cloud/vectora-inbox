# 🚨 DIAGNOSTIC v14 - SYNTHÈSE 5 MINUTES

**Date**: 2026-02-03  
**Statut**: ✅ CAUSE TROUVÉE

---

## LE PROBLÈME

**V14 perd 2 items matchés (-14%) et -5.2 points de score moyen (-13.6%)**

---

## LA CAUSE

**`normalized_content['entities']['companies']` est VIDE**

```json
{
  "title": "Nanexa and Moderna...",
  "normalized_content": {
    "entities": {
      "companies": [],  // ❌ VIDE (devrait contenir ["Nanexa", "Moderna"])
      "technologies": []
    }
  },
  "domain_scoring": {
    "signals": {
      "strong": []  // ❌ Pas de pure_player_company → -25 points
    }
  }
}
```

**Résultat** : Nanexa, Camurus, MedinCell ne sont plus détectés comme pure_player → perte de 25 points de boost par item

---

## LA SOLUTION

### Option A : Corriger le Code (2h)

Fixer `src_v2/vectora_core/normalization/normalizer.py` pour que Bedrock remplisse correctement `companies_detected`

**Avantages** : Solution propre  
**Inconvénients** : Nécessite code + deploy

### Option B : Workaround Prompt (5 min)

Modifier `canonical/prompts/domain_scoring/lai_domain_scoring.yaml` pour permettre l'inférence des companies depuis le texte

**Avantages** : Rapide, débloque immédiatement  
**Inconvénients** : Risque hallucinations

### Option C : Hybride (RECOMMANDÉ)

1. Déployer Option B maintenant (5 min)
2. Corriger Option A en parallèle (2h)
3. Retirer workaround une fois A validé

---

## FICHIERS GÉNÉRÉS

1. **Rapport complet** : `docs/diagnostics/diagnostic_regression_matching_v14_2026-02-03.md` (10 pages)
2. **Résumé exécutif** : `docs/diagnostics/RESUME_EXECUTIF_v14_2026-02-03.md` (3 pages)
3. **Ce fichier** : Synthèse 5 min

---

## DÉCISION ADMIN

Quelle option choisir ?

- [ ] Option A : Corriger le code (2h)
- [ ] Option B : Workaround prompt (5 min)
- [ ] Option C : Hybride (5 min + 2h)

---

**Recommandation** : Option C (Hybride)
