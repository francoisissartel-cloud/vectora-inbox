# Plan de Correction Bedrock pour normalize_score_v2

## Section 1 : Contexte

### Rôle de normalize_score_v2
La Lambda `vectora-inbox-normalize-score-v2` est responsable de :
- Normalisation des items bruts via Bedrock (extraction d'entités, classification d'événements, résumés)
- Matching des items aux domaines de veille du client (technology, regulatory, etc.)
- Scoring de pertinence basé sur les règles métier et les scopes canonical
- Stockage des items normalisés et scorés dans S3 (`curated/` layer)

### Criticité de l'accès Bedrock
L'accès à Bedrock est critique car il permet :
- **Extraction d'entités** : Détection des entreprises, molécules, technologies, trademarks
- **Classification d'événements** : Identification du type d'événement (partnership, clinical_update, etc.)
- **Génération de résumés** : Synthèse intelligente du contenu
- **Évaluation LAI** : Score de pertinence pour les technologies Long-Acting Injectable

Sans Bedrock fonctionnel, la Lambda ne peut pas produire les données structurées nécessaires au workflow V2.

## Section 2 : Analyse Bedrock V1 (ingest-normalize)

### Configuration Bedrock V1 fonctionnelle
**Région** : `us-east-1` (défaut observé dans le code V1)
```python
region = os.environ.get('BEDROCK_REGION', 'us-east-1')
```

**Model ID** : Variable d'environnement `BEDROCK_MODEL_ID`
- Exemple observé : `anthropic.claude-3-sonnet-20240229-v1:0`

**Client Bedrock** :
```python
def get_bedrock_client():
    region = os.environ.get('BEDROCK_REGION', 'us-east-1')
    return boto3.client('bedrock-runtime', region_name=region)
```

**Format d'appel V1** :
```python
request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1000,
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.0
}

response = client.invoke_model(
    modelId=model_id,
    body=json.dumps(request_body)
)
```

**Gestion des erreurs V1** :
- Retry automatique sur `ThrottlingException`
- Backoff exponentiel avec jitter : `base_delay * (2 ** attempt) + random.uniform(0, 0.1)`
- Maximum 3 tentatives par défaut
- Parsing robuste de la réponse JSON

**Prompts V1** :
- Template LAI spécialisé avec focus sur les technologies Long-Acting Injectable
- Exemples d'entités depuis canonical scopes
- Format de réponse JSON structuré avec champs LAI obligatoires

## Section 3 : Analyse Bedrock V2 (normalize_score_v2)

### Configuration Bedrock V2 actuelle
**Région** : `us-east-1` (même que V1)
```python
"BEDROCK_REGION": os.environ.get("BEDROCK_REGION", "us-east-1")
```

**Model ID** : Variable d'environnement `BEDROCK_MODEL_ID` (même que V1)

**Client Bedrock V2** :
```python
def _get_bedrock_client(self):
    return boto3.client('bedrock-runtime', region_name=self.region)
```

### Différences critiques identifiées

**1. Structure de classe vs fonctions**
- V1 : Fonctions simples (`get_bedrock_client()`, `normalize_item_with_bedrock()`)
- V2 : Classe `BedrockNormalizationClient` avec méthodes

**2. Gestion des appels**
- V1 : Fonction `_call_bedrock_with_retry()` éprouvée
- V2 : Méthode `_call_bedrock_with_retry_v1()` qui copie V1 mais peut avoir des différences subtiles

**3. Parsing des réponses**
- V1 : Fonction `_parse_bedrock_response()` avec validation LAI complète
- V2 : Méthodes `_parse_response_with_validation()` et `_validate_lai_fields_v1()`

**4. Construction des prompts**
- V1 : Fonction `_build_normalization_prompt_v1()` avec support canonical + fallback
- V2 : Méthode `_build_prompt_from_canonical()` simplifiée

### Causes probables des erreurs critiques

**1. Différences dans l'initialisation du client**
- V2 utilise une classe avec `self.client` vs V1 qui crée le client à chaque appel
- Possible problème de réutilisation de connexion

**2. Différences dans le format de requête**
- V2 peut avoir des variations subtiles dans le `request_body`
- Possible problème dans la sérialisation JSON

**3. Gestion des erreurs incomplète**
- V2 peut ne pas gérer tous les cas d'erreur de V1
- Possible problème dans la logique de retry

**4. Variables d'environnement manquantes**
- V2 peut ne pas avoir toutes les variables nécessaires configurées dans AWS
- Possible problème de configuration Lambda

## Section 4 : Plan de correction par phases

### Phase 1 : Harmonisation du client Bedrock (30 min)
**Objectif** : Utiliser exactement la même logique de création de client que V1

**Actions** :
1. Remplacer la méthode `_get_bedrock_client()` de V2 par la fonction exacte de V1
2. Modifier l'initialisation pour créer le client à chaque appel (comme V1)
3. Vérifier que la région est bien `us-east-1` par défaut

**Validation** : Test d'import et d'initialisation sans erreur

### Phase 2 : Harmonisation des appels Bedrock (45 min)
**Objectif** : Utiliser exactement la même logique d'appel que V1

