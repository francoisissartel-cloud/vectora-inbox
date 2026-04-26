
# Plan d'implémentation : Lambda normalize-score-matching-v2

## Phase 0 – Préambule & rappel des contraintes

### Résumé du contrat métier normalize_score_v2

- **Rôle** : Normalisation intelligente des items bruts ingérés + scoring de pertinence pour préparer la génération de newsletter
- **Inputs** : Items ingérés depuis S3 `ingested/` (outputs de ingest V2)
- **Outputs** : Items normalisés + scorés dans S3 `curated/` pour consommation par newsletter V2
- **Traitement** : Normalisation Bedrock (entités, classification) + matching aux domaines + scoring selon règles métier
- **Contrainte clé** : Traiter UNIQUEMENT le dernier run d'ingestion par client, pas tout l'historique

### Règles d'hygiène V4 applicables

- **Architecture 3 Lambdas V2** : Handler minimal dans `/src_v2/lambdas/normalize_score/`, logique dans `vectora_core/normalization/`
- **Généricité absolue** : Pilotage par `client_config + canonical`, aucune logique hardcodée spécifique à un client
- **Environnement AWS** : Région `eu-west-3`, profil `rag-lai-prod`, Bedrock `us-east-1` par défaut
- **Dépendances** : Lambda Layers uniquement, aucune lib tierce dans `/src_v2/`
- **Imports relatifs** : `from ..shared import`, `from . import` dans vectora_core

### Objectifs principaux

- **Dernier run uniquement** : Stratégie robuste pour identifier et traiter le dernier run d'ingestion par client
- **Préparation newsletter** : Structure de sortie optimisée pour consommation par Lambda newsletter V2
- **Générique** : Aucun couplage dur à un client spécifique, pilotage par configuration
- **Pas usine à gaz** : Code simple, testable, maintenable sans sur-architecture

---

## Phase 1 – Audit de l'existant

### Analyse structure /src_v2/

**État actuel observé** :
- Structure 3 Lambdas V2 validée : `ingest/`, `normalize_score/`, `newsletter/`
- Handler normalize_score existant mais minimal (délégation à vectora_core)
- Modules vectora_core organisés : `shared/`, `ingest/`, `normalization/`, `newsletter/`
- Conformité règles d'hygiène V4 : aucune violation détectée

**Modules vectora_core disponibles** :
- `shared/` : config_loader, s3_io, models, utils (réutilisables)
- `normalization/` : structure existante mais à compléter pour V2

### Analyse Lambda ingest V2 et ses outputs

**Contrat ingest V2 analysé** :
- **Outputs S3** : `s3://vectora-inbox-data/ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json`
- **Structure items** : item_id, source_key, title, content, url, published_at, ingested_at, metadata
- **Convention runs** : Un run = un dossier par date d'ingestion (YYYY/MM/DD)
- **Dernier run** : Dossier avec la date la plus récente pour un client donné

**Shape exacte des items ingérés** (depuis contrat ingest_v2.md) :
```json
{
  "item_id": "press_corporate__medincell_20250115_001",
  "source_key": "press_corporate__medincell", 
  "title": "MedinCell Announces Partnership...",
  "content": "Full article text...",
  "url": "https://...",
  "published_at": "2025-01-15",
  "ingested_at": "2025-01-15T10:30:00Z",
  "metadata": {"author": "...", "tags": [...], "word_count": 450}
}
```

### Analyse canonical & client_config

**Scopes canonical disponibles** :
- `company_scopes.yaml` : 180+ entreprises LAI (pure_players, hybrid, global)
- `molecule_scopes.yaml` : 90+ molécules par indication
- `technology_scopes.yaml` : 80+ mots-clés LAI
- `trademark_scopes.yaml` : 70+ marques commerciales
- `exclusion_scopes.yaml` : Termes de filtrage du bruit

**Client_config lai_weekly_v3 analysé** :
- 2 domaines de veille : `tech_lai_ecosystem`, `regulatory_lai`
- Règles matching : `trademark_privileges`, `require_entity_signals`
- Règles scoring : Bonus pure players (5.0), trademarks (4.0), partnerships (8.0)
- Seuils sélection : min_score 12, max_items_total 15

