# Plan Test E2E LAI_WEEKLY_V9 + Résumé Modifications Phase 6bis → Phase 8

**Date**: 2026-02-02  
**Objectif**: Tester lai_weekly_v9 avec domain scoring + Résumé complet modifications  
**Template utilisé**: `docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`  
**Statut**: 📋 Prêt à exécuter

---

## 🎯 OBJECTIFS

1. **Tester lai_weekly_v9** avec domain scoring activé (architecture 2 appels Bedrock)
2. **Utiliser le template E2E** disponible dans `docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`
3. **Résumé avant/après** de toutes les modifications Phase 6bis → Phase 8
4. **Valider matching** avec domain scoring (attendu : taux matching > 0%)

---

## 📝 PHASE 1 : PRÉPARATION TEST E2E

### Étape 1.1 : Ingestion lai_weekly_v9

**Commande**:
```bash
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v9 --env dev
```

**Attendu**:
- Items ingérés dans `s3://vectora-inbox-data-dev/ingested/lai_weekly_v9/[date]/items.json`
- Volume similaire à v8 (~28 items)
- Sources LAI scrapées avec succès

**Validation**:
- [ ] Commande exécutée sans erreur
- [ ] Fichier items.json créé sur S3
- [ ] Volume items cohérent

---

### Étape 1.2 : Normalisation avec domain scoring

**Commande**:
```bash
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v9 --env dev --timeout 300
```

**Attendu**:
- 2 appels Bedrock par item :
  1. `generic_normalization` (normalisation générique)
  2. `lai_domain_scoring` (scoring domaine LAI)
- Section `domain_scoring` présente dans items.json
- Temps exécution : ~170-200s pour 28 items (+44-69% vs v8)
- Coût : ~+70% vs v8

**Validation**:
- [ ] Commande exécutée sans erreur
- [ ] Temps exécution dans la fourchette attendue
- [ ] Fichier curated/items.json créé sur S3

---

### Étape 1.3 : Télécharger résultats

**Commandes**:
```bash
# Télécharger items.json curated
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v9/2026/02/02/items.json .tmp/items_lai_weekly_v9_phase8.json --profile rag-lai-prod

# Télécharger aussi v8 pour comparaison
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v8/2026/02/02/items.json .tmp/items_lai_weekly_v8_phase8.json --profile rag-lai-prod
```

**Validation**:
- [ ] Fichier v9 téléchargé
- [ ] Fichier v8 téléchargé (baseline)
- [ ] Fichiers lisibles (JSON valide)

---

## 📊 PHASE 2 : ANALYSE AVEC TEMPLATE E2E

### Étape 2.1 : Analyse rapide Python

**Script d'analyse**:
```python
import json

# Charger v9
with open('.tmp/items_lai_weekly_v9_phase8.json') as f:
    data_v9 = json.load(f)

# Charger v8 (baseline)
with open('.tmp/items_lai_weekly_v8_phase8.json') as f:
    data_v8 = json.load(f)

items_v9 = data_v9['items']
items_v8 = data_v8['items']

print("=" * 60)
print("COMPARAISON V8 (baseline) vs V9 (domain scoring)")
print("=" * 60)

# Statistiques v8
print(f"\n📊 V8 (baseline - sans domain scoring):")
print(f"  - Total items: {len(items_v8)}")
print(f"  - Items avec domain_scoring: {sum(1 for i in items_v8 if 'domain_scoring' in i)}")
print(f"  - Items matched: {sum(1 for i in items_v8 if i.get('matching_results', {}).get('matched_domains'))}")
print(f"  - Items scored >0: {sum(1 for i in items_v8 if i.get('scoring_results', {}).get('final_score', 0) > 0)}")

# Statistiques v9
print(f"\n📊 V9 (avec domain scoring):")
print(f"  - Total items: {len(items_v9)}")
print(f"  - Items avec domain_scoring: {sum(1 for i in items_v9 if 'domain_scoring' in i)}")
print(f"  - Items matched: {sum(1 for i in items_v9 if i.get('matching_results', {}).get('matched_domains'))}")
print(f"  - Items scored >0: {sum(1 for i in items_v9 if i.get('scoring_results', {}).get('final_score', 0) > 0)}")

# Vérifier structure domain_scoring
print(f"\n🔍 Exemples domain_scoring (v9):")
for item in items_v9[:3]:
    if 'domain_scoring' in item:
        ds = item['domain_scoring']
        print(f"\n  {item['title'][:60]}...")
        print(f"    - is_relevant: {ds.get('is_relevant')}")
        print(f"    - score: {ds.get('score')}")
        print(f"    - confidence: {ds.get('confidence')}")
        print(f"    - signals: {len(ds.get('signals_detected', {}).get('strong', []))} strong, {len(ds.get('signals_detected', {}).get('medium', []))} medium")

# Comparaison matching
matched_v8 = sum(1 for i in items_v8 if i.get('matching_results', {}).get('matched_domains'))
matched_v9 = sum(1 for i in items_v9 if i.get('matching_results', {}).get('matched_domains'))

print(f"\n📈 Amélioration matching:")
print(f"  - V8: {matched_v8}/{len(items_v8)} ({matched_v8/len(items_v8)*100:.1f}%)")
print(f"  - V9: {matched_v9}/{len(items_v9)} ({matched_v9/len(items_v9)*100:.1f}%)")
print(f"  - Delta: +{matched_v9 - matched_v8} items (+{(matched_v9 - matched_v8)/len(items_v8)*100:.1f}%)")
```