**Actions** :
1. Copier intégralement la fonction `_call_bedrock_with_retry()` de V1 vers V2
2. Remplacer la méthode `_call_bedrock_with_retry_v1()` par cette fonction
3. Vérifier le format exact du `request_body` (anthropic_version, max_tokens, messages, temperature)
4. Vérifier la logique de retry sur `ThrottlingException`

**Validation** : Test d'appel Bedrock avec mock ou modèle simple

### Phase 3 : Harmonisation du parsing des réponses (30 min)
**Objectif** : Utiliser exactement la même logique de parsing que V1

**Actions** :
1. Copier intégralement la fonction `_parse_bedrock_response()` de V1 vers V2
2. Vérifier que tous les champs LAI obligatoires sont présents
3. Vérifier la gestion des erreurs JSON (fallback sur structure vide)

**Validation** : Test de parsing avec réponses JSON valides et invalides

### Phase 4 : Harmonisation des prompts (30 min)
**Objectif** : Utiliser les mêmes prompts LAI que V1

**Actions** :
1. Copier la fonction `_build_normalization_prompt_v1()` de V1 vers V2
2. Vérifier le template LAI avec focus sur les technologies Long-Acting Injectable
3. Vérifier les exemples d'entités depuis canonical scopes
4. Vérifier le format de réponse JSON avec champs LAI

**Validation** : Test de génération de prompt avec exemples canonical

### Phase 5 : Tests locaux avec mock Bedrock (45 min)
**Objectif** : Valider le fonctionnement sans coût AWS

**Actions** :
1. Créer un mock Bedrock qui retourne des réponses JSON valides
2. Tester la normalisation d'un item simple
3. Vérifier que tous les champs LAI sont présents dans le résultat
4. Tester la gestion d'erreurs (throttling, JSON invalide)

**Validation** : Normalisation réussie avec structure de données conforme

### Phase 6 : Invocation CLI sur lai_weekly_v3 (30 min)
**Objectif** : Test en conditions réelles avec Bedrock

**Actions** :
1. Déployer la Lambda V2 corrigée sur AWS
2. Invoquer avec l'event `{"client_id": "lai_weekly_v3"}`
3. Utiliser `--cli-binary-format raw-in-base64-out`
4. Vérifier les logs CloudWatch pour les appels Bedrock

**Validation** : Exécution sans erreur Bedrock, items normalisés produits

### Phase 7 : Déploiement AWS (dev) avec profil rag-lai-prod (15 min)
**Objectif** : Déploiement propre en environnement de développement

**Actions** :
1. Utiliser le script de déploiement existant avec les corrections
2. Profil : `--profile rag-lai-prod`
3. Région : `--region eu-west-3`
4. Vérifier les variables d'environnement Lambda (BEDROCK_MODEL_ID, BEDROCK_REGION)

**Validation** : Lambda déployée et accessible via AWS CLI

### Phase 8 : Vérification CloudWatch et diagnostic final (30 min)
**Objectif** : Confirmer le bon fonctionnement en production

**Actions** :
1. Analyser les logs CloudWatch pour les appels Bedrock réussis
2. Vérifier les métriques de latence et d'erreur
3. Tester avec plusieurs items pour confirmer la robustesse
4. Documenter les corrections apportées

**Validation** : Aucune erreur Bedrock, temps de réponse acceptable, items normalisés conformes

## Section 5 : Contraintes / garde-fous

### Ce que je ne dois PAS faire

**❌ Interdictions absolues** :
- Ne PAS créer de nouveaux fichiers YAML de configuration
- Ne PAS ajouter de nouveaux scripts de build à la racine
- Ne PAS polluer `/src_v2/` avec des dépendances tierces
- Ne PAS ajouter de stubs ou hacks autour de PyYAML ou autres libs
- Ne PAS toucher aux autres Lambdas V2 (ingest V2, newsletter V2)
- Ne PAS modifier le comportement métier global (shape des events, logique de scoring, matching)
- Ne PAS créer de nouvelle usine à gaz

**✅ Bonnes pratiques à respecter** :
- Respecter strictement `src_lambda_hygiene_v4.md`
- Maintenir l'architecture clean actuelle de `src_v2/`
- Réutiliser ce qui marche déjà dans V1 sans réinventer
- Garder la logique métier inchangée (normalisation/matching/scoring)
- Utiliser les conventions AWS établies (profil rag-lai-prod, région eu-west-3)
- Documenter les changements dans ce plan

### Validation finale

**Critères de succès** :
- ✅ `normalize_score_v2` fait des appels Bedrock fonctionnels
- ✅ Items normalisés avec structure LAI complète
- ✅ Aucune régression sur les autres fonctionnalités
- ✅ Temps de réponse acceptable (< 30s par item)
- ✅ Gestion robuste des erreurs Bedrock

**Critères d'échec** :
- ❌ Erreurs Bedrock persistantes (ThrottlingException, ModelNotFound, etc.)
- ❌ Réponses Bedrock vides ou mal formatées
- ❌ Régression sur le matching ou scoring
- ❌ Pollution de l'architecture `src_v2/`

---

**Estimation totale** : 4h15 (255 minutes)
**Priorité** : CRITIQUE - Bloque le workflow V2 complet
**Responsable** : Amazon Q Developer en mode maintenance ciblée