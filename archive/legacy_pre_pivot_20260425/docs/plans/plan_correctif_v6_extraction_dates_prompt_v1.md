# Plan Correctif v6 - Extraction Dates Bedrock (Prompt V1 Hardcodé)
## Date: 2026-01-29 16:50 UTC
## Objectif: Corriger le prompt V1 hardcodé pour extraire les dates réelles

---

## 🎯 CADRAGE

### Problème Identifié

**Symptôme**: 0% de dates extraites par Bedrock (cible: >95%)

**Cause racine découverte**: 
- Le prompt LAI pré-construit (Approche B) contient bien les instructions d'extraction de date
- MAIS le code utilise le **prompt V1 hardcodé** dans `bedrock_client.py` qui N'INCLUT PAS l'extraction de date
- Le prompt V1 ne demande que 10 tâches (sans extraction date)
- Bedrock ne peut pas extraire ce qu'on ne lui demande pas

**Preuve**:
```python
# Dans bedrock_client.py ligne ~336
tasks = [
    "1. Generate summary",
    "2. Classify event type",
    ...
    "10. Assess pure player context"
    # ❌ PAS de tâche extraction date
]
```

**Impact**: 
- 100% des dates utilisent le fallback (date d'ingestion)
- Chronologie perdue dans les newsletters
- Scoring basé sur de mauvaises dates

### Objectif du Correctif

**Cible**: >95% de dates extraites par Bedrock

**Approche**: Corriger le prompt V1 hardcodé dans `bedrock_client.py` pour inclure l'extraction de date en tâche #2 (prioritaire)

### Périmètre

**Fichiers à modifier**:
1. `src_v2/vectora_core/normalization/bedrock_client.py` (prompt V1 hardcodé)

**Fichiers déjà corrects** (ne PAS modifier):
1. `canonical/prompts/normalization/lai_prompt.yaml` (Approche B - déjà corrigé)
2. `src_v2/vectora_core/normalization/normalizer.py` (parsing dates OK)
3. `src_v2/vectora_core/normalization/scorer.py` (effective_date OK)
4. `src_v2/vectora_core/newsletter/assembler.py` (affichage dates OK)

**Contraintes**:
- Respecter les règles de développement vectora-inbox
- Utiliser `src_v2/` comme base
- Tester localement avant déploiement
- Créer layer vectora-core avec script officiel
- Valider E2E avec lai_weekly_v7

---

## 🔍 PHASE 1: DIAGNOSTIC APPROFONDI

### 1.1 Analyse du Code Actuel

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonction concernée**: `_build_normalization_prompt_v1()` (ligne ~280)

**Problème identifié**:
```python
# Ligne ~336 - Liste des tâches
tasks = [
    "1. Generate a concise summary (2-3 sentences)",
    "2. Classify the event type",
    "3. Extract ALL pharmaceutical/biotech company names",
    "4. Extract ALL drug/molecule names",
    "5. Extract ALL technology keywords",
    "6. Extract ALL trademark names",
    "7. Extract ALL therapeutic indications",
    "8. Evaluate LAI relevance (0-10 score)",
    "9. Detect anti-LAI signals",
    "10. Assess pure player context"
    # ❌ MANQUE: Extraction date
]

# Ligne ~350 - Format JSON exemple
json_example = {
    "summary": "...",
    "event_type": "...",
    "companies_detected": [...],
    ...
    # ❌ MANQUE: extracted_date et date_confidence
}
```

**Conséquence**: Bedrock ne génère pas les champs `extracted_date` et `date_confidence` car ils ne sont pas demandés.

### 1.2 Validation du Parsing

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonction**: `_parse_bedrock_response_v1()` (ligne ~450)

**Code actuel** (déjà correct):
```python
result.setdefault('extracted_date', None)
result.setdefault('date_confidence', 0.0)
```

✅ Le parsing est correct, mais Bedrock ne retourne jamais ces champs.

### 1.3 Validation Items Curated

**Test réel** (lai_weekly_v7, 2026-01-29):
```json
{
  "normalized_content": {
    "extracted_date": null,        ← Toujours null
    "date_confidence": 0.0          ← Toujours 0.0
  }
}
```

**Contenu item**:
```
"content": "...December 9, 2025December 9, 2025"
```

✅ La date est présente dans le contenu, mais Bedrock ne l'extrait pas.

### 1.4 Conclusion Diagnostic

**Problème confirmé**: Le prompt V1 hardcodé ne demande pas l'extraction de date.

**Solution**: Ajouter l'extraction de date en tâche #2 (prioritaire) dans le prompt V1.

---

## 🔧 PHASE 2: CORRECTIF LOCAL

### 2.1 Modification du Prompt V1

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Fonction**: `_build_normalization_prompt_v1()`

**Changements**:

#### Changement 1: Ajouter tâche extraction date en position #2

**Avant**:
```python
tasks = [
    "1. Generate a concise summary (2-3 sentences)",
    "2. Classify the event type",
    ...
]
```

**Après**:
```python
tasks = [
    "1. Generate a concise summary (2-3 sentences)",
    "2. CRITICAL: Extract publication date from content (format: YYYY-MM-DD) - REQUIRED FIELD",
    "3. Classify the event type",
    "4. Extract ALL pharmaceutical/biotech company names",
    "5. Extract ALL drug/molecule names",
    "6. Extract ALL technology keywords",
    "7. Extract ALL trademark names",
    "8. Extract ALL therapeutic indications",
    "9. Evaluate LAI relevance (0-10 score)",
    "10. Detect anti-LAI signals",
    "11. Assess pure player context"
]
```

#### Changement 2: Ajouter instructions extraction date

**Après les tâches, ajouter**:
```python
prompt += """

DATE EXTRACTION INSTRUCTIONS (CRITICAL - REQUIRED):
- Look for dates like "27 January, 2026", "January 28, 2026", "09 January 2026", "December 9, 2025"
- Return format: YYYY-MM-DD (REQUIRED)
- If multiple dates, choose the publication date (not future event dates)
- If no clear date found, return null
- Confidence: 0.0-1.0 (1.0 = certain, 0.5 = uncertain, 0.0 = no date)
- YOU MUST include both "extracted_date" and "date_confidence" in your response

IMPORTANT:
- Extract the EXACT company names as they appear in the text
- Include ALL companies mentioned, not just those in the examples
- Be comprehensive in entity extraction"""
```

#### Changement 3: Modifier l'exemple JSON

**Avant**:
```python
json_example = {
    "summary": "...",
    "event_type": "...",
    "companies_detected": [...],
    ...
}
```

**Après**:
```python
json_example = {
    "summary": "...",
    "extracted_date": "2025-12-09",
    "date_confidence": 0.95,
    "event_type": "...",
    "companies_detected": [...],
    ...
}
```

#### Changement 4: Ajouter emphase sur champs requis

**Avant**:
```python
prompt += f"\n\nRESPONSE FORMAT (JSON only):\n{json.dumps(json_example, indent=2)}\n\nRespond with ONLY the JSON, no additional text."
```

**Après**:
```python
prompt += f"\n\nRESPONSE FORMAT (JSON only):\n{json.dumps(json_example, indent=2)}\n\nCRITICAL: The fields \"extracted_date\" and \"date_confidence\" are REQUIRED in your JSON response.\n\nRespond with ONLY the JSON, no additional text."
```

### 2.2 Vérification du Code Modifié

**Checklist**:
- [ ] Tâche extraction date en position #2
- [ ] Instructions détaillées ajoutées
- [ ] Exemple JSON avec extracted_date et date_confidence
- [ ] Emphase "CRITICAL" et "REQUIRED"
- [ ] Pas de régression sur autres fonctionnalités

---

## 🧪 PHASE 3: TESTS LOCAUX SUR DONNÉES RÉELLES

### 3.1 Préparation Environnement Test

**Données de test**: Items ingérés lai_weekly_v7 (23 items réels)

**Fichier**: `items_ingested_v7.json` (déjà téléchargé)

**Contenu exemple**:
```json
{
  "title": "Medincell Partner Teva Pharmaceuticals Announces NDA Submission",
  "content": "December 9, 2025 - Teva Pharmaceuticals announced...",
  "published_at": "2026-01-29"
}
```

### 3.2 Test Unitaire Prompt Construction

**Script**: `scripts/test_prompt_v1_dates.py`

**Objectif**: Vérifier que le prompt V1 contient bien les instructions de date

**Test**:
```python
from src_v2.vectora_core.normalization.bedrock_client import BedrockNormalizationClient

client = BedrockNormalizationClient("test-model", "us-east-1")
prompt = client._build_normalization_prompt_v1(
    item_text="December 9, 2025 - Test content",
    canonical_examples={"companies_examples": "Test", ...}
)

# Vérifications
assert "Extract publication date" in prompt
assert "extracted_date" in prompt
assert "date_confidence" in prompt
assert "CRITICAL" in prompt
assert "REQUIRED" in prompt
```

### 3.3 Test Intégration avec Bedrock (Local)

**Script**: `scripts/test_bedrock_date_extraction_local.py`

**Objectif**: Tester l'extraction de date avec un item réel

**Test**:
```python
import json
from src_v2.vectora_core.normalization.bedrock_client import BedrockNormalizationClient

# Charger item réel
with open('items_ingested_v7.json') as f:
    items = json.load(f)
    test_item = items[0]

# Construire texte
item_text = f"TITLE: {test_item['title']}\n\nCONTENT: {test_item['content']}"

# Appeler Bedrock
client = BedrockNormalizationClient(
    model_id="anthropic.claude-3-sonnet-20240229-v1:0",
    region="us-east-1"
)

result = client.normalize_item(item_text, canonical_examples={})

# Vérifications
print(f"extracted_date: {result.get('extracted_date')}")
print(f"date_confidence: {result.get('date_confidence')}")

assert result.get('extracted_date') is not None, "Date non extraite"
assert result.get('date_confidence') > 0.5, "Confiance trop faible"
```

**Critères de succès**:
- ✅ `extracted_date` non-null
- ✅ `date_confidence` > 0.5
- ✅ Format date: YYYY-MM-DD
- ✅ Date cohérente avec contenu

### 3.4 Test sur Échantillon (5 items)

**Script**: `scripts/test_date_extraction_sample.py`

**Objectif**: Valider sur 5 items réels

**Métriques attendues**:
- ✅ 5/5 items avec `extracted_date` non-null (100%)
- ✅ 4/5 items avec `date_confidence` > 0.8 (80%)
- ✅ Dates cohérentes avec contenu

---

## 🚀 PHASE 4: DÉPLOIEMENT AWS

### 4.1 Création Layer vectora-core

**Script officiel**: `scripts/layers/create_vectora_core_layer.py`

**Commande**:
```bash
python scripts/layers/create_vectora_core_layer.py
```

**Vérifications**:
- [ ] Layer créé avec succès
- [ ] ARN récupéré
- [ ] Taille < 50MB
- [ ] Structure `python/vectora_core/` correcte

**Output attendu**:
```
[OK] Layer publié: arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev
[OK] Version ARN: arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:40
```

### 4.2 Mise à Jour Lambda normalize-score-v2

**Commande**:
```bash
aws lambda update-function-configuration \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --layers arn:aws:lambda:eu-west-3:786469175371:layer:vectora-inbox-vectora-core-dev:40 \
  --region eu-west-3 \
  --profile rag-lai-prod
```

**Vérifications**:
- [ ] Layer appliqué avec succès
- [ ] Status: Active
- [ ] LastUpdateStatus: Successful

**Attendre**: 15 secondes pour que la Lambda soit prête

### 4.3 Test E2E avec lai_weekly_v7

**Commande**:
```bash
aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload '{"client_id": "lai_weekly_v7"}' \
  --region eu-west-3 \
  --profile rag-lai-prod \
  response_normalize_v7_final.json
```

**Attendre**: 5-10 minutes pour 23 items

**Vérification fichier curated**:
```bash
aws s3 ls s3://vectora-inbox-data-dev/curated/lai_weekly_v7/2026/01/29/ \
  --region eu-west-3 \
  --profile rag-lai-prod
```

**Télécharger résultats**:
```bash
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v7/2026/01/29/items.json \
  items_curated_v7_final.json \
  --region eu-west-3 \
  --profile rag-lai-prod
```

### 4.4 Validation Extraction Dates

**Script**: `scripts/validate_bedrock_dates_v7.py`

**Commande**:
```bash
python scripts/validate_bedrock_dates_v7.py
```

**Métriques attendues**:
```
Métrique                    | Cible  | Actuel | Status
----------------------------|--------|--------|--------
Dates Bedrock extraites     | >95%   | [TBD]  | 
Haute confiance (>0.8)      | >90%   | [TBD]  |
Dates fallback utilisées    | <5%    | [TBD]  |
Effective_date = Bedrock    | >95%   | [TBD]  |
```

**Critères de succès**:
- ✅ >95% items avec `extracted_date` non-null
- ✅ >90% items avec `date_confidence` > 0.8
- ✅ <5% items utilisent date fallback
- ✅ Dates cohérentes avec contenu

### 4.5 Vérification Logs CloudWatch

**Commande**:
```bash
aws logs tail /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --since 10m \
  --region eu-west-3 \
  --profile rag-lai-prod \
  --format short | findstr "Date extracted"
```

**Logs attendus**:
```
[INFO] Date extracted by Bedrock: 2025-12-09 (confidence: 0.95)
[INFO] Using Bedrock date: 2025-12-09
```

---

## 📊 PHASE 5: VALIDATION FINALE

### 5.1 Métriques Finales

**Tableau de bord**:
```
Métrique                    | Avant  | Cible  | Après  | Delta  | Status
----------------------------|--------|--------|--------|--------|--------
Vraies dates extraites      | 0%     | >95%   | [TBD]  | [TBD]  |
Dates Bedrock fiables       | N/A    | >90%   | [TBD]  | [TBD]  |
Dates fallback              | 100%   | <5%    | [TBD]  | [TBD]  |
Temps normalisation/item    | 4.9s   | <5.5s  | [TBD]  | [TBD]  |
Coût par run (23 items)     | $0.21  | <$0.25 | [TBD]  | [TBD]  |
```

### 5.2 Validation Qualitative

**Échantillon 5 items**:
```
Item 1:
- Title: [TBD]
- Content date: [TBD]
- Extracted_date: [TBD]
- Date_confidence: [TBD]
- Match correct: OUI / NON

[Items 2-5]
```

### 5.3 Checklist Validation

**Extraction Dates**:
- [ ] >95% items avec `extracted_date` non-null
- [ ] >90% items avec `date_confidence` > 0.8
- [ ] <5% items utilisent date fallback
- [ ] Dates extraites cohérentes avec contenu

**Scoring**:
- [ ] `effective_date` présent dans tous items
- [ ] `effective_date` utilise date Bedrock si confiance > 0.7
- [ ] Recency factor calculé avec date effective
- [ ] Penalties calculées avec date effective

**Newsletter** (Phase suivante):
- [ ] Dates affichées != toutes fallback
- [ ] Dates cohérentes avec contenu
- [ ] Format dates correct
- [ ] Chronologie restaurée

**Performance**:
- [ ] Temps normalisation < 10min
- [ ] Coût Bedrock < $0.30
- [ ] Aucune erreur Lambda
- [ ] Aucun throttling

### 5.4 Décision GO/NO-GO

**Critères**:
- [ ] Extraction dates >= 95%
- [ ] Performance acceptable
- [ ] Aucune régression
- [ ] Tests E2E passés

**Décision**: ✅ GO / ❌ NO-GO / ⚠️ GO avec réserves

**Si NO-GO**:
- Analyser logs CloudWatch
- Vérifier réponse Bedrock
- Ajuster prompt si nécessaire
- Retester

---

## 📝 PHASE 6: RETOUR USER

### 6.1 Rapport Final

**Document**: `docs/reports/rapport_final_correctif_v6_extraction_dates.md`

**Contenu**:
1. Résumé exécutif
2. Problème identifié (prompt V1 hardcodé)
3. Solution appliquée (ajout extraction date tâche #2)
4. Résultats obtenus (métriques)
5. Validation E2E
6. Prochaines étapes

### 6.2 Métriques Livrées

**Tableau final**:
```
Métrique                    | Avant  | Cible  | Après  | Delta  | Status
----------------------------|--------|--------|--------|--------|--------
Vraies dates extraites      | 0%     | >95%   | XX%    | +XX%   | ✅/❌
Dates Bedrock fiables       | N/A    | >90%   | XX%    | N/A    | ✅/❌
Dates fallback              | 100%   | <5%    | XX%    | -XX%   | ✅/❌
```

### 6.3 Fichiers Livrés

**Code modifié**:
1. `src_v2/vectora_core/normalization/bedrock_client.py` (prompt V1 corrigé)

**Tests créés**:
1. `scripts/test_prompt_v1_dates.py`
2. `scripts/test_bedrock_date_extraction_local.py`
3. `scripts/test_date_extraction_sample.py`

**Scripts validation**:
1. `scripts/validate_bedrock_dates_v7.py` (déjà existant)

**Rapports**:
1. `docs/plans/plan_correctif_v6_extraction_dates_prompt_v1.md` (ce fichier)
2. `docs/reports/rapport_final_correctif_v6_extraction_dates.md`

**Déploiement AWS**:
- Layer vectora-core v40 (ou version suivante)
- Lambda normalize-score-v2 mise à jour

### 6.4 Prochaines Étapes

**Si succès (>95% dates extraites)**:
1. ✅ Valider avec lai_weekly_v6 (client production)
2. ✅ Générer newsletter avec dates réelles
3. ✅ Vérifier chronologie restaurée
4. ✅ Documenter solution dans wiki

**Si échec partiel (80-95% dates extraites)**:
1. ⚠️ Analyser items sans date extraite
2. ⚠️ Ajuster prompt pour cas edge
3. ⚠️ Retester avec échantillon ciblé

**Si échec total (<80% dates extraites)**:
1. ❌ Analyser logs Bedrock en détail
2. ❌ Vérifier format réponse JSON
3. ❌ Considérer approche alternative (appel Bedrock dédié)

---

## 📋 CHECKLIST CONFORMITÉ RÈGLES DÉVELOPPEMENT

### Architecture
- [x] Utilise `src_v2/` comme base
- [x] Modification dans `vectora_core/normalization/`
- [x] Aucune modification dans handlers
- [x] Aucune référence architecture historique

### Configuration
- [x] Bedrock: us-east-1 + Sonnet 3
- [x] Nommage: `-v2-dev`
- [x] Variables environnement standard
- [x] Structure S3: ingested/ + curated/

### Déploiement
- [x] Layer créé avec script officiel
- [x] Tests locaux avant déploiement
- [x] Validation E2E avec client test
- [x] Logs CloudWatch vérifiés

### Tests
- [x] Tests unitaires (prompt construction)
- [x] Tests intégration (Bedrock local)
- [x] Tests E2E (lai_weekly_v7)
- [x] Validation métriques

---

## 🎯 RÉSUMÉ EXÉCUTIF

**Problème**: Prompt V1 hardcodé ne demande pas l'extraction de date → 0% dates extraites

**Solution**: Ajouter extraction date en tâche #2 (prioritaire) dans prompt V1

**Fichier modifié**: `src_v2/vectora_core/normalization/bedrock_client.py`

**Changements**:
1. Tâche #2: "CRITICAL: Extract publication date (YYYY-MM-DD) - REQUIRED"
2. Instructions détaillées extraction date
3. Exemple JSON avec `extracted_date` et `date_confidence`
4. Emphase "CRITICAL" et "REQUIRED"

**Tests**:
1. Tests locaux sur données réelles (5 items)
2. Déploiement layer vectora-core
3. Validation E2E lai_weekly_v7 (23 items)

**Critères succès**: >95% dates extraites, >90% haute confiance, <5% fallback

**Durée estimée**: 2 heures (tests locaux 30min, déploiement 15min, validation 1h15)

---

**Plan Correctif v6 - Extraction Dates Bedrock**  
**Date**: 2026-01-29 16:50 UTC  
**Status**: ✅ PRÊT POUR EXÉCUTION  
**Conformité**: ✅ Respecte vectora-inbox-development-rules.md
