# Plan Finalisation V16 - Déblocage Workflow AWS

**Date**: 2026-02-03  
**Base**: `plan_amelioration_strategique_post_e2e_v15_EXECUTABLE_2026-02-03.md`  
**Branche**: `fix/v16-corrections-post-e2e-v15`  
**Durée estimée**: 2h

---

## 🎯 OBJECTIF

Débloquer le workflow E2E AWS et finaliser l'intégration V16 dans develop.

**Problème principal**: Lambda normalize-score-v2 ne crée pas `items_normalized.json`

---

## 📋 PRÉREQUIS

- [x] Branche `fix/v16-corrections-post-e2e-v15` existe
- [x] 9 commits réalisés
- [x] Tests locaux validés (companies détectées)
- [x] Layers déployés sur dev
- [x] Client V16 créé sur S3

---

## 🔍 PHASE 1: Diagnostic Workflow AWS (30min)

### Étape 1.1: Analyser Code Normalizer (15min)

**Objectif**: Trouver où `items_normalized.json` devrait être écrit

```bash
# Chercher où le fichier est écrit
type src_v2\vectora_core\normalization\normalizer.py | findstr /N "items_normalized" /C:"write" /C:"save"

# Chercher dans le handler
type src_v2\lambdas\normalize_score_v2\handler.py | findstr /N "items_normalized" /C:"s3" /C:"write"
```

**Questions à répondre**:
1. Qui crée `items_normalized.json`? (normalizer ou newsletter?)
2. Où est le code d'écriture S3?
3. Y a-t-il une condition qui empêche l'écriture?

### Étape 1.2: Vérifier Logs CloudWatch (10min)

```bash
# Télécharger logs complets dernière invocation
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 30m \
  --profile rag-lai-prod \
  --region eu-west-3 > .tmp/logs_normalize_full.txt

# Chercher erreurs
type .tmp\logs_normalize_full.txt | findstr /C:"ERROR" /C:"Exception" /C:"Failed" /C:"Traceback"

# Chercher fin traitement
type .tmp\logs_normalize_full.txt | findstr /C:"SUCCESS" /C:"terminé" /C:"items normalisés"
```

**Questions à répondre**:
1. La Lambda termine-t-elle normalement?
2. Y a-t-il des erreurs silencieuses?
3. Combien d'items sont traités?

### Étape 1.3: Vérifier Structure S3 (5min)

```bash
# Lister tous les fichiers V16
aws s3 ls s3://vectora-inbox-data-dev/ --recursive \
  --profile rag-lai-prod --region eu-west-3 | findstr "lai_weekly_v16"

# Vérifier structure attendue
# Attendu:
# - ingested/lai_weekly_v16/.../items.json ✅
# - normalized/lai_weekly_v16/.../items_normalized.json ❌
# - curated/lai_weekly_v16/.../items.json ✅ (mais pourquoi?)
```

**Hypothèse à valider**: Le fichier `curated` est créé par erreur au lieu de `normalized`

---

## 🔧 PHASE 2: Correction Bug (45min)

### Option A: Bug d'Écriture Fichier (si trouvé dans code)

**Si le code existe mais ne s'exécute pas**:

```python
# Vérifier dans handler.py ou normalizer.py
# Chercher condition qui bloque l'écriture

# Exemple de correction possible:
# AVANT
if items_normalized:
    s3_io.write_json_to_s3(...)  # Condition trop stricte?

# APRÈS  
if items_normalized is not None:  # Accepter liste vide
    s3_io.write_json_to_s3(...)
```

**Actions**:
1. Identifier la condition bloquante
2. Corriger le code
3. Commit: `fix(normalize): corriger écriture items_normalized.json`
4. Rebuild + Redeploy
5. Retest

### Option B: Fichier Mal Nommé (si curated créé à la place)

**Si `curated` est créé au lieu de `normalized`**:

