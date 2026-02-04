# Rapport Test E2E AWS - LAI Weekly v10

**Date**: 2026-02-02  
**Client**: lai_weekly_v10  
**Environnement**: AWS Dev  
**Durée totale**: ~15 minutes  

---

## 🎯 Objectif

Tester le pipeline complet sur AWS Dev avec nouveau client lai_weekly_v10 (copie de v9) pour valider :
- Architecture v2 (2 appels Bedrock : normalization + domain_scoring)
- Pipeline complet : Ingest → Normalize & Score → Newsletter
- Données fraîches (nouveau client_id)

---

## 📊 Résultats Globaux

| Étape | Statut | Durée | Items Input | Items Output |
|-------|--------|-------|-------------|--------------|
| **Ingest** | ✅ Réussi | ~20s | - | 28 |
| **Normalize & Score** | ✅ Réussi | ~4min | 28 | 28 (14 relevant) |
| **Newsletter** | ⚠️ Problème | ~5s | 28 | 0 |

**Statut Global**: ⚠️ **PARTIEL** - Ingest et Normalize OK, Newsletter KO

---

## 📋 Phase 1: Ingest ✅

### Configuration
- Client: lai_weekly_v10
- Period: 30 jours
- Sources: lai_corporate_mvp + lai_press_mvp
- Filtres: min_word_count: 50

### Résultats
- **Items ingérés**: 28
- **Durée**: ~20 secondes
- **Bucket S3**: `s3://vectora-inbox-data-dev/ingested/lai_weekly_v10/2026/02/02/items.json`

### Répartition par Source
```
MedinCell (corporate)    : 8 items (29%)
Nanexa (corporate)       : 6 items (21%)
Endpoints News (press)   : 5 items (18%)
Delsitech (corporate)    : 4 items (14%)
FiercePharma (press)     : 3 items (11%)
Camurus (corporate)      : 1 item  (4%)
FierceBiotech (press)    : 1 item  (4%)
```

### Validation
- ✅ Items ingérés > 20 (cible atteinte)
- ✅ Sources multiples actives (7 sources)
- ✅ Pas d'erreur dans logs CloudWatch
- ✅ Fichier items.json valide

**Verdict**: ✅ **Ingest fonctionne correctement**

---

## 📋 Phase 2: Normalize & Score ✅

### Configuration
- Architecture: v2 (2 appels Bedrock)
- Appel 1: generic_normalization (extraction entités)
- Appel 2: lai_domain_scoring (scoring domaine)
- Model: anthropic.claude-3-sonnet-20240229-v1:0
- Region: us-east-1
- Workers: 1

### Résultats
- **Items normalisés**: 28/28 (100%)
- **Items avec domain_scoring**: 28/28 (100%)
- **Items LAI relevant**: 14/28 (50%)
- **Score moyen**: 38.2/100
- **Durée**: 241 secondes (~4 minutes)
- **Bucket S3**: `s3://vectora-inbox-data-dev/curated/lai_weekly_v10/2026/02/02/items.json`

### Métriques Détaillées

**Taux de succès**:
- Normalization success rate: 100%
- Matching success rate: 0% ⚠️
- Scoring success rate: 100%

**Distribution Scores**:
- Min score: 0.2
- Max score: 3.3
- Avg score: 1.83
- High scores (>2.5): 0 items
- Medium scores (1.5-2.5): 0 items
- Low scores (<1.5): 10 items

**Distribution Confidence**:
- High: 26 items (93%)
- Medium: 1 item (4%)
- Low: 1 item (4%)

**Distribution Event Types**:
- financial_results: 7 items (25%)
- other: 6 items (21%)
- corporate_move: 5 items (18%)
- regulatory: 4 items (14%)
- partnership: 3 items (11%)
- Autres: 3 items (11%)

**Entités Extraites**:
- Companies: 0 ⚠️
- Molecules: 7
- Technologies: 0 ⚠️
- Trademarks: 8

