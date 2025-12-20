# Plan Correctif - Architecture Bedrock Matching Pure

**Date :** 19 décembre 2025  
**Version :** 1.0  
**Objectif :** Corriger définitivement le problème de matching 0% en implémentant une architecture Bedrock-Only pure  
**Conformité :** 100% vectora-inbox-development-rules.md  
**Durée estimée :** 15 minutes  

---

## 🎯 RÉSUMÉ EXÉCUTIF

### Problème Identifié
**Architecture hybride conflictuelle** où le matching Bedrock fonctionne (7/15 items) mais est écrasé par une logique déterministe défaillante, résultant en 0% de matching final.

### Solution Proposée
**Architecture Bedrock-Only Pure** avec suppression complète du matching déterministe et garantie de préservation des résultats Bedrock.

### Résultat Attendu
**Matching rate : 0% → 47%** (7/15 items) avec architecture simplifiée et conforme aux règles V2.

---

## 📊 ANALYSE ARCHITECTURALE ACTUELLE

### Flux Lambda normalize-score-v2-dev

#### Architecture Actuelle (PROBLÉMATIQUE)
```
Raw Items (15) 
    ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 1: Normalisation Bedrock                         │
│ - normalizer.py → normalize_items_batch()              │
│ - 15 appels Bedrock normalisation                      │
│ - Extraction entités, summary, classification          │
│ - STATUS: ✅ FONCTIONNE (100% succès)                  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 2: Matching Bedrock (DANS normalizer.py)         │
│ - bedrock_matcher.py → match_item_to_domains_bedrock() │
│ - 15 appels Bedrock matching                           │
│ - Résultat: 7/15 items matchés                         │
│ - STATUS: ✅ FONCTIONNE (47% matching rate)            │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 3: "Architecture Bedrock-Only Pure" (__init__.py)│
│ - matched_items = normalized_items                      │
│ - Log: "matching déterministe supprimé"                │
│ - STATUS: ✅ DÉCLARÉ mais pas vérifié                  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 4: Scoring                                       │
│ - scorer.py → score_items()                            │
│ - Utilise les résultats de matching                    │
│ - STATUS: ⚠️ DÉPEND DU MATCHING                        │
└─────────────────────────────────────────────────────────┘
    ↓
Curated Items (15) avec matched_domains = [] ❌
```

#### Appels Bedrock Actuels
- **Normalisation :** 15 appels (1 par item)
- **Matching :** 15 appels (1 par item)
- **Total :** 30 appels Bedrock
- **Coût estimé :** ~$0.09 USD par run

### Problème Racine Identifié

**Dans `normalizer.py` ligne 65-75 :** Le matching Bedrock est conditionnel et peut ne pas être appliqué correctement.

```python
# PROBLÉMATIQUE ACTUELLE
if watch_domains and len(watch_domains) > 0:
    bedrock_matching_result = match_item_to_domains_bedrock(...)
else:
    bedrock_matching_result = {'matched_domains': [], 'domain_relevance': {}}
```

---

## 🏗️ ARCHITECTURE CIBLE OPTIMISÉE

### Flux Bedrock-Only Pure Proposé

```
Raw Items (15)
    ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 1: Normalisation + Matching Bedrock Intégré      │
│ - normalizer.py → normalize_items_batch()              │
│ - 15 appels Bedrock normalisation                      │
│ - 15 appels Bedrock matching (SYSTÉMATIQUE)            │
│ - Résultats Bedrock GARANTIS dans matching_results     │
│ - STATUS: ✅ OPTIMISÉ                                  │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 2: Architecture Bedrock-Only Pure Validée       │
│ - matched_items = normalized_items                      │
│ - Validation: comptage items matchés                   │
│ - Log: "Matching Bedrock V2: X items matchés"         │
│ - STATUS: ✅ VÉRIFIÉ                                   │
└─────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────┐
│ PHASE 3: Scoring Optimisé                              │
│ - scorer.py → score_items()                            │
│ - Utilise matching_results Bedrock validés             │
│ - STATUS: ✅ FIABLE                                    │
└─────────────────────────────────────────────────────────┘
    ↓
Curated Items (15) avec matched_domains = [7 items] ✅
```

