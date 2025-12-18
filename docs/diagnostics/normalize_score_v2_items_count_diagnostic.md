# Diagnostic : Écart entre items ingérés réels vs items traités en test local

## Problème identifié

**Observation** : Les tests locaux de normalize-score-v2 ne traitent que **3 items** alors que le dernier run réel d'ingest V2 pour `lai_weekly_v3` contient **15 items**.

**Impact** : Sous-estimation de la charge de traitement réelle et validation incomplète du workflow.

---

## Investigation des données réelles

### Dernier run d'ingestion réel (2025-12-16)
- **Localisation S3** : `s3://vectora-inbox-data-dev/ingested/lai_weekly_v3/2025/12/16/items.json`
- **Taille fichier** : 12,860 octets
- **Nombre d'items** : **15 items**
- **Sources représentées** :
  - `press_corporate__nanexa` : 6 items
  - `press_corporate__medincell` : 8 items  
  - `press_corporate__delsitech` : 1 item

### Analyse qualitative des items réels

**Items de haute qualité LAI** :
1. **Nanexa + Moderna** : "license and option agreement for PharmaShell®-based products" (USD 3M upfront, USD 500M milestones)
2. **MedinCell + Teva** : "Olanzapine Extended-Release Injectable Suspension NDA submission to FDA"
3. **UZEDY expansion** : "FDA Approves Expanded Indication for UZEDY® for Bipolar I Disorder"

**Items de qualité moyenne/faible** :
- Rapports financiers trimestriels (contenu minimal)
- Liens "Download attachment" (contenu vide)
- Annonces événements/conférences

**Problèmes de qualité observés** :
- **Doublons** : Même item_id pour contenus différents (ex: `press_corporate__nanexa_20251216_6f822c`)
- **Contenu tronqué** : Beaucoup d'items avec <50 mots
- **Métadonnées pauvres** : Tags vides, authors manquants

---

## Cause racine du problème

### 1. **Fixtures de test trop limitées**

**Test local actuel** :
```python
def create_sample_fixtures() -> List[Dict[str, Any]]:
    return [
        # Seulement 3 items synthétiques optimaux
        {"item_id": "medincell_partnership", ...},
        {"item_id": "camurus_clinical", ...}, 
        {"item_id": "delsitech_regulatory", ...}
    ]
```

**Problème** : Les fixtures ne représentent pas :
- Le volume réel (15 items vs 3)
- La diversité qualitative (items excellents + moyens + faibles)
- Les problèmes de données réelles (doublons, contenu tronqué)

### 2. **Mock S3 simplifié**

**Mock actuel** :
```python
def mock_read_items(bucket: str, key: str) -> List[Dict[str, Any]]:
    if "items.json" in key:
        return create_sample_fixtures()  # Toujours les mêmes 3 items
```

**Problème** : Le mock ne simule pas la lecture des données réelles depuis S3.

### 3. **Absence de tests avec données réelles**

Le script de test n'a pas d'option pour utiliser les vraies données S3 au lieu des mocks.

---

## Impact sur la validation

### Sous-estimation des performances
- **Temps Bedrock** : 3 appels vs 15 appels réels (5x plus)
- **Coût** : Estimation incorrecte des coûts Bedrock
- **Latence** : 842ms pour 3 items vs ~4-5s pour 15 items

### Validation incomplète du matching/scoring
- **Cas limites non testés** : Items avec contenu minimal, doublons
- **Distribution scores** : Pas de validation sur items de qualité variable
- **Filtrage exclusions** : Non testé sur vrais cas de bruit

### Problèmes de qualité non détectés
- **Gestion doublons** : Pas de déduplication implémentée
- **Contenu minimal** : Pas de filtrage sur word_count
- **Métadonnées manquantes** : Pas de validation robustesse

---

## Recommandations d'amélioration

### 1. **Fixtures réalistes** (Priorité HAUTE)

**Action** : Créer des fixtures basées sur les vraies données
```python
def create_realistic_fixtures() -> List[Dict[str, Any]]:
    # Mélange de 15 items : 5 excellents + 5 moyens + 5 faibles
    # Inclure cas problématiques : doublons, contenu court, métadonnées vides
```

