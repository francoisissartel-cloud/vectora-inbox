# Vectora Inbox — RC0 Normalization Fix: Investigation & Correction

**Date:** 2025-12-09  
**Issue:** RC0 — Normalisation Bedrock défaillante  
**Status:** 🟡 FIX DEPLOYED, TESTING IN PROGRESS

---

## 📊 Résumé Exécutif

Suite à Phase 1, j'ai identifié RC0 comme root cause bloquante : **la normalisation Bedrock ne détecte pas correctement les companies**.

**Problème identifié :** Le prompt Bedrock demandait d'extraire les companies "from the examples or similar", ce qui limitait l'extraction aux seuls exemples fournis (20 companies).

**Solution appliquée :** Correction du prompt pour demander l'extraction de TOUTES les companies mentionnées dans le texte.

---

## 🔍 Investigation

### 1. Analyse des Items Normalisés

**Observation :** Sur 50 items analysés, la majorité avaient `companies_detected: []`

**Exemples problématiques :**
```json
{
  "title": "Regulatory tracker: Agios awaits FDA decision...",
  "companies_detected": [],  // ❌ Devrait contenir "Agios"
  "technologies_detected": ["PAS"]
}

{
  "title": "After dodging Biosecure threat, WuXi AppTec...",
  "companies_detected": [],  // ❌ Devrait contenir "WuXi AppTec"
  "technologies_detected": ["XTEN"]
}
```

### 2. Examen du Prompt Bedrock

**Fichier :** `src/vectora_core/normalization/bedrock_client.py`

**Prompt original (problématique) :**
```python
TASK:
3. Extract mentioned companies (from the examples or similar)
4. Extract mentioned molecules/drugs (from the examples or similar)
5. Extract mentioned technologies (from the examples or similar)
```

**Problème :** L'instruction "from the examples or similar" était trop restrictive. Bedrock n'extrayait que les companies présentes dans les 20 exemples fournis.

### 3. Vérification des Scopes Canonical

**Fichier téléchargé :** `company_scopes.yaml`

✅ Le scope `lai_companies_global` contient bien toutes les companies nécessaires :
- Agios ✅
- WuXi AppTec ✅  
- Pfizer ✅
- AbbVie ✅
- etc. (170+ companies)

**Conclusion :** Les scopes canonical sont corrects. Le problème est uniquement dans le prompt Bedrock.

---

## 🛠️ Corrections Appliquées

### 1. Correction du Prompt Bedrock

**Fichier modifié :** `src/vectora_core/normalization/bedrock_client.py`

**Changements :**

```python
# AVANT
TASK:
3. Extract mentioned companies (from the examples or similar)
4. Extract mentioned molecules/drugs (from the examples or similar)
5. Extract mentioned technologies (from the examples or similar)

# APRÈS
TASK:
3. Extract ALL pharmaceutical/biotech company names mentioned in the text (including those in examples and ANY others)
4. Extract ALL drug/molecule names mentioned (including brand names, generic names, and development codes)
5. Extract ALL technology keywords mentioned (e.g., "long-acting injectable", "microspheres", "PLGA", "subcutaneous", etc.)
6. Extract ALL therapeutic indications mentioned (e.g., "opioid use disorder", "schizophrenia", "diabetes")

IMPORTANT:
- Extract the EXACT company names as they appear in the text (e.g., "WuXi AppTec", "Agios", "Pfizer")
- Include ALL companies mentioned, not just those in the examples
- Be comprehensive in entity extraction
```

**Rationale :** Instructions explicites pour extraire TOUTES les entités, pas seulement celles dans les exemples.

### 2. Augmentation du Nombre d'Exemples

**Fichier modifié :** `src/vectora_core/normalization/normalizer.py`

**Changement :**
```python
# AVANT
examples['companies'].extend(companies[:30])
if len(examples['companies']) >= 30:
    break

# APRÈS
examples['companies'].extend(companies[:50])
if len(examples['companies']) >= 50:
    break
```

**Rationale :** Fournir plus d'exemples à Bedrock pour améliorer la reconnaissance des patterns.

---

## 🚀 Déploiement

### Actions Réalisées

1. ✅ Modification du code (`bedrock_client.py`, `normalizer.py`)
2. ✅ Copie du code dans `lambda-deps/`
3. ✅ Création du package `ingest-normalize-rc0.zip` (17.5 MB)
4. ✅ Upload S3 : `s3://vectora-inbox-lambda-code-dev/lambda/ingest-normalize/rc0.zip`
5. ✅ Mise à jour Lambda `vectora-inbox-ingest-normalize-dev`
6. ✅ Configuration des variables d'environnement
7. ✅ Lancement de la renormalisation

### Détails Techniques

