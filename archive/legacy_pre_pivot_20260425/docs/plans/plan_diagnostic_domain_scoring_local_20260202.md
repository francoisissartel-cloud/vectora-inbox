# Plan Diagnostic et Correction - Domain Scoring (Tests Locaux Obligatoires)

**Date**: 2026-02-02  
**Objectif**: Corriger le domain scoring avec validation locale AVANT tout déploiement AWS  
**Principe**: NO PUSH TO AWS WITHOUT LOCAL SUCCESS  
**Durée estimée**: 2-3 heures

---

## 🎯 PROBLÈME IDENTIFIÉ

### Symptômes
- `enable_domain_scoring: true` dans config ✅
- Flag `has_domain_scoring=False` dans tous les items ❌
- Temps exécution: 70s (1 appel Bedrock) au lieu de 200s+ (2 appels) ❌
- Erreur logs: "Impossible de charger les prompts canonical: argument of type 'NoneType' is not iterable"

### Cause Racine Suspectée
Le chargement des prompts `domain_scoring` échoue dans `config_loader.py`

### Erreur de Processus
- ❌ Déploiement AWS sans tests locaux
- ❌ Validation E2E uniquement en cloud
- ❌ Pas de tests unitaires pour config_loader
- ❌ Gestion d'erreur silencieuse (try/except cache le problème)

---

## 📋 PLAN D'EXÉCUTION

### Phase 1: Setup Environnement Local ⏱️ 15 min

**Objectif**: Préparer environnement de test local

