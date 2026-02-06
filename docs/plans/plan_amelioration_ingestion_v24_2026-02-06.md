# Plan Amélioration Qualité Ingestion - lai_weekly_v24 (AJUSTÉ)

**Date**: 2026-02-06  
**Contexte**: Analyse post-test E2E lai_weekly_v24  
**Objectif**: Réduire les faux positifs en ingestion SANS modifier le moteur

**⚠️ CONTRAINTE** : Améliorer UNIQUEMENT les filtres dans les fichiers canonical existants. PAS de nouveau code, PAS de nouveaux fichiers.

---

## 📊 ANALYSE DES ITEMS NON-PERTINENTS (17/24 = 71%)

### Catégories de Bruit Identifiées

| Catégorie | Count | % | Exemples |
|-----------|-------|---|----------|
| **Conférences génériques** | 4 | 24% | BIO Convention, TIDES Asia, Bio Europe Spring, Drug Delivery 2025 |
| **Rapports financiers génériques** | 3 | 18% | Interim reports Q1/Q2/Q3, Financial calendar |
| **Corporate générique** | 3 | 18% | CEO appointment, Stock index inclusion, CEO strategy |
| **Presse hors-sujet** | 2 | 12% | Abbott CGM (non-injectable), Marketing profile |
| **Placeholder/Erreur** | 1 | 6% | "Download attachment" |
| **Items anciens** | 2 | 12% | 2023 news (GSK CEO, Novo Nordisk) |
| **Duplicate** | 1 | 6% | Nanexa semaglutide (2x) |
| **Business LAI mal scoré** | 1 | 6% | UZEDY sales (sera résolu par event type `business`) |

---

## 🎯 QUICK WINS RÉALISABLES (Sans toucher au moteur)

### ✅ Quick Win #1 : Renforcer keywords existants

**Problème** : 17/24 items non-pertinents (conférences, rapports financiers, corporate)

**Solution** : Enrichir les listes de keywords EXISTANTES dans `exclusion_scopes.yaml`

```yaml
# Dans canonical/scopes/exclusion_scopes.yaml
# ENRICHIR les scopes existants (ne PAS créer de nouveaux)

hr_content:
  # Ajouter keywords conférences
  - "BIO International Convention"
  - "Bio Europe Spring"
  - "TIDES Asia"
  - "conference announcement"
  - "save the date"
  - "register now"
  - "booth number"

financial_reporting_terms:
  # Ajouter keywords rapports financiers
  - "publishes interim report"
  - "financial calendar"
  - "publication of the"
  - "consolidated half-year"

corporate_noise_terms:
  # Ajouter keywords corporate générique
  - "chief strategy officer"
  - "chief financial officer"
  - "MSCI"
  - "stock index"
  - "index inclusion"
```

**Implémentation** :
- Enrichir UNIQUEMENT les listes existantes
- PAS de nouveaux scopes
- PAS de modification du moteur

**Impact estimé** : -30 à -40% de bruit (7-10 items filtrés sur 17)

**Risque** : Très faible - Keywords spécifiques au bruit identifié

---

### ❌ Quick Wins NON réalisables (nécessitent code moteur)

**Quick Win #2-6 ABANDONNÉS** car nécessitent modifications du moteur :
- Filtrage items anciens (>2 ans) → Nécessite code
- Déduplication par content_hash → Déjà fait par moteur existant
- Filtrage word_count → Nécessite code
- Nouveaux scopes avec patterns regex → Moteur ne les gère pas

---

## 📈 IMPACT ESTIMÉ (AJUSTÉ)

### Réduction Bruit Réaliste

| Action | Items Filtrés | % Réduction | Faisabilité |
|--------|---------------|-------------|-------------|
| Enrichir keywords existants | 7-10 | 30-40% | ✅ Immédiat |
| Autres Quick Wins | 7-10 | 30-40% | ❌ Nécessite code |
| **TOTAL RÉALISABLE** | **7-10** | **30-40%** | **Sans code** |

