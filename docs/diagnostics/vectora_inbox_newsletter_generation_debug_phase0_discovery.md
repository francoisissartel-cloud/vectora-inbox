# Vectora Inbox - Phase 0 : Discovery & Diagnostic Newsletter Generation

**Date** : 2025-12-12  
**Phase** : 0 - Discovery & Diagnostic Précis  
**Statut** : ✅ TERMINÉE

---

## 🔍 Module Newsletter Identifié

### 📁 Architecture Newsletter

**Module principal** : `src/vectora_core/newsletter/`
- **assembler.py** : Orchestration génération newsletter
- **bedrock_client.py** : Appels Bedrock pour contenu éditorial
- **formatter.py** : Assemblage Markdown final

**Point d'entrée** : `run_engine_for_client()` dans `src/vectora_core/__init__.py`
- Ligne 280 : Appel `assembler.generate_newsletter()`
- Ligne 285 : Écriture newsletter dans S3

### 🔗 Flux d'Appel Newsletter

```
Lambda Engine Handler
  ↓
run_engine_for_client()
  ↓
assembler.generate_newsletter()
  ↓
bedrock_client.generate_editorial_content()
  ↓
formatter.assemble_markdown()
```

---

## ⚙️ Configuration Bedrock Newsletter

### 🌍 Région & Modèle

**Configuration actuelle** :
- **BEDROCK_REGION** : `us-east-1` ✅
- **BEDROCK_MODEL_ID** : `us.anthropic.claude-sonnet-4-5-20250929-v1:0` ✅
- **Client Bedrock** : `boto3.client('bedrock-runtime', region_name='us-east-1')`

**Cohérence avec normalisation** : ✅ IDENTIQUE
- Normalisation : us-east-1 + claude-sonnet-4-5
- Newsletter : us-east-1 + claude-sonnet-4-5

### 📝 Paramètres d'Appel

**Request body newsletter** (`bedrock_client.py:85`) :
```json
{
  "anthropic_version": "bedrock-2023-05-31",
  "max_tokens": 8000,
  "messages": [{"role": "user", "content": "PROMPT"}],
  "temperature": 0.3
}
```

**Différences vs normalisation** :
- Newsletter : `max_tokens: 8000` vs Normalisation : `max_tokens: 4000`
- Newsletter : `temperature: 0.3` vs Normalisation : `temperature: 0.1`

---

## 🔄 Mécanisme de Fallback

### 📍 Localisation du Fallback

**Fichier** : `src/vectora_core/newsletter/bedrock_client.py`
**Fonction** : `generate_editorial_content()` ligne 54
**Condition** : `except Exception as e:` ligne 96

### 🛡️ Logique de Fallback

```python
try:
    response_text = _call_bedrock_with_retry(bedrock_model_id, request_body)
    result = _parse_editorial_response(response_text)
    return result
except Exception as e:
    logger.error(f"Erreur finale lors de l'appel à Bedrock après tous les retries: {e}")
    # FALLBACK DÉCLENCHÉ ICI
    return _generate_fallback_editorial(sections_data, client_profile, target_date)
```

**Fallback content** (`_generate_fallback_editorial()` ligne 234) :
- Titre : `"{client_name} – {target_date}"`
- Intro : `"Newsletter générée en mode dégradé (erreur Bedrock)."`
- Sections : Items bruts sans réécriture éditoriale
- **Indicateur** : Intro contient "mode dégradé (erreur Bedrock)"

---

## 📊 Logs d'Erreur Dernière Exécution

### 🚨 Problème Principal : Throttling Bedrock

**Source** : Validation P0 lai_weekly_v3 (2025-12-12)
**Phase bloquée** : Normalisation (avant newsletter)

**Erreurs observées** :
```
[WARNING] ThrottlingException détectée (tentative 1/4). Retry dans 0.57s...
[WARNING] ThrottlingException détectée (tentative 2/4). Retry dans 1.08s...
[WARNING] ThrottlingException détectée (tentative 3/4). Retry dans 2.03s...
[ERROR] ThrottlingException - Échec après 4 tentatives. Abandon de l'appel Bedrock.
[WARNING] Réponse Bedrock non-JSON, tentative d'extraction manuelle
```

### 🔍 Analyse des Erreurs

**Problème 1** : Volume élevé (104 items sur 30 jours)
- Appels Bedrock séquentiels pour normalisation
- Quotas Bedrock dépassés en us-east-1
- Pipeline bloqué avant la phase newsletter

**Problème 2** : Réponses non-JSON
- Parsing failures fréquents
- Extraction manuelle échoue
- Fallback déclenché

**Impact sur newsletter** :
- ❌ Phase newsletter jamais atteinte
- ❌ Pas d'items normalisés disponibles
- ❌ Newsletter minimale générée (aucun item)

