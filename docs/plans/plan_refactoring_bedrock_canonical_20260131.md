# Plan de Développement - Refactoring Architecture Bedrock et Canonical LAI

**Date**: 2026-01-31  
**Objectif**: Simplifier architecture Bedrock (2 appels vs 3) et unifier définition LAI (1 fichier vs 8)  
**Durée estimée**: 4-6 heures  
**Risque**: Moyen (refactoring majeur mais architecture validée)  
**Environnements impactés**: dev, stage

---

## 🎯 Contexte et Justification

**Besoin métier**: 
- Architecture actuelle incohérente (3 systèmes de scoring différents)
- Matière canonical LAI fragmentée (8 fichiers, 130+ éléments)
- Coût Bedrock élevé (prompts surchargés)
- Maintenance complexe

**Impact attendu**: 
- ✅ Réduction 33% appels Bedrock (3→2)
- ✅ Simplification 60% matière canonical (130→50 éléments)
- ✅ Réduction 75% taille prompts (2000→500 tokens)
- ✅ Généricité totale (réutilisable pour siRNA, cell therapy)

**Contraintes**: 
- Garder effective_date inchangé (déjà OK)
- Valider avec lai_weekly_v3 (client de référence)
- Maintenir compatibilité backward

---

## 📋 Plan d'Exécution

### Phase 0: Cadrage ⏱️ 30 min
- [ ] Lire fichiers actuels (normalizer.py, bedrock_client.py, prompts)
- [ ] Valider que effective_date reste inchangé
- [ ] Identifier tous les fichiers canonical à simplifier
- [ ] Créer backup des fichiers critiques

**Livrables Phase 0**:
- [ ] Liste complète fichiers à modifier
- [ ] Backup dans `.tmp/backup_refactoring_20260131/`

**✋ CHECKPOINT**: Validation utilisateur avant Phase 1

---

### Phase 1: Simplification Canonical (1 fichier unifié) ⏱️ 60 min

**Objectif**: Créer `canonical/domains/lai_domain_definition.yaml` unifié

- [ ] Créer structure `canonical/domains/` si nécessaire
- [ ] Créer `lai_domain_definition.yaml` avec:
  - Définition conceptuelle LAI
  - Strong signals (core_technologies, pure_players, trademarks)
  - Medium signals (technology_families, dosing_intervals, hybrid_companies)
  - Weak signals (routes, molecules)
  - Exclusions (anti-LAI)
  - Matching rules explicites
  - Scoring criteria intégré
- [ ] Réduire de 130→50 éléments essentiels
- [ ] Valider syntaxe YAML

**Livrables Phase 1**:
- [ ] `canonical/domains/lai_domain_definition.yaml` créé
- [ ] Réduction 60% éléments validée

**✋ CHECKPOINT**: Validation utilisateur avant Phase 2

---

### Phase 2: Nouveau Prompt Normalisation Générique ⏱️ 30 min

**Objectif**: Créer prompt 100% générique (pas de LAI hardcodé)

- [ ] Créer `canonical/prompts/normalization/generic_normalization.yaml`
- [ ] Supprimer `lai_relevance_score` du prompt
- [ ] Garder extraction date (extracted_date + date_confidence)
- [ ] Extraction entités générique (companies, molecules, technologies, trademarks, indications)
- [ ] Classification événement générique
- [ ] Génération résumé

**Livrables Phase 2**:
- [ ] `generic_normalization.yaml` créé
- [ ] Prompt ~500 tokens (vs 2000 actuellement)

**✋ CHECKPOINT**: Validation utilisateur avant Phase 3

---

### Phase 3: Nouveau Prompt Domain Scoring ⏱️ 30 min

**Objectif**: Créer prompt matching + scoring unifié par domaine

