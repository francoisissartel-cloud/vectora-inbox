# Plan de Développement - Correctifs Matching et Dates

**Date**: 2026-01-31  
**Type**: Développement - Refactoring  
**Complexité**: Moyenne  
**Durée estimée**: 2-3 heures  
**Environnement cible**: dev → stage

---

## 🎯 Objectif

Corriger 2 problèmes architecturaux identifiés dans le rapport d'évaluation:
1. **Unifier matching**: Supprimer `matcher.py` (legacy, inutilisé)
2. **Cohérence dates**: Centraliser logique de date dans `effective_date`

---

## 📋 Analyse de la Demande

**Demande utilisateur**: "Corriger les problèmes: Unifier matching (supprimer matcher.py) et Cohérence dates (effective_date)"

**Type de tâche**: Refactoring architectural

**Règles appliquées**:
- `.q-context/vectora-inbox-development-rules.md` - Architecture 3 Lambdas V2
- `.q-context/vectora-inbox-git-workflow.md` - Git avant build
- `.q-context/q-planning-rules.md` - Phases Git/Versioning/Tests obligatoires

---

## 📊 Analyse Technique

### Fichiers à Modifier

**Correctif 1 - Matching**:
- ❌ `src_v2/vectora_core/normalization/matcher.py` (supprimer)
- ✏️ `src_v2/vectora_core/normalization/normalizer.py` (nettoyer imports)

**Correctif 2 - Dates**:
- ✏️ `src_v2/vectora_core/normalization/normalizer.py` (ajouter effective_date)
- ✏️ `src_v2/vectora_core/normalization/scorer.py` (simplifier)
- ✏️ `src_v2/vectora_core/newsletter/assembler.py` (simplifier × 2 fonctions)

**Total**: 4 fichiers modifiés, 1 fichier supprimé

### Environnement Cible

- **Développement**: dev (tests)
- **Validation**: stage (après succès dev)
- **Ressources AWS**: Lambda normalize-score-v2-dev

### Livrables Prévus

- [ ] matcher.py supprimé
- [ ] effective_date centralisé dans normalizer.py
- [ ] scorer.py simplifié
- [ ] assembler.py simplifié
- [ ] VERSION incrémenté (PATCH: 1.2.3 → 1.2.4)
- [ ] Tests E2E passés
- [ ] Documentation mise à jour

---

## ⚠️ Points de Vigilance

1. **Vérifier que matcher.py n'est plus utilisé** avant suppression
2. **Seuil de confiance 0.7** pour dates Bedrock est arbitraire
3. **Tester avec items sans date** (effective_date = None)
4. **Backward compatibility**: Vérifier que les items existants fonctionnent

---

## 📅 Plan d'Exécution

### Phase 0: Cadrage et Validation (5 min)

**Objectif**: Vérifier faisabilité et préparer environnement

**Actions**:
1. Vérifier que matcher.py n'est plus référencé
2. Analyser impact sur items existants
3. Créer branche Git

**Livrables**:
- Confirmation aucune référence à matcher.py
- Branche `refactor/unify-matching-dates` créée

**Commandes**:
```bash
# Rechercher références matcher.py
grep -r "from.*matcher import" src_v2/
grep -r "import.*matcher" src_v2/

# Créer branche
git checkout develop
git pull origin develop
git checkout -b refactor/unify-matching-dates
```

---

### Phase 1: Correctif Matching (15 min)

**Objectif**: Supprimer matcher.py et nettoyer imports

**Actions**:
1. Supprimer `src_v2/vectora_core/normalization/matcher.py`
2. Vérifier imports dans `normalizer.py`
3. Vérifier aucune autre référence

**Livrables**:
- matcher.py supprimé
- Imports nettoyés
- Code compile sans erreur

**Modifications**:
```python
# Dans normalizer.py, garder uniquement:
from .bedrock_matcher import match_item_to_domains_bedrock
# Supprimer: from .matcher import ...
```

---

### Phase 2: Correctif Dates - Normalizer (20 min)

**Objectif**: Centraliser logique effective_date dans normalizer.py

**Actions**:
1. Ajouter calcul effective_date dans `_enrich_item_with_normalization()`
2. Ajouter date_metadata pour traçabilité
3. Tester logique de sélection

**Livrables**:
- effective_date calculé après Bedrock
- date_metadata ajouté
- Logique testée