### Optimisations Architecturales

#### Option A : Appels Séparés (ACTUEL - RECOMMANDÉ)
- **Normalisation :** 1 appel Bedrock par item
- **Matching :** 1 appel Bedrock par item
- **Total :** 30 appels (2 × 15 items)
- **Avantages :**
  - ✅ Séparation des responsabilités
  - ✅ Prompts spécialisés optimisés
  - ✅ Gestion d'erreurs granulaire
  - ✅ Parallélisation possible
  - ✅ Debugging facilité

#### Option B : Appel Unifié (ALTERNATIVE)
- **Normalisation + Matching :** 1 appel Bedrock par item
- **Total :** 15 appels (1 × 15 items)
- **Avantages :**
  - ✅ Réduction coûts (-50%)
  - ✅ Réduction latence
- **Inconvénients :**
  - ❌ Prompts complexes
  - ❌ Parsing réponse complexe
  - ❌ Gestion d'erreurs difficile

#### Recommandation : Option A (Appels Séparés)
**Justification :**
- **Scalabilité :** Parallélisation native (max_workers configurable)
- **Précision :** Prompts spécialisés pour chaque tâche
- **Puissance :** Gestion d'erreurs granulaire
- **Volume :** Architecture linéaire jusqu'à 100 items
- **Maintenance :** Code modulaire et testable

---

## 📋 PLAN D'EXÉCUTION - 4 PHASES

### Phase 1 : Correction Matching Systématique (5 min)

#### Objectif
Garantir que le matching Bedrock est TOUJOURS exécuté, même avec domaines vides.

#### Modification : `src_v2/vectora_core/normalization/normalizer.py`

**Ligne 65-75 :** Remplacer la logique conditionnelle

```python
# AVANT (PROBLÉMATIQUE)
if watch_domains and len(watch_domains) > 0:
    from .bedrock_matcher import match_item_to_domains_bedrock
    temp_item = _enrich_item_with_normalization(item, normalization_result)
    bedrock_matching_result = match_item_to_domains_bedrock(
        temp_item, watch_domains, canonical_scopes, matching_config or {},
        canonical_prompts or {}, bedrock_model
    )
else:
    bedrock_matching_result = {'matched_domains': [], 'domain_relevance': {}}

# APRÈS (CORRIGÉ)
from .bedrock_matcher import match_item_to_domains_bedrock
temp_item = _enrich_item_with_normalization(item, normalization_result)
bedrock_matching_result = match_item_to_domains_bedrock(
    temp_item, watch_domains or [], canonical_scopes, matching_config or {},
    canonical_prompts or {}, bedrock_model
)
```

#### Conformité
- ✅ **Architecture V2** : Modification dans vectora_core uniquement
- ✅ **Hygiène V4** : Simplification du code
- ✅ **Configuration pilotée** : watch_domains depuis client config

### Phase 2 : Validation Architecture Pure (2 min)

#### Objectif
Ajouter validation que l'architecture Bedrock-Only fonctionne réellement.

#### Modification : `src_v2/vectora_core/normalization/__init__.py`

**Ligne 95-96 :** Ajouter validation des résultats

```python
# AVANT
matched_items = normalized_items
logger.info("Architecture Bedrock-Only Pure : matching déterministe supprimé")

# APRÈS
matched_items = normalized_items
logger.info("Architecture Bedrock-Only Pure : matching déterministe supprimé")

# NOUVEAU: Validation que le matching Bedrock a fonctionné
bedrock_matched_count = sum(1 for item in matched_items 
                           if item.get("matching_results", {}).get("matched_domains"))
total_items = len(matched_items)
matching_rate = (bedrock_matched_count / total_items * 100) if total_items > 0 else 0

logger.info(f"Matching Bedrock V2: {bedrock_matched_count}/{total_items} items matchés ({matching_rate:.1f}%)")

if bedrock_matched_count == 0 and total_items > 0:
    logger.warning("ATTENTION: Aucun item matché - vérifier configuration watch_domains")
```

#### Conformité
- ✅ **Logs standardisés** : Format conforme CloudWatch
- ✅ **Monitoring** : Métriques de matching exposées
- ✅ **Debugging** : Alertes si matching 0%

