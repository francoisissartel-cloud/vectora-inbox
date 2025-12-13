# Vectora Inbox — LAI Runtime Matching Corrections Plan

**Date:** 2025-12-09  
**Auteur:** Amazon Q Developer  
**Statut:** 🟡 PLAN READY FOR EXECUTION  
**Objectif:** Passer de 0% à ≥80% de précision LAI en corrigeant RC1, RC2, RC3

---

## 1. Contexte & Objectif Global

### Situation Actuelle

Après le refactor canonical complet et l'adaptation du runtime (Phases 1-4), le MVP LAI reste en échec :

| Métrique | Résultat Actuel | Objectif MVP | Status |
|----------|-----------------|--------------|--------|
| LAI precision | 0% | ≥80% | ❌ |
| Pure player % | 0% | ≥50% | ❌ |
| False positives | 2/5 (40%) | 0 | ❌ |

### Root Causes Identifiées

**🔴 RC1 – Profile technology_complex jamais activé**
- Le système n'utilise jamais la logique avancée par catégories
- Fallback systématique sur la règle classique binaire (keyword présent/absent)
- Impact : Tous les bénéfices du refactor canonical sont perdus

**🔴 RC2 – generic_terms et negative_terms non filtrés**
- Les termes génériques (PEG, liposomes, subcutaneous) matchent seuls
- Les termes négatifs (oral tablet, topical) ne rejettent pas le match
- Impact : Faux positifs sur des signaux faibles

**🟡 RC3 – Distinction pure_player/hybrid non exploitée**
- Sans profile matching, la différenciation n'est jamais appliquée
- Pas de bonus de scoring pour les pure players
- Impact : Pas de priorisation des acteurs clés LAI

### Objectif Global

Corriger RC1, RC2, RC3 au niveau runtime (matching & scoring) pour atteindre les objectifs MVP LAI, sans casser le pipeline Vectora Inbox et en restant générique (piloté par client_config + canonical).

---

## 2. Principes Directeurs

### Périmètre d'Intervention

**✅ Autorisé:**
- `canonical/matching/domain_matching_rules.yaml`
- `canonical/scopes/*.yaml` (si nécessaire)
- `src/vectora_core/matching/matcher.py`
- `src/vectora_core/scoring/scorer.py`
- `src/vectora_core/config/loader.py` / `resolver.py`
- `docs/diagnostics/*.md`
- `CHANGELOG.md`

**❌ Interdit:**
- Configuration Bedrock
- Lambdas d'ingest (normalize, enrich)
- Mécanisme général d'engine (orchestration)
- Infrastructure AWS (hors redéploiement Lambda engine)

### Contraintes

1. **Généricité:** Pas de hardcoding "LAI" dans le code
2. **Backward compatibility:** Ne pas casser les autres clients (si futurs)
3. **End-to-end:** Protéger le workflow ingest → engine → newsletter
4. **Traçabilité:** Documenter chaque phase avec diagnostics + CHANGELOG

---

## 3. Architecture du Plan

### 4 Phases Séquentielles

```
Phase 1: INSTRUMENTATION (P0.1)
   ↓ Logs détaillés, pas de changement fonctionnel
   
Phase 2: FILTRAGE CATÉGORIES (P0.2)
   ↓ Exclure generic_terms, appliquer negative_terms
   
Phase 3: FALLBACK & PURE_PLAYER (P0.3 + RC3)
   ↓ Durcir règle classique, exploiter scopes companies
   
Phase 4: TEST END-TO-END & MÉTRIQUES
   ↓ Validation complète, décision GO/NO-GO
```

### Durée Estimée

| Phase | Durée Estimée | Cumul |
|-------|---------------|-------|
| Phase 1 | 2h | 2h |
| Phase 2 | 3h | 5h |
| Phase 3 | 3h | 8h |
| Phase 4 | 2h | 10h |

**Total:** 10 heures (vs 6h estimées dans root cause analysis, ajustées pour tests)

---

## 4. Phase 1 — Instrumentation & Validation du Profile

### Objectif

Confirmer noir sur blanc, via logs, que :
1. `domain_matching_rules.yaml` est bien lu
2. Le profile `technology_complex` est bien sélectionné pour `tech_lai_ecosystem`
3. `lai_keywords` est bien chargé comme structure hiérarchique (7 catégories), PAS aplati

### Actions Techniques

#### 4.1. Ajouter logs dans matcher.py