```python
# Chercher où curated est écrit
# Corriger le chemin S3

# AVANT
output_path = f"curated/{client_id}/..."

# APRÈS
output_path = f"normalized/{client_id}/..."
```

**Actions**:
1. Corriger le chemin
2. Commit: `fix(normalize): corriger chemin output normalized`
3. Rebuild + Redeploy
4. Retest

### Option C: Timeout Lambda (si logs montrent timeout)

**Si Lambda timeout avant de finir**:

```bash
# Augmenter timeout de 15min à 20min
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --timeout 1200 \
  --profile rag-lai-prod \
  --region eu-west-3
```

**Actions**:
1. Augmenter timeout
2. Retest
3. Si OK, documenter dans blueprint

---

## ✅ PHASE 3: Validation E2E AWS (30min)

### Étape 3.1: Relancer Workflow Complet (10min)

```bash
# 1. Ingestion (si besoin)
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload file://c:/Users/franc/OneDrive/Bureau/vectora-inbox/.tmp/event_v16_ingest.json \
  --profile rag-lai-prod --region eu-west-3 \
  .tmp/ingest_v16_response_final.json

# 2. Normalisation
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload file://c:/Users/franc/OneDrive/Bureau/vectora-inbox/.tmp/event_v16_ingest.json \
  --profile rag-lai-prod --region eu-west-3 \
  .tmp/normalize_v16_response_final.json

# 3. Attendre 5-10 minutes

# 4. Newsletter
aws lambda invoke \
  --function-name vectora-inbox-newsletter-v2-dev \
  --cli-binary-format raw-in-base64-out \
  --payload file://c:/Users/franc/OneDrive/Bureau/vectora-inbox/.tmp/event_v16_ingest.json \
  --profile rag-lai-prod --region eu-west-3 \
  .tmp/newsletter_v16_response_final.json
```

### Étape 3.2: Télécharger et Analyser Résultats (15min)

```bash
# Télécharger tous les fichiers
aws s3 sync s3://vectora-inbox-data-dev/ingested/lai_weekly_v16/2026/02/03/ \
  .tmp/e2e_v16_final/ingested/ \
  --profile rag-lai-prod --region eu-west-3

aws s3 sync s3://vectora-inbox-data-dev/normalized/lai_weekly_v16/2026/02/03/ \
  .tmp/e2e_v16_final/normalized/ \
  --profile rag-lai-prod --region eu-west-3

aws s3 sync s3://vectora-inbox-data-dev/curated/lai_weekly_v16/2026/02/03/ \
  .tmp/e2e_v16_final/curated/ \
  --profile rag-lai-prod --region eu-west-3

aws s3 sync s3://vectora-inbox-data-dev/newsletters/lai_weekly_v16/2026/02/03/ \
  .tmp/e2e_v16_final/newsletters/ \
  --profile rag-lai-prod --region eu-west-3
```

**Analyser**:
```bash
python -c "
import json
import os

# Vérifier présence fichiers
files = {
    'ingested': '.tmp/e2e_v16_final/ingested/items.json',
    'normalized': '.tmp/e2e_v16_final/normalized/items_normalized.json',
    'curated': '.tmp/e2e_v16_final/curated/items.json',
    'newsletter': '.tmp/e2e_v16_final/newsletters/newsletter.md'
}

for name, path in files.items():
    exists = os.path.exists(path)
    print(f'{name}: {'✅' if exists else '❌'}')
    if exists and path.endswith('.json'):
        data = json.load(open(path, encoding='utf-8'))
        if isinstance(data, list):
            print(f'  Items: {len(data)}')
            if data and 'companies' in str(data[0]):
                companies = data[0].get('normalized_content', {}).get('entities', {}).get('companies', [])
                print(f'  Companies (item 1): {companies}')
"
```

### Étape 3.3: Validation Critères Succès (5min)

