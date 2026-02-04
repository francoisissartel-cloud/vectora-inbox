# Plan Deep Diagnostic - Étape Scoring/Matching

**Date**: 2026-02-04  
**Objectif**: Diagnostic complet de l'étape normalize-score-v2  
**Durée estimée**: 45 minutes  

---

## 🎯 QUE VEUT-ON ACCOMPLIR ?

### Objectif Business
- Filtrer les 30-40 items ingérés pour ne garder que les 15-25 items pertinents pour LAI
- Score de pertinence 0-100 pour chaque item
- Taux de précision > 90% (peu de faux positifs/négatifs)

### Objectif Technique
- **1er appel Bedrock** : Normalisation générique (extraction entités)
- **2ème appel Bedrock** : Domain scoring LAI (évaluation pertinence)
- Temps total : < 5 minutes pour 30 items
- Coût : < $0.50 par run

---

## 📊 ÉTAT ACTUEL (OBSERVÉ)

### Résultats V18-V21
- ✅ Normalisation (1er appel) : Fonctionne (77% companies détectées)
- ❌ Domain scoring (2ème appel) : 100% échec
- ❌ Tous items rejetés avec "Bedrock domain scoring failed"
- ⏱️ Temps : 10-15 minutes (attendu 5 min)

### Symptômes
1. Fallback systématique sur tous les items
2. Pas d'erreur ERROR loggée dans CloudWatch
3. Réponse Bedrock vide ou non-parsable
4. Stage et Dev ont le même problème

---

## 🔍 PLAN D'INVESTIGATION

### PHASE 1: Cartographie Architecture (10 min)

**1.1 Identifier tous les fichiers impliqués**
```bash
# Code
src_v2/vectora_core/normalization/bedrock_client.py (invoke_with_prompt)
src_v2/vectora_core/normalization/bedrock_domain_scorer.py (score_item_for_domain)
src_v2/vectora_core/normalization/__init__.py (orchestration)

# Configuration S3
canonical/prompts/domain_scoring/lai_domain_scoring.yaml
canonical/domains/lai_domain_definition.yaml
canonical/scopes/*.yaml

# Client config
clients/lai_weekly_vXX.yaml
```

**1.2 Vérifier présence fichiers S3**
```bash
# Dev
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/ --profile rag-lai-prod
aws s3 ls s3://vectora-inbox-config-dev/canonical/domains/ --profile rag-lai-prod

# Stage
aws s3 ls s3://vectora-inbox-config-stage/canonical/prompts/domain_scoring/ --profile rag-lai-prod
aws s3 ls s3://vectora-inbox-config-stage/canonical/domains/ --profile rag-lai-prod

# Prod (si existe)
aws s3 ls s3://vectora-inbox-config-prod/canonical/prompts/domain_scoring/ --profile rag-lai-prod
```

**1.3 Documenter versions déployées**
```bash
# Layers versions
aws lambda get-function --function-name vectora-inbox-normalize-score-v2-dev \
  --profile rag-lai-prod --region eu-west-3 \
  --query 'Configuration.Layers[*].Arn' > .tmp/dev_layers.txt

aws lambda get-function --function-name vectora-inbox-normalize-score-v2-stage \
  --profile rag-lai-prod --region eu-west-3 \
  --query 'Configuration.Layers[*].Arn' > .tmp/stage_layers.txt

# Comparer
diff .tmp/dev_layers.txt .tmp/stage_layers.txt
```

---

### PHASE 2: Analyse Flux de Données (15 min)

