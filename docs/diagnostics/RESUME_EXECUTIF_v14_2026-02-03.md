# Résumé Exécutif - Diagnostic Régression Matching v14

**Date**: 2026-02-03  
**Statut**: ✅ CAUSE RACINE IDENTIFIÉE  
**Urgence**: 🔴 CRITIQUE

---

## 🎯 PROBLÈME

**Régression matching après déploiement canonical v2.2** :
- V13 (avant) : 14/29 items relevant (48.3%), score moyen 38.3
- V14 (après) : 12/29 items relevant (41.4%), score moyen 33.1
- **Impact** : -14% items matchés, -13.6% score moyen

---

## 🔍 CAUSE RACINE

### Problème Principal : Perte Détection Pure Player Companies

**Symptôme** :
- V13 détectait : `pure_player_company: Nanexa`, `pure_player_company: Camurus`, `pure_player_company: MedinCell`
- V14 ne détecte PLUS ces signaux → perte de 25 points de boost par item

**Cause Technique** :
1. Les entités `companies` sont dans `normalized_content['entities']['companies']` mais sont **VIDES** (array vide)
2. Le prompt `lai_domain_scoring.yaml` v2.2 a des CRITICAL RULES anti-hallucination trop strictes
3. Bedrock ne peut plus inférer les companies depuis le texte → 0 pure_player détectés

**Preuve** :
```json
// Item Nanexa + Moderna
{
  "title": "Nanexa and Moderna enter into license...",
  "normalized_content": {
    "entities": {
      "companies": [],  // ❌ VIDE alors que Nanexa devrait être là
      "technologies": [],
      "trademarks": ["PharmaShell®"]
    }
  },
  "domain_scoring": {
    "signals_detected": {
      "strong": [],  // ❌ Pas de pure_player_company
      "medium": ["technology_family: PharmaShell"]
    }
  }
}
```

### Problème Secondaire : Template Non Résolu

**Symptôme** : `'dosing_intervals: {{item_dosing_intervals}}'` dans Item 3 (Camurus)

**Impact** : Signal medium invalide, confusion dans l'analyse

---

## ✅ SOLUTION RECOMMANDÉE

### Option 1 : Corriger la Normalisation (RECOMMANDÉ)

**Objectif** : Faire en sorte que `normalized_content['entities']['companies']` soit rempli correctement

**Actions** :

1. **Vérifier le prompt `generic_normalization.yaml`** :
   - Le prompt demande bien `companies_detected` dans la réponse JSON
   - ✅ Prompt correct (vérifié)

2. **Vérifier le code `normalizer.py`** :
   - Vérifier que la réponse Bedrock est bien parsée
   - Vérifier que `companies_detected` est bien copié dans `normalized_content['entities']['companies']`
   - **HYPOTHÈSE** : Le mapping est cassé ou incomplet

3. **Corriger le mapping** :
   ```python
   # Dans normalizer.py
   # S'assurer que :
   bedrock_response = {
     "companies_detected": ["Nanexa", "Moderna"],
     ...
   }
   
   # Est bien mappé vers :
   item["normalized_content"]["entities"]["companies"] = bedrock_response["companies_detected"]
   ```

4. **Tester localement** :
   ```bash
   python tests/local/test_normalization_prompt.py --item-id "nanexa_moderna"
   ```

5. **Re-déployer et tester** :
   ```bash
   python scripts/build/build_all.py
   python scripts/deploy/deploy_env.py --env dev
   python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v15
   ```

**Avantages** :
- ✅ Corrige le problème à la source
- ✅ Les entités seront disponibles pour tous les usages futurs
- ✅ Cohérent avec l'architecture

**Inconvénients** :
- ⏱️ Nécessite modification code + re-déploiement

---

### Option 2 : Assouplir le Domain Scoring (WORKAROUND)

**Objectif** : Permettre au domain_scoring de détecter les companies depuis le texte

**Actions** :

1. **Modifier `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`** :
   ```yaml
   # MODIFIER les CRITICAL RULES
   CRITICAL RULES FOR SIGNAL DETECTION:
   1. Detect signals from normalized item entities when available
   2. If entities are empty, infer from title and content
   3. For pure_player companies, use this list:
      - Nanexa, Camurus, MedinCell, Delsitech, Peptron
   4. Be conservative but not overly strict
   ```

2. **Incrémenter VERSION** : 2.2 → 2.3

3. **Déployer canonical** :
   ```bash
   python scripts/deploy/deploy_canonical.py --env dev
   ```

4. **Tester** :
   ```bash
   python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v15
   ```

