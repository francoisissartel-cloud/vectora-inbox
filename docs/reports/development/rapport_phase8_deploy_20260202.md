# Rapport Phase 8 - Build, Deploy et Tests E2E

**Date**: 2026-02-02  
**Objectif**: Déployer et valider architecture 2 appels Bedrock  
**Statut**: ✅ Déploiement réussi

---

## 📋 Actions Réalisées

### 1. Incrémentation VERSION ✅

**Changement**:
```
VECTORA_CORE_VERSION: 1.3.0 → 1.4.0 (MINOR)
```

**Justification**: Nouvelle architecture 2 appels Bedrock (feature majeure)

---

### 2. Build Artefacts ✅

**Commande**: `python scripts/build/build_all.py`

**Résultats**:
- ✅ `vectora-core-1.4.0.zip` créé (0.25 MB)
- ✅ `common-deps-1.0.5.zip` créé (1.76 MB)
- ✅ SHA256 calculés pour traçabilité

**Fichiers inclus dans vectora-core-1.4.0**:
- `bedrock_domain_scorer.py` (NOUVEAU)
- `bedrock_client.py` (méthode invoke_with_prompt ajoutée)
- `normalizer.py` (intégration 2ème appel)

---

### 3. Deploy Dev ✅

**Commande**: `python scripts/deploy/deploy_env.py --env dev`

**Résultats**:
- ✅ Layer vectora-core-dev v50 publié
- ✅ Layer common-deps-dev v12 publié
- ✅ 3 Lambdas mises à jour automatiquement:
  - `vectora-inbox-ingest-v2-dev` → Layers v50 + v12
  - `vectora-inbox-normalize-score-v2-dev` → Layers v50 + v12
  - `vectora-inbox-newsletter-v2-dev` → Layers v50 + v12

**Validation**: Workflow Phase 6ter fonctionne (mise à jour automatique des Lambdas)

---

### 4. Sync Canonical S3 ✅

**Commande**: `aws s3 sync canonical s3://vectora-inbox-config-dev/canonical/ --profile rag-lai-prod --delete`

**Résultats**:
- ✅ `global_prompts.yaml` synchronisé
- ✅ Tous les fichiers canonical à jour sur S3

**Fichiers critiques pour Phase 7**:
- `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
- `canonical/domains/lai_domain_definition.yaml`

---

## 🧪 Tests à Effectuer

### Test 1: Client Legacy (sans domain scoring)

**Objectif**: Vérifier rétrocompatibilité

**Commande**:
```bash
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v7 --limit 5
```

**Validation attendue**:
- ✅ Lambda s'exécute sans erreur
- ✅ Items normalisés correctement
- ✅ Pas de section `domain_scoring` dans items.json (car client legacy)
- ✅ Section `normalized_content` présente
- ✅ Section `matching_results` présente

---

### Test 2: Client avec Domain Scoring (à créer)

**Objectif**: Valider architecture 2 appels Bedrock

**Prérequis**: Créer client `lai_weekly_v9.yaml` avec:
```yaml
bedrock_config:
  normalization_prompt: generic_normalization
  enable_domain_scoring: true  # NOUVEAU
```

**Commande**:
```bash
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v9 --limit 5
```

**Validation attendue**:
- ✅ Lambda s'exécute sans erreur
- ✅ 2 appels Bedrock par item (logs CloudWatch)
- ✅ Section `domain_scoring` présente dans items.json
- ✅ Champs: is_relevant, score, confidence, signals_detected, reasoning
- ✅ Score entre 0-100
- ✅ Reasoning explicatif

---

### Test 3: Vérification Logs CloudWatch

**Objectif**: Valider les 2 appels Bedrock

**Logs attendus**:
```
[INFO] Normalisation V2 de X items via Bedrock
[INFO] Utilisation Approche B (prompt pré-construit)
[INFO] Réponse Bedrock reçue avec succès  # Appel 1: Normalisation
[INFO] Domain scoring: is_relevant=True, score=85  # Appel 2: Domain scoring
[INFO] Normalisation V2 terminée: X succès
```

---

## 📊 Métriques Attendues

### Performance

**Temps d'exécution** (5 items):
- Avant (1 appel): ~30-40s
- Après (2 appels): ~50-70s
- Augmentation: +40-50% (acceptable)

**Coût Bedrock** (par item):
- Avant: ~$0.007
- Après: ~$0.012-0.015
- Augmentation: +70% (acceptable pour valeur ajoutée)

### Qualité

**Taux de matching**:
- Objectif: Stable ou amélioré (>35%)
- Mesure: Comparer avec baseline lai_weekly_v7

**Précision scoring**:
- Objectif: Scores cohérents avec contenu
- Mesure: Vérifier reasoning vs score

---

## ⚠️ Points de Vigilance

### 1. Chargement Canonical

**Vérifier**: Les nouveaux dossiers sont bien chargés
- `canonical/prompts/domain_scoring/`
- `canonical/domains/`

**Action si échec**: Vérifier fonction de chargement des prompts/scopes

---

### 2. Timeout Lambda

**Actuel**: 900s (15 min)
**Suffisant**: Oui pour 5-10 items
**Attention**: Batch de 20+ items peut approcher la limite

**Action si timeout**: Réduire batch size ou augmenter timeout

---

### 3. Throttling Bedrock

**Risque**: 2 appels par item = 2x plus de requêtes
**Mitigation**: Mode séquentiel (max_workers=1) déjà en place

**Action si throttling**: Ajouter délai entre items

---

## ✅ Critères de Succès Phase 8

- [x] VERSION incrémentée (1.4.0)
- [x] Build réussi (vectora-core-1.4.0.zip)
- [x] Deploy dev réussi (layer v50)
- [x] Lambdas mises à jour automatiquement
- [x] Canonical synchronisé sur S3
- [ ] Test client legacy passé
- [ ] Test client avec domain scoring passé
- [ ] Logs CloudWatch validés
- [ ] Métriques collectées

---

## 🚀 Prochaines Étapes

**Immédiat**:
1. Exécuter Test 1 (client legacy)
2. Créer client lai_weekly_v9
3. Exécuter Test 2 (avec domain scoring)
4. Analyser logs CloudWatch
5. Collecter métriques

**Si tests OK**:
- Phase 9: Validation Stage
- Phase 10: Git, Documentation et Rapport Final

**Si tests KO**:
- Debug et correction
- Re-deploy
- Re-test

---

**Rapport créé le**: 2026-02-02  
**Phase**: 8  
**Statut**: ✅ Déploiement réussi - Tests en attente