- [ ] Créer `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
- [ ] Référencer `lai_domain_definition.yaml` unique
- [ ] Scoring 0-100 avec breakdown détaillé
- [ ] Détection signaux (strong/medium/weak)
- [ ] Reasoning explicite
- [ ] Confiance (high/medium/low)

**Livrables Phase 3**:
- [ ] `lai_domain_scoring.yaml` créé
- [ ] Prompt simplifié avec 1 seule référence

**✋ CHECKPOINT**: Validation utilisateur avant Phase 4

---

### Phase 4: Adaptation Code Python ⏱️ 60 min

**Objectif**: Adapter normalizer.py et bedrock_client.py

- [ ] Modifier `bedrock_client.py`:
  - Appel 1: Normalisation générique (generic_normalization.yaml)
  - Appel 2: Domain scoring (lai_domain_scoring.yaml)
  - Supprimer appel 3 (scoring déterministe)
- [ ] Modifier `normalizer.py`:
  - Garder logique effective_date INCHANGÉE
  - Supprimer `lai_relevance_score` de normalized_content
  - Ajouter `domain_scores` de Bedrock
- [ ] Créer `bedrock_domain_scorer.py` (nouveau module)
- [ ] Adapter `prompt_builder.py` pour nouveaux prompts

**Livrables Phase 4**:
- [ ] Code Python adapté
- [ ] Tests unitaires passent
- [ ] effective_date inchangé (validé)

**✋ CHECKPOINT**: Validation utilisateur avant Phase 5

---

### Phase 5: Build et Deploy Dev ⏱️ 20 min

- [ ] Incrémenter VERSION:
  - VECTORA_CORE_VERSION: 1.X.Y → 1.X+1.0 (MINOR - nouvelle architecture)
  - CANONICAL_VERSION: 1.1 → 2.0 (MAJOR - breaking change structure)
- [ ] Build: `python scripts/build/build_all.py`
- [ ] Deploy dev: `python scripts/deploy/deploy_env.py --env dev`
- [ ] Sync canonical: `python scripts/sync/sync_canonical.py --env dev`

**Livrables Phase 5**:
- [ ] Build réussi
- [ ] Deploy dev OK
- [ ] Canonical synced

**✋ CHECKPOINT**: Validation utilisateur avant Phase 6

---

### Phase 6: Tests E2E Dev ⏱️ 30 min

- [ ] Test normalize-score-v2: `python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v3`
- [ ] Valider:
  - 2 appels Bedrock (vs 3 avant)
  - effective_date présent et correct
  - domain_scores présent
  - Pas de lai_relevance_score
  - Signaux détectés (strong/medium/weak)
  - Score 0-100 avec breakdown
- [ ] Comparer avec baseline précédente
- [ ] Vérifier aucune régression

**Livrables Phase 6**:
- [ ] Tests E2E dev passés
- [ ] Comparaison baseline OK
- [ ] Métriques collectées

**✋ CHECKPOINT**: Validation utilisateur avant Phase 7

---

### Phase 7: Promote Stage et Validation ⏱️ 30 min

- [ ] Promote stage: `python scripts/deploy/promote.py --to stage --version X.Y.Z`
- [ ] Test stage: `python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v3 --env stage`
- [ ] Validation métier:
  - Scores cohérents
  - Reasoning clair
  - Pas de faux positifs/négatifs
- [ ] Tests non-régression

**Livrables Phase 7**:
- [ ] Deploy stage OK
- [ ] Validation métier passée

**✋ CHECKPOINT**: Validation utilisateur avant Phase 8

---

### Phase 8: Git et Documentation ⏱️ 30 min

- [ ] Créer branche: `git checkout -b refactor/bedrock-canonical-unified`
- [ ] Commit:
  ```bash
  git add .
  git commit -m "refactor: Unify Bedrock architecture (2 calls) and LAI canonical (1 file)
  
  - Create canonical/domains/lai_domain_definition.yaml (130→50 elements)
  - Create generic_normalization.yaml (no LAI hardcoded)
  - Create lai_domain_scoring.yaml (matching + scoring unified)
  - Adapt bedrock_client.py and normalizer.py
  - Keep effective_date logic unchanged
  - Reduce prompt size 75% (2000→500 tokens)
  
  BREAKING CHANGE: Canonical structure changed (v1.1→v2.0)"
  ```
- [ ] Push: `git push origin refactor/bedrock-canonical-unified`
- [ ] Créer rapport final: `docs/reports/development/refactoring_bedrock_canonical_20260131.md`
- [ ] Mettre à jour blueprint si nécessaire

**Livrables Phase 8**:
- [ ] Code commité et pushé
- [ ] Rapport final créé
- [ ] Documentation à jour

---

## ✅ Critères de Succès

- [ ] 2 appels Bedrock au lieu de 3 (réduction 33%)
- [ ] 1 fichier canonical au lieu de 8 (simplification)
- [ ] 50 éléments au lieu de 130 (réduction 60%)
- [ ] Prompts 500 tokens au lieu de 2000 (réduction 75%)
- [ ] effective_date inchangé et fonctionnel
- [ ] Tests dev et stage passés
- [ ] Aucune régression détectée
- [ ] Scores cohérents avec baseline
- [ ] Code commité et documenté

---

## 🚨 Plan de Rollback

**En cas de problème critique**:
1. **Stop immédiat** de l'exécution
2. **Diagnostic rapide** (< 10 min)
3. **Rollback** vers version précédente

**Commandes rollback**:
```bash
# Rollback dev
python scripts/deploy/rollback.py --env dev --to-version [VERSION_PRECEDENTE]

# Rollback stage
python scripts/deploy/rollback.py --env stage --to-version [VERSION_PRECEDENTE]

# Restore canonical
aws s3 sync s3://vectora-inbox-canonical-dev-backup/ s3://vectora-inbox-canonical-dev/ --profile rag-lai-prod
```

**Backup disponible**: `.tmp/backup_refactoring_20260131/`

---

## 📊 Métriques et Suivi

**Métriques à surveiller**:
- [ ] Nombre appels Bedrock (objectif: 2)
- [ ] Taille prompts (objectif: <600 tokens)
- [ ] Temps exécution normalize-score-v2
- [ ] Coût Bedrock par item
- [ ] Taux matching correct (vs baseline)

**Suivi post-déploiement**:
- [ ] Monitoring 24h après deploy stage
- [ ] Validation métriques métier
- [ ] Feedback utilisateurs

---

## 📝 Notes et Observations

**Décisions prises**:
- Garder effective_date inchangé (déjà optimal)
- Créer nouveau dossier `canonical/domains/` pour définitions unifiées
- Supprimer scoring déterministe (remplacé par Bedrock)
- Versioning: CANONICAL v2.0 (breaking change structure)

**Points d'attention**:
- Valider que lai_weekly_v3 fonctionne identiquement
- Comparer scores avant/après (corrélation >0.9)
- Vérifier coût Bedrock réduit

**Améliorations futures**:
- Créer `sirna_domain_definition.yaml` (même pattern)
- Créer `cell_therapy_domain_definition.yaml`
- Feedback loop pour améliorer prompts

---

**Plan créé le**: 2026-01-31  
**Dernière mise à jour**: 2026-01-31  
**Statut**: En attente validation
