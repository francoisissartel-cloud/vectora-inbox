# Plan d'Exécution : Restauration Lambda normalize_score V2

**Date** : 15 janvier 2025  
**Objectif** : Restaurer une lambda normalize_score V2 puissante, efficace et bien architecturée  
**Base** : Diagnostic `normalize_score_v2_dysfunction_analysis.md`  
**Contraintes** : Respect strict `src_lambda_hygiene_v4.md`

---

## 0. Cadrage et Objectifs

### 0.1 Vision Cible
- **Lambda V2 puissante** : Performances égales ou supérieures à V1
- **Architecture propre** : Respect architecture 3 Lambdas V2 + vectora_core
- **Généricité absolue** : Pilotage 100% par client_config + canonical
- **Cohérence workflow** : Intégration parfaite ingest V2 → normalize V2 → newsletter V2

### 0.2 Principes Directeurs
- **Pas de hardcoding** : Toute logique métier dans client_config/canonical
- **Robustesse** : Gestion d'erreurs, retry, fallbacks comme V1
- **Performance** : Parallélisation contrôlée, optimisations Bedrock
- **Testabilité** : Tests sur données réelles, métriques qualité

### 0.3 Contraintes Techniques
- **Architecture V2** : Handler minimal + vectora_core/normalization/
- **Imports relatifs** : `from ..shared import`, `from . import`
- **Environnement AWS** : eu-west-3, profil rag-lai-prod, Bedrock us-east-1
- **Pas de libs tierces** : Lambda Layers uniquement

---

## Phase 1 : Cadrage et Analyse (2h)

### 1.1 Audit Détaillé État Actuel
**Objectif** : Cartographie précise des dysfonctionnements V2

**Actions** :
1. **Analyser modules V2 existants** :
   ```bash
   # Inventaire des fichiers src_v2/vectora_core/normalization/
   ls -la src_v2/vectora_core/normalization/
   # Analyser les imports et dépendances
   grep -r "import" src_v2/vectora_core/normalization/
   ```

2. **Identifier fonctionnalités manquantes** :
   - Comparer ligne par ligne avec modules V1 fonctionnels
   - Lister les méthodes/classes absentes ou incomplètes
   - Documenter les régressions par rapport au diagnostic

3. **Valider configuration disponible** :
   ```bash
   # Vérifier canonical scopes
   ls -la canonical/scopes/
   # Vérifier prompts canoniques
   cat canonical/prompts/global_prompts.yaml
   # Vérifier client config LAI
   cat client-config-examples/lai_weekly_v3.yaml
   ```

**Livrables** :
- `docs/design/normalize_v2_gap_analysis.md` : Liste précise des gaps V1→V2
- Validation que tous les inputs nécessaires sont disponibles

### 1.2 Définition Architecture Cible
**Objectif** : Spécifier l'architecture V2 restaurée

**Structure cible** :
```
src_v2/vectora_core/normalization/
├── __init__.py                 # run_normalize_score_for_client()
├── bedrock_client.py          # Client robuste avec retry V1
├── normalizer.py              # Normalisation batch + prompts canoniques
├── matcher.py                 # Matching sophistiqué + domain_relevance
├── scorer.py                  # Scoring LAI complet + bonus métier
└── data_manager.py            # Gestion dernier run + I/O S3
```

**Interfaces définies** :
- Signature `run_normalize_score_for_client()` compatible handler
- Contrats entre modules (normalizer → matcher → scorer)
- Format de sortie conforme contrat normalize_score_v2.md

---

## Phase 2 : Implémentation Core (8h)

### 2.1 Client Bedrock Robuste (2h)
**Objectif** : Restaurer client Bedrock V1 avec améliorations V2