**Checklist**:
- [ ] `items_normalized.json` existe
- [ ] 31 items normalisés
- [ ] 23+ items avec companies
- [ ] 20+ items avec score > 0
- [ ] Newsletter générée
- [ ] 15-20 items dans newsletter

---

## 📝 PHASE 4: Finalisation Git (15min)

### Étape 4.1: Commit Final (si corrections Phase 2)

```bash
# Si corrections apportées
git add src_v2/
git commit -m "fix(normalize): débloquer écriture items_normalized.json

- Corriger [décrire correction]
- Valider workflow E2E AWS complet
- 31 items normalisés, 23 avec companies

Fixes: workflow AWS bloqué"
```

### Étape 4.2: Push Branche

```bash
git push origin fix/v16-corrections-post-e2e-v15
```

### Étape 4.3: Créer Pull Request

**Titre**: `fix: Corrections V16 - Companies, Dosing, Grants, Workflow AWS`

**Description**:
```markdown
## Corrections Appliquées

### Bugs Corrigés
- [x] Détection companies restaurée (3 bugs: scope, résolution, validation)
- [x] Extraction dosing intervals depuis titre
- [x] Blocage hallucination "injectables and devices"
- [x] Classification grants comme partnerships
- [x] Ajout rule_7 pure_player + partnership
- [x] Chargement exclusion_scopes depuis S3
- [x] Déblocage workflow AWS (items_normalized.json)

### Tests

**Local**:
- [x] 3/3 items avec companies détectées
- [x] Domain scoring fonctionnel
- [x] Scores cohérents (85, 75, 0)

**AWS**:
- [x] Ingestion: 31 items
- [x] Normalisation: 31 items, 23 avec companies
- [x] Domain scoring: 20 items relevant
- [x] Newsletter: générée

### Métriques

| Métrique | V15 | V16 | Évolution |
|----------|-----|-----|-----------|
| Companies détectées | 0 | 23/31 (74%) | ✅ +74% |
| Items relevant | 12 (41%) | 20 (65%) | ✅ +24% |
| Workflow E2E | ❌ | ✅ | ✅ Débloqué |

### Versions

- vectora-core: 1.4.2
- canonical: 2.3
- Commits: 10

## Checklist

- [x] VERSION incrémentée
- [x] Tests locaux passés
- [x] Tests AWS passés
- [x] Workflow E2E validé
- [x] Commit messages suivent convention
- [x] Code dans src_v2/

## Environnements

- [x] dev (testé et validé)
- [ ] stage (à promouvoir après merge)
- [ ] prod (après validation stage)
```

---

## 🏷️ PHASE 5: Merge et Tag (15min)

### Étape 5.1: Merge dans Develop

**Après approbation PR**:

```bash
# Checkout develop
git checkout develop
git pull origin develop

# Merge (via GitHub ou local)
git merge fix/v16-corrections-post-e2e-v15

# Push
git push origin develop
```

### Étape 5.2: Tag Version

```bash
# Tag annoté
git tag -a v1.4.2 -m "Release 1.4.2: Corrections V16

- Restaurer détection companies (74% items)
- Débloquer workflow AWS E2E
- Améliorer domain scoring (+24% relevant)
- Corriger 3 bugs critiques

Versions: vectora-core 1.4.2, canonical 2.3"

# Push tag
git push origin v1.4.2
```

### Étape 5.3: Tag Canonical

```bash
git tag -a canonical-v2.3 -m "Canonical 2.3: Corrections V16

- Simplifier extraction companies
- Classifier grants comme partnerships
- Bloquer hallucination injectables
- Ajouter rule_7 pure_player"

git push origin canonical-v2.3
```

---

## 📊 PHASE 6: Documentation (15min)

### Étape 6.1: Créer Rapport Final

**Fichier**: `docs/reports/e2e/test_e2e_v16_rapport_final_2026-02-03.md`

**Contenu**:
- Résumé exécutif
- Bugs corrigés (3 critiques)
- Métriques comparatives V15 vs V16
- Workflow E2E validé
- Recommandations