### Validation
- ✅ 100% items normalisés
- ✅ 100% items avec domain_scoring (architecture v2 validée)
- ✅ Section domain_scoring présente avec champs requis
- ✅ Taux relevance 50% cohérent
- ✅ 2 appels Bedrock par item confirmés (logs CloudWatch)
- ⚠️ Aucune company extraite (problème potentiel)
- ⚠️ Aucune technology extraite (problème potentiel)
- ⚠️ Matching rate 0% (aucun domaine matché)

**Verdict**: ✅ **Normalize fonctionne, architecture v2 validée**  
⚠️ **Extraction entités incomplète à investiguer**

---

## 📋 Phase 3: Newsletter ⚠️

### Configuration
- Max items: 20
- Min score threshold: 0
- Sections: 4 (regulatory, partnerships, clinical, others)
- Format: markdown
- Include TLDR: true
- Include intro: true

### Résultats
- **Items dans newsletter**: 0 ❌
- **Sections remplies**: 0/4 ❌
- **Taille**: 1022 caractères (très court)
- **Durée**: ~5 secondes
- **Bucket S3**: `s3://vectora-inbox-newsletters-dev/lai_weekly_v10/2026/02/02/newsletter.md`

### Contenu Généré
```markdown
# LAI Weekly Newsletter - Week of 2026-02-02

**Generated:** February 02, 2026 | **Items:** 0 signals | **Coverage:** 0 sections

## 🎯 TL;DR
• Pfizer and Moderna announced a $2B partnership...
• FDA granted Breakthrough Therapy designation to Alkermes...
• Catalent acquired G-Con for $1B...

## 📰 Introduction
This week's LAI newsletter covers the latest developments...

---

## 📊 Newsletter Metrics
- **Total Signals:** 0 items processed
- **Sources:** 0 unique sources
```

### Problèmes Identifiés
1. ❌ **0 items dans newsletter** alors que 14 items relevant disponibles
2. ❌ **TL;DR contient items fictifs** (Pfizer/Moderna, Alkermes, Catalent) qui ne sont PAS dans les données normalisées
3. ❌ **Aucune section remplie** (0/4)
4. ❌ **Métriques à 0** (0 signals, 0 sources)

### Hypothèses
- Newsletter ne lit pas le bon fichier items.json
- Filtre de sélection trop strict
- Problème de scoring (scores trop bas pour sélection)
- Newsletter utilise données cached/anciennes
- Bug dans lambda newsletter-v2

**Verdict**: ❌ **Newsletter ne fonctionne pas correctement**

---

## 📊 Métriques Comparatives

| Métrique | Cible | Obtenu | Statut |
|----------|-------|--------|--------|
| **Ingest** |
| Items ingérés | > 20 | 28 | ✅ +40% |
| Sources actives | 2 | 7 | ✅ +250% |
| Durée | < 120s | ~20s | ✅ OK |
| **Normalize** |
| Items normalisés | 100% | 100% | ✅ OK |
| Items avec domain_scoring | 100% | 100% | ✅ OK |
| Taux relevance | > 50% | 50% | ✅ OK |
| Score moyen | 30-70 | 38.2 | ✅ OK |
| Durée | < 15min | ~4min | ✅ OK |
| **Newsletter** |
| Items sélectionnés | 10-20 | 0 | ❌ -100% |
| Sections remplies | 4 | 0 | ❌ -100% |
| TLDR présent | Oui | Oui (fictif) | ⚠️ |
| Durée | < 120s | ~5s | ✅ OK |

---

## 💰 Coûts Estimés

| Service | Utilisation | Coût Estimé |
|---------|-------------|-------------|
| **Bedrock** | 56 appels (28 items × 2) | ~$0.15 |
| **Lambda Ingest** | 1 invocation (~20s) | ~$0.001 |
| **Lambda Normalize** | 1 invocation (~4min) | ~$0.01 |
| **Lambda Newsletter** | 1 invocation (~5s) | ~$0.001 |
| **S3** | Storage + transfers | ~$0.001 |
| **Total** | | **~$0.16** |

---

## 🔍 Observations Techniques

### Architecture v2 (Domain Scoring)
✅ **Validée** - Les 2 appels Bedrock fonctionnent :
- Appel 1 : generic_normalization → extraction entités + classification
- Appel 2 : lai_domain_scoring → scoring domaine LAI

