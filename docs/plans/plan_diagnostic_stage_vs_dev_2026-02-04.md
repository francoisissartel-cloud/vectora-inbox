# Plan Diagnostic Stage vs Dev - Vectora Inbox

**Date**: 2026-02-04  
**Objectif**: Comparer stage (qui fonctionne) vs dev (qui échoue) pour identifier où ça a cassé  
**Durée estimée**: 30 minutes  

---

## 🎯 HYPOTHÈSE

**Stage = versions anciennes qui fonctionnent**  
**Dev = versions récentes avec domain scoring cassé**

En comparant les deux, on identifie exactement où ça a dévié.

---

## 📋 ÉTAPES

### ÉTAPE 1: Run Stage avec données fraîches (10 min)

```bash
# 1. Créer config client pour stage
cp client-config-examples/production/lai_weekly_v17.yaml \
   client-config-examples/production/lai_weekly_stage_test.yaml

# 2. Upload vers S3 stage
aws s3 cp client-config-examples/production/lai_weekly_stage_test.yaml \
  s3://vectora-inbox-config-stage/clients/lai_weekly_stage_test.yaml \
  --profile rag-lai-prod --region eu-west-3

# 3. Run workflow stage
aws lambda invoke \
  --function-name vectora-inbox-ingest-v2-stage \
  --cli-binary-format raw-in-base64-out \
  --payload "{\"client_id\":\"lai_weekly_stage_test\"}" \
  .tmp/stage_ingest_response.json \
  --profile rag-lai-prod --region eu-west-3

aws lambda invoke \
  --function-name vectora-inbox-normalize-score-v2-stage \
  --invocation-type Event \
  --cli-binary-format raw-in-base64-out \
  --payload "{\"client_id\":\"lai_weekly_stage_test\"}" \
  .tmp/stage_normalize_response.json \
  --profile rag-lai-prod --region eu-west-3

# 4. Attendre 5-10 min puis télécharger résultats
aws s3 cp s3://vectora-inbox-data-stage/curated/lai_weekly_stage_test/2026/02/04/items.json \
  .tmp/stage_curated.json --profile rag-lai-prod
```

---

### ÉTAPE 2: Analyser résultats Stage (5 min)

```bash
python -c "
import json

items = json.load(open('.tmp/stage_curated.json', encoding='utf-8'))
total = len(items)
relevant = sum(1 for i in items if i.get('domain_scoring',{}).get('is_relevant'))
scores = [i.get('domain_scoring',{}).get('score',0) for i in items if i.get('domain_scoring',{}).get('is_relevant')]
avg_score = sum(scores)/len(scores) if scores else 0

print('STAGE RESULTS:')
print(f'Total items: {total}')
print(f'Items relevant: {relevant} ({relevant/total*100:.0f}%)')
print(f'Score moyen: {avg_score:.1f}')
print(f'Verdict: {\"✅ OK\" if relevant > 0 else \"❌ FAIL\"}')
"
```

---

### ÉTAPE 3: Comparer versions code (5 min)

```bash
# Récupérer versions déployées
aws lambda get-function --function-name vectora-inbox-normalize-score-v2-stage \
  --profile rag-lai-prod --region eu-west-3 \
  --query 'Configuration.Layers[0].Arn' > .tmp/stage_layer_arn.txt

aws lambda get-function --function-name vectora-inbox-normalize-score-v2-dev \
  --profile rag-lai-prod --region eu-west-3 \
  --query 'Configuration.Layers[0].Arn' > .tmp/dev_layer_arn.txt

# Comparer
echo "STAGE Layer:" && cat .tmp/stage_layer_arn.txt
echo "DEV Layer:" && cat .tmp/dev_layer_arn.txt
```

---

### ÉTAPE 4: Identifier différences code (10 min)

**Fichiers à comparer** :
- `src_v2/vectora_core/normalization/bedrock_client.py` (méthode `invoke_with_prompt`)
- `src_v2/vectora_core/normalization/bedrock_domain_scorer.py`

**Questions clés** :
1. Est-ce que `invoke_with_prompt` existe en stage ?
2. Si oui, quelle est la structure du message Bedrock ?
3. Y a-t-il du `cache_control` en stage ?
4. Quelle est la différence entre stage et dev ?

```bash
# Chercher invoke_with_prompt dans le code actuel
findstr /S /N "def invoke_with_prompt" src_v2\vectora_core\normalization\*.py

# Voir le contenu de la méthode
# (lignes à extraire selon résultat précédent)
```

---

## 📊 COMPARATIF ATTENDU

| Métrique | Stage (attendu) | Dev (actuel) | Écart |
|----------|-----------------|--------------|-------|
| Items relevant | 60-70% | 0% | -60% |
| Score moyen | 65-75 | 0 | -70 |
| Temps exec | 5-10 min | 10-15 min | +50% |
| Erreurs Bedrock | 0 | 31 | +31 |

---

## 🔍 DIAGNOSTIC ATTENDU

**Si stage fonctionne** :
- ✅ Confirme que le problème est dans dev uniquement
- ✅ Permet de comparer le code qui marche vs celui qui ne marche pas
- ✅ Identifie exactement quelle modification a cassé le système

**Hypothèses à valider** :
1. Stage n'a pas `invoke_with_prompt` → utilise une autre méthode
2. Stage a `invoke_with_prompt` mais avec structure message différente
3. Dev a introduit une régression lors d'un refactoring récent

---

## 📝 RAPPORT FINAL

Créer : `docs/reports/diagnostic_stage_vs_dev_2026-02-04.md`

**Contenu** :
```markdown
# Diagnostic Stage vs Dev

## Résultats Stage
- Items relevant: X%
- Score moyen: X
- Temps: X min
- Verdict: ✅/❌

## Résultats Dev
- Items relevant: 0%
- Score moyen: 0
- Temps: 10-15 min
- Verdict: ❌

## Différences Code Identifiées
1. [Fichier X] : Ligne Y - Changement Z
2. [Fichier A] : Ligne B - Changement C

## Cause Racine
[Explication claire de ce qui a cassé]

## Solution
[Code exact à restaurer ou corriger]
```

---

## ✅ CRITÈRES DE SUCCÈS

1. Stage produit des résultats corrects (>60% relevant)
2. Différences code stage/dev identifiées
3. Cause racine comprise
4. Solution claire pour fixer dev

---

**Temps total estimé : 30 minutes**