**2.1 Tracer un item de bout en bout**
```python
# Script: .tmp/trace_item_flow.py
import json

# Charger item ingéré
ingested = json.load(open('.tmp/v21_ingested.json'))
item = ingested[0]

print("=== ITEM INGÉRÉ ===")
print(f"Title: {item.get('title')}")
print(f"Source: {item.get('source_id')}")

# Charger item curé
curated = json.load(open('.tmp/v21_curated.json'))
curated_item = curated[0]

print("\n=== APRÈS NORMALISATION (1er appel) ===")
nc = curated_item.get('normalized_content', {})
print(f"Summary: {nc.get('summary', '')[:100]}")
print(f"Companies: {nc.get('entities', {}).get('companies')}")
print(f"Technologies: {nc.get('entities', {}).get('technologies')}")
print(f"Dosing intervals: {nc.get('entities', {}).get('dosing_intervals')}")

print("\n=== APRÈS DOMAIN SCORING (2ème appel) ===")
ds = curated_item.get('domain_scoring', {})
print(f"has_domain_scoring: {curated_item.get('has_domain_scoring')}")
print(f"is_relevant: {ds.get('is_relevant')}")
print(f"score: {ds.get('score')}")
print(f"reasoning: {ds.get('reasoning')}")

print("\n=== DIAGNOSTIC ===")
if ds.get('reasoning') == 'Bedrock domain scoring failed - fallback to not relevant':
    print("❌ PROBLÈME: Appel Bedrock échoue silencieusement")
    print("   → Vérifier logs CloudWatch pour cet item")
    print("   → Vérifier structure request_body Bedrock")
    print("   → Vérifier réponse Bedrock (vide ? mal formatée ?)")
```

**2.2 Examiner logs CloudWatch détaillés**
```bash
# Récupérer logs avec timestamp précis
aws logs filter-log-events \
  --log-group-name /aws/lambda/vectora-inbox-normalize-score-v2-dev \
  --start-time 1738681260000 \
  --end-time 1738681400000 \
  --profile rag-lai-prod --region eu-west-3 \
  --query "events[*].[timestamp,message]" \
  --output text > .tmp/v21_full_logs.txt

# Chercher patterns spécifiques
grep -i "invoke_with_prompt" .tmp/v21_full_logs.txt
grep -i "domain scoring" .tmp/v21_full_logs.txt
grep -i "DEBUG" .tmp/v21_full_logs.txt
grep -i "Response length" .tmp/v21_full_logs.txt
```

**2.3 Identifier où ça casse**
```
FLUX ATTENDU:
1. score_item_for_domain() appelé
2. item_context construit
3. bedrock_client.invoke_with_prompt() appelé
4. full_prompt construit
5. call_bedrock_with_retry() appelé
6. Bedrock retourne JSON
7. json.loads(response) → OK
8. Retour résultat

FLUX ACTUEL (hypothèses à valider):
1-5. OK
6. Bedrock retourne ??? (vide ? erreur ? texte non-JSON ?)
7. json.loads() → JSONDecodeError
8. Exception catchée → fallback
```

---

### PHASE 3: Analyse Code Source (10 min)

**3.1 Vérifier cohérence invoke_with_prompt**
```bash
# Lire le code actuel
cat src_v2/vectora_core/normalization/bedrock_client.py | grep -A 70 "def invoke_with_prompt"

# Questions:
# - Est-ce que item_dosing_intervals est dans le contexte ?
# - Est-ce que domain_definition est bien passé ?
# - Est-ce que le prompt est bien construit ?
# - Est-ce que la structure request_body est correcte ?
```

**3.2 Comparer avec code qui fonctionnait**
```bash
# Si on a un commit Git qui fonctionnait
git log --oneline --all | grep -i "domain scoring"
git show <commit_hash>:src_v2/vectora_core/normalization/bedrock_client.py > .tmp/old_bedrock_client.py

# Comparer
diff src_v2/vectora_core/normalization/bedrock_client.py .tmp/old_bedrock_client.py
```

**3.3 Identifier fichiers obsolètes**
```bash
# Chercher références à lai_matching (obsolète)
findstr /S /I "lai_matching" src_v2\*.py
findstr /S /I "lai_matching" canonical-config\*.yaml

# Chercher références à domain_matching (obsolète ?)
findstr /S /I "domain_matching" src_v2\*.py

# Lister tous les prompts canonical
aws s3 ls s3://vectora-inbox-config-dev/canonical/prompts/ --recursive --profile rag-lai-prod
```

