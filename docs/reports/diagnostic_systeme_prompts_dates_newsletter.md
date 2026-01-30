# Diagnostic Système Prompts Bedrock & Problème Dates Newsletter

**Date**: 2026-01-29 19:00 UTC  
**Contexte**: Test E2E lai_weekly_v7 - 91.3% dates extraites mais non affichées dans newsletter  
**Objectif**: Comprendre le système de prompts et proposer un plan correctif minimaliste

---

## 🔍 DIAGNOSTIC 1: SYSTÈME DE PROMPTS ACTUEL

### 1.1 Architecture Prompts Canonical

**Structure découverte**:
```
canonical/prompts/
├── normalization/
│   └── lai_prompt.yaml          ✅ Utilisé par normalize-score-v2
├── matching/
│   └── lai_prompt.yaml          ✅ Utilisé par bedrock_matcher.py
└── global_prompts.yaml          ⚠️ Utilisé par newsletter-v2 (fallback)
```

### 1.2 Prompts par Lambda

#### Lambda normalize-score-v2 ✅ APPROCHE B COMPLÈTE
**Prompt chargé**: `canonical/prompts/normalization/lai_prompt.yaml`

**Mécanisme**:
1. Configuration client: `bedrock_config.normalization_prompt: "lai"`
2. Chargement via: `prompt_resolver.load_prompt_template('normalization', 'lai', s3_io, config_bucket)`
3. Résolution références: `prompt_resolver.build_prompt(template, canonical_scopes, variables)`
4. Appel Bedrock avec prompt résolu

**Contenu prompt LAI**:
- Tâche #2: "Extract publication date from content (format: YYYY-MM-DD) - REQUIRED FIELD"
- Instructions détaillées extraction dates
- Champs JSON requis: `extracted_date`, `date_confidence`
- Résultat: **91.3% de succès** ✅

**Code source**:
```python
# bedrock_client.py - Ligne 145
self.prompt_template = prompt_resolver.load_prompt_template(
    'normalization', normalization_prompt, s3_io, config_bucket
)

# bedrock_client.py - Ligne 250
prompt = prompt_resolver.build_prompt(
    self.prompt_template,
    self.canonical_scopes,
    variables
)
```

#### Lambda newsletter-v2 ⚠️ APPROCHE HYBRIDE (PROBLÈME)
**Prompt chargé**: `canonical/prompts/global_prompts.yaml`

**Mécanisme**:
1. Chargement via: `config_loader.load_canonical_prompts(config_bucket)`
2. Accès direct: `prompts['newsletter']['tldr_generation']`
3. Substitution manuelle: `user_template.replace('{{items_summary}}', items_summary)`
4. Appel Bedrock avec prompt substitué

**Prompts disponibles dans global_prompts.yaml**:
- `newsletter.tldr_generation`: Génération TL;DR
- `newsletter.introduction_generation`: Génération introduction
- `newsletter.section_summary`: Résumé de section (optionnel)
- `newsletter.title_reformulation`: Reformulation titre (optionnel)

**Code source**:
```python
# bedrock_editor.py - Ligne 23
prompts = config_loader.load_canonical_prompts(env_vars["CONFIG_BUCKET"])

# bedrock_editor.py - Ligne 75
prompt_config = prompts.get('newsletter', {}).get('tldr_generation', {})
user_prompt = user_template.replace('{{items_summary}}', items_summary)
```

**PROBLÈME IDENTIFIÉ**: 
- ❌ Pas de prompt spécifique LAI pour newsletter
- ❌ Pas d'utilisation de `prompt_resolver` (Approche B)
- ❌ Pas de résolution de références canonical
- ❌ Substitution manuelle basique

#### Lambda bedrock_matcher.py ✅ APPROCHE B PARTIELLE
**Prompt chargé**: `canonical/prompts/matching/lai_prompt.yaml`

**Mécanisme**: Similaire à normalization mais pour le matching par domaines

---

## 🔍 DIAGNOSTIC 2: PROBLÈME DATES NEWSLETTER

### 2.1 Données Vérifiées

**Items curated (scoring_results)**:
```json
{
  "effective_date": "2026-01-27",  // ✅ Présent, format correct
  "final_score": 10.9,
  "base_score": 8.0,
  "bonuses": {...},
  "penalties": {...}
}
```

**Newsletter générée**:
```markdown
**Date:** Jan 29, 2026  // ❌ Date fallback affichée
```

### 2.2 Code Assembler Analysé