**Modifications**:
```python
# Dans normalizer.py, fonction _enrich_item_with_normalization()
# Après ligne 450 (section normalized_content)

# Calcul de effective_date (date unique pour tout le pipeline)
extracted_date = normalization_result.get('extracted_date')
date_confidence = normalization_result.get('date_confidence', 0.0)
published_at = original_item.get('published_at', '')

# Logique de sélection
if extracted_date and date_confidence > 0.7:
    effective_date = extracted_date
    date_source = 'bedrock'
else:
    effective_date = published_at[:10] if published_at else None
    date_source = 'published_at'

# Ajouter au niveau racine
enriched_item['effective_date'] = effective_date
enriched_item['date_metadata'] = {
    'source': date_source,
    'bedrock_date': extracted_date,
    'bedrock_confidence': date_confidence,
    'published_at': published_at
}
```

---

### Phase 3: Correctif Dates - Scorer (15 min)

**Objectif**: Simplifier scorer.py pour utiliser effective_date

**Actions**:
1. Supprimer calcul de effective_date dans `_calculate_item_score()`
2. Utiliser `item.get('effective_date')` directement
3. Supprimer fonctions de calcul de date

**Livrables**:
- scorer.py simplifié (-20 lignes)
- Utilise effective_date directement

**Modifications**:
```python
# Dans scorer.py, fonction _calculate_item_score()
# REMPLACER lignes 60-75 par:

# Utiliser effective_date calculé en amont
effective_date = item.get('effective_date')

# Supprimer toute la logique:
# extracted_date = normalized.get('extracted_date')
# date_confidence = normalized.get('date_confidence', 0.0)
# if extracted_date and date_confidence > 0.7: ...
```

---

### Phase 4: Correctif Dates - Assembler (15 min)

**Objectif**: Simplifier assembler.py pour utiliser effective_date

**Actions**:
1. Modifier `_format_item_markdown()` pour utiliser effective_date
2. Modifier `_format_item_json()` pour utiliser effective_date
3. Supprimer logique de calcul de date

**Livrables**:
- assembler.py simplifié (-10 lignes)
- Dates cohérentes dans newsletter

**Modifications**:
```python
# Dans assembler.py, fonction _format_item_markdown()
# REMPLACER ligne ~280:
effective_date = item.get('effective_date', '')[:10]

# Dans assembler.py, fonction _format_item_json()
# REMPLACER ligne ~350:
effective_date = item.get('effective_date', '')
```

---

### Phase 5: Versioning (2 min)

**Objectif**: Incrémenter VERSION

**Actions**:
1. Analyser type de changement: PATCH (refactoring interne)
2. Incrémenter VECTORA_CORE_VERSION
3. Documenter raison

**Livrables**:
- VERSION incrémenté: 1.2.3 → 1.2.4

**Modifications**:
```bash
# Éditer VERSION
VECTORA_CORE_VERSION=1.2.4  # Was 1.2.3
# Raison: Refactoring - Unify matching + centralize date logic
```

---

### Phase 6: Commit Git (3 min)

**Objectif**: Commit des modifications

**Actions**:
1. Préparer message commit (Conventional Commits)
2. Lister fichiers modifiés
3. Commit

**Livrables**:
- Commit avec message descriptif

**Commandes**:
```bash
git add src_v2/vectora_core/normalization/normalizer.py
git add src_v2/vectora_core/normalization/scorer.py
git add src_v2/vectora_core/newsletter/assembler.py
git add VERSION

# Supprimer matcher.py
git rm src_v2/vectora_core/normalization/matcher.py

git commit -m "refactor(vectora-core): unify matching and centralize date logic

- Remove legacy matcher.py (unused)
- Centralize effective_date calculation in normalizer.py
- Simplify scorer.py and assembler.py date logic
- Add date_metadata for traceability

BREAKING: None
IMPACT: Internal refactoring, no API changes
VERSION: 1.2.3 → 1.2.4"
```

---

### Phase 7: Tests & Validation (15 min)

**Objectif**: Valider les correctifs en dev

**Actions**:
1. Build artefacts
2. Deploy vers dev
3. Test E2E lai_weekly_v7
4. Vérifier dates dans output

**Livrables**:
- Build réussi
- Deploy dev réussi
- Tests E2E passés
- Dates cohérentes

**Commandes**:
```bash
# Build
python scripts/build/build_all.py

# Deploy dev
python scripts/deploy/deploy_env.py --env dev

# Test E2E
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7

# Vérifier output
cat .tmp/responses/normalize_v7_*.json | jq '.body.items_processed'
cat .tmp/responses/normalize_v7_*.json | jq '.body.items[0].effective_date'
cat .tmp/responses/normalize_v7_*.json | jq '.body.items[0].date_metadata'
```