---

## 🎯 Causes Probables Newsletter

### 🔴 Cause Primaire : Pipeline Bloqué en Amont

**Problème** : La newsletter n'est jamais générée car la normalisation échoue
**Symptôme** : `run_engine_for_client()` reçoit 0 items normalisés
**Résultat** : Newsletter minimale générée (ligne 207 dans `__init__.py`)

### 🟡 Causes Secondaires Potentielles

1. **Prompt Newsletter Trop Long**
   - Prompt newsletter plus complexe que normalisation
   - Sections multiples + exemples + instructions
   - Risque de dépassement token limit

2. **Format JSON Complexe**
   - Structure JSON newsletter plus complexe
   - Nested sections avec items
   - Parsing plus fragile

3. **Retry Logic Insuffisant**
   - Même retry logic que normalisation
   - Pas d'optimisation spécifique newsletter
   - Backoff peut être insuffisant pour gros prompts

### 🟢 Causes Peu Probables

1. **Modèle Incompatible** : ❌ Même modèle que normalisation (fonctionne)
2. **Région Incorrecte** : ❌ us-east-1 configuré correctement
3. **Permissions AWS** : ❌ Même permissions que normalisation

---

## 📋 Solutions Identifiées

### 🚀 Solution Primaire : Résoudre Throttling Normalisation

**Priorité** : P0+ (Bloquant)
**Actions** :
1. Optimiser prompts normalisation (-50% taille)
2. Implémenter parallélisation (2-3 workers)
3. Augmenter backoff delays (5-10s)
4. Mode batch avec pauses forcées

### 🔧 Solutions Secondaires : Optimiser Newsletter

**Priorité** : P1 (Préventif)
**Actions** :
1. Réduire taille prompt newsletter
2. Simplifier structure JSON de sortie
3. Améliorer parsing avec fallbacks
4. Cache résultats éditoriaux

### 🛡️ Solution de Contournement : Mode Dégradé

**Priorité** : P1 (Robustesse)
**Actions** :
1. Améliorer fallback newsletter (plus informatif)
2. Utiliser données pré-normalisées si disponibles
3. Mode simulation pour tests

---

## 🎯 Recommandations Phase 1

### ✅ Corrections Minimales Nécessaires

1. **Pas de modification newsletter requise** : Le problème est en amont
2. **Focus sur normalisation** : Résoudre throttling Bedrock
3. **Test isolé newsletter** : Valider avec données simulées

### 📊 Métriques de Validation

**Indicateurs de succès** :
- Newsletter générée sans fallback
- Intro ne contient pas "mode dégradé"
- Sections avec contenu éditorial Bedrock
- Format JSON parsé correctement

**Indicateurs d'échec** :
- Fallback déclenché (intro "mode dégradé")
- Newsletter minimale (0 items)
- Erreurs parsing JSON
- Timeout Lambda

---

## 🔍 Diagnostic Complémentaire

### 📁 Fichiers Clés Analysés

- ✅ `src/vectora_core/newsletter/bedrock_client.py` : Configuration et appels
- ✅ `src/vectora_core/newsletter/assembler.py` : Orchestration
- ✅ `src/vectora_core/newsletter/formatter.py` : Assemblage final
- ✅ `src/vectora_core/__init__.py` : Point d'entrée engine
- ✅ `lambda-env-bedrock-migration.json` : Variables d'environnement

### 🔧 Configuration Validée

- ✅ **Région Bedrock** : us-east-1 (cohérent)
- ✅ **Modèle** : claude-sonnet-4-5 (compatible)
- ✅ **Retry Logic** : Implémenté avec backoff
- ✅ **Fallback** : Mécanisme robuste en place

### 🚨 Points d'Attention

- ⚠️ **Prompt Size** : Newsletter plus complexe que normalisation
- ⚠️ **JSON Parsing** : Structure nested plus fragile
- ⚠️ **Token Limit** : max_tokens: 8000 (vs 4000 normalisation)

---

## ✅ Conclusion Phase 0

### 🎯 Diagnostic Principal

**Le problème de génération newsletter est un symptôme, pas la cause racine.**

**Cause racine** : Throttling Bedrock en normalisation empêche le pipeline d'atteindre la phase newsletter.

**Solution** : Résoudre la scalabilité Bedrock en normalisation avant d'optimiser la newsletter.

### 📋 Prochaines Étapes

1. **Phase 1** : Optimiser normalisation Bedrock (throttling)
2. **Phase 2** : Tests locaux newsletter avec données simulées
3. **Phase 3** : Déploiement optimisations normalisation
4. **Phase 4** : Run E2E complet avec newsletter fonctionnelle

**La newsletter elle-même est techniquement correcte - le problème est l'absence d'inputs normalisés.**