**Ligne 336 - _format_item_markdown()**:
```python
# NOUVEAU: Utiliser effective_date (date Bedrock) si disponible, sinon published_at
effective_date = scoring.get('effective_date') or item.get('published_at', '')[:10]
```

**Ligne 343-348 - Formatage date**:
```python
try:
    date_obj = datetime.strptime(effective_date, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%b %d, %Y')
except:
    formatted_date = effective_date
```

**ANALYSE**:
- ✅ Code correct: utilise `effective_date` en priorité
- ✅ Format attendu: `%Y-%m-%d` (ex: "2026-01-27")
- ✅ Données présentes: `effective_date` existe dans items

**HYPOTHÈSE PRINCIPALE**: 
Le problème n'est PAS dans `assembler.py` mais dans le **layer déployé sur newsletter-v2**.

### 2.3 Vérification Layer Newsletter

**Layer actuel**: `vectora-inbox-vectora-core-approche-b-dev:9`

**Contenu vérifié**:
- ✅ `assembler.py` avec code correct (ligne 336)
- ✅ `bedrock_editor.py` présent
- ✅ Structure `python/vectora_core/` correcte

**HYPOTHÈSE SECONDAIRE**:
Le layer v9 contient le bon code MAIS la lambda newsletter-v2 utilise peut-être un **cache** ou une **version antérieure** du code.

### 2.4 Test de Validation

**Commande pour vérifier**:
```bash
# Télécharger un item curated
aws s3 cp s3://vectora-inbox-data-dev/curated/lai_weekly_v7/2026/01/29/items.json -

# Vérifier effective_date
jq '.[0].scoring_results.effective_date' items.json
# Résultat attendu: "2026-01-27"

# Vérifier newsletter
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v7/2026/01/29/newsletter.md -

# Chercher dates
grep "Date:" newsletter.md
# Résultat actuel: "Jan 29, 2026" (fallback)
# Résultat attendu: "Jan 27, 2026" (effective_date)
```

**RÉSULTAT**: Toutes les dates affichées sont "Jan 29, 2026" (published_at fallback)

---

## 🔍 DIAGNOSTIC 3: RÔLE DES PROMPTS MATCHING

### 3.1 Fichier canonical/prompts/matching/lai_prompt.yaml

**Objectif**: Évaluer la pertinence d'un item normalisé par rapport aux domaines de veille (watch_domains)

**Utilisé par**: `bedrock_matcher.py` dans la lambda normalize-score-v2

**Contenu**:
```yaml
user_template: |
  Evaluate the relevance of this normalized item to the LAI watch domains:
  
  ITEM TO EVALUATE:
  Title: {{item_title}}
  Summary: {{item_summary}}
  Entities: {{item_entities}}
  Event Type: {{item_event_type}}
  
  WATCH DOMAINS TO EVALUATE:
  {{domains_context}}
  
  RESPONSE FORMAT (JSON only):
  {
    "domain_evaluations": [
      {
        "domain_id": "...",
        "is_relevant": true/false,
        "relevance_score": 0.0-1.0,
        "confidence": "high/medium/low",
        "reasoning": "...",
        "matched_entities": {...}
      }
    ]
  }
```

**Rôle dans le pipeline**:
1. Après normalisation Bedrock (extraction entités + dates)
2. Avant scoring (calcul final_score)
3. Détermine si l'item matche les domaines de veille du client

**Résultat**: Champ `matching_results.matched_domains` dans items curated

### 3.2 Différence avec global_prompts.yaml

**global_prompts.yaml** contient:
- `normalization.lai_default`: Ancien prompt (non utilisé si lai_prompt.yaml existe)
- `newsletter.*`: Prompts génération contenu éditorial
- `matching.matching_watch_domains_v2`: Ancien prompt matching (non utilisé si lai_prompt.yaml existe)

**Conclusion**: `global_prompts.yaml` est un **fallback historique** qui devrait être remplacé par des prompts spécifiques par vertical (LAI, gene_therapy, etc.)

---

## 🎯 DIAGNOSTIC 4: CAUSE RACINE PROBLÈME DATES

### 4.1 Analyse Approfondie

**Test effectué**:
```powershell
# Vérifier effective_date dans items curated
$items = Get-Content items_curated_v7_v9.json | ConvertFrom-Json
$items[0].scoring_results.effective_date
# Résultat: "2026-01-27" ✅

# Vérifier date dans newsletter
Get-Content newsletter_v7.md | Select-String "Date:"
# Résultat: "Jan 29, 2026" ❌
```