**Prompts Bedrock disponibles** :
- `global_prompts.yaml` : Prompt normalisation LAI avec extraction entités, classification événements
- Template avec placeholders : `{{item_text}}`, `{{companies_examples}}`, etc.

### Résultat Phase 1

**Entrées disponibles identifiées** :
- Items ingérés structurés avec métadonnées complètes
- Configuration client complète pour matching et scoring
- Scopes canonical exhaustifs pour LAI
- Prompts Bedrock prêts pour normalisation

**Stratégie dernier run** :
- Convention S3 : `ingested/{client_id}/{YYYY}/{MM}/{DD}/`
- Identification : Lister les préfixes, trier par date, prendre le plus récent
- Robustesse : Gestion des cas multiples runs même jour via timestamp

---

## Phase 2 – Conception fonctionnelle & technique

### Signature du handler

**Handler standardisé** :
```python
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # Event minimal : {"client_id": "lai_weekly"}
    # Event complet : {"client_id": "lai_weekly", "period_days": 7, "force_reprocess": false}
```

**Variables d'environnement requises** :
- `CONFIG_BUCKET` : vectora-inbox-config-dev
- `DATA_BUCKET` : vectora-inbox-data-dev  
- `BEDROCK_MODEL_ID` : eu.anthropic.claude-sonnet-4-5-20250929-v1:0
- `BEDROCK_REGION_NORMALIZATION` : us-east-1 (défaut observé)

### Stratégie identification dernier run

**Méthode robuste proposée** :
1. **Lister les préfixes S3** : `s3://data-bucket/ingested/{client_id}/`
2. **Parser les dates** : Extraire YYYY/MM/DD de chaque préfixe
3. **Trier par date décroissante** : Utiliser datetime pour comparaison
4. **Prendre le plus récent** : Premier élément après tri
5. **Vérifier existence fichier** : `items.json` présent dans le dossier

**Gestion cas limites** :
- Aucun run trouvé : Erreur explicite "Aucune donnée ingérée pour ce client"
- Multiples runs même jour : Prendre le dernier par timestamp de modification S3
- Fichier items.json manquant : Erreur explicite avec chemin attendu

### Structure entrée/sortie

**S3 Input** : `s3://vectora-inbox-data/ingested/{client_id}/{YYYY}/{MM}/{DD}/items.json`

**S3 Output** : `s3://vectora-inbox-data/curated/{client_id}/{YYYY}/{MM}/{DD}/items.json`

**Shape JSON sortie** (selon contrat normalize_score_v2.md) :
```json
{
  "item_id": "...",
  "source_key": "...", 
  "title": "...",
  "content": "...",
  "url": "...",
  "published_at": "...",
  "normalized_at": "2025-01-15T11:45:00Z",
  
  "normalized_content": {
    "summary": "...",
    "entities": {"companies": [...], "molecules": [...], "technologies": [...], "trademarks": [...]},
    "event_classification": {"primary_type": "partnership", "confidence": 0.92}
  },
  
  "matching_results": {
    "matched_domains": ["tech_lai_ecosystem"],
    "domain_relevance": {"tech_lai_ecosystem": {"score": 0.89, "reasons": [...]}}
  },
  
  "scoring_results": {
    "base_score": 8.5,
    "bonuses": {"pure_player_company": 5.0, "trademark_mention": 4.0},
    "final_score": 20.0
  }
}
```

### Découpage du code

**Handler minimal** : `/src_v2/lambdas/normalize_score/handler.py`
- Validation event, lecture env vars, appel `run_normalize_score_for_client()`

**Logique métier** : `vectora_core/normalization/`
- `__init__.py` : Fonction orchestratrice `run_normalize_score_for_client()`
- `normalizer.py` : Appels Bedrock pour extraction entités + classification
- `matcher.py` : Matching items aux domaines de veille client
- `scorer.py` : Calcul scores selon règles métier + bonus/malus
- `bedrock_client.py` : Client Bedrock spécialisé avec retry et gestion erreurs

**Modules partagés réutilisés** :
- `vectora_core/shared/config_loader.py` : Chargement client_config + canonical
- `vectora_core/shared/s3_io.py` : Lecture/écriture S3 standardisée
- `vectora_core/shared/utils.py` : Utilitaires dates, logging, etc.

### Interactions Bedrock

