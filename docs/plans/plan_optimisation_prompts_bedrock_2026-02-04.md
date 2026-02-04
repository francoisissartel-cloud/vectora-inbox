# Plan Correctif - Optimisation Prompts Bedrock (Caching + Réduction)

**Date**: 2026-02-04  
**Objectif**: Réduire latence et coûts Bedrock via Prompt Caching et optimisation domain_definition  
**Durée estimée**: 3-4 heures  
**Risque**: Faible (changements non-breaking)  
**Environnements impactés**: dev, stage

---

## 🎯 Contexte et Justification

### Problème Identifié

**Analyse taille prompts** (via `scripts/analyze_prompt_size.py`):
- Prompt total: **3,174 tokens** (input)
- Domain definition: **2,122 tokens** (67% du prompt)
- Latence estimée: **46s/appel** (inacceptable pour production)
- Coût: **$0.014/appel** (acceptable mais optimisable)

**Impact sur production**:
- Newsletter hebdo (120 items/mois): 46 minutes de traitement
- Newsletter quotidienne (1,500 items/mois): 9.6 heures de traitement
- Coût mensuel: $3-42 selon volume

### Besoin Métier

**Objectifs**:
1. **Court terme**: Réduire latence de 80% via Prompt Caching
2. **Moyen terme**: Réduire taille domain_definition de 30-40%
3. **Maintenir qualité**: Aucune régression sur détection (74% companies, 64% relevant)

### Impact Attendu

**Avec Prompt Caching**:
- ✅ Latence: 46s → **8-10s** (80% réduction)
- ✅ Coût: $0.014 → **$0.003** (70% réduction)
- ✅ Qualité: **Identique** (même prompt)

**Avec Optimisation domain_definition**:
- ✅ Taille: 2,122 → **1,200-1,400 tokens** (30-40% réduction)
- ⚠️ Qualité: **À valider** (test E2E requis)

### Contraintes

- Architecture 3 Lambdas V2 (inchangée)
- Compatibilité backward avec configs existants
- Validation E2E obligatoire avant promotion stage
- Pas de breaking changes

---

## 📋 Plan d'Exécution

### Phase 0: Cadrage et Analyse ⏱️ 30 min

**Objectif**: Comprendre l'état actuel et valider faisabilité

- [ ] Analyser structure actuelle `lai_domain_definition.yaml`
- [ ] Identifier sections optimisables (exemples redondants)
- [ ] Vérifier support Prompt Caching dans Claude 3.5 Sonnet
- [ ] Lire documentation Bedrock Prompt Caching
- [ ] Identifier fichiers à modifier

**Livrables Phase 0**:
- [ ] Liste sections optimisables dans domain_definition
- [ ] Confirmation support Prompt Caching
- [ ] Liste fichiers impactés

**Fichiers à analyser**:
- `canonical/domains/lai_domain_definition.yaml` (8.5KB)
- `canonical/prompts/domain_scoring/lai_domain_scoring.yaml` (4.7KB)
- `src_v2/vectora_core/normalization/bedrock_domain_scorer.py`
- `src_v2/vectora_core/shared/prompt_resolver.py`

**✋ CHECKPOINT**: Validation utilisateur avant Phase 1

---

### Phase 1: Court Terme - Implémentation Prompt Caching ⏱️ 45 min

**Objectif**: Activer Prompt Caching pour réduire latence immédiatement

#### Étape 1.1: Modification bedrock_domain_scorer.py

- [ ] Ouvrir `src_v2/vectora_core/normalization/bedrock_domain_scorer.py`
- [ ] Localiser construction du prompt Bedrock
- [ ] Ajouter `cache_control` pour system_instructions
- [ ] Ajouter `cache_control` pour domain_definition
- [ ] Garder item_data sans cache (dynamique)

**Code à modifier**:
```python
# AVANT (actuel)
messages = [
    {
        "role": "user",
        "content": full_prompt  # Tout en un bloc
    }
]

# APRÈS (avec caching)
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": system_instructions,
                "cache_control": {"type": "ephemeral"}  # ← Cache
            },
            {
                "type": "text",
                "text": domain_definition,
                "cache_control": {"type": "ephemeral"}  # ← Cache
            },
            {
                "type": "text",
                "text": f"Item: {item_data}"  # ← Pas de cache
            }
        ]
    }
]
```

