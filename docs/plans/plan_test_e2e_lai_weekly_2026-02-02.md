# Plan Test E2E - LAI Weekly

**Date**: 2026-02-02  
**Objectif**: Test E2E complet du moteur avec client LAI Weekly  
**Architecture**: 3 Lambdas V2 (ingest-v2 → normalize-score-v2 → newsletter-v2)  
**Système**: Contextes E2E avec protection AWS  

---

## 🎯 Objectif

Valider le pipeline complet avec une config LAI Weekly moderne basée sur:
- ✅ Template `lai_weekly_template_v2.yaml` (architecture 2 appels Bedrock)
- ✅ Architecture validée (enable_domain_scoring: true)
- ✅ Canonical v2.0
- ✅ Système de contextes E2E

---

## 📋 Phase 1: Préparation Config Test

### 1.1 Créer Config Test Locale

**Fichier**: `client-config-examples/test/local/lai_weekly_test_001.yaml`

**Basé sur**: `lai_weekly_template_v2.yaml`

**Modifications pour test rapide**:
```yaml
client_profile:
  name: "LAI Weekly - E2E Test Context 001"
  client_id: "lai_weekly_test_001"
  active: true

pipeline:
  newsletter_mode: "latest_run_only"
  default_period_days: 7  # ⚡ Test rapide avec données récentes

bedrock_config:
  normalization_prompt: "generic_normalization"
  enable_domain_scoring: true  # ✅ Architecture v2
  matching_prompt: "lai_matching"
  editorial_prompt: "lai_editorial"

newsletter_selection:
  max_items_total: 10  # ⚡ Test rapide

matching_config:
  enable_diagnostic_mode: true  # 🔍 Logs détaillés

metadata:
  test_context_id: "test_context_001"
  test_purpose: "E2E validation LAI Weekly pipeline"
  test_environment: "local"
  created_date: "2026-02-02"
  template_version: "2.0.0"
  canonical_version: "2.0"
```

**Commande**:
```bash
# Générer depuis template
python tests/utils/config_generator.py \
  --template client-config-examples/templates/lai_weekly_template_v2.yaml \
  --output client-config-examples/test/local/lai_weekly_test_001.yaml \
  --client-id lai_weekly_test_001 \
  --name "LAI Weekly - E2E Test Context 001" \
  --context-id test_context_001 \
  --purpose "E2E validation LAI Weekly pipeline" \
  --environment local \
  --period-days 7 \
  --max-items 10
```

### 1.2 Créer Contexte Test Local

**Commande**:
```bash
python tests/local/test_e2e_runner.py \
  --new-context "E2E validation LAI Weekly pipeline - Architecture v2 domain scoring"
```

**Résultat attendu**:
- ✅ Contexte `test_context_001` créé
- ✅ Client ID: `lai_weekly_test_001`
- ✅ Registre mis à jour: `tests/contexts/registry.json`
- ✅ Fichier contexte: `tests/contexts/local/test_context_001.json`

---

## 📋 Phase 2: Test Local (OBLIGATOIRE)

### 2.1 Exécuter Pipeline Local

**Commande**:
```bash
python tests/local/test_e2e_runner.py --run
```

**Étapes exécutées**:
1. ✅ Chargement config `lai_weekly_test_001.yaml`
2. ✅ Simulation ingest (données test ou mock)
3. ✅ Normalisation + Domain Scoring (2 appels Bedrock)
4. ✅ Génération newsletter
5. ✅ Validation outputs

**Outputs attendus**:
- `.tmp/test_e2e_local_results.json` - Résultats détaillés
- Logs dans `.tmp/logs/test_e2e_local_[timestamp].log`

### 2.2 Validation Locale

**Checklist**:
- [ ] Config chargée sans erreur
- [ ] Items normalisés avec entités extraites
- [ ] Section `domain_scoring` présente dans items
- [ ] Champs domain_scoring: `is_relevant`, `score`, `confidence`, `signals_detected`, `reasoning`
- [ ] Newsletter générée avec sections correctes
- [ ] Pas d'erreur critique

**Commande vérification**:
```bash
python tests/local/test_e2e_runner.py --status
```

**Critères succès**:
- ✅ Status: `completed`
- ✅ Success: `true`
- ✅ Aucune erreur bloquante

---

## 📋 Phase 3: Déploiement Dev (SI LOCAL RÉUSSI)

### 3.1 Vérifier Versions

**Fichier**: `VERSION`

