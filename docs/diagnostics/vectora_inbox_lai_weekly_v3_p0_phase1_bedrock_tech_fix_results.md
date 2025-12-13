# Vectora Inbox LAI Weekly v3 - Phase 1 : Bedrock Technology Detection Fix

**Date** : 2025-12-11  
**Phase** : P0-1 Bedrock Technology Detection  
**Objectif** : Améliorer la détection des technologies LAI par Bedrock

---

## Modifications Apportées

### 1. Amélioration du Prompt Bedrock

**Fichier modifié** : `src/vectora_core/normalization/bedrock_client.py`

#### Ajout d'une section LAI spécialisée dans le prompt :
```python
# Extraire spécifiquement les termes LAI pour améliorer la détection
lai_tech_terms = [
    "Extended-Release Injectable", "Long-Acting Injectable", "LAI",
    "PharmaShell®", "SiliaShell®", "BEPO®", "UZEDY®",
    "depot injection", "once-monthly injection", "sustained-release injectable",
    "controlled-release injection", "long-acting depot"
]
```

#### Patterns de détection LAI explicites :
- "Extended-Release Injectable" ou "extended-release injectable" → "Extended-Release Injectable"
- "Long-Acting Injectable" ou "long-acting injectable" → "Long-Acting Injectable" 
- "LAI" (acronyme) → "LAI"
- "PharmaShell®" (technologie Nanexa) → "PharmaShell®"
- "UZEDY®" (risperidone LAI) → "UZEDY®"
- "depot injection" → "depot injection"
- "once-monthly" ou "once monthly" → "once-monthly injection"

### 2. Fonction d'Extraction d'Exemples Améliorée

**Fichier modifié** : `src/vectora_core/normalization/normalizer.py`

#### Changements :
- Renommage : `_extract_canonical_examples()` → `_extract_canonical_examples_enhanced()`
- Priorité aux termes LAI dans les exemples fournis à Bedrock
- Extraction spécifique des `core_phrases` et `technology_terms_high_precision` depuis `technology_scopes.yaml`

---

## Tests Prévus

### Test Cases pour Validation

1. **UZEDY Extended-Release Injectable**
   - Input : "FDA Approves Expanded Indication for UZEDY® (risperidone) Extended-Release Injectable"
   - Expected : `technologies_detected: ["Extended-Release Injectable", "UZEDY®"]`

2. **Nanexa PharmaShell®**
   - Input : "Nanexa and Moderna enter into license agreement for PharmaShell®-based products"
   - Expected : `technologies_detected: ["PharmaShell®"]`

3. **LAI Générique**
   - Input : "Olanzapine LAI submission to FDA"
   - Expected : `technologies_detected: ["LAI"]`

### Commandes de Test

```bash
# Test avec payload UZEDY
echo '{"title": "FDA Approves UZEDY Extended-Release Injectable", "raw_text": "UZEDY (risperidone) extended-release injectable suspension..."}' | base64 > test_uzedy.b64

aws lambda invoke --function-name vectora-inbox-ingest-normalize-rag-lai-prod \
  --payload file://test_uzedy.b64 \
  --profile rag-lai-prod --region eu-west-3 response_uzedy.json

# Vérifier que technologies_detected contient "Extended-Release Injectable"
cat response_uzedy.json | jq '.technologies_detected'
```

---

## Critères de Succès Phase 1

- ✅ UZEDY items : `"technologies_detected": ["Extended-Release Injectable"]`
- ✅ Nanexa items : `"technologies_detected": ["PharmaShell®"]`
- ✅ LAI items génériques : `"technologies_detected": ["LAI"]`

---

## Statut

**Phase 1 : EN COURS**

### Prochaines Étapes
1. Tester les modifications localement
2. Déployer sur AWS DEV
3. Valider avec les cas de test critiques
4. Passer à la Phase 2 (Exclusions HR/Finance)

---

## Notes Techniques

- Le prompt Bedrock inclut maintenant une section "SPECIAL FOCUS - LAI TECHNOLOGY DETECTION"
- Les termes LAI sont normalisés vers des formes standardisées
- Les symboles de marque (®, ™) sont préservés
- La fonction d'extraction d'exemples priorise les termes LAI depuis `technology_scopes.yaml`

Cette amélioration devrait considérablement améliorer la détection des technologies LAI qui étaient précédemment manquées par Bedrock.