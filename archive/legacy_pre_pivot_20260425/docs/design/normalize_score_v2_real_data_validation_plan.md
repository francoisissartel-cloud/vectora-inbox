# Plan de validation : Lambda normalize-score-v2 avec données réelles

## Objectif

Valider la qualité, performance et scalabilité de la Lambda normalize-score-v2 avec les **vraies données d'ingestion** (15 items réels vs 3 fixtures synthétiques) pour décider du déploiement AWS.

## Contexte du problème

**Diagnostic identifié** : Les tests actuels utilisent 3 fixtures synthétiques optimales alors que les runs réels contiennent 15 items de qualité variable avec des problèmes (doublons, contenu tronqué, métadonnées vides).

**Impact** : Sous-estimation critique des performances, coûts et qualité réelle du système.

---

## Phase 1 – Correction des fixtures de test (1-2h)

### Objectif
Remplacer les 3 fixtures synthétiques par les 15 items réels du dernier run d'ingestion.

### Actions

#### 1.1 Extraction des données réelles
- ✅ **Déjà fait** : Fichier `output/real_ingested_items.json` téléchargé (15 items du 2025-12-16)
- **Analyser la qualité** : Identifier items excellents/moyens/faibles
- **Documenter les problèmes** : Doublons, contenu court, métadonnées manquantes

#### 1.2 Création de fixtures réalistes
```python
# Modifier scripts/test_normalize_score_v2_local.py
def create_realistic_fixtures() -> List[Dict[str, Any]]:
    """Charge les 15 vrais items du dernier run d'ingestion."""
    fixtures_file = Path(__file__).parent.parent / "output" / "real_ingested_items.json"
    with open(fixtures_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_sample_fixtures() -> List[Dict[str, Any]]:
    # Remplacer par create_realistic_fixtures()
    return create_realistic_fixtures()
```

#### 1.3 Test avec fixtures réalistes
- **Exécuter** : `python scripts/test_normalize_score_v2_local.py --client-id lai_weekly_v3`
- **Mesurer** : Temps traitement, nombre d'appels Bedrock, distribution scores
- **Comparer** : Résultats vs test précédent (3 items)

### Critères de succès Phase 1
- ✅ 15 items traités (vs 3 précédemment)
- ✅ Temps traitement réaliste (4-5s vs 842ms)
- ✅ Tous les items normalisés sans erreur
- ✅ Distribution scores cohérente

---

## Phase 2 – Mode test avec données réelles S3 (2-3h)

### Objectif
Ajouter un mode de test qui utilise directement les données S3 sans mocks pour validation end-to-end.

### Actions

#### 2.1 Extension du script de test
```python
# Ajouter dans scripts/test_normalize_score_v2_local.py
def setup_real_aws_environment():
    """Configure l'environnement pour utiliser les vraies données S3."""
    os.environ.update({
        'AWS_PROFILE': 'rag-lai-prod',
        'AWS_REGION': 'eu-west-3'
    })

def run_test(client_id: str = "lai_weekly_v3", use_real_data: bool = False, mock_bedrock: bool = True):
    if use_real_data:
        logger.info("Mode données réelles S3 activé")
        setup_real_aws_environment()
        # Pas de mock S3, utiliser vraies opérations
    else:
        logger.info("Mode fixtures locales")
        mock_s3_operations()
    
    if mock_bedrock:
        mock_bedrock_operations()
```

#### 2.2 Nouvelle option CLI
```bash
# Test avec fixtures réalistes (local)
python scripts/test_normalize_score_v2_local.py --client-id lai_weekly_v3

# Test avec vraies données S3 + mock Bedrock
python scripts/test_normalize_score_v2_local.py --client-id lai_weekly_v3 --use-real-data

# Test end-to-end complet (S3 + Bedrock réels)
python scripts/test_normalize_score_v2_local.py --client-id lai_weekly_v3 --use-real-data --no-mock-bedrock
```

#### 2.3 Validation end-to-end
- **Test S3 + Mock Bedrock** : Validation lecture/écriture S3 réelles
- **Test S3 + Bedrock réels** : Validation complète avec vrais appels Bedrock
- **Mesure coûts** : Estimation coût Bedrock réel (15 appels)