**Fichier** : `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonctionnalités à implémenter** :
```python
class BedrockNormalizationClient:
    def __init__(self, model_id: str, region: str = "us-east-1"):
        # Configuration client boto3 avec région
        
    def normalize_item(self, item_text: str, canonical_examples: Dict, 
                      domain_contexts: List = None) -> Dict[str, Any]:
        # ✅ Retry automatique avec backoff exponentiel (3 tentatives)
        # ✅ Gestion ThrottlingException spécifique
        # ✅ Prompts canoniques depuis global_prompts.yaml
        # ✅ Parsing robuste avec validation champs LAI
        # ✅ Logging détaillé des appels et latences
        
    def _build_prompt_from_canonical(self, item_text: str, examples: Dict) -> str:
        # ✅ Utilisation template depuis canonical/prompts/global_prompts.yaml
        # ✅ Substitution placeholders {{item_text}}, {{companies_examples}}
        # ✅ Fallback vers prompt hardcodé si canonical indisponible
```

**Champs LAI obligatoires** :
- `lai_relevance_score` (0-10)
- `anti_lai_detected` (boolean)
- `pure_player_context` (boolean)
- `domain_relevance` (array)

### 2.2 Normalisation Batch Optimisée (2h)
**Objectif** : Normalisation parallélisée avec gestion d'erreurs

**Fichier** : `src_v2/vectora_core/normalization/normalizer.py`

**Fonctionnalités à implémenter** :
```python
def normalize_items_batch(raw_items: List[Dict], canonical_scopes: Dict,
                         canonical_prompts: Dict, bedrock_model: str,
                         bedrock_region: str, max_workers: int = 1) -> List[Dict]:
    # ✅ Parallélisation contrôlée (ThreadPoolExecutor)
    # ✅ Préparation exemples depuis canonical_scopes
    # ✅ Gestion d'erreurs par item (continue si échec)
    # ✅ Statistiques détaillées (success/failed/total)
    # ✅ Enrichissement items avec normalized_content
    
def _prepare_canonical_examples(canonical_scopes: Dict) -> Dict[str, str]:
    # ✅ Extraction exemples depuis scopes LAI
    # ✅ Limitation taille pour éviter surcharge prompts
    # ✅ Priorité scopes MVP (lai_companies_mvp_core, lai_keywords)
```

### 2.3 Matching Sophistiqué (2h)
**Objectif** : Matching multi-critères avec privilèges trademarks

**Fichier** : `src_v2/vectora_core/normalization/matcher.py`

**Fonctionnalités à implémenter** :
```python
def match_items_to_domains(normalized_items: List[Dict], client_config: Dict,
                          canonical_scopes: Dict) -> List[Dict]:
    # ✅ Matching par watch_domains depuis client_config
    # ✅ Privilèges trademarks avec boost_factor
    # ✅ Règles par type de domaine (technology vs regulatory)
    # ✅ Évaluation domain_relevance avec scores et raisons
    
def _evaluate_domain_relevance(item: Dict, domain_config: Dict,
                              canonical_scopes: Dict) -> Dict:
    # ✅ Calcul score de pertinence par domaine
    # ✅ Détection entités matchées (companies, molecules, technologies)
    # ✅ Génération raisons explicites
    # ✅ Application règles require_entity_signals, min_technology_signals
```

### 2.4 Scoring Métier Complet (2h)
**Objectif** : Scoring LAI avec bonus et règles métier

**Fichier** : `src_v2/vectora_core/normalization/scorer.py`

**Fonctionnalités à implémenter** :
```python
def score_items(matched_items: List[Dict], client_config: Dict,
               canonical_scopes: Dict, scoring_mode: str = "balanced",
               target_date: str = None) -> List[Dict]:
    # ✅ Score de base par type d'événement
    # ✅ Bonus pure players LAI (5.0)
    # ✅ Bonus trademarks LAI (4.0)
    # ✅ Bonus molécules et technologies
    # ✅ Facteurs de récence
    # ✅ Application seuils de sélection
    
def _calculate_entity_bonuses(item: Dict, client_config: Dict,
                             canonical_scopes: Dict) -> Dict:
    # ✅ Bonus par scope d'entités détectées
    # ✅ Gestion scopes multiples (pure_players, hybrid, global)
    # ✅ Calcul bonus cumulatifs avec plafonnement
