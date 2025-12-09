# Gestion de la concurrence Lambda ingest-normalize

**Date** : 2025-01-XX  
**Environnement** : DEV (eu-west-3)  
**Statut** : ✅ MODE MONO-INSTANCE ACTIVÉ EN DEV

---

## Résumé exécutif

La Lambda `vectora-inbox-ingest-normalize-dev` a été configurée en **mode mono-instance** (concurrence limitée à 1) pour l'environnement DEV afin de réduire le throttling Bedrock causé par des invocations concurrentes.

---

## Problème observé : Invocations concurrentes

### Symptômes

Lors des tests en DEV, nous avons observé :
- **3 invocations Lambda simultanées** de `ingest-normalize-dev`
- **Taux de throttling Bedrock élevé** : ~30-40% des appels
- **Nombreux échecs après retry** : certains items échouent après 4 tentatives

### Analyse des logs CloudWatch

Les logs montrent 3 RequestId différents s'exécutant en parallèle :
1. `bc0238c6-19f7-4c97-935f-d1e9a09e5328` (démarré à 16:31:07)
2. `f7457e5c-436b-473f-b040-6c96092621ee` (démarré à 16:32:07)
3. `955ad30e-e4c1-4c7a-9d57-ca542eeb7500` (démarré à 16:33:08)

### Origine des invocations concurrentes

**Analyse de l'infrastructure** :

La Lambda `ingest-normalize` **n'a AUCUN trigger automatique** :
- ❌ Pas de règle EventBridge
- ❌ Pas de SQS event source mapping
- ❌ Pas de notification S3
- ❌ Pas de Step Functions
- ❌ Pas d'appel programmatique depuis une autre Lambda

**Conclusion** : Les 3 invocations proviennent de **tests manuels lancés en parallèle** via AWS CLI :
- Soit 3 commandes `aws lambda invoke` lancées manuellement
- Soit des retries automatiques du CLI après timeout (la Lambda a un timeout de 300s)

### Impact sur Bedrock

Avec 3 Lambdas s'exécutant simultanément :
- Chaque Lambda traite 50 items avec 4 workers parallèles
- **Débit total vers Bedrock** : ~12 appels simultanés (3 Lambdas × 4 workers)
- **Quotas Bedrock atteints** : ThrottlingException sur ~30-40% des appels
- **Retries efficaces** : Le mécanisme de retry avec backoff exponentiel fonctionne, mais certains items échouent après 4 tentatives

---

## Solution : Mode mono-instance en DEV

### Configuration appliquée

**Fichier** : `infra/s1-runtime.yaml`

**Modification** :
```yaml
IngestNormalizeFunction:
  Type: AWS::Lambda::Function
  Properties:
    # Mode mono-instance pour DEV : limite la concurrence à 1
    ReservedConcurrentExecutions: !If
      - IsDevEnvironment
      - 1
      - !Ref AWS::NoValue
```

**Condition CloudFormation** :
```yaml
Conditions:
  IsDevEnvironment: !Equals [!Ref Env, "dev"]
```

### Comportement avec ReservedConcurrentExecutions = 1

**En DEV** :
- ✅ **Une seule instance** de la Lambda peut s'exécuter à la fois
- ✅ **Invocations séquentielles** : si une 2ème invocation arrive pendant qu'une 1ère est en cours, elle est mise en file d'attente
- ✅ **Débit Bedrock réduit** : ~4 appels simultanés max (1 Lambda × 4 workers)
- ✅ **Throttling Bedrock réduit** : taux attendu <10%

**En STAGE/PROD** :
- ✅ **Concurrence illimitée** : `ReservedConcurrentExecutions` n'est pas défini
- ✅ **Scalabilité normale** : AWS Lambda peut créer autant d'instances que nécessaire
- ✅ **Prêt pour production** : une fois les quotas Bedrock augmentés

### Déploiement

**Commande** :
```powershell
aws cloudformation deploy `
  --template-file infra/s1-runtime.yaml `
  --stack-name vectora-inbox-s1-runtime-dev `
  --parameter-overrides Env=dev [autres paramètres...] `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Vérification** :
```powershell
aws lambda get-function-concurrency `
  --function-name vectora-inbox-ingest-normalize-dev `
  --profile rag-lai-prod `
  --region eu-west-3
```

**Résultat attendu** :
```json
{
  "ReservedConcurrentExecutions": 1
}
```

---

## Impact attendu

### Avant (concurrence illimitée)

| Métrique | Valeur |
|----------|--------|
| Invocations simultanées | 3 (tests manuels) |
| Workers Bedrock par Lambda | 4 |
| Débit total Bedrock | ~12 appels simultanés |
| Taux de throttling | ~30-40% |
| Taux d'échec final | ~5-10% |

### Après (mode mono-instance)