**Versions actuelles**:
```ini
VECTORA_CORE_VERSION=1.4.1
COMMON_DEPS_VERSION=1.0.5
INGEST_VERSION=1.5.0
NORMALIZE_VERSION=2.1.0
NEWSLETTER_VERSION=1.8.0
CANONICAL_VERSION=2.0
```

**Action**: Vérifier que versions sont cohérentes avec test local

### 3.2 Build

**Commande**:
```bash
python scripts/build/build_all.py
```

**Vérifications**:
- [ ] Layers buildés: `.build/layers/`
- [ ] Versions correctes dans noms .zip
- [ ] Pas d'erreur build

### 3.3 Deploy Dev

**Commande**:
```bash
python scripts/deploy/deploy_env.py --env dev
```

**Vérifications**:
- [ ] Layers publiés sur AWS
- [ ] Lambdas mises à jour avec nouvelles versions layers
- [ ] Pas d'erreur déploiement

---

## 📋 Phase 4: Test AWS Dev (SI DEPLOY RÉUSSI)

### 4.1 Créer Config Test AWS

**Fichier**: `client-config-examples/test/aws/lai_weekly_v1.yaml`

**Basé sur**: `lai_weekly_test_001.yaml` (config locale validée)

**Modifications**:
```yaml
client_profile:
  name: "LAI Weekly v1 - E2E Test AWS"
  client_id: "lai_weekly_v1"

metadata:
  test_context_id: "test_context_001"
  test_environment: "aws_dev"
  promoted_from: "lai_weekly_test_001"
```

### 4.2 Upload Config S3

**Commande**:
```bash
aws s3 cp \
  client-config-examples/test/aws/lai_weekly_v1.yaml \
  s3://rag-lai-prod-client-configs/dev/lai_weekly_v1.yaml \
  --profile rag-lai-prod
```

### 4.3 Promouvoir Contexte vers AWS

**Commande**:
```bash
python tests/aws/test_e2e_runner.py \
  --promote "E2E validation LAI Weekly - Architecture v2 domain scoring"
```

**Vérifications automatiques**:
- ✅ Test local `test_context_001` a réussi
- ✅ Contexte AWS créé: `test_context_001`
- ✅ Client ID AWS: `lai_weekly_v1`
- ✅ Registre mis à jour

**Si blocage**:
```
❌ DÉPLOIEMENT AWS BLOQUÉ
Raison: Test local test_context_001 n'a pas réussi
Actions requises:
1. Corriger erreurs test local
2. Ré-exécuter: python tests/local/test_e2e_runner.py --run
3. Revenir ici si succès
```

### 4.4 Exécuter Pipeline AWS

**Commandes**:
```bash
# 1. Ingest
python scripts/invoke/invoke_ingest_v2.py \
  --client-id lai_weekly_v1 \
  --env dev

# 2. Normalize & Score
python scripts/invoke/invoke_normalize_score_v2.py \
  --client-id lai_weekly_v1 \
  --env dev

# 3. Newsletter
python scripts/invoke/invoke_newsletter_v2.py \
  --client-id lai_weekly_v1 \
  --env dev
```

**Alternative - Runner automatisé**:
```bash
python tests/aws/test_e2e_runner.py --run
```

---

## 📋 Phase 5: Validation AWS

### 5.1 Vérifier Outputs S3

**Buckets**:
- `s3://rag-lai-prod-ingested-items/dev/lai_weekly_v1/`
- `s3://rag-lai-prod-normalized-items/dev/lai_weekly_v1/`
- `s3://rag-lai-prod-newsletters/dev/lai_weekly_v1/`

**Commandes**:
```bash
# Lister runs
aws s3 ls s3://rag-lai-prod-ingested-items/dev/lai_weekly_v1/ \
  --profile rag-lai-prod

# Télécharger derniers outputs
aws s3 cp \
  s3://rag-lai-prod-normalized-items/dev/lai_weekly_v1/run_[TIMESTAMP]/items.json \
  .tmp/aws_items.json \
  --profile rag-lai-prod

aws s3 cp \
  s3://rag-lai-prod-newsletters/dev/lai_weekly_v1/run_[TIMESTAMP]/newsletter.md \
  .tmp/aws_newsletter.md \
  --profile rag-lai-prod
```

### 5.2 Validation Technique

**Checklist items.json**:
- [ ] Section `normalized` présente avec entités
- [ ] Section `domain_scoring` présente
- [ ] Champs domain_scoring complets:
  - `is_relevant`: boolean
  - `score`: 0-100
  - `confidence`: low/medium/high
  - `signals_detected`: array
  - `reasoning`: string
