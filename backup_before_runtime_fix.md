# Backup État Actuel - Avant Corrections Runtime

**Date** : 2025-12-12  
**Objectif** : Sauvegarder l'état actuel avant les corrections du matching/scoring  

## Fichiers Sources Actuels

### Fichiers Critiques à Modifier
- `src/vectora_core/normalization/bedrock_client.py` : Prompt Bedrock
- `src/vectora_core/normalization/normalizer.py` : Parsing normalisation
- `src/vectora_core/ingestion/html_extractor_robust.py` : Extraction HTML
- `src/vectora_core/matching/matcher.py` : Matching contextuel

### État des Métriques Baseline
- Items avec technologies : 0/104 (0.0%)
- Items gold matchés : 0/4
- Items avec matched_domains : 5/104 (4.8%)
- Newsletter LAI authentique : 0%

### Configuration AWS Actuelle
- Région Bedrock : us-east-1
- Modèle : us.anthropic.claude-sonnet-4-5-20250929-v1:0
- Lambdas : vectora-inbox-ingest-normalize-dev, vectora-inbox-engine-dev

## Point de Restauration Créé

Ce fichier sert de point de référence pour restaurer l'état actuel si nécessaire.