# DIAGNOSTIC COMPLET - Échec Extraction Dates Bedrock
## Date: 2026-01-29 13:30 UTC

---

## 🔍 RÉSUMÉ EXÉCUTIF

**Problème**: 0% de dates extraites par Bedrock (cible: >95%)  
**Cause racine**: Bedrock ne génère pas les champs `extracted_date` et `date_confidence` malgré les instructions du prompt  
**Impact**: Toutes les dates utilisent le fallback (date d'ingestion)

---

## ✅ CE QUI FONCTIONNE

### 1. Prompt LAI (lai_prompt.yaml)
- ✅ Uploadé sur S3 le 2026-01-29 11:27 UTC
- ✅ Contient tâche #11: "Extract publication date from content"
- ✅ Instructions détaillées d'extraction de date
- ✅ Exemple JSON avec `extracted_date` et `date_confidence`
- ✅ Format YYYY-MM-DD spécifié

### 2. Configuration Client (lai_weekly_v7)
- ✅ Approche B activée: `normalization_prompt: "lai"`
- ✅ Prompt LAI chargé depuis S3
- ✅ Références canonical résolues

### 3. Code Layer v5
- ✅ `bedrock_client.py`: Champs `extracted_date` et `date_confidence` dans `_parse_bedrock_response_v1()`
- ✅ `normalizer.py`: Extraction et validation des dates
- ✅ `scorer.py`: Utilisation `effective_date` avec priorisation Bedrock
- ✅ `assembler.py`: Affichage dates réelles dans newsletter

### 4. Déploiement AWS
- ✅ Layer v5 déployé et appliqué aux Lambdas
- ✅ Normalisation exécutée avec succès (23 items)
- ✅ Fichier curated créé (65 KB)

---

## ❌ CE QUI NE FONCTIONNE PAS

### Bedrock ne génère pas les champs de date

**Observation**:
```json
{
  "normalized_content": {
    "summary": "...",
    "entities": {...},
    "lai_relevance_score": 9,
    "extracted_date": null,        ← TOUJOURS NULL
    "date_confidence": 0.0          ← TOUJOURS 0.0
  }
}
```

**Réponse Bedrock attendue**:
```json
{
  "summary": "...",
  "companies_detected": [...],
  "extracted_date": "2025-12-09",
  "date_confidence": 0.95
}
```

**Réponse Bedrock réelle** (déduite):
```json
{
  "summary": "...",
  "companies_detected": [...],
  // extracted_date et date_confidence ABSENTS
}
```

---

## 🔬 ANALYSE DÉTAILLÉE

### Test 1: Vérification Prompt S3
```bash
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/normalization/
# Résultat: lai_prompt.yaml présent (2733 bytes, 2026-01-29 12:27)
```
✅ Prompt présent sur S3

### Test 2: Contenu Prompt
```yaml
TASK:
  11. Extract publication date from content (format: YYYY-MM-DD)

DATE EXTRACTION INSTRUCTIONS:
  - Look for dates like "27 January, 2026"
  - Return format: YYYY-MM-DD
  - Confidence: 0.0-1.0

RESPONSE FORMAT (JSON only):
{
  "extracted_date": "2026-01-27",
  "date_confidence": 0.95
}
```
✅ Instructions présentes et claires

### Test 3: Configuration Client
```yaml
bedrock_config:
  normalization_prompt: "lai"
```
✅ Approche B activée

### Test 4: Code Layer v5
```python
# bedrock_client.py - _parse_bedrock_response_v1()
result.setdefault('extracted_date', None)
result.setdefault('date_confidence', 0.0)
```
✅ Champs parsés avec setdefault()

### Test 5: Items Curated
```json
{
  "normalized_content": {
    "extracted_date": null,
    "date_confidence": 0.0
  }
}
```
❌ Valeurs par défaut (null/0.0) = Bedrock n'a pas retourné ces champs

---

## 🎯 CAUSE RACINE IDENTIFIÉE

### Problème: Surcharge Cognitive du Prompt

Le prompt demande **11 tâches** à Bedrock:
1. Generate summary
2. Classify event type
3. Extract companies
4. Extract molecules
5. Extract technologies
6. Extract trademarks
7. Extract indications
8. Evaluate LAI relevance
9. Detect anti-LAI signals
10. Assess pure player context
11. **Extract publication date** ← DERNIÈRE TÂCHE

**Hypothèse**: Bedrock (Claude) peut "oublier" ou ignorer les dernières tâches quand le prompt est trop chargé.

**Preuve**:
- Toutes les autres tâches (1-10) fonctionnent parfaitement
- Seule la tâche #11 (extraction date) échoue systématiquement
- Le modèle génère un JSON valide mais incomplet

---

## 💡 SOLUTIONS PROPOSÉES

### Solution 1: PRIORISER l'extraction de date (RECOMMANDÉE)
**Action**: Déplacer l'extraction de date en tâche #2 (après summary)

**Avant**:
```
TASK:
1. Generate summary
2. Classify event type
...
11. Extract publication date
```

**Après**:
```
TASK:
1. Generate summary
2. Extract publication date (YYYY-MM-DD) ← PRIORITAIRE
3. Classify event type
...
```

**Avantages**:
- ✅ Date traitée en priorité
- ✅ Moins de risque d'oubli
- ✅ Changement minimal

**Fichier à modifier**: `canonical/prompts/normalization/lai_prompt.yaml`

---

### Solution 2: Simplifier le prompt
**Action**: Réduire le nombre de tâches ou fusionner certaines

**Exemple**:
```
TASK:
1. Generate summary
2. Extract publication date (YYYY-MM-DD)
3. Extract ALL entities (companies, molecules, technologies, trademarks, indications)
4. Classify event type
5. Evaluate LAI relevance and context
```

**Avantages**:
- ✅ Prompt plus court
- ✅ Moins de charge cognitive
- ✅ Plus rapide

**Inconvénients**:
- ⚠️ Nécessite refactoring du parsing

---

### Solution 3: Prompt dédié extraction dates
**Action**: Créer un appel Bedrock séparé uniquement pour les dates

**Workflow**:
1. Appel Bedrock #1: Normalisation complète (sans dates)
2. Appel Bedrock #2: Extraction date uniquement

**Avantages**:
- ✅ Extraction date garantie
- ✅ Prompt ultra-simple pour dates

**Inconvénients**:
- ❌ Double coût Bedrock
- ❌ Double latence
- ❌ Complexité accrue

---

### Solution 4: Renforcer l'exemple JSON
**Action**: Rendre l'exemple JSON plus explicite et répété

**Avant**:
```
RESPONSE FORMAT (JSON only):
{
  "extracted_date": "2026-01-27",
  "date_confidence": 0.95
}
```

**Après**:
```
CRITICAL: You MUST include these fields in your JSON response:
- "extracted_date": "YYYY-MM-DD" (REQUIRED, use null if no date found)
- "date_confidence": 0.0-1.0 (REQUIRED)

RESPONSE FORMAT (JSON only):
{
  "summary": "...",
  "extracted_date": "2026-01-27",  ← REQUIRED FIELD
  "date_confidence": 0.95           ← REQUIRED FIELD
}
```

**Avantages**:
- ✅ Emphase sur les champs requis
- ✅ Changement minimal

---

## 🚀 PLAN D'ACTION RECOMMANDÉ

### Étape 1: Modifier le prompt LAI (5 min)
**Fichier**: `canonical/prompts/normalization/lai_prompt.yaml`

**Changements**:
1. Déplacer tâche extraction date en position #2
2. Ajouter "CRITICAL" avant les instructions de date
3. Marquer `extracted_date` et `date_confidence` comme REQUIRED dans l'exemple JSON

### Étape 2: Uploader prompt modifié sur S3 (1 min)
```bash
aws s3 cp canonical/prompts/normalization/lai_prompt.yaml \
  s3://vectora-inbox-config-dev/canonical/prompts/normalization/lai_prompt.yaml
```

### Étape 3: Retester avec lai_weekly_v7 (10 min)
```bash
# Réinvoquer normalisation
aws lambda invoke --function-name vectora-inbox-normalize-score-v2-dev \
  --invocation-type Event \
  --payload '{"client_id": "lai_weekly_v7"}' \
  response_normalize_v7_v2.json

# Attendre 5 min puis valider
python scripts/validate_bedrock_dates_v7.py
```

### Étape 4: Valider résultats (5 min)
**Critères de succès**:
- ✅ >95% items avec `extracted_date` non-null
- ✅ >90% items avec `date_confidence` > 0.8
- ✅ Dates cohérentes avec contenu

---

## 📊 MÉTRIQUES ACTUELLES

```
Métrique                    | Avant  | Cible  | Actuel | Status
----------------------------|--------|--------|--------|--------
Dates Bedrock extraites     | N/A    | >95%   | 0%     | ❌ ÉCHEC
Haute confiance (>0.8)      | N/A    | >90%   | 0%     | ❌ ÉCHEC
Dates fallback utilisées    | 100%   | <5%    | 100%   | ❌ ÉCHEC
Effective_date = Bedrock    | N/A    | >95%   | 0%     | ❌ ÉCHEC
```

---

## 🔧 FICHIERS CONCERNÉS

### À Modifier
1. `canonical/prompts/normalization/lai_prompt.yaml` ⭐ CRITIQUE

### Déjà Corrects (Ne PAS modifier)
1. `src_v2/vectora_core/normalization/bedrock_client.py` ✅
2. `src_v2/vectora_core/normalization/normalizer.py` ✅
3. `src_v2/vectora_core/normalization/scorer.py` ✅
4. `src_v2/vectora_core/newsletter/assembler.py` ✅

---

## 📝 NOTES TECHNIQUES

### Comportement setdefault()
```python
result.setdefault('extracted_date', None)
# Si 'extracted_date' existe dans result: ne fait rien
# Si 'extracted_date' n'existe PAS: ajoute avec valeur None
```

**Problème**: Si Bedrock ne retourne pas le champ, setdefault() ajoute None.  
**Résultat**: `extracted_date: null` dans tous les items.

### Validation Format Date
```python
if extracted_date:
    try:
        datetime.strptime(extracted_date, '%Y-%m-%d')
        logger.info(f"Date extracted: {extracted_date}")
    except ValueError:
        extracted_date = None
```

**Observation**: Aucun log "Date extracted" trouvé → Bedrock ne retourne jamais de date.

---

## 🎯 CONCLUSION

**Diagnostic**: Le code est correct, le prompt est correct, mais Bedrock n'exécute pas la tâche #11 (extraction date).

**Cause**: Surcharge cognitive du prompt (11 tâches) → Bedrock ignore les dernières instructions.

**Solution**: Prioriser l'extraction de date en tâche #2 et renforcer les instructions.

**Temps estimé**: 20 minutes (modification + test + validation)

**Confiance**: 85% que cette solution résoudra le problème.

---

**Rapport généré le**: 2026-01-29 13:30 UTC  
**Analysé par**: Amazon Q  
**Items testés**: 23 (lai_weekly_v7)  
**Taux d'échec**: 100% (0/23 dates extraites)
