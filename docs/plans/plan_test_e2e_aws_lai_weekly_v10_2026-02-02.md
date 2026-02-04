# Plan Test E2E AWS - LAI Weekly v10

**Date**: 2026-02-02  
**Objectif**: Test E2E complet sur AWS Dev avec nouveau client lai_weekly_v10  
**Base**: Copie identique de lai_weekly_v9 (architecture v2 validée)  
**Environnement**: AWS Dev  

---

## 🎯 Objectif

Tester le pipeline complet sur AWS Dev avec données fraîches :
- ✅ Ingest : Récupération sources réelles (7 derniers jours)
- ✅ Normalize & Score : Architecture v2 (2 appels Bedrock)
- ✅ Newsletter : Génération complète avec sections
- ✅ Métriques détaillées à chaque étape

---

## 📋 Phase 1: Création Client Config lai_weekly_v10

### 1.1 Copier lai_weekly_v9 → lai_weekly_v10

**Fichier source**: `client-config-examples/production/lai_weekly_dev.yaml` (lai_weekly_v9)  
**Fichier cible**: `client-config-examples/production/lai_weekly_v10.yaml`

**Modifications à faire**:
```yaml
client_profile:
  name: "LAI Intelligence Weekly v10 (Test E2E 2026-02-02)"
  client_id: "lai_weekly_v10"  # ← CHANGEMENT PRINCIPAL

metadata:
  template_version: "10.0.0"
  created_date: "2026-02-02"
  last_modified: "2026-02-02"
  created_by: "Test E2E AWS - Validation architecture v2"
  
  creation_notes: |
    Création lai_weekly_v10.yaml depuis lai_weekly_v9.yaml
    
    OBJECTIF v10 (Test E2E AWS):
    🎯 Valider pipeline complet sur AWS Dev
    🎯 Données fraîches (nouveau client_id)
    🎯 Métriques détaillées à chaque étape
    🎯 Architecture v2 (enable_domain_scoring: true)
    
    MODIFICATIONS v9 → v10:
    ✅ client_id: "lai_weekly_v9" → "lai_weekly_v10"
    ✅ client_profile.name: "v9 (Phase 8)" → "v10 (Test E2E 2026-02-02)"
    ✅ notification_email: "lai-weekly-v10@vectora.com"
    ✅ template_version: "9.0.0" → "10.0.0"
    ✅ created_date: "2026-02-02"
    
    CONFIG IDENTIQUE À v9:
    ✅ bedrock_config.enable_domain_scoring: true
    ✅ pipeline.default_period_days: 30
    ✅ newsletter_selection.max_items_total: 20
    ✅ Tous les autres paramètres identiques
    
    PRÊT POUR TEST E2E AWS DEV
```

**Commande**:
```bash
# Copier et modifier
cp client-config-examples/production/lai_weekly_dev.yaml \
   client-config-examples/production/lai_weekly_v10.yaml

# Éditer lai_weekly_v10.yaml avec modifications ci-dessus
```

### 1.2 Valider Config Localement