**Bénéfices** :
- Tests plus représentatifs du volume réel
- Validation des cas limites
- Estimation correcte des performances

### 2. **Mode test avec données réelles** (Priorité HAUTE)

**Action** : Ajouter option `--use-real-data` au script de test
```python
def run_test(client_id: str, use_real_data: bool = False):
    if use_real_data:
        # Pas de mock S3, utiliser vraies données
        setup_real_aws_environment()
    else:
        # Mocks comme actuellement
        mock_s3_operations()
```

**Bénéfices** :
- Validation end-to-end avec vraies données
- Détection problèmes de qualité réels
- Tests de performance réalistes

### 3. **Amélioration qualité données** (Priorité MOYENNE)

**Action** : Ajouter filtres de qualité dans normalize-score-v2
```python
def filter_low_quality_items(items):
    # Filtrer items avec word_count < 20
    # Déduplication sur content_hash
    # Validation métadonnées minimales
```

**Bénéfices** :
- Réduction du bruit dans les résultats
- Optimisation coûts Bedrock
- Amélioration qualité newsletter

### 4. **Tests de charge** (Priorité MOYENNE)

**Action** : Créer fixtures de test avec 50-100 items
```python
def create_load_test_fixtures() -> List[Dict[str, Any]]:
    # Simulation d'un gros run d'ingestion
    # Test limites timeout Lambda (15min)
    # Test limites mémoire (1GB)
```

**Bénéfices** :
- Validation scalabilité
- Optimisation configuration Lambda
- Détection goulots d'étranglement

---

## Plan d'action immédiat

### Phase 1 : Correction fixtures (1-2h)
1. **Télécharger vraies données** : Utiliser le fichier `real_ingested_items.json` déjà récupéré
2. **Créer fixtures réalistes** : Sélectionner 15 items représentatifs
3. **Mettre à jour script test** : Remplacer `create_sample_fixtures()`

### Phase 2 : Mode données réelles (2-3h)
1. **Ajouter option CLI** : `--use-real-data` dans le script de test
2. **Implémenter mode réel** : Désactiver mocks S3 conditionnellement
3. **Tester end-to-end** : Validation avec vraies données AWS

### Phase 3 : Amélioration qualité (3-4h)
1. **Ajouter filtres qualité** : Dans `normalizer.py` avant appels Bedrock
2. **Déduplication** : Basée sur `content_hash` ou similarité contenu
3. **Métriques qualité** : Logging items filtrés avec raisons

### Phase 4 : Tests de charge (optionnel)
1. **Fixtures volumineuses** : 50-100 items synthétiques
2. **Tests performance** : Mesure temps/mémoire avec gros volumes
3. **Optimisation** : Batch processing si nécessaire

---

## Critères de succès

### Validation corrigée
- ✅ Tests locaux avec 15 items (volume réel)
- ✅ Temps traitement réaliste (4-5s vs 842ms)
- ✅ Validation cas limites (contenu court, doublons)
- ✅ Tests end-to-end avec vraies données S3

### Qualité améliorée
- ✅ Filtrage items de faible qualité (word_count < 20)
- ✅ Déduplication automatique
- ✅ Métriques qualité loguées

### Performance validée
- ✅ Traitement 15 items < 15min (limite Lambda)
- ✅ Mémoire < 1GB (limite Lambda)
- ✅ Coût Bedrock estimé correctement

---

## Conclusion

Le problème identifié est **critique** car il fausse complètement la validation du système. Les tests actuels avec 3 items synthétiques ne représentent ni le volume réel (15 items) ni la complexité des données (qualité variable, doublons, contenu minimal).

**Action prioritaire** : Corriger immédiatement les fixtures de test pour utiliser des données réalistes et ajouter un mode de test avec les vraies données S3.

**Impact estimé** : 
- Temps de traitement réel : ~5x plus long (4-5s vs 842ms)
- Coût Bedrock : ~5x plus élevé (15 appels vs 3)
- Qualité résultats : Amélioration significative avec filtrage

Cette correction est **indispensable** avant le déploiement en production.