```

---

## Phase 3 : Orchestration et Intégration (3h)

### 3.1 Fonction Orchestratrice (1h)
**Objectif** : Pipeline complet normalize → match → score

**Fichier** : `src_v2/vectora_core/normalization/__init__.py`

**Implémentation** :
```python
def run_normalize_score_for_client(client_id: str, env_vars: Dict,
                                  period_days: Optional[int] = None,
                                  force_reprocess: bool = False,
                                  **kwargs) -> Dict[str, Any]:
    # 1. Chargement configurations (client_config + canonical)
    # 2. Identification dernier run d'ingestion
    # 3. Chargement items ingérés
    # 4. Normalisation batch via Bedrock
    # 5. Matching aux domaines de veille
    # 6. Scoring de pertinence
    # 7. Écriture résultats S3 curated/
    # 8. Retour statistiques détaillées
```

### 3.2 Gestionnaire de Données (1h)
**Objectif** : Gestion robuste dernier run + I/O S3

**Fichier** : `src_v2/vectora_core/normalization/data_manager.py`

**Fonctionnalités** :
```python
def find_last_ingestion_run(client_id: str, data_bucket: str) -> Optional[str]:
    # ✅ Listing préfixes S3 ingested/{client_id}/
    # ✅ Parsing et tri dates YYYY/MM/DD
    # ✅ Validation existence items.json
    # ✅ Gestion cas multiples runs même jour
    
def load_ingested_items(data_bucket: str, run_path: str) -> List[Dict]:
    # ✅ Chargement items.json depuis S3
    # ✅ Validation format et champs obligatoires
    # ✅ Gestion d'erreurs avec messages explicites
    
def save_curated_items(data_bucket: str, client_id: str, 
                      items: List[Dict], run_date: str) -> str:
    # ✅ Écriture S3 curated/{client_id}/{YYYY}/{MM}/{DD}/items.json
    # ✅ Format conforme contrat normalize_score_v2.md
```

### 3.3 Handler Lambda Finalisé (1h)
**Objectif** : Handler minimal conforme règles hygiène V4

**Fichier** : `src_v2/lambdas/normalize_score/handler.py`

**Validation complète** :
- Event parsing et validation
- Variables d'environnement requises
- Gestion d'erreurs avec codes HTTP appropriés
- Logging structuré
- Délégation totale à vectora_core

---

## Phase 4 : Tests Locaux sur Données Réelles (4h)

### 4.1 Préparation Environnement de Test (1h)
**Objectif** : Setup environnement local avec données réelles

**Actions** :
1. **Configuration AWS locale** :
   ```bash
   # Profil rag-lai-prod configuré
   aws configure list --profile rag-lai-prod
   # Accès buckets dev validé
   aws s3 ls s3://vectora-inbox-config-dev/ --profile rag-lai-prod
   aws s3 ls s3://vectora-inbox-data-dev/ --profile rag-lai-prod
   ```

2. **Données de test réelles** :
   ```bash
   # Téléchargement dernier run LAI weekly v3
   aws s3 cp s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/ \
       tests/fixtures/real_data/ --recursive --profile rag-lai-prod
   ```

3. **Script de test local** :
   ```python
   # scripts/test_normalize_score_v2_local.py
   # Simulation complète avec données réelles
   # Comparaison résultats V1 vs V2
   ```

### 4.2 Tests Unitaires par Module (1h)
**Objectif** : Validation fonctionnelle de chaque module

**Tests à implémenter** :
```python
# tests/unit/test_bedrock_client_v2.py
def test_normalize_item_with_retry():
    # Test retry automatique sur ThrottlingException
    
def test_canonical_prompts_loading():
    # Test chargement prompts depuis global_prompts.yaml
    
# tests/unit/test_matcher_v2.py  
def test_trademark_privileges():
    # Test boost_factor trademarks LAI
    
def test_domain_relevance_scoring():
    # Test calcul scores par domaine
    
# tests/unit/test_scorer_v2.py
def test_lai_bonuses():
    # Test bonus pure players (5.0) et trademarks (4.0)
