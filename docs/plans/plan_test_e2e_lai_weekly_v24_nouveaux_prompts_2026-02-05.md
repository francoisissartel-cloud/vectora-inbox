# Plan Test E2E - lai_weekly_v24 - Nouveaux Prompts Normalization & Domain Scoring

**Date**: 2026-02-05  
**Objectif**: Tester E2E complet avec les nouveaux prompts améliorés (normalization v2.0 + domain scoring v5.0)  
**Client**: lai_weekly_v24 (nouveau, copie de v23)  
**Environnement**: dev

---

## 🎯 OBJECTIFS

1. **Valider les nouveaux prompts**:
   - `generic_normalization.yaml` v2.0 (summary 10-15 lignes + routes d'administration)
   - `lai_domain_scoring.yaml` v5.0 (définition LAI riche + évaluation naturelle)

2. **Tester avec données fraîches**: Ingestion de nouvelles news (30 derniers jours)

3. **Générer rapport E2E complet**: Format `test-e2e-gold-standard.md`

4. **Garantir utilisation des nouveaux prompts**: Nettoyage S3 avant déploiement

---

## 📋 PLAN D'EXÉCUTION

### PHASE 0: Préparation Client v24

**Objectif**: Créer lai_weekly_v24 comme copie exacte de v23

**Actions**:
```bash
# 1. Copier config v23 → v24
cp client-config-examples/production/lai_weekly_v23.yaml \
   client-config-examples/production/lai_weekly_v24.yaml

# 2. Éditer lai_weekly_v24.yaml
# - Remplacer "v23" par "v24" partout
# - Mettre à jour metadata.created_date: "2026-02-05"
# - Mettre à jour metadata.created_by: "Test E2E V24 - Nouveaux prompts normalization + domain scoring"
# - Mettre à jour metadata.creation_notes avec description des nouveaux prompts
```

**Validation**:
- [ ] Fichier `lai_weekly_v24.yaml` créé
- [ ] Tous les champs mis à jour (client_id, name, metadata)
- [ ] Config identique à v23 sauf version

**Durée estimée**: 5 min

---

### PHASE 1: Nettoyage S3 Prompts

**Objectif**: Supprimer les anciens prompts sur S3 pour forcer l'utilisation des nouveaux

**Actions**:
```bash
# 1. Lister les prompts actuels sur S3
aws s3 ls s3://rag-lai-canonical-dev/prompts/normalization/ --profile rag-lai-prod
aws s3 ls s3://rag-lai-canonical-dev/prompts/domain_scoring/ --profile rag-lai-prod

# 2. Supprimer les anciens prompts
aws s3 rm s3://rag-lai-canonical-dev/prompts/normalization/generic_normalization.yaml --profile rag-lai-prod
aws s3 rm s3://rag-lai-canonical-dev/prompts/domain_scoring/lai_domain_scoring.yaml --profile rag-lai-prod

# 3. Vérifier suppression
aws s3 ls s3://rag-lai-canonical-dev/prompts/normalization/ --profile rag-lai-prod
aws s3 ls s3://rag-lai-canonical-dev/prompts/domain_scoring/ --profile rag-lai-prod
```

**Validation**:
- [ ] Anciens prompts supprimés de S3
- [ ] Buckets prompts vides ou ne contenant que d'autres fichiers

**Durée estimée**: 5 min

---

### PHASE 2: Upload Nouveaux Prompts

**Objectif**: Uploader les nouveaux prompts sur S3 dev

**Actions**:
```bash
# 1. Upload nouveau prompt normalization
aws s3 cp canonical/prompts/normalization/generic_normalization.yaml \
  s3://rag-lai-canonical-dev/prompts/normalization/generic_normalization.yaml \
  --profile rag-lai-prod

# 2. Upload nouveau prompt domain scoring
aws s3 cp canonical/prompts/domain_scoring/lai_domain_scoring.yaml \
  s3://rag-lai-canonical-dev/prompts/domain_scoring/lai_domain_scoring.yaml \
  --profile rag-lai-prod

# 3. Vérifier upload
aws s3 ls s3://rag-lai-canonical-dev/prompts/normalization/ --profile rag-lai-prod
aws s3 ls s3://rag-lai-canonical-dev/prompts/domain_scoring/ --profile rag-lai-prod

# 4. Télécharger et vérifier contenu
aws s3 cp s3://rag-lai-canonical-dev/prompts/normalization/generic_normalization.yaml \
  .tmp/verify_normalization.yaml --profile rag-lai-prod
aws s3 cp s3://rag-lai-canonical-dev/prompts/domain_scoring/lai_domain_scoring.yaml \
  .tmp/verify_domain_scoring.yaml --profile rag-lai-prod

# 5. Comparer avec fichiers locaux
diff canonical/prompts/normalization/generic_normalization.yaml .tmp/verify_normalization.yaml
diff canonical/prompts/domain_scoring/lai_domain_scoring.yaml .tmp/verify_domain_scoring.yaml
```

**Validation**:
- [ ] Nouveaux prompts uploadés sur S3
- [ ] Contenu vérifié (diff = 0 différences)
- [ ] Versions correctes (v2.0 normalization, v5.0 domain scoring)

**Durée estimée**: 10 min

---

### PHASE 3: Upload Config Client v24

**Objectif**: Uploader la config lai_weekly_v24 sur S3 dev

**Actions**:
```bash
# 1. Upload config client
aws s3 cp client-config-examples/production/lai_weekly_v24.yaml \
  s3://rag-lai-canonical-dev/clients/lai_weekly_v24.yaml \
  --profile rag-lai-prod

# 2. Vérifier upload
aws s3 ls s3://rag-lai-canonical-dev/clients/ --profile rag-lai-prod | grep v24

# 3. Télécharger et vérifier
aws s3 cp s3://rag-lai-canonical-dev/clients/lai_weekly_v24.yaml \
  .tmp/verify_client_v24.yaml --profile rag-lai-prod

diff client-config-examples/production/lai_weekly_v24.yaml .tmp/verify_client_v24.yaml
```

**Validation**:
- [ ] Config lai_weekly_v24.yaml uploadée sur S3
- [ ] Contenu vérifié (diff = 0)

**Durée estimée**: 5 min

---

### PHASE 4: Lancement Run E2E

**Objectif**: Lancer le workflow complet ingest → normalize-score → newsletter

**Actions**:
```bash
# 1. Lancer ingest-v2 (données fraîches 30 derniers jours)
python scripts/invoke/invoke_ingest_v2.py \
  --client-id lai_weekly_v24 \
  --env dev \
  --period-days 30

# 2. Attendre fin ingest (vérifier CloudWatch logs)
# Lambda: rag-lai-ingest-v2-dev
# Chercher: "Ingest completed" ou "ERROR"

# 3. Lancer normalize-score-v2
python scripts/invoke/invoke_normalize_score_v2.py \
  --client-id lai_weekly_v24 \
  --env dev

# 4. Attendre fin normalize-score (vérifier CloudWatch logs)
# Lambda: rag-lai-normalize-score-v2-dev
# Chercher: "Normalize-score completed" ou "ERROR"

# 5. Lancer newsletter-v2
python scripts/invoke/invoke_newsletter_v2.py \
  --client-id lai_weekly_v24 \
  --env dev

# 6. Attendre fin newsletter (vérifier CloudWatch logs)
# Lambda: rag-lai-newsletter-v2-dev
# Chercher: "Newsletter completed" ou "ERROR"
```

**Validation**:
- [ ] Ingest-v2 terminé avec succès
- [ ] Normalize-score-v2 terminé avec succès
- [ ] Newsletter-v2 terminé avec succès
- [ ] Aucune erreur dans CloudWatch logs

**Durée estimée**: 10-15 min (selon volume items)

---

### PHASE 5: Récupération Données S3

**Objectif**: Télécharger les résultats du run pour analyse

**Actions**:
```bash
# 1. Créer dossier local pour v24
mkdir -p .tmp/e2e/lai_weekly_v24

# 2. Télécharger items ingérés
aws s3 cp s3://rag-lai-data-dev/clients/lai_weekly_v24/ingested/ \
  .tmp/e2e/lai_weekly_v24/ingested/ --recursive --profile rag-lai-prod

# 3. Télécharger items normalisés
aws s3 cp s3://rag-lai-data-dev/clients/lai_weekly_v24/normalized/ \
  .tmp/e2e/lai_weekly_v24/normalized/ --recursive --profile rag-lai-prod

# 4. Télécharger items curated
aws s3 cp s3://rag-lai-data-dev/clients/lai_weekly_v24/curated/ \
  .tmp/e2e/lai_weekly_v24/curated/ --recursive --profile rag-lai-prod

# 5. Télécharger newsletter
aws s3 cp s3://rag-lai-data-dev/clients/lai_weekly_v24/newsletters/ \
  .tmp/e2e/lai_weekly_v24/newsletters/ --recursive --profile rag-lai-prod

# 6. Identifier le dernier run (timestamp le plus récent)
ls -lt .tmp/e2e/lai_weekly_v24/curated/
```

**Validation**:
- [ ] Fichiers ingested téléchargés
- [ ] Fichiers normalized téléchargés
- [ ] Fichiers curated téléchargés
- [ ] Newsletter téléchargée
- [ ] Dernier run identifié

**Durée estimée**: 5 min

---

### PHASE 6: Génération Rapport E2E

**Objectif**: Générer rapport complet format `test-e2e-gold-standard.md`

**Actions**:
```bash
# 1. Identifier fichier curated du dernier run
CURATED_FILE=".tmp/e2e/lai_weekly_v24/curated/curated_items_YYYYMMDD_HHMMSS.json"

# 2. Générer rapport E2E avec Q Developer
# Prompt:
# "Génère un rapport E2E complet pour lai_weekly_v24 en utilisant le format exact 
# de test-e2e-gold-standard.md. Données source: $CURATED_FILE
# 
# Le rapport doit inclure:
# - Métriques de performance (temps, throughput)
# - Métriques Bedrock (appels, tokens, coûts)
# - Volumétrie détaillée
# - Projections coûts
# - KPIs pilotage
# - Détail de tous les items pertinents (avec summary complet, routes d'administration)
# - Résumé des items non-pertinents
# - Analyse par catégorie
# 
# Utilise les mêmes sections, emojis, et structure que le golden standard."

# 3. Sauvegarder rapport
# Fichier: docs/reports/e2e/test_e2e_lai_weekly_v24_rapport_detaille_2026-02-05.md
```

**Validation**:
- [ ] Rapport généré avec toutes les sections
- [ ] Format identique à test-e2e-gold-standard.md
- [ ] Métriques calculées (performance, Bedrock, coûts)
- [ ] Tous les items pertinents détaillés
- [ ] Items non-pertinents résumés
- [ ] Analyse par catégorie présente

**Durée estimée**: 20-30 min

---

### PHASE 7: Analyse Qualitative

**Objectif**: Valider la qualité des nouveaux prompts

**Critères d'évaluation**:

1. **Summary (normalization)**:
   - [ ] Longueur: 10-15 lignes minimum
   - [ ] Contenu: Détaillé, capture toutes les infos clés
   - [ ] Structure: Companies + Action + Technical details + Context
   - [ ] Routes d'administration: Extraites quand présentes

2. **Domain Scoring**:
   - [ ] Taux pertinence: 50-70% attendu
   - [ ] Score moyen: 65-75 attendu
   - [ ] Reasoning: Clair, mentionne indicateurs LAI
   - [ ] Pas d'hallucination: Pas de catégories inventées
   - [ ] Trademarks LAI: Reconnus même sans autres mots-clés

3. **Comparaison v23 vs v24**:
   - [ ] Summary plus riches en v24
   - [ ] Routes d'administration présentes en v24
   - [ ] Scoring plus cohérent en v24
   - [ ] Moins d'hallucinations en v24

**Actions**:
```bash
# 1. Comparer quelques items v23 vs v24
# Sélectionner 5-10 items communs et comparer:
# - Longueur summary
# - Richesse informations
# - Présence routes d'administration
# - Cohérence scoring

# 2. Vérifier cas edge:
# - "UZEDY strong sales" → Doit être détecté (trademark seul)
# - News avec dosing + route mais pas de trademark → Doit scorer correctement
# - News avec technologies DDS/HLE → Doit être pertinent

# 3. Documenter observations dans rapport
```

**Validation**:
- [ ] Summary significativement plus riches
- [ ] Routes d'administration extraites
- [ ] Scoring cohérent et sans hallucination
- [ ] Cas edge validés

**Durée estimée**: 30 min

---

## 📊 LIVRABLES ATTENDUS

1. **Config client**: `client-config-examples/production/lai_weekly_v24.yaml`
2. **Rapport E2E**: `docs/reports/e2e/test_e2e_lai_weekly_v24_rapport_detaille_2026-02-05.md`
3. **Données run**: `.tmp/e2e/lai_weekly_v24/` (ingested, normalized, curated, newsletter)
4. **Analyse comparative**: Section dans rapport E2E comparant v23 vs v24

---

## ✅ CRITÈRES DE SUCCÈS

### Critères techniques
- [ ] Run E2E complet sans erreur
- [ ] Nouveaux prompts utilisés (vérifié via S3)
- [ ] Données fraîches ingérées (30 derniers jours)

### Critères qualité
- [ ] Summary 10-15 lignes minimum (vs 2-3 en v23)
- [ ] Routes d'administration extraites
- [ ] Taux pertinence 50-70%
- [ ] Score moyen 65-75
- [ ] Reasoning clair sans hallucination
- [ ] Trademarks LAI reconnus seuls

### Critères documentation
- [ ] Rapport E2E complet format gold standard
- [ ] Analyse comparative v23 vs v24
- [ ] Recommandations pour amélioration continue

---

## 🚨 POINTS D'ATTENTION

1. **Nettoyage S3**: CRITIQUE - Sans ça, anciens prompts seront utilisés
2. **Vérification upload**: Toujours diff local vs S3 pour confirmer
3. **CloudWatch logs**: Surveiller pour détecter erreurs rapidement
4. **Volume items**: Si >50 items, temps normalize-score peut être long (3-5 min/item)
5. **Coûts Bedrock**: Avec summary plus longs, tokens output augmentent (~30-40%)

---

## 📅 TIMELINE ESTIMÉE

| Phase | Durée | Cumul |
|-------|-------|-------|
| Phase 0: Préparation v24 | 5 min | 5 min |
| Phase 1: Nettoyage S3 | 5 min | 10 min |
| Phase 2: Upload prompts | 10 min | 20 min |
| Phase 3: Upload config | 5 min | 25 min |
| Phase 4: Run E2E | 15 min | 40 min |
| Phase 5: Récupération S3 | 5 min | 45 min |
| Phase 6: Génération rapport | 30 min | 75 min |
| Phase 7: Analyse qualitative | 30 min | 105 min |

**Total estimé**: ~2 heures

---

## 🔄 PROCHAINES ÉTAPES (POST-TEST)

Si test v24 réussi:
1. Promouvoir prompts vers stage
2. Tester sur stage avec lai_weekly_v24
3. Valider avec données production
4. Déployer en prod si validé

Si test v24 échoue:
1. Analyser logs CloudWatch
2. Identifier problème (prompt, config, Lambda)
3. Corriger et relancer
4. Documenter learnings

---

**Prêt pour exécution** ✅
