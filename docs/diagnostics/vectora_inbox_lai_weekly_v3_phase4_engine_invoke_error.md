# Vectora Inbox LAI Weekly v3 - Phase 4 Engine Invocation Error

**Date** : 2025-12-11  
**Client** : lai_weekly_v3  
**Phase** : 4 - Engine (Matching + Scoring + Newsletter)  
**Status** : ❌ ÉCHEC - Erreur d'invocation Lambda

---

## Commande Exacte Exécutée

```powershell
$Payload = '{"client_id":"lai_weekly_v3","period_days":30}'
aws lambda invoke --function-name vectora-inbox-engine-dev --payload $Payload --cli-binary-format raw-in-base64-out --profile rag-lai-prod --region eu-west-3 out-lai-weekly-v3-phase4.json
```

---

## Message d'Erreur Complet

```
An error occurred (InvalidRequestContentException) when calling the Invoke operation: Could not parse request body into json: Could not parse payload into json: Unexpected character ('c' (code 99)): was expecting double-quote to start field name
 at [Source: REDACTED (`StreamReadFeature.INCLUDE_SOURCE_IN_LOCATION` disabled); line: 1, column: 2]
```

---

## Diagnostic Technique

### Type d'Erreur
- **Catégorie** : InvalidRequestContentException
- **Cause** : Parsing JSON du payload
- **Symptôme** : Caractère 'c' inattendu à la position 2

### Analyse du Problème

#### 1. Format JSON Invalide
L'erreur indique que le parser JSON AWS Lambda s'attend à une double-quote pour commencer un nom de champ, mais trouve le caractère 'c' à la position 2.

#### 2. Hypothèses sur la Cause
- **Encodage PowerShell** : La variable `$Payload` pourrait être mal interprétée par PowerShell
- **Échappement des guillemets** : Les guillemets doubles dans le JSON pourraient être corrompus
- **Transmission AWS CLI** : Le payload pourrait être altéré lors de la transmission à AWS

#### 3. Position de l'Erreur
- **Line 1, column 2** : Suggère que le premier caractère est correct mais le second ('c') pose problème
- **Attendu** : `"client_id"`
- **Reçu** : Probablement quelque chose comme `{client_id` (guillemet manquant)

### Tentatives de Résolution Possibles

#### Option 1 : Échappement PowerShell
```powershell
$Payload = '{\"client_id\":\"lai_weekly_v3\",\"period_days\":30}'
```

#### Option 2 : Utilisation de fichier temporaire
```bash
echo '{"client_id":"lai_weekly_v3","period_days":30}' > payload.json
aws lambda invoke --function-name vectora-inbox-engine-dev --payload file://payload.json --profile rag-lai-prod --region eu-west-3 out.json
```

#### Option 3 : Base64 manuel
```powershell
$PayloadBase64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('{"client_id":"lai_weekly_v3","period_days":30}'))
aws lambda invoke --function-name vectora-inbox-engine-dev --payload $PayloadBase64 --profile rag-lai-prod --region eu-west-3 out.json
```

---

## Impact sur le Plan

### Phase 4 Bloquée
- ❌ **Matching** : Non exécuté
- ❌ **Scoring** : Non exécuté  
- ❌ **Newsletter** : Non générée
- ❌ **Métriques** : Indisponibles

### Phases Suivantes
- **Phase 5** : Impossible sans données Phase 4
- **Phase 6** : Executive summary incomplet

---

## Recommandations

### Immédiat
1. **Tester échappement PowerShell** : Essayer l'Option 1
2. **Vérifier AWS CLI version** : `aws --version`
3. **Tester avec payload simple** : `{"test":"value"}`

### Alternatif
1. **Utiliser CMD au lieu de PowerShell**
2. **Créer script bash/batch dédié**
3. **Vérifier configuration AWS CLI**

---

**Status** : Phase 4 ❌ BLOQUÉE - Erreur technique d'invocation Lambda

**Prochaine action** : Résoudre le problème d'encodage/parsing JSON avant de continuer le plan.