**Fonction `_get_technology_profile()`:**
```python
logger.info(f"[PROFILE_DEBUG] Technology scope key: {technology_scope_key}")
logger.info(f"[PROFILE_DEBUG] Scope data type: {type(scope_data)}")
logger.info(f"[PROFILE_DEBUG] Metadata: {scope_data.get('_metadata', 'MISSING')}")
logger.info(f"[PROFILE_DEBUG] Profile detected: {metadata.get('profile', 'MISSING')}")
```

**Fonction `_evaluate_domain_match()`:**
```python
logger.info(f"[MATCHING_DEBUG] Domain: {domain_type}, Tech scope: {technology_scope_key}")
logger.info(f"[MATCHING_DEBUG] Profile name: {profile_name}")
logger.info(f"[MATCHING_DEBUG] Using profile matching: {profile_name is not None}")
```

**Fonction `_categorize_technology_keywords()`:**
```python
logger.info(f"[CATEGORY_DEBUG] Categories found: {list(scope_data.keys())}")
for category_name, keywords in scope_data.items():
    if category_name != '_metadata':
        logger.info(f"[CATEGORY_DEBUG] {category_name}: {len(keywords)} keywords")
```

#### 4.2. Aucun changement fonctionnel

Le comportement du matching reste identique, seuls les logs sont ajoutés.

### Fichiers Modifiés

- `src/vectora_core/matching/matcher.py` (ajout de logs uniquement)

### Déploiement

1. Modifier `matcher.py` localement
2. Repackager la Lambda : `python scripts/package_lambda.py`
3. Redéployer : `python scripts/deploy_lambda.py --env dev`
4. Vérifier le déploiement : `aws lambda get-function --function-name vectora-inbox-engine-dev`

### Tests

1. Lancer `python scripts/run_engine.py --env dev --client lai_weekly`
2. Consulter les logs CloudWatch :
   ```powershell
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[PROFILE_DEBUG]"
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[MATCHING_DEBUG]"
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[CATEGORY_DEBUG]"
   ```

### Critères de Succès

✅ **Profile détecté:**
- Log `[PROFILE_DEBUG] Profile detected: technology_complex` présent
- Log `[MATCHING_DEBUG] Using profile matching: True` présent

✅ **Structure hiérarchique préservée:**
- Log `[CATEGORY_DEBUG] Categories found: ['core_phrases', 'technology_terms_high_precision', ...]` présent
- 7 catégories listées (pas une liste plate)

✅ **Pas d'erreur runtime:**
- Exécution Lambda réussie
- Newsletter générée

### Livrables

- `docs/diagnostics/vectora_inbox_lai_runtime_phase1_instrumentation_results.md`
- Mise à jour `CHANGELOG.md` (section Phase 1)

### Risques

🟢 **Aucun risque fonctionnel** (logs seulement)

---

## 5. Phase 2 — Filtrage des Catégories (generic_terms / negative_terms)

### Objectif

Faire en sorte que :
1. `generic_terms` ne puissent jamais matcher seuls
2. `negative_terms` puissent annuler un match
3. Les signaux utilisés pour matcher soient prioritairement : `core_phrases`, `technology_terms_high_precision`, `technology_use`, `route_admin_terms`, `interval_patterns`

### Actions Techniques

#### 5.1. Modifier la logique de comptage des signaux

**Dans `_evaluate_technology_profile_match()`:**

```python
# Exclure generic_terms du comptage high_precision et supporting
excluded_categories = ['generic_terms', '_metadata']

high_precision_count = 0
for cat in high_precision_signals:
    if cat not in excluded_categories and cat in category_matches:
        high_precision_count += len(category_matches[cat])
        logger.debug(f"[SIGNAL_COUNT] High precision: {cat} = {len(category_matches[cat])}")

supporting_count = 0
for cat in supporting_signals:
    if cat not in excluded_categories and cat in category_matches:
        supporting_count += len(category_matches[cat])
        logger.debug(f"[SIGNAL_COUNT] Supporting: {cat} = {len(category_matches[cat])}")
```

#### 5.2. Implémenter le veto negative_terms

**Dans `_evaluate_technology_profile_match()`:**

```python
# Vérifier negative_terms
negative_detected = category_matches.get('negative_terms', [])
if negative_detected:
    logger.info(f"[NEGATIVE_VETO] Match rejected due to negative terms: {negative_detected}")
    return False, {
        'matched': False,
        'rule_applied': profile_name,
        'match_confidence': 'rejected_negative',
        'negative_terms_detected': negative_detected
    }
```

#### 5.3. Logger les signaux utilisés

```python
logger.info(f"[SIGNAL_SUMMARY] High precision: {high_precision_count}, Supporting: {supporting_count}")
logger.info(f"[SIGNAL_SUMMARY] Categories used: {[c for c in category_matches.keys() if c not in excluded_categories]}")
```