### Phase 3 : Optimisation Gestion Domaines Vides (2 min)

#### Objectif
Améliorer la gestion des cas où aucun domaine n'est configuré.

#### Validation : `src_v2/vectora_core/normalization/bedrock_matcher.py`

**Ligne 20 :** Vérifier gestion domaines vides (AUCUNE MODIFICATION REQUISE)

```python
# DÉJÀ CORRECT
def match_item_to_domains_bedrock(...):
    if not watch_domains:
        logger.debug("Aucun domaine de veille configuré")
        return {"matched_domains": [], "domain_relevance": {}}
```

#### Conformité
- ✅ **Pas de modification** : Code déjà conforme
- ✅ **Gestion d'erreurs** : Cas domaines vides géré

### Phase 4 : Déploiement et Validation (6 min)

#### Étape 4.1 : Build Layer (2 min)
```bash
cd c:\Users\franc\OneDrive\Bureau\vectora-inbox
cd layer_build
zip -r ../vectora-core-bedrock-pure-v20.zip vectora_core/
```

#### Étape 4.2 : Déploiement AWS (2 min)
```bash
# Publication layer
aws lambda publish-layer-version \
  --layer-name vectora-inbox-vectora-core-dev \
  --zip-file fileb://vectora-core-bedrock-pure-v20.zip \
  --region eu-west-3 \
  --profile rag-lai-prod

# Mise à jour Lambda
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:20 \
  --region eu-west-3 \
  --profile rag-lai-prod
```

#### Étape 4.3 : Test E2E (2 min)
```bash
# Test lai_weekly_v4
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly_v4"}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_v20.json
```

---

## 📊 MÉTRIQUES DE VALIDATION

### Critères de Succès

#### Métriques Techniques
- ✅ **StatusCode :** 200
- ✅ **Durée d'exécution :** < 120 secondes
- ✅ **Appels Bedrock :** 30 (15 normalisation + 15 matching)
- ✅ **Erreurs Bedrock :** 0

#### Métriques Métier
- ✅ **Matching rate :** ≥ 40% (6+ items sur 15)
- ✅ **Items haute qualité :** ≥ 3 items (score > 10)
- ✅ **Domaines matchés :** tech_lai_ecosystem présent
- ✅ **Entités détectées :** ≥ 30 entités total

#### Métriques Coût/Performance
- ✅ **Coût par run :** ≤ $0.10 USD
- ✅ **Coût par item matché :** ≤ $0.02 USD
- ✅ **Temps par item :** ≤ 8 secondes
- ✅ **Scalabilité :** Linéaire jusqu'à 50 items

### Validation Logs CloudWatch

#### Logs Attendus
```
[INFO] Normalisation V2 de 15 items via Bedrock (workers: 1)
[INFO] Matching Bedrock V2: 1 domaines matchés sur 1 évalués
[INFO] Architecture Bedrock-Only Pure : matching déterministe supprimé
[INFO] Matching Bedrock V2: 7/15 items matchés (46.7%)
[INFO] Normalisation/scoring terminée : {"status": "completed", "items_matched": 7}
```

#### Alertes à Surveiller
- ⚠️ **"ATTENTION: Aucun item matché"** → Configuration watch_domains
- ❌ **"Erreur matching Bedrock"** → Problème prompts/scopes
- ❌ **"ThrottlingException"** → Réduire max_workers

---

## 🎯 ANALYSE SCALABILITÉ ET PERFORMANCE

### Scalabilité par Volume

#### Volume Faible (1-20 items)
- **Configuration :** max_workers = 1 (séquentiel)
- **Temps d'exécution :** 60-120 secondes
- **Coût :** $0.05-0.15 USD
- **Recommandation :** Architecture actuelle optimale

#### Volume Moyen (20-50 items)
- **Configuration :** max_workers = 2-3 (parallèle)
- **Temps d'exécution :** 80-150 secondes
- **Coût :** $0.15-0.40 USD
- **Recommandation :** Parallélisation contrôlée

#### Volume Élevé (50-100 items)
- **Configuration :** max_workers = 3-5 + batch processing
- **Temps d'exécution :** 120-300 secondes
- **Coût :** $0.40-1.00 USD
- **Recommandation :** Considérer Option B (appels unifiés)