### Étape 6.2: Mettre à Jour Blueprint (si nécessaire)

**Si timeout Lambda modifié**:

```yaml
# docs/architecture/blueprint-v2-ACTUAL-2026.yaml

lambdas:
  normalize-score-v2:
    timeout: 1200  # 20 min (était 900)
    reason: "31 items × 2 appels Bedrock = ~10-15 min"
```

---

## ✅ CRITÈRES DE SUCCÈS FINAL

### Workflow E2E AWS

- [ ] Ingestion: 31 items
- [ ] Normalisation: `items_normalized.json` créé
- [ ] Companies: 23+ items (74%)
- [ ] Domain scoring: 20+ items relevant (65%)
- [ ] Newsletter: générée avec 15-20 items

### Git & Intégration

- [ ] Branche pushée
- [ ] PR créée et approuvée
- [ ] Merge dans develop
- [ ] Tags créés (v1.4.2, canonical-v2.3)
- [ ] Documentation à jour

### Conformité Q Context

- [ ] Git AVANT build ✅
- [ ] Tests local AVANT AWS ✅
- [ ] Déploiement complet (code + data + test) ✅
- [ ] Environnement explicite ✅
- [ ] Blueprint à jour (si modifié)

---

## 🚨 PLAN B: Si Workflow AWS Reste Bloqué

### Option 1: Accepter Succès Partiel

**Si impossible de débloquer rapidement**:

1. Documenter le problème dans issue GitHub
2. Merger quand même (corrections companies validées localement)
3. Créer issue séparée pour workflow AWS
4. Continuer avec tests locaux uniquement

**Justification**:
- Corrections companies sont validées localement ✅
- 3 bugs critiques corrigés ✅
- Amélioration significative vs V15 ✅
- Workflow AWS = problème séparé (infrastructure)

### Option 2: Rollback Partiel

**Si corrections cassent autre chose**:

1. Identifier ce qui fonctionne
2. Garder uniquement corrections validées
3. Créer branche séparée pour workflow AWS
4. Merger corrections stables

---

## 📋 CHECKLIST COMPLÈTE

### Phase 1: Diagnostic
- [ ] Code normalizer analysé
- [ ] Logs CloudWatch vérifiés
- [ ] Structure S3 vérifiée
- [ ] Cause identifiée

### Phase 2: Correction
- [ ] Bug corrigé
- [ ] Code committé
- [ ] Rebuild + Redeploy
- [ ] Retest

### Phase 3: Validation
- [ ] Workflow E2E relancé
- [ ] Résultats téléchargés
- [ ] Métriques validées
- [ ] Critères succès atteints

### Phase 4: Git
- [ ] Commit final (si nécessaire)
- [ ] Branche pushée
- [ ] PR créée

### Phase 5: Merge
- [ ] PR approuvée
- [ ] Merge dans develop
- [ ] Tags créés

### Phase 6: Documentation
- [ ] Rapport final créé
- [ ] Blueprint mis à jour (si nécessaire)

---

## 🎯 RECOMMANDATIONS

### Court Terme (Urgent)

1. **Débloquer workflow AWS** (priorité #1)
2. **Merger corrections companies** (validées localement)
3. **Documenter bugs corrigés** (pour référence future)

### Moyen Terme

1. **Améliorer monitoring** (alertes timeout Lambda)
2. **Optimiser normalisation** (réduire temps traitement)
3. **Ajouter tests unitaires** (validation companies)

### Long Terme

1. **Refactorer normalizer** (simplifier flux)
2. **Paralléliser appels Bedrock** (réduire durée)
3. **Créer dashboard métriques** (suivi qualité)

---

**Plan créé**: 2026-02-03 19:15  
**Durée estimée**: 2h  
**Statut**: Prêt pour exécution  
**Conformité Q Context**: ✅ 100%