---

### PHASE 4: Test Isolé Domain Scoring (10 min)

**4.1 Créer test unitaire minimal**
```python
# Script: .tmp/test_domain_scoring_isolated.py
import sys
sys.path.insert(0, 'src_v2')

from vectora_core.normalization.bedrock_client import BedrockNormalizationClient
from vectora_core.shared import s3_io
import yaml

# Charger configs
with open('canonical-config/prompts/domain_scoring/lai_domain_scoring.yaml') as f:
    prompt = yaml.safe_load(f)

with open('canonical-config/domains/lai_domain_definition.yaml') as f:
    domain_def = yaml.safe_load(f)

# Créer client
client = BedrockNormalizationClient(
    model_id='anthropic.claude-3-5-sonnet-20241022-v2:0',
    region='us-east-1'
)

# Contexte minimal
context = {
    'item_title': 'Teva submits NDA for once-monthly olanzapine LAI',
    'item_summary': 'Teva Pharmaceuticals submitted NDA to FDA for TEV-749',
    'item_event_type': 'regulatory',
    'item_effective_date': '2025-12-09',
    'item_companies': 'Teva, MedinCell',
    'item_molecules': 'olanzapine',
    'item_technologies': 'extended-release injectable',
    'item_trademarks': 'TEV-749',
    'item_indications': 'schizophrenia',
    'item_dosing_intervals': 'once-monthly'
}

# Appel
try:
    response = client.invoke_with_prompt(prompt, context, domain_def)
    print(f"Response length: {len(response)}")
    print(f"Response preview: {response[:500]}")
    
    import json
    result = json.loads(response)
    print(f"\n✅ SUCCESS")
    print(f"is_relevant: {result.get('is_relevant')}")
    print(f"score: {result.get('score')}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
```

**4.2 Exécuter test local**
```bash
python .tmp/test_domain_scoring_isolated.py
```

**4.3 Analyser résultat**
- Si ✅ : Le code fonctionne localement → problème environnement Lambda
- Si ❌ : Le code est cassé → identifier la ligne exacte qui échoue

---

### PHASE 5: Analyse Prompts & Configuration (5 min)

**5.1 Télécharger et examiner prompts**
```bash
# Télécharger
aws s3 cp s3://vectora-inbox-config-dev/canonical/prompts/domain_scoring/lai_domain_scoring.yaml \
  .tmp/lai_domain_scoring.yaml --profile rag-lai-prod

aws s3 cp s3://vectora-inbox-config-dev/canonical/domains/lai_domain_definition.yaml \
  .tmp/lai_domain_definition.yaml --profile rag-lai-prod

# Examiner structure
cat .tmp/lai_domain_scoring.yaml
cat .tmp/lai_domain_definition.yaml
```

**5.2 Vérifier cohérence**
```yaml
# lai_domain_scoring.yaml doit avoir:
system_instructions: "..."
user_template: "... {{item_title}} ... {{item_dosing_intervals}} ..."
bedrock_config:
  max_tokens: 1500
  temperature: 0.0

# lai_domain_definition.yaml doit avoir:
domain_name: "Long-Acting Injectables (LAI)"
core_technologies: [...]
pure_players: [...]
```

**5.3 Identifier variables manquantes**
```bash
# Extraire toutes les variables {{xxx}} du prompt
grep -o "{{[^}]*}}" .tmp/lai_domain_scoring.yaml

# Vérifier que toutes sont dans item_context
# item_title, item_summary, item_companies, etc.
```

---

### PHASE 6: Analyse Performance & Scalabilité (5 min)

**6.1 Mesurer temps par étape**
```python
# Analyser logs CloudWatch pour extraire timings
# Chercher patterns:
# - "Appel à Bedrock (tentative X)"
# - "Réponse Bedrock reçue"
# - Calculer delta entre les deux

# Objectif: Identifier si le problème est:
# - Throttling Bedrock (retry multiples)
# - Timeout Lambda
# - Latence réseau
```

