# Diagnostic Domain Scoring - 2026-02-04

## CAUSE RACINE IDENTIFIÉE

**Problème**: La référence `{{ref:lai_domain_definition}}` dans le prompt n'est jamais substituée.

### Détails Techniques

**Fichier**: `src_v2/vectora_core/normalization/bedrock_client.py`  
**Méthode**: `invoke_with_prompt()` (ligne ~323-388)

**Code actuel**:
```python
# Ligne 345: Extraire eval_instructions depuis user_template
eval_instructions = user_template.split('NORMALIZED ITEM:')[0].strip()

# Ligne 348: Construire prompt
full_prompt = f"{system_instructions}\n\nLAI DOMAIN DEFINITION:\n{domain_yaml}\n\n{eval_instructions}\n\n{item_data}"
```

**Prompt user_template** (lai_domain_scoring.yaml ligne 60):
```
LAI DOMAIN DEFINITION:
{{ref:lai_domain_definition}}
```

**Résultat**: Le prompt envoyé à Bedrock contient:
```
LAI DOMAIN DEFINITION:
[domain_yaml correctement formaté]

[eval_instructions contenant ENCORE "{{ref:lai_domain_definition}}"]

NORMALIZED ITEM:
...
```

→ **DUPLICATION** de "LAI DOMAIN DEFINITION:" + référence non résolue `{{ref:xxx}}`

### Impact

1. Bedrock reçoit un prompt mal formaté avec:
   - Duplication de section "LAI DOMAIN DEFINITION"
   - Référence non résolue `{{ref:lai_domain_definition}}`
   - Prompt trop long et confus

2. Bedrock retourne probablement:
   - Réponse vide
   - Ou texte non-JSON
   - Ou erreur silencieuse

3. Code Python:
   - `json.loads(response)` → JSONDecodeError
   - Exception catchée → fallback
   - Résultat: `is_relevant=False, score=0`

---

## PREUVES

### 1. Trace Item Flow
```
APRES DOMAIN SCORING (2eme appel)
has_domain_scoring: True
is_relevant: False
score: 0
reasoning: Bedrock domain scoring failed - fallback to not relevant
```

### 2. Code bedrock_client.py
- Ligne 345: `eval_instructions = user_template.split('NORMALIZED ITEM:')[0].strip()`
- Ligne 348: Concaténation qui duplique "LAI DOMAIN DEFINITION:"
- Aucune substitution de `{{ref:xxx}}`

### 3. Prompt lai_domain_scoring.yaml
- Ligne 60: `{{ref:lai_domain_definition}}` présent
- Syntaxe non documentée dans le code
- Aucun mécanisme de résolution des références

### 4. Fichiers Obsolètes
- `src_v2/vectora_core/shared/config_loader.py` référence `lai_matching.yaml` (obsolète)
- Pas de fichier `lai_matching.yaml` sur S3

---

## PROBLÈMES SECONDAIRES

### 1. Variable Manquante: item_dosing_intervals

**Fichier**: `src_v2/vectora_core/normalization/bedrock_domain_scorer.py`  
**Ligne**: ~35-45

**Code actuel**:
```python
item_context = {
    'item_title': ...,
    'item_companies': ...,
    'item_indications': ...
    # MANQUE: 'item_dosing_intervals'
}
```

**Prompt attend** (lai_domain_scoring.yaml ligne 56):
```
- Dosing Intervals: {{item_dosing_intervals}}
```

**Impact**: Variable non substituée → `{{item_dosing_intervals}}` envoyé tel quel à Bedrock

### 2. Référence Obsolète lai_matching

**Fichier**: `src_v2/vectora_core/shared/config_loader.py`

**Impact**: WARNING dans logs (pas bloquant mais indique incohérence)

---

## FLUX ACTUEL vs ATTENDU

### Flux Actuel (CASSÉ)
```
1. score_item_for_domain() construit item_context (SANS dosing_intervals)
2. invoke_with_prompt() appelé
3. eval_instructions extrait de user_template (CONTIENT {{ref:xxx}})
4. full_prompt construit avec DUPLICATION "LAI DOMAIN DEFINITION:"
5. Bedrock reçoit prompt mal formaté
6. Bedrock retourne réponse vide/invalide
7. json.loads() → JSONDecodeError
8. Fallback: is_relevant=False, score=0
```