### Critères de succès Phase 2
- ✅ Lecture automatique dernier run S3 (2025-12-16)
- ✅ Écriture résultats dans S3 `curated/`
- ✅ Appels Bedrock réels fonctionnels
- ✅ Coût Bedrock mesuré et acceptable

---

## Phase 3 – Analyse qualité et performance (2-3h)

### Objectif
Évaluer la qualité des résultats, identifier les problèmes et mesurer les performances réelles.

### Actions

#### 3.1 Analyse qualité des résultats
```python
# Nouveau script : scripts/analyze_normalize_results.py
def analyze_normalization_quality(results_file: str):
    """Analyse la qualité des résultats de normalisation."""
    
    # Métriques de base
    - Taux de normalisation réussie (items avec entités extraites)
    - Distribution des types d'événements détectés
    - Couverture des entités (companies, molecules, technologies, trademarks)
    
    # Métriques de matching
    - Taux de matching aux domaines (tech_lai_ecosystem, regulatory_lai)
    - Pertinence des matches (cohérence entités <-> domaines)
    - Items exclus et raisons
    
    # Métriques de scoring
    - Distribution des scores finaux (min, max, moyenne, médiane)
    - Cohérence scores vs qualité perçue
    - Impact des bonus/malus
```

#### 3.2 Détection des problèmes qualité
- **Doublons** : Items avec même content_hash ou similarité élevée
- **Contenu minimal** : Items avec word_count < 20
- **Entités manquées** : Items LAI sans entités détectées
- **Faux positifs** : Items non-LAI avec scores élevés

#### 3.3 Mesure des performances
```python
# Métriques à collecter
performance_metrics = {
    "total_processing_time": "Temps total de traitement",
    "bedrock_calls_count": "Nombre d'appels Bedrock",
    "bedrock_avg_latency": "Latence moyenne Bedrock",
    "bedrock_total_cost": "Coût total estimé Bedrock",
    "memory_usage_peak": "Pic d'utilisation mémoire",
    "items_per_second": "Débit de traitement"
}
```

### Critères de succès Phase 3
- ✅ Taux normalisation > 90% (13+ items sur 15)
- ✅ Taux matching > 80% (12+ items matchés)
- ✅ Distribution scores cohérente (items excellents > scores élevés)
- ✅ Temps traitement < 5min (limite raisonnable)
- ✅ Coût Bedrock < $0.50 par run

---

## Phase 4 – Amélioration qualité (optionnel, 2-4h)

### Objectif
Si Phase 3 révèle des problèmes qualité, implémenter les corrections nécessaires.

### Actions conditionnelles

#### 4.1 Filtrage qualité des items
```python
# Dans vectora_core/normalization/normalizer.py
def filter_low_quality_items(items: List[Dict]) -> List[Dict]:
    """Filtre les items de faible qualité avant normalisation."""
    
    filtered_items = []
    for item in items:
        # Filtrer contenu trop court
        word_count = item.get('metadata', {}).get('word_count', 0)
        if word_count < 20:
            logger.debug(f"Item filtré (contenu court): {item['item_id']}")
            continue
            
        # Filtrer titres génériques
        title = item.get('title', '').lower()
        if title in ['download attachment', 'read more']:
            logger.debug(f"Item filtré (titre générique): {item['item_id']}")
            continue
            
        filtered_items.append(item)
    
    return filtered_items
```

#### 4.2 Déduplication intelligente
```python
def deduplicate_items(items: List[Dict]) -> List[Dict]:
    """Supprime les doublons basés sur content_hash et similarité."""
    
    seen_hashes = set()
    deduplicated = []
    
    for item in items:
        content_hash = item.get('content_hash')
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            deduplicated.append(item)
        else:
            logger.debug(f"Doublon détecté: {item['item_id']}")
    
    return deduplicated
```

#### 4.3 Amélioration prompts Bedrock
- **Analyse des échecs** : Items mal normalisés
- **Optimisation prompts** : Ajout d'exemples spécifiques
- **Validation améliorée** : Vérification cohérence entités extraites