**Actions**:
1. Créer script de test local: `tests/local/test_domain_scoring_local.py`
2. Télécharger fichiers S3 nécessaires en local:
   - `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
   - `canonical/domains/lai_domain_definition.yaml`
   - `canonical/prompts/normalization/generic_normalization.yaml`
   - `client-configs/lai_weekly_v9.yaml`
3. Créer mock S3 local ou utiliser fichiers locaux
4. Préparer 1-2 items de test (extraits de lai_weekly_v9)

**Livrables**:
- [ ] Script test local créé
- [ ] Fichiers canonical en local
- [ ] Items de test préparés

---

### Phase 2: Test Unitaire config_loader ⏱️ 30 min

**Objectif**: Identifier EXACTEMENT pourquoi le chargement échoue

**Actions**:
1. Créer test unitaire: `tests/unit/test_config_loader_domain_scoring.py`
2. Tester `load_canonical_prompts()`:
   ```python
   def test_load_canonical_prompts_domain_scoring():
       prompts = config_loader.load_canonical_prompts('vectora-inbox-config-dev')
       
       # Vérifications
       assert prompts is not None
       assert 'domain_scoring' in prompts
       assert 'lai_domain_scoring' in prompts['domain_scoring']
       assert prompts['domain_scoring']['lai_domain_scoring'] is not None
   ```

3. Tester `load_canonical_scopes()`:
   ```python
   def test_load_canonical_scopes_domains():
       scopes = config_loader.load_canonical_scopes('vectora-inbox-config-dev')
       
       # Vérifications
       assert scopes is not None
       assert 'domains' in scopes
       assert 'lai_domain_definition' in scopes['domains']
       assert scopes['domains']['lai_domain_definition'] is not None
   ```

4. Ajouter logs détaillés dans config_loader.py:
   ```python
   logger.info(f"Prompts loaded: {list(prompts.keys())}")
   logger.info(f"Domain_scoring keys: {list(prompts.get('domain_scoring', {}).keys())}")
   ```

5. Exécuter tests locaux et capturer output

**Livrables**:
- [ ] Tests unitaires créés
- [ ] Cause exacte identifiée
- [ ] Logs détaillés capturés

---

### Phase 3: Correction Code ⏱️ 30 min

**Objectif**: Corriger le problème identifié

**Scénarios possibles**:

**Scénario A: Structure S3 incorrecte**
- Vérifier que les fichiers sont au bon endroit
- Vérifier la structure YAML (indentation, clés)
- Corriger si nécessaire

**Scénario B: config_loader ne charge pas domain_scoring**
- Modifier `load_canonical_prompts()` pour inclure domain_scoring
- Ajouter logique de chargement récursif si nécessaire

**Scénario C: Structure retournée incorrecte**
- Vérifier format attendu vs format réel
- Adapter code normalizer si nécessaire

**Actions communes**:
1. Corriger le code identifié
2. Ajouter validation stricte (fail-fast si prompts manquants)
3. Améliorer gestion d'erreur (logs explicites)
4. Retirer try/except silencieux

**Livrables**:
- [ ] Code corrigé
- [ ] Validation stricte ajoutée
- [ ] Logs améliorés

---

### Phase 4: Test Local Complet ⏱️ 45 min

**Objectif**: Valider le fix en local AVANT déploiement

**Actions**:
1. Créer script test E2E local: `tests/local/test_e2e_domain_scoring.py`
   ```python
   def test_normalize_with_domain_scoring():
       # Setup
       raw_items = load_test_items()  # 2-3 items
       client_config = load_local_config('lai_weekly_v9.yaml')
       canonical_scopes = load_local_canonical_scopes()
       canonical_prompts = load_local_canonical_prompts()
       
       # Vérifications pré-test
       assert client_config['bedrock_config']['enable_domain_scoring'] == True
       assert 'domain_scoring' in canonical_prompts
       assert 'domains' in canonical_scopes
       
       # Exécution
       normalized_items = normalizer.normalize_items_batch(
           raw_items,
           canonical_scopes,
           canonical_prompts,
           bedrock_model="anthropic.claude-3-sonnet-20240229-v1:0",
           bedrock_region="us-east-1",
           enable_domain_scoring=True
       )
       
       # Validations
       assert len(normalized_items) > 0
       for item in normalized_items:
           assert 'has_domain_scoring' in item
           assert item['has_domain_scoring'] == True
           assert 'domain_scoring' in item
           assert 'is_relevant' in item['domain_scoring']
           assert 'score' in item['domain_scoring']
           assert 'confidence' in item['domain_scoring']
           assert 'signals_detected' in item['domain_scoring']
           assert 'reasoning' in item['domain_scoring']
   ```

2. Exécuter test local avec Bedrock réel (2-3 items max)
3. Vérifier structure domain_scoring complète
4. Mesurer temps exécution (doit être ~2x vs 1 appel)
5. Valider qualité du reasoning

**Critères de succès**:
- [ ] Test passe sans erreur
- [ ] domain_scoring présent dans 100% des items
- [ ] has_domain_scoring=True pour tous
- [ ] Temps exécution cohérent (2 appels Bedrock)
- [ ] Reasoning pertinent et clair

**Livrables**:
- [ ] Test E2E local créé
- [ ] Test passe avec succès
- [ ] Métriques collectées

---

### Phase 5: Build et Tests Layer Local ⏱️ 20 min

**Objectif**: Valider le layer avant déploiement

**Actions**:
1. Build layer local:
   ```bash
   python scripts/layers/create_vectora_core_layer.py --local-only
   ```

2. Extraire layer et vérifier contenu:
   ```bash
   unzip -l output/layers/vectora-inbox-vectora-core-dev.zip | grep normalizer
   unzip -l output/layers/vectora-inbox-vectora-core-dev.zip | grep config_loader
   ```

3. Tester import depuis layer:
   ```python
   import sys
   sys.path.insert(0, 'path/to/extracted/layer/python')
   from vectora_core.normalization import normalizer
   from vectora_core.shared import config_loader
   # Vérifier versions
   ```

4. Simuler environnement Lambda local (optionnel):
   ```bash
   sam local invoke normalize-score-v2 --event test_event.json
   ```

**Livrables**:
- [ ] Layer buildé localement
- [ ] Contenu vérifié
- [ ] Imports testés

---

### Phase 6: Déploiement AWS (SI ET SEULEMENT SI Phase 4 OK) ⏱️ 15 min

**Pré-requis OBLIGATOIRES**:
- ✅ Tests unitaires passent
- ✅ Test E2E local passe
- ✅ domain_scoring présent dans items
- ✅ has_domain_scoring=True
- ✅ Temps exécution cohérent

**Actions**:
1. Incrémenter version: 1.4.0 → 1.4.1 (PATCH)
2. Build layer: `python scripts/layers/create_vectora_core_layer.py`
3. Deploy dev: `python scripts/deploy/deploy_env.py --env dev`
4. Vérifier layer ARN mis à jour sur Lambda

**Livrables**:
- [ ] Layer v52 déployé
- [ ] Lambda mise à jour
- [ ] Version 1.4.1 taguée

---

### Phase 7: Test E2E AWS ⏱️ 20 min

**Objectif**: Valider en environnement réel

**Actions**:
1. Test lai_weekly_v9 complet (28 items):
   ```bash
   python scripts/invoke/invoke_normalize_score_v2.py --event lai_weekly_v9
   ```

2. Télécharger résultats:
   ```bash
   aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v9/2026/02/02/items.json .tmp/
   ```

3. Analyser résultats:
   ```python
   # Vérifier domain_scoring présent
   # Vérifier has_domain_scoring=True
   # Vérifier temps exécution
   # Vérifier logs CloudWatch
   ```

4. Comparer v8 (baseline) vs v9 (domain scoring):
   ```bash
   python .tmp/analyse_v8_vs_v9.py
   ```

**Critères de succès**:
- [ ] 28/28 items avec domain_scoring
- [ ] 28/28 items avec has_domain_scoring=True
- [ ] Temps exécution 180-250s (2 appels × 28 items)
- [ ] Aucune erreur dans logs
- [ ] Matching amélioré vs v8

**Livrables**:
- [ ] Test E2E AWS réussi
- [ ] Rapport comparatif v8 vs v9
- [ ] Métriques validées

---

### Phase 8: Documentation et Rapport ⏱️ 15 min

**Objectif**: Documenter le fix et les leçons apprises

**Actions**:
1. Créer rapport: `docs/reports/development/fix_domain_scoring_20260202.md`
2. Documenter:
   - Cause racine exacte
   - Solution implémentée
   - Tests ajoutés
   - Leçons apprises
3. Mettre à jour plan refactoring avec statut final
4. Commit et push:
   ```bash
   git add .
   git commit -m "fix: Domain scoring not executed - config_loader issue
   
   - Add unit tests for config_loader
   - Fix domain_scoring prompts loading
   - Add strict validation (fail-fast)
   - Improve error logging
   - Add local E2E test
   
   Tests: All local tests pass before AWS deployment"
   ```

**Livrables**:
- [ ] Rapport fix créé
- [ ] Tests documentés
- [ ] Code commité

---

## 🔒 RÈGLES STRICTES

### Tests Locaux Obligatoires
1. **AUCUN déploiement AWS sans tests locaux passants**
2. **AUCUN build layer sans tests unitaires OK**
3. **AUCUN push code sans validation locale**

### Validation Multi-Niveaux
1. Tests unitaires (config_loader, normalizer)
2. Tests intégration (chargement prompts + normalisation)
3. Tests E2E local (2-3 items avec Bedrock)
4. Tests E2E AWS (dataset complet)

### Fail-Fast
1. Arrêter immédiatement si prompts manquants
2. Logger explicitement chaque étape
3. Pas de try/except silencieux
4. Validation stricte des structures

---

## 📊 MÉTRIQUES DE SUCCÈS

### Tests Locaux
- [ ] 100% tests unitaires passent
- [ ] Test E2E local passe (2-3 items)
- [ ] domain_scoring présent localement
- [ ] Temps cohérent (2 appels Bedrock)

### Tests AWS
- [ ] 100% items avec domain_scoring
- [ ] 100% items avec has_domain_scoring=True
- [ ] Temps exécution dans fourchette attendue
- [ ] Logs sans erreur
- [ ] Matching amélioré vs baseline

### Qualité
- [ ] Tests unitaires ajoutés
- [ ] Documentation complète
- [ ] Leçons apprises documentées
- [ ] Processus amélioré

---

## 🎓 LEÇONS APPRISES (À DOCUMENTER)

1. **Toujours tester localement avant AWS**
2. **Tests unitaires pour config_loader obligatoires**
3. **Validation stricte > gestion d'erreur permissive**
4. **Logs détaillés à chaque étape critique**
5. **Fail-fast > continue silencieusement**

---

## 📁 FICHIERS À CRÉER

### Tests
- `tests/unit/test_config_loader_domain_scoring.py`
- `tests/local/test_domain_scoring_local.py`
- `tests/local/test_e2e_domain_scoring.py`

### Scripts
- `scripts/test/run_local_tests.py` (runner pour tous les tests locaux)

### Documentation
- `docs/reports/development/fix_domain_scoring_20260202.md`
- `docs/testing/local_testing_guide.md` (guide tests locaux)

---

**Prochaine action**: Phase 1 - Setup environnement local