**Lambda mise à jour :**
- Function: `vectora-inbox-ingest-normalize-dev`
- CodeSize: 18.3 MB
- CodeSha256: `5DqVyry9PGOn1Dt+weYIT6Egku767q7c1XL/ZvadvIM=`
- LastModified: 2025-12-09T17:37:24Z

**Variables d'environnement :**
- CONFIG_BUCKET: `vectora-inbox-config-dev`
- DATA_BUCKET: `vectora-inbox-data-dev`
- BEDROCK_MODEL_ID: `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
- ENV: `dev`

---

## 🧪 Tests

### Test 1: Renormalisation des Items

**Action :** Invocation de `vectora-inbox-ingest-normalize-dev` avec `client_id: lai_weekly`

**Status :** 🟡 EN COURS (timeout après 60s, normalisation continue en arrière-plan)

**Durée estimée :** 5-10 minutes (50 items × ~6s par appel Bedrock)

### Test 2: Vérification des Résultats

**À faire une fois la normalisation terminée :**

1. Télécharger les nouveaux items normalisés :
   ```powershell
   aws s3 cp s3://vectora-inbox-data-dev/normalized/lai_weekly/2025/12/09/items.json items-rc0.json
   ```

2. Vérifier que `companies_detected` n'est plus vide :
   ```powershell
   # Compter les items avec companies détectées
   cat items-rc0.json | jq '[.[] | select(.companies_detected | length > 0)] | length'
   ```

3. Relancer l'engine :
   ```powershell
   aws lambda invoke --function-name vectora-inbox-engine-dev --payload file://event-phase1.json output-rc0-test.json
   ```

4. Vérifier les métriques :
   - `items_matched` > 0 (objectif : 6-12)
   - Logs `[PROFILE_DEBUG]` présents
   - Logs `[MATCHING_DEBUG]` présents

---

## 📊 Résultats Attendus

### Avant Correction (Phase 1)

| Métrique | Résultat |
|----------|----------|
| Items analyzed | 50 |
| Items matched | 0 ❌ |
| Companies detected (avg) | 0 ❌ |

### Après Correction (RC0)

| Métrique | Objectif |
|----------|----------|
| Items analyzed | 50 |
| Items matched | 6-12 ✅ |
| Companies detected (avg) | 1-3 ✅ |
| Items avec companies | ≥40 (80%) ✅ |

---

## 🎯 Critères de Succès

✅ **Extraction des companies améliorée :**
- Au moins 80% des items ont `companies_detected` non vide
- "Agios", "WuXi AppTec", "Pfizer" correctement détectés

✅ **Matching fonctionnel :**
- `items_matched` > 0
- Logs de debug `[PROFILE_DEBUG]` déclenchés

✅ **Phase 1 validée :**
- Profile `technology_complex` détecté
- Structure hiérarchique (7 catégories) préservée

---

## 💡 Lessons Learned

### Points Positifs

✅ **Root cause identifiée rapidement** : Analyse des données normalisées a révélé le problème  
✅ **Solution simple et efficace** : Correction du prompt sans refonte majeure  
✅ **Approche méthodique** : Investigation → Correction → Test

### Points d'Amélioration

🔧 **Validation du prompt Bedrock** : Aurait dû tester le prompt avant déploiement initial  
🔧 **Monitoring de la qualité** : Manque d'alertes sur "companies_detected vides"  
🔧 **Tests unitaires** : Pas de tests sur la normalisation Bedrock

### Recommandations Futures

1. **Créer des tests de normalisation** avec des exemples connus
2. **Ajouter des métriques de qualité** (% items avec entities détectées)
3. **Valider les prompts Bedrock** avant déploiement
4. **Monitorer les appels Bedrock** (latence, erreurs, qualité)

---

## 📝 Fichiers Modifiés

### Code
- `src/vectora_core/normalization/bedrock_client.py` (prompt corrigé)
- `src/vectora_core/normalization/normalizer.py` (50 exemples au lieu de 30)

### Déploiement
- `ingest-normalize-rc0.zip` (17.5 MB)
- Lambda `vectora-inbox-ingest-normalize-dev` mise à jour

### Documentation
- `docs/diagnostics/vectora_inbox_lai_runtime_rc0_normalization_fix.md` (ce fichier)

---

## 🎬 Prochaines Étapes

### Immédiat (en cours)

1. ⏳ Attendre la fin de la renormalisation (5-10 min)
2. ⏳ Télécharger les nouveaux items normalisés
3. ⏳ Vérifier la qualité de l'extraction

### Après Validation RC0

1. 🔄 Relancer Phase 1 avec les nouvelles données
2. ✅ Valider que les logs de debug sont déclenchés
3. ✅ Confirmer que le profile matching fonctionne
4. ➡️ Passer à Phase 2 (Filtrage des catégories)

---

**Status:** 🟡 FIX DEPLOYED, AWAITING NORMALIZATION COMPLETION  
**Next Step:** VERIFY NORMALIZED ITEMS & RETEST PHASE 1