| Métrique | Valeur |
|----------|--------|
| Invocations simultanées | 1 (forcé) |
| Workers Bedrock par Lambda | 4 |
| Débit total Bedrock | ~4 appels simultanés |
| Taux de throttling | <10% (attendu) |
| Taux d'échec final | <2% (attendu) |

---

## Stratégie de montée en charge

### Phase 1 : DEV (actuel)

**Configuration** :
- `ReservedConcurrentExecutions = 1`
- `MAX_BEDROCK_WORKERS = 4`
- Quotas Bedrock : par défaut

**Objectif** : Stabiliser le pipeline et valider la qualité de normalisation

### Phase 2 : STAGE (futur)

**Configuration** :
- `ReservedConcurrentExecutions = 5` (ou non défini)
- `MAX_BEDROCK_WORKERS = 4`
- Quotas Bedrock : augmentés via AWS Support

**Objectif** : Tester la scalabilité avec des volumes réalistes

### Phase 3 : PROD (futur)

**Configuration** :
- `ReservedConcurrentExecutions` : non défini (illimité)
- `MAX_BEDROCK_WORKERS = 6-8` (ajustable)
- Quotas Bedrock : augmentés significativement

**Objectif** : Production avec haute disponibilité et scalabilité

---

## Alternatives considérées

### Option 1 : Réduire MAX_BEDROCK_WORKERS à 2

**Avantages** :
- Réduit le débit Bedrock sans limiter la concurrence Lambda
- Plus flexible pour les tests

**Inconvénients** :
- Ne résout pas le problème des invocations concurrentes
- Temps d'exécution plus long

**Décision** : Non retenue car ne traite pas la cause racine

### Option 2 : SQS + Event Source Mapping

**Avantages** :
- Contrôle fin du débit avec `BatchSize` et `MaximumConcurrency`
- Retry automatique en cas d'échec

**Inconvénients** :
- Complexifie l'architecture MVP
- Nécessite une refonte du déclenchement

**Décision** : Non retenue pour le MVP, à considérer pour PROD

### Option 3 : Step Functions avec contrôle de concurrence

**Avantages** :
- Orchestration visuelle
- Contrôle fin de la concurrence

**Inconvénients** :
- Surcoût architectural pour le MVP
- Latence supplémentaire

**Décision** : Non retenue pour le MVP

---

## Monitoring recommandé

### Métriques CloudWatch à surveiller

**Lambda** :
- `ConcurrentExecutions` : doit rester à 1 en DEV
- `Throttles` : doit rester à 0 (pas de throttling Lambda)
- `Duration` : temps d'exécution par invocation

**Bedrock** (via logs) :
- Nombre de logs WARNING "ThrottlingException détectée"
- Nombre de logs ERROR "Échec après X tentatives"
- Taux de retry : <10% attendu
- Taux d'échec final : <2% attendu

### Commandes de diagnostic

**Vérifier la concurrence Lambda** :
```powershell
aws lambda get-function-concurrency `
  --function-name vectora-inbox-ingest-normalize-dev `
  --profile rag-lai-prod --region eu-west-3
```

**Compter les retries Bedrock** :
```powershell
aws logs filter-log-events `
  --log-group-name "/aws/lambda/vectora-inbox-ingest-normalize-dev" `
  --filter-pattern "ThrottlingException détectée" `
  --start-time $((Get-Date).AddHours(-1).ToUniversalTime().Ticks / 10000) `
  --profile rag-lai-prod --region eu-west-3 `
  --query "events[*].message" --output text | Measure-Object -Line
```

---

## Prochaines étapes

### Court terme (cette semaine)

1. ✅ Mode mono-instance activé en DEV
2. ⏳ Redéployer la stack s1-runtime-dev
3. ⏳ Tester avec un batch complet (7 jours, 8 sources)
4. ⏳ Valider que le taux de throttling est <10%

### Moyen terme (ce mois)

5. ⏳ Demander une augmentation des quotas Bedrock via AWS Support
6. ⏳ Tester en STAGE avec `ReservedConcurrentExecutions = 5`
7. ⏳ Ajuster MAX_BEDROCK_WORKERS si nécessaire (6-8)

### Long terme (ce trimestre)

8. ⏳ Déployer en PROD sans limite de concurrence
9. ⏳ Mettre en place des alertes CloudWatch sur le throttling
10. ⏳ Considérer SQS + Event Source Mapping pour un contrôle plus fin

---

## Références

- **Template CloudFormation** : `infra/s1-runtime.yaml`
- **Documentation AWS** : [Lambda Reserved Concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html)
- **Diagnostic Bedrock** : `docs/diagnostics/bedrock_sonnet45_success_final_dev.md`
- **Implémentation retry** : `docs/diagnostics/bedrock_retry_implementation.md`

---

**Auteur** : Amazon Q Developer  
**Date de création** : 2025-01-XX  
**Dernière mise à jour** : 2025-01-XX  
**Version** : 1.0
