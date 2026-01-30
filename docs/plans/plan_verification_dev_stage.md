# Plan de Vérification et Comparaison - Environnements Dev vs Stage

**Date**: 2026-01-30  
**Objectif**: Valider qualité promotion dev → stage et fonctionnement moteur stage  
**Client test**: lai_weekly_v7  
**Durée estimée**: 60 minutes

---

## 🎯 OBJECTIFS

1. **Vérifier parité complète** dev vs stage (infrastructure, code, configs)
2. **Évaluer qualité promotion** dev → stage effectuée
3. **Tester moteur stage E2E** avec lai_weekly_v7
4. **Valider isolation** environnements (dev modifiable sans risque)
5. **Confirmer environnement propre** et production-ready

---

## 📋 PHASES DU PLAN

### PHASE 0: Audit Infrastructure (10 min)

**Objectif**: Inventorier et comparer ressources AWS dev vs stage

#### 0.1 Buckets S3

**Commandes**:
```bash
# Lister buckets dev
aws s3 ls --profile rag-lai-prod --region eu-west-3 | findstr "vectora-inbox.*dev"

# Lister buckets stage
aws s3 ls --profile rag-lai-prod --region eu-west-3 | findstr "vectora-inbox.*stage"
```

**Validation**:
```
Bucket                          | Dev | Stage | Statut
--------------------------------|-----|-------|--------
vectora-inbox-config            | ✅  | ✅    |
vectora-inbox-data              | ✅  | ✅    |
vectora-inbox-newsletters       | ✅  | ✅    |
vectora-inbox-lambda-code       | ✅  | ✅    |
```

**Checklist**:
- [ ] 4 buckets dev présents
- [ ] 4 buckets stage présents
- [ ] Nommage cohérent (-dev, -stage)

#### 0.2 Lambda Layers

**Commandes**:
```bash
# Lister layers dev
aws lambda list-layers --profile rag-lai-prod --region eu-west-3 \
  --query "Layers[?contains(LayerName, 'dev')].LayerName" --output table

# Lister layers stage
aws lambda list-layers --profile rag-lai-prod --region eu-west-3 \
  --query "Layers[?contains(LayerName, 'stage')].LayerName" --output table
```

**Validation**:
```
Layer                           | Dev | Stage | Statut
--------------------------------|-----|-------|--------
vectora-inbox-vectora-core      | ✅  | ✅    |
vectora-inbox-common-deps       | ✅  | ✅    |
```

**Checklist**:
- [ ] 2 layers dev présents
- [ ] 2 layers stage présents
- [ ] Versions cohérentes

#### 0.3 Lambdas

**Commandes**:
```bash
# Lister Lambdas dev
aws lambda list-functions --profile rag-lai-prod --region eu-west-3 \
  --query "Functions[?contains(FunctionName, 'v2-dev')].FunctionName" --output table

# Lister Lambdas stage
aws lambda list-functions --profile rag-lai-prod --region eu-west-3 \
  --query "Functions[?contains(FunctionName, 'v2-stage')].FunctionName" --output table
```

**Validation**:
```
Lambda                          | Dev | Stage | Statut
--------------------------------|-----|-------|--------
vectora-inbox-ingest-v2         | ✅  | ✅    |
vectora-inbox-normalize-score-v2| ✅  | ✅    |
vectora-inbox-newsletter-v2     | ✅  | ✅    |
```

**Checklist**:
- [ ] 3 Lambdas dev présentes
- [ ] 3 Lambdas stage présentes
- [ ] Nommage cohérent

**CRITIQUE**: Vérifier que newsletter-v2-stage existe (oubli corrigé)

---

### PHASE 1: Comparaison Configurations (15 min)

**Objectif**: Vérifier synchronisation configs dev → stage

#### 1.1 Configurations Lambda

**Script de comparaison**:
```bash
# Créer script compare_lambda_configs.ps1
```