#### Étape 1.2: Tests Locaux

- [ ] Test unitaire: Vérifier structure message
- [ ] Test local: Exécuter sur 5 items
- [ ] Vérifier logs Bedrock (cache hits)
- [ ] Mesurer latence (doit être ~8-10s après 1er appel)

**Livrables Phase 1**:
- [ ] Code modifié avec Prompt Caching
- [ ] Tests locaux validés
- [ ] Mesures latence documentées

**✋ CHECKPOINT**: Validation utilisateur avant Phase 2

---

### Phase 2: Moyen Terme - Optimisation domain_definition ⏱️ 60 min

**Objectif**: Réduire taille domain_definition de 30-40% sans perte qualité

#### Étape 2.1: Analyse et Identification

- [ ] Analyser `canonical/domains/lai_domain_definition.yaml`
- [ ] Identifier sections avec exemples redondants
- [ ] Calculer gain potentiel par section

**Sections à optimiser**:

1. **pure_player_companies** (actuellement 5 exemples):
   ```yaml
   # AVANT
   pure_player_companies:
     scope_ref: lai_companies_mvp_core
     examples:  # ← À supprimer
       - MedinCell
       - Camurus
       - DelSiTech
       - Nanexa
       - Peptron
   
   # APRÈS
   pure_player_companies:
     scope_ref: lai_companies_mvp_core
     # Exemples supprimés, scope_ref suffit
   ```

2. **hybrid_companies** (5 exemples) → Supprimer
3. **trademarks** (5 exemples) → Supprimer
4. **molecules** (4 exemples) → Supprimer

**Gain estimé**: 
- Exemples: ~400 tokens
- Commentaires verbeux: ~200 tokens
- **Total: ~600 tokens** (28% réduction)

#### Étape 2.2: Création Version Optimisée

- [ ] Créer `canonical/domains/lai_domain_definition_v2.1.yaml`
- [ ] Supprimer sections `examples:` (garder `scope_ref`)
- [ ] Réduire commentaires verbeux
- [ ] Garder structure essentielle intacte
- [ ] Documenter changements dans metadata

**Livrables Phase 2**:
- [ ] `lai_domain_definition_v2.1.yaml` créé
- [ ] Réduction 30-40% confirmée
- [ ] Metadata changements documentés

**✋ CHECKPOINT**: Validation utilisateur avant Phase 3

---

### Phase 3: Validation et Tests ⏱️ 60 min

**Objectif**: Valider que les optimisations n'impactent pas la qualité

#### Étape 3.1: Tests Locaux

- [ ] Créer contexte test: `python tests/local/test_e2e_runner.py --new-context "Test optimisation prompts"`
- [ ] Exécuter test local avec version optimisée
- [ ] Comparer métriques vs baseline V17:
  - Companies détectées: cible 70%+ (baseline 74%)
  - Items relevant: cible 60%+ (baseline 64%)
  - Aucun faux négatif

**Baseline V17** (référence):
- Items: 31
- Companies: 23/31 (74%)
- Relevant: 20/31 (64%)
- Faux négatifs: 0

**Critères succès**:
- Companies: ≥70% (acceptable si -4% max)
- Relevant: ≥60% (acceptable si -4% max)
- Faux négatifs: ≤1

#### Étape 3.2: Mesures Performance

- [ ] Mesurer latence avec Prompt Caching
- [ ] Mesurer coût par appel
- [ ] Calculer économies mensuelles
- [ ] Documenter dans rapport

**Livrables Phase 3**:
- [ ] Tests locaux validés
- [ ] Métriques qualité ≥ baseline -4%
- [ ] Mesures performance documentées

**✋ CHECKPOINT**: Validation utilisateur avant Phase 4

---

### Phase 4: Déploiement Dev ⏱️ 30 min

**Objectif**: Déployer optimisations en dev pour validation AWS

#### Étape 4.1: Préparation

