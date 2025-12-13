# Phase 1 Diagnostic: Domain Context Builder

## Modifications Effectuées

### Nouveau Module: `domain_context_builder.py`
- **Localisation**: `src/vectora_core/normalization/domain_context_builder.py`
- **Fonction**: Construit des représentations compactes des domaines clients pour injection dans les prompts Bedrock

### Fonctionnalités Implémentées

1. **Classe DomainContext**: Structure de données pour représenter un domaine
   - `domain_id`, `domain_type`, `priority`
   - `description`: Description contextuelle du domaine
   - `example_entities`: Exemples d'entités par catégorie (companies, technologies, molecules, indications)
   - `context_phrases`: Phrases de contexte métier

2. **Classe DomainContextBuilder**: Constructeur de contextes
   - Analyse `client_config.watch_domains`
   - Extrait des exemples d'entités depuis les scopes canoniques
   - Gère les scopes technologiques complexes (ex: `lai_keywords` avec catégories)
   - Construit des descriptions concises pour chaque domaine

### Logique de Construction

1. **Extraction d'Entités**:
   - Companies: 10 exemples max depuis `company_scopes`
   - Molecules: 8 exemples max depuis `molecule_scopes`
   - Technologies: 12 exemples max avec priorité aux `core_phrases` et `technology_terms_high_precision`
   - Indications: 8 exemples max depuis `indication_scopes`

2. **Gestion des Scopes Technologiques Complexes**:
   - Priorité aux `core_phrases` (6 exemples)
   - Puis `technology_terms_high_precision` (4 exemples)
   - Puis `interval_patterns` (2 exemples)
   - Extraction du contexte depuis `_metadata.description`

3. **Construction de Descriptions**:
   - Description de base selon le type de domaine
   - Ajout du contexte d'entités clés
   - Intégration des notes du client_config

## Intégration avec le Pipeline

Le module s'intègre dans la normalisation via:
1. Chargement des scopes canoniques (existant)
2. Construction des contextes de domaines
3. Injection dans le prompt Bedrock enrichi (Phase 2)

## Généricité

- Aucune logique LAI codée en dur
- Fonctionne avec tout domaine correctement déclaré dans `client_config.watch_domains`
- Extensible pour nouveaux types de scopes (trademarks, etc.)

## Risques et Limitations

1. **Dépendance aux Scopes**: Si un scope référencé n'existe pas, le domaine sera construit avec moins de contexte
2. **Taille du Contexte**: Les exemples sont limités pour éviter de surcharger le prompt Bedrock
3. **Complexité des Scopes**: Seuls les scopes technologiques complexes sont gérés spécifiquement

## Prochaine Étape

Phase 2: Enrichissement du prompt Bedrock pour intégrer ces contextes de domaines et générer les évaluations `domain_relevance`.