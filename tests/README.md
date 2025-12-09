# Tests Vectora Inbox

Ce répertoire contient les tests unitaires et d'intégration pour Vectora Inbox.

## Structure

```
tests/
├── unit/                           # Tests unitaires
│   ├── test_bedrock_retry.py      # Tests du mécanisme de retry Bedrock
│   └── ...
├── events/                         # Événements de test pour les Lambdas
│   └── test-ingest-small-batch.json
└── README.md
```

## Tests unitaires

### Test du mécanisme de retry Bedrock

**Fichier** : `unit/test_bedrock_retry.py`

**Objectif** : Valider que le wrapper `_call_bedrock_with_retry()` gère correctement les ThrottlingException avec backoff exponentiel.

**Exécution** :

```powershell
# Depuis la racine du projet
python -m pytest tests/unit/test_bedrock_retry.py -v

# Ou avec unittest
python -m unittest tests.unit.test_bedrock_retry
```

**Scénarios testés** :
- ✅ Retry réussi après une ThrottlingException
- ✅ Échec après épuisement des retries (max_retries atteint)
- ✅ Pas de retry sur erreur non-throttling (ValidationException, etc.)
- ✅ Succès dès la première tentative

**Résultat attendu** :
```
test_no_retry_on_non_throttling_error ... ok
test_retry_exhausted_after_max_retries ... ok
test_retry_on_throttling_success_on_second_attempt ... ok
test_success_on_first_attempt ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.XXXs

OK
```

## Tests d'intégration

### Test de la Lambda ingest-normalize avec petit batch

**Événement** : `events/test-ingest-small-batch.json`

**Description** : Teste l'ingestion et la normalisation sur un petit échantillon de 2 sources presse (FierceBiotech, FiercePharma) sur 1 jour.

**Exécution locale** (si environnement configuré) :

```powershell
# Depuis la racine du projet
python -c "
import json
import sys
sys.path.insert(0, 'src')
from lambdas.ingest_normalize.handler import lambda_handler

with open('tests/events/test-ingest-small-batch.json') as f:
    event = json.load(f)

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
```

**Exécution sur AWS** :

```powershell
aws lambda invoke `
  --function-name vectora-inbox-ingest-normalize-dev `
  --payload file://tests/events/test-ingest-small-batch.json `
  --cli-binary-format raw-in-base64-out `
  out-test-small-batch.json `
  --profile rag-lai-prod `
  --region eu-west-3

# Afficher le résultat
type out-test-small-batch.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Résultat attendu** :
- `statusCode: 200`
- `sources_processed: 2`
- `items_ingested: 10-50` (selon le contenu RSS du jour)
- `items_normalized: 10-50` (même nombre que items_ingested)
- Logs CloudWatch montrant les retries Bedrock si throttling

## Monitoring des retries Bedrock

### Logs CloudWatch à surveiller

**Logs de retry** (niveau WARNING) :
```
ThrottlingException détectée (tentative 1/4). Retry dans 0.52s...
ThrottlingException détectée (tentative 2/4). Retry dans 1.03s...
```

**Logs d'échec final** (niveau ERROR) :
```
ThrottlingException - Échec après 4 tentatives. Abandon de l'appel Bedrock.
Erreur finale lors de l'appel à Bedrock après tous les retries: ...
```

**Commande pour consulter les logs** :

```powershell
aws logs tail /aws/lambda/vectora-inbox-ingest-normalize-dev `
  --since 10m `
  --filter-pattern "Throttling" `
  --profile rag-lai-prod `
  --region eu-west-3
```

### Métriques à surveiller

**Taux de retry** :
- Compter les logs WARNING avec "ThrottlingException détectée"
- Objectif : <20% des appels Bedrock

**Taux d'échec final** :
- Compter les logs ERROR avec "Échec après X tentatives"
- Objectif : <5% des appels Bedrock

**Temps d'exécution Lambda** :
- Augmentation = signe de throttling et retries
- Objectif : <5 minutes pour 100 items

## Ajustement des paramètres

### Augmenter la parallélisation

Si les quotas Bedrock sont suffisants et le taux de throttling <5%, vous pouvez augmenter `MAX_BEDROCK_WORKERS` :

**Fichier** : `src/vectora_core/normalization/normalizer.py`

```python
# Valeur actuelle (conservatrice)
MAX_BEDROCK_WORKERS = 4

# Valeur plus agressive (si quotas suffisants)
MAX_BEDROCK_WORKERS = 8
```

### Augmenter le nombre de retries

Si le taux d'échec final est >5%, vous pouvez augmenter `max_retries` :

**Fichier** : `src/vectora_core/normalization/bedrock_client.py`

```python
# Dans normalize_item_with_bedrock()
response_text = _call_bedrock_with_retry(
    model_id, 
    request_body,
    max_retries=5  # Au lieu de 3
)
```

### Ajuster le délai de base

Si les retries sont trop rapides et échouent systématiquement, augmenter `base_delay` :

```python
response_text = _call_bedrock_with_retry(
    model_id, 
    request_body,
    base_delay=1.0  # Au lieu de 0.5
)
```

## Prochaines étapes

1. **Exécuter les tests unitaires** pour valider le mécanisme de retry
2. **Tester sur AWS** avec l'événement `test-ingest-small-batch.json`
3. **Analyser les logs CloudWatch** pour mesurer le taux de retry et d'échec
4. **Ajuster les paramètres** si nécessaire (MAX_BEDROCK_WORKERS, max_retries)
5. **Tester avec un batch complet** (7 jours, toutes les sources)
6. **Monitorer les coûts** Bedrock pendant 1 semaine

## Ressources

- **Documentation Bedrock** : [AWS Bedrock Throttling](https://docs.aws.amazon.com/bedrock/latest/userguide/quotas.html)
- **Diagnostic complet** : `docs/diagnostics/bedrock_sonnet45_success_final_dev.md`
- **CHANGELOG** : `CHANGELOG.md` (section "Résilience Bedrock")