**Validation**:
- [ ] Script exécuté sans erreur
- [ ] Section domain_scoring présente dans 100% items v9
- [ ] Section domain_scoring absente dans 100% items v8
- [ ] Taux matching v9 > v8 (attendu)

---

### Étape 2.2 : Créer rapport E2E complet

**Utiliser template**: `docs/templates/TEMPLATE_TEST_E2E_STANDARD.md`

**Sections à remplir**:

1. **📋 MÉTADONNÉES DU TEST**
   - Client: lai_weekly_v9
   - Date: 2026-02-02
   - Environnement: dev
   - Objectif: Validation architecture 2 appels Bedrock

2. **🎯 RÉSUMÉ EXÉCUTIF**
   - Métriques clés vs baseline v8
   - Funnel de conversion
   - Verdict global

3. **📊 PHASE 1 : INGESTION**
   - Volume items
   - Sources scrapées
   - Distribution word count

4. **📊 PHASE 2 : NORMALISATION & SCORING**
   - ✅ **NOUVEAU** : Section domain_scoring
   - Extraction entités
   - Event classification
   - Domain scoring : is_relevant, score, confidence, signals_detected, reasoning
   - Matching results

5. **📊 PHASE 3 : GÉNÉRATION NEWSLETTER**
   - Sélection items
   - Répartition sections
   - Génération éditoriale

6. **🔍 ANALYSE ITEM PAR ITEM**
   - Items sélectionnés newsletter
   - Items matchés non sélectionnés
   - Items non matchés
   - Évaluation humaine (D'ACCORD / PAS D'ACCORD)

7. **📈 MÉTRIQUES DE PERFORMANCE**
   - Métriques techniques
   - Métriques qualité
   - Métriques business

8. **💰 ANALYSE COÛTS DÉTAILLÉE**
   - Coûts Bedrock (2 appels vs 1 appel)
   - Coûts AWS
   - Projections

9. **🔧 RECOMMANDATIONS D'AMÉLIORATION**
   - Priorité CRITIQUE
   - Priorité HAUTE
   - Priorité MOYENNE

10. **🎯 VALIDATION READINESS PRODUCTION**
    - Critères validés
    - Actions requises

**Fichier de sortie**: `docs/reports/development/rapport_e2e_lai_weekly_v9_phase8_20260202.md`

**Validation**:
- [ ] Rapport créé avec template
- [ ] Toutes les sections remplies
- [ ] Comparaison v8 vs v9 documentée
- [ ] Évaluation humaine complétée

---

## 📈 PHASE 3 : RÉSUMÉ AVANT/APRÈS MODIFICATIONS

### Étape 3.1 : Créer document récapitulatif

**Fichier de sortie**: `docs/reports/development/resume_modifications_phase6bis_phase8_20260202.md`

**Contenu**:

#### 🔄 Récapitulatif Complet Phase 6bis → Phase 8

##### **AVANT (Phase 6bis - lai_weekly_v8)**

**Architecture**:
- 1 appel Bedrock par item (generic_normalization)
- Prompt : `canonical/prompts/normalization/generic_normalization.yaml`
- Pas de domain scoring

**Structure items.json**:
```json
{
  "item_id": "...",
  "normalized_content": {
    "summary": "...",
    "event_type": "...",
    "entities": {...}
  },
  "matching_results": {
    "matched_domains": [],
    "domain_relevance": {}
  },
  "scoring_results": {...},
  "has_lai_relevance_score": false  // ✅ Supprimé Phase 6bis
}
```

**Fichiers modifiés**:
- `src_v2/vectora_core/normalization/normalizer.py` : Suppression lai_relevance_score
- `canonical/prompts/normalization/generic_normalization.yaml` : Prompt générique