**Module dédié** : `vectora_core/normalization/bedrock_client.py`
- Classe `BedrockNormalizationClient` avec configuration région/modèle
- Méthode `normalize_item()` : Appel Bedrock avec prompt canonical
- Gestion retry automatique (3 tentatives)
- Gestion timeouts (30s par appel)
- Logging détaillé des appels et erreurs

---

## Phase 3 – Plan d'implémentation dans /src_v2

### Fichiers à créer/modifier

**Handler Lambda** :
- `src_v2/lambdas/normalize_score/handler.py` : **MODIFIER** (structure existante à compléter)
- Rôle : Validation event, lecture env vars, appel fonction orchestratrice
- Dépendances : `from vectora_core.normalization import run_normalize_score_for_client`

**Modules vectora_core/normalization/** :
- `__init__.py` : **MODIFIER** (ajouter fonction orchestratrice complète)
- `normalizer.py` : **CRÉER** (logique normalisation Bedrock)
- `matcher.py` : **CRÉER** (matching aux domaines de veille)
- `scorer.py` : **CRÉER** (calcul scores selon règles métier)
- `bedrock_client.py` : **CRÉER** (client Bedrock spécialisé)

**Modules vectora_core/shared/** :
- Réutilisation modules existants : config_loader, s3_io, utils, models
- Pas de modification prévue (API stable)

**Tests et fixtures** :
- `scripts/test_normalize_score_v2_local.py` : **CRÉER** (tests locaux)
- `tests/fixtures/lai_weekly_ingested_sample.json` : **CRÉER** (données test)

### Points d'attention règles d'hygiène

**Éviter usine à gaz** :
- Fonctions pures pour normalisation, matching, scoring
- Pas de cascade de classes inutiles
- Logique métier simple et testable

**Généricité** :
- Aucun `if client_id == 'lai_weekly'` dans le code
- Toute logique métier pilotée par client_config + canonical
- Paramètres configurables via event ou variables d'environnement

**Imports relatifs corrects** :
```python
# Dans vectora_core/normalization/__init__.py
from ..shared import config_loader, s3_io, utils
from . import normalizer, matcher, scorer, bedrock_client

# Dans vectora_core/normalization/normalizer.py  
from ..shared.models import NormalizedItem
from .bedrock_client import BedrockNormalizationClient
```

---

## Phase 4 – Plan de tests locaux

### Génération fixtures

**Récupération données réelles** :
- Script `scripts/extract_lai_weekly_last_run.py` pour télécharger dernier run lai_weekly_v3
- Anonymisation si nécessaire (URLs, emails)
- Stockage dans `tests/fixtures/lai_weekly_ingested_sample.json`

**Fixtures synthétiques** :
- 5-10 items représentatifs : partnerships, clinical updates, regulatory
- Couverture entités : MedinCell, Camurus, BEPO, Aristada, etc.
- Cas limites : items sans entités LAI, contenu très court/long

### Script de test local

**Script principal** : `scripts/test_normalize_score_v2_local.py`

**Fonctionnalités** :
- Chargement fixtures locales (pas de S3)
- Mock ou appel réel Bedrock (paramètre `--mock-bedrock`)
- Simulation complète du workflow normalize-score
- Génération fichier output local `output/normalized_items.json`
- Validation structure JSON de sortie

**Tests du flux complet** :
1. **Chargement config** : client_config + canonical depuis fichiers locaux
2. **Normalisation** : Appel Bedrock (réel ou mock) pour extraction entités
3. **Matching** : Application règles matching aux domaines de veille
4. **Scoring** : Calcul scores avec bonus/malus selon règles métier
5. **Validation** : Vérification présence champs obligatoires

### Checks qualité

**Métriques de base** :
- Nombre items traités vs nombre items en entrée (100% attendu)
- Présence champs obligatoires : normalized_content, matching_results, scoring_results
- Distribution scores : min, max, moyenne, médiane

**Gestion erreurs Bedrock** :
- Simulation timeout : Mock avec délai > 30s
- Simulation rate limit : Mock avec erreur 429
- Simulation réponse vide : Mock avec JSON invalide
- Vérification retry automatique (3 tentatives)

**Validation contenu** :
- Entités extraites cohérentes avec texte source
- Scores dans plages attendues (0-50 typique)
- Matching domaines conforme aux scopes configurés

---

## Phase 5 – Plan de métriques & audit qualité

### Métriques loguées

**Statistiques traitement** :
- `items_input_count` : Nombre items en entrée
- `items_normalized_count` : Nombre items normalisés avec succès
- `items_matched_count` : Nombre items matchés à au moins un domaine
- `items_scored_count` : Nombre items avec score final
- `items_rejected_count` : Nombre items rejetés (avec raisons)

**Métriques Bedrock** :
- `bedrock_calls_total` : Nombre total d'appels Bedrock
- `bedrock_calls_success` : Nombre d'appels réussis
- `bedrock_calls_retry` : Nombre de retry effectués
- `bedrock_calls_failed` : Nombre d'échecs définitifs
- `bedrock_latency_avg` : Latence moyenne par appel (ms)

**Distribution scores** :
- `scores_min`, `scores_max`, `scores_avg`, `scores_median`
- `scores_distribution` : Histogramme par tranches (0-5, 5-10, 10-15, 15+)
- `high_score_items_count` : Nombre items score > seuil client

### Protocole audit manuel

**Échantillon représentatif** :
- 10 items par tranche de score (bas, moyen, élevé)
- 5 items par type d'événement (partnership, clinical, regulatory)
- 3 items par source principale (MedinCell, Camurus, FierceBiotech)

**Checklist qualitative** :
1. **Cohérence entités** : Entités extraites présentes dans le texte source ?
2. **Pertinence classification** : Type d'événement correct ?
3. **Matching logique** : Domaines matchés justifiés par les entités ?
4. **Scoring cohérent** : Score final reflète la pertinence perçue ?
5. **Bruit filtré** : Items non-LAI correctement exclus ?

**Métriques qualité** :
- Taux de cohérence entités : % items avec entités justifiées
- Taux de classification correcte : % items avec event_type pertinent  
- Taux de matching logique : % items avec domaines justifiés
- Taux de faux positifs : % items non-LAI avec score élevé

### Logging et agrégation

**CloudWatch Logs** :
- Logs structurés JSON avec métriques par item
- Niveau INFO pour statistiques globales
- Niveau DEBUG pour détails Bedrock et scoring

**Métriques CloudWatch** (futur) :
- Métriques custom pour dashboard : items/min, erreurs Bedrock, scores moyens
- Alarmes sur taux d'erreur > 10% ou latence > 60s

---

## Phase 6 – Plan de déploiement AWS (profil rag-lai-prod)

### Analyse méthode déploiement actuelle

**Méthode observée pour ingest V2** :
- CloudFormation stack : `vectora-inbox-s1-runtime-dev`
- Template : `infra/s1-ingest-v2.yaml`
- Déploiement via CLI : `aws cloudformation deploy --profile rag-lai-prod --region eu-west-3`
- Code Lambda : Upload S3 puis update-function-code

**Ressources existantes réutilisables** :
- Buckets S3 : vectora-inbox-config-dev, vectora-inbox-data-dev
- Rôles IAM : vectora-inbox-lambda-execution-role-dev
- Lambda Layers : vectora-core-layer, common-deps-layer (si existants)

### Intégration normalize-score-v2

**Nouveau template CloudFormation** : `infra/s1-normalize-score-v2.yaml`

**Ressources à créer** :
```yaml
VectoraInboxNormalizeScoreV2:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: vectora-inbox-normalize-score-v2-dev
    Runtime: python3.11
    Handler: handler.lambda_handler
    Code:
      S3Bucket: vectora-inbox-lambda-code-dev
      S3Key: normalize-score-v2.zip
    Environment:
      Variables:
        ENV: dev
        CONFIG_BUCKET: vectora-inbox-config-dev
        DATA_BUCKET: vectora-inbox-data-dev
        BEDROCK_MODEL_ID: eu.anthropic.claude-sonnet-4-5-20250929-v1:0
        BEDROCK_REGION_NORMALIZATION: us-east-1
    Layers:
      - !Ref VectoraCoreLayer
      - !Ref CommonDepsLayer
```

**Variables d'environnement** :
- `ENV` : dev (environnement de déploiement)
- `CONFIG_BUCKET` : vectora-inbox-config-dev
- `DATA_BUCKET` : vectora-inbox-data-dev  
- `BEDROCK_MODEL_ID` : eu.anthropic.claude-sonnet-4-5-20250929-v1:0
- `BEDROCK_REGION_NORMALIZATION` : us-east-1

**Permissions IAM requises** :
- S3 : GetObject sur config-bucket, GetObject/PutObject sur data-bucket
- Bedrock : InvokeModel sur modèles Claude dans us-east-1
- CloudWatch : CreateLogGroup, CreateLogStream, PutLogEvents

### Commandes de déploiement

**Packaging Lambda** :
```bash
cd src_v2/lambdas/normalize_score
zip -r ../../../normalize-score-v2.zip . -x "*.pyc" "__pycache__/*"
aws s3 cp normalize-score-v2.zip s3://vectora-inbox-lambda-code-dev/ --profile rag-lai-prod --region eu-west-3
```

**Déploiement stack** :
```bash
aws cloudformation deploy \
  --template-file infra/s1-normalize-score-v2.yaml \
  --stack-name vectora-inbox-s1-normalize-score-v2-dev \
  --capabilities CAPABILITY_IAM \
  --profile rag-lai-prod \
  --region eu-west-3
```

**Test post-déploiement** :
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --payload '{"client_id": "lai_weekly"}' \
  --profile rag-lai-prod \
  --region eu-west-3 \
  response.json
```

### Liaison future EventBridge

**Trigger automatique** (à implémenter plus tard) :
- EventBridge rule sur événement "Ingestion Completed" de ingest V2
- Target : normalize-score-v2 avec transformation event
- Pattern : `{"source": ["vectora.inbox"], "detail-type": ["Ingestion Completed"]}`

---

## Phase 7 – Critères de succès & risques

### Critères de succès

**Déploiement** :
- ✅ Lambda déployable sans violation règles d'hygiène V4
- ✅ Aucune dépendance tierce dans /src_v2/
- ✅ Handler < 5MB, utilisation layers pour vectora_core
- ✅ Variables d'environnement correctement configurées

**Fonctionnel** :
- ✅ Traitement correct dernier run lai_weekly_v3 (identification automatique)
- ✅ Normalisation Bedrock : extraction entités + classification événements
- ✅ Matching domaines : application règles client_config
- ✅ Scoring : calcul avec bonus/malus selon canonical
- ✅ Output S3 : structure JSON conforme contrat newsletter V2

**Qualité** :
- ✅ Logs et métriques suffisants pour évaluer performance
- ✅ Gestion erreurs Bedrock robuste (retry, timeout)
- ✅ Code maintenable : fonctions pures, tests locaux
- ✅ Généricité : aucun couplage dur lai_weekly

### Principaux risques

**Identification dernier run** :
- 🔴 **Risque** : Logique fragile si convention S3 change
- 🟡 **Mitigation** : Tests avec multiples structures, gestion cas limites
- 🟢 **Fallback** : Paramètre event pour forcer date spécifique

**Coût/latence Bedrock** :
- 🔴 **Risque** : Coût élevé si volume important (100+ items/run)
- 🟡 **Mitigation** : Monitoring coûts, optimisation prompts
- 🟢 **Fallback** : Paramètre pour limiter nombre items traités

**Complexité code** :
- 🔴 **Risque** : Sur-architecture si logique trop complexe
- 🟡 **Mitigation** : Revue code, privilégier simplicité
- 🟢 **Fallback** : Refactoring si nécessaire en Phase 2

**Dépendance canonical** :
- 🔴 **Risque** : Couplage fort aux détails scopes LAI
- 🟡 **Mitigation** : API stable config_loader, tests avec fixtures
- 🟢 **Fallback** : Graceful degradation si scopes manquants

**Performance Bedrock** :
- 🔴 **Risque** : Timeouts fréquents ou rate limiting
- 🟡 **Mitigation** : Retry exponentiel, monitoring latence
- 🟢 **Fallback** : Mode dégradé sans normalisation Bedrock

---

## Résumé exécutif

Ce plan d'implémentation respecte strictement les contraintes V4 et l'architecture 3 Lambdas V2. La stratégie d'identification du dernier run est robuste et basée sur les conventions S3 existantes. Le code sera générique, piloté par configuration, et maintiendra la simplicité requise. Les tests locaux et métriques permettront de valider la qualité avant déploiement AWS.

**Prochaine étape** : Validation de ce plan puis implémentation Phase 3 (création des modules vectora_core/normalization/).