**Checklist validation**:
- [ ] `client_id: "lai_weekly_v10"`
- [ ] `enable_domain_scoring: true`
- [ ] `default_period_days: 30`
- [ ] `max_items_total: 20`
- [ ] Metadata à jour
- [ ] YAML valide (pas d'erreur syntaxe)

**Commande validation**:
```bash
# Vérifier syntaxe YAML
python -c "import yaml; yaml.safe_load(open('client-config-examples/production/lai_weekly_v10.yaml'))"
```

---

## 📋 Phase 2: Déploiement Config sur AWS

### 2.1 Upload Config S3

**Bucket**: `s3://rag-lai-prod-client-configs/dev/`  
**Fichier**: `lai_weekly_v10.yaml`

**Commande**:
```bash
aws s3 cp \
  client-config-examples/production/lai_weekly_v10.yaml \
  s3://rag-lai-prod-client-configs/dev/lai_weekly_v10.yaml \
  --profile rag-lai-prod
```

**Vérification**:
```bash
# Vérifier upload
aws s3 ls s3://rag-lai-prod-client-configs/dev/ \
  --profile rag-lai-prod | grep lai_weekly_v10

# Télécharger et comparer
aws s3 cp \
  s3://rag-lai-prod-client-configs/dev/lai_weekly_v10.yaml \
  .tmp/lai_weekly_v10_s3.yaml \
  --profile rag-lai-prod

diff client-config-examples/production/lai_weekly_v10.yaml .tmp/lai_weekly_v10_s3.yaml
```

### 2.2 Vérifier Lambdas Déployées

**Lambdas requises**:
- `rag-lai-ingest-v2-dev`
- `rag-lai-normalize-score-v2-dev`
- `rag-lai-newsletter-v2-dev`

**Versions attendues** (depuis VERSION):
```
VECTORA_CORE_VERSION=1.4.1
NORMALIZE_VERSION=2.1.0
NEWSLETTER_VERSION=1.8.0
CANONICAL_VERSION=2.0
```

**Commande vérification**:
```bash
# Vérifier versions layers
aws lambda get-function --function-name rag-lai-normalize-score-v2-dev \
  --profile rag-lai-prod \
  --query 'Configuration.Layers[*].Arn'
```

---

## 📋 Phase 3: Test E2E - Étape 1 : Ingest

### 3.1 Exécuter Ingest

**Commande**:
```bash
python scripts/invoke/invoke_ingest_v2.py \
  --client-id lai_weekly_v10 \
  --env dev
```

**Paramètres effectifs**:
- `default_period_days: 30` → Récupère items des 30 derniers jours
- Sources : `lai_corporate_mvp` + `lai_press_mvp`
- Filtres : `min_word_count: 50`

**Durée attendue**: 30-90 secondes

### 3.2 Vérifier Outputs Ingest

**Bucket**: `s3://rag-lai-prod-ingested-items/dev/lai_weekly_v10/`

**Commandes**:
```bash
# Lister runs
aws s3 ls s3://rag-lai-prod-ingested-items/dev/lai_weekly_v10/ \
  --profile rag-lai-prod

# Identifier dernier run
LAST_RUN=$(aws s3 ls s3://rag-lai-prod-ingested-items/dev/lai_weekly_v10/ \
  --profile rag-lai-prod | tail -1 | awk '{print $2}')

echo "Dernier run: $LAST_RUN"

# Télécharger items ingérés
aws s3 cp \
  s3://rag-lai-prod-ingested-items/dev/lai_weekly_v10/${LAST_RUN}items.json \
  .tmp/ingest_items.json \
  --profile rag-lai-prod
```

**Métriques à collecter**:
```bash
# Nombre items ingérés
jq 'length' .tmp/ingest_items.json

# Répartition par source
jq 'group_by(.source_key) | map({source: .[0].source_key, count: length})' .tmp/ingest_items.json

# Période couverte
jq '[.[].ingestion_date] | min, max' .tmp/ingest_items.json
```

**Critères succès**:
- [ ] Items ingérés > 20
- [ ] Sources multiples présentes
- [ ] Pas d'erreur dans logs CloudWatch
- [ ] Fichier `items.json` valide

---

## 📋 Phase 4: Test E2E - Étape 2 : Normalize & Score

### 4.1 Exécuter Normalize & Score

**Commande**:
```bash
python scripts/invoke/invoke_normalize_score_v2.py \
  --client-id lai_weekly_v10 \
  --env dev
```

**Architecture v2 activée**:
- Appel 1 : `generic_normalization` (extraction entités)
- Appel 2 : `lai_domain_scoring` (scoring domaine)

**Durée attendue**: 5-15 minutes (selon nombre items)

### 4.2 Vérifier Outputs Normalize

**Bucket**: `s3://rag-lai-prod-normalized-items/dev/lai_weekly_v10/`

**Commandes**:
```bash
# Lister runs
aws s3 ls s3://rag-lai-prod-normalized-items/dev/lai_weekly_v10/ \
  --profile rag-lai-prod

# Identifier dernier run
LAST_RUN=$(aws s3 ls s3://rag-lai-prod-normalized-items/dev/lai_weekly_v10/ \
  --profile rag-lai-prod | tail -1 | awk '{print $2}')

# Télécharger items normalisés
aws s3 cp \
  s3://rag-lai-prod-normalized-items/dev/lai_weekly_v10/${LAST_RUN}items.json \
  .tmp/normalized_items.json \
  --profile rag-lai-prod
```

**Métriques à collecter**:
```bash
# Nombre items normalisés
jq 'length' .tmp/normalized_items.json

# Items avec domain_scoring
jq '[.[] | select(.has_domain_scoring == true)] | length' .tmp/normalized_items.json

# Taux relevance
jq '[.[] | select(.domain_scoring.is_relevant == true)] | length' .tmp/normalized_items.json

# Distribution scores
jq '[.[] | .domain_scoring.score] | add / length' .tmp/normalized_items.json

# Distribution confidence
jq 'group_by(.domain_scoring.confidence) | map({confidence: .[0].domain_scoring.confidence, count: length})' .tmp/normalized_items.json

# Distribution event_type
jq 'group_by(.normalized_content.event_classification.primary_type) | map({type: .[0].normalized_content.event_classification.primary_type, count: length})' .tmp/normalized_items.json
```

**Critères succès**:
- [ ] 100% items avec `has_domain_scoring: true`
- [ ] Section `domain_scoring` présente dans tous les items
- [ ] Champs requis : `is_relevant`, `score`, `confidence`, `reasoning`
- [ ] Taux relevance > 50%
- [ ] Score moyen cohérent (30-70)
- [ ] Pas d'erreur dans logs CloudWatch

### 4.3 Vérifier Logs CloudWatch

**Log Group**: `/aws/lambda/rag-lai-normalize-score-v2-dev`

**Commandes**:
```bash
# Télécharger logs dernière exécution
python scripts/utils/download_logs.py \
  --lambda normalize-score-v2 \
  --env dev \
  --hours 1 \
  --output .tmp/normalize_logs.txt
```

**Vérifications**:
- [ ] 2 appels Bedrock par item (normalization + domain_scoring)
- [ ] Pas d'erreur "Prompt not found"
- [ ] Pas d'erreur "Scope not found"
- [ ] Temps exécution cohérent (~5-10s par item)

---

## 📋 Phase 5: Test E2E - Étape 3 : Newsletter

### 5.1 Exécuter Newsletter

**Commande**:
```bash
python scripts/invoke/invoke_newsletter_v2.py \
  --client-id lai_weekly_v10 \
  --env dev
```

**Paramètres effectifs**:
- `max_items_total: 20`
- `distribution_strategy: specialized_with_fallback`
- Sections : regulatory_updates, partnerships_deals, clinical_updates, others
- `include_tldr: true`
- `include_intro: true`

**Durée attendue**: 30-60 secondes

### 5.2 Vérifier Outputs Newsletter

**Bucket**: `s3://rag-lai-prod-newsletters/dev/lai_weekly_v10/`

**Commandes**:
```bash
# Lister runs
aws s3 ls s3://rag-lai-prod-newsletters/dev/lai_weekly_v10/ \
  --profile rag-lai-prod

# Identifier dernier run
LAST_RUN=$(aws s3 ls s3://rag-lai-prod-newsletters/dev/lai_weekly_v10/ \
  --profile rag-lai-prod | tail -1 | awk '{print $2}')

# Télécharger newsletter
aws s3 cp \
  s3://rag-lai-prod-newsletters/dev/lai_weekly_v10/${LAST_RUN}newsletter.md \
  .tmp/newsletter_v10.md \
  --profile rag-lai-prod

# Télécharger metadata
aws s3 cp \
  s3://rag-lai-prod-newsletters/dev/lai_weekly_v10/${LAST_RUN}metadata.json \
  .tmp/newsletter_metadata.json \
  --profile rag-lai-prod
```

**Métriques à collecter**:
```bash
# Nombre total items dans newsletter
grep -c "^## " .tmp/newsletter_v10.md

# Items par section
grep "^### " .tmp/newsletter_v10.md

# Présence TLDR
grep -c "TL;DR" .tmp/newsletter_v10.md

# Présence intro
grep -c "This week" .tmp/newsletter_v10.md

# Metadata
jq '.' .tmp/newsletter_metadata.json
```

**Critères succès**:
- [ ] Newsletter générée (fichier .md existe)
- [ ] TLDR présent
- [ ] Intro présente
- [ ] 4 sections présentes (regulatory, partnerships, clinical, others)
- [ ] Items répartis dans sections
- [ ] Pas de placeholder non remplacé
- [ ] Markdown valide
- [ ] Metadata complètes

---

## 📋 Phase 6: Analyse Résultats E2E

### 6.1 Métriques Globales

**Tableau récapitulatif**:

| Étape | Métrique | Valeur | Cible | Statut |
|-------|----------|--------|-------|--------|
| **Ingest** | Items ingérés | ? | > 20 | ? |
| | Sources actives | ? | 2 | ? |
| | Durée (s) | ? | < 120 | ? |
| **Normalize** | Items normalisés | ? | 100% | ? |
| | Items avec domain_scoring | ? | 100% | ? |
| | Taux relevance | ? | > 50% | ? |
| | Score moyen | ? | 30-70 | ? |
| | Durée (min) | ? | < 15 | ? |
| **Newsletter** | Items sélectionnés | ? | 10-20 | ? |
| | Sections remplies | ? | 4 | ? |
| | TLDR présent | ? | Oui | ? |
| | Durée (s) | ? | < 120 | ? |
| **Global** | Durée totale (min) | ? | < 20 | ? |
| | Coût Bedrock ($) | ? | < 1.00 | ? |

### 6.2 Comparaison avec lai_weekly_v9

**Si v9 a été testé précédemment**, comparer :
- Nombre items ingérés
- Taux matching
- Distribution scores
- Qualité newsletter

### 6.3 Validation Qualité

**Checklist qualité newsletter**:
- [ ] Items pertinents pour LAI
- [ ] Résumés clairs et concis
- [ ] Event types cohérents
- [ ] Pas de doublons
- [ ] Sections équilibrées
- [ ] Pas d'erreur factuelle visible

---

## 📋 Phase 7: Génération Rapport

### 7.1 Créer Rapport Détaillé

**Fichier**: `docs/reports/test_e2e_aws_lai_weekly_v10_2026-02-02.md`

**Structure**:
```markdown
# Rapport Test E2E AWS - LAI Weekly v10

## Contexte
- Date: 2026-02-02
- Client: lai_weekly_v10
- Environnement: AWS Dev
- Base: Copie lai_weekly_v9

## Configuration
- Architecture: v2 (2 appels Bedrock)
- Period: 30 jours
- Max items: 20
- Domain scoring: Activé

## Résultats

### Ingest
- Items ingérés: X
- Sources: Y
- Durée: Z secondes

### Normalize & Score
- Items normalisés: X
- Taux domain_scoring: 100%
- Taux relevance: X%
- Score moyen: X/100
- Durée: Y minutes

### Newsletter
- Items sélectionnés: X
- Sections: 4/4
- TLDR: Oui
- Durée: Y secondes

## Métriques Détaillées
[Tableaux et graphiques]

## Problèmes Détectés
[Liste des problèmes]

## Recommandations
[Actions à prendre]

## Conclusion
[Succès / Échec / Partiel]
```

### 7.2 Sauvegarder Artifacts

**Dossier**: `.tmp/test_e2e_v10_2026-02-02/`

**Fichiers à sauvegarder**:
```
.tmp/test_e2e_v10_2026-02-02/
├── ingest_items.json
├── normalized_items.json
├── newsletter_v10.md
├── newsletter_metadata.json
├── normalize_logs.txt
├── metrics.json
└── report.md
```

---

## 📋 Phase 8: Décision Suite

### Si Test Réussi ✅

**Options**:

1. **Garder lai_weekly_v10 comme référence**
   - Config validée
   - Données fraîches
   - Prêt pour utilisation régulière

2. **Promouvoir vers Stage**
   ```bash
   # Upload config stage
   aws s3 cp \
     client-config-examples/production/lai_weekly_v10.yaml \
     s3://rag-lai-prod-client-configs/stage/lai_weekly_v10.yaml \
     --profile rag-lai-prod
   
   # Tester sur stage
   python scripts/invoke/invoke_normalize_score_v2.py \
     --client-id lai_weekly_v10 \
     --env stage
   ```

3. **Créer lai_weekly_v11 pour prochains tests**

### Si Test Échoué ❌

**Actions**:

1. **Analyser logs CloudWatch**
   ```bash
   python scripts/utils/download_logs.py \
     --lambda normalize-score-v2 \
     --env dev \
     --hours 2
   ```

2. **Identifier cause**
   - Erreur config ?
   - Erreur Bedrock ?
   - Erreur matching ?
   - Erreur scoring ?

3. **Corriger et retester**
   - Modifier config si nécessaire
   - Re-upload S3
   - Relancer pipeline

4. **Créer lai_weekly_v11 après correction**

---

## 🚨 Règles Critiques

### RÈGLE 1: Nouveau Client = Données Fraîches

✅ **CORRECT**:
```
lai_weekly_v10 → Nouveau client_id → Nouveaux dossiers S3 → Données fraîches
```

❌ **INTERDIT**:
```
Réutiliser lai_weekly_v9 → Données existantes → Pas de test E2E valide
```

### RÈGLE 2: Tester Chaque Étape

✅ **CORRECT**:
```
1. Ingest → Vérifier outputs
2. Normalize → Vérifier outputs
3. Newsletter → Vérifier outputs
```

❌ **INTERDIT**:
```
Lancer tout d'un coup sans vérifier les étapes intermédiaires
```

### RÈGLE 3: Sauvegarder Artifacts

✅ **CORRECT**:
```
Télécharger tous les outputs S3 dans .tmp/ pour analyse
```

❌ **INTERDIT**:
```
Analyser uniquement dans S3 sans sauvegarder localement
```

---

## ✅ Checklist Complète

### Préparation
- [ ] Lire plan complet
- [ ] Vérifier AWS CLI configuré
- [ ] Vérifier Lambdas déployées en dev

### Phase 1: Config
- [ ] Copier lai_weekly_v9 → lai_weekly_v10
- [ ] Modifier client_id et metadata
- [ ] Valider YAML localement

### Phase 2: Déploiement
- [ ] Upload config S3
- [ ] Vérifier upload réussi
- [ ] Vérifier Lambdas opérationnelles

### Phase 3: Ingest
- [ ] Exécuter ingest
- [ ] Télécharger outputs
- [ ] Collecter métriques
- [ ] Valider succès

### Phase 4: Normalize
- [ ] Exécuter normalize & score
- [ ] Télécharger outputs
- [ ] Collecter métriques
- [ ] Vérifier domain_scoring
- [ ] Analyser logs CloudWatch
- [ ] Valider succès

### Phase 5: Newsletter
- [ ] Exécuter newsletter
- [ ] Télécharger outputs
- [ ] Collecter métriques
- [ ] Valider qualité
- [ ] Valider succès

### Phase 6: Analyse
- [ ] Compiler métriques globales
- [ ] Comparer avec v9 si disponible
- [ ] Valider qualité globale

### Phase 7: Rapport
- [ ] Créer rapport détaillé
- [ ] Sauvegarder artifacts
- [ ] Documenter problèmes
- [ ] Formuler recommandations

### Phase 8: Suite
- [ ] Décider action suivante
- [ ] Documenter décision
- [ ] Planifier prochaine étape

---

## 🎓 Commandes Rapides

```bash
# Workflow complet
# 1. Créer config
cp client-config-examples/production/lai_weekly_dev.yaml \
   client-config-examples/production/lai_weekly_v10.yaml
# Éditer lai_weekly_v10.yaml

# 2. Déployer
aws s3 cp client-config-examples/production/lai_weekly_v10.yaml \
  s3://rag-lai-prod-client-configs/dev/lai_weekly_v10.yaml \
  --profile rag-lai-prod

# 3. Tester E2E
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v10 --env dev
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v10 --env dev
python scripts/invoke/invoke_newsletter_v2.py --client-id lai_weekly_v10 --env dev

# 4. Télécharger résultats
# (voir commandes détaillées dans phases 3-5)
```

---

**Plan Test E2E AWS LAI Weekly v10**  
**Version**: 1.0  
**Date**: 2026-02-02  
**Statut**: Prêt pour exécution  
**Respect Q Context**: ✅ Gouvernance, Versioning, Workflow
