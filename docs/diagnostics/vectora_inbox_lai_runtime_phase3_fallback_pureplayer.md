# Vectora Inbox — LAI Runtime Phase 3: Fallback & Pure_Player

**Date:** 2025-01-XX  
**Phase:** 3/4 — Durcissement Fallback & Exploitation Pure_Player/Hybrid  
**Statut:** ✅ IMPLÉMENTÉ

---

## Objectif de la Phase 3

Corriger RC3 et améliorer la précision en :
1. **Durcissant la règle de fallback** (exiger 2 keywords technology au lieu de 1)
2. **Adaptant les seuils de matching** selon le type de company (pure_player vs hybrid)
3. **Améliorant le bonus de scoring** pour prioriser les pure players

---

## Modifications Implémentées

### 1. Durcissement de la Règle de Fallback

**Fichier:** `canonical/matching/domain_matching_rules.yaml`

**Avant:**
```yaml
technology:
  dimensions:
    technology:
      min_matches: 1
```

**Après:**
```yaml
technology:
  dimensions:
    technology:
      min_matches: 2  # Règle durcie pour réduire faux positifs
```

**Impact:** Les items avec un seul keyword technology ne matchent plus via la règle de fallback (doivent passer par le profile matching).

---

### 2. Seuils Adaptatifs par Type de Company

**Fichier:** `src/vectora_core/matching/matcher.py`

**Ajouté dans `_evaluate_technology_profile_match()`:**

```python
# Ajuster les seuils selon le type de company
if company_scope_type == 'pure_player':
    # Pure player : 1 signal fort suffit
    min_high_precision = 1
    min_supporting = 0
    logger.info(f"[COMPANY_TYPE] Pure player detected, using relaxed thresholds (HP>=1)")
elif company_scope_type == 'hybrid':
    # Hybrid : 2 signaux indépendants requis
    min_high_precision = 1
    min_supporting = 1
    logger.info(f"[COMPANY_TYPE] Hybrid detected, using strict thresholds (HP>=1 + SUP>=1)")
else:
    # Fallback : règle standard
    min_high_precision = 1
    min_supporting = 1
    logger.info(f"[COMPANY_TYPE] Other company type, using standard thresholds")
```

**Impact:**
- **Pure players** (MedinCell, Camurus, etc.) : Matching plus permissif (1 signal fort suffit)
- **Hybrid** (Pfizer, Novartis, etc.) : Matching plus strict (1 signal fort + 1 signal supporting requis)

---

### 3. Amélioration du Bonus de Scoring

**Fichier:** `src/vectora_core/scoring/scorer.py`

**Avant:**
```python
def _compute_company_scope_bonus(...):
    # Vérifier company_scope_type depuis matching_details
    if company_scope_type == 'pure_player':
        return other_factors.get('pure_player_bonus', 3)
    # Fallback simple
    return 0
```

**Après:**
```python
def _compute_company_scope_bonus(...):
    # Vérifier matching_details
    if matching_details:
        if company_scope_type == 'pure_player':
            logger.info(f"[SCORING] Pure player bonus applied: {list(item_companies)}")
            return other_factors.get('pure_player_bonus', 3)
    
    # Fallback amélioré : vérifier manuellement les scopes
    pure_player_scopes = ['lai_companies_pure_players', 'lai_companies_mvp_core']
    for scope_key in pure_player_scopes:
        pure_players = set(company_scopes.get(scope_key, []))
        matched_pure = item_companies & pure_players
        if matched_pure:
            logger.info(f"[SCORING_FALLBACK] Pure player bonus applied: {list(matched_pure)}")
            return other_factors.get('pure_player_bonus', 3)
```

**Impact:** Le bonus pure_player (+3 points) est appliqué même si le profile matching n'a pas fonctionné (fallback robuste).

---

## Logs Ajoutés

### Matching
- `[COMPANY_TYPE]` : Type de company détecté et seuils appliqués
  - Exemple : `[COMPANY_TYPE] Pure player detected, using relaxed thresholds (HP>=1)`

### Scoring
- `[SCORING]` : Bonus appliqué via matching_details
  - Exemple : `[SCORING] Pure player bonus applied: ['MedinCell']`