**Avantages** :
- ⚡ Rapide à implémenter (5 minutes)
- ✅ Pas besoin de re-déployer Lambda
- ✅ Débloque immédiatement

**Inconvénients** :
- ❌ Risque de faux positifs (hallucinations)
- ❌ Ne corrige pas le problème de fond (entités vides)
- ❌ Incohérent avec l'objectif anti-hallucination

---

## 📋 PLAN D'ACTION IMMÉDIAT

### Phase 1 : Investigation Code (30 min)

1. **Lire `src_v2/vectora_core/normalization/normalizer.py`** :
   - Chercher où la réponse Bedrock est parsée
   - Identifier le mapping `companies_detected` → `entities.companies`
   - Vérifier si le mapping existe et fonctionne

2. **Vérifier les logs Lambda** :
   ```bash
   aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
     --since 3h \
     --filter-pattern "companies_detected" \
     --profile rag-lai-prod \
     --region eu-west-3
   ```

3. **Identifier le bug exact** :
   - Mapping manquant ?
   - Bedrock ne retourne pas les companies ?
   - Parsing JSON échoue ?

### Phase 2 : Correction (1h)

**Si mapping manquant** :
1. Ajouter le mapping dans `normalizer.py`
2. Tester localement
3. Build + Deploy
4. Tester sur AWS

**Si Bedrock ne retourne pas** :
1. Améliorer le prompt `generic_normalization.yaml`
2. Ajouter exemples explicites
3. Deploy canonical
4. Tester

### Phase 3 : Validation (30 min)

1. **Créer lai_weekly_v15** avec canonical v2.3 (ou code corrigé)
2. **Tester E2E** :
   ```bash
   python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v15
   ```
3. **Vérifier métriques** :
   - Items relevant ≥ 14/29 (48.3%)
   - Score moyen ≥ 38.0
   - Pure player détectés : 5-7 items
   - Pas de template non résolu

4. **Comparer v14 vs v15** :
   ```bash
   python scripts/compare_v13_v14.py  # Adapter pour v15
   ```

---

## 📊 CRITÈRES DE SUCCÈS

| Métrique | V13 (Baseline) | V14 (Cassé) | V15 (Cible) |
|----------|----------------|-------------|-------------|
| Items relevant | 14/29 (48.3%) | 12/29 (41.4%) | ≥14/29 (48.3%) |
| Score moyen | 38.3 | 33.1 | ≥38.0 |
| Pure player détectés | 5-7 items | 0 items | 5-7 items |
| Companies array vide | Non | Oui | Non |
| Templates non résolus | 0 | 1+ | 0 |

---

## 🚨 ACTIONS PRÉVENTIVES FUTURES

1. **Tests de régression automatiques** :
   - Créer `tests/regression/test_pure_player_detection.py`
   - Valider que Nanexa, Camurus, MedinCell sont détectés
   - Exécuter avant chaque promotion stage/prod

2. **Validation entités** :
   - Ajouter assertion : `assert len(companies_detected) > 0 for pure_player items`
   - Logger un WARNING si companies_detected est vide

3. **Changements incrémentaux** :
   - Modifier 1-2 fichiers à la fois
   - Tester après chaque modification
   - Commit séparé par type de changement

4. **Métriques de référence** :
   - Documenter les métriques comme baseline
   - Comparer systématiquement après chaque changement
   - Alerter si régression > 10%

---

## 📎 FICHIERS GÉNÉRÉS

1. **Rapport complet** : `docs/diagnostics/diagnostic_regression_matching_v14_2026-02-03.md`
2. **Script comparaison** : `scripts/compare_v13_v14.py`
3. **Script analyse structure** : `scripts/diagnostic_item_structure.py`
4. **Items téléchargés** : `temp_items_v13.json`, `temp_items_v14.json`

---

## 🎯 PROCHAINE ÉTAPE

**DÉCISION ADMIN REQUISE** :

- [ ] **Option 1** : Corriger le code normalizer.py (solution propre, 2h)
- [ ] **Option 2** : Assouplir domain_scoring.yaml (workaround rapide, 5 min)
- [ ] **Option 3** : Hybride (Option 2 maintenant, Option 1 plus tard)

**Recommandation** : Option 3 (Hybride)
1. Déployer Option 2 maintenant pour débloquer (5 min)
2. Investiguer et corriger Option 1 en parallèle (2h)
3. Retirer le workaround une fois Option 1 validée

---

**Rapport créé** : 2026-02-03  
**Durée diagnostic** : 45 minutes  
**Statut** : ✅ PRÊT POUR CORRECTION
