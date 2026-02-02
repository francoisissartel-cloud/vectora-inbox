# Proposition: Architecture Bedrock Repensée
## Matching + Scoring Unifié par Watch Domain

**Date**: 2026-01-31  
**Auteur**: Analyse Architecturale  
**Statut**: Proposition pour validation

---

## 🎯 Problème Identifié

### Architecture Actuelle (Incohérente)

```
Appel 1: Normalisation
├─ Extraction entités ✅ (générique)
├─ Classification événement ✅ (générique)
├─ Génération résumé ✅ (générique)
└─ Score LAI (0-10) ❌ (spécifique LAI, pas générique!)

Appel 2: Matching par domaine
├─ Évaluation pertinence ✅
├─ Score 0.0-1.0 ✅
└─ Confiance high/medium/low ✅

Appel 3: Scoring déterministe
├─ 15+ règles imbriquées ❌
├─ Bonus/pénalités hardcodés ❌
└─ Logique complexe ❌
```

### Incohérences Majeures

1. **"lai_relevance_score" dans normalisation** → Pas générique, spécifique LAI
2. **Matching retourne score 0.0-1.0** → Puis scoring recalcule tout
3. **Scoring déterministe avec 15+ règles** → Difficile à maintenir
4. **3 systèmes de scoring différents** → Confusion

---

## 💡 Architecture Proposée (Cohérente)

### Principe Directeur

**"Bedrock fait le matching ET le scoring par watch domain en un seul appel"**

### Nouveau Flux

```
Appel 1: Normalisation Générique (1 par item)
├─ Extraction entités (companies, molecules, technologies, trademarks)
├─ Classification événement (partnership, regulatory, clinical_update)
├─ Génération résumé (2-3 phrases)
├─ Extraction date publication
└─ STOP - Pas de score vertical-spécifique

Appel 2: Matching + Scoring par Watch Domain (1 par item)
├─ Pour chaque watch domain du client:
│   ├─ Évaluation pertinence sémantique
│   ├─ Score de pertinence (0-100)
│   ├─ Confiance (high/medium/low)
│   ├─ Justification (reasoning)
│   └─ Signaux détectés (entités matchées)
└─ Output: Scores par domaine, prêts pour sélection

Appel 3: Génération Éditoriale (1 par newsletter)
└─ TL;DR + Introduction + Synthèses sections
```

### Avantages

✅ **Généricité**: Normalisation 100% générique (transposable à toute verticale)  
✅ **Cohérence**: 1 seul score par domaine (Bedrock)  
✅ **Simplicité**: Pas de scoring déterministe complexe  
✅ **Pilotabilité**: Ajuster via prompts canonical  
✅ **Feedback loop**: Améliorer prompts avec retours utilisateur  
✅ **Scalabilité**: Même logique pour LAI, siRNA, cell therapy, etc.

---

## 🏗️ Architecture Détaillée

### Appel 1: Normalisation Générique

**Fichier**: `bedrock_client.py`  
**Prompt**: `canonical/prompts/normalization/generic_normalization.yaml`

**Rôle**: Extraction d'informations factuelles uniquement

```yaml
# generic_normalization.yaml (NOUVEAU)
user_template: |
  Analyze this biotech/pharma news item and extract structured information.
  
  TEXT TO ANALYZE:
  {{item_text}}
  
  TASK:
  1. Generate a concise summary (2-3 sentences)
  2. Extract publication date (format: YYYY-MM-DD)
  3. Classify event type: partnership, regulatory, clinical_update, corporate_move, etc.
  4. Extract ALL company names mentioned
  5. Extract ALL drug/molecule names mentioned
  6. Extract ALL technology keywords mentioned
  7. Extract ALL trademark names mentioned
  8. Extract ALL therapeutic indications mentioned
  
  CRITICAL: Only extract entities EXPLICITLY mentioned in the text.
  DO NOT evaluate relevance to any specific domain - just extract facts.
  
  RESPONSE FORMAT (JSON only):
  {
    "summary": "...",
    "extracted_date": "2025-12-09",
    "date_confidence": 0.95,
    "event_type": "partnership",
    "companies_detected": ["Company A", "Company B"],
    "molecules_detected": ["Molecule X"],
    "technologies_detected": ["Technology Y"],
    "trademarks_detected": ["Trademark Z"],
    "indications_detected": ["Indication W"]
  }
```