**Critères de succès**:
- ✅ statusCode: 200
- ✅ items_processed > 0
- ✅ effective_date présent dans tous les items
- ✅ date_metadata présent
- ✅ Aucune erreur d'import

---

### Phase 8: Tag & Promotion (10 min)

**Objectif**: Promouvoir vers stage si tests dev réussis

**Actions**:
1. Créer tag Git v1.2.4
2. Push tag
3. Promouvoir vers stage
4. Test stage

**Livrables**:
- Tag Git créé
- Stage déployé
- Tests stage passés

**Commandes**:
```bash
# Tag Git
git tag v1.2.4 -m "Release 1.2.4 - Unify matching and centralize dates"
git push origin refactor/unify-matching-dates --tags

# Promouvoir vers stage
python scripts/deploy/promote.py --to stage --version 1.2.4 --git-sha $(git rev-parse HEAD)

# Test stage
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --env stage
```

---

### Phase 9: Rollback (si échec) (5 min)

**Objectif**: Restaurer état précédent si problème

**Actions**:
1. Identifier problème
2. Rollback code
3. Rollback deploy
4. Valider restauration

**Livrables**:
- État précédent restauré
- Problème documenté

**Commandes**:
```bash
# Rollback Git
git checkout develop
git branch -D refactor/unify-matching-dates

# Rollback deploy dev
python scripts/deploy/rollback.py --env dev --to-version 1.2.3

# Rollback deploy stage (si déployé)
python scripts/deploy/rollback.py --env stage --to-version 1.2.3
```

---

### Phase 10: Documentation & Finalisation (10 min)

**Objectif**: Documenter les changements

**Actions**:
1. Créer rapport final
2. Mettre à jour documentation
3. Créer PR vers develop
4. Nettoyer fichiers temporaires

**Livrables**:
- Rapport final créé
- PR créée
- Documentation à jour

**Commandes**:
```bash
# Créer PR
git push origin refactor/unify-matching-dates
# Créer PR sur GitHub/GitLab

# Nettoyer .tmp/
python scripts/maintenance/cleanup_tmp.py
```

---

## 📊 Métriques de Succès

### Métriques Techniques
- ✅ matcher.py supprimé
- ✅ effective_date présent dans 100% des items
- ✅ date_metadata présent pour traçabilité
- ✅ Tests E2E passés (dev + stage)
- ✅ Aucune régression

### Métriques Qualité
- ✅ Code plus simple (-30 lignes)
- ✅ 1 seule logique de date (vs 3)
- ✅ Traçabilité améliorée (date_metadata)
- ✅ Cohérence dates dans newsletter

### Métriques Temps
- Phase 0: 5 min
- Phase 1: 15 min
- Phase 2: 20 min
- Phase 3: 15 min
- Phase 4: 15 min
- Phase 5: 2 min
- Phase 6: 3 min
- Phase 7: 15 min
- Phase 8: 10 min
- Phase 10: 10 min
- **Total**: ~2h

---

## ✅ CONFORMITÉ Q-CONTEXT

**Ce plan respecte les règles de gouvernance Vectora Inbox** :

✅ **Architecture** : 3 Lambdas V2 (`.q-context/vectora-inbox-development-rules.md`)
✅ **Git Workflow** : Branche → Commit → Build → Deploy (`.q-context/vectora-inbox-git-workflow.md`)
✅ **Planification** : Phases structurées avec Git/Versioning/Tests (`.q-context/q-planning-rules.md`)
✅ **Versioning** : Incrémentation VERSION avant build
✅ **Environnement** : Cible explicite (dev/stage/prod)
✅ **Scripts** : Utilisation scripts standardisés uniquement
✅ **Hygiène** : Temporaires dans `.tmp/`, builds dans `.build/`
✅ **Tests** : Validation dev avant promotion stage

**Vous pouvez suivre ce plan en toute sécurité - il ne risque pas d'abîmer le projet.**

---

## 🎯 Validation Avant Exécution

**Confirmez-vous que je peux procéder avec ce plan ?**

Options:
- ✅ **OUI** - Commencer par Phase 0
- ⚠️ **MODIFIER** - Ajuster [préciser quoi]
- ❌ **ANNULER** - Ne pas exécuter

---

**Plan créé le**: 2026-01-31  
**Template utilisé**: plan-development-template.md  
**Statut**: En attente de validation