### Critères de succès Phase 4
- ✅ Réduction du bruit (items filtrés documentés)
- ✅ Amélioration taux de matching (+10%)
- ✅ Cohérence scores améliorée
- ✅ Coût Bedrock optimisé (moins d'appels inutiles)

---

## Phase 5 – Tests de charge et scalabilité (optionnel, 2-3h)

### Objectif
Valider la scalabilité avec des volumes plus importants pour anticiper la croissance.

### Actions

#### 5.1 Création de fixtures volumineuses
```python
def create_load_test_fixtures(target_count: int = 50) -> List[Dict]:
    """Génère des fixtures de test de charge."""
    
    # Base : 15 vrais items
    real_items = create_realistic_fixtures()
    
    # Duplication avec variations
    load_items = []
    for i in range(target_count):
        base_item = real_items[i % len(real_items)].copy()
        base_item['item_id'] = f"{base_item['item_id']}_load_{i}"
        base_item['ingested_at'] = datetime.now().isoformat() + "Z"
        load_items.append(base_item)
    
    return load_items
```

#### 5.2 Tests de performance
- **50 items** : Simulation d'un gros run d'ingestion
- **100 items** : Test des limites Lambda (timeout 15min, mémoire 1GB)
- **Mesures** : Temps, mémoire, coût, taux d'erreur

#### 5.3 Optimisations si nécessaire
- **Batch processing** : Traitement par lots pour réduire latence
- **Parallélisation** : Appels Bedrock concurrents (avec rate limiting)
- **Cache** : Éviter re-normalisation items identiques

### Critères de succès Phase 5
- ✅ 50 items traités < 10min
- ✅ 100 items traités < 15min (limite Lambda)
- ✅ Mémoire < 1GB
- ✅ Taux d'erreur < 5%

---

## Phase 6 – Décision de déploiement

### Critères de validation globale

#### ✅ **Qualité acceptable**
- Taux normalisation > 90%
- Taux matching > 80%
- Distribution scores cohérente
- Problèmes qualité identifiés et corrigés

#### ✅ **Performance acceptable**
- Traitement 15 items < 5min
- Coût Bedrock < $0.50 par run
- Scalabilité validée jusqu'à 50-100 items

#### ✅ **Robustesse validée**
- Gestion erreurs Bedrock
- Filtrage qualité des données
- Déduplication fonctionnelle

### Décisions possibles

#### **Scénario A : Déploiement immédiat**
Si tous les critères sont atteints :
1. **Packaging** : `python scripts/package_normalize_score_v2.py`
2. **Déploiement** : CloudFormation avec template existant
3. **Tests AWS** : Validation post-déploiement

#### **Scénario B : Améliorations nécessaires**
Si des problèmes critiques sont détectés :
1. **Plan d'amélioration** : Corrections prioritaires identifiées
2. **Nouvelle itération** : Phases 4-5 avec corrections
3. **Re-validation** : Tests complets après corrections

#### **Scénario C : Refactoring majeur**
Si des problèmes architecturaux sont détectés :
1. **Analyse d'impact** : Évaluation des changements nécessaires
2. **Plan de refactoring** : Modifications structurelles
3. **Nouvelle implémentation** : Cycle complet de développement

---

## Livrables attendus

### Rapports d'analyse
1. **`normalize_score_v2_real_data_quality_report.md`** : Analyse qualité détaillée
2. **`normalize_score_v2_performance_report.md`** : Métriques de performance
3. **`normalize_score_v2_deployment_decision.md`** : Recommandation finale

### Artefacts techniques
1. **Scripts de test améliorés** : Mode données réelles
2. **Fixtures réalistes** : 15 vrais items + fixtures de charge
3. **Métriques de qualité** : Dashboard d'analyse des résultats

### Décision finale
- **GO/NO-GO déploiement** avec justification détaillée
- **Plan d'amélioration** si corrections nécessaires
- **Estimation coûts** et performance en production

---

## Planning d'exécution

### Jour 1 (4-6h)
- **Phase 1** : Correction fixtures (1-2h)
- **Phase 2** : Mode données réelles (2-3h)
- **Phase 3** : Analyse qualité (2-3h)

### Jour 2 (optionnel, 4-6h)
- **Phase 4** : Améliorations qualité (2-4h)
- **Phase 5** : Tests de charge (2-3h)
- **Phase 6** : Décision finale (1h)

**Objectif** : Décision de déploiement dans 1-2 jours maximum avec validation complète sur données réelles.