**Output**: Item normalisé générique (pas de score vertical)

---

### Appel 2: Matching + Scoring Unifié par Watch Domain

**Fichier**: `bedrock_domain_scorer.py` (NOUVEAU)  
**Prompt**: `canonical/prompts/domain_scoring/{vertical}_domain_scoring.yaml`

**Rôle**: Évaluer pertinence ET scorer pour chaque watch domain

```yaml
# lai_domain_scoring.yaml (NOUVEAU)
user_template: |
  Evaluate the relevance of this normalized item to LAI watch domains and score it.
  
  NORMALIZED ITEM:
  Title: {{item_title}}
  Summary: {{item_summary}}
  Event Type: {{item_event_type}}
  Entities: {{item_entities}}
  Date: {{item_date}}
  
  WATCH DOMAINS TO EVALUATE:
  {{ref:lai_watch_domains}}
  
  SCORING CRITERIA (per domain):
  {{ref:lai_scoring_criteria}}
  
  For each domain, evaluate:
  1. Is this item relevant? (yes/no)
  2. Relevance score (0-100):
     - Base score from event type importance
     - Boost for key entities (pure players, trademarks)
     - Boost for recency
     - Penalty for low relevance signals
  3. Confidence level (high/medium/low)
  4. Which entities contributed to the score?
  5. Brief reasoning
  
  RESPONSE FORMAT (JSON only):
  {
    "domain_scores": [
      {
        "domain_id": "tech_lai_ecosystem",
        "is_relevant": true,
        "score": 85,
        "confidence": "high",
        "reasoning": "Extended-release injectable + pure player company",
        "score_breakdown": {
          "base_score": 60,
          "entity_boost": 20,
          "recency_boost": 5,
          "total": 85
        },
        "matched_entities": {
          "companies": ["MedinCell"],
          "technologies": ["Extended-Release Injectable"],
          "trademarks": ["UZEDY®"]
        }
      }
    ]
  }
```

**Configuration Canonical**: `canonical/scoring_criteria/lai_scoring_criteria.yaml`

```yaml
# lai_scoring_criteria.yaml (NOUVEAU)
event_type_base_scores:
  partnership: 60
  regulatory: 70
  clinical_update: 50
  corporate_move: 40
  financial_results: 30
  other: 20

entity_boosts:
  pure_player_companies:
    scope: lai_companies_mvp_core
    boost: 25
  
  trademark_mentions:
    scope: lai_trademarks_global
    boost: 20
  
  key_molecules:
    scope: lai_molecules_global
    boost: 15
  
  hybrid_companies:
    scope: lai_companies_hybrid
    boost: 10

recency_boosts:
  - age_days: 0-7
    boost: 10
  - age_days: 8-30
    boost: 5
  - age_days: 31-90
    boost: 0
  - age_days: 91+
    penalty: -10

penalties:
  no_relevant_entities: -20
  low_confidence: -10
```

**Output**: Scores par domaine, prêts pour sélection

---

## 📊 Comparaison Architectures

### Architecture Actuelle

| Aspect | Évaluation |
|--------|------------|
| **Généricité** | ❌ "lai_relevance_score" hardcodé |
| **Cohérence** | ❌ 3 systèmes de scoring différents |
| **Simplicité** | ❌ 15+ règles déterministes |
| **Pilotabilité** | ⚠️ Modifier code Python pour ajuster |
| **Feedback loop** | ❌ Difficile d'intégrer retours |
| **Scalabilité** | ⚠️ Dupliquer logique par verticale |

### Architecture Proposée

| Aspect | Évaluation |
|--------|------------|
| **Généricité** | ✅ Normalisation 100% générique |
| **Cohérence** | ✅ 1 seul score par domaine (Bedrock) |
| **Simplicité** | ✅ Pas de scoring déterministe |
| **Pilotabilité** | ✅ Ajuster via prompts + canonical |
| **Feedback loop** | ✅ Améliorer prompts facilement |
| **Scalabilité** | ✅ Même pattern pour toutes verticales |

---

## 🔄 Migration Path

### Étape 1: Créer Nouveau Système (Parallèle)

1. Créer `bedrock_domain_scorer.py`
2. Créer prompts `canonical/prompts/domain_scoring/`
3. Créer `canonical/scoring_criteria/`
4. Tester en parallèle de l'ancien système

### Étape 2: Valider avec Feedback Humain