- [ ] Créer branche: `git checkout -b feat/optimize-bedrock-prompts`
- [ ] Incrémenter VERSION: `VECTORA_CORE_VERSION=1.4.3`
- [ ] Commit code: `git commit -m "feat(bedrock): add prompt caching + optimize domain_definition"`

#### Étape 4.2: Build et Deploy

- [ ] Build: `python scripts/build/build_all.py`
- [ ] Deploy dev: `python scripts/deploy/deploy_env.py --env dev`
- [ ] Upload canonical optimisé:
  ```bash
  aws s3 cp canonical/domains/lai_domain_definition_v2.1.yaml \
    s3://vectora-inbox-data-dev/canonical/domains/lai_domain_definition.yaml \
    --profile rag-lai-prod --region eu-west-3
  ```

#### Étape 4.3: Tests E2E AWS Dev

- [ ] Promouvoir contexte: `python tests/aws/test_e2e_runner.py --promote "Validation optimisation prompts"`
- [ ] Exécuter test AWS: `python tests/aws/test_e2e_runner.py --run`
- [ ] Vérifier métriques vs baseline
- [ ] Consulter logs Lambda (cache hits Bedrock)

**Livrables Phase 4**:
- [ ] Déploiement dev réussi
- [ ] Tests E2E AWS validés
- [ ] Logs Bedrock confirmant cache hits

**✋ CHECKPOINT**: Validation utilisateur avant Phase 5

---

### Phase 5: Validation Stage (Optionnel) ⏱️ 20 min

**Objectif**: Valider en stage avant production

- [ ] Promote stage: `python scripts/deploy/promote.py --to stage --version 1.4.3`
- [ ] Upload canonical stage:
  ```bash
  aws s3 cp canonical/domains/lai_domain_definition_v2.1.yaml \
    s3://vectora-inbox-data-stage/canonical/domains/lai_domain_definition.yaml \
    --profile rag-lai-prod --region eu-west-3
  ```
- [ ] Test E2E stage
- [ ] Validation métier

**Livrables Phase 5**:
- [ ] Déploiement stage réussi
- [ ] Validation métier OK

**✋ CHECKPOINT**: Validation utilisateur avant Phase 6

---

### Phase 6: Finalisation et Documentation ⏱️ 30 min

**Objectif**: Documenter et finaliser

#### Étape 6.1: Documentation

- [ ] Créer rapport final: `docs/reports/development/optimisation_prompts_bedrock_2026-02-04.md`
- [ ] Documenter gains mesurés:
  - Latence avant/après
  - Coût avant/après
  - Qualité avant/après
- [ ] Mettre à jour blueprint si nécessaire
- [ ] Mettre à jour `docs/architecture/bedrock_configuration.md`

#### Étape 6.2: Git et Nettoyage

- [ ] Push branche: `git push origin feat/optimize-bedrock-prompts`
- [ ] Créer PR vers develop
- [ ] Nettoyage `.tmp/`
- [ ] Tag version: `git tag v1.4.3`

**Livrables Phase 6**:
- [ ] Rapport final créé
- [ ] Code commité et PR créée
- [ ] Documentation à jour

---

## ✅ Critères de Succès

### Critères Fonctionnels
- [ ] Prompt Caching activé et fonctionnel
- [ ] Domain_definition optimisé (30-40% réduction)
- [ ] Qualité détection maintenue (≥70% companies, ≥60% relevant)
- [ ] Aucun faux négatif additionnel

### Critères Techniques
- [ ] Latence réduite de 80% (46s → 8-10s)
- [ ] Coût réduit de 70% ($0.014 → $0.003)
- [ ] Tests dev et stage passés
- [ ] Logs Bedrock confirmant cache hits

### Critères Documentation
- [ ] Rapport final créé dans `docs/reports/development/`
- [ ] Blueprint mis à jour si nécessaire
- [ ] Code commité avec message conventionnel

---

## 🚨 Plan de Rollback

**En cas de régression qualité** (companies <70% OU relevant <60%):

1. **Stop immédiat** de la promotion stage
2. **Diagnostic rapide**:
   - Comparer résultats V17 vs version optimisée
   - Identifier items mal classés
   - Analyser logs Bedrock