### Fichiers Modifiés

- `src/vectora_core/matching/matcher.py` (logique de filtrage)

### Déploiement

1. Modifier `matcher.py` localement
2. Repackager + redéployer Lambda
3. Vérifier le déploiement

### Tests

1. Lancer `python scripts/run_engine.py --env dev --client lai_weekly`
2. Analyser la nouvelle newsletter :
   ```powershell
   aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/latest/newsletter.json .
   python scripts/analyze_newsletter.py newsletter.json
   ```
3. Vérifier les logs :
   ```powershell
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[NEGATIVE_VETO]"
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[SIGNAL_COUNT]"
   ```

### Critères de Succès

✅ **generic_terms exclus:**
- Items avec seulement "PEG" ou "liposomes" ne matchent plus
- Log `[SIGNAL_COUNT]` ne compte pas `generic_terms`

✅ **negative_terms appliqués:**
- Items avec "oral tablet" sont rejetés
- Log `[NEGATIVE_VETO]` présent pour ces items

✅ **Amélioration métrique:**
- Précision LAI > 0% (objectif minimum : 20%)
- Faux positifs < 2/5

### Livrables

- `docs/diagnostics/vectora_inbox_lai_runtime_phase2_filtering_results.md`
- Mise à jour `CHANGELOG.md` (section Phase 2)

### Risques

🟡 **Réduction du recall:** Vrais positifs potentiellement rejetés si trop strict

**Mitigation:** Analyser les items rejetés dans les logs pour ajuster si nécessaire

---

## 6. Phase 3 — Durcissement Fallback & Exploitation Pure_Player/Hybrid

### Objectif

1. Rendre la règle de fallback plus stricte (pour les cas où le profile ne fonctionne pas)
2. Exploiter les scopes `lai_companies_pure_players` (14) et `lai_companies_hybrid` (27)
3. Appliquer une logique métier différenciée :
   - **Pure player:** 1 signal LAI fort peut suffire
   - **Hybrid:** exiger au moins 2 signaux indépendants

### Actions Techniques

#### 6.1. Durcir la règle de fallback classique

**Dans `canonical/matching/domain_matching_rules.yaml`:**

```yaml
technology:
  match_mode: all_required
  dimensions:
    technology:
      requirement: required
      min_matches: 2  # Au lieu de 1
    entity:
      requirement: required
      min_matches: 1
```

#### 6.2. Adapter le matching pour pure_player vs hybrid

**Dans `_evaluate_technology_profile_match()`:**

```python
# Identifier le type de company
company_scope_type = matching_details.get('scopes_hit', {}).get('company_scope_type', 'other')

# Ajuster les seuils selon le type
if company_scope_type == 'pure_player':
    # Pure player : 1 signal fort suffit
    min_high_precision = 1
    min_supporting = 0
    logger.info(f"[COMPANY_TYPE] Pure player detected, using relaxed thresholds")
elif company_scope_type == 'hybrid':
    # Hybrid : 2 signaux indépendants requis
    min_high_precision = 1
    min_supporting = 1
    logger.info(f"[COMPANY_TYPE] Hybrid detected, using strict thresholds")
else:
    # Fallback : règle standard
    min_high_precision = signal_reqs.get('min_high_precision_signals', 1)
    min_supporting = signal_reqs.get('min_supporting_signals', 1)
```

#### 6.3. Améliorer le bonus de scoring pour pure players

**Dans `src/vectora_core/scoring/scorer.py`, fonction `_compute_company_scope_bonus()`:**

```python
# Fallback amélioré : utiliser les nouveaux scopes
if matching_details is None:
    # Vérifier manuellement si pure player
    companies_match = item.get('companies_match', [])
    pure_player_scope = canonical_scopes.get('companies', {}).get('lai_companies_pure_players', [])
    
    for company in companies_match:
        if company in pure_player_scope:
            logger.info(f"[SCORING_FALLBACK] Pure player bonus applied: {company}")
            return other_factors.get('pure_player_bonus', 3)
    
    return 0
```

### Fichiers Modifiés

- `canonical/matching/domain_matching_rules.yaml` (règle fallback)
- `src/vectora_core/matching/matcher.py` (seuils adaptatifs)
- `src/vectora_core/scoring/scorer.py` (bonus fallback)

### Déploiement

1. Uploader la nouvelle config canonical :
   ```powershell
   aws s3 cp canonical/matching/domain_matching_rules.yaml s3://vectora-inbox-config-dev/canonical/matching/
   ```