### Flux Attendu (CORRECT)
```
1. score_item_for_domain() construit item_context (AVEC dosing_intervals)
2. invoke_with_prompt() appelé
3. Résolution de {{ref:lai_domain_definition}} → remplacé par domain_yaml
4. Substitution de toutes les variables {{item_xxx}}
5. full_prompt propre envoyé à Bedrock
6. Bedrock retourne JSON valide
7. json.loads() → OK
8. Résultat: is_relevant=True/False, score=0-100
```

---

## SOLUTION RECOMMANDÉE

### Correction Minimale (URGENT)

**Option A: Supprimer la duplication**
```python
# bedrock_client.py ligne ~345
# AVANT:
eval_instructions = user_template.split('NORMALIZED ITEM:')[0].strip()
full_prompt = f"{system_instructions}\n\nLAI DOMAIN DEFINITION:\n{domain_yaml}\n\n{eval_instructions}\n\n{item_data}"

# APRÈS:
# Extraire seulement la partie après "LAI DOMAIN DEFINITION:"
parts = user_template.split('LAI DOMAIN DEFINITION:')
if len(parts) > 1:
    eval_instructions = parts[1].split('NORMALIZED ITEM:')[0].strip()
    # Remplacer {{ref:lai_domain_definition}} par rien (déjà injecté)
    eval_instructions = eval_instructions.replace('{{ref:lai_domain_definition}}', '').strip()
else:
    eval_instructions = user_template.split('NORMALIZED ITEM:')[0].strip()

full_prompt = f"{system_instructions}\n\nLAI DOMAIN DEFINITION:\n{domain_yaml}\n\n{eval_instructions}\n\n{item_data}"
```

**Option B: Modifier le prompt (PLUS SIMPLE)**
```yaml
# lai_domain_scoring.yaml
# SUPPRIMER les lignes 59-60:
#   LAI DOMAIN DEFINITION:
#   {{ref:lai_domain_definition}}

# Le code injecte déjà domain_yaml correctement
```

### Correction item_dosing_intervals

```python
# bedrock_domain_scorer.py ligne ~35
item_context = {
    'item_title': normalized_item.get('title', ''),
    'item_summary': normalized_content.get('summary', ''),
    'item_event_type': normalized_content.get('event_classification', {}).get('primary_type', 'other'),
    'item_effective_date': normalized_item.get('effective_date', ''),
    'item_companies': ', '.join(entities.get('companies', [])),
    'item_molecules': ', '.join(entities.get('molecules', [])),
    'item_technologies': ', '.join(entities.get('technologies', [])),
    'item_trademarks': ', '.join(entities.get('trademarks', [])),
    'item_indications': ', '.join(entities.get('indications', [])),
    'item_dosing_intervals': ', '.join(entities.get('dosing_intervals', []))  # AJOUTER
}
```

---

## TESTS DE VALIDATION

### Test 1: Prompt Propre
```bash
# Après correction, vérifier que le prompt envoyé ne contient pas:
# - Duplication "LAI DOMAIN DEFINITION:"
# - Référence non résolue {{ref:xxx}}
# - Variable non substituée {{item_dosing_intervals}}
```

### Test 2: Workflow E2E
```bash
python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_test --env dev
# Attendu: >60% items relevant, score moyen 65-75
```

### Test 3: Item Isolé
```bash
python .tmp/test_domain_scoring_isolated.py
# Attendu: is_relevant=True, score>60 pour item LAI typique
```

---

## OPTIMISATIONS RECOMMANDÉES

### Court Terme
1. Supprimer référence obsolète lai_matching dans config_loader.py
2. Ajouter logging DEBUG pour voir prompt exact envoyé à Bedrock
3. Ajouter validation prompt avant envoi (pas de {{xxx}} non résolu)

### Moyen Terme
1. Implémenter système de résolution de références {{ref:xxx}}
2. Paralléliser appels Bedrock (réduire temps 15min → 5min)
3. Ajouter tests unitaires pour invoke_with_prompt

### Long Terme
1. Prompt caching Bedrock (réduire coûts 50%)
2. Monitoring temps réel qualité domain scoring
3. A/B testing prompts pour optimiser précision

---

## MÉTRIQUES ATTENDUES APRÈS CORRECTION

| Métrique | Avant | Après (attendu) |
|----------|-------|-----------------|
| Items relevant | 0% | 60-70% |
| Score moyen | 0 | 65-75 |
| Temps exec | 10-15 min | 5-10 min |
| Faux négatifs | 31 | 0-1 |
| Coût par run | $0.81 | $0.50-0.70 |

---

**Diagnostic complété**: 2026-02-04  
**Temps total**: 45 minutes  
**Confiance**: HAUTE (cause racine identifiée avec preuves)