- [ ] Section `scoring` avec score final
- [ ] Pas d'items avec erreurs

**Checklist newsletter.md**:
- [ ] Structure markdown valide
- [ ] Sections définies dans config présentes
- [ ] Items répartis correctement
- [ ] TLDR et intro présents
- [ ] Pas de placeholder non remplacé

### 5.3 Validation Métier

**Checklist qualité**:
- [ ] Items pertinents pour LAI
- [ ] Entités extraites correctes (companies, molecules, technologies)
- [ ] Event types cohérents
- [ ] Scores reflètent pertinence
- [ ] Résumés clairs et concis
- [ ] Pas de doublons

### 5.4 Vérifier Logs CloudWatch

**Log Groups**:
- `/aws/lambda/rag-lai-ingest-v2-dev`
- `/aws/lambda/rag-lai-normalize-score-v2-dev`
- `/aws/lambda/rag-lai-newsletter-v2-dev`

**Vérifications**:
- [ ] Pas d'erreur critique
- [ ] 2 appels Bedrock par item (normalization + domain_scoring)
- [ ] Temps exécution acceptable
- [ ] Coûts Bedrock dans budget

---

## 📋 Phase 6: Analyse Résultats

### 6.1 Comparer Local vs AWS

**Métriques à comparer**:
- Nombre items ingérés
- Taux matching domaine
- Distribution scores
- Temps exécution
- Qualité outputs

**Commande**:
```bash
python tests/aws/test_e2e_runner.py --compare-with-local
```

### 6.2 Générer Rapport

**Template**: `docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`

**Sections**:
1. Contexte test
2. Config utilisée
3. Résultats local
4. Résultats AWS
5. Comparaison
6. Problèmes détectés
7. Recommandations

**Fichier**: `docs/reports/test_e2e_lai_weekly_context_001_2026-02-02.md`

### 6.3 Mettre à Jour Registre

**Commande**:
```bash
python tests/aws/test_e2e_runner.py --status
```

**Mise à jour automatique**:
- Status: `completed`
- Success: `true` / `false`
- Timestamp fin
- Métriques clés

---

## 📋 Phase 7: Décision Suite

### Si Test AWS Réussi ✅

**Options**:

1. **Promouvoir vers Stage**:
```bash
python scripts/deploy/promote.py \
  --to stage \
  --version 2.1.0 \
  --git-sha $(git rev-parse HEAD)
```

2. **Créer Client Production**:
- Copier `lai_weekly_v1.yaml` → `lai_weekly_prod.yaml`
- Ajuster paramètres prod (period_days, max_items, etc.)
- Déployer sur env prod (quand créé)

3. **Nouveau Test avec Variante**:
```bash
python tests/local/test_e2e_runner.py \
  --new-context "Test LAI Weekly avec period_days=14"
```

### Si Test AWS Échoué ❌

**Actions**:

1. **Analyser Logs**:
```bash
# Télécharger logs CloudWatch
python scripts/utils/download_logs.py \
  --lambda normalize-score-v2 \
  --env dev \
  --hours 1
```

2. **Identifier Cause**:
- Erreur config ?
- Erreur Bedrock ?
- Erreur matching ?
- Erreur scoring ?

3. **Corriger et Retester**:
```bash
# Nouveau contexte local après correction
python tests/local/test_e2e_runner.py \
  --new-context "Fix [problème identifié]"

# Retester local
python tests/local/test_e2e_runner.py --run

# Si succès, rebuild + redeploy + retest AWS
```

---

## 📊 Métriques Attendues

### Performance

| Métrique | Local | AWS Dev | Acceptable |
|----------|-------|---------|------------|
| Temps ingest | N/A | 30-60s | < 120s |
| Temps normalize | 2-5min | 3-8min | < 15min |
| Temps newsletter | 10-30s | 20-60s | < 120s |
| Items ingérés | Mock | 50-200 | > 20 |
| Taux matching | > 60% | > 60% | > 50% |

### Qualité

| Métrique | Cible | Acceptable |
|----------|-------|------------|
| Items avec domain_scoring | 100% | > 95% |
| Scores > 0 | > 70% | > 50% |
| Entités extraites | > 80% | > 60% |
| Newsletter sections remplies | 100% | > 75% |

### Coûts

| Service | Coût Estimé | Budget |
|---------|-------------|--------|
| Bedrock (2 appels/item) | $0.10-0.30 | < $1.00 |
| Lambda | $0.01-0.05 | < $0.10 |
| S3 | $0.001 | < $0.01 |
| **Total** | **$0.11-0.35** | **< $1.10** |