**Version**: VECTORA_CORE 1.3.0 (layer v49)

---

##### **APRÈS (Phase 8 - lai_weekly_v9)**

**Architecture**:
- 2 appels Bedrock par item :
  1. `generic_normalization` (normalisation générique)
  2. `lai_domain_scoring` (scoring domaine LAI) - **CONDITIONNEL** si `enable_domain_scoring: true`
- Prompts : 
  - `canonical/prompts/normalization/generic_normalization.yaml`
  - `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`

**Structure items.json**:
```json
{
  "item_id": "...",
  "normalized_content": {
    "summary": "...",
    "event_type": "...",
    "entities": {...}
  },
  "domain_scoring": {  // ✅ NOUVEAU
    "is_relevant": true,
    "score": 85,
    "confidence": "high",
    "signals_detected": {
      "strong": [...],
      "medium": [...],
      "weak": [...]
    },
    "reasoning": "..."
  },
  "matching_results": {
    "matched_domains": ["tech_lai_ecosystem"],
    "domain_relevance": {...}
  },
  "scoring_results": {...},
  "has_lai_relevance_score": false,
  "has_domain_scoring": true  // ✅ NOUVEAU
}
```

**Fichiers modifiés**:
1. **Nouveau module** : `src_v2/vectora_core/normalization/bedrock_domain_scorer.py`
   - Classe `BedrockDomainScorer`
   - Méthode `score_item_for_domain()`
   - Gestion signaux strong/medium/weak

2. **Modifié** : `src_v2/vectora_core/normalization/normalizer.py`
   - Intégration domain scoring conditionnel
   - Appel `bedrock_domain_scorer.score_item_for_domain()` si `enable_domain_scoring: true`
   - Ajout section `domain_scoring` dans items

3. **Nouveau canonical** :
   - `canonical/prompts/domain_scoring/lai_domain_scoring.yaml`
   - `canonical/domains/lai_domain_definition.yaml`

4. **Client config** : `client-config-examples/lai_weekly_v9.yaml`
   - `bedrock_config.enable_domain_scoring: true`

**Version**: VECTORA_CORE 1.4.0 (layer v50)

---

#### 📊 Tableau Comparatif Détaillé

| Aspect | Phase 6bis (v8) | Phase 8 (v9) | Changement |
|--------|-----------------|--------------|------------|
| **Appels Bedrock** | 1 (normalization) | 2 (normalization + domain scoring) | +100% |
| **Temps exécution** | ~118s (28 items) | ~170-200s (28 items) | +44-69% |
| **Coût estimé** | $0.XX | $0.XX | +70% |
| **Section domain_scoring** | ❌ Absente | ✅ Présente (si activé) | Nouveau |
| **lai_relevance_score** | ❌ Supprimé | ❌ Supprimé | Maintenu |
| **Rétrocompatibilité** | N/A | ✅ 100% (v8 fonctionne) | Validé |
| **Layer version** | v49 | v50 | +1 |
| **VECTORA_CORE** | 1.3.0 | 1.4.0 | +0.1.0 |
| **Taux matching** | 0% (v8) | XX% (v9) | +XX% |

---

#### 🎯 Modifications Clés Résumées

##### ✅ **Ajouts Phase 8**
1. Module `bedrock_domain_scorer.py` (nouveau)
2. Prompt `lai_domain_scoring.yaml` (nouveau)
3. Domain definition `lai_domain_definition.yaml` (nouveau)
4. Section `domain_scoring` dans items.json (conditionnel)
5. Flag `has_domain_scoring` dans items (nouveau)
6. Client `lai_weekly_v9.yaml` avec `enable_domain_scoring: true`

##### ✅ **Maintenu Phase 6bis**
1. Suppression `lai_relevance_score` (0 occurrences)
2. Prompt `generic_normalization.yaml` (inchangé)
3. Rétrocompatibilité clients legacy (v8 fonctionne sans domain scoring)