2. Modifier `matcher.py` et `scorer.py` localement
3. Repackager + redéployer Lambda

### Tests

1. Lancer `python scripts/run_engine.py --env dev --client lai_weekly`
2. Analyser la newsletter :
   ```powershell
   python scripts/analyze_newsletter.py newsletter.json --check-pure-players
   ```
3. Vérifier les logs :
   ```powershell
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[COMPANY_TYPE]"
   aws logs tail /aws/lambda/vectora-inbox-engine-dev --since 1h --filter-pattern "[SCORING_FALLBACK]"
   ```

### Critères de Succès

✅ **Pure players favorisés:**
- Au moins 1 pure player (MedinCell, Camurus, etc.) dans les résultats
- Pure player % > 0%

✅ **Hybrid filtrés:**
- Items hybrid sans signaux forts rejetés
- Moins de faux positifs sur big pharma

✅ **Amélioration métrique:**
- Précision LAI ≥ 50%
- Pure player % ≥ 30%

### Livrables

- `docs/diagnostics/vectora_inbox_lai_runtime_phase3_matching_results.md`
- Mise à jour `CHANGELOG.md` (section Phase 3)

### Risques

🟡 **Seuils trop stricts:** Risque de rejeter des vrais positifs hybrid

**Mitigation:** Analyser les items rejetés et ajuster les seuils si nécessaire

---

## 7. Phase 4 — Test End-to-End & Métriques LAI

### Objectif

1. Relancer un run complet `lai_weekly` en DEV
2. Mesurer : précision LAI, % pure players, faux positifs
3. Décider : MVP LAI en DEV = RED / AMBER / GREEN ?

### Actions Techniques

#### 7.1. Repackage & redéploiement complet

```powershell
# Repackager la Lambda avec toutes les corrections
python scripts/package_lambda.py

# Redéployer
python scripts/deploy_lambda.py --env dev

# Vérifier
aws lambda get-function --function-name vectora-inbox-engine-dev
```

#### 7.2. Lancer les tests (lai_weekly, 7 jours)

```powershell
# Exécuter l'engine
python scripts/run_engine.py --env dev --client lai_weekly

# Télécharger la newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly/latest/newsletter.json .

# Analyser les résultats
python scripts/analyze_newsletter.py newsletter.json --detailed
```

#### 7.3. Calculer les métriques finales

**Métriques à mesurer:**
- Items analyzed
- Items matched
- Items selected
- **LAI precision** (% vrais positifs LAI)
- **Pure player %** (% pure players dans les résultats)
- **False positives** (nombre de faux positifs manifestes)

**Validation manuelle:**
- Examiner chaque item sélectionné
- Classifier : vrai LAI / faux positif
- Identifier : pure player / hybrid / autre

### Critères de Succès MVP LAI

| Métrique | Objectif | Status |
|----------|----------|--------|
| LAI precision | ≥80% | ? |
| Pure player % | ≥50% | ? |
| False positives | 0 | ? |

**Décision GO/NO-GO:**
- 🟢 **GREEN (GO PROD):** Les 3 objectifs atteints
- 🟡 **AMBER (ITERATION):** 2/3 objectifs atteints, itération mineure nécessaire
- 🔴 **RED (NO-GO):** <2 objectifs atteints, refonte nécessaire

### Livrables

- `docs/diagnostics/vectora_inbox_lai_runtime_phase4_final_results_v2.md`
- Mise à jour de :
  - `docs/diagnostics/lai_weekly_mvp_recentrage_summary.md`
  - `docs/diagnostics/vectora_inbox_lai_runtime_adaptation_complete_summary.md`
  - `CHANGELOG.md` (section Phase 4 + résumé global)

### Risques

🟢 **Aucun risque technique** (validation finale)

---

## 8. Rollback Plan

### Si Phase 1 Échoue (Profile non détecté)

**Symptôme:** Logs montrent que `profile = None` ou `profile = 'MISSING'`

**Actions:**
1. Vérifier la structure de `technology_scopes.yaml` dans S3
2. Vérifier le chargement dans `loader.py`
3. Corriger le problème identifié
4. Redéployer et retester

**Durée:** +2h

### Si Phase 2 Échoue (Précision toujours à 0%)

**Symptôme:** Aucune amélioration de la précision LAI après filtrage

**Actions:**
1. Analyser les logs pour comprendre pourquoi les signaux ne sont pas comptés
2. Vérifier que les catégories sont bien exclues
3. Ajuster la logique de filtrage
4. Redéployer et retester

**Durée:** +3h

### Si Phase 3 Échoue (Pas de pure players)

**Symptôme:** Pure player % toujours à 0%