### Projection Nouveau Taux Pertinence

**Avant** :
- Items ingérés: 24
- Items pertinents: 7 (29%)
- Items non-pertinents: 17 (71%)

**Après enrichissement keywords** :
- Items ingérés: 14-17 (24 - 7 à 10 filtrés)
- Items pertinents: 7 (maintenu)
- Items non-pertinents: 7-10 (41-59%)

**Amélioration** : +12 à +30 points de taux pertinence (29% → 41-59%)

**Note** : Amélioration modeste mais SANS risque (pas de modification moteur)

---

## 🚀 PLAN D'IMPLÉMENTATION (AJUSTÉ)

### Phase Unique : Enrichissement Keywords

**Durée** : 30 min  
**Principe** : Enrichir UNIQUEMENT les listes de keywords existantes

#### Étape 1 : Modifications Canonical (Local)

1. **Enrichir** `canonical/scopes/exclusion_scopes.yaml`
   - [ ] Ajouter keywords conférences dans `hr_content` ou `event_generic`
   - [ ] Ajouter keywords rapports financiers dans `financial_reporting_terms`
   - [ ] Ajouter keywords corporate dans `corporate_noise_terms`

2. **NE PAS modifier** `ingestion_profiles.yaml` (déjà configuré)

3. **NE PAS créer** de nouveaux fichiers

4. **NE PAS modifier** le code moteur

#### Étape 2 : Upload S3

```bash
# Upload canonical modifié
aws s3 cp canonical/scopes/exclusion_scopes.yaml s3://vectora-inbox-config-dev/canonical/scopes/ --profile rag-lai-prod --region eu-west-3
```

#### Étape 3 : Test

```bash
# Tester avec v24
python -c "import boto3, json; client = boto3.client('lambda', region_name='eu-west-3'); response = client.invoke(FunctionName='vectora-inbox-ingest-v2-dev', InvocationType='RequestResponse', Payload=json.dumps({'client_id': 'lai_weekly_v24'})); result = json.loads(response['Payload'].read()); print('Items:', result['body']['items_final'])"
```

**Validation** :
- Items ingérés < 24 (filtrage actif)
- Items pertinents = 7 (pas de faux négatifs)
- Pas d'erreur Lambda

---

## ✅ CONFORMITÉ Q CONTEXT

- [x] **Pas de nouveau fichier** (filters.py supprimé)
- [x] **Pas de modification moteur** (__init__.py restauré)
- [x] **Uniquement canonical** (exclusion_scopes.yaml enrichi)
- [x] **Rollback validé** (v24 fonctionne)
- [x] **Snapshot préservé** (.snapshots/20260206_moteur_v24_stable/)

---

**Plan ajusté** : 2026-02-06  
**Rollback complété** : ✅  
**Approche** : Amélioration incrémentale SANS risqueash
# DELETE ancien canonical (évite conflits)
aws s3 rm s3://vectora-inbox-config-dev/canonical/scopes/exclusion_scopes.yaml --profile rag-lai-prod --region eu-west-3
aws s3 rm s3://vectora-inbox-config-dev/canonical/ingestion/ingestion_profiles.yaml --profile rag-lai-prod --region eu-west-3

# REUPLOAD nouveau canonical
aws s3 cp canonical/scopes/exclusion_scopes.yaml s3://vectora-inbox-config-dev/canonical/scopes/ --profile rag-lai-prod --region eu-west-3
aws s3 cp canonical/ingestion/ingestion_profiles.yaml s3://vectora-inbox-config-dev/canonical/ingestion/ --profile rag-lai-prod --region eu-west-3
```

#### Étape 2.3 : Build & Deploy Code

```bash
# Build layers
python scripts/build/build_all.py