**Métriques à comparer**:
```
Métrique                | Dev    | Stage  | Match
------------------------|--------|--------|-------
Runtime ingest          |        |        |
Runtime normalize       |        |        |
Runtime newsletter      |        |        |
Memory ingest           |        |        |
Memory normalize        |        |        |
Memory newsletter       |        |        |
Timeout ingest          |        |        |
Timeout normalize       |        |        |
Timeout newsletter      |        |        |
Layers ingest           |        |        |
Layers normalize        |        |        |
Layers newsletter       |        |        |
```

**Checklist**:
- [ ] Runtimes identiques (sauf versions Python acceptables)
- [ ] Memory sizes cohérentes
- [ ] Timeouts identiques
- [ ] Layers attachés correctement

#### 1.2 Variables Environnement

**Commandes**:
```bash
# Dev
aws lambda get-function-configuration \
  --function-name vectora-inbox-ingest-v2-dev \
  --profile rag-lai-prod --region eu-west-3 \
  --query "Environment.Variables" > .tmp/env_ingest_dev.json

# Stage
aws lambda get-function-configuration \
  --function-name vectora-inbox-ingest-v2-stage \
  --profile rag-lai-prod --region eu-west-3 \
  --query "Environment.Variables" > .tmp/env_ingest_stage.json
```

**Validation**:
```
Variable                | Dev Value              | Stage Value            | Correct
------------------------|------------------------|------------------------|--------
ENV                     | dev                    | stage                  | ✅
CONFIG_BUCKET           | ...-config-dev         | ...-config-stage       | ✅
DATA_BUCKET             | ...-data-dev           | ...-data-stage         | ✅
NEWSLETTERS_BUCKET      | ...-newsletters-dev    | ...-newsletters-stage  | ✅
BEDROCK_MODEL_ID        | (identique)            | (identique)            | ✅
BEDROCK_REGION          | us-east-1              | us-east-1              | ✅
LOG_LEVEL               | INFO                   | INFO                   | ✅
```

**Checklist**:
- [ ] ENV correctement défini (dev/stage)
- [ ] Buckets pointent vers bon environnement
- [ ] Bedrock config identique
- [ ] Aucune variable hardcodée incorrecte

#### 1.3 Canonical

**Commandes**:
```bash
# Compter fichiers canonical dev
aws s3 ls s3://vectora-inbox-config-dev/canonical/ --recursive \
  --profile rag-lai-prod --region eu-west-3 | find /c /v ""

# Compter fichiers canonical stage
aws s3 ls s3://vectora-inbox-config-stage/canonical/ --recursive \
  --profile rag-lai-prod --region eu-west-3 | find /c /v ""
```

**Validation**:
```
Dossier                 | Dev    | Stage  | Match
------------------------|--------|--------|-------
scopes/                 |        |        |
prompts/                |        |        |
sources/                |        |        |
scoring/                |        |        |
ingestion/              |        |        |
events/                 |        |        |
matching/               |        |        |
imports/                |        |        |
TOTAL                   | 37     | 37     | ✅
```

**Checklist**:
- [ ] Même nombre de fichiers
- [ ] Fichiers critiques présents (scopes, prompts)
- [ ] Tailles cohérentes

#### 1.4 Config Client lai_weekly

**Commandes**:
```bash
# Télécharger configs
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly.yaml \
  .tmp/lai_weekly_dev.yaml --profile rag-lai-prod --region eu-west-3

aws s3 cp s3://vectora-inbox-config-stage/clients/lai_weekly.yaml \
  .tmp/lai_weekly_stage.yaml --profile rag-lai-prod --region eu-west-3

# Comparer
fc .tmp\lai_weekly_dev.yaml .tmp\lai_weekly_stage.yaml
```

**Validation**:
- [ ] Fichiers identiques
- [ ] client_id: "lai_weekly"
- [ ] version: "7.0.0"

---

### PHASE 2: Évaluation Qualité Promotion (10 min)

**Objectif**: Analyser qualité de la promotion dev → stage effectuée

#### 2.1 Grille d'Évaluation