### Optimisations Futures

#### Court Terme (1 mois)
1. **Cache Bedrock** : Éviter re-normalisation items identiques
2. **Prompts optimisés** : Réduire tokens input/output
3. **Parallélisation intelligente** : Adaptation dynamique workers

#### Moyen Terme (3 mois)
1. **Appels unifiés** : Normalisation + Matching en 1 appel
2. **Modèle EU** : Migration Bedrock vers région européenne
3. **Scoring adaptatif** : Apprentissage sur feedback utilisateur

#### Long Terme (6 mois)
1. **Fine-tuning** : Modèle spécialisé LAI
2. **Architecture streaming** : Traitement temps réel
3. **Multi-région** : Répartition charge géographique

---

## 🔒 CONFORMITÉ RÈGLES VECTORA-INBOX

### ✅ Architecture V2 Respectée
- **3 Lambdas V2** : normalize-score-v2 optimisée
- **Handler minimal** : Délégation à vectora_core préservée
- **Code dans src_v2** : Aucune pollution /src
- **Lambda Layers** : Dépendances externalisées

### ✅ Hygiène V4 Respectée
- **Simplification code** : Suppression logique hybride
- **Pas de duplication** : Réutilisation modules existants
- **Imports propres** : Pas de nouvelles dépendances
- **Modularité** : Séparation responsabilités préservée

### ✅ Configuration Pilotée
- **Client config** : watch_domains depuis lai_weekly_v4.yaml
- **Canonical scopes** : Entités LAI chargées dynamiquement
- **Prompts canonical** : Prompts Bedrock standardisés
- **Seuils configurables** : min_domain_score respecté

### ✅ Environnement AWS Conforme
- **Région principale** : eu-west-3 (Paris)
- **Bedrock région** : us-east-1 (validé E2E)
- **Profil CLI** : rag-lai-prod
- **Conventions nommage** : Suffixes -v2-dev

---

## 📋 CHECKLIST VALIDATION FINALE

### Avant Exécution
- [ ] **Code modifié** : normalizer.py + __init__.py uniquement
- [ ] **Conformité règles** : 100% vectora-inbox-development-rules.md
- [ ] **Pas de breaking changes** : Interface publique préservée
- [ ] **Tests locaux** : Import vectora_core réussi

### Après Déploiement
- [ ] **Layer publiée** : Version 20 disponible
- [ ] **Lambda mise à jour** : Configuration layer v20
- [ ] **Test E2E réussi** : StatusCode 200
- [ ] **Logs validés** : Matching rate > 0%

### Validation Métier
- [ ] **Items matchés** : ≥ 6 items sur 15 (40%+)
- [ ] **Domaine tech_lai_ecosystem** : Items présents
- [ ] **Entités LAI** : Sociétés, molécules, technologies détectées
- [ ] **Scores cohérents** : Distribution 2-15 points

---

## 🎯 CONCLUSION

### Résultat Attendu
**Architecture Bedrock-Only Pure fonctionnelle** avec matching rate 47% (7/15 items) au lieu de 0%.

### Impact Technique
- **Simplification** : Suppression logique hybride défaillante
- **Fiabilité** : Résultats Bedrock garantis
- **Performance** : Temps d'exécution stable
- **Scalabilité** : Architecture linéaire validée

### Impact Métier
- **Newsletter ready** : Items structurés par domaine
- **Qualité signaux** : Items LAI haute valeur identifiés
- **Coûts maîtrisés** : $0.09 par run (acceptable)
- **Évolutivité** : Base solide pour optimisations futures

### Prochaines Étapes
1. **Validation plan** : Accord sur approche technique
2. **Exécution** : 15 minutes d'implémentation
3. **Test E2E** : Validation lai_weekly_v4
4. **Documentation** : Mise à jour contrats Lambda
5. **Newsletter V2** : Implémentation avec résultats matchés

---

**Plan Correctif - Architecture Bedrock Matching Pure**  
**Prêt pour exécution - Conformité 100% règles V2**  
**Durée : 15 minutes - Risque : Minimal - Impact : Majeur**