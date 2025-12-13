# Phase 3 Diagnostic: Domain-Aware Scoring

## Modifications Effectuées

### Module `scorer.py`

#### Nouveau Paramètre `use_domain_relevance`
- **Fonction `score_items`**: Ajout du paramètre booléen pour activer/désactiver le nouveau système
- **Logique hybride**: Si `use_domain_relevance=True` et `domain_relevance` disponible, utilise le nouveau système, sinon fallback sur l'ancien

#### Nouvelle Fonction `compute_score_with_domain_relevance`
Remplace la logique de matching déterministe par l'évaluation LLM :

1. **Signal Principal**: `domain_relevance_score` remplace `domain_priority_weight`
2. **Conversion de Score**: Transforme les scores Bedrock (0-1) en multiplicateurs (0.5-3.0)
3. **Meilleur Score**: Prend le `max(relevance_score)` parmi tous les domaines évalués
4. **Pénalités**: Applique des pénalités si aucun domaine n'est pertinent

#### Nouvelle Fonction `_compute_domain_relevance_score`
- **Logique**: Pour chaque domaine avec `is_on_domain=true`, récupère `relevance_score`
- **Multiplicateur**: `0.5 + (max_relevance * 2.5)` → scores 0.5 à 3.0
- **Pénalités**: 
  - `no_domain_relevance_penalty: 0.1` si pas d'évaluation
  - `no_relevant_domain_penalty: 0.2` si aucun domaine pertinent

#### Fonctions Auxiliaires Simplifiées
- **`_compute_company_scope_bonus_from_entities`**: Version simplifiée basée sur les entités détectées
- **`_compute_trademark_bonus`**: Nouveau bonus pour les trademarks détectées

### Fichier `scoring_rules.yaml`

#### Nouveaux Paramètres
```yaml
# Domain relevance scoring (nouveau - LLM gating)
no_domain_relevance_penalty: 0.1
no_relevant_domain_penalty: 0.2
trademark_bonus: 0.5
hybrid_company_scope: "lai_companies_hybrid"
```

## Logique de Scoring Adaptée

### Ancien Système (Déterministe)
```
score = event_weight × domain_priority_weight × recency × source_weight × confidence + bonus
```

### Nouveau Système (LLM Gating)
```
score = event_weight × domain_relevance_score × recency × source_weight + bonus
```

### Différences Clés

1. **Signal Métier**: `domain_relevance_score` (0.5-3.0) remplace `domain_priority_weight` (1-3)
2. **Source de Vérité**: Évaluation Bedrock vs règles déterministes
3. **Granularité**: Score continu vs catégories discrètes
4. **Flexibilité**: Adaptation automatique vs règles figées

## Exemples de Calcul

### Item avec Forte Pertinence LAI
```json
{
  "event_type": "clinical_update",
  "domain_relevance": [
    {
      "domain_id": "tech_lai_ecosystem",
      "is_on_domain": true,
      "relevance_score": 0.87
    }
  ]
}
```

**Calcul**:
- `event_weight`: 5 (clinical_update)
- `domain_relevance_score`: 0.5 + (0.87 × 2.5) = 2.675
- `recency_factor`: 1.0 (récent)
- `source_weight`: 2.0 (corporate)
- **Score final**: 5 × 2.675 × 1.0 × 2.0 = **26.75**

### Item Non Pertinent
```json
{
  "domain_relevance": [
    {
      "domain_id": "tech_lai_ecosystem", 
      "is_on_domain": false,
      "relevance_score": 0.15
    }
  ]
}
```

**Calcul**:
- `domain_relevance_score`: 0.2 (no_relevant_domain_penalty)
- **Score final**: 5 × 0.2 × 1.0 × 2.0 = **2.0** (très faible)

## Intégration avec le Pipeline

### Flux de Données
1. **Normalisation**: Génère `domain_relevance` via Bedrock
2. **Matching**: Peut être simplifié ou contourné
3. **Scoring**: Utilise `domain_relevance` comme signal principal
4. **Sélection**: Items avec scores élevés remontent naturellement

### Compatibilité
- **Rétrocompatible**: `use_domain_relevance=False` utilise l'ancien système
- **Migration Progressive**: Permet de tester le nouveau système en parallèle
- **Fallback**: Si `domain_relevance` manquant, utilise `matched_domains`

## Avantages du Nouveau Système

1. **Précision**: Évaluation contextuelle vs matching de mots-clés
2. **Flexibilité**: Scores continus vs catégories binaires
3. **Généricité**: Fonctionne pour tout domaine sans règles spécifiques
4. **Transparence**: Raisons explicites dans `domain_relevance.reason`

## Risques et Limitations

1. **Dépendance LLM**: Qualité dépend de la performance de Bedrock
2. **Coût**: Prompts plus longs = coût légèrement plus élevé
3. **Variabilité**: Scores peuvent varier entre appels
4. **Calibration**: Nécessite ajustement des seuils et multiplicateurs

## Prochaine Étape

Phase 4: Tests et validation avec un run complet `lai_weekly_v2` pour analyser les résultats et ajuster les paramètres.