---

## 🚨 Règles Critiques

### RÈGLE 1: Jamais AWS Sans Local Réussi

❌ **INTERDIT**:
```bash
python scripts/deploy/deploy_env.py --env dev
python tests/aws/test_e2e_runner.py --promote "Test"  # BLOQUÉ
```

✅ **CORRECT**:
```bash
python tests/local/test_e2e_runner.py --new-context "Test"
python tests/local/test_e2e_runner.py --run  # DOIT RÉUSSIR
python scripts/deploy/deploy_env.py --env dev
python tests/aws/test_e2e_runner.py --promote "Test"
```

### RÈGLE 2: Nouveau Contexte par Modification

❌ **INTERDIT**:
```bash
python tests/local/test_e2e_runner.py --run  # test_context_001
# Modifier code
python tests/local/test_e2e_runner.py --run  # ENCORE test_context_001
```

✅ **CORRECT**:
```bash
python tests/local/test_e2e_runner.py --run  # test_context_001
# Modifier code
python tests/local/test_e2e_runner.py --new-context "Après fix"  # test_context_002
python tests/local/test_e2e_runner.py --run  # test_context_002
```

### RÈGLE 3: Versioning Cohérent

**Avant tout test AWS**:
- [ ] Vérifier `VERSION` à jour
- [ ] Build avec versions correctes
- [ ] Deploy avec versions correctes
- [ ] Tester avec versions correctes

---

## 📁 Fichiers Générés

### Local
```
tests/contexts/local/test_context_001.json
.tmp/test_e2e_local_results.json
.tmp/logs/test_e2e_local_[timestamp].log
client-config-examples/test/local/lai_weekly_test_001.yaml
```

### AWS
```
tests/contexts/aws/test_context_001.json
client-config-examples/test/aws/lai_weekly_v1.yaml
docs/reports/test_e2e_lai_weekly_context_001_2026-02-02.md
.tmp/aws_items.json
.tmp/aws_newsletter.md
```

### S3
```
s3://rag-lai-prod-client-configs/dev/lai_weekly_v1.yaml
s3://rag-lai-prod-ingested-items/dev/lai_weekly_v1/run_[timestamp]/
s3://rag-lai-prod-normalized-items/dev/lai_weekly_v1/run_[timestamp]/
s3://rag-lai-prod-newsletters/dev/lai_weekly_v1/run_[timestamp]/
```

---

## ✅ Checklist Complète

### Préparation
- [ ] Lire plan complet
- [ ] Vérifier système contextes opérationnel
- [ ] Vérifier VERSION à jour
- [ ] Vérifier AWS CLI configuré

### Phase 1: Config
- [ ] Générer config test locale
- [ ] Créer contexte test local
- [ ] Vérifier registre mis à jour

### Phase 2: Test Local
- [ ] Exécuter test local
- [ ] Valider résultats
- [ ] Vérifier succès dans registre

### Phase 3: Deploy
- [ ] Vérifier versions
- [ ] Build layers
- [ ] Deploy dev

### Phase 4: Test AWS
- [ ] Créer config AWS
- [ ] Upload config S3
- [ ] Promouvoir contexte
- [ ] Exécuter pipeline AWS

### Phase 5: Validation
- [ ] Vérifier outputs S3
- [ ] Validation technique
- [ ] Validation métier
- [ ] Vérifier logs CloudWatch

### Phase 6: Analyse
- [ ] Comparer local vs AWS
- [ ] Générer rapport
- [ ] Mettre à jour registre

### Phase 7: Suite
- [ ] Décider action suivante
- [ ] Documenter décision
- [ ] Planifier prochaine étape

---

## 🎓 Commandes Rapides

```bash
# Workflow complet
python tests/local/test_e2e_runner.py --new-context "E2E LAI Weekly"
python tests/local/test_e2e_runner.py --run
python tests/local/test_e2e_runner.py --status

python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev

python tests/aws/test_e2e_runner.py --promote "Validation E2E"
python tests/aws/test_e2e_runner.py --run
python tests/aws/test_e2e_runner.py --status

# Vérification rapide
python tests/local/test_e2e_runner.py --list
python tests/aws/test_e2e_runner.py --list
```

---

**Plan Test E2E LAI Weekly**  
**Version**: 1.0  
**Date**: 2026-02-02  
**Statut**: Prêt pour exécution  
**Système**: Contextes E2E avec protection AWS