```

### 4.3 Tests d'Intégration End-to-End (2h)
**Objectif** : Validation pipeline complet sur données réelles

**Scénarios de test** :
1. **Test nominal LAI weekly v3** :
   - Input : Dernier run ingested/lai_weekly_v3/
   - Process : Pipeline complet normalize → match → score
   - Output : Validation format curated/ + métriques

2. **Test gestion d'erreurs** :
   - Simulation échecs Bedrock (throttling, timeout)
   - Validation fallbacks et retry
   - Vérification statistiques d'erreurs

3. **Test performance** :
   - Mesure temps de traitement par item
   - Validation parallélisation
   - Comparaison latences V1 vs V2

**Métriques attendues** :
- **Taux de succès** : >95% normalisation Bedrock
- **Performance** : <2s par item en moyenne
- **Qualité** : Scores LAI cohérents avec attentes métier

---

## Phase 5 : Validation Qualité et Métriques (3h)

### 5.1 Métriques de Qualité Fonctionnelle (1h)
**Objectif** : Validation qualité métier des résultats

**Métriques à mesurer** :
```python
# Qualité normalisation Bedrock
bedrock_success_rate = successful_calls / total_calls
avg_lai_relevance_score = mean([item['lai_relevance_score'] for item in results])
entities_detection_rate = items_with_entities / total_items

# Qualité matching
domain_matching_rate = items_matched / total_items  
trademark_boost_effectiveness = avg_score_with_trademarks / avg_score_without

# Qualité scoring
score_distribution = histogram([item['final_score'] for item in results])
bonus_application_rate = items_with_bonuses / total_items
```

**Seuils de validation** :
- Taux succès Bedrock : >95%
- Taux matching domaines : >80% pour items LAI
- Score LAI moyen : >15 pour pure players
- Bonus trademarks appliqués : >90% quand détectés

### 5.2 Métriques de Performance Technique (1h)
**Objectif** : Validation performance et robustesse

**Métriques à mesurer** :
```python
# Performance Bedrock
avg_bedrock_latency_ms = mean([call['duration'] for call in bedrock_calls])
bedrock_throttling_rate = throttled_calls / total_calls
retry_success_rate = successful_retries / failed_first_attempts