1. Comparer scores anciens vs nouveaux
2. Ajuster prompts selon feedback
3. Itérer jusqu'à corrélation >0.9

### Étape 3: Basculer

1. Supprimer `scorer.py` (déterministe)
2. Supprimer "lai_relevance_score" de normalisation
3. Utiliser uniquement scores Bedrock

### Étape 4: Généraliser

1. Créer `sirna_domain_scoring.yaml`
2. Créer `cell_therapy_domain_scoring.yaml`
3. Même architecture pour toutes verticales

---

## 💰 Impact Coût et Performance

### Coût

**Actuel**:
- Normalisation: $0.003 × N items
- Matching: $0.004 × N items
- **Total: $0.007 × N items**

**Proposé**:
- Normalisation: $0.003 × N items
- Domain Scoring: $0.005 × N items (prompt plus riche)
- **Total: $0.008 × N items**

**Différence**: +$0.001 par item (+14%)

**Justification**: Gain en simplicité, cohérence, pilotabilité >> Coût marginal

### Performance

**Actuel**: 2 appels × 5s = 10s par item

**Proposé**: 2 appels × 5s = 10s par item (identique)

**Pas d'impact performance**

---

## 🎯 Bénéfices Clés

### 1. Généricité Totale

```python
# Normalisation identique pour LAI, siRNA, cell therapy
normalize_item(text)  # Pas de paramètre vertical

# Scoring adapté par vertical via prompts
score_for_domains(item, "lai")  # Prompt lai_domain_scoring.yaml
score_for_domains(item, "sirna")  # Prompt sirna_domain_scoring.yaml
```

### 2. Feedback Loop Simplifié

```
Utilisateur: "Item X devrait avoir score plus élevé"
↓
Ajuster: canonical/scoring_criteria/lai_scoring_criteria.yaml
↓
Sync S3
↓
Tester immédiatement (pas de redéploiement)
```

### 3. Traçabilité Améliorée

```json
{
  "domain_id": "tech_lai_ecosystem",
  "score": 85,
  "score_breakdown": {
    "base_score": 60,
    "pure_player_boost": 25,
    "recency_boost": 0,
    "total": 85
  },
  "reasoning": "Pure player MedinCell + Extended-Release Injectable technology"
}
```

### 4. Scalabilité Verticales

**Ajouter nouvelle verticale = 2 fichiers**:
1. `canonical/prompts/domain_scoring/sirna_domain_scoring.yaml`
2. `canonical/scoring_criteria/sirna_scoring_criteria.yaml`

**Pas de code Python à modifier**

---

## ⚠️ Risques et Mitigations

### Risque 1: Scores Bedrock Moins Précis

**Mitigation**:
- Phase de validation avec comparaison ancien/nouveau
- Ajustement prompts itératif
- Garder ancien système en fallback temporairement

### Risque 2: Coût Légèrement Supérieur

**Mitigation**:
- +14% acceptable pour gains en simplicité
- Optimiser prompts pour réduire tokens
- ROI positif sur maintenance long terme

### Risque 3: Dépendance Bedrock Accrue

**Mitigation**:
- Garder fallback déterministe simple
- Cache Bedrock pour items similaires
- Monitoring coûts et performance

---

## 🎓 Recommandation Finale

### ✅ ADOPTER cette architecture car:

1. **Cohérence**: 1 seul score par domaine (pas 3 systèmes)
2. **Généricité**: Normalisation 100% réutilisable
3. **Simplicité**: Pas de scoring déterministe complexe
4. **Pilotabilité**: Ajuster via prompts (pas code)
5. **Feedback loop**: Amélioration continue facile
6. **Scalabilité**: Pattern identique pour toutes verticales

### 📅 Timeline Proposée

**Semaine 1-2**: Créer nouveau système en parallèle  
**Semaine 3-4**: Validation avec feedback humain  
**Semaine 5**: Basculement progressif  
**Semaine 6**: Suppression ancien système

**Durée totale**: 6 semaines

---

## 🤔 Questions pour Validation

1. **Acceptes-tu le coût marginal** (+14%) pour gains en simplicité ?
2. **Veux-tu une phase de validation** (ancien vs nouveau) ou bascule directe ?
3. **Préfères-tu garder fallback déterministe** ou 100% Bedrock ?
4. **Quelle priorité** vs correctifs matching/dates ?

---

**Prochaine étape**: Valider cette proposition avant de créer plan d'implémentation.