```
Critère                         | Note /10 | Commentaire
--------------------------------|----------|-------------
Parité infrastructure           |          |
Parité configurations           |          |
Parité code Lambda              |          |
Variables env correctes         |          |
Isolation environnements        |          |
Documentation promotion         |          |
Scripts promotion               |          |
Rollback possible               |          |
Tests validation                |          |
Traçabilité                     |          |
--------------------------------|----------|-------------
MOYENNE                         |          |
```

**Échelle**:
- 9-10: Excellent
- 7-8: Bon
- 5-6: Acceptable
- 3-4: Insuffisant
- 0-2: Critique

#### 2.2 Points Forts Identifiés

```
1. _________________________________
2. _________________________________
3. _________________________________
```

#### 2.3 Points d'Amélioration

```
1. _________________________________
2. _________________________________
3. _________________________________
```

#### 2.4 Risques Identifiés

```
Risque                          | Probabilité | Impact | Mitigation
--------------------------------|-------------|--------|------------
                                |             |        |
                                |             |        |
                                |             |        |
```

---

### PHASE 3: Test E2E Stage - lai_weekly_v7 (20 min)

**Objectif**: Valider fonctionnement complet moteur sur stage

#### 3.1 Préparation

**Vérifier config lai_weekly_v7 en stage**:
```bash
# Copier config v7 vers stage si nécessaire
aws s3 cp s3://vectora-inbox-config-dev/clients/lai_weekly_v7.yaml \
  s3://vectora-inbox-config-stage/clients/lai_weekly_v7.yaml \
  --profile rag-lai-prod --region eu-west-3
```

**Checklist**:
- [ ] Config lai_weekly_v7.yaml présente en stage
- [ ] Canonical synchronisé
- [ ] Buckets stage vides (pas de données résiduelles)

#### 3.2 Test Ingest Stage

**Event**: `.tmp/event_ingest_v7_stage.json`
```json
{
  "client_id": "lai_weekly_v7",
  "force_refresh": true
}
```

**Commande**:
```bash
aws lambda invoke --function-name vectora-inbox-ingest-v2-stage \
  --cli-binary-format raw-in-base64-out \
  --payload file://.tmp/event_ingest_v7_stage.json \
  --region eu-west-3 --profile rag-lai-prod \
  .tmp/response_ingest_v7_stage.json
```

**Validation**:
```bash
# Vérifier réponse
type .tmp\response_ingest_v7_stage.json | jq ".statusCode"

# Vérifier items ingérés
aws s3 ls s3://vectora-inbox-data-stage/ingested/lai_weekly_v7/ \
  --recursive --profile rag-lai-prod --region eu-west-3
```

**Métriques**:
```
Métrique                | Attendu | Réel   | Statut
------------------------|---------|--------|--------
StatusCode              | 200     |        |
Items ingérés           | 20-25   |        |
Temps exécution         | <30s    |        |
Erreurs                 | 0       |        |
```

**Checklist**:
- [ ] Lambda exécutée sans erreur
- [ ] Items présents dans S3 stage
- [ ] Nombre items cohérent
- [ ] Temps exécution acceptable

#### 3.3 Test Normalize-Score Stage

**Event**: `.tmp/event_normalize_v7_stage.json`
```json
{
  "client_id": "lai_weekly_v7"
}
```

**Commande**:
```bash
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-stage \
  --cli-binary-format raw-in-base64-out \
  --payload file://.tmp/event_normalize_v7_stage.json \
  --region eu-west-3 --profile rag-lai-prod \
  .tmp/response_normalize_v7_stage.json
```

**Validation**:
```bash
# Vérifier réponse
type .tmp\response_normalize_v7_stage.json | jq ".statusCode"

# Télécharger items curated
aws s3 cp s3://vectora-inbox-data-stage/curated/lai_weekly_v7/2026/01/30/items.json \
  .tmp/items_curated_v7_stage.json --profile rag-lai-prod --region eu-west-3

# Analyser extraction dates
type .tmp\items_curated_v7_stage.json | jq "[.[] | select(.normalized_content.extracted_date != null)] | length"
```

