# Phase 2 Diagnostic: Enhanced Bedrock Normalization

## Modifications Effectuées

### Module `normalizer.py`
- **Ajout paramètre `watch_domains`**: Les fonctions `normalize_item` et `normalize_items_batch` acceptent maintenant les domaines de surveillance
- **Intégration DomainContextBuilder**: Construction automatique des contextes de domaines si `watch_domains` fourni
- **Nouveau champ `domain_relevance`**: Ajouté dans l'item normalisé pour stocker les évaluations de pertinence

### Module `bedrock_client.py`
- **Paramètre `domain_contexts`**: Ajouté à `normalize_item_with_bedrock` et `_build_normalization_prompt`
- **Prompt enrichi**: Le prompt Bedrock inclut maintenant :
  - Section "DOMAINS TO EVALUATE" avec description détaillée de chaque domaine
  - Exemples d'entités par domaine (companies, technologies, molecules, indications)
  - Phrases de contexte métier
  - Tâche d'évaluation pour chaque domaine (is_on_domain, relevance_score, reason)
- **Format JSON étendu**: Le schéma de réponse inclut le champ `domain_relevance`
- **Gestion des fallbacks**: Tous les cas d'erreur retournent un `domain_relevance` vide

## Logique d'Évaluation de Domaines

### Construction du Contexte
Pour chaque domaine dans `watch_domains`:
1. **Description**: Type de domaine + contexte métier + notes client
2. **Exemples d'entités**: 5 exemples max par catégorie (companies, technologies, etc.)
3. **Contexte métier**: Phrases extraites des métadonnées des scopes (ex: "Long-Acting Injectables - requires multiple signal types")

### Prompt Bedrock
Le prompt demande à Bedrock d'évaluer chaque domaine avec:
- **is_on_domain**: Boolean indiquant la pertinence
- **relevance_score**: Score 0.0-1.0 de pertinence
- **reason**: Explication courte (max 2 phrases)

### Instructions Spécifiques
- Évaluation contextuelle, pas seulement matching de mots-clés
- Considération de l'ensemble du contenu de l'article
- Explication obligatoire pour chaque évaluation

## Intégration avec le Pipeline

### Flux de Données
1. **Ingestion**: Items bruts collectés
2. **Normalisation enrichie**: 
   - Extraction d'entités (existant)
   - **NOUVEAU**: Évaluation de pertinence par domaine via Bedrock
3. **Matching**: Utilisation des `domain_relevance` (Phase 3)
4. **Scoring**: Intégration des `relevance_score` (Phase 3)

### Compatibilité
- **Rétrocompatible**: Si `watch_domains` non fourni, fonctionne comme avant
- **Pas d'appel Bedrock supplémentaire**: L'évaluation est intégrée dans l'appel de normalisation existant
- **Générique**: Fonctionne avec tout type de domaine correctement configuré

## Exemple de Sortie

```json
{
  "source_key": "press_corporate__camurus",
  "title": "Camurus Announces Positive Phase 3 Results for Brixadi",
  "summary": "Camurus reported positive results from Phase 3 trial...",
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
    },
    {
      "domain_id": "regulatory_lai", 
      "domain_type": "regulatory",
      "is_on_domain": false,
      "relevance_score": 0.15,
      "reason": "While clinical trial results may lead to regulatory submissions, this article focuses on clinical outcomes rather than regulatory processes."
    }
  ]
}
```

## Risques et Limitations

1. **Taille du prompt**: L'ajout des contextes de domaines augmente la taille du prompt Bedrock
2. **Coût**: Pas d'appel supplémentaire mais prompt plus long = coût légèrement plus élevé
3. **Qualité d'évaluation**: Dépend de la capacité de Bedrock à comprendre les nuances métier
4. **Cohérence**: Les scores peuvent varier entre appels pour le même contenu

## Prochaine Étape

Phase 3: Modification du système de scoring pour utiliser `domain_relevance` comme signal principal au lieu des règles déterministes strictes.