# Performance globale
total_processing_time_s = end_time - start_time
items_per_second = total_items / total_processing_time_s
memory_usage_mb = max_memory_usage
```

**Seuils de validation** :
- Latence Bedrock moyenne : <3s par item
- Taux throttling : <5%
- Débit global : >0.5 items/seconde
- Utilisation mémoire : <512MB

### 5.3 Comparaison V1 vs V2 (1h)
**Objectif** : Validation non-régression vs V1

**Comparaisons à effectuer** :
1. **Qualité des entités détectées** :
   - Précision/rappel companies LAI
   - Détection trademarks spécialisés
   - Classification événements

2. **Cohérence des scores** :
   - Corrélation scores V1 vs V2 sur mêmes items
   - Validation bonus LAI appliqués
   - Respect seuils de sélection

3. **Performance relative** :
   - Temps de traitement V1 vs V2
   - Consommation ressources
   - Robustesse aux erreurs

**Critères de succès** :
- Corrélation scores V1/V2 : >0.85
- Performance V2 : ±20% de V1
- Qualité entités : égale ou supérieure à V1

---

## Phase 6 : Préparation Déploiement AWS (2h)

### 6.1 Packaging et Layers (1h)
**Objectif** : Préparation artefacts de déploiement

**Actions** :
1. **Packaging Lambda** :
   ```bash
   # Script packaging conforme règles hygiène V4
   cd scripts/
   python package_normalize_score_v2.py
   # Validation taille <50MB, pas de libs tierces
   ```

2. **Validation layers** :
   ```bash
   # Vérification layer vectora-core
   # Vérification layer common-deps
   # Test import depuis handler
   ```

3. **Variables d'environnement** :
   ```yaml
   # Configuration pour déploiement dev
   ENV: dev
   CONFIG_BUCKET: vectora-inbox-config-dev
   DATA_BUCKET: vectora-inbox-data-dev
   BEDROCK_MODEL_ID: eu.anthropic.claude-sonnet-4-5-20250929-v1:0
   BEDROCK_REGION: us-east-1
   ```

### 6.2 Tests de Déploiement (1h)
**Objectif** : Validation déploiement et configuration AWS

**Actions** :
1. **Déploiement dev** :
   ```bash
   # Déploiement stack CloudFormation
   aws cloudformation deploy --template-file infra/s1-normalize-score-v2.yaml \
       --stack-name vectora-inbox-normalize-score-v2-dev \
       --profile rag-lai-prod --region eu-west-3
   ```

2. **Test invocation AWS** :
   ```bash
   # Test avec event minimal
   aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
       --payload '{"client_id": "lai_weekly_v3"}' \
       --profile rag-lai-prod --region eu-west-3 response.json
   ```

3. **Validation logs CloudWatch** :
   ```bash
   # Vérification logs détaillés
   aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
       --profile rag-lai-prod --region eu-west-3
   ```

**Critères de succès déploiement** :
- Lambda déployée sans erreur
- Invocation test réussie
- Logs structurés et détaillés
- Métriques CloudWatch disponibles

---

## Phase 7 : Validation Production et Documentation (1h)

### 7.1 Tests de Charge (30min)
**Objectif** : Validation comportement sous charge

**Scénarios** :
- 50 items simultanés (batch normal)
- 100 items simultanés (pic de charge)
- Gestion throttling Bedrock
- Récupération après erreurs

### 7.2 Documentation Finale (30min)
**Objectif** : Documentation complète pour maintenance

**Livrables** :
- `docs/design/normalize_score_v2_final_architecture.md`
- `docs/guides/normalize_score_v2_operations.md`
- Mise à jour `contracts/lambdas/normalize_score_v2.md`

---

## Critères de Succès Global

### Fonctionnels
- ✅ **Normalisation robuste** : >95% succès Bedrock avec retry
- ✅ **Matching sophistiqué** : Privilèges trademarks + domain_relevance
- ✅ **Scoring LAI complet** : Bonus métier + seuils configurables
- ✅ **Généricité absolue** : Pilotage 100% par client_config/canonical

### Techniques  
- ✅ **Architecture V2 propre** : Respect règles hygiène V4
- ✅ **Performance** : ≥V1 en vitesse et robustesse
- ✅ **Intégration** : Compatible workflow ingest V2 → newsletter V2
- ✅ **Déployabilité** : Packaging et déploiement AWS automatisés

### Qualité
- ✅ **Tests complets** : Unitaires + intégration + données réelles
- ✅ **Métriques** : Qualité fonctionnelle + performance technique
- ✅ **Documentation** : Architecture + opérations + maintenance

---

## Planning Estimé

| Phase | Durée | Dépendances | Livrables |
|-------|-------|-------------|-----------|
| 1. Cadrage | 2h | - | Gap analysis, architecture cible |
| 2. Implémentation | 8h | Phase 1 | Modules core fonctionnels |
| 3. Orchestration | 3h | Phase 2 | Pipeline complet |
| 4. Tests locaux | 4h | Phase 3 | Validation données réelles |
| 5. Métriques | 3h | Phase 4 | Validation qualité/performance |
| 6. Déploiement | 2h | Phase 5 | Artefacts AWS prêts |
| 7. Production | 1h | Phase 6 | Documentation finale |

**Total estimé** : 23h sur 3-4 jours

---

## Conclusion

Ce plan d'exécution restaure une lambda normalize_score V2 **puissante et bien architecturée** en :

1. **Préservant l'architecture V2** (séparation des responsabilités)
2. **Restaurant la logique métier V1** (normalisation, matching, scoring)
3. **Respectant les règles d'hygiène V4** (généricité, imports, environnement)
4. **Assurant la cohérence workflow** (intégration ingest V2 → newsletter V2)

L'approche **test-driven avec données réelles** garantit la qualité fonctionnelle, tandis que les **métriques détaillées** assurent la performance et la robustesse.

Q Developer dispose de toutes les informations nécessaires pour exécuter ce plan de manière **autonome et méthodique**.