**6.2 Calculer coûts**
```
Coût par appel Bedrock Claude 3.5 Sonnet:
- Input: $3 / 1M tokens
- Output: $15 / 1M tokens

Pour 30 items × 2 appels = 60 appels:
- Input moyen: ~2000 tokens/appel = 120K tokens = $0.36
- Output moyen: ~500 tokens/appel = 30K tokens = $0.45
- TOTAL: ~$0.81 par run

Objectif: < $0.50 → Optimiser prompts (réduire tokens)
```

**6.3 Identifier goulots d'étranglement**
```
Temps actuel: 10-15 min pour 30 items
Temps attendu: 5 min

Causes possibles:
1. Appels séquentiels (pas de parallélisation)
2. Retry multiples (throttling)
3. Prompts trop longs (latence Bedrock)
4. Timeout Lambda mal configuré
```

---

## 📋 CHECKLIST DIAGNOSTIC

### Fichiers S3
- [ ] `canonical/prompts/domain_scoring/lai_domain_scoring.yaml` existe en dev
- [ ] `canonical/domains/lai_domain_definition.yaml` existe en dev
- [ ] Mêmes fichiers existent en stage
- [ ] Pas de fichiers obsolètes (lai_matching.yaml)

### Code Source
- [ ] `invoke_with_prompt()` construit le prompt correctement
- [ ] `item_dosing_intervals` est dans le contexte
- [ ] `domain_definition` est passé et converti en YAML
- [ ] Structure `request_body` Bedrock est correcte
- [ ] Pas de `cache_control` dans le code

### Logs & Erreurs
- [ ] Logs CloudWatch montrent "DEBUG invoke_with_prompt"
- [ ] Logs montrent "Response length: X"
- [ ] Identifier si réponse Bedrock est vide ou mal formatée
- [ ] Pas d'erreur ValidationException

### Configuration
- [ ] Toutes les variables {{xxx}} du prompt ont une valeur dans context
- [ ] `bedrock_config` a max_tokens et temperature
- [ ] Client config référence le bon prompt

### Performance
- [ ] Temps par item < 20 secondes
- [ ] Pas de retry excessif (throttling)
- [ ] Coût par run < $1

---

## 🎯 LIVRABLES

### 1. Rapport Diagnostic
```markdown
# Diagnostic Domain Scoring - 2026-02-04

## Cause Racine Identifiée
[Description précise du problème]

## Preuves
- Logs CloudWatch: [extraits]
- Code problématique: [lignes exactes]
- Fichiers manquants: [liste]

## Impact
- Business: 100% items rejetés
- Technique: Fallback systématique
- Coût: Appels Bedrock gaspillés

## Solution Recommandée
[Correction minimale et précise]
```

### 2. Plan d'Action
```markdown
## Corrections Immédiates (< 1h)
1. [Action 1]
2. [Action 2]

## Optimisations Court Terme (< 1 jour)
1. [Optimisation 1]
2. [Optimisation 2]

## Améliorations Long Terme (< 1 semaine)
1. [Amélioration 1]
2. [Amélioration 2]
```

### 3. Tests de Validation
```bash
# Test 1: Domain scoring fonctionne
python .tmp/test_domain_scoring_isolated.py
# Attendu: ✅ is_relevant=True, score>60

# Test 2: Workflow E2E
python scripts/invoke/invoke_e2e_workflow.py --client-id lai_weekly_test --env dev
# Attendu: >60% items relevant

# Test 3: Performance
# Attendu: < 5 min pour 30 items
```

---

## 🚀 PROCHAINES ÉTAPES

1. **Exécuter Phase 1-6** (45 min)
2. **Rédiger rapport diagnostic** (15 min)
3. **Proposer corrections** (pas d'implémentation encore)
4. **Valider avec vous** avant toute modification

---

**Temps total estimé : 1h**  
**Objectif : Comprendre EXACTEMENT ce qui ne va pas avant de toucher au code**