# Deploy dev (remplace Lambdas)
python scripts/deploy/deploy_env.py --env dev
```

#### Étape 2.4 : Vérification S3

```bash
# Vérifier fichiers uploadés
aws s3 ls s3://vectora-inbox-config-dev/canonical/scopes/ --profile rag-lai-prod --region eu-west-3
aws s3 ls s3://vectora-inbox-config-dev/canonical/ingestion/ --profile rag-lai-prod --region eu-west-3

# Télécharger et comparer
aws s3 cp s3://vectora-inbox-config-dev/canonical/scopes/exclusion_scopes.yaml .tmp/verify_s3_exclusion_scopes.yaml --profile rag-lai-prod
diff canonical/scopes/exclusion_scopes.yaml .tmp/verify_s3_exclusion_scopes.yaml
```

---

### Phase 3 : Test E2E AWS

**Durée** : 30 min (+ 5-10 min attente normalize)

#### Étape 3.1 : Créer Client Config v25

```bash
# Copier config v24 → v25
cp client_configs/lai_weekly_v24.yaml client_configs/lai_weekly_v25.yaml

# Modifier client_id dans v25
sed -i 's/lai_weekly_v24/lai_weekly_v25/g' client_configs/lai_weekly_v25.yaml

# Upload config v25
aws s3 cp client_configs/lai_weekly_v25.yaml s3://vectora-inbox-config-dev/client_configs/ --profile rag-lai-prod --region eu-west-3
```

#### Étape 3.2 : Exécuter Workflow E2E

```bash
# Ingest
aws lambda invoke --function-name vectora-inbox-ingest-v2-dev --payload '{"client_id":"lai_weekly_v25"}' .tmp/v25_ingest_response.json --profile rag-lai-prod --region eu-west-3

# Normalize (asynchrone)
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev --invocation-type Event --payload '{"client_id":"lai_weekly_v25"}' .tmp/v25_normalize_response.json --profile rag-lai-prod --region eu-west-3

# Attendre 5-10 min puis télécharger résultats
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v25/$(date +%Y/%m/%d)/items.json .tmp/v25_curated.json --profile rag-lai-prod
```

#### Étape 3.3 : Analyse Résultats

```bash
# Métriques v25
python -c "import json; items=json.load(open('.tmp/v25_curated.json', encoding='utf-8')); print(f'Items ingérés: {len(items)}'); relevant=sum(1 for i in items if i.get('domain_scoring',{}).get('is_relevant')); print(f'Items pertinents: {relevant} ({relevant/len(items)*100:.0f}%)')"