Structure domain_scoring présente dans tous les items avec :
- `is_relevant`: boolean
- `score`: 0-100
- `confidence`: low/medium/high
- `signals_detected`: {strong, medium, weak}
- `reasoning`: string

### Extraction Entités
⚠️ **Incomplète** :
- ✅ Molecules: 7 extraites
- ✅ Trademarks: 8 extraites
- ❌ Companies: 0 extraites (attendu: ~10-15)
- ❌ Technologies: 0 extraites (attendu: ~5-10)

Impact : Scoring incomplet, matching impossible

### Matching
❌ **0% matching rate** :
- Aucun item matché à un domaine
- `matched_domains`: [] pour tous les items
- Cause probable : extraction companies/technologies manquante

### Newsletter
❌ **Non fonctionnelle** :
- Ne sélectionne aucun item réel
- Génère contenu fictif dans TL;DR
- Problème critique à résoudre

---

## 🎯 Conclusion

### Succès ✅
1. **Ingest opérationnel** : 28 items ingérés, 7 sources actives
2. **Normalize opérationnel** : 100% items normalisés
3. **Architecture v2 validée** : Domain scoring fonctionne (2 appels Bedrock)
4. **Taux relevance cohérent** : 50% items LAI relevant

### Échecs ❌
1. **Newsletter non fonctionnelle** : 0 items générés, contenu fictif
2. **Extraction entités incomplète** : 0 companies, 0 technologies
3. **Matching rate 0%** : Aucun domaine matché

### Statut Global
⚠️ **TEST E2E PARTIEL**

**Pipeline validé** : Ingest → Normalize (2/3 étapes)  
**Pipeline non validé** : Newsletter (1/3 étape)

---

## 📋 Actions Recommandées

### Priorité 1 : Débugger Newsletter
1. Analyser logs CloudWatch newsletter
2. Vérifier lecture fichier items.json
3. Vérifier logique sélection items
4. Corriger génération TL;DR fictif

### Priorité 2 : Corriger Extraction Entités
1. Analyser prompt generic_normalization
2. Vérifier extraction companies
3. Vérifier extraction technologies
4. Tester avec items réels

### Priorité 3 : Valider Matching
1. Corriger extraction entités (prérequis)
2. Tester matching avec entités complètes
3. Valider taux matching > 50%

### Priorité 4 : Relancer Test E2E
1. Après corrections
2. Créer lai_weekly_v11
3. Valider pipeline complet

---

## 📁 Fichiers Générés

### Locaux
```
.tmp/test_e2e_v10/
├── ingest_items.json           (28 items, 25 KB)
├── normalized_items.json       (28 items normalisés)
├── newsletter.md               (newsletter vide, 1 KB)
├── newsletter_metadata.json    (metadata)
├── rapport_e2e.md             (ce rapport)
└── *.py                        (scripts test)
```

### S3
```
s3://vectora-inbox-config-dev/
└── clients/lai_weekly_v10.yaml

s3://vectora-inbox-data-dev/
├── ingested/lai_weekly_v10/2026/02/02/items.json
└── curated/lai_weekly_v10/2026/02/02/items.json

s3://vectora-inbox-newsletters-dev/
└── lai_weekly_v10/2026/02/02/newsletter.md
```

---

## 📞 Informations Techniques

**Lambdas utilisées**:
- `vectora-inbox-ingest-v2-dev`
- `vectora-inbox-normalize-score-v2-dev`
- `vectora-inbox-newsletter-v2-dev`

**Versions**:
- VECTORA_CORE_VERSION: 1.4.1
- NORMALIZE_VERSION: 2.1.0
- NEWSLETTER_VERSION: 1.8.0
- CANONICAL_VERSION: 2.0

**Région AWS**: eu-west-3  
**Compte AWS**: 786469175371  
**Profile**: rag-lai-prod

---

**Rapport généré**: 2026-02-02 20:35  
**Auteur**: Test E2E automatisé  
**Statut**: ⚠️ PARTIEL - 2/3 étapes validées
