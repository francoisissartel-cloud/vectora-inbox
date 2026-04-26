# LLM Domain Gating Design - Vectora Inbox

## État Actuel

### Normalisation
- Bedrock extrait les entités (companies, molecules, technologies, indications)
- Calcul d'intersections avec les scopes canoniques
- Pas d'évaluation de pertinence par domaine

### Matching
- Règles déterministes strictes dans `domain_matching_rules.yaml`
- Logique complexe pour `technology_complex` profile
- Taux de matching très faible (porte blindée)

### Scoring
- Basé sur intersections binaires + bonus/malus
- Pas de signal de pertinence métier nuancé

## Nouvelle Architecture Domain Relevance

### Objectif
Remplacer le matching déterministe par une évaluation LLM de pertinence par domaine, intégrée dans la normalisation sans appel Bedrock supplémentaire.

### Schéma de Sortie Cible
```json
{
  "domain_relevance": [
    {
      "domain_id": "tech_lai_ecosystem",
      "domain_type": "technology", 
      "is_on_domain": true,
      "relevance_score": 0.87,
      "reason": "Article discusses long-acting injectable technology with specific mention of depot formulations"
    }
  ]
}
```

### Composants Clés

1. **Domain Context Builder**: Construit une représentation compacte des domaines clients
2. **Enhanced Bedrock Prompt**: Enrichit le prompt de normalisation avec évaluation de domaines
3. **Domain-Aware Scoring**: Utilise `relevance_score` comme signal principal

## Plan d'Exécution

### Phase 1: Domain Context Builder
- Analyser `client_config.watch_domains` et scopes canoniques associés
- Créer une représentation compacte de chaque domaine pour injection dans prompt
- Extraire exemples d'entités et contexte métier

### Phase 2: Enhanced Bedrock Normalization
- Enrichir le prompt de normalisation avec contexte des domaines
- Adapter le schéma de sortie pour inclure `domain_relevance`
- Modifier `normalizer.py` et `bedrock_client.py`

### Phase 3: Domain-Aware Scoring
- Intégrer `domain_relevance` dans le système de scoring
- Atténuer les règles déterministes strictes
- Conserver les bonus existants (pure_player, trademarks, etc.)

### Phase 4: Tests & Validation
- Déployer en DEV
- Lancer un run complet `lai_weekly_v2`
- Analyser les résultats et ajuster les seuils

## Généricité
- Aucune logique LAI codée en dur
- Système piloté par `client_config` + `canonical`
- Réutilisable pour tout domaine correctement déclaré