# Comparer v24 vs v25
echo "V24: 24 items, 7 pertinents (29%)"
echo "V25: [résultats ci-dessus]"
```

**Validation** :
- [ ] Items ingérés < 24 (filtrage actif)
- [ ] Items pertinents ≥ 7 (pas de faux négatifs)
- [ ] Taux pertinence > 60% (objectif atteint)
- [ ] Conférences génériques filtrées
- [ ] Rapports financiers génériques filtrés
- [ ] Items anciens (>2 ans) filtrés
- [ ] Pas de duplicates

---

### Phase 2 : Validation et Ajustement (1 semaine)

**Durée** : 1 semaine monitoring

1. Monitorer taux pertinence sur 3-5 runs
2. Ajuster seuils si nécessaire (word_count, age_days)
3. Affiner exclusion_scopes si faux négatifs

**Métriques à suivre** :
- Taux pertinence (objectif: >60%)
- Faux négatifs (items pertinents filtrés)
- Faux positifs restants

---

### Phase 3 : Optimisations Avancées (Futur)

**Durée** : 2-4 semaines

1. **Filtrage intelligent presse sectorielle**
   - Renforcer `press_technology_focused`
   - Exiger company LAI + (technology OR trademark)

2. **Scoring pré-ingestion**
   - Calculer score de pertinence avant Bedrock
   - Filtrer items <threshold

3. **Machine Learning**
   - Entraîner modèle sur items pertinents/non-pertinents
   - Prédiction pertinence avant normalisation

---

## 🎯 RECOMMANDATIONS PRIORITAIRES

### Priorité 1 : Implémenter Immédiatement

1. ✅ **Exclusion conférences génériques** (Quick Win #1)
   - Impact: -17% bruit
   - Risque: Très faible
   - Effort: 30 min

2. ✅ **Exclusion rapports financiers** (Quick Win #2)
   - Impact: -13% bruit
   - Risque: Faible
   - Effort: 20 min

3. ✅ **Filtre items anciens** (Quick Win #4)
   - Impact: -8% bruit
   - Risque: Très faible
   - Effort: 15 min

4. ✅ **Déduplication** (Quick Win #5)
   - Impact: -4% bruit
   - Risque: Nul
   - Effort: 20 min

**Total Priorité 1** : -42% bruit, 1h30 effort

### Priorité 2 : Valider Avant Implémentation

5. ⚠️ **Exclusion corporate générique** (Quick Win #3)
   - Impact: -13% bruit
   - Risque: Moyen (pourrait filtrer "Appoints VP LAI Development")
   - Action: Implémenter avec détection trademark/technology

6. ⚠️ **Filtrage presse hors-sujet** (Quick Win #6)
   - Impact: -8% bruit
   - Risque: Moyen
   - Action: Analyser patterns avant implémentation

---

## 🔄 WORKFLOW ROLLBACK (Si Échec)

### Rollback Local

```bash
# Restaurer depuis snapshot
cp -r .snapshots/20260206_moteur_v24_stable/canonical/* canonical/
cp -r .snapshots/20260206_moteur_v24_stable/src_v2/* src_v2/
```

### Rollback S3

```bash
# Restaurer canonical depuis backup
aws s3 sync .tmp/backup_canonical_pre_v25_YYYYMMDD_HHMMSS/ s3://vectora-inbox-config-dev/canonical/ --delete --profile rag-lai-prod --region eu-west-3

# Rebuild & redeploy version stable
python scripts/build/build_all.py
python scripts/deploy/deploy_env.py --env dev
```

---

## ✅ CONFORMITÉ Q CONTEXT

### Règles Critiques Respectées

- [x] **Règle #1** : Architecture 3 Lambdas V2 (pas de modification architecture)
- [x] **Règle #2** : Code dans `src_v2/` uniquement
- [x] **Règle #3** : Snapshot local créé AVANT modification
- [x] **Règle #4** : Environnement explicite (`--env dev`)
- [x] **Règle #5** : Déploiement = Code + Data + Test (Phase 2 + 3)
- [x] **Règle #6** : Tests local possibles (validation YAML)
- [x] **Règle #7** : Client config v25 auto-généré depuis v24
- [x] **Règle #8** : Bedrock inchangé (us-east-1 + Sonnet)
- [x] **Règle #9** : Temporaires dans `.tmp/`
- [x] **Règle #10** : Blueprint à jour si nécessaire

### Workflow Gouvernance Respecté

- [x] **Étape 1** : Planification (ce document = MANIFEST)
- [x] **Étape 2** : Backup local (snapshot validé)
- [x] **Étape 3** : Modification locale (Phase 1)
- [x] **Étape 4** : Build & Deploy AWS (Phase 2)
- [x] **Étape 5** : Test E2E (Phase 3)
- [x] **Étape 6** : Rapport (à créer après test)
- [x] **Étape 7** : Décision merge/rollback (selon résultats)

### Principe DELETE + REUPLOAD

**Pourquoi** : Évite conflits entre versions de fichiers canonical sur S3

**Comment** :
1. Backup S3 actuel (sécurité)
2. DELETE fichiers modifiés sur S3
3. REUPLOAD nouveaux fichiers depuis local
4. Vérifier cohérence (diff local vs S3)

**Avantage** : Garantit que Lambda charge EXACTEMENT les fichiers locaux modifiés

---

## 📊 MÉTRIQUES SUCCÈS

### Objectifs v25

| Métrique | v24 (Baseline) | v25 (Objectif) | Amélioration |
|----------|----------------|----------------|---------------|
| Items ingérés | 24 | 10-15 | -40 à -60% |
| Items pertinents | 7 (29%) | 7-10 (>60%) | +31 pts |
| Conférences génériques | 4 | 0 | -100% |
| Rapports financiers | 3 | 0 | -100% |
| Items anciens (>2 ans) | 2 | 0 | -100% |
| Duplicates | 1 | 0 | -100% |
| Faux négatifs | 0 | 0 | Maintenu |

### Critères Validation

**✅ SUCCÈS** si :
- Items pertinents ≥ 7 (pas de perte)
- Taux pertinence ≥ 60% (+31 pts vs v24)
- Conférences génériques = 0
- Items anciens = 0
- Duplicates = 0

**⚠️ ATTENTION** si :
- Items pertinents = 6 (1 faux négatif)
- Taux pertinence 50-60%

**❌ ÉCHEC** si :
- Items pertinents < 6 (>1 faux négatif)
- Taux pertinence < 50%
- Rollback immédiat

---

## 📝 FICHIERS IMPACTÉS

### Canonical (Modifications)

- `canonical/scopes/exclusion_scopes.yaml` (ajout 3 scopes)
- `canonical/ingestion/ingestion_profiles.yaml` (ajout filtres runtime)

### Code (Modifications)

- `src_v2/vectora_core/ingestion/deduplication.py` (nouveau)
- `src_v2/vectora_core/ingestion/filters.py` (ajout filtres date/word_count)
- `src_v2/lambdas/ingest_v2/handler.py` (intégration filtres)

### Config Client (Nouveau)

- `client_configs/lai_weekly_v25.yaml` (copie v24)

### S3 (Remplacement)

- `s3://vectora-inbox-config-dev/canonical/scopes/exclusion_scopes.yaml`
- `s3://vectora-inbox-config-dev/canonical/ingestion/ingestion_profiles.yaml`
- `s3://vectora-inbox-config-dev/client_configs/lai_weekly_v25.yaml`

---

**Plan validé** : 2026-02-06  
**Snapshot local** : `.snapshots/20260206_moteur_v24_stable/`  
**Prêt pour implémentation** : ✅ltrer appointments LAI-relevant)
   - Effort: 30 min
   - **Action** : Tester sur plus de données avant activation

### Priorité 3 : Futur

6. 🔮 **Filtrage intelligent presse** (Phase 3)
7. 🔮 **Scoring pré-ingestion** (Phase 3)

---

## 📝 FICHIERS À MODIFIER

### 1. `canonical/scopes/exclusion_scopes.yaml`
- Ajouter: conference_generic_announcements
- Ajouter: financial_reporting_generic
- Ajouter: corporate_generic_announcements

### 2. `canonical/ingestion/ingestion_profiles.yaml`
- Référencer nouveaux exclusion_scopes
- Ajouter: max_age_days: 730
- Ajouter: minimum_word_count: 10

### 3. `src_v2/vectora_core/ingestion/deduplication.py` (NOUVEAU)
- Créer fonction deduplicate_items()

### 4. `src_v2/lambda_handlers/ingest_v2_handler.py`
- Appeler deduplicate_items() après scraping

---

## ✅ CRITÈRES DE SUCCÈS

**Objectifs Quantitatifs** :
- Taux pertinence: >60% (vs 29% actuellement)
- Réduction bruit: >50%
- Faux négatifs: <5%

**Objectifs Qualitatifs** :
- Aucun item pertinent filtré
- Conférences génériques éliminées
- Rapports financiers génériques éliminés
- Items anciens (>2 ans) éliminés

---

**Statut** : 📋 Plan prêt pour implémentation
**Effort estimé** : 1h30 (Priorité 1) + 1 semaine validation
**Impact attendu** : Taux pertinence 29% → 70%