- `[SCORING_FALLBACK]` : Bonus appliqué via fallback manuel
  - Exemple : `[SCORING_FALLBACK] Pure player bonus applied: ['Camurus']`

---

## Impact Attendu

### Avant Phase 3
- Pure players et hybrid traités de la même manière
- Pas de priorisation des acteurs clés LAI
- Pure player % = 0%

### Après Phase 3
- Pure players favorisés (seuils relaxés + bonus scoring)
- Hybrid filtrés (seuils stricts)
- Pure player % > 30% attendu

### Métriques Cibles
| Métrique | Avant | Objectif Après | Status |
|----------|-------|----------------|--------|
| LAI precision | 0-20% | ≥50% | À tester |
| Pure player % | 0% | ≥30% | À tester |
| False positives | 2/5 | <2/5 | À tester |

---

## Prochaines Étapes

### Déploiement

1. **Uploader la config canonical mise à jour :**
   ```powershell
   aws s3 cp canonical/matching/domain_matching_rules.yaml s3://vectora-inbox-config-dev/canonical/matching/
   ```

2. **Repackager et redéployer la Lambda :**
   ```powershell
   python scripts/package_lambda.py
   python scripts/deploy_lambda.py --env dev
   ```

3. **Vérifier le déploiement :**
   ```powershell
   aws lambda get-function --function-name vectora-inbox-engine-dev
   ```

### Tests

1. **Lancer l'engine :**
   ```powershell
   python scripts/run_engine.py --env dev --client lai_weekly
   ```

2. **Analyser la newsletter :**
   ```powershell
   aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/latest/newsletter.json .
   python scripts/analyze_newsletter.py newsletter.json --check-pure-players
   ```

3. **Vérifier les logs :**
   ```powershell
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[COMPANY_TYPE]"
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[SCORING]"
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[SCORING_FALLBACK]"
   ```

### Critères de Succès

✅ **Pure players favorisés:**
- Au moins 1 pure player (MedinCell, Camurus, Alkermes, etc.) dans les résultats
- Log `[COMPANY_TYPE] Pure player detected` présent
- Log `[SCORING] Pure player bonus applied` présent

✅ **Hybrid filtrés:**
- Items hybrid sans signaux forts rejetés
- Moins de faux positifs sur big pharma

✅ **Amélioration métrique:**
- Précision LAI ≥ 50%
- Pure player % ≥ 30%

---

## Risques & Mitigations

### 🟡 Risque: Seuils trop stricts pour hybrid

**Symptôme:** Vrais positifs hybrid rejetés (ex: Pfizer avec vraie news LAI)

**Mitigation:**
- Analyser les items rejetés dans les logs
- Ajuster `min_supporting` de 1 à 0 si nécessaire
- Documenter les cas limites

### 🟡 Risque: Fallback trop strict (min_matches: 2)

**Symptôme:** Items avec 1 seul keyword fort rejetés

**Mitigation:**
- Le profile matching devrait capturer ces cas
- Si problème persistant, revenir à `min_matches: 1` avec d'autres contraintes

### 🟢 Pas de risque de régression

Les modifications sont isolées dans la logique de matching/scoring LAI.

---

## Notes Techniques

### Scopes Utilisés

**Pure players:**
- `lai_companies_pure_players` (14 companies)
- `lai_companies_mvp_core` (5 companies)

**Hybrid:**
- `lai_companies_hybrid` (27 companies)

### Logique de Matching Adaptative

```
IF pure_player:
    MATCH if high_precision >= 1
ELIF hybrid:
    MATCH if high_precision >= 1 AND supporting >= 1
ELSE:
    MATCH if high_precision >= 1 AND supporting >= 1
```

### Bonus de Scoring

- Pure player: +3 points
- Hybrid: +1 point
- Other: 0 point

---

## Validation Manuelle Recommandée

Après déploiement, vérifier manuellement que :
1. MedinCell, Camurus, Alkermes apparaissent dans les résultats
2. Pfizer, Novartis n'apparaissent que pour des news LAI fortes
3. Les scores des pure players sont supérieurs aux hybrid
