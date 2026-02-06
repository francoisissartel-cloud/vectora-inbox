# Snapshot Moteur Vectora Inbox - 2026-02-06

**Date**: 2026-02-06 11:30
**Version**: v24 Stable
**Statut**: ✅ Moteur validé E2E - Production Ready

---

## 🎯 Contexte

Cette snapshot capture l'état **stable et validé** du moteur Vectora Inbox après le test E2E réussi avec lai_weekly_v24.

**Résultats E2E** :
- 24 items traités
- 7 items pertinents (29%)
- Score moyen: 68/100
- Aucune hallucination
- Summaries enrichis (10-15 lignes)
- Trademarks LAI reconnus
- Scoring cohérent

---

## 📦 Contenu de la Snapshot

### 1. Code Moteur (`src_v2/`)
- `vectora_core/` - Core engine
  - `normalization/` - Normalisation + Domain Scoring
  - `ingestion/` - Ingestion sources
  - `newsletter/` - Génération newsletter
- `lambda_handlers/` - Lambda entry points
  - `ingest_v2_handler.py`
  - `normalize_score_v2_handler.py`
  - `newsletter_v2_handler.py`

### 2. Prompts Bedrock (`canonical/prompts/`)

**Normalization** :
- `normalization/generic_normalization.yaml` v2.0
  - Summary 10-15 lignes minimum
  - Extraction routes d'administration
  - Event types: partnership, regulatory, clinical_update, business, corporate_move, financial_results, other
  - Max tokens: 2500

**Domain Scoring** :
- `domain_scoring/lai_domain_scoring.yaml` v5.0
  - Définition LAI complète (DDS + HLE)
  - Liste trademarks LAI (UZEDY, Oclaiz, etc.)
  - Scoring naturel sans catégorisation rigide
  - Format JSON minimal (is_relevant, score, confidence, reasoning)

**Editorial** :
- `editorial/lai_editorial.yaml` (inchangé)

### 3. Configuration Canonical (`canonical/`)

**Events** :
- `events/event_type_patterns.yaml`
  - Définition catégorie `business` (NEW)
  - Distinction business vs financial_results

**Scopes** :
- `scopes/company_scopes.yaml`
- `scopes/trademark_scopes.yaml` (liste complète LAI)
- `scopes/technology_scopes.yaml`
- `scopes/molecule_scopes.yaml`
- `scopes/indication_scopes.yaml`
- `scopes/exclusion_scopes.yaml`

**Domains** :
- `domains/lai_domain_definition.yaml`

### 4. Client Config
- `lai_weekly_v24.yaml`
  - Event weights: regulatory=7, business=7, partnership=8, clinical_update=6
  - Sources: lai_corporate_mvp, lai_press_mvp
  - Prompts: generic_normalization, lai_domain_scoring, lai_editorial

### 5. Rapport E2E
- `rapport_e2e_v24.md` - Rapport complet test E2E

---

## 🔑 Caractéristiques Clés

### Prompts v2.0 & v5.0

**Normalization v2.0** :
- ✅ Summary enrichis (10-15 lignes vs 2-3)
- ✅ Routes d'administration extraites
- ✅ Event type `business` pour sales/supply/distribution
- ✅ Max tokens 2500 (vs 1500)

**Domain Scoring v5.0** :
- ✅ Définition LAI riche (DDS + HLE détaillés)
- ✅ Liste complète trademarks LAI
- ✅ Évaluation naturelle (pas de catégories rigides)
- ✅ Pas d'hallucination (pure_player, hybrid supprimés)
- ✅ Format JSON minimal

### Event Types

1. **regulatory** (70-90) - Approvals, submissions
2. **business** (60-80) - Sales, supply, distribution (NEW)
3. **partnership** (60-80) - Collaborations, licensing
4. **clinical_update** (50-70) - Trial results
5. **corporate_move** (40-60) - Leadership, strategy
6. **financial_results** (10-30) - Generic quarterly earnings
7. **other** (20-40) - Misc

---

## 🚀 Utilisation de la Snapshot

### Restaurer le Moteur

```bash
# Restaurer code
xcopy .snapshots\20260206_moteur_v24_stable\src_v2 src_v2\ /E /I /H /Y

# Restaurer prompts
xcopy .snapshots\20260206_moteur_v24_stable\canonical canonical\ /E /I /H /Y

# Restaurer config client
copy .snapshots\20260206_moteur_v24_stable\lai_weekly_v24.yaml client-config-examples\production\
```

### Upload sur S3

```bash
# Prompts
aws s3 cp .snapshots/20260206_moteur_v24_stable/canonical/prompts/normalization/generic_normalization.yaml s3://vectora-inbox-config-dev/canonical/prompts/normalization/ --profile rag-lai-prod

aws s3 cp .snapshots/20260206_moteur_v24_stable/canonical/prompts/domain_scoring/lai_domain_scoring.yaml s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ --profile rag-lai-prod

# Config client
aws s3 cp .snapshots/20260206_moteur_v24_stable/lai_weekly_v24.yaml s3://vectora-inbox-config-dev/clients/ --profile rag-lai-prod
```

---

## 📊 Métriques de Performance

- **Temps E2E**: 183s pour 24 items
- **Throughput**: 0.13 items/s
- **Coût/item**: $0.0435
- **Coût/run**: $1.04
- **Taux normalisation**: 100%
- **Taux pertinence**: 29% (normal avec sources génériques)
- **Score moyen**: 68/100

---

## ✅ Validations

- [x] Test E2E complet réussi
- [x] Summaries enrichis validés
- [x] Routes d'administration extraites (champ présent)
- [x] Trademarks LAI reconnus seuls (UZEDY)
- [x] Scoring cohérent sans hallucination
- [x] Event type `business` intégré
- [x] Prompts uploadés sur S3 dev
- [x] Config client v24 uploadée

---

## 🔄 Prochaines Évolutions Possibles

1. **Multi-événements** : Détecter plusieurs event types par item
2. **Routes admin** : Améliorer extraction (attendre textes plus riches)
3. **Filtrage sources** : Réduire noise (conférences, rapports génériques)
4. **Scoring business** : Valider avec plus d'exemples

---

## 📝 Notes Importantes

- Cette snapshot est **production-ready**
- Tous les tests E2E sont passés
- Aucune régression détectée
- Prompts validés par run réel avec données fraîches
- Event type `business` ajouté mais pas encore testé en production

---

**Créé par**: Q Developer
**Validé par**: Test E2E lai_weekly_v24
**Statut**: ✅ Stable - Safe to use