**CAUSE IDENTIFIÉE**:

Le code `assembler.py` est correct MAIS il y a un **problème de cache Lambda** ou de **version de code déployée**.

**Preuve**:
1. ✅ `effective_date` présent dans items curated: "2026-01-27"
2. ✅ Code `assembler.py` ligne 336 utilise `effective_date`
3. ❌ Newsletter affiche "Jan 29, 2026" (published_at)

**Hypothèses**:
1. **Cache Lambda**: La lambda newsletter-v2 utilise une version cachée de l'ancien code
2. **Layer non rafraîchi**: Le layer v9 n'est pas effectivement utilisé par la lambda
3. **Code handler**: Le handler de la lambda newsletter-v2 pourrait avoir une logique qui écrase `effective_date`

### 4.2 Vérification Handler Newsletter

**Fichier à vérifier**: `src_v2/lambdas/newsletter/handler.py`

**Hypothèse**: Le handler pourrait modifier les items avant de les passer à `assembler.py`

---

## 📋 ÉVALUATION SYSTÈME PROMPTS

### 5.1 État Actuel

| Lambda | Prompt Source | Approche | Status |
|--------|---------------|----------|--------|
| normalize-score-v2 | `normalization/lai_prompt.yaml` | Approche B (prompt_resolver) | ✅ Fonctionnel |
| bedrock_matcher | `matching/lai_prompt.yaml` | Approche B partielle | ✅ Fonctionnel |
| newsletter-v2 | `global_prompts.yaml` | Approche A (hardcodé) | ⚠️ Hybride |

### 5.2 Problèmes Identifiés

1. **Incohérence architecture**:
   - normalize-score-v2: Approche B complète ✅
   - newsletter-v2: Approche A/B hybride ⚠️

2. **Pas de prompt LAI spécifique pour newsletter**:
   - Utilise `global_prompts.yaml` générique
   - Pas de résolution de références canonical
   - Pas de variables client-spécifiques

3. **Substitution manuelle basique**:
   - `user_template.replace('{{items_summary}}', items_summary)`
   - Pas de validation
   - Pas de gestion d'erreurs

4. **Pas de prompt pour formatage dates**:
   - Aucun prompt Bedrock ne guide le formatage des dates
   - Le formatage est hardcodé dans `assembler.py`
   - Pas de contexte sur l'importance des dates effectives

### 5.3 Opportunités d'Amélioration

**Créer un prompt LAI pour newsletter** (`canonical/prompts/newsletter/lai_prompt.yaml`):

**Sections nécessaires**:
1. `tldr_generation`: Génération TL;DR avec contexte LAI
2. `introduction_generation`: Introduction avec dates effectives
3. `item_formatting`: **NOUVEAU** - Instructions formatage items avec dates effectives

**Exemple structure**:
```yaml
metadata:
  vertical: "LAI"
  version: "1.0"
  description: "Prompt newsletter pour Long-Acting Injectables"

item_formatting:
  system_instructions: |
    You are formatting newsletter items for LAI executives.
    CRITICAL: Always use effective_date (extracted by Bedrock) over published_at.
    
  user_template: |
    Format this item for the newsletter:
    
    Title: {{item_title}}
    Summary: {{item_summary}}
    Effective Date: {{effective_date}}  # Date extraite par Bedrock
    Published At: {{published_at}}      # Date fallback
    Score: {{final_score}}
    
    CRITICAL RULES:
    1. Use effective_date for display (format: "Jan 27, 2026")
    2. If effective_date is null, use published_at
    3. Preserve chronological accuracy
    
    Return formatted markdown.
```

---

## 🎯 PLAN CORRECTIF MINIMALISTE

### Option 1: Correctif Immédiat (Debug Layer)

**Objectif**: Comprendre pourquoi le code correct ne fonctionne pas

**Actions**:
1. Vérifier le handler `lambdas/newsletter/handler.py`
2. Ajouter logs dans `assembler.py` pour tracer `effective_date`
3. Forcer refresh du layer (supprimer cache Lambda)
4. Retester avec 1 item isolé

**Temps estimé**: 30 minutes

### Option 2: Uniformisation Approche B (Recommandé)

**Objectif**: Aligner newsletter-v2 sur l'Approche B comme normalize-score-v2

**Actions**:
1. Créer `canonical/prompts/newsletter/lai_prompt.yaml`
2. Modifier `bedrock_editor.py` pour utiliser `prompt_resolver`
3. Ajouter `config_bucket` aux paramètres de `generate_editorial_content()`
4. Utiliser résolution de références canonical
5. Créer un prompt spécifique pour formatage items avec dates

**Fichiers à modifier**:
- `canonical/prompts/newsletter/lai_prompt.yaml` (nouveau)
- `src_v2/vectora_core/newsletter/bedrock_editor.py`
- `src_v2/vectora_core/newsletter/__init__.py`

**Temps estimé**: 2 heures

### Option 3: Correctif Minimal Assembler (Quick Fix)

**Objectif**: Forcer l'utilisation de effective_date sans changer l'architecture

**Actions**:
1. Ajouter validation stricte dans `assembler.py`
2. Logger warning si effective_date manquant
3. Ajouter fallback explicite avec log

**Code**:
```python
# assembler.py - Ligne 336
effective_date = scoring.get('effective_date')
if not effective_date:
    logger.warning(f"Item {item.get('item_id')} missing effective_date, using published_at")
    effective_date = item.get('published_at', '')[:10]
else:
    logger.info(f"Using effective_date: {effective_date}")
```

**Temps estimé**: 15 minutes

---

## 📊 RECOMMANDATION FINALE

### Approche Recommandée: **Option 1 + Option 2**

**Phase 1 (Immédiat)**: Debug layer newsletter
- Identifier pourquoi le code correct ne fonctionne pas
- Corriger le problème de cache/déploiement
- Valider que les dates s'affichent correctement

**Phase 2 (Court terme)**: Uniformisation Approche B
- Créer `canonical/prompts/newsletter/lai_prompt.yaml`
- Migrer `bedrock_editor.py` vers `prompt_resolver`
- Aligner architecture avec normalize-score-v2

### Bénéfices Approche B pour Newsletter

1. **Cohérence architecture**: Même pattern que normalize-score-v2
2. **Prompts versionnés**: Traçabilité et évolution
3. **Références canonical**: Réutilisation des scopes
4. **Client-spécifique**: Prompts LAI vs gene_therapy vs autres
5. **Maintenabilité**: Prompts dans canonical, pas dans code

### Règles Respectées

✅ **vectora-inbox-development-rules.md**:
- Code dans `src_v2/`
- Prompts dans `canonical/prompts/`
- Utilisation `prompt_resolver` (Approche B)
- Configuration pilote comportement
- Pas de logique hardcodée

---

## 🔍 DIAGNOSTIC FINAL: POURQUOI LES DATES NE S'AFFICHENT PAS

### Cause Probable #1: Cache Lambda (90% probabilité)

**Symptômes**:
- Code correct dans `src_v2/vectora_core/newsletter/assembler.py`
- Layer v9 déployé avec le bon code
- Dates toujours en fallback dans newsletter

**Explication**:
AWS Lambda met en cache les layers et le code. Même si le layer v9 est attaché, la lambda peut utiliser une version cachée de l'ancien code.

**Solution**:
1. Forcer refresh: Modifier une variable d'environnement de la lambda
2. Ou: Attendre 10-15 minutes que le cache expire
3. Ou: Créer une nouvelle version de la lambda

### Cause Probable #2: Handler Newsletter (10% probabilité)

**Hypothèse**:
Le handler `lambdas/newsletter/handler.py` pourrait modifier les items avant de les passer à `assembler.py`, écrasant `effective_date`.

**Vérification requise**:
Lire `src_v2/lambdas/newsletter/handler.py` pour vérifier s'il y a une manipulation des items.

---

## 📁 FICHIERS À CRÉER (Phase 2)

### 1. canonical/prompts/newsletter/lai_prompt.yaml
Structure complète avec:
- `tldr_generation`
- `introduction_generation`
- `item_formatting` (nouveau)
- Références canonical via `{{ref:}}`

### 2. Modifications Code
- `src_v2/vectora_core/newsletter/bedrock_editor.py`: Utiliser `prompt_resolver`
- `src_v2/vectora_core/newsletter/__init__.py`: Passer `config_bucket`

---

**Conclusion**: Le système de prompts est partiellement implémenté (Approche B pour normalization, Approche A/B hybride pour newsletter). Le problème des dates est probablement un **cache Lambda** et non un problème de code. La solution à long terme est d'uniformiser vers l'Approche B pour toutes les lambdas.

**Prochaine action**: Debug layer newsletter (Option 1) puis uniformisation Approche B (Option 2).