**Métriques**:
```
Métrique                | Attendu | Réel   | Statut
------------------------|---------|--------|--------
StatusCode              | 200     |        |
Items matched           | >15     |        |
Dates extraites (%)     | >95%    |        |
Temps exécution         | <10min  |        |
Appels Bedrock          | ~30     |        |
Erreurs                 | 0       |        |
```

**Checklist**:
- [ ] Lambda exécutée sans erreur
- [ ] Items curated présents dans S3 stage
- [ ] Extraction dates fonctionnelle
- [ ] Matching fonctionnel
- [ ] Scoring cohérent

#### 3.4 Test Newsletter Stage

**Event**: `.tmp/event_newsletter_v7_stage.json`
```json
{
  "client_id": "lai_weekly_v7"
}
```

**Commande**:
```bash
aws lambda invoke --function-name vectora-inbox-newsletter-v2-stage \
  --cli-binary-format raw-in-base64-out \
  --payload file://.tmp/event_newsletter_v7_stage.json \
  --region eu-west-3 --profile rag-lai-prod \
  .tmp/response_newsletter_v7_stage.json
```

**Validation**:
```bash
# Vérifier réponse
type .tmp\response_newsletter_v7_stage.json | jq ".statusCode"

# Télécharger newsletter
aws s3 cp s3://vectora-inbox-newsletters-stage/lai_weekly_v7/2026/01/30/newsletter.md \
  .tmp/newsletter_v7_stage.md --profile rag-lai-prod --region eu-west-3

# Vérifier dates affichées
type .tmp\newsletter_v7_stage.md | findstr "Date:"
```

**Métriques**:
```
Métrique                | Attendu | Réel   | Statut
------------------------|---------|--------|--------
StatusCode              | 200     |        |
Items newsletter        | 15-20   |        |
Sections                | 4       |        |
Dates réelles (%)       | >95%    |        |
Temps exécution         | <60s    |        |
Erreurs                 | 0       |        |
```

**Checklist**:
- [ ] Lambda exécutée sans erreur
- [ ] Newsletter présente dans S3 stage
- [ ] Dates affichées correctes
- [ ] Format newsletter correct
- [ ] Sections cohérentes

#### 3.5 Comparaison Dev vs Stage (Même Run)

**Objectif**: Vérifier que stage produit résultats identiques à dev

**Télécharger données dev** (si run récent existe):
```bash
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v7/2026/01/30/items.json \
  .tmp/items_curated_v7_dev.json --profile rag-lai-prod --region eu-west-3
```

**Comparer métriques**:
```
Métrique                | Dev    | Stage  | Delta  | Acceptable
------------------------|--------|--------|--------|------------
Items ingérés           |        |        |        | ±2
Items matched           |        |        |        | ±1
Dates extraites (%)     |        |        |        | ±5%
Items newsletter        |        |        |        | ±2
Temps total             |        |        |        | ±20%
```

**Checklist**:
- [ ] Résultats cohérents dev vs stage
- [ ] Pas de régression stage
- [ ] Qualité équivalente

---

### PHASE 4: Validation Isolation (5 min)

**Objectif**: Confirmer que dev et stage sont isolés

#### 4.1 Tests Isolation

**Test 1: Modification dev n'affecte pas stage**
```bash
# Créer fichier test en dev
echo "test isolation" > test_isolation.txt
aws s3 cp test_isolation.txt s3://vectora-inbox-config-dev/test_isolation.txt \
  --profile rag-lai-prod --region eu-west-3

# Vérifier absence en stage
aws s3 ls s3://vectora-inbox-config-stage/test_isolation.txt \
  --profile rag-lai-prod --region eu-west-3
# Doit retourner: erreur (fichier n'existe pas)

# Nettoyer
aws s3 rm s3://vectora-inbox-config-dev/test_isolation.txt \
  --profile rag-lai-prod --region eu-west-3
```

**Test 2: Buckets séparés**
```bash
# Lister données dev
aws s3 ls s3://vectora-inbox-data-dev/curated/ --recursive \
  --profile rag-lai-prod --region eu-west-3 | find /c /v ""

# Lister données stage
aws s3 ls s3://vectora-inbox-data-stage/curated/ --recursive \
  --profile rag-lai-prod --region eu-west-3 | find /c /v ""
```

**Validation**:
- [ ] Fichier test dev non visible en stage
- [ ] Données dev != données stage
- [ ] Aucune référence croisée

#### 4.2 Sécurité Modification Dev

**Scénarios testés**:
```
Scénario                        | Impact Dev | Impact Stage | Risque
--------------------------------|------------|--------------|--------
Modifier config dev             | ✅         | ❌           | Aucun
Modifier canonical dev          | ✅         | ❌           | Aucun
Modifier code Lambda dev        | ✅         | ❌           | Aucun
Supprimer données dev           | ✅         | ❌           | Aucun
Casser Lambda dev               | ✅         | ❌           | Aucun
```

**Conclusion**:
- [ ] Dev modifiable sans risque pour stage
- [ ] Stage protégé des modifications dev
- [ ] Promotion contrôlée via script

---

### PHASE 5: Rapport Final (10 min)

**Objectif**: Synthèse et recommandations

#### 5.1 Synthèse Infrastructure

```
Ressource               | Dev | Stage | Parité | Qualité
------------------------|-----|-------|--------|----------
Buckets S3              | 4   | 4     | ✅     | 
Layers Lambda           | 2   | 2     | ✅     |
Lambdas                 | 3   | 3     | ✅     |
Canonical               | 37  | 37    | ✅     |
Config client           | ✅  | ✅    | ✅     |
```

**Note globale infrastructure**: _____ /10

#### 5.2 Synthèse Tests E2E Stage

```
Lambda                  | StatusCode | Temps  | Erreurs | Qualité
------------------------|------------|--------|---------|----------
ingest-v2-stage         |            |        |         |
normalize-score-v2-stage|            |        |         |
newsletter-v2-stage     |            |        |         |
```

**Note globale fonctionnement**: _____ /10

#### 5.3 Synthèse Isolation

```
Test                    | Résultat | Risque
------------------------|----------|--------
Modification dev        |          |
Buckets séparés         |          |
Promotion contrôlée     |          |
```

**Note globale isolation**: _____ /10

#### 5.4 Décision Finale

**Environnement DEV**:
- [ ] ✅ Propre et fonctionnel
- [ ] ✅ Modifiable sans risque
- [ ] ✅ Snapshot disponible

**Environnement STAGE**:
- [ ] ✅ Propre et fonctionnel
- [ ] ✅ Parité avec dev
- [ ] ✅ Moteur opérationnel
- [ ] ✅ Isolé de dev

**Qualité Promotion**:
- [ ] ✅ Excellente (9-10/10)
- [ ] ⚠️ Bonne (7-8/10)
- [ ] ❌ Insuffisante (<7/10)

**Recommandations**:
```
1. _________________________________
2. _________________________________
3. _________________________________
```

**Actions Correctives** (si nécessaire):
```
1. _________________________________
2. _________________________________
3. _________________________________
```

---

## 📊 CONCLUSION

### Questions Clés - Réponses

**1. Ai-je un environnement propre et fonctionnel en dev?**
- Réponse: _______________
- Preuve: _______________

**2. Ai-je un environnement propre et fonctionnel en stage?**
- Réponse: _______________
- Preuve: _______________

**3. Puis-je modifier dev sans risque de casser et perdre mon travail?**
- Réponse: _______________
- Preuve: _______________

**4. La promotion dev → stage est-elle de qualité?**
- Réponse: _______________
- Note: _____ /10

**5. Le moteur tourne-t-il correctement sur stage?**
- Réponse: _______________
- Preuve: _______________

### Statut Final

**GO PRODUCTION**: ✅ OUI / ❌ NON / ⚠️ AVEC RÉSERVES

**Réserves**:
- _________________________________
- _________________________________

---

**Plan de Vérification - Version 1.0**  
**Date**: 2026-01-30  
**Durée estimée**: 60 minutes  
**Statut**: PRÊT POUR EXÉCUTION