**Actions:**
1. Vérifier que les scopes `lai_companies_pure_players` sont bien chargés
2. Vérifier que le bonus de scoring est appliqué
3. Ajuster les seuils de matching pour pure players
4. Redéployer et retester

**Durée:** +2h

### Rollback Complet (Si échec critique)

**Quand utiliser:** Si les corrections causent des erreurs runtime ou cassent le pipeline

**Actions:**
1. Restaurer la version Lambda précédente :
   ```powershell
   aws lambda update-function-code --function-name vectora-inbox-engine-dev --s3-bucket vectora-inbox-lambda-packages-dev --s3-key engine/previous_version.zip
   ```
2. Restaurer la configuration canonical précédente :
   ```powershell
   aws s3 cp s3://vectora-inbox-config-dev/canonical/matching/domain_matching_rules.yaml.backup s3://vectora-inbox-config-dev/canonical/matching/domain_matching_rules.yaml
   ```
3. Documenter l'échec dans `docs/diagnostics/rollback_report.md`

**Durée:** 30 minutes

---

## 9. Success Metrics & KPIs

### Métriques Techniques

| Métrique | Avant | Objectif Après | Mesure |
|----------|-------|----------------|--------|
| Profile activé | Non | Oui | Logs CloudWatch |
| Catégories filtrées | Non | Oui | Logs CloudWatch |
| Pure player bonus | Non | Oui | Logs CloudWatch |
| Exécution Lambda | 17.6s | <20s | CloudWatch Metrics |

### Métriques Business

| Métrique | Avant | Objectif Après | Mesure |
|----------|-------|----------------|--------|
| LAI precision | 0% | ≥80% | Analyse newsletter |
| Pure player % | 0% | ≥50% | Analyse newsletter |
| False positives | 2/5 | 0 | Analyse newsletter |
| Items matched | 6 (12%) | 8-12 (16-24%) | Analyse newsletter |

### Métriques de Qualité

| Métrique | Objectif | Mesure |
|----------|----------|--------|
| Documentation complète | 100% | 4 fichiers diagnostics |
| CHANGELOG à jour | 100% | 4 entrées (1 par phase) |
| Pas de breaking change | 100% | Tests end-to-end |
| Backward compatible | 100% | Autres clients non impactés |

---

## 10. Lessons Learned & Recommandations Futures

### Points d'Amélioration Identifiés

1. **Validation insuffisante avant déploiement:** Pas de logs debug initiaux
2. **Tests manquants:** Pas de tests unitaires pour profile matching
3. **Vérification structure:** Pas de validation que scopes chargés correctement

### Recommandations pour Futurs Clients

1. **Ajouter logs debug systématiquement** dans matcher.py avant premier déploiement
2. **Créer tests unitaires** pour profile matching (P2.1)
3. **Valider structure scopes** après chargement (P2.2)
4. **Tester en local** avec données mockées avant déploiement AWS
5. **Créer un outil de diagnostic** des scopes (P2.2)

### Améliorations P2 (Post-MVP)

**P2.1 - Tests unitaires pour profile matching:**
- Créer `tests/test_matcher_profiles.py`
- Tester `_get_technology_profile()` avec différentes structures
- Tester `_evaluate_technology_profile_match()` avec différents signaux

**P2.2 - Outil de diagnostic des scopes:**
- Créer `tools/diagnose_scopes.py`
- Charger les scopes depuis S3
- Valider leur structure
- Tester le matching sur des exemples connus

---

## 11. Résumé Exécutif

### Problème

Précision LAI à 0% après refactor canonical + adaptation runtime, causée par 3 root causes :
- RC1 : Profile technology_complex jamais activé
- RC2 : generic_terms et negative_terms non filtrés
- RC3 : Distinction pure_player/hybrid non exploitée

### Solution

Plan en 4 phases pour corriger les root causes :
1. **Phase 1 (2h):** Instrumentation pour diagnostiquer RC1
2. **Phase 2 (3h):** Filtrage des catégories pour corriger RC2
3. **Phase 3 (3h):** Exploitation pure_player/hybrid pour corriger RC3
4. **Phase 4 (2h):** Validation end-to-end et métriques

### Durée Totale

10 heures (incluant tests et documentation)

### Risques

🟢 Faibles : Approche incrémentale, rollback possible à chaque phase

### Décision Attendue

Après Phase 4 : GO PROD / ITERATION / NO-GO selon les métriques finales

---

**Status:** ✅ PLAN READY FOR EXECUTION  
**Next Step:** VALIDATION DU PLAN PAR LE CLIENT, PUIS LANCEMENT PHASE 1