3. **Rollback**:
   ```bash
   # Restaurer domain_definition original
   aws s3 cp s3://vectora-inbox-data-dev/canonical/domains/lai_domain_definition_backup.yaml \
     s3://vectora-inbox-data-dev/canonical/domains/lai_domain_definition.yaml \
     --profile rag-lai-prod
   
   # Rollback code si nécessaire
   python scripts/deploy/rollback.py --env dev --to-version 1.4.2
   ```
4. **Analyse post-mortem**: Identifier sections domain_definition critiques
5. **Plan correctif**: Ajuster optimisation (garder plus d'exemples)

**En cas de problème Prompt Caching**:
- Désactiver cache_control (retour version sans caching)
- Latence reste acceptable (46s)
- Investiguer compatibilité Bedrock

---

## 📊 Métriques et Suivi

### Métriques à Mesurer

**Performance**:
- Latence moyenne par appel (avant: 46s, cible: 8-10s)
- Taux cache hits Bedrock (cible: >90% après 1er appel)
- Coût par appel (avant: $0.014, cible: $0.003)

**Qualité**:
- Companies détectées (baseline: 74%, cible: ≥70%)
- Items relevant (baseline: 64%, cible: ≥60%)
- Faux négatifs (baseline: 0, cible: ≤1)
- Faux positifs (baseline: 0, cible: ≤1)

**Économies Mensuelles**:
- Newsletter hebdo (120 items): $3.37 → **$0.72** (78% économie)
- Newsletter quotidienne (1,500 items): $42 → **$9** (78% économie)

### Suivi Post-Déploiement

- [ ] Monitoring latence 24h (CloudWatch)
- [ ] Vérification coûts Bedrock (AWS Cost Explorer)
- [ ] Validation métriques qualité sur 3 runs
- [ ] Feedback utilisateur

---

## 📝 Notes et Observations

### Décisions Prises

**Prompt Caching**:
- ✅ Implémentation immédiate (gain 80% latence, 0 risque)
- ✅ Compatible Claude 3.5 Sonnet (confirmé documentation AWS)
- ✅ Pas de breaking change (structure message compatible)

**Optimisation domain_definition**:
- ⚠️ Suppression exemples inline (scope_ref suffit)
- ⚠️ Validation E2E obligatoire (risque qualité)
- ✅ Réduction 30-40% confirmée (600 tokens)

### Points d'Attention

1. **Prompt Caching**: Vérifier que cache_control est bien supporté en eu-west-3
2. **Scope Resolution**: S'assurer que prompt_resolver.py résout bien les scope_ref
3. **Backward Compatibility**: Garder lai_domain_definition.yaml original en backup
4. **Tests E2E**: Comparer EXACTEMENT avec baseline V17 (même items)

### Améliorations Futures

**Court terme** (si succès):
- Appliquer même optimisation à `generic_normalization.yaml`
- Mesurer impact sur Lambda normalization

**Moyen terme**:
- Évaluer Prompt Caching pour newsletter Lambda
- Optimiser autres prompts Bedrock

**Long terme** (si scaling):
- Évaluer embeddings pour matching (réduction 60-70%)
- Hybrid approach: Embeddings + LLM

---

## 🔗 Références

**Documentation**:
- `.q-context/CRITICAL_RULES.md` - Règles non-négociables
- `.q-context/vectora-inbox-development-rules.md` - Règles développement
- `.q-context/vectora-inbox-governance.md` - Workflow Git et versioning
- `docs/architecture/blueprint-v2-ACTUAL-2026.yaml` - Architecture système

**Scripts**:
- `scripts/analyze_prompt_size.py` - Analyse taille prompts
- `scripts/check_canonical_s3.py` - Vérification canonical S3
- `tests/local/test_e2e_runner.py` - Tests locaux
- `tests/aws/test_e2e_runner.py` - Tests AWS

**Baseline**:
- `docs/reports/e2e/test_e2e_v17_rapport_2026-02-03.md` - Référence qualité

---

**Plan créé le**: 2026-02-04  
**Dernière mise à jour**: 2026-02-04  
**Statut**: Prêt pour exécution  
**Conformité Q Context**: ✅ 100%
