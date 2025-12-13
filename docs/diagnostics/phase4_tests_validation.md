# Phase 4 Diagnostic: Tests & Validation

## Modifications Effectuées

### Intégration dans le Pipeline Principal

#### Module `__init__.py` (vectora_core)

1. **Fonction `run_ingest_normalize_for_client`**:
   - **Extraction des watch_domains**: Récupération depuis `client_config.watch_domains`
   - **Passage aux normaliseurs**: Les `watch_domains` sont maintenant transmis à `normalize_items_batch`
   - **Évaluation automatique**: Si des domaines sont configurés, Bedrock évalue automatiquement leur pertinence

2. **Fonction `run_engine_for_client`**:
   - **Détection automatique**: Vérifie si les items contiennent des `domain_relevance`
   - **Système hybride**: Utilise le nouveau scoring si `domain_relevance` disponible, sinon fallback sur l'ancien
   - **Logging informatif**: Indique quel système de scoring est utilisé

### Script de Test Complet

#### Fichier `test_llm_domain_gating.py`
- **Test end-to-end**: Lance un run complet ingestion → normalisation → engine → newsletter
- **Analyse des métriques**: Calcule les taux de matching et sélection
- **Analyse des scores**: Examine les `domain_relevance` générés par Bedrock
- **Recommandations**: Propose des ajustements selon les résultats observés

## Flux de Données Intégré

### Pipeline Complet avec LLM Gating

```
1. Ingestion
   ↓
2. Normalisation + Domain Evaluation (Bedrock)
   ├─ Entités détectées (existant)
   └─ domain_relevance (NOUVEAU)
   ↓
3. Matching (optionnel/simplifié)
   ↓
4. Scoring avec domain_relevance
   ├─ Ancien système si pas de domain_relevance
   └─ Nouveau système si domain_relevance disponible
   ↓
5. Newsletter Assembly
```

### Exemple de Données Enrichies

```json
{
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "companies_detected": ["Camurus"],
  "technologies_detected": ["long acting", "depot"],
  "event_type": "clinical_update",
  "domain_relevance": [
    {
      "domain_id": "tech_lai_ecosystem",
      "domain_type": "technology",
      "is_on_domain": true,
      "relevance_score": 0.87,
      "reason": "Article discusses long-acting injectable technology with specific mention of depot formulations and Phase 3 clinical results."
    }
  ],
  "score": 26.75
}
```

## Métriques de Validation

### Métriques Clés à Surveiller

1. **Taux de Matching**: `items_matched / items_normalized`
   - **Cible**: 15-40% (équilibré)
   - **< 10%**: Domaines trop restrictifs ou contextes insuffisants
   - **> 80%**: Domaines trop larges, manque de sélectivité

2. **Taux de Sélection**: `items_selected / items_normalized`
   - **Cible**: 5-25% (sélectif mais pas vide)
   - **< 5%**: Seuils de scoring trop élevés
   - **> 50%**: Manque de sélectivité, newsletter trop longue

3. **Distribution des Scores de Pertinence**:
   - **Moyenne**: 0.4-0.8 (équilibré)
   - **Écart-type**: > 0.2 (bonne discrimination)
   - **Items avec score > 0.7**: Signaux forts détectés

### Analyse Qualitative

1. **Cohérence des Évaluations**:
   - Les `reason` sont-elles pertinentes ?
   - Les scores reflètent-ils la réalité métier ?
   - Y a-t-il des faux positifs/négatifs évidents ?

2. **Couverture des Domaines**:
   - Tous les domaines configurés sont-ils évalués ?
   - Les domaines prioritaires remontent-ils bien ?
   - Les exclusions fonctionnent-elles ?

## Commandes de Test

### Test Local Complet
```bash
cd vectora-inbox
python test_llm_domain_gating.py
```

### Test AWS Lambda (si déployé)
```bash
# Ingestion + Normalisation
aws lambda invoke --function-name vectora-inbox-ingest-normalize-dev \
  --payload '{"client_id": "lai_weekly_v2", "period_days": 7}' \
  response_ingest.json

# Engine
aws lambda invoke --function-name vectora-inbox-engine-dev \
  --payload '{"client_id": "lai_weekly_v2", "period_days": 7}' \
  response_engine.json
```

### Analyse des Résultats S3
```bash
# Vérifier les items normalisés avec domain_relevance
aws s3 cp s3://vectora-inbox-data-dev/normalized/lai_weekly_v2/2025/01/15/items.json items_normalized.json

# Vérifier la newsletter générée
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v2/2025/01/15/newsletter.md newsletter.md
```

## Calibration et Ajustements

### Paramètres à Ajuster

1. **Multiplicateurs Domain Relevance** (`scoring_rules.yaml`):
   ```yaml
   # Si trop peu d'items sélectionnés
   no_relevant_domain_penalty: 0.1  # Réduire à 0.05
   
   # Si trop d'items sélectionnés  
   no_relevant_domain_penalty: 0.3  # Augmenter
   ```

2. **Seuils de Sélection**:
   ```yaml
   selection_thresholds:
     min_score: 8  # Réduire si pas assez d'items
   ```

3. **Contextes de Domaines**:
   - Enrichir les descriptions dans `client_config.watch_domains.notes`
   - Ajouter des exemples dans les scopes canoniques
   - Affiner les `context_phrases` des scopes technologiques

### Indicateurs de Bon Fonctionnement

✅ **Système bien calibré**:
- Taux de matching: 20-35%
- Taux de sélection: 8-20%
- Scores de pertinence variés (0.2-0.9)
- Raisons cohérentes et spécifiques
- Newsletter équilibrée (pas vide, pas surchargée)

⚠️ **Ajustements nécessaires**:
- Taux extrêmes (< 5% ou > 80%)
- Scores uniformes (tous proches de 0.5)
- Raisons génériques ou répétitives
- Newsletter vide ou trop longue

## Prochaines Étapes

1. **Lancer le test complet** avec `lai_weekly_v2`
2. **Analyser les métriques** et ajuster les paramètres
3. **Valider la qualité** des évaluations Bedrock
4. **Déployer en DEV** et tester avec d'autres clients
5. **Documenter les bonnes pratiques** de configuration des domaines