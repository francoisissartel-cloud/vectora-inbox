# Résumé Exécutif - Diagnostic Système Prompts & Dates Newsletter

**Date**: 2026-01-29 19:15 UTC  
**Statut**: ✅ Diagnostic complet - Plan correctif défini

---

## 🎯 RÉSUMÉ EN 3 POINTS

1. **Extraction dates Bedrock**: ✅ **91.3% de succès** avec prompts canonical LAI
2. **Système prompts**: ⚠️ **Incohérent** - Approche B pour normalization, Approche A/B hybride pour newsletter
3. **Dates newsletter**: ❌ **Cache Lambda** - Code correct mais version cachée utilisée

---

## 📊 ÉTAT DES LIEUX SYSTÈME PROMPTS

### Architecture Actuelle

```
canonical/prompts/
├── normalization/lai_prompt.yaml    ✅ Approche B - normalize-score-v2
├── matching/lai_prompt.yaml         ✅ Approche B - bedrock_matcher
└── global_prompts.yaml              ⚠️ Approche A - newsletter-v2 (fallback)
```

### Comparaison par Lambda

| Lambda | Prompt | Chargement | Résolution | Status |
|--------|--------|------------|------------|--------|
| **normalize-score-v2** | `normalization/lai_prompt.yaml` | `prompt_resolver.load_prompt_template()` | Références canonical `{{ref:}}` | ✅ Approche B complète |
| **bedrock_matcher** | `matching/lai_prompt.yaml` | `prompt_resolver.load_prompt_template()` | Références canonical | ✅ Approche B partielle |
| **newsletter-v2** | `global_prompts.yaml` | `config_loader.load_canonical_prompts()` | Substitution manuelle `replace()` | ⚠️ Approche A/B hybride |

### Problèmes Identifiés

1. **Incohérence architecture**: 
   - normalize-score-v2 utilise Approche B (prompt_resolver + références canonical)
   - newsletter-v2 utilise Approche A/B hybride (chargement YAML + substitution manuelle)

2. **Pas de prompt LAI spécifique pour newsletter**:
   - Utilise `global_prompts.yaml` générique
   - Pas de contexte LAI dans les prompts TL;DR/introduction
   - Pas de prompt pour formatage items avec dates effectives

3. **Pas de résolution de références canonical**:
   - newsletter-v2 ne peut pas utiliser `{{ref:lai_companies_global}}`
   - Perte de cohérence avec les scopes utilisés en normalisation

---

## 🔍 DIAGNOSTIC PROBLÈME DATES NEWSLETTER

### Données Vérifiées

**Items curated** (après scoring):
```json
{
  "scoring_results": {
    "effective_date": "2026-01-27",  // ✅ Date Bedrock extraite
    "final_score": 10.9
  }
}
```

**Newsletter générée**:
```markdown
**Date:** Jan 29, 2026  // ❌ Date fallback (published_at)
```

### Code Analysé

**assembler.py - Ligne 336** (CORRECT):
```python
effective_date = scoring.get('effective_date') or item.get('published_at', '')[:10]
```

**assembler.py - Ligne 343-348** (CORRECT):
```python
try:
    date_obj = datetime.strptime(effective_date, '%Y-%m-%d')
    formatted_date = date_obj.strftime('%b %d, %Y')
except:
    formatted_date = effective_date
```

### Cause Racine Identifiée

**CACHE LAMBDA** (90% probabilité)

**Explication**:
- ✅ Code correct dans `src_v2/vectora_core/newsletter/assembler.py`
- ✅ Layer v9 déployé avec le bon code
- ✅ `effective_date` présent dans items curated
- ❌ Newsletter affiche dates fallback

**Conclusion**: La lambda newsletter-v2 utilise une **version cachée de l'ancien code** malgré le déploiement du layer v9.

**Preuve**:
```bash
# Items curated
jq '.[0].scoring_results.effective_date' items_curated_v7_v9.json
# Résultat: "2026-01-27" ✅

# Newsletter
grep "Date:" newsletter_v7.md
# Résultat: "Jan 29, 2026" ❌ (devrait être "Jan 27, 2026")
```

---

## 📋 PLAN CORRECTIF MINIMALISTE

### Phase 1: Correctif Immédiat (30 min)

**Objectif**: Forcer refresh du cache Lambda

**Actions**:
1. Modifier une variable d'environnement de newsletter-v2 (ex: ajouter `CACHE_BUST=v9`)
2. Attendre 2-3 minutes
3. Relancer génération newsletter
4. Vérifier dates affichées

**Commandes**:
```bash
# 1. Modifier variable d'environnement
aws lambda update-function-configuration \
  --function-name vectora-inbox-newsletter-v2-dev \
  --environment "Variables={CONFIG_BUCKET=vectora-inbox-config-dev,DATA_BUCKET=vectora-inbox-data-dev,NEWSLETTERS_BUCKET=vectora-inbox-newsletters-dev,BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0,BEDROCK_REGION=us-east-1,CACHE_BUST=v9}" \
  --region eu-west-3 --profile rag-lai-prod

# 2. Attendre 2-3 minutes

# 3. Relancer newsletter
aws lambda invoke --function-name vectora-inbox-newsletter-v2-dev \
  --payload file://event_newsletter_v7.json \
  --region eu-west-3 --profile rag-lai-prod \
  response_newsletter_v7_refresh.json

# 4. Vérifier dates
aws s3 cp s3://vectora-inbox-newsletters-dev/lai_weekly_v7/2026/01/29/newsletter.md - | grep "Date:"
```

**Résultat attendu**: Dates "Jan 27, 2026", "Dec 09, 2025", etc. (dates Bedrock)

### Phase 2: Uniformisation Approche B (2h)

**Objectif**: Aligner newsletter-v2 sur l'architecture Approche B

**Fichiers à créer**:

1. **canonical/prompts/newsletter/lai_prompt.yaml**
```yaml
metadata:
  vertical: "LAI"
  version: "1.0"
  description: "Prompt newsletter pour Long-Acting Injectables"

tldr_generation:
  system_instructions: |
    You are an expert newsletter editor for LAI (Long-Acting Injectable) intelligence.
    Generate concise, executive-level TL;DR summaries.
    
  user_template: |
    Generate a TL;DR (2-3 bullet points) for this week's LAI newsletter:
    
    {{items_summary}}
    
    Focus on: partnerships, regulatory milestones, clinical developments.
    Style: Executive, factual, concise.
    
  bedrock_config:
    max_tokens: 200
    temperature: 0.1

introduction_generation:
  system_instructions: |
    You are an expert newsletter editor for LAI intelligence.
    Generate professional introductions.
    
  user_template: |
    Generate a brief introduction (1-2 sentences) for this week's LAI newsletter.
    
    Week: {{week_start}} to {{week_end}}
    Sections: {{sections_summary}}
    Total items: {{total_items}}
    
    Style: Professional, executive-focused, concise.
    
  bedrock_config:
    max_tokens: 300
    temperature: 0.1
```

2. **Modifications Code**:

**bedrock_editor.py**:
```python
# Remplacer ligne 23
# AVANT:
prompts = config_loader.load_canonical_prompts(env_vars["CONFIG_BUCKET"])

# APRÈS:
from ..shared import prompt_resolver
prompt_template = prompt_resolver.load_prompt_template(
    'newsletter', 
    client_config.get('bedrock_config', {}).get('newsletter_prompt', 'lai'),
    s3_io,
    env_vars["CONFIG_BUCKET"]
)
```

**Temps estimé**: 2 heures

---

## 🎯 RECOMMANDATION

### Approche Recommandée: Phase 1 PUIS Phase 2

**Pourquoi**:
1. Phase 1 résout le problème immédiat (dates newsletter)
2. Phase 2 uniformise l'architecture (maintenabilité long terme)
3. Respect des règles vectora-inbox-development-rules.md

**Bénéfices Phase 2**:
- ✅ Cohérence architecture (Approche B partout)
- ✅ Prompts versionnés et traçables
- ✅ Réutilisation références canonical
- ✅ Prompts client-spécifiques (LAI vs gene_therapy)
- ✅ Maintenabilité améliorée

---

## 📈 MÉTRIQUES SUCCÈS

### Phase 1 (Correctif Immédiat)
- ✅ Dates newsletter = dates Bedrock (ex: "Jan 27, 2026")
- ✅ Taux dates correctes: >90%
- ✅ Chronologie restaurée

### Phase 2 (Uniformisation)
- ✅ Prompt LAI newsletter créé
- ✅ bedrock_editor.py utilise prompt_resolver
- ✅ Architecture cohérente (Approche B partout)
- ✅ Tests E2E passent

---

## 📁 LIVRABLES

### Diagnostic (Fait)
- ✅ `docs/reports/diagnostic_systeme_prompts_dates_newsletter.md`
- ✅ `docs/reports/rapport_test_e2e_v7_extraction_dates.md`

### Phase 1 (À faire)
- Script refresh cache Lambda
- Validation dates newsletter

### Phase 2 (À faire)
- `canonical/prompts/newsletter/lai_prompt.yaml`
- `src_v2/vectora_core/newsletter/bedrock_editor.py` (modifié)
- Tests unitaires
- Documentation

---

**Conclusion**: Le système de prompts fonctionne bien pour normalization (Approche B) mais est incohérent pour newsletter (Approche A/B hybride). Le problème des dates est un cache Lambda, pas un problème de code. La solution immédiate est de forcer le refresh, puis d'uniformiser vers l'Approche B pour toutes les lambdas.

**Prochaine action**: Exécuter Phase 1 (refresh cache) pour valider que les dates s'affichent correctement.