##### ✅ **Améliorations Architecture**
1. Architecture 2 appels Bedrock validée
2. Domain scoring conditionnel (pas d'impact clients legacy)
3. Signaux LAI structurés (strong/medium/weak)
4. Reasoning explicite pour matching
5. Amélioration taux matching attendue

**Validation**:
- [ ] Document récapitulatif créé
- [ ] Tableau comparatif complet
- [ ] Modifications clés listées
- [ ] Avant/après documenté

---

## 🚀 PHASE 4 : EXÉCUTION ET VALIDATION

### Checklist Complète

**Préparation**:
- [ ] Client lai_weekly_v9 uploadé sur S3 dev
- [ ] Canonical synchronisé (prompts + domains)
- [ ] Layer v50 déployé sur 3 Lambdas

**Exécution**:
- [ ] Ingestion lai_weekly_v9 réussie
- [ ] Normalisation lai_weekly_v9 réussie (timeout 5 min)
- [ ] Fichiers téléchargés depuis S3

**Analyse**:
- [ ] Script Python exécuté
- [ ] Section domain_scoring validée (v9)
- [ ] Rétrocompatibilité validée (v8)
- [ ] Rapport E2E créé avec template
- [ ] Résumé modifications créé

**Validation**:
- [ ] Taux matching v9 > v8
- [ ] Temps exécution dans fourchette attendue
- [ ] Coût dans fourchette attendue
- [ ] Qualité signaux LAI validée
- [ ] Aucune régression détectée

---

## 📋 LIVRABLES ATTENDUS

1. **Rapport E2E complet** : `docs/reports/development/rapport_e2e_lai_weekly_v9_phase8_20260202.md`
   - Utilise template `TEMPLATE_TEST_E2E_STANDARD.md`
   - Toutes sections remplies
   - Évaluation humaine complétée

2. **Résumé modifications** : `docs/reports/development/resume_modifications_phase6bis_phase8_20260202.md`
   - Avant/après détaillé
   - Tableau comparatif
   - Modifications clés

3. **Fichiers items.json** :
   - `.tmp/items_lai_weekly_v8_phase8.json` (baseline)
   - `.tmp/items_lai_weekly_v9_phase8.json` (avec domain scoring)

4. **Script d'analyse** : `.tmp/analyse_v8_vs_v9.py`
   - Comparaison automatisée
   - Métriques clés

---

## ✅ CRITÈRES DE SUCCÈS

### Critères Techniques
- [ ] lai_weekly_v9 ingestion réussie
- [ ] lai_weekly_v9 normalisation réussie (2 appels Bedrock)
- [ ] Section `domain_scoring` présente dans 100% des items v9
- [ ] Section `domain_scoring` absente dans 100% des items v8 (rétrocompatibilité)
- [ ] Temps exécution v9 : +40-70% vs v8 (acceptable)
- [ ] Coût v9 : +70% vs v8 (acceptable)

### Critères Qualité
- [ ] Matching amélioré (taux matching v9 > v8)
- [ ] Signaux LAI pertinents détectés (strong/medium/weak)
- [ ] Reasoning explicite et cohérent
- [ ] Aucune régression sur v8

### Critères Documentation
- [ ] Rapport E2E complet avec template
- [ ] Résumé modifications avant/après documenté
- [ ] Évaluation humaine complétée
- [ ] Recommandations d'amélioration listées

---

## 🎯 DÉCISION ATTENDUE

### Critères de Validation

| Critère | Objectif | Statut |
|---------|----------|--------|
| Architecture 2 appels fonctionnelle | ✅ | ⏳ |
| Section domain_scoring présente (v9) | ✅ | ⏳ |
| Rétrocompatibilité v8 | ✅ | ⏳ |
| Taux matching amélioré | >0% (v9) | ⏳ |
| Temps exécution acceptable | <300s | ⏳ |
| Coût acceptable | <$2/run | ⏳ |
| Qualité signaux LAI | >80% | ⏳ |
| Documentation complète | ✅ | ⏳ |

### Décision Finale

🟢 **GO POUR PROMOTION STAGE** si tous critères validés  
🟡 **GO CONDITIONNEL** si critères partiels  
🔴 **NO-GO** si critères critiques non validés

---

## 📞 COMMANDES RAPIDES

```bash
# Ingestion v9
python scripts/invoke/invoke_ingest_v2.py --client-id lai_weekly_v9 --env dev

# Normalisation v9 (timeout 5 min)
python scripts/invoke/invoke_normalize_score_v2.py --client-id lai_weekly_v9 --env dev --timeout 300

# Télécharger résultats
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v9/2026/02/02/items.json .tmp/items_lai_weekly_v9_phase8.json --profile rag-lai-prod
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v8/2026/02/02/items.json .tmp/items_lai_weekly_v8_phase8.json --profile rag-lai-prod

# Logs CloudWatch
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev --since 10m --follow --profile rag-lai-prod
```

---

**Plan créé le**: 2026-02-02  
**Prêt pour exécution**: ✅ OUI  
**Durée estimée**: 1-2 heures  
**Prochaine étape**: Exécuter Phase 1 - Étape 1.1 (Ingestion lai